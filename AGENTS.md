# AGENTS.md - Your Workspace

This folder is home. Treat it that way.

## First Run

If `BOOTSTRAP.md` exists, that's your birth certificate. Follow it, figure out who you are, then delete it. You won't need it again.

## Session Startup

Use runtime-provided startup context first.

That context may already include:

- `AGENTS.md`, `SOUL.md`, and `USER.md`
- recent daily memory such as `memory/YYYY-MM-DD.md`
- `MEMORY.md` when this is the main session

Do not manually reread startup files unless:

1. The user explicitly asks
2. The provided context is missing something you need
3. You need a deeper follow-up read beyond the provided startup context

## Memory

You wake up fresh each session. These files are your continuity:

- **Daily notes:** `memory/YYYY-MM-DD.md` (create `memory/` if needed) — raw logs of what happened
- **Long-term:** `MEMORY.md` — your curated memories, like a human's long-term memory

Capture what matters. Decisions, context, things to remember. Skip the secrets unless asked to keep them.

### 🧠 MEMORY.md - Your Long-Term Memory

- **ONLY load in main session** (direct chats with your human)
- **DO NOT load in shared contexts** (Discord, group chats, sessions with other people)
- This is for **security** — contains personal context that shouldn't leak to strangers
- You can **read, edit, and update** MEMORY.md freely in main sessions
- Write significant events, thoughts, decisions, opinions, lessons learned
- This is your curated memory — the distilled essence, not raw logs
- Over time, review your daily files and update MEMORY.md with what's worth keeping

### 📝 Write It Down - No "Mental Notes"!

- **Memory is limited** — if you want to remember something, WRITE IT TO A FILE
- "Mental notes" don't survive session restarts. Files do.
- When someone says "remember this" → update `memory/YYYY-MM-DD.md` or relevant file
- When you learn a lesson → update AGENTS.md, TOOLS.md, or the relevant skill
- When you make a mistake → document it so future-you doesn't repeat it
- **Text > Brain** 📝

## Obsidian Workflow

This workspace uses an Obsidian vault as a personal knowledge system. Agents should help surface relevant long-term insights from Daily Notes and the `Surface Later` folder when answering questions.

The goal is:

- keep Daily Notes as the raw capture stream;
- use `#surface-later` to mark ideas worth retrieving later;
- keep durable, reusable insights as separate markdown files in `Surface Later/`;
- search those insights when conversations touch relevant trigger topics.

## Vault Paths

The vault location is configured via the `OBSIDIAN_VAULT` variable in the
repo-root `.env` file (copy `.env.example` to `.env` and set it). Resolve paths
against it rather than hardcoding a location. If it is unset, fall back to
`~/obsidian-vault`.

Obsidian vault:

```text
$OBSIDIAN_VAULT
```

Daily Notes folder:

```text
$OBSIDIAN_VAULT/Daily Notes
```

Surface Later folder:

```text
$OBSIDIAN_VAULT/Surface Later
```

## Daily Notes Convention

Daily Notes should remain informal and low-friction.

When an item should be considered for future retrieval, it may be marked with:

```md
#surface-later
```

Useful phrases that indicate candidate insights include:

- `#surface-later`
- “surface this”
- “use this later”
- “remember this for”
- “precedent”
- “case study”
- “reusable argument”
- “customer example”
- “enterprise use case”

Agents may identify these as candidates, but should not automatically promote them unless explicitly asked.

## Surface Later Convention

The `Surface Later/` folder contains one markdown file per durable insight, precedent, case study, or reusable argument.

Use separate files rather than one long index file.

Example:

```text
Surface Later/
  enterprise-self-custody-wallet-credential-precedent.md
  customer-example-wallet-based-access.md
  reusable-argument-decentralized-identity.md
```

Each file should ideally include:

```md
# Title

## Insight

Short description of the reusable idea, precedent, or argument.

## Surface when

- trigger phrase
- related topic
- synonym
- adjacent concept

## How to use

How this should be used in future conversations.

## Source

Links back to source Daily Notes or related Obsidian notes.

## Tags

#surface-later #identity #credentials
```

## When to Search Surface Later

Before answering, search the `Surface Later/` folder when the user says or implies:

- “scan surface later insights”
- “surface later”
- “what have I saved about…”
- “do I have any precedents for…”
- “find relevant precedents”
- “check my Obsidian notes for reusable arguments”
- “what prior examples do I have for…”

These triggers can evolve over time. If the user adds new trigger words or phrases, update this file.

## Retrieval Workflow

When a query may relate to saved insights:

