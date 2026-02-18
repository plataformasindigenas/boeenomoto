#!/usr/bin/env python3
"""
Build the Boe Eno Moto site with i18n support.

For each locale (pt, en), generates HTML pages in docs/{locale}/.
Also generates a root docs/index.html language picker.
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
CONFIG_DIR = BASE_DIR / "config"
DOCS_DIR = BASE_DIR / "docs"
LOCALES_DIR = BASE_DIR / "locales"

LOCALES = ["pt", "en"]
DEFAULT_LOCALE = "pt"


def load_locale(locale: str) -> dict:
    path = LOCALES_DIR / f"{locale}.yaml"
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


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
