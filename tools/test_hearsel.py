"""Prove hearsel.js reads a selection in the NATURAL voice, and never in the phone voice.

    python tools/test_hearsel.py

Serves this checkout on localhost, opens an app in real Chrome, fakes ONLY the relay (no real
password is ever used or typed), and checks, with a control each way:
  1. connected device: select words -> tap Hear this -> ONE POST /tts with the words, the saved
     voice and the X-Pass header, audio plays, and speechSynthesis.speak is NEVER called;
  2. data-no-natural page: nothing is sent, and it says why;
  3. device with no password: it asks once (prompt), checks /ping, then reads.
"""
import http.server
import json
import pathlib
import sys
import threading
from functools import partial
from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), partial(http.server.SimpleHTTPRequestHandler, directory=str(ROOT)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = "http://127.0.0.1:%d" % srv.server_address[1]
WAV = (b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00@\x1f\x00\x00@\x1f\x00\x00\x01\x00\x08\x00data\x00\x00\x00\x00")

PAGE = """<!doctype html><meta charset=utf-8><main><p id=t>Bolt the barista reads this sentence aloud.</p></main>
%s<script src="/hearsel.js"></script>"""

results = []
def check(name, ok, detail=""):
    results.append(ok); print(("ok   " if ok else "FAIL ") + name + ("  | " + detail if detail else ""))

with sync_playwright() as p:
    b = p.chromium.launch(channel="chrome", args=["--autoplay-policy=no-user-gesture-required"])
    for case in ("connected", "no_natural", "no_password"):
        ctx = b.new_context()
        pg = ctx.new_page()
        calls = []
        def relay(route, req, calls=calls):
            calls.append((req.url.rsplit("/", 1)[1], req.headers.get("x-pass"), req.post_data))
            if req.url.endswith("/ping"):
                return route.fulfill(status=200, body="{}", headers={"Access-Control-Allow-Origin": "*"})
            return route.fulfill(status=200, body=WAV, headers={"Content-Type": "audio/wav", "Access-Control-Allow-Origin": "*"})
        pg.route("https://apps-notion-relay.apps-notion-relay.workers.dev/**", relay)
        extra = '<script src="/speak.js" data-no-natural></script>' if case == "no_natural" else ""
        # built first: Playwright passes (route, request) to a two-argument handler, which once
        # silently replaced a default argument here and served the page WITHOUT the tag under test
        html = PAGE % extra
        pg.route(BASE + "/case.html", lambda r: r.fulfill(status=200, body=html, headers={"Content-Type": "text/html"}))
        pg.goto(BASE + "/case.html")
        pg.evaluate("""() => { window.__phone = 0; window.__played = 0;
            if (window.speechSynthesis) speechSynthesis.speak = () => { window.__phone++; };
            const op = HTMLMediaElement.prototype.play; HTMLMediaElement.prototype.play = function(){ window.__played++; return op.call(this).catch(()=>{}); }; }""")
        if case == "connected":
            pg.evaluate("() => { localStorage.setItem('notionSync.pass', JSON.stringify('TEST-NOT-REAL')); localStorage.setItem('speak.nvoice','kore'); }")
        if case == "no_password":
            pg.on("dialog", lambda d: d.accept("TEST-NOT-REAL"))
        pg.evaluate("() => { const r = document.createRange(); r.selectNodeContents(document.getElementById('t')); const s = getSelection(); s.removeAllRanges(); s.addRange(r); }")
        pg.wait_for_selector("#hearsel", state="visible", timeout=3000)
        pg.click("#hearsel")
        pg.wait_for_timeout(1500)
        phone = pg.evaluate("window.__phone"); played = pg.evaluate("window.__played")
        tts = [c for c in calls if c[0] == "tts"]
        note = pg.evaluate("(document.getElementById('hearsel-note')||{}).textContent || ''")
        if case == "connected":
            body = json.loads(tts[0][2]) if tts else {}
            check("connected: one /tts call", len(tts) == 1, str(calls))
            check("connected: sends the words, the saved voice and the password header",
                  body.get("text", "").startswith("Bolt the barista") and body.get("voice") == "kore" and tts[0][1] == "TEST-NOT-REAL", str(body))
            check("connected: natural audio played", played == 1, "played=%d" % played)
            check("connected: phone voice never used", phone == 0, "phone=%d" % phone)
        if case == "no_natural":
            check("no-natural page: nothing sent", not calls, str(calls))
            check("no-natural page: says why", "keeps its words on your phone" in note, repr(note))
            check("no-natural page: phone voice never used", phone == 0)
        if case == "no_password":
            check("no password: /ping checked, then /tts", [c[0] for c in calls] == ["ping", "tts"], str([c[0] for c in calls]))
            check("no password: password kept for next time", pg.evaluate("localStorage.getItem('notionSync.pass')") == '"TEST-NOT-REAL"')
            check("no password: natural audio played, phone voice never", played == 1 and phone == 0)
        ctx.close()
    b.close()
srv.shutdown()
print("%d of %d checks passed" % (sum(results), len(results)))
sys.exit(0 if all(results) else 1)
