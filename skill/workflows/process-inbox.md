# Workflow: Process the Inbox

**Triggers:** "process inbox," "process the scans," "I dropped scans in,"
"OCR these," "file this PDF," or any time the user drops a file into `_inbox/`.

This workflow chains OCR → sidecar generation → fact extraction →
inbox→sources filing. It's the marquee end-to-end pipeline.

## Steps

1. **List the inbox.**
   ```sh
   ls _inbox/
   ```

2. **Scan-OCR pre-pass.** For every `*.pdf` in `_inbox/` that is NOT already
   referenced by a `source: "[[<stem>.pdf]]"` wikilink in some `_inbox/*.md`,
   run the OCR + interpretation pipeline (see "OCR pass" below). This
   produces a descriptively-named `<YYYY>-<slug>.md` in `_inbox/` for each
   PDF, linked back to the original PDF via its `source:` wikilink.

3. **Re-`ls _inbox/`.** Now every PDF is referenced by some `.md`, so the
   rest of the pass can pair them up.

4. **File-into-sources pass.** Run:
   ```sh
   python3 _scripts/scan-pipeline/move_inbox_to_sources.py
   ```
   For each `_inbox/*.md`, this reads the `source:` wikilink, finds the
   matching `_inbox/<original-stem>.pdf`, and moves both into `sources/` —
   renaming the PDF to match the markdown's descriptive name and rewriting
   wikilinks.

5. **Categorize anything else** in `_inbox/`:
   - Images (JPG/PNG) → `media/` (most cases) or `sources/` (when they
     document facts — death certs, tombstones, scanned letters).
   - GEDCOM → see `process-source.md` § GEDCOM.
   - XLSX/CSV → extract with Python; save summary; remove the original.

6. **Process each newly-filed item** via the relevant workflow:
   - Death certificate → `process-source.md` § Death certificates
   - Tombstone photo → `process-source.md` § Tombstones
   - Translation needed → `translate-document.md`
   - Generic source → `process-source.md`

7. **Caption-vehicle PDFs.** If a PDF is an email-export bundle (a forwarded
   "look what I found" message with attached JPGs printed alongside typed
   captions), the PDF is a *vehicle* for the captions — not a record. The
   accompanying JPGs are the durable artifact:
   - Move each JPG to `media/` with a descriptive filename.
   - Create a sidecar whose `## Caption` block preserves the sender's exact
     wording (see `schemas/document.schema.md` § Captions).
   - Delete the PDF — it's been distilled into the sidecars.
   - Confirm with the user before deleting if there's narrative text in the
     PDF beyond per-image captions.

## OCR pass

Invoked automatically by step 2, or directly when the user says "OCR the
scans," "process the scans," or "I dropped scans in."

**Inputs:** PDFs in `_inbox/` not yet referenced by any `_inbox/*.md`
`source:` wikilink.

**Pipeline:**

1. **Run OCR:**
   ```sh
   _scripts/scan-pipeline/process-scans.sh
   ```
   This calls `ocr_scan.py` which:
   - OCRs each PDF in place (replaces original with searchable PDF/A)
   - Writes raw OCR text to `_scripts/scan-pipeline/.ocr-cache/<stem>.txt`
   - Logs to `_scripts/scan-pipeline/logs/`
   - For 500+ pages this is slow (estimate 30s–2min per page). Run in
     background and tail the log file. Don't poll.

2. **Quality gate.** Read 2–3 random `.ocr-cache/*.txt` files. If most pages
   are garbled, STOP and tell the user to re-scan at higher DPI (600+)
   before continuing. Don't burn tokens interpreting bad OCR.

3. **Interpretation pass.** Read the prompt at
   `_scripts/scan-pipeline/interpret-prompt.md` and follow it for every
   `.txt` in `.ocr-cache/`. This produces a descriptively-named
   `_inbox/<YYYY>-<slug>.md` for each, with frontmatter, cleaned body text,
   entity extraction, and `todo:` flags for uncertain readings. Each `.md`'s
   `source:` wikilink points back to the scanner-named PDF in `_inbox/`.

   For large batches (>20 docs), process in groups of 10–20 so token use
   stays bounded; tell the user how many remain after each batch.

4. **Cleanup.** After each `.md` is written, the matching `.txt` in
   `.ocr-cache/` is deleted (the PDF's embedded text layer is the durable
   copy).

## Languages

Default OCR language is English. For mixed-language batches (German letters,
Yiddish typewriter pages, etc.):

```sh
_scripts/scan-pipeline/process-scans.sh --language eng+deu
```

Combine language codes with `+`. See the Tesseract docs for codes.

## Idempotency

Re-running the inbox processor on the same `_inbox/` skips PDFs already
referenced by some `_inbox/*.md` `source:` wikilink. Pass `--force` to the
OCR script to redo a specific file.
