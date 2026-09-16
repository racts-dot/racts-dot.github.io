# RECIPE 20 — CLAUDE.md built by interview

From: [Claude Code Will 10X Your Productivity (ADVANCED COURSE)](https://www.youtube.com/watch?v=efaBaxDN_q8) · 16 Mar 2026 · 1:29:50 · [watch](https://www.youtube.com/watch?v=efaBaxDN_q8)

**Her way to write a CLAUDE.md: let Claude ask you questions one at a time, then have it write down what it learned so you never answer them again. It is aimed at someone with an empty file. Your files are the opposite of empty, so for you the useful version runs the other way: an interview to decide what to cut.**

# ⭐⭐ THE ONE THING — questions first, then write it down

Step one is her lazy-prompt habit. Type the task, then add:

> "Ask me clarifying questions and one at a time until you're 95% confident you can complete the task." ([23:31](https://www.youtube.com/watch?v=efaBaxDN_q8&t=1411s))

Step two, once the questions are answered:

> "Create a Claude.md file based on everything you've learned about my preferences and how I work." ([28:31](https://www.youtube.com/watch?v=efaBaxDN_q8&t=1711s))

```
a task with no context
        │
        ▼
Claude asks, one question at a time
        │
        ▼
you answer each one
        │
        ▼
"write what you learned into CLAUDE.md"
        │
        ▼
next session reads it, and skips the questions
```

Her reason is simple: "make sure Claude remembers it so we don't have to do that ever again" ([27:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=1621s)). She calls the file "the instruction manual for each project", and Claude reads it every time a session starts ([27:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=1650s), [28:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=1681s)).

⭐ For setting up a real project, she says it is "a really nice shortcut to just have Claude ask you clarifying questions and continuously write the Claude.md file" ([29:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=1741s)).

## Her three layers

| Layer | What she says it is | Where |
| --- | --- | --- |
| Project CLAUDE.md | the manual for one folder | [54:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3241s) |
| Global CLAUDE.md | "a meta instruction manual" for every project | [54:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3270s) |
| Claude's own memory | "Claude's personal notebook" | [54:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3270s) |

Her advice for most people: "focus just on continually updating your Claude MD file" ([55:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3301s)).

# ⚠ Why the lesson for you is probably pruning

She warns about the opposite problem from yours:

> "one common mistake people make is they just make it once and then never update it" ([30:00](https://www.youtube.com/watch?v=efaBaxDN_q8&t=1800s))

You update yours constantly. Measured on this Mac, 16 Sep, the three rule files that loaded into this chat:

| File | Size |
| --- | --- |
| ~/.claude/CLAUDE.md (global) | 35,720 bytes, 540 lines |
| ~/.claude/LESSONS.md | 8,441 bytes |
| ~/pf/CLAUDE.md (printables) | 16,365 bytes |

⚠ Those three are not the whole load. Other folders have their own. The copy under home-notes/costway-scraper is 46,572 bytes. The handover register, which your global file says is injected at every session start, measured 421,256 bytes today.

Her whiteboard picture of the context window explains why size matters. When too much is on the board, "it can be difficult for AI to distinguish which information is actually important" ([36:30](https://www.youtube.com/watch?v=efaBaxDN_q8&t=2190s)). She says answers get worse as the context gets large.

⚠ This next point is my inference, not hers. She says it about long chats. A rule file is loaded into every chat before you type anything, so the same whiteboard problem starts at the first message.

⭐ Her own tool points the same way. She suggests a refactor once you have several projects: pull what they share into one global file ([56:32](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3392s), [57:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3421s)). ⚠ My reading, not her words: a rule kept once at the top does not need repeating in each project file. Her real content file is "really, really long and extensive" ([30:00](https://www.youtube.com/watch?v=efaBaxDN_q8&t=1800s)). She never says how long, so there is no size to compare with yours.

```
HER READER                     YOU
──────────                     ───
empty file                     60+ KB loading per chat
interview to ADD               interview to CUT
"what do you prefer?"          "is this rule still needed?"
```

# The interview, turned around

Same shape as hers: one question at a time, and you answer. The questions change.

1. Is this rule still true?
2. Does a hook already enforce it? If so, does the prose still need to be here?
3. Is it written twice, in two files?
4. Is it a story about why, which could move to a history file?
5. Does it apply to this folder, or every folder?

⛔ Your rule files are standing configuration and shared across both machines. Nothing gets deleted or moved without your yes. The step below only produces a list.

# What to try — one step, tonight

Read-only. It changes no file.

```
1. open a chat in plan mode (Recipe 09) and paste:

   Read ~/.claude/CLAUDE.md. Do not edit anything.
   Interview me about it ONE rule at a time, starting
   with the longest section. For each rule ask: still
   true? already enforced by a hook? written twice?
   story that could move out? Wait for my answer
   before the next one. After 10 rules, stop and show
   a table: rule, my answer, keep / shorten / move /
   cut, and bytes saved.

2. answer 10. Stop there.

3. keep the table. Decide on it another day.
```

⚠ Use your strongest model for this. Deciding whether a rule is still needed is a judgement, and your rule keeps Haiku out of judging.

## ALSO MENTIONED

- She runs a /learn skill after long sessions. It "makes Claude reflect on the conversation and update the Claude.md file" ([29:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=1741s)). ⚠ That keeps adding, so it makes your problem bigger unless something also cuts. Recipe 09 already covers her end-of-session habit.
- She updates hers "almost on a daily basis, for sure on a weekly basis" ([30:00](https://www.youtube.com/watch?v=efaBaxDN_q8&t=1800s)).
- Her content file includes autonomy rules, caption types per platform, character limits and where to find brand voice templates ([30:31](https://www.youtube.com/watch?v=efaBaxDN_q8&t=1831s)).
- A global file from repeated habits: "create a global claude.md file based on things you've seen me do repeatedly in multiple projects" ([56:00](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3360s)).
- /insights suggests CLAUDE.md changes, and she suggests running it about once a week ([57:31](https://www.youtube.com/watch?v=efaBaxDN_q8&t=3451s), [1:28:00](https://www.youtube.com/watch?v=efaBaxDN_q8&t=5280s)). Recipe 02 covers /insights.
- In plan mode, Claude may interview you before planning. You can answer by number, or pick "skip interview and plan immediately" ([34:01](https://www.youtube.com/watch?v=efaBaxDN_q8&t=2041s)). Recipe 09 covers plan mode.

## See also

RECIPE 01, AI social media manager: the same "95% confident" prompt, used to build a skill. RECIPE 02, seven Claude commands: /insights and /clear. RECIPE 09, plan mode and quality gates: plan mode and the end-of-session CLAUDE.md habit. RECIPE 18 and RECIPE 19 come from the same video.
