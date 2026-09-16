/* Priest Hood: pull down to refresh.
   Rachel, 16 Sep 2026, from the home-screen app on her phone: "No drag down to refresh."
   An app saved to the iPhone home screen has no address bar and no reload button, and iOS gives it no
   pull-to-refresh of its own, so without this there was no way to fetch a newer copy short of closing it.

   How it behaves: at the very top of the page, drag down. A small pill follows the finger; past the line it
   says "Release to refresh". Letting go asks the service worker to look for a newer version, then reloads.
   It never starts inside an open card, a text box being typed in, the bottom bar or the floating buttons, never when the
   page is scrolled down, and a sideways swipe (next/previous section) is left to shell.js. */
(function () {
  "use strict";
  if (window.__phPull) return;
  window.__phPull = true;

  var LINE = 70;      // pixels of (damped) pull needed to refresh
  var MAX = 110;      // the pill stops following the finger here

  var css = document.createElement("style");
  css.textContent =
    "html,body{overscroll-behavior-y:contain}" +
    ".ph-pull{position:fixed;left:50%;top:0;z-index:60;display:flex;align-items:center;gap:.5rem;" +
    "transform:translate(-50%,-3.5rem);padding:.5rem .9rem;border-radius:999rem;background:var(--panel,#fff);" +
    "color:var(--ink,#1f1a14);border:1px solid var(--line,#d9cebd);box-shadow:0 4px 14px rgba(0,0,0,.14);" +
    "font:600 .875rem/1.2 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;pointer-events:none;" +
    "opacity:0;margin-top:env(safe-area-inset-top)}" +
    ".ph-pull.go{transition:transform .2s ease,opacity .2s ease}" +
    ".ph-pull svg{width:1.1rem;height:1.1rem;flex:0 0 auto;transition:transform .15s ease}" +
    ".ph-pull.ready svg{transform:rotate(180deg)}" +
    ".ph-pull.busy svg{animation:ph-spin .8s linear infinite}" +
    "@keyframes ph-spin{to{transform:rotate(360deg)}}" +
    "@media (prefers-reduced-motion:reduce){.ph-pull.busy svg{animation:none}}";
  document.head.appendChild(css);

  var pill = document.createElement("div");
  pill.className = "ph-pull";
  pill.setAttribute("role", "status");
  pill.setAttribute("aria-live", "polite");
  var ARROW = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 5v14M6 13l6 6 6-6"/></svg>';
  var SPIN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M21 12a9 9 0 1 1-6.2-8.56"/></svg>';
  function paint(html, text) { pill.innerHTML = html + "<span></span>"; pill.lastChild.textContent = text; }
  paint(ARROW, "Pull to refresh");
  document.body.appendChild(pill);

  function atTop() {
    return (window.scrollY || document.documentElement.scrollTop || 0) <= 0;
  }
  // True if the finger is on something that scrolls up and down by itself and is not at its own top.
  function innerScrolled(node) {
    for (; node && node !== document.body && node.nodeType === 1; node = node.parentElement) {
      var oy = getComputedStyle(node).overflowY;
      if ((oy === "auto" || oy === "scroll") && node.scrollHeight > node.clientHeight + 2 && node.scrollTop > 0) return true;
    }
    return false;
  }

  var y0 = 0, x0 = 0, pull = 0, state = "idle";   // idle | maybe | pulling | busy

  function show(dist) {
    pill.classList.remove("go");
    var y = Math.min(dist, MAX) - 56;
    pill.style.transform = "translate(-50%," + y + "px)";
    pill.style.opacity = String(Math.min(1, dist / 40));
    var ready = dist >= LINE;
    if (ready !== pill.classList.contains("ready")) {
      pill.classList.toggle("ready", ready);
      paint(ARROW, ready ? "Release to refresh" : "Pull to refresh");
    }
  }
  function hide() {
    pill.classList.add("go");
    pill.classList.remove("ready");
    pill.style.transform = "translate(-50%,-3.5rem)";
    pill.style.opacity = "0";
    setTimeout(function () { if (state === "idle") paint(ARROW, "Pull to refresh"); }, 220);
  }

  function refresh() {
    state = "busy";
    pill.classList.add("go", "busy");
    pill.classList.remove("ready");
    pill.style.transform = "translate(-50%,12px)";
    pill.style.opacity = "1";
    paint(SPIN, "Refreshing…");
    var done = false;
    function reload() { if (done) return; done = true; location.reload(); }
    // Ask for a newer service worker first, so the parts kept offline are replaced too, not only the page.
    // Never wait more than 1.5 seconds for it: with no signal the reload still shows the saved copy.
    setTimeout(reload, 1500);
    try {
      if ("serviceWorker" in navigator) {
        navigator.serviceWorker.getRegistration().then(function (reg) {
          if (!reg) return reload();
          return reg.update().then(function () {
            if (reg.installing || reg.waiting) setTimeout(reload, 600); else reload();
          });
        }).catch(reload);
      } else reload();
    } catch (e) { reload(); }
  }

  document.addEventListener("touchstart", function (e) {
    if (state === "busy") return;
    state = "idle";
    if (e.touches.length !== 1 || !atTop()) return;
    // Zoomed in with two fingers: a drag down is panning the zoomed page, not a pull.
    if (window.visualViewport && window.visualViewport.scale > 1.01) return;
    var tg = e.target;
    if (document.querySelector("dialog[open]")) return;
    // A text box only counts while it is being typed in: dragging down from the search box at the top is a pull.
    if (tg === document.activeElement && tg.matches && tg.matches("input,textarea,select,[contenteditable]")) return;
    if (tg.closest && tg.closest("[contenteditable],nav.ph-bar,.ts-fab,.fb-fab,.sa-fab,.ts-panel,.fb-panel,.sa-panel")) return;
    if (innerScrolled(tg)) return;
    y0 = e.touches[0].clientY; x0 = e.touches[0].clientX; pull = 0; state = "maybe";
  }, { passive: true });

  // Not passive: once it is clearly a downward pull at the top, the page's own rubber-band bounce is held
  // still so the pill, not the whole page, moves with the finger.
  document.addEventListener("touchmove", function (e) {
    if (state !== "maybe" && state !== "pulling") return;
    if (e.touches.length !== 1) { state = "idle"; hide(); return; }
    var dy = e.touches[0].clientY - y0, dx = e.touches[0].clientX - x0;
    if (state === "maybe") {
      if (Math.abs(dy) < 8 && Math.abs(dx) < 8) return;
      // Upward, or more sideways than down: not a pull. Leave it to scrolling and to the section swipe.
      if (dy <= 0 || Math.abs(dx) > dy || !atTop()) { state = "idle"; return; }
      state = "pulling";
    }
    if (e.cancelable) e.preventDefault();
    pull = Math.max(0, dy) * 0.55;
    show(pull);
  }, { passive: false });

  function end() {
    if (state === "pulling" && pull >= LINE) { refresh(); return; }
    if (state !== "busy") { if (state === "pulling") hide(); state = "idle"; }
  }
  document.addEventListener("touchend", end, { passive: true });
  document.addEventListener("touchcancel", function () {
    if (state !== "busy") { if (state === "pulling") hide(); state = "idle"; }
  }, { passive: true });
})();
