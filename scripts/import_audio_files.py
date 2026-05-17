#!/usr/bin/env python3
"""Import a batch of audio files into data/audio/ under slug convention.

Consults data/audio/_planned.tsv (produced by import_new_dictionary.py) to
know which source filename belongs to which dictionary entry. Each delivered
file is converted to .webm (Opus 48k) if needed and placed at
data/audio/<slug>.webm. Homophones that share a source file get __2, __3
suffixes so each entry has its own playable file.

The terradoc cross_linker auto-attaches anything in data/audio/ matching
<slug>.webm or <slug>__*.webm to the corresponding dictionary entry.

Files in the source dir whose names appear in _planned.tsv are imported;
unrecognized filenames are listed but not copied. The import is idempotent:
re-running it skips files that already exist at the destination.

Usage:
    python scripts/import_audio_files.py <source_dir>
"""
import csv
import shutil
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
AUDIO_DIR = BASE_DIR / "data" / "audio"
PLAN = AUDIO_DIR / "_planned.tsv"


def load_plan() -> dict[str, list[tuple[int, str]]]:
    """source_filename -> [(dictionary_id, slug), ...]."""
    plan: dict[str, list[tuple[int, str]]] = defaultdict(list)
    if not PLAN.is_file():
        sys.exit(f"Plan not found: {PLAN}. Run import_new_dictionary.py first.")
    with PLAN.open(encoding="utf-8") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            try:
                rid = int(row["dictionary_id"])
            except (ValueError, KeyError):
                continue
            slug = row["slug"]
            fname = row["source_filename"]
            plan[fname].append((rid, slug))
    return dict(plan)


def convert_to_webm(src: Path, dst: Path) -> None:
    """ffmpeg encode to webm/opus at 48k, mono."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(src),
        "-c:a", "libopus", "-b:a", "48k", "-ac", "1",
        str(dst),
    ]
    subprocess.run(cmd, check=True)


def next_variant_path(slug: str) -> Path:
    """Return the next free path for a slug: slug.webm, slug__2.webm, ..."""
    base = AUDIO_DIR / f"{slug}.webm"
    if not base.exists():
        return base
    i = 2
    while True:
        p = AUDIO_DIR / f"{slug}__{i}.webm"
        if not p.exists():
            return p
        i += 1


def main(source_dir: str) -> None:
    src_dir = Path(source_dir)
    if not src_dir.is_dir():
        sys.exit(f"Source directory not found: {src_dir}")

    plan = load_plan()
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)

    imported = 0
    skipped_existing = 0
    unrecognized = []

    # For each file the source delivered, look it up in the plan.
    for src_file in sorted(src_dir.iterdir()):
        if not src_file.is_file():
            continue
        if src_file.name not in plan:
            unrecognized.append(src_file.name)
            continue

        targets = plan[src_file.name]
        # Multiple entries may share one source filename (homophones).
        # First entry takes <slug>.webm; later ones take __N variants under
        # their own slug.
        for rid, slug in targets:
            dst = next_variant_path(slug)
            if dst.exists():
                skipped_existing += 1
                continue
            try:
                if src_file.suffix.lower() == ".webm":
                    shutil.copy2(src_file, dst)
                else:
                    convert_to_webm(src_file, dst)
                imported += 1
                print(f"  {src_file.name} -> {dst.relative_to(BASE_DIR)} (id={rid})")
            except subprocess.CalledProcessError as e:
                print(f"  FAIL {src_file.name}: ffmpeg returned {e.returncode}")

    print()
    print(f"Imported: {imported}")
    print(f"Skipped (already present): {skipped_existing}")
    if unrecognized:
        print(f"Unrecognized filenames (not in _planned.tsv): {len(unrecognized)}")
        for name in unrecognized[:20]:
            print(f"  {name}")
        if len(unrecognized) > 20:
            print(f"  ... and {len(unrecognized) - 20} more")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/import_audio_files.py <source_dir>")
    main(sys.argv[1])
