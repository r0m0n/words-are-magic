"""Browser-Smoke-Test der Lernapp mit Playwright (python -m playwright install chromium). Spielt eine komplette Session mit den Beispieldaten durch."""
import json, shutil, subprocess, sys, tempfile, time, os
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent
tmp = Path(tempfile.mkdtemp())
shutil.copy(REPO / "index.html", tmp / "index.html")
shutil.copy(REPO / "vocab.sample.json", tmp / "vocab.json")
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1"], cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
errors = []
try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 390, "height": 800})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.goto("http://127.0.0.1:8765/index.html")
        pg.wait_for_function("document.getElementById('stTotal').textContent==='6'")
        assert "Beispieldaten" in pg.inner_text("#loadBanner")
        print("dash:", pg.inner_text("#dashHint"))
        pg.click("#btnStart")
        # Session: 6 Wörter * (de_fr + fr_de [+ ipa_fr für U1-001]) = 13 Karten, alle neu
        seen = 0
        answers = {  # de -> input; erste richtig, zweite ohne Akzent, dritte ohne Artikel
            "die Bäckerei": "la boulangerie",
            "das Fahrrad": "le velo",
            "etwas brauchen": "avoir besoin de qc",
            "Belgien": "Belgique",
            "plötzlich": "tout à coup",
            "die Schule": "l'école",
        }
        verdicts = []
        tried = set()
        guard = 0
        while pg.is_visible("#quiz") and guard < 40:
            guard += 1
            label = pg.inner_text("#qLabel")
            prompt = pg.inner_text("#qPrompt")
            if label.upper().startswith("DEUTSCH"):
                a = answers.get(prompt, "xyz")
                if prompt in tried: a = {"das Fahrrad":"le vélo","Belgien":"la Belgique"}.get(prompt, a)
                tried.add(prompt)
                pg.fill("#answer", a)
                pg.press("#answer", "Enter")
                verdicts.append((prompt, pg.inner_text("#verdict").split("\n")[0]))
                assert pg.is_visible("#reveal")
                pg.press("body", "Enter")
            elif "LAUTSCHRIFT" in label.upper():
                pg.fill("#answer", "la boulangerie")
                pg.press("#answer", "Enter")
                verdicts.append((prompt, pg.inner_text("#verdict").split("\n")[0]))
                pg.press("body", "Enter")
            else:
                pg.press("body", " ")
                assert pg.is_visible("#judgeRow")
                pg.press("body", "2")
            seen += 1
        print("cards:", seen)
        for v in verdicts: print("  ", v)
        assert pg.is_visible("#done"), "done screen missing"
        print("done:", pg.inner_text("#doneText"))
        # Lernstand persistiert?
        st = json.loads(pg.evaluate("localStorage.getItem('wam:state:v1')"))
        print("introduced:", len(st["introduced"]), "cards:", len(st["cards"]))
        assert len(st["introduced"]) == 6 and len(st["cards"]) == 13, (len(st["introduced"]), len(st["cards"]))
        # Reload -> dash zeigt 'alles erledigt' bzw. nur fällige
        pg.reload(); pg.wait_for_function("document.getElementById('stTotal').textContent==='6'")
        print("after reload:", pg.inner_text("#stDue"), "fällig |", pg.inner_text("#dashHint"))
        # Cahier
        pg.click("[data-tab=cahier]")
        rows = pg.locator("#cahierBody tr").count(); print("cahier rows:", rows); assert rows == 6
        pg.fill("#filter", "ecole"); assert pg.locator("#cahierBody tr").count() == 1
        pg.screenshot(path=str(tmp / "cahier.png"))
        b.close()
finally:
    srv.terminate()
print("page errors:", errors)
assert not errors
print("ALL OK", tmp)
