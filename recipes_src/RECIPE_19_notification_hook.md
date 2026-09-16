# RECIPE 19 — A hook that tells you when Claude is done

From: [Claude Code Will 10X Your Productivity (ADVANCED COURSE)](https://www.youtube.com/watch?v=efaBaxDN_q8) · 16 Mar 2026 · 1:29:50 · [watch](https://www.youtube.com/watch?v=efaBaxDN_q8)

**Her Claude Code moos when it finishes. It is a hook: a desktop notification plus a sound, set up by typing one sentence. You already run many hooks, so the setup is not the hard part for you. The hard parts are getting it into the right file, and keeping it from pinging you when a chat is not really done.**

# ⭐⭐ THE ONE THING — one sentence sets it up

Her prompt ([1:06:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3990s)):

> "Set up a hook so my Mac sends me a desktop notification every time you finish a long task." ([1:06:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3990s))

It goes on: she wants a sound too, "so I don't need to watch the screen". Hers shows "Cloud Code finished" in the top right corner ([1:06:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3990s)) and "plays a moo sound at 46% volume" ([1:07:00](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4020s)).

What a hook is, in her words:

> "when something happens with Claude Code, you can trigger something else to happen." ([16:31](https://www.youtube.com/watch?v=efaBaxDN_q8&t=991s))

And why it beats remembering:

> "you don't have to remember to run them. Like they will just happen." ([1:07:00](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4020s))

```
Claude finishes a turn
        │
        ▼
the hook fires  ──►  notification: "Claude Code finished"
                ──►  sound
        │
        ▼
you come back only when pinged
```

## Why this matters to you

You run many chats in parallel on two machines. Without a ping, you either keep checking every window or leave a chat waiting for you for an hour. A ping turns checking into waiting to be told.

# ⚠ What the video covers, and what it does not

The video covers **done**. Her hook fires "after Cloud Code completes" ([1:05:32](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3932s)).

It does not cover **needs you**: a chat stuck on a permission question. The only time she mentions that is on her phone, through remote control: "if Cloud Code gets stuck needing your permission, you'll see a request" ([1:23:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4981s)).

⚠ The rest of this section is not from the video. Claude Code has a separate hook event called Notification, for when it is waiting on you. "Done" is the Stop event. Ask for both by name.

```
EVENT          FIRES WHEN                      IN THE VIDEO?
─────          ──────────                      ─────────────
Stop           Claude finishes its turn        yes, the moo
Notification   Claude is waiting on you        no
```

# How it fits the hooks you already have

Checked on this Mac, 16 Sep:

| What | Count |
| --- | --- |
| Hook commands wired in ~/.claude/settings.json | 37 |
| Hook commands in the shared settings.template.json | 39 |
| Hooks on the Stop event, live | 16 |
| Hooks on the Notification event | 0 |

So you have no ping of either kind today. Three warnings follow from those numbers.

⛔ **A hook that is not listed in settings.json never runs.** Putting a script in ~/.claude/hooks does nothing by itself. The file only counts once settings.json names it. The template and the live file already differ by two today (both on SessionStart), so check the live file.

⚠ **Your settings.json is built from a shared template.** If the new hook goes only into the live file, the next rebuild can wipe it, and Windows never gets it. It belongs in settings.template.json as well. The Mac command will not work on Windows, which needs its own.

⚠ **A Stop ping can lie.** This is not from the video. Hooks on the same event run side by side. Some of your Stop hooks can block the stop and send Claude back to work. The ping may already have gone off by then. Test this before trusting the ping: run a chat that one of your gates will block, and see whether it pings.

# The noise problem

Her hook fires every time Claude finishes, including in "my other Cloud Code" ([1:05:32](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3932s)). With several chats going, every short reply in every chat would ping. Two cheap fixes:

1. Put the folder name in the notification text, so you know which chat it was.
2. Use a quiet sound for Stop and a louder one for Notification, since "needs you" is the one that costs you time.

# What to try — one step, tonight

This costs nothing and touches nothing public. It changes a settings file, so read the plan before approving it.

```
1. open a chat in plan mode (Recipe 09) and paste:

   Add two hooks on this Mac.
   Stop: a macOS notification "Claude done: <folder>"
   and the Glass sound.
   Notification: a notification "Claude needs you:
   <folder>" and the Hero sound.
   Add them to BOTH ~/.claude/settings.json and
   ~/.claude/settings.template.json. Change no other
   hook. Show me the diff before saving.

2. approve only if the diff adds exactly two entries
   and removes nothing

3. start a NEW chat (hooks load at start), type /hooks,
   and check both are listed

4. ask it something that needs a permission, walk
   away, and see if "needs you" arrives
```

⚠ The first macOS notification from a script may need you to allow notifications in System Settings. Glass and Hero are standard Mac sounds (both present in /System/Library/Sounds, checked 16 Sep).

## ALSO MENTIONED

- Her other hook is a quality gate that checks captions before posting: banned words, character limits, whether there is a video to post ([1:06:00](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3960s)). Recipes 04 and 09 cover that idea.
- When she typed her prompt, Claude answered that the hook already existed ([1:06:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3990s)). So you never see a new hook built on camera. If you run the prompt fresh, she says it will ask what the notification and sound should be ([1:07:00](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4020s)).
- Control B sends a running task to the background ([12:00](https://www.youtube.com/watch?v=efaBaxDN_q8&t=720s)).
- Remote control lets her approve permission requests from her phone ([1:23:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=4981s)).
- /loop tasks run only while the laptop is on and the session is open, and "expire after 3 days" ([1:24:32](https://www.youtube.com/watch?v=efaBaxDN_q8&t=5072s)). Recipe 02 covers /loop.

## See also

RECIPE 02, seven Claude commands: /loop, /btw and /insights. RECIPE 09, plan mode and quality gates: review the hook's diff in plan mode. RECIPE 11, loop engineering: /goal also runs on the Stop hook. RECIPE 18 and RECIPE 20 come from the same video.
