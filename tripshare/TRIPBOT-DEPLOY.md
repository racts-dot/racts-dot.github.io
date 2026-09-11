# Switching the TripShare planner on

**Right now it is OFF, and the page behaves exactly as it did before.**
Nothing below costs anything until the last step.

---

## What you are building, in one sentence

A little Google program that holds the AI key, so the public web page can ask
it questions without ever holding the key itself.

```
  someone's browser                    a Google Apps Script            OpenAI
  (tripshare page)                     (only you can see inside)
  "5 days in Kyoto"   ──────────────▶  checks the daily limit  ─────▶  writes
                                        adds the secret key            the plan
  a list of items     ◀──────────────  passes the answer back  ◀─────
```

**Why it has to work this way:** the TripShare page is on a public website.
Anything written into that page can be read by anyone who visits it. So the key
cannot live there. It lives in the middle box instead.

---

## Step 1 — make the script

1. Go to **https://script.google.com** and click **New project**.
2. Delete whatever is in the editor.
3. Open `AppsScript-TripBot.gs` from this folder, copy **all** of it, paste it in.
4. Rename the project (top left) to **TripShare planner** so you can find it later.

## Step 2 — get an OpenAI key

You already have one in `claude desktoi\.env` as `OPENAI_API_KEY`.
Use that, or make a new one at **https://platform.openai.com/api-keys**.

> A separate key just for this is tidier — if it ever leaks you can cancel that
> one without breaking anything else.

## Step 3 — put the key where only the script can see it

⛔ **Do NOT paste the key into the code.** This folder is published to GitHub.

1. In the Apps Script editor, click the **gear icon** (Project Settings), left side.
2. Scroll to **Script Properties** → **Add script property**.
3. Property: `OPENAI_API_KEY`
4. Value: your key.
5. **Save script properties.**

## Step 4 — publish the script

1. **Deploy** → **New deployment**.
2. Gear next to "Select type" → **Web app**.
3. Set:
   - **Execute as:** Me
   - **Who has access:** **Anyone**
4. **Deploy**, then approve the permission screen Google shows you.
5. Copy the **Web app URL**. It looks like
   `https://script.google.com/macros/s/AKfyc.../exec`

> "Anyone" sounds alarming and is correct here — the visitors are strangers, so
> the door has to be open. What stops it being abused is the daily limit inside
> the script, not the door.

## Step 5 — point the page at it

In `tripshare/index.html`, find this line (near the top of the script, ~line 219):

```js
var TRIPBOT = { url: "" };
```

Put your Web app URL in the quotes:

```js
var TRIPBOT = { url: "https://script.google.com/macros/s/AKfyc.../exec" };
```

Then, from the `Sales Tracker Website` folder:

```
git add -A && git commit -m "Turn the TripShare planner on" && git push
```

**That push makes it live for everyone.** Until then, nothing has changed.

---

## What it costs

| | |
|---|---|
| Model | `gpt-5.6-luna` |
| Price | **$0.20 in / $1.20 out per 1M tokens** — read off OpenAI's live pricing page 8 Sep 2026 |
| One plan, typical | about **US$0.002** |
| **One plan, worst it can be** | **about US$0.0026** — set by `MAX_OUTPUT_TOKENS`, not by the typical case |
| Daily limit | **100 plans**, set by `DAILY_CALL_CAP` in the script |
| **Worst case per day** | **about US$0.26** |
| Worst case per month | about **US$8** |

⛔ **The US$0.20/day and US$6/month written here until 11 Sep 2026 were WRONG, and
wrong in the direction that flatters.** They were the *typical* cost multiplied by
the cap. A cap has to be priced at the worst a call can cost: 2,000 output tokens
is US$0.0024 on its own, before a single input token. Found by an outside reviewer,
not by us.

⚠ **And the day resets at UTC midnight, not yours.** Someone who wanted to could
use one day's allowance just before it and the next day's just after, so the real
short-term worst case is about **two days' worth back to back**.

**To spend less, lower `DAILY_CALL_CAP`.** It is the ceiling: the script counts
every call *before* it makes it, so the number cannot be beaten by bad luck or
by two people clicking at once.

### To see what it has actually used

In the Apps Script editor, choose `checkUsage` from the function dropdown and
press **Run**. Then **View → Logs**. It prints today's count and the spend.

---

## The four things protecting the money

| | What it does |
|---|---|
| `DAILY_CALL_CAP` | hard ceiling on calls per day — **this is the spend limit** |
| `MAX_INPUT_CHARS` | nobody can post a novel and have you billed for it |
| `MAX_OUTPUT_TOKENS` | caps the expensive half of every single call |
| `MIN_MS_BETWEEN` | slows a rapid loop without blocking a real person |

⚠ **Honest limit, said plainly rather than hidden:** the door is open to
strangers, so somebody determined could still use up the daily allowance. The
cap is what protects you — it makes the worst case **a known small number per
day**, not zero. If that ever happens, lower the cap or take the URL out of the
page.

🚨 **"Nothing else breaks" was WRONG, and this is the finding that matters most.**
An outside reviewer pointed out on 11 Sep 2026 that Google Apps Script has its own
daily quotas on the whole **Google account**, not on one script. Somebody
hammering this endpoint would not cost you OpenAI money past the cap — but they
could exhaust that Google quota, and **your Sales Tracker and your Worklog both
run on Apps Script too.**

> Gemini 3.1 Pro: *"will break the AI feature **and** the two other apps relying
> on GAS until the quota resets."*

**So the blast radius is bigger than this one feature.** That is an argument for
keeping `DAILY_CALL_CAP` low, and for the kill switch — not for abandoning the
design, which both reviewers called appropriate for the constraints.

⚠ **The cap protects THIS endpoint, not your OpenAI account.** If the same key is
used anywhere else, or an old deployment is still live, those spend separately.
**Use a key made only for this**, so you can cancel it without breaking anything
else.

---

## 🛑 The fastest way to stop it — ten seconds, no website change

1. Apps Script editor → **gear icon** (Project Settings) → **Script Properties**.
2. Add (or edit) a property called `ENABLED` and set its value to **`no`**.
3. Save.

It stops answering immediately. Visitors see *"The planner is switched off at the
moment."* Nothing else on your site changes, and you do not touch git at all.

Set it back to `yes` (or delete the property) to start it again.

> **Why this exists:** the other way to stop it needs a code edit, a commit and a
> push. If something is going wrong you want it off *now*, not after three steps
> you have to remember. If the property is missing the planner runs — so deleting
> it by accident cannot silently kill the feature.

---

## To switch it off again, properly

Put the line back to `var TRIPBOT = { url: "" };`, commit and push. The panel
disappears and the page is exactly as it was. You can leave the Apps Script
deployed — with nothing calling it, it costs nothing.
