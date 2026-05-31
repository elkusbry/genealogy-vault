# CLAUDE.md

This file is loaded automatically by Claude Code when working in this vault.

## What this vault is

An Obsidian-based genealogy knowledge base. The full agent-agnostic skill —
schemas, workflows, conventions, tooling reference — lives in
**`skill/SKILL.md`**. Read it first.

## When to trigger genealogy work

Any of these signal that the user wants genealogy work done — load
`skill/SKILL.md` and follow the relevant workflow:

- Document processing: "process the inbox," "OCR these scans," "file this
  PDF," "process this letter," "I dropped scans in"
- Person edits: "add a person," "add my grandmother," "parents are X and Y,"
  "married to Z," "fix that relationship"
- Photo work: "tag photos," "open the photo tagger," "who's in this photo"
- Research: "what's open," "review questions," "research status"
- Translation: "translate this document," "add an English translation"
- The user shares a PDF, photo, scan, or GEDCOM file
- The user mentions a surname listed in `skill/family-context.md` (if
  present)

## How to work in this vault

1. **First action on any genealogy task:** read `skill/SKILL.md`.
2. **Per-task:** read the relevant `skill/workflows/<file>.md` or
   `skill/schemas/<file>.md`. Don't try to hold the whole skill in context.
3. **Tooling:** invoke scripts under `_scripts/` from the shell. The skill
   lists them.
4. **Tooling vs data separation:** never modify files under `skill/`,
   `_scripts/`, `_tools/`, or `templates/` during normal genealogy work —
   those are the toolkit. User data lives in `people/`, `sources/`,
   `media/`, `_inbox/`, and `MOC.md`.

## Claude Code skill discovery

The skill is also registered at `.claude/skills/genealogy/SKILL.md` (a thin
wrapper that points back at `skill/SKILL.md`). Use it via the skill
mechanism, or follow this file's pointer directly.

## Demo data

The `demo/` directory contains a fictional family (the **Riverstones**) so
you can see the vault working end-to-end before adding your own data. To
start with your own family, delete `demo/` (or move `demo/*` to the root
and rename people as desired). See `demo/README.md`.
