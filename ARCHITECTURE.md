# Architecture

For developers, forkers, and anyone curious about the pattern. The
genealogy domain is the demo — the architecture generalizes to any
opinionated Obsidian + AI workflow.

## Top-level layout

```
genealogy-vault/
├── README.md                    Human entry point
├── ARCHITECTURE.md              This file
├── CHANGELOG.md                 Versioned history + migration discipline
├── VERSION                      Semver, single line
├── LICENSE                      MIT
├── CLAUDE.md                    Claude Code project-mode entry point
├── AGENTS.md                    Codex CLI entry point
├── install.sh                   Idempotent installer + updater
│
├── skill/                       ⭐ CANONICAL agent-agnostic skill
│   ├── SKILL.md                 Manual + TOC
│   ├── family-context.md.template
│   ├── workflows/               One file per workflow group
│   └── schemas/                 One file per schema (the public API)
│
├── .claude/skills/genealogy/
│   └── SKILL.md                 Thin wrapper for Claude Code skill discovery
│
├── templates/                   person.md, document.md, media.md
│                                These ARE the public API. Breaking changes
│                                require migration scripts.
│
├── _scripts/
│   ├── scan-pipeline/           OCR + sidecar generation
│   ├── taggers/                 HTML tagger builders + JSON appliers
│   ├── migrations/              YYYY-MM-DD-<slug>.py per breaking change
│   └── migrate.py               Runner — reads stamp, runs pending migrations
│
├── _tools/                      Built HTML artifacts (gitignored)
├── _inbox/                      Drop zone (gitignored except .gitkeep + README)
│
├── docs/                        Tiered docs + screenshots
├── demo/                        Riverstone family fixture
└── .github/workflows/           CI
```

## Core design decisions

### One canonical skill, multiple agent wrappers

**Problem:** Claude Code and Codex CLI discover skills/instructions
differently. Maintaining two copies guarantees drift.

**Solution:** `skill/SKILL.md` is the single source of truth. Both
wrappers point to it:

- `.claude/skills/genealogy/SKILL.md` — Claude Code skill with
  YAML frontmatter (name, description); body says "See `/skill/SKILL.md`."
- `AGENTS.md` — Codex auto-loads this file; says the same thing.
- `CLAUDE.md` — Claude Code project mode; same pointer.

When the skill content evolves, you edit one file. Both agents pick it
up.

### Schemas as the public API

The three files in `templates/` are this project's API contract. Field
adds, renames, or removals are breaking changes — they require a
migration script and a version bump in the same commit. See
`_scripts/migrations/README.md` and the discipline statement in
`CHANGELOG.md`.

Why this matters: users who run `./install.sh` get the latest tooling
but keep their data. If a tooling update changes the schema without a
migration, their existing files become invalid silently. The migration
discipline prevents that.

### Tooling vs. data separation

Two trees coexist in every vault:

- **Tooling** (versioned, owned by this repo): `skill/`, `_scripts/`,
  `_tools/`, `templates/`, `CLAUDE.md`, `AGENTS.md`, the Claude Code
  skill wrapper.
- **Data** (user-owned, never touched by upgrades): `people/`,
  `sources/`, `media/`, `_inbox/`, `MOC.md`, `skill/family-context.md`
  (user-filled-in copy of the template).

`install.sh` overwrites tooling, ignores data. Re-running it is the
safe upgrade path.

### Demo lives in a subdirectory

`demo/` mirrors the root structure (`demo/people/`, `demo/sources/`,
`demo/media/`, `demo/MOC.md`, `demo/OPEN-QUESTIONS.md`) so the agent
can find the same shapes. But it's segregated so:

- Cloning gives you a working vault (the Riverstones).
- The installer skips `demo/` — power users don't get a fictional
  family dumped into their real vault.
- Hobbyists can delete `demo/` (or move it up to root) when ready.

### Idempotent installer = updater

`install.sh` is the only deployment artifact. Run it once to install,
re-run it to update. The behaviors:

- **Toolkit directories** (`skill/`, `_scripts/`, `.claude/skills/`):
  always overwrite.
- **Templates** (`templates/`): skip existing files unless `--force`.
  Users may have customized.
- **Agent entry points** (`CLAUDE.md`, `AGENTS.md`): if present,
  sideload to `*.from-genealogy-vault` and ask the user to merge.
- **Data directories** (`people/`, `sources/`, `media/`, `_inbox/`):
  create if missing, never touch contents.
