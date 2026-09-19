# Rachel's start page as Chrome's new tab

Two files. Nothing is built, nothing is downloaded from anywhere.

1. Chrome → `chrome://extensions` → turn on **Developer mode** (top right).
2. **Load unpacked** → pick this folder (`website/start/newtab` on either computer).
3. Turn Momentum **off** (two extensions cannot both own the new tab).

Open a new tab. The page it shows is https://racts-dot.github.io/start/ so any change pushed
to the site is live in the next tab, with no reinstall.

If you would rather not install anything: Chrome → Settings → On startup → *Open a specific page*
→ `https://racts-dot.github.io/start/`. That covers opening Chrome, not every new tab.
