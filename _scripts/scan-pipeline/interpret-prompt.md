# Interpret OCR'd genealogy text → KB-ready markdown

You are processing OCR text from a scanned genealogy document (typewriter or
printed) for an Obsidian-based genealogy vault. Conventions are defined in
the canonical skill at `skill/SKILL.md` (relative to the vault root), with
family-specific knowledge in `skill/family-context.md` if present. **Read
both before starting.**

## Inputs

For each scanned PDF in `_inbox/<original-stem>.pdf`:
- The searchable PDF itself: `_inbox/<original-stem>.pdf` (already OCR'd in
  place by `ocr_scan.py` — it has a text layer now). `<original-stem>` is
  typically a scanner-generated name like `2026_05_03_13_27_59`.
- Raw OCR text: `_scripts/scan-pipeline/.ocr-cache/<original-stem>.txt`
  (cleaner to parse than the PDF's embedded text layer; use this as the
  primary input).

## Goal

For each `.txt` file in `.ocr-cache/`, produce ONE markdown file at
`_inbox/<descriptive-slug>.md` (NOT sibling-named — see step 5). The
markdown's frontmatter `source:` wikilink points at the original PDF stem
so the next pipeline step (`move_inbox_to_sources.py`) can match them up,
move both into `sources/`, and rename the PDF to match the descriptive
slug.

## Steps

### 1. Read and clean the OCR

Common typewriter / scan OCR errors to fix silently:

| OCR'd          | Likely real           | When                                             |
| -------------- | --------------------- | ------------------------------------------------ |
| `l`, `I`       | `1`                   | Inside a number or date                          |
| `O`, `o`       | `0`                   | Inside a number or date                          |
| `S`            | `5`, `8`              | Inside a number                                  |
| `B`            | `8`                   | Inside a number                                  |
| `rn`           | `m`                   | Inside a word                                    |
| `cl`           | `d`                   | Inside a word                                    |
| line-end `-`   | join words            | Hyphen at line break in flowing prose            |
| double newline | paragraph break       | Preserve                                         |
| single newline | space                 | Inside a paragraph (typewriter line wrap)        |
| `~`, `^`, `*`  | likely punctuation    | Often a period, comma, or apostrophe smudge      |

Reflow paragraphs from typewriter line wraps, but preserve list-like
structures (addresses, name lists, family group sheets) as separate lines.

If a passage is unreadable, mark it `[illegible]` rather than guessing. If you
correct an obvious OCR error inline, do not annotate it. If a reading is
genuinely uncertain (e.g. a name or date you had to guess), put it in
`?text?` and add an entry to `todo:` in the frontmatter.

### 2. Identify the document

Pick the best `type:` value from the canonical list — do NOT invent new
values or use aliases like `letter`, `death-certificate`, or `passenger-list`:

- Vital: `birth-record`, `death-record`, `marriage-record`, `burial-record`, `census`
- Government / institutional: `immigration-record`, `naturalization-record`,
  `military-record`, `legal-record`, `financial-record`, `city-directory`
- News & writing: `correspondence`, `obituary`, `eulogy`,
  `newspaper-clipping`, `memoir`, `sermon`, `diary`
- Researcher artifacts: `family-group-sheet`, `genealogy-notes`, `research`,
  `historical-context`
- Long tail: `yearbook`, `screenshot`, `map`
- Media: `photo`, `portrait`, `tombstone`, `handwritten-fragment`
- Sentinels: `blank-scan`, `unknown`

If a single PDF is multiple distinct documents concatenated (common for batch
scans), produce ONE markdown per logical document. Append `-1`, `-2`, ... to
the filename. Note in `## Notes` that the source PDF holds multiple docs so
the inbox-processing pass keeps them grouped.

### 3. Extract entities

Tag every:

- **Person** mentioned, by full name. Cross-reference `people/` — if the
  person already has a file (`ls people/ | rg -i "lastname"`), use that exact
  filename in wikilinks: `[[Firstname Lastname (YYYY)]]`. If not, still link
  with the same convention; the inbox-processing pass will create the file.
