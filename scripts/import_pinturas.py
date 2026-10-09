#!/usr/bin/env python3
"""Import the Boe Ejerare facial paintings as encyclopedia entries.

Source: github.com/LanguageStructure/boe-ejerare (data/pinturas.json +
assets/images/pinturas/). One gallery entry per clan plus an overview entry.
Images are resized for the web into docs/images/pinturas/. Idempotent.

    scripts/import_pinturas.py /path/to/boe-ejerare
"""
import json
import re
import sys
import unicodedata
from collections import OrderedDict
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
OUT_IMG = ROOT / "docs" / "images" / "pinturas"
OUT_MD = ROOT / "data" / "encyclopedia"
MAX_SIDE = 1000
CREDIT = "Boe Ejerare (LanguageStructure/boe-ejerare)"
PLACEHOLDER = "A documentar."
CATEGORIES = ["cultura-material/ornamentação", "organização-social/clãs"]


def slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def yq(s):
    return json.dumps(s, ensure_ascii=False)


def find_image(src, rel):
    p = src / rel
    if p.exists():
        return p
    # a few records point at assets/ root instead of assets/images/pinturas/
    alt = src / "assets" / Path(rel).name
    return alt if alt.exists() else None


def convert(path):
    dest = OUT_IMG / (slug(path.stem) + ".jpg")
    if not dest.exists():
        im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
        im.thumbnail((MAX_SIDE, MAX_SIDE))
        im.save(dest, "JPEG", quality=82, optimize=True, progressive=True)
    return "images/pinturas/" + dest.name


def entry(id_, title, abstract, images, body, see_also, infobox):
    lines = ["---", f"id: {id_}", f"title: {yq(title)}", "variants: []",
             f"abstract: {yq(abstract)}", "categories:"]
    lines += [f"- {c}" for c in CATEGORIES]
    lines += ["date: '2026-10-09'", "url: ''"]
    if images:
        lines.append("images:")
        for url, alt in images:
            lines += [f"- url: {url}", f"  alt: {yq(alt)}", f"  credit: {yq(CREDIT)}"]
    else:
        lines.append("images: []")
    lines += ["examples: []", "entry_type: social_structure", "infobox:"]
    lines += [f"  {k}: {yq(v)}" for k, v in infobox.items()]
    lines += ["references: []", "see_also:"] + [f"- {s}" for s in see_also]
    lines += ["---", "", body, ""]
    return "\n".join(lines)


def main(src):
    src = Path(src)
    data = json.load(open(src / "data" / "pinturas.json"))
    OUT_IMG.mkdir(parents=True, exist_ok=True)

    clans = OrderedDict()
    for p in data:
        clans.setdefault((p["metade"], p["cla"]), []).append(p)

    overview_rows, clan_ids, skipped = [], [], []
    for (metade, cla), items in clans.items():
        cid = "pinturas-" + slug(cla)
        clan_ids.append(cid)
        seen, imgs, rows = set(), [], []
        for p in items:
            path = find_image(src, p["imagem"])
            if path is None:
                skipped.append(p["id"])
                continue
            url = convert(path)
            label = p["nome"] + (f" ({p['subcla']})" if p["subcla"] else "")
            if url not in seen:  # same file twice in one clan gallery
                seen.add(url)
                imgs.append((url, label))
            desc = p["descricao"]
            desc = "" if not desc or desc == PLACEHOLDER else desc
            rows.append(f"- **{label}**" + (f" — {desc}" if desc else ""))
        body = (f"Pinturas faciais do clã **{cla}**, metade **{metade}**. "
                "Descrições marcadas como pendentes foram omitidas; "
                "os dados aguardam validação pela comunidade.\n\n" + "\n".join(rows))
        title = f"Pinturas faciais: {cla}"
        abstract = (f"Pinturas faciais (boe ejiwu) do clã {cla}, metade {metade}: "
                    f"{len(items)} registros.")
        (OUT_MD / f"{cid}.md").write_text(entry(
            cid, title, abstract, imgs, body,
            ["pinturas-faciais", "ecerae" if metade == "Ecerae" else "tugarege"],
            {"metade": metade, "clã": cla, "registros": str(len(items))}))
        overview_rows.append(f"- [[{cid}]] — metade {metade}, {len(items)} pinturas")

    body = ("Repositório das pinturas faciais Boe (Bororo), organizadas por "
            "metade → clã → subclã → pintura. Dados do projeto *Boe Ejerare*, "
            "em desenvolvimento e sujeitos a validação pela comunidade.\n\n"
            + "\n".join(overview_rows))
    (OUT_MD / "pinturas-faciais.md").write_text(entry(
        "pinturas-faciais", "Pinturas faciais",
        "Pinturas faciais Boe (boe ejiwu), organizadas por metade, clã e subclã.",
        [], body, ["boe-ewa", "ecerae", "tugarege"] + clan_ids,
        {"registros": str(len(data))}))
    print(f"{len(data)} paintings, {len(clans)} clans, skipped: {skipped}")


if __name__ == "__main__":
    main(sys.argv[1])
