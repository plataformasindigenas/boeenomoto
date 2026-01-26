#!/usr/bin/env python3
"""
Convert Bororo data files to JSON using aptoro.

This script validates all source data files against their schemas
and generates JSON files for use with kodudo templates.

Usage:
    python scripts/convert.py
"""

import csv
import json
import sys
from pathlib import Path

import aptoro

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


def convert_encyclopedia():
    """Convert encyclopedia JSON to kodudo-compatible format."""
    print("=== Converting Encyclopedia ===")

    input_file = DATA_DIR / "encyclopedia.json"
    with open(input_file, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    entries = raw_data.get("entries", [])
    print(f"  Processing {len(entries)} entries...")

    # Validate required fields
    errors = []
    for i, entry in enumerate(entries):
        if not entry.get("id"):
            errors.append(f"Entry {i}: missing 'id'")
        if not entry.get("headword"):
            errors.append(f"Entry {i}: missing 'headword'")

    if errors:
        print(f"  Validation errors: {len(errors)}")
        for error in errors[:10]:
            print(f"    {error}")
        if len(errors) > 10:
            print(f"    ... and {len(errors) - 10} more errors")
        raise ValueError("Encyclopedia validation failed")

    # Output in kodudo-compatible format (with meta)
    output_data = {
        "meta": {
            "name": "bororo_encyclopedia",
            "description": "Bororo Encyclopedia Entries",
            "version": "1.0",
            "record_count": len(entries)
        },
        "data": entries
    }

    output_file = DATA_DIR / "encyclopedia_output.json"
    output_file.write_text(json.dumps(output_data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"  Exported {len(entries)} entries to {output_file}")
    return len(entries)


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
