"""Checks on a local build of the site (terradoc v2 templates, since 2026-11-19).

Build first:  terradoc build --config terradoc.yaml --out docs
(docs/ is not in git; CI builds the site itself and runs terradoc's own checks.)
"""

import json
import re

import pytest

PAGES = ["index", "dictionary", "encyclopedia", "fauna", "ethnobotany", "bibliography",
         "videos", "about"]


@pytest.fixture(autouse=True)
def built(docs_dir):
    if not (docs_dir / "pt" / "index.html").exists():
        pytest.skip("no local build: terradoc build --config terradoc.yaml --out docs")


def test_html_files_exist(docs_dir):
    for locale in ["pt", "en"]:
        for page in PAGES:
            html_file = docs_dir / locale / f"{page}.html"
            assert html_file.exists() and html_file.stat().st_size > 0, f"{locale}/{page}.html"
        assert (docs_dir / locale / "dictionary" / "index.html").exists()


def test_language_picker(docs_dir):
    content = (docs_dir / "index.html").read_text(encoding="utf-8")
    assert 'href="pt/index.html"' in content and 'href="en/index.html"' in content


def test_search_index(docs_dir):
    """The dictionary search index (replaces v1's dictionary-data.json)."""
    page = (docs_dir / "pt" / "dictionary" / "index.html").read_text(encoding="utf-8")
    name = re.search(r"assets/search/dictionary\.[0-9a-f]+\.json", page).group(0)
    data = json.loads((docs_dir / name).read_text(encoding="utf-8"))
    assert data["v"] == 2 and len(data["rows"]) > 4000


def test_accessibility_basics(docs_dir):
    for locale in ["pt", "en"]:
        for page in PAGES[1:]:
            content = (docs_dir / locale / f"{page}.html").read_text(encoding="utf-8")
            if "td-redirect" in content or "location.replace" in content[:3000]:
                continue  # dictionary.html forwards old ?entry= / ?search= links
            assert 'class="td-skip"' in content and 'href="#main"' in content, f"{locale}/{page}"
            assert 'id="main"' in content and "<main" in content, f"{locale}/{page}"


def test_lang_attribute(docs_dir):
    assert '<html lang="pt-BR"' in (docs_dir / "pt" / "index.html").read_text(encoding="utf-8")
    assert '<html lang="en"' in (docs_dir / "en" / "index.html").read_text(encoding="utf-8")


def test_language_switcher(docs_dir):
    pt = (docs_dir / "pt" / "index.html").read_text(encoding="utf-8")
    en = (docs_dir / "en" / "index.html").read_text(encoding="utf-8")
    assert 'class="td-lang"' in pt and "../en/index.html" in pt
    assert "../pt/index.html" in en


def test_article_pages_exist(docs_dir):
    for locale in ["pt", "en"]:
        pages = list((docs_dir / locale / "encyclopedia").glob("*.html"))
        assert len(pages) > 100, f"{locale}: {len(pages)} article pages"


def test_article_page(docs_dir):
    content = (docs_dir / "pt" / "encyclopedia" / "ecerae.html").read_text(encoding="utf-8")
    assert '<html lang="pt-BR"' in content and "td-article" in content
    assert 'href="../encyclopedia.html' in content
    assert '../../en/encyclopedia/ecerae.html' in content
    assert "../bibliography.html#ref-" in content


def test_encyclopedia_list_links_to_articles(docs_dir):
    content = (docs_dir / "pt" / "encyclopedia.html").read_text(encoding="utf-8")
    assert 'href="encyclopedia/ecerae.html"' in content
