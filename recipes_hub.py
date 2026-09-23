#!/usr/bin/env python3
"""One Recipes app: /recipes/ becomes the home for all four recipe collections.

Her words, 15 Sep 2026: "can you combine the recipes into one recipes", and her pick
"All four in one Recipes app": the 11 Recipes pages, Hormozi Marketing Recipes,
Doser AI Marketing Workflows and Sabrina's Prompt Cookbook. One home-screen icon, tabs,
and one search box across all of them.

Nothing inside the four collections is rewritten. Each keeps its own page, read aloud, videos
and Notion saving. This script:
  1. writes recipes/cards-hormozi.json, cards-doser.json and cards-prompts.json - this app's own
     copy of the other three collections' cards, so /recipes/ no longer needs those pages to be
     there (her pick, 20 Sep 2026: "Not yet - move data first");
  2. writes recipes/index.html, the combined home, from what the four pages actually contain;
  3. adds a slim "All recipes" bar and a find-on-open helper (#find=...) to the three other pages,
     so a card tapped on the home opens that exact recipe.

    python3 recipes_hub.py          # after build_recipes.py or publish_marketing_pages.py

build_recipes.py and publish_marketing_pages.py both call it at the end, so a rebuild keeps the home.
"""
import glob
import hashlib
import html as H
import json
import os
import pathlib
import re

SITE = pathlib.Path(__file__).resolve().parent
MARK = "<!--recipes-hub-bar-->"
# 23 Sep 2026, her pick: "The Workflows address forwards to Recipes". A page carrying this mark is only a
# forwarder now: no bar is added to it, and its cards come from the source the publisher hands over.
RETIRED = "<!--retired-to-recipes-->"

BAR = MARK + """
<style>
.rh-bar{position:sticky;top:0;z-index:2147483000;display:flex;align-items:center;gap:10px;padding:8px 14px;
  font:600 14px/1.2 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:rgba(15,17,21,.92);color:#f2efe8;
  -webkit-backdrop-filter:blur(10px);backdrop-filter:blur(10px)}
.rh-bar a{color:#f2efe8;text-decoration:none;padding:6px 10px;border-radius:999px;background:rgba(255,255,255,.1)}
.rh-bar span{opacity:.7;font-weight:500}
</style>
<nav class="rh-bar" aria-label="Recipes"><a href="../recipes/">&#8592; All recipes</a><span>__NAME__</span></nav>
<script>
/* Opened from the Recipes home as page/#find=Title: put the title in this page's own search box
   and bring the first match into view, opened if it folds. */
(function(){
  var m = location.hash.match(/^#find=(.+)$/); if(!m) return;
  var want = decodeURIComponent(m[1]);
  function go(tries){
    var q = document.getElementById("q");
    if(q){ q.value = want; q.dispatchEvent(new Event("input", {bubbles:true})); }
    setTimeout(function(){
      var low = want.toLowerCase(), hit = null;
      document.querySelectorAll("details, article, .card, section, li").forEach(function(el){
        if(!hit && el.offsetParent !== null && (el.textContent || "").toLowerCase().indexOf(low) >= 0 && el.textContent.length < 20000) hit = el;
      });
      if(!hit){ if(tries < 10) setTimeout(function(){ go(tries + 1); }, 300); return; }
      var d = hit.closest("details") || (hit.tagName === "DETAILS" ? hit : null); if(d) d.open = true;
      var btn = hit.querySelector("button[aria-expanded='false']"); if(btn) btn.click();
      hit.scrollIntoView({block:"start"}); window.scrollBy(0, -60);
    }, 250);
  }
  if(document.readyState === "complete") go(0); else window.addEventListener("load", function(){ go(0); });
})();
</script>
"""


def add_bar(html, name):
    """Idempotent: the bar goes right after <body>, once."""
    if MARK in html:
        return html
    bar = BAR.replace("__NAME__", H.escape(name))
    m = re.search(r"<body[^>]*>", html, re.I)
    if m:
        return html[:m.end()] + "\n" + bar + html[m.end():]
    return bar + html


def data_blob(path, text=None):
    s = text if text is not None else open(path, encoding="utf-8").read()
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', s, re.S)
    return json.loads(m.group(1).replace("<\\/", "</")) if m else None


def txt(s, n=160):
    s = re.sub(r"<[^>]+>", " ", str(s or ""))
    s = H.unescape(re.sub(r"\s+", " ", s)).strip()
    return s if len(s) <= n else s[: n - 1].rsplit(" ", 1)[0] + "…"


