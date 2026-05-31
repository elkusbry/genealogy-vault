#!/usr/bin/env bash
# OCR every PDF in _inbox/ in place. Idempotent — PDFs that already have a
# matching .md sidecar (i.e. interpretation already happened) are skipped
# unless --force is passed.
#
# This is the OCR half of the pipeline. After it finishes, run the
# interpretation pass — easiest path: open Claude Code in the genealogy repo
# and say "process the inbox", which now also handles OCR'd PDFs.
#
# Usage:
#   ./process-scans.sh                # OCR everything new in _inbox/
#   ./process-scans.sh --force        # re-OCR PDFs even if a .md sidecar exists
#   ./process-scans.sh --language eng+deu   # multilingual (e.g. German letters)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="$(cd "$SCRIPT_DIR/../.." && pwd)"
INBOX="$VAULT/_inbox"

if ! command -v ocrmypdf >/dev/null 2>&1; then
  echo "error: ocrmypdf not on PATH" >&2
  echo "  install with: brew install ocrmypdf" >&2
  exit 1
fi

shopt -s nullglob
pdfs=("$INBOX"/*.pdf)
shopt -u nullglob

if [ ${#pdfs[@]} -eq 0 ]; then
  echo "no PDFs in $INBOX/ — drop scanned PDFs there and re-run."
  exit 0
fi

echo "OCR'ing ${#pdfs[@]} PDF(s) in $INBOX/ ..."
python3 "$SCRIPT_DIR/ocr_scan.py" "$@"

cat <<EOF

==========================================================================
OCR pass complete. Searchable PDFs are in $INBOX/ (originals replaced
in place). Raw OCR text is cached in $SCRIPT_DIR/.ocr-cache/.

NEXT STEP — interpretation
--------------------------------------------------------------------------
Open Claude Code in the genealogy repo and say:

  Process the inbox.

The genealogy skill will detect the OCR'd PDFs, run the interpretation pass
(see _scripts/scan-pipeline/interpret-prompt.md), generate structured .md
sidecars next to each PDF, then file everything into sources/ and update
people/.

For a quality check, look at a few .txt files in $SCRIPT_DIR/.ocr-cache/
before running interpretation. If many pages came out garbled, re-scan at
higher DPI (600+).
==========================================================================
EOF
