#!/usr/bin/env python3
"""
One-time migration script for encyclopedia entries.

Renames front matter fields:
  headword → title
  summary → abstract
  updated_at → date
  keywords → categories

Adds new fields with defaults:
  entry_type, infobox, references, see_also

Normalizes file IDs: replaces spaces with hyphens, lowercases.
Renames files accordingly.

Usage:
    python scripts/migrate_encyclopedia.py
"""

from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
ENTRIES_DIR = BASE_DIR / "data" / "encyclopedia"

FIELD_RENAMES = {
    "headword": "title",
    "summary": "abstract",
    "updated_at": "date",
    "keywords": "categories",
}

NEW_DEFAULTS = {
    "entry_type": "",
    "infobox": {},
    "references": [],
    "see_also": [],
}

# Desired field order for the front matter output
FIELD_ORDER = [
    "id",
    "title",
    "variants",
    "abstract",
    "categories",
    "date",
    "url",
    "images",
    "examples",
    "dictionary_ids",
    "fauna_ids",
    "entry_type",
    "infobox",
    "references",
    "see_also",
]


def _parse_front_matter(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise ValueError(f"{path}: missing front matter start (---)")

    parts = raw.split("\n---\n", 1)
    if len(parts) != 2:
        raise ValueError(f"{path}: missing front matter end (---)")

    front_matter = yaml.safe_load(parts[0][4:]) or {}
    if not isinstance(front_matter, dict):
        raise ValueError(f"{path}: front matter must be a mapping")

    body = parts[1]
    return front_matter, body


def _normalize_id(entry_id: str) -> str:
    return entry_id.strip().lower().replace(" ", "-")


def _write_entry(path: Path, front_matter: dict, body: str) -> None:
    # Write front matter in desired field order
    ordered = {}
    for key in FIELD_ORDER:
        if key in front_matter:
            ordered[key] = front_matter[key]
    # Add any remaining keys not in FIELD_ORDER
    for key in front_matter:
        if key not in ordered:
            ordered[key] = front_matter[key]

    fm_str = yaml.dump(
        ordered,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
    )
    path.write_text(f"---\n{fm_str}---\n{body}", encoding="utf-8")


def main():
    if not ENTRIES_DIR.exists():
        print(f"Missing encyclopedia directory: {ENTRIES_DIR}")
        return 1

    md_files = sorted(p for p in ENTRIES_DIR.rglob("*.md") if p.name != "README.md")
    print(f"Found {len(md_files)} entries to migrate\n")

    renamed_files = []
    migrated = 0

    for path in md_files:
        try:
            front_matter, body = _parse_front_matter(path)
        except Exception as exc:
            print(f"  SKIP {path.name}: {exc}")
            continue

        # Rename fields
        for old_name, new_name in FIELD_RENAMES.items():
            if old_name in front_matter:
                front_matter[new_name] = front_matter.pop(old_name)

        # Add new fields with defaults (only if not already present)
        for field, default in NEW_DEFAULTS.items():
            if field not in front_matter:
                front_matter[field] = default

        # Normalize ID
        old_id = front_matter.get("id", "")
        new_id = _normalize_id(old_id)
        if new_id != old_id:
            print(f"  ID: '{old_id}' → '{new_id}'")
            front_matter["id"] = new_id

        # Write updated content
        _write_entry(path, front_matter, body)

        # Rename file if needed
        expected_name = f"{new_id}.md"
        if path.name != expected_name:
            new_path = path.parent / expected_name
            if new_path.exists() and new_path != path:
                print(f"  WARNING: target file already exists: {new_path}")
            else:
                path.rename(new_path)
                renamed_files.append((path.name, expected_name))
                print(f"  FILE: '{path.name}' → '{expected_name}'")

        migrated += 1

    print(f"\nMigrated {migrated} entries")
    if renamed_files:
        print(f"Renamed {len(renamed_files)} files:")
        for old, new in renamed_files:
            print(f"  {old} → {new}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
