#!/usr/bin/env python3
"""
Categorize uncategorized encyclopedia entries, normalize existing categories,
and add see_also links based on content analysis.

Run from project root:
    .venv/bin/python scripts/categorize_entries.py
"""

import yaml
import re
from pathlib import Path

DATA_DIR = Path("data/encyclopedia")

# ── Category normalization map ──────────────────────────────────────────────
# old_category → new_category (fixes inconsistencies)
NORMALIZE = {
    "cultura material": "cultura-material",
    "organizacao-social": "organização-social",
    "organização social": "organização-social",
    "organizacao-clanica": "organização-social/clãs",
    "organizacao domestica": "cultura-material/vida-doméstica",
    "territorio": "território",
    "historia": "história",
    "musica": "música",
    "gramatica": "gramática",
    "lingua": "língua",
    "ornamentos": "cultura-material/ornamentação",
    "fauna": "natureza/fauna",
    "flora": "natureza/flora",
    "caca": "natureza/fauna/caça",
    "clas": "organização-social/clãs",
    "nomes-clanicos": "nomes-próprios/clânicos",
    "nomes próprios": "nomes-próprios",
    "nomes-proprios": "nomes-próprios",
    "termos relacionais": "linguística/termos-relacionais",
    "advérbios": "linguística/advérbios",
    "morfossintaxe": "linguística/morfossintaxe",
    "gramática": "linguística/gramática",
    "saude": "saúde",
    "costumes": "sociedade/costumes",
    "subsistencia": "sociedade/subsistência",
    "mobilidade": "sociedade/mobilidade",
    "cuidado infantil": "sociedade/cuidado-infantil",
    "práticas corporais": "corpo/práticas",
    "práticas cotidianas": "sociedade/vida-cotidiana",
    "vida cotidiana": "sociedade/vida-cotidiana",
    "vida social": "sociedade/vida-social",
    "vida-social": "sociedade/vida-social",
    "reciprocidade": "sociedade/reciprocidade",
    "morte": "cosmologia/morte",
    "ancestralidade": "cosmologia/antepassados",
    "mitologia": "cosmologia/mitologia",
    "xamanismo": "cosmologia/xamanismo",
    "religião": "cosmologia/religião",
    "comunicação": "linguística/comunicação",
    "linguagem": "linguística",
    "hidrografia": "geografia/hidrografia",
    "tradição oral": "tradição-oral",
    "língua": "linguística",
    "história": "etnografia/história",
    "anatomia": "corpo",
    "parentesco": "sociedade/parentesco",
    "cerimonial": "ritual",

    "alimentacao": "cultura-material/alimentação",
    "bebidas": "cultura-material/alimentação",
    "plantas": "natureza/flora",
    "substancias": "cultura-material/substâncias",
    "tecnologia": "cultura-material/tecnologia",
    "tecnologia tradicional": "cultura-material/tecnologia",
    "economia": "sociedade/economia",
    "magia": "cosmologia/xamanismo",
    "cosmetica ritual": "ritual/cosmética",
    "etnobotanica": "natureza/flora",
    "botânica": "natureza/flora",
    "arquitetura": "cultura-material/habitação",
    "etnologia": "etnografia",
    "sociedade/contato": "sociedade/contato",
    "sociedade/organização-social": "organização-social",
    "sociedade/organização-social/metades": "organização-social/metades",
    "sociedade/organização-social/clãs": "organização-social/clãs",
    "etnografia/história": "etnografia/história",
    "sociedade/espaço-social": "sociedade/espaço-social",
    "linguística/polissemia": "linguística/polissemia",
    "linguística/topônimo": "linguística/topônimo",
}

