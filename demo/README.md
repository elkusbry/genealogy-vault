# The Riverstone family (demo data)

This directory contains a fully-worked example vault: 10 people across 3
generations, 9 source sidecars, a Map of Content, and an open-questions
backlog. Cloning this repo and opening it in Obsidian gives you something
you can immediately poke at — every workflow in the skill has a fixture
to land on.

## What's here

```
demo/
├── README.md          (this file)
├── MOC.md             Map of Content — family tree with wikilinks
├── OPEN-QUESTIONS.md  Research backlog
├── people/            10 person files spanning 1885–today
└── sources/           9 source sidecars covering:
    - German-language letter (translation companion demo)
    - 1920 US Census (multi-person source)
    - Tombstone (Hebrew/German + English)
    - Undated photo (date-inference demo)
    - Marriage record with date discrepancy (confidence demo)
    - WWII V-mail fragment (handwritten-fragment type)
    - Death certificate (death-record workflow)
    - Passport photo (related_people demo)
```

## Demoable scenarios

| Scenario | Where to look |
|---|---|
| Translation companion (Translation tab) | `1937-letter-from-heinrich-to-klara-vienna.md` ↔ `*-english-translation.md` |
| Multi-person source extraction | `1920-us-census-riverstone-household-philadelphia.md` |
| Tombstone with bilingual inscription | `heinrich-riverstone-tombstone.md` |
| Undated artifact, date inference | `undated-riverstone-family-portrait.md` |
| Conflicting dates → `confidence` + `todo:[discrepancy]` | `1937-mary-thomas-marriage-record.md` + `Mary Riverstone (1915).md` |
| Handwritten fragment type | `1944-friedrich-riverstone-handwritten-fragment.md` |
| Death-certificate workflow | `1992-mary-brennan-death-certificate.md` |
| Person with `confidence: uncertain` + multiple `[document-search]` todos | `Aaron Adler.md` |
| Living person, sparse data, no PII | `Catherine Brennan (1940).md`, `Linda Sandstrom (1950).md` |
| Open research backlog aggregation | `OPEN-QUESTIONS.md` |

## Binary assets

**Three CC0 placeholder JPEGs ship with this demo** so the photo tagger
renders something out of the box:

- `demo/sources/heinrich-riverstone-tombstone.jpg`
- `demo/sources/1912-klara-passport-photo.jpg`
- `demo/media/undated-riverstone-family-portrait.jpg`

They're synthetically generated (PIL drawings with sepia tones) and
clearly labeled "PLACEHOLDER." Replace with your own scans whenever you
want — the sidecars don't change.

**PDFs referenced by the source sidecars are NOT shipped.** To exercise
the OCR pipeline against the demo, drop a sample PDF named exactly to
match one of the referenced stems (e.g.,
`1937-letter-from-heinrich-to-klara-vienna.pdf`) into `demo/sources/`.
The skill will pick it up.

## Starting with your own family

When you're ready to use this vault for your own research:

1. **Delete this `demo/` directory entirely.**
2. **Move new files into the repo root** — `people/`, `sources/`, `media/`
   (the installer / template already created empty versions of these).
3. **Copy `skill/family-context.md.template` → `skill/family-context.md`**
   and fill in your tree root and surnames so the skill recognizes them.
4. **Edit the root `MOC.md`** (or rename it from `MOC.md.template` if
   such a thing exists in your version) to reflect your family.
5. **Open in Claude Code or Codex** and start with "process the inbox"
   or "add a person."

Alternatively, keep `demo/` for a while as a reference — its sidecars are
canonical examples of each schema's intended shape.

## Why these scenarios?

The Riverstones are designed to surface every interesting case the skill
has to handle:

- **Immigration** — names that change form across the language boundary
  (Heinrich/Henry, Klara/Clara, Friedrich/Freddy).
- **Wartime loss** — a person with no descendants but full source
  coverage.
- **Cross-language documents** — the canonical Translation companion
  workflow.
- **Conflicting sources** — Mary's marriage date, Heinrich's birth year.
- **Living people, privacy** — Generation 3 entries are deliberately
  sparse and contain no real PII.
- **Uncertain ancestors** — Aaron Adler is `confidence: uncertain` and
  shows how to keep an unresolved entry without breaking the tree.

If you find a workflow case the Riverstones don't cover, that's likely a
gap in v0.1's fixture — open an issue.
