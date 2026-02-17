#!/usr/bin/env python3
"""
Convert WAV recordings to WebM (Opus), flatten all audio into docs/recordings/,
and update recordings.yaml with new paths/formats.

Usage:
    python scripts/convert_audio.py
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"
RECORDINGS_SRC = DATA_DIR / "recordings"
RECORDINGS_DST = DOCS_DIR / "recordings"
RECORDINGS_YAML = DATA_DIR / "recordings.yaml"


def safe_filename(word: str) -> str:
    """Sanitize a word for use in a filename."""
    name = word.replace(" ", "_")
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    return name.lower()


def build_dest_filename(entry: dict) -> str:
    """Build flat destination filename: {id:04d}_{speaker}_{word}.webm"""
    entry_id = entry["id"]
    speaker = entry["speaker"]
    word = safe_filename(entry.get("normalized_word") or entry.get("raw_word", "unknown"))
    return f"{entry_id:04d}_{speaker}_{word}.webm"


def convert_wav_to_webm(src: Path, dst: Path) -> bool:
    """Convert a WAV file to WebM with Opus codec. Returns True on success."""
    result = subprocess.run(
        [
            "ffmpeg", "-y", "-i", str(src),
            "-c:a", "libopus", "-b:a", "48k",
            str(dst),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"  ERROR converting {src.name}: {result.stderr[:200]}")
        return False
    return True


def main():
    print("=== Audio Conversion & Flattening ===\n")

    # Load recordings
    if not RECORDINGS_YAML.exists():
        print(f"ERROR: {RECORDINGS_YAML} not found")
        sys.exit(1)

    with open(RECORDINGS_YAML, "r", encoding="utf-8") as f:
        entries = yaml.safe_load(f) or []

    print(f"Loaded {len(entries)} recording entries from recordings.yaml")

    # Remove symlink if it exists, then create real directory
    if RECORDINGS_DST.is_symlink():
        RECORDINGS_DST.unlink()
        print(f"Removed symlink: {RECORDINGS_DST}")
    RECORDINGS_DST.mkdir(parents=True, exist_ok=True)

    converted = 0
    copied = 0
    errors = 0

    for entry in entries:
        src = RECORDINGS_SRC / entry["file_path"]
        dest_name = build_dest_filename(entry)
        dst = RECORDINGS_DST / dest_name

        if not src.exists():
            print(f"  MISSING: {src}")
            errors += 1
            continue

        fmt = entry["format"]
        if fmt == "wav":
            if convert_wav_to_webm(src, dst):
                converted += 1
            else:
                errors += 1
                continue
        elif fmt == "webm":
            shutil.copy2(src, dst)
            copied += 1
        else:
            print(f"  UNKNOWN format '{fmt}' for id={entry['id']}")
            errors += 1
            continue

        # Update entry
        entry["file_path"] = dest_name
        entry["format"] = "webm"

        if (converted + copied) % 50 == 0:
            print(f"  Progress: {converted + copied}/{len(entries)} ...")

    print(f"\nDone: {converted} converted, {copied} copied, {errors} errors")
    print(f"Total output files: {converted + copied}")

    if errors > 0:
        print(f"\nWARNING: {errors} errors occurred. Not updating recordings.yaml.")
        sys.exit(1)

    # Write updated recordings.yaml
    with open(RECORDINGS_YAML, "w", encoding="utf-8") as f:
        yaml.dump(entries, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"Updated {RECORDINGS_YAML}")

    # Clean up source recordings directory
    shutil.rmtree(RECORDINGS_SRC)
    print(f"Removed source directory: {RECORDINGS_SRC}")

    print("\n=== Conversion Complete ===")


if __name__ == "__main__":
    main()
