# Datenschnittstelle `vocab.json` – À plus! 3, Lernapp

Stand: 2026-10-24. Dieses Format ist der Vertrag zwischen Masterliste (GPT-Sitzung) und Lernapp (Claude-Sitzung). Die App liest ausschließlich diese Datei. Alles, was hier nicht steht, sieht die App nicht.

## Grundregeln

1. `id` ist stabil und wird nie geändert, auch nicht bei Korrekturen am Inhalt. Der Lernstand hängt an der ID.
2. Fehlende oder nicht validierbare Angaben sind `null`, nie `""` und nie geschätzt. Redaktionelle Einschätzungen stehen in `editorial`, nicht in den Datenfeldern.
3. IPA ist Standard-IPA. Das Feld heißt `ipa`, nicht „Lautschrift Cornelsen“.
4. Substantive tragen den Artikel in `fr`; Verben die relevante Konstruktion; Mehrwortausdrücke stehen als Ganzes.
5. Beispielsätze sind eigene Formulierungen, kurz, ungefähr A2.
6. Die Datei ist UTF-8, JSON, ein Objekt mit Kopf und Einträgen.

## Kopf

```json
{
  "schema": 1,
  "source": "Cornelsen À plus! 3, Neubearbeitung 2020, NRW",
  "version": "2026-10-24",
  "changelog": [
    { "version": "2026-10-24", "note": "Unité 1, 88 Notes, Pilot" }
  ],
  "entries": [ ... ]
}
```

`version` wird bei jeder inhaltlichen Änderung hochgezählt (Datum reicht). `changelog` hält fest, was sich geändert hat – das ist die Nachvollziehbarkeit aus den Projektregeln.

## Eintrag

```json
{
  "id": "U1-017",
  "unit": 1,
  "section": "Auftakt",
  "order": 17,
  "fr": "la boulangerie",
  "fr_accept": ["la boulangerie"],
  "de": "die Bäckerei",
  "pos": "noun",
  "gender": "f",
  "ipa": "la bulɑ̃ʒʁi",
  "example_fr": "Le matin, je vais à la boulangerie.",
  "example_de": "Morgens gehe ich zur Bäckerei.",
  "cefr": "A1",
  "cefr_source": "FLELex",
  "freq": null,
  "freq_source": null,
  "tags": ["Essen", "Stadt"],
  "editorial": null,
  "proper_name": false
}
```

### Feldbeschreibung

| Feld | Typ | Pflicht | Bedeutung |
|---|---|---|---|
| `id` | string | ja | Stabil. Muster `U<unité>-<laufende Nr.>`, dreistellig: `U1-017`. Nie recyceln, nie umnummerieren. |
| `unit` | int | ja | Unité laut Cornelsen. |
| `section` | string | ja | Abschnitt laut Buch (`Auftakt`, `Vocabulaire thématique`, `Leçon 1` …). |
| `order` | int | ja | Schulische Reihenfolge innerhalb der Unité. Bestimmt, in welcher Folge neue Wörter freigeschaltet werden. |
| `fr` | string | ja | Anzeigeform Französisch: Substantiv mit Artikel, Verb mit Konstruktion (`avoir besoin de qc`), Ausdruck als Ganzes. |
| `fr_accept` | string[] | ja | Alle Schreibweisen, die beim Tippen als voll richtig gelten. Mindestens `[fr]`. Hier gehören Varianten hinein, die das Buch ebenfalls führt (`le vélo` / `la bicyclette` nur, wenn beide gelernt werden sollen). Keine Tippfehler-Toleranz eintragen; die macht die App. |
| `de` | string | ja | Deutsche Bedeutung in Lernform (Substantiv mit Artikel). |
| `pos` | string | ja | `noun`, `verb`, `adj`, `adv`, `expr`, `prep`, `conj`, `pron`, `num`, `name`, `other`. |
| `gender` | string/null | bei `noun` | `m`, `f`; `null` sonst. |
| `ipa` | string/null | nein | Standard-IPA ohne Schrägstriche. `null`, wenn nicht validierbar. |
| `example_fr` | string/null | nein | Eigener Beispielsatz, A2, enthält das Wort in `fr`-Form oder flektiert. |
| `example_de` | string/null | nein | Übersetzung des Beispielsatzes. |
| `cefr` | string/null | nein | Nur mit belegbarer Quelle; sonst `null`. Eigennamen immer `null`. |
| `cefr_source` | string/null | nein | `FLELex`, `Lexique4` o. ä.; `null`, wenn `cefr` null ist. |
| `freq` | number/null | nein | Frequenzwert aus offener Quelle; sonst `null`. |
| `freq_source` | string/null | nein | Quelle inkl. Version, z. B. `Lexique 4 freqlivres`. |
| `tags` | string[] | ja | Themenschlagworte, darf leer sein `[]`. |
| `editorial` | string/null | nein | Freitext für redaktionelle Einschätzungen und Hinweise (`CEFR geschätzt A2, nicht belegt`). Wird in der App nicht angezeigt. |
| `proper_name` | bool | ja | `true` bei Eigennamen; die App überspringt dann die IPA-Richtung und zeigt kein CEFR. |

## Was die App mit den Feldern macht

Deutsch → Französisch: zeigt `de`, erwartet getippte Eingabe, vergleicht gegen `fr_accept`.
Französisch → Deutsch: zeigt `fr`, Antwort wird aufgedeckt und per Treffer/Fehler bestätigt; hier ist Tippen nicht sinnvoll, weil deutsche Synonyme zu viele sind.
IPA → Schreibweise: zeigt `ipa`, erwartet getippte Eingabe, vergleicht gegen `fr_accept`; Einträge mit `ipa: null` oder `proper_name: true` fallen aus diesem Modus heraus.
Nach dem Aufdecken erscheinen immer `fr`, `de`, `ipa`, `example_fr`, `example_de`.

Toleranz beim Tippen (macht die App, nicht die Liste): fehlende oder falsche Akzente, Groß-/Kleinschreibung und Leerzeichen um Apostrophe werden als „fast richtig“ gewertet und angezeigt, zählen aber nicht als voller Treffer. Fehlender oder falscher Artikel bei `noun` ist ein Fehler.

## Validierung

Vor jeder Übergabe sollte die Datei diese Prüfungen bestehen; ich liefere dazu ein Skript `validate_vocab.py`:

- alle `id` eindeutig und nach Muster
- `fr` in `fr_accept` enthalten
- `gender` gesetzt genau dann, wenn `pos == "noun"`
- `cefr_source` genau dann gesetzt, wenn `cefr` gesetzt
- `proper_name == true` ⇒ `cefr == null`
- `order` innerhalb einer Unité eindeutig
- kein Feld mit leerem String

## Was sich ändern darf, ohne dass Lernstand verloren geht

Alles außer `id`. Ein Eintrag kann gelöscht werden; sein Lernstand bleibt dann unbenutzt liegen. Ein Eintrag kann umsortiert werden (`order`); das ändert nur die Freischaltfolge künftiger neuer Wörter.