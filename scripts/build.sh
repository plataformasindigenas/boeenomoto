#!/bin/bash
# Build the site into docs/ (git-ignored), exactly as CI does.
# Sources: data/ (tables, Markdown, BibTeX), static/ (images, audio: copied
# verbatim into the site root), terradoc.yaml, locales/, config/.
set -euo pipefail
cd "$(dirname "$0")/.."
terradoc build --config terradoc.yaml --out docs --bundle-dir .terradoc/bundle --clean "$@"
echo ""
echo "Open docs/index.html in your browser to preview the site."
