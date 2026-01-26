#!/bin/bash
# Build the Boe Eno Moto site
# Converts source data to JSON with aptoro, then renders HTML with kodudo

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=== Boe Eno Moto Build ==="
echo ""

echo "Step 1: Converting source data to JSON with aptoro"
python scripts/convert.py
echo ""

echo "Step 2: Rendering HTML pages with kodudo"
kodudo cook config/dictionary.yaml
kodudo cook config/encyclopedia.yaml
kodudo cook config/fauna.yaml
kodudo cook config/index.yaml
echo ""

echo "=== Build Complete ==="
echo ""
echo "Open docs/index.html in your browser to preview the site."