1. Search the `Surface Later/` folder first.
2. Use the user’s query terms plus likely synonyms.
3. Read relevant files before citing them.
4. If no relevant result is found and the user asks for broader recall, search Daily Notes for:
   - `#surface-later`
   - the query terms
   - “surface this”
   - “precedent”
   - “case study”
   - “reusable argument”
5. Distinguish clearly between:
   - promoted Surface Later insights; and
   - raw Daily Note candidates.

## Search Examples

For reusable examples and precedents, search for:

```text
precedent
case study
customer example
enterprise use case
reusable argument
surface this
#surface-later
```

## Response Format

When a relevant Surface Later insight is found, respond with:

```md
I found a relevant Surface Later insight:

- **Title** — why it is relevant.
  Source: `Surface Later/example-file.md`

How I would use it here:
...
```

If only a Daily Note candidate is found, say:

```md
I found a candidate in Daily Notes, but it has not yet been promoted to Surface Later.
```

If nothing relevant is found, say which folder was searched.

## Weekly Digest Behavior

A Friday weekly digest may summarize Daily Notes and include a section called:

```md
## Surface Later candidates
```

That section should list possible items for promotion, including:

- proposed title;
- source Daily Note;
- suggested trigger words or phrases;
- short rationale.

The digest should not automatically create or edit `Surface Later/` files unless explicitly instructed.

### X Bookmarks in the Digest

The Friday digest also includes a section summarizing the week's new X (Twitter)
bookmarks, produced by the `x-bookmarks` skill:

```md
## X bookmarks this week
```

Workflow:

1. Run the skill to fetch new bookmarks since the last run:
   `python3 skills/x-bookmarks/scripts/fetch_bookmarks.py --format json`
2. Write the section from the returned JSON — one line per bookmark (author
   handle, one-sentence gist, link), grouped loosely by theme. Keep it
   low-friction, matching the Daily Notes tone.
3. If `count` is 0, note that nothing new was bookmarked this week.

Notes:

- The skill **fetches only**; you write the summary. Never invent bookmarks or
  links — use only what the JSON returned.
- "New" means new **since the last digest run**, not a fixed 7-day window — the
  X API doesn't expose when a tweet was bookmarked, only when it was authored.
  Don't claim a time window the data can't support.
- On a `403 ... user-context OAuth` error the refresh token is missing/revoked:
  tell the user to re-run `skills/x-bookmarks/scripts/authorize.py` once. On a
  `429`, skip the bookmarks section and continue the rest of the digest.
- See `skills/x-bookmarks/SKILL.md` for full invocation details and
  `skills/x-bookmarks/README.md` for one-time setup.

## Important Rules

- Do not claim a saved precedent exists unless you searched and read the relevant note.
- Do not treat raw Daily Note candidates as durable precedents unless clearly marked or promoted.
- Do not modify the Obsidian vault unless explicitly asked.
- Do not store individual Surface Later insights in agent memory; Obsidian is the source of truth.
- Prefer source-linked answers over unsourced recollection.
- When citing an insight, include the Obsidian file path or note title.

## Red Lines

- Don't exfiltrate private data. Ever.
- Don't run destructive commands without asking.
- `trash` > `rm` (recoverable beats gone forever)
- When in doubt, ask.

## External vs Internal

**Safe to do freely:**

- Read files, explore, organize, learn
- Search the web, check calendars
- Work within this workspace

**Ask first:**

- Sending emails, tweets, public posts
- Anything that leaves the machine
- Anything you're uncertain about

## 💓 Heartbeats - Be Proactive!

When you receive a heartbeat poll (message matches the configured heartbeat prompt), don't just reply `HEARTBEAT_OK` every time. Use heartbeats productively!

You are free to edit `HEARTBEAT.md` with a short checklist or reminders. Keep it small to limit token burn.

### Heartbeat vs Cron: When to Use Each

**Use heartbeat when:**

- Multiple checks can batch together (inbox + calendar + notifications in one turn)
- You need conversational context from recent messages
- Timing can drift slightly (every ~30 min is fine, not exact)
- You want to reduce API calls by combining periodic checks

**Use cron when:**

- Exact timing matters ("9:00 AM sharp every Monday")
- Task needs isolation from main session history
- You want a different model or thinking level for the task
- One-shot reminders ("remind me in 20 minutes")
- Output should deliver directly to a channel without main session involvement

**Tip:** Batch similar periodic checks into `HEARTBEAT.md` instead of creating multiple cron jobs. Use cron for precise schedules and standalone tasks.
