#!/usr/bin/env python3
"""Import a new authoritative dictionary CSV and produce data/dictionary.tsv.

Reads the source CSV (path as argument), normalizes it to the project's TSV
schema, and writes two files:

  data/dictionary.tsv          - the dictionary, ready for terradoc build
  data/audio/_planned.tsv      - sidecar listing every audio filename the
                                 source CSV references, keyed by entry id
                                 (and entry slug for convenience)

The `audio` schema field on dictionary entries is intentionally left blank in
the TSV. The CSVReader in aptoro cannot parse a list out of a single cell, and
terradoc's attach_audio_to_dictionary step overwrites this field from the
data/audio/ filesystem anyway. The _planned.tsv sidecar is what later steps
(wanted-list generation, audio import) consult.

Behavior:
  - Rows with no `id` get sequential new ids starting at max(existing id) + 1
  - `áudio` / `áudio2` / `áudio3` are collapsed into the sidecar (deduplicated)
  - `X` / `x` -> marked: true; blank -> marked: false
  - `pos` is left empty when blank in source (schema makes pos optional)
  - 24 entries present only in the previous TSV are dropped (intentional)

Usage:
    python scripts/import_new_dictionary.py <path_to_source_csv>
"""
import csv
import re
import sys
import unicodedata
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DICT_TSV = DATA_DIR / "dictionary.tsv"
AUDIO_PLAN = DATA_DIR / "audio" / "_planned.tsv"

# Output column order (matches schema). 'audio' kept as schema placeholder.
COLUMNS = [
    "id", "entry", "ipa", "pos", "definition", "example_sent",
    "scientific_name", "wiki_link", "pic_link", "comment",
    "audio", "created_at", "marked",
]


def slugify(text: str) -> str:
    """Match terradoc's slugify used for audio file lookups."""
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def parse_int(value: str) -> int | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def main(csv_path: str) -> None:
    src = Path(csv_path)
    if not src.is_file():
        sys.exit(f"Source CSV not found: {src}")

    with src.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    # Assign sequential ids to rows with empty id, continuing past max.
    have_id = [r for r in rows if parse_int(r.get("id", "")) is not None]
    max_id = max(parse_int(r["id"]) for r in have_id) if have_id else 0
    next_id = max_id + 1
    for r in rows:
        if parse_int(r.get("id", "")) is None:
            r["id"] = str(next_id)
            next_id += 1

    # Dedup ids (defensive: source had no duplicate ids at last check).
    seen_ids: set[int] = set()
    deduped = []
    for r in rows:
        rid = parse_int(r["id"])
        if rid in seen_ids:
            print(f"  WARN: duplicate id {rid} for entry {r.get('entry')!r}, skipping")
            continue
        seen_ids.add(rid)
        deduped.append(r)
    rows = deduped

    # Build dictionary TSV rows.
    out_rows = []
    audio_plan_rows = []
    audio_total = 0
    marked_total = 0
    pos_empty = 0

    for r in rows:
        entry = (r.get("entry") or "").strip()
        if not entry:
            continue  # nothing to anchor an entry on
        rid = int(r["id"])

        pos = (r.get("pos") or "").strip()
        if not pos:
            pos_empty += 1

        x_raw = (r.get("X") or "").strip()
        marked = x_raw.lower() == "x"
        if marked:
            marked_total += 1

        audio_files = []
        for col in ("áudio", "áudio2", "áudio3"):
            v = (r.get(col) or "").strip()
            if v and v not in audio_files:
                audio_files.append(v)
        audio_total += len(audio_files)
        slug = slugify(entry)
        for fname in audio_files:
            audio_plan_rows.append({
                "dictionary_id": rid,
                "entry": entry,
                "slug": slug,
                "source_filename": fname,
            })

        out_rows.append({
            "id": rid,
            "entry": entry,
            "ipa": (r.get("ipa") or "").strip(),
            "pos": pos,
            "definition": (r.get("definition") or "").strip(),
            "example_sent": (r.get("example_sent") or "").strip(),
            "scientific_name": (r.get("scientific_name") or "").strip(),
            "wiki_link": (r.get("wiki_link") or "").strip(),
            "pic_link": (r.get("pic_link") or "").strip(),
            "comment": (r.get("comment") or "").strip(),
            "audio": "",  # terradoc populates this; sidecar is source of truth
            "created_at": (r.get("created_at") or "").strip(),
            "marked": "true" if marked else "",
        })

    out_rows.sort(key=lambda r: r["id"])
    audio_plan_rows.sort(key=lambda r: (r["dictionary_id"], r["source_filename"]))

    AUDIO_PLAN.parent.mkdir(parents=True, exist_ok=True)
    with DICT_TSV.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, delimiter="\t",
                           quoting=csv.QUOTE_MINIMAL)
        w.writeheader()
        w.writerows(out_rows)

    with AUDIO_PLAN.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["dictionary_id", "entry", "slug", "source_filename"],
            delimiter="\t",
            quoting=csv.QUOTE_MINIMAL,
        )
        w.writeheader()
        w.writerows(audio_plan_rows)

    print(f"Wrote {len(out_rows)} entries to {DICT_TSV.relative_to(BASE_DIR)}")
    print(f"Wrote {len(audio_plan_rows)} audio refs to {AUDIO_PLAN.relative_to(BASE_DIR)}")
    print(f"  rows with empty pos: {pos_empty}")
    print(f"  rows marked (X):     {marked_total}")
    print(f"  audio refs total:    {audio_total}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: python scripts/import_new_dictionary.py <source.csv>")
    main(sys.argv[1])
