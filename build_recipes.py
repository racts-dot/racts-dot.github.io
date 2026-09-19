#!/usr/bin/env python3
"""Render the Sabrina recipe markdown into pages for the site.

Source of truth is the markdown in costway-scraper. This script only renders;
never edit the generated HTML by hand, or the next run silently throws the
edit away.

Run:  python build_recipes.py
"""
import io
import json
import os
import re
import html
import glob
import datetime

SRC = r"C:\Users\soyan\costway-scraper"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recipes")

CSS = """
:root{--bg:#0f1115;--card:#171a21;--border:#2a2e38;--text:#e8e9ed;--muted:#8b8f9b;--accent:#6c8cff;--chip:#3c4050;--danger:#ff6b6b;--ok:#4ade80}
*{box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:var(--bg);color:var(--text);min-height:100vh;padding:max(20px,env(safe-area-inset-top)) 16px 80px;line-height:1.6}
.wrap{max-width:720px;margin:0 auto}
a{color:var(--accent)}
.back{display:inline-block;color:var(--muted);text-decoration:none;font-size:13px;margin-bottom:18px}
.back:hover{color:var(--text)}
h1{font-size:24px;line-height:1.3;margin:0 0 18px}
h2{font-size:19px;line-height:1.35;margin:32px 0 12px;padding-top:14px;border-top:1px solid var(--border)}
h3{font-size:16px;margin:24px 0 8px;color:var(--accent)}
p{margin:0 0 14px}
strong{color:#fff}
hr{border:none;border-top:1px solid var(--border);margin:28px 0}
blockquote{margin:0 0 16px;padding:12px 16px;background:var(--card);border-left:3px solid var(--accent);border-radius:0 10px 10px 0;color:var(--muted);font-style:italic}
blockquote strong{color:var(--text)}
pre{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:14px;overflow-x:auto;margin:0 0 18px}
pre code{font:13px/1.5 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color:var(--muted);white-space:pre;background:none;padding:0}
code{font:13px ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--chip);padding:2px 6px;border-radius:6px;color:var(--text)}
.tablewrap{overflow-x:auto;margin:0 0 18px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--border);vertical-align:top}
th{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em;font-weight:600}
tr:last-child td{border-bottom:none}
ul,ol{margin:0 0 16px;padding-left:22px}
li{margin-bottom:6px}
.cards{display:flex;flex-direction:column;gap:10px;margin-bottom:26px}
.card{display:block;padding:14px 16px;background:var(--card);border:1px solid var(--border);border-radius:12px;text-decoration:none;color:var(--text)}
.card:hover{border-color:var(--accent)}
.card .n{font-size:11px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase}
.card .t{font-size:15px;font-weight:600;margin:3px 0 4px;line-height:1.35}
.card .d{font-size:13px;color:var(--muted);line-height:1.45}
.card.warn{border-color:#5a3a3a}
.lede{color:var(--muted);font-size:14px;margin-bottom:22px}
.foot{margin-top:40px;padding-top:16px;border-top:1px solid var(--border);color:var(--muted);font-size:12px}
"""

HEAD = (
    '<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">\n'
    '<meta name="robots" content="noindex,nofollow">\n'
    '<meta name="apple-mobile-web-app-capable" content="yes">\n'
    '<meta name="theme-color" content="#0f1115">\n'
    '<title>{title}</title>\n<style>{css}</style>\n<script src="../textsize.js"></script><script src="../feedback.js" defer></script>\n</head>\n<body>\n<div class="wrap">\n'
)
TAIL = '\n<div class="foot">{foot}</div>\n</div>\n</body>\n</html>\n'


def inline(t):
    """Inline markdown -> HTML. Code spans are protected before anything else."""
    spans = []

    def stash(m):
        spans.append(m.group(1))
        return "\x00%d\x00" % (len(spans) - 1)

    t = re.sub(r"`([^`]+)`", stash, t)
    t = html.escape(t, quote=False)
    t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
               r'<a href="\2" target="_blank" rel="noopener">\1</a>', t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", t)
    t = re.sub(r"(?<![*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", t)
    return re.sub(r"\x00(\d+)\x00",
                  lambda m: "<code>%s</code>" % html.escape(spans[int(m.group(1))], quote=False),
                  t)


def _cells(row):
    return [c.strip() for c in row.strip().strip("|").split("|")]


def render(md):
    lines = md.split("\n")
    out = []
    i = 0
    while i < len(lines):
        ln = lines[i]

        if ln.startswith("```"):
            i += 1
            buf = []
            while i < len(lines) and not lines[i].startswith("```"):
                buf.append(lines[i])
                i += 1
            i += 1
            out.append("<pre><code>%s</code></pre>"
                       % html.escape("\n".join(buf), quote=False))
            continue

        if (re.match(r"^\s*\|.*\|\s*$", ln) and i + 1 < len(lines)
                and re.match(r"^\s*\|[\s:|-]+\|\s*$", lines[i + 1])):
            head = _cells(ln)
            i += 2
            body = []
            while i < len(lines) and re.match(r"^\s*\|.*\|\s*$", lines[i]):
                body.append(_cells(lines[i]))
                i += 1
            th = "".join("<th>%s</th>" % inline(c) for c in head)
            tr = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % inline(c) for c in r)
                         for r in body)
            out.append('<div class="tablewrap"><table><thead><tr>%s</tr></thead>'
                       "<tbody>%s</tbody></table></div>" % (th, tr))
            continue

        if re.match(r"^\s*(---|___|\*\*\*)\s*$", ln):
            out.append("<hr>")
            i += 1
            continue

        m = re.match(r"^(#{1,4})\s+(.*)$", ln)
        if m:
            lvl = min(len(m.group(1)), 3)
            out.append("<h%d>%s</h%d>" % (lvl, inline(m.group(2)), lvl))
            i += 1
            continue

        if ln.startswith(">"):
            buf = []
            while i < len(lines) and lines[i].startswith(">"):
                buf.append(lines[i].lstrip(">").strip())
                i += 1
            out.append("<blockquote>%s</blockquote>"
                       % inline(" ".join(b for b in buf if b)))
            continue

        m = re.match(r"^\s*([-*]|\d+\.)\s+", ln)
        if m:
            ordered = m.group(1) not in ("-", "*")
            items = []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]))
                i += 1
            tag = "ol" if ordered else "ul"
            out.append("<%s>%s</%s>"
                       % (tag, "".join("<li>%s</li>" % inline(x) for x in items), tag))
            continue

        if not ln.strip():
            i += 1
            continue

        buf = []
        while (i < len(lines) and lines[i].strip()
               and not re.match(r"^\s*(#{1,4}\s|>|```|\||[-*]\s|\d+\.\s|---\s*$)", lines[i])):
            buf.append(lines[i])
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(buf)))

    return "\n".join(out)


def title_of(md, fallback):
    """The H1, minus the 'RECIPE 07 -- ' prefix the card already shows as a chip."""
    m = re.search(r"^#\s+(.*)$", md, re.M)
    if not m:
        return fallback
    t = re.sub(r"\s+", " ", re.sub(r"[*`#]", "", m.group(1))).strip()
    return re.sub(r"^RECIPE\s+\d+\s*[\u2014\u2013-]\s*", "", t)


