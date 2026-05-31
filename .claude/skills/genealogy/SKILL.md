---
name: genealogy
description: "Manage an Obsidian-based family history vault. Use this skill whenever the user wants to: add a person to the family tree, process a family document (eulogy, letter, certificate, photo, death certificate, tombstone), OCR a stack of scanned PDFs, update or correct family relationships, add life events or stories to a person's entry, file photos or documents into the vault, process the inbox, translate a non-English document, tag photos via the viewer, review open research questions, or anything involving the family-history project. Triggers on: genealogy terms (family tree, ancestor, descendant, branch, generation, DNA, haplogroup, tombstone, headstone, death certificate, census, immigration, marriage record, GEDCOM), document processing ('process this', 'file this', 'add this to the tree', 'process inbox', 'OCR the scans', 'process the scans', 'I dropped scans in'), relationship edits ('add children', 'parents are', 'married to', 'fix that relationship'), and the user's family surnames listed in skill/family-context.md. Also trigger when the user shares PDFs, photos, or documents about family members."
---

# Genealogy Vault

This skill is a **thin wrapper** around the canonical agent-agnostic skill at
`skill/SKILL.md` (at the vault root). Read that file for the full manual:
schemas, workflows, conventions, tooling reference.

The same skill is loaded by Codex CLI via `AGENTS.md` at the vault root, and
by Claude Code project mode via `CLAUDE.md`. Workflow content lives in one
place; this wrapper exists only for Claude Code's skill-discovery mechanism.

## How to use this skill in Claude Code

1. **First action:** read `skill/SKILL.md` (the canonical manual).
2. **Per-task:** read the relevant file under `skill/workflows/` or
   `skill/schemas/`. Don't try to hold the whole skill in context at once.
3. **Tooling:** invoke the scripts listed in `skill/SKILL.md` § Tooling
   reference. Never edit files under `skill/`, `_scripts/`, `_tools/`, or
   `templates/` during normal genealogy work — those are the toolkit. User
   data lives in `people/`, `sources/`, `media/`, `_inbox/`, and `MOC.md`.

## Family-specific context

If a `skill/family-context.md` file exists (copied from
`skill/family-context.md.template` on first use), read it for the user's
specific family — tree root(s), branches, surnames to trigger on, name
aliases, known discrepancies, and DNA research context.

If it doesn't exist yet, offer to scaffold it from the template before the
first substantive task.
