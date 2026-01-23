# Boe Eno Moto

Plataforma de recursos linguisticos e culturais do povo Bororo.

## Estrutura do Repositorio

```
boeenomoto/
├── data/                    # Dados fonte e schemas
│   ├── dictionary.tsv       # Dicionario Bororo (fonte)
│   ├── dictionary_schema.yaml
│   ├── fauna.yaml           # Fauna Bororo (fonte)
│   └── fauna_schema.yaml
├── config/                  # Configuracao de geracao
│   ├── templates/           # Templates Jinja2
│   │   ├── base.html.j2
│   │   ├── dictionary.html.j2
│   │   ├── fauna.html.j2
│   │   └── index.html.j2
│   ├── dictionary.yaml      # Config kodudo para dicionario
│   ├── fauna.yaml           # Config kodudo para fauna
│   └── index.yaml           # Config kodudo para index
├── docs/                    # Site gerado (GitHub Pages)
├── scripts/
│   ├── convert.py           # Conversao de dados com aptoro
│   └── build.sh             # Script de build completo
└── .github/workflows/
    └── build-deploy.yml     # CI/CD para GitHub Pages
```

## Plataformas Disponiveis

- **Dicionario**: Palavras e expressoes da lingua Bororo com traducao para Portugues
- **Fauna**: Nomes de animais na lingua Bororo com classificacao tradicional

## Desenvolvimento Local

### Requisitos

- Python 3.11+
- [aptoro](https://github.com/plataformasindigenas/aptoro)
- [kodudo](https://github.com/plataformasindigenas/kodudo)

### Instalacao

```bash
pip install aptoro kodudo
```

### Build

```bash
# Build completo
./scripts/build.sh

# Ou passo a passo:
python scripts/convert.py              # Converte dados para JSON
kodudo cook config/dictionary.yaml config/fauna.yaml config/index.yaml  # Gera HTML
```

### Preview

Abra `docs/index.html` no navegador.

## Deploy

O site e automaticamente publicado no GitHub Pages quando ha mudancas nos diretórios `data/`, `config/`, ou `scripts/` na branch `main`.

Tambem e possivel disparar o deploy manualmente via GitHub Actions.

## Adicionar Nova Plataforma

1. Adicione o arquivo de dados em `data/` (TSV, YAML, ou JSON)
2. Crie o schema em `data/<nome>_schema.yaml`
3. Atualize `scripts/convert.py` para processar o novo dataset
4. Crie o template em `config/templates/<nome>.html.j2`
5. Crie a config kodudo em `config/<nome>.yaml`
6. Atualize `scripts/build.sh` e o workflow para incluir a nova config
7. Atualize `config/templates/base.html.j2` para incluir o link na navegacao
8. Atualize `config/templates/index.html.j2` para incluir o card na landing page

## Licenca

GPL-3.0-or-later

## Projeto

Parte da iniciativa [Plataformas Indigenas](https://github.com/plataformasindigenas).

