#!/usr/bin/env python3
"""Record every Hormozi, Doser and Prompt card in Recipes in the natural voice.

Her words 23 Sep 2026: "i have the read aloud but i want the recorded good quality read", and her pick
"All 527 cards" on a question that priced it at "at most about US$12.50, paid once". The phone voice the
panel had is the one she does not want; the recipe PAGES already had recordings (record_recipes.py),
the cards did not.

Same voice and route as record_recipes.py: Chirp3-HD en-AU Aoede, gcloud token, no key. The API's own
MP3 is 32 kbps mono, so it is saved as it comes - re-encoding at 64k (what record_recipes does after
joining lines) doubles the bytes and adds nothing. One request per card: the longest card is ~1,600
characters, under the API's 5,000-byte limit, so nothing is joined.

Output: recipes/a/c/<src>/<key>.mp3, src = hormozi | doser | prompts, key = the card's own key (a
prompt's key is its place in the list). recipes_hub.py marks each card that has one, and only those
get a Listen button. Skips cards already recorded, so a stopped run resumes where it stopped.

The text read is built by speech() below from the same fields the panel shows. If a card's text
changes, delete its mp3 and run again.

  python3 tools/record_cards.py --price     # count characters and price it, sends nothing
  python3 tools/record_cards.py --limit 3   # record three, to listen to first
  python3 tools/record_cards.py             # the rest
"""
import argparse, concurrent.futures, html, json, pathlib, re, subprocess, sys, tempfile, threading

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from record_recipes import synth, token, RATE   # same voice, same retries, same price

ROOT = pathlib.Path(__file__).resolve().parent.parent / "recipes"
OUT = ROOT / "a" / "c"
FILES = {"hormozi": "cards-hormozi.json", "doser": "cards-doser.json", "prompts": "cards-prompts.json",
         "molly": "cards-molly.json"}   # 23 Sep 2026, her "record the natural voice for molly's cards", ~US$1.01
WORKERS = 16   # her "double it", 23 Sep 2026
CAP_USD = 14.25   # she approved US$14.20 for all 527 (23 Sep 2026); the run stops before a card that would pass this
# (--cap sets it per run: her yes for the 15 Molly cards was ~US$1.01, so that run went with --cap 1.10)
LIMIT_BYTES = 4800   # the API refuses more than 5,000 bytes of text in one request


def end(s):
    s = (s or "").strip()
    return s if not s or s[-1] in ".!?\"'" else s + "."


def molly_speech(c):
    """A Molly Keyser card (recipes_molly.py): the title, then the section as the panel shows it. A table is read
    row by row, each cell after its column name; link text and struck-out words are read like any other words."""
    def clean(x):
        return html.unescape(re.sub(r"<[^>]+>", "", x)).strip()

    def table(m):
        heads = [clean(x) for x in re.findall(r"<th>(.*?)</th>", m.group(0), re.S)]
        rows = []
        for r in re.findall(r"<tbody>(.*?)</tbody>", m.group(0), re.S)[0].split("</tr>"):
            cells = [clean(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", r, re.S)]
            if cells:
                rows.append(" ".join("%s: %s." % (heads[i] if i < len(heads) else "", v.rstrip("."))
                                     for i, v in enumerate(cells) if v))
        return " " + " ".join(rows) + " "
    h = re.sub(r'<div class="tw">.*?</div>', table, c.get("html") or "", flags=re.S)
    h = re.sub(r"</(p|li|ul|ol)>", ". ", h)
    t = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))
    t = re.sub(r"(\s*\.\s*){2,}", ". ", t).replace(" .", ".").strip()
    return (c["title"].rstrip(".") + ". " + t).strip()


def pieces(text):
    """Text cut at sentence ends into requests the API will take. Only a Molly card is ever this long."""
    out, buf = [], ""
    for s in re.findall(r"[^.!?]+[.!?]*\s*", text) or [text]:
        if buf and len((buf + s).encode("utf-8")) > LIMIT_BYTES:
            out.append(buf.strip()); buf = ""
        buf += s
    if buf.strip():
        out.append(buf.strip())
    assert all(len(x.encode("utf-8")) <= LIMIT_BYTES for x in out), "a single sentence is over the limit"
    return out


