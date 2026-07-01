---
name: x-bookmarks
description: >-
  Fetch the user's new X (Twitter) bookmarks / saved tweets since the last run,
  for the weekly Friday digest or on demand. Use when asked about "X bookmarks",
  "Twitter bookmarks", "saved tweets", "what did I bookmark this week", "bookmark
  digest", or when building the Friday weekly digest. Returns structured bookmark
  data; the agent writes the summary.
---

# x-bookmarks

Pulls the **new** X bookmarks since the last run and hands them back as
structured data. This skill only **fetches and de-duplicates** — it does not
summarize. You (the agent) write the summary, matching the tone of the Daily
Notes digest.

## When to use

- Building the **Friday weekly digest** — add an `## X bookmarks this week`
  section from this skill's output.
- Any ad-hoc ask: "what did I bookmark on X this week / recently", "show my
  saved tweets", "catch me up on my bookmarks".

## How to run it

```bash
python3 skills/x-bookmarks/scripts/fetch_bookmarks.py --format json
```

- `--format json` (default) → `{"count": N, "bookmarks": [...]}`. Use this for
  the digest; each item has `text`, `author_handle`, `url`, `created_at`,
  `metrics`, `id`.
- `--format markdown` → a ready-to-read bullet list. Fine for a quick ad-hoc
  reply, but for the digest prefer JSON and write the prose yourself.
- `--seed` → record the current bookmarks as the baseline and emit **nothing**.
  Run this **once** the very first time so the first real digest isn't a dump of
  the entire bookmark history.

Exit code `0` = success (even with zero new bookmarks). Exit code `1` = a real
error printed to stderr — surface it, don't fabricate a summary.

## What "new this week" means (important)

The X API does **not** expose when *you* bookmarked a tweet — only when the
tweet was authored. So this skill can't filter by date. Instead it keeps a state
file of bookmark IDs seen last run and returns `current − seen`. Consequences:

- If the user bookmarks and then un-bookmarks between runs, it won't appear.
- Cadence is defined by **how often the script runs**, not a fixed 7-day window.
  Run it once per digest cycle (weekly) and "new since last Friday" holds.
- Don't claim a time window the data can't support. Say "new bookmarks since the
  last digest", not "bookmarked in the last 7 days".

## Writing the digest section

1. Run with `--format json`.
2. If `count` is 0 → `## X bookmarks this week` → "_Nothing new this week._"
3. Otherwise, one line per bookmark: author handle, a one-sentence gist, the
   link. Group loosely by theme if a pattern is obvious. Keep it low-friction,
   like the rest of the digest. Optionally note anything high-engagement.
4. Never invent bookmarks or links — only use what the JSON returned. Include the
   real `url` for each.

## Failure handling

- **`403 ... needs user-context OAuth`** → the refresh token is missing/revoked.
  Tell the user to re-run `scripts/authorize.py` once (see README). Do not retry
  blindly.
- **`429 rate limited`** → back off; report it and continue the rest of the
  digest without the bookmarks section.
- **No refresh token** → authorization was never completed. Point the user at
  the README setup steps.

## Setup & secrets

One-time setup (OAuth, env vars, secrets) lives in `README.md`. Secrets — the
refresh token — live outside this repo (default `~/.config/openclaw/x-bookmarks/`)
and must never be committed or pasted into chat. This skill folder is safe to
share; the user's tokens are not part of it.

## Files

- `scripts/fetch_bookmarks.py` — the fetch + state-diff (what you invoke).
- `scripts/authorize.py` — one-time interactive OAuth (the user runs this, not you).
- `README.md` — human setup guide.
