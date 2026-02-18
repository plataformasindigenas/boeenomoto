#!/bin/bash
# Build the Boe Eno Moto site
# Converts source data to JSON with aptoro, then renders HTML with kodudo

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=== Boe Eno Moto Build ==="
echo ""

echo "Step 1: Checking encyclopedia entries"
python scripts/check_encyclopedia_entries.py
echo ""

echo "Step 2: Converting source data to JSON with aptoro"
python scripts/convert.py
echo ""

echo "Step 3: Rendering HTML pages with kodudo (i18n)"
python scripts/build_site.py
echo ""

echo "=== Build Complete ==="
echo ""
echo "Open docs/index.html in your browser to preview the site."
