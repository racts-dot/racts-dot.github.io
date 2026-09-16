/* Priest Hood: bottom navigation bar and sideways swipe between sections (written by site_shell.py).
   Rachel, 17 Sep 2026: "I'd like the bottom thing to be able to navigate the sections that I need to navigate".
   The sections come from the page itself (D.sections), in the order the home screen lists them. */
(function () {
  "use strict";
  if (typeof D === "undefined" || !D.sections || document.querySelector("nav.ph-bar")) return;
  var SHORT = { names: "Names", angels: "Angels", demons: "Demons", elements: "Elements", ordinances: "Ordinances" };
  var TABS = [{ id: "", label: "Home" }].concat(D.sections.map(function (s) {
    return { id: s.id, label: SHORT[s.id] || s.title.split(" ")[0], title: s.title };
  }));

  var css = document.createElement("style");
  css.textContent =
    "body{padding-bottom:calc(4.25rem + env(safe-area-inset-bottom))}" +
    "nav.ph-bar{position:fixed;left:0;right:0;bottom:0;z-index:40;background:var(--panel);border-top:1px solid var(--line);" +
    "padding:0 .25rem env(safe-area-inset-bottom);display:flex;overflow-x:auto;scrollbar-width:none;" +
    "box-shadow:0 -2px 10px rgba(0,0,0,.06)}" +
    "nav.ph-bar::-webkit-scrollbar{display:none}" +
    "nav.ph-bar a{flex:1 0 auto;min-width:3.5rem;min-height:3.5rem;display:flex;align-items:center;justify-content:center;" +
    "padding:.25rem .375rem;font-size:.75rem;font-weight:600;color:var(--soft);text-decoration:none;white-space:nowrap;" +
    "border-top:3px solid transparent;-webkit-tap-highlight-color:transparent}" +
    "nav.ph-bar a[aria-current=page]{color:var(--accent);border-top-color:var(--accent)}" +
    "nav.ph-bar a:focus-visible{outline-offset:-3px}";
  document.head.appendChild(css);

  var nav = document.createElement("nav");
  nav.className = "ph-bar";
  nav.setAttribute("aria-label", "Sections");
  TABS.forEach(function (t) {
    var a = document.createElement("a");
    a.href = "#" + t.id;
    a.textContent = t.label;
    if (t.title) a.title = t.title;
    a.addEventListener("click", function () { setTimeout(function () { window.scrollTo(0, 0); }, 0); });
    nav.appendChild(a);
  });
  document.body.appendChild(nav);

  function current() {
    var id = decodeURIComponent(location.hash.replace(/^#/, ""));
    for (var i = 1; i < TABS.length; i++) if (TABS[i].id === id) return i;
    return 0;
  }
  function mark() {
    var k = current(), links = nav.querySelectorAll("a");
    for (var i = 0; i < links.length; i++) {
      if (i === k) links[i].setAttribute("aria-current", "page"); else links[i].removeAttribute("aria-current");
    }
    var on = links[k];
    if (on && nav.scrollWidth > nav.clientWidth) on.scrollIntoView({ block: "nearest", inline: "center" });
  }
  function go(step) {
    var k = current() + step;
    if (k < 0 || k >= TABS.length) return;
    location.hash = TABS[k].id;
    window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", mark);
  mark();

  // A sideways swipe moves to the next or previous section, in the order of the bar.
  // Not while a card is open, not from the phone's own edge-swipe zone, not while selecting words,
  // not on a text box, the bar or the bubbles, and not on something that scrolls sideways itself.
  // A swipe that starts on an entry still counts: the entries are most of each section screen.
  function scrollsSideways(node) {
    for (; node && node !== document.body; node = node.parentElement) {
      var ox = getComputedStyle(node).overflowX;
      if ((ox === "auto" || ox === "scroll") && node.scrollWidth > node.clientWidth + 2) return true;
    }
    return false;
  }
  var sx = 0, sy = 0, st = 0, armed = false;
  document.addEventListener("touchstart", function (e) {
    armed = false;
    if (e.touches.length !== 1) return;
    var t = e.touches[0], tg = e.target;
    if (document.querySelector("dialog[open]")) return;
    if (t.clientX < 28 || t.clientX > window.innerWidth - 28) return;
    if (tg.closest && tg.closest("input,textarea,select,nav.ph-bar,.ts-fab,.fb-fab,.sa-fab,.ts-panel,.fb-panel,.sa-panel")) return;
    if (scrollsSideways(tg)) return;
    sx = t.clientX; sy = t.clientY; st = Date.now(); armed = true;
  }, { passive: true });
  document.addEventListener("touchend", function (e) {
    if (!armed) return;
    armed = false;
    var t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy;
    if (Date.now() - st > 800 || Math.abs(dx) < 70 || Math.abs(dy) > Math.abs(dx) * 0.5) return;
    var sel = window.getSelection && window.getSelection();
    if (sel && !sel.isCollapsed) return;
    go(dx < 0 ? 1 : -1);
  }, { passive: true });
})();
