"""The videos box on the Hormozi and Doser recipe cards, like the one on the recipe pages.

Her ask, 16 Sep 2026: "No video for the two creators other than sabrina's".
Each card gets: listening time, every source video with its length, ▶ moments (his words,
each step, watch out) that play in a small player on the page instead of leaving for YouTube.
Lengths come from ~/yt-transcripts/metadata.csv (read when the page is published).
The box is built from div/span/a/button only, and the page's own Listen reads the card's data,
not the page, so nothing in it is read aloud. Idempotent: a page already carrying MARK is left alone.
"""
import csv
import json
import pathlib
import re
import subprocess

MARK = "<!--videobox-->"
META = pathlib.Path.home() / "yt-transcripts" / "metadata.csv"

CSS = """<style>
.vbox{border:1px solid var(--line);border-radius:12px;padding:10px 12px;display:grid;gap:8px;min-width:0}
.vbox .vhead{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:13px;color:var(--muted);font-weight:600}
.vbox .vrow{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 10px;align-items:baseline;min-width:0}
.vbox .vrow+.vrow{border-top:1px dashed var(--line);padding-top:8px}
.vbox .vtitle{min-width:0;overflow-wrap:anywhere;font-size:14px}
.vbox .vlen{font-variant-numeric:tabular-nums;color:var(--muted);font-size:13px}
.vbox .vmoments{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:6px}
.vbox a.vp{display:inline-flex;align-items:center;gap:4px;padding:3px 9px;border-radius:999px;border:1px solid var(--line);
  color:var(--marker);text-decoration:none;font-size:13px;font-weight:600;white-space:nowrap}
.vbox a.vp:hover{border-color:var(--marker)}
#vdock{position:fixed;z-index:70;top:8px;right:8px;width:min(420px,calc(100vw - 16px));background:var(--card);
  border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow);overflow:hidden}
#vdock .vdbar{display:flex;align-items:center;gap:8px;padding:6px 8px 6px 12px;font-size:13px;color:var(--muted)}
#vdock .vdname{flex:1;min-width:0;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
#vdock button{all:unset;cursor:pointer;padding:4px 10px;border-radius:8px;font-size:18px;line-height:1;color:var(--ink)}
#vdock button:focus-visible{outline:2px solid var(--marker)}
#vdock .vdframe{position:relative;aspect-ratio:16/9}
#vdock .vdframe>div,#vdock .vdframe iframe{position:absolute;inset:0;width:100%;height:100%}
</style>"""

JS = r"""<script>
(function(){
var VDUR = __VDUR__, RECDUR = __RECDUR__, WORDS = __WORDS__;
function esc(x){ return String(x==null?'':x).replace(/[&<>"']/g, function(ch){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]; }); }
function mm(t){ t=Math.round(+t||0); var h=Math.floor(t/3600), m=Math.floor(t%3600/60), s=t%60;
  return (h? h+':'+String(m).padStart(2,'0') : m)+':'+String(s).padStart(2,'0'); }
window.vbox = function(c){
  var total = 0; c.src.forEach(function(v){ total += VDUR[v.id]||0; });
  var rec = RECDUR[c.key], listen = rec ? Math.max(1, Math.round(rec/60)) + ' min listen'
    : '~' + Math.max(1, Math.round((WORDS[c.key]||0)/160)) + ' min listen';
  var first = [];
  if (c.claim_t != null) first.push([+c.claim_t, 'His words']);
  c.steps.forEach(function(s,i){ if (s.q && s.t != null) first.push([+s.t, 'Step '+(i+1)]); });
  if (c.warn && c.warn_t != null) first.push([+c.warn_t, 'Watch out']);
  first.sort(function(a,b){ return a[0]-b[0]; });
  var rows = c.src.map(function(v,k){
    var pills = '<a class="vp" href="https://www.youtube.com/watch?v='+v.id+'" data-v="'+v.id+'" data-s="0" aria-label="Play from the start">▶ Start</a>';
    if (k === 0) pills += first.map(function(p){ return '<a class="vp" href="https://www.youtube.com/watch?v='+v.id+'&t='+p[0]+'s" data-v="'+v.id+'" data-s="'+p[0]+'" aria-label="Play '+p[1]+' at '+mm(p[0])+'">▶ '+mm(p[0])+' '+p[1]+'</a>'; }).join('');
    return '<div class="vrow"><span class="vtitle">'+esc(v.title)+'</span><span class="vlen">'+(VDUR[v.id]? mm(VDUR[v.id]) : '')+'</span><div class="vmoments">'+pills+'</div></div>';
  }).join('');
  return '<div class="vbox"><div class="vhead"><span>🎧 '+listen+'</span><span>▶ Videos ('+c.src.length+')'+(total? ' · '+mm(total)+' total':'')+'</span></div>'+rows+'</div>';
};
var dock, yt, ytReady = false, pending = null;
function makeDock(){
  dock = document.createElement('div'); dock.id = 'vdock'; dock.hidden = true;
  dock.innerHTML = '<div class="vdbar"><span class="vdname"></span><button type="button" aria-label="Close video">✕</button></div><div class="vdframe"><div id="vdplayer"></div></div>';
  document.body.appendChild(dock);
  dock.querySelector('button').addEventListener('click', function(){ try { yt && yt.pauseVideo(); } catch(e){} dock.hidden = true; });
  var s = document.createElement('script'); s.src = 'https://www.youtube.com/iframe_api'; document.head.appendChild(s);
  var prev = window.onYouTubeIframeAPIReady;
  window.onYouTubeIframeAPIReady = function(){ prev && prev();
    yt = new YT.Player('vdplayer', { playerVars:{ playsinline:1, rel:0 }, events:{ onReady:function(){ ytReady = true; if (pending){ play(pending[0], pending[1]); pending = null; } } } });
  };
}
function play(id, s){
  if (!ytReady){ pending = [id, s]; return; }
  yt.loadVideoById({ videoId:id, startSeconds:s });
}
document.addEventListener('click', function(e){
  var a = e.target.closest('a.vp, a.t'); if (!a || e.metaKey || e.ctrlKey || e.shiftKey) return;
  var m = a.href.match(/[?&]v=([\w-]{11})(?:&t=(\d+)s)?/); if (!m) return;
  e.preventDefault();
  if (!dock) makeDock();
  var card = a.closest('.card'), title = '';
  var row = a.closest('.vrow'); if (row) title = row.querySelector('.vtitle').textContent;
  else if (card){ var cite = card.querySelector('.cite span'); title = cite ? cite.textContent : ''; }
  dock.querySelector('.vdname').textContent = (m[2] ? mm(m[2]) + ' · ' : '') + title;
  dock.hidden = false;
  try { speechSynthesis.pause(); } catch(err){}
  play(m[1], +(m[2]||0));
}, true);
})();
</script>"""