- **Version stamp** (`.genealogy-vault-version`): always update.

### Migrations are idempotent shell

`_scripts/migrate.py` reads `<vault>/.genealogy-vault-version`,
compares to current `VERSION`, runs every migration in date range, and
re-stamps. Each migration script:

- Names itself `YYYY-MM-DD-<slug>.py`
- Exposes a `migrate(vault: Path) -> int` function
- Is idempotent — re-running on a migrated vault is a no-op

The runner doesn't track "migrations already run." If a user re-runs
the installer, every migration in range runs again. This is fine
because of the idempotency requirement.

## The OCR pipeline

```
_inbox/Scan_2026_05_03_001.pdf  (raw scan)
   │
   │  _scripts/scan-pipeline/process-scans.sh
   │  └── ocr_scan.py (ocrmypdf wrapper; in-place PDF/A replacement)
   ▼
_inbox/Scan_2026_05_03_001.pdf  (same name, now searchable)
_scripts/scan-pipeline/.ocr-cache/Scan_2026_05_03_001.txt  (raw OCR text)
   │
   │  Agent reads interpret-prompt.md and processes each .txt
   ▼
_inbox/1937-letter-from-heinrich-to-klara-vienna.md  (sidecar draft,
                                                       source: wikilink
                                                       back to PDF)
   │
   │  _scripts/scan-pipeline/move_inbox_to_sources.py
   ▼
sources/1937-letter-from-heinrich-to-klara-vienna.pdf   (PDF renamed)
sources/1937-letter-from-heinrich-to-klara-vienna.md    (sidecar moved)
   │
   │  Agent processes the source via skill/workflows/process-source.md
   ▼
people/Heinrich Riverstone (1885).md   (facts merged, citations added)
people/Klara Adler (1890).md           (facts merged, citations added)
```

The pipeline is **idempotent at every step**. Re-running
`process-scans.sh` skips PDFs already referenced by some `_inbox/*.md`'s
`source:` wikilink. Re-running `move_inbox_to_sources.py` is a no-op on
already-moved files.

## The tagger pattern

Both `document-tagger.html` and `photo-tagger.html` follow the same
pattern:

1. **Build script** (`_scripts/taggers/build_*_tagger.py`) scans
   `sources/`, `media/`, `people/` and produces a self-contained HTML
   file with everything baked in. No backend, loads via `file://`.
2. **Browser UI** lets the user edit metadata; edits persist in
   `localStorage`.
3. **Export Changes** downloads a JSON diff.
4. **Applier script** (`_scripts/taggers/apply_*_tagger_changes.py`)
   reads the JSON and surgically edits sidecars + person files.
   Idempotent.

This is fast (no LLM per-edit), works offline, and produces auditable
diffs.

## Cross-agent compatibility rules

For the skill to work in both Claude Code and Codex, two rules:

1. **Workflows reference scripts by shell command**, never tool names.
   ✅ `_scripts/scan-pipeline/process-scans.sh`
   ❌ "Use the Bash tool to run..."
2. **All metadata files (CLAUDE.md, AGENTS.md, skill frontmatter) point
   at the same canonical source.** Don't duplicate content; reference.

If you add a new agent (e.g., Cursor, Cline), follow the same pattern:
a thin wrapper file in whatever location that agent expects, pointing
at `skill/SKILL.md`.

## Distribution channels

| Channel | Status | Update mechanism |
|---|---|---|
| GitHub repo clone | v0.1 | `git pull` (template) or `./install.sh` (power user) |
| Claude Code plugin | v0.2 (planned) | `/plugin upgrade genealogy` |
| Codex CLI plugin | n/a | Codex has no plugin system; AGENTS.md is the API |

## Why genealogy?

The domain has every interesting AI-assisted-knowledge-base property
in one package:

- **Long-form structured data** (people files with deep YAML).
- **Heterogeneous source documents** (PDFs, photos, RTF, GEDCOM).
- **Bilingual/multilingual content** (German, Russian, Hebrew,
  Yiddish, French — wherever your family came from).
- **Bidirectional relationships** that must stay in sync.
- **Genuine uncertainty** that has to be tracked, not collapsed
  (`confidence: uncertain`, `[discrepancy]` todos).
- **OCR + handwriting recognition** that need to be in the loop.

If you build for genealogy correctly, the pattern transfers to almost
any other domain with these properties.
