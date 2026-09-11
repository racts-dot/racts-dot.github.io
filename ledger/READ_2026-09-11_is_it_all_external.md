# Is everything external? — 11 September 2026

## Almost. Two things live only on this Mac, and one of them matters.

I checked every piece of today's work against what is actually on GitHub.

| The thing | Where it also lives | Safe if the Mac dies? |
|---|---|---|
| The ledger page people open | GitHub, and served from there | **Yes** |
| The loader that fills the spreadsheet | GitHub | **Yes** |
| The rules note about the builder | GitHub | **Yes** |
| The 111 items themselves | your live Google Sheet, and Google Drive | **Yes** |
| The original June spreadsheet | Google Drive | **Yes** |
| The private app on claude.ai | claude.ai | **Yes** |
| **Two write-ups from this afternoon** | nowhere | **No** |
| **The spreadsheet robot's key** | nowhere, on purpose | **No, and that is correct** |

---

## The two write-ups

They are sitting in your Sales Tracker Website folder, saved to disk but never
sent up. One command fixes it:

    cd ~/"Sales Tracker Website" && git add -A && git commit -m "Ledger notes" && git pull --rebase && git push

---

## The key, and why it is deliberate

To read your spreadsheet I made a small pass for the robot account and put it in
a hidden folder on this Mac. It is not on GitHub and it must never be. A pass
that lives in a code folder is a pass anyone who sees that folder can use — that
is exactly the fault I found on your old tracker page this morning.

**Nothing is lost if the Mac dies.** A fresh one can be made from your Google
account in about ten seconds. It is a key, not a record.

---

## One other thing I noticed

**Your Mac is five changes behind the website.** Another chat pushed work up and
this folder has not caught up. The command above collects those on its way past.

---

## Recap

Everything that matters from today is off this Mac — the page, the loader, the
figures and the original spreadsheet. Two write-ups from this afternoon are not,
and one command sends them. The robot's key stays local on purpose and can be
remade in seconds.
