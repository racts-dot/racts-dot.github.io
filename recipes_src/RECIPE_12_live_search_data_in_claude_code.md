# RECIPE 12 — Live search data in Claude Code

From: [How to do Keyword Research in Claude Code (Goodbye Semrush)](https://www.youtube.com/watch?v=_DxP2qVulDM) · 24 Mar 2026 · 17:39 · [watch](https://www.youtube.com/watch?v=_DxP2qVulDM)

From: [How I Built an AI SEO Agent to Rank #1 in 10 Minutes (Claude Code)](https://www.youtube.com/watch?v=vKBVCIU2fzo) · 23 May 2026 · 20:40 · [watch](https://www.youtube.com/watch?v=vKBVCIU2fzo)

**Two creators plug the same paid data service, DataForSEO, into Claude Code so it can read real search numbers instead of guessing them. The idea is sound. The data is Google's, not Etsy's.**

## ⚠ Read this first

Ryan sells his keyword skill and skips the setup, saying it is in another video. Sandy's video is sponsored by DataForSEO, and the site she audits and fixes is her own. So neither video shows the whole build. The build below fills the gaps from DataForSEO's own setup page and Claude Code's own help text, both read on 16 Sep 2026. It needs neither the paid skill nor the missing video.

# ⭐⭐ THE ONE THING — don't ask a model for numbers it doesn't have

Ask Claude "what do people search for?" and it gives a confident answer from memory. Ryan's point is that the model is not reading live data.

> "they're not up-to-date 24/7"

([2:32](https://www.youtube.com/watch?v=_DxP2qVulDM&t=152s)) Connect a data service, and the same question comes back with real columns. His came back with monthly search volume, keyword difficulty and cost per click ([7:31](https://www.youtube.com/watch?v=_DxP2qVulDM&t=451s)).

```
   ASK THE MODEL               ASK THE MODEL + DATA SERVICE
   ─────────────               ────────────────────────────
   "people search for X"       Claude calls DataForSEO
   (from memory, undated)            │
                               real volume, difficulty,
                               cost per click, dated today
```

## Why this matters to you

Your rules say research comes before building, with a demand figure read this month and dated. This is a way to get that figure inside Claude Code, dated, without opening another tool.

⛔ But be clear about what it does not touch. You already rank #2 on Etsy AU for "dementia caregiver binder", and you have zero sales. Your gap is what happens after someone sees a listing. Search data can't see that. This recipe is for choosing and wording the NEXT product, not for fixing the current one.

# ⚠ THE BIG CAVEAT — this is Google, not Etsy

Everything both videos pull is Google search (and AI chatbot answers). Your Etsy ranking was measured by searching Etsy itself, logged out. That is still the only way to know where you rank on Etsy.

I searched DataForSEO's docs index page on 16 Sep 2026 for "etsy" and found nothing. It does list Google, Bing and Amazon.

| It CAN tell you | It CAN'T tell you |
| --- | --- |
| How often a phrase is searched on Google, by country | How often it is searched on Etsy |
| Which wording people use: "caregiver binder" vs "care planner" | Where your listing ranks in Etsy search |
| Whether a phrase is growing or shrinking over 12 months | Whether an Etsy shopper clicks, favourites or buys |
| What pages Google shows for a phrase, which may include Etsy listings | Why your listings have zero sales |
| What ChatGPT or Gemini recommend when asked | Anything about Etsy ads or Etsy's own algorithm |

⭐ Google volume is a fair proxy for "does this need exist, and what do people call it". It isn't a proxy for Etsy demand.

# How each video builds it

## Ryan: a keyword skill

1. Write a keyword research skill. He sells his, but says to write your own first ([1:31](https://www.youtube.com/watch?v=_DxP2qVulDM&t=91s)).
2. Connect DataForSEO or Ahrefs ([3:32](https://www.youtube.com/watch?v=_DxP2qVulDM&t=212s)).
3. Ask the skill for keywords on a root topic, then tell it which rows you dislike and which columns to add. That updates the skill as you go ([8:30](https://www.youtube.com/watch?v=_DxP2qVulDM&t=510s)).
4. Hand a chosen keyword to a writing skill ([9:00](https://www.youtube.com/watch?v=_DxP2qVulDM&t=540s)).

> "Use my keyword research skill to find me 15 relevant and intentful keyword ideas based on the root topic of Claude code marketing."

⚠ The gap: at step 2 he says "I have a full other video showing you how to set this up, so I'm not going to do that in this video." ([5:30](https://www.youtube.com/watch?v=_DxP2qVulDM&t=330s)) All you see is the idea: paste DataForSEO's documentation link into Claude Code and ask for help, then give it your API login.

## Sandy: an "SEO agent" loop

```
   audit the site ──► ask AI engines who they recommend
        ▲                        │
        │               search volumes, 12-month trend,
        │               Google AI overview, competitors
        │                        │
   re-audit ◄──── Claude fixes the website
```

1. Get an API login and password from DataForSEO. The password is emailed ([6:00](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=360s)).
2. Paste a setup command with them into Claude Code, then check it with a list command ([7:00](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=420s)). ⚠ The command is on screen, not in the captions. They only say to paste "this right here".
3. Give Claude a research prompt ([8:30](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=510s)). She reads out part of it: who AI engines recommend in her niche, search volumes and trends, a Google AI overview check, and competitor patterns. ⚠ The full prompt is a skill she gives by email or in her paid community.
4. Have Claude fix the site. She calls this the step most people skip ([11:30](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=690s)).
5. Re-run the audit. She went from F to D ([19:00](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=1140s)).

⚠ Steps 4 and 5 need a website whose code you control. An Etsy listing isn't one, so for you they stop at step 3. She also says AI engines take "about 14 to 21 days" to notice changes ([12:02](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=722s)). So her F-to-D score comes from her own audit tool, not from AI engines naming her.

# The build, rewritten — no paid skill, no missing video

⛔ Signing up, accepting DataForSEO's terms and adding credit are yours to do. So is typing the password. Keep it out of the chat.

The setup, from DataForSEO's own GitHub page (read 16 Sep 2026): they run a hosted server at `https://mcp.dataforseo.com/v3/mcp`, and it signs in with OAuth. That means a browser login instead of a pasted password. Claude Code's own `claude mcp add --help` shows the matching command:

```
claude mcp add --transport http dataforseo https://mcp.dataforseo.com/v3/mcp
```

Then type `/mcp` in Claude Code, pick dataforseo and choose authenticate. Ryan does exactly that for Ahrefs ([13:01](https://www.youtube.com/watch?v=_DxP2qVulDM&t=781s)). ⚠ I haven't run this on your machines. Check it by reading `/mcp` back before trusting it.

The GitHub page also offers a local version that takes the login and password as settings. Sandy keeps hers in a `.env` file and changes the key often ([10:02](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=602s)).

# Money — every price the videos give

| Price | Who said it, and when |
| --- | --- |
| "you start with $1, which I know does not seem like a lot, which it is not." | Ryan, Mar 2026 ([5:01](https://www.youtube.com/watch?v=_DxP2qVulDM&t=301s)) |
| "about maybe 5 to 10 cents per output" | Ryan, Mar 2026 ([5:01](https://www.youtube.com/watch?v=_DxP2qVulDM&t=301s)) |
| $5 trial credit through her link, "instead of $1" | Sandy, May 2026, sponsored ([5:30](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=330s)) |
| "It cost 3 cents, guys, for us to do this." | Sandy, May 2026, her whole research step ([14:01](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=841s)) |
| Ahrefs API on its lowest plan, "$129 a month"; it was enterprise-only at about $1,500 | Ryan, Mar 2026 ([10:30](https://www.youtube.com/watch?v=_DxP2qVulDM&t=630s)) |
| SEO agencies at $5,000 to $20,000 a month | Sandy, May 2026 ([13:00](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=780s)) |

⚠ Ryan's 5 to 10 cents a run sits right on your 10c ask line. So every run needs a stated price first. Sandy says spending comes off a prepaid deposit ([11:01](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=661s)), which should cap spending at the balance (not tested here). Topping it up is money, so it goes to you.

⚠ Both creators run with bypass permissions ([7:00](https://www.youtube.com/watch?v=_DxP2qVulDM&t=420s), [17:31](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=1051s)). With paid calls, that means no pause before spending. Ryan himself suggests plan mode the first time. See Recipe 09.

# What to try — one step, tonight

Only if you are choosing the next product. It does nothing for the current zero-sales problem.

```
1. YOU: sign up at DataForSEO, then run the one
   claude mcp add line above in your own terminal,
   then /mcp → authenticate

2. In plan mode, paste the prompt below

3. Read the price it states. Under 10c: say go.
   10c or more: stop.
```

The prompt:

> Using only the DataForSEO MCP, get Google search volume in Australia, with a 12-month trend, for these 10 phrases: [your phrases]. Before any paid call, state the endpoint and estimated cost. After it, report the real cost from the API response. Label the result "Google, not Etsy", with today's date.

Then search the best two phrases on Etsy yourself, logged out, the way you measured your rankings. The Google number says the need exists. Only the Etsy search says who you'd be up against.

## ALSO MENTIONED

- Ryan uses Ahrefs for backlink checks, his own and competitors' ([16:02](https://www.youtube.com/watch?v=_DxP2qVulDM&t=962s)). You need a paid Ahrefs account for any of it.
- After changing data services, he had to update the skill to use the new one ([13:30](https://www.youtube.com/watch?v=_DxP2qVulDM&t=810s)).
- Sandy's reason for live data: chatbot answers are personalised to your past chats ([4:31](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=271s)).
- ⚠ Sandy says "Almost 77% of the people in the US" use AI instead of Google to search ([2:02](https://www.youtube.com/watch?v=vKBVCIU2fzo&t=122s)). She gives no source.
- ⚠ Asking ChatGPT or Gemini through DataForSEO is a third-party route. It isn't your Vertex route for Gemini, so decide whether that's allowed before you use it.

## See also

- RECIPE 09 — plan mode, which both creators turned off here.
- RECIPE 04 — the grader pattern, for checking what you write with these keywords.
- RECIPE 08 — your tool stack, where a data service would sit.