def durations(ids):
    out = {}
    with open(META, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["video_id"] in ids and r.get("duration_sec"):
                out[r["video_id"]] = int(float(r["duration_sec"]))
    return out


def recorded(audio_dir):
    out = {}
    for mp3 in sorted(pathlib.Path(audio_dir).glob("*.mp3")):
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp3)],
                           capture_output=True, text=True)
        try:
            out[mp3.stem] = round(float(r.stdout.strip()))
        except ValueError:
            pass
    return out


def script_for(c):
    """The same lines the page's own Listen reads (scriptFor in the page), for the listening time."""
    parts = [c["title"] + ".", "What it can get you: " + c["gets"]]
    if c.get("fit") == "no":
        parts.append("Not for your shop. " + c.get("why", ""))
    elif c.get("fit") == "later":
        parts.append("Later, once you have sales. " + c.get("why", ""))
    for k, lab in (("shop", "For your Etsy shop: "), ("watch", "Watch for: "), ("rule", "Rules: ")):
        if c.get(k):
            parts.append(lab + c[k])
    parts += ["In his words: " + c["claim"] + ".", "How to do it."]
    parts += ["Step %d. %s" % (i + 1, s["do"]) for i, s in enumerate(c["steps"])]
    if c.get("warn"):
        parts.append("Watch out. In his words: " + c["warn"] + ".")
    if c.get("checks"):
        parts.append("Ask yourself. " + " ".join(c["checks"]))
    return parts


def add_videos(html, label, audio_dir=None):
    if MARK in html:
        return html
    m = re.search(r'<script id="data" type="application/json">(.*?)</script>', html, re.S)
    data = json.loads(m.group(1))
    ids = {v["id"] for t in data["topics"] for c in t["cards"] for v in c["src"]}
    vdur = durations(ids)
    missing = ids - set(vdur)
    if missing:
        print(f"  {label}: no length for {len(missing)} of {len(ids)} videos")
    rec = recorded(audio_dir) if audio_dir else {}

    # the box goes between the buttons and "His words"
    new, n = re.subn(r'(\n\s*<div>\s*<div class="label">His words</div>)', r"\n      ${vbox(c)}\1", html, count=1)
    if n != 1:
        raise SystemExit(f"{label}: could not find where the videos box goes")
    # the old "Also in N more videos" list is now inside the box
    old = "${others?`<details class=\"src\"><summary>Also in ${c.src.length-1} more video${c.src.length>2?'s':''}</summary><ul>${others}</ul></details>`:''}"
    if old not in new:
        raise SystemExit(f"{label}: could not find the old sources list")
    new = new.replace(old, "", 1)
    words = {c["key"]: len(" ".join(script_for(c)).split()) for t in data["topics"] for c in t["cards"]}
    js = JS.replace("__WORDS__", json.dumps(words, separators=(",", ":"))).replace("__VDUR__", json.dumps(vdur, separators=(",", ":"))).replace("__RECDUR__", json.dumps(rec, separators=(",", ":")))
    # vbox() must exist before the page first calls render(), so it goes before the page's own script
    i = new.find("<script id=\"data\"")
    new = new[:i] + MARK + "\n" + CSS + "\n" + js + "\n" + new[i:]
    print(f"  {label}: videos box on {sum(len(t['cards']) for t in data['topics'])} cards, {len(vdur)} lengths, {len(rec)} recordings")
    return new
