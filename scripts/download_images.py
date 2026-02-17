#!/usr/bin/env python3
"""
Download external images for fauna and encyclopedia entries,
save them locally in docs/images/, and update source data files
with relative paths.

Usage:
    python scripts/download_images.py
"""

import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"
IMAGES_DST = DOCS_DIR / "images"
FAUNA_YAML = DATA_DIR / "fauna.yaml"
ENCYCLOPEDIA_DIR = DATA_DIR / "encyclopedia"

# Mime type to extension mapping
MIME_TO_EXT = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "image/svg+xml": "svg",
}


def safe_filename(name: str) -> str:
    """Sanitize a name for use in a filename."""
    name = name.replace(" ", "_")
    name = re.sub(r"[^a-zA-Z0-9_]", "", name)
    return name.lower()


def ext_from_url(url: str) -> str:
    """Extract file extension from a URL path."""
    # Strip query params and fragments
    path = url.split("?")[0].split("#")[0]
    # Get last component
    filename = path.rsplit("/", 1)[-1]
    if "." in filename:
        ext = filename.rsplit(".", 1)[-1].lower()
        # Normalize common extensions
        if ext in ("jpg", "jpeg"):
            return "jpg"
        if ext in ("png", "gif", "webp", "svg"):
            return ext
    return "jpg"  # default fallback


def ext_from_content_type(content_type: str) -> str | None:
    """Extract extension from Content-Type header."""
    mime = content_type.split(";")[0].strip().lower()
    return MIME_TO_EXT.get(mime)


DOWNLOAD_DELAY = 2  # seconds between downloads (Wikimedia rate limit compliance)

# Wikimedia requires a descriptive User-Agent with contact info
USER_AGENT = (
    "BoeEnoMotoBot/1.0 "
    "(https://github.com/boeenomoto; bororo language documentation project) "
    "Python-urllib"
)


def encode_url(url: str) -> str:
    """Encode non-ASCII characters in URL path for urllib compatibility.

    Handles URLs that already contain percent-encoded sequences (e.g. %28)
    by unquoting first, then re-quoting everything properly.
    """
    parsed = urllib.parse.urlsplit(url)
    # Unquote first to avoid double-encoding, then re-encode
    raw_path = urllib.parse.unquote(parsed.path)
    encoded_path = urllib.parse.quote(raw_path, safe="/:@!$&'()*+,;=-._~")
    return urllib.parse.urlunsplit((
        parsed.scheme, parsed.netloc, encoded_path, parsed.query, parsed.fragment
    ))


def download_image(url: str, dest: Path, max_retries: int = 4) -> bool:
    """Download an image from url to dest with retry/backoff. Returns True on success."""
    encoded = encode_url(url)
    req = urllib.request.Request(
        encoded,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Encoding": "gzip",
        },
    )
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                # Determine extension from content-type if available
                ct = resp.headers.get("Content-Type", "")
                ct_ext = ext_from_content_type(ct)
                if ct_ext:
                    dest = dest.with_suffix(f".{ct_ext}")
                data = resp.read()
                dest.write_bytes(data)
                return True
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < max_retries - 1:
                wait = 5 * (2 ** attempt)  # 5, 10, 20 seconds
                print(f"    Rate limited, waiting {wait}s (attempt {attempt + 1}/{max_retries})...")
                time.sleep(wait)
                continue
            print(f"  FAILED: {url}\n    {e}")
            return False
        except Exception as e:
            print(f"  FAILED: {url}\n    {e}")
            return False
    return False


