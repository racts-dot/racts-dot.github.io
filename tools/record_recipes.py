#!/usr/bin/env python3
"""Record the recipes in a natural voice, so Read aloud keeps going with the phone locked.

Her pick 15 Sep 2026, the voice question: "Everything." (option quoted as ~US$1.50 once for the recipes).
The phone's own voice stops when the screen locks or the app goes to the background; a real audio file does not.

Input: recipes/parts_for_recording.json - for each page, the exact lines the page's own Read aloud
collect() makes, taken from the pages in a browser, so the recording and the highlighting line up.
Output: recipes/a/<page>.mp3 and recipes/a/<page>.json {"parts": [{"t": text, "s": start seconds}], "dur": s}.
The page checks every line still matches before it uses the recording; if a page changed, it falls back
to the phone voice rather than highlight the wrong line.

Google Cloud Text-to-Speech, Chirp3-HD en-AU Aoede (same voice as the Reading Room). gcloud token, no key.
Price used: US$30 per 1M characters (Google's list price). Skips pages already recorded.

  python3 tools/record_recipes.py --only recipe-03-cowork-what-you-dont-use.html
  python3 tools/record_recipes.py
"""
import argparse, base64, json, pathlib, subprocess, sys, tempfile, time, urllib.error, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent / "recipes"
OUT = ROOT / "a"
URL = "https://texttospeech.googleapis.com/v1/text:synthesize"
PROJECT = "gen-lang-client-0626840434"
VOICE = "en-AU-Chirp3-HD-Aoede"
RATE = 30.0 / 1_000_000


def token():
    return subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True).stdout.strip()


def synth(text, tok):
    body = json.dumps({"input": {"text": text}, "voice": {"languageCode": "en-AU", "name": VOICE},
                       "audioConfig": {"audioEncoding": "MP3", "speakingRate": 1.0}}).encode()
    for attempt in range(5):
        req = urllib.request.Request(URL, data=body, headers={"Authorization": "Bearer " + tok,
                                     "Content-Type": "application/json", "x-goog-user-project": PROJECT})
        try:
            with urllib.request.urlopen(req, timeout=300) as r:
                return base64.b64decode(json.load(r)["audioContent"])
        except urllib.error.HTTPError as e:
            msg = e.read().decode("utf-8", "replace")[:300]
            if e.code == 401 and attempt < 4:   # 16 Sep: the gcloud token expires after an hour, mid-run
                tok = token(); continue
            if e.code in (429, 500, 503) and attempt < 4:
                time.sleep(5 * (attempt + 1)); continue
            sys.exit("HTTP %d: %s" % (e.code, msg))
        except (urllib.error.URLError, ConnectionError, TimeoutError) as e:   # 15 Sep: a connection reset killed a run
            if attempt < 4:
                time.sleep(5 * (attempt + 1)); continue
            sys.exit("network: %s" % e)


def duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True).stdout.strip()
    return float(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--only")
    a = ap.parse_args()
    pages = json.loads((ROOT / "parts_for_recording.json").read_text(encoding="utf-8"))
    if a.only:
        pages = {a.only: pages[a.only]}
    OUT.mkdir(exist_ok=True)
    tok = token(); chars = made = 0
    for name, lines in pages.items():
        stem = name[:-5]
        if (OUT / (stem + ".mp3")).exists():
            continue
        with tempfile.TemporaryDirectory() as tmp:
            tmp = pathlib.Path(tmp); files = []; marks = []; t = 0.0
            for k, text in enumerate(lines):
                f = tmp / ("%03d.mp3" % k)
                f.write_bytes(synth(text.strip(), tok))
                chars += len(text)
                marks.append({"t": text, "s": round(t, 2)})
                t += duration(f); files.append(f)
            lst = tmp / "list.txt"
            lst.write_text("".join("file '%s'\n" % f for f in files))
            mp3 = OUT / (stem + ".mp3")
            r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                                "-c:a", "libmp3lame", "-b:a", "64k", "-ac", "1", str(mp3)], capture_output=True, text=True)
            if r.returncode:
                sys.exit("ffmpeg failed on %s: %s" % (name, r.stderr[:300]))
        (OUT / (stem + ".json")).write_text(json.dumps({"parts": marks, "dur": round(t, 2)}, ensure_ascii=False))
        made += 1
        print("%s  %d lines  %.0fs  %.0f KB  running US$%.2f" % (name, len(lines), t, mp3.stat().st_size / 1024,
              chars * RATE), flush=True)
    print("made %d | %d characters | ESTIMATE US$%.2f at Google's list price" % (made, chars, chars * RATE))


if __name__ == "__main__":
    main()
