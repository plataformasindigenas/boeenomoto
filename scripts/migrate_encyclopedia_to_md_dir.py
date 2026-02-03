#!/usr/bin/env python3
"""
Split data/encyclopedia.yaml into per-entry markdown files with YAML front matter.

Usage:
    python scripts/migrate_encyclopedia_to_md_dir.py
"""

from __future__ import annotations

from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
SOURCE_FILE = DATA_DIR / "encyclopedia.yaml"
TARGET_DIR = DATA_DIR / "encyclopedia"


def _front_matter(entry: dict) -> str:
    keys = [
        "id",
        "headword",
        "variants",
        "summary",
        "keywords",
        "updated_at",
        "url",
        "images",
        "examples",
    ]
    fm = {k: entry.get(k) for k in keys if k in entry}
    return yaml.safe_dump(fm, allow_unicode=True, sort_keys=False).strip()


def main() -> None:
    if not SOURCE_FILE.exists():
        raise FileNotFoundError(f"Missing source file: {SOURCE_FILE}")

    TARGET_DIR.mkdir(parents=True, exist_ok=True)
    existing = list(TARGET_DIR.rglob("*.md"))
    if existing:
        raise RuntimeError(f"Target directory already has markdown files: {TARGET_DIR}")

    entries = yaml.safe_load(SOURCE_FILE.read_text(encoding="utf-8"))
    if not isinstance(entries, list):
        raise ValueError("encyclopedia.yaml must be a list of entries")

    for entry in entries:
        entry_id = entry.get("id")
        if not entry_id:
            raise ValueError("Entry missing id")
        content_md = (entry.get("content_md") or "").strip()

        fm = _front_matter(entry)
        text = f"---\n{fm}\n---\n\n{content_md}\n"
        (TARGET_DIR / f"{entry_id}.md").write_text(text, encoding="utf-8")

    print(f"Wrote {len(entries)} markdown files to {TARGET_DIR}")


if __name__ == "__main__":
    main()
