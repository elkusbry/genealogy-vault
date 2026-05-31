# Workflows reference

Every workflow this skill supports, with triggers and where to read.

The canonical workflows live in [`../skill/workflows/`](../skill/workflows/).
This page is a navigation index.

## Process the inbox

**Triggers:** "process inbox," "process the scans," "I dropped scans in,"
"OCR these," "file this PDF."

Full doc: [`skill/workflows/process-inbox.md`](../skill/workflows/process-inbox.md).

End-to-end pipeline: OCR every PDF in `_inbox/`, generate a structured
sidecar per document, file PDF + sidecar into `sources/`, extract facts
into `people/`.

## Add a person

**Triggers:** "add a person," "add my grandmother," "parents are X and Y."

Full doc: [`skill/workflows/add-person.md`](../skill/workflows/add-person.md).

Creates `people/Firstname Lastname (YYYY).md` from the template, updates
all bidirectional links (parents/children/siblings/spouses), computes
branch + generation + tags, adds research follow-ups.

## Process a source document

**Triggers:** A new sidecar arrives in `sources/`. Also includes
specialized subworkflows for **death certificates**, **tombstones**, and
**GEDCOM files**.

Full doc: [`skill/workflows/process-source.md`](../skill/workflows/process-source.md).

Extracts facts into person files, adds citations, photos get embedded
with cross-references in both directions.

## Translate a non-English document

**Triggers:** "translate this document," "add an English translation,"
or sidecar with non-English `languages:`.

Full doc: [`skill/workflows/translate-document.md`](../skill/workflows/translate-document.md).

Creates a companion sidecar at `<stem>-english-translation.md`, wires it
into the primary via the `translation:` key, regenerates the tagger.

## Tag photos via the viewer

**Triggers:** "tag photos," "open the photo tagger."

Full doc: [`skill/workflows/tag-photos.md`](../skill/workflows/tag-photos.md).

Regenerates `_tools/photo-tagger.html`, user clicks through, exports
JSON, applier script surgically edits sidecars + person files.

## Research and maintenance

**Triggers:** "what's open," "review questions," "fix that relationship,"
"split this PDF," "what's untagged," DNA queries.

Full doc: [`skill/workflows/research-and-maintenance.md`](../skill/workflows/research-and-maintenance.md).

A grab-bag of maintenance procedures:

- **Review open questions** — regenerate `OPEN-QUESTIONS.md` from every
  `todo:` array.
- **Handle relationship corrections** — bidirectional fix with branch /
  generation recompute.
- **Split fragment batches** — multi-page handwritten-fragment PDFs.
- **Untagged inventory** — find images without sidecars, sidecars
  without people, etc.
- **Document DNA research** — capture Y-DNA / mtDNA / autosomal findings.
