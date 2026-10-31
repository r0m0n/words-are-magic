# Words are magic

Vokabeltrainer Französisch–Deutsch für *Cornelsen À plus! 3* (Neubearbeitung 2020, NRW, Klasse 9) und Englisch–Deutsch für *Access 1* (Klasse 5, unter `/en/`). Eine einzelne HTML-Seite, keine Installation, kein Server, keine Anmeldung. Die Wörter kommen aus einer Datei `vocab.json`; der Lernstand bleibt im Browser des Geräts, auf dem gelernt wird.

## Was die App macht

Die Lernerin wählt eine **Lerneinheit**: Unité → Abschnitt (Auftaktseite, Vocabulaire thématique, Volet 1, Volet 2 oder alle) → Lerntag. Ein Abschnitt wird in Lerntage zu etwa 8–10 Wörtern geteilt; bei „alle Abschnitte“ gilt die Lerntag-Einteilung der Masterliste. Der Ring oben zählt, wie viele Wörter des Lerntags in allen Wortrichtungen „gesammelt“ sind.

Dann wählt sie eine Übung und arbeitet den Lerntag als Runde durch; Fehler kommen in derselben Runde noch bis zu zweimal wieder, danach bietet „Nur die Fehler nochmal“ eine kurze Extrarunde:

| Übung | Was passiert |
|---|---|
| Deutsch → Französisch | deutsche Bedeutung sehen, französisch **tippen** |
| Französisch → Deutsch | französisch sehen, aufdecken, selbst mit ✓/✗ bewerten |
| Lautschrift → Französisch | Standard-IPA sehen, französisch **tippen** (nur Einträge mit IPA, keine Eigennamen) |
| Sätze: Deutsch → Französisch | Beispielsatz übersetzen, **tippen**, Vergleich mit der Musterlösung |
| Sätze: Französisch → Deutsch | Beispielsatz übersetzen, aufdecken, selbst bewerten |
| Fehlerliste | alle Wörter der Unité, deren letzte Antwort falsch war |
| Wiederholung fällig | alle Karten über alle Unités, deren Leitner-Frist abgelaufen ist |

Nach jeder Antwort erscheinen Wort, Bedeutung, Lautschrift und beide Beispielsätze. Am Anfang jeder Runde steht einer der zehn Lerntipps; alle zehn mit Begründung und Literatur stehen unter *Lerntipps*.

Getippte Antworten werden gegen `fr_accept` geprüft. Fehlende oder falsche Akzente, Groß-/Kleinschreibung und Leerzeichen um Apostrophe gelten als **fast richtig**; fehlender oder falscher Artikel bei Substantiven ist ein **Fehler**. Ein Zeichen-Diff zeigt, was abweicht.

Jede richtige Antwort hebt die Karte eine Leitner-Stufe (0 → sofort, 1 → 1 Tag, 2 → 3 Tage, 3 → 7, 4 → 14, 5 → 30 Tage); ein Fehler setzt sie auf 0 und auf die Fehlerliste.

## Dateien

| Datei | Zweck |
|---|---|
| `index.html` | die komplette App |
| `vocab.json` | die Wortliste: Unités 1–5, 397 Einträge, aus der Masterliste |
| `vocab.sample.json` | sechs Beispieleinträge zum Ausprobieren |
| `docs/vocab-schema.md` | der Vertrag für `vocab.json` (Felder, Regeln, Validierung) |
| `convert_gpt_export.py` | übersetzt den Export der GPT-/Codex-Sitzung in `vocab.json` |
| `pos_overrides.json` | Wortart und Genus je ID, redaktionell gesetzt – bitte prüfen |
| `sections_from_master.json` | Abschnitt je ID aus der Masterliste (für Unité 1 nötig) |
| `validate_vocab.py` | prüft eine `vocab.json` gegen den Vertrag |
| `tests_smoke.py` | Browser-Test, spielt Auswahl, Lerntage, alle Übungen und Reload durch |
| `tests_sync.py`, `tests_mock_server.py` | Abgleich-Test mit zwei „Geräten“ gegen einen lokalen Nachbau der Netlify-Funktion |
| `netlify.toml`, `netlify/functions/state.mjs`, `package.json` | Netlify: Veröffentlichung und Abgleich-Funktion |

## Benutzen

**Online (GitHub Pages):** Repository-Einstellungen → Pages → Branch `main`, Ordner `/`. Danach ist die App unter `https://r0m0n.github.io/words-are-magic/` erreichbar und liest `vocab.json` aus dem Repo.

**Lokal ohne Server:** `index.html` doppelklicken. Browser verbieten Dateien aus dem Dateisystem nachzuladen, deshalb unter *Einstellungen → Daten* die `vocab.json` einmal auswählen; die App merkt sich eine Kopie.

**Zum Testen:** `vocab.sample.json` nach `vocab.json` kopieren oder in der App laden.

## Wortliste aktualisieren

Wenn die GPT-/Codex-Sitzung eine neue `A_plus_3_Lernapp_Daten.json` liefert:

```
python convert_gpt_export.py A_plus_3_Lernapp_Daten.json vocab.json --version 2026-11-01 --note "was sich geändert hat"
python validate_vocab.py vocab.json
```

