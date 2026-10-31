# Datenschnittstelle `en/vocab.json` – Access 1, Lernapp Englisch

Stand: 2026-10-31. Abweichungen und Ergänzungen gegenüber `docs/vocab-schema.md` (Französisch). Die App liest diese Datei unter `?lang=en` bzw. `/en/` und bildet `en`/`en_accept`/`example_en` intern auf die französischen Feldnamen ab.

## Kopf

`schema: 1`, `lang: "en-GB"` (daran erkennt `validate_vocab.py` die Englisch-Regeln), `source`, `version`, `changelog` wie beim Französischen.

## Eintrag

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `id` | string | ja | `AC1-U<unit>-<nnn>`, stabil. Welcome = Unit 0 (`AC1-U0-…`). |
| `unit` | int | ja | 0 = Welcome, 1–4 = Unit. |
| `section` | string | ja | `Welcome`, `Einstieg`, `Part A`, `Part B`, `Part C`, `Story`; Unit 4 vorerst nur `Unit 4`. |
| `order` | int | ja | Reihenfolge im Buch, eindeutig je Unit. |
| `page` | int/null | nein | Lehrbuchseite. |
| `en` | string | ja | Anzeigeform wie im Buch: `(to) see`, `look sth. up`, `holidays (pl)`. Plural- und Kurzformhinweise stehen in `note`, nicht in `en`. |
| `en_accept` | string[] | ja | Getippte Formen, die als richtig gelten: mit/ohne „to“, Klammern aufgelöst, Alternativen getrennt, Platzhalter am Ende bzw. vor Partikel weggelassen. Die App ergänzt `something`/`somebody`/`someone` für `sth.`/`sb.`. `en` muss nicht enthalten sein. |
| `de` | string | ja | Deutsche Bedeutung wie im Buch. |
| `pos` | string | ja | wie Französisch, zusätzlich `det`. Teilweise automatisch bestimmt; wird von der App nicht ausgewertet. |
| `gender_de` | string/null | nein | `m`/`f`/`n` des deutschen Artikels, nur bei `noun`. |
| `ipa` | string/null | nein | Lautschrift aus dem Buch, ohne Klammern; Varianten mit ` · ` getrennt. |
| `ipa_full` | bool | ja | `false`, wenn das Buch die Lautschrift nur für einen Teil angibt; dann nicht im Modus Lautschrift → Englisch. |
| `ipa_source` | string/null | nein | `Access 1, Vokabelverzeichnis` bzw. `Access 1, Vokabeltaschenbuch`; genau dann gesetzt, wenn `ipa` gesetzt ist. |
| `note` | string/null | nein | Lernhinweis aus dem Buch in eigenen Worten; wird nach dem Aufdecken angezeigt. |
| `example_en`/`example_de` | string/null | nein | Eigener Beispielsatz, A1, höchstens ca. 10 Wörter, nur Grammatik bis zur jeweiligen Unit. Keine Sätze aus dem Buch. |
| `example2_en`/`example2_de` | string/null | nein | Zweiter eigener Satz, andere typische Verwendung. |
| `tags` | string[] | ja | z. B. `Infokasten`. |
| `editorial` | string/null | nein | Redaktionelle Hinweise, nicht angezeigt. |
| `proper_name` | bool | ja | Eigennamen. |
| `day` | int | ja | Lerntag, 8 Einträge je Tag, je Unit fortlaufend. |
| `book_en` | string/null | nein | Originalzeile aus der Excel-Liste (Welcome, Unit 1); dient dem Konverter, damit IDs bei erneutem Lauf stabil bleiben. |

## Prüfungen (`python validate_vocab.py en/vocab.json`)

IDs eindeutig, nach Muster und passend zur Unit; `order` je Unit eindeutig; keine leeren Strings; `en_accept` nicht leer; `gender_de` nur bei `noun`; `ipa` ohne Schrägstriche/Klammern; `ipa` und `ipa_source` nur gemeinsam; `ipa_full` nur mit `ipa`; Beispielsätze nur paarweise. Warnungen: Zielwort im Beispielsatz nicht gefunden, Satz länger als 12 Wörter, Dubletten in `en_accept`.
