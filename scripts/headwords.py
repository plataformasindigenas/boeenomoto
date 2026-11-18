#!/usr/bin/env python3
"""Take homonym numbers and IPA out of the headwords in data/dictionary.tsv.

The source dictionary types homonym numbers into the headword ("aka1", "ba 1",
"meki (megi)1") and sometimes IPA ("kudo1 [kuˈdɔ]", "peˈreto"). The site shows
the number as a superscript from its own column, and IPA from `ipa`, so:

- a trailing number goes to the new `homonym` column ("aka1" → "aka", 1); the same
  number at the end of `ipa` goes too;
- "[...]" after the word goes to `ipa` when `ipa` only repeated the headword;
- the stress mark ˈ leaves the headword when `ipa` is filled (it already has it);
- notes in parentheses ("amo (pl. amoe)") stay as they are, for now.

Mechanical only: nothing else in the row changes, and rows the rules do not cover are
left alone. import_new_dictionary.py applies the same rules to a new import.

Usage: python scripts/headwords.py            (rewrites data/dictionary.tsv)
       python scripts/headwords.py --dry-run  (lists the changes)
"""
import csv
import io
import re
import sys
import unicodedata
from pathlib import Path

TSV = Path(__file__).resolve().parent.parent / "data" / "dictionary.tsv"
NUMBER = re.compile(r"^(?P<word>.*?\S)\s*(?P<n>[0-9]+)$")
BRACKET_IPA = re.compile(r"^(?P<word>.*?)\s*\[(?P<ipa>[^\[\]]+)\]$")


def split_headword(entry: str, ipa: str) -> tuple[str, str, str]:
    """(entry, homonym, ipa) for one row; homonym is '' when there is none."""
    entry = unicodedata.normalize("NFC", entry).strip()
    ipa = unicodedata.normalize("NFC", ipa).strip()
    original = entry
    m = BRACKET_IPA.match(entry)
    if m:
        entry = m["word"]
        if not ipa or ipa == original:
            ipa = m["ipa"].strip()
    homonym = ""
    m = NUMBER.match(entry)
    if m and not re.search(r"[0-9]", m["word"]):
        entry, homonym = m["word"], str(int(m["n"]))
        m_ipa = NUMBER.match(ipa)
        if m_ipa and str(int(m_ipa["n"])) == homonym:
            ipa = m_ipa["word"]
    if "ˈ" in entry and ipa:
        head, sep, note = entry.partition("(")
        entry = head.replace("ˈ", "") + sep + note  # stress inside a note stays
    return entry, homonym, ipa


def main() -> None:
    dry = "--dry-run" in sys.argv
    raw = TSV.read_text(encoding="utf-8")
    rows = list(csv.reader(io.StringIO(raw, newline=""), delimiter="\t"))
    header = rows[0]
    if "homonym" in header:
        sys.exit("data/dictionary.tsv already has a homonym column")
    i_entry, i_ipa = header.index("entry"), header.index("ipa")
    out = [header[: i_entry + 1] + ["homonym"] + header[i_entry + 1:]]
    changed = 0
    for row in rows[1:]:
        entry, homonym, ipa = split_headword(row[i_entry], row[i_ipa])
        if (entry, ipa) != (row[i_entry], row[i_ipa]) or homonym:
            changed += 1
            if dry:
                print(f"{row[0]}\t{row[i_entry]!r} → {entry!r} {homonym}\tipa {row[i_ipa]!r} → {ipa!r}")
        new = list(row)
        new[i_entry], new[i_ipa] = entry, ipa
        out.append(new[: i_entry + 1] + [homonym] + new[i_entry + 1:])
    if not dry:
        buf = io.StringIO(newline="")
        csv.writer(buf, delimiter="\t", lineterminator="\r\n").writerows(out)
        TSV.write_text(buf.getvalue(), encoding="utf-8", newline="")
    print(f"{changed} of {len(rows) - 1} rows {'would change' if dry else 'changed'}")


if __name__ == "__main__":
    main()
