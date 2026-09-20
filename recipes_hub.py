#!/usr/bin/env python3
"""One Recipes app: /recipes/ becomes the home for all four recipe collections.

Her words, 15 Sep 2026: "can you combine the recipes into one recipes", and her pick
"All four in one Recipes app": the 11 Recipes pages, Hormozi Marketing Recipes,
Doser AI Marketing Workflows and Sabrina's Prompt Cookbook. One home-screen icon, tabs,
and one search box across all of them.

Nothing inside the four collections is rewritten. Each keeps its own page, read aloud, videos
and Notion saving. This script:
  1. writes recipes/index.html, the combined home, from what the four pages actually contain;
  2. adds a slim "All recipes" bar and a find-on-open helper (#find=...) to the three other pages,
     so a card tapped on the home opens that exact recipe.

    python3 recipes_hub.py          # after build_recipes.py or publish_marketing_pages.py

build_recipes.py and publish_marketing_pages.py both call it at the end, so a rebuild keeps the home.
"""
import glob
import html as H
import json
import os
import pathlib
import re

SITE = pathlib.Path(__file__).resolve().parent
MARK = "<!--recipes-hub-bar-->"

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


def data_blob(path):
    s = open(path, encoding="utf-8").read()
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


def topic_cards(folder, src, label):
    d = data_blob(SITE / folder / "index.html")
    out = []
    if not d:
        return out
    for t in d.get("topics", []):
        for c in t.get("cards", []):
            title = txt(c.get("title"), 120)
            out.append({"src": src, "label": txt(t.get("name"), 40) or label, "title": title,
                        "desc": txt(c.get("gets"), 150), "href": f"../{folder}/#find=" + title,
                        # 20 Sep, her "I'll want it like in the same app": the card's own key travels with
                        # it, so opening it here finds the one card and never a title that merely matches
                        "k": c.get("key", ""),
                        # 17 Sep, her "no thumbnail ... no video": the card's first source video, like the recipe cards
                        "thumb": (f"https://i.ytimg.com/vi/{c['src'][0]['id']}/mqdefault.jpg" if c.get("src") and c["src"][0].get("id") else ""),
                        "vid": (c["src"][0]["id"] if c.get("src") and c["src"][0].get("id") else ""),
                        "listen": False,
                        "meta": ("\u25B6 %d video%s" % (len(c["src"]), "" if len(c["src"]) == 1 else "s")) if c.get("src") else ""})
    return out