def blurb(md):
    """First real sentence of the page.

    Everything above it is provenance -- the 'From: <video> - <date>' line, the
    bare [watch] link, and the 'Rewritten after ...' note. Those must be
    stripped BEFORE any length test, or a long URL passes as a sentence.
    """
    lines = md.split("\n")
    # Some pages open straight into a numbered section with no lede paragraph.
    # Their first sub-heading summarises the page better than their first
    # sentence does, so keep it as a fallback.
    sub = ""
    for ln in lines:
        m = re.match(r"^#{2,3}\s+(.*)$", ln)
        if m:
            sub = re.sub(r"\s+", " ", re.sub(r"[*`#]", "", m.group(1))).strip()
            break

    i = 0
    while i < len(lines):
        raw = lines[i]
        if not raw.strip() or raw.lstrip().startswith(("#", "|", "```", "---")):
            i += 1
            continue
        # A markdown paragraph is every consecutive non-blank line, not one line.
        # Taking a single line truncates the blurb at the author's line wrap.
        para = []
        while i < len(lines) and lines[i].strip() and not lines[i].lstrip().startswith(
                ("#", "|", "```", "---")):
            para.append(lines[i].strip())
            i += 1
        s = re.sub(r"[*`>]", "", " ".join(para)).strip()
        s = re.sub(r"\[([^\]]+)\]\((?:[^)]*)\)", r"\1", s)
        s = re.sub(r"https?://\S+", "", s).strip()
        if s.startswith("From:") or s.startswith("\u26a0 Rewritten"):
            continue
        s = re.sub(r"\s+", " ", re.sub(r"[\s\u00b7\u2014\u2013:-]+$", "", s)).strip()
        if len(s.split()) < 6:
            continue
        if len(s.split()) < 10 and len(sub.split()) >= 5:
            s = sub
        if len(s) <= 150:
            return s
        cut = s[:150]
        # Prefer a word boundary so the card never ends mid-word.
        return cut[:cut.rfind(" ")].rstrip(" ,;:") + "\u2026"
    return sub


LOCAL_SRC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recipes_src")


def local_sources():
    """16 Sep 2026: recipes 11+ were written on the Mac and their markdown lives in this repo, so both machines have it."""
    return sorted(glob.glob(os.path.join(LOCAL_SRC, "RECIPE_*.md")))


def render_page(p, today):
    md = io.open(p, encoding="utf-8").read()
    base = os.path.basename(p)
    slug = re.sub(r"[^a-z0-9]+", "-", os.path.splitext(base)[0].lower()).strip("-")
    page = (HEAD.format(title=html.escape(title_of(md, base)), css=CSS)
            + '<a class="back" href="./">← all recipes</a>\n'
            + render(md)
            + TAIL.format(foot="Built %s from %s. Edit the markdown, not this page."
                          % (today, html.escape(base))))
    io.open(os.path.join(OUT, slug + ".html"), "w", encoding="utf-8", newline="\n").write(page)
    return slug + ".html"


def render_local():
    """The Mac has only recipes_src: render those pages and leave the index to recipes_hub."""
    today = datetime.date.today().isoformat()
    for p in local_sources():
        print("rendered", render_page(p, today))


def main():
    os.makedirs(OUT, exist_ok=True)
    today = datetime.date.today().isoformat()

    srcs = sorted(glob.glob(os.path.join(SRC, "RECIPE_*.md")))
    have = {os.path.basename(p) for p in srcs}
    srcs += [p for p in local_sources() if os.path.basename(p) not in have]
    risk =os.path.join(SRC, "READ_2026-09-13_the_git_risk_and_what_i_got_wrong.md")
    if os.path.exists(risk):
        srcs.append(risk)

    cards = []
    for p in srcs:
        md = io.open(p, encoding="utf-8").read()
        base = os.path.basename(p)
        slug = re.sub(r"[^a-z0-9]+", "-", os.path.splitext(base)[0].lower()).strip("-")
        title = title_of(md, base)
        m = re.match(r"RECIPE_(\d+)", base)
        num = m.group(1) if m else "NOTE"

        page = (HEAD.format(title=html.escape(title), css=CSS)
                + '<a class="back" href="./">\u2190 all recipes</a>\n'
                + render(md)
                + TAIL.format(foot="Built %s from %s. Edit the markdown, not this page."
                              % (today, html.escape(base))))
        io.open(os.path.join(OUT, slug + ".html"), "w",
                encoding="utf-8", newline="\n").write(page)
        cards.append((num, title, blurb(md), slug + ".html", num == "NOTE"))

    body = [
        "<h1>Recipes</h1>",
        '<p class="lede">Ten videos, read in full and written down. One page each '
        "\u2014 what it actually teaches, and what to skip.</p>",
        '<div class="cards">',
    ]
    for num, title, desc, href, is_note in cards:
        label = "Note" if num == "NOTE" else "Recipe %s" % num.lstrip("0")
        body.append('<a class="card%s" href="%s"><div class="n">%s</div>'
                    '<div class="t">%s</div><div class="d">%s</div></a>'
                    % (" warn" if is_note else "", href, label,
                       html.escape(title), html.escape(desc)))
    body.append("</div>")

    io.open(os.path.join(OUT, "index.html"), "w", encoding="utf-8", newline="\n").write(
        HEAD.format(title="Recipes", css=CSS)
        + "\n".join(body)
        + TAIL.format(foot="%d pages, built %s." % (len(cards), today))
    )
    print("built %d pages + index -> %s" % (len(cards), OUT))


def copy_to_notion():
    """Added 14 Sep 2026: keep the Notion "Recipes" database in step with the pages.

    Sends through apps-notion-relay (C:/Users/soyan/apps-notion-relay). A failure here
    never stops the build - the pages are the job, Notion is the copy.
    """
    try:
        import sys
        sys.dont_write_bytecode = True  # keep __pycache__ out of the published site
        sys.path.insert(0, r"C:\Users\soyan\apps-notion-relay")
        import backfill_static
        app, rows = backfill_static.recipes()
        for rid, title, detail, when, data in rows:
            backfill_static.send(app, rid, title, detail, when, data)
        print("copied %d recipes to Notion" % len(rows))
    except Exception as e:  # report, never break the build
        print("NOTION COPY FAILED (pages still built): %s" % e)



# ---------------- pictures and the video, 15 Sep 2026 ----------------
# Her words: "I want it to be more illustrative. And have the references as well, so I can just
# go and click and then it plays a video." The picture is the video's own YouTube thumbnail
# (a real frame, never drawn). Tapping it plays the video on the page; any other link to the
# same video with a time (&t=) plays from that time. Runs on rendered HTML so the Mac, which
# has no recipe markdown, can apply it to the pages already built. Safe to run twice.
VID = re.compile(r'href="https://(?:www\.)?youtube\.com/watch\?v=([A-Za-z0-9_-]{11})[^"]*"')
ILL_MARK = "<!--illustrated-->"
PLAYER_CSS = """
.player{position:relative;aspect-ratio:16/9;max-width:100%;border-radius:14px;overflow:hidden;background:#000;margin:4px 0 20px;border:1px solid var(--border)}
.player button{all:unset;cursor:pointer;display:block;width:100%;height:100%;position:relative}
.player img{width:100%;height:100%;object-fit:cover;display:block}
.player .play{position:absolute;inset:0;display:grid;place-items:center}
.player .play span{width:68px;height:68px;border-radius:50%;background:rgba(0,0,0,.62);display:grid;place-items:center;font-size:28px;color:#fff;padding-left:5px;box-sizing:border-box}
.player .cap{position:absolute;left:0;right:0;bottom:0;padding:10px 12px;font-size:13px;color:#fff;background:linear-gradient(transparent,rgba(0,0,0,.75))}
.player iframe{width:100%;height:100%;border:0;display:block}
.card{display:grid;grid-template-columns:112px 1fr;gap:12px;align-items:start}
.card .thumb{width:112px;aspect-ratio:16/9;object-fit:cover;border-radius:8px;display:block;grid-row:span 3}
.card.nothumb{display:block}
a.ts{white-space:nowrap}
"""
PLAYER_JS = """<script>
(function(){
  function play(box, id, start){
    box.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&playsinline=1&rel=0' +
      (start ? '&start=' + start : '') + '" title="Video" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>';
  }
  document.addEventListener('click', function(e){
    var b = e.target.closest('.player button');
    if (b) { play(b.parentNode, b.dataset.id, 0); return; }
    var a = e.target.closest('a[href*="youtube.com/watch"]');
    var box = document.querySelector('.player');
    if (!a || !box) return;
    var m = a.href.match(/[?&]v=([A-Za-z0-9_-]{11})/), t = a.href.match(/[?&]t=(\\d+)/);
    if (!m || m[1] !== box.dataset.id) return;
    e.preventDefault();
    play(box, m[1], t ? t[1] : 0);
    box.scrollIntoView({behavior: 'smooth', block: 'start'});
  });
})();
</script>"""

