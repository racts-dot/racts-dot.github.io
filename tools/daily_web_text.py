#!/usr/bin/env python3
"""Fetch the World English Bible (public domain) chapter by chapter from bible-api.com, the same source
Daily Chapter shows for "web", and store it for pricing and recording the natural voice.

Her 16 Sep 2026 yes (relayed): "Just do the whole book recordings". WEB, not NLT: the NLT is licensed
text and a kept recording is a copy of it, which she has not agreed to. This script costs nothing.
Output: daily_voice/web/<Book>_<n>.json {"ref","text","chars"}; skips chapters already fetched.
"""
import json, pathlib, re, sys, time, urllib.request, urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT.parent / "daily_voice" / "web"          # outside the site: never published
html = (ROOT / "daily" / "index.html").read_text(encoding="utf-8")
books = json.loads(re.search(r"BOOKS_JSON_START \*/\s*const \w+ = (\[.*?\]);", html, re.S).group(1))
one = json.loads(re.search(r"const ONE_CHAPTER_VERSES = (\{.*?\});", html).group(1))
OUT.mkdir(parents=True, exist_ok=True)
total = 0
books = [b for b in books if b["testament"] == "NT"] + [b for b in books if b["testament"] != "NT"]   # the NT plan first
for b in books:
    name, chapters = (b["name"], b["chapters"]) if isinstance(b, dict) else (b[0], b[1])
    for n in range(1, chapters + 1):
        f = OUT / f"{name.replace(' ', '_')}_{n}.json"
        if f.exists():
            total += json.loads(f.read_text())["chars"]; continue
        ref = f"{name} 1:1-{one[name]}" if name in one else f"{name} {n}"
        for attempt in range(6):
            try:
                with urllib.request.urlopen("https://bible-api.com/" + urllib.parse.quote(ref) + "?translation=web", timeout=60) as r:
                    data = json.load(r); break
            except Exception as e:
                time.sleep(10 * (attempt + 1))
        else:
            sys.exit(f"failed {ref}")
        text = " ".join(re.sub(r"\s+", " ", v["text"]).strip() for v in data["verses"])
        f.write_text(json.dumps({"ref": f"{name} {n}", "text": text, "chars": len(text)}, ensure_ascii=False))
        total += len(text)
        print(f"{name} {n}  {len(text)}  running {total}", flush=True)
        time.sleep(2.1)
print("TOTAL chars", total)
