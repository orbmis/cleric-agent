#!/usr/bin/env python3
"""Fetch new X (Twitter) bookmarks since the last run.

Deterministic, dependency-free (stdlib only). Handles the two things that are
easy to get wrong with the X bookmarks API:

  1. Auth. The bookmarks endpoint is user-context only (OAuth 2.0 PKCE). An app
     API key / bearer token returns 403. We refresh a stored refresh token into
     a short-lived access token on every run. X rotates the refresh token on
     each refresh, so we persist the new one back to the token file immediately.

  2. "This week." The API returns each tweet's *authored* time, never the time
     *you* bookmarked it. So you cannot filter by date. Instead we diff the
     current bookmark set against the IDs we saw last run: new = current - seen.

Output: JSON (default) or Markdown to stdout. The Friday digest consumes the
JSON; a human can eyeball the Markdown.

See README.md for setup and SKILL.md for how the agent should invoke this.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

from _env import load_dotenv

TOKEN_URL = "https://api.x.com/2/oauth2/token"
ME_URL = "https://api.x.com/2/users/me"
BOOKMARKS_URL = "https://api.x.com/2/users/{user_id}/bookmarks"

# Home for secrets/state. Deliberately OUTSIDE the repo so nothing sensitive is
# ever committed. Override with X_TOKEN_FILE / X_BOOKMARKS_STATE.
DEFAULT_DIR = os.path.expanduser("~/.config/openclaw/x-bookmarks")
DEFAULT_TOKEN_FILE = os.path.join(DEFAULT_DIR, "token.json")
DEFAULT_STATE_FILE = os.path.join(DEFAULT_DIR, "state.json")

TWEET_FIELDS = "created_at,public_metrics,note_tweet,entities,lang"
EXPANSIONS = "author_id"
USER_FIELDS = "username,name"


class BookmarksError(RuntimeError):
    """Anything the caller should see as a clean, actionable failure."""


# --------------------------------------------------------------------------- #
# Small JSON file helpers                                                      #
# --------------------------------------------------------------------------- #
def _read_json(path: str) -> dict:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError as exc:
        raise BookmarksError(f"Corrupt JSON at {path}: {exc}") from exc


def _write_json(path: str, data: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = f"{path}.tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
    os.replace(tmp, path)  # atomic; never leaves a half-written token file
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass  # best effort on platforms without POSIX perms


# --------------------------------------------------------------------------- #
# HTTP                                                                         #
# --------------------------------------------------------------------------- #
def _request(url: str, *, method: str = "GET", headers=None, data=None) -> dict:
    req = urllib.request.Request(url, method=method, data=data, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        if exc.code == 403:
            raise BookmarksError(
                "403 from X. The bookmarks endpoint needs user-context OAuth 2.0 "
                "with the 'bookmark.read' scope — a plain app key/bearer will not "
                "work. Re-run authorize.py to (re)issue a refresh token.\n" + body
            ) from exc
        if exc.code == 429:
            raise BookmarksError(
                "429 rate limited by X. Try again after the reset window.\n" + body
            ) from exc
        raise BookmarksError(f"HTTP {exc.code} from X: {body}") from exc
    except urllib.error.URLError as exc:
        raise BookmarksError(f"Network error talking to X: {exc.reason}") from exc


# --------------------------------------------------------------------------- #
# Auth: refresh token -> access token (and persist the rotated refresh token)  #
# --------------------------------------------------------------------------- #
def get_access_token(token_file: str) -> str:
    client_id = os.environ.get("X_CLIENT_ID")
    client_secret = os.environ.get("X_CLIENT_SECRET")  # only for confidential apps
    if not client_id:
        raise BookmarksError("X_CLIENT_ID is not set (see README.md).")

    token_state = _read_json(token_file)
    refresh_token = token_state.get("refresh_token") or os.environ.get("X_REFRESH_TOKEN")
    if not refresh_token:
        raise BookmarksError(
            f"No refresh token in {token_file} or X_REFRESH_TOKEN. "
            "Run authorize.py once to mint one."
        )

    form = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": client_id,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if client_secret:
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers["Authorization"] = f"Basic {basic}"

    payload = _request(
        TOKEN_URL,
        method="POST",
        headers=headers,
        data=urllib.parse.urlencode(form).encode(),
    )

    if "access_token" not in payload:
        raise BookmarksError(f"Token refresh returned no access_token: {payload}")

    # X rotates the refresh token — persist the new one or the next run breaks.
    new_refresh = payload.get("refresh_token", refresh_token)
    _write_json(token_file, {"refresh_token": new_refresh})
    return payload["access_token"]


# --------------------------------------------------------------------------- #
# Bookmarks fetch (paginated)                                                  #
# --------------------------------------------------------------------------- #
def resolve_user_id(access_token: str) -> str:
    if os.environ.get("X_USER_ID"):
        return os.environ["X_USER_ID"]
    me = _request(ME_URL, headers={"Authorization": f"Bearer {access_token}"})
    try:
        return me["data"]["id"]
    except (KeyError, TypeError) as exc:
        raise BookmarksError(f"Could not resolve user id from /users/me: {me}") from exc


def fetch_all_bookmarks(access_token: str, user_id: str) -> list[dict]:
    """Return every current bookmark, flattened with author handle attached."""
    headers = {"Authorization": f"Bearer {access_token}"}
    base = BOOKMARKS_URL.format(user_id=user_id)
    params = {
        "max_results": "100",
        "tweet.fields": TWEET_FIELDS,
        "expansions": EXPANSIONS,
        "user.fields": USER_FIELDS,
    }

    bookmarks: list[dict] = []
    next_token = None
    while True:
        query = dict(params)
        if next_token:
            query["pagination_token"] = next_token
        page = _request(f"{base}?{urllib.parse.urlencode(query)}", headers=headers)

        users = {u["id"]: u for u in page.get("includes", {}).get("users", [])}
        for tweet in page.get("data", []):
            author = users.get(tweet.get("author_id"), {})
            note = (tweet.get("note_tweet") or {}).get("text")  # long-form tweets
            bookmarks.append(
                {
                    "id": tweet["id"],
                    "text": note or tweet.get("text", ""),
                    "created_at": tweet.get("created_at"),
                    "author_handle": author.get("username"),
                    "author_name": author.get("name"),
                    "metrics": tweet.get("public_metrics", {}),
                    "url": f"https://x.com/{author.get('username', 'i')}/status/{tweet['id']}",
                }
            )

        next_token = page.get("meta", {}).get("next_token")
        if not next_token:
            return bookmarks


# --------------------------------------------------------------------------- #
# Diff against last run                                                        #
# --------------------------------------------------------------------------- #
def diff_new(current: list[dict], state_file: str, *, seed: bool) -> list[dict]:
    state = _read_json(state_file)
    seen = set(state.get("seen_ids", []))
    current_ids = [b["id"] for b in current]

    new_items = [b for b in current if b["id"] not in seen]

    # Persist the current set as the new baseline (also drops un-bookmarked ids).
    _write_json(state_file, {"seen_ids": current_ids})

    if seed:
        # Baseline only: record what exists now, emit nothing. Use on first run
        # so the first real digest isn't a dump of your entire history.
        return []
    return new_items


# --------------------------------------------------------------------------- #
# Rendering                                                                    #
# --------------------------------------------------------------------------- #
def render_markdown(items: list[dict]) -> str:
    if not items:
        return "_No new X bookmarks this week._"
    lines = []
    for b in items:
        who = f"@{b['author_handle']}" if b["author_handle"] else "unknown"
        snippet = " ".join(b["text"].split())
        if len(snippet) > 200:
            snippet = snippet[:197] + "…"
        likes = b["metrics"].get("like_count", 0)
        lines.append(f"- **{who}** — {snippet}\n  {b['url']} · ♥ {likes}")
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
# Entry point                                                                  #
# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    load_dotenv()  # populate os.environ from .env before reading config below
    parser = argparse.ArgumentParser(description="Fetch new X bookmarks since last run.")
    parser.add_argument("--format", choices=["json", "markdown"], default="json")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Record current bookmarks as the baseline and emit nothing (first run).",
    )
    parser.add_argument("--token-file", default=os.environ.get("X_TOKEN_FILE", DEFAULT_TOKEN_FILE))
    parser.add_argument("--state-file", default=os.environ.get("X_BOOKMARKS_STATE", DEFAULT_STATE_FILE))
    args = parser.parse_args(argv)

    try:
        access_token = get_access_token(args.token_file)
        user_id = resolve_user_id(access_token)
        current = fetch_all_bookmarks(access_token, user_id)
        new_items = diff_new(current, args.state_file, seed=args.seed)
    except BookmarksError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.format == "markdown":
        print(render_markdown(new_items))
    else:
        print(json.dumps({"count": len(new_items), "bookmarks": new_items}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
