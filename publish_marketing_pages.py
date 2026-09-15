"""Copy the four marketing pages from racts-dot/printables into this site.

Her pick, 15 Sep 2026: "Public only". The pages used to be claude.ai artifacts, which belong to
one Claude account and cannot reach Notion. Here they open on any phone and any account.

    /cookbook/   Sabrina's Prompt Cookbook       printables sabrina_cookbook/
    /videos/     video search (출처 찾기)          printables apps/video_search_site/public/
    /hormozi/    Hormozi Marketing Recipes       printables hormozi_cookbook/   + Notion
    /workflows/  Doser AI Marketing Workflows    printables doser_cookbook/     + Notion

The printables repo stays the source. Rebuild a page there, then run this again:

    python3 publish_marketing_pages.py            # reads origin/main of ~/printables

Files are read with `git show origin/main:...`, so a sparse or stale checkout still works.
"""
import json
import pathlib
import re
import subprocess
import sys

SITE = pathlib.Path(__file__).resolve().parent
PRINTABLES = pathlib.Path.home() / "printables"
REF = "origin/main"

NOTION_DBS = {  # the database each page's rows land in, under Notion "Apps → Notion"
    "hormozi": "https://app.notion.com/p/c6733655743f423f94711f600792d0ee",
    "workflows": "https://app.notion.com/p/20c2e1e5f76440dd83e8bf0eb411863e",
}

# What the claude.ai artifact frame supplied around a page that has no <head> of its own.
ARTIFACT_HEAD = (
    '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
    '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
    "<style>:root{color-scheme:light}body{margin:0;font:14px/1.5 system-ui,-apple-system,"
    "'Segoe UI',sans-serif;background:#faf9f7}img{max-width:100%}[hidden]{display:none!important}</style>\n"
    "</head>\n<body>\n"
)


def git_bytes(path):
    return subprocess.run(
        ["git", "-C", str(PRINTABLES), "show", f"{REF}:{path}"], check=True, capture_output=True
    ).stdout


def git_list(folder):
    out = subprocess.run(
        ["git", "-C", str(PRINTABLES), "ls-tree", "-r", "--name-only", REF, folder],
        check=True, capture_output=True, text=True,
    ).stdout
    return [line for line in out.splitlines() if line]


def write(rel, data):
    dest = SITE / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, str):
        data = data.encode("utf-8")
    dest.write_bytes(data)
    print(f"  {rel}  {len(data):,} bytes")


def replace_once(html, old, new, label):
    if old not in html:
        sys.exit(f"STOP: {label}: expected text not found - the source page changed, check it by hand")
    return html.replace(old, new)


def as_document(html):
    """Artifact pages are fragments; give them the head the artifact frame used to add."""
    if html.lstrip().lower().startswith("<!doctype"):
        return html
    return ARTIFACT_HEAD + html + "\n</body>\n</html>\n"


SHOP_WORDS = re.compile(r"46 listings|her 46|zero sales|no sales|her shop|your shop|Etsy shop|her listings|her current", re.I)


def strip_shop(html, label):
    """Her pick, 15 Sep 2026: "Remove shop details first". The private pages judged every recipe
    against her own shop (46 listings, no sales). The public copies keep the recipes and drop that layer."""
    open_tag = '<script id="data" type="application/json">'
    i = html.index(open_tag) + len(open_tag)
    j = html.index("</script>", i)
    data = json.loads(html[i:j])
    data["has_fit"] = False
    for topic in data["topics"]:
        for card in topic["cards"]:
            for field in ("shop", "why", "watch", "fit", "start"):
                if field in card:
                    card[field] = "" if isinstance(card[field], str) else False
    blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = html[:i] + blob + html[j:]
    html = re.sub(r"<p><b>Fit for your shop\.</b>.*?</p>", "", html, flags=re.S)
    html = html.replace("A shop with no sales yet should begin at stop 1; the", "Begin at stop 1; the")
    left = [m.group(0) for m in SHOP_WORDS.finditer(html)]
    print(f"  {label}: shop words left after stripping: {len(left)} {sorted(set(left))}")
    return html


