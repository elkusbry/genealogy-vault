#!/usr/bin/env python3
"""Process OCR'd .txt files in _scripts/scan-pipeline/.ocr-cache/ into
_inbox/ markdowns.

Workflow per _scripts/scan-pipeline/interpret-prompt.md:
  1. Read each .txt
  2. Apply OCR cleanup rules
  3. Write one inbox markdown per .txt (or per logical doc when batch-scanned)
  4. Link the searchable PDF in _inbox/ via source: frontmatter wikilink

This script handles the bulk transformation. Hand-review pass follows.
"""
from __future__ import annotations

import re
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent.parent
OCR_TEXT = VAULT / "_scripts" / "scan-pipeline" / ".ocr-cache"
INBOX = VAULT / "_inbox"
SOURCES = VAULT / "sources"

# Per-file manifest: stem → metadata
# Keys: title, type, year_slug, ocr_confidence, body_subjects (optional summary hint)
MANIFEST = {
    # This MANIFEST is HAND-CURATED per project. Map each scanner-generated
    # stem (the filename Tesseract sees in .ocr-cache/) to the metadata you
    # want the inbox draft to carry. The keys below are illustrative — replace
    # them with your own batch.
    #
    # The point of this script (vs. having the agent interpret each scan)
    # is cost: when you have hundreds of pages with predictable shape
    # (e.g. one typescript scanned across many days), authoring the manifest
    # once is much cheaper than asking the agent to interpret each one.
    #
    # Example entries (replace with your own):
    "2026_05_03_13_27_59": {
        "title": "Sample typewritten genealogy notes — pages 1-2",
        "type": "genealogy-notes",
        "year_slug": "1989-sample-genealogy-notes-pages-1-2",
        "ocr_confidence": "high",
        "summary": "Body entry covering a hypothetical ancestor with marriage details, occupation, and probate notes. Replace this entry with your own metadata.",
    },
    "2026_05_03_13_28_44": {
        "title": "1983 letter from researcher describing trip to county courthouse",
        "type": "correspondence",
        "year_slug": "1983-researcher-letter-courthouse-trip",
        "ocr_confidence": "high",
        "doc_date": "1983-05-23",
        "author": "",  # wikilink to author if known
        "summary": "May 1983 letter from a family researcher describing a trip to a county courthouse for probate records. Replace this entry with your own metadata.",
    },
}


# ---------- OCR cleanup helpers ----------

def basic_substitutions(text: str) -> str:
    """Apply the OCR cleanup table from interpret-prompt.md (conservative).

    Most rules need context — we only apply the SAFE ones globally:
    - line-end hyphen joining inside a paragraph
    - normalize multiple spaces
    """
    # Join hyphenated line breaks: "exam-\nple" → "example"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # Collapse 3+ blank lines to 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse runs of spaces
    text = re.sub(r"  +", " ", text)
    # Common OCR-typewriter artifacts at line starts (kept as-is in body but flagged)
    return text


def reflow_paragraphs(text: str) -> str:
    """Lightly reflow paragraphs: keep blocks separated by blank lines as paragraphs,
    keep clearly tabular/code-like lines (mostly uppercase, lots of numbers) as-is.

    This is intentionally conservative — we keep the original line structure
    for typewriter family-group-sheet style content."""
    return text  # no reflow — let next pass handle, since structure is informative


def cleaned_block(text: str) -> str:
    """Build the > blockquote for the cleaned-text section."""
    text = basic_substitutions(text)
    # Quote each line
    lines = text.splitlines()
    quoted = []
    for ln in lines:
        if ln.strip() == "":
            quoted.append(">")
        else:
            quoted.append(f"> {ln}")
    return "\n".join(quoted)


# ---------- Frontmatter helpers ----------

CODE_PAT = re.compile(r"\b([2-5]?[A-K])[-=]+(\d{1,12}|\d+<\d+>)\b")

def extract_codes(text: str) -> list[str]:
    """Extract genealogy codes mentioned in this scan (deduped, original order)."""
    seen = set()
    out = []
    for m in CODE_PAT.finditer(text):
        code = f"{m.group(1)}-{m.group(2)}"
        if code not in seen:
            seen.add(code)
            out.append(code)
    return out


