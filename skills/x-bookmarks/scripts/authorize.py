#!/usr/bin/env python3
"""One-time OAuth 2.0 PKCE authorization for X bookmarks.

Run this once, interactively, from a machine with a browser. It:

  1. builds the X authorize URL (scopes include offline_access -> refresh token),
  2. spins up a tiny localhost server to catch the redirect,
  3. exchanges the returned code for tokens,
  4. writes the refresh token to the token file that fetch_bookmarks.py reads.

After this, the scheduled task runs headless forever (until you revoke access).

Prereqs (see README.md):
  * An X app with OAuth 2.0 enabled.
  * Redirect URI registered on the app EXACTLY matching --redirect-uri below.
  * env X_CLIENT_ID set (and X_CLIENT_SECRET too, if it's a confidential app).

Usage:
  X_CLIENT_ID=... python3 authorize.py
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import http.server
import json
import os
import secrets
import urllib.parse
import urllib.request
import webbrowser

AUTHORIZE_URL = "https://x.com/i/oauth2/authorize"
TOKEN_URL = "https://api.x.com/2/oauth2/token"
SCOPES = "bookmark.read tweet.read users.read offline_access"

DEFAULT_DIR = os.path.expanduser("~/.config/openclaw/x-bookmarks")
DEFAULT_TOKEN_FILE = os.path.join(DEFAULT_DIR, "token.json")


def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(64)).rstrip(b"=").decode()
    digest = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def _catch_redirect(host: str, port: int, expected_state: str) -> str:
    """Block until the browser hits our redirect URI; return the auth code."""
    holder: dict[str, str] = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 (stdlib naming)
            qs = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(qs)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            if params.get("state", [""])[0] != expected_state:
                self.wfile.write(b"<h1>State mismatch - aborted.</h1>")
                return
            if "code" in params:
                holder["code"] = params["code"][0]
                self.wfile.write(b"<h1>Authorized. You can close this tab.</h1>")
            else:
                self.wfile.write(b"<h1>No code returned.</h1>")

        def log_message(self, *args):  # silence the default stderr spam
            pass

    server = http.server.HTTPServer((host, port), Handler)
    while "code" not in holder:
        server.handle_request()
    return holder["code"]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="One-time X OAuth PKCE authorization.")
    parser.add_argument("--redirect-uri", default="http://localhost:8723/callback")
    parser.add_argument("--token-file", default=os.environ.get("X_TOKEN_FILE", DEFAULT_TOKEN_FILE))
    args = parser.parse_args(argv)

    client_id = os.environ.get("X_CLIENT_ID")
    client_secret = os.environ.get("X_CLIENT_SECRET")
    if not client_id:
        print("error: X_CLIENT_ID must be set.")
        return 1

    parsed = urllib.parse.urlparse(args.redirect_uri)
    host, port = parsed.hostname or "localhost", parsed.port or 80

    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(16)
    auth_url = f"{AUTHORIZE_URL}?" + urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": args.redirect_uri,
            "scope": SCOPES,
            "state": state,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
        }
    )

    print("\nOpen this URL and approve access (attempting to launch a browser):\n")
    print(auth_url + "\n")
    webbrowser.open(auth_url)

    code = _catch_redirect(host, port, state)

    form = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": args.redirect_uri,
        "client_id": client_id,
        "code_verifier": verifier,
    }
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    if client_secret:
        basic = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
        headers["Authorization"] = f"Basic {basic}"

    req = urllib.request.Request(
        TOKEN_URL,
        method="POST",
        data=urllib.parse.urlencode(form).encode(),
        headers=headers,
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        tokens = json.loads(resp.read().decode())

    if "refresh_token" not in tokens:
        print(f"error: no refresh_token returned (is offline_access in scopes?): {tokens}")
        return 1

    os.makedirs(os.path.dirname(args.token_file) or ".", exist_ok=True)
    with open(args.token_file, "w", encoding="utf-8") as fh:
        json.dump({"refresh_token": tokens["refresh_token"]}, fh, indent=2)
    os.chmod(args.token_file, 0o600)

    print(f"\nSuccess. Refresh token written to {args.token_file}")
    print("The scheduled fetch will now run headless. Keep this file secret.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
