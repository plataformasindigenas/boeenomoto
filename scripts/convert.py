#!/usr/bin/env python3
"""
Convert Bororo data files to JSON using aptoro.

This script validates all source data files against their schemas
and generates JSON files for use with kodudo templates.

Usage:
    python scripts/convert.py
"""

import csv
import html as html_lib
import json
import re
import sys
from dataclasses import asdict, is_dataclass
from html.parser import HTMLParser
from pathlib import Path

import aptoro
from bibtexparser import bparser
import yaml
from markdown_it import MarkdownIt
from mdit_py_plugins.footnote import footnote_plugin

# Increase CSV field size limit for large fields
csv.field_size_limit(sys.maxsize)

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"


def convert_dictionary():
    """Convert dictionary TSV to JSON."""
    print("=== Converting Dictionary ===")

    schema = aptoro.load_schema(str(DATA_DIR / "dictionary_schema.yaml"))
    data = aptoro.read(str(DATA_DIR / "dictionary.tsv"), format="csv", delimiter="\t")

    print(f"  Validating {len(data)} entries...")
    try:
        records = aptoro.validate(data, schema, collect_errors=True)
    except aptoro.ValidationError as e:
        print(f"  Validation errors: {len(e.errors)}")
        for error in e.errors[:10]:
            print(f"    {error}")
        if len(e.errors) > 10:
            print(f"    ... and {len(e.errors) - 10} more errors")
        raise

    normalized_records = []
    for record in records:
        entry = asdict(record) if is_dataclass(record) else dict(record)
        normalized_records.append(entry)

    output_data = {
        "meta": {
            "name": "bororo_dictionary",
            "description": "Bororo Dictionary Entries",
            "version": "1.0",
            "record_count": len(normalized_records),
        },
        "data": normalized_records,
    }

    output_file = DATA_DIR / "dictionary.json"
    output_file.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  Exported {len(normalized_records)} entries to {output_file}")
    return len(normalized_records)


def convert_fauna():
    """Convert fauna YAML to JSON."""
    print("=== Converting Fauna ===")

    schema = aptoro.load_schema(str(DATA_DIR / "fauna_schema.yaml"))
    data = aptoro.read(str(DATA_DIR / "fauna.yaml"), format="yaml")

    print(f"  Validating {len(data)} entries...")
    try:
        records = aptoro.validate(data, schema, collect_errors=True)
    except aptoro.ValidationError as e:
        print(f"  Validation errors: {len(e.errors)}")
        for error in e.errors[:10]:
            print(f"    {error}")
        if len(e.errors) > 10:
            print(f"    ... and {len(e.errors) - 10} more errors")
        raise

    normalized_records = []
    for record in records:
        entry = asdict(record) if is_dataclass(record) else dict(record)
        normalized_records.append(entry)

    output_data = {
        "meta": {
            "name": "bororo_fauna",
            "description": "Bororo Fauna Dictionary",
            "version": "1.0",
            "record_count": len(normalized_records),
        },
        "data": normalized_records,
    }

    output_file = DATA_DIR / "fauna.json"
    output_file.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  Exported {len(normalized_records)} entries to {output_file}")
    return len(normalized_records)


