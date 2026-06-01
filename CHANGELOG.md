# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Schema as Public API

The `templates/` schemas are this project's public API. Any field add, remove,
or rename in `templates/person.md`, `templates/document.md`, or
`templates/media.md` is a breaking change and **MUST** ship in the same commit as:

1. A migration script in `_scripts/migrations/YYYY-MM-DD-<slug>.py`
2. A CHANGELOG entry under "Migration required" noting the migration
3. A bump of `VERSION`

## [Unreleased]

### Changed

- **Hero GIF rebuilt with REAL tagger screenshots.** Headless Chrome
  drives the actual `demo/_tools/document-tagger.html` and
  `photo-tagger.html` shipped with the repo (Vienna letter selected,
  Heinrich's tombstone selected) and the captured screenshots are
  spliced into the GIF as frames 9–10. The four PIL-drawn frames that
  pretended to be Obsidian graph view / person preview / synthetic
  taggers were dropped — they didn't match what the user actually
  encounters and were misleading. GIF is now 10 frames / ~23 s / 390 KB.
- **README also shows the real tagger screenshots inline** in a two-up
  table beneath the hero so they're legible at full resolution without
  watching the animation. PNGs saved to `docs/screenshots/`.

## [0.4.0] - 2026-05-31

### Added

- **Animated hero GIF** (`docs/screenshots/hero.gif`, 163 KB, 8 frames,
  ~15s loop) replacing the static composite at the top of the README.
  Shows the full workflow: PDF drops → user types "process the inbox" →
  OCR runs → German letter text appears → entities highlighted → YAML
  person-file diff → PDF + sidecar filed into `sources/` → summary
  with one open research question logged. PIL-generated. Static
  composite preserved at `docs/screenshots/hero.png` as the high-res
  fallback.
- **Maintainer workflow doc** (`docs/maintainer-workflow.md`) explaining
  the relationship between a personal vault and this toolkit: which
  files the toolkit owns, the supported dev loop (edit upstream → test
  → re-install), how to handle drift, and the release flow.
- **Drift-check script** (`_scripts/drift_check.sh`) that diffs the
  toolkit's owned files against a target vault's copies and reports
  drifted/missing/only-in-vault counts. Filters out noise
  (`.DS_Store`, logs, OCR cache, `archive/`). Useful before re-running
  `install.sh` against a vault that may have local script edits.

## [0.3.0] - 2026-05-31

### Added

- **Hero composite image** (`docs/screenshots/hero.png`, 94 KB) at the
  top of the README — shows the workflow visually: scanned German letter
  → "process inbox" agent badge → structured YAML person file with
  extracted facts, confidence, and discrepancy todos. Generated with PIL;
  no external dependencies on real screenshots yet.
- **Skill validator** (`_scripts/validate_skill.py`) that checks:
  - `skill/SKILL.md` parses cleanly
  - every workflow/schema reference resolves to an existing file
  - both skill wrappers exist with valid YAML frontmatter
  - `plugin.json` parses and its version matches `VERSION`
  - no workflow file references agent-specific tool names ("the Bash
    tool," etc.)
- **CI jobs** for the validator and a tagger-build smoke test against
  the Riverstone fixture (catches regressions in the build scripts and
  ensures the prebuilt taggers stay reproducible).

### Fixed

- Broken reference in `skill/SKILL.md` to a non-existent
  `workflows/relationship-correction.md` (the procedure consolidated
  into `research-and-maintenance.md` in v0.1 but the cross-reference
  wasn't updated). Caught by the new validator.
- `install.sh` SC2295 shellcheck warning (`${src_file#$src/}` →
  `${src_file#"$src"/}`).

## [0.2.0] - 2026-05-31

### Added

- Claude Code plugin scaffolding: `.claude-plugin/plugin.json` and
  `.claude-plugin/marketplace.json` make this repo installable as a
  self-published plugin. Users can install via:
  ```
  /plugin marketplace add elkusbry/genealogy-vault
  /plugin install genealogy-vault@genealogy-vault
  ```
  The plugin packages the skill (`skills/genealogy/SKILL.md`) but expects
  the toolkit (scripts, templates, tools) to be present in the vault via
  `install.sh`.
- Three CC0 placeholder JPEGs in the Riverstone fixture so the photo
  tagger renders out of the box:
  `demo/sources/heinrich-riverstone-tombstone.jpg`,
  `demo/sources/1912-klara-passport-photo.jpg`,
  `demo/media/undated-riverstone-family-portrait.jpg`.
- Prebuilt `_tools/document-tagger.html` and `_tools/photo-tagger.html`
  against the Riverstone fixture (94 KB and 35 KB respectively).
  Cloning the repo now gives a working tagger with no build step.

### Changed

- `demo/README.md` updated to reflect that placeholder images ship.

## [0.1.0] - 2026-05-31

### Added

- Initial public release.
- Canonical agent-agnostic skill at `skill/SKILL.md` with workflows for
  inbox processing, source extraction, scan OCR, photo tagging, and
  research-question tracking.
- Thin per-agent wrappers: `.claude/skills/genealogy/SKILL.md` for Claude
  Code; `AGENTS.md` for Codex CLI; `CLAUDE.md` for Claude Code project mode.
- Schemas + templates for `person`, `document`, and `media` files.
- Scan pipeline (`_scripts/scan-pipeline/`): Tesseract-based OCR with
  in-place PDF replacement, sidecar generation, and inbox→sources filing.
- Document tagger and photo tagger (`_tools/*.html`) with builders in
  `_scripts/taggers/`.
- Idempotent `install.sh` that doubles as the updater for power users.
- Migration runner (`_scripts/migrate.py`) and migrations directory.
- The Riverstone family fixture in `demo/` covering every demoable skill
  scenario.
- Documentation for hobbyists, power users, Claude Code users, Codex users,
  and contributors.
