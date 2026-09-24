# -*- coding: utf-8 -*-
"""Draw the My Binders app icon on Vertex (gemini-3-pro-image, US$0.12, via spend_gate).
Her yes in chat, 24 Sep 2026. Same clay style as the To-Do icon she approved.
    python make_icon.py
"""
import base64, json, os, subprocess, sys, urllib.request
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, r"C:\Users\soyan\claude desktoi\review_board")
import spend_gate
GCLOUD = r"C:\Users\soyan\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"
MODEL = "gemini-3-pro-image"
URL = ("https://aiplatform.googleapis.com/v1/projects/gen-lang-client-0626840434/locations/global/"
       "publishers/google/models/%s:generateContent" % MODEL)
PROMPT = ("A square app icon, full bleed to every edge, soft matte clay 3D style with gentle shadow, "
          "on a plain warm cream background filling the whole square. Subject: three upright ring binders "
          "standing side by side, in muted terracotta, sage green and warm ivory, with a small green tick on "
          "the front binder's spine label. Centred, simple, readable at phone-icon size. "
          "Absolutely no text, letters, numbers or logos. No rounded-corner tile, no border, no frame.")
out = os.path.join(HERE, "icon-source.png")
if os.path.exists(out):
    sys.exit("already drawn: " + out)
tok = subprocess.run([GCLOUD, "auth", "print-access-token"], capture_output=True, text=True).stdout.strip()
rid = spend_gate.check("vertex", 0.12, MODEL, kind="art")
body = {"contents": [{"role": "user", "parts": [{"text": PROMPT}]}],
        "generationConfig": {"responseModalities": ["TEXT", "IMAGE"],
                             "imageConfig": {"aspectRatio": "1:1", "imageSize": "2K"}}}
req = urllib.request.Request(URL, data=json.dumps(body).encode(), headers={
    "Authorization": "Bearer " + tok, "Content-Type": "application/json"})
try:
    r = json.loads(urllib.request.urlopen(req, timeout=300).read())
except Exception as e:
    spend_gate.record("vertex", 0.0, MODEL, note="binders icon failed", reservation_id=rid, kind="art")
    sys.exit("failed: %s" % e)
img = None
for p in r["candidates"][0]["content"]["parts"]:
    d = p.get("inlineData") or p.get("inline_data")
    if d and d.get("data"):
        img = base64.b64decode(d["data"]); break
spend_gate.record("vertex", 0.12 if img else 0.0, MODEL, note="binders app icon", reservation_id=rid, kind="art")
if not img:
    sys.exit("no image in reply")
open(out, "wb").write(img)
print("drew", out, len(img) // 1024, "KB")