- **Date** — normalize to `YYYY-MM-DD` (or `YYYY-MM` / `YYYY` if partial).
- **Place** — preserve as written; note modern equivalents in body if known
  (e.g., a historic name → its modern country/city equivalent).
- **Relationship** — every "father of", "married to", "son of", etc.
- **Vital event** — birth, death, marriage, immigration, naturalization,
  burial, military service.
- **Occupation, residence, religion** when present.

### 4. Write the markdown

Use this exact frontmatter (consistent with `templates/document.md` extended
with the source-sidecar fields from `SKILL.md`):

```yaml
---
title: "Concise descriptive title"
type: letter|eulogy|...      # from the list above
date: "YYYY-MM-DD"           # date the doc was written/issued, not scan date
author: "[[Author Name (YYYY)]]"  # or "" if unknown
recipients: []
related_people:              # ALL people mentioned, as wikilinks
  - "[[Person One (YYYY)]]"
  - "[[Person Two (YYYY)]]"
places: []                   # raw place strings
events:                      # vital events extracted
  - person: "[[Person (YYYY)]]"
    type: birth|death|marriage|...
    date: "YYYY-MM-DD"
    place: ""
source: "[[<original-stem>.pdf]]"  # the scanner-named PDF in _inbox/;
                                   # move_inbox_to_sources.py uses this
                                   # wikilink to find and rename the PDF
ocr_confidence: high|medium|low
todo: []                     # uncertain readings, follow-ups
---

# {{title}}

## Summary

2-4 sentence neutral summary of the document's content and significance.

## Cleaned Text

The full cleaned OCR text, paragraph-reflowed. Preserve original spelling and
phrasing — this is a primary source. Use blockquote (`> `) for the entire
quoted body so it renders distinctly from your annotations.

## Entities

### People
- [[Person Name (YYYY)]] — role/relationship in this document
- ...

### Places
- Place as written (modern equivalent if known)

### Dates & Events
- YYYY-MM-DD — what happened

## Notes

Anything important the inbox processor should know: discrepancies with
existing data, unusual claims, illegible passages, multi-document boundaries,
suspected dates of authorship if undated.

## Source

This document was OCR'd from a typewritten/printed scan on YYYY-MM-DD.
Source PDF: `[[<original-stem>.pdf]]` (in `_inbox/`; will be renamed to
match this markdown's filename and moved to `sources/` by
`move_inbox_to_sources.py`).
```

### 5. Filename

`_inbox/<YYYY>-<descriptive-slug>.md` — e.g.
`1937-letter-from-heinrich-to-klara.md`. Use the document date when known;
otherwise the scan year. Slug is lowercase, hyphenated, descriptive of
WHO + WHAT.

This is NOT the original PDF's stem. The PDF stays at
`_inbox/<scanner-stem>.pdf` and the link from this markdown to its PDF is
the `source: "[[<scanner-stem>.pdf]]"` frontmatter wikilink. The next
pipeline step (`move_inbox_to_sources.py`) uses that wikilink to match
markdown to PDF and rename the PDF to match the descriptive slug when
filing into `sources/`.

If one PDF holds multiple distinct documents, produce multiple
`<descriptive-slug>-1.md`, `<descriptive-slug>-2.md` files. Each carries
the same `source:` wikilink to the same PDF, and `move_inbox_to_sources.py`
will copy the PDF to each descriptive name (or you can adjust the
post-processing rule for multi-doc cases).

### 6. Cleanup

After writing each `.md`, delete the matching `.txt` in
`_scripts/scan-pipeline/.ocr-cache/`. The PDF holds the same text in its
embedded layer so the cache file is no longer needed.

### 7. After all files in this batch are written

Print a summary:

- Number of source `.txt` files processed
- Number of markdown files produced (may differ if a PDF held multiple docs)
- Total people referenced (deduplicated count)
- Any people NOT yet in `people/` — flag for the next inbox pass
- Any flags raised (low OCR confidence, illegible passages, suspected
  duplicates of existing sources)

Do not edit `people/` files in this pass. Do not move PDFs out of `_inbox/`.
The next "process the inbox" step does that — it sees `<stem>.pdf` +
`<stem>.md` together, files them into `sources/`, and updates the relevant
`people/` files using the entities you extracted.