def thumb(vid):
    return "https://i.ytimg.com/vi/%s/hqdefault.jpg" % vid

def illustrate_page(page):
    if ILL_MARK in page:
        return page
    m = VID.search(page)
    page = page.replace("</style>", PLAYER_CSS + "</style>", 1)
    # the "From:" line came through with its markdown stars showing
    page = re.sub(r"<p>\*\*From:(.*?)·\*\*", r"<p><strong>From:</strong>\1·", page, count=1)
    if m:
        vid = m.group(1)
        h1 = page.find("</h1>")
        title = re.search(r"<h1>(.*?)</h1>", page)
        player = ('\n<div class="player" data-id="%s"><button type="button" data-id="%s" aria-label="Play the video">'
                  '<img src="%s" alt="" loading="lazy"><span class="play"><span>&#9654;</span></span>'
                  '<span class="cap">Tap to play the video this recipe comes from</span></button></div>\n'
                  % (vid, vid, thumb(vid)))
        if h1 != -1:
            page = page[:h1 + 5] + player + page[h1 + 5:]
    page = page.replace("</body>", PLAYER_JS + ILL_MARK + "\n</body>", 1)
    return page

def illustrate_index(index_html, pages):
    """Put each recipe's video thumbnail on its card."""
    if ILL_MARK in index_html:
        return index_html
    index_html = index_html.replace("</style>", PLAYER_CSS + "</style>", 1)
    def card(m):
        href = m.group(2)
        vid = pages.get(href)
        if not vid:
            return m.group(0).replace('class="card', 'class="card nothumb', 1)
        return m.group(1) + '<img class="thumb" src="%s" alt="" loading="lazy">' % thumb(vid)
    index_html = re.sub(r'(<a class="card[^"]*" href="([^"]+)">)', card, index_html)
    return index_html.replace("</body>", ILL_MARK + "\n</body>", 1)


# ---------------- move and resize every box, 20 Sep 2026 ----------------
# Her words: "in every boxes, even for this one, I want to be able to have the option to resize,
# move it around", and the same day "The the video should be resizable."
# The video player has worked this way since 16-17 Sep, so its own dragIt and sizeIt move out here
# unchanged and the player now borrows them instead of keeping a private copy. The Read aloud bar,
# the listen/videos box, the checklist and the "I've done it" box each get the same grip, the same
# corner and their own remembered place - one box per key, kept on this phone in localStorage.
# Grab the corner and the box lifts off the page (position:fixed) the way the player does; the
# &#8634; button next to the grip puts it back and forgets the place, so nothing is a one-way trip.
BOX_BEGIN, BOX_END = "<!--boxmove-->", "<!--/boxmove-->"
BOX = BOX_BEGIN + """<style>
.bx{position:relative}
.readbar.bx,.sources.bx,.ck.bx,.done.bx{padding-right:28px}
.bx>.bxg{position:absolute;top:-11px;right:12px;display:flex;gap:4px;z-index:4}
.bx>.bxg>button{all:unset;box-sizing:border-box;cursor:grab;touch-action:none;background:var(--chip);color:var(--text);
  border:1px solid var(--border);border-radius:999px;font:600 11px/1 -apple-system,BlinkMacSystemFont,sans-serif;padding:4px 9px;opacity:.8}
.bx>.bxg>button[data-home]{cursor:pointer}
.bx>.bxg>button[hidden]{display:none}
.bx>.bxr{position:absolute;right:2px;bottom:2px;width:22px;height:22px;cursor:nwse-resize;touch-action:none;opacity:.6;
  background:linear-gradient(135deg,transparent 52%,var(--muted) 52%,var(--muted) 60%,transparent 60%,transparent 70%,var(--muted) 70%,var(--muted) 78%,transparent 78%)}
.bx.bxfloat{position:fixed;z-index:60;margin:0;max-width:calc(100vw - 12px);box-shadow:0 10px 24px -12px rgba(0,0,0,.8)}
.readbar.bxfloat{background:var(--card);border:1px solid var(--border);border-radius:12px;padding:8px 28px 8px 8px}
.bx.dragging{-webkit-user-select:none;user-select:none}
</style>
<script>
/*boxmove*/
(function(){
  function dragIt(el, handle, key){   // 16 Sep: "the videos should be movable" - same feel as the Read aloud bubble
    var sx, sy, ox, oy, moved = false, on = false, endedAt = 0;
    function clamp(x, y){ var r = el.getBoundingClientRect();
      return [Math.max(0, Math.min(x, innerWidth - r.width)), Math.max(0, Math.min(y, innerHeight - Math.min(r.height, 60)))]; }
    function place(x, y){ var c = clamp(x, y); el.style.setProperty('left', c[0] + 'px', 'important'); el.style.setProperty('top', c[1] + 'px', 'important');
      el.style.setProperty('right', 'auto', 'important'); el.style.setProperty('bottom', 'auto', 'important'); }
    el.restorePos = function(){ try { var p = JSON.parse(localStorage.getItem(key) || 'null'); if (p) place(p[0] * innerWidth, p[1] * innerHeight); } catch (e) {} };
    handle.style.touchAction = 'none';
    handle.addEventListener('pointerdown', function(e){ if (e.target.closest('button:not([data-drag])')) return;
      on = true; moved = false; sx = e.clientX; sy = e.clientY; var r = el.getBoundingClientRect(); ox = r.left; oy = r.top;
      try { handle.setPointerCapture(e.pointerId); } catch (x) {} });
    handle.addEventListener('pointermove', function(e){ if (!on) return;
      var dx = e.clientX - sx, dy = e.clientY - sy;
      if (!moved && Math.abs(dx) < 8 && Math.abs(dy) < 8) return;
      if (!moved) { moved = true; el.classList.add('dragging'); if (el.onDragStart) el.onDragStart(); }
      place(ox + dx, oy + dy); e.preventDefault(); });
    function end(){ if (!on) return; on = false; endedAt = Date.now(); el.classList.remove('dragging');
      if (moved) { var r = el.getBoundingClientRect(); try { localStorage.setItem(key, JSON.stringify([r.left / innerWidth, r.top / innerHeight])); } catch (e) {} } }
    handle.addEventListener('pointerup', end); handle.addEventListener('pointercancel', end);
    handle.addEventListener('click', function(e){ if (moved && Date.now() - endedAt < 400) { e.stopPropagation(); e.preventDefault(); } moved = false; }, true);
    addEventListener('resize', function(){ if (el.style.left) { var r = el.getBoundingClientRect(); place(r.left, r.top); } });
  }
  function sizeIt(el, grip, key, min){   // 17 Sep: "everything is resizable the boxes and movable" - drag the corner
    var sx, w0, on = false;
    el.restoreSize = function(){ try { var f = +localStorage.getItem(key); if (f) el.style.setProperty('width', Math.max(min, Math.min(f * innerWidth, innerWidth - 16)) + 'px', 'important'); } catch (e) {} };
    grip.style.touchAction = 'none';
    grip.addEventListener('pointerdown', function(e){ on = true; sx = e.clientX; w0 = el.getBoundingClientRect().width;
      if (el.onDragStart) el.onDragStart(); el.classList.add('dragging'); try { grip.setPointerCapture(e.pointerId); } catch (x) {} e.preventDefault(); e.stopPropagation(); });
    grip.addEventListener('pointermove', function(e){ if (!on) return;
      var left = el.getBoundingClientRect().left;
      var w = Math.max(min, Math.min(w0 + e.clientX - sx, innerWidth - left - 4));
      el.style.setProperty('width', w + 'px', 'important'); e.preventDefault(); });
    function end(){ if (!on) return; on = false; el.classList.remove('dragging');
      try { localStorage.setItem(key, String(el.getBoundingClientRect().width / innerWidth)); } catch (e) {} }
    grip.addEventListener('pointerup', end); grip.addEventListener('pointercancel', end);
    grip.addEventListener('click', function(e){ e.stopPropagation(); e.preventDefault(); }, true);
  }
  function enhance(el, key){   // one ordinary box: grip, corner, and the place it was left in
    if (!el || el.dataset.bx) return; el.dataset.bx = '1'; el.classList.add('bx');
    var g = document.createElement('div'); g.className = 'bxg';
    g.innerHTML = '<button type="button" data-drag="1" title="Drag to move this box" aria-label="Drag to move this box">&#10303;</button>' +
                  '<button type="button" data-home="1" title="Put this box back" aria-label="Put this box back" hidden>&#8634;</button>';
    el.appendChild(g);
    var r = document.createElement('div'); r.className = 'bxr'; r.title = 'Drag to resize this box';
    r.setAttribute('aria-label', 'Resize this box'); el.appendChild(r);
    var home = g.querySelector('[data-home]');
    function lift(){   // the box leaves the page's flow only once she actually moves it
      if (el.classList.contains('bxfloat')) return;
      var b = el.getBoundingClientRect();
      el.style.setProperty('width', b.width + 'px', 'important'); el.classList.add('bxfloat');
      el.style.setProperty('left', b.left + 'px', 'important'); el.style.setProperty('top', Math.max(0, b.top) + 'px', 'important');
      home.hidden = false;
    }
    el.onDragStart = lift;
    dragIt(el, g.querySelector('[data-drag]'), key + '.pos');
    sizeIt(el, r, key + '.w', 160);
    home.addEventListener('click', function(){
      el.classList.remove('bxfloat'); ['left', 'top', 'right', 'bottom', 'width'].forEach(function(k){ el.style.removeProperty(k); });
      try { localStorage.removeItem(key + '.pos'); localStorage.removeItem(key + '.w'); } catch (e) {}
      home.hidden = true;
    });
    try { if (localStorage.getItem(key + '.pos') || localStorage.getItem(key + '.w')) { lift(); el.restoreSize(); el.restorePos(); } } catch (e) {}
  }
  window.RecipeBox = { drag: dragIt, size: sizeIt, enhance: enhance };
  // #doneBox, not .done: the checklist puts class "done" on every ticked row, so a saved tick would
  // otherwise hand a checklist LINE its own move grip the next time the page opened.
  var BOXES = [['.readbar', 'recipes.readbar'], ['.sources', 'recipes.sources'],
               ['.ck', 'recipes.checklist'], ['#doneBox', 'recipes.done']];
  function all(){ BOXES.forEach(function(p){ document.querySelectorAll(p[0]).forEach(function(el){ enhance(el, p[1]); }); }); }
  // The checklist builds itself while the page is still parsing, so wait for the end of it, not for load.
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', all); else all();
})();
</script>""" + BOX_END


