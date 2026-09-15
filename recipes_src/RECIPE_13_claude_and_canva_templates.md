# RECIPE 13 — Fill a Canva template from Claude without breaking it

From: [Claude + Canva Is the Content Creation Combo I Wish I Found Sooner](https://www.youtube.com/watch?v=MQjCyQBRZ_M) · 24 May 2026 · 27:47 · [watch](https://www.youtube.com/watch?v=MQjCyQBRZ_M)

From: [I Made 200 Social Posts in 10 Minutes With Claude + Canva](https://www.youtube.com/watch?v=FwWZ1ivy5F4) · 20 May 2026 · 14:49 · [watch](https://www.youtube.com/watch?v=FwWZ1ivy5F4)

From: [The Beginner's Guide to Claude + Canva (Start Here)](https://www.youtube.com/watch?v=pYuqMeP7ilk) · 3 Jun 2026 · 24:03 · a shorter re-edit of the first video, read in full, nothing new for this recipe

**Connect Canva inside claude.ai, clone a template you already like, and make Claude count the words in every text box before it writes anything. The design survives because the copy is cut to fit it.**

## ⚠ Read this first

All three videos are by Sabrina Ramonov, and the posting half sells her own app, Blotato. You can skip that half. The making half is free on claude.ai with a free Canva account.

⚠ The second title says 200 posts. On screen she makes one Instagram post from scratch and one seven-slide carousel. That is all.

# ⭐⭐ THE ONE THING — count the words before you replace them

She does not ask Claude to "make a flyer". She clones a Canva template, pastes its link, and reads out this prompt:

> "Analyze the following Canva template, especially the number of words per section."

> "Then ask me questions to replace the text with my information, roughly following the number of words per section."

Her reason, at [8:00](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=480s):

> "if you were to replace this with like five sentence paragraph, it just wouldn't look good."

```
   WHAT USUALLY HAPPENS          WHAT SHE DOES
   ────────────────────          ─────────────
   "put my info in this"         Claude reads the template
        │                             │
   long text pours in            counts words, box by box
        │                             │
   boxes overflow,               asks you for the facts
   layout breaks                      │
                                 writes to each box's count
                                      │
                                 you open it in Canva and look
```

A human designed the template, so the layout already works. Claude only has to respect it.

## Why this matters to you

Your shop is found. You rank #2 on Etsy AU for "dementia caregiver binder", with 46 live listings and zero sales as of 12 Sep 2026. So the unproven part is what happens after someone sees a listing.

Listing images are part of that. This recipe does not prove your images are the problem; nothing here measures that. It gives you a cheap way to make one alternative image from a template you chose, so you have something to test.

⭐ It also fits your rule against code-drawn art. The design comes from a Canva template a person made. Claude only writes the words into it.

# How it goes, step by step

## 1. Connect Canva (once)

In claude.ai: your name, bottom left, then Settings, then Connectors. Browse connectors, search Canva, press +, and allow ([1:00](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=60s)). She says you do not need Cowork, Desktop or Claude Code for this.

Then press Configure. Each Canva action is marked always allow or needs approval, and you can switch any of them ([2:30](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=150s)).

⚠ Connecting grants Canva access to your account. That is your click, not mine.

## 2. Ask what the connector can do

Her "product tour" prompt, from the second video at [2:01](https://www.youtube.com/watch?v=FwWZ1ivy5F4&t=121s):

> "List every Canva connector feature available. Output a bullet point list with a sample prompt for each feature and Canva plan required."

It returns a table of features, sample prompts, and free versus paid.

## 3. Clone a template, then fill it

In Canva: Home, Templates, search (flyer, carousel, infographic), pick one, press "Customize this template". That makes your own editable copy ([7:30](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=450s)). Paste its link into the prompt above.

She shows three ways to feed it the facts:

| Way | What she typed | Where |
|---|---|---|
| Claude interviews you | answered its questions for a hiring flyer | [9:01](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=541s) |
| A topic only | "nature heals founders" for a carousel | [11:30](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=690s) |
| Your website | "replace the text with information from my website" | [15:32](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=932s) |

For the carousel she approves each slide's copy before Claude builds it.

## 4. Open it in Canva and look

Everything saves to your Canva account and stays in sync. Hand edits in Canva are fine ([17:01](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=1021s)).

⚠ The fit is rough, not exact. In the second video one slide's text was "a little much" and overlapped, so she fixed it by hand ([7:30](https://www.youtube.com/watch?v=FwWZ1ivy5F4&t=450s)). Claude had already flagged it:

> "Claude actually said the subtitle positioning slightly overlaps with the text."

⭐ Read Claude's notes before you open the design. She did not, and it had caught the fault.

# Swapping in your own photos

She uploads her photos into the chat and asks Claude to swap the backgrounds ([12:30](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=750s)). Two limits:

- A landscape photo in a portrait slot failed: "It was not able to handle that horizontal photo that I was just testing out". Match the photo's shape to the slot.
- Her method runs through Blotato: "If you haven't set up Blotato yet, this obviously won't work." Without it, she warns, Claude tries workarounds and may hit problems.

⚠ So the photo swap is the one part the video only shows working with the paid app. It shows no free way. Uploading photos into Canva yourself might work, but that is my guess and it is untested.

⛔ If it is a product photo, the image must not change what the buyer gets. Swapping a background is one thing. Changing a page, a page count or a feature is misrepresentation.

# The two error fixes, word for word

She says the two errors are related, and both fixes name Blotato.

| Error you see | What she types |
|---|---|
| Canva export domain "not in my sandbox's network allow list" ([12:30](https://www.youtube.com/watch?v=FwWZ1ivy5F4&t=750s)) | "export from Canva and then pass the Canva export domain URLs directly to Blotato to post" ([20:00](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=1200s)) |
| Claude stuck uploading your photos, or trying to start an HTTP server ([13:30](https://www.youtube.com/watch?v=FwWZ1ivy5F4&t=810s)) | "use Blotato to upload my photos or videos so Canva can use them" ([20:31](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=1231s)) |

She says the reason the second works is that Blotato "has a media library endpoint". Once it works, she tells Claude to remember the fix.

⚠ Without Blotato, neither fix applies. For your use you do not need the first. Export the PNG or PDF from Canva by hand. Claude's own reply on screen offers PNG or PDF export ([5:01](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=301s)).

# Money, and what needs your yes

| Item | Price as stated | Date |
|---|---|---|
| claude.ai with the Canva connector | no price given | 24 May 2026 |
| Canva | "Many features will still work with a free Canva account" | 24 May 2026 |
| Canva brand kit | paid: "Notice it has this crown icon, which means it requires a paid plan." No figure given | 24 May 2026 |
| Blotato posting | "It does require a paid plan of $29 per month" | 24 May 2026 |
| Blotato, second video | "the lowest plan of $29 per month", 20 social accounts, "as of today, May 2026" | 20 May 2026 |

⚠ Blotato is her own app. Its "full refund, no questions asked" offer and its benefits have only her word behind them.

⛔ Posting is public. In the demo, Claude posted to Facebook and Instagram "right now". When Instagram rejected the size, Claude and Canva worked around it on their own with a square crop ([21:31](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=1291s)). Her own verdict: "I probably shouldn't have posted this really long infographic to Instagram." Any post goes to you first.

⚠ Not covered in any of the three videos: whether Canva's licence lets you use community templates in paid Etsy listing images. Check Canva's terms before a template goes on a listing.

# What to try — one image, tonight

```
   1. claude.ai → Settings → Connectors → add Canva
      (free Canva account is enough)

   2. In Canva, pick ONE template in a listing-image
      shape and press "Customize this template"

   3. Paste her two-line word-count prompt with that link.
      Give it the facts of ONE listing:
      title, what's inside, page count

   4. Read Claude's notes. Open it in Canva. Look.

   5. Export a PNG by hand. Do not post anything.
```

Cost: nothing beyond the claude.ai plan you already use. No API call, no Blotato.

⚠ Every number on the image must match the file the buyer downloads. Take the page count from the built PDF, not from memory.

⚠ Whether it looks premium is a judgement. Look at it yourself, and do not let a cheap model sign it off.

## ALSO MENTIONED

- Designs from scratch: Canva offers four options, you pick one and ask for changes in chat ([4:31](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=271s))
- A paid Canva brand kit (logo, colours, fonts) that Claude can use. She keeps several kits for several clients ([23:31](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=1411s))
- Blotato's calendar queue for scheduling batches of posts ([19:30](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=1170s))
- She adds Blotato as a custom connector at mcp.blotato.com/mcp ([18:30](https://www.youtube.com/watch?v=MQjCyQBRZ_M&t=1110s))
- Of the connector's features: "We really only touched the surface" ([14:00](https://www.youtube.com/watch?v=FwWZ1ivy5F4&t=840s))
- ⚠ The captions mishear Blotato many ways ("Vota", "Bloop to", "blue potato"). Quotes here keep only lines where it came through correctly

## See also

RECIPE 01 covers the Blotato posting half in full. RECIPE 04, the grader pattern, fits the copy Claude writes into the template: grade it against your banned words before you export. RECIPE 10 is the wider social automation family.
