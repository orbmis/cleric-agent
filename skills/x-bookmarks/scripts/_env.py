"""Minimal, dependency-free .env loader (stdlib only).

Reads `KEY=VALUE` lines from a `.env` file and injects them into `os.environ`
*without* overriding variables already present in the real environment — so a
value exported in your shell or provided by a gateway secret store always wins
over the file. Empty values are ignored, so blank placeholders copied from
`.env.example` never clobber a script's built-in default.

Lookup order for the file:
  1. `$DOTENV_PATH` if set;
  2. otherwise the nearest `.env` found walking up from this file toward the
     filesystem root (this finds the repo-root `.env` even though the scripts
     live under `skills/x-bookmarks/scripts/`).

Kept intentionally tiny: no interpolation, no multiline values. Just enough to
load the handful of config vars this skill needs.
"""

from __future__ import annotations

import os


def _find_dotenv() -> str | None:
    explicit = os.environ.get("DOTENV_PATH")
    if explicit:
        return explicit if os.path.isfile(explicit) else None
    here = os.path.dirname(os.path.abspath(__file__))
    while True:
        candidate = os.path.join(here, ".env")
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(here)
        if parent == here:  # reached filesystem root
            return None
        here = parent


def load_dotenv(path: str | None = None) -> str | None:
    """Load `.env` into os.environ (non-overriding). Returns the path used, if any."""
    path = path or _find_dotenv()
    if not path or not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            key, sep, value = line.partition("=")
            if not sep:
                continue
            key = key.strip()
            value = value.strip()
            # Strip one layer of matching surrounding quotes.
            if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
                value = value[1:-1]
            if key and value:  # skip blanks so placeholders don't override defaults
                os.environ.setdefault(key, value)  # real env wins
    return path