def add_boxmove(page):
    """The grip-and-corner helper, at the top of the body so the player below can use it. Safe to run again."""
    page = re.sub(re.escape(BOX_BEGIN) + r"[\s\S]*?" + re.escape(BOX_END) + r"\n*", "", page)
    tag = '<div class="wrap">'
    at = page.find(tag)
    if at == -1:
        return page
    at += len(tag)
    return page[:at] + "\n" + BOX + page[at:]


# ---------------- timestamps like the Creator Reading Room, 16 Sep 2026 ----------------
# Her words: "Can you do the timestamp as well as the videos ... just as the creators of reading room."
# Same pattern as the reading room: ONE YouTube player made once through YouTube's API, so a tap on a time
# plays with sound inside that tap on a phone; every time on the page is a pill button; any video the page
# names plays in that same player; while it plays it stays pinned at the top (Small / Big / close).
# Labels of added timestamps are CSS (data-l), not text, so Read aloud and its recordings still match.
P2_BEGIN, P2_END = "<!--player2-->", "<!--/player2-->"
P2_CSS_BEGIN, P2_CSS_END = "/*player2*/", "/*/player2*/"
P2_CSS = P2_CSS_BEGIN + """
.player{position:relative}
.player>button{position:absolute;inset:0;z-index:2}
.player>button[hidden]{display:none}
.player .yt,.player .yt iframe{position:absolute;inset:0;width:100%;height:100%;border:0}
.player.on{position:sticky;top:0;z-index:30;box-shadow:0 10px 24px -12px rgba(0,0,0,.8)}
.player.on.small{width:52%;margin-left:auto}
.player.on{overflow:visible;margin-bottom:40px}
.player .pbar{position:absolute;bottom:-32px;right:0;z-index:3;display:none;gap:6px}
.player.on .pbar{display:flex}
.player .pbar button{all:unset;width:auto;height:auto;cursor:pointer;background:rgba(0,0,0,.7);color:#fff;font-size:12px;padding:4px 9px;border-radius:999px}
.player.on.float{position:fixed;z-index:60;width:min(420px,calc(100vw - 16px));margin:0}
.player.on.float.small{width:min(240px,60vw)}
.player.dragging iframe{pointer-events:none}
.player .rsz{display:none}
.player.on .rsz{display:block;position:absolute;right:0;bottom:0;z-index:5;width:30px;height:30px;cursor:nwse-resize;touch-action:none;background:linear-gradient(135deg,transparent 50%,rgba(255,255,255,.85) 50%,rgba(255,255,255,.85) 58%,transparent 58%,transparent 68%,rgba(255,255,255,.85) 68%,rgba(255,255,255,.85) 76%,transparent 76%);border-radius:0 0 10px 0}
.player .pbar button[data-drag]{cursor:grab;touch-action:none}
a.ts{display:inline-flex;align-items:center;gap:3px;margin:0 2px 0 6px;padding:1px 8px;border-radius:999px;border:1px solid var(--chip);
  background:var(--card);font:500 12px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--accent);text-decoration:none;
  vertical-align:1px;white-space:nowrap}
a.ts::before{content:"\\25B6";font-size:9px}
a.ts:empty::after{content:attr(data-l)}
a.ts.now{background:var(--accent);color:#fff;border-color:var(--accent)}
""" + P2_CSS_END
P2_JS = P2_BEGIN + """<script src="https://www.youtube.com/iframe_api" async></script>
<script>
(function(){
  var box = document.querySelector('.player'); if (!box) return;
  var cover = box.querySelector('button'), host = document.createElement('div');
  host.className = 'yt'; host.id = 'ytp'; box.appendChild(host);
  var bar = document.createElement('div'); bar.className = 'pbar';
  bar.innerHTML = '<button type="button" data-drag="1" aria-label="Drag to move the video">&#10303; Move</button><button type="button" data-a="size">Small</button><button type="button" data-a="close">&#10005;</button>';
  box.appendChild(bar);
  var rsz = document.createElement('div'); rsz.className = 'rsz'; rsz.title = 'Drag to resize'; rsz.setAttribute('aria-label', 'Resize the video'); box.appendChild(rsz);
  var YTP = null, ready = false, loaded = box.dataset.id, pending = null;
  // 20 Sep 2026: dragIt and sizeIt now live in the boxmove block at the top of the body, so the Read aloud
  // bar, the listen box, the checklist and the "I've done it" box move and resize exactly like the video.
  var RB = window.RecipeBox || {};
  if (RB.drag) RB.drag(box, bar.querySelector('[data-drag]'), 'recipes.player.pos');
  if (RB.size) RB.size(box, rsz, 'recipes.player.w', 200);
  box.onDragStart = function(){ if (!box.classList.contains('float')) { var r = box.getBoundingClientRect(); box.classList.add('float');
    box.style.setProperty('left', r.left + 'px', 'important'); box.style.setProperty('top', Math.max(0, r.top) + 'px', 'important'); } };
  var idOf = function(h){ var m = /[?&]v=([A-Za-z0-9_-]{11})/.exec(h); return m && m[1]; };
  var tOf = function(h){ var m = /[?&]t=(\\d+)/.exec(h); return m ? +m[1] : 0; };
  document.querySelectorAll('a[href*="youtube.com/watch"]').forEach(function(a){
    if (tOf(a.getAttribute('href'))) { a.classList.add('ts'); if (!a.getAttribute('aria-label')) a.setAttribute('aria-label', 'Play from ' + (a.dataset.l || a.textContent)); }
  });
  function stopReader(){ var s = document.getElementById('rdStop'); if (s && !s.hidden) s.click(); }
  function make(){
    if (YTP || !window.YT || !YT.Player) return;
    YTP = new YT.Player('ytp', { host: 'https://www.youtube-nocookie.com', videoId: loaded,
      playerVars: { rel: 0, playsinline: 1 },
      events: { onReady: function(){ ready = true; if (pending) { var p = pending; pending = null; go(p.id, p.t); } },
                onStateChange: function(e){ if (e.data === 1) stopReader(); } } });
  }
  if (window.YT && YT.loaded) make();
  var prev = window.onYouTubeIframeAPIReady;
  window.onYouTubeIframeAPIReady = function(){ if (prev) prev(); make(); };
  function frame(id, t){   // the API never arrived: a plain embed, which may need one more tap on a phone
    host.innerHTML = '<iframe src="https://www.youtube-nocookie.com/embed/' + id + '?autoplay=1&playsinline=1&rel=0' +
      (t ? '&start=' + t : '') + '" allow="autoplay; encrypted-media; picture-in-picture" allowfullscreen></iframe>';
    loaded = id;
  }
  function go(id, t){
    var was = box.classList.contains('on');
    cover.hidden = true; box.classList.add('on');
    if (!was) { try { if (localStorage.getItem('recipes.player.pos') || localStorage.getItem('recipes.player.w')) { box.classList.add('float'); box.restoreSize(); box.restorePos(); } } catch (x) {} }
    if (ready) {
      if (loaded === id) { YTP.seekTo(t, true); YTP.playVideo(); }
      else { YTP.loadVideoById({ videoId: id, startSeconds: t }); loaded = id; }
    } else if (YTP) { pending = { id: id, t: t }; }
    else frame(id, t);
    if (!was && !box.classList.contains('float')) box.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  document.addEventListener('click', function(e){
    if (e.target.closest('.player>button')) { e.preventDefault(); go(box.dataset.id, 0); return; }
    var b = e.target.closest('.pbar button');
    if (b) {
      if (b.dataset.a === 'size') { box.classList.toggle('small'); b.textContent = box.classList.contains('small') ? 'Big' : 'Small'; }
      else { try { YTP && YTP.pauseVideo(); } catch (x) {} if (!YTP) host.innerHTML = ''; box.classList.remove('on', 'small', 'float'); ['left','top','right','bottom','width'].forEach(function(k){ box.style.removeProperty(k); }); cover.hidden = false; }
      return;
    }
    var a = e.target.closest('a[href*="youtube.com/watch"]'); if (!a) return;
    var id = idOf(a.href); if (!id) return;
    e.preventDefault();
    document.querySelectorAll('a.ts.now').forEach(function(x){ x.classList.remove('now'); });
    if (a.classList.contains('ts')) a.classList.add('now');
    go(id, tOf(a.href));
  });
  var rp = document.getElementById('rdPlay');
  if (rp) rp.addEventListener('click', function(){ try { YTP && YTP.pauseVideo(); } catch (x) {} });
})();
</script>""" + P2_END


