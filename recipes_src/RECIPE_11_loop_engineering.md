# RECIPE 11 — Loop engineering: /goal and routines

From: [Loop Engineering, Claude Code /goal, and Agent Routines](https://www.youtube.com/watch?v=uLaDjhTkJKM) · 19 Jun 2026 · 1:46:04 · [watch](https://www.youtube.com/watch?v=uLaDjhTkJKM)

Worked examples from: [6 INSANE Projects to Learn Claude Fable and /goal](https://www.youtube.com/watch?v=Hg1Y7mp9aYo) · 10 Jul 2026 · 1:47:17 livestream · and its 13-minute cut, [Claude Fable 6 INSANE Projects To Get Ahead of 99%](https://www.youtube.com/watch?v=nw0pNT_5rtM) · 3 Aug 2026 · 13:29

**A loop is three things: do a step, check it against a finish line you wrote down, then go again or stop. /goal runs that loop while you watch. A routine runs it on a timer in the cloud. The hard part, she says, is the checker. Her own checker is the part that breaks your rules.**

# ⭐⭐ THE ONE THING — write the finish line before the task

Her shape for every /goal prompt, from her [cheat sheet](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=2130s):

```
/goal  <the task>
       done looks like:  <an end state you can count>
       checked by:       <how it proves it: a count, tests passing>
       guardrail:        do not <delete / touch X>
       stop after:       <N> turns
```

Her first demo sorted her Downloads folder into subfolders by type. The prompt ended:

> "Keep going until no files are left. Do not delete anything. And stop after 30 turns." ([27:30](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=1650s))

She names [three things](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=1831s) that made it a good goal: a clear end state, a check it can run, and a guardrail. The turn limit is her token brake.

In July she stretched it to five parts: task, why, outcome, constraints, verification. Verification matters most ([9:00](https://www.youtube.com/watch?v=Hg1Y7mp9aYo&t=540s)).

> "actually the hardest part is defining the checker" ([21:01](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=1261s))

## Why this matters to you

In most chats today, you are the loop. I say something is done, and you decide whether it is. Her whole case for a separate checker is one you already hold:

> "the first agent is just biased and will lie to you" ([11:01](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=661s))

A written finish line means your review starts from a number, not from my word.

# ⚠ The checker problem — her setup breaks your rule

```
HER LOOP                          YOUR RULE
────────                          ─────────
maker:   big model                Haiku may DO the work
checker: small, fast, "Haiku"     Haiku may NOT judge it
            │                          │
            └── "goal achieved" is a verdict ──┘
```

She says it three times:

> "such as a cheaper model like Haiku checking and reviewing the work independently" ([16:32](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=992s))

> "default checker in cloud code is haiku. You can change it so it uses a different model" ([23:02](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=1382s))

> "I believe the default is Hi Q." ([24:31](https://www.youtube.com/watch?v=Hg1Y7mp9aYo&t=1471s))

⚠ This is NOT confirmed. She states it flatly in June and says "I believe" in July. Neither video shows a setting, a document or how to change it. Treat the checker's model as unknown until you have read /goal's own help text.

Two fixes, both built from her own advice:

1. Make "checked by" something a plain command can count. Her own question is "Is it a count?" Then the checker only reads a number. It never has to judge quality.
2. Never treat "goal achieved" as a pass. Have a strong model or a script recount before you believe it. For routines, the form has a model picker ([42:00](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=2520s)), so give the checker routine a strong model.

## How /goal works, in her words

She says /goal wraps the Stop hook: "it runs that a small prompt at the end of each cloud code" turn ([26:31](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=1591s)). `/goal clear` stops it. Typing `/goal` while it runs gives a status update ([1:05:31](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=3931s)).

⚠ You run your own hooks. Neither video tests /goal alongside other hooks, so try your first goal in a scratch folder.

# ⭐ A loose finish line, caught on camera

In July she trained a simulated spider to climb stairs. The goal passed. The staircase had about three steps.

> "technically the verification step is correct" ... "make sure there's 20 stairs instead of like three" ([46:31](https://www.youtube.com/watch?v=Hg1Y7mp9aYo&t=2791s))

In June she gave the same warning about code: your "end condition was make sure all the tests pass but your tests were garbage" ([58:30](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=3510s)).

⭐ This is the grader pattern from Recipe 04, failing the way it fails. The gate is only as good as what it counts.

# Routines — the same loop on a timer

A routine is a saved loop. It runs in the cloud "even when your laptop is closed" ([39:02](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=2342s)), in a fresh environment that pulls your GitHub project.

The form has these fields:

- a name and instructions
- a GitHub project, which is optional
- a model
- a trigger: a schedule, a GitHub webhook or a POST request ([40:30](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=2430s))
- connectors
- environments, which hold API keys ([50:01](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=3001s))

Her real maker and checker pair, for her support inbox:

```
MAKER routine, daily 8am          CHECKER routine, ~2 hours later
────────────────────────          ───────────────────────────────
run the cleanup-tickets skill     re-read every ticket closed today
close tickets that are solved     reopen any not clearly solved
post a summary to Slack           post the audit to Slack
                    │
   her result: 151 correctly closed, 1 reopened
```

([52:30](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=3150s), [53:31](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=3211s))

Her safety advice is to start read-only: "let it summarize stuff for a few days before you let it write anything" ([56:00](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=3360s)). For connector permissions she suggests "always allow for read only things" and approval for any write, edit or delete ([45:31](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=2731s)).

For a loop that stays on your own machine, she points Mac users to launchd ([39:31](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=2371s)). She does not demo it.

⛔ Each of these needs your yes first:

- connecting Gmail, Slack or any account to a cloud routine
- putting an API key into a cloud environment
- any routine that sends, closes, edits or posts something
- her marketing demo's last step, "Claude post everything" ([54:00](https://www.youtube.com/watch?v=Hg1Y7mp9aYo&t=3240s)), which is public posting

# Money and limits — her figures, not advice

Neither video gives a price per /goal run. It spends your plan allowance.

| What | Her words | Video |
| --- | --- | --- |
| Routines | "use the same plan as your normal claude and there's a daily limit in settings" | [19 Jun](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=3300s) |
| Her plan | "the $200 plan" (Max) | [10 Jul](https://www.youtube.com/watch?v=Hg1Y7mp9aYo&t=5911s) |
| 72-hour A/B loop | "almost ran out of tokens this week, but it was so worth it" | [10 Jul](https://www.youtube.com/watch?v=Hg1Y7mp9aYo&t=3570s) |
| Why it cost so much | "I accidentally like left it on Fable" | [10 Jul](https://www.youtube.com/watch?v=Hg1Y7mp9aYo&t=4801s) |
| Apify scrape, about 5,000 videos | "under like $10, honestly" | [10 Jul](https://www.youtube.com/watch?v=Hg1Y7mp9aYo&t=2912s) |
| The spider demo | "it's 100% for free" | [3 Aug](https://www.youtube.com/watch?v=nw0pNT_5rtM&t=30s) |

⚠ "100% for free" means the simulation tools are free. It all still runs through Claude Code, on a plan.

Her token-saving move is to use the big model while the loop learns a messy task. Then "write it into your Claude MD file for the project, and then you can switch to a cheaper model" ([1:21:01](https://www.youtube.com/watch?v=Hg1Y7mp9aYo&t=4861s)). That fits your rule: the cheap model does the repeat work, but it still does not give the verdict.

⚠ The A/B result has no evidence behind it. She says the loop "ended up tripling my CTR for that first step" ([1:03:31](https://www.youtube.com/watch?v=Hg1Y7mp9aYo&t=3811s)). She also says it "never reached 40%", her target. She showed only a blurry screenshot and no figures.

# What to try — one step, tonight

This costs no API money, stays on your Mac and touches nothing public.

```
1. make a new empty folder and copy in 5 of your
   listing text files (copies, not the originals)

2. open Claude Code in that folder and type:

   /goal For every .md file here, write its name and
   word count to counts.txt, one line per file.
   Done looks like: counts.txt has exactly one line
   per .md file. Checked by: count both, and match
   each number against wc -w. Do not edit any .md
   file. Stop after 15 turns.

3. when it says goal achieved, do NOT accept it.
   ask: "recount both with a plain shell command
   and show me the two numbers side by side"
```

Step 3 is the point. It puts your rule into the loop: the checker's "done" is a claim, and the recount is the evidence.

## ALSO MENTIONED

- Her [six parts](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=362s) of a loop: automations, worktrees, skills, connectors, subagents (maker and checker), and memory, which for her is usually the GitHub repo.
- Her formula: AI leverage depends on "my skill and my clarity" ([57:30](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=3450s)): defining done, and spotting a bad check.
- On overnight runs: "stop after x number of turns and produce a summary of what you've done" ([1:30:01](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=5401s)).
- On permissions: "I do not recommend like allowing it to dangerously skip permissions" ([1:01:00](https://www.youtube.com/watch?v=Hg1Y7mp9aYo&t=3660s)). She reads each prompt, often picks "don't ask me again", and approves from her phone by remote control.
- On Cowork: "I think co-work doesn't have the /goal command yet" ([1:04:00](https://www.youtube.com/watch?v=uLaDjhTkJKM&t=3840s)). It does have schedules.
- Her marketing goal used a post-grader skill from her own Blotato pack, and looped until every post scored above 8 out of 10. ⚠ It is her product's grader, marking copy for her product's rubric.
- Every other price she states. 10 Jul: "$1,000 per month for ManyChat", "$29 if you subscribe to my app", "This video cost $2,000 in editing", Voice In at "$30", "probably like 40,000 a month on ads", and a trip-planning goal capped "under $800 per person". 19 Jun: an n8n support bot for "$1 a month", Beehiiv at "400 a month", and "I put 10K in the Tik Tok title" of a free training.

## See also

RECIPE 04, the grader pattern: a loop is a grader that also decides the next step. RECIPE 09, plan mode and quality gates: argue the finish line in plan mode first. RECIPE 03, Cowork: schedules without /goal.
