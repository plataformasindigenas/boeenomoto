# Boe Eno Moto

Linguistic and cultural resources platform for the Bororo people.

## Repository Structure

```
boeenomoto/
├── data/                    # Source data and schemas
│   ├── dictionary.tsv       # Bororo dictionary (source)
│   ├── dictionary_schema.yaml
│   ├── encyclopedia.json    # Bororo encyclopedia (source)
│   ├── encyclopedia_schema.yaml
│   ├── fauna.yaml           # Bororo fauna (source)
│   └── fauna_schema.yaml
├── config/                  # Generation configuration
│   ├── templates/           # Jinja2 templates
│   │   ├── base.html.j2
│   │   ├── dictionary.html.j2
│   │   ├── encyclopedia.html.j2
│   │   ├── fauna.html.j2
│   │   └── index.html.j2
│   ├── dictionary.yaml      # kodudo config for dictionary
│   ├── encyclopedia.yaml    # kodudo config for encyclopedia
│   ├── fauna.yaml           # kodudo config for fauna
│   └── index.yaml           # kodudo config for index
├── docs/                    # Generated site (GitHub Pages)
├── scripts/
│   ├── convert.py           # Data conversion with aptoro
│   └── build.sh             # Full build script
└── .github/workflows/
    └── build-deploy.yml     # CI/CD for GitHub Pages
```

## Available Platforms

- **Dictionary**: Words and expressions in the Bororo language with Portuguese translations
- **Encyclopedia**: Entries about culture, rituals, social organization, and traditional knowledge of the Bororo people
- **Fauna**: Animal names in the Bororo language with traditional classification

## Local Development

### Requirements

- Python 3.11+
- [aptoro](https://github.com/plataformasindigenas/aptoro)
- [kodudo](https://github.com/plataformasindigenas/kodudo)

### Installation

```bash
pip install aptoro kodudo
```

### Build

```bash
# Full build
./scripts/build.sh

# Or step by step:
python scripts/convert.py              # Convert data to JSON
kodudo cook config/dictionary.yaml config/encyclopedia.yaml config/fauna.yaml config/index.yaml  # Generate HTML
```

### Preview

Open `docs/index.html` in your browser.

## Deployment

The site is automatically published to GitHub Pages when there are changes to the `data/`, `config/`, or `scripts/` directories on the `master` branch.

Manual deployment can also be triggered via GitHub Actions.

## Adding a New Platform

1. Add the data file to `data/` (TSV, YAML, or JSON)
2. Create the schema at `data/<name>_schema.yaml`
3. Update `scripts/convert.py` to process the new dataset
4. Create the template at `config/templates/<name>.html.j2`
5. Create the kodudo config at `config/<name>.yaml`
6. Update `scripts/build.sh` and the workflow to include the new config
7. Update `config/templates/base.html.j2` to include the link in the navigation
8. Update `config/templates/index.html.j2` to include the card on the landing page

## License

GPL-3.0-or-later

## Project

Part of the [Plataformas Indigenas](https://github.com/plataformasindigenas) initiative.
