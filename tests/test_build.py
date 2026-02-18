"""Integration tests for the build output."""

import json
from pathlib import Path


def test_html_files_exist(docs_dir):
    """Verify all expected HTML files are generated for each locale."""
    for locale in ["pt", "en"]:
        locale_dir = docs_dir / locale
        assert locale_dir.exists(), f"Missing locale directory: {locale}"

        for page in ["dictionary", "encyclopedia", "fauna", "bibliography", "index"]:
            html_file = locale_dir / f"{page}.html"
            assert html_file.exists(), f"Missing {locale}/{page}.html"
            assert html_file.stat().st_size > 0, f"Empty {locale}/{page}.html"


def test_language_picker_exists(docs_dir):
    """Verify root index.html language picker exists."""
    picker = docs_dir / "index.html"
    assert picker.exists()
    content = picker.read_text(encoding="utf-8")
    assert "pt/index.html" in content
    assert "en/index.html" in content


def test_common_js_exists(docs_dir):
    """Verify common.js utility file exists."""
    js_file = docs_dir / "js" / "common.js"
    assert js_file.exists()
    content = js_file.read_text(encoding="utf-8")
    assert "escapeHtml" in content
    assert "initSearchPage" in content


def test_data_json_in_locale_dirs(docs_dir):
    """Verify data JSON files are available in locale directories."""
    for locale in ["pt", "en"]:
        for name in ["dictionary-data.json", "encyclopedia-data.json"]:
            data_file = docs_dir / locale / name
            assert data_file.exists(), f"Missing {locale}/{name}"
            with open(data_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            assert "data" in data


def test_html_has_common_js(docs_dir):
    """Verify all HTML pages include common.js."""
    for locale in ["pt", "en"]:
        for page in ["dictionary", "fauna", "bibliography", "encyclopedia", "index"]:
            html_file = docs_dir / locale / f"{page}.html"
            content = html_file.read_text(encoding="utf-8")
            assert "common.js" in content, f"{locale}/{page}.html missing common.js"


def test_html_has_accessibility_features(docs_dir):
    """Verify HTML pages include accessibility features."""
    html_file = docs_dir / "pt" / "dictionary.html"
    content = html_file.read_text(encoding="utf-8")
    assert 'class="skip-link"' in content
    assert 'id="main-content"' in content
    assert '<main' in content
    assert 'aria-live="polite"' in content
    assert 'aria-label=' in content


def test_html_has_lang_attribute(docs_dir):
    """Verify HTML pages have correct lang attributes."""
    pt_content = (docs_dir / "pt" / "index.html").read_text(encoding="utf-8")
    assert 'lang="pt-BR"' in pt_content

    en_content = (docs_dir / "en" / "index.html").read_text(encoding="utf-8")
    assert 'lang="en"' in en_content


def test_html_has_language_switcher(docs_dir):
    """Verify pages have language switch links."""
    pt_content = (docs_dir / "pt" / "index.html").read_text(encoding="utf-8")
    assert "lang-switch" in pt_content
    assert "../en/" in pt_content

    en_content = (docs_dir / "en" / "index.html").read_text(encoding="utf-8")
    assert "../pt/" in en_content


def test_article_pages_exist(docs_dir):
    """Verify encyclopedia article pages are generated for each locale."""
    for locale in ["pt", "en"]:
        enc_dir = docs_dir / locale / "encyclopedia"
        assert enc_dir.exists(), f"Missing {locale}/encyclopedia/ directory"
        html_files = list(enc_dir.glob("*.html"))
        assert len(html_files) > 100, (
            f"Expected >100 article pages in {locale}/encyclopedia/, got {len(html_files)}"
        )


def test_article_page_structure(docs_dir):
    """Verify article pages have expected structure."""
    article = docs_dir / "pt" / "encyclopedia" / "boe.html"
    assert article.exists(), "Missing boe.html article page"
    content = article.read_text(encoding="utf-8")
    assert 'lang="pt-BR"' in content
    assert "<article>" in content
    assert "Boe" in content
    assert 'class="breadcrumb"' in content
    assert "common.js" in content
    assert 'class="skip-link"' in content


def test_article_page_nav_links(docs_dir):
    """Verify article page navigation links resolve correctly."""
    article = docs_dir / "pt" / "encyclopedia" / "ecerae.html"
    content = article.read_text(encoding="utf-8")
    # Nav links should use ../ to go up to locale dir
    assert '../dictionary.html' in content
    assert '../encyclopedia.html' in content
    assert '../fauna.html' in content
    # Lang switch should use ../../ to go up to docs root
    assert '../../en/encyclopedia.html' in content
    # Back to index link
    assert '../encyclopedia.html' in content


def test_encyclopedia_search_page_links_to_articles(docs_dir):
    """Verify the encyclopedia search page references article pages."""
    content = (docs_dir / "pt" / "encyclopedia.html").read_text(encoding="utf-8")
    assert "encyclopedia/" in content or "encyclopedia-data.json" in content