def recipe_meta(name, page):
    """Listening time and source videos for a recipe card (her 16 Sep ask)."""
    parts = []
    try:
        dur = json.load(open(SITE / "recipes" / "a" / (name[:-5] + ".json"), encoding="utf-8")).get("dur")
        if dur:
            parts.append("\U0001F3A7 %d min listen" % max(1, round(dur / 60)))
    except (OSError, ValueError):
        pass
    try:
        videos = json.load(open(SITE / "recipes_src" / "videos.json", encoding="utf-8"))
    except (OSError, ValueError):
        videos = {}
    body = re.sub(r"<script.*?</script>", " ", page, flags=re.S)
    ids = [v for v in dict.fromkeys(re.findall(r"youtube\.com/watch\?v=([A-Za-z0-9_-]{11})", body)) if v in videos]
    if ids:
        t = sum(videos[v].get("dur") or 0 for v in ids)
        clock = ("%d:%02d:%02d" % (t // 3600, t // 60 % 60, t % 60)) if t >= 3600 else ("%d:%02d" % (t // 60, t % 60))
        parts.append("\u25B6 %d video%s, %s" % (len(ids), "" if len(ids) == 1 else "s", clock))
    return " \u00B7 ".join(parts)


def recipe_pages():
    idx = open(SITE / "recipes" / "index.html", encoding="utf-8").read() if (SITE / "recipes" / "index.html").exists() else ""
    blurbs = {m.group(1): txt(m.group(2)) for m in re.finditer(r'<a class="card" href="([^"]+\.html)">.*?<div class="d">(.*?)</div>', idx, re.S)}
    hub = re.search(r'<script id="hub" type="application/json">(.*?)</script>', idx, re.S)
    if hub:   # the home already replaced the old list: keep the one-line blurbs it carried
        for x in json.loads(hub.group(1).replace("<\\/", "</")):
            if x.get("src") == "recipes" and x.get("desc"):
                blurbs.setdefault(x["href"], x["desc"])
    out = []
    for f in sorted(glob.glob(str(SITE / "recipes" / "*.html"))):
        name = os.path.basename(f)
        if name == "index.html":
            continue
        s = open(f, encoding="utf-8").read()
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
        vid = re.search(r"(?:youtube(?:-nocookie)?\.com/(?:embed/|watch\?v=)|youtu\.be/|i\.ytimg\.com/vi/)([A-Za-z0-9_-]{11})", s)
        num = re.match(r"recipe-(\d+)", name)
        # skip the "From: <video>" provenance line, or a new recipe's card shows the source instead of the point
        first_p = next((m for m in re.finditer(r"<p[^>]*>(.*?)</p>", s, re.S)
                        if not re.match(r"^(\S+\s+){0,3}from:", re.sub(r"<[^>]+>", "", m.group(1)).strip(), re.I)), None)
        out.append({
            "src": "recipes", "label": ("Recipe " + str(int(num.group(1)))) if num else "Read",
            "title": re.sub(r"^RECIPE\s*\d+\s*[—-]\s*", "", txt(h1.group(1) if h1 else name, 140), flags=re.I),
            "desc": blurbs.get(name) or txt(first_p.group(1) if first_p else "", 150),
            "href": name, "thumb": f"https://i.ytimg.com/vi/{vid.group(1)}/hqdefault.jpg" if vid else "",
            # 19 Sep, her "no video engraved in it": the id travels with the card so the picture plays here
            "vid": vid.group(1) if vid else "",
            "listen": os.path.exists(SITE / "recipes" / "a" / (name[:-5] + ".mp3")),
            "meta": recipe_meta(name, s),
        })
    return out


# ---- the cards this app now carries itself ------------------------------------------------
#
# 20 Sep 2026. Asked whether to retire /cookbook/ and /hormozi/, her pick was "Not yet - move data
# first". Until today a Hormozi, Doser or Prompt card opened here by FETCHING that other app's page
# and reading its data blob, so /recipes/ could not live without /hormozi/, /workflows/ and
# /cookbook/ - which is exactly what blocked retiring them. So the cards are now written into this
# folder as its own files and the page reads those first. The three old pages are NOT touched:
# retiring them is hers to trigger, and this is only the move.
#
# SEPARATE FILES, NOT INLINED IN THE PAGE, and the reason is the phone. Measured 20 Sep 2026: the
# three blobs are 657 KB, 127 KB and 47 KB, and even cut back to what the panel actually draws they
# come to 481 + 87 + 38 = 606 KB against a home page of 253 KB. Inlining would make every visit
# carry all of it before a single card is tapped. The panel was already lazy, so files fetched on
# demand leave the home page the size it is and make a tapped card CHEAPER than it was - 87 KB of
# JSON instead of the 186 KB HTML page it used to pull.
#
# Only the fields the home card and the panel read are copied. Nothing else travels.

LOCAL = {"hormozi": "cards-hormozi.json", "doser": "cards-doser.json", "prompts": "cards-prompts.json"}


def slim_card(topic, c, full=False):
    """One Hormozi/Doser card, cut to what the home card and the panel draw.

    full (the Doser cards only, 23 Sep 2026): her pick, "Recipes cards gain the 'Ask yourself' questions,
    the diagrams, the 'play from this moment' buttons and the 'I've done this' ticks, then Workflows
    forwards to Recipes. Nothing is lost." So a Doser card also keeps its check questions (checks), its
    diagram (dia), the second each quote starts at (claim_t, warn_t and each step's t), and prereq and
    rule when it has them. The ticks themselves live on the phone under each card's key, which is kept.
    Hormozi cards are cut exactly as before.
    """
    out = {"topic": txt(topic, 40)}
    for k in ("title", "gets", "claim", "warn"):
        if c.get(k):
            out[k] = c[k]
    if full:
        for k in ("claim_t", "warn_t"):
            if c.get(k) is not None:   # 0 is a real second: the quote is at the very start
                out[k] = c[k]
        # fit, start, shop, why and watch (23 Sep 2026): what /workflows/' fit filters and "Start here" read. Empty
        # on every card today (its has_fit is false), so they change nothing now and are there the day they are filled
        for k in ("checks", "dia", "prereq", "rule", "fit", "start", "shop", "why", "watch"):
            if c.get(k):
                out[k] = c[k]
    steps = []
    for v in c.get("steps") or []:
        # the page's own test is (sup === "no" || sup === "none" || !q), so an empty sup or q reads
        # the same as none at all - but "no", "none" and "partly" have to survive the cut, because
        # they are what marks a step as the AI's words rather than his
        st = {"do": v.get("do", "")}
        if v.get("q"):
            st["q"] = v["q"]
        if v.get("sup"):
            st["sup"] = v["sup"]
        if full and v.get("t") is not None:
            st["t"] = v["t"]
        steps.append(st)
    if steps:
        out["steps"] = steps
    src = [{k: v[k] for k in ("id", "title", "date") if v.get(k)} for v in c.get("src") or []]
    if src:
        out["src"] = src
    return out


def slim_prompt(p):
    """One cookbook prompt, cut the same way."""
    out = {"n": p.get("n", ""), "p": p.get("p", "")}
    tools = p.get("t")
    if isinstance(tools, str):
        tools = re.findall(r"'([^']+)'", tools) or [tools]
    if tools:
        out["t"] = tools
    src = [{k: v[k] for k in ("u", "v", "y") if v.get(k)} for v in p.get("src") or []]
    if src:
        out["src"] = src
    return out


# 23 Sep 2026, the last sentence sweep: every video's running time and each card's listening time were on /workflows/
# (video_box.py put them there from ~/yt-transcripts/metadata.csv) and nowhere in Recipes' card data. The publisher
# now runs video_box on the Doser source before handing it over, so they are read here from the very same line.
BOX = re.compile(r"var VDUR = (\{[^{}]*\}), RECDUR = (\{[^{}]*\}), WORDS = (\{[^{}]*\});")


def add_lengths(cards, text):
    """Put each video's length in seconds (d) on its source entry, and each card's word count (nw) on the card.

    From the videos box in the page handed over (text); a video or card it does not cover keeps what our own
    copy already had, so a rebuild never drops a length. Nothing is estimated: without a number, none is shown.
    """
    m = BOX.search(text or "")
    vdur, words = (json.loads(m.group(1)), json.loads(m.group(3))) if m else ({}, {})
    kept = SITE / "recipes" / LOCAL["doser"]
    old = json.loads(kept.read_text(encoding="utf-8")) if kept.exists() else {}
    olddur = {v["id"]: v["d"] for c in old.values() for v in c.get("src") or [] if v.get("id") and v.get("d")}
    for key, c in cards.items():
        for v in c.get("src") or []:
            d = vdur.get(v.get("id")) or olddur.get(v.get("id"))
            if d:
                v["d"] = d
        nw = words.get(key) or (old.get(key) or {}).get("nw")
        if nw:
            c["nw"] = nw
    ids = {v.get("id") for c in cards.values() for v in c.get("src") or []}
    have = {v.get("id") for c in cards.values() for v in c.get("src") or [] if v.get("d")}
    print("  doser: lengths for %d of %d videos (%s), listening time for %d of %d cards" % (
        len(have), len(ids), "from the videos box" if m else "our own copy only - no videos box handed over",
        sum(1 for c in cards.values() if c.get("nw")), len(cards)))
    return cards


def own_cards(folder, src, text=None):
    """Hormozi/Doser cards: from the other app while it is still there, from our copy once it is not.

    Keyed by each card's own key, in the order the topics list them. The fallback is the whole point
    of the move - once /hormozi/ or /workflows/ is retired the page that fed this is gone, and
    without it the next rebuild would quietly empty the tab it had been filling.
    """
    # 23 Sep 2026: text is the page the publisher built from its source but no longer writes to the site
    # (/workflows/ only forwards now), so the cards keep following their source instead of freezing
    if text is None and (SITE / folder / "index.html").exists():
        text = (SITE / folder / "index.html").read_text(encoding="utf-8")
        where = folder
    else:
        where = folder + " source"
    d = data_blob(None, text) if text is not None else None
    if d:
        cards = {c.get("key", ""): slim_card(t.get("name"), c, full=(src == "doser"))
                 for t in d.get("topics", []) for c in t.get("cards", [])}
        return (add_lengths(cards, text) if src == "doser" else cards), where
    kept = SITE / "recipes" / LOCAL[src]
    if kept.exists():
        return (json.loads(kept.read_text(encoding="utf-8")), "our own copy, /%s/ is gone" % folder)
    return ({}, "nothing: /%s/ is gone and there is no copy" % folder)


def own_prompts():
    """The cookbook prompts, the same way round. A plain list: a prompt's place in it is its key."""
    d = data_blob(SITE / "cookbook" / "index.html") if (SITE / "cookbook" / "index.html").exists() else None
    if d:
        return ([slim_prompt(x) for x in d], "cookbook")
    kept = SITE / "recipes" / LOCAL["prompts"]
    if kept.exists():
        return (json.loads(kept.read_text(encoding="utf-8")), "our own copy, /cookbook/ is gone")
    return ([], "nothing: /cookbook/ is gone and there is no copy")


def write_local(src, data):
    """Write this folder's copy, and hand back a URL that changes when the contents do.

    Without the stamp a phone that cached yesterday's file would keep it after a rebuild, which is
    the same fault the kit scripts already carry a ?v= for.
    """
    body = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    (SITE / "recipes" / LOCAL[src]).write_text(body, encoding="utf-8")
    return LOCAL[src] + "?v=" + hashlib.sha256(body.encode("utf-8")).hexdigest()[:10]


def recorded(src, key):
    """23 Sep 2026, her "i want the recorded good quality read": tools/record_cards.py writes one natural-voice
    mp3 per card, and only a card that has one gets the Listen button."""
    return 1 if (SITE / "recipes" / "a" / "c" / src / ("%s.mp3" % key)).exists() else 0


def topic_cards(folder, src, label, cards):
    out = []
    for key, c in cards.items():
        title = txt(c.get("title"), 120)
        out.append({"src": src, "label": txt(c.get("topic"), 40) or label, "title": title,
                    "desc": txt(c.get("gets"), 150),
                    # 23 Sep 2026, her "no links": the card opens here from our own copy, so it no longer
                    # carries a way out to the old app it came from
                    # 20 Sep, her "I'll want it like in the same app": the card's own key travels with
                    # it, so opening it here finds the one card and never a title that merely matches
                    "k": key, "a": recorded(src, key),
                    # 17 Sep, her "no thumbnail ... no video": the card's first source video, like the recipe cards
                    "thumb": (f"https://i.ytimg.com/vi/{c['src'][0]['id']}/mqdefault.jpg" if c.get("src") and c["src"][0].get("id") else ""),
                    "vid": (c["src"][0]["id"] if c.get("src") and c["src"][0].get("id") else ""),
                    "listen": False,
                    "meta": ("\u25B6 %d video%s" % (len(c["src"]), "" if len(c["src"]) == 1 else "s")) if c.get("src") else ""})
        if src == "doser":
            # 23 Sep 2026, her "nothing is lost": the Doser tab's map, filters and "already doing" badge are drawn
            # before any card is opened, so each Doser card carries how many questions it asks (nq) and how many
            # of his videos it comes from (ns), and its fit and start-here mark when the source has them
            out[-1].update({"nq": len(c.get("checks") or []), "ns": len(c.get("src") or [])})
            if c.get("fit"):
                out[-1]["fit"] = c["fit"]
            if c.get("start"):
                out[-1]["st"] = 1
    return out


def prompts(items):
    out = []
    for i, p in enumerate(items):
        tools = p.get("t") or []
        # 19 Sep, her "There's no thumbnail updated just yet": every one of these cards was pictureless,
        # and the cookbook already carried the video each prompt came from. Measured 20 Sep: all 99
        # resolve to a YouTube id, so the whole Prompts tab gets the same real frame the other tabs use.
        vids = [m.group(1) for m in (re.search(r"[?&]v=([A-Za-z0-9_-]{11})", s.get("u") or "")
                                     for s in (p.get("src") or [])) if m]
        vids = list(dict.fromkeys(vids))
        out.append({"src": "prompts", "label": ", ".join(tools)[:40] or "Prompt", "title": txt(p.get("n"), 120),
                    "desc": txt(p.get("p"), 150),   # no link out to /cookbook/, same reason as topic_cards
                    # the cookbook's data is a plain list, so its place in that list is its key
                    "k": i, "a": recorded("prompts", i),
                    "thumb": (f"https://i.ytimg.com/vi/{vids[0]}/mqdefault.jpg" if vids else ""),
                    "vid": vids[0] if vids else "",
                    "meta": ("\u25B6 %d video%s" % (len(vids), "" if len(vids) == 1 else "s")) if vids else "",
                    "listen": False})
    return out


PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex,nofollow">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Recipes">
<meta name="theme-color" content="#0f1115">
<link rel="apple-touch-icon" href="icon-180.png">
<link rel="icon" type="image/png" sizes="192x192" href="icon-192.png">
<link rel="manifest" href="manifest.webmanifest">
<title>Recipes</title>
<style>
:root{--bg:#f6f3ee;--card:#fff;--ink:#1a1a1a;--ink2:#5d5a55;--line:#e6e0d6;--accent:#b4541e;--chip:#efe9df;
  --recipes:#b4541e;--hormozi:#1d5b8f;--doser:#2f7a4f;--prompts:#7a3f8f;--serif:"Iowan Old Style","Palatino Linotype",Georgia,serif;
  --sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0f1115;--card:#171a20;--ink:#f2efe8;--ink2:#a8a39a;
  --line:#262a31;--accent:#e08a4e;--chip:#20242b;--recipes:#e08a4e;--hormozi:#6fa8dc;--doser:#6cc08e;--prompts:#c38fd6}}
:root[data-theme="dark"]{--bg:#0f1115;--card:#171a20;--ink:#f2efe8;--ink2:#a8a39a;--line:#262a31;--accent:#e08a4e;--chip:#20242b;
  --recipes:#e08a4e;--hormozi:#6fa8dc;--doser:#6cc08e;--prompts:#c38fd6}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 var(--sans);padding-inline:16px;padding-block:0 60px}
.wrap{max-width:900px;margin:0 auto}
header{padding-block:28px 10px}
h1{font:600 clamp(32px,8vw,46px)/1.05 var(--serif);margin:0 0 6px;letter-spacing:-.01em}
.sub{margin:0;color:var(--ink2);font-size:15px}
.search{position:sticky;top:0;z-index:5;background:var(--bg);padding-block:12px 8px}
.search input{width:100%;font:17px var(--sans);padding:13px 16px;border-radius:14px;border:1px solid var(--line);background:var(--card);color:var(--ink)}
.tabs{display:flex;gap:8px;overflow-x:auto;padding-block:6px 4px;scrollbar-width:none}
.tabs::-webkit-scrollbar{display:none}
.tab{flex:none;border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:9px 14px;font:600 14px var(--sans);cursor:pointer}
.tab[aria-pressed="true"]{background:var(--ink);color:var(--bg);border-color:var(--ink)}
.tab b{font-weight:500;opacity:.65;margin-left:4px}
.count{color:var(--ink2);font-size:13px;margin:10px 2px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:12px}
.card{display:flex;flex-direction:column;background:var(--card);border:1px solid var(--line);border-radius:16px;overflow:hidden;
  text-decoration:none;color:inherit;transition:transform .12s ease}
.card:active{transform:scale(.99)}
.th img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:var(--chip)}
/* 19 Sep, her "no video engraved in it ... there is nothing": the picture is its own button now, not part
   of the link, so tapping it plays the video right here instead of leaving for the page. The words below
   still open the recipe. A button cannot sit inside a link, which is why the card stopped being one. */
.th{all:unset;display:block;position:relative;width:100%;aspect-ratio:16/9;background:var(--chip)}
button.th{cursor:pointer}
.th::after{content:"\\25B6";position:absolute;left:10px;bottom:10px;width:34px;height:34px;border-radius:50%;background:rgba(0,0,0,.65);color:#fff;display:grid;place-items:center;font-size:14px;padding-left:2px;box-sizing:border-box}
.th:focus-visible{outline:3px solid var(--accent);outline-offset:-3px}
.th.playing{cursor:default}
.th.playing::after{display:none}
.th iframe{position:absolute;inset:0;width:100%;height:100%;border:0;display:block}
/* top LEFT on purpose: YouTube puts its own share and title buttons in the top right of the embed */
.th .x{all:unset;position:absolute;left:6px;top:6px;z-index:2;width:28px;height:28px;border-radius:50%;
  background:rgba(0,0,0,.72);color:#fff;display:grid;place-items:center;font-size:13px;cursor:pointer}
.card .in{padding:12px 14px 14px;display:grid;gap:6px;text-decoration:none;color:inherit}
/* 20 Sep, her "I don't want it in a separate links or some sort. I'll want it like in the same app":
   tapping the words on a Hormozi, Doser or Prompt card opens what that card SAYS right here, under it,
   instead of sending her to the other app. The words stay a real link, so a long press, a new tab and a
   phone with the script blocked all still work, and the full card - the ticks, Notion, the read-aloud -
   is one tap away at the bottom of the panel. The other apps are untouched. */
.panel{grid-column:1/-1;background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;display:grid;gap:12px}
.panel h2{font:600 clamp(20px,5vw,25px)/1.25 var(--serif);margin:0}
.panel .label{font:700 11px/1 var(--sans);letter-spacing:.04em;text-transform:uppercase;color:var(--accent);display:block;margin-bottom:6px}
.panel p{margin:0}
.panel q{color:var(--ink2)}
.panel ol{margin:0;padding-left:20px;display:grid;gap:10px}
.panel .sq{display:block;color:var(--ink2);font-size:14px;margin-top:3px}
.panel .ai{font:400 10.5px/1.5 ui-monospace,Menlo,Consolas,monospace;letter-spacing:.04em;color:var(--ink2);
  border:1px dashed var(--line);border-radius:5px;padding:1px 5px;white-space:nowrap}
.panel pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.55 ui-monospace,Menlo,Consolas,monospace;
  background:var(--chip);padding:12px 14px;border-radius:12px;margin:0}
.panel .vids{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}
.panel .vids .th{border-radius:12px;overflow:hidden}
.panel .vids .l{font-size:12px;color:var(--ink2);margin-top:5px}
.panel .row{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.panel .btn{font:700 14px/1 var(--sans);padding:11px 14px;border-radius:10px;border:1px solid var(--line);
  background:var(--bg);color:var(--ink);cursor:pointer;text-decoration:none}
.panel .btn.close{margin-left:auto}
.panel .btn.listen{background:var(--accent);border-color:var(--accent);color:#fff}
.panel .busy{color:var(--ink2)}
/* 23 Sep 2026, her pick: "Recipes cards gain the 'Ask yourself' questions, the diagrams, the 'play from this
   moment' buttons and the 'I've done this' ticks, then Workflows forwards to Recipes. Nothing is lost."
   A Doser card's panel draws them the way /workflows/ drew them, in this app's colours. */
.panel .dia{background:var(--bg);border:1px solid var(--line);border-radius:12px;padding:10px}
.panel .dia svg{display:block;width:100%;max-width:520px;height:auto;margin:0 auto}
.dia text{font-family:var(--sans);fill:var(--ink)}
.dia .box{fill:var(--card);stroke:var(--ink2);stroke-opacity:.45;stroke-width:1.5}
.dia .boxm{fill:var(--chip);stroke:var(--doser);stroke-width:1.5}
.dia .ln{stroke:var(--ink2);stroke-width:1.6;fill:none}
.dia .ah{fill:var(--ink2)}
.dia .num{fill:var(--doser);font-weight:800}
.dia .mut{fill:var(--ink2)}
.dia .big{font-weight:800}
.panel .moments{display:flex;flex-wrap:wrap;gap:6px}
.panel .vp{font:600 13px/1 var(--sans);padding:8px 11px;border-radius:999px;border:1px solid var(--line);background:var(--bg);
  color:var(--doser);cursor:pointer;white-space:nowrap}
.panel .tm{font:500 12px/1 ui-monospace,Menlo,Consolas,monospace;padding:3px 6px;border-radius:6px;border:1px solid var(--line);
  background:none;color:var(--doser);cursor:pointer;white-space:nowrap;margin-left:4px;vertical-align:1px}
.panel .check{display:grid;gap:10px}
.panel .qq{display:grid;grid-template-columns:1fr auto;gap:8px;align-items:center;font-size:15px}
@media (max-width:560px){.panel .qq{grid-template-columns:1fr}.panel .yn{justify-self:start}}
html.ts-big .panel .qq{grid-template-columns:1fr}
html.ts-big .panel .yn{justify-self:start}
.panel .yn{display:inline-flex;border:1px solid var(--line);border-radius:9px;overflow:hidden}
.panel .yn button{border:0;background:transparent;color:var(--ink);padding:8px 11px;font:600 13.5px/1 var(--sans);cursor:pointer}
.panel .yn button+button{border-left:1px solid var(--line)}
.panel .yn button[aria-pressed="true"].y{background:var(--doser);color:var(--card)}
.panel .yn button[aria-pressed="true"].n{background:#b8322a;color:#fff}
.panel .yn button[aria-pressed="true"].x{background:var(--ink2);color:var(--card)}
.panel .have{justify-self:start;font:700 12px/1 var(--sans);padding:6px 10px;border-radius:999px;background:var(--chip);color:var(--doser)}
.panel .rule{border-left:3px solid var(--accent);padding-left:10px}
/* 23 Sep 2026, her "then Workflows forwards to Recipes. Nothing is lost.": the page-level features /workflows/ had
   come to the Doser workflows tab, and only to it - the journey map with its green bars, the "Hide what I already
   do", "Only ones he repeats" and fit filters, "Listen to all shown" and "Listen to this stop", a card's other videos
   from the start, and the "already doing" badge on the card itself. Everything here is .dx-, .stop- or .hv-scoped,
   so the other tabs do not change. */
.panel .vbox{border:1px solid var(--line);border-radius:12px;padding:10px 12px;display:grid;gap:8px;min-width:0;background:var(--bg)}
.panel .vhead{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px;color:var(--ink2);font-weight:600}
.panel .vrow{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:4px 10px;align-items:baseline;min-width:0}
.panel .vrow+.vrow{border-top:1px dashed var(--line);padding-top:8px}
.panel .vtitle{min-width:0;overflow-wrap:anywhere;font-size:14px}
.panel .vlen{font-variant-numeric:tabular-nums;color:var(--ink2);font-size:13px}
.panel .vrow .moments{grid-column:1/-1}
.dx{display:grid;gap:10px;margin:2px 0 4px}
.dx[hidden]{display:none}
.dx .map{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 10px 8px;overflow-x:auto}
.dx .map svg{display:block;min-width:900px;width:100%;height:auto}
.dx .map .st{cursor:pointer}
.dx .map .st .box{fill:var(--bg);stroke:var(--line);stroke-width:1.5}
.dx .map .st:hover .box,.dx .map .st:focus .box{stroke:var(--doser);stroke-width:2.5}
.dx .map text{fill:var(--ink);font-family:var(--sans)}
.dx .map .num{font-weight:800;font-size:26px}
.dx .map .nm{font-size:13px;font-weight:600}
.dx .map .sub{fill:var(--ink2);font:10.5px ui-monospace,Menlo,Consolas,monospace}
.dx .map .arr{stroke:var(--ink2);stroke-opacity:.45;stroke-width:2;fill:none}
.dx .map .ah{fill:var(--ink2);fill-opacity:.45}
.dx .map .st .track{fill:var(--line)}
.dx .map .st .done{fill:var(--doser)}
.dx .hint{margin:0 2px;font-size:13px;color:var(--ink2)}
.dx .ctl{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.dx .fchip{border:1px solid var(--line);background:var(--card);color:var(--ink);border-radius:999px;padding:8px 13px;font:600 14px var(--sans);cursor:pointer}
.dx .fchip[aria-pressed="true"]{background:var(--doser);color:var(--card);border-color:var(--doser)}
.dx .voice{display:flex;flex-wrap:wrap;gap:6px;align-items:center}
.dx select{font:600 14px var(--sans);padding:8px 8px;border-radius:10px;border:1px solid var(--line);background:var(--card);color:var(--ink);max-width:190px}
.dbtn{font:700 14px/1 var(--sans);padding:10px 13px;border-radius:10px;border:1px solid var(--doser);background:var(--doser);color:var(--card);cursor:pointer;white-space:nowrap}
.dbtn.ghost{background:transparent;color:var(--doser)}
.dx .player{display:inline-flex;gap:6px}
.dx .player[hidden]{display:none}
.dx .now{font-size:13px;color:var(--ink2);min-height:1em;flex-basis:100%}
.dx .start{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:12px 14px;display:grid;gap:8px}
.dx .start h2{font:600 20px/1.2 var(--serif);margin:0}
.dx .start p{margin:0;color:var(--ink2);font-size:14px}
.dx .startlist{display:flex;flex-wrap:wrap;gap:8px}
.dx .startlist button{font:14px/1.3 var(--sans);text-align:left;background:var(--bg);color:var(--ink);border:1px solid var(--line);border-radius:10px;padding:7px 11px;cursor:pointer}
.dx .startlist span{font:11px ui-monospace,Menlo,Consolas,monospace;color:var(--ink2);text-transform:uppercase;margin-right:6px}
.stop{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:6px 14px;align-items:baseline;justify-content:space-between;
  border-bottom:2px solid var(--ink);padding:16px 2px 6px;scroll-margin-top:150px}
.stop h2{font:600 clamp(20px,5vw,26px)/1.2 var(--serif);margin:0}
.stop .meta{display:flex;flex-wrap:wrap;gap:8px;align-items:center;color:var(--ink2);font-size:13px}
.grid .dxe{grid-column:1/-1;padding:4px 4px 8px;margin:0}
.card .hv{justify-self:start;font:700 12px/1 var(--sans);padding:5px 9px;border-radius:999px;background:var(--chip);color:var(--doser)}
.card .hv.part{color:var(--ink2)}
.card .rp{justify-self:start;font:600 12px/1 var(--sans);padding:4px 8px;border-radius:999px;border:1px solid var(--line);color:var(--ink2)}
.card.reading{outline:3px solid var(--doser);outline-offset:2px}
.chip{justify-self:start;font:700 11px/1 var(--sans);letter-spacing:.04em;text-transform:uppercase;padding:5px 8px;border-radius:6px;background:var(--chip)}
.s-recipes .chip{color:var(--recipes)} .s-hormozi .chip{color:var(--hormozi)} .s-doser .chip{color:var(--doser)} .s-prompts .chip{color:var(--prompts)}
.card .t{font:600 17px/1.3 var(--serif)}
.card .d{font-size:14px;color:var(--ink2)}
.card .l{font-size:12px;color:var(--ink2)}
.empty{color:var(--ink2);padding:24px 4px}
/* 23 Sep 2026, her "then Workflows forwards to Recipes. Nothing is lost.": the Workflows page's own words - her goal
   line and the intro at the front, "How this was made" and the caveats at the foot - on the Doser workflows tab only */
.dxh{display:grid;gap:10px;margin:0 0 16px}
.dxh[hidden],.dxf[hidden]{display:none}
.dxh .label{display:block;margin-bottom:2px;font:11.5px ui-monospace,Menlo,Consolas,monospace;letter-spacing:.08em;text-transform:uppercase;color:var(--ink2)}
.dxh .kick{display:flex;flex-wrap:wrap;gap:6px 16px;align-items:baseline}
.dxh .kick .label{margin:0}
.dxh .dxt{font:600 clamp(26px,6vw,36px)/1.05 var(--serif);margin:0;letter-spacing:-.01em}
.dxh .dxt span{color:var(--doser)}
.dxh .goal{max-width:64ch;color:var(--ink);font-size:19.5px;line-height:1.35;margin:0;font-weight:600}
.dxh .lede{max-width:64ch;color:var(--ink2);font-size:17px;margin:0}
.dxh .lede b{color:var(--ink)}
.dxf{margin:46px 0 70px;padding-top:16px;border-top:1px solid var(--line);font-size:14px;color:var(--ink2);max-width:78ch}
.dxf b{color:var(--ink)}
mark{background:rgba(224,138,78,.28);color:inherit;border-radius:3px}
.coach{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:14px;margin:0 0 16px;display:grid;gap:8px}
.coach label{font:700 13px/1 var(--sans);letter-spacing:.04em;text-transform:uppercase;color:var(--accent)}
.coach .cq{display:flex;gap:8px;align-items:stretch}
.coach textarea{flex:1;min-width:0;font:16px/1.4 var(--sans);padding:10px 12px;border-radius:10px;border:1px solid var(--line);background:var(--bg);color:var(--ink);resize:vertical}
.coach button{font:700 15px/1 var(--sans);padding:0 16px;border-radius:10px;border:0;background:var(--accent);color:#fff;cursor:pointer}
.coach button[disabled]{opacity:.5}
.coach .cnote{font-size:12px;color:var(--ink2);margin:0}
.coach h3{font:700 14px/1.2 var(--sans);margin:12px 0 4px}
.coach ul{margin:0;padding-left:20px}.coach li{margin:4px 0;font-size:15px}
.coach .ev{color:var(--ink2);font-size:13px}
.coach .tom{background:var(--chip);border-radius:10px;padding:10px 12px;font-size:15px}
</style>
<script src="../textsize.js"></script><script src="../feedback.js" defer></script><script src="../pull.js" defer></script><script src="../hearsel.js" defer></script>
</head>
<body>
<div class="wrap">
<header>
  <h1>Recipes</h1>
  <p class="sub" id="sub"></p>
</header>
<div class="search">
  <input id="q" type="search" placeholder="Search every recipe and prompt" autocomplete="off" aria-label="Search every recipe and prompt">
  <div class="tabs" role="group" aria-label="Collections" id="tabs"></div>
</div>
<!-- 20 Sep 2026, her words: "So the terminal of how the goal will be should be at the front." It was the first thing
     on /workflows/ under its title; since 23 Sep that page forwards here, so it is the first thing on the Doser tab
     after that same title, its "Marketing cookbook" label and its counts, as /workflows/ opened. -->
<div class="dxh" id="dxhead" hidden>
  <div class="kick"><span class="label">Marketing cookbook</span>__DXCOUNT__</div>
  <h2 class="dxt">Doser <span>AI Marketing</span> Workflows</h2>
  <p class="goal"><span class="label">Where this ends up</span>A stranger becomes a customer who comes back. Every stop below is one leg of that trip, in the order a buyer meets them.</p>
  <p class="lede">How to do each thing, step by step, starting with what acts on your own listings. Begin at stop 1; the automation stops come last on purpose. <b>His words are shown as he said them</b>, matched to the video captions, with a link to the exact second. Tick <b>Already doing this?</b> and the map shows what's left.</p>
</div>
<section class="coach" aria-label="Ask the coach">
  <label for="cq">Ask the coach</label>
  <div class="cq"><textarea id="cq" rows="2" placeholder="e.g. What do I need to go through to learn Claude Code for my shop?"></textarea>
  <button type="button" id="cgo">Ask</button></div>
  <p class="cnote">Reads your "I've done this" ticks and your Morning &amp; Evening notes from the last 30 days. About 1&ndash;2c a question, capped at US$1 a day.</p>
  <div id="cout" aria-live="polite"></div>
</section>
<div class="dx" id="dx" hidden></div>
<p class="count" id="count" aria-live="polite"></p>
<div class="grid" id="grid"></div>
<footer class="dxf" id="dxfoot" hidden>__DXMADE__<p><b>What is his and what isn't.</b> Words in quotation marks and highlights are his, matched word for word to the captions; the ▶ link opens the video at that second. Captions are machine-made, so a word he said can be misheard in them. Titles, steps, "What it can get you", the diagrams, the check questions and everything about your shop are written by the AI, not his words. A step marked <i>AI step, not his words</i> is not supported by the quote beside it.</p>

<p><b>Private.</b> His words are here for your own learning, not to republish or sell. The read-aloud uses your device's built-in voice, and your Yes/No answers are saved in this browser and copied to your Notion once this device is connected (the Connect to Notion button).</p></footer>
</div>
<script id="hub" type="application/json">__DATA__</script>
<script>
(function(){
  var ALL = JSON.parse(document.getElementById("hub").textContent);
  var TABS = [["all","All"],["recipes","Recipes"],["hormozi","Hormozi"],["doser","Doser workflows"],["prompts","Prompts"]];
  var NAME = {recipes:"Recipe", hormozi:"Hormozi", doser:"Doser", prompts:"Prompt"};
  var cur = "all", q = document.getElementById("q");
  try{ var s = localStorage.getItem("recipesHub.tab"); if(s) cur = s; }catch(e){}
  function esc(s){ return String(s||"").replace(/[&<>"]/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }
  function mark(s, term){ s = esc(s); if(!term) return s;
    var re = new RegExp("(" + term.replace(/[.*+?^${}()|[\\]\\\\]/g, "\\\\$&") + ")", "ig"); return s.replace(re, "<mark>$1</mark>"); }
  function n(src){ return src === "all" ? ALL.length : ALL.filter(function(x){ return x.src === src; }).length; }
  function tabs(){
    document.getElementById("tabs").innerHTML = TABS.map(function(t){
      return '<button type="button" class="tab" data-t="' + t[0] + '" aria-pressed="' + (cur === t[0]) + '">' + t[1] + '<b>' + n(t[0]) + '</b></button>';
    }).join("");
  }
  function draw(){
    var term = q.value.trim(), low = term.toLowerCase();
    var rows = ALL.filter(function(x){
      return (cur === "all" || x.src === cur) && (!low || (x.title + " " + x.desc + " " + x.label).toLowerCase().indexOf(low) >= 0);
    });
    if(cur === "doser") rows = rows.filter(dxShow);   /* 23 Sep 2026: the Doser tab's own filters, on that tab only */
    document.getElementById("count").textContent = rows.length + (rows.length === 1 ? " recipe" : " recipes") + (term ? " match “" + term + "”" : "");
    stop(); shut();   // the rows are about to be thrown away, so nothing is playing or open any more
    SHOWN = rows;
    /* 23 Sep 2026: on the Doser tab the cards sit under their stops, as they did on /workflows/ */
    document.getElementById("grid").innerHTML = cur === "doser" ? dxGrid(rows, term) : rows.length ? rows.map(function(x, i){
      return cardHTML(x, i, term);
    }).join("") : '<p class="empty">Nothing matches. Try fewer words.</p>';
    dxAfter();
  }
  function cardHTML(x, i, term){
      var pic = !x.thumb ? "" : (x.vid
        ? '<button type="button" class="th" data-v="' + esc(x.vid) + '" aria-label="Play the video for ' + esc(x.title) + '"><img src="' + esc(x.thumb) + '" alt="" loading="lazy"></button>'
        : '<div class="th"><img src="' + esc(x.thumb) + '" alt="" loading="lazy"></div>');
      return '<div class="card s-' + x.src + '" data-i="' + i + '">' + pic +
        '<a class="in" href="' + esc(x.href || "#") + '"><span class="chip">' + esc(NAME[x.src]) + (x.label && x.src !== "prompts" ? " · " + esc(x.label) : "") + '</span>' +
        (cur === "doser" ? dxRepeat(x) + dxBadge(x) : "") +
        '<div class="t">' + mark(x.title, term) + '</div>' +
        (x.desc ? '<div class="d">' + mark(x.desc, term) + '</div>' : "") +
        (x.meta ? '<div class="l">' + esc(x.meta) + '</div>' : (x.listen ? '<div class="l">🎙 Natural voice</div>' : "")) + '</a></div>';
  }
  /* 19 Sep, her "there is nothing, no video engraved in it": tapping a card's picture plays the video in
     that picture, the way the recipe pages already play theirs. One at a time - starting another, changing
     tab or searching puts the picture back. The words under it still open the recipe. */
  var NOW = null, SHOWN = [], PANEL = null, DATA = {}, AU = null, AUBTN = null;
  /* 23 Sep 2026, her "i want the recorded good quality read": a card recorded by tools/record_cards.py
     plays its own mp3 - the natural voice, and it keeps going with the phone locked. One voice at a time:
     a video, another card or closing the panel stops it. */
  function hush(){
    if(AU){ AU.pause(); }
    if(AUBTN){ AUBTN.textContent = "\u25B6 Listen"; AUBTN = null; }
  }
  function listen(btn, x){
    if(AUBTN === btn && AU && !AU.paused){ AU.pause(); btn.textContent = "\u25B6 Listen"; return; }
    var src = "a/c/" + x.src + "/" + encodeURIComponent(x.k) + ".mp3";
    if(!AU){ AU = new Audio(); AU.preload = "auto"; AU.addEventListener("ended", hush); }
    if(AUBTN !== btn){ hush(); AU.src = src; }
    AUBTN = btn; stop();
    if(RD.playing && !RD.paused) dxPause();
    btn.textContent = "\u275A\u275A Pause";
    AU.play().catch(function(){ btn.textContent = "Did not play - tap again"; AUBTN = null; });
  }
  function stop(){
    if(!NOW) return;
    if(NOW.isConnected){ NOW.innerHTML = NOW.dataset.pic; NOW.classList.remove("playing"); }
    NOW = null;
  }
  function play(th){
    if(th === NOW) return;
    stop(); hush();
    if(RD.playing && !RD.paused) dxPause();   /* one voice at a time: a video pauses the Doser reader, Resume carries on */
    th.dataset.pic = th.innerHTML;
    th.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + encodeURIComponent(th.dataset.v) +
      '?autoplay=1&playsinline=1&rel=0' + (+th.dataset.s > 0 ? '&start=' + (+th.dataset.s) : '') +
      '" title="Video" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>' +
      '<button type="button" class="x" aria-label="Close the video">✕</button>';
    th.classList.add("playing");
    NOW = th;
  }
  /* 20 Sep, her "I don't want it in a separate links or some sort. I'll want it like in the same app":
     a Hormozi, Doser or Prompt card opens what it actually says HERE, under the card. The ticks, the
     Notion button and the read-aloud lived on the full card in the old app; since 23 Sep there is no link to it.

     20 Sep, her pick on retiring /cookbook/ and /hormozi/: "Not yet - move data first". So this app
     now carries those cards itself, in cards-*.json beside this page, and reads its own copy first.
     23 Sep 2026, her "no links": the fallback fetch from the other app's page, the "Open the full
     card in ..." button and the card links out are all gone. MINE is the only source. */
  var MINE = __LOCAL__;
  function load(src){
    if(!DATA[src]) DATA[src] = fetch(MINE[src]).then(function(r){
      if(!r.ok) throw new Error("no copy of " + src + " here yet");
      return r.json();
    }).catch(function(e){ delete DATA[src]; throw e; });   /* 23 Sep 2026, her "no links": our own copy only, no
       quiet fetch from the old apps any more - and a failed load is forgotten, so tapping again retries */
    return DATA[src];
  }
  function pick(d, x){
    if(x.src === "prompts") return d[+x.k];          /* a list either way: the place in it is the key */
    if(d.topics){                                     /* the other app's blob, still in its own shape */
      var hit = null;
      (d.topics || []).forEach(function(t){ (t.cards || []).forEach(function(c){ if(!hit && c.key === x.k) hit = c; }); });
      return hit;
    }
    return d[x.k];                                    /* our own copy, keyed by the card's own key */
  }
  function pic(id, name){
    return '<button type="button" class="th" data-v="' + esc(id) + '" aria-label="Play ' + esc(name) + '">' +
      '<img src="https://i.ytimg.com/vi/' + esc(id) + '/mqdefault.jpg" alt="" loading="lazy"></button>';
  }
  /* 23 Sep 2026: /workflows/ wrote a video's date as "15 Jun 2025", not "2025-06-15"; the Doser cards keep its words */
  function dmy(s){
    var m = /^(\\d{4})-(\\d{2})-(\\d{2})$/.exec(s || "");
    return m ? +m[3] + " " + ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"][+m[2] - 1] + " " + m[1] : (s || "");
  }
  function shot(id, name, when){
    return '<div>' + pic(id, name) + '<div class="l">' + esc(name) + (when ? " \u00B7 " + esc(when) : "") + '</div></div>';
  }
  /* 23 Sep 2026, her pick: "Recipes cards gain the 'Ask yourself' questions, the diagrams, the 'play from this
     moment' buttons and the 'I've done this' ticks, then Workflows forwards to Recipes. Nothing is lost."
     What follows is /workflows/' own card code, carried over: its answers store, its diagrams and its moments. */
  var CHECKS_KEY = "hmr-checks";   /* the SAME key /workflows/ kept her answers under, so ticks already made carry over */
  function answers(){ try { return JSON.parse(localStorage.getItem(CHECKS_KEY) || "{}") || {}; } catch(e){ return {}; } }
  function haveState(k, c){   /* /workflows/' own test: 'Not for me' answers are left out of the count */
    var a = answers()[k] || {}, n = (c.checks || []).length, idx = [], i;
    if(!n) return "unknown";
    for(i = 0; i < n; i++) if(a[i] !== "x") idx.push(i);
    if(!idx.length) return "na";
    var ys = idx.filter(function(j){ return a[j] === "y"; }).length, ns = idx.filter(function(j){ return a[j] === "n"; }).length;
    if(ys === idx.length) return "have";
    if(ys + ns === 0) return "unknown";
    return "partly";
  }
  function haveText(st){ return st === "have" ? "✓ already doing" : st === "partly" ? "partly doing" : ""; }
  function mmss(t){ t = Math.max(0, Math.round(+t || 0)); var h = Math.floor(t / 3600), m = Math.floor(t % 3600 / 60), s = t % 60;
    return (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(s).padStart(2, "0"); }
  function tbtn(t, what){   /* the ▶ m:ss beside a quote: plays the card's video from that second, here */
    return t == null ? "" : ' <button type="button" class="tm" data-s="' + (+t) + '" aria-label="Play ' + esc(what) + ' from ' + mmss(t) + '">▶ ' + mmss(t) + '</button>';
  }
  function moments(c){   /* /workflows/' "vbox" list: every quoted moment in the card's first video, in time order */
    var first = [], v0 = (c.src || [])[0];
    if(!v0 || !v0.id) return [];
    if(c.claim_t != null) first.push([+c.claim_t, "His words"]);
    (c.steps || []).forEach(function(s, i){ if(s.q && s.t != null) first.push([+s.t, "Step " + (i + 1)]); });
    if(c.warn && c.warn_t != null) first.push([+c.warn_t, "Watch out"]);
    return first.sort(function(a, b){ return a[0] - b[0]; });
  }
  function vbox(c){   /* /workflows/' videos box (video_box.py), in its words and numbers: the listening time, every video
       with its running time and the total, a Start for each, and the first video's moments; they play in the panel */
    var src = (c.src || []).filter(function(v){ return v.id; }), total = 0, mo = moments(c);
    if(!src.length) return "";
    src.forEach(function(v){ total += +v.d || 0; });
    var head = (c.nw ? '<span>🎧 ~' + Math.max(1, Math.round(c.nw / 160)) + ' min listen</span>' : "") +
      '<span>▶ Videos (' + src.length + ')' + (total ? ' · ' + mmss(total) + ' total' : '') + '</span>';
    return '<div class="vbox"><div class="vhead">' + head + '</div>' + src.map(function(v, k){
      var pills = '<button type="button" class="vp" data-v="' + esc(v.id) + '" data-s="0" aria-label="Play from the start">▶ Start</button>';
      if(k === 0) pills += mo.map(function(p){
        return '<button type="button" class="vp" data-v="' + esc(v.id) + '" data-s="' + p[0] + '" aria-label="Play ' + esc(p[1]) + ' at ' + mmss(p[0]) + '">▶ ' + mmss(p[0]) + ' ' + esc(p[1]) + '</button>';
      }).join("");
      return '<div class="vrow"><span class="vtitle">' + esc(v.title || "video") + '</span><span class="vlen">' + (v.d ? mmss(v.d) : "") + '</span><div class="moments">' + pills + '</div></div>';
    }).join("") + '</div>';
  }
  function checksHTML(k, c){
    var a = answers()[k] || {};
    return (c.checks || []).map(function(q, i){
      return '<div class="qq"><span>' + esc(q) + '</span><span class="yn" role="group" aria-label="Answer">' +
        [["y", "Yes"], ["n", "No"], ["x", "Not for me"]].map(function(o){
          return '<button type="button" class="' + o[0] + '" data-i="' + i + '" data-a="' + o[0] + '" aria-pressed="' + (a[i] === o[0]) + '">' + o[1] + '</button>';
        }).join("") + '</span></div>';
    }).join("");
  }
  function tick(b, P){   /* same shape /workflows/ saved: {cardKey: {questionIndex: "y" | "n" | "x"}}; a second tap clears */
    var k = P.row.k, i = b.dataset.i, v = b.dataset.a, all = answers();
    all[k] = all[k] || {};
    all[k][i] = all[k][i] === v ? undefined : v;
    try { localStorage.setItem(CHECKS_KEY, JSON.stringify(all)); } catch(e){}
    var now = all[k][i];
    b.parentNode.querySelectorAll("button").forEach(function(x){ x.setAttribute("aria-pressed", String(x.dataset.a === now)); });
    var hv = P.el.querySelector("[data-have]");
    if(hv && P.card){ var t = haveText(haveState(k, P.card)); hv.textContent = t; hv.hidden = !t; }
    dxRefresh(P);
  }
  function seek(P, id, s){   /* a moment starts the card's video at that second, in the panel's own player */
    var th = P.el.querySelector('.vids .th[data-v="' + id + '"]');
    if(!th) return;
    if(NOW === th) stop();
    th.dataset.s = s;
    play(th);
    th.scrollIntoView({block:"center", behavior:"smooth"});
  }
  var DIAGRAM = (function(){   /* /workflows/' diagram drawer, unchanged but for its colours */
    function wrap(text, max){
      var words = String(text || "").split(/\\s+/), lines = [], cur = "";
      words.forEach(function(w){ if((cur + " " + w).trim().length > max && cur){ lines.push(cur); cur = w; } else cur = (cur + " " + w).trim(); });
      if(cur) lines.push(cur); return lines;
    }
    function tspans(lines, x, y, lh){ return lines.map((l,i)=>`<tspan x="${x}" y="${y + i*lh}">${esc(l)}</tspan>`).join(''); }
    const ARROW = `<defs><marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah" d="M0 0L10 5L0 10z"/></marker></defs>`;
    const DIA = {
      levers(c){
        const it = (c.dia.items||[]).slice(0,8); if (it.length < 2) return DIA.flow(c);
        const W = 440, cols = 2, rows = Math.ceil(it.length/cols), bh = 54, parts = [];
        const H = 70 + rows*(bh+10);
        parts.push(`<rect class="boxm" x="120" y="8" width="200" height="40" rx="20"/><text class="big" x="220" y="33" text-anchor="middle" font-size="14.5">${esc(wrap(c.title.replace(/^How to /i,''),26)[0])}</text>`);
        it.forEach((t,i)=>{ const col = i%cols, row = Math.floor(i/cols); const x = 14 + col*214, y = 64 + row*(bh+10); const ls = wrap(t, 22).slice(0,2);
          parts.push(`<path class="ln" d="M220 48 V56 H${x+100} V${y}" opacity=".45"/>`);
          parts.push(`<rect class="box" x="${x}" y="${y}" width="198" height="${bh}" rx="10"/>`);
          parts.push(`<text x="${x+99}" y="${y + (ls.length>1?23:32)}" text-anchor="middle" font-size="13.5">${ls.map((l,k)=>`<tspan x="${x+99}" dy="${k?16:0}">${esc(l)}</tspan>`).join('')}</text>`); });
        return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Separate options, any order">${parts.join('')}</svg>`;
      },
      flow(c){
        const W = 440, bw = 360, x = 40; let y = 12; const parts = [];
        (c.steps||[]).forEach((s,i)=>{
          const lines = wrap(s.do, 40); const h = 18 + lines.length*18;
          if (i) parts.push(`<path class="ln" marker-end="url(#ah)" d="M${W/2} ${y-14} V${y-2}"/>`);
          parts.push(`<rect class="${i===c.steps.length-1?'boxm':'box'}" x="${x}" y="${y}" width="${bw}" height="${h}" rx="10"/>`);
          parts.push(`<text class="num" x="${x+14}" y="${y+23}" font-size="16">${i+1}</text>`);
          parts.push(`<text x="${x+38}" y="${y+23}" font-size="14.5">${tspans(lines, x+38, y+23, 18)}</text>`);
          y += h + 16;
        });
        return `<svg viewBox="0 0 ${W} ${y}" role="img" aria-label="Flowchart of the steps">${ARROW}${parts.join('')}</svg>`;
      },
      funnel(c){
        const st = (c.dia.stages||[]).slice(0,5); if (st.length < 2) return DIA.flow(c);
        const W = 440, top = 380, bot = 150, h = 58; const parts = [];
        st.forEach((s,i)=>{
          const w1 = top - (top-bot)*i/st.length, w2 = top - (top-bot)*(i+1)/st.length, y = 10 + i*(h+6);
          const x1 = (W-w1)/2, x2 = (W-w2)/2;
          parts.push(`<path class="${i===st.length-1?'boxm':'box'}" d="M${x1} ${y}H${x1+w1}L${x2+w2} ${y+h}H${x2}Z"/>`);
          parts.push(`<text x="${W/2}" y="${y+24}" text-anchor="middle" font-size="15" font-weight="700">${esc(s.label)}</text>`);
          if (s.note) parts.push(`<text class="mut" x="${W/2}" y="${y+43}" text-anchor="middle" font-size="12.5">${esc(wrap(s.note, 34)[0])}</text>`);
        });
        return `<svg viewBox="0 0 ${W} ${10 + st.length*(h+6)}" role="img" aria-label="Funnel">${parts.join('')}</svg>`;
      },
      equation(c){
        const top = (c.dia.top||[]).slice(0,4), bottom = (c.dia.bottom||[]).slice(0,4);
        if (!top.length) return DIA.flow(c);
        const W = 440, parts = []; const result = c.dia.result || '';
        const rows = (arr, y, cls) => { const n = arr.length, cw = 300/n;
          arr.forEach((t,i)=>{ const cx = 130 + cw*i + cw/2; const ls = wrap(t, 14).slice(0,2);
            parts.push(`<rect class="${cls}" x="${cx-cw/2+4}" y="${y}" width="${cw-8}" height="52" rx="9"/>`);
            parts.push(`<text x="${cx}" y="${y + (ls.length>1?22:31)}" text-anchor="middle" font-size="13.5">${ls.map((l,k)=>`<tspan x="${cx}" dy="${k?16:0}">${esc(l)}</tspan>`).join('')}</text>`);
            if (i) parts.push(`<text class="mut big" x="${130 + cw*i}" y="${y+33}" text-anchor="middle" font-size="16">×</text>`);
          }); };
        rows(top, 14, 'boxm');
        parts.push(`<line class="ln" x1="130" x2="430" y1="80" y2="80" stroke-width="2.5"/>`);
        if (bottom.length) rows(bottom, 90, 'box');
        const rl = wrap(result, 12).slice(0,3);
        parts.push(`<text class="big" x="62" y="${78 - (rl.length-1)*9}" text-anchor="middle" font-size="16">${rl.map((l,k)=>`<tspan x="62" dy="${k?18:0}">${esc(l)}</tspan>`).join('')}</text>`);
        parts.push(`<text class="big" x="118" y="86" text-anchor="middle" font-size="22">=</text>`);
        return `<svg viewBox="0 0 ${W} ${bottom.length?152:96}" role="img" aria-label="Equation: ${esc(result)}">${parts.join('')}</svg>`;
      },
      matrix(c){
        const m = c.dia, cells = m.cells||{}; if (!cells.tl && !cells.br) return DIA.flow(c);
        const W = 440, x0 = 60, y0 = 10, s = 170; const parts = [];
        const cell = (k, x, y, hi) => { const ls = wrap(cells[k]||'', 20).slice(0,3);
          parts.push(`<rect class="${hi?'boxm':'box'}" x="${x}" y="${y}" width="${s-6}" height="${s-6}" rx="10"/>`);
          parts.push(`<text x="${x+(s-6)/2}" y="${y+(s-6)/2 - (ls.length-1)*9 + 5}" text-anchor="middle" font-size="14">${ls.map((l,k2)=>`<tspan x="${x+(s-6)/2}" dy="${k2?18:0}">${esc(l)}</tspan>`).join('')}</text>`); };
        cell('tl', x0, y0); cell('tr', x0+s, y0, true); cell('bl', x0, y0+s); cell('br', x0+s, y0+s);
        parts.push(`<path class="ln" marker-end="url(#ah)" d="M${x0-12} ${y0+2*s} V${y0+4}"/><path class="ln" marker-end="url(#ah)" d="M${x0} ${y0+2*s+10} H${x0+2*s}"/>`);
        parts.push(`<text class="mut" x="${x0+s}" y="${y0+2*s+30}" text-anchor="middle" font-size="13">${esc(m.x||'')} →</text>`);
        parts.push(`<text class="mut" transform="translate(${x0-24} ${y0+s}) rotate(-90)" text-anchor="middle" font-size="13">${esc(m.y||'')} →</text>`);
        return `<svg viewBox="0 0 ${W} ${y0+2*s+40}" role="img" aria-label="Two by two grid">${ARROW}${parts.join('')}</svg>`;
      },
      cycle(c){
        const n0 = (c.dia.nodes||[]).slice(0,6); if (n0.length < 3) return DIA.flow(c);
        const W = 440, H = 330, cx = 220, cy = 165, r = 118, parts = [];
        const pts = n0.map((_,i)=>{ const a = -Math.PI/2 + i*2*Math.PI/n0.length; return [cx + r*Math.cos(a), cy + r*Math.sin(a)]; });
        pts.forEach((p,i)=>{ const q = pts[(i+1)%pts.length]; const mx = (p[0]+q[0])/2, my = (p[1]+q[1])/2;
          const ox = (mx-cx)*0.35, oy = (my-cy)*0.35;
          const sx = p[0] + (q[0]-p[0])*0.28, sy = p[1] + (q[1]-p[1])*0.28, ex = p[0] + (q[0]-p[0])*0.72, ey = p[1] + (q[1]-p[1])*0.72;
          parts.push(`<path class="ln" marker-end="url(#ah)" d="M${sx} ${sy} Q${mx+ox} ${my+oy} ${ex} ${ey}"/>`); });
        n0.forEach((t,i)=>{ const [x,y] = pts[i]; const ls = wrap(t, 14).slice(0,2);
          parts.push(`<rect class="${i===0?'boxm':'box'}" x="${x-62}" y="${y-24}" width="124" height="48" rx="24"/>`);
          parts.push(`<text x="${x}" y="${y + (ls.length>1?-3:5)}" text-anchor="middle" font-size="13">${ls.map((l,k)=>`<tspan x="${x}" dy="${k?16:0}">${esc(l)}</tspan>`).join('')}</text>`); });
        return `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Loop">${ARROW}${parts.join('')}</svg>`;
      },
      ladder(c){
        const r0 = (c.dia.rungs||[]).slice(0,6); if (r0.length < 2) return DIA.flow(c);
        const W = 440, stepH = 46, n = r0.length, parts = [];
        r0.forEach((t,i)=>{ const x = 20 + i*(260/Math.max(1,n-1)); const y = 10 + (n-1-i)*(stepH+6);
          parts.push(`<rect class="${i===n-1?'boxm':'box'}" x="${x}" y="${y}" width="${W-20-x}" height="${stepH}" rx="9"/>`);
          parts.push(`<text class="num" x="${x+14}" y="${y+29}" font-size="15">${i+1}</text>`);
          parts.push(`<text x="${x+36}" y="${y+29}" font-size="14">${esc(wrap(t, Math.max(14, Math.floor((W-60-x)/7.6)))[0])}</text>`); });
        return `<svg viewBox="0 0 ${W} ${10 + n*(stepH+6)}" role="img" aria-label="Levels, lowest first">${parts.join('')}</svg>`;
      },
      compare(c){
        const rows = (c.dia.rows||[]).slice(0,5); if (!rows.length) return DIA.flow(c);
        const W = 440, rh = 50, parts = [];
        parts.push(`<rect class="box" x="10" y="8" width="206" height="34" rx="8"/><rect class="boxm" x="224" y="8" width="206" height="34" rx="8"/>`);
        parts.push(`<text x="113" y="30" text-anchor="middle" font-size="14" font-weight="700">${esc(c.dia.left||'')}</text><text x="327" y="30" text-anchor="middle" font-size="14" font-weight="700">${esc(c.dia.right||'')}</text>`);
        rows.forEach((r,i)=>{ const y = 50 + i*rh;
          [0,1].forEach(k=>{ const x = k? 327 : 113; const ls = wrap(r[k]||'', 26).slice(0,2);
            parts.push(`<text x="${x}" y="${y+ (ls.length>1?18:26)}" text-anchor="middle" font-size="13.5">${ls.map((l,j)=>`<tspan x="${x}" dy="${j?16:0}">${esc(l)}</tspan>`).join('')}</text>`); });
          parts.push(`<line class="ln" x1="10" x2="430" y1="${y+rh-4}" y2="${y+rh-4}" stroke-width="1" opacity=".35"/>`); });
        return `<svg viewBox="0 0 ${W} ${54 + rows.length*rh}" role="img" aria-label="Side by side">${parts.join('')}</svg>`;
      }
    };
    return function(card){ const f = DIA[(card.dia||{}).type] || DIA.flow; try { return f(card); } catch(e){ return DIA.flow(card); } };
  })();
  /* 23 Sep 2026, her "then Workflows forwards to Recipes. Nothing is lost.": /workflows/' page-level features,
     carried over for the Doser workflows tab only, from its own code - the journey map (drawMap), the filters
     (visibleCards), the stop headings with "Listen to this stop" (render), "Start here" (drawStart) and the
     natural-voice reader behind "Listen to all shown" (speakCards). Its saved keys are kept as they were:
     hmr-checks (her answers), hmr-rate (speed), speak.nvoice (voice) and hmr-last (the card she last heard). */
  var DXFIT = ALL.some(function(x){ return x.src === "doser" && x.fit; });   /* /workflows/' has_fit: false on 23 Sep, so the fit menu stays hidden, as it was there */
  var dxHide = false, dxRep = false, dxFitMode = DXFIT ? "fits" : "all", DXB = false;
  var RD = {list: [], idx: 0, lines: [], playing: false, paused: false, wake: null};
  function dxState(x){ return haveState(x.k, {checks: {length: +x.nq || 0}}); }
  function dxFits(x){ return !DXFIT || x.fit === "now" || x.fit === "adapt"; }
  function dxShow(x){   /* /workflows/' visibleCards, less the words, which this page's own search box already does */
    if(dxHide && dxState(x) === "have") return false;
    if(dxRep && (+x.ns || 0) < 2) return false;
    if(dxFitMode === "fits" && !dxFits(x)) return false;
    if(dxFitMode === "start" && !x.st) return false;
    if(dxFitMode === "later" && x.fit !== "later") return false;
    if(dxFitMode === "no" && x.fit !== "no") return false;
    return true;
  }
  function dxTopics(){   /* the stops, in the order the source lists them - the cards arrive in that order */
    var out = [], at = {};
    ALL.forEach(function(x){
      if(x.src !== "doser") return;
      if(!(x.label in at)){ at[x.label] = out.length; out.push({name: x.label, items: []}); }
      out[at[x.label]].items.push(x);
    });
    return out;
  }
  function dxRepeat(x){   /* /workflows/' badge beside the stop name, in its words and with its caution */
    var n = +x.ns || 0;
    return n ? '<span class="rp" title="How often it comes up in his videos, not proof it works">repeated in ' + n + ' video' + (n > 1 ? 's' : '') + '</span>' : "";
  }
  function dxBadge(x){
    if(!x.nq) return "";
    var st = dxState(x);
    return st === "have" ? '<span class="hv">✓ already doing</span>' : st === "partly" ? '<span class="hv part">partly doing</span>' : "";
  }
  function dxMeta(t){ return t.items.filter(function(x){ return dxFits(x) && dxState(x) === "have"; }).length + " already doing"; }
  function dxGrid(rows, term){
    return dxTopics().map(function(t, ti){
      var vis = rows.filter(function(x){ return x.label === t.name; });
      return '<div class="stop" id="stop-' + ti + '"><h2>' + (ti + 1) + '. ' + esc(t.name) + '</h2><span class="meta"><span>' + vis.length + ' of ' + t.items.length +
        ' shown · <span data-sh="' + ti + '">' + dxMeta(t) + '</span></span><button type="button" class="dbtn ghost playtopic" data-t="' + ti + '">▶ Listen to this stop</button></span></div>' +
        (vis.length ? vis.map(function(x){ return cardHTML(x, SHOWN.indexOf(x), term); }).join("") : '<p class="dxe empty">Nothing here matches.</p>');
    }).join("");
  }
  function dxMap(){   /* /workflows/' drawMap: one box per stop, how many it holds, and a green bar for the ones she already does */
    const T = dxTopics(), n = T.length, W = 1120, H = 150, gap = W/n, parts = [];
    T.forEach((t,i)=>{
      const x = i*gap + 8, w = gap - 30, y = 20;
      const fit = t.items.filter(dxFits), total = fit.length, have = fit.filter(c=>dxState(c)==='have').length;
      if (i < n-1) parts.push(`<path class="arr" d="M${x+w+2} ${y+52} H${x+gap-6}"/><path class="ah" d="M${x+gap-6} ${y+46} L${x+gap+2} ${y+52} L${x+gap-6} ${y+58}z"/>`);
      const frac = total ? have/total : 0, bw = w-24;
      parts.push(`<g class="st" tabindex="0" role="link" data-go="${i}" aria-label="${esc(t.name)}: ${total} recipes for your shop now, ${have} already doing">
        <rect class="box" x="${x}" y="${y}" width="${w}" height="104" rx="12"/>
        <text class="sub" x="${x+12}" y="${y+18}">STOP ${i+1}</text>
        <text class="num" x="${x+12}" y="${y+50}">${total}</text>
        <text class="nm" x="${x+12}" y="${y+72}">${esc(t.name.replace(' & referrals',''))}</text>
        <rect class="track" x="${x+12}" y="${y+84}" width="${bw}" height="6" rx="3"/>
        <rect class="done" x="${x+12}" y="${y+84}" width="${Math.max(0,bw*frac)}" height="6" rx="3"/>
      </g>`);
    });
    parts.push(`<text class="sub" x="8" y="12">STRANGER</text><text class="sub" x="${W-8}" y="12" text-anchor="end">CUSTOMER WHO COMES BACK</text>`);
    document.getElementById("dxmap").innerHTML = `<svg viewBox="0 0 ${W} ${H}">${parts.join('')}</svg>`;
  }
  function dxStart(){   /* /workflows/' drawStart: only when the source marks what fits her shop, which it does not on 23 Sep */
    var el = document.getElementById("dxstart"), picks = DXFIT ? ALL.filter(function(x){ return x.src === "doser" && x.st; }) : [];
    el.innerHTML = !picks.length ? "" : '<section class="start" aria-labelledby="dxsh"><p class="hint">For a shop with no sales yet</p><h2 id="dxsh">Start here: ' + picks.length +
      ' recipes</h2><p>The ones most likely to bring your first buyers, in customer order. Tap one to open it.</p><div class="startlist">' +
      picks.map(function(x){ return '<button type="button" data-k="' + esc(x.k) + '"><span>' + esc(x.label.replace(" & referrals", "")) + '</span>' + esc(x.title) + '</button>'; }).join("") + '</div></section>';
  }
  function dxOpen(k){
    var x = ALL.filter(function(r){ return r.src === "doser" && String(r.k) === k; })[0], i = SHOWN.indexOf(x);
    var card = i >= 0 ? document.querySelector('.card[data-i="' + i + '"]') : null;
    if(!card) return;
    card.scrollIntoView({block:"start"});
    if(!(PANEL && PANEL.row === x)) show(card, x);
  }
  function dxGo(i){ var h = document.getElementById("stop-" + i); if(h) h.scrollIntoView({behavior:"smooth", block:"start"}); }
  var NVOICES = [["aoede","Aoede"],["achernar","Achernar"],["kore","Kore"],["charon","Charon"],["puck","Puck"]];
  function dxBuild(){
    if(DXB) return;
    DXB = true;
    var rates = ["0.9","1","1.15","1.3","1.5","1.75","2","2.5","3"], rate = "1.5", nv = nvVoice();   /* 1.5x to start, her 15 Sep ask */
    try { var v = localStorage.getItem("hmr-rate"); if(v && rates.indexOf(v) >= 0) rate = v; } catch(e){}
    var fits = [["fits","For my shop now"],["start","Start here"],["later","Later, once I have sales"],["no","Not for my shop"],["all","All recipes"]];
    var dx = document.getElementById("dx");
    dx.innerHTML = '<div class="map" id="dxmap" role="navigation" aria-label="Stops in customer order"></div>' +
      '<p class="hint">Green bar: recipes you&#39;ve marked as already doing. Tap a stop to jump to it.</p>' +
      '<div id="dxstart"></div>' +
      '<div class="ctl">' +
        '<select id="dxfit" aria-label="Which recipes to show"' + (DXFIT ? "" : " hidden") + '>' + fits.map(function(f){
          return '<option value="' + f[0] + '"' + (f[0] === dxFitMode ? " selected" : "") + '>' + f[1] + '</option>'; }).join("") + '</select>' +
        '<button type="button" class="fchip" id="dxrep" aria-pressed="false">Only ones he repeats</button>' +
        '<button type="button" class="fchip" id="dxtodo" aria-pressed="false">Hide what I already do</button>' +
        '<span class="voice"><button type="button" class="dbtn" id="dxall">▶ Listen to all shown</button>' +
          '<span class="player" id="dxplayer" hidden><button type="button" class="dbtn ghost" id="dxprev" aria-label="Previous recipe">⏮</button>' +
          '<button type="button" class="dbtn ghost" id="dxpause">Pause</button><button type="button" class="dbtn ghost" id="dxnext" aria-label="Next recipe">⏭</button>' +
          '<button type="button" class="dbtn ghost" id="dxstop">Stop</button></span>' +
          '<select id="dxvoice" aria-label="Voice">' + NVOICES.map(function(o){ return '<option value="' + o[0] + '"' + (o[0] === nv ? " selected" : "") + '>' + o[1] + ' (natural)</option>'; }).join("") + '</select>' +
          '<select id="dxrate" aria-label="Speed">' + rates.map(function(r){ return '<option value="' + r + '"' + (r === rate ? " selected" : "") + '>' + r + '×</option>'; }).join("") + '</select></span>' +
        '<div class="now" id="dxnow" aria-live="polite"></div>' +
      '</div>';
    dx.addEventListener("click", function(e){
      var g = e.target.closest(".st"); if(g){ dxGo(+g.dataset.go); return; }
      var sb = e.target.closest(".startlist button"); if(sb){ dxOpen(sb.dataset.k); return; }
      var b = e.target.closest("button"); if(!b) return;
      if(b.id === "dxrep"){ dxRep = !dxRep; b.setAttribute("aria-pressed", String(dxRep)); draw(); }
      else if(b.id === "dxtodo"){ dxHide = !dxHide; b.setAttribute("aria-pressed", String(dxHide)); draw(); }
      else if(b.id === "dxall") dxSpeak(SHOWN.slice(), true);
      else if(b.id === "dxstop") dxStopAll();
      else if(b.id === "dxpause") dxPause();
      else if((b.id === "dxnext" || b.id === "dxprev") && RD.playing){
        nvStop(); RD.paused = false; document.getElementById("dxpause").textContent = "Pause";
        dxCard(b.id === "dxnext" ? RD.idx + 1 : Math.max(0, RD.idx - 1));
      }
    });
    dx.addEventListener("keydown", function(e){
      var g = e.target.closest && e.target.closest(".st");
      if(g && (e.key === "Enter" || e.key === " ")){ e.preventDefault(); dxGo(+g.dataset.go); }
    });
    dx.addEventListener("change", function(e){
      if(e.target.id === "dxfit"){ dxFitMode = e.target.value; draw(); }
      else if(e.target.id === "dxvoice"){ try { localStorage.setItem("speak.nvoice", e.target.value); } catch(err){} }
      else if(e.target.id === "dxrate"){ try { localStorage.setItem("hmr-rate", e.target.value); } catch(err){} }
    });
  }
  function dxAfter(){   /* after every draw: the Doser block shows on the Doser tab only, and leaving the tab stops the reader */
    var dx = document.getElementById("dx");
    document.getElementById("dxhead").hidden = document.getElementById("dxfoot").hidden = cur !== "doser";
    if(cur !== "doser"){ dx.hidden = true; if(RD.playing) dxStopAll(); return; }
    dxBuild(); dx.hidden = false; dxMap(); dxStart(); dxMark(false);
  }
  function dxRefresh(P){   /* a Yes / No / Not for me in an open card updates its badge, the map and the stop counts at once */
    if(cur !== "doser" || !P || P.row.src !== "doser") return;
    var cardEl = P.el.previousElementSibling, inn = cardEl && cardEl.querySelector("a.in");
    if(inn){
      var old = inn.querySelector(".hv"); if(old) old.parentNode.removeChild(old);
      var h = dxBadge(P.row); if(h) (inn.querySelector(".rp") || inn.querySelector(".chip")).insertAdjacentHTML("afterend", h);
    }
    dxMap();
    dxTopics().forEach(function(t, ti){ var s = document.querySelector('[data-sh="' + ti + '"]'); if(s) s.textContent = dxMeta(t); });
  }
  /* the reader: /workflows/' natural-voice card player, unchanged but for where it finds the cards */
  var NV_URL = "https://apps-notion-relay.apps-notion-relay.workers.dev/tts";
  var nvAudio = null, nvToken = 0, nvCache = {};
  function nvPass(){ try { var raw = localStorage.getItem("notionSync.pass"); if(!raw) return null;
    try { var p = JSON.parse(raw); if(typeof p === "string" && p) return p; } catch(e){}
    return raw[0] !== "{" && raw[0] !== "[" ? raw : null; } catch(e){ return null; } }
  function nvVoice(){ try { return localStorage.getItem("speak.nvoice") || "aoede"; } catch(e){ return "aoede"; } }
  function nvClip(text){
    var k = nvVoice() + "|" + text; if(nvCache[k]) return nvCache[k];
    var pw = nvPass();
    if(!pw) return Promise.reject(new Error("The natural voice needs this device connected once - tap Connect to Notion."));
    var pr = fetch(NV_URL, {method:"POST", headers:{"Content-Type":"application/json", "X-Pass": pw}, body: JSON.stringify({text: text, voice: nvVoice()})})
      .then(function(r){ return r.ok ? r.blob() : r.json().catch(function(){ return {}; }).then(function(j){ throw new Error(j.error || "The natural voice could not be reached just now."); }); })
      .then(function(b){ return URL.createObjectURL(b); });
    pr.catch(function(){ delete nvCache[k]; }); nvCache[k] = pr; return pr;
  }
  function nvStop(){ nvToken++; try { if(nvAudio){ nvAudio.onended = null; nvAudio.pause(); } } catch(e){} try { window.speechSynthesis && speechSynthesis.cancel(); } catch(e){} }
  function nvTake(){   /* the next lines of this card, joined up to 1,400 characters */
    var t = ""; while(RD.lines.length && (t + " " + RD.lines[0]).length <= 1400) t += (t ? " " : "") + RD.lines.shift();
    if(!t && RD.lines.length) t = RD.lines.shift().slice(0, 1400);
    return t;
  }
  function scriptFor(c){   /* what a card says aloud - "Ask yourself" and its questions come last, as on /workflows/ */
    var parts = [c.title + ".", "What it can get you: " + c.gets];
    if(c.fit === "no") parts.push("Not for your shop. " + c.why);
    else if(c.fit === "later") parts.push("Later, once you have sales. " + c.why);
    if(c.shop) parts.push("For your Etsy shop: " + c.shop);
    if(c.watch) parts.push("Watch for: " + c.watch);
    if(c.rule) parts.push("Rules: " + c.rule);
    parts.push("In his words: " + c.claim + ".", "How to do it.");
    (c.steps || []).forEach(function(s, i){ parts.push("Step " + (i + 1) + ". " + s.do); });
    if(c.warn) parts.push("Watch out. In his words: " + c.warn + ".");
    if((c.checks || []).length) parts.push("Ask yourself. " + c.checks.join(" "));
    return parts;
  }
  function dxWake(on){
    try {
      if(on && "wakeLock" in navigator && !RD.wake){ navigator.wakeLock.request("screen").then(function(w){ RD.wake = w; w.addEventListener("release", function(){ RD.wake = null; }); }).catch(function(){}); }
      if(!on && RD.wake){ RD.wake.release(); RD.wake = null; }
    } catch(e){}
  }
  document.addEventListener("visibilitychange", function(){ if(RD.playing && document.visibilityState === "visible") dxWake(true); });
  function dxSpeak(items, askResume){
    if(!items.length) return;
    var now = document.getElementById("dxnow");
    load("doser").then(function(d){
      var list = items.map(function(x){ return {x: x, c: pick(d, x)}; }).filter(function(p){ return p.c; });
      if(!list.length) return;
      var at = 0;
      if(askResume){
        var last = ""; try { last = localStorage.getItem("hmr-last") || ""; } catch(e){}
        var j = list.findIndex(function(p){ return p.x.k === last; });
        if(j > 0 && confirm("Carry on from the recipe you last listened to?")) at = j;
      }
      stop(); hush(); nvStop();
      RD.list = list; RD.playing = true; RD.paused = false;
      document.getElementById("dxplayer").hidden = false; document.getElementById("dxpause").textContent = "Pause";
      dxWake(true); dxCard(at);
    }).catch(function(){ now.textContent = "The workflows did not load. Check the connection and tap again."; });
  }
  function dxCard(i){
    RD.idx = i; var p = RD.list[i]; if(!p){ dxStopAll(); return; }
    RD.lines = ["Recipe " + (i + 1) + " of " + RD.list.length + ". " + (p.x.label ? p.x.label + "." : "")].concat(scriptFor(p.c));
    try { localStorage.setItem("hmr-last", p.x.k); } catch(e){}
    dxMark(true);
    document.getElementById("dxnow").textContent = "Reading " + (i + 1) + " of " + RD.list.length + ": " + p.c.title;
    dxLine();
  }
  function dxMark(scroll){   /* the card being read is outlined, and brought into view */
    document.querySelectorAll(".card.reading").forEach(function(el){ el.classList.remove("reading"); });
    var p = RD.playing && RD.list[RD.idx]; if(!p) return;
    var i = SHOWN.indexOf(p.x), el = i >= 0 ? document.querySelector('.card[data-i="' + i + '"]') : null;
    if(!el) return;
    el.classList.add("reading");
    var r = el.getBoundingClientRect();
    if(scroll && !(r.top >= 0 && r.top < innerHeight * 0.6)) el.scrollIntoView({behavior:"smooth", block:"center"});
  }
  function dxLine(){
    if(!RD.playing || RD.paused) return;
    if(!RD.lines.length){ dxCard(RD.idx + 1); return; }
    var text = nvTake(), tok = ++nvToken;
    nvClip(text).then(function(url){
      if(tok !== nvToken || !RD.playing || RD.paused) return;
      if(!nvAudio){ nvAudio = new Audio(); nvAudio.setAttribute("playsinline", ""); }
      nvAudio.src = url; nvAudio.playbackRate = +document.getElementById("dxrate").value || 1;
      nvAudio.onended = function(){ if(tok === nvToken) dxLine(); };
      nvAudio.play().catch(function(){ if(tok !== nvToken) return; RD.paused = true; document.getElementById("dxpause").textContent = "Resume"; document.getElementById("dxnow").textContent = "Tap Resume to start reading."; });
      var ahead = RD.lines.slice(0), nx = ""; while(ahead.length && (nx + " " + ahead[0]).length <= 1400) nx += (nx ? " " : "") + ahead.shift();
      if(nx) nvClip(nx).catch(function(){});
    }, function(e){ if(tok !== nvToken) return; dxStopAll(); document.getElementById("dxnow").textContent = e.message; });
  }
  function dxPause(){
    if(!RD.playing) return;
    var b = document.getElementById("dxpause");
    if(!RD.paused){ RD.paused = true; nvStop(); RD.lines.unshift("Recipe " + (RD.idx + 1) + "."); b.textContent = "Resume"; }
    else { RD.paused = false; b.textContent = "Pause"; dxCard(RD.idx); }
  }
  function dxStopAll(){
    RD.playing = false; RD.paused = false; RD.lines = []; nvStop(); dxWake(false);
    var pl = document.getElementById("dxplayer"); if(pl) pl.hidden = true;
    var nw = document.getElementById("dxnow"); if(nw) nw.textContent = "";
    document.querySelectorAll(".card.reading").forEach(function(el){ el.classList.remove("reading"); });
  }
  function body(x, c){
    var foot = '<div class="row"><button type="button" class="btn close">Close</button></div>';
    var lis = x.a ? '<div class="row"><button type="button" class="btn listen">\u25B6 Listen</button></div>' : "";
    if(x.src === "prompts"){
      var seen = {}, films = (c.src || []).map(function(v){
        var id = (String(v.u || "").match(/[?&]v=([A-Za-z0-9_-]{11})/) || [])[1];
        if(!id || seen[id]) return ""; seen[id] = 1;
        return shot(id, (v.v || "video").slice(0, 70), v.y || "");
      }).join("");
      return '<h2>' + esc(c.n) + '</h2>' + lis +
        '<div><span class="label">The prompt, word for word</span><pre>' + esc(c.p) + '</pre></div>' +
        '<div class="row"><button type="button" class="btn copy">Copy</button>' +
        (c.t || []).map(function(t){ return '<span class="chip">' + esc(t) + '</span>'; }).join("") + '</div>' +
        (films ? '<div><span class="label">Where she said it</span><div class="vids">' + films + '</div></div>' : "") + foot;
    }
    var steps = (c.steps || []).map(function(v, i){
      /* Both source pages mark which steps are his words and which the AI wrote, and a step must not
         lose that mark by being read here. The wording is theirs. Measured 20 Sep over all 1,731 steps:
         this one test reproduces both pages exactly - on Hormozi every quote-less step is already
         sup "none" or "no", and on Doser sup is always empty so the missing quote is the whole test. */
      var sup = (v.sup === "no" || v.sup === "none" || !v.q)
        ? ' <span class="ai" title="Written by the AI; his words here do not say this">AI step, not his words</span>'
        : v.sup === "partly"
          ? ' <span class="ai" title="Goes a little beyond what he says">loosely from his words</span>' : "";
      return '<li>' + esc(v.do) + sup + (v.q ? '<span class="sq"><q>' + esc(v.q) + '</q>' + tbtn(v.t, "step " + (i + 1)) + '</span>' : "") + '</li>';
    }).join("");
    var vids = (c.src || []).map(function(v){ return shot(v.id, v.title || "video", x.src === "doser" ? dmy(v.date) : (v.date || "")); }).join("");
    /* 23 Sep 2026: the Doser card's own features from /workflows/ - a card without them draws as before */
    var have = c.checks && c.checks.length ? haveText(haveState(x.k, c)) : null;
    var box = x.src === "doser" ? vbox(c) : "";
    return '<h2>' + esc(c.title) + '</h2>' +
      (have === null ? "" : '<span class="have" data-have' + (have ? "" : " hidden") + '>' + esc(have) + '</span>') + lis +
      (c.gets ? '<p><b>What it can get you:</b> ' + esc(c.gets) + '</p>' : "") +
      (c.prereq ? '<p><b>First:</b> ' + esc(c.prereq) + '</p>' : "") +
      (c.rule ? '<div class="rule"><span class="label">Rules</span><p>' + esc(c.rule) + '</p></div>' : "") +
      (c.claim ? '<div><span class="label">His words</span><p><q>' + esc(c.claim) + '</q>' + tbtn(c.claim_t, "his words") + '</p></div>' : "") +
      (steps ? '<div><span class="label">How to do it</span><ol>' + steps + '</ol></div>' : "") +
      (c.warn ? '<div><span class="label">Watch out</span><p><q>' + esc(c.warn) + '</q>' + tbtn(c.warn_t, "watch out") + '</p></div>' : "") +
      (c.dia ? '<div><span class="label">At a glance</span><div class="dia">' + DIAGRAM(c) + '</div></div>' : "") +
      (c.checks && c.checks.length ? '<div><span class="label">Ask yourself: already doing this?</span><div class="check">' + checksHTML(x.k, c) + '</div></div>' : "") +
      (box ? '<div><span class="label">Play from this moment</span>' + box + '</div>' : "") +
      (vids ? '<div><span class="label">From</span><div class="vids">' + vids + '</div></div>' : "") + foot;
  }
  function shut(){
    if(!PANEL) return;
    if(NOW && PANEL.el.contains(NOW)) stop();   // the player is about to be thrown away with the panel
    hush();
    if(PANEL.el.parentNode) PANEL.el.parentNode.removeChild(PANEL.el);
    PANEL = null;
  }
  function show(card, x){
    var again = PANEL && PANEL.row === x;
    shut();
    if(again) return;   // a second tap on the same card closes it
    var el = document.createElement("div");
    el.className = "panel";
    el.innerHTML = '<p class="busy">Opening\u2026</p>';
    card.parentNode.insertBefore(el, card.nextSibling);
    PANEL = {el: el, row: x};
    load(x.src).then(function(d){
      if(!PANEL || PANEL.el !== el) return;
      var c = pick(d, x);
      if(!c) throw new Error("no card " + x.k + " in " + x.src);
      PANEL.card = c;
      el.innerHTML = body(x, c);
      var top = el.getBoundingClientRect().top;
      if(top < 0 || top > window.innerHeight - 140) el.scrollIntoView({block:"center"});
    }).catch(function(){ if(PANEL && PANEL.el === el) el.innerHTML = '<p class="busy">This card did not open. Check the connection and tap it again.</p>'; });
  }
  document.getElementById("grid").addEventListener("click", function(e){
    if(e.target.closest(".th .x")){ stop(); return; }
    var pt = e.target.closest(".stop .playtopic");   /* "Listen to this stop": the cards of that stop now showing */
    if(pt){ var tp = dxTopics()[+pt.dataset.t]; if(tp) dxSpeak(tp.items.filter(function(x){ return SHOWN.indexOf(x) >= 0; }), false); return; }
    var th = e.target.closest("button.th[data-v]");
    if(th && !th.classList.contains("playing")){ delete th.dataset.s; play(th); return; }
    var mo = e.target.closest(".panel .vp, .panel .tm");
    if(mo){ if(PANEL && PANEL.card && PANEL.card.src && PANEL.card.src[0]) seek(PANEL, mo.dataset.v || PANEL.card.src[0].id, +mo.dataset.s || 0); return; }
    var yn = e.target.closest(".panel .yn button");
    if(yn){ if(PANEL && PANEL.card) tick(yn, PANEL); return; }
    if(e.target.closest(".panel .close")){ shut(); return; }
    var lb = e.target.closest(".panel .listen");
    if(lb){ if(PANEL) listen(lb, PANEL.row); return; }
    var cp = e.target.closest(".panel .copy");
    if(cp){
      var pre = cp.closest(".panel").querySelector("pre");
      if(pre && navigator.clipboard) navigator.clipboard.writeText(pre.textContent).then(function(){
        cp.textContent = "Copied"; setTimeout(function(){ cp.textContent = "Copy"; }, 1500);
      });
      return;
    }
    var a = e.target.closest("a.in");
    if(!a || e.metaKey || e.ctrlKey || e.shiftKey || e.button) return;
    var card = a.closest(".card"), row = card && SHOWN[+card.dataset.i];
    if(row && row.src !== "recipes" && row.k !== "" && row.k != null){ e.preventDefault(); show(card, row); }
  });
  document.addEventListener("keydown", function(e){ if(e.key === "Escape") shut(); });
  document.getElementById("tabs").addEventListener("click", function(e){
    var b = e.target.closest(".tab"); if(!b) return;
    cur = b.dataset.t; try{ localStorage.setItem("recipesHub.tab", cur); }catch(err){}
    tabs(); draw();
  });
  q.addEventListener("input", draw);
  /* swipe left or right to change collection, like every other app (her 15 Sep "for every app ... the swipe") */
  var x0 = null, y0 = 0, t0 = 0;
  document.addEventListener("touchstart", function(e){
    if(e.touches.length !== 1 || e.target.closest("input, .tabs, .dx .map")){ x0 = null; return; }   /* the map scrolls sideways */
    x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; t0 = Date.now();
  }, {passive:true});
  document.addEventListener("touchend", function(e){
    if(x0 === null) return;
    var dx = e.changedTouches[0].clientX - x0, dy = e.changedTouches[0].clientY - y0; x0 = null;
    if(Math.abs(dx) < 70 || Math.abs(dy) > 50 || Date.now() - t0 > 700) return;
    var i = TABS.findIndex(function(t){ return t[0] === cur; }) + (dx < 0 ? 1 : -1);
    if(i < 0 || i >= TABS.length) return;
    cur = TABS[i][0]; try{ localStorage.setItem("recipesHub.tab", cur); }catch(err){}
    tabs(); draw(); window.scrollTo(0, 0);
  }, {passive:true});
  document.getElementById("sub").textContent = n("recipes") + " recipes, " + n("hormozi") + " Hormozi, " + n("doser") + " Doser workflows and " + n("prompts") + " prompts, in one place.";
  tabs(); draw();
  /* 23 Sep 2026: an old /workflows/#find=<title> (or #c-<card key>) link forwards here with its hash, and
     lands on that card, opened - not just on the tab. */
  (function(){
    var h = location.hash, m = h.match(/^#find=(.+)$/), c = h.match(/^#c-(.+)$/), hit = null, want = "";
    try { want = decodeURIComponent((m || c || [])[1] || "").trim(); } catch(e){ return; }
    if(!want) return;
    if(c) hit = ALL.filter(function(x){ return x.src === "doser" && String(x.k) === want; })[0];
    else {
      var low = want.toLowerCase(), near = function(x){ var t = x.title.toLowerCase().replace(/…$/, ""); return t && (low.indexOf(t) === 0 || t.indexOf(low) === 0); };
      var pool = ALL.filter(function(x){ return x.src === "doser"; });
      hit = pool.filter(function(x){ return x.title.toLowerCase() === low; })[0] || pool.filter(near)[0] ||
            ALL.filter(function(x){ return x.title.toLowerCase() === low; })[0] || ALL.filter(near)[0];
    }
    if(!hit) return;
    cur = hit.src; q.value = ""; tabs(); draw();
    var card = document.querySelector('.card[data-i="' + SHOWN.indexOf(hit) + '"]');
    if(!card) return;
    card.scrollIntoView({block:"start"});
    if(hit.src !== "recipes") show(card, hit);
  })();
  /* marketing-notion.js copies the answers to Notion under each card's title; on /workflows/ it read the
     title off the drawn card, and here not every card is drawn, so this page names them itself */
  window.MN_TITLE = function(k){ var r = ALL.filter(function(x){ return x.src === "doser" && x.k === k; })[0]; return r ? r.title : ""; };
})();
</script>
<script src="../notion-sync.js" data-quiet></script>
<!-- 23 Sep 2026: /workflows/ copied her Yes / No / Not for me answers to Notion with this; they are answered here now -->
<script src="../marketing-notion.js" data-app="workflows" data-notion="https://app.notion.com/p/20c2e1e5f76440dd83e8bf0eb411863e"></script>
<script>
(function(){
  var go = document.getElementById("cgo"), box = document.getElementById("cq"), out = document.getElementById("cout");
  function esc(s){ return String(s||"").replace(/[&<>"]/g, function(c){ return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]; }); }
  function link(name, recipes){
    var r = (recipes||[]).filter(function(x){ return name && (name.indexOf(x.id) > -1 || name.toLowerCase().indexOf(x.title.toLowerCase()) > -1 || new RegExp("\\b" + x.n + "\\b").test(name)); })[0];
    return r ? '<a href="' + r.id + '.html">Recipe ' + r.n + ' \u2014 ' + esc(r.title) + '</a>' : esc(name);
  }
  function ask(){
    var q = box.value.trim(); if(!q) { box.focus(); return; }
    if(!window.NotionSync){ out.textContent = "The coach could not load. Refresh the page."; return; }
    go.disabled = true; out.innerHTML = '<p class="cnote">Thinking\u2026</p>';
    window.NotionSync.post("/coach", {question: q}).then(function(r){
      go.disabled = false;
      var o = r.out || {};
      if(!r.ok || !o.plan){ out.innerHTML = '<p class="cnote">' + esc(o.error || ("Could not reach the coach (" + r.status + ").")) + '</p>'; return; }
      var p = o.plan, h = '<p>' + esc(p.answer) + '</p>';
      if((p.already||[]).length) h += '<h3>\u2713 Already doing</h3><ul>' + p.already.map(function(a){ return '<li>' + esc(a.what) + ' <span class="ev">' + esc(a.evidence) + '</span></li>'; }).join("") + '</ul>';
      if((p.not_yet||[]).length) h += '<h3>Not doing yet</h3><ul>' + p.not_yet.map(function(a){ return '<li>' + esc(a.what) + (a.recipe ? ' \u2014 ' + link(a.recipe, o.recipes) : '') + '</li>'; }).join("") + '</ul>';
      if((p.path||[]).length) h += '<h3>Go through, in this order</h3><ol>' + p.path.map(function(a){ return '<li>' + link(a.recipe, o.recipes) + ' <span class="ev">' + esc(a.why) + '</span></li>'; }).join("") + '</ol>';
      if(p.tomorrow) h += '<h3>Next day</h3><div class="tom">' + esc(p.tomorrow) + '</div>';
      h += '<p class="cnote">This question cost about US$' + (o.cost||0).toFixed(3) + '. Today so far: US$' + (o.spentToday||0).toFixed(2) + ' of $1.</p>';
      out.innerHTML = h;
    }).catch(function(e){ go.disabled = false; out.innerHTML = '<p class="cnote">' + esc(e.message === "no password" ? "The apps password is needed to ask the coach." : "Could not reach the coach. Check your connection.") + '</p>'; });
  }
  go.addEventListener("click", ask);
  box.addEventListener("keydown", function(e){ if(e.key === "Enter" && (e.metaKey || e.ctrlKey)) ask(); });
})();
</script>
<script src="../speak.js" data-icon-only defer></script>
</body>
</html>
"""


def coach_catalogue():
    """16 Sep 2026: what the recipe coach (apps-notion-relay /coach) reads - one short entry per recipe."""
    def plain(h):
        return H.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))).strip()
    out = []
    for f in sorted(glob.glob(str(SITE / "recipes" / "recipe-*.html"))):
        name = os.path.basename(f)
        s = open(f, encoding="utf-8").read()
        body = re.sub(r"<script.*?</script>|<style.*?</style>|<pre>.*?</pre>", " ", s, flags=re.S)
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)
        paras = [plain(m.group(1)) for m in re.finditer(r"<p[^>]*>(.*?)</p>", body, re.S)]
        summary = next((x for x in paras if not re.match(r"^(\S+\s+){0,3}from:", x, re.I) and len(x) > 40), "")
        def section(word):
            m = re.search(r"<h[12][^>]*>[^<]*%s.*?</h[12]>(.*?)(?=<h[12][ >])" % word, body, re.S | re.I)
            return plain(m.group(1))[:600] if m else ""
        n = re.match(r"recipe-(\d+)", name)
        out.append({"id": name[:-5], "n": int(n.group(1)), "title": re.sub(r"^RECIPE\s*\d+\s*[\u2014-]\s*", "", plain(h1.group(1) if h1 else name)),
                    "url": "https://racts-dot.github.io/recipes/" + name, "summary": summary[:400],
                    "one_thing": section("THE ONE THING"), "try_tonight": section("What to try"),
                    "sections": [plain(m.group(1))[:80] for m in re.finditer(r"<h[123][^>]*>(.*?)</h[123]>", body, re.S)][1:14]})
    (SITE / "recipes" / "coach.json").write_text(json.dumps({"recipes": out}, ensure_ascii=False), encoding="utf-8")
    return len(out)


# 23 Sep 2026: /workflows/' "How this was made", word for word; the two numbers came from its data blob
# (n_videos_used, n_recipes: 62 and 109 on main that day)
MADE = ("<p><b>How this was made.</b> %d of Ryan Doser's AI marketing videos were read in full from their caption files by "
        "Gemini 3.1 Pro, which pulled out each method as steps. %d recipes came out; ones teaching the same method were "
        "grouped, and the clearest version is shown, with the other videos listed under it.</p>\n")


def doser_made(text):
    """The "How this was made" paragraph for the Doser tab, with the counts from wherever they still are.

    The Doser source when the publisher hands it over; else /workflows/ while it is a real page; else the
    numbers this page already shows, so a plain rebuild keeps them. Only when none of those has them is the
    paragraph left out - a count this script cannot read is never made up.
    """
    d = data_blob(None, text) if text is not None else (
        data_blob(SITE / "workflows" / "index.html") if (SITE / "workflows" / "index.html").exists() else None)
    if d and isinstance(d.get("n_videos_used"), int) and isinstance(d.get("n_recipes"), int):
        return MADE % (d["n_videos_used"], d["n_recipes"])
    home = SITE / "recipes" / "index.html"
    rx = re.escape(MADE).replace("%d", r"(\d+)")
    m = re.search(rx, home.read_text(encoding="utf-8")) if home.exists() else None
    if m:
        return MADE % (int(m.group(1)), int(m.group(2)))
    print("  WARNING: no Doser video/recipe counts found; the Doser tab's \"How this was made\" paragraph is left out")
    return ""


# 23 Sep 2026: /workflows/' count line under "Marketing cookbook", from its data blob (n_cards, n_videos_used: 75 and 62)
COUNT = '<span class="label">%d recipes · %d videos</span>'


def doser_count(text):
    """The "75 recipes · 62 videos" label for the Doser tab, found the same way round as doser_made()."""
    d = data_blob(None, text) if text is not None else (
        data_blob(SITE / "workflows" / "index.html") if (SITE / "workflows" / "index.html").exists() else None)
    if d and isinstance(d.get("n_cards"), int) and isinstance(d.get("n_videos_used"), int):
        return COUNT % (d["n_cards"], d["n_videos_used"])
    home = SITE / "recipes" / "index.html"
    rx = re.escape(COUNT).replace("%d", r"(\d+)")
    m = re.search(rx, home.read_text(encoding="utf-8")) if home.exists() else None
    if m:
        return COUNT % (int(m.group(1)), int(m.group(2)))
    print("  WARNING: no Doser recipe/video counts found; the Doser tab's count label is left out")
    return ""


def keep_cache_bust(new_html, old_html):
    """Keep a ?v=... that somebody put on a kit script tag in the built page.

    The site's script tags get a cache-busting ?v=<date> stamped on them page by page, outside this
    script. That stamp lives only in the built file, so writing a fresh page drops it and the phones
    keep yesterday's notion-sync.js. Measured 20 Sep 2026: the live /recipes/ carried
    notion-sync.js?v=20260920b and a plain rebuild took it straight back off.
    """
    for src, q in re.findall(r'<script src="(\.\./[^"?]+\.js)(\?[^"]+)"', old_html):
        new_html = new_html.replace('<script src="%s"' % src, '<script src="%s%s"' % (src, q))
    return new_html


def main(sources=None):
    """sources: {folder: page html} built by the publisher for a folder that only forwards now."""
    sources = sources or {}
    horm, horm_from = own_cards("hormozi", "hormozi", sources.get("hormozi"))
    dose, dose_from = own_cards("workflows", "doser", sources.get("workflows"))
    prom, prom_from = own_prompts()
    # this folder's own copy is written before the page that reads it, so a rebuild can never leave
    # the page pointing at a file that is not there
    mine = {"hormozi": write_local("hormozi", horm), "doser": write_local("doser", dose),
            "prompts": write_local("prompts", prom)}
    items = (recipe_pages() + topic_cards("hormozi", "hormozi", "Hormozi", horm)
             + topic_cards("workflows", "doser", "Doser", dose) + prompts(prom))
    blob = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    home = SITE / "recipes" / "index.html"
    page = (PAGE.replace("__DATA__", blob).replace("__LOCAL__", json.dumps(mine, ensure_ascii=False))
            .replace("__DXMADE__", doser_made(sources.get("workflows")))
            .replace("__DXCOUNT__", doser_count(sources.get("workflows"))))
    if home.exists():
        page = keep_cache_bust(page, home.read_text(encoding="utf-8"))
        import site_tags   # 23 Sep 2026: keep kit pieces added on the site (marks.js, the dock) - see site_tags.py
        page, carried = site_tags.carry(page, home.read_text(encoding="utf-8"))
        if carried:
            print("  recipes/index.html: kept from the site page:", ", ".join(carried))
    home.write_text(page, encoding="utf-8")
    for folder, name in (("hormozi", "Hormozi Marketing Recipes"), ("workflows", "Doser AI Marketing Workflows"),
                         ("cookbook", "Sabrina's Prompt Cookbook")):
        p = SITE / folder / "index.html"
        if p.exists():
            s = p.read_text(encoding="utf-8")
            if RETIRED in s:
                continue   # a forwarder: nothing to put a bar on
            t = add_bar(s, name).replace('<script src="../speak.js" defer>', '<script src="../speak.js" data-icon-only defer>')
            if t != s:
                p.write_text(t, encoding="utf-8")
    print("coach catalogue:", coach_catalogue(), "recipes")
    for src, where in (("hormozi", horm_from), ("doser", dose_from), ("prompts", prom_from)):
        f = SITE / "recipes" / LOCAL[src]
        print("  %-8s <- %-28s %s, %d KB" % (src, where, LOCAL[src], round(f.stat().st_size / 1024)))
    counts = {}
    for x in items:
        counts[x["src"]] = counts.get(x["src"], 0) + 1
    print("recipes home:", counts)


if __name__ == "__main__":
    main()