# ── New categories for uncategorized entries ────────────────────────────────
NEW_CATEGORIES = {
    # ── Fauna: birds ──
    "ceje": ["natureza/fauna/ave"],
    "cijiji": ["natureza/fauna/ave"],
    "cinadatao": ["natureza/fauna/ave"],
    "ciwororo": ["natureza/fauna/ave"],
    "ciwabo": ["natureza/fauna/ave"],
    "ciwabo-bataru-okeadu": ["natureza/fauna/ave"],
    "ciwae": ["natureza/fauna/ave"],
    "cucu": ["natureza/fauna/ave"],
    "uwarinogo": ["natureza/fauna/ave"],
    "kurugugwa-ywariga": ["natureza/fauna/ave"],
    "ciwu": ["natureza/fauna/ave"],
    "jajadoge": ["natureza/fauna/ave"],
    "jajadoge-2": ["natureza/fauna"],

    # ── Fauna: mammals ──
    "adugo-aredu": ["natureza/fauna/mamífero", "ritual"],
    "adugodo": ["natureza/fauna/mamífero"],
    "jakorewu": ["natureza/fauna/mamífero"],
    "jugodoge-eimiejera-uiorubo": ["natureza/fauna/mamífero", "cosmologia/xamanismo"],

    # ── Fauna: insects ──
    "kurugutugu": ["natureza/fauna/inseto"],
    "ciriwore": ["natureza/fauna/inseto", "cosmologia/espírito"],

    # ── Fauna: general ──
    "kururewu": ["sociedade/vida-cotidiana"],

    # ── Flora ──
    "bokwado": ["natureza/flora"],
    "ciocio": ["natureza/flora"],
    "kuogo-i": ["natureza/flora"],
    "itoborewu": ["natureza/flora/palmeira"],
    "akiri-i-kuru": ["natureza/flora"],
    "ewo-o-jorubo": ["natureza/flora", "cosmologia/xamanismo"],
    "ciwaje-uiorubo": ["natureza/flora", "cosmologia/xamanismo"],
    "tadari": ["natureza/flora", "cultura-material/alimentação"],
    "tadari-umana": ["natureza/flora", "cultura-material/alimentação"],

    # ── Food ──
    "boe-eke": ["cultura-material/alimentação"],

    # ── Cultural material: ornaments & adornment ──
    "adugo-biri": ["cultura-material/ornamentação", "ritual"],
    "pariko": ["cultura-material/ornamentação", "ritual"],
    "kurugugwa-upebo": ["cultura-material/ornamentação"],
    "cibaiwodo": ["cultura-material/ornamentação"],
    "cibae-egyrea": ["cultura-material/ornamentação"],
    "cibaiwo": ["cultura-material"],
    "cibaiwo-ekurewu": ["cultura-material/ornamentação"],
    "cibaiwo-je-ekurewu": ["cultura-material/ornamentação"],
    "cibaiwo-kujagurewu": ["cultura-material/ornamentação"],
    "cinadatao-imo": ["cultura-material/ornamentação", "ritual"],
    "ciwaje-atugo": ["cultura-material/ornamentação", "ritual"],
    "ciwabo-biri": ["cultura-material/ornamentação", "natureza/fauna/ave"],
    "ciwabo-bataru-okeadu-biri": ["cultura-material/ornamentação", "natureza/fauna/ave"],
    "ciwabo-boro": ["cultura-material/ornamentação"],
    "jakomea-atugo-padure-paru-jiwu-pariko": ["cultura-material/ornamentação", "ritual"],
    "boe-ekudawu": ["cultura-material"],

    # ── Cultural material: weapons ──
    "jakomea-ika": ["cultura-material/arma"],
    "jakomea-utugo": ["cultura-material/arma"],
    "jakomea-utugo-by-ekurewu": ["cultura-material/arma"],
    "jakomea-utugo-by-kujagurewu": ["cultura-material/arma"],

    # ── Music / instruments ──
    "ceje-bari": ["música", "cultura-material"],
    "jure-bari": ["música", "cultura-material"],

    # ── Ritual / spiritual ──
    "adugodoge-aroe": ["ritual/representações", "cosmologia/espírito"],
    "aroe-etawara-are": ["cosmologia/espírito"],
    "aroe-jakomea-po": ["cosmologia/espírito"],
    "aroe-kodu": ["cosmologia/espírito"],
    "aroe-maiwu": ["cosmologia/espírito"],
    "bope": ["cosmologia/espírito"],
    "jakomea": ["cosmologia/espírito"],
    "ciwae-aroe": ["ritual/representações"],
    "ciwaje-aroe": ["ritual/representações"],
    "mano-akurararewu-aroe": ["ritual"],
    "mano-aroe": ["ritual"],
    "mano-kurirewu": ["ritual"],
    "tabo": ["cosmologia/espírito"],
    "erubo": ["cosmologia/xamanismo", "natureza/flora"],
    "amoe-erubo": ["cosmologia/xamanismo"],

    # ── Linguistic: advérbios ──
    "cai": ["linguística/advérbios"],
    "caije": ["linguística/advérbios"],
    "camu": ["linguística/advérbios"],
    "camugogo": ["linguística/advérbios"],
    "cebegi": ["linguística/advérbios"],
    "coboje": ["linguística/advérbios"],
    "cigo": ["linguística/advérbios"],
    "cigocigo": ["linguística/advérbios"],
    "jagu": ["linguística/advérbios"],
    "woe": ["linguística/advérbios"],
    "ce-2": ["linguística/advérbios"],

    # ── Linguistic: gramática / pronomes ──
    "ce-4": ["linguística/gramática"],
    "cegi": ["linguística/gramática"],
    "cewy": ["linguística/gramática"],
    "ma-3": ["linguística/gramática"],
    "akodo": ["linguística", "música"],
    "bataru": ["linguística"],

    # ── Linguistic: léxico ──
    "ce": ["linguística"],
    "ce-3": ["linguística"],
    "ceboere": ["linguística"],
    "cebegiwu": ["linguística"],
    "cerewu": ["linguística"],
    "co": ["linguística"],
    "cobogiwu": ["linguística"],
    "cobogiwu-2": ["linguística"],
    "jaku": ["linguística"],
    "mae-1": ["linguística"],
    "maedo-1": ["linguística"],
    "maedodu-1": ["linguística"],
    "maedodurewu-1": ["linguística"],
    "maegodu-1": ["linguística"],
    "maegodu-1-2": ["linguística"],
    "maekodudo-1": ["linguística"],
    "mori-2": ["linguística"],
    "ra-2": ["linguística", "corpo"],
    "rakojerewu": ["linguística"],
    "ta": ["linguística"],
    "carugirirabo": ["linguística"],

    # ── Body / anatomy ──
    "ao": ["corpo"],
    "iwu": ["corpo"],

    # ── Proper names ──
    "jakomea-ekure": ["nomes-próprios"],
    "jakomea-enawu": ["nomes-próprios"],
    "jakomea-epa": ["nomes-próprios"],
    "jakomea-ewoeiga": ["nomes-próprios"],
    "jakomea-kago": ["nomes-próprios"],
    "jakomea-kurirewu": ["nomes-próprios"],
    "jakomea-mugu": ["nomes-próprios"],
    "jakomea-okwoda": ["nomes-próprios"],
    "jakomea-ruko": ["nomes-próprios"],
    "jakoro-wari": ["nomes-próprios"],
    "cenawu-kyri": ["nomes-próprios"],
    "cibae-eceba": ["nomes-próprios"],
    "cibae-modojeba": ["nomes-próprios"],
    "cibairago": ["nomes-próprios"],
    "cibairewu": ["nomes-próprios"],

    # ── Geography ──
    "cibae-eiari": ["geografia"],
    "cibaibo": ["geografia/hidrografia"],
    "cibaibo-bororo": ["geografia"],
    "cibaiborewu": ["geografia/hidrografia"],
    "ciwabori": ["geografia"],
    "ciwabori-bororo": ["geografia"],
    "ciwu-baga": ["geografia/hidrografia"],
    "jakorewuge-eiao": ["geografia/hidrografia"],
    "tori": ["linguística", "geografia"],

    # ── Social / clan ──
    "bokodori-ecerae": ["organização-social/clãs"],
    "cibae-ecerae": ["organização-social/clãs"],
    "tugarege": ["organização-social/metades"],
    "okoge": ["organização-social/clãs"],

    # ── Oral tradition ──
    "boe-ewadaru": ["tradição-oral"],

    # ── Society / daily life ──
    "tubore-tubore": ["sociedade/vida-cotidiana"],
    "butao-butu": ["natureza"],

    # ── Remaining entries with limited info ──
    "ae": ["linguística"],
    "aredu": ["linguística"],
    "no": ["linguística"],
    "ro": ["linguística"],
    "bari": ["linguística"],
    "baado-jebage-cebegiwuge": ["ritual"],
    "bai-mana-gejewu": ["ritual"],
    "bapo-kurirewu": ["ritual"],
    "baporogu": ["ritual"],
    "baraedu": ["linguística"],
    "beo-uke-jorubo": ["cosmologia/xamanismo"],
    "boadody": ["sociedade"],
    "boe-eimejera": ["sociedade"],
    "boe-epa": ["sociedade"],
    "cibae": ["natureza/fauna/ave"],
    "ery-pa": ["linguística"],
    "ikuieje": ["linguística"],
    "iworo": ["linguística"],
    "kamorewu": ["linguística"],
    "pogubo-cerewu": ["linguística"],
}