def make_placeholder_jpeg(dest: Path) -> None:
    """Create a minimal 1x1 pixel JPEG placeholder."""
    # Minimal valid JPEG: SOI + JFIF APP0 + DQT + SOF0 + DHT + SOS + data + EOI
    # Simplest approach: use a known minimal JPEG byte sequence
    minimal_jpeg = bytes([
        0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46,
        0x49, 0x46, 0x00, 0x01, 0x01, 0x00, 0x00, 0x01,
        0x00, 0x01, 0x00, 0x00, 0xFF, 0xDB, 0x00, 0x43,
        0x00, 0x08, 0x06, 0x06, 0x07, 0x06, 0x05, 0x08,
        0x07, 0x07, 0x07, 0x09, 0x09, 0x08, 0x0A, 0x0C,
        0x14, 0x0D, 0x0C, 0x0B, 0x0B, 0x0C, 0x19, 0x12,
        0x13, 0x0F, 0x14, 0x1D, 0x1A, 0x1F, 0x1E, 0x1D,
        0x1A, 0x1C, 0x1C, 0x20, 0x24, 0x2E, 0x27, 0x20,
        0x22, 0x2C, 0x23, 0x1C, 0x1C, 0x28, 0x37, 0x29,
        0x2C, 0x30, 0x31, 0x34, 0x34, 0x34, 0x1F, 0x27,
        0x39, 0x3D, 0x38, 0x32, 0x3C, 0x2E, 0x33, 0x34,
        0x32, 0xFF, 0xC0, 0x00, 0x0B, 0x08, 0x00, 0x01,
        0x00, 0x01, 0x01, 0x01, 0x11, 0x00, 0xFF, 0xC4,
        0x00, 0x1F, 0x00, 0x00, 0x01, 0x05, 0x01, 0x01,
        0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x03, 0x04,
        0x05, 0x06, 0x07, 0x08, 0x09, 0x0A, 0x0B, 0xFF,
        0xC4, 0x00, 0xB5, 0x10, 0x00, 0x02, 0x01, 0x03,
        0x03, 0x02, 0x04, 0x03, 0x05, 0x05, 0x04, 0x04,
        0x00, 0x00, 0x01, 0x7D, 0x01, 0x02, 0x03, 0x00,
        0x04, 0x11, 0x05, 0x12, 0x21, 0x31, 0x41, 0x06,
        0x13, 0x51, 0x61, 0x07, 0x22, 0x71, 0x14, 0x32,
        0x81, 0x91, 0xA1, 0x08, 0x23, 0x42, 0xB1, 0xC1,
        0x15, 0x52, 0xD1, 0xF0, 0x24, 0x33, 0x62, 0x72,
        0x82, 0x09, 0x0A, 0x16, 0x17, 0x18, 0x19, 0x1A,
        0x25, 0x26, 0x27, 0x28, 0x29, 0x2A, 0x34, 0x35,
        0x36, 0x37, 0x38, 0x39, 0x3A, 0x43, 0x44, 0x45,
        0x46, 0x47, 0x48, 0x49, 0x4A, 0x53, 0x54, 0x55,
        0x56, 0x57, 0x58, 0x59, 0x5A, 0x63, 0x64, 0x65,
        0x66, 0x67, 0x68, 0x69, 0x6A, 0x73, 0x74, 0x75,
        0x76, 0x77, 0x78, 0x79, 0x7A, 0x83, 0x84, 0x85,
        0x86, 0x87, 0x88, 0x89, 0x8A, 0x92, 0x93, 0x94,
        0x95, 0x96, 0x97, 0x98, 0x99, 0x9A, 0xA2, 0xA3,
        0xA4, 0xA5, 0xA6, 0xA7, 0xA8, 0xA9, 0xAA, 0xB2,
        0xB3, 0xB4, 0xB5, 0xB6, 0xB7, 0xB8, 0xB9, 0xBA,
        0xC2, 0xC3, 0xC4, 0xC5, 0xC6, 0xC7, 0xC8, 0xC9,
        0xCA, 0xD2, 0xD3, 0xD4, 0xD5, 0xD6, 0xD7, 0xD8,
        0xD9, 0xDA, 0xE1, 0xE2, 0xE3, 0xE4, 0xE5, 0xE6,
        0xE7, 0xE8, 0xE9, 0xEA, 0xF1, 0xF2, 0xF3, 0xF4,
        0xF5, 0xF6, 0xF7, 0xF8, 0xF9, 0xFA, 0xFF, 0xDA,
        0x00, 0x08, 0x01, 0x01, 0x00, 0x00, 0x3F, 0x00,
        0x7B, 0x94, 0x11, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
        0x00, 0xFF, 0xD9,
    ])
    dest.write_bytes(minimal_jpeg)


def process_fauna():
    """Download fauna images and update fauna.yaml."""
    print("=== Processing Fauna ===\n")

    with open(FAUNA_YAML, "r", encoding="utf-8") as f:
        entries = yaml.safe_load(f) or []

    downloaded = 0
    failed = 0
    skipped = 0

    for entry in entries:
        pic_link = entry.get("pic_link", "")
        if not pic_link or not pic_link.startswith("http"):
            skipped += 1
            continue

        entry_id = entry["id"]
        name = entry.get("name_bororo", "") or entry.get("name_portuguese", "unknown")
        safe_name = safe_filename(name)

        url_ext = ext_from_url(pic_link)
        dest_name = f"fauna_{entry_id:03d}_{safe_name}.{url_ext}"
        dest_path = IMAGES_DST / dest_name

        if dest_path.exists():
            print(f"  EXISTS: {dest_name}")
            entry["pic_link"] = f"images/{dest_name}"
            skipped += 1
            continue

        print(f"  Downloading fauna {entry_id}: {safe_name}...")
        if download_image(pic_link, dest_path):
            # Re-check actual filename (extension may have changed)
            actual = list(IMAGES_DST.glob(f"fauna_{entry_id:03d}_{safe_name}.*"))
            if actual:
                actual_name = actual[0].name
            else:
                actual_name = dest_name
            entry["pic_link"] = f"images/{actual_name}"
            downloaded += 1
        else:
            failed += 1
        time.sleep(DOWNLOAD_DELAY)

    # Write updated fauna.yaml
    with open(FAUNA_YAML, "w", encoding="utf-8") as f:
        yaml.dump(entries, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"\nFauna: {downloaded} downloaded, {failed} failed, {skipped} skipped")
    return downloaded, failed


