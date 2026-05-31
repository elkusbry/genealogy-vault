---
title: ""
type: ""                  # see skill/schemas/document.schema.md for canonical types
date: ""                  # YYYY-MM-DD or YYYY
author: ""                # wikilink: "[[Firstname Lastname (YYYY)]]"
recipients: []            # array of wikilinks
related_people: []        # wikilinks to ALL people mentioned in the source
source: ""                # wikilink to the original file, e.g., "[[1937-family-letter.pdf]]"
languages: ["English"]    # ["English"], ["German"], ["English", "Hebrew"], etc.
topics: []                # free-form: "immigration", "wedding", "schoolwork"
confidence: ""            # proven | probable | possible | uncertain

# Companion files (optional — see skill/schemas/document.schema.md § Companion files)
# Use BARE filename with .md, NOT a wikilink — wikilink form silently breaks the tagger.
translation: ""           # "<stem>-english-translation.md"
notes: ""                 # "<stem>-notes.md"
transcription: ""         # "<stem>-transcription.md"
content: ""               # "<stem>-content.md"

# For research artifacts (translations, notes documents)
translator: ""            # name or "model + date"
covers: ""                # which pages / sections / scope; what is NOT covered
---

# {{title}}

## Description

(Brief prose describing the document — what it is, its provenance, significance.
Distinct from any quoted caption.)

## Caption

(If the source arrived with a sender-supplied caption, preserve it verbatim
with attribution — see skill/schemas/document.schema.md § Captions. Delete
this section if there's no caption.)

## Cleaned Text

(The OCR/transcribed text, cleaned of OCR artifacts but faithful to the
original. Omit for images-only sources.)

## Extracted Facts

- (Bulleted list of facts pulled from the source, each with a citation back
  to the source itself — these will be merged into person files.)

## Related People

- (Same as `related_people:` frontmatter; spelled out for human reading in
  Obsidian.)

## Source

![[{{filename}}]]
