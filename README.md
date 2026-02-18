# Boe Eno Moto

Linguistic and cultural resources platform for the Bororo people.

## Repository Structure

```
boeenomoto/
├── data/                    # Source data and schemas
│   ├── dictionary.tsv       # Bororo dictionary (source)
│   ├── dictionary_schema.yaml
│   ├── encyclopedia/         # Bororo encyclopedia entries (markdown files)
│   ├── encyclopedia_schema.yaml
│   ├── fauna.yaml           # Bororo fauna (source)
│   ├── fauna_schema.yaml
│   ├── bororo.bib           # BibTeX bibliography
│   ├── bibliography_schema.yaml
│   ├── recordings.yaml      # Audio recordings inventory
│   └── recordings_schema.yaml
├── config/                  # Generation configuration
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html.j2
│   │   ├── dictionary.html.j2
│   │   ├── encyclopedia.html.j2
│   │   ├── fauna.html.j2
│   │   ├── bibliography.html.j2
│   │   └── index.html.j2
│   ├── dictionary.yaml      # kodudo config for dictionary
│   ├── encyclopedia.yaml
│   ├── fauna.yaml
│   ├── bibliography.yaml
│   └── index.yaml
├── locales/                 # i18n locale files
│   ├── pt.yaml              # Portuguese (Brazilian)
│   └── en.yaml              # English
├── docs/                    # Generated site (GitHub Pages)
│   ├── index.html           # Language picker
│   ├── pt/                  # Portuguese pages
│   ├── en/                  # English pages
│   ├── js/common.js         # Shared JavaScript utilities
│   ├── images/              # Localized images
│   └── recordings/          # Audio recordings
├── scripts/
│   ├── convert.py           # Data conversion with aptoro
│   ├── build.sh             # Full build script
│   ├── build_site.py        # i18n site generation
│   ├── check_encyclopedia_entries.py
│   ├── convert_audio.py     # WAV to WebM converter
│   ├── download_images.py   # Image downloader
│   └── inventory_recordings.py
├── tests/                   # Test suite
│   ├── conftest.py
│   ├── test_convert.py
│   ├── test_front_matter.py
│   └── test_build.py
└── .github/workflows/
    └── build-deploy.yml     # CI/CD for GitHub Pages
```

## Available Platforms

- **Dictionary**: Words and expressions in the Bororo language with Portuguese translations, phonetic transcriptions, and examples. Includes audio recordings for many entries.
- **Encyclopedia**: Entries about culture, rituals, social organization, and traditional knowledge of the Bororo people.
- **Fauna**: Animal names in the Bororo language with traditional classification, scientific names, and images.
- **Bibliography**: Bibliographic references on the language, culture, and history of the Bororo people.
- **Recordings**: Audio recordings linked to dictionary entries from fieldwork sessions.

## Local Development

### Requirements

- Python 3.11+
- [aptoro](https://github.com/plataformasindigenas/aptoro)
- [kodudo](https://github.com/plataformasindigenas/kodudo)

### Installation

```bash
pip install aptoro kodudo
pip install -r requirements.txt
```

### Build

```bash
# Full build (convert data + render all locales)
./scripts/build.sh

# Or step by step:
python scripts/convert.py              # Convert data to JSON
python scripts/build_site.py           # Render HTML for all locales
```

### Testing

```bash
pip install pytest
pytest tests/ -v
```

### Preview

Open `docs/index.html` in your browser (language picker), or `docs/pt/index.html` / `docs/en/index.html` directly.

## Deployment

The site is automatically published to GitHub Pages when there are changes to the `data/`, `config/`, `scripts/`, or `locales/` directories on the `master` branch.

Manual deployment can also be triggered via GitHub Actions.

## i18n (Internationalization)

The site supports multiple languages. Locale files are stored in `locales/` as YAML files.

### Adding a New Language

1. Copy `locales/pt.yaml` to `locales/{code}.yaml`
2. Translate all strings in the new locale file
3. Add the locale code to `LOCALES` in `scripts/build_site.py`
4. Update the language picker in `build_site.py`'s `build_language_picker()` function

### How It Works

- Templates use `{{ t.key }}` for all user-facing strings
- The build script renders each template once per locale
- Output goes to `docs/{locale}/` subdirectories
- A root `docs/index.html` language picker redirects to locale pages
- Shared assets (JS, images, recordings) live in `docs/` and are referenced via `../`

## Cross-linking

Datasets are automatically cross-linked during the build process:
- Dictionary entries with scientific names are linked to matching Fauna entries (and vice versa)
- Cross-links appear as "See in Fauna" / "See in Dictionary" links in search results
- Clicking a cross-link navigates to the other page with the term pre-filled in the search

## Adding a New Platform

1. Add the data file to `data/` (TSV, YAML, BibTeX, or markdown)
2. Create the schema at `data/<name>_schema.yaml`
3. Add a converter function in `scripts/convert.py` and register it in the `CONVERTERS` dict
4. Create the template at `config/templates/<name>.html.j2`
5. Create the kodudo config at `config/<name>.yaml`
6. Add locale strings to all files in `locales/`
7. Update `config/templates/base.html.j2` to include the link in the navigation
8. Update `config/templates/index.html.j2` to include the card on the landing page

## License

GPL-3.0-or-later

## Project

Part of the [Plataformas Indigenas](https://github.com/plataformasindigenas) initiative.
