"""Molly Keyser's playbook as cards for the Recipes app.

23 Sep 2026, her pick from a question box: "Molly into Recipes - Molly's Etsy playbook becomes cards in Recipes,
like Doser's, nothing lost." The playbook is one long page (racts-dot/testing,
other-projects/molly_keyser/PLAYBOOK.md, last changed 7017e71 on 14 Sep 2026); a copy sits beside this file in
recipes_src/molly_keyser_playbook.md. Each "## " section becomes one card, and the card's panel shows that
section in full: every line, table, link and struck-out correction, in the playbook's own words.

No wording is changed. The card face adds only a short label ("Part 1", or "Playbook" for the sections
outside the eight parts) and the section's first sentence. recipes_hub.py reads recipes/cards-molly.json
when the source copy is missing, so a rebuild without it keeps the cards rather than emptying the tab.

Run it on its own to check the cards against the source, word by word and link by link: python recipes_molly.py
"""
import html
import json
import pathlib
import re
import sys

SITE = pathlib.Path(__file__).resolve().parent
SOURCE = SITE / "recipes_src" / "molly_keyser_playbook.md"


def inline(s):
    """One line of the playbook's markdown to HTML. Text is escaped first; only the marks it uses are turned
    into tags: `code`, **bold**, *italic*, ~~struck~~ and [text](link)."""
    out, pos = [], 0
    for m in re.finditer(r"`([^`]+)`", s):   # code first, so nothing inside it is read as a mark
        out.append(("t", s[pos:m.start()]))
        out.append(("c", m.group(1)))
        pos = m.end()
    out.append(("t", s[pos:]))
    res = []
    for kind, part in out:
        if kind == "c":
            res.append("<code>" + html.escape(part, quote=False) + "</code>")
            continue
        t = html.escape(part, quote=False)
        t = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)",
                   lambda m: '<a href="%s" target="_blank" rel="noopener">%s</a>' % (html.escape(m.group(2)), m.group(1)), t)
        t = re.sub(r"~~(.+?)~~", r"<s>\1</s>", t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"(?<![*\w])\*(?!\s)(.+?)(?<!\s)\*(?![*\w])", r"<i>\1</i>", t)
        res.append(t)
    return "".join(res)


def plain(s):
    """The same line with its marks taken off, for the card face and the search."""
    s = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", s)
    s = re.sub(r"~~.+?~~", "", s)
    return re.sub(r"\s+", " ", s.replace("**", "").replace("`", "").replace("*", "")).strip()


def block_html(lines):
    """A section's lines to HTML: paragraphs, bullet and numbered lists (a line indented under an item carries
    on that item), and tables. HTML comments (the playbook's VIDEOS START / END markers) are left out, as a
    reader never saw them."""
    out, i = [], 0
    lines = [l for l in lines if not re.match(r"^\s*<!--.*-->\s*$", l)]
    while i < len(lines):
        l = lines[i]
        if not l.strip():
            i += 1
            continue
        if l.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            head, body = rows[0], [r for r in rows[1:] if not all(re.fullmatch(r":?-+:?", c) for c in r)]
            out.append('<div class="tw"><table><thead><tr>' + "".join("<th>%s</th>" % inline(c) for c in head) +
                       "</tr></thead><tbody>" + "".join("<tr>" + "".join(
                           # each cell carries its column name, shown above it when a phone stacks the row
                           '<td data-h="%s">%s</td>' % (html.escape(plain(head[j]) if j < len(head) else ""), inline(c))
                           for j, c in enumerate(r)) + "</tr>" for r in body) + "</tbody></table></div>")
            continue
        m = re.match(r"^(-|\d+\.) ", l)
        if m:
            tag = "ul" if m.group(1) == "-" else "ol"
            items = []
            while i < len(lines):
                l = lines[i]
                m2 = re.match(r"^(-|\d+\.) (.*)$", l)
                if m2 and (m2.group(1) == "-") == (tag == "ul"):
                    items.append(m2.group(2))
                elif l.startswith(" ") and l.strip() and items:
                    items[-1] += " " + l.strip()
                else:
                    break
                i += 1
            out.append("<%s>%s</%s>" % (tag, "".join("<li>%s</li>" % inline(t) for t in items), tag))
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not lines[i].startswith("|") and not re.match(r"^(-|\d+\.) ", lines[i]):
            para.append(lines[i].strip())
            i += 1
        out.append("<p>%s</p>" % inline(" ".join(para)))
    return "".join(out)


