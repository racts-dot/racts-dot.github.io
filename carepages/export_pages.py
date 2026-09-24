# -*- coding: utf-8 -*-
"""Export the care-kit page specs (costway-scraper/caregiver_generator.py) to pages.json
for the Care Pages picker. Re-run after any change to the generator:
    python export_pages.py
"""
import inspect, json, os, sys
SRC = os.path.join(os.path.expanduser("~"), "costway-scraper")
sys.path.insert(0, SRC)
import caregiver_generator as G, caregiver_kits as K
pages = {}
for key, fn in G.P.items():
    cv = inspect.getclosurevars(fn).nonlocals
    pages[key] = dict(title=cv["title"], note=cv["note"],
                      blocks=[{k: v for k, v in b.items() if k not in ("ex", "fill")} for b in cv["blocks"]])
kits = [dict(key=k, title=v["title"], moment=v["moment"], pages=v["pages"]) for k, v in K.KITS.items()]
kits.append(dict(key="all", title="Whole care binder", moment="Every page from all the kits", pages=list(G.P)))
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pages.json")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    json.dump(dict(source="costway-scraper/caregiver_generator.py", pages=pages, kits=kits), f, ensure_ascii=False, indent=1)
print(len(pages), "pages,", sum(len(p["blocks"]) for p in pages.values()), "sections,", len(kits), "kits ->", out)
