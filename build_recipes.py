#!/usr/bin/env python3
"""Render the Sabrina recipe markdown into pages for the site.

Source of truth is the markdown in costway-scraper. This script only renders;
never edit the generated HTML by hand, or the next run silently throws the
edit away.

Run:  python build_recipes.py
"""
import io
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
    '<title>{title}</title>\n<style>{css}</style>\n</head>\n<body>\n<div class="wrap">\n'
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


def main():
    os.makedirs(OUT, exist_ok=True)
    today = datetime.date.today().isoformat()

    srcs = sorted(glob.glob(os.path.join(SRC, "RECIPE_*.md")))
    risk = os.path.join(SRC, "READ_2026-09-13_the_git_risk_and_what_i_got_wrong.md")
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


if __name__ == "__main__":
    main()
