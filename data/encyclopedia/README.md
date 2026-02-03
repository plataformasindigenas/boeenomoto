# Encyclopedia Entry Guide

Each entry lives in `data/encyclopedia/<id>.md` and uses YAML front matter plus a
markdown body.

## Front Matter (YAML)

Required:
- `id` (string, unique, stable)
- `headword` (string)

Optional (defaults shown):
- `variants` (list, default `[]`)
- `summary` (string, optional)
- `keywords` (list, default `[]`)
- `updated_at` (string, recommended `YYYY-MM-DD`)
- `url` (string, optional)
- `images` (list, default `[]`)
- `examples` (list, default `[]`)

### `images` format
```yaml
images:
  - url: https://example.com/image.jpg
    alt: Descrição da imagem
    credit: Fonte/Autor
```

### `examples` format
```yaml
examples:
  - bororo: Texto em bororo
    translation: Tradução em português
```

## Body (Markdown)

The entry content goes below the front matter. Use standard markdown:

- Headings: `###` and `####` (used for the TOC); do not prefix with numbering (e.g., avoid "1.1")
- Lists, tables, and footnotes are supported
- **No HTML tags** in the body

## Example
```markdown
---
id: arago
headword: Arago
variants: []
summary: Porrete de madeira.
keywords:
  - arma
  - caça
  - porrete
updated_at: "2026-02-03"
url: ""
images: []
examples: []
---

Com esta denominação designam-se verdadeiros cacetes...

### 1.1 Principais tipos de porretes

#### Arago akurararewu

Pequeno cacete...
```
