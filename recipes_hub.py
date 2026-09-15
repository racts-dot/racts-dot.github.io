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
            "listen": os.path.exists(SITE / "recipes" / "a" / (name[:-5] + ".mp3")),
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
                        "thumb": "", "listen": False})
    return out


def prompts():
    d = data_blob(SITE / "cookbook" / "index.html") or []
    out = []
    for p in d:
        tools = p.get("t")
        if isinstance(tools, str):
            tools = re.findall(r"'([^']+)'", tools) or [tools]
        out.append({"src": "prompts", "label": ", ".join(tools or [])[:40] or "Prompt", "title": txt(p.get("n"), 120),
                    "desc": txt(p.get("p"), 150), "href": "../cookbook/#find=" + txt(p.get("n"), 120),
                    "thumb": "", "listen": False})
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
.card img{width:100%;aspect-ratio:16/9;object-fit:cover;display:block;background:var(--chip)}
.card .in{padding:12px 14px 14px;display:grid;gap:6px}
.chip{justify-self:start;font:700 11px/1 var(--sans);letter-spacing:.04em;text-transform:uppercase;padding:5px 8px;border-radius:6px;background:var(--chip)}
.s-recipes .chip{color:var(--recipes)} .s-hormozi .chip{color:var(--hormozi)} .s-doser .chip{color:var(--doser)} .s-prompts .chip{color:var(--prompts)}
.card .t{font:600 17px/1.3 var(--serif)}
.card .d{font-size:14px;color:var(--ink2)}
.card .l{font-size:12px;color:var(--ink2)}
.empty{color:var(--ink2);padding:24px 4px}
mark{background:rgba(224,138,78,.28);color:inherit;border-radius:3px}
</style>
<script src="../textsize.js"></script>
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
    document.getElementById("grid").innerHTML = rows.length ? rows.map(function(x){
      return '<a class="card s-' + x.src + '" href="' + esc(x.href) + '">' +
        (x.thumb ? '<img src="' + esc(x.thumb) + '" alt="" loading="lazy">' : "") +
        '<div class="in"><span class="chip">' + esc(NAME[x.src]) + (x.label && x.src !== "prompts" ? " · " + esc(x.label) : "") + '</span>' +
        '<div class="t">' + mark(x.title, term) + '</div>' +
        (x.desc ? '<div class="d">' + mark(x.desc, term) + '</div>' : "") +
        (x.listen ? '<div class="l">🎙 Natural voice</div>' : "") + '</div></a>';
    }).join("") : '<p class="empty">Nothing matches. Try fewer words.</p>';
  }
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
<script src="../speak.js" defer></script>
</body>
</html>
"""


def main():
    items = recipe_pages() + topic_cards("hormozi", "hormozi", "Hormozi") + topic_cards("workflows", "doser", "Doser") + prompts()
    blob = json.dumps(items, ensure_ascii=False).replace("</", "<\\/")
    (SITE / "recipes" / "index.html").write_text(PAGE.replace("__DATA__", blob), encoding="utf-8")
    for folder, name in (("hormozi", "Hormozi Marketing Recipes"), ("workflows", "Doser AI Marketing Workflows"),
                         ("cookbook", "Sabrina's Prompt Cookbook")):
        p = SITE / folder / "index.html"
        if p.exists():
            s = p.read_text(encoding="utf-8")
            t = add_bar(s, name)
            if t != s:
                p.write_text(t, encoding="utf-8")
    counts = {}
    for x in items:
        counts[x["src"]] = counts.get(x["src"], 0) + 1
    print("recipes home:", counts)


if __name__ == "__main__":
    main()
