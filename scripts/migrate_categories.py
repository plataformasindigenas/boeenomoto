#!/usr/bin/env python3
"""
One-time migration script: convert flat category keywords to hierarchical paths.

Usage:
    python scripts/migrate_categories.py
"""

from pathlib import Path

import yaml

BASE_DIR = Path(__file__).parent.parent
ENTRIES_DIR = BASE_DIR / "data" / "encyclopedia"

# Mapping from flat keywords to hierarchical paths.
# Unmapped keywords are kept as-is and logged for review.
CATEGORY_MAP = {
    # Ritual
    "ritual": "ritual",
    "funeral": "ritual/funeral",
    "ritos fúnebres": "ritual/funeral",
    "canto ritual": "ritual/canto",
    "dança": "ritual/dança",
    "representações rituais": "ritual/representações",
    "pranto ritual": "ritual/pranto",
    "acolhimento ritual": "ritual/acolhimento",
    "adornos rituais": "ritual/adornos",
    "aparência funerária": "ritual/funeral",
    "festas": "ritual/festas",
    "iniciação": "ritual/iniciação",
    "retorno": "ritual/retorno",
    "retribuição": "ritual/retribuição",
    # Cosmologia
    "alma": "cosmologia/alma",
    "espírito": "cosmologia/espírito",
    "fantasma": "cosmologia/espírito",
    "cosmologia": "cosmologia",
    "mitologia": "cosmologia/mitologia",
    "morte": "cosmologia/morte",
    "xamanismo": "cosmologia/xamanismo",
    "metempsicose": "cosmologia/metempsicose",
    "espiritualidade": "cosmologia/espiritualidade",
    "primazia": "cosmologia/primazia",
    "ser primacial": "cosmologia/primazia",
    "antepassados": "cosmologia/antepassados",
    # Sociedade
    "organização social": "sociedade/organização-social",
    "metades exógamas": "sociedade/organização-social/metades",
    "metades": "sociedade/organização-social/metades",
    "clãs": "sociedade/organização-social/clãs",
    "clã": "sociedade/organização-social/clãs",
    "subclã": "sociedade/organização-social/clãs",
    "estrutura social": "sociedade/organização-social",
    "parentesco": "sociedade/parentesco",
    "vida social": "sociedade",
    "obrigação social": "sociedade",
    "vingança": "sociedade/vingança",
    "contato": "sociedade/contato",
    "civilizado": "sociedade/contato",
    "espaço social": "sociedade/espaço-social",
    # Natureza / Fauna
    "animal": "natureza/fauna",
    "mamífero": "natureza/fauna/mamífero",
    "inseto": "natureza/fauna/inseto",
    "himenóptero": "natureza/fauna/inseto",
    "culicídeos": "natureza/fauna/inseto",
    "fauna": "natureza/fauna",
    "ave": "natureza/fauna/ave",
    "arara": "natureza/fauna/ave",
    "felino": "natureza/fauna/mamífero",
    "onça": "natureza/fauna/mamífero",
    "onça-pintada": "natureza/fauna/mamífero",
    "caça": "natureza/fauna/caça",
    "classificação zoológica": "natureza/fauna/classificação",
    "classificação indígena": "natureza/fauna/classificação",
    "classificação simbólica": "natureza/fauna/classificação",
    "analogia zoológica": "natureza/fauna/classificação",
    "metáfora zoológica": "natureza/fauna/classificação",
    "jaquiranabóia": "natureza/fauna",
    "gavião-real": "natureza/fauna/ave",
    "formiga-onça": "natureza/fauna/inseto",
    "mutillidae": "natureza/fauna/inseto",
    "Fulgora": "natureza/fauna/inseto",
    "Mutillidae": "natureza/fauna/inseto",
    # Natureza / Flora
    "botânica": "natureza/flora",
    "etnobotânica": "natureza/flora",
    "palmeira": "natureza/flora/palmeira",
    "babaçu": "natureza/flora/palmeira",
    "acacia": "natureza/flora",
    "angico": "natureza/flora",
    "flora": "natureza/flora",
    "cerrado": "natureza",
    "natureza": "natureza",
    # Cultura material
    "habitação": "cultura-material/habitação",
    "aldeia": "cultura-material/habitação",
    "casa": "cultura-material/habitação",
    "casa central": "cultura-material/habitação",
    "casa do clã": "cultura-material/habitação",
    "arquitetura tradicional": "cultura-material/habitação",
    "praça": "cultura-material/habitação",
    "vestimenta": "cultura-material/vestimenta",
    "indumentária": "cultura-material/vestimenta",
    "estojo peniano": "cultura-material/vestimenta",
    "masculinidade": "cultura-material/vestimenta",
    "coroa": "cultura-material/vestimenta",
    "ornamentação": "cultura-material/ornamentação",
    "ornamentos": "cultura-material/ornamentação",
    "penas": "cultura-material/ornamentação",
    "arte corporal": "cultura-material/ornamentação",
    "corpo": "cultura-material/ornamentação",
    "cultura material": "cultura-material",
    "artesanato": "cultura-material/artesanato",
    "cestaria": "cultura-material/artesanato",
    "arma": "cultura-material/arma",
    "porrete": "cultura-material/arma",
    "urucum": "cultura-material",
    # Linguística
    "polissemy": "linguística/polissemia",
    "topônimo": "linguística/topônimo",
    # Etnografia / História
    "etnografia": "etnografia",
    "história": "etnografia/história",
    # Clãs / Metades nomeados
    "Tugarege": "sociedade/organização-social/metades",
    "Ecerae": "sociedade/organização-social/metades",
    "Aroe": "cosmologia",
    "Aroroe": "sociedade/organização-social/clãs",
    "Baado Jebage": "sociedade/organização-social/clãs",
    "Iwagududoge": "sociedade/organização-social/clãs",
    "Kie": "sociedade/organização-social/clãs",
    "Bororo": "sociedade",
    # Lugares
    "Pogúbo": "geografia",
    "Poxoreu": "geografia",
    "Cuiabá": "geografia",
    "Colônia Teresa Cristina": "geografia",
    "São Lourenço": "geografia",
    "Salesianos": "etnografia/história",
    "córrego": "geografia",
    "viagem": "sociedade",
    "éua": "cultura-material",
    "bái": "cosmologia/xamanismo",
    "bái-mánna-gueggéu": "cosmologia/xamanismo",
}


