"""Tests for the convert.py script."""

import json
from pathlib import Path


def test_all_json_files_exist(data_dir):
    """Verify all expected JSON output files exist after conversion."""
    expected = [
        "dictionary.json",
        "fauna.json",
        "encyclopedia.json",
        "bibliography.json",
        "recordings.json",
        "index.json",
    ]
    for name in expected:
        path = data_dir / name
        assert path.exists(), f"Missing expected output: {path}"


def test_json_files_valid(data_dir):
    """Verify all JSON files are valid JSON with expected structure."""
    for path in data_dir.glob("*.json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "meta" in data, f"{path.name}: missing 'meta' key"
        assert "data" in data, f"{path.name}: missing 'data' key"
        assert isinstance(data["data"], list), f"{path.name}: 'data' is not a list"


def test_json_meta_structure(data_dir):
    """Verify meta fields are consistent across all dataset JSON files."""
    datasets = [
        "dictionary.json",
        "fauna.json",
        "encyclopedia.json",
        "bibliography.json",
        "recordings.json",
    ]
    for name in datasets:
        path = data_dir / name
        if not path.exists():
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        meta = data["meta"]
        assert "name" in meta, f"{name}: meta missing 'name'"
        assert "description" in meta, f"{name}: meta missing 'description'"
        assert "version" in meta, f"{name}: meta missing 'version'"
        assert "record_count" in meta, f"{name}: meta missing 'record_count'"
        assert meta["record_count"] == len(data["data"]), (
            f"{name}: record_count ({meta['record_count']}) != len(data) ({len(data['data'])})"
        )


def test_dictionary_has_entries(data_dir):
    """Verify dictionary has a reasonable number of entries."""
    with open(data_dir / "dictionary.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data["data"]) > 2000, "Dictionary should have >2000 entries"


def test_dictionary_entry_structure(data_dir):
    """Verify dictionary entries have required fields."""
    with open(data_dir / "dictionary.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    entry = data["data"][0]
    assert "id" in entry
    assert "entry" in entry
    assert isinstance(entry["id"], int)
    assert isinstance(entry["entry"], str)


def test_dictionary_has_audio_attached(data_dir):
    """Verify some dictionary entries have audio recordings attached."""
    with open(data_dir / "dictionary.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    with_audio = [e for e in data["data"] if "audio" in e and e["audio"]]
    assert len(with_audio) > 0, "No dictionary entries have audio attached"


def test_dictionary_cross_links(data_dir):
    """Verify cross-linking produced _linked_fauna entries."""
    with open(data_dir / "dictionary.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    linked = [e for e in data["data"] if "_linked_fauna" in e]
    assert len(linked) > 0, "No dictionary entries cross-linked to fauna"


def test_fauna_cross_links(data_dir):
    """Verify cross-linking produced _linked_dictionary entries in fauna."""
    with open(data_dir / "fauna.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    linked = [e for e in data["data"] if "_linked_dictionary" in e]
    assert len(linked) > 0, "No fauna entries cross-linked to dictionary"


def test_fauna_entry_structure(data_dir):
    """Verify fauna entries have required fields."""
    with open(data_dir / "fauna.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    entry = data["data"][0]
    assert "id" in entry
    assert "name_bororo" in entry


def test_encyclopedia_has_html(data_dir):
    """Verify encyclopedia entries have rendered HTML content."""
    with open(data_dir / "encyclopedia.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    with_html = [e for e in data["data"] if e.get("content_html")]
    assert len(with_html) > 0, "No encyclopedia entries have content_html"


def test_index_has_counts(data_dir):
    """Verify index.json has count fields for all platforms."""
    with open(data_dir / "index.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    counts = data["data"][0]
    assert "dictionary_count" in counts
    assert "fauna_count" in counts
    assert "encyclopedia_count" in counts
    assert "bibliography_count" in counts
    assert "recordings_count" in counts
    assert all(v > 0 for v in counts.values()), "All counts should be > 0"


def test_encyclopedia_index_exists(data_dir):
    """Verify encyclopedia_index.json is generated."""
    path = data_dir / "encyclopedia_index.json"
    assert path.exists(), "Missing encyclopedia_index.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "meta" in data
    assert "data" in data
    assert data["meta"]["record_count"] == len(data["data"])
    assert len(data["data"]) > 100


def test_encyclopedia_index_is_lightweight(data_dir):
    """Verify encyclopedia_index.json does not contain content_html."""
    with open(data_dir / "encyclopedia_index.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    entry = data["data"][0]
    assert "content_html" not in entry, "Index should not contain content_html"
    assert "content_text" not in entry, "Index should not contain content_text"
    assert "id" in entry
    assert "title" in entry


def test_encyclopedia_full_has_new_fields(data_dir):
    """Verify full encyclopedia.json has new schema v2 fields."""
    with open(data_dir / "encyclopedia.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    entry = data["data"][0]
    assert "title" in entry
    assert "content_html" in entry
    assert "resolved_references" in entry
    assert isinstance(entry.get("infobox"), dict), "infobox should be a dict in JSON output"


def test_encyclopedia_entry_ids_normalized(data_dir):
    """Verify all encyclopedia entry IDs are URL-safe (no spaces)."""
    with open(data_dir / "encyclopedia.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    for entry in data["data"]:
        eid = entry["id"]
        assert " " not in eid, f"Entry ID '{eid}' contains spaces"
