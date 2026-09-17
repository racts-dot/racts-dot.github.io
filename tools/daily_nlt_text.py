#!/usr/bin/env python3
"""Fetch the NLT text for Daily Chapter's recordings, one chapter at a time, split into its own sections.

Her 16 Sep 2026 picks: "Whole book nlt - nothing else to be recorded", then "A" (whole Bible, ~US$130)
"but can it be divided into seperate code sections". Sections = the NLT's own headings (h3.subhead), so each
recording can be jumped to section by section. This script costs nothing; recording is a separate step.
The text stays private on this Mac (~/daily_voice/nlt), never in a repo: the NLT is licensed text.
api.nlt.to without a key: 50 verses a request, about 500 requests a day - so this stops at 480 and is re-run
the next day; chapters already fetched are skipped.
"""
import html, json, pathlib, re, sys, time, urllib.parse, urllib.request

SITE = pathlib.Path(__file__).resolve().parent.parent
OUT = pathlib.Path.home() / "daily_voice" / "nlt"
LOG = OUT / "requests.json"
page = (SITE / "daily" / "index.html").read_text(encoding="utf-8")
books = json.loads(re.search(r"BOOKS_JSON_START \*/\s*const BOOKS = (\[.*?\]);", page, re.S).group(1))
books = [b for b in books if b["testament"] == "NT"] + [b for b in books if b["testament"] != "NT"]
NLT_NAMES = {"Song of Solomon": "Song of Songs"}
OUT.mkdir(parents=True, exist_ok=True)
today = time.strftime("%Y-%m-%d")
log = json.loads(LOG.read_text()) if LOG.exists() else {}
used = log.get(today, 0)
LIMIT = 480


def get(ref):
    global used
    if used >= LIMIT:
        print(f"stopped for today at {used} requests; run again tomorrow"); sys.exit(0)
    url = "https://api.nlt.to/api/passages?ref=" + urllib.parse.quote(ref) + "&version=NLT&key=TEST"
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (daily-chapter personal reader)"}), timeout=60) as r:
                used += 1; log[today] = used; LOG.write_text(json.dumps(log))
                return r.read().decode("utf-8")
        except Exception as e:
            print("retry", ref, e); time.sleep(15 * (attempt + 1))
    sys.exit(f"failed {ref}")


def clean(fragment):
    t = re.sub(r'<span class="(?:tn|a-tn|vn)"[^>]*>.*?</span>', " ", fragment, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    return re.sub(r"\s+", " ", html.unescape(t)).strip()


for b in books:
    for n in range(1, b["chapters"] + 1):
        f = OUT / f"{b['name'].replace(' ', '_')}_{n}.json"
        if f.exists():
            continue
        name = NLT_NAMES.get(b["name"], b["name"])
        body, start, last = "", 1, 0
        while True:
            raw = get(f"{name}.{n}.{start}-{start + 49}")
            m = re.search(r'<div id="bibletext"[^>]*>(.*)</div>', raw, re.S)
            chunk = m.group(1) if m else raw
            nums = [int(x) for x in re.findall(r'<span class="vn">(\d+)</span>', chunk)]
            if not nums or max(nums) <= last:
                break
            chunk = re.sub(r'<h2 class="bk_ch_vs_header">.*?</h2>', "", chunk, flags=re.S)
            body += chunk
            last = max(nums)
            if last < start + 49:
                break
            start += 50
            time.sleep(1)
        if not last:
            sys.exit(f"no verses for {b['name']} {n}")
        parts = re.split(r'<h3 class="subhead">(.*?)</h3>', body, flags=re.S)
        sections = []
        lead = clean(parts[0])
        if lead:
            sections.append({"title": "", "text": lead})
        for i in range(1, len(parts), 2):
            sections.append({"title": clean(parts[i]), "text": clean(parts[i + 1])})
        sections = [s for s in sections if s["text"]]
        chars = sum(len(s["title"]) + len(s["text"]) for s in sections)
        f.write_text(json.dumps({"ref": f"{b['name']} {n}", "verses": last, "sections": sections, "chars": chars},
                                ensure_ascii=False))
        print(f"{b['name']} {n}: {len(sections)} sections, {chars} chars, requests today {used}", flush=True)
        time.sleep(1)
print("all chapters fetched")
