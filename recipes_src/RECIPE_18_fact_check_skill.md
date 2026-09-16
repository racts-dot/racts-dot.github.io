# RECIPE 18 — A /fact-check skill that gives every claim a verdict

From: [Claude Code Will 10X Your Productivity (ADVANCED COURSE)](https://www.youtube.com/watch?v=efaBaxDN_q8) · 16 Mar 2026 · 1:29:50 · [watch](https://www.youtube.com/watch?v=efaBaxDN_q8)

**One skill, written in one sentence: read a draft line by line, find a primary source for every claim, and mark each one confirmed, unverified or wrong. She runs it again and again on her video outlines. The idea is sound. Two parts of her setup need changing before it fits your rules: which model gives the verdict, and the paid search tool behind it.**

# ⭐⭐ THE ONE THING — the skill is one prompt

She builds it by typing this into Claude Code ([1:16:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4590s)):

> "Create a skill called fact check. It should read whatever contents I'm writing, go line by line" ([1:16:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4590s))

The rest of her prompt, paraphrased: use Perplexity to find primary sources for every claim, flag anything unverified, and give each claim one of three verdicts, with citations.

```
your draft
    │
    ▼
split into claims, line by line
    │
    ▼
search for a primary source per claim
    │
    ▼
CONFIRMED  ·  UNVERIFIED  ·  WRONG   + the source link
```

How she uses it:

> "I will run fact-check like again and again on the outline" ([1:17:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4650s))

Her aim is that everything she says on camera "has at least a primary source" ([1:17:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4650s)). She also says it works for research, competitor analysis and reports ([1:16:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4590s)).

## Why this matters to you

Your listings make claims: page counts, what a binder covers, what a worksheet teaches. On 12 Sep you ranked #2 on Etsy AU for "dementia caregiver binder". People are finding you. A wrong claim on a page someone actually reads costs more than one nobody sees.

⭐ A fact-check skill is a gate for words, like Recipe 04's grader. The difference is that it checks facts against sources, not style against a rubric.

# ⚠ The checker problem — her setup does not pin the model

A verdict is a judgement. Your rule says Haiku may do work but never judge it.

The video never says which model runs the fact-check. Earlier in the same course she was on Haiku:

> "I was using Haiku just because it's faster for the purpose of this demo." ([38:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=2281s))

She then tried Haiku on a research task, and it failed:

> "Okay, well, it can't even search the internet." ([44:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=2641s))

She switched to Sonnet for that test. Her normal model is Opus ([38:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=2281s)). Nothing on screen shows which one was active when she built or ran /fact-check.

```
HER SKILL                          YOUR RULE
─────────                          ─────────
model: whatever is on              verdicts = judging
(Haiku earlier in this course)     judging ≠ Haiku
         │                                 │
         └──── if it runs on Haiku, ───────┘
               it breaks your rule
```

⛔ If this skill ever runs on Haiku, it breaks your rule. Run it only in a chat on your strongest model, and check /model before you start.

A second trap is completeness. A checker can check 20 claims out of 60 and still say "all confirmed". Two fixes you can build in:

1. Make the skill list and number every claim before it checks any of them.
2. Make it end with two counts: claims found, and claims given a verdict. If they differ, the run is incomplete.

# The paid part — Perplexity

Her skill searches with a Perplexity MCP server. She thinks it is much better for research:

> "I personally think Perplexity MCP is like vastly superior when it comes to research." ([1:15:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4530s))

⚠ It needs a Perplexity API account with a card on file ([1:16:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4561s)). She states no price. Her own advice: "if you don't have budget, like skip this step" ([1:15:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4530s)).

⛔ Adding a card and an API key is money, so that decision is yours. You do not have a Perplexity server set up on this Mac (checked 16 Sep). Claude Code can already search the web without it. She shows that at [1:07:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4050s). Start there. Add Perplexity only if the free version keeps marking things "unverified" that you know have sources.

⚠ Her own caveat when she showed the skill she had built: "I already actually have the skill, so I don't know if it updated it at all" ([1:17:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4621s)). She never shows it running on a draft. The output format above is what she asked for, not a result she showed.

# What to try — one step, tonight

This uses Claude Code's built-in web search, so no new API, no card and nothing public. You have no fact-check skill yet (checked 16 Sep: only notion-summary is installed).

```
1. open a chat, type /model, and pick the strongest model

2. paste:

   Create a skill called fact-check. When I run it on a
   file, first list and number every factual claim in it.
   Then, for each numbered claim, search the web for a
   primary source and give one verdict: CONFIRMED,
   UNVERIFIED or WRONG, with the link. Never use a
   cheaper model or subagent for the verdicts.
   End with two numbers: claims found, claims given a
   verdict.

3. start a new chat (she says to reload after
   making a skill), then run:

   /fact-check <one of your listing_text.md files>

4. check the two numbers at the end match
```

⭐ Try it first on a listing where you already know the right answers. Then you can tell whether the checker is right before you trust it on anything else.

## ALSO MENTIONED

- She pairs it with a YouTube news research skill that is "almost a thousand lines" ([1:17:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4650s)).
- Her other quality check is a hook that looks for banned words and em dashes in captions ([12:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=750s)). Recipes 04 and 09 already cover that.
- On API keys: "The secure thing to do would be to open the file afterwards and then paste your API key in" yourself, rather than giving the key to Claude ([1:12:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4321s)).
- She has a global preference that tells Claude to use Perplexity for research ([1:08:00](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4080s)).
- Prices she states in this video: Pro "$20 per month", and she recommends "the $100 per month plan". She is on "the $200 per month plan" ([5:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=301s), [5:31](https://www.youtube.com/watch?v=efaBaxDN_q8&t=331s)). These are her figures from 16 Mar 2026, not advice.

## See also

RECIPE 04, the grader pattern: the same gate idea, for style. RECIPE 09, plan mode and quality gates: gates on your words. RECIPE 11, loop engineering: the same problem of a cheap checker giving the verdict. RECIPE 19 and RECIPE 20 come from the same video.
