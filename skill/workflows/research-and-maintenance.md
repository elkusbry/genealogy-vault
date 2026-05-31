# Workflow: Research & Maintenance

A grab-bag of recurring maintenance procedures. Each subsection is a distinct
workflow with its own triggers.

## Review open questions

**Triggers:** "review questions," "what's open," "research status," "open
questions."

1. Scan all `people/*.md` files for non-empty `todo:` arrays.
2. Also scan `## Research Notes` sections for inline questions and
   discrepancies that should be formal todos.
3. Group by category: `vital-records`, `identity`, `relationship`,
   `discrepancy`, `document-search`, `dna`.
4. Regenerate `Research Questions.md` (or `OPEN-QUESTIONS.md` — pick one and
   stick to it) with:
   - Count summary at top.
   - Questions grouped by category.
   - Each question links back to its person file:
     `- [[Person Name (YYYY)]]: question text`.
   - Priority items (discrepancies, relationship questions) at top.
5. Ensure all files with open questions carry the
   `research/has-questions` tag.
6. Report summary to user: total open questions, by category, any newly
   discovered.

## Handle relationship corrections

**Triggers:** "X is actually the parent of Y," "wrong parent on Z," "fix
that relationship."

1. **Remove** the child from the wrong parent's `children:` array AND from
   any body bullets that list them.
2. **Add** the child to the correct parent's `children:` array AND body.
3. **Update** the child's `parents:` to reflect the correct parent(s).
4. **Update `siblings:`** for all affected siblings — both the children of
   the wrong parent (who lose a sibling) and the children of the correct
   parent (who gain one).
5. **Recalculate `branch` and `generation`** for the moved person and
   anyone descended from them. Branch may stay the same if the correction
   is within-family; generation usually stays the same too.
6. **If the correction also affects `cr_id` relationship arrays** (Charted
   Roots integration), regenerate `parents_id` / `children_id` /
   `siblings_id` to match the new wikilink arrays.
7. **Document the correction** in `## Research Notes` of all affected
   people with a citation to the source that prompted the fix.

## Split fragment batches

**Triggers:** "split this PDF," "the fragment batch needs splitting," when
the inbox/sources contains a multi-page PDF where each page is a distinct
scan (e.g., `handwritten-fragment-21-02-27.pdf`).

```sh
python3 _scripts/split_fragment_pdf.py sources/<filename>.pdf
```

(If the script isn't present in your vault, it's optional — see
`_scripts/scan-pipeline/README.md` for whether your version includes it.)

The splitter:
- Extracts each page's embedded JPEG → `<stem>-p01.jpg`, `-p02.jpg`, …
- Creates a stub sidecar per page with `type: handwritten-fragment` (or
  `blank-scan` for visibly blank pages), `related_people: []`, and a
  `parent_batch:` wikilink back to the original.
- Marks the parent sidecar with `split: true` and notes the split in its
  body.
- Archives the original PDF to `_archive/fragment-pdfs/`.

After splitting, regenerate the photo tagger so the new fragment JPGs
appear:

```sh
python3 _scripts/taggers/build_photo_tagger.py
```

## Untagged inventory

**Triggers:** "what's untagged," "what needs attention," "untagged
inventory," "scan the vault for work."

```sh
python3 _scripts/build_untagged_inventory.py
```

(Optional — present in some vaults; see the script's source for what it
checks.) Produces a markdown report with Obsidian wikilinks to every:

- **A.** Multi-page fragment batch that should be split.
- **B.** Image file with no sidecar.
- **C.** Sidecar with empty `related_people:` / `people:`.
- **D.** Photo visible in the tagger but currently untagged.

Each row carries the date, location, author, and title pulled from the
sidecar so the user can prioritize without opening every file. Click any
wikilink in Obsidian to dive in.

## Document DNA research

**Triggers:** "DNA results," "Y-DNA," "haplogroup," "genetic match."

1. **Create sidecars** per research document / email chain in `sources/`.
2. **Update the relevant patrilineal/matrilineal ancestor** with findings:
   SNPs, haplogroup path, matches, CMH markers, expert opinions.
3. **Update tested individuals** with kit numbers and results.
4. **Tag:** `dna/ydna`, `dna/mtdna`, `dna/autosomal`, `research/<topic>` as
   appropriate.
