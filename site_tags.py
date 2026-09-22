"""Keep what was added to a page ON THE SITE when a builder rewrites it from its source.

Measured 23 Sep 2026 (Mac, session 46a766bd): a run of publish_marketing_pages.py would have silently
dropped kit pieces added straight to the site pages and never carried back to printables - the icon
links, pull.js, hearsel.js, marks.js and kit-dock.js on /hormozi/, marks.js and the dock on /recipes/.
Every one of them is something she asked for; a rebuild must not take any of them away.

carry(new, old) returns the new page plus every <script src> and icon/manifest <link> the old page had
and the new one lacks - matched by FILE NAME, so "/textsize.js" and "../textsize.js" count as the same
file and nothing is loaded twice. Links go before </head>, scripts before </body>. The caller prints
what was carried, so nothing is added silently either.
"""
import re

SCRIPT = re.compile(r'<script\b[^>]*\bsrc="([^"]+)"[^>]*>\s*</script>', re.I)
LINK = re.compile(r'<link\b[^>]*\brel="(?:icon|apple-touch-icon|manifest|shortcut icon)"[^>]*\bhref="([^"]+)"[^>]*>', re.I)


def _name(url):
    return url.split("?")[0].split("#")[0].rstrip("/").rsplit("/", 1)[-1].lower()


def carry(new, old):
    carried = []
    have_s = {_name(m.group(1)) for m in SCRIPT.finditer(new)}
    have_l = {_name(m.group(1)) for m in LINK.finditer(new)}
    add_s = [m.group(0) for m in SCRIPT.finditer(old) if _name(m.group(1)) not in have_s]
    add_l = [m.group(0) for m in LINK.finditer(old) if _name(m.group(1)) not in have_l]
    # one of each, in the old page's order
    seen, uniq = set(), []
    for t in add_s:
        n = _name(SCRIPT.search(t).group(1))
        if n not in seen:
            seen.add(n); uniq.append(t)
    add_s = uniq
    if add_l:
        block = "\n".join(add_l) + "\n"
        i = new.lower().find("</head>")
        new = new[:i] + block + new[i:] if i >= 0 else block + new
        carried += [_name(LINK.search(t).group(1)) for t in add_l]
    if add_s:
        block = "<!-- kept from the site page (site_tags.carry) -->\n" + "\n".join(add_s) + "\n"
        i = new.lower().rfind("</body>")
        new = new[:i] + block + new[i:] if i >= 0 else new + block
        carried += [_name(SCRIPT.search(t).group(1)) for t in add_s]
    return new, carried
