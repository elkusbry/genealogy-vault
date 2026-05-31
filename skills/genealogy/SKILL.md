---
name: genealogy
description: "Manage an Obsidian-based family history vault. Use this skill whenever the user wants to: add a person to the family tree, process a family document (eulogy, letter, certificate, photo, death certificate, tombstone), OCR a stack of scanned PDFs, update or correct family relationships, add life events or stories to a person's entry, file photos or documents into the vault, process the inbox, translate a non-English document, tag photos via the viewer, review open research questions, or anything involving the family-history project. Triggers on: genealogy terms (family tree, ancestor, descendant, branch, generation, DNA, haplogroup, tombstone, headstone, death certificate, census, immigration, marriage record, GEDCOM), document processing ('process this', 'file this', 'add this to the tree', 'process inbox', 'OCR the scans', 'process the scans', 'I dropped scans in'), relationship edits ('add children', 'parents are', 'married to', 'fix that relationship'), and the user's family surnames listed in skill/family-context.md. Also trigger when the user shares PDFs, photos, or documents about family members."
---

# Genealogy Vault (Claude Code plugin)

This skill is a **thin wrapper** around the canonical agent-agnostic skill.
The actual workflow content lives in the **genealogy-vault toolkit**
(https://github.com/elkusbry/genealogy-vault) which the user must clone
and install into their Obsidian vault:

```sh
git clone https://github.com/elkusbry/genealogy-vault.git ~/code/genealogy-vault
~/code/genealogy-vault/install.sh /path/to/their/obsidian/vault
```

After installation, the user's vault contains:

- `skill/SKILL.md` — the canonical manual (read first)
- `skill/workflows/*.md` — one file per workflow group
- `skill/schemas/*.md` — schema definitions (the public API)
- `skill/family-context.md` — family-specific context (user-filled)
- `_scripts/scan-pipeline/`, `_scripts/taggers/`, `_scripts/migrate.py`
- `_tools/document-tagger.html`, `_tools/photo-tagger.html`
- `templates/person.md`, `document.md`, `media.md`

## How to use this skill

1. **First action on any genealogy task:** read `skill/SKILL.md` at the
   vault root. If it doesn't exist, the user hasn't run the installer —
   point them at the install instructions above.
2. **Per-task:** read the relevant `skill/workflows/<file>.md` or
   `skill/schemas/<file>.md`. Don't try to hold the whole skill in
   context at once.
3. **Tooling:** invoke scripts under `_scripts/` from the shell.
4. **Tooling vs data separation:** never modify files under `skill/`,
   `_scripts/`, `_tools/`, or `templates/` during normal genealogy work
   — those are the toolkit. User data lives in `people/`, `sources/`,
   `media/`, `_inbox/`, and `MOC.md`.

## Family-specific context

If `skill/family-context.md` exists, read it before any substantive task.
If only `skill/family-context.md.template` exists, offer to scaffold the
real file from the template.

## Why this skill is a thin wrapper

The same skill content drives Claude Code (this plugin), Codex CLI (via
`AGENTS.md` at the vault root), and Claude Code project mode (via
`CLAUDE.md`). Each agent loads the skill via its native discovery
mechanism, then reads the canonical workflows from `skill/SKILL.md`.
One source of truth, multiple agent integrations.
