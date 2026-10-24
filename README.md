# Words are magic

Vokabeltrainer Französisch–Deutsch für *Cornelsen À plus! 3* (Neubearbeitung 2020, NRW, Klasse 9). Eine einzelne HTML-Seite, keine Installation, kein Server, keine Anmeldung. Die Wörter kommen aus einer Datei `vocab.json`; der Lernstand bleibt im Browser des Geräts, auf dem gelernt wird.

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

## Lernstand sichern oder umziehen

*Einstellungen → Lernstand → Exportieren* schreibt eine JSON-Datei; *Importieren* liest sie auf einem anderen Gerät ein. Der Lernstand ist an den Browser gebunden – ein anderes Gerät oder ein privates Fenster startet bei null.

## Entwicklung

```
python validate_vocab.py vocab.sample.json
pip install playwright && python -m playwright install chromium
python tests_smoke.py
```

Keine Build-Schritte, keine Abhängigkeiten im Browser.

## Transparenzhinweis

Bei der Erstellung dieser App wurde Claude Fable 5.1 für Entwurf, Implementierung und automatisierte Tests genutzt. Wortliste, Beispielsätze und didaktische Regeln werden von Roman Bartnik geprüft, überarbeitet und verantwortet.
