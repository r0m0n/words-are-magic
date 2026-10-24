#!/usr/bin/env python3
"""Prüft eine vocab.json gegen den Vertrag in vocab-schema.md.

Aufruf:
    python validate_vocab.py vocab.json
    python validate_vocab.py vocab.json --strict   (Warnungen zählen als Fehler)

Exit-Code 0 = sauber, 1 = Fehler gefunden, 2 = Datei nicht lesbar.
Nur Standardbibliothek, läuft überall (auch in Google Colab).
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ID_RE = re.compile(r"^(?:U(\d+)-(\d{3})|A3-U(\d+)-(?:A|VT|V\d)-(\d{3}))$")  # Schema-Muster oder Masterlisten-ID
POS = {"noun", "verb", "adj", "adv", "expr", "prep", "conj", "pron", "num", "name", "other"}
GENDER = {"m", "f"}
CEFR = {"A1", "A2", "B1", "B2", "C1", "C2"}
REQUIRED = {
    "id": str, "unit": int, "section": str, "order": int, "fr": str,
    "fr_accept": list, "de": str, "pos": str, "tags": list, "proper_name": bool,
}
OPTIONAL = {
    "gender": str, "ipa": str, "example_fr": str, "example_de": str,
    "cefr": str, "cefr_source": str, "freq": (int, float), "freq_source": str, "editorial": str,
    # Erweiterungen seit 2026-10-24 (optional, dürfen fehlen)
    "day": int, "example2_fr": str, "example2_de": str, "ipa_sources": list,
}
EXTENSIONS = {"day", "example2_fr", "example2_de", "ipa_sources"}
KNOWN = set(REQUIRED) | set(OPTIONAL)
IPA_SUSPECT = re.compile(r"[/\[\]]")  # Schrägstriche/Klammern gehören nicht ins Feld


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    strict = "--strict" in argv
    path = Path(argv[1])
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001
        print(f"FEHLER: {path} nicht lesbar: {exc}")
        return 2

    errors: list[str] = []
    warnings: list[str] = []

    # ---- Kopf ----
    if not isinstance(data, dict):
        errors.append("Wurzel ist kein Objekt")
        return report(errors, warnings, strict)
    if data.get("schema") != 1:
        errors.append(f"schema muss 1 sein, ist {data.get('schema')!r}")
    for key in ("source", "version"):
        if not isinstance(data.get(key), str) or not data.get(key).strip():
            errors.append(f"Kopf: {key} fehlt oder leer")
    if not isinstance(data.get("changelog"), list):
        errors.append("Kopf: changelog fehlt (Liste)")
    else:
        for i, c in enumerate(data["changelog"]):
            if not isinstance(c, dict) or not c.get("version") or not c.get("note"):
                errors.append(f"changelog[{i}]: braucht version und note")
        versions = [c.get("version") for c in data["changelog"] if isinstance(c, dict)]
        if data.get("version") and data["version"] not in versions:
            warnings.append(f"Kopf: version {data['version']!r} hat keinen changelog-Eintrag")
    entries = data.get("entries")
    if not isinstance(entries, list):
        errors.append("entries fehlt oder ist keine Liste")
        return report(errors, warnings, strict)

    # ---- Einträge ----
    ids = Counter()
    orders: dict[int, Counter] = defaultdict(Counter)
    fr_seen: dict[str, str] = {}
    for i, e in enumerate(entries):
        where = f"entries[{i}]"
        if not isinstance(e, dict):
            errors.append(f"{where}: kein Objekt")
            continue
        eid = e.get("id")
        where = f"{eid or where}"

        # Pflichtfelder + Typen
        for f, t in REQUIRED.items():
            if f not in e:
                errors.append(f"{where}: Pflichtfeld {f} fehlt")
            elif not isinstance(e[f], t) or (t is int and isinstance(e[f], bool)):
                errors.append(f"{where}: {f} hat Typ {type(e[f]).__name__}, erwartet {t.__name__}")
        for f, t in OPTIONAL.items():
            if f in e and e[f] is not None and not isinstance(e[f], t):
                errors.append(f"{where}: {f} hat Typ {type(e[f]).__name__}, erwartet {t if isinstance(t, tuple) else t.__name__} oder null")
        for f in e:
            if f not in KNOWN:
                warnings.append(f"{where}: unbekanntes Feld {f}")
        for f in OPTIONAL:
            if f not in e and f not in EXTENSIONS:
                warnings.append(f"{where}: optionales Feld {f} fehlt (bitte explizit null setzen)")
        if (e.get("example2_fr") is None) != (e.get("example2_de") is None):
            warnings.append(f"{where}: example2_fr/example2_de nur einseitig gesetzt")

        # Leere Strings sind verboten (auch in Listen)
        for f, v in e.items():
            if isinstance(v, str) and not v.strip():
                errors.append(f"{where}: {f} ist leerer String (null verwenden)")
            if isinstance(v, list):
                for j, x in enumerate(v):
                    if not isinstance(x, str) or not x.strip():
                        errors.append(f"{where}: {f}[{j}] ist kein nicht-leerer String")

        # ID-Muster und Konsistenz zur Unité
        if isinstance(eid, str):
            ids[eid] += 1
            m = ID_RE.match(eid)
            if not m:
                errors.append(f"{where}: id passt nicht auf U<n>-<nnn>")
            else:
                id_unit = int(m.group(1) or m.group(3))
                if isinstance(e.get("unit"), int) and id_unit != e["unit"]:
                    errors.append(f"{where}: id-Unité {id_unit} ≠ unit {e['unit']}")

        if isinstance(e.get("unit"), int) and isinstance(e.get("order"), int):
            orders[e["unit"]][e["order"]] += 1

        # fr in fr_accept
        if isinstance(e.get("fr"), str) and isinstance(e.get("fr_accept"), list):
            if e["fr"] not in e["fr_accept"]:
                errors.append(f"{where}: fr {e['fr']!r} nicht in fr_accept")
            if len(set(e["fr_accept"])) != len(e["fr_accept"]):
                warnings.append(f"{where}: fr_accept enthält Dubletten")
            if e["fr"] in fr_seen:
                warnings.append(f"{where}: fr {e['fr']!r} auch in {fr_seen[e['fr']]}")
            fr_seen.setdefault(e["fr"], eid)

        # pos / gender
        pos = e.get("pos")
        if isinstance(pos, str) and pos not in POS:
            errors.append(f"{where}: pos {pos!r} unbekannt")
        g = e.get("gender")
        if pos == "noun":
            if g not in GENDER:
                errors.append(f"{where}: noun braucht gender m/f, ist {g!r}")
            if isinstance(e.get("fr"), str) and not re.match(r"^((le|la|les|un|une|des)\s|l['\u2019])", e["fr"], re.I):
                warnings.append(f"{where}: noun ohne Artikel in fr: {e['fr']!r}")
        elif g is not None:
            errors.append(f"{where}: gender nur bei noun, hier pos={pos!r}")

        # cefr / cefr_source
        cefr, src = e.get("cefr"), e.get("cefr_source")
        if cefr is not None and cefr not in CEFR:
            errors.append(f"{where}: cefr {cefr!r} ungültig")
        if (cefr is None) != (src is None):
            errors.append(f"{where}: cefr und cefr_source müssen beide gesetzt oder beide null sein")
        if e.get("proper_name") is True:
            if cefr is not None:
                errors.append(f"{where}: Eigenname darf kein cefr tragen")
            if pos not in ("name", None):
                warnings.append(f"{where}: proper_name=true, aber pos={pos!r} (erwartet 'name')")
        elif pos == "name":
            warnings.append(f"{where}: pos='name', aber proper_name=false")

        # freq / freq_source
        if (e.get("freq") is None) != (e.get("freq_source") is None):
            errors.append(f"{where}: freq und freq_source müssen beide gesetzt oder beide null sein")

        # ipa
        ipa = e.get("ipa")
        if isinstance(ipa, str) and IPA_SUSPECT.search(ipa):
            errors.append(f"{where}: ipa enthält Schrägstriche/Klammern: {ipa!r}")

        # Beispiele
        ex_fr, ex_de = e.get("example_fr"), e.get("example_de")
        if (ex_fr is None) != (ex_de is None):
            warnings.append(f"{where}: example_fr/example_de nur einseitig gesetzt")

    for eid, n in ids.items():
        if n > 1:
            errors.append(f"id {eid} kommt {n}× vor")
    for unit, cnt in orders.items():
        for o, n in cnt.items():
            if n > 1:
                errors.append(f"Unité {unit}: order {o} kommt {n}× vor")

    print(f"{path}: {len(entries)} Einträge, Version {data.get('version')!r}")
    return report(errors, warnings, strict)


def report(errors: list[str], warnings: list[str], strict: bool) -> int:
    for w in warnings:
        print(f"  WARNUNG  {w}")
    for e in errors:
        print(f"  FEHLER   {e}")
    print(f"{len(errors)} Fehler, {len(warnings)} Warnungen")
    if errors or (strict and warnings):
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
