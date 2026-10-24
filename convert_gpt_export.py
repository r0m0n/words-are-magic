#!/usr/bin/env python3
"""Übersetzt den Export der GPT-/Codex-Sitzung (A_plus_3_Lernapp_Daten.json)
in die vocab.json nach docs/vocab-schema.md.

Aufruf:
    python convert_gpt_export.py A_plus_3_Lernapp_Daten.json vocab.json [--version 2026-10-24] [--note "..."]

Regeln:
- IDs werden unverändert übernommen (Stabilität geht vor Muster).
- Nichts wird erfunden: CEFR und Frequenz bleiben null; IPA nur, wenn der
  Export sie als ipaEligible markiert. Schrägstriche werden entfernt.
- Wortart und Genus werden aus dem Hinweistext und dem Artikel abgeleitet;
  wo das nicht eindeutig ist, steht pos="other" und ein Vermerk in editorial.
- Der zweite Beispielsatz landet in example2_fr/example2_de (optionale Felder).
- Bestehender changelog einer vorhandenen Zieldatei wird fortgeschrieben.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

ARTICLE = re.compile(r"^(le|la|les|un|une|des)\s+|^l'", re.I)
PLURAL = re.compile(r"^(les|des)\s+", re.I)
VERB_END = re.compile(r"^(se\s|s')?[a-zéèêëàâîïôûùç]+(er|ir|re|oir)\b", re.I)


def derive_pos_gender(w: dict) -> tuple[str, str | None, bool, str | None]:
    """liefert (pos, gender, proper_name, hinweis_für_editorial)"""
    hint = (w.get("hint") or "")
    h = hint.lower()
    fr = w["fr"].strip()
    note = None

    if any(k in h for k in ("stadtname", "ländername", "eigenname", "name der", "ortsname", "regionsname", "flussname", "personenname")):
        return "name", None, True, None
    if "sprachname" in h:
        # le français: grammatisch Substantiv, kein Eigenname im Sinn des Vertrags
        g = "m" if fr.lower().startswith("le ") else ("f" if fr.lower().startswith("la ") else None)
        return ("noun" if g else "other"), g, False, None if g else "Genus nicht ableitbar"
    if "substantiv" in h or ARTICLE.match(fr):
        if "feminin" in h:
            g = "f"
        elif "maskulin" in h:
            g = "m"
        elif fr.lower().startswith("le "):
            g = "m"
        elif fr.lower().startswith("la "):
            g = "f"
        elif " / " in fr and fr.lower().startswith(("le ", "l'")):
            g = "m"  # le lecteur / la lectrice → Grundform maskulin
            note = "Paarform m/f; Genus der Grundform"
        else:
            g = None
        if PLURAL.match(fr) and g is None:
            # Plural-only: Genus nicht aus Artikel ableitbar
            note = "Pluralform; Genus nicht aus Artikel ableitbar"
        if g is None:
            return "other", None, False, note or "Genus nicht ableitbar (l'-Elision ohne Hinweis)"
        return "noun", g, False, note
    if any(k in h for k in ("fester ausdruck", "feste wortgruppe", "feste wendung", "feste konstruktion", "redewendung")):
        return "expr", None, False, None
    if "adjektiv" in h:
        return "adj", None, False, None
    if "adverb" in h:
        return "adv", None, False, None
    if "konjunktion" in h:
        return "conj", None, False, None
    if "pronomen" in h:
        return "pron", None, False, None
    if "zahl" in h:
        return "num", None, False, None
    if "verb" in h or "transitiv" in h or "muster:" in h or "immer mit" in h or VERB_END.match(fr):
        return "verb", None, False, None
    if "präposition" in h:
        return "prep", None, False, None
    if any(k in h for k in ("fester ausdruck", "feste wortgruppe", "feste wendung", "wendung", "redewendung", "ausdruck")):
        return "expr", None, False, None
    return "other", None, False, "Wortart nicht ableitbar"


def clean_ipa(s: str | None) -> str | None:
    """'/a/ · /b/' → 'a · b'; Schrägstriche und Klammern raus, Varianten bleiben."""
    if not s:
        return None
    parts = [p.strip().strip("/[]\\").strip() for p in re.split(r"\s*[·;]\s*", s)]
    s = " · ".join(p for p in parts if p)
    return s or None


def tidy_fr(s: str) -> str:
    """typografischer Apostroph → gerader Apostroph; Mehrfach-Leerzeichen weg."""
    return re.sub(r"\s+", " ", s.replace("\u2019", "'").replace("\u02bc", "'")).strip()


def convert(src: list[dict], overrides: dict | None = None, sections: dict | None = None) -> list[dict]:
    overrides = overrides or {}
    sections = sections or {}
    out = []
    for w in src:
        pos, gender, proper, note = derive_pos_gender(w)
        ov = overrides.get(w["id"])
        if ov:
            pos = ov.get("pos", pos)
            gender = ov.get("gender") if pos == "noun" else None
            proper = bool(ov.get("proper_name", proper if pos != "name" else True))
            note = "pos/Genus redaktionell (pos_overrides.json), bitte prüfen"
        if pos == "name":
            proper = True
        if pos != "noun":
            gender = None
        fr = tidy_fr(w["fr"])
        accept = []
        for a in [fr] + [tidy_fr(a) for a in (w.get("frAnswers") or []) if a and a.strip()]:
            if a not in accept:
                accept.append(a)
        ex = w.get("examples") or []
        ed_parts = []
        if w.get("hint"):
            ed_parts.append(w["hint"].strip())
        if w.get("ipaStatus"):
            ed_parts.append("IPA: " + w["ipaStatus"].strip())
        if note:
            ed_parts.append("Ableitung: " + note)
        if not w.get("section") and not sections.get(w["id"]):
            ed_parts.append("Abschnitt weder im Export noch in der Masterliste")
        entry = {
            "id": w["id"],
            "unit": int(w["unit"]),
            "section": (w.get("section") or sections.get(w["id"]) or f"Unité {w['unit']}").strip(),
            "order": int(w["order"]),
            "day": int(w["day"]) if w.get("day") is not None else None,
            "fr": fr,
            "fr_accept": accept,
            "de": w["de"].strip(),
            "pos": pos,
            "gender": gender,
            "ipa": clean_ipa(w.get("ipa")) if w.get("ipaEligible") else None,
            "ipa_sources": [s.get("url") for s in (w.get("sources") or []) if s.get("url")] or None,
            "example_fr": (ex[0]["fr"].strip() if len(ex) > 0 and ex[0].get("fr") else None),
            "example_de": (ex[0]["de"].strip() if len(ex) > 0 and ex[0].get("de") else None),
            "example2_fr": (ex[1]["fr"].strip() if len(ex) > 1 and ex[1].get("fr") else None),
            "example2_de": (ex[1]["de"].strip() if len(ex) > 1 and ex[1].get("de") else None),
            "cefr": None,
            "cefr_source": None,
            "freq": None,
            "freq_source": None,
            "tags": [],
            "editorial": " · ".join(ed_parts) or None,
            "proper_name": proper,
        }
        out.append(entry)
    out.sort(key=lambda e: (e["unit"], e["order"]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--version", default=dt.date.today().isoformat())
    ap.add_argument("--note", default="Konvertiert aus dem GPT-/Codex-Export")
    ap.add_argument("--overrides", default=str(Path(__file__).with_name("pos_overrides.json")))
    ap.add_argument("--sections", default=str(Path(__file__).with_name("sections_from_master.json")))
    a = ap.parse_args()

    src = json.loads(Path(a.src).read_text(encoding="utf-8"))
    if isinstance(src, dict):
        src = next(v for v in src.values() if isinstance(v, list))
    overrides = {}
    if a.overrides and Path(a.overrides).exists():
        overrides = {k: v for k, v in json.loads(Path(a.overrides).read_text(encoding="utf-8")).items() if not k.startswith("_")}
    sections = {}
    if a.sections and Path(a.sections).exists():
        sections = {k: v for k, v in json.loads(Path(a.sections).read_text(encoding="utf-8")).items() if not k.startswith("_")}
    entries = convert(src, overrides, sections)

    changelog = []
    dst = Path(a.dst)
    if dst.exists():
        try:
            old = json.loads(dst.read_text(encoding="utf-8"))
            changelog = list(old.get("changelog") or [])
            old_ids = {e["id"] for e in old.get("entries", [])}
            new_ids = {e["id"] for e in entries}
            gone = sorted(old_ids - new_ids)
            if gone:
                print(f"HINWEIS: {len(gone)} IDs verschwinden gegenüber der alten Datei: {gone[:10]}", file=sys.stderr)
            added = sorted(new_ids - old_ids)
            if added:
                print(f"HINWEIS: {len(added)} neue IDs: {added[:10]}", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            print(f"HINWEIS: alte Zieldatei nicht lesbar ({exc}); changelog beginnt neu", file=sys.stderr)
    if not any(c.get("version") == a.version for c in changelog):
        changelog.append({"version": a.version, "note": a.note})

    doc = {
        "schema": 1,
        "source": "Cornelsen À plus! 3, Neubearbeitung 2020, NRW",
        "version": a.version,
        "changelog": changelog,
        "entries": entries,
    }
    dst.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    from collections import Counter
    print(f"{len(entries)} Einträge → {dst}")
    print("pos:", dict(Counter(e["pos"] for e in entries)))
    print("ipa gesetzt:", sum(1 for e in entries if e["ipa"]), "· Eigennamen:", sum(1 for e in entries if e["proper_name"]))
    print("Ableitung unklar:", [e["id"] for e in entries if e["editorial"] and "Ableitung:" in e["editorial"]])
    return 0


if __name__ == "__main__":
    sys.exit(main())
