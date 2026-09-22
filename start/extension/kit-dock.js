/* kit-dock.js — put the kit controls in a bottom dock instead of on top of the text.
 *
 * WHY, measured 21 Sep 2026 on https://racts-dot.github.io/rules/ at 375x812:
 *   .fb-fab  44x44 at left:12, top 520
 *   .sa-fab  44x44 at left:12, top 576
 *   .ts-fab  44x44 at left:12, top 648
 * A 172px column of position:fixed buttons down the left edge, floating OVER the
 * body text. A screenshot showed a heading rendering as "T A SESSION ACTUALLY
 * LOADS" and three lines of body copy partly covered. A fourth fixed element,
 * the 137x33 "Connect to Notion" chip, overlaid the bottom-right corner.
 *
 * Her feedback, 20 Sep: "The tap to speak takes too much spacr as well as the
 * feedback for this app is like 1/5. Too big".
 *
 * Two reviewers, blind to each other, 21 Sep, both landed on the same fix and
 * both warned about the same two ways of getting it wrong:
 *   - A bottom bar WITHOUT content clearance just moves the overlap from the
 *     left edge to the bottom edge. So this injects padding, and measures it.
 *   - The Notion chip is already fixed bottom-right and will collide with a
 *     bottom bar. So this adopts the chip into the dock too.
 * Both also advised AGAINST folding the three behind one button, which was the
 * direction Rachel was leaning: read-aloud is the control she uses most, and a
 * fold costs it a second tap. `[HUMAN 2026-09-21]` she chose the dock.
 *
 * The controls are created asynchronously by three separate files, so this
 * cannot simply query once at load. It adopts whatever appears, whenever it
 * appears, and re-measures clearance when the dock's height changes.
 */