def convert_bibliography():
    """Convert bibliography BibTeX to JSON."""
    print("=== Converting Bibliography ===")

    bib_file = DATA_DIR / "bororo.bib"
    if not bib_file.exists():
        print(f"  BibTeX file not found: {bib_file}")
        return 0

    with open(bib_file, "r", encoding="utf-8") as f:
        bib_database = bparser.parse(f.read())

    schema = aptoro.load_schema(str(DATA_DIR / "bibliography_schema.yaml"))

    data = []
    for entry in bib_database.entries:
        record = {"id": entry.get("ID", "")}
        bibtex_type = entry.get("ENTRYTYPE", "misc")
        if bibtex_type.startswith("@"):
            bibtex_type = bibtex_type[1:]
        record["type"] = bibtex_type

        field_mapping = {
            "author": "author",
            "title": "title",
            "year": "year",
            "journal": "journal",
            "volume": "volume",
            "number": "number",
            "pages": "pages",
            "doi": "doi",
            "url": "url",
            "publisher": "publisher",
            "address": "address",
            "school": "school",
            "note": "note",
            "editor": "editor",
            "booktitle": "booktitle",
        }

        for bib_field, schema_field in field_mapping.items():
            if bib_field in entry:
                record[schema_field] = entry[bib_field]

        data.append(record)

    print(f"  Validating {len(data)} entries...")
    try:
        records = aptoro.validate(data, schema, collect_errors=True)
    except aptoro.ValidationError as e:
        print(f"  Validation errors: {len(e.errors)}")
        for error in e.errors[:10]:
            print(f"    {error}")
        if len(e.errors) > 10:
            print(f"    ... and {len(e.errors) - 10} more errors")
        raise

    normalized_records = []
    for record in records:
        entry = asdict(record) if is_dataclass(record) else dict(record)
        normalized_records.append(entry)

    output_data = {
        "meta": {
            "name": "bororo_bibliography",
            "description": "Bororo Bibliography References",
            "version": "1.0",
            "record_count": len(normalized_records),
        },
        "data": normalized_records,
    }

    output_file = DATA_DIR / "bibliography.json"
    output_file.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  Exported {len(normalized_records)} entries to {output_file}")
    return len(normalized_records)


HTML_TAG_RE = re.compile(r"<\s*[a-zA-Z][^>]*>")


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {
            "p",
            "br",
            "hr",
            "li",
            "tr",
            "th",
            "td",
            "h1",
            "h2",
            "h3",
            "h4",
            "h5",
            "h6",
        }:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"p", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6"}:
            self.parts.append("\n")

    def get_text(self) -> str:
        text = html_lib.unescape("".join(self.parts))
        return re.sub(r"\\s+", " ", text).strip()


def _build_markdown_renderer() -> MarkdownIt:
    md = MarkdownIt("gfm-like", {"html": False, "linkify": False})
    md.use(footnote_plugin)
    return md


def _assert_no_html(content_md: str, entry_id: str) -> None:
    if content_md and HTML_TAG_RE.search(content_md):
        raise ValueError(
            f"Entry {entry_id}: content_md contains HTML tags; use markdown only"
        )


def _html_to_text(html: str) -> str:
    if not html:
        return ""
    parser = _TextExtractor()
    parser.feed(html)
    return parser.get_text()


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

    body = parts[1].lstrip("\n")
    return front_matter, body


def _load_encyclopedia_entries() -> list[dict]:
    entries_dir = DATA_DIR / "encyclopedia"
    if not entries_dir.exists():
        raise FileNotFoundError(f"Missing encyclopedia directory: {entries_dir}")

    md_files = sorted(p for p in entries_dir.rglob("*.md") if p.name != "README.md")
    if not md_files:
        raise FileNotFoundError(f"No markdown entries found in {entries_dir}")

    entries: list[dict] = []
    seen_ids: set[str] = set()

    for path in md_files:
        front_matter, body = _parse_front_matter(path)
        entry = dict(front_matter)
        entry_id = entry.get("id")
        if not entry_id:
            raise ValueError(f"{path}: missing required front matter field 'id'")
        if entry_id in seen_ids:
            raise ValueError(f"Duplicate encyclopedia id: {entry_id}")
        seen_ids.add(entry_id)

        entry["content_md"] = body.strip()

        # Defaults for optional list fields
        for key in ("variants", "keywords", "images", "examples"):
            if entry.get(key) is None:
                entry[key] = []

        entries.append(entry)

    return entries


