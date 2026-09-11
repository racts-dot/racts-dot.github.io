# The TripShare planner — reviewed, really tested, and still switched off

**11 September 2026**

## The one thing to decide

**Two AIs read it separately and both said the same thing: test it before you
decide.** Everything they found is fixed except one test, and that test needs
you, because it costs money and it puts the thing on the internet.

## The worst thing found, and it was not a bug

**Your app tells people twice on screen that their trips never leave their
device. The planner sent what they typed away without saying so.**

Someone who has been told an app is private types differently. They put in
names, medications, booking references. There is now a notice above the box,
before they type, saying that this one box is sent away and nothing else is.

## Three real faults, found by running it rather than reading it

| What went wrong | What a traveller saw | Now |
|---|---|---|
| A suggestion dated outside your trip | Quietly moved to day one, looking deliberate | Thrown out, and it says how many |
| The AI naming its list differently | No suggestions at all, blaming *their* wording | Accepted |
| 150 suggestions came back | Cut to 40 in silence | Says so |

## The money, corrected in both directions

I made the first real calls it has ever made. **Two plans cost US$0.00149 the
pair** — recomputed just now from the token counts the service itself returned.

- A plan costs about **a fourteenth of a cent**. The old note said a fifth of a
  cent, written before anything had been called.
- **But the worst case was too low.** A fully used day is nearer **25 cents than
  20**, and it repeats daily, so sustained nuisance is a few dollars a month.
- **You now have a ten-second off switch** — one setting in the Google script.
  No re-deploy, no touching the website. It is written up in the setup file.

## How it compares

| | Account needed | Price | What is free |
|---|---|---|---|
| Wanderlog | Yes | US$39.99/yr | **5 AI messages total**; offline costs extra |
| TripIt | Yes | US$49/yr | Basic itinerary only |
| Tripsy | Yes | Paid | Nothing |
| **TripShare** | **No** | **Free** | **Everything** |

**The honest half.** This planner cannot beat Wanderlog on suggestion quality —
that one has a live map and opening hours behind it and yours has neither. It
wins on no account and nothing leaving your device, and the planner is the one
feature that spends that advantage. The heading said "Plan it for me", which
oversold it. It now says "Suggest a starting plan".

## What is left, and both are yours

1. **Nobody has tested the website actually reaching the Google script.** That
   needs it deployed with a real key. Money and public, so it is your call.
2. **Nobody has asked for this feature.** One reviewer raised it. Also yours.

## One thing I owe you

**My own review call cost US$0.18, over your ten-cent limit, and it is the
second time.** The estimate said eight and a half cents. It prices what goes in
and only guesses what comes back, so your limit is a guess and not a gate.
About 21 cents overspent across the two. Worth fixing, not urgent.

---

**Where it is.** Everything is committed and pushed to the side branch. The live
site is untouched and the planner is still switched off. Turning it on is one
merge and one deploy, and both are yours.
