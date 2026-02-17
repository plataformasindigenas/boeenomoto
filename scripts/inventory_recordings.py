#!/usr/bin/env python3
"""
Inventory Bororo audio recordings and match them to dictionary entries.

Scans data/recordings/, extracts metadata from paths/filenames, and matches
against dictionary entries. Outputs data/recordings.yaml.

Usage:
    python scripts/inventory_recordings.py
"""

import csv
import re
import sys
from pathlib import Path

import yaml

# Increase CSV field size limit for large fields
csv.field_size_limit(sys.maxsize)

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RECORDINGS_DIR = DATA_DIR / "recordings"

# Directories/files to exclude entirely
EXCLUDED_SESSIONS = {"bor_lex08-benito-IMG_8685-DIRTY", "bor_lex23-fernando03"}
EXCLUDED_FILES = {
    "143959_tiago_tv.webm",
    "174014_FFG_blabla.webm",
    "142654_tiago_computer.webm",
}

# English → Portuguese hints for definition-based matching
ENGLISH_HINTS = {
    "rabbit": ["coelho"],
    "rain": ["chuva"],
    "above": ["acima", "em cima", "sobre"],
    "scrub": ["mato", "cerrado", "arbusto"],
    "wall_of_house": ["parede", "casa"],
    "plant_verb": ["plantar"],
}

# Known speakers (for stripping from filenames)
KNOWN_SPEAKERS = {
    "leonida", "terezinha", "teresinha", "benito", "pedrosa",
    "nazario", "fernando", "valdemar", "elizete", "erotildes",
    "bosco", "jussila", "tiago",
}


def load_dictionary():
    """Load dictionary.tsv and build lookup indices."""
    dict_path = DATA_DIR / "dictionary.tsv"
    entries = []
    with open(dict_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter="\t")
        for row in reader:
            entries.append(row)

    # Build headword index: normalized_headword → [(id, entry, definition)]
    headword_index = {}
    for e in entries:
        entry_text = e.get("entry", "")
        entry_id = int(e["id"])
        definition = e.get("definition", "") or ""

        # Normalize: strip leading -, strip trailing (2) etc., lowercase
        normalized = entry_text.strip()
        normalized = re.sub(r"\s*\(\d+\)\s*$", "", normalized)
        if normalized.startswith("-"):
            normalized = normalized[1:]
        normalized = normalized.lower().strip()

        if normalized:
            headword_index.setdefault(normalized, []).append(
                (entry_id, entry_text, definition)
            )

    return entries, headword_index


def normalize_word(raw_word, speaker=None):
    """Normalize a word extracted from a filename.

    Steps:
    1. Strip speaker prefix (Leonida_ etc.)
    2. Strip numeric suffix (okwa01 → okwa, variant=1)
    3. Strip parenthetical suffix (ako(1) → ako)
    4. Split CamelCase (boeEtugu → boe etugu)
    5. Underscores to spaces
    6. Lowercase everything
    """
    word = raw_word

    # Strip speaker prefix if present (e.g., Leonida_kabi → kabi)
    if speaker and "_" in word:
        # Check if word starts with any known speaker name (case-insensitive)
        for sp in KNOWN_SPEAKERS:
            if word.lower().startswith(sp + "_"):
                word = word[len(sp) + 1:]
                break

    # Detect variant number (trailing digits like okwa01, ao02)
    variant_num = None
    paren_match = re.search(r"\((\d+)\)$", word)
    if paren_match:
        variant_num = int(paren_match.group(1))
        word = word[:paren_match.start()]
    else:
        num_match = re.search(r"(\d+)$", word)
        if num_match:
            variant_num = int(num_match.group(1))
            word = word[:num_match.start()]

    # Split CamelCase: boeEtugu → boe Etugu
    word = re.sub(r"([a-z])([A-Z])", r"\1 \2", word)

    # Underscores to spaces
    word = word.replace("_", " ")

    # Lowercase and clean up whitespace
    word = word.lower().strip()
    word = re.sub(r"\s+", " ", word)

    return word, variant_num


