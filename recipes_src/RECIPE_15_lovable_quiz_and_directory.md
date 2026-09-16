# RECIPE 15 — Lovable: a lead-magnet quiz and a directory

From: [Create a high converting lead magnet (Lovable Cloud AI)](https://www.youtube.com/watch?v=GJIDAOesz4U) · 25 Oct 2025 · 16:37 · [watch](https://www.youtube.com/watch?v=GJIDAOesz4U)

From: [How To Build Profitable Website Directory WITHOUT Coding (Using AI)](https://www.youtube.com/watch?v=PNyjhx-q4bU) · 20 May 2025 · 14:09 · [watch](https://www.youtube.com/watch?v=PNyjhx-q4bU)

**Two small web apps built by typing into Lovable, each with a Supabase database behind it. The quiz collects emails, so its database must be closed to the public. The directory shows a list, so its database must be open for reading only. In both videos the first build got that rule wrong.**

# ⭐⭐ THE ONE THING — run the security scan before you publish

In the quiz video the app was working and collecting emails. Then she opened Lovable's security scan, just before publishing. It found this:

> "Customer email addresses and business data exposed to public." ([14:31](https://www.youtube.com/watch?v=GJIDAOesz4U&t=871s))

That happened even though Lovable said earlier that it had turned on row-level security, "really important from a security perspective" ([06:01](https://www.youtube.com/watch?v=GJIDAOesz4U&t=361s)). Saying it was on did not make the data safe.

Her fix is a short sequence ([14:31](https://www.youtube.com/watch?v=GJIDAOesz4U&t=871s) to [15:31](https://www.youtube.com/watch?v=GJIDAOesz4U&t=931s)):

```
1. Publish  ->  Security scan
2. if "Try to fix all" is greyed out: update the scan first
3. Try to fix all
   her result: "removed public read access to customer data"
4. scan AGAIN
5. left over: 2 warnings (verbose errors, unbounded text input)
   she judged those "okay to proceed with"
6. only then: Publish
```

> "I definitely recommend this before publishing your lovable app." ([14:31](https://www.youtube.com/watch?v=GJIDAOesz4U&t=871s))

⚠ Step 5 is her call, not a check. The scan is Lovable checking Lovable's own work. After step 4, open the live page in a private window and try to see the table. Believe what you can see, not the scan's green result.

## Why this matters to you

The part of your shop nobody has proved yet is what happens after someone sees a listing. A quiz like "which planner fits you" is one way to catch a visitor who is not ready to buy.

But it collects personal data the moment it goes live. For caregivers the answers can be about a parent's illness. One leaked table is worse than no list at all.

```
              WHO MAY READ THE TABLE?   WHO MAY WRITE?
              ──────────────────────    ──────────────
QUIZ          only you                  anyone who answers
DIRECTORY     anyone                    only you
```

Both videos are about getting that one line right.

# The shared start — Lovable basics

Both builds begin the same way:

- Sign up for Lovable and Supabase, then connect Supabase to Lovable ([03:01](https://www.youtube.com/watch?v=GJIDAOesz4U&t=181s), [04:30](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=270s)). Check it is the right organisation before you authorise.
- Read what the agent says it is doing in the left panel. She says so in both videos ([04:30](https://www.youtube.com/watch?v=GJIDAOesz4U&t=270s), [10:00](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=600s)).
- Wait for the first version before you prompt again: "I would not put in another prompt until you can play with the first version" ([06:30](https://www.youtube.com/watch?v=GJIDAOesz4U&t=390s)). The first build "can take 5 minutes or so".
- The clock icon holds version history, so you can roll back to a version that worked ([12:30](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=750s)).
- Publish goes to a free lovable.app address. A custom domain is a separate step.

⚠ Lovable asks for permission to manage the backend, and offers "always allow" ([05:30](https://www.youtube.com/watch?v=GJIDAOesz4U&t=330s)). She clicked allow once. Do the same.

# Build 1 — the quiz that captures emails

Her prompt, paraphrased: use Lovable Cloud to build a quiz with a calculator, ask 15 questions, make a personal report, and ask for the email at the last step ([04:00](https://www.youtube.com/watch?v=GJIDAOesz4U&t=240s)).

> "it's important you use the term lovable cloud here" ([04:00](https://www.youtube.com/watch?v=GJIDAOesz4U&t=240s))

Those words tell Lovable to set up the database for you.

⭐ Her credit-saving move: write the questions somewhere else while Lovable builds. She used ChatGPT and says Claude works too. Then paste them in with "replace your 15 questions with the following and update the scoring logic" ([10:02](https://www.youtube.com/watch?v=GJIDAOesz4U&t=602s)).

Her question prompt used her "two favorite techniques": tell the AI it is a top expert, and have it ask you questions first.

> "ask me clarifying questions about this task until you're 95% confident you can complete the task successfully" ([07:30](https://www.youtube.com/watch?v=GJIDAOesz4U&t=450s))

```
visitor answers 15 questions
        │
   email box (last step)
        │
   score + report + "book a call" button
        │
   email saved in Lovable: cloud icon -> Database
```

The report could be saved as a PDF ([13:31](https://www.youtube.com/watch?v=GJIDAOesz4U&t=811s)). The emails sit in the database, not in a mailing tool ([14:01](https://www.youtube.com/watch?v=GJIDAOesz4U&t=841s)).

## ⛔ Privacy and consent — this part is yours

- The video never mentions a consent box, a privacy note or a way to unsubscribe. The email box is just "get my results" ([01:30](https://www.youtube.com/watch?v=GJIDAOesz4U&t=90s)).
- Marketing emails usually need clear permission. Add a plain line saying what you will send, plus a separate opt-in tick. Check the rules where you and your buyers live before you email anyone.
- Ask about preferences, like format or how much time someone has. Do not ask about a parent's diagnosis. Data you never collect cannot leak.
- ⚠ Before you put the quiz link on a listing or in a buyer message, read Etsy's own rules on sending buyers elsewhere. Neither video covers Etsy.
- Publishing puts it in public. That is your yes, after the second scan.

# Build 2 — the directory

She remixed her own public Lovable project, a directory of AI tools, into a dog-toy directory ([01:01](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=61s)). The data was a CSV from ChatGPT deep research, capped at 30 rows. The categories were written as a list of tags so visitors can filter them ([02:00](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=120s)). She imported it into a Supabase table and picked title as the primary key ([04:01](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=241s)).

Then the page showed nothing. Lovable's query came back as an empty list ([07:01](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=421s)). The table had no access policy.

```
EASY FIX (don't)                 HER FIX
────────────────                 ───────
turn off row-level security      add a policy named "read"
"you will get a lot of           type: SELECT
 warnings"                       "enable read access for all users"
                                 -> the site can read, never write
```

> "lovable will be able to read our database, but won't be able to update our database, which is fine for a directory." ([08:30](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=510s))

She calls it "probably the most common issue when connecting superbase with lovable" ([09:01](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=541s)). She also added an id column ([07:32](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=452s)).

⚠ A read-for-everyone policy is right for a public list. It is exactly wrong for the quiz's email table. Never copy this policy across.

## ⚠ Why it is a weaker fit for you

- Her pitch is a niche directory "that drives relevant users to your website" ([00:30](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=30s)). Your sales happen on Etsy, not on a site of your own.
- It is a second site to fill and keep current. No evidence here says caregivers want a directory from a planner shop.
- ⛔ "on the free plan, you can't deploy this on a custom domain yet" ([13:01](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=781s)). A domain means upgrading and buying one. That is money.

Research first. If you already have a curated list of caregiver resources, a page on racts-dot.github.io does the same job with no database.

# Money — her figures

Neither video gives a dollar price. What they do say:

| What | Her words | Video |
| --- | --- | --- |
| Lovable Cloud backend | "free to start and you just pay as you scale" | [25 Oct 2025](https://www.youtube.com/watch?v=GJIDAOesz4U&t=330s) |
| Lovable and Supabase sign-up | a "free plan"; Supabase "for free" | [20 May 2025](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=30s), [01:30](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=90s) |
| Custom domain | free plan can't; "purchase a new domain" | [20 May 2025](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=781s), [25 Oct 2025](https://www.youtube.com/watch?v=GJIDAOesz4U&t=960s) |

⚠ Every prompt spends Lovable credits. Settings shows how many you have used ([03:01](https://www.youtube.com/watch?v=GJIDAOesz4U&t=181s)). Both videos are about a year old, so check today's plans before you count on free. Buying credits or a paid plan is money, so that is your yes.

# What to try — one step, tonight

No account, no database, nothing public.

```
1. Open Claude and paste:

   You are a top 0.1% product guide for a shop selling
   printable caregiver binders and planners. Write an
   8-question quiz, "which binder fits you", where every
   result points to one real product type. Ask about
   situation and preferences only - no health details.
   Before you start, ask me clarifying questions until
   you are 95% confident.

2. Answer its questions using your real listings.

3. Check it: does every answer path end at a product
   you actually sell? Does any question ask for
   something you would not want leaked?
```

If it passes step 3, you have the question set. Build it in Lovable only after that, following her scan, fix, scan again order.

## ALSO MENTIONED

- Her first demo was an AI readiness calculator. It gave estimated yearly savings and a consultation button ([01:30](https://www.youtube.com/watch?v=GJIDAOesz4U&t=90s)).
- When a build failed she clicked "try to fix it" ([06:01](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=361s)). When the page was still wrong, she dropped in a screenshot and described the problem ([06:30](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=390s)).
- She says one task per prompt is best practice, though her lazy combined prompt still worked ([09:31](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=571s)).
- Remixing is optional. A simple app like this could be built from scratch ([11:02](https://www.youtube.com/watch?v=PNyjhx-q4bU&t=662s)).
- ⚠ The quiz transcript's captions stop mid-sentence at 16:30 of 16:37, during her sign-off. No steps are missing.

## See also

RECIPE 04, the grader pattern: the security scan is a grader, and the second scan plus your own look is the check on it. RECIPE 16, websites simple to advanced: where a directory would live if you ever built one. RECIPE 05, audience playbook: what to do with an email list once you have consent.