Der Konverter schreibt den `changelog` fort und meldet verschwundene oder neue IDs. Steht am Ende `OK`, Datei pushen; die GitHub Action prüft noch einmal. Neue Einträge ohne Wortart tauchen als `pos: "other"` auf und gehören in `pos_overrides.json`.

IDs bleiben stabil; der Lernstand hängt an `id` + Richtung. Alles andere darf sich ändern, ohne dass Lernstand verloren geht.

## Englisch: Access 1 (Klasse 5)

Dieselbe App läuft für Englisch unter `…/en/` bzw. `…/?lang=en` (z. B. `https://r0m0n.github.io/words-are-magic/en/`). Sie liest `en/vocab.json` (Welcome, Units 1–4, 1 006 Einträge aus dem Vokabelverzeichnis von *English G Access 1*). Unterschiede zum Französischen:

- Auswahl Welcome / Unit 1–4 → Abschnitt (Einstieg, Part A–C, Story) → Lerntag (8 Wörter).
- Kein Artikelzwang. „to“ bei Verben ist freiwillig; `sth.`/`sb.` dürfen weggelassen oder als something/somebody ausgeschrieben werden.
- Großbuchstaben der Lösung (Monday, I, English) müssen stimmen, sonst „fast richtig“; ein großgeschriebener Anfang bei kleingeschriebener Lösung zählt nicht als Fehler.
- Lautschrift → Englisch nur für Einträge, deren Lautschrift im Buch den ganzen Ausdruck abdeckt (`ipa_full`).
- Nach dem Aufdecken erscheinen die Buchhinweise (`note`, z. B. Plural, Gegenteil) und ein Vorlese-Knopf (Sprachausgabe des Browsers, britisches Englisch).
- Eigene Lerntipps in Kindersprache; Regel 6 behandelt englische Schreibung.
- Eigener Lernstand im Browser (Schlüssel `wam-en:`) und eigener Lernschlüssel für den Abgleich – Französisch und Englisch beeinflussen sich nicht.

Werkzeuge im Ordner `en/`:

| Datei | Zweck |
|---|---|
| `en/vocab.json` | Wortliste Englisch (Schema: `docs/vocab-schema-en.md`) |
| `en/convert_access_xlsx.py` | übernimmt Welcome und Unit 1 aus der Excel-Liste; IDs bleiben bei erneutem Lauf stabil |
| `en/check_ipa.py` | gleicht die Buch-Lautschrift gegen ipa-dict en_UK und Britfone ab |
| `en/beispielsaetze_probe_u2_tag1-2.tsv` | Probe der eigenen Beispielsätze (Unit 2, Lerntage 1–2) |
| `tests_smoke_en.py` | Browser-Test der Englisch-Variante inkl. Vergleichsregeln und getrenntem Lernstand |


## Lernstand: wo er liegt und wie er zwischen Geräten wandert

Der Lernstand (Leitner-Stufen je Karte, Fehlerliste, Rundenfortschritt) liegt im Browser des Geräts (localStorage). Zwei Wege, ihn auf ein anderes Gerät zu bringen:

**Abgleich über Netlify (empfohlen).** Läuft die App auf Netlify, erscheint unter *Einstellungen → Abgleich zwischen Geräten* ein **Lernschlüssel**. Einmal „Neu erzeugen“, „Verbinden“, den Schlüssel auf dem zweiten Gerät eintragen – fertig. Die App holt beim Start den Stand, mischt ihn mit dem lokalen (je Karte gewinnt die mit mehr Antworten) und schreibt nach jeder Antwort zurück. Der Schlüssel ist das einzige Geheimnis; es gibt kein Konto und keinen Namen. Technisch: `netlify/functions/state.mjs` legt ein JSON-Dokument je Schlüssel in Netlify Blobs ab (`netlify.toml`, `package.json`).

**Export/Import.** *Einstellungen → Lernstand → Exportieren* schreibt eine JSON-Datei; *Importieren* liest sie auf einem anderen Gerät ein. Funktioniert überall, auch auf GitHub Pages, wo es keinen Abgleich gibt.

### Auf Netlify veröffentlichen

1. Bei Netlify: „Add new project → Import an existing project → GitHub“, Repository `words-are-magic` wählen.
2. Build-Einstellungen: Build command leer lassen, Publish directory `.` (steht in `netlify.toml`). „Deploy“.
3. Danach läuft die App unter `https://<name>.netlify.app/`, die Funktion unter `/api/state`. Jeder Push auf `main` veröffentlicht neu.

GitHub Pages kann parallel weiterlaufen; dort fehlt nur der Abgleich.

## Entwicklung

```
python validate_vocab.py vocab.sample.json
pip install playwright && python -m playwright install chromium
python validate_vocab.py en/vocab.json
python tests_smoke.py
python tests_smoke_en.py
python tests_sync.py
```

Keine Build-Schritte, keine Abhängigkeiten im Browser.

## Transparenzhinweis

Bei der Erstellung dieser App wurden Claude Fable 5.1 und Claude Opus 5.5 für Entwurf, Implementierung und automatisierte Tests genutzt. Wortliste, Beispielsätze und didaktische Regeln werden von Roman Bartnik geprüft, überarbeitet und verantwortet.