def match_dictionary(normalized_word, headword_index, all_entries):
    """Try to match a normalized word to dictionary entries.

    Returns (dictionary_id, match_type, needs_review, notes).
    """
    # 1. Exact headword match
    if normalized_word in headword_index:
        matches = headword_index[normalized_word]
        if len(matches) == 1:
            return matches[0][0], "exact", False, None
        else:
            # Multiple matches (homonyms)
            candidates = "; ".join(
                f"id={m[0]} ({m[1]}: {m[2][:50]})" for m in matches
            )
            return None, "exact", True, f"Multiple matches: {candidates}"

    # 1b. If word has spaces (from CamelCase split or underscores), try joined form
    if " " in normalized_word:
        joined = normalized_word.replace(" ", "")
        if joined in headword_index:
            matches = headword_index[joined]
            if len(matches) == 1:
                return matches[0][0], "exact", False, None
            else:
                candidates = "; ".join(
                    f"id={m[0]} ({m[1]}: {m[2][:50]})" for m in matches
                )
                return None, "exact", True, f"Multiple matches: {candidates}"

    # 2. Definition search for English/Portuguese labels
    search_terms = [normalized_word]
    if normalized_word in ENGLISH_HINTS:
        search_terms.extend(ENGLISH_HINTS[normalized_word])

    # Only try definition search if the word looks like it could be English/Portuguese
    is_english = normalized_word in ENGLISH_HINTS or re.match(
        r"^[a-z_]+$", normalized_word
    ) and normalized_word in {
        "above", "rain", "rabbit", "scrub", "plant_verb", "wall_of_house",
        "pegar", "porcao",
    }

    if is_english:
        candidates = []
        for e in all_entries:
            definition = (e.get("definition", "") or "").lower()
            entry_text = e.get("entry", "")
            for term in search_terms:
                if term.lower() in definition:
                    candidates.append(
                        (int(e["id"]), entry_text, definition[:80])
                    )
                    break

        if candidates:
            if len(candidates) == 1:
                return (
                    candidates[0][0],
                    "definition_search",
                    True,
                    f"Matched via definition: {candidates[0][1]}",
                )
            else:
                desc = "; ".join(
                    f"id={c[0]} ({c[1]}: {c[2][:50]})" for c in candidates[:5]
                )
                note = f"Definition search candidates: {desc}"
                if len(candidates) > 5:
                    note += f" ... and {len(candidates) - 5} more"
                return None, "definition_search", True, note

    # 3. No match
    return None, "none", True, None


def parse_bor_lex_session(session_dir):
    """Parse a bor_lex## session directory.

    Returns list of recording dicts.
    """
    dirname = session_dir.name
    recordings = []

    # Extract session_id and speaker from directory name
    # Pattern: bor_lex##-speaker-ID or bor_lex##-speaker##
    match = re.match(r"(bor_lex\d+)-(\w+?)(?:-.*|(?:\d+))$", dirname)
    if not match:
        # Try simpler pattern: bor_lex##-speaker##
        match = re.match(r"(bor_lex\d+)-([a-zA-Z]+)\d*$", dirname)
    if not match:
        # Fallback: just extract session and first word
        match = re.match(r"(bor_lex\d+)-([a-zA-Z]+)", dirname)

    if match:
        session_id = match.group(1)
        speaker = match.group(2).lower()
    else:
        session_id = dirname
        speaker = "unknown"

    for audio_file in sorted(session_dir.iterdir()):
        if not audio_file.is_file():
            continue
        if audio_file.suffix.lower() not in (".wav", ".webm"):
            continue

        stem = audio_file.stem
        fmt = audio_file.suffix.lower().lstrip(".")

        # Extract raw word (stripping speaker prefix happens in normalize)
        raw_word = stem

        # Strip speaker prefix from raw_word for storage
        stripped_word = stem
        for sp in KNOWN_SPEAKERS:
            if stem.lower().startswith(sp + "_"):
                stripped_word = stem[len(sp) + 1:]
                break

        normalized, variant_num = normalize_word(stem, speaker)

        rel_path = audio_file.relative_to(RECORDINGS_DIR)

        recordings.append({
            "file_path": str(rel_path),
            "format": fmt,
            "speaker": speaker,
            "session_id": session_id,
            "recording_date": None,
            "recording_time": None,
            "location": None,
            "raw_word": stripped_word,
            "normalized_word": normalized,
            "variant_num": variant_num,
        })

    return recordings


def parse_webm_location(location_dir):
    """Parse a location-based directory (Taradrimana, field, fieldwork2026).

    Pattern: Location/YYYY-MM-DD/HHMMSS_Speaker_word.webm
    """
    recordings = []
    location = location_dir.name

    for date_dir in sorted(location_dir.iterdir()):
        if not date_dir.is_dir():
            continue

        # Check if it's a date directory or nested structure
        if re.match(r"\d{4}-\d{2}-\d{2}$", date_dir.name):
            recordings.extend(
                _parse_date_dir(date_dir, location, date_dir.name)
            )
        else:
            # Nested structure like fieldwork2026/field/YYYY-MM-DD/
            for subdir in sorted(date_dir.iterdir()):
                if subdir.is_dir():
                    if re.match(r"\d{4}-\d{2}-\d{2}$", subdir.name):
                        recordings.extend(
                            _parse_date_dir(subdir, location, subdir.name)
                        )

    return recordings


