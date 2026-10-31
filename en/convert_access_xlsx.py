#!/usr/bin/env python3
"""Übernimmt Welcome und Unit 1 aus Access1_Unit1_Vokabeln.xlsx in en/vocab.json.

Aufruf:
    python en/convert_access_xlsx.py Access1_Unit1_Vokabeln.xlsx en/vocab.json

- Welcome wird als unit 0 geführt (Anzeige „Welcome“), IDs AC1-U0-nnn; Unit 1 bekommt AC1-U1-nnn.
- Bestehende Einträge (Units 2–4) bleiben unverändert; Zeilen der Excel-Datei, die schon in Unit 2
  stehen (SB-Seiten 52–54), werden übersprungen.
- IDs sind stabil: Ein zweiter Lauf vergibt für denselben Eintrag (Unit, Abschnitt, Englisch, Deutsch)
  dieselbe ID wie beim ersten Lauf, weil vorhandene AC1-U0/U1-Einträge wiederverwendet werden.
- Lautschrift wie gedruckt; ipa_full = false, wenn das Buch sie nur für einen Teil des Ausdrucks angibt.
- Nur Standardbibliothek + openpyxl.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

import openpyxl

UNIT_OF = {"Welcome": 0, "Unit 1": 1}
DAY_SIZE = 8

# ---- Handkorrekturen: Anzeigeform, Annahmen, Hinweis, Lautschrift ----
# Schlüssel = englischer Text wie in der Excel-Datei.
OVR: dict[str, dict] = {
    "I'm from Brighton. (= I am from Brighton.)": {"en": "I'm from Brighton.", "accept": ["I'm from Brighton", "I am from Brighton"], "note": "I'm = I am", "ipa_full": False},
    "a city, pl cities": {"en": "city", "accept": ["city", "a city"], "ipa": "ˈsɪti", "note": "Plural: cities [ˈsɪtiz]"},
    "I'm fine(, thanks).": {"accept": ["I'm fine", "I'm fine, thanks", "I am fine", "I am fine, thanks"]},
    "Bye. (auch: Goodbye.)": {"en": "Bye. / Goodbye.", "accept": ["Bye", "Goodbye"], "ipa": "baɪ · ˌɡʊdˈbaɪ", "ipa_full": True},
    "Thanks. (auch: Thank you.)": {"en": "Thanks. / Thank you.", "accept": ["Thanks", "Thank you"], "ipa": "ˈθæŋks · ˈθæŋk juː", "ipa_full": True},
    "(It's) your turn.": {"accept": ["your turn", "It's your turn", "It is your turn"]},
    "family, pl families": {"en": "family", "note": "Plural: families"},
    "fish, pl fish": {"en": "fish", "note": "Plural: fish (gleiche Form)"},
    "hobby, pl hobbies": {"en": "hobby", "note": "Plural: hobbies"},
    "country, pl countries": {"en": "country", "note": "Plural: countries"},
    "story, pl stories": {"en": "story", "note": "Plural: stories"},
    "box, pl boxes": {"en": "box", "note": "Plural: boxes"},
    "shelf, pl shelves": {"en": "shelf", "ipa": "ʃelf", "note": "Plural: shelves [ʃelvz]"},
    "It/He/She isn't here (= is not)": {"en": "It/He/She isn't here.", "accept": ["It isn't here", "He isn't here", "She isn't here", "It is not here", "He is not here", "She is not here"], "ipa": "ˈɪznt", "note": "isn't = is not"},
    "she's (she is)": {"accept": ["she's", "she is"], "note": "she's = she is"},
    "Here's … (= Here is …) / Here are …": {"en": "Here's … / Here are …", "accept": ["Here's", "Here is", "Here are"], "note": "Here's = Here is"},
    "grandfather, grandpa": {"accept": ["grandfather", "grandpa"]},
    "grandmother, grandma": {"accept": ["grandmother", "grandma"]},
    "stepmother, stepmum": {"accept": ["stepmother", "stepmum"]},
    "stepfather, stepdad": {"accept": ["stepfather", "stepdad"]},
    "a hundred / one hundred": {"accept": ["a hundred", "one hundred"], "ipa": "əˈhʌndrəd · ˌwʌnˈhʌndrəd", "ipa_full": True},
    "You're right / wrong.": {"accept": ["You're right", "You're wrong", "You are right", "You are wrong"]},
    "in English / in German": {"accept": ["in English", "in German"]},
    "this classroom/city/name": {"accept": ["this classroom", "this city", "this name"]},
    "so cool/hot/…": {"accept": ["so cool", "so hot"]},
    "before a, e, i, o, u": {"accept": ["before a, e, i, o, u", "before a e i o u"]},
    "(to) be good at football/art/…": {"accept": ["be good at", "to be good at", "be good at football", "be good at art"]},
    "(to) describe sth. (to sb.)": {"accept": ["describe", "to describe", "describe sth.", "describe sth. to sb.", "to describe sth.", "to describe sth. to sb."]},
    "(to) ask (sb.) a question": {"accept": ["ask a question", "ask sb. a question", "to ask a question", "to ask sb. a question"]},
    "(to) remember (sth.)": {"accept": ["remember", "to remember", "remember sth.", "to remember sth."]},
    "(to) talk (to)": {"accept": ["talk", "talk to", "to talk", "to talk to"]},
    "grand-": {"accept": ["grand-", "grand"]},
    "Well, …": {"accept": ["Well", "Well,"]},
    "around …": {"accept": ["around"]},
}

# Wortart für Einwortausdrücke ohne Artikel, wo die Regel daneben liegt
POS_OVR = {
    "too": "adv", "here": "adv", "there": "adv", "today": "adv", "now": "adv", "very": "adv", "really": "adv",
    "also": "adv", "only": "adv", "again": "adv", "together": "adv", "often": "adv", "sometimes": "adv",
    "never": "adv", "usually": "adv", "always": "adv", "then": "adv", "please": "adv", "yes": "adv", "no": "adv",
    "the": "det", "a": "det", "an": "det", "my": "det", "your": "det", "his": "det", "her": "det", "its": "det",
    "our": "det", "their": "det", "this": "det", "that": "det", "some": "det", "any": "det",
    "I": "pron", "you": "pron", "he": "pron", "she": "pron", "it": "pron", "we": "pron", "they": "pron",
    "what": "pron", "who": "pron", "everyone": "pron", "something": "pron",
    "and": "conj", "but": "conj", "or": "conj", "if": "conj", "so": "conj",
    "in": "prep", "on": "prep", "at": "prep", "with": "prep", "from": "prep", "for": "prep", "to": "prep",
    "of": "prep", "about": "prep", "under": "prep", "next to": "prep", "behind": "prep", "near": "prep",
    "where": "adv", "how": "adv", "when": "adv", "why": "adv",
}
# Nachkorrektur nach Durchsicht der automatisch bestimmten Wortarten (Anzeigeform → Wortart)
POS_FIX = {
    "you're": "pron", "they're": "pron", "me": "pron", "us": "pron", "she's (she is)": "pron",
    "maybe": "adv", "upstairs": "adv", "downstairs": "adv", "already": "adv", "soon": "adv", "back": "adv",
    "just": "adv", "first": "adv", "late": "adj", "can": "verb", "many": "det", "all": "det", "another": "det",
    "other": "det", "more": "det", "4 pm": "expr", "4 am": "expr", "grand-": "other", "rubber": "noun",
    "where?": "adv", "why?": "adv", "Who?": "pron", "around …": "prep", "no …": "det", "e.g.": "expr",
}
NUMBERS = set("one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen "
              "seventeen eighteen nineteen twenty thirty forty fifty sixty seventy eighty ninety".split())
ART = {"der": "m", "die": "f", "das": "n", "eine": "f"}


def clean_display(en: str) -> str:
    return re.sub(r"\s+", " ", en).strip()


def accept_variants(en: str) -> list[str]:
    """Automatische Annahmen nach denselben Regeln wie Units 2–4."""
    s = en
    s = re.sub(r"\s*\((?:infml|pl|no pl)\)", "", s)
    s = re.sub(r"\s*\(=[^)]*\)", "", s)
    s = s.replace("…", "").replace("...", "")
    s = re.sub(r"\s+([?.!,])", r"\1", s)
    s = re.sub(r"\s+", " ", s).strip()
    out: list[str] = []
    bases = [s]
    # optionale Klammern: mit und ohne Inhalt
    exp: list[str] = []
    for b in bases:
        m = re.search(r"\(([^)]*)\)", b)
        if m and not b.startswith("(to)"):
            exp += [re.sub(r"\s+", " ", b[:m.start()] + m.group(1) + b[m.end():]).strip(),
                    re.sub(r"\s+", " ", b[:m.start()] + b[m.end():]).strip()]
        else:
            exp.append(b)
    for b in exp:
        if b.startswith("(to) "):
            core = b[5:]
            forms = [core, "to " + core]
        else:
            forms = [b]
        for f in forms:
            out.append(f)
            # Platzhalter am Ende oder vor Partikel entfernen
            g = re.sub(r"\s+(?:sth\.|sb\.)(?:/(?:sth\.|sb\.))?$", "", f)
            g = re.sub(r"\s+(?:sth\.|sb\.)\s+(up|down|out|in|on|off|away|back)\b", r" \1", g)
            if g != f:
                out.append(g)
    seen, res = set(), []
    for x in out:
        x = x.strip().rstrip(",").strip()
        if x and x not in seen:
            seen.add(x); res.append(x)
    return res


def content_words(en: str) -> list[str]:
    s = re.sub(r"\((?:to|infml|pl|no pl)\)", "", en)
    s = re.sub(r"\(=[^)]*\)", "", s)
    s = re.sub(r"\b(?:sth|sb)\.", "", s)
    s = s.replace("…", " ").replace("/", " ")
    return [w for w in re.findall(r"[A-Za-z][A-Za-z'\-]*", s)]


def ipa_tokens(ipa: str) -> int:
    first = re.split(r"[,;·]| \(", ipa)[0]
    return len([t for t in re.split(r"[\s‿]+", first.strip()) if t])


def guess_pos(en: str, de: str) -> tuple[str, str | None]:
    core = re.sub(r"\s*\((?:infml|pl|no pl)\)", "", en).strip()
    if core.startswith("(to) "):
        return "verb", None
    low = core.lower()
    if low in NUMBERS or re.fullmatch(r"(twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety)-\w+", low) or "hundred" in low:
        return "num", None
    if core in POS_OVR or low in POS_OVR:
        return POS_OVR.get(core, POS_OVR.get(low)), None
    words = content_words(core)
    m = re.match(r"(der|die|das|eine)\s", de)
    if len(words) == 1 and m:
        g = ART[m.group(1)]
        if g == "f" and (core.endswith("(pl)") or en.endswith("(pl)")):
            g = None  # Plural-Artikel „die“ ist kein Genus
        return "noun", g
    if len(words) > 1 or re.search(r"[.?!…]", core):
        return "expr", None
    if de[:1].isupper():
        return "noun", None
    return "adj", None


def main(xlsx: str, vocab_path: str) -> None:
    vp = Path(vocab_path)
    data = json.loads(vp.read_text(encoding="utf-8"))
    keep = [e for e in data["entries"] if e["unit"] >= 2]
    old_by_key = {(e["unit"], e["section"], e["book_en"] if "book_en" in e else e["en"], e["de"]): e
                  for e in data["entries"] if e["unit"] < 2}
    ws = openpyxl.load_workbook(xlsx)["Vokabeln"]
    rows = [r for r in ws.iter_rows(min_row=2, values_only=True) if r[1] in UNIT_OF]
    new: list[dict] = []
    counters = {0: 0, 1: 0}
    for nr, unit_s, section, page, en_raw, ipa, de, hint in rows:
        unit = UNIT_OF[unit_s]
        counters[unit] += 1
        o = OVR.get(en_raw, {})
        en = o.get("en", clean_display(en_raw))
        en = re.sub(r",\s*pl\s+\w+$", "", en)
        acc = o.get("accept") or accept_variants(en)
        pos, g = guess_pos(o.get("en", re.sub(r",\s*pl\s+\w+$", "", en_raw)), de)
        pos = POS_FIX.get(en, pos)
        notes = []
        if "(infml)" in en_raw:
            notes.append("infml = umgangssprachlich")
        if o.get("note"):
            notes.append(o["note"])
        ipa_v = o.get("ipa", ipa)
        if ipa_v:
            ipa_v = ipa_v.strip().replace(", ", " · ") if "ipa" not in o else ipa_v
        if en in ("4 pm", "4 am"):
            o = {**o, "ipa_full": False}
        if "ipa_full" in o:
            full = o["ipa_full"] if ipa_v else False
        elif not ipa_v:
            full = False
        else:
            n_en = len(content_words(re.sub(r"\(.*?\)", "", en)))
            full = ipa_tokens(ipa_v) >= n_en
        editorial = []
        if hint:
            editorial.append(hint)
        if ipa_v and not full:
            editorial.append("IPA im Buch nur für ein Teilwort; nicht für IPA→Englisch-Abfrage.")
        if not ipa_v:
            editorial.append("Im Buch ohne Lautschrift.")
        key = (unit, "Welcome" if unit == 0 else section, en_raw, de)
        e = {
            "id": None, "unit": unit, "section": "Welcome" if unit == 0 else section,
            "order": counters[unit], "page": page, "en": en, "en_accept": acc, "de": de,
            "pos": pos, "gender_de": (g if pos == "noun" else None) if en != "rubber" else "m",
            "ipa": ipa_v or None, "ipa_full": bool(full),
            "ipa_source": "Access 1, Vokabeltaschenbuch" if ipa_v else None,
            "note": "; ".join(notes) or None, "example_en": None, "example_de": None,
            "tags": ["Infokasten"] if hint else [],
            "editorial": " ".join(editorial) or None, "proper_name": False,
            "day": (counters[unit] - 1) // DAY_SIZE + 1, "book_en": en_raw,
        }
        prev = old_by_key.get(key)
        e["id"] = prev["id"] if prev else f"AC1-U{unit}-{counters[unit]:03d}"
        if prev:  # vorhandene Beispielsätze/Korrekturen nicht überschreiben
            for f in ("example_en", "example_de", "example2_en", "example2_de"):
                if prev.get(f):
                    e[f] = prev[f]
        new.append(e)
    ids = [e["id"] for e in new]
    assert len(ids) == len(set(ids)), "ID doppelt"
    data["entries"] = new + keep
    data["source"] = "Cornelsen English G Access 1 (Klasse 5), Vokabelverzeichnis Welcome, Units 1–4"
    v = date.today().isoformat()
    data["version"] = v
    note = f"Welcome ({counters[0]}) und Unit 1 ({counters[1]}) aus Access1_Unit1_Vokabeln.xlsx ergänzt"
    if not any(c.get("note") == note for c in data["changelog"]):
        data["changelog"].append({"version": v, "note": note})
    vp.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Welcome {counters[0]}, Unit 1 {counters[1]}, gesamt {len(data['entries'])}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
