#!/usr/bin/env python3
"""Move OCR'd PDFs from _inbox/ to sources/, and move matching markdowns
from _inbox/ to sources/, updating source: frontmatter wikilinks to use the
new descriptive filename.

Match by reading the original PDF stem from the `source:` wikilink in each
inbox md. The PDF lives in _inbox/ alongside the markdown — `ocr_scan.py`
OCRs it in place.
"""
from __future__ import annotations
import re
import shutil
from pathlib import Path

VAULT = Path(__file__).resolve().parent.parent.parent
INBOX = VAULT / "_inbox"
SOURCES = VAULT / "sources"

SOURCE_LINE_PAT = re.compile(r'^source:\s*"\[\[([^\]]+)\.pdf\]\]"', re.MULTILINE)


def main():
    if not INBOX.exists():
        print("No _inbox/")
        return

    md_files = sorted(INBOX.glob("*.md"))
    print(f"Found {len(md_files)} inbox markdowns")

    moved_pdfs = 0
    moved_mds = 0
    errors = 0

    for md in md_files:
        target_basename = md.stem
        new_md_path = SOURCES / f"{target_basename}.md"
        new_pdf_path = SOURCES / f"{target_basename}.pdf"

        text = md.read_text()
        m = SOURCE_LINE_PAT.search(text)
        if not m:
            print(f"  ! NO source: line found in {md.name}")
            errors += 1
            continue

        original_pdf_stem = m.group(1)
        original_pdf = INBOX / f"{original_pdf_stem}.pdf"

        if not original_pdf.exists():
            print(f"  ! Original PDF missing in _inbox/: {original_pdf.name}")
            errors += 1
            continue

        # Move PDF
        if new_pdf_path.exists():
            print(f"  - PDF already at target: {new_pdf_path.name}")
        else:
            shutil.move(str(original_pdf), str(new_pdf_path))
            moved_pdfs += 1
            print(f"  + moved PDF: {original_pdf.name} → {new_pdf_path.name}")

        # Update source: wikilink and inline refs
        new_text = text.replace(
            f'source: "[[{original_pdf_stem}.pdf]]"',
            f'source: "[[{target_basename}.pdf]]"'
        )
        new_text = new_text.replace(
            f'`[[{original_pdf_stem}.pdf]]`',
            f'`[[{target_basename}.pdf]]`'
        )

        if new_md_path.exists():
            print(f"  - Sidecar already at target: {new_md_path.name}")
        else:
            # Use shutil.move (rename) then overwrite content. Avoids the
            # write-new-then-unlink-old pattern, which fails in sandboxes that
            # block deletion of mounted files (e.g. the cowork mount on
            # macOS). On macOS the rename is atomic on the same filesystem.
            shutil.move(str(md), str(new_md_path))
            new_md_path.write_text(new_text)
            moved_mds += 1
            print(f"  + moved sidecar: {md.name} → sources/{new_md_path.name}")

    print(f"\nDone: {moved_pdfs} PDFs moved, {moved_mds} sidecars moved, {errors} errors")


if __name__ == "__main__":
    main()