def _parse_date_dir(date_dir, location, recording_date):
    """Parse a single date directory for webm files."""
    recordings = []

    for audio_file in sorted(date_dir.iterdir()):
        if not audio_file.is_file():
            continue
        if audio_file.suffix.lower() not in (".wav", ".webm"):
            continue
        if audio_file.name in EXCLUDED_FILES:
            continue

        stem = audio_file.stem
        fmt = audio_file.suffix.lower().lstrip(".")

        # Pattern: HHMMSS_Speaker_word
        match = re.match(r"(\d{6})_(\w+?)_(.*)", stem)
        if match:
            recording_time = match.group(1)
            # Format as HH:MM:SS
            recording_time = f"{recording_time[:2]}:{recording_time[2:4]}:{recording_time[4:6]}"
            speaker = match.group(2).lower()
            raw_word = match.group(3)
        else:
            recording_time = None
            speaker = "unknown"
            raw_word = stem

        # Handle Jussila special case: strip tore_boudo prefix
        notes = None
        if speaker == "jussila" and raw_word.startswith("tore_boudo_"):
            notes = "Full name: Jussila Tore Boudo"
            raw_word = raw_word[len("tore_boudo_"):]

        # For webm files, underscores → spaces is handled in normalize
        normalized, variant_num = normalize_word(raw_word)

        rel_path = audio_file.relative_to(RECORDINGS_DIR)

        recordings.append({
            "file_path": str(rel_path),
            "format": fmt,
            "speaker": speaker,
            "session_id": None,
            "recording_date": recording_date,
            "recording_time": recording_time,
            "location": location,
            "raw_word": raw_word,
            "normalized_word": normalized,
            "variant_num": variant_num,
            "_notes": notes,
        })

    return recordings


def inventory_recordings():
    """Main inventory function. Returns list of recording dicts."""
    all_recordings = []

    for item in sorted(RECORDINGS_DIR.iterdir()):
        if not item.is_dir():
            continue

        if item.name in EXCLUDED_SESSIONS:
            print(f"  Skipping excluded session: {item.name}")
            continue

        if item.name.startswith("bor_lex"):
            all_recordings.extend(parse_bor_lex_session(item))
        else:
            # Location-based directory (Taradrimana, field, fieldwork2026)
            all_recordings.extend(parse_webm_location(item))

    return all_recordings


def main():
    print("=== Bororo Recordings Inventory ===\n")

    # Load dictionary
    print("Loading dictionary...")
    all_entries, headword_index = load_dictionary()
    print(f"  {len(all_entries)} dictionary entries loaded")
    print(f"  {len(headword_index)} unique headwords indexed\n")

    # Scan recordings
    print("Scanning recordings directory...")
    recordings = inventory_recordings()
    print(f"  {len(recordings)} recordings found\n")

    # Match against dictionary
    print("Matching recordings to dictionary entries...")
    stats = {"exact": 0, "definition_search": 0, "none": 0, "needs_review": 0}

    output_records = []
    for i, rec in enumerate(recordings, start=1):
        dict_id, match_type, needs_review, notes = match_dictionary(
            rec["normalized_word"], headword_index, all_entries
        )

        # Merge any pre-existing notes (e.g. Jussila)
        existing_notes = rec.pop("_notes", None)
        if existing_notes and notes:
            notes = f"{existing_notes}; {notes}"
        elif existing_notes:
            notes = existing_notes

        record = {
            "id": i,
            "file_path": rec["file_path"],
            "format": rec["format"],
            "speaker": rec["speaker"],
            "session_id": rec["session_id"],
            "recording_date": rec["recording_date"],
            "recording_time": rec["recording_time"],
            "location": rec["location"],
            "raw_word": rec["raw_word"],
            "normalized_word": rec["normalized_word"],
            "variant_num": rec["variant_num"],
            "dictionary_id": dict_id,
            "match_type": match_type,
            "needs_review": needs_review,
            "notes": notes,
        }
        output_records.append(record)

        stats[match_type] += 1
        if needs_review:
            stats["needs_review"] += 1

    # Print statistics
    print(f"\n=== Match Statistics ===")
    print(f"  Exact matches:       {stats['exact']}")
    print(f"  Definition search:   {stats['definition_search']}")
    print(f"  No match:            {stats['none']}")
    print(f"  Needs review:        {stats['needs_review']}")
    print(f"  Total:               {len(output_records)}")

    # Write output
    output_path = DATA_DIR / "recordings.yaml"
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(
            output_records,
            f,
            default_flow_style=False,
            allow_unicode=True,
            sort_keys=False,
        )

    print(f"\nOutput written to {output_path}")

    # Show some unmatched examples
    unmatched = [r for r in output_records if r["match_type"] == "none"]
    if unmatched:
        print(f"\nSample unmatched words (first 15):")
        for r in unmatched[:15]:
            print(f"  {r['normalized_word']:30s} ← {r['file_path']}")


if __name__ == "__main__":
    main()
