#!/usr/bin/env python3
"""
Validate encyclopedia markdown entries in data/encyclopedia/.

Usage:
    python scripts/check_encyclopedia_entries.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
ENTRIES_DIR = DATA_DIR / "encyclopedia"

HTML_TAG_RE = re.compile(r"<\s*[a-zA-Z][^>]*>")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_front_matter(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise ValueError("missing front matter start (---)")

    parts = raw.split("\n---\n", 1)
    if len(parts) != 2:
        raise ValueError("missing front matter end (---)")

    front_matter = yaml.safe_load(parts[0][4:]) or {}
    if not isinstance(front_matter, dict):
        raise ValueError("front matter must be a mapping")

    body = parts[1].lstrip("\n")
    return front_matter, body


def main() -> int:
    if not ENTRIES_DIR.exists():
        print(f"Missing encyclopedia directory: {ENTRIES_DIR}", file=sys.stderr)
        return 1

    md_files = sorted(ENTRIES_DIR.rglob("*.md"))
    if not md_files:
        print(f"No markdown entries found in {ENTRIES_DIR}", file=sys.stderr)
        return 1

    errors: list[str] = []
    seen_ids: set[str] = set()

    for path in md_files:
        if path.name == "README.md":
            continue

        try:
            front_matter, body = _parse_front_matter(path)
        except Exception as exc:
            errors.append(f"{path}: {exc}")
            continue

        entry_id = front_matter.get("id")
        headword = front_matter.get("headword")
        if not entry_id:
            errors.append(f"{path}: missing 'id'")
        if not headword:
            errors.append(f"{path}: missing 'headword'")

        if entry_id in seen_ids:
            errors.append(f"{path}: duplicate id '{entry_id}'")
        if entry_id:
            seen_ids.add(entry_id)

        updated_at = front_matter.get("updated_at")
        if updated_at and not DATE_RE.match(str(updated_at)):
            errors.append(f"{path}: updated_at must be YYYY-MM-DD")

        for key in ("variants", "keywords", "images", "examples"):
            val = front_matter.get(key)
            if val is not None and not isinstance(val, list):
                errors.append(f"{path}: '{key}' must be a list")

        if HTML_TAG_RE.search(body):
            errors.append(f"{path}: HTML tags found in body (not allowed)")

    if errors:
        print("Encyclopedia entry check failed:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1

    print(f"Checked {len(md_files) - 1} entries: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
