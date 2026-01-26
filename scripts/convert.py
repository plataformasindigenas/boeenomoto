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
import re
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


def format_encyclopedia_content(content: str) -> str:
    """
    Transform plain text content into structured HTML.

    Rules:
    1. Skip if content already has structural HTML tags
    2. Convert numbered sections (1., 2., 2.1.) to headings
    3. Break long text blocks into paragraphs (every 2-3 sentences)
    4. Preserve existing inline HTML like <em>
    """
    if not content or len(content.strip()) == 0:
        return content

    # Skip if already has structural HTML
    if re.search(r'<(h[1-6]|p\s|p>|ul|ol|div)', content, re.IGNORECASE):
        return content

    # Check if content has numbered sections
    # Pattern 1: Section at start of line (clean formatting)
    # Pattern 2: Section embedded in text (OCR artifacts) - number after period or space
    has_clean_sections = bool(re.search(r'(?:^|\n)\s*\d+\.(?:\d+\.)*\s+[A-ZÁÉÍÓÚÀÂÃÊÎÔÕÇ]', content))
    has_embedded_sections = bool(re.search(r'(?<=[.!?\s])\d+\.\s+[A-ZÁÉÍÓÚÀÂÃÊÎÔÕÇ]', content))

    if has_clean_sections or has_embedded_sections:
        return _format_with_sections(content)
    else:
        return _format_paragraphs(content)


def _format_with_sections(content: str) -> str:
    """Format content that has numbered sections like '1. Title', '2.1. Subtitle'."""
    # First, normalize the content by adding line breaks before section numbers
    # This handles OCR artifacts where sections run together

    # Pattern to find section numbers (handles both clean and embedded)
    # Matches: "1. ", "2.1. ", "2.1.1. " followed by capital letter
    # But not things like "p. ex." or decimal numbers
    normalized = re.sub(
        r'(?<=[.!?\s])(\d+\.(?:\d+\.)*)\s+([A-ZÁÉÍÓÚÀÂÃÊÎÔÕÇ])',
        r'\n\n\1 \2',
        content
    )

    # Also handle section numbers at the very start
    normalized = re.sub(
        r'^(\d+\.(?:\d+\.)*)\s+([A-ZÁÉÍÓÚÀÂÃÊÎÔÕÇ])',
        r'\1 \2',
        normalized
    )

    result = []

    # Split content by section markers (now on their own lines)
    parts = re.split(r'\n\n(?=\d+\.(?:\d+\.)*\s+[A-ZÁÉÍÓÚÀÂÃÊÎÔÕÇ])', normalized)

    for part in parts:
        part = part.strip()
        if not part:
            continue

        # Check if this part starts with a section number
        section_match = re.match(r'^(\d+\.(?:\d+\.)*)\s+(.+)', part, re.DOTALL)

        if section_match:
            section_num = section_match.group(1)
            section_content = section_match.group(2).strip()

            # Determine heading level based on section depth
            depth = section_num.count('.')
            heading_tag = 'h3' if depth <= 1 else 'h4'

            # Extract title - text up to the next sentence ending or newline
            # But be careful not to grab too much
            title_match = re.match(r'^([A-ZÁÉÍÓÚÀÂÃÊÎÔÕÇ][^.!?\n]{0,100}(?:[.!?])?)', section_content)
            if title_match:
                title = title_match.group(1).strip()
                remaining = section_content[len(title):].strip()

                # Clean up title - remove trailing punctuation for heading
                title_clean = re.sub(r'[.!?:]+$', '', title).strip()

                # If title is too short and remaining starts with lowercase, include more
                if len(title_clean) < 20 and remaining and remaining[0].islower():
                    # Title might have been cut off, include the rest of the sentence
                    extended_match = re.match(r'^([^.!?\n]+[.!?]?)', section_content)
                    if extended_match:
                        title_clean = re.sub(r'[.!?:]+$', '', extended_match.group(1)).strip()
                        remaining = section_content[len(extended_match.group(1)):].strip()

                result.append(f'<{heading_tag}>{section_num} {title_clean}</{heading_tag}>')

                if remaining:
                    # Format the remaining content as paragraphs
                    formatted_remaining = _format_paragraphs(remaining)
                    result.append(formatted_remaining)
            else:
                result.append(f'<{heading_tag}>{section_num} {section_content}</{heading_tag}>')
        else:
            # No section number - format as introduction paragraphs
            formatted = _format_paragraphs(part)
            result.append(formatted)

    return '\n\n'.join(result)


def _format_paragraphs(content: str) -> str:
    """Break text into paragraphs, grouping 2-3 sentences each."""
    if not content or len(content.strip()) == 0:
        return content

    content = content.strip()

    # If content is very short, wrap in single paragraph
    if len(content) < 150:
        return f'<p>{content}</p>'

    # Split into sentences
    # Pattern: period/exclamation/question followed by space and capital letter
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÀÂÃÊÎÔÕÇ])', content)

    if len(sentences) <= 2:
        return f'<p>{content}</p>'

    # Group sentences into paragraphs (2-3 sentences each)
    paragraphs = []
    current_para = []

    for i, sentence in enumerate(sentences):
        sentence = sentence.strip()
        if not sentence:
            continue

        current_para.append(sentence)

        # Create paragraph every 2-3 sentences, or at the end
        if len(current_para) >= 2:
            # Check if adding another sentence would make it too long
            current_length = sum(len(s) for s in current_para)
            next_sentence = sentences[i + 1] if i + 1 < len(sentences) else None

            if len(current_para) >= 3 or current_length > 400 or next_sentence is None:
                para_text = ' '.join(current_para)
                paragraphs.append(f'<p>{para_text}</p>')
                current_para = []

    # Don't forget remaining sentences
    if current_para:
        para_text = ' '.join(current_para)
        paragraphs.append(f'<p>{para_text}</p>')

    return '\n\n'.join(paragraphs)


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

    # Format content for each entry
    formatted_count = 0
    for entry in entries:
        if entry.get("content"):
            original = entry["content"]
            entry["content"] = format_encyclopedia_content(original)
            if entry["content"] != original:
                formatted_count += 1

    print(f"  Formatted {formatted_count} entries with auto-structure")

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