# ── see_also links ──────────────────────────────────────────────────────────
# Based on content families (shared prefixes, conceptual links)
SEE_ALSO = {
    # Adugo family
    "adugo": ["adugo-aredu", "adugo-biri", "adugodo", "adugodoge-aroe", "adugo-mutillidae"],
    "adugo-aredu": ["adugo", "adugo-biri"],
    "adugo-biri": ["adugo", "adugo-aredu", "pariko"],
    "adugodo": ["adugo"],
    "adugodoge-aroe": ["adugo", "aroe"],
    "adugo-mutillidae": ["adugo"],

    # Aroe family
    "aroe": ["aroe-eceba-kejebo", "aroe-eoprewu", "aroe-etawara-are", "aroe-jakomea-po", "aroe-kodu", "aroe-maiwu", "bope", "itaga"],
    "aroe-eceba-kejebo": ["aroe", "pariko"],
    "aroe-eoprewu": ["aroe"],
    "aroe-etawara-are": ["aroe"],
    "aroe-jakomea-po": ["aroe", "jakomea"],
    "aroe-kodu": ["aroe"],
    "aroe-maiwu": ["aroe"],

    # Jakomea family
    "jakomea": ["aroe", "jakomea-ika", "jakomea-utugo", "jakomea-kaworu", "jakomea-ridurewu"],
    "jakomea-ika": ["jakomea", "arago"],
    "jakomea-utugo": ["jakomea", "jakomea-utugo-by-ekurewu", "jakomea-utugo-by-kujagurewu"],
    "jakomea-utugo-by-ekurewu": ["jakomea-utugo"],
    "jakomea-utugo-by-kujagurewu": ["jakomea-utugo"],
    "jakomea-atugo-padure-paru-jiwu-pariko": ["jakomea", "pariko"],
    "jakomea-kaworu": ["jakomea"],
    "jakomea-ridurewu": ["jakomea"],
    "jakomea-ekure": ["jakomea"],
    "jakomea-enawu": ["jakomea"],
    "jakomea-epa": ["jakomea"],
    "jakomea-ewoeiga": ["jakomea"],
    "jakomea-kago": ["jakomea"],
    "jakomea-kurirewu": ["jakomea"],
    "jakomea-mugu": ["jakomea"],
    "jakomea-okwoda": ["jakomea"],
    "jakomea-ruko": ["jakomea"],

    # Cibae family
    "cibae-ecerae": ["ecerae", "bokodori-ecerae", "cibae-eceraedu"],
    "cibae-eceraedu": ["cibae-ecerae", "ecerae"],
    "cibae-egyrea": ["cibae-ecerae"],
    "cibae-eiari": ["cibae-ecerae"],
    "cibae-eceba": ["cibae-ecerae"],
    "cibae-modojeba": ["cibae-ecerae"],
    "cibairago": ["cibae-ecerae"],
    "cibairewu": ["cibae-ecerae"],

    # Cibaiwo family
    "cibaiwo": ["cibaiwo-ekurewu", "cibaiwo-je-ekurewu", "cibaiwo-kujagurewu", "cibaiwodo"],
    "cibaiwo-ekurewu": ["cibaiwo"],
    "cibaiwo-je-ekurewu": ["cibaiwo"],
    "cibaiwo-kujagurewu": ["cibaiwo"],
    "cibaiwodo": ["cibaiwo", "pariko"],

    # Cibaibo family (geography)
    "cibaibo": ["cibaibo-bororo", "cibaiborewu"],
    "cibaibo-bororo": ["cibaibo"],
    "cibaiborewu": ["cibaibo"],

    # Ciwabo family (birds)
    "ciwabo": ["ciwabo-bataru-okeadu", "ciwabo-biri", "ciwabo-boro"],
    "ciwabo-bataru-okeadu": ["ciwabo", "ciwabo-bataru-okeadu-biri"],
    "ciwabo-bataru-okeadu-biri": ["ciwabo-bataru-okeadu", "ciwabo-biri"],
    "ciwabo-biri": ["ciwabo", "ciwabo-boro"],
    "ciwabo-boro": ["ciwabo", "ciwabo-biri"],
    "ciwabori": ["ciwabori-bororo", "ciwabo"],
    "ciwabori-bororo": ["ciwabori"],

    # Ciwae/Ciwaje family
    "ciwae": ["ciwae-aroe"],
    "ciwae-aroe": ["ciwae", "aroe"],
    "ciwaje-aroe": ["aroe", "ciwaje-atugo"],
    "ciwaje-atugo": ["ciwaje-aroe"],
    "ciwaje-uiorubo": ["ciwae", "erubo"],

    # Ba family (palm, clothing, housing)
    "ba": ["ba-1", "ba-2", "ba-1-leaf", "ba-2-penile-sheath-daily", "ba-3-penile-sheath-festive", "ba-4-crown", "ba-5-house-village"],
    "ba-1": ["ba", "ba-5-house-village"],
    "ba-1-leaf": ["ba", "ba-1"],
    "ba-2": ["ba", "ba-2-penile-sheath-daily"],
    "ba-2-penile-sheath-daily": ["ba-2", "ba-3-penile-sheath-festive"],
    "ba-3-penile-sheath-festive": ["ba-2-penile-sheath-daily", "ba-4-crown"],
    "ba-4-crown": ["ba-3-penile-sheath-festive", "pariko"],
    "ba-5-house-village": ["ba-1", "boe-ewa"],

    # Boe family
    "boe": ["boe-ewa", "boe-eke", "boe-ekudawu", "boe-epa", "boe-eimejera", "boe-ewadaru"],
    "boe-ewa": ["boe", "ba-5-house-village", "ecerae", "tugarege"],
    "boe-eke": ["boe"],
    "boe-ekudawu": ["boe"],
    "boe-epa": ["boe"],
    "boe-eimejera": ["boe"],
    "boe-ewadaru": ["boe", "bakaru"],

    # Moieties and clans
    "ecerae": ["tugarege", "boe-ewa", "bokodori-ecerae", "cibae-ecerae"],
    "tugarege": ["ecerae", "boe-ewa"],
    "bokodori-ecerae": ["ecerae", "cibae-ecerae"],
    "okoge": ["ecerae", "tugarege"],

    # Mano family (ritual)
    "mano": ["mano-pa", "mano-aroe", "mano-akurararewu-aroe", "mano-kurirewu"],
    "mano-pa": ["mano", "mano-aroe"],
    "mano-aroe": ["mano", "mano-pa", "aroe"],
    "mano-akurararewu-aroe": ["mano", "aroe"],
    "mano-kurirewu": ["mano"],

    # Spiritual
    "bope": ["aroe", "tabo"],
    "tabo": ["bope", "aroe"],
    "erubo": ["amoe-erubo", "ewo-o-jorubo", "beo-uke-jorubo"],
    "amoe-erubo": ["erubo"],
    "ewo-o-jorubo": ["erubo"],
    "beo-uke-jorubo": ["erubo"],

    # Food
    "tadari": ["tadari-umana", "boe-eke"],
    "tadari-umana": ["tadari"],

    # Ornaments
    "pariko": ["ba-4-crown", "aroe-eceba-kejebo", "kurugugwa-upebo"],
    "kurugugwa-upebo": ["pariko"],
    "kurugugwa-ywariga": ["kurugugwa-upebo"],

    # Linguistic: mae family
    "mae-1": ["maedo-1", "maedodu-1"],
    "maedo-1": ["mae-1", "maedodu-1", "maedodurewu-1"],
    "maedodu-1": ["maedo-1", "maedodurewu-1"],
    "maedodurewu-1": ["maedodu-1"],
    "maegodu-1": ["maegodu-1-2", "maekodudo-1"],
    "maegodu-1-2": ["maegodu-1"],
    "maekodudo-1": ["maegodu-1"],

    # Instruments
    "ceje-bari": ["jure-bari", "ceje", "akodo"],
    "jure-bari": ["ceje-bari", "akodo"],

    # Geography
    "ciwu-baga": ["ciwu"],
    "jakorewuge-eiao": ["jakorewu"],
    "jakorewu": ["jakorewuge-eiao"],

    # Body
    "ao": ["iwu"],
    "iwu": ["ao", "ra-2"],
    "ra-2": ["iwu"],

    # Misc cross-links
    "bakaru": ["tradição-oral", "boe-ewadaru"],
    "arago": ["jakomea-ika"],
    "itaga": ["aroe", "mori"],
    "awara-are": ["boe-ewa"],
}