def render(stem: str, raw_text: str, meta: dict) -> str:
    title = meta["title"]
    type_ = meta["type"]
    confidence = meta["ocr_confidence"]
    summary = meta["summary"]
    doc_date = meta.get("doc_date", "")
    author = meta.get("author", "")

    codes = extract_codes(raw_text)
    codes_block = "\n".join(f"  - {c}" for c in codes[:30]) or "  []"

    pdf_link = f"[[{stem}.pdf]]"

    return f"""---
title: "{title}"
type: {type_}
date: "{doc_date}"
author: "{author}"
recipients: []
related_people: []   # populated by next inbox pass
places: []
events: []
genealogy_codes:
{codes_block}
source: "{pdf_link}"
ocr_confidence: {confidence}
todo:
  - "[document-search] Cross-reference codes mentioned against existing /people/ files; create stubs for any unmatched codes"
  - "[vital-records] Extract dates from each body entry into the corresponding person file"
---

# {title}

## Summary

{summary}

## Cleaned Text

The full cleaned OCR text from `_scripts/scan-pipeline/.ocr-cache/{stem}.txt`. Preserved original spelling and typewriter line structure. Where ?text? appears the OCR reading is uncertain; correct in subsequent processing.

{cleaned_block(raw_text)}

## Entities

### Genealogy Codes Mentioned

{chr(10).join(f"- `{c}`" for c in codes[:30])}

### People

_(To be extracted by the inbox-processing pass — every body entry typically lists a person at top with code, dates, marriage, occupation, and children.)_

### Places

_(To be extracted by the inbox-processing pass.)_

## Notes

OCR'd from a typewritten page via `_scripts/scan-pipeline/process-scans.sh`.

If your source has a regular per-entry shape (e.g. a typescript with one
ancestor per body block, each carrying a fixed code + dates + relations +
occupation), document that shape here so downstream extraction can follow
it. Example shape:

```
<CODE>
NAME (caps)
bd. MM-DD-YYYY <birthplace>
dd. MM-DD-YYYY <deathplace>
M. MM-DD-YYYY <spouse>
oc. <occupation>
rs. <residence>
ch. <child names>
ms./sr. <miscellaneous notes / source>
```

Many embedded artifacts in OCR (e.g. `am`, `™`, `-`, `~`, "`pee`", `om`) are
typewriter ink-mark misreads. Treat as ignorable.

## Source

This document was OCR'd from a typewritten/printed scan on 2026-05-03.
Searchable PDF: `[[{stem}.pdf]]` (in `_inbox/`; will be renamed to match
this markdown's filename and moved to `sources/` by
`move_inbox_to_sources.py`).
Raw OCR text: `_scripts/scan-pipeline/.ocr-cache/{stem}.txt` (transient).
"""


def main():
    INBOX.mkdir(exist_ok=True)
    txt_files = sorted(OCR_TEXT.glob("*.txt"))
    print(f"Found {len(txt_files)} OCR'd text files")

    created = 0
    skipped_inbox = 0
    skipped_finalized = 0
    missing = 0
    for f in txt_files:
        stem = f.stem
        if stem not in MANIFEST:
            print(f"  ! NO MANIFEST entry for {stem} — skip")
            missing += 1
            continue
        meta = MANIFEST[stem]
        out_path = INBOX / f"{meta['year_slug']}.md"
        finalized_path = SOURCES / f"{meta['year_slug']}.md"
        if finalized_path.exists():
            print(f"  - skip (already finalized in sources/): {finalized_path.name}")
            skipped_finalized += 1
            continue
        if out_path.exists():
            print(f"  - skip (already in _inbox/): {out_path.name}")
            skipped_inbox += 1
            continue
        raw = f.read_text(encoding="utf-8", errors="replace")
        out_path.write_text(render(stem, raw, meta))
        created += 1
        print(f"  + created: {out_path.name}")

    print(
        f"\nDone: {created} created, {skipped_inbox} skipped (inbox), "
        f"{skipped_finalized} skipped (already in sources/), "
        f"{missing} missing manifest (of {len(txt_files)} total)"
    )


if __name__ == "__main__":
    main()
