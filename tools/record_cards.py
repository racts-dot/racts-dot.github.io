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
import argparse, concurrent.futures, json, pathlib, sys, threading

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from record_recipes import synth, token, RATE   # same voice, same retries, same price

ROOT = pathlib.Path(__file__).resolve().parent.parent / "recipes"
OUT = ROOT / "a" / "c"
FILES = {"hormozi": "cards-hormozi.json", "doser": "cards-doser.json", "prompts": "cards-prompts.json"}
WORKERS = 16   # her "double it", 23 Sep 2026
CAP_USD = 14.25   # she approved US$14.20 for all 527 (23 Sep 2026); the run stops before a card that would pass this


def end(s):
    s = (s or "").strip()
    return s if not s or s[-1] in ".!?\"'" else s + "."


def speech(src, c):
    """The words spoken for one card, in the order the panel draws them."""
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
    a = ap.parse_args()
    todo = [(s, k, speech(s, c)) for s, k, c in cards() if not (OUT / s / (k + ".mp3")).exists()]
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
            if state["stop"] or (state["spent"] + len(text)) * RATE > CAP_USD:
                state["stop"] = True
                return
            state["spent"] += len(text)
        mp3 = OUT / src / (key + ".mp3")
        mp3.parent.mkdir(parents=True, exist_ok=True)
        audio = synth(text, tok)
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
        print("STOPPED: the next card would pass the US$%.2f she approved" % CAP_USD, flush=True)
    spent, made = state["spent"], state["made"]
    print("made %d | %d characters | US$%.2f at list price" % (made, spent, spent * RATE), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
