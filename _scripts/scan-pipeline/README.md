# Scan Pipeline

OCR + interpretation pipeline for genealogy scans. Drop scanned PDFs into
`_inbox/` and ask Claude to "process the inbox" — the rest is handled.

## TL;DR

```
<vault>/_inbox/Scan_2026_05_03_001.pdf   # drop here
```

In Claude Code or Codex, opened in the vault:

> Process the inbox.

The genealogy skill OCRs every new PDF in `_inbox/`, generates a structured
markdown sidecar per document, files both into `sources/`, and updates
`people/` files with the extracted facts. No separate folders, no manual
script invocation.

## Folder map

```
_inbox/                                   # drop zone for ANYTHING
  Scan_*.pdf                              # raw scans (OCR'd in place)
  1957-letter-from-philip-to-fannie.md    # interpretation output
                                          #   -> linked to its PDF via
                                          #      `source: "[[Scan_*.pdf]]"`
                                          #      frontmatter wikilink
sources/                                  # final destination after move
  1957-letter-from-philip-to-fannie.pdf   # PDF renamed to descriptive slug
  1957-letter-from-philip-to-fannie.md    # markdown moved alongside

_scripts/scan-pipeline/
  ocr_scan.py                             # OCR every new PDF in _inbox/
  process-scans.sh                        # convenience wrapper for the above
  interpret-prompt.md                     # Claude's interpretation playbook
  generate_inbox_drafts.py                # bulk programmatic interpretation
                                          #   (alternative to Claude — has a
                                          #    hand-curated MANIFEST per file)
  move_inbox_to_sources.py                # match .md to its PDF via source:
                                          #   wikilink, file both into sources/
  .ocr-cache/<stem>.txt                   # transient raw OCR text
                                          #   (auto-deleted after .md is written)
  logs/ocr_<timestamp>.log                # per-run OCR log
```

## The pipeline, in 3 steps

### 1. OCR

```bash
./process-scans.sh                # OCR every new PDF in _inbox/
./process-scans.sh --language eng+deu   # multilingual batch
```

What happens:

- Every `*.pdf` in `_inbox/` that is NOT already referenced by some
  `_inbox/*.md`'s `source:` wikilink is OCR'd.
- Each PDF is replaced in place with a searchable PDF/A (text layer added).
- Raw OCR text lands in `.ocr-cache/<original-stem>.txt` for the
  interpretation pass.
- Logs go to `logs/`.

Tuning is in `ocr_scan.py`: deskew, clean (unpaper), 300 DPI oversample,
LSTM tesseract engine (oem 1), --force-ocr always (the bulk-import scanner
embeds empty text layers that would otherwise cause skips).

### 2. Interpret

Two paths:

**a) Claude (preferred for variety / one-off batches).** In Claude Code:

> Process the OCR'd files in `_scripts/scan-pipeline/.ocr-cache/` following
> `_scripts/scan-pipeline/interpret-prompt.md`.

Claude reads each `.txt`, fixes typewriter OCR errors, identifies the
document type, extracts entities (people, places, dates, vital events),
and writes a descriptively-named markdown to `_inbox/` with a `source:`
wikilink back to the original PDF. Process in batches of 10–20 for large
runs.

**b) `generate_inbox_drafts.py` (preferred for repetitive batches —
e.g., a multi-hundred-page typescript scanned across many days).** This is
a Python script with a hand-curated MANIFEST mapping each scanner
timestamp to a title, slug, type, and summary. Cheaper than the agent for
hundreds of similar pages.

Either path produces `_inbox/<YYYY>-<descriptive-slug>.md` with `source:
"[[<original-stem>.pdf]]"` in frontmatter.

### 3. File into sources/

```bash
python3 _scripts/scan-pipeline/move_inbox_to_sources.py
```

For each `_inbox/<descriptive>.md`:

1. Read the `source:` wikilink to find the original PDF stem.
2. Move `_inbox/<original-stem>.pdf` → `sources/<descriptive>.pdf` (PDF
   gets renamed to match the markdown).
3. Move `_inbox/<descriptive>.md` → `sources/<descriptive>.md`.
4. Update any `<original-stem>.pdf` wikilink references inside the
   markdown to use the new descriptive name.

Then continue with the regular "process the inbox" workflow — extract
facts into `people/` files, add citations, update relationships.

## Why this design

