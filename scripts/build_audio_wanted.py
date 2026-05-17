#!/usr/bin/env python3
"""Generate data/audio/_wanted.tsv from _planned.tsv minus what's on disk.

A row in _planned.tsv is "covered" if either:
  - <slug>.webm or <slug>__*.webm exists in data/audio/, or
  - the original source_filename exists in data/audio/ (unconverted case)

Anything not covered is written to _wanted.tsv as the shopping list.

Usage:
    python scripts/build_audio_wanted.py
"""
import csv
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
AUDIO_DIR = BASE_DIR / "data" / "audio"
PLAN = AUDIO_DIR / "_planned.tsv"
WANTED = AUDIO_DIR / "_wanted.tsv"


def main() -> None:
    existing = {
        p.name for p in AUDIO_DIR.iterdir()
        if p.is_file() and p.suffix in (".webm", ".wav")
    }
    wanted_rows = []
    covered = 0
    with PLAN.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            slug = row["slug"]
            present = (
                row["source_filename"] in existing
                or any(
                    n == f"{slug}.webm" or n.startswith(f"{slug}__")
                    for n in existing
                )
            )
            if present:
                covered += 1
            else:
                wanted_rows.append(row)

    with WANTED.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["dictionary_id", "entry", "slug", "source_filename"],
            delimiter="\t",
            quoting=csv.QUOTE_MINIMAL,
        )
        w.writeheader()
        w.writerows(wanted_rows)

    print(f"Covered (already in data/audio/): {covered}")
    print(f"Wanted (not yet delivered):       {len(wanted_rows)}")
    print(f"Written to {WANTED.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
