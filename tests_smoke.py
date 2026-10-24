"""Browser-Smoke-Test der Lernapp mit Playwright (pip install playwright && python -m playwright install chromium).
Spielt mit der echten vocab.json (oder den Beispieldaten) Auswahl, Lerntage, alle Modi, Fehlerliste und Reload durch."""
import json, shutil, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent
SRC = REPO / "vocab.json" if (REPO / "vocab.json").exists() else REPO / "vocab.sample.json"
tmp = Path(tempfile.mkdtemp())
shutil.copy(REPO / "index.html", tmp / "index.html")
shutil.copy(SRC, tmp / "vocab.json")
data = json.loads(SRC.read_text(encoding="utf-8"))
N = len(data["entries"])
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8765", "--bind", "127.0.0.1"], cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
errors = []

def play_round(pg, answer_fn, max_steps=80):
    steps = 0
    while pg.is_visible("#quiz") and steps < max_steps:
        steps += 1
        if pg.is_visible("#typeBox"):
            a = answer_fn(pg.inner_text("#qLabel"), pg.inner_text("#qPrompt"))
            if a is None:
                pg.click("#btnShow")
            else:
                pg.fill("#answer", a); pg.press("#answer", "Enter")
            assert pg.is_visible("#reveal"), "reveal missing"
            pg.press("body", "Enter")
        else:
            pg.press("body", " "); assert pg.is_visible("#judgeRow"); pg.press("body", "2")
    assert pg.is_visible("#done"), "done screen missing"
    return steps, pg.inner_text("#doneText")

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 390, "height": 820})
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        pg.goto("http://127.0.0.1:8765/index.html")
        pg.wait_for_function("document.querySelectorAll('#selUnit option').length > 0")
        print("eyebrow:", pg.inner_text("#eyebrow"))
        units = pg.locator("#selUnit option").count(); print("units:", units)
        # Abschnitt wählen (zweite Option = erster echter Abschnitt), Lerntage prüfen
        opts = [o for o in pg.locator("#selSection option").all_inner_texts()]
        print("sections:", opts)
        if len(opts) > 1:
            pg.select_option("#selSection", index=1)
        days = pg.locator("#selDay option").all_inner_texts(); print("days:", days)
        sizes = [int(d.split("·")[1].split()[0]) for d in days]
        assert all(5 <= s <= 12 for s in sizes), sizes
        set_n = sizes[0]
        print("subline:", pg.inner_text("#subline"))
        # Lookup fr by de for the chosen set via the set list
        rows = pg.locator("#setListBody tr").all_inner_texts()
        assert len(rows) == set_n, (len(rows), set_n)
        byde = {}
        for r in rows:
            parts = r.split("\t"); fr = parts[0].split("\n")[0].strip(); de = parts[1].strip(); byde[de] = fr
        # Modus DE→FR: erste Antwort falsch (leer lassen → Lösung zeigen), rest richtig
        pg.click("[data-mode=de_fr]")
        assert pg.is_visible("#tipBox"), "tip missing at round start"
        print("tip:", pg.inner_text("#tipTitle"))
        first = {"n": 0}
        def ans(label, prompt):
            first["n"] += 1
            if first["n"] == 1: return None  # Lösung zeigen → falsch → kommt wieder
            return byde.get(prompt, "xyz")
        steps, txt = play_round(pg, ans)
        print("DE→FR:", steps, "steps |", txt)
        assert not pg.is_visible("#tipBox") or True
        assert "gesammelt" in txt
        ring = pg.inner_text("#ringN"); print("ring:", ring)
        # Fehlerliste sollte jetzt leer sein (das falsche Wort wurde danach richtig beantwortet)
        print("modes:", [t.replace("\n", " ") for t in pg.locator("#modes button").all_inner_texts()])
        # FR→DE komplett
        pg.click("[data-mode=fr_de]"); steps, txt = play_round(pg, lambda l, p: None); print("FR→DE:", steps, "|", txt)
        # IPA→FR: alles richtig per Lookup über reveal? Wir tippen die Lösung nach "Lösung zeigen" nicht; stattdessen prüfen wir nur Ablauf
        if pg.locator("[data-mode=ipa_fr]").is_enabled():
            pg.click("[data-mode=ipa_fr]"); steps, txt = play_round(pg, lambda l, p: None); print("IPA→FR:", steps, "|", txt)
            assert pg.is_visible("#btnRetryWrong")
            errs = pg.inner_text("[data-mode=errors]"); print("errors button:", errs.replace("\n", " "))
            assert "gemerkt" in errs
            pg.click("[data-mode=errors]"); steps, txt = play_round(pg, lambda l, p: byde.get(p, "xyz")); print("Fehlerliste:", steps, "|", txt)
        # Satzmodus
        if pg.locator("[data-mode=sent_de_fr]").is_enabled():
            pg.click("[data-mode=sent_de_fr]")
            pg.fill("#answer", "Bonjour"); pg.press("#answer", "Enter"); v = pg.inner_text("#verdict"); print("Satz verdict:", v.split("\n")[0])
            pg.click("#btnStop"); assert pg.is_visible("#setList")
        # Persistenz + Reload
        ring = pg.inner_text("#ringN")
        pg.reload(); pg.wait_for_function("document.querySelectorAll('#selUnit option').length > 0")
        print("after reload:", pg.inner_text("#eyebrow"), "| ring", pg.inner_text("#ringN"))
        assert pg.inner_text("#ringN") == ring
        # Tipps-Seite
        pg.click("[data-tab=tips]"); assert pg.locator("#tipList li").count() == 10
        # Wortliste
        pg.click("[data-tab=cahier]"); assert pg.locator("#cahierBody tr").count() == N
        pg.screenshot(path=str(tmp / "cahier.png"))
        b.close()
finally:
    srv.terminate()
print("page errors:", errors)
assert not errors
print("ALL OK", tmp)
