# Genealogy Vault Skill

> **Agent-agnostic.** This skill is the canonical source of truth for both
> Claude Code and Codex CLI. Per-agent wrappers
> (`.claude/skills/genealogy/SKILL.md` and `AGENTS.md`) point here.

You manage an Obsidian-based genealogy knowledge base. The vault is the source
of truth — inspect it directly (`ls people/`, `ls sources/`, `ls _inbox/`).

## When to use this skill

Trigger whenever the user wants to do anything with their family history vault:

- **Process inbox.** Drop a scan or document into `_inbox/`, then say "process
  the inbox," "OCR these scans," "I dropped scans in," "process this PDF,"
  "file this document."
- **Add a person.** "Add my grandfather," "add a person to the tree,"
  "parents are X and Y," "married to Z."
- **Process a specific document type.** Eulogy, letter, death certificate,
  tombstone photo, census page, immigration record, marriage record,
  obituary, GEDCOM file.
- **Tag photos.** "Tag photos," "open the photo tagger," "who's in this photo."
- **Update relationships.** "Add children," "correct that relationship," "X is
  also Y's sibling."
- **Research.** "What's open," "review questions," "research status," "find
  the marriage record for X."
- **Translate.** "Translate this document," "add an English translation."

The user's specific family surnames are listed in `skill/family-context.md`
(generated from `skill/family-context.md.template` on first use) — those names
should also trigger this skill.

## Vault structure

```
<vault>/
├── MOC.md              # Map of Content — tree overview with wikilinks
├── people/             # One .md per person: "Firstname Lastname (YYYY).md"
├── sources/            # Original documents + sidecar .md with metadata
│   ├── *.pdf, *.jpg, *.rtf, *.docx, etc.
│   └── *.md            # Sidecar files (same base name as source)
├── media/              # Photos + sidecar .md
├── _inbox/             # Unprocessed files dropped by user
├── _scripts/           # OCR pipeline, tagger builders, migration runner
│   ├── scan-pipeline/
│   ├── taggers/
│   ├── migrations/
│   └── migrate.py
├── _tools/             # Prebuilt tagger HTMLs
├── templates/          # person.md, document.md, media.md
└── skill/              # This skill (canonical)
```

## Schemas (the public API)

Three schemas govern this vault. They are the project's public API — see
`schemas/` for the canonical definitions.

- **`skill/schemas/person.schema.md`** — every person file's YAML + body
  sections.
- **`skill/schemas/document.schema.md`** — every source/sidecar's frontmatter,
  the canonical `type:` list, companion-file keys (translation, notes,
  transcription, content), and the caption convention.
- **`skill/schemas/media.schema.md`** — photo/image sidecars.

Read the relevant schema before creating or editing a file.

## Workflows

Detailed step-by-step procedures live in `skill/workflows/`. Read the relevant
file when the user asks for that workflow.

| Workflow | File | Triggers |
|---|---|---|
| Process the inbox (OCR + sidecars + filing) | `workflows/process-inbox.md` | "process inbox," "OCR these scans," "I dropped scans in" |
| Add a person | `workflows/add-person.md` | "add a person," "add my grandmother," any new-person request |
| Process a source document (incl. death certs, tombstones, GEDCOM, RTF) | `workflows/process-source.md` | A new sidecar arrives; extract facts into person files |
| Translate a non-English document | `workflows/translate-document.md` | Foreign-language sidecar |
| Tag photos via the viewer | `workflows/tag-photos.md` | "Tag photos," "open photo tagger" |
| Research & maintenance (review questions, relationship corrections, fragment splits, untagged inventory, DNA) | `workflows/research-and-maintenance.md` | "What's open," "fix that relationship," "split this PDF," "what's untagged" |

## File-naming conventions

- **People:** `Firstname Lastname (YYYY).md` — birth year disambiguates duplicates. If
  birth year is unknown: `Firstname Lastname.md`. Some filenames retain old
  birth years for consistency even when corrected by later sources — always
  check YAML `birth.date` for the authoritative date.
- **Source sidecars:** match the original filename's stem
  (`1947-family-letter.pdf` ↔ `1947-family-letter.md`), or use a descriptive
  name when generating from scratch (`YYYY-<slug>.md`).