def prompts():
    d = data_blob(SITE / "cookbook" / "index.html") or []
    out = []
    for i, p in enumerate(d):
        tools = p.get("t")
        if isinstance(tools, str):
            tools = re.findall(r"'([^']+)'", tools) or [tools]
        # 19 Sep, her "There's no thumbnail updated just yet": every one of these cards was pictureless,
        # and the cookbook already carried the video each prompt came from. Measured 20 Sep: all 99
        # resolve to a YouTube id, so the whole Prompts tab gets the same real frame the other tabs use.
        vids = [m.group(1) for m in (re.search(r"[?&]v=([A-Za-z0-9_-]{11})", s.get("u") or "")
                                     for s in (p.get("src") or [])) if m]
        vids = list(dict.fromkeys(vids))
        out.append({"src": "prompts", "label": ", ".join(tools or [])[:40] or "Prompt", "title": txt(p.get("n"), 120),
                    "desc": txt(p.get("p"), 150), "href": "../cookbook/#find=" + txt(p.get("n"), 120),
                    # the cookbook's data is a plain list, so its place in that list is its key
                    "k": i,
                    "thumb": (f"https://i.ytimg.com/vi/{vids[0]}/mqdefault.jpg" if vids else ""),
                    "vid": vids[0] if vids else "",
                    "meta": ("▶ %d video%s" % (len(vids), "" if len(vids) == 1 else "s")) if vids else "",
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
.panel .busy{color:var(--ink2)}
.chip{justify-self:start;font:700 11px/1 var(--sans);letter-spacing:.04em;text-transform:uppercase;padding:5px 8px;border-radius:6px;background:var(--chip)}
.s-recipes .chip{color:var(--recipes)} .s-hormozi .chip{color:var(--hormozi)} .s-doser .chip{color:var(--doser)} .s-prompts .chip{color:var(--prompts)}
.card .t{font:600 17px/1.3 var(--serif)}
.card .d{font-size:14px;color:var(--ink2)}
.card .l{font-size:12px;color:var(--ink2)}
.empty{color:var(--ink2);padding:24px 4px}
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
<section class="coach" aria-label="Ask the coach">
  <label for="cq">Ask the coach</label>
  <div class="cq"><textarea id="cq" rows="2" placeholder="e.g. What do I need to go through to learn Claude Code for my shop?"></textarea>
  <button type="button" id="cgo">Ask</button></div>
  <p class="cnote">Reads your "I've done this" ticks and your Morning &amp; Evening notes from the last 30 days. About 1&ndash;2c a question, capped at US$1 a day.</p>
  <div id="cout" aria-live="polite"></div>
</section>
<p class="count" id="count" aria-live="polite"></p>
<div class="grid" id="grid"></div>
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
    document.getElementById("count").textContent = rows.length + (rows.length === 1 ? " recipe" : " recipes") + (term ? " match “" + term + "”" : "");
    stop(); shut();   // the rows are about to be thrown away, so nothing is playing or open any more
    SHOWN = rows;
    document.getElementById("grid").innerHTML = rows.length ? rows.map(function(x, i){
      var pic = !x.thumb ? "" : (x.vid
        ? '<button type="button" class="th" data-v="' + esc(x.vid) + '" aria-label="Play the video for ' + esc(x.title) + '"><img src="' + esc(x.thumb) + '" alt="" loading="lazy"></button>'
        : '<div class="th"><img src="' + esc(x.thumb) + '" alt="" loading="lazy"></div>');
      return '<div class="card s-' + x.src + '" data-i="' + i + '">' + pic +
        '<a class="in" href="' + esc(x.href) + '"><span class="chip">' + esc(NAME[x.src]) + (x.label && x.src !== "prompts" ? " · " + esc(x.label) : "") + '</span>' +
        '<div class="t">' + mark(x.title, term) + '</div>' +
        (x.desc ? '<div class="d">' + mark(x.desc, term) + '</div>' : "") +
        (x.meta ? '<div class="l">' + esc(x.meta) + '</div>' : (x.listen ? '<div class="l">🎙 Natural voice</div>' : "")) + '</a></div>';
    }).join("") : '<p class="empty">Nothing matches. Try fewer words.</p>';
  }
  /* 19 Sep, her "there is nothing, no video engraved in it": tapping a card's picture plays the video in
     that picture, the way the recipe pages already play theirs. One at a time - starting another, changing
     tab or searching puts the picture back. The words under it still open the recipe. */
  var NOW = null, SHOWN = [], PANEL = null, DATA = {};
  function stop(){
    if(!NOW) return;
    if(NOW.isConnected){ NOW.innerHTML = NOW.dataset.pic; NOW.classList.remove("playing"); }
    NOW = null;
  }
  function play(th){
    if(th === NOW) return;
    stop();
    th.dataset.pic = th.innerHTML;
    th.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + encodeURIComponent(th.dataset.v) +
      '?autoplay=1&playsinline=1&rel=0" title="Video" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>' +
      '<button type="button" class="x" aria-label="Close the video">✕</button>';
    th.classList.add("playing");
    NOW = th;
  }
  /* 20 Sep, her "I don't want it in a separate links or some sort. I'll want it like in the same app":
     a Hormozi, Doser or Prompt card opens what it actually says HERE, under the card. The other app's
     page is fetched once and read for that one card, so the words stay in one place and nothing is
     copied into this file. The ticks, the Notion button and the read-aloud still live on the full card,
     one tap away at the bottom. If the fetch fails the link does what it always did. */
  var WHERE = {hormozi:"../hormozi/", doser:"../workflows/", prompts:"../cookbook/"};
  var FULL = {hormozi:"Open the full card in Hormozi", doser:"Open the full card in Doser workflows",
              prompts:"Open in the Prompt Cookbook"};
  function load(src){
    if(!DATA[src]) DATA[src] = fetch(WHERE[src]).then(function(r){ return r.text(); }).then(function(t){
      var i = t.indexOf('<script id="data"');
      var a = i < 0 ? -1 : t.indexOf(">", i) + 1, b = a < 1 ? -1 : t.indexOf("</" + "script>", a);
      if(b < 0) throw new Error("no data blob in " + src);
      return JSON.parse(t.slice(a, b));   /* the other page escapes its closing tags, which JSON itself reads back */
    });
    return DATA[src];
  }
  function pick(d, x){
    if(x.src === "prompts") return d[+x.k];
    var hit = null;
    (d.topics || []).forEach(function(t){ (t.cards || []).forEach(function(c){ if(!hit && c.key === x.k) hit = c; }); });
    return hit;
  }
  function pic(id, name){
    return '<button type="button" class="th" data-v="' + esc(id) + '" aria-label="Play ' + esc(name) + '">' +
      '<img src="https://i.ytimg.com/vi/' + esc(id) + '/mqdefault.jpg" alt="" loading="lazy"></button>';
  }
  function shot(id, name, when){
    return '<div>' + pic(id, name) + '<div class="l">' + esc(name) + (when ? " \u00B7 " + esc(when) : "") + '</div></div>';
  }
  function body(x, c){
    var foot = '<div class="row"><a class="btn" href="' + esc(x.href) + '">' + esc(FULL[x.src]) + '</a>' +
      '<button type="button" class="btn close">Close</button></div>';
    if(x.src === "prompts"){
      var seen = {}, films = (c.src || []).map(function(v){
        var id = (String(v.u || "").match(/[?&]v=([A-Za-z0-9_-]{11})/) || [])[1];
        if(!id || seen[id]) return ""; seen[id] = 1;
        return shot(id, (v.v || "video").slice(0, 70), v.y || "");
      }).join("");
      return '<h2>' + esc(c.n) + '</h2>' +
        '<div><span class="label">The prompt, word for word</span><pre>' + esc(c.p) + '</pre></div>' +
        '<div class="row"><button type="button" class="btn copy">Copy</button>' +
        (c.t || []).map(function(t){ return '<span class="chip">' + esc(t) + '</span>'; }).join("") + '</div>' +
        (films ? '<div><span class="label">Where she said it</span><div class="vids">' + films + '</div></div>' : "") + foot;
    }
    var steps = (c.steps || []).map(function(v){
      /* Both source pages mark which steps are his words and which the AI wrote, and a step must not
         lose that mark by being read here. The wording is theirs. Measured 20 Sep over all 1,731 steps:
         this one test reproduces both pages exactly - on Hormozi every quote-less step is already
         sup "none" or "no", and on Doser sup is always empty so the missing quote is the whole test. */
      var sup = (v.sup === "no" || v.sup === "none" || !v.q)
        ? ' <span class="ai" title="Written by the AI; his words here do not say this">AI step, not his words</span>'
        : v.sup === "partly"
          ? ' <span class="ai" title="Goes a little beyond what he says">loosely from his words</span>' : "";
      return '<li>' + esc(v.do) + sup + (v.q ? '<span class="sq"><q>' + esc(v.q) + '</q></span>' : "") + '</li>';
    }).join("");
    var vids = (c.src || []).map(function(v){ return shot(v.id, v.title || "video", v.date || ""); }).join("");
    return '<h2>' + esc(c.title) + '</h2>' +
      (c.gets ? '<p><b>What it can get you:</b> ' + esc(c.gets) + '</p>' : "") +
      (c.claim ? '<div><span class="label">His words</span><p><q>' + esc(c.claim) + '</q></p></div>' : "") +
      (steps ? '<div><span class="label">How to do it</span><ol>' + steps + '</ol></div>' : "") +
      (c.warn ? '<div><span class="label">Watch out</span><p><q>' + esc(c.warn) + '</q></p></div>' : "") +
      (vids ? '<div><span class="label">From</span><div class="vids">' + vids + '</div></div>' : "") + foot;
  }
  function shut(){
    if(!PANEL) return;
    if(NOW && PANEL.el.contains(NOW)) stop();   // the player is about to be thrown away with the panel
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
      el.innerHTML = body(x, c);
      var top = el.getBoundingClientRect().top;
      if(top < 0 || top > window.innerHeight - 140) el.scrollIntoView({block:"center"});
    }).catch(function(){ if(PANEL && PANEL.el === el) location.href = x.href; });
  }
  document.getElementById("grid").addEventListener("click", function(e){
    if(e.target.closest(".th .x")){ stop(); return; }
    var th = e.target.closest("button.th[data-v]");
    if(th && !th.classList.contains("playing")){ play(th); return; }
    if(e.target.closest(".panel .close")){ shut(); return; }
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
    if(e.touches.length !== 1 || e.target.closest("input, .tabs")){ x0 = null; return; }
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
})();
</script>
<script src="../notion-sync.js" data-quiet></script>
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


def main():
    items = recipe_pages() + topic_cards("hormozi", "hormozi", "Hormozi") + topic_cards("workflows", "doser", "Doser") + prompts()
    blob = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    home = SITE / "recipes" / "index.html"
    page = PAGE.replace("__DATA__", blob)
    if home.exists():
        page = keep_cache_bust(page, home.read_text(encoding="utf-8"))
    home.write_text(page, encoding="utf-8")
    for folder, name in (("hormozi", "Hormozi Marketing Recipes"), ("workflows", "Doser AI Marketing Workflows"),
                         ("cookbook", "Sabrina's Prompt Cookbook")):
        p = SITE / folder / "index.html"
        if p.exists():
            s = p.read_text(encoding="utf-8")
            t = add_bar(s, name).replace('<script src="../speak.js" defer>', '<script src="../speak.js" data-icon-only defer>')
            if t != s:
                p.write_text(t, encoding="utf-8")
    print("coach catalogue:", coach_catalogue(), "recipes")
    counts = {}
    for x in items:
        counts[x["src"]] = counts.get(x["src"], 0) + 1
    print("recipes home:", counts)


if __name__ == "__main__":
    main()
