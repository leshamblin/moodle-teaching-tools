#!/usr/bin/env bash
# Convert an HTML file to PDF using headless Chrome, then trim trailing blank pages.
#
# Usage: ./html_to_pdf.sh <input.html> <output.pdf>
#
# Requires Chrome installed at the standard macOS path. Falls back to
# Chromium or Google Chrome if found in PATH.

set -euo pipefail

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <input.html> <output.pdf>" >&2
    exit 1
fi

INPUT="$1"
OUTPUT="$2"

if [ ! -f "$INPUT" ]; then
    echo "Input file not found: $INPUT" >&2
    exit 1
fi

# Find Chrome
CHROME=""
if [ -x "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
    CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
elif command -v google-chrome >/dev/null 2>&1; then
    CHROME="google-chrome"
elif command -v chromium >/dev/null 2>&1; then
    CHROME="chromium"
else
    echo "Error: Could not find Chrome or Chromium." >&2
    echo "Install Google Chrome or set CHROME env var to the binary path." >&2
    exit 1
fi

# Convert to absolute file:// URL — Chrome headless requires this
ABS_INPUT="$(cd "$(dirname "$INPUT")" && pwd)/$(basename "$INPUT")"

# Generate PDF
"$CHROME" \
    --headless \
    --disable-gpu \
    --no-pdf-header-footer \
    --print-to-pdf="$OUTPUT" \
    "file://$ABS_INPUT" >/dev/null 2>&1

if [ ! -f "$OUTPUT" ]; then
    echo "Error: PDF was not generated." >&2
    exit 1
fi

# Trim trailing blank pages with Python + PyPDF2
python3 - "$OUTPUT" << 'PYEOF'
import sys
from pathlib import Path

try:
    from PyPDF2 import PdfReader, PdfWriter
except ImportError:
    # PyPDF2 not installed; skip trimming
    print("Note: PyPDF2 not installed, skipping blank-page trim.", file=sys.stderr)
    sys.exit(0)

pdf_path = Path(sys.argv[1])
reader = PdfReader(str(pdf_path))

def page_is_blank(page) -> bool:
    """Heuristic: a page is blank if it contains no text and no images."""
    try:
        text = page.extract_text() or ""
    except Exception:
        text = ""
    if text.strip():
        return False
    # Check for images / xobjects
    resources = page.get("/Resources")
    if resources:
        xobj = resources.get("/XObject")
        if xobj:
            return False
    return True

# Determine the last non-blank page
last_kept = len(reader.pages) - 1
while last_kept > 0 and page_is_blank(reader.pages[last_kept]):
    last_kept -= 1

if last_kept < len(reader.pages) - 1:
    writer = PdfWriter()
    for i in range(last_kept + 1):
        writer.add_page(reader.pages[i])
    with open(pdf_path, "wb") as f:
        writer.write(f)
    trimmed = len(reader.pages) - (last_kept + 1)
    print(f"Trimmed {trimmed} trailing blank page(s).", file=sys.stderr)
PYEOF

echo "Wrote $OUTPUT"
