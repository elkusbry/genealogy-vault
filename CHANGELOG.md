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
