## Purpose

This workspace uses an Obsidian vault as a personal knowledge system. Agents should help surface relevant long-term insights from Daily Notes and the `Surface Later` folder when answering questions.

The goal is:

- keep Daily Notes as the raw capture stream;
- use `#surface-later` to mark ideas worth retrieving later;
- keep durable, reusable insights as separate markdown files in `Surface Later/`;
- search those insights when conversations touch relevant trigger topics.

## Vault Paths

The vault location is configured via the `OBSIDIAN_VAULT` variable in the
repo-root `.env` file (copy `.env.example` to `.env` and set it). Resolve the
paths below against it rather than hardcoding a location. If it is unset, fall
back to `~/obsidian-vault`.

See `.env.example` for all configuration variables (vault path and the
`x-bookmarks` skill's X credentials).

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

## Important Rules

- Do not claim a saved precedent exists unless you searched and read the relevant note.
- Do not treat raw Daily Note candidates as durable precedents unless clearly marked or promoted.
- Do not modify the Obsidian vault unless explicitly asked.
- Do not store individual Surface Later insights in agent memory; Obsidian is the source of truth.
- Prefer source-linked answers over unsourced recollection.
- When citing an insight, include the Obsidian file path or note title.
