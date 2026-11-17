#!/usr/bin/env python3
"""Write data/audio/manifest.tsv: which dictionary entry each recording belongs to.

Until now a recording was matched to entries by its filename (the headword's slug), so
homonyms shared recordings and editing a headword lost its audio. The manifest fixes the
match by entry id. This script writes the first version from the current state:

- a file whose slug matches one entry goes to that entry;
- a file whose slug matches several entries goes to the ones that data/audio/_planned.tsv
  (the source dictionary's audio columns) gives a recording, or the one whose planned
  source file has the recording's name, when that narrows it down to one; otherwise it
  stays with all of them, as before, and is listed in _manifest_review.tsv.

Speakers are ids (s01, s02, ...), never names: the sites name nobody for now (2026-11-17).
The filename suffix decides the id; a file without a suffix, or `__unknown`, has none.
Consent: approved, under the communities' general approval recorded by the coordinator
(2026-11-17).

After this first run, edit manifest.tsv by hand (add a row per new recording).

Usage: python scripts/build_audio_manifest.py
"""
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

from terradoc.cross_linker import _slugify

BASE = Path(__file__).resolve().parent.parent
AUDIO = BASE / "data" / "audio"


def main() -> None:
    manifest = AUDIO / "manifest.tsv"
    if manifest.exists():
        sys.exit(f"{manifest} exists; edit it by hand")
    with (BASE / "data" / "dictionary.tsv").open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    by_slug = defaultdict(list)
    for r in rows:
        by_slug[_slugify(r["entry"])].append(r)
    planned = defaultdict(set)
    with (AUDIO / "_planned.tsv").open(encoding="utf-8") as f:
        for p in csv.DictReader(f, delimiter="\t"):
            planned[p["dictionary_id"]].add(p["source_filename"])

    files = sorted(p.name for p in AUDIO.glob("*.webm"))
    names = sorted({re.sub(r"\d+$", "", f[:-5].partition("__")[2]) for f in files} - {"", "unknown"})
    speaker_id = {name: f"s{i:02d}" for i, name in enumerate(names, start=1)}

    out, review = [], []
    for name in files:
        slug, _, variant = name[:-5].partition("__")
        hits = by_slug.get(slug, [])
        if not hits:
            sys.exit(f"{name}: no entry has the slug {slug!r}; add its row by hand")
        chosen = hits
        if len(hits) > 1:
            with_plan = [h for h in hits if planned.get(h["id"])]
            same_name = [h for h in hits
                         if any(_slugify(Path(src).stem) == slug for src in planned.get(h["id"], ()))]
            if len(with_plan) == 1:
                chosen = with_plan
            elif len(same_name) == 1:
                chosen = same_name
            else:
                review.append((name, " ".join(h["id"] for h in hits),
                               " | ".join(f"{h['id']} {h['entry']}: {h['definition'][:40]}" for h in hits)))
        speaker = speaker_id.get(re.sub(r"\d+$", "", variant), "")
        out += [(name, h["id"], speaker, "approved") for h in chosen]

    with manifest.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["file", "entry_id", "speaker", "consent"])
        w.writerows(out)
    with (AUDIO / "_manifest_review.tsv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["file", "entry_ids", "entries"])
        w.writerows(review)
    print(f"{len(files)} files, {len(out)} rows; {len(review)} files serve several entries "
          f"(see _manifest_review.tsv)")


if __name__ == "__main__":
    main()