def load_entry(path: Path):
    """Load a markdown file and return (front_matter_dict, body_text, raw_text)."""
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None, text, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text, text

    fm = yaml.safe_load(parts[1])
    body = parts[2]
    return fm, body, text


def save_entry(path: Path, fm: dict, body: str):
    """Save front matter + body back to file."""
    # Ensure consistent field order
    ordered_keys = [
        "id", "title", "variants", "abstract", "categories", "date", "url",
        "images", "examples", "entry_type", "infobox", "references", "see_also"
    ]
    ordered_fm = {}
    for k in ordered_keys:
        if k in fm:
            ordered_fm[k] = fm[k]
    # Add any remaining keys
    for k in fm:
        if k not in ordered_fm:
            ordered_fm[k] = fm[k]

    yaml_str = yaml.dump(ordered_fm, allow_unicode=True, default_flow_style=False, sort_keys=False)
    path.write_text(f"---\n{yaml_str}---{body}", encoding="utf-8")


def normalize_categories(cats: list) -> list:
    """Apply normalization map to a list of categories."""
    result = []
    for cat in cats:
        normalized = NORMALIZE.get(cat, cat)
        if normalized not in result:
            result.append(normalized)
    return result


def main():
    files = sorted(DATA_DIR.glob("*.md"))
    stats = {"categorized": 0, "normalized": 0, "see_also_added": 0, "skipped": 0}

    for f in files:
        fm, body, raw = load_entry(f)
        if fm is None:
            stats["skipped"] += 1
            continue

        entry_id = fm.get("id", f.stem)
        changed = False

        # 1. Normalize existing categories
        old_cats = fm.get("categories", []) or []
        if old_cats:
            new_cats = normalize_categories(old_cats)
            if new_cats != old_cats:
                fm["categories"] = new_cats
                changed = True
                stats["normalized"] += 1

        # 2. Add categories to uncategorized entries
        if not old_cats and entry_id in NEW_CATEGORIES:
            fm["categories"] = NEW_CATEGORIES[entry_id]
            changed = True
            stats["categorized"] += 1

        # 3. Add see_also links
        if entry_id in SEE_ALSO:
            old_see_also = fm.get("see_also", []) or []
            new_see_also = SEE_ALSO[entry_id]
            # Filter to only include IDs that actually exist as files
            existing_ids = {p.stem for p in files}
            valid_see_also = [s for s in new_see_also if s in existing_ids]
            if valid_see_also and set(valid_see_also) != set(old_see_also):
                fm["see_also"] = valid_see_also
                changed = True
                stats["see_also_added"] += 1

        if changed:
            save_entry(f, fm, body)

    # Summary
    remaining = 0
    for f in files:
        fm, _, _ = load_entry(f)
        if fm and not (fm.get("categories") or []):
            remaining += 1
            print(f"  STILL UNCATEGORIZED: {fm.get('id', f.stem)}")

    print(f"\nDone!")
    print(f"  Categorized: {stats['categorized']}")
    print(f"  Normalized:  {stats['normalized']}")
    print(f"  See-also:    {stats['see_also_added']}")
    print(f"  Skipped:     {stats['skipped']}")
    print(f"  Still uncategorized: {remaining}")


if __name__ == "__main__":
    main()
