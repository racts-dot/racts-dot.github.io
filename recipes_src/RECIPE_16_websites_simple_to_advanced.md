# RECIPE 16 — Websites, simple to advanced

From: [I Replaced My $500/Month Website With Claude Design](https://www.youtube.com/watch?v=rKpvo1LpTxs) · 4 Jun 2026 · 9:58 · [watch](https://www.youtube.com/watch?v=rKpvo1LpTxs)

From: [The Correct Way to Build Website with Claude Code (New)](https://www.youtube.com/watch?v=anc8klnrwC4) · 29 Mar 2026 · 51:45 · [watch](https://www.youtube.com/watch?v=anc8klnrwC4)

**Two levels. Simple: Sabrina chats a landing page and a pricing page into shape in Claude Design, then drags a zip onto Netlify Drop. Advanced: Sandy has Claude Code build a site that takes Stripe payments, on Vercel and Supabase, with a domain she bought. Both creators already had an audience before the site. The site did not bring it.**

# ⭐⭐ THE ONE THING — a website is a shop with no street

Both videos show a site going live. Neither shows a site finding its own visitors.

```
SABRINA                            SANDY
───────                            ─────
old site already had               550,000 followers first,
"1.6 million website visitors"     then a waitlist page
        │                                  │
new site = same traffic,           "websites nowadays is just
nicer page                          like a business card"
```

Sabrina: "last year my website brought in 1.6 million website visitors" ([0:00](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=0s)). Sandy grew her channel "to 550,000 followers across three different platforms" ([1:00](https://www.youtube.com/watch?v=anc8klnrwC4&t=60s)), and says sites are "just like a business card" ([6:30](https://www.youtube.com/watch?v=anc8klnrwC4&t=390s)).

## Why this matters to you

On 12 Sep you had 46 live listings and zero sales, and you ranked #2 on Etsy AU for "dementia caregiver binder". Etsy is already sending you searchers. What is unproven is what happens after they see a listing. A website does not fix that. It adds a second shop that nobody walks past.

⚠ So a site to sell printables beyond Etsy is a big decision, and it goes to you: new costs, a payment account, a public page, and no built-in traffic. Build the simple level to learn. Hold the advanced level until a listing sells.

# Level 1 — simple: Claude Design + Netlify Drop

Her route, in order:

```
claude.ai/design → "company website", high fidelity
        │  describe offers, or paste your old site
answer its clarifying questions
        │  5 to 10 min first build, two themes side by side
comment / edit to fine-tune
        │
rename main page to index.html → download zip
        │
app.netlify.com/drop → drag the zip in → live link
```

Useful details she gives:

- Paste a screenshot of a colour scheme you like, say from dribbble.com, and it restyles the whole site ([3:00](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=180s)).
- Use the left chat for site-wide changes. Use Comment to point at one element. Use Edit to change words or fonts by hand. Edit means "you don't burn your tokens" ([5:30](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=330s)).
- After the first build, switch model: "you definitely don't need Opus 4.7. It's way overkill after the initial build" ([6:01](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=361s)). She moves to Sonnet 4.6.
- Netlify "just expects it to be called" index.html ([8:30](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=510s)).

⚠ "The designs are not necessarily mobile responsive" ([7:30](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=450s)). Her check is right-click, Inspect, phone view. Then screenshot anything broken and tell it to fix it.

⚠ Netlify Drop gives a password-protected link. She calls it "a publicly accessible link as long as you have the password" ([9:02](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=542s)). Removing the password needs a Netlify account: "click sign up for free" ([9:30](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=570s)). She mentions adding your own domain but doesn't show it.

⛔ Creating the Netlify account and removing the password makes the page public. Both need your yes.

This level partly overlaps the Doser website cards.

# Level 2 — advanced: Claude Code, payments, a domain

Sandy's video runs 51 minutes and wanders. The build itself, with the side trips cut:

```
1. Claude Code (inside Antigravity): "use Vercel for my front
   end and Supabase for my back end ... give me all the
   instructions"                                        [10:30]
2. it asks: site type, framework (she picks Next.js),
   login or not (she says no: people just pay)          [11:32]
3. YOU sign up: Supabase free tier, Vercel hobby,
   Vercel CLI                                           [12:30]
4. launch on a free vercel.app address first            [19:01]
5. feed it the real content from a .md file             [30:30]
6. ask for Stripe checkout, two prices                  [31:30]
7. buy a domain, paste DNS records it gives you         [38:30]
8. pay yourself once, check the Stripe dashboard        [47:31]
```

Her demand on the payment step: "make sure it's 98% correct before you move on to next step" ([31:30](https://www.youtube.com/watch?v=anc8klnrwC4&t=1890s)). Before a context fill-up she has it "save this into MD file" ([26:31](https://www.youtube.com/watch?v=anc8klnrwC4&t=1591s)). Then a new chat picks the project back up.

The free trial stage, in her words: "if you want to test things out for free, this is my recommendation" ([19:31](https://www.youtube.com/watch?v=anc8klnrwC4&t=1171s)). A vercel.app address is a real public link at no cost.

## ⛔ The Stripe keys — do not copy her here

She copies both Stripe keys, publishable and secret, straight into Claude Code. Then she rotates them: "I gave it to Claw Code and they'll rotate it" ([36:01](https://www.youtube.com/watch?v=anc8klnrwC4&t=2161s), [36:31](https://www.youtube.com/watch?v=anc8klnrwC4&t=2191s)).

```
HER WAY                         YOUR WAY
───────                         ────────
paste secret key into chat      never paste it into chat
rotate it afterwards            YOU type it into Vercel's
                                environment settings yourself
```

⚠ The following is not in the video. Stripe also gives test keys that move no real money. A first build should run on those. She tested by paying herself: "$2.99 from me" ([48:30](https://www.youtube.com/watch?v=anc8klnrwC4&t=2910s)). That was a real charge.

⚠ She also says a new Stripe account "will take a little bit of time" to be verified for your business ([36:01](https://www.youtube.com/watch?v=anc8klnrwC4&t=2161s)).

⛔ Each of these needs your yes: putting the site on any public link (a free vercel.app or Netlify address included), opening a Stripe account, switching to live keys, buying a domain, and pointing the domain at the site.

## The audit step — check it against real data

Her site sells an AI "GEO audit". It scored her own site a C, with "AI visibility is 25%" ([44:31](https://www.youtube.com/watch?v=anc8klnrwC4&t=2671s)). The audit is a model run through her OpenRouter key ([48:01](https://www.youtube.com/watch?v=anc8klnrwC4&t=2881s)). It is a model's opinion, not measured search data.

She also claims blogs help AI tools recommend a business ([3:01](https://www.youtube.com/watch?v=anc8klnrwC4&t=181s)). She shows no evidence.

⭐ Before you build a site to catch searches, measure the searches. RECIPE 12 plugs live search data into Claude Code. Ask it whether anyone searches Google for your product outside Etsy. If nobody does, a site has nothing to rank for.

# Money — every price they state

| What | Their words | Video |
| --- | --- | --- |
| Sabrina's old site | "$500 per month" | [4 Jun](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=0s) |
| Her old template | "a $50 Webflow template" | [4 Jun](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=30s) |
| Netlify account | "sign up for free" | [4 Jun](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=570s) |
| Old cost of a site | "pay over $10,000" | [29 Mar](https://www.youtube.com/watch?v=anc8klnrwC4&t=421s) |
| Supabase | "I'm going to use free tier" | [29 Mar](https://www.youtube.com/watch?v=anc8klnrwC4&t=750s) |
| A .ai domain | "like $92 a year" | [29 Mar](https://www.youtube.com/watch?v=anc8klnrwC4&t=2371s) |
| Her two audit prices | "$2.99" and "$14.99" | [29 Mar](https://www.youtube.com/watch?v=anc8klnrwC4&t=2040s) |
| A human-made report | "they charge $1,200" | [29 Mar](https://www.youtube.com/watch?v=anc8klnrwC4&t=2101s) |
| Her SEO client | "$5,500 per month" retainer | [29 Mar](https://www.youtube.com/watch?v=anc8klnrwC4&t=1980s) |
| Time | "about 5 and 1/2 hours" | [29 Mar](https://www.youtube.com/watch?v=anc8klnrwC4&t=2940s) |

⚠ Neither video states Stripe's fees, Vercel's paid tiers, or what Claude Design costs. Sabrina only hints at plan limits: "If you are not on the Claude Max plan" ([5:30](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=330s)). The .com price Sandy paid isn't shown. She used a new-customer promo code.

# What to try — one step, tonight

This costs nothing, stays on your Mac, and puts nothing online.

```
1. make an empty folder and copy in the real listing
   images and listing text for ONE caregiver binder

2. open Claude Code there, in plan mode, and paste:

   Build one static index.html landing page for this
   product, using only the images and text in this
   folder. No drawn artwork. The buy button links to
   my Etsy listing. No payments, no deploy. Check it
   at phone width. Stop when it opens locally.

3. open index.html in your browser and look at it

4. then write one line under it:
   "Visitors would come from ______."
```

Step 4 is the point. If the blank stays empty, the site waits. The Etsy listing is where the work goes.

## ALSO MENTIONED

- Sandy's free route: a Canva website with a free Canva domain ([9:30](https://www.youtube.com/watch?v=anc8klnrwC4&t=570s)).
- Hero sections copied as prompts from 21st.dev, restyled to your brand ([21:00](https://www.youtube.com/watch?v=anc8klnrwC4&t=1260s)).
- A scroll animation built from 121 video frames made in OpenArt with Kling 3.0. She then threw it away as wrong for her site ([25:00](https://www.youtube.com/watch?v=anc8klnrwC4&t=1500s)). Generating the clip costs credits.
- A logo from Nano Banana Pro, after several tries she didn't like ([22:32](https://www.youtube.com/watch?v=anc8klnrwC4&t=1352s)).
- An admin dashboard designed in Google Stitch, pasted in as code. Its numbers are fake: "this is not real number, guys" ([48:30](https://www.youtube.com/watch?v=anc8klnrwC4&t=2910s)).
- A blog fed by an n8n workflow ([43:30](https://www.youtube.com/watch?v=anc8klnrwC4&t=2610s)).
- Waitlist and form entries go to a Google Sheet ([0:30](https://www.youtube.com/watch?v=anc8klnrwC4&t=30s)).
- Sabrina can capture an element from a site you like with "Claude design capture" ([7:00](https://www.youtube.com/watch?v=rKpvo1LpTxs&t=420s)).

## See also

RECIPE 12, live search data: measure demand before building anything to catch it. RECIPE 09, plan mode: argue the site plan before any code. RECIPE 15, the Lovable quiz and directory: another no-code route to a live page. RECIPE 05, the audience playbook: where visitors actually come from.
