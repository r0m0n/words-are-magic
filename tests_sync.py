"""Abgleich-Test: zwei Browser-Kontexte (zwei Geräte) teilen einen Lernschlüssel gegen einen lokalen Nachbau
der Netlify-Funktion (tests_mock_server.py). Prüft A→B, B→A nach Reload und dass nichts überschrieben wird."""
import json, shutil, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright

REPO = Path(__file__).resolve().parent
tmp = Path(tempfile.mkdtemp()); shutil.copy(REPO / "index.html", tmp / "index.html")
shutil.copy(REPO / "vocab.json" if (REPO / "vocab.json").exists() else REPO / "vocab.sample.json", tmp / "vocab.json")
srv = subprocess.Popen([sys.executable, "-I", str(REPO / "tests_mock_server.py"), "8769"], cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
errs = []
READY = "document.querySelectorAll('#selUnit option').length > 0"

def wait_server(key, pred, timeout=10):
    """wartet, bis der Serverstand unter key das Prädikat erfüllt"""
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            doc = json.load(urllib.request.urlopen(f"http://127.0.0.1:8769/api/state?key={key}"))
            if pred(doc["data"]): return doc
        except Exception: pass
        time.sleep(0.3)
    raise AssertionError("Server hat den erwarteten Stand nicht erhalten")

def open_device(browser, key=None):
    ctx = browser.new_context(); pg = ctx.new_page()
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.goto("http://127.0.0.1:8769/index.html"); pg.wait_for_function(READY)
    pg.click("[data-tab=settings]"); pg.wait_for_selector("#syncAvailable", state="visible")
    if key is None: pg.click("#btnSyncGen"); key = pg.input_value("#syncKey")
    else: pg.fill("#syncKey", key)
    pg.click("#btnSyncConnect"); pg.wait_for_function("document.getElementById('syncStatus').textContent.includes('verbunden')")
    pg.click("[data-tab=learn]"); pg.select_option("#selSection", index=1); time.sleep(0.3)
    return pg, key

try:
    with sync_playwright() as p:
        b = p.chromium.launch()
        pa, key = open_device(b)
        # A: FR→DE komplett richtig
        pa.click("[data-mode=fr_de]")
        while pa.is_visible("#quiz"): pa.press("body", " "); pa.press("body", "2")
        wait_server(key, lambda d: any(k.endswith("|fr_de") for k in d.get("rounds", {})))
        a_frde = pa.inner_text("[data-mode=fr_de]").replace("\n", " "); print("A:", a_frde)
        # B: gleicher Schlüssel, sieht A's Runde
        pb, _ = open_device(b, key)
        b_frde = pb.inner_text("[data-mode=fr_de]").replace("\n", " "); print("B sieht:", b_frde); assert b_frde == a_frde
        # B: ein Fehler in DE→FR
        pb.click("[data-mode=de_fr]"); pb.click("#btnShow"); pb.press("body", "Enter"); pb.click("#btnStop")
        wait_server(key, lambda d: any(c.get("last") == "bad" for c in d["state"]["cards"].values()))
        assert "1 gemerkt" in pb.inner_text("[data-mode=errors]")
        # A lädt neu → Fehler aus B sichtbar, A's Runde bleibt
        pa.reload(); pa.wait_for_function(READY); pa.wait_for_function("document.getElementById('syncLine').textContent.includes('gespeichert')")
        print("A nach Reload:", pa.inner_text("[data-mode=errors]").replace("\n", " "), "|", pa.inner_text("[data-mode=fr_de]").replace("\n", " "))
        assert "1 gemerkt" in pa.inner_text("[data-mode=errors]") and pa.inner_text("[data-mode=fr_de]").replace("\n", " ") == a_frde
        # Gleichzeitig: A antwortet, ohne vorher zu pullen – B's Stand darf nicht verloren gehen
        pa.click("[data-mode=ipa_fr]"); pa.click("#btnShow"); pa.press("body", "Enter"); pa.click("#btnStop")
        doc = wait_server(key, lambda d: sum(1 for c in d["state"]["cards"].values() if c.get("last") == "bad") == 2)
        bad = sorted(k for k, c in doc["data"]["state"]["cards"].items() if c.get("last") == "bad"); print("Server Fehlerkarten:", bad)
        assert len(bad) == 2
        b.close()
finally:
    srv.terminate()
print("page errors:", errs); assert not errs
print("SYNC OK")
