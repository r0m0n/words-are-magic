"""Browser-Smoke-Test der Englisch-Variante (/en/ bzw. ?lang=en) mit Playwright.
Prüft Umleitung, Unit-Auswahl (Welcome, Unit 1–4), Lerntage, DE→EN tippen, Groß-/Kleinschreibung,
IPA-Modus nur mit vollständiger Lautschrift, Hinweise, Vorlese-Knopf, getrennten Lernstand und Reload."""
import json, shutil, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent
tmp = Path(tempfile.mkdtemp())
shutil.copy(REPO / "index.html", tmp / "index.html")
shutil.copy(REPO / "vocab.json", tmp / "vocab.json")
(tmp / "en").mkdir()
shutil.copy(REPO / "en" / "index.html", tmp / "en" / "index.html")
shutil.copy(REPO / "en" / "vocab.json", tmp / "en" / "vocab.json")
data = json.loads((REPO / "en" / "vocab.json").read_text(encoding="utf-8"))
E = data["entries"]
N = len(E)
srv = subprocess.Popen([sys.executable, "-m", "http.server", "8766", "--bind", "127.0.0.1"], cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
errors = []


def play_round(pg, answer_fn, max_steps=120):
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
        pg.on("console", lambda m: errors.append(m.text) if m.type == "error" and "404" not in m.text else None)
        pg.goto("http://127.0.0.1:8766/en/")
        pg.wait_for_function("document.querySelectorAll('#selUnit option').length > 0")
        assert "lang=en" in pg.url, pg.url
        eb = pg.text_content("#eyebrow"); print("eyebrow:", eb)
        assert eb.startswith("Englisch · Welcome"), eb
        units = pg.locator("#selUnit option").all_inner_texts(); print("units:", units)
        assert len(units) == 5 and units[0].startswith("Welcome") and units[1].startswith("Unit 1"), units
        assert "Englisch" in pg.inner_text("#modes"), "mode labels not localised"
        assert pg.title() == "Words are magic · Englisch"

        # Groß-/Kleinschreibung und Annahmen direkt prüfen
        def cmp(id_, given):
            return pg.evaluate("([id, g]) => compareWord(g, BYID.get(id)).result", [id_, given])
        by_en = {e["en"]: e["id"] for e in E}
        mon = next(e["id"] for e in E if e["en"] == "Monday")
        assert cmp(mon, "Monday") == "ok" and cmp(mon, "monday") == "near", (cmp(mon, "Monday"), cmp(mon, "monday"))
        see = by_en["(to) see"]
        assert cmp(see, "see") == "ok" and cmp(see, "to see") == "ok" and cmp(see, "See") == "ok" and cmp(see, "sea") == "bad"
        city = by_en["city"]
        assert cmp(city, "city") == "ok" and cmp(city, "a city") == "ok"
        fine = by_en["I'm fine(, thanks)."]
        assert cmp(fine, "I’m fine, thanks.") == "ok" and cmp(fine, "i'm fine") == "near"
        want = by_en["(to) want to do sth."]
        assert cmp(want, "want to do something") == "ok" and cmp(want, "want to do") == "ok"
        assert cmp(by_en["There's …"], "There is") == "ok" and cmp(by_en["It/He/She isn't here."], "she is not here") == "ok"
        assert cmp(by_en["I can't …"], "I cannot") == "ok" and cmp(by_en["I can't …"], "I can") == "bad"
        print("Vergleichsregeln OK")

        # Unit 2, alle Abschnitte → Lerntage aus der Wortliste (8 Wörter)
        pg.select_option("#selUnit", "2")
        days = pg.locator("#selDay option").all_inner_texts(); print("U2 days:", len(days), days[:2])
        assert all("8 Wörter" in d for d in days[:-1])
        u2d1 = [e for e in E if e["unit"] == 2 and e["day"] == 1]
        accept_by_de = {e["de"]: e["en_accept"][0] for e in u2d1}
        pg.click("[data-mode=de_fr]")
        assert pg.is_visible("#tipBox")
        tip = pg.inner_text("#tipTitle"); print("tip:", tip)
        first = {"n": 0}
        def ans(label, prompt):
            first["n"] += 1
            if first["n"] == 1:
                return None
            return accept_by_de.get(prompt, "xyz")
        steps, txt = play_round(pg, ans); print("DE→EN:", steps, "|", txt)
        assert "8 von 8" in txt, txt
        # Hinweis aus dem Buch erscheint nach dem Aufdecken (U2-001 hat einen)
        pg.click("[data-mode=fr_de]")
        seen_note = False
        for _ in range(12):
            if not pg.is_visible("#quiz"):
                break
            pg.press("body", " ")
            if "💡" in pg.inner_text("#reveal"):
                seen_note = True
                assert pg.locator("#reveal [data-say]").count() >= 1, "Vorlese-Knopf fehlt"
            pg.press("body", "2")
        assert seen_note, "note not shown"
        # IPA-Modus: nur Einträge mit vollständiger Lautschrift
        n_ipa = sum(1 for e in u2d1 if e.get("ipa") and e.get("ipa_full"))
        ipa_btn = pg.inner_text("[data-mode=ipa_fr]"); print("ipa button:", ipa_btn.replace("\n", " "))
        assert ipa_btn.strip().endswith(f"/ {n_ipa}"), (ipa_btn, n_ipa)
        pg.click("[data-mode=ipa_fr]")
        assert pg.is_visible("#btnSayPrompt"), "Anhören-Knopf im IPA-Modus fehlt"
        assert not pg.is_visible("#accents"), "Akzentleiste sollte im Englischen fehlen"
        steps, txt = play_round(pg, lambda l, p: None); print("IPA→EN:", steps, "|", txt)
        errs = pg.inner_text("[data-mode=errors]"); assert "gemerkt" in errs
        # Satzmodus mit den Probesätzen (16 Sätze in Lerntag 1)
        sent = {e["example_de"]: e["example_en"] for e in u2d1 if e.get("example_en")}
        sent.update({e["example2_de"]: e["example2_en"] for e in u2d1 if e.get("example2_en")})
        assert pg.inner_text("[data-mode=sent_de_fr]").strip().endswith(f"/ {len(sent)}")
        pg.click("[data-mode=sent_de_fr]")
        p0 = pg.inner_text("#qPrompt"); pg.fill("#answer", sent[p0].lower()); pg.press("#answer", "Enter")
        v = pg.inner_text("#verdict"); print("Satz klein getippt:", v.split("\n")[0]); assert "Großschreibung" in v
        pg.press("body", "Enter")
        steps, txt = play_round(pg, lambda l, p: sent.get(p, "xyz")); print("Sätze DE→EN:", steps, "|", txt)
        ring = pg.inner_text("#ringN")
        # Lernstand getrennt vom Französischen
        keys = pg.evaluate("Object.keys(localStorage)"); print("localStorage:", sorted(keys))
        assert any(k.startswith("wam-en:state") for k in keys) and not any(k.startswith("wam:state") for k in keys)
        pg.reload(); pg.wait_for_function("document.querySelectorAll('#selUnit option').length > 0")
        assert pg.inner_text("#ringN") == ring and pg.text_content("#eyebrow").startswith("Englisch · Unit 2")
        pg.click("[data-tab=tips]"); assert pg.locator("#tipList li").count() == 10
        assert "two, too und to" in pg.inner_text("#tipList")
        pg.click("[data-tab=cahier]"); assert pg.locator("#cahierBody tr").count() == N
        assert pg.locator("th.th-lang").first.inner_text() == "Englisch"
        # Französisch daneben unverändert erreichbar
        pg.goto("http://127.0.0.1:8766/")
        pg.wait_for_function("document.querySelectorAll('#selUnit option').length > 0")
        assert pg.text_content("#eyebrow").startswith("Französisch · Unité"), pg.text_content("#eyebrow")
        assert pg.inner_text("#ringN").startswith("0 /")
        pg.screenshot(path=str(tmp / "fr.png"))
        b.close()
finally:
    srv.terminate()
print("page errors:", errors)
assert not errors
print("ALL OK", tmp)
