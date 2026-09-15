#!/usr/bin/env python3
"""Find where each quoted line in recipes 01-10 is said in its video, so the page can play from there.

Her words, 16 Sep 2026: "Can you do the timestamp as well as the videos ... just as the creators of reading room."
Input: a folder of Notion transcript pages (<video_id>.md) whose cues look like [\\[01:30\\]](https://www.youtube.com/watch?v=ID&t=90s).
Output: recipes_src/timestamps.json  {page: [[quote_start, video_id, seconds], ...]}
A quote counts as found only when 6 of its words in a row appear, in order, in the transcript. Cues are
30-second chunks, so a time can be up to 30 s before the line; that is the same granularity the reading room uses.
No AI, no cost. build_recipes.add_timestamps() applies the file to the pages.

  python3 tools/match_timestamps.py <transcripts_dir>
"""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGES = {
    "recipe-01-ai-social-media-manager.html": ["XPl6IKDADkU"],
    "recipe-02-seven-claude-commands.html": ["rabGqnyd_Zw"],
    "recipe-03-cowork-what-you-dont-use.html": ["-q_wgmmD0e0"],
    "recipe-04-the-grader-pattern.html": ["PakM11AJAlE"],
    "recipe-05-the-audience-playbook.html": ["8gqAd-sRyIQ"],
    "recipe-06-she-switched-away-from-claude.html": ["TES0N3m6jkM"],
    "recipe-07-microsoft-copilot.html": ["rFtpXLlzzPg"],
    "recipe-08-her-whole-tool-stack.html": ["cH0Pw3Dgpmc"],
    "recipe-09-plan-mode-and-quality-gates.html": ["fYX6hHC9FhQ"],
    "recipe-10-the-social-automation-family.html": ["N4Q4iM05PPc", "o5GsAxEX-Bk", "BdKqEkdvlgQ", "YZn6MuUIW0A"],
}
CUE = re.compile(r"\[\\\[(\d{1,2}(?::\d{2}){1,2})\\\]\]\(https?://[^)]*\)")
QUOTE = re.compile(r'(["“])([^"“”<>]{20,}?)(["”])')
N = 6


def words(s):
    return re.findall(r"[a-z0-9]+", s.lower().replace("’", "'").replace("'", ""))


def secs(t):
    p = [int(x) for x in t.split(":")]
    return p[0] * 3600 + p[1] * 60 + p[2] if len(p) == 3 else p[0] * 60 + p[1]


def stream(md):
    ws, at = [], []
    parts = CUE.split(md)          # text, time, text, time, text ...
    t = 0
    for k, chunk in enumerate(parts):
        if k % 2 == 1:
            t = secs(chunk); continue
        for w in words(re.sub(r"\[[^\]]*\]\([^)]*\)|<[^>]+>", " ", chunk)):
            ws.append(w); at.append(t)
    return ws, at


def find(q, ws, at):
    qw = words(q)
    if len(qw) < N:
        return None
    index = {}
    for i in range(len(ws) - N + 1):
        index.setdefault(tuple(ws[i:i + N]), i)
    for off in range(0, len(qw) - N + 1):
        i = index.get(tuple(qw[off:off + N]))
        if i is not None:
            return at[i]
    return None


def main():
    src = pathlib.Path(sys.argv[1])
    out, report = {}, []
    for page, vids in PAGES.items():
        html = (ROOT / "recipes" / page).read_text(encoding="utf-8")
        body = re.sub(r"<pre>.*?</pre>|<script.*?</script>|<style.*?</style>", " ", html, flags=re.S)
        streams = {}
        for v in vids:
            f = src / (v + ".md")
            if f.exists():
                ws, at = stream(f.read_text(encoding="utf-8"))
                if at:
                    streams[v] = (ws, at)
        rows, seen, total = [], set(), 0
        for m in QUOTE.finditer(body):
            q = m.group(2)
            if len(words(q)) < N or q in seen:
                continue
            seen.add(q); total += 1
            for v, (ws, at) in streams.items():
                t = find(q, ws, at)
                if t is not None:
                    rows.append([q[:60], v, t]); break
        out[page] = rows
        report.append("%-48s quotes %3d  timed %3d" % (page, total, len(rows)))
    (ROOT / "recipes_src" / "timestamps.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n".join(report))


if __name__ == "__main__":
    main()
