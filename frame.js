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

  function already(file) {
    // A tag for this piece is on the page already — the app loads it itself.
    return document.querySelector('script[src*="' + file +
                                  '"]:not([src*="frame.js"])');
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
  var pieces = [
    { key: "textsize",  file: "textsize.js",    attrs: {} },
    { key: "speak",     file: "speak.js",       attrs: {} },
    { key: "hearsel",   file: "hearsel.js",     attrs: {} },
    { key: "feedback",  file: "feedback.js",    attrs: {} },
    { key: "notion",    file: "notion-sync.js", attrs: {} },
    { key: "marks",     file: "marks.js",       attrs: {} },
    { key: "pull",      file: "pull.js",        attrs: {} },
    { key: "swipe",     file: "swipe.js",       attrs: {} },
    { key: "dock",      file: "kit-dock.js",    attrs: {} }
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
    sw.file = "swipe-hint.js";
    sw.key = "swipe-hint";
    sw.attrs = {};
  }

  function byKey(k) {
    for (var i = 0; i < pieces.length; i++) if (pieces[i].key === k) return pieces[i];
    return { attrs: {} };
  }

  // --- load, in order, and write down what actually happened ----------------
  pieces.forEach(function (p) {
    if (omit.indexOf(p.key) !== -1) return;              // left out on purpose
    var own = already(p.file);
    if (own) { state.skipped.push(p.file); noteMixed(p.file, own); return; }

    var s = document.createElement("script");
    s.src = base + p.file + "?v=" + VERSION;
    s.async = false;                 // keeps them in the order written above
    Object.keys(p.attrs).forEach(function (a) { s.setAttribute(a, p.attrs[a]); });
    s.onload  = function () { state.loaded.push(p.file); };
    s.onerror = function () {
      state.failed.push(p.file);
      // Loud on purpose. A kit piece that 404s used to be invisible.
      if (window.console) console.error("[frame.js] kit piece failed to load: " + s.src);
    };
    document.head.appendChild(s);
  });
})();