def sections(text):
    """(title, lines) for the opening (the "# " title and what comes before the first "## ") and each "## "."""
    secs, title, cur = [], None, []
    for l in text.splitlines():
        if l.startswith("## "):
            secs.append((title, cur))
            title, cur = l[3:].strip(), []
        elif l.startswith("# ") and title is None and not cur:
            title = l[2:].strip()
        else:
            cur.append(l)
    secs.append((title, cur))
    return [(t, ls) for t, ls in secs if t]


def build(text):
    """{key: card}. Keys are m01, m02 ... in the playbook's order, so a reader's place survives a rebuild
    as long as the sections keep their order."""
    cards = {}
    for n, (title, lines) in enumerate(sections(text), 1):
        words = plain(" ".join(re.sub(r"^(-|\d+\.) ", "", l.strip()) for l in lines
                               if l.strip() and not l.startswith("|") and not l.strip().startswith("<!--")))
        first = re.split(r"(?<=[.!?])\s", words, maxsplit=1)[0] if words else ""
        m = re.match(r"^(Part \d+)\.\s*(.*)$", title)
        cards["m%02d" % n] = {"title": title, "topic": m.group(1) if m else "Playbook", "gets": first,
                              "html": block_html(lines), "n": n}
    return cards


def load():
    """(cards, where they came from): the source copy when it is here, else the copy the page already reads."""
    if SOURCE.exists():
        return build(SOURCE.read_text(encoding="utf-8")), "recipes_src/molly_keyser_playbook.md"
    kept = SITE / "recipes" / "cards-molly.json"
    if kept.exists():
        return json.loads(kept.read_text(encoding="utf-8")), "our own copy, the source is not here"
    return {}, "nothing: no source and no copy"


def _tokens(s):
    return re.findall(r"\w+|[$%€£]", s.lower())


def check(text, cards):
    """Section by section, in order: the source's words (marks, list numbers and table rules taken off, struck-out
    text kept, since it is still on the page) against the words of that card's title and HTML. Returns
    [(card key, missing words in order)] - any word the converter dropped, even one that appears elsewhere."""
    import difflib
    probs = []
    for (title, lines), (key, c) in zip(sections(text), cards.items()):
        src = []
        for l in lines:
            if l.strip().startswith("<!--") or re.fullmatch(r"\|?[\s:|-]+\|?", l.strip() or "x"):
                continue
            l = re.sub(r"^\s*(-|\d+\.) ", " ", l)
            l = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", l)
            src.append(l.replace("|", " "))
        a = _tokens(title + " " + " ".join(src))
        b = _tokens(c["title"] + " " + html.unescape(re.sub(r"<[^>]+>", " ", c["html"])))
        miss = []
        for op, i1, i2, j1, j2 in difflib.SequenceMatcher(None, a, b, autojunk=False).get_opcodes():
            if op in ("delete", "replace"):
                miss += a[i1:i2]
        # every link the section had, pointing where it pointed
        want = re.findall(r"\]\((https?://[^)\s]+)\)", "\n".join(lines))
        got = [html.unescape(u) for u in re.findall(r'<a href="([^"]+)"', c["html"])]
        miss += ["link:" + u for u in want if u not in got]
        if miss or len(cards) != len(sections(text)):
            probs.append((key, miss))
    return probs


if __name__ == "__main__":
    text = SOURCE.read_text(encoding="utf-8")
    cards = build(text)
    probs = check(text, cards)
    print("%d cards from %d source lines; cards with words missing: %d" % (len(cards), len(text.splitlines()), len(probs)))
    for k, miss in probs:
        print("  %s MISSING: %s" % (k, " ".join(miss[:40])))
    sys.exit(1 if probs else 0)