def convert_encyclopedia():
    """Convert encyclopedia YAML + markdown to kodudo-compatible JSON."""
    print("=== Converting Encyclopedia ===")

    schema = aptoro.load_schema(str(DATA_DIR / "encyclopedia_schema.yaml"))
    data = _load_encyclopedia_entries()

    print(f"  Validating {len(data)} entries...")
    try:
        records = aptoro.validate(data, schema, collect_errors=True)
    except aptoro.ValidationError as e:
        print(f"  Validation errors: {len(e.errors)}")
        for error in e.errors[:10]:
            print(f"    {error}")
        if len(e.errors) > 10:
            print(f"    ... and {len(e.errors) - 10} more errors")
        raise

    md = _build_markdown_renderer()
    normalized_records = []
    for record in records:
        entry = asdict(record) if is_dataclass(record) else dict(record)
        content_md = entry.get("content_md") or ""
        _assert_no_html(content_md, entry.get("id", "<unknown>"))
        content_html = md.render(content_md) if content_md else ""
        entry["content_html"] = content_html
        entry["content_text"] = _html_to_text(content_html)
        entry.pop("content_md", None)
        normalized_records.append(entry)

    output_data = {
        "meta": {
            "name": "bororo_encyclopedia",
            "description": "Bororo Encyclopedia Entries",
            "version": "1.0",
            "record_count": len(normalized_records),
        },
        "data": normalized_records,
    }

    output_file = DATA_DIR / "encyclopedia.json"
    output_file.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  Exported {len(normalized_records)} entries to {output_file}")
    return len(normalized_records)


