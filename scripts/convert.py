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


HTML_TAG_RE = re.compile(r"<\s*[a-zA-Z][^>]*>")


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"p", "br", "hr", "li", "tr", "th", "td", "h1", "h2", "h3", "h4", "h5", "h6"}:
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
        raise ValueError(f"Entry {entry_id}: content_md contains HTML tags; use markdown only")


def _html_to_text(html: str) -> str:
    if not html:
        return ""
    parser = _TextExtractor()
    parser.feed(html)
    return parser.get_text()


def convert_encyclopedia():
    """Convert encyclopedia YAML + markdown to kodudo-compatible JSON."""
    print("=== Converting Encyclopedia ===")

    schema = aptoro.load_schema(str(DATA_DIR / "encyclopedia_schema.yaml"))
    data = aptoro.read(str(DATA_DIR / "encyclopedia.yaml"), format="yaml")

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
            "record_count": len(normalized_records)
        },
        "data": normalized_records
    }

    output_file = DATA_DIR / "encyclopedia_output.json"
    output_file.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  Exported {len(normalized_records)} entries to {output_file}")
    return len(normalized_records)


def generate_index(dictionary_count: int, fauna_count: int, encyclopedia_count: int):
    """Generate index JSON with platform counts."""
    print("=== Generating Index Data ===")

    index_data = {
        "meta": {
            "description": "Boe Eno Moto - Index data"
        },
        "data": [
            {
                "dictionary_count": dictionary_count,
                "fauna_count": fauna_count,
                "encyclopedia_count": encyclopedia_count
            }
        ]
    }

    output_file = DATA_DIR / "index.json"
    output_file.write_text(json.dumps(index_data, indent=2), encoding="utf-8")

    print(f"  Exported to {output_file}")


def main():
    print("Boe Eno Moto - Data Conversion\n")

    # Convert all datasets
    dictionary_count = convert_dictionary()
    print()

    fauna_count = convert_fauna()
    print()

    encyclopedia_count = convert_encyclopedia()
    print()

    generate_index(dictionary_count, fauna_count, encyclopedia_count)
    print()

    print("=== Conversion Complete ===")


if __name__ == "__main__":
    main()
