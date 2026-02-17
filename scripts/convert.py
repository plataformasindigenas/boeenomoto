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
            print(f"    Row {error.row}: {error.field} - {error.message}")
        if len(e.errors) > 10:
            print(f"    ... and {len(e.errors) - 10} more errors")
        raise

    json_output = aptoro.to_json(records, schema=schema, include_meta=True)
    output_file = DATA_DIR / "dictionary.json"
    output_file.write_text(json_output, encoding="utf-8")

    print(f"  Exported {len(records)} entries to {output_file}")
    return len(records)


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
            print(f"    Row {error.row}: {error.field} - {error.message}")
        if len(e.errors) > 10:
            print(f"    ... and {len(e.errors) - 10} more errors")
        raise

    json_output = aptoro.to_json(records, schema=schema, include_meta=True)
    output_file = DATA_DIR / "fauna.json"
    output_file.write_text(json_output, encoding="utf-8")

    print(f"  Exported {len(records)} entries to {output_file}")
    return len(records)


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
            print(f"    Row {error.row}: {error.field} - {error.message}")
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

    output_file = DATA_DIR / "bibliography_output.json"
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
            print(f"    Row {error.row}: {error.field} - {error.message}")
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

    # Output in kodudo-compatible format (with meta)
    output_data = {
        "meta": {
            "name": "bororo_encyclopedia",
            "description": "Bororo Encyclopedia Entries",
            "version": "1.0",
            "record_count": len(normalized_records),
        },
        "data": normalized_records,
    }

    output_file = DATA_DIR / "encyclopedia_output.json"
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


def generate_index(
    dictionary_count: int,
    fauna_count: int,
    encyclopedia_count: int,
    bibliography_count: int,
    recordings_count: int = 0,
):
    """Generate index JSON with platform counts."""
    print("=== Generating Index Data ===")

    index_data = {
        "meta": {"description": "Boe Eno Moto - Index data"},
        "data": [
            {
                "dictionary_count": dictionary_count,
                "fauna_count": fauna_count,
                "encyclopedia_count": encyclopedia_count,
                "bibliography_count": bibliography_count,
                "recordings_count": recordings_count,
            }
        ],
    }

    output_file = DATA_DIR / "index.json"
    output_file.write_text(json.dumps(index_data, indent=2), encoding="utf-8")

    print(f"  Exported to {output_file}")


def main():
    print("Boe Eno Moto - Data Conversion\n")

    dictionary_count = convert_dictionary()
    print()

    fauna_count = convert_fauna()
    print()

    encyclopedia_count = convert_encyclopedia()
    print()

    bibliography_count = convert_bibliography()
    print()

    recordings_count = convert_recordings()
    print()

    attach_recordings_to_dictionary()
    print()

    generate_index(
        dictionary_count,
        fauna_count,
        encyclopedia_count,
        bibliography_count,
        recordings_count,
    )
    print()

    print("=== Conversion Complete ===")


if __name__ == "__main__":
    main()
