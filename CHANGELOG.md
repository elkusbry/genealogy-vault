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