def convert_recordings():
    """Convert recordings YAML to JSON."""
    print("=== Converting Recordings ===")

    recordings_file = DATA_DIR / "recordings.yaml"
    if not recordings_file.exists():
        print(f"  Recordings file not found: {recordings_file}")
        print("  Run 'python scripts/inventory_recordings.py' first.")
        return 0

    schema = aptoro.load_schema(str(DATA_DIR / "recordings_schema.yaml"))

    with open(recordings_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []

    print(f"  Validating {len(data)} entries...")
    try:
        records = aptoro.validate(data, schema, collect_errors=True)
    except aptoro.ValidationError as e:
        print(f"  Validation errors: {len(e.errors)}")
        for error in e.errors[:10]:
            print(f"    {error}")
        if len(e.errors) > 10:
            print(f"    ... and {len(e.errors) - 10} more errors")
        raise

    normalized_records = []
    for record in records:
        entry = asdict(record) if is_dataclass(record) else dict(record)
        normalized_records.append(entry)

    output_data = {
        "meta": {
            "name": "bororo_recordings",
            "description": "Bororo Language Audio Recordings",
            "version": "1.0",
            "record_count": len(normalized_records),
        },
        "data": normalized_records,
    }

    output_file = DATA_DIR / "recordings.json"
    output_file.write_text(
        json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  Exported {len(normalized_records)} entries to {output_file}")
    return len(normalized_records)


def attach_recordings_to_dictionary():
    """Attach audio recordings to dictionary entries."""
    print("=== Attaching Recordings to Dictionary ===")

    recordings_file = DATA_DIR / "recordings.yaml"
    dictionary_file = DATA_DIR / "dictionary.json"

    if not recordings_file.exists():
        print("  No recordings.yaml found, skipping.")
        return
    if not dictionary_file.exists():
        print("  No dictionary.json found, skipping.")
        return

    # Build map: dictionary_id → list of audio info
    with open(recordings_file, "r", encoding="utf-8") as f:
        recordings = yaml.safe_load(f) or []

    audio_map = {}
    for rec in recordings:
        dict_id = rec.get("dictionary_id")
        if dict_id is None:
            continue
        audio_map.setdefault(dict_id, []).append({
            "file_path": rec["file_path"],
            "speaker": rec["speaker"],
            "format": rec["format"],
        })

    # Read dictionary.json and inject audio arrays
    with open(dictionary_file, "r", encoding="utf-8") as f:
        dictionary = json.load(f)

    attached_count = 0
    for entry in dictionary["data"]:
        entry_id = entry.get("id")
        if entry_id in audio_map:
            entry["audio"] = audio_map[entry_id]
            attached_count += 1

    # Rewrite dictionary.json
    dictionary_file.write_text(
        json.dumps(dictionary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  Attached audio to {attached_count} dictionary entries")
    print(f"  Total audio files linked: {sum(len(v) for v in audio_map.values())}")


def cross_link_datasets():
    """Cross-link dictionary, fauna, and encyclopedia entries by scientific name."""
    print("=== Cross-linking Datasets ===")

    dict_file = DATA_DIR / "dictionary.json"
    fauna_file = DATA_DIR / "fauna.json"
    enc_file = DATA_DIR / "encyclopedia.json"

    if not all(f.exists() for f in [dict_file, fauna_file, enc_file]):
        print("  Missing JSON files, skipping cross-linking.")
        return

    with open(dict_file, "r", encoding="utf-8") as f:
        dictionary = json.load(f)
    with open(fauna_file, "r", encoding="utf-8") as f:
        fauna = json.load(f)
    with open(enc_file, "r", encoding="utf-8") as f:
        encyclopedia = json.load(f)

    # Build lookup indices
    fauna_by_sci = {}
    for entry in fauna["data"]:
        sci = (entry.get("scientific_name") or "").strip().lower()
        if sci:
            fauna_by_sci.setdefault(sci, []).append(entry)

    dict_by_sci = {}
    for entry in dictionary["data"]:
        sci = (entry.get("scientific_name") or "").strip().lower()
        if sci:
            dict_by_sci.setdefault(sci, []).append(entry)

    link_count = 0

    # Dictionary → Fauna: match by scientific_name
    for entry in dictionary["data"]:
        sci = (entry.get("scientific_name") or "").strip().lower()
        if sci and sci in fauna_by_sci:
            linked = []
            for f_entry in fauna_by_sci[sci]:
                linked.append({
                    "id": f_entry["id"],
                    "name_bororo": f_entry.get("name_bororo", ""),
                    "name_portuguese": f_entry.get("name_portuguese", ""),
                })
            entry["_linked_fauna"] = linked
            link_count += 1

    # Fauna → Dictionary: match by scientific_name
    for entry in fauna["data"]:
        sci = (entry.get("scientific_name") or "").strip().lower()
        if sci and sci in dict_by_sci:
            linked = []
            for d_entry in dict_by_sci[sci]:
                linked.append({
                    "id": d_entry["id"],
                    "entry": d_entry.get("entry", ""),
                    "definition": d_entry.get("definition", ""),
                })
            entry["_linked_dictionary"] = linked

    # Write updated files
    dict_file.write_text(
        json.dumps(dictionary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    fauna_file.write_text(
        json.dumps(fauna, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"  Cross-linked {link_count} dictionary↔fauna entries by scientific name")


def generate_index(counts):
    """Generate index JSON with platform counts."""
    print("=== Generating Index Data ===")

    index_data = {
        "meta": {"description": "Boe Eno Moto - Index data"},
        "data": [
            {f"{name}_count": count for name, count in counts.items()}
        ],
    }

    output_file = DATA_DIR / "index.json"
    output_file.write_text(json.dumps(index_data, indent=2), encoding="utf-8")

    print(f"  Exported to {output_file}")


# Registry of converters — add new platforms here
CONVERTERS = {
    "dictionary": convert_dictionary,
    "fauna": convert_fauna,
    "encyclopedia": convert_encyclopedia,
    "bibliography": convert_bibliography,
    "recordings": convert_recordings,
}


def main():
    print("Boe Eno Moto - Data Conversion\n")

    counts = {}
    for name, converter in CONVERTERS.items():
        counts[name] = converter()
        print()

    # Post-processing: attach recordings to dictionary entries
    attach_recordings_to_dictionary()
    print()

    # Cross-link datasets
    cross_link_datasets()
    print()

    # Copy large datasets to docs/ for fetch()-based loading
    import shutil
    for name in ("dictionary", "encyclopedia"):
        src = DATA_DIR / f"{name}.json"
        dst = DOCS_DIR / f"{name}-data.json"
        shutil.copy2(src, dst)
        print(f"  Copied {src.name} → {dst}")
    print()

    # Generate index with all counts
    generate_index(counts)
    print()

    print("=== Conversion Complete ===")


if __name__ == "__main__":
    main()
