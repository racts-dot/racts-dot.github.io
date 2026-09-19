# The website and every app — Rachel's rule book for this work

`[HUMAN 2026-09-19]` her words: *"separate - so the main rule stays as it is, but with the website and
everything I will want something separate ... rules specifically for that, separate to the digital products."*

**Scope:** everything a person opens on a phone or in a browser that is hers - this folder
(racts-dot.github.io and every app in it), the pages.dev copies (prayer-points, morning-and-evening,
creator-reading-room), stay-ledger, and the Notion relay. **Not** the digital products; their book is
`~/claude desktoi\CLAUDE.md`. The global book (`~/.claude/CLAUDE.md`) still loads first and
still wins on money, public and hard-to-undo.

## Her rules for the apps

- `[HUMAN 2026-09-17]` **EVERY APP CARRIES THE KIT: Aa text size, Read aloud, the 🎙 feedback button, swipe, and Notion.
  A NEW APP IS NOT DONE UNTIL `python status/app_kit_check.py` SHOWS IT WITH NO GAP.** Her words: "Every app I told
  you to have all those things, like to be wired into Notion and everything like that... there's nothing on the new
  apps", and "Why have it not been applied that the swipe for every app?" Her pick: "Yes, rule + nightly check".
  An app is excused from a piece only by a written reason in that script's NOT_NEEDED. Windows Task Scheduler
  **`app-kit-check`** runs it at 23:30 every night (no AI) and writes any gaps at the top of HANDOVER.md.
  Why: each piece had been added by hand to the apps that existed on the day she asked, so Priest Hood shipped with 3 of 5.

- `[HUMAN 2026-09-17]` **THE ICON SET SHE APPROVED STANDS.** Shown all eighteen at phone size on a dark
  background, her words: *"I like the thumbnail to be as the above."* An icon is replaced only by a
  full-size redraw of the SAME picture, or on her word. Her picks are read from the artifact database
  behind her tick-box page, never from a README or a summary of it - the summary was a day stale.

- `[HUMAN 2026-09-17]` **ICONS ARE DRAWN AT SOURCE, NEVER CUT OUT OF A CONTACT SHEET.** Her *"Go ahead"*
  after being shown the halo: a tile cropped from a 30-design sheet is ~175 px, so 512 is an upscale, and
  the crop carries the sheet's grey into the rounded corners. Regenerate on Vertex (gemini-3-pro-image,
  US$0.12 each through spend_gate), full bleed to the edge; a tile that comes back floating on a field is
  cut to alpha or cropped to the tile, and the result is LOOKED AT on a dark background before it ships.

- **NO LIKENESS OF A REAL PERSON AS AN ICON** - a session's call, 18 Sep 2026, said out loud not assumed:
  her notes *"Maybe just Hormozi"* and *"Maybe just Doser"* were drawn as what those apps hold (coins and
  an arrow; a flow of steps), not as faces. If she wants a face, she says so.

- `[HUMAN 2026-09-18]` **NOTHING IS UNPINNED OR MERGED ON A CLAIM OF DUPLICATION UNTIL THE CLAIM IS MEASURED.**
  Her *"as long as it is the same duplicate that we have on recipes"* was checked and failed: Hormozi
  held 202 items Recipes lacked, Workflows 69. The condition was hers; the measurement decides.

## The checks (mechanisms, no AI) - an app is not done until these say so

