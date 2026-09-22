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
import hashlib
import pathlib
import re
import sys

SCRIPT = re.compile(r'<script\b[^>]*\bsrc="([^"]+)"[^>]*>\s*</script>', re.I)
LINK = re.compile(r'<link\b[^>]*\brel="(?:icon|apple-touch-icon|manifest|shortcut icon)"[^>]*\bhref="([^"]+)"[^>]*>', re.I)


def _name(url):
    return url.split("?")[0].split("#")[0].rstrip("/").rsplit("/", 1)[-1].lower()


ATTR = re.compile(r'([\w:-]+)(?:\s*=\s*"([^"]*)")?')
ANY_TAG = re.compile(r"<(script|link)\b[^>]*>", re.I)


def _attrs(tag):
    return {k.lower(): v for k, v in ATTR.findall(re.sub(r"^<\w+|/?>$", "", tag))}


def _key(tag):
    """'script:marks.js' / 'link:favicon.png' - what the tag loads, however it is spelled. None = not kit."""
    a = _attrs(tag)
    if tag[1:7].lower() == "script" and a.get("src"):
        if "://" in a["src"] and "racts-dot.github.io" not in a["src"]:
            return None   # a third party (YouTube) is the source page's business
        return "script:" + _name(a["src"])
    if tag[1:5].lower() == "link" and a.get("rel", "").lower() in ("icon", "apple-touch-icon", "manifest", "shortcut icon"):
        return "link:" + _name(a.get("href", ""))
    return None


def kit(html):
    out = {}
    for m in ANY_TAG.finditer(html):
        k = _key(m.group(0))
        if k and k not in out:
            out[k] = m.group(0)
    return out


def _local(url):
    """A bare file name: a copy in the page's own folder, not the site's one shared copy."""
    return bool(url) and "/" not in url.split("?", 1)[0]


def _merge(new_tag, old_tag):
    """The rebuilt tag plus whatever only the site copy carried: an attribute (data-quiet, data-icon-only,
    sizes) or the ?v= cache-bust stamp. Measured 23 Sep 2026: the first carry() kept every tag but took
    notion-sync.js?v=20260920b back to a bare name on three pages, so phones kept yesterday's copy."""
    na, oa = _attrs(new_tag), _attrs(old_tag)
    tag = new_tag
    u = "src" if "src" in na else "href"
    if _local(na.get(u, "")) and not _local(oa.get(u, "")):
        tag = tag.replace(f'{u}="{na[u]}"', f'{u}="{oa[u]}"', 1)   # keep the site's shared copy
        na = _attrs(tag)
    if u in na and "?" not in na[u] and "?" in oa.get(u, ""):
        tag = tag.replace(f'{u}="{na[u]}"', f'{u}="{na[u]}?{oa[u].split("?", 1)[1]}"', 1)
    extra = "".join(f' {k}="{v}"' if f'{k}="' in old_tag else f" {k}" for k, v in oa.items() if k not in na)
    if extra:
        tag = re.sub(r"\s*/?>$", lambda m: extra + m.group(0), tag, count=1)
    return tag


def carry(new, old):
    carried = []
    have_new = kit(new)
    for k, old_tag in kit(old).items():
        if k in have_new:
            merged = _merge(have_new[k], old_tag)
            if merged != have_new[k]:
                new = new.replace(have_new[k], merged, 1)
                carried.append(k.split(":", 1)[1] + " (attrs)")
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


# 23 Sep 2026: the refusal. Snapshot before a publish; afterwards, if any kit tag, attribute, ?v= stamp,
# icon link or site icon file is gone, put every snapshotted file back and stop with the list.
SITE_OWNED = re.compile(r"(^|/)(favicon[^/]*\.png|icon-\d+\.png|apple-touch-icon[^/]*\.png|[^/]+\.js)$")


def _h(b):
    return hashlib.sha1(b).hexdigest()[:10]


class Guard:
    """Snapshot before a publish, refuse after it if anything the site had is gone."""

    def __init__(self, site, pages, folders):
        self.site = pathlib.Path(site)
        self.pages = pages
        self.saved = {}
        for rel in pages:
            p = self.site / rel
            if p.exists():
                self.saved[rel] = p.read_bytes()
        for folder in folders:
            for p in (self.site / folder).glob("*"):
                rel = p.relative_to(self.site).as_posix()
                if p.is_file() and SITE_OWNED.search(rel):
                    self.saved[rel] = p.read_bytes()

    def lost(self):
        out = []
        for rel, before in self.saved.items():
            p = self.site / rel
            if not p.exists():
                out.append(f"{rel}: file deleted")
            elif rel in self.pages:
                old, new = kit(before.decode("utf-8")), kit(p.read_text(encoding="utf-8"))
                for k, tag in old.items():
                    if k not in new:
                        out.append(f"{rel}: {tag}")
                        continue
                    oa, na = _attrs(tag), _attrs(new[k])
                    for a in oa:
                        if a not in na:
                            out.append(f"{rel}: {k} lost its {a} attribute")
                    for u in ("src", "href") if k.startswith("script:") else ():
                        if not _local(oa.get(u, "")) and _local(na.get(u, "")):
                            out.append(f"{rel}: {k} moved from the shared {oa[u]} to a local copy")
                    for u in ("src", "href"):
                        if "?" in oa.get(u, "") and "?" not in na.get(u, ""):
                            out.append(f"{rel}: {k} lost its {oa[u].split('?', 1)[1]}")
            elif p.read_bytes() != before:
                out.append(f"{rel}: site copy {_h(before)} replaced by {_h(p.read_bytes())}")
        return out

    def check(self):
        bad = self.lost()
        if not bad:
            print(f"kit guard: nothing lost ({len(self.saved)} pages and site-owned files checked)")
            return
        for rel, data in self.saved.items():
            (self.site / rel).write_bytes(data)
        sys.exit("REFUSED - this run would have dropped site-side kit pieces, so every checked file was "
                 "put back as it was:\n  " + "\n  ".join(bad))
