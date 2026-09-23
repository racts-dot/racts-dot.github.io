/* frame.js — ONE tag that gives an app its whole frame.
 *
 * WHY, measured 23 Sep 2026 on the live pages (not read off any summary):
 *   - 23 reachable apps each hand-list 5 to 10 separate kit tags, in a different
 *     ORDER and a different SUBSET every time.
 *   - Three path styles are in use for the SAME files: "/marks.js", "../marks.js"
 *     and "https://racts-dot.github.io/marks.js". /study/ uses all three at once.
 *   - Cache-busting is per app: "?v=fold1", "?v=20260920d", "?v=20260920b", or
 *     nothing at all. An app with no ?v can serve a stale kit file for ever while
 *     the app next to it gets the new one.
 *   - 4 apps carry NO kit-dock.js: board.html, app.html, /daily-chapter/, /ledgers/.
 *     Measured on the AI Handoff Board at 375x812 that day: .fb-fab at (12,520),
 *     .sa-fab at (12,576), .ts-fab at (12,628) — three 44px buttons stacked down
 *     the left edge, over the body text. That is exactly the fault her 20 Sep
 *     words named ("takes too much spacr ... Too big") and that kit-dock.js fixed
 *     on 21 Sep. The fix shipped; four apps never got it, because getting it meant
 *     somebody editing each page by hand.
 *   - status/app_kit_check.py reported all four as complete, because it checks that
 *     a page REFERENCES the pieces, and the dock is not one of the pieces it checks.
 *
 * So the defect is not any one app. It is that the frame has no single definition.
 * This file is that definition. A page carries one tag:
 *
 *     <script src="/frame.js" data-app="Prompt Cookbook" defer></script>
 *
 * and gets: Aa, Read aloud, Hear-the-selection, the mic, swipe, pull-to-refresh,
 * Notion, highlights and notes, and the dock they all sit in — in a fixed order,
 * from one place, with one cache stamp.
 *
 * WHAT A PAGE MAY SAY ON THE TAG (everything is optional):
 *   data-app="Prompt Cookbook"   name shown on feedback and on marks in Notion
 *   data-swipe-select="#tool"    swipe steps this menu          (swipe.js)
 *   data-swipe-links="#nav a"    swipe steps these links        (swipe.js)
 *   data-swipe-sections="section"  swipe scrolls these blocks   (swipe.js)
 *   data-swipe-pages="./ a.html" swipe opens the next page      (swipe.js)
 *   data-swipe="own"             the page has its OWN swipe — load only the hint
 *   data-speak="icon-only"       small Read-aloud button
 *   data-notion="quiet"          no Notion chip until it is needed
 *   data-omit="notion,marks"     leave pieces out ON PURPOSE. Say why in
 *                                status/app_frame_check.py, or the check fails:
 *                                an omission with no reason is indistinguishable
 *                                from a piece somebody forgot.
 *
 * WHAT IT DOES NOT DO: it never replaces a piece a page already loads itself.
 * During the migration a page may carry both the old tags and this one; each piece
 * is skipped if a tag for it is already on the page. So a half-migrated page is
 * never a double-loaded page.
 *
 * WHAT IT PROVES: window.APP_FRAME.loaded / .failed are written at RUNTIME, so a
 * piece that 404s is visible instead of silent. On 18 Sep two kit scripts 404'd on
 * a page that scored 5/5 on the reference check. A reference is not a load.
 */