def _parse_front_matter(path: Path) -> tuple[dict, str]:
    raw = path.read_text(encoding="utf-8")
    if not raw.startswith("---\n"):
        raise ValueError(f"{path}: missing front matter start (---)")

    parts = raw.split("\n---\n", 1)
    if len(parts) != 2:
        raise ValueError(f"{path}: missing front matter end (---)")

    front_matter = yaml.safe_load(parts[0][4:]) or {}
    if not isinstance(front_matter, dict):
        raise ValueError(f"{path}: front matter must be a mapping")

    body = parts[1]
    return front_matter, body


def _write_entry(path: Path, front_matter: dict, body: str) -> None:
    fm_str = yaml.dump(
        front_matter,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
    )
    path.write_text(f"---\n{fm_str}---\n{body}", encoding="utf-8")


def main():
    if not ENTRIES_DIR.exists():
        print(f"Missing encyclopedia directory: {ENTRIES_DIR}")
        return 1

    md_files = sorted(p for p in ENTRIES_DIR.rglob("*.md") if p.name != "README.md")
    print(f"Found {len(md_files)} entries\n")

    unmapped = set()
    migrated = 0

    for path in md_files:
        try:
            front_matter, body = _parse_front_matter(path)
        except Exception as exc:
            print(f"  SKIP {path.name}: {exc}")
            continue

        categories = front_matter.get("categories", [])
        if not categories:
            continue

        new_categories = []
        for cat in categories:
            if cat in CATEGORY_MAP:
                mapped = CATEGORY_MAP[cat]
                if mapped not in new_categories:
                    new_categories.append(mapped)
            else:
                unmapped.add(cat)
                if cat not in new_categories:
                    new_categories.append(cat)

        if new_categories != categories:
            front_matter["categories"] = new_categories
            _write_entry(path, front_matter, body)
            migrated += 1

    print(f"Migrated categories in {migrated} entries")
    if unmapped:
        print(f"\nUnmapped categories ({len(unmapped)}):")
        for cat in sorted(unmapped):
            print(f"  - {cat}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
