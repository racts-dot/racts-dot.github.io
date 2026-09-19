#!/usr/bin/env python3
"""Record Daily Chapter's NLT chapters in the natural voice, section by section.

Her 16 Sep 2026 yes: "A" (whole Bible in NLT, quoted ~US$130) "but can it be divided into seperate code sections".
Input: ~/daily_voice/nlt/<Book>_<n>.json from daily_nlt_text.py.
Output (private, on this Mac): ~/daily_voice/audio/<Book>_<n>.mp3 + .json {"ref","sections":[{"title","s"}],"dur"}
so the app can list the sections and jump to one. Google Chirp3-HD en-AU Aoede, US$30 per 1M characters.
HARD STOP: the running spend (kept in spent.json, across runs) never passes US$130.
Loops: records whatever text has arrived, waits, and carries on while the text fetch is still running.
"""
import base64, json, pathlib, subprocess, sys, tempfile, time, urllib.error, urllib.request

HOME = pathlib.Path.home() / "daily_voice"
SRC, OUT = HOME / "nlt", HOME / "audio"
SPENT = HOME / "spent.json"
URL = "https://texttospeech.googleapis.com/v1/text:synthesize"
PROJECT = "gen-lang-client-0626840434"
VOICE = "en-AU-Chirp3-HD-Aoede"
RATE = 30.0 / 1_000_000
CAP = 155.0   # [HUMAN 2026-09-19] raised from 130 on her pick "Raise it to US$155" - 130 stopped at ~1027 of 1189
OUT.mkdir(parents=True, exist_ok=True)


class SynthRefused(Exception):
    """Google refused this piece. Skip the chapter, keep the run alive."""


def token():
    return subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True).stdout.strip()


def synth(text, tok):
    body = json.dumps({"input": {"text": text}, "voice": {"languageCode": "en-AU", "name": VOICE},
                       "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.0}}).encode()
    for attempt in range(6):
        req = urllib.request.Request(URL, data=body, headers={"Authorization": "Bearer " + tok[0],
                                     "Content-Type": "application/json", "x-goog-user-project": PROJECT})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return base64.b64decode(json.load(r)["audioContent"])
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:300]
            if e.code == 401 and attempt < 5:
                tok[0] = token(); continue
            if e.code in (429, 500, 503) and attempt < 5:
                time.sleep(10 * (attempt + 1)); continue
            # 19 Sep 2026: a 400 used to sys.exit and stop everything. One bad chapter
            # now fails loudly and is skipped; the rest of the Bible still records.
            raise SynthRefused("HTTP %d: %s" % (e.code, msg))
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:
            if attempt < 5:
                time.sleep(10 * (attempt + 1)); continue
            sys.exit("network: %s" % e)


def sentences(text):
    """Google refuses one very long sentence (Exodus 35's lists), so a long one is cut at ; : or , into shorter ones."""
    out = []
    for s in __import__("re").findall(r"[^.!?]+[.!?”’\"]*\s*", text) or [text]:
        while len(s) > 200:
            cut = max(s.rfind(ch, 0, 200) for ch in ";:,")
            if cut < 60:
                cut = s.rfind(" ", 0, 200)
            if cut < 60:
                cut = 200          # 19 Sep 2026: was `break`, which handed Google the whole
                                   # long sentence and got HTTP 400, killing the entire run.
            out.append(s[:cut].rstrip(" ,;:") + ". ")
            s = s[cut + 1:].lstrip()
        out.append(s)
    return out


def pieces(text, limit=4000):
    out, buf = [], ""
    for s in sentences(text):
        if len((buf + s).encode()) > limit and buf:
            out.append(buf); buf = ""
        buf += s
    if buf.strip():
        out.append(buf)
    return out


def duration(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout.strip())


spent = json.loads(SPENT.read_text()) if SPENT.exists() else {"chars": 0}
tok = [token()]
idle = 0
while True:
    todo = [f for f in sorted(SRC.glob("*.json")) if f.name != "requests.json" and not (OUT / (f.stem + ".json")).exists()]
    if not todo:
        if len([f for f in SRC.glob("*_*.json")]) >= 1189:   # every chapter of the Bible has text and a recording
            print("all 1189 chapters recorded"); break
        idle += 1; time.sleep(300); continue
    idle = 0
    for f in todo:
        if __import__("shutil").disk_usage(str(HOME)).free < 2 * 1024**3:   # 16 Sep: the Mac had 2.9 GB free
            sys.exit("STOP: less than 2 GB free on the Mac - clear space, then run again (it carries on where it stopped)")
        ch = json.loads(f.read_text())
        if (spent["chars"] + ch["chars"]) * RATE > CAP:
            sys.exit(f"STOP: next chapter would pass US${CAP:.0f} (spent US${spent['chars'] * RATE:.2f})")
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp); files = []; marks = []; t = 0.0
            try:
                for i, sec in enumerate(ch["sections"]):
                    marks.append({"title": sec["title"], "s": round(t, 2)})
                    spoken = (sec["title"] + ". " if sec["title"] else "") + sec["text"]
                    for j, p in enumerate(pieces(spoken)):
                        a = tmp / f"{i:03d}_{j:02d}.mp3"
                        a.write_bytes(synth(p.strip(), tok))
                        spent["chars"] += len(p)
                        t += duration(a); files.append(a)
            except SynthRefused as e:
                SPENT.write_text(json.dumps(spent))
                print(f"SKIPPED {ch['ref']}: {e}", flush=True)
                (OUT / (f.stem + ".refused")).write_text(str(e))
                continue
            SPENT.write_text(json.dumps(spent))
            lst = tmp / "list.txt"
            lst.write_text("".join(f"file '{a}'\n" for a in files))
            mp3 = OUT / (f.stem + ".mp3")
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                                "-c:a", "libmp3lame", "-b:a", "48k", "-ac", "1", str(mp3)], capture_output=True, text=True)
            if r.returncode:
                sys.exit("ffmpeg failed on %s: %s" % (f.stem, r.stderr[:300]))
        (OUT / (f.stem + ".json")).write_text(json.dumps({"ref": ch["ref"], "sections": marks, "dur": round(t, 2)}, ensure_ascii=False))
        print(f"{ch['ref']}: {len(marks)} sections {t/60:.1f} min {mp3.stat().st_size//1024} KB  spent US${spent['chars'] * RATE:.2f}", flush=True)
