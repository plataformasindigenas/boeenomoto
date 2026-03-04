"""Tests for encyclopedia front matter parsing."""

import pytest
from terradoc.markdown_utils import assert_no_html, process_wikilinks


def test_assert_no_html_clean():
    """Test that clean markdown passes HTML check."""
    assert_no_html("This is **bold** and *italic*.", "test-entry")


def test_assert_no_html_with_tags():
    """Test that HTML tags in markdown raise ValueError."""
    with pytest.raises(ValueError, match="contains HTML tags"):
        assert_no_html("<p>HTML content</p>", "test-entry")


def test_wikilink_valid():
    """Test that valid wikilinks are converted to markdown links."""
    all_ids = {"boe", "aroe", "ecerae"}
    out = process_wikilinks("See [[boe]] for details.", all_ids)
    assert "[boe](boe.html)" in out


def test_wikilink_broken():
    """Test that broken wikilinks produce span.broken-link."""
    all_ids = {"boe"}
    out = process_wikilinks("See [[nonexistent]] entry.", all_ids)
    assert "broken-link" in out
    assert "nonexistent" in out


def test_wikilink_piped():
    """Test that piped wikilinks use display text."""
    all_ids = {"boe"}
    out = process_wikilinks("See [[boe|the Bororo people]].", all_ids)
    assert "[the Bororo people](boe.html)" in out