TS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recipes_src", "timestamps.json")
TS_QUOTE = re.compile(r'(["\u201c])([^"\u201c\u201d<>]{20,}?)(["\u201d])')
TS_ADDED = re.compile(r'<a class="ts" data-add="1"[^>]*></a>')
# Recipe 10 names its four videos in a table and never linked them.
TITLE_LINKS = {"recipe-10-the-social-automation-family.html": {
    "From Google Drive to Social Media": "N4Q4iM05PPc",
    "Automate Social Media (Blotato Beginner)": "o5GsAxEX-Bk",
    "Viral Reels clone machine": "BdKqEkdvlgQ",
    "Repurpose Instagram Reels with Human Approval": "YZn6MuUIW0A"}}


def add_timestamps(page, name):
    """Put a play-from-here pill after each quote whose time tools/match_timestamps.py found. Safe to run again."""
    page = TS_ADDED.sub("", page)
    for title, vid in TITLE_LINKS.get(name, {}).items():
        page = page.replace('<td><strong>%s</strong></td>' % title,
                            '<td><a href="https://www.youtube.com/watch?v=%s"><strong>%s</strong></a></td>' % (vid, title))
    try:
        rows = json.load(io.open(TS_FILE, encoding="utf-8")).get(name, [])
    except (OSError, ValueError):
        rows = []
    if not rows:
        return page
    want = {q: (v, t) for q, v, t in rows}
    pres = [(m.start(), m.end()) for m in re.finditer(r"<pre>.*?</pre>|<script.*?</script>|<style.*?</style>", page, re.S)]
    cuts = []
    for m in TS_QUOTE.finditer(page):
        hit = want.get(m.group(2)[:60])
        if not hit or any(a <= m.start() < b for a, b in pres):
            continue
        if page.rfind("<", 0, m.start()) > page.rfind(">", 0, m.start()):   # inside a tag's attributes
            continue
        v, t = hit
        label = "%d:%02d:%02d" % (t // 3600, t // 60 % 60, t % 60) if t >= 3600 else "%d:%02d" % (t // 60, t % 60)
        cuts.append((m.end(), '<a class="ts" data-add="1" href="https://www.youtube.com/watch?v=%s&amp;t=%ds" data-l="%s" '
                              'aria-label="Play from %s"></a>' % (v, t, label, label)))
    for at, tag in reversed(cuts):
        page = page[:at] + tag + page[at:]
    return page


PROG_BEGIN, PROG_END = "<!--progress-->", "<!--/progress-->"
PROG = PROG_BEGIN + """<style>
.done{margin:32px 0 0;padding:14px;border:1px solid var(--border);border-radius:12px;background:var(--card);display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.done span{flex:1 1 100%;font-size:14px;color:var(--muted)}
.done button{font:600 14px/1 -apple-system,BlinkMacSystemFont,sans-serif;padding:10px 14px;border-radius:10px;border:1px solid var(--border);background:var(--bg);color:var(--text);cursor:pointer}
.done button.on{background:var(--accent);border-color:var(--accent);color:#0f1115}
.done .dsv{font-size:13px}
</style>
<div class="done" id="doneBox"><span>Have you tried this recipe? The coach on the Recipes home uses this.</span>
<button type="button" data-s="started">Started</button><button type="button" data-s="done">&#10003; I've done it</button>
<span class="dsv" id="doneSaved" aria-live="polite"></span></div>
<script src="../notion-sync.js" data-quiet></script>
<script>
(function(){
  var box = document.getElementById("doneBox"); if(!box) return;
  var id = (location.pathname.split("/").pop() || "").replace(/\\.html$/, ""), K = "recipeDone." + id;
  var h1 = document.querySelector("h1"), title = h1 ? h1.textContent.trim() : id;
  function get(){ try { return localStorage.getItem(K) || ""; } catch(e){ return ""; } }
  /* 20 Sep 2026, her words: "Is it not saved yet". The tick used to save in silence, so there was nothing
     on the page that said where it had got to. These three lines are read off what notion-sync.js itself
     keeps: its queue (still waiting) and its sent2 map (the version Notion already has). */
  var line = document.getElementById("doneSaved");
  function where(){
    if(!get()) return "";
    var k = "recipeprogress|" + id, q = [], sent = {};
    try { q = JSON.parse(localStorage.getItem("notionSync.queue") || "[]"); } catch(e){}
    try { sent = JSON.parse(localStorage.getItem("notionSync.sent2") || "{}"); } catch(e){}
    var out = window.NotionSync && window.NotionSync.connected();
    if(q.some(function(x){ return x.body && (x.body.app + "|" + x.body.id) === k; }))
      return out ? "Saved on this phone · waiting for Notion" : "Saved on this phone · waiting for Notion - tap Connect";
    if(sent && sent[k]) return "Saved to Notion ✓";
    return "Saved on this phone";
  }
  function said(){ if(line) line.textContent = where(); }
  function paint(){ var st = get(); box.querySelectorAll("button[data-s]").forEach(function(b){ b.classList.toggle("on", b.dataset.s === st); b.setAttribute("aria-pressed", b.dataset.s === st); }); said(); }
  box.addEventListener("click", function(e){
    var b = e.target.closest("button[data-s]"); if(!b) return;   // not the move grip, which lives in here too
    var st = get() === b.dataset.s ? "" : b.dataset.s;
    try { if(st) localStorage.setItem(K, st); else localStorage.removeItem(K); } catch(x){}
    paint();
    if(window.NotionSync){
      if(st) window.NotionSync.save("recipeprogress", id, {title: title, detail: st, when: new Date().toISOString(), data: {state: st}});
      else window.NotionSync.remove("recipeprogress", id);
    }
    said();   // the queue only grows on this click; the poll below catches it leaving
  });
  paint();
  setInterval(said, 2000);   // so "waiting for Notion" turns into "Saved to Notion" by itself
})();
</script>""" + PROG_END


def add_progress(page):
    """16 Sep 2026: "I've done this" ticks, which the recipe coach reads. Safe to run again."""
    page = re.sub(re.escape(PROG_BEGIN) + ".*?" + re.escape(PROG_END) + r"\n*", "", page, flags=re.S)
    at = page.find('<div class="foot">')
    return page if at == -1 else page[:at] + PROG + "\n" + page[at:]


SRC_BEGIN, SRC_END = "<!--sources-->", "<!--/sources-->"
VIDEOS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recipes_src", "videos.json")


def clock(sec):
    sec = int(round(sec or 0))
    return "%d:%02d:%02d" % (sec // 3600, sec // 60 % 60, sec % 60) if sec >= 3600 else "%d:%02d" % (sec // 60, sec % 60)


def add_sources(page, name):
    """16 Sep 2026, her words: "why has it not been linked all those videos in the recipes i have and the time it
    takes for it to play out". Under the Read aloud bar: how long the recording is, and every source video with its
    length. Each video link plays in the page's own player. No <p>/<li>, so the recordings still match."""
    page = re.sub(re.escape(SRC_BEGIN) + ".*?" + re.escape(SRC_END) + r"\n*", "", page, flags=re.S)
    try:
        videos = json.load(io.open(VIDEOS_FILE, encoding="utf-8"))
    except (OSError, ValueError):
        videos = {}
    body = re.sub(r"<script.*?</script>", " ", page, flags=re.S)
    ids = [v for v in dict.fromkeys(re.findall(r"youtube\.com/watch\?v=([A-Za-z0-9_-]{11})", body)) if v in videos]
    listen = ""
    try:
        dur = json.load(io.open(os.path.join(OUT, "a", name[:-5] + ".json"), encoding="utf-8")).get("dur")
        if dur:
            listen = '<div class="srow"><span class="sk">&#127911; Listen</span><span>%d min</span></div>' % max(1, round(dur / 60))
    except (OSError, ValueError):
        pass
    if not ids and not listen:
        return page
    total = sum(videos[v].get("dur") or 0 for v in ids)
    rows = "".join('<a class="svid" href="https://www.youtube.com/watch?v=%s"><span class="st">&#9654; %s</span><span class="sd">%s</span></a>'
                   % (v, html.escape(videos[v]["title"]), clock(videos[v].get("dur"))) for v in ids)
    block = (SRC_BEGIN + '<style>.sources{margin:0 0 18px;padding:10px 12px;border:1px solid var(--border);border-radius:12px;background:var(--card);display:grid;grid-template-columns:minmax(0,1fr);gap:6px;font-size:14px}.sources>*{min-width:0}'
             '.sources .srow{display:flex;justify-content:space-between;gap:10px;color:var(--muted)}.sources .sk{font-weight:600;color:var(--text)}'
             '.sources .svid{display:flex;justify-content:space-between;gap:10px;text-decoration:none;color:var(--accent)}'
             '.sources .st{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.sources .sd{flex:none;color:var(--muted);font-variant-numeric:tabular-nums}</style>'
             '<div class="sources" aria-label="Listening time and source videos">' + listen +
             ('<div class="srow"><span class="sk">Videos (%d)</span><span>%s total</span></div>' % (len(ids), clock(total)) if ids else "") +
             rows + '</div>' + SRC_END)
    at = page.find('<div class="readbar"')
    if at != -1:
        end = page.find("</div>", at) + len("</div>")
    else:
        end = page.find("</h1>") + 5
    return page[:end] + "\n" + block + page[end:]


def upgrade_player(page):
    """Swap the old one-video player for the reading-room style one. Safe to run again; refreshes the block."""
    page = page.replace(PLAYER_JS, "")
    page = re.sub(re.escape(P2_BEGIN) + ".*?" + re.escape(P2_END) + r"\n*", "", page, flags=re.S)
    page = re.sub(re.escape(P2_CSS_BEGIN) + ".*?" + re.escape(P2_CSS_END), "", page, flags=re.S)
    m = VID.search(page)
    if m and 'class="player"' not in page:   # a page whose only videos are named in a table (recipe 10)
        h1 = page.find("</h1>")
        if h1 != -1:
            vid = m.group(1)
            page = page[:h1 + 5] + (
                '\n<div class="player" data-id="%s"><button type="button" data-id="%s" aria-label="Play the video">'
                '<img src="%s" alt="" loading="lazy"><span class="play"><span>&#9654;</span></span>'
                '<span class="cap">Tap to play the first video this recipe comes from</span></button></div>\n'
                % (vid, vid, thumb(vid))) + page[h1 + 5:]
    if 'class="player"' not in page:
        return page
    page = page.replace("</style>", P2_CSS + "</style>", 1)
    return page.replace("</body>", P2_JS + "\n</body>", 1)


# ---------------- read aloud, 15 Sep 2026 ----------------
# Her words: "I need a reading, like the speak out loud for the recipes." The phone's own voice reads
# the page from the top, a paragraph at a time, highlighting where it is. Free: no recording, no API.
# Not stopped on leaving the page (her 15 Sep: play in the background).
READ_MARK = "<!--read-aloud-->"
READ_CSS = """
.readbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin:0 0 18px}
.readbar button,.readbar select{font:600 14px/1 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;border-radius:10px;border:1px solid var(--border);background:var(--card);color:var(--text);padding:10px 14px;cursor:pointer}
.readbar button.primary{background:var(--accent);border-color:var(--accent);color:#0f1115}
.readbar .rs{font-size:12px;color:var(--muted)}
.readbar button.icon{font-size:20px;line-height:1;min-width:46px;padding:8px 12px}
.reading{outline:2px solid var(--accent);outline-offset:4px;border-radius:6px}
"""
READ_BAR = ('<div class="readbar" role="group" aria-label="Read aloud">'
            '<button type="button" class="primary icon" id="rdPlay" aria-label="Read aloud" title="Read aloud">&#128266;</button>'
            '<button type="button" class="icon" id="rdStop" aria-label="Stop" title="Stop" hidden>&#9632;</button>'
            '<select id="rdRate" aria-label="Speed"><option value="0.9">Slow</option><option value="1" selected>Normal</option>'
            '<option value="1.15">Brisk</option><option value="1.3">Fast</option></select>'
            '<span class="rs" id="rdNow"></span></div>')
READ_JS = """<script>
(function(){
  /* Natural voice, her 15 Sep "Everything.": if tools/record_recipes.py made a recording for this page, and every
     line still matches, Read aloud plays that recording (keeps going with the phone locked); otherwise the phone voice. */
  var stem=(location.pathname.split('/').pop()||'').replace(/\\.html$/,''), rec=null, audio=null;
  fetch('a/'+stem+'.json').then(function(r){ return r.ok?r.json():null; }).then(function(j){
    if(!j) return; rec=j; var b=document.getElementById('rdPlay'); if(b&&!b.dataset.busy){ b.setAttribute('aria-label','Listen (natural voice)'); b.title='Listen (natural voice)'; }
  }).catch(function(){});
  var hasSS=('speechSynthesis' in window);
  var play=document.getElementById('rdPlay'), stop=document.getElementById('rdStop'), rate=document.getElementById('rdRate'), now=document.getElementById('rdNow');
  var parts=[], i=0, on=false, paused=false, voice=null;
  function pickVoice(){
    var vs=speechSynthesis.getVoices(); if(!vs.length) return null;
    var good=/Siri|Natural|Premium|Enhanced|Karen|Lee|Catherine|Daniel|Serena/i;
    var by=function(lang){ var l=vs.filter(function(v){return v.lang&&v.lang.replace('_','-').indexOf(lang)===0;}); return l.filter(function(v){return good.test(v.name);})[0]||l[0]; };
    return by('en-AU')||by('en-GB')||by('en-US')||by('en')||vs[0];
  }
  function collect(){
    var wrap=document.querySelector('.wrap'), out=[];
    wrap.querySelectorAll('h1,h2,h3,p,li,blockquote,td').forEach(function(el){
      if (el.closest('pre,.player,.readbar,.foot,.back,table td table')) return;
      if (el.tagName==='P' && el.closest('li,blockquote,td')) return;
      var t=(el.innerText||'').replace(/[\\u2B50\\u26A0\\u26D4\\u2705\\u274C]/g,'').replace(/\\s+/g,' ').trim();
      if (t.length<2) return;
      var bits=t.match(/[^.!?]+[.!?]*\\s*/g)||[t], buf='';
      bits.forEach(function(s){ if((buf+s).length>220 && buf){ out.push({el:el,text:buf}); buf=''; } buf+=s; });
      if (buf.trim()) out.push({el:el,text:buf});
    });
    return out;
  }
  function mark(el){ document.querySelectorAll('.reading').forEach(function(x){x.classList.remove('reading');}); if(el){ el.classList.add('reading'); }   /* her 16 Sep: the page no longer scrolls along; the line is only highlighted */ }
  function step(){
    if(!on||mode==='audio') return;
    if(i>=parts.length){ finish(); return; }
    var p=parts[i], u=new SpeechSynthesisUtterance(p.text);
    voice=voice||pickVoice(); if(voice){ u.voice=voice; u.lang=voice.lang; }
    u.rate=parseFloat(rate.value)||1;
    u.onend=function(){ if(!on||paused) return; i++; step(); };
    u.onerror=function(){ if(!on||paused) return; i++; step(); };
    mark(p.el); now.textContent=Math.round(i/parts.length*100)+'%';
    speechSynthesis.speak(u);
  }
  function matches(ps){ if(!rec||rec.parts.length!==ps.length) return false; for(var k=0;k<ps.length;k++){ if(rec.parts[k].t!==ps[k].text) return false; } return true; }
  function label(){ play.setAttribute('aria-label', rec?'Listen (natural voice)':'Read aloud'); delete play.dataset.busy; return '&#128266;'; }
  function finish(){ on=false; paused=false; i=0; if(hasSS) speechSynthesis.cancel(); if(audio){ audio.pause(); audio.currentTime=0; } mark(null); play.innerHTML=label(); stop.hidden=true; now.textContent=''; }
  function startAudio(){
    if(!audio){
      audio=new Audio('a/'+stem+'.mp3'); audio.preload='auto';
      audio.addEventListener('timeupdate', function(){
        var t=audio.currentTime, k=0; while(k+1<rec.parts.length && rec.parts[k+1].s<=t) k++;
        if(k!==i || !document.querySelector('.reading')){ i=k; mark(parts[k]&&parts[k].el); }
        now.textContent=Math.round(t/(rec.dur||audio.duration||1)*100)+'%';
      });
      audio.addEventListener('ended', finish);
      if('mediaSession' in navigator){
        var h=document.querySelector('h1');
        navigator.mediaSession.metadata=new MediaMetadata({title:h?h.innerText:document.title, artist:'Recipes'});
        navigator.mediaSession.setActionHandler('play', function(){ play.click(); });
        navigator.mediaSession.setActionHandler('pause', function(){ play.click(); });
        try{ navigator.mediaSession.setActionHandler('seekbackward', function(){ audio.currentTime=Math.max(0,audio.currentTime-15); });
             navigator.mediaSession.setActionHandler('seekforward', function(){ audio.currentTime=audio.currentTime+15; }); }catch(e){}
      }
    }
    audio.playbackRate=parseFloat(rate.value)||1;
    return audio.play();
  }
  var mode='';
  play.addEventListener('click', function(){
    if(!on){
      parts=collect(); i=0; on=true; paused=false; stop.hidden=false; play.textContent='\\u23F8'; play.setAttribute('aria-label','Pause'); play.dataset.busy='1';
      if(matches(parts)){ mode='audio'; startAudio().catch(function(){ mode='speech'; if(hasSS){ step(); } }); return; }
      mode='speech'; if(!hasSS){ finish(); now.textContent='Read aloud is not available on this browser'; return; }
      speechSynthesis.cancel(); step(); return;
    }
    if(!paused){ paused=true; if(mode==='audio') audio.pause(); else speechSynthesis.cancel(); play.innerHTML='&#9654;'; play.setAttribute('aria-label','Resume'); return; }
    paused=false; play.textContent='\\u23F8'; play.setAttribute('aria-label','Pause'); play.dataset.busy='1'; if(mode==='audio') audio.play(); else step();
  });
  stop.addEventListener('click', finish);
  rate.addEventListener('change', function(){ if(mode==='audio'&&audio){ audio.playbackRate=parseFloat(rate.value)||1; return; } if(on&&!paused){ speechSynthesis.cancel(); step(); } });
  if (hasSS && speechSynthesis.onvoiceschanged!==undefined) speechSynthesis.onvoiceschanged=function(){ voice=pickVoice(); };
})();
</script>"""

def add_reader(page):
    if READ_MARK in page:
        page = re.sub(r'<div class="readbar" role="group" aria-label="Read aloud">.*?</div>', READ_BAR.replace("\\", "\\\\"), page, count=1, flags=re.S)
        if ".readbar button.icon{" not in page:   # 16 Sep: icon-only buttons need their own size
            page = page.replace("</style>", ".readbar button.icon{font-size:20px;line-height:1;min-width:46px;padding:8px 12px}</style>", 1)
        b = page.find(READ_MARK)
        a = page.rfind("<script>\n(function(){", 0, b)   # the reader script sits right before the mark
        if a != -1 and b > a:   # replace an older reader script with the current one
            return page[:a] + READ_JS + page[b:]
        return page
    page = page.replace("</style>", READ_CSS + "</style>", 1)
    at = page.find('<div class="player"')
    if at != -1:
        end = page.find("</div>", at) + len("</div>")
    else:
        h1 = page.find("</h1>")
        end = h1 + 5 if h1 != -1 else page.find('<div class="wrap">') + len('<div class="wrap">')
    page = page[:end] + "\n" + READ_BAR + "\n" + page[end:]
    return page.replace("</body>", READ_JS + READ_MARK + "\n</body>", 1)

# ---------------- swipe, 15 Sep 2026 ----------------
# Her words: "everything swipe to left and right has it been done?" Swipe left on the list opens recipe 1,
# left again the next recipe, right goes back. The gesture itself lives in the site's shared swipe.js.
SWIPE_MARK = "<!--swipe-->"


CHECK_BEGIN, CHECK_END = "<!--checklist-->", "<!--/checklist-->"
CHECK = CHECK_BEGIN + """<style>
.ck{margin:14px 0 22px;padding:14px 14px 10px;border:1px solid var(--chip,#ddd);border-radius:14px;background:var(--card,#fff)}
.ck .ckh{display:flex;align-items:center;justify-content:space-between;gap:10px;flex-wrap:wrap;margin-bottom:6px;font-weight:700}
.ck .ckn{font-weight:500;font-size:13px;opacity:.75}
.ck .cksv{font-size:13px;opacity:.7;margin:0 0 4px}
.ck label{display:grid;grid-template-columns:28px minmax(0,1fr);gap:8px;align-items:start;padding:9px 0;border-top:1px solid var(--chip,#eee);cursor:pointer}
.ck input{width:22px;height:22px;margin:2px 0 0;accent-color:var(--accent,#2b6)}
.ck .cks{white-space:pre-wrap;overflow-wrap:anywhere;font-size:15px;line-height:1.45}
.ck label.done .cks{text-decoration:line-through;opacity:.55}
.ck button{all:unset;cursor:pointer;font-size:13px;padding:4px 10px;border-radius:999px;border:1px solid var(--chip,#ccc)}
</style>
<script>
(function(){   // 16-17 Sep 2026, her "Can I also have the checklist for the recipes?": the try-it steps as tick boxes
  var key = 'recipe.ticks.' + location.pathname.split('/').pop();
  function fromSection(re){   // the steps under a heading: numbered lines in its code box, else its list
    var head = [].slice.call(document.querySelectorAll('h1,h2')).filter(function(h){ return re.test(h.textContent.trim()); })[0];
    var out = [], at = head, n = head && head.nextElementSibling;
    for (; n && !/^H[12]$/.test(n.tagName); n = n.nextElementSibling) {
      if (n.tagName === 'PRE') {
        var cur = null;
        n.textContent.split('\\n').forEach(function(line){
          var m = /^\\s*(\\d+)[.)]\\s+(.*)$/.exec(line);
          if (m) { cur = { t: m[2] }; out.push(cur); }
          else if (cur && line.trim()) cur.t += '\\n' + line.trim();
        });
        at = n;
      } else if (!out.length && /^(OL|UL)$/.test(n.tagName)) {
        [].forEach.call(n.children, function(li){ out.push({ t: li.textContent.trim() }); }); at = n;
      }
    }
    return { steps: out, last: at };
  }
  var r = fromSection(/^what to try/i), steps = r.steps, last = r.last;
  if (!steps.length) {   // recipes 01-10 predate the "What to try" block: numbered step headings, else "worth taking"
    var nums = [].slice.call(document.querySelectorAll('h1,h2,h3')).filter(function(h){ return /^\\d+\\s*·/.test(h.textContent.trim()); });
    if (nums.length >= 2) {
      nums.forEach(function(h){ steps.push({ t: h.textContent.trim().replace(/^\\d+\\s*·\\s*/, '') }); });
      last = nums[0].previousElementSibling || nums[0];
    } else { r = fromSection(/worth taking/i); steps = r.steps; last = r.last; }
  }
  if (!steps.length) return;
  var saved = {}; try { saved = JSON.parse(localStorage.getItem(key) || '{}'); } catch (e) {}
  var box = document.createElement('div'); box.className = 'ck'; box.setAttribute('data-speak-skip', '');
  box.innerHTML = '<div class="ckh"><span>&#9745; Checklist <span class="ckn"></span></span><button type="button">Start again</button></div>' +
                  '<div class="cksv" aria-live="polite"></div>';
  steps.forEach(function(st, i){
    var l = document.createElement('label');
    l.innerHTML = '<input type="checkbox"><span class="cks"></span>';
    l.querySelector('.cks').textContent = st.t;
    var cb = l.querySelector('input'); cb.checked = !!saved[i]; l.classList.toggle('done', cb.checked);
    cb.addEventListener('change', function(){ saved[i] = cb.checked; l.classList.toggle('done', cb.checked);
      try { localStorage.setItem(key, JSON.stringify(saved)); } catch (e) {} count(); });
    box.appendChild(l);
  });
  function count(){ var d = steps.filter(function(_, i){ return saved[i]; }).length;
    box.querySelector('.ckn').textContent = d + ' of ' + steps.length + ' done';
    /* 20 Sep 2026, her words: "Is it not saved yet". A tick used to save in silence. These ticks are kept
       on this phone only - unlike the "I've done it" box, they never go to Notion - so say exactly that. */
    box.querySelector('.cksv').textContent = d ? '✓ Saved on this phone' : 'Nothing ticked yet'; }
  box.querySelector('button').addEventListener('click', function(){ saved = {}; try { localStorage.removeItem(key); } catch (e) {}
    [].forEach.call(box.querySelectorAll('label'), function(l){ l.querySelector('input').checked = false; l.classList.remove('done'); }); count(); });
  count();
  last.parentNode.insertBefore(box, last.nextSibling);
})();
</script>""" + CHECK_END


def add_checklist(page):
    """Idempotent: the checklist script sits just before </body>, once."""
    page = re.sub(re.escape(CHECK_BEGIN) + r"[\s\S]*?" + re.escape(CHECK_END) + r"\n*", "", page)
    head, found, tail = page.rpartition("</body>")
    return head + CHECK + "\n</body>" + tail if found else page + CHECK

def add_swipe(page, order):
    tag = '<script src="../swipe.js" data-pages="%s" defer></script>' % " ".join(order)
    if SWIPE_MARK in page:
        b = page.find(SWIPE_MARK)
        a = page.rfind('<script src="../swipe.js"', 0, b)
        return page[:a] + tag + page[b:] if a != -1 else page   # refresh the list if recipes were added
    return page.replace("</body>", tag + SWIPE_MARK + "\n</body>", 1)

TEXTSIZE_TAG = '<script src="../textsize.js"></script>'

FEEDBACK_TAG = '<script src="../feedback.js" defer></script>'

def add_feedback(page):
    """17 Sep 2026, her words: "add everything, every app, the mic button for me to give you the feedback".
    The 🎙 bubble lives in the site's shared feedback.js; it goes right after the textsize.js tag. Idempotent."""
    if "feedback.js" in page:
        return page
    i = page.find(TEXTSIZE_TAG)
    if i == -1:
        return page.replace("</body>", FEEDBACK_TAG + "\n</body>", 1)
    j = i + len(TEXTSIZE_TAG)
    return page[:j] + FEEDBACK_TAG + page[j:]

def add_textsize(page):
    """16 Sep 2026, her words: "the option to have a bolder or ... bigger fonts". The Aa button lives in the
    site's shared textsize.js. It goes right after the page's last style block, so a saved size is in place
    before the first paint. Idempotent."""
    if "textsize.js" in page:
        return page
    i = page.rfind("</style>")
    if i == -1:
        return page.replace("</body>", TEXTSIZE_TAG + "\n</body>", 1)
    j = i + len("</style>")
    return page[:j] + "\n" + TEXTSIZE_TAG + page[j:]

def illustrate_existing():
    pages = {}
    order = ["./"] + sorted(os.path.basename(f) for f in glob.glob(os.path.join(OUT, "recipe-*.html")))
    for f in sorted(glob.glob(os.path.join(OUT, "*.html"))):
        name = os.path.basename(f)
        if name == "index.html":
            continue
        s = io.open(f, encoding="utf-8").read()
        m = VID.search(s)
        if m:
            pages[name] = m.group(1)
        io.open(f, "w", encoding="utf-8", newline="\n").write(add_boxmove(add_feedback(add_textsize(add_checklist(add_swipe(add_sources(add_reader(add_progress(upgrade_player(add_timestamps(illustrate_page(s), name)))), name), order))))))
    ip = os.path.join(OUT, "index.html")
    idx = io.open(ip, encoding="utf-8").read()   # read BEFORE opening for write, or the file is emptied
    if 'id="hub"' not in idx:   # 15 Sep: the index is now the combined Recipes home, rebuilt below
        io.open(ip, "w", encoding="utf-8", newline="\n").write(add_swipe(illustrate_index(idx, pages), order))
    print("illustrated %d pages (%d with a video) + index" % (len(pages) if pages else 0, len(pages)))
    import recipes_hub   # one Recipes app for all four collections, her pick 15 Sep 2026
    recipes_hub.main()


if __name__ == "__main__":
    import sys as _sys
    if "--local" in _sys.argv:
        render_local()          # Mac: recipes_src only; the full main() would rewrite the index from 4 cards
        illustrate_existing()
    elif "--illustrate-existing" in _sys.argv:
        illustrate_existing()   # the Mac has no recipe markdown; this only adds pictures and the player
    else:
        main()
        illustrate_existing()
        copy_to_notion()