- **One drop folder.** No `_scan-inbox/` vs `_inbox/`. Drop anything in
  `_inbox/`; the pipeline handles whatever's there.
- **In-place OCR.** The original scanned PDF is replaced by a searchable
  PDF/A. The original isn't preserved separately because the searchable
  version is strictly an upgrade (same image, plus a text layer). PDF/A
  is also the right archival format.
- **Descriptive renaming at move time.** Scanner-generated names
  (`Scan_2026_05_03_13_27_59.pdf`) are useless. The markdown carries the
  descriptive name; `move_inbox_to_sources.py` propagates it to the PDF
  during the move into `sources/`. This matches the long-standing
  convention in `sources/`.
- **Idempotent.** Re-running the pipeline on the same `_inbox/` is safe.
  A PDF is "done" once some `_inbox/*.md` references it via
  `source:` — that signal survives across runs.

## Prerequisites

```bash
brew install ocrmypdf      # bundles tesseract, ghostscript, qpdf, unpaper
brew install tesseract-lang # adds 163 language packs (deu, fra, heb, pol, rus, yid, etc.)
```

Verify:

```bash
ocrmypdf --version          # 17.x
tesseract --version         # 5.x
tesseract --list-langs      # should list deu, fra, heb, pol, rus, yid
```

## Future work — Transkribus for handwriting

**Status: TODO, not yet integrated.**

Tesseract (the OCR engine ocrmypdf wraps) is good at typewriter print but
**very poor at cursive handwriting** — German Sütterlin / Kurrent, French
19th-century cursive, Russian Cyrillic vital records, Yiddish handwriting,
and similar pre-typewriter scripts often appear in 19th- and early 20th-
century family papers.

**Transkribus** ([transkribus.eu](https://www.transkribus.eu)) is the academic-grade
HTR (Handwritten Text Recognition) platform purpose-built for historical
manuscripts. It has pre-trained models for German Sütterlin, French period
scripts, Yiddish, Russian Cyrillic, and Hebrew. Free tier: ≤500 credits/month
(~500 pages); paid tier: ~€0.20/page beyond that.

### Setup steps (when ready to take this on)

1. **Sign up** for a free account at https://app.transkribus.org/signin
2. **Upload one of your handwritten PDFs as a test batch.** Pick a
   representative document — a Holocaust-era German letter, a 19th-century
   Russian/Polish vital record, a French cursive postcard, whatever your
   collection includes.
3. **Select a pre-trained model**:
   - German Sütterlin / Kurrent: `German_Kurrent_M2` or `German_Handwriting_M3`
   - French 19th-century cursive: `French_Mixed_M1`
   - Russian Cyrillic vital records: `Transkribus_Russian_Imperial_19c`
   - Hebrew: `Modern_Hebrew_M1` (or for older scripts, a custom-trained model)
4. **Run the transcription** — Transkribus returns plain text + bounding
   boxes per word, downloadable as `.txt` or PAGE-XML.
5. **Drop the resulting text into the matching sidecar** in this vault and
   set `ocr_confidence: medium-transkribus` (a new value) so the source of
   the transcription is auditable.

A `_scripts/scan-pipeline/transkribus_push.py` could be added in the future
to push selected PDFs and pull back their transcripts via the
[Transkribus REST API](https://readcoop.eu/transkribus/howto/how-to-use-the-transkribus-api/).
Until that's built, the workflow above (manual upload via the web app) is
the recommended path.

## Troubleshooting

- **OCR is producing garbage.** Check `.ocr-cache/<stem>.txt`. If most
  pages are illegible, the scan resolution is too low. Re-scan at 600+
  DPI before proceeding. Don't burn tokens interpreting bad OCR.
- **`move_inbox_to_sources.py` says "Original PDF missing".** The
  markdown's `source:` wikilink points to a stem that's not in `_inbox/`.
  Either the PDF was already moved, or the wikilink is wrong. Check
  manually.
- **Re-OCR a specific file.** Pass `--force` to `process-scans.sh`. This
  re-OCRs every PDF regardless of whether it's already referenced.
- **One PDF holds multiple distinct documents.** The interpretation pass
  produces multiple `<descriptive>-1.md`, `<descriptive>-2.md` files,
  each with the same `source:` wikilink. The move step needs a manual
  decision on PDF naming in this case (you may want to keep the PDF at
  one of the names and reference it from both markdowns).
