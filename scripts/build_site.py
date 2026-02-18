#!/usr/bin/env python3
"""
Build the Boe Eno Moto site with i18n support.

For each locale (pt, en), generates HTML pages in docs/{locale}/.
Also generates individual encyclopedia article pages in docs/{locale}/encyclopedia/.
Also generates a root docs/index.html language picker.
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
DOCS_DIR = BASE_DIR / "docs"
LOCALES_DIR = BASE_DIR / "locales"
DATA_DIR = BASE_DIR / "data"
TEMPLATE_DIR = CONFIG_DIR / "templates"

LOCALES = ["pt", "en"]
DEFAULT_LOCALE = "pt"


def load_locale(locale: str) -> dict:
    path = LOCALES_DIR / f"{locale}.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _generate_toc(content_html: str, entry_id: str) -> tuple[str, str]:
    """Generate a table of contents from h3/h4 headings and add IDs to them.

    Returns (toc_html, modified_content_html).
    """
    heading_re = re.compile(r"<h([34])([^>]*)>([^<]+)</h\1>", re.IGNORECASE)
    headings = []
    index = 0

    for match in heading_re.finditer(content_html):
        level = match.group(1)
        text = match.group(3).strip()
        heading_id = f"{entry_id}-section-{index}"
        headings.append({"level": level, "text": text, "id": heading_id})
        index += 1

    if len(headings) < 2:
        return "", content_html

    # Build TOC HTML
    toc_parts = ['<div class="toc"><div class="toc-title">']
    toc_parts.append("</div><ul class='toc-list'>")
    for i, h in enumerate(headings):
        cls = ' class="toc-h4"' if h["level"] == "4" else ""
        toc_parts.append(
            f'<li{cls}><a href="#{h["id"]}">{i + 1}. {h["text"]}</a></li>'
        )
    toc_parts.append("</ul></div>")
    toc_html = "".join(toc_parts)

    # Add IDs to headings in content
    index = 0

    def _add_id(match):
        nonlocal index
        level = match.group(1)
        attrs = match.group(2)
        text = match.group(3)
        heading_id = f"{entry_id}-section-{index}"
        index += 1
        return f'<h{level}{attrs} id="{heading_id}">{text}</h{level}>'

    modified_content = heading_re.sub(_add_id, content_html)

    return toc_html, modified_content


def render_article_pages(locale: str, translations: dict):
    """Render individual encyclopedia article pages."""
    enc_file = DATA_DIR / "encyclopedia.json"
    if not enc_file.exists():
        print(f"  [{locale}] No encyclopedia.json found, skipping article pages")
        return

    with open(enc_file, "r", encoding="utf-8") as f:
        enc_data = json.load(f)

    entries = enc_data["data"]
    if not entries:
        return

    # Build title lookup for see_also resolution
    all_titles = {e["id"]: e.get("title", e["id"]) for e in entries}

    other_locale = [l for l in LOCALES if l != locale][0]

    # Create encyclopedia subdirectory
    enc_dir = DOCS_DIR / locale / "encyclopedia"
    enc_dir.mkdir(parents=True, exist_ok=True)

    # Set up Jinja2 environment
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,
    )
    template = env.get_template("article.html.j2")

    for entry in entries:
        entry_id = entry.get("id", "")
        if not entry_id:
            continue

        content_html = entry.get("content_html", "")
        toc_html = ""
        if content_html:
            toc_html, content_html = _generate_toc(content_html, entry_id)
            # Update entry with modified content that has heading IDs
            entry["content_html"] = content_html

        html = template.render(
            entry=entry,
            toc_html=toc_html,
            all_titles=all_titles,
            t=translations,
            locale=locale,
            other_locale=other_locale,
            base_path="../../",
            page="encyclopedia",
            title=entry.get("title", ""),
        )

        output_path = enc_dir / f"{entry_id}.html"
        output_path.write_text(html, encoding="utf-8")

    print(f"  [{locale}] Rendered {len(entries)} article pages in encyclopedia/")


def build_locale(locale: str, translations: dict):
    """Build all pages for a given locale."""
    locale_dir = DOCS_DIR / locale
    locale_dir.mkdir(parents=True, exist_ok=True)

    other_locale = [l for l in LOCALES if l != locale][0]

    for config_path in sorted(CONFIG_DIR.glob("*.yaml")):
        name = config_path.stem

        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # Override output to locale subdirectory
        original_output = config.get("output", "")
        output_filename = Path(original_output).name
        config["output"] = f"../docs/{locale}/{output_filename}"

        # Add translations and locale context
        ctx = config.get("context", {})
        ctx["t"] = translations
        ctx["locale"] = locale
        ctx["other_locale"] = other_locale
        ctx["base_path"] = "../"
        config["context"] = ctx

        # Write temporary config
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", dir=str(CONFIG_DIR),
            delete=False, encoding="utf-8"
        ) as tmp:
            yaml.dump(config, tmp, allow_unicode=True, default_flow_style=False)
            tmp_path = Path(tmp.name)

        try:
            subprocess.run(
                [sys.executable.replace("python", "kodudo"), "cook", str(tmp_path)],
                check=True, capture_output=True, text=True
            )
        except subprocess.CalledProcessError as e:
            # Try finding kodudo in the same venv
            kodudo_path = Path(sys.executable).parent / "kodudo"
            subprocess.run(
                [str(kodudo_path), "cook", str(tmp_path)],
                check=True
            )
        finally:
            tmp_path.unlink()

        print(f"  [{locale}] Rendered {name}")

    # Render individual article pages
    render_article_pages(locale, translations)

    # Copy data files for fetch-based pages
    for name in ("dictionary-data", "encyclopedia-data"):
        src = DOCS_DIR / f"{name}.json"
        if src.exists():
            dst = locale_dir / f"{name}.json"
            shutil.copy2(src, dst)


def build_language_picker():
    """Generate root docs/index.html with language selection."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Boe Eno Moto</title>
    <style>
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            max-width: 600px;
            margin: 0 auto;
            padding: 2rem 1rem;
            background: #F9F6F2;
            color: #333;
            text-align: center;
        }
        h1 { color: #3D352F; font-size: 2.5rem; margin-bottom: 0.5rem; }
        .subtitle { color: #666; font-size: 1.2rem; margin-bottom: 2rem; }
        .languages {
            display: flex;
            gap: 1.5rem;
            justify-content: center;
            flex-wrap: wrap;
        }
        .lang-card {
            display: block;
            background: white;
            border: 1px solid #E8E4DF;
            border-radius: 4px;
            padding: 2rem 3rem;
            text-decoration: none;
            color: inherit;
            transition: border-color 0.2s;
            min-width: 200px;
        }
        .lang-card:hover { border-color: #C75B39; }
        .lang-card h2 { margin: 0 0 0.25rem 0; color: #3D352F; }
        .lang-card p { margin: 0; color: #666; font-size: 0.9rem; }
    </style>
</head>
<body>
    <h1>Boe Eno Moto</h1>
    <p class="subtitle">Mundo Bororo / Bororo World</p>
    <div class="languages">
        <a href="pt/index.html" class="lang-card">
            <h2>Português</h2>
            <p>Acessar em Português</p>
        </a>
        <a href="en/index.html" class="lang-card">
            <h2>English</h2>
            <p>Access in English</p>
        </a>
    </div>
</body>
</html>
"""
    (DOCS_DIR / "index.html").write_text(html, encoding="utf-8")
    print("  Generated language picker at docs/index.html")


def main():
    print("=== Building i18n Site ===\n")

    for locale in LOCALES:
        print(f"Building locale: {locale}")
        translations = load_locale(locale)
        build_locale(locale, translations)
        print()

    build_language_picker()
    print("\n=== i18n Build Complete ===")


if __name__ == "__main__":
    main()
