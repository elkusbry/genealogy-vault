#!/usr/bin/env python3
"""
OCR every PDF in _inbox/ in place and emit a raw text sidecar for the
interpretation pass.

Tuned for ~500 pages of typewriter and printed genealogy documents:
- Deskew + clean (unpaper) before OCR — typewritten pages drift on flatbed scanners
- Optimize level 2 — shrinks archive PDFs without quality loss
- 300dpi minimum — typewriter glyphs need resolution
- LSTM tesseract engine (oem 1) — best on degraded type
- Per-page progress logging — at 500 pages a silent script is unacceptable
- --force-ocr always: the bulk-import scanner embeds empty text layers that
  would otherwise cause ocrmypdf to skip pages

In-place flow (no separate scan inbox):
    _inbox/<name>.pdf      original (scanned or born-digital)
        → ocrmypdf → temp .pdf with text layer → atomic rename back
    _inbox/<name>.pdf      searchable PDF/A (replaces original)
    _scripts/scan-pipeline/.ocr-cache/<name>.txt   raw OCR text (transient)
    _scripts/scan-pipeline/logs/ocr_<timestamp>.log

Idempotency:
- Skip a PDF if any _inbox/*.md has a `source: "[[<stem>.pdf]]"` wikilink
  pointing to it (the interpretation pass writes that, so its presence
  means we're done). Markdowns have descriptive names; the PDF stem lives
  in their `source:` frontmatter wikilink.
- --force overrides and re-OCRs even processed PDFs.
"""

from __future__ import annotations

import argparse
import logging
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

SOURCE_LINE_PAT = re.compile(r'^source:\s*"\[\[([^\]]+)\.pdf\]\]"', re.MULTILINE)

VAULT = Path(__file__).resolve().parents[2]
INBOX = VAULT / "_inbox"
PIPELINE = Path(__file__).resolve().parent
OCR_CACHE = PIPELINE / ".ocr-cache"
LOGS = PIPELINE / "logs"


def setup_logging() -> Path:
    LOGS.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    log_path = LOGS / f"ocr_{timestamp}.log"
    handlers = [logging.FileHandler(log_path), logging.StreamHandler(sys.stdout)]
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s  %(levelname)-7s  %(message)s",
        datefmt="%H:%M:%S",
        handlers=handlers,
    )
    return log_path


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(f"required tool not on PATH: {name}")


def already_processed(pdf: Path, referenced_stems: set[str]) -> bool:
    """Has some _inbox/*.md already claimed this PDF as its source?"""
    return pdf.stem in referenced_stems


def collect_referenced_stems(inbox: Path) -> set[str]:
    """Return the set of PDF stems referenced by _inbox/*.md `source:` wikilinks."""
    stems: set[str] = set()
    for md in inbox.glob("*.md"):
        try:
            text = md.read_text()
        except OSError:
            continue
        for m in SOURCE_LINE_PAT.finditer(text):
            stems.add(m.group(1))
    return stems


def ocr_one(pdf: Path, *, language: str) -> bool:
    """OCR a single PDF in place. Returns True on success."""
    text_file = OCR_CACHE / (pdf.stem + ".txt")

    # OCR to a temp file in the same directory, then atomic-rename back over
    # the original. Same-directory keeps the rename atomic on the same fs.
    tmp_pdf = pdf.with_suffix(pdf.suffix + ".ocr-tmp")

    cmd = [
        "ocrmypdf",
        "--language", language,
        "--deskew",
        "--clean",
        "--rotate-pages",
        "--optimize", "2",
        "--output-type", "pdfa",
        "--oversample", "300",
        "--tesseract-oem", "1",
        "--sidecar", str(text_file),
        "--jobs", "4",
        "--force-ocr",
        str(pdf), str(tmp_pdf),
    ]

    logging.info("ocr start: %s", pdf.name)
    t0 = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    except FileNotFoundError as exc:
        logging.error("ocrmypdf not found: %s", exc)
        return False

    elapsed = time.time() - t0
    if result.returncode != 0:
        logging.error(
            "ocr FAIL (%.1fs, exit=%d): %s\nstderr:\n%s",
            elapsed, result.returncode, pdf.name, result.stderr.strip(),
        )
        # Clean up partial output
        if tmp_pdf.exists():
            tmp_pdf.unlink()
        return False

    if result.stderr.strip():
        logging.debug("ocrmypdf stderr for %s: %s", pdf.name, result.stderr.strip())

    # Replace original with searchable version
    try:
        tmp_pdf.replace(pdf)
    except OSError as exc:
        logging.error("could not replace %s: %s", pdf.name, exc)
        return False

    text_chars = text_file.stat().st_size if text_file.exists() else 0
    logging.info(
        "ocr OK  (%.1fs, %d chars text): %s",
        elapsed, text_chars, pdf.name,
    )
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input", type=Path, default=INBOX,
        help="folder containing PDFs (default: _inbox/)",
    )
    parser.add_argument(
        "--language", default="eng",
        help="tesseract language(s), e.g. 'eng' or 'eng+deu' (default: eng)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="re-OCR even PDFs already referenced by an _inbox/*.md source: wikilink",
    )
    args = parser.parse_args()

    log_path = setup_logging()
    require_tool("ocrmypdf")

    OCR_CACHE.mkdir(parents=True, exist_ok=True)

    # Top-level PDFs only — skip subfolders (the inbox has no subfolders by
    # convention, but be safe)
    pdfs = sorted(p for p in args.input.glob("*.pdf") if p.is_file())
    if not pdfs:
        logging.warning("no PDFs found in %s", args.input)
        return 0

    referenced = collect_referenced_stems(args.input)
    logging.info(
        "found %d PDF(s); %d already referenced by an _inbox/*.md source: wikilink; log: %s",
        len(pdfs), len(referenced & {p.stem for p in pdfs}), log_path,
    )
    ok = 0
    fail = 0
    skipped = 0
    run_start = time.time()
    for i, pdf in enumerate(pdfs, 1):
        logging.info("[%d/%d] %s", i, len(pdfs), pdf.name)
        if already_processed(pdf, referenced) and not args.force:
            skipped += 1
            logging.info("skip (referenced by existing _inbox/*.md): %s", pdf.name)
            continue
        if ocr_one(pdf, language=args.language):
            ok += 1
        else:
            fail += 1

    total = time.time() - run_start
    logging.info(
        "done: %d ok, %d fail, %d skipped, %.1fs total",
        ok, fail, skipped, total,
    )
    return 0 if fail == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
