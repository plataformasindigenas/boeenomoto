#!/usr/bin/env python3
"""Fetch ethnobotany data from the old Boe Eno Moto backend and prepare it for terradoc."""

import re
import sys
import time
import urllib.request
import urllib.error
import urllib.parse
import json
from pathlib import Path

import yaml


API_URL = "https://boeenomoto-backend.onrender.com/api/etno"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
IMAGES_DIR = Path(__file__).resolve().parent.parent / "docs" / "images"

VILLAGE_FIELDS = [
    ("abundance_piebaga", "Piébaga"),
    ("abundance_korogedu", "Córrego Grande"),
    ("abundance_tadarimana", "Tadarimana"),
    ("abundance_meruri", "Meruri"),
]

DROP_FIELDS = {"created_at"}


def fetch_data() -> list[dict]:
    """Fetch ethnobotany entries from the API."""
    print(f"Fetching data from {API_URL}...")
    req = urllib.request.Request(API_URL, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = json.loads(resp.read().decode("utf-8"))

    # The API may return [...], {"data": [...]}, or {"etno": [...]} etc.
    if isinstance(raw, list):
        entries = raw
    elif isinstance(raw, dict):
        # Try common wrapper keys
        for key in ("data", "etno", "results", "entries"):
            if key in raw and isinstance(raw[key], list):
                entries = raw[key]
                break
        else:
            # Use the first list value found
            for val in raw.values():
                if isinstance(val, list):
                    entries = val
                    break
            else:
                raise ValueError(f"Unexpected API response structure: keys={list(raw.keys())}")
    else:
        raise ValueError(f"Unexpected API response type: {type(raw)}")

    print(f"  Fetched {len(entries)} entries")
    return entries


def slugify(text: str) -> str:
    """Create a filesystem-safe slug from text."""
    s = text.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_]+", "_", s)
    return s[:40]


def download_image(url: str, entry_id: int, name: str) -> str | None:
    """Download an image and return the local relative path, or None on failure."""
    if not url or not url.startswith("http"):
        return None

    slug = slugify(name) if name else str(entry_id)
    # Determine extension from URL
    ext = ".jpg"
    lower_url = url.lower()
    if ".png" in lower_url:
        ext = ".png"
    elif ".svg" in lower_url:
        ext = ".svg"
    elif ".webp" in lower_url:
        ext = ".webp"

    filename = f"ethnobotany_{entry_id:03d}_{slug}{ext}"
    local_path = IMAGES_DIR / filename

    if local_path.exists():
        return f"images/{filename}"

    try:
        # Encode non-ASCII characters in the URL path
        parsed = urllib.parse.urlsplit(url)
        safe_path = urllib.parse.quote(parsed.path, safe="/:@!$&'()*+,;=-._~")
        safe_url = urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, safe_path, parsed.query, parsed.fragment))
        req = urllib.request.Request(safe_url, headers={
            "User-Agent": "Mozilla/5.0 (terradoc ethnobotany importer)"
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            local_path.write_bytes(resp.read())
        print(f"    Downloaded: {filename}")
        return f"images/{filename}"
    except Exception as e:
        print(f"    Failed to download {url}: {e}")
        return None


def transform_entry(entry: dict, download_images: bool = True) -> dict:
    """Transform an API entry to the terradoc ethnobotany schema."""
    result = {}

    # Copy standard fields
    result["id"] = entry["id"]
    for field in ("name_bororo", "name_portuguese", "scientific_name", "family",
                  "usage", "types_of_use", "descriptions_of_use",
                  "fruiting_period", "environment"):
        val = entry.get(field)
        if val and str(val).strip():
            result[field] = str(val).strip()

    # Collapse abundance fields into list
    abundance = []
    for api_field, village_name in VILLAGE_FIELDS:
        val = entry.get(api_field)
        if val and str(val).strip():
            abundance.append({"village": village_name, "level": str(val).strip()})
    if abundance:
        result["abundance"] = abundance

    # Handle image
    pic_link = entry.get("pic_link")
    if pic_link and str(pic_link).strip():
        pic_link = str(pic_link).strip()
        if download_images:
            name = result.get("name_bororo") or result.get("name_portuguese") or ""
            local = download_image(pic_link, result["id"], name)
            if local:
                result["pic_link"] = local
            # If download fails, omit pic_link (don't keep external URL)
        else:
            result["pic_link"] = pic_link

    return result


def main():
    download_imgs = "--no-images" not in sys.argv

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    entries = fetch_data()

    print(f"Transforming {len(entries)} entries...")
    transformed = []
    for entry in entries:
        transformed.append(transform_entry(entry, download_images=download_imgs))

    # Sort by id
    transformed.sort(key=lambda e: e["id"])

    output_file = DATA_DIR / "ethnobotany.yaml"
    with open(output_file, "w", encoding="utf-8") as f:
        yaml.dump(transformed, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"\nWrote {len(transformed)} entries to {output_file}")

    # Stats
    fields = ["name_bororo", "name_portuguese", "scientific_name", "family",
              "usage", "types_of_use", "descriptions_of_use",
              "fruiting_period", "environment", "abundance", "pic_link"]
    print("\nField completeness:")
    for field in fields:
        count = sum(1 for e in transformed if e.get(field))
        print(f"  {field}: {count}/{len(transformed)}")


if __name__ == "__main__":
    main()
