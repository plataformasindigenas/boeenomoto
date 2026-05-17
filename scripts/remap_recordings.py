#!/usr/bin/env python3
"""Translate dictionary_id in recordings.yaml from old to new IDs.

The new dictionary CSV reassigned every id, so the dictionary_id values in
recordings.yaml now point to the wrong entries. This script rewrites them by
looking up each old id's `entry` text in the old dictionary and finding the
matching entry text in the new dictionary.

Outcomes per row:
  - exact-1 match  -> rewrite dictionary_id to the new value
  - 0 matches      -> entry was dropped between versions; null the id and
                      annotate the row so curators see what happened
  - 2+ matches     -> ambiguous; set needs_review=true and add a note
                      listing the candidate new ids

A backup of the original recordings.yaml is written next to it.

Usage:
    python scripts/remap_recordings.py <old_dict.tsv> <new_dict.tsv>
"""
import csv
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
RECORDINGS_YAML = BASE_DIR / "data" / "recordings.yaml"


def load_dict_tsv(path: Path) -> dict[int, str]:
    """Return mapping of id -> entry text from a dictionary TSV."""
    result: dict[int, str] = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            try:
                rid = int(row["id"])
            except (ValueError, KeyError):
                continue
            entry = (row.get("entry") or "").strip()
            if entry:
                result[rid] = entry
    return result


def build_reverse(new_dict: dict[int, str]) -> dict[str, list[int]]:
    """Map entry text -> list of new ids (multiple if duplicates)."""
    rev: dict[str, list[int]] = defaultdict(list)
    for nid, entry in new_dict.items():
        rev[entry].append(nid)
    return dict(rev)


def main(old_path: str, new_path: str) -> None:
    old_dict = load_dict_tsv(Path(old_path))
    new_dict = load_dict_tsv(Path(new_path))
    new_by_entry = build_reverse(new_dict)
    print(f"Old dictionary: {len(old_dict)} entries")
    print(f"New dictionary: {len(new_dict)} entries")

    with RECORDINGS_YAML.open(encoding="utf-8") as f:
        recordings = yaml.safe_load(f) or []

    # Backup
    backup = RECORDINGS_YAML.with_suffix(".yaml.pre-remap.bak")
    shutil.copy2(RECORDINGS_YAML, backup)
    print(f"Backed up to {backup.relative_to(BASE_DIR)}")

    rewritten = 0
    dropped = 0
    ambiguous = 0
    unchanged = 0

    for row in recordings:
        old_id = row.get("dictionary_id")
        if old_id is None:
            unchanged += 1
            continue

        entry = old_dict.get(int(old_id))
        if entry is None:
            # Recording referenced an id that's not in the old dict at all
            # (data drift). Null it out and flag.
            row["dictionary_id"] = None
            row["match_type"] = "remap_orphan"
            row["needs_review"] = True
            note = "remap: old dictionary_id had no entry in pre-migration TSV"
            row["notes"] = _append_note(row.get("notes"), note)
            dropped += 1
            continue

        candidates = new_by_entry.get(entry, [])
        if len(candidates) == 1:
            row["dictionary_id"] = candidates[0]
            # Keep match_type as-is; the remap doesn't change match quality
            rewritten += 1
        elif len(candidates) == 0:
            row["dictionary_id"] = None
            row["match_type"] = "remap_dropped"
            row["needs_review"] = True
            note = f"remap: entry {entry!r} no longer in new dictionary"
            row["notes"] = _append_note(row.get("notes"), note)
            dropped += 1
        else:
            # Ambiguous: multiple new ids share this entry text.
            # Use first candidate but flag for review.
            row["dictionary_id"] = candidates[0]
            row["match_type"] = "remap_ambiguous"
            row["needs_review"] = True
            note = (
                f"remap: entry {entry!r} matches multiple new ids "
                f"({sorted(candidates)}); using {candidates[0]}"
            )
            row["notes"] = _append_note(row.get("notes"), note)
            ambiguous += 1

    with RECORDINGS_YAML.open("w", encoding="utf-8") as f:
        yaml.safe_dump(
            recordings,
            f,
            allow_unicode=True,
            sort_keys=False,
            default_flow_style=False,
        )

    print(f"Rewrote dictionary_id on {rewritten} rows")
    print(f"Dropped/nulled (entry no longer exists): {dropped}")
    print(f"Ambiguous (multiple candidates, flagged): {ambiguous}")
    print(f"Unchanged (no dictionary_id to remap):   {unchanged}")


def _append_note(existing: str | None, addition: str) -> str:
    if existing:
        return f"{existing}; {addition}"
    return addition


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python scripts/remap_recordings.py <old.tsv> <new.tsv>")
    main(sys.argv[1], sys.argv[2])