(function () {
  "use strict";
  if (window.APP_FRAME) return;

  var VERSION = "20260923a";        // ONE stamp for every piece, every app.

  var me = document.currentScript ||
           document.querySelector('script[src*="frame.js"]');
  if (!me) return;                   // nothing sane to do without our own tag

  var d = me.dataset || {};
  var base = me.src.replace(/frame\.js(\?.*)?$/, "");   // pieces sit beside us
  var omit = (d.omit || "").split(",").map(function (s) { return s.trim(); })
                           .filter(Boolean);

  var state = { version: VERSION, base: base, loaded: [], failed: [],
                skipped: [], mixed: [], omitted: omit.slice() };
  window.APP_FRAME = state;

  function already(p) {
    // Is this COMPONENT already on the page? Asked per component, not per
    // filename: swipe.js and swipe-hint.js are two implementations of one thing,
    // and the first draft could load the hint on top of a page's own swipe.js
    // because it only looked for the file it had decided to use.
    var names = p.alternatives || [p.file];
    for (var i = 0; i < names.length; i++) {
      var t = document.querySelector('script[src*="' + names[i] +
                                     '"]:not([src*="frame.js"])');
      if (t) return t;
    }
    return null;
  }

  // A skipped piece is not a harmless skip: the page's own tag may carry an OLD
  // cache stamp (?v=fold1, ?v=20260920d, or none at all), so a half-migrated page
  // can run one piece from September beside another from today. The 23 Sep 2026
  // review called that the real risk in this design, and it is right. Nothing here
  // can fix it — only finishing the migration can — so it is made LOUD instead of
  // silent, and state.mixed is what a check can read.
  function noteMixed(file, tag) {
    var src = tag.getAttribute("src") || "";
    var v = (src.match(/[?&]v=([^&]*)/) || [])[1] || "(no version)";
    if (v === VERSION) return;
    state.mixed.push({ file: file, pageVersion: v, frameVersion: VERSION });
    if (window.console) {
      console.warn("[frame.js] " + file + " is loaded by the page itself at " +
                   v + ", not by the frame at " + VERSION +
                   " — finish this page's migration.");
    }
  }

  // ORDER IS DELIBERATE, and the dock is last on purpose: kit-dock.js adopts the
  // buttons the other pieces make, and re-measures whenever one more appears.
  // There is NO defer flag here on purpose. A first draft carried one, and the
  // 23 Sep 2026 review was right that it would have been dead code: `defer` has
  // no effect on a script made with createElement, only on one the parser found.
  // The thing that actually holds the order below is `async = false`.
  // There is NO defer flag here on purpose. A first draft carried one, and the
  // 23 Sep 2026 review was right that it would have been dead code: `defer` has
  // no effect on a script made with createElement, only on one the parser found.
  // The thing that actually holds the order below is `async = false`.
  //
  // KEY is the component and never changes. FILE is only which implementation of
  // it gets loaded. The second review (gpt-5.6-sol, 23 Sep) found a real bug in
  // the first draft: swipe's KEY was rewritten to "swipe-hint" before the omit
  // test ran, so data-omit="swipe" silently did nothing, and a page that already
  // had swipe.js could still be given the hint on top. Identity and implementation
  // are separate now, and every check below uses the key.
  //
  // ORDER IS DELIBERATE, and the dock is last on purpose: kit-dock.js adopts the
  // buttons the other pieces make, and re-measures whenever one more appears.
  var pieces = [
    { key: "textsize", file: "textsize.js",    marker: "TextSize",   sees: ".ts-fab",  attrs: {} },
    // speak.js returns at its own line 26 on a browser with no speech engine, and
    // then builds nothing. That is not a fault, so it must not read as one.
    { key: "speak",    file: "speak.js",       marker: "SpeakAloud", sees: ".sa-fab",
      needs: function () { return "speechSynthesis" in window; }, attrs: {} },
    { key: "hearsel",  file: "hearsel.js",     marker: "__hearSel",  attrs: {} },
    { key: "feedback", file: "feedback.js",    marker: "AppFeedback", sees: ".fb-fab", attrs: {} },
    { key: "notion",   file: "notion-sync.js", marker: "NotionSync", attrs: {} },
    { key: "marks",    file: "marks.js",       marker: "__appMarks", sees: ".am-bar", attrs: {} },
    { key: "pull",     file: "pull.js",        marker: "__appPull",  sees: ".app-pull", attrs: {} },
    { key: "swipe",    file: "swipe.js",       marker: "__swipeJs",  attrs: {},
      hintMarker: "__swipeHint",
      alternatives: ["swipe.js", "swipe-hint.js"] },
    { key: "dock",     file: "kit-dock.js",    marker: "__kitDock",  sees: "#kit-dock", attrs: {} }
  ];

  // --- per-app settings, read off our one tag -------------------------------
  var appName = d.app || document.title || "";
  if (appName) {
    byKey("feedback").attrs["data-app"] = appName;
    byKey("marks").attrs["data-app"] = appName;
  }

  if (d.speak === "icon-only") byKey("speak").attrs["data-icon-only"] = "";
  if (d.notion === "quiet")    byKey("notion").attrs["data-quiet"] = "";

  // Swipe is the one piece with real per-page configuration, so it is passed
  // through rather than guessed at.
  var sw = byKey("swipe");
  var swMap = { swipeSelect: "data-select", swipeLinks: "data-links",
                swipeSections: "data-sections", swipePages: "data-pages",
                swipeChips: "data-chips", swipeInput: "data-input" };
  var swAny = false;
  Object.keys(swMap).forEach(function (k) {
    if (d[k]) { sw.attrs[swMap[k]] = d[k]; swAny = true; }
  });
  if (d.swipe === "own" || (!swAny && !d.swipe)) {
    // Either the page swipes by its own code, or it gave swipe.js nothing to
    // move through — in both cases swipe.js would do nothing, and the HINT is
    // the part she asked for ("Where is the buttons", 21 Sep 2026).
    sw.file = "swipe-hint.js";   // the KEY stays "swipe" - see the note above
    sw.impl = "hint";
    sw.attrs = {};
  }

  function byKey(k) {
    for (var i = 0; i < pieces.length; i++) if (pieces[i].key === k) return pieces[i];
    return { attrs: {} };
  }

  // A file arriving is not a feature working. The 23 Sep review put it plainly:
  // `loaded` proves the browser evaluated the script, nothing more - and it
  // refused HTTP 200 and script.onload as evidence that the frame works. So every
  // component is also asked, a moment after loading, whether the thing it builds
  // is actually there: each kit file sets one global, and those names were READ
  // OFF the files, not guessed (two first guesses, __textSize and __speakJs, did
  // not exist - the real names are TextSize and SpeakAloud).
  //
  // state.ready[key] is true, false, or "unproven" where a component publishes
  // nothing to check. "unproven" is deliberately not "true": a check that cannot
  // fail is not a check.
  // HOW THIS CHECK WAS WRONG TWICE, MEASURED 23 Sep 2026 on a cold server with
  // 350 ms in front of every script:
  //   a single look at 400 ms called Read aloud BROKEN while it was still building;
  //   three looks ending at 4 s did the same.
  // CORRECTED 23 Sep 2026: the first version of this comment blamed speak.js for
  // waiting on the browser's voice list. That was a guess written up as a finding,
  // and it is false - speak.js publishes its global at its line 560, before the
  // line that asks for voices. The real cause was this file: it asked for a global
  // named __speakJs, which nothing on the site has ever defined.
  // A check that cries wolf on every cold load is worse than no check, so it no
  // longer guesses a deadline. It WATCHES: a component flips to true the moment it
  // appears, stays "pending" until then, and is only called false at a horizon far
  // beyond anything observed (15 s). Whoever wants a verdict sooner calls
  // APP_FRAME.check() and reads what is true AT THAT MOMENT - the deadline belongs
  // to the checker, not to the page.
  var HORIZON = 15000, STEP = 500, waited = 0;

  function verdict(final) {
    var out = {}, pending = 0;
    pieces.forEach(function (p) {
      if (omit.indexOf(p.key) !== -1) { out[p.key] = "omitted"; return; }
      if (p.needs && !p.needs()) { out[p.key] = "not applicable"; return; }
      // SEES beats MARKER. The 23 Sep verification round was blunt about this:
      // six of the nine globals are re-entry guards set on the file's FIRST line,
      // so window[marker] proves only "the file started", which is the very kind
      // of evidence the earlier review refused. Where a component puts something
      // on the page, that is what gets looked at.
      // Which implementation actually got loaded decides which name to look for:
      // swipe.js publishes __swipeJs, swipe-hint.js publishes __swipeHint. Asking
      // for the wrong one leaves the component "pending" for ever, which is what
      // the first cold run did.
      var mark = (p.impl === "hint" && p.hintMarker) ? p.hintMarker : p.marker;
      // The hint is a flash of text shown once per device; there is nothing on
      // the page to find a second later, so it is judged on having run.
      var look = (p.impl === "hint") ? null : p.sees;
      if (look && document.querySelector(look)) { out[p.key] = true; return; }
      if (!look && mark && window[mark]) { out[p.key] = true; return; }
      if (!look && !mark) { out[p.key] = "unproven"; return; }
      if (state.failed.indexOf(p.file) !== -1) { out[p.key] = false; return; }
      if (final) { out[p.key] = false; } else { out[p.key] = "pending"; pending++; }
    });
    out.__pending = pending;
    return out;
  }

  function settle() {
    if (settle.t) return;                    // one watcher, however many onloads
    settle.t = setInterval(function () {
      waited += STEP;
      var final = waited >= HORIZON;
      state.ready = verdict(final);
      var p = state.ready.__pending; delete state.ready.__pending;
      if (!p || final) {
        clearInterval(settle.t);
        state.settled = true;
        var bad = Object.keys(state.ready).filter(function (k) {
          return state.ready[k] === false;
        });
        if (bad.length && window.console) {
          console.error("[frame.js] loaded but not working: " + bad.join(", "));
        }
      }
    }, STEP);
  }

  state.check = function () {
    var v = verdict(false); delete v.__pending; return v;
  };

  // --- load, in order, and write down what actually happened ----------------
  pieces.forEach(function (p) {
    if (omit.indexOf(p.key) !== -1) return;              // left out on purpose
    var own = already(p);
    if (own) { state.skipped.push(p.file); noteMixed(p.file, own); return; }

    var s = document.createElement("script");
    s.src = base + p.file + "?v=" + VERSION;
    s.async = false;                 // keeps them in the order written above
    Object.keys(p.attrs).forEach(function (a) { s.setAttribute(a, p.attrs[a]); });
    s.onload  = function () { state.loaded.push(p.file); settle(); };
    s.onerror = function () {
      state.failed.push(p.file);
      settle();                 // a piece that 404s must still reach a verdict
      // Loud on purpose. A kit piece that 404s used to be invisible.
      if (window.console) console.error("[frame.js] kit piece failed to load: " + s.src);
    };
    document.head.appendChild(s);
  });

  // A page where every piece was already present creates no script at all, so no
  // onload ever fires. Without this line that page never reaches a verdict and
  // APP_FRAME.ready stays undefined for ever - which reads exactly like "fine".
  settle();
})();
