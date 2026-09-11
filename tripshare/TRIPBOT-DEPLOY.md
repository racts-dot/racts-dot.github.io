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

You already have one. ⛔ **The path here used to be the WINDOWS one
(`claude desktoi\.env`), which does not exist on the Mac.** On the Mac it is
`~/Desktop/costway scraper/.env`, measured 11 Sep 2026.

⭐ **Do not open the file and read the key.** Copy it straight to the clipboard,
so it never appears on screen and never gets read out loud:

```
grep '^OPENAI_API_KEY' ~/Desktop/"costway scraper"/.env | cut -d= -f2- | tr -d '"'"'"' \n' | pbcopy
```

Then paste it into the box in step 3. Or make a separate key at
**https://platform.openai.com/api-keys**.

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
| One plan, **measured** | about **US$0.00075** — under a tenth of a US cent |
| One plan, worst case | about **US$0.0025** if it writes the longest answer allowed |
| Daily limit | **100 plans**, set by `DAILY_CALL_CAP` |
| Monthly limit | **1,000 plans**, set by `MONTHLY_CALL_CAP` |
| Busiest realistic day | about **US$0.08** |
| Worst possible day | about **US$0.25** |
| **Worst possible month** | **about US$2.50** — this is the real ceiling |

⭐ **The "one plan" figure is measured, not guessed `[MEASURED 2026-09-11]`.** Two
real calls to this exact model with this exact prompt used 692 tokens in and
1,129 out, costing **US$0.00149 for both**. The doc used to say US$0.002 a plan,
which was written before anything had ever been called and was nearly three
times too high.

⛔ **But the OLD "worst case US$0.20/day" was too LOW, and that is the one that
mattered.** A single call is allowed 2,000 tokens of answer, and 2,000 × $1.20
per million is US$0.0024 of output on its own — so a fully used day is nearer
**25 cents than 20**, before the input side. The daily cap counts CALLS exactly.
It only estimates DOLLARS, and only at today's prices.

⛔ **And it is a DAILY limit, not a total one.** Somebody who comes back every
day pays it every day. That is why `MONTHLY_CALL_CAP` now exists: it is the
thing that stops a bad month becoming a bad year.

**To spend less, lower `DAILY_CALL_CAP`.** The script counts every call *before*
it makes it, so the number cannot be beaten by bad luck or by two people
clicking at once.

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
| `MONTHLY_CALL_CAP` | the ceiling on a whole month, so daily abuse cannot repeat forever |
| `ENABLED` | your off switch — see below |

⚠ **Honest limit, said plainly rather than hidden:** the door is open to
strangers, so somebody determined could still use up the daily allowance — about
two and a half minutes of clicking. The caps are what protect you: they make the
worst case **a known small number**, not zero. Sustained abuse costs roughly
**US$2.50 a month at most**, and the visible effect is that the planner stops
answering for everybody until the next day.

⚠ **One thing the caps do NOT stop, named rather than hidden:** Google gives
every Apps Script a daily allowance of its own for reading and writing settings.
Somebody hammering the door can use that up even when no OpenAI call is made. It
costs nothing, but the planner would return an error for the rest of that day.
There is no way to prevent it without making people sign in, which this app
deliberately does not do.

---

## 🚨 If it gets abused, it does not only break the planner

An outside reviewer raised this on 11 Sep 2026 and it had been missed:

**Google Apps Script's daily limits apply to your whole Google account, not to
one script.** Somebody hammering this endpoint cannot cost you OpenAI money past
the caps — but they can use up that Google allowance, and

> **your Sales Tracker and your Worklog both run on Apps Script too.**

Gemini 3.1 Pro, verbatim: *"will break the AI feature **and** the two other apps
relying on GAS until the quota resets."*

**So the damage from abuse is wider than this one feature.** That is a reason to
keep `DAILY_CALL_CAP` low and to know where the off switch is — not a reason to
change the design, which both reviewers called appropriate for the constraints.

**If your Sales Tracker suddenly stops saving,** check this planner first: the off
switch below frees the quota.

---

## 🔴 The off switch — how to stop it in ten seconds

You do not need to touch the website, and nothing needs re-deploying.

1. Open the Apps Script project.
2. **Project Settings → Script Properties → Add script property.**
3. Name it `ENABLED`, set the value to `no`, and save.

The very next request is refused, and visitors see *"The planner is switched off
at the moment."* Set it back to `yes` to turn it on again.

**Use this if:** the bill looks wrong, the suggestions come back nonsense, or you
simply want it off while you think. It is faster and safer than editing the page,
and unlike editing the page it works even if you are away from your computer.

---

> **One thing worth keeping from the duplicate of this section that was merged
> away:** if the `ENABLED` property is missing entirely the planner RUNS. That is
> deliberate — deleting it by accident cannot silently kill the feature — but it
> does mean "I don't see the property" is not the same as "it is off".

---

## To switch it off again, properly

Put the line back to `var TRIPBOT = { url: "" };`, commit and push. The panel
disappears and the page is exactly as it was. You can leave the Apps Script
deployed — with nothing calling it, it costs nothing.