def speech(src, c):
    """The words spoken for one card, in the order the panel draws them."""
    if src == "molly":
        return molly_speech(c)
    if src == "prompts":
        return "%s The prompt: %s" % (end(c.get("n")), end(c.get("p")))
    out = [end(c.get("title"))]
    if c.get("gets"):
        out.append("What it can get you: " + end(c["gets"]))
    if c.get("claim"):
        out.append("In his words: " + end(c["claim"]))
    steps = c.get("steps") or []
    if steps:
        out.append("How to do it.")
        for i, v in enumerate(steps, 1):
            out.append("Step %d. %s" % (i, end(v.get("do"))))
            if v.get("q"):
                out.append("He says: " + end(v["q"]))
    if c.get("warn"):
        out.append("Watch out: " + end(c["warn"]))
    return " ".join(out)


def cards():
    for src, f in FILES.items():
        d = json.loads((ROOT / f).read_text(encoding="utf-8"))
        items = enumerate(d) if isinstance(d, list) else d.items()
        for key, c in items:
            yield src, str(key), c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--price", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--only", help="one source: hormozi, doser, prompts or molly")
    ap.add_argument("--cap", type=float, default=CAP_USD, help="stop before this many US$ at list price")
    a = ap.parse_args()
    cap = a.cap
    todo = [(s, k, speech(s, c)) for s, k, c in cards() if not (OUT / s / (k + ".mp3")).exists()
            and (not a.only or s == a.only)]
    total = sum(len(t) for _, _, t in todo)
    print("%d cards to record, %d characters, at most US$%.2f at Google's list price"
          % (len(todo), total, total * RATE), flush=True)
    if a.price:
        return 0
    if a.limit:
        todo = todo[:a.limit]
    # 23 Sep 2026: one card at a time took ~30 s each (four hours for 524), so WORKERS run at once. The
    # money check reserves a card's characters under the lock BEFORE its request goes out, so the cap
    # still holds exactly however many are in flight.
    tok = token(); state = {"spent": 0, "made": 0, "stop": False}; lock = threading.Lock()

    def one(job):
        src, key, text = job
        with lock:
            if state["stop"] or (state["spent"] + len(text)) * RATE > cap:
                state["stop"] = True
                return
            state["spent"] += len(text)
        mp3 = OUT / src / (key + ".mp3")
        mp3.parent.mkdir(parents=True, exist_ok=True)
        parts = pieces(text)
        if len(parts) == 1:
            audio = synth(text, tok)
        else:   # joined the way record_recipes.py joins its lines: ffmpeg concat, no re-encode needed for one voice
            with tempfile.TemporaryDirectory() as d:
                d = pathlib.Path(d); files = []
                for i, x in enumerate(parts):
                    f = d / ("%02d.mp3" % i); f.write_bytes(synth(x, tok)); files.append(f)
                lst = d / "list.txt"; lst.write_text("".join("file '%s'\n" % f.as_posix() for f in files), encoding="utf-8")
                out = d / "all.mp3"
                r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)],
                                   capture_output=True, text=True)
                if r.returncode:
                    raise RuntimeError("ffmpeg failed on %s/%s: %s" % (src, key, r.stderr[:300]))
                audio = out.read_bytes()
        if not audio or len(audio) < 1000:
            raise RuntimeError("empty audio for %s/%s" % (src, key))
        tmp = mp3.with_suffix(".part")
        tmp.write_bytes(audio)
        tmp.replace(mp3)
        with lock:
            state["made"] += 1
            if state["made"] % 25 == 0 or state["made"] == len(todo):
                print("%d/%d  running US$%.2f" % (state["made"], len(todo), state["spent"] * RATE), flush=True)

    with concurrent.futures.ThreadPoolExecutor(WORKERS) as pool:
        for f in [pool.submit(one, j) for j in todo]:
            f.result()
    if state["stop"]:
        print("STOPPED: the next card would pass the US$%.2f she approved" % cap, flush=True)
    spent, made = state["spent"], state["made"]
    print("made %d | %d characters | US$%.2f at list price" % (made, spent, spent * RATE), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
