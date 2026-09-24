# -*- coding: utf-8 -*-
"""Stage the shop's PDFs + page thumbnails for Care Pages (Cloudflare R2), and write catalog.json.
Input: a mapping json [{id,title,files:[{path,name,pages}]}] (paths relative to claude desktoi).
Output (D:/carepages_r2/stage): pdf/<id>/<name>, thumb/<id>/<fileidx>/<n>.jpg, catalog.json
    python build_stage.py mapped.json
"""
import json, os, shutil, sys, pymupdf as fz
SRC = r"C:\Users\soyan\claude desktoi"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stage")
m = json.load(open(sys.argv[1], encoding="utf-8"))
cat_path = os.path.join(OUT, "catalog.json")
cat = json.load(open(cat_path, encoding="utf-8")) if os.path.exists(cat_path) else {"products": []}
have = {p["id"] for p in cat["products"]}
for prod in m:
    if prod["id"] in have: continue
    entry = {"id": prod["id"], "title": prod["title"], "files": []}
    for fi, f in enumerate(prod["files"]):
        src = os.path.join(SRC, f["path"])
        d = fz.open(src)
        pdir = os.path.join(OUT, "pdf", str(prod["id"])); os.makedirs(pdir, exist_ok=True)
        shutil.copy2(src, os.path.join(pdir, f["name"]))
        tdir = os.path.join(OUT, "thumb", str(prod["id"]), str(fi)); os.makedirs(tdir, exist_ok=True)
        for n, pg in enumerate(d):
            zoom = 170 / pg.rect.width
            pg.get_pixmap(matrix=fz.Matrix(zoom, zoom)).save(os.path.join(tdir, f"{n+1}.jpg"), jpg_quality=62)
        entry["files"].append({"name": f["name"], "pages": len(d),
                               "w": round(d[0].rect.width), "h": round(d[0].rect.height)})
        d.close()
    cat["products"].append(entry)
    json.dump(cat, open(cat_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(prod["id"], len(entry["files"]), "files", flush=True)
print("done", len(cat["products"]), "products")
