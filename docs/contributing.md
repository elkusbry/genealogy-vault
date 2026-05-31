# Contributing

Thanks for considering a contribution. The project is small enough that
this is a short doc.

## What contributions are welcome

- **Bug fixes** in scripts, the installer, or migrations.
- **New workflows** that generalize across families (e.g., handling
  newspaper archives, immigration databases, military records).
- **Schema improvements** — but breaking schema changes need migration
  scripts (see below).
- **Documentation** — especially screenshots and screencasts.
- **Translations** of the Riverstone demo into other languages for
  international users.
- **Issues** describing workflow gaps the Riverstones don't cover.

## What's out of scope

- Changes that bake in a particular family's structure or assumptions.
- Adding closed-source dependencies.
- Schema changes that don't ship with a migration script.

## Development setup

1. Fork the repo, clone your fork.
2. Run `./install.sh /tmp/test-vault` to smoke-test the installer.
3. Open the cloned repo in Obsidian to view the demo Riverstones.
4. Open it in Claude Code AND Codex CLI to verify both agents see the
   skill.

## The hard rule: test in BOTH agents

The skill is cross-agent. Every PR that touches `skill/`, `_scripts/`,
or the entry-point files (`CLAUDE.md`, `AGENTS.md`, `.claude/skills/`)
must be tested against:

- **Claude Code** — start a session in the cloned repo, run `/skill`,
  verify the skill is discovered. Then exercise the workflow you
  changed.
- **Codex CLI** — start a session in the cloned repo, ask "what
  genealogy workflows are available," verify it reads from AGENTS.md →
  `skill/SKILL.md`. Then exercise the workflow you changed.

Document the test in the PR body.

## Breaking schema changes

A breaking schema change is:

- Adding a required field to `templates/person.md`, `document.md`, or
  `media.md`.
- Renaming an existing field.
- Removing a field.
- Changing the format of an existing field (e.g., string → list).

Any of these require, in the same commit:

1. A migration script at `_scripts/migrations/YYYY-MM-DD-<slug>.py`
   following the template in `_scripts/migrations/README.md`.
2. A CHANGELOG entry under "Migration required."
3. A bump of `VERSION` (minor or major).

The migration script must be **idempotent** — re-running on an
already-migrated vault is a no-op.

## Coding conventions

- **Shell** — bash with `set -euo pipefail`. Pass through `shellcheck`
  cleanly.
- **Python** — 3.10+ for `match` and union types. Pass through `ruff`
  cleanly.
- **Markdown** — keep lines under 80 chars in workflow docs.

## What CI checks

(The v0.1 CI is minimal; expanding over time.)

- `shellcheck` on `install.sh` and `_scripts/scan-pipeline/process-scans.sh`.
- `ruff` on Python.
- Schema validation of `demo/sources/*.md` and `demo/people/*.md`
  against the templates.
- Smoke test: `install.sh` against a tempdir succeeds.

## Adding a new agent integration

If you want to add support for a new AI agent (Cursor, Cline, etc.):

1. Create a wrapper file in whatever location that agent expects (e.g.,
   `.cursorrules` for Cursor).
2. The wrapper should point at `skill/SKILL.md` — don't duplicate
   content.
3. Update the installer to copy the wrapper.
4. Add a `docs/using-with-<agent>.md`.
5. Test the full skill workflow in that agent.

## Releasing

1. Update `VERSION` (semver).
2. Update `CHANGELOG.md` under a new dated header.
3. Tag the release: `git tag -a v0.1.0 -m "Release v0.1.0" && git push --tags`.
4. Cut a GitHub release pointing at the tag.

## Code of conduct

Be kind. This is a hobby project for many of us.
