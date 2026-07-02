# x-bookmarks — weekly X bookmarks for the Friday digest

A skill for the OpenClaw agent that fetches your **new X (Twitter) bookmarks**
since the last run and returns them as structured data, so the agent can fold an
`## X bookmarks this week` section into the Friday weekly digest. It can also be
called ad hoc ("what did I bookmark recently?").

The skill **fetches**; the agent **summarizes**. That split keeps the brittle,
auth-heavy part deterministic and lets the summary match your Daily Notes tone.

---

## Why there's a one-time OAuth step (not just an API key)

The bookmarks endpoint (`GET /2/users/:id/bookmarks`) is **user-context only**.
It requires **OAuth 2.0 Authorization Code with PKCE** and the `bookmark.read`
scope. An app API key / bearer token — even on a paid tier — returns `403`. Your
paid tier covers *access*; the *auth flow* still has to be user-context OAuth.

So there's exactly one manual step: authorize once in a browser to mint a
**refresh token**. After that the scheduled task runs headless. X rotates the
refresh token on every refresh, and the fetch script persists the new one each
run, so you won't need to re-authorize unless you revoke access or change scopes.

---

## Setup (once)

### 1. Configure your X app
In the X developer portal, on your app:
- Enable **OAuth 2.0**, type **Native App** (public client) or **Web App**
  (confidential client — then you'll also have a client secret).
- Set a **redirect URI** of `http://localhost:8723/callback` (must match exactly).
- Note the **Client ID** (and **Client Secret** for a confidential app).

### 2. Set environment variables
Config is read from the environment. The easiest way to set it is the repo-root
`.env` file — copy the template and fill in your values:

```bash
cp .env.example .env   # from the repo root, then edit .env
```

Both scripts load `.env` automatically at startup (via `scripts/_env.py`, stdlib
only — no dependency). Anything already exported in your shell or provided by a
gateway secret store **takes precedence** over `.env`, so you can keep real
secrets in a secret store and use `.env` only for local/dev. `.env` is
git-ignored; never commit it. You can point the loader at a different file with
`DOTENV_PATH=/path/to/file`.

| Variable | Required | Purpose |
|---|---|---|
| `X_CLIENT_ID` | yes | OAuth 2.0 client ID |
| `X_CLIENT_SECRET` | only for confidential apps | client secret |
| `X_USER_ID` | optional | numeric user id; auto-resolved via `/users/me` if unset |
| `X_TOKEN_FILE` | optional | refresh-token path (default `~/.config/openclaw/x-bookmarks/token.json`) |
| `X_BOOKMARKS_STATE` | optional | state-file path (default `~/.config/openclaw/x-bookmarks/state.json`) |
| `X_REFRESH_TOKEN` | optional | refresh token; normally lives in `X_TOKEN_FILE`, not here |

### 3. Authorize once (interactive, needs a browser)
With `X_CLIENT_ID` set in `.env` (or the environment):
```bash
python3 scripts/authorize.py
```
Or pass it inline for a one-off: `X_CLIENT_ID=your_client_id python3 scripts/authorize.py`
Approve access in the browser. The refresh token is written to `X_TOKEN_FILE`
with `0600` perms. Keep that file secret.

### 4. Seed the baseline (so the first digest isn't a full-history dump)
```bash
python3 scripts/fetch_bookmarks.py --seed
```
This records what you've bookmarked *so far* and emits nothing. From the next run
on, you only get what's new.

---

## Usage

```bash
# Structured output for the digest
python3 scripts/fetch_bookmarks.py --format json

# Human-readable list
python3 scripts/fetch_bookmarks.py --format markdown
```

`--format json` returns:
```json
{
  "count": 2,
  "bookmarks": [
    {
      "id": "1790...",
      "text": "…",
      "created_at": "2026-06-30T12:00:00.000Z",
      "author_handle": "someone",
      "author_name": "Some One",
      "metrics": {"like_count": 42, "retweet_count": 5},
      "url": "https://x.com/someone/status/1790..."
    }
  ]
}
```

Exit `0` = success (including zero new). Exit `1` = error on stderr.

---

## "New since last run", not "last 7 days"

The API never exposes *when you bookmarked* a tweet — only when it was authored.
So this skill can't filter by a date window. It diffs the current bookmark set
against the IDs it saw last run: **new = current − seen**. Run it once per digest
cycle and "new since last Friday" holds. Un-bookmarking between runs hides an
item; that's expected.

---

## Wiring into the Friday digest

The digest already summarizes Daily Notes (see `AGENTS.md` → *Weekly Digest
Behavior*). Add a step: run `fetch_bookmarks.py --format json`, then write an
`## X bookmarks this week` section from the result. Whether that runs via the
gateway agent config or a `0 16 * * 5` UTC cron depends on how the digest is
currently scheduled — one job, one delivery, no second cron.

---

## Security

- The refresh token lives outside this repo and is git-ignored even if pathed
  inside it. Never commit it or paste it into chat.
- Bookmarks are private data — the summary is delivered only into your own vault
  / digest, never to an external service.
- Revoke anytime in the X app settings; then re-run `authorize.py` to restore.

---

## Files

| File | Who runs it | What it does |
|---|---|---|
| `SKILL.md` | the agent (auto) | how the agent invokes and interprets this skill |
| `scripts/fetch_bookmarks.py` | agent / cron | refresh → fetch → diff → emit JSON/Markdown |
| `scripts/authorize.py` | you, once | interactive OAuth to mint the refresh token |
| `scripts/_env.py` | imported by both | loads the repo-root `.env` into the environment |

---

## Activating the skill for the agent

Skills load from `~/.claude/skills` (symlinked to `~/.agents/skills`). To make
this repo-tracked skill available to the running agent, symlink it in:

```bash
ln -s "$(pwd)/skills/x-bookmarks" ~/.claude/skills/x-bookmarks
```

It stays version-controlled here; the symlink just exposes it to the runtime.
