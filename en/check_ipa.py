#!/usr/bin/env python3
"""Gleicht die Buch-Lautschrift in en/vocab.json gegen zwei offene britische Aussprachewörterbücher ab.

Quellen (vorher herunterladen):
  ipa-dict en_UK  https://raw.githubusercontent.com/open-dict-data/ipa-dict/master/data/en_UK.txt
  Britfone 3.0.1  https://raw.githubusercontent.com/JoseLlarena/Britfone/master/britfone.main.3.0.1.csv

Aufruf:
    python en/check_ipa.py en/vocab.json en_UK.txt britfone.main.3.0.1.csv ipa_abgleich.csv

Vergleich nach Normalisierung: Betonungszeichen, Leerzeichen, Bindebögen und Silbenpunkte entfernt;
ɛ→e, ɡ→g, ɹ→r, ɐ→ʌ, ʤ→dʒ, ʧ→tʃ. Die Buch-Lautschrift bleibt führend; die Liste zeigt nur,
wo ein Blick ins Buch lohnt (Abschreibfehler, Varianten, schwache Formen).
Zweite Stufe „gleich bis auf Schreibkonvention“: silbische Konsonanten (ˈsevn = ˈsevən), i/ɪ, u/ʊ, ʌ/ə und
Längenzeichen werden ignoriert, weil Buch und Wörterbücher hier verschiedene Konventionen nutzen.
Ergebnis je Eintrag: gleich | gleich bis auf Schreibkonvention | abweichend | nicht im Wörterbuch | übersprungen (Teil-IPA oder keine IPA).
"""
from __future__ import annotations

import csv
import itertools
import json
import re
import sys
from collections import Counter, defaultdict

MAP = str.maketrans({"ɛ": "e", "ɡ": "g", "ɹ": "r", "ɐ": "ʌ"})


def norm(ipa: str) -> str:
    s = ipa.replace("ʤ", "dʒ").replace("ʧ", "tʃ").translate(MAP)
    return re.sub(r"[ˈˌ\s‿.\-/()]", "", s)


def loose(s: str) -> str:
    """Gröbere Form: Silbische Konsonanten, i/ɪ, u/ʊ, ʌ/ə und Längenzeichen gelten als gleich."""
    s = re.sub(r"ə(?=[lnm](?![aeiouɪʊʌəɒæɑɔɜ]))", "", s)
    return s.translate(str.maketrans({"ɪ": "i", "ʊ": "u", "ʌ": "ə", "ː": None}))


def load_ipadict(path: str) -> dict[str, set[str]]:
    d: dict[str, set[str]] = defaultdict(set)
    for line in open(path, encoding="utf-8"):
        w, _, prons = line.rstrip("\n").partition("\t")
        for p in prons.split(","):
            d[w.lower()].add(norm(p.strip()))
    return d


def load_britfone(path: str) -> dict[str, set[str]]:
    d: dict[str, set[str]] = defaultdict(set)
    for row in csv.reader(open(path, encoding="utf-8")):
        if len(row) < 2:
            continue
        w = re.sub(r"\(\d+\)$", "", row[0]).lower()
        d[w].add(norm(row[1]))
    return d


def words_of(e: dict) -> list[str]:
    s = re.sub(r"\([^)]*\)", "", e["en"])
    s = re.sub(r"\b(?:sth|sb)\.", "", s)
    s = re.sub(r"^to\s+", "", s)
    return [w.lower() for w in re.findall(r"[A-Za-z][A-Za-z']*", s)]


def candidates(words: list[str], dicts: list[dict[str, set[str]]]) -> set[str] | None:
    per_word = []
    for w in words:
        prons = set().union(*(d.get(w, set()) for d in dicts))
        if not prons:
            return None
        per_word.append(sorted(prons)[:4])
    if len(per_word) > 5:
        return None
    return {"".join(c) for c in itertools.product(*per_word)}


def main(vocab: str, ipadict: str, britfone: str, out: str) -> None:
    entries = json.load(open(vocab, encoding="utf-8"))["entries"]
    dicts = [load_ipadict(ipadict), load_britfone(britfone)]
    stats: Counter = Counter()
    rows = []
    for e in entries:
        if not e.get("ipa") or not e.get("ipa_full"):
            stats["übersprungen"] += 1
            continue
        book_variants = [norm(v) for v in re.split(r"\s*[·,;]\s*", e["ipa"]) if v.strip()]
        cand = candidates(words_of(e), dicts)
        if cand is None:
            res = "nicht im Wörterbuch"
        elif any(b in cand for b in book_variants):
            res = "gleich"
        elif {loose(b) for b in book_variants} & {loose(c) for c in cand}:
            res = "gleich bis auf Schreibkonvention"
        else:
            res = "abweichend"
        stats[res] += 1
        if res not in ("gleich", "gleich bis auf Schreibkonvention"):
            rows.append([e["id"], e["unit"], e.get("page"), e["en"], e["ipa"], res,
                         " | ".join(sorted(cand)[:4]) if cand else ""])
    with open(out, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["id", "unit", "Seite", "Englisch", "IPA Buch", "Ergebnis", "Wörterbuch (normalisiert, ohne Betonung)"])
        w.writerows(rows)
    print(dict(stats))


if __name__ == "__main__":
    main(*sys.argv[1:5])