(function () {
  "use strict";
  if (window.__kitDock) return;
  window.__kitDock = true;

  var DOCK_ID = "kit-dock";
  // Order is deliberate: read-aloud sits in the middle, under the thumb.
  var WANTED = [
    ".fb-fab",
    ".sa-fab",
    ".ts-fab",
    '[aria-label="Connect this app to Notion"]'
  ];

  function css() {
    if (document.getElementById(DOCK_ID + "-css")) return;
    var s = document.createElement("style");
    s.id = DOCK_ID + "-css";
    s.textContent =
      "#" + DOCK_ID + "{position:fixed;left:0;right:0;bottom:0;z-index:2147483644;" +
      "display:flex;gap:10px;align-items:center;justify-content:center;flex-wrap:nowrap;" +
      "padding:8px 12px calc(8px + env(safe-area-inset-bottom));box-sizing:border-box;" +
      "background:rgba(255,255,255,.94);border-top:1px solid rgba(0,0,0,.08);" +
      "-webkit-backdrop-filter:saturate(180%) blur(14px);backdrop-filter:saturate(180%) blur(14px)}" +
      "@media (prefers-color-scheme:dark){#" + DOCK_ID + "{background:rgba(28,28,30,.94);" +
      "border-top-color:rgba(255,255,255,.12)}}" +
      // Inside the dock a control is a flex item, not a floating element. The
      // !important is not decoration: each control sets position:fixed in its
      // own stylesheet and would otherwise ignore the dock entirely.
      "#" + DOCK_ID + ">*{position:static !important;left:auto !important;right:auto !important;" +
      "top:auto !important;bottom:auto !important;margin:0 !important;flex:0 0 auto}" +
      // The chip is wider than the round buttons; let it shrink before they do.
      "#" + DOCK_ID + ">button[aria-label='Connect this app to Notion']{flex:0 1 auto;" +
      "overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:46vw}" +
      // FOLDED - `[HUMAN 2026-09-21]` her words: "Make it foldable. It is
      // obstructing things." Folded is the DEFAULT: the dock shrinks to one
      // small tab in the bottom-right corner; tapping it opens the controls.
      ".kd-toggle{width:34px;height:34px;border-radius:17px;border:1px solid rgba(0,0,0,.15);" +
      "background:rgba(255,255,255,.94);color:#333;font:600 18px/1 system-ui,sans-serif;" +
      "padding:0;cursor:pointer;box-shadow:0 1px 4px rgba(0,0,0,.18)}" +
      "#" + DOCK_ID + ".kd-folded{left:auto;right:10px;bottom:10px;padding:0;background:none;" +
      "border:0;-webkit-backdrop-filter:none;backdrop-filter:none}" +
      "#" + DOCK_ID + ".kd-folded>*:not(.kd-toggle){display:none !important}";
    (document.head || document.documentElement).appendChild(s);
  }

  function dock() {
    var d = document.getElementById(DOCK_ID);
    if (!d) {
      d = document.createElement("div");
      d.id = DOCK_ID;
      d.setAttribute("role", "toolbar");
      d.setAttribute("aria-label", "App controls");
      var tg = document.createElement("button");
      tg.type = "button";
      tg.className = "kd-toggle";
      tg.addEventListener("click", function () { setFolded(!isFolded()); });
      d.appendChild(tg);
      document.body.appendChild(d);
      var open = false;
      try { open = localStorage.getItem("kitDockOpen") === "1"; } catch (e) {}
      setFolded(!open);
    }
    return d;
  }

  function isFolded() {
    var d = document.getElementById(DOCK_ID);
    return !!(d && d.classList.contains("kd-folded"));
  }

  function setFolded(f) {
    var d = document.getElementById(DOCK_ID);
    if (!d) return;
    d.classList.toggle("kd-folded", f);
    var tg = d.querySelector(".kd-toggle");
    if (tg) {
      tg.textContent = f ? "⋯" : "×";   // ⋯ folded, × open
      tg.setAttribute("aria-label", f ? "Show app controls" : "Hide app controls");
      tg.setAttribute("aria-expanded", f ? "false" : "true");
    }
    try { localStorage.setItem("kitDockOpen", f ? "0" : "1"); } catch (e) {}
    clearance();
  }

  /* Keep the page scrollable clear of the dock. Both reviewers named the
     absence of this as the thing that turns a bottom bar into a new overlap. */
  function clearance() {
    var d = document.getElementById(DOCK_ID);
    if (!d || !document.body) return;
    var h = d.offsetHeight;
    if (!h) return;
    document.body.style.setProperty("padding-bottom", h + 16 + "px", "important");
  }

  function adopt() {
    if (!document.body) return;
    css();
    var moved = 0, d = null;
    WANTED.forEach(function (sel) {
      var el = document.querySelector(sel);
      if (!el) return;
      if (el.parentNode && el.parentNode.id === DOCK_ID) return;
      d = d || dock();
      d.appendChild(el);
      moved++;
    });
    if (moved) clearance();
    return moved;
  }

  function start() {
    adopt();
    // The three kit files create their buttons at different times, and some
    // apps re-render. Watch rather than poll a fixed number of times.
    try {
      new MutationObserver(function () { adopt(); })
        .observe(document.body, { childList: true, subtree: false });
    } catch (e) { /* observer unsupported: the interval below still covers it */ }
    var n = 0, t = setInterval(function () {
      adopt();
      if (++n > 40) clearInterval(t);          // ~20s, then stop
    }, 500);
    try {
      new ResizeObserver(clearance).observe(dock());
    } catch (e) {
      window.addEventListener("resize", clearance);
    }
    window.addEventListener("orientationchange", clearance);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", start);
  } else {
    start();
  }

  /* Exposed so a check can assert the dock is real and nothing overlaps text,
     which is the thing the existing kit check cannot see: it searches the
     served HTML for the WORD naming each piece, and a reference is not a
     working feature (19 Sep lesson). */
  window.KitDock = {
    controls: function () {
      var d = document.getElementById(DOCK_ID);
      return d ? Array.prototype.filter.call(d.children, function (c) {
        return !c.classList.contains("kd-toggle");
      }) : [];
    },
    overlaps: function (textSelector) {
      var d = document.getElementById(DOCK_ID);
      var t = document.querySelector(textSelector || "body");
      if (!d || !t) return null;
      var a = d.getBoundingClientRect();
      var hits = [];
      Array.prototype.forEach.call(t.querySelectorAll("p,h1,h2,h3,li,td"), function (el) {
        var r = el.getBoundingClientRect();
        if (r.height && r.bottom > a.top && r.top < a.bottom &&
            r.right > a.left && r.left < a.right) {
          hits.push((el.textContent || "").trim().slice(0, 40));
        }
      });
      return hits;
    }
  };
})();
