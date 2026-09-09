# Sales Tracker Website — read before touching anything here

This folder IS the live website. It publishes to https://racts-dot.github.io/

## The one rule

**There must only ever be ONE copy of this folder on this computer, and it is
this one: `C:\Users\soyan\Desktop\Sales Tracker Website`.**

- Never copy or duplicate it anywhere else — not Downloads, not Google Drive,
  not a backup folder.
- Never put it in a Drive-synced folder. Drive fights with the hidden `.git`
  record and corrupts it silently.
- To work on it from another computer, `git clone` a fresh copy. Never carry
  the folder across.

**Why:** on 9 Sep 2026 there were two copies. They drifted apart, and one held
TripShare — 1,210 lines that existed nowhere else and had never been sent up.
It was nearly deleted. The duplicate was removed the same day.

## Before you finish, always

    git add -A && git commit -m "what changed" && git push

Work sitting on this disk and not on GitHub is work that can vanish. If a push
is refused, say so plainly — do not leave it unsaid.

## What is in here

| Path | What it is |
|---|---|
| `app.html` | Sales Tracker — the resale stock/sales app |
| `tripshare/` | TripShare |
| `todo/`, `worklog/` | the other two pages |
| `index.html` | front page linking them |
| `AppsScript-Code.gs` | connects the app to Google Sheets |
| `DEPLOY-INSTRUCTIONS.txt` | how to set that connector up |

## app.html — the trap that has already broken it once

The data is baked into the page as `data-*` attributes on
`<div class=stock>` cards and `<tr class=fb>` rows. There is no data file and no
generator script.

- **Plain search-and-replace on it is unreliable.** Attribute values contain `>`
  characters, and some cards nest blocks holding the opposite `data-sold` value,
  so naive counting double-counts #67, #111 and #114.
- **Counting brackets is not a syntax check.** On 24 Aug an edit produced
  `markSoldPrompt(''+d.num+'')`, which reads as three strings jammed together.
  The whole page died — every tab, filter and button — and the bracket check had
  passed.
- **So: load the page in a real browser and read the console before pushing.**
  That is the only check that would have caught it.