| Check | What it proves | Run |
|---|---|---|
| `python status/app_kit_check.py` | Aa, Read aloud, 🎙, swipe, Notion are REFERENCED | nightly 23:30, `app-kit-check` |
| **Asset sweep** | every file each live page asks for LOADS (a reference is not a load - 18 Sep: two kit scripts 404'd on a page scored 5/5) | fetch each page, request every `src`/`href`, expect 200 |
| **Corner check** | no sheet grey / white field in the four corners of any icon | read the corner pixels |
| **Served bytes** | what is live is what is on disk | md5 of the served file = md5 on disk, never a 200 alone |
| **Read the page, not the folder** | `/videos/` is 출처 찾기, a word-search inside videos, not a library | open the page before drawing for it |

## Deploying

- racts-dot.github.io: commit, push, wait for Pages, then the served-bytes check. Public - so her word first.
- The pages.dev apps deploy with wrangler **from the Mac only** (Windows wrangler is not logged in). Windows
  commits; a Mac chat runs `npx wrangler pages deploy`, on her word, and reports the URL; Windows checks the bytes.
- Never relay her "go" to another session as authorisation for something she was not shown. If a session
  needs her yes, it asks her. (18 Sep, the Mac was right to refuse.)

---

## Sales Tracker and this folder — the traps already paid for

This folder IS the live website. It publishes to https://racts-dot.github.io/

### The one rule

**There must only ever be ONE copy of this folder on this computer, and it is
this one: `~/Desktop/Sales Tracker Website`.**

- Never copy or duplicate it anywhere else — not Downloads, not Google Drive,
  not a backup folder.
- Never put it in a Drive-synced folder. Drive fights with the hidden `.git`
  record and corrupts it silently.
- To work on it from another computer, `git clone` a fresh copy. Never carry
  the folder across.

**Why:** on 9 Sep 2026 there were two copies. They drifted apart, and one held
TripShare — 1,210 lines that existed nowhere else and had never been sent up.
It was nearly deleted. The duplicate was removed the same day.

### Before you finish, always

    git add -A && git commit -m "what changed" && git push

Work sitting on this disk and not on GitHub is work that can vanish. If a push
is refused, say so plainly — do not leave it unsaid.

### What is in here

| Path | What it is |
|---|---|
| `app.html` | Sales Tracker — the resale stock/sales app |
| `tripshare/` | TripShare |
| `todo/`, `worklog/` | the other two pages |
| `index.html` | front page linking them |
| `AppsScript-Code.gs` | connects the app to Google Sheets |
| `DEPLOY-INSTRUCTIONS.txt` | how to set that connector up |

### app.html — the trap that has already broken it once

The data is baked into the page as `data-*` attributes on
`<div class=stock>` cards and `<tr class=fb>` rows. ~~There is no data file and no
generator script.~~

⛔ **CORRECTED 10 Sep 2026 BY MEASUREMENT — THE DATA FILE AND THE GENERATOR BOTH
EXIST. They are just not in this repo.** They are in Google Drive, at
`My Drive/01 BUSINESS & CREATION/Ecommerce integration/racts-tracker-backup/`:

| File | What it is |
|---|---|
| `June Sales Tracker.xlsx` | the master data — one sheet, 296 rows |
| `gen_tracker_html.py` | 70 KB. Builds the whole page and writes `Tracker_View.html` |
| `gen_stock.py`, `html2pdf.py` | build the printable stock list and its PDF |

⛔ **DO NOT REGENERATE `app.html` FROM IT. It would delete four things.** The
generator was saved 2 Aug. Everything added by hand after that is missing from
it — checked by searching both files on 10 Sep 2026:

| Feature | in `app.html` | in the generator |
|---|---|---|
| `markSoldPrompt` | yes | **no** |
| Apps Script link (`script.google.com`) | yes | **no** |
| Mark Sold button | yes | **no** |
| Test products section | yes | **no** |

So `app.html` is the newer artefact and the generator is behind it. Treat the
generator as a record of how the page was first built, not as a way to rebuild
it. Anyone who runs it and copies the result over `app.html` loses the Sheets
connection.

- **Plain search-and-replace on it is unreliable.** Attribute values contain `>`
  characters, and some cards nest blocks holding the opposite `data-sold` value,
  so naive counting double-counts #67, #111 and #114.
- **Counting brackets is not a syntax check.** On 24 Aug an edit produced
  `markSoldPrompt(''+d.num+'')`, which reads as three strings jammed together.
  The whole page died — every tab, filter and button — and the bracket check had
  passed.
- **So: load the page in a real browser and read the console before pushing.**
  That is the only check that would have caught it.