def parse_front_matter(text: str) -> tuple[dict | None, str]:
    """Parse YAML front matter from markdown text.

    Returns (front_matter_dict, body_text).
    If no front matter found, returns (None, original_text).
    """
    if not text.startswith("---"):
        return None, text

    # Find closing ---
    end = text.find("\n---", 3)
    if end == -1:
        return None, text

    yaml_text = text[4:end]  # skip opening ---\n
    body = text[end + 4:]  # skip \n---

    try:
        fm = yaml.safe_load(yaml_text)
        return fm, body
    except yaml.YAMLError:
        return None, text


def serialize_front_matter(fm: dict, body: str) -> str:
    """Serialize front matter dict + body back to markdown."""
    yaml_text = yaml.dump(
        fm, default_flow_style=False, allow_unicode=True, sort_keys=False
    )
    return f"---\n{yaml_text}---{body}"


def process_encyclopedia():
    """Download encyclopedia images and update .md files."""
    print("\n=== Processing Encyclopedia ===\n")

    downloaded = 0
    failed = 0
    placeholders = 0
    skipped = 0

    md_files = sorted(ENCYCLOPEDIA_DIR.glob("*.md"))
    for md_file in md_files:
        if md_file.name == "README.md":
            continue

        text = md_file.read_text(encoding="utf-8")
        fm, body = parse_front_matter(text)
        if fm is None:
            continue

        images = fm.get("images")
        if not images or not isinstance(images, list):
            continue

        modified = False
        entry_id = fm.get("id", md_file.stem)

        for idx, img in enumerate(images):
            # Handle bare URL strings (e.g. aroe-eporewu.md)
            if isinstance(img, str):
                url = img
                if not url.startswith("http"):
                    continue
                url_ext = ext_from_url(url)
                dest_name = f"enc_{safe_filename(str(entry_id))}_{idx}.{url_ext}"
                dest_path = IMAGES_DST / dest_name

                if dest_path.exists():
                    print(f"  EXISTS: {dest_name}")
                    images[idx] = f"images/{dest_name}"
                    modified = True
                    skipped += 1
                    continue

                print(f"  Downloading enc {entry_id} image {idx}...")
                if download_image(url, dest_path):
                    actual = list(IMAGES_DST.glob(f"enc_{safe_filename(str(entry_id))}_{idx}.*"))
                    actual_name = actual[0].name if actual else dest_name
                    images[idx] = f"images/{actual_name}"
                    modified = True
                    downloaded += 1
                else:
                    failed += 1
                time.sleep(DOWNLOAD_DELAY)
                continue

            # Handle dict format: {url, alt, credit}
            if not isinstance(img, dict):
                continue

            url = img.get("url", "")
            if not url:
                continue

            # External URL
            if url.startswith("http"):
                url_ext = ext_from_url(url)
                dest_name = f"enc_{safe_filename(str(entry_id))}_{idx}.{url_ext}"
                dest_path = IMAGES_DST / dest_name

                if dest_path.exists():
                    print(f"  EXISTS: {dest_name}")
                    img["url"] = f"images/{dest_name}"
                    modified = True
                    skipped += 1
                    continue

                print(f"  Downloading enc {entry_id} image {idx}...")
                if download_image(url, dest_path):
                    actual = list(IMAGES_DST.glob(f"enc_{safe_filename(str(entry_id))}_{idx}.*"))
                    actual_name = actual[0].name if actual else dest_name
                    img["url"] = f"images/{actual_name}"
                    modified = True
                    downloaded += 1
                else:
                    failed += 1
                time.sleep(DOWNLOAD_DELAY)

            # Broken local path (images/foo.jpg)
            elif url.startswith("images/"):
                local_name = url.split("/", 1)[1]
                dest_path = IMAGES_DST / local_name
                if not dest_path.exists():
                    print(f"  PLACEHOLDER: {local_name}")
                    make_placeholder_jpeg(dest_path)
                    placeholders += 1
                # Path is already relative, no change needed

        if modified:
            fm["images"] = images
            md_file.write_text(serialize_front_matter(fm, body), encoding="utf-8")

    print(f"\nEncyclopedia: {downloaded} downloaded, {failed} failed, {placeholders} placeholders, {skipped} skipped")
    return downloaded, failed, placeholders


def main():
    print("=== Image Download & Localization ===\n")

    IMAGES_DST.mkdir(parents=True, exist_ok=True)

    fauna_dl, fauna_fail = process_fauna()
    enc_dl, enc_fail, enc_placeholders = process_encyclopedia()

    total_dl = fauna_dl + enc_dl
    total_fail = fauna_fail + enc_fail

    print(f"\n=== Summary ===")
    print(f"Total downloaded: {total_dl}")
    print(f"Total failed: {total_fail}")
    print(f"Placeholders created: {enc_placeholders}")

    image_count = len(list(IMAGES_DST.iterdir()))
    print(f"Files in docs/images/: {image_count}")

    if total_fail > 0:
        print(f"\nWARNING: {total_fail} downloads failed. Original URLs preserved for those entries.")
        sys.exit(1)


if __name__ == "__main__":
    main()
