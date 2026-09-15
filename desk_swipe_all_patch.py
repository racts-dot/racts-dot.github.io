#!/usr/bin/env python3
"""Desk: the whole page slides with your finger on EVERY page, and a swipe may start on a card or button.
Her words, 15 Sep 2026: "I was expecting the whole page moves" (on the Desk). Before: only the five tab pages
slid, and a swipe that began on a button was ignored - most of Today is buttons and cards.
More pages slide to the next More page; the five tab pages still slide among themselves.
    python3 desk_swipe_all_patch.py ~/website/desk/index.html <home-notes>/secretary/secretary_app.html
"""
import pathlib, sys
MARK = "/* swipe on every page, 15 Sep */"
for f in sys.argv[1:]:
    p = pathlib.Path(f).expanduser(); s = p.read_text(encoding="utf-8")
    if MARK in s:
        print("already", f); continue
    reps = [
        ('  const NAV = PAGES.filter(p=>p.nav).map(p=>p.id);\n',
         '  ' + MARK + '\n  const NAV = PAGES.filter(p=>p.nav).map(p=>p.id);\n'
         '  const MORE = PAGES.filter(p=>!p.nav).map(p=>p.id);\n'
         '  const groupOf = id => NAV.indexOf(id) >= 0 ? NAV : MORE;\n'
         '  const sideways = el => { for(; el && el !== document.body; el = el.parentElement){\n'
         '    if(el.scrollWidth > el.clientWidth + 2){ const ox = getComputedStyle(el).overflowX; if(ox === "auto" || ox === "scroll") return true; } } return false; };\n'),
        ('    if(NAV.indexOf(page) < 0) return;\n    if(e.target.closest("audio,input,textarea,select,button,.p-bar")) return;\n',
         '    if(!document.getElementById("p-" + page)) return;\n    if(e.target.closest("audio,input,textarea,select,.p-bar") || sideways(e.target)) return;\n'),
        ('      const t = NAV[NAV.indexOf(page) + dir];\n',
         '      const G = groupOf(page), t = G[G.indexOf(page) + dir];\n'),
    ]
    for old, new in reps:
        if s.count(old) != 1:
            sys.exit(f"{f}: expected once: {old[:50]!r} found {s.count(old)}")
        s = s.replace(old, new, 1)
    p.write_text(s, encoding="utf-8"); print("patched", f)