- **Companion files** (translation, notes, transcription, content):
  `<stem>-translation.md`, `<stem>-notes.md`, etc. See
  `schemas/document.schema.md`.

## Wikilink format

Always `[[Firstname Lastname (YYYY)]]` in both frontmatter and body. The
disambiguating year is required even if there's only one person with that
name today — future additions may collide.

## Citation pattern

Inline citations in body text use sidecar names (not raw filenames):

```markdown
- **1936** — Family moved to Vienna. ^[[[1937 Family Letter from Vienna]]]
```

In frontmatter `sources:` arrays:

```yaml
sources:
  - title: "1937 Family Letter from Vienna"
    type: correspondence
    link: "[[1937-family-letter-from-vienna]]"
```

## Bidirectional links are mandatory

If person A lists B as a child, B **must** list A as a parent. Same for
spouses ↔ spouses and siblings ↔ siblings. Edits that touch a relationship
must update both halves. See `workflows/relationship-correction.md`.

## Confidence levels

Every person file carries `confidence:` — one of:

- `proven` — multiple primary sources agree.
- `probable` — single reliable source.
- `possible` — oral history or indirect evidence.
- `uncertain` — unconfirmed.

When a fact conflicts across sources, do **not** silently pick one. Record both
values + their sources in `## Research Notes` and add a `[discrepancy]` entry
to `todo:`.

## Research-questions tagging

Person files use `todo:` for open research questions, with category prefixes:

- `[vital-records]` — missing birth, death, marriage dates/places
- `[identity]` — name confirmation, alias resolution, "is this the same person"
- `[relationship]` — uncertain parentage, adoption questions
- `[discrepancy]` — conflicting data across sources
- `[document-search]` — specific records to find
- `[dna]` — Y-DNA, haplogroup, genetic genealogy

Files with any non-empty `todo:` get the `research/has-questions` tag. Removed
when all questions are resolved. The "review questions" workflow regenerates
an aggregated MOC.

## Tags

Standard tag patterns: `branch/<name>`, `generation/N`,
`gender/male|female|other`, `status/living|deceased`, `surname/<name>`.

Domain-specific tags (e.g., `dna/ydna`, `research/<topic>`) are fine — invent
as needed and document the meaning in `skill/family-context.md`.

## Optional integrations

The schemas in `templates/` are designed to be compatible with the
**Charted Roots** Obsidian plugin (`cr_id`, `cr_type`, flat
`born`/`died`/`birth_place`/`death_place` duplicates of nested fields, and
parallel `*_id` arrays). If you don't use Charted Roots, those fields are
harmless — leave them blank.

See `templates/person.md` for the full schema with optional fields called out.

## Rules

- **Never overwrite enriched content.** Read files first, then surgically edit.
- **Bidirectional links are mandatory.**
- **Every fact needs a source citation.**
- **Data discrepancies:** record both values, do not silently pick one.
- **Tooling vs data separation:** never modify files under `skill/`,
  `_scripts/`, `_tools/`, `templates/` during normal genealogy work — those
  are the toolkit. User data lives in `people/`, `sources/`, `media/`,
  `_inbox/`, and `MOC.md`.

## Tooling reference

Scripts live under `_scripts/`. All are invokable via shell — no agent-specific
tool names are referenced in workflows.

| Script | Purpose |
|---|---|
| `_scripts/scan-pipeline/process-scans.sh` | OCR every PDF in `_inbox/` |
| `_scripts/scan-pipeline/generate_inbox_drafts.py` | Generate sidecars from OCR text |
| `_scripts/scan-pipeline/move_inbox_to_sources.py` | File inboxed pairs into `sources/` |
| `_scripts/taggers/build_document_tagger.py` | (Re)build `_tools/document-tagger.html` |
| `_scripts/taggers/build_photo_tagger.py` | (Re)build `_tools/photo-tagger.html` |
| `_scripts/taggers/apply_document_tagger_changes.py` | Apply exported tagger JSON edits |
| `_scripts/taggers/apply_photo_tagger_changes.py` | Apply exported photo-tagger JSON edits |
| `_scripts/migrate.py` | Run schema migrations after `install.sh` updates |

See `_scripts/scan-pipeline/README.md` for pipeline details and
`_scripts/migrations/README.md` for the migration discipline.
