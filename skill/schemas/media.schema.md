# Media Sidecar Schema

Photos, scanned images, family-tree diagrams, and other visual artifacts live
in `media/`. Each gets a sidecar `.md` with the same base name.

The full template lives at `templates/media.md`.

## When to put a file in `media/` vs `sources/`

- **`media/`** — photos, portraits, tombstones, family-tree images, anything
  the user might want to display in a person file via `![[filename]]`.
- **`sources/`** — original documents (records, letters, certificates) that
  are *evidence* of facts. PDFs go here even if they contain images.

A scanned death certificate is a `sources/` document. A portrait photo is a
`media/` item. A tombstone photo is a `sources/` document with `type:
tombstone` (because it documents Hebrew/English inscriptions that the
photo-tagger needs to surface) AND is embedded into the person's body.

## Frontmatter

```yaml
---
title: ""
type: ""                  # photo, portrait, family-tree-diagram, scan
date: ""
date_approximate: false
location: ""
people: []                # wikilinks — alias for related_people; both keys accepted
related_people: []        # same — pick one and stick to it
source: ""                # archive, family member name, or wikilink
photographer: ""
condition: ""             # good, fair, poor, damaged
original_format: ""       # print, negative, slide, digital, scan
notes: ""
tags:
  - media
---
```

## Body sections

```markdown
# {{title}}

![[{{filename}}]]

## Details

**Date:**
**Location:**
**Source:**

## People

(Same as `related_people:`; spelled out for human reading.)

## Notes
```

## Cross-reference rule

For **every** person listed in `related_people:`, the workflows MUST do both
halves of the cross-reference:

1. Append the photo wikilink to that person's `photos:` YAML array.
2. **Embed the image in their body** with `![[filename]]` — typically inside
   `## Stories & Memories` (or `### Headstone` for tombstones).

The body embed is what makes the image render in Obsidian's reading view of
the person; the YAML array alone is not enough. Add a short prose bullet
near the embed describing what the photo shows, with a `^[[[sidecar-name]]]`
citation so the caption is reachable in one click.

## Both `people:` and `related_people:` are recognized

Historic vaults used `people:`. Newer ones use `related_people:`. Both keys
are read by the photo-tagger and applier scripts; pick one within a vault
and stay consistent.
