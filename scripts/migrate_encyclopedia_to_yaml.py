#!/usr/bin/env python3
"""
Migrate encyclopedia entries from JSON (HTML content) to YAML (markdown content).

Usage:
    python scripts/migrate_encyclopedia_to_yaml.py
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"

HTML_TAG_RE = re.compile(r"<\s*[a-zA-Z][^>]*>")


class _LiteralStr(str):
    pass


def _literal_str_representer(dumper: yaml.Dumper, data: _LiteralStr) -> yaml.ScalarNode:
    return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")


def _repair_missing_commas(text: str) -> str:
    result: list[str] = []
    in_string = False
    escape = False

    for i, ch in enumerate(text):
        result.append(ch)

        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == "\"":
                in_string = False
            continue

        if ch == "\"":
            in_string = True
            continue

        if ch == "}":
            j = i + 1
            while j < len(text) and text[j].isspace():
                j += 1
            if j < len(text) and text[j] == "{":
                result.append(",")

    return "".join(result)


def _load_json_with_repair(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        repaired = _repair_missing_commas(raw)
        return json.loads(repaired)


def _pandoc_html_to_md(html: str) -> str:
    if not html.strip():
        return ""
    result = subprocess.run(
        ["pandoc", "--from=html", "--to=gfm", "--wrap=preserve"],
        input=html,
        text=True,
        capture_output=True,
        check=True,
    )
    text = result.stdout.strip()
    return re.sub(r"\n{3,}", "\n\n", text)


def _normalize_markdown(content: str) -> str:
    content = content.replace("\r\n", "\n").strip()
    return re.sub(r"\n{3,}", "\n\n", content)


def _convert_entry(entry: dict) -> dict:
    entry = dict(entry)
    html_content = entry.pop("content", "") or ""

    if HTML_TAG_RE.search(html_content):
        content_md = _pandoc_html_to_md(html_content)
    else:
        content_md = _normalize_markdown(html_content)

    entry["content_md"] = content_md
    return entry


def main() -> None:
    input_file = DATA_DIR / "encyclopedia_output.json"
    output_file = DATA_DIR / "encyclopedia.yaml"

    if input_file.exists():
        data = json.loads(input_file.read_text(encoding="utf-8"))
        entries = data.get("data", [])
    else:
        legacy_input = DATA_DIR / "encyclopedia.json"
        data = _load_json_with_repair(legacy_input)
        entries = data.get("entries", [])

    converted = []
    html_count = 0
    for entry in entries:
        if HTML_TAG_RE.search(entry.get("content", "") or ""):
            html_count += 1
        converted.append(_convert_entry(entry))

    yaml.add_representer(_LiteralStr, _literal_str_representer, Dumper=yaml.SafeDumper)
    for entry in converted:
        content = entry.get("content_md", "")
        if "\n" in content:
            entry["content_md"] = _LiteralStr(content)

    output_file.write_text(
        yaml.safe_dump(converted, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    print(f"Converted {len(converted)} entries ({html_count} with HTML content).")
    print(f"Wrote {output_file}")


if __name__ == "__main__":
    main()
