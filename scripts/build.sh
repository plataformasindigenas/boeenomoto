#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_DIR"
echo "=== Boe Eno Moto Build ==="
echo ""
# docs/ is the build output, gitignored and absent on fresh clones.
# terradoc's copy_data_to_docs writes into docs/ before any step that
# would mkdir it, so we create it here.
mkdir -p docs
terradoc build --config terradoc.yaml
echo ""
echo "Open docs/index.html in your browser to preview the site."