def add_notion(html, app):
    html = replace_once(html, "your Yes/No answers are saved in this browser only.",
                        "your Yes/No answers are saved in this browser and copied to your Notion once this "
                        "device is connected (the Connect to Notion button).", f"{app} storage sentence")
    tags = (
        '\n<script src="/notion-sync.js"></script>\n'
        f'<script src="/marketing-notion.js" data-app="{app}" data-notion="{NOTION_DBS[app]}"></script>\n'
    )
    if "</body>" in html:
        return html.replace("</body>", tags + "</body>", 1)
    return html + tags


def add_swipe(html, attrs, label):
    """Her 15 Sep 2026: "everything swipe to left and right". The gesture lives in this site's swipe.js,
    so the printables source (also deployed to Cloudflare, which has no swipe.js) stays untouched."""
    head, found, tail = html.rpartition("</body>")
    if not found:
        sys.exit(f"STOP: {label}: no </body> - the source page changed, check it by hand")
    return f'{head}<script src="../swipe.js" {attrs} defer></script>\n</body>{tail}'


def use_site_textsize(html, label):
    """16 Sep 2026: the Aa text size button. The printables pages load a local textsize.js (they also deploy to
    Cloudflare); here they load the site's one shared copy instead, so there is only one file to keep level."""
    if 'src="textsize.js"' not in html and 'src="/textsize.js"' not in html:
        sys.exit(f"STOP: {label}: no textsize.js tag - the source page changed, check it by hand")
    return html.replace('<script src="textsize.js"></script>', '<script src="/textsize.js"></script>')


def main():
    subprocess.run(["git", "-C", str(PRINTABLES), "fetch", "-q", "origin"], check=True)

    print("cookbook/")
    for path in git_list("sabrina_cookbook"):
        name = path.split("/", 1)[1]
        if name == "index.html":
            page = use_site_textsize(git_bytes(path).decode("utf-8"), "cookbook")
            # the source loads its own speak.js (Cloudflare copy); this site's one lives at the root
            page = page.replace('<script src="speak.js" defer></script>', '<script src="../speak.js" defer></script>')
            write("cookbook/index.html", add_swipe(page, 'data-select="#tool"', "cookbook swipe"))
        elif name in {"favicon.png", "icon-180.png", "icon-192.png", "icon-512.png", "og.png"}:
            write(f"cookbook/{name}", git_bytes(path))
    manifest = git_bytes("sabrina_cookbook/manifest.webmanifest").decode("utf-8")
    write("cookbook/manifest.webmanifest",
          replace_once(manifest, '"start_url": "/"', '"start_url": "./"', "cookbook manifest"))

    print("videos/")
    for path in git_list("apps/video_search_site/public"):
        name = path.rsplit("/", 1)[1]
        if name == "index.html":
            write("videos/index.html", add_swipe(use_site_textsize(git_bytes(path).decode("utf-8"), "videos"),
                                                 'data-chips="#chips .chip" data-input="#q"', "videos swipe"))
        elif name not in {"_headers", "textsize.js"}:  # _headers is Cloudflare-only; textsize.js: the site's root copy
            write(f"videos/{name}", git_bytes(path))

    print("hormozi/")
    html = git_bytes("hormozi_cookbook/index.html").decode("utf-8")
    html = replace_once(html, "https://claude.ai/code/artifact/d1047394-8a8b-4c1c-9b2d-0fe740848361",
                        "https://racts-dot.github.io/hormozi/", "hormozi artifact link")
    # The relay queues the row and sends it within seconds; "Saved" would claim more than is known.
    html = replace_once(html, "Saved: <a href=\"${url}\" target=\"_blank\" rel=\"noopener\">open in Notion</a>",
                        "Sending to Notion: <a href=\"${url}\" target=\"_blank\" rel=\"noopener\">open the list</a>",
                        "hormozi saved message")
    write("hormozi/index.html", add_notion(as_document(strip_shop(use_site_textsize(html, "hormozi"), "hormozi")), "hormozi"))
    for path in git_list("hormozi_cookbook/audio"):
        write("hormozi/audio/" + path.rsplit("/", 1)[1], git_bytes(path))

    print("workflows/")
    html = git_bytes("doser_cookbook/index.html").decode("utf-8")
    write("workflows/index.html", add_notion(as_document(strip_shop(use_site_textsize(html, "workflows"), "workflows")), "workflows"))

    import recipes_hub   # 15 Sep: the combined Recipes home, and its "All recipes" bar on these pages
    recipes_hub.main()


if __name__ == "__main__":
    main()
