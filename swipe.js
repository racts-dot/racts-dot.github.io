/* swipe.js - swipe left or right to move through a page that has no swipe of its own.
 *
 * Her words, 15 Sep 2026: "everything swipe to left and right has it been done?" She then picked all four
 * that had none: the prompt cookbook + video search, the recipes, the AI handoff board, the eBay stock ledger.
 *
 * The script tag says what to move through. Swipe left = next, swipe right = back.
 *   data-sections="section"                   scroll to the next or previous block
 *   data-select="#cat"                        step the menu to its next or previous choice
 *   data-chips="#chips .chip" data-input="#q" step through the quick-search words
 *   data-pages="./ a.html b.html"             open the next or previous page in the list
 * Same guard as the other apps on this site (todo, app): more than 70px sideways, under 50px up or down,
 * under 0.7 s, and never when the finger starts on a field, a menu or anything that scrolls sideways.
 */
(function () {
  "use strict";
  var me = document.currentScript;
  if (!me || window.__swipeJs) return;
  window.__swipeJs = true;
  var cfg = me.dataset;

  var toast, hideT;
  function say(msg) {
    if (!toast) {
      toast = document.createElement("div");
      toast.setAttribute("role", "status");
      toast.style.cssText = "position:fixed;left:50%;bottom:calc(24px + env(safe-area-inset-bottom));transform:translateX(-50%);" +
        "z-index:2147483646;max-width:calc(100% - 32px);padding:9px 16px;border-radius:999px;background:#1c1c1e;" +
        "box-shadow:0 4px 14px rgba(0,0,0,.28);" +   /* solid, to match the hint - 21 Sep */
        "color:#fff;font:600 13px/1.3 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;white-space:nowrap;overflow:hidden;" +
        "text-overflow:ellipsis;pointer-events:none;opacity:0;transition:opacity .2s";
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = "1";
    clearTimeout(hideT);
    hideT = setTimeout(function () { toast.style.opacity = "0"; }, 1400);
  }
  function label(el) { return String(el.textContent || "").replace(/\s+/g, " ").trim(); }
  function reveal(el) {   // bring the control back into view if she has scrolled past it
    var r = el.getBoundingClientRect();
    if (r.top < 0 || r.top > innerHeight) el.scrollIntoView({ block: "start", behavior: "smooth" });
  }

  /* ---------- what one swipe does, per mode ---------- */
  var aimed = null, aimedAt = 0;   // where the last swipe sent her, while the smooth scroll is still moving
  function sections(d) {
    var list = [].slice.call(document.querySelectorAll(cfg.sections));
    if (!list.length) return;
    var cur = -1;
    list.forEach(function (s, i) { if (s.getBoundingClientRect().top <= 90) cur = i; });
    if (innerHeight + scrollY >= document.documentElement.scrollHeight - 4) {   // at the bottom, short last sections never reach the top
      list.forEach(function (s, i) { if (s.getBoundingClientRect().top < innerHeight - 60) cur = i; });
    }
    if (aimed !== null && Date.now() - aimedAt < 1200) cur = aimed;   // two quick swipes move two sections
    var next = cur + d;
    aimedAt = Date.now();
    if (next < 0) {
      aimed = -1;
      if (scrollY > 5) scrollTo({ top: 0, behavior: "smooth" });
      say("Top");
      return;
    }
    if (next >= list.length) { aimed = list.length - 1; say("Last section"); return; }
    aimed = next;
    list[next].scrollIntoView({ block: "start", behavior: "smooth" });
    var h = list[next].querySelector("h1,h2,h3");
    say(h ? label(h) : "Section " + (next + 1) + " of " + list.length);
  }

  function select(d) {
    var sel = document.querySelector(cfg.select);
    if (!sel) return;
    var opts = [].slice.call(sel.options).filter(function (o) { return !o.disabled; });
    var cur = opts.indexOf(sel.options[sel.selectedIndex]);
    var next = cur + d;
    if (next < 0 || next >= opts.length) { say(d > 0 ? "Last one" : "First one"); return; }
    sel.value = opts[next].value;
    sel.dispatchEvent(new Event("input", { bubbles: true }));
    sel.dispatchEvent(new Event("change", { bubbles: true }));
    reveal(sel);
    say(label(opts[next]) + "  ·  " + (next + 1) + " of " + opts.length);
  }

  function chips(d) {
    var list = [].slice.call(document.querySelectorAll(cfg.chips));
    var box = document.querySelector(cfg.input);
    if (!list.length || !box) return;
    var now = String(box.value || "").trim().toLowerCase();
    var cur = list.findIndex(function (c) { return label(c).toLowerCase() === now; });
    var next = cur === -1 ? (d > 0 ? 0 : list.length - 1) : cur + d;
    if (next < 0 || next >= list.length) { say(d > 0 ? "Last word" : "First word"); return; }
    box.value = label(list[next]);   // no focus, so the phone keyboard stays down
    box.dispatchEvent(new Event("input", { bubbles: true }));
    reveal(box);
    say(label(list[next]) + "  ·  " + (next + 1) + " of " + list.length);
  }

  function pages(d) {
    var list = cfg.pages.split(/\s+/).filter(Boolean);
    var here = location.pathname.split("/").pop() || "./";
    if (here === "index.html") here = "./";
    var cur = list.indexOf(here);
    if (cur === -1) return;
    var next = cur + d;
    if (next < 0 || next >= list.length) { say(d > 0 ? "Last page" : "First page"); return; }
    say(d > 0 ? "Next →" : "← Back");
    setTimeout(function () { location.href = list[next]; }, 120);
  }

  /* data-links="#nav a[data-go]" - step through a list of links that swap what the page shows
     WITHOUT leaving it. Added 21 Sep 2026 for the Rule Shelf, which loaded this file with no
     data- attribute at all: with no mode `act` was null, the listeners below were never added,
     and the page had NO swipe while app_kit_check.py scored it "Swipe: yes" (it was finding the
     word touchstart inside pull.js). Measured in two browsers before and after.
     The one that is on is marked class="on" (the Rule Shelf), aria-current="page", or .active. */
  function links(d) {
    var list = [].slice.call(document.querySelectorAll(cfg.links));
    if (list.length < 2) return;
    var cur = -1;
    list.forEach(function (a, i) {
      if (a.classList.contains("on") || a.classList.contains("active") ||
          a.getAttribute("aria-current") === "page" ||
          a.getAttribute("aria-selected") === "true") cur = i;   /* a tablist says it this way - added 21 Sep 2026 for Ledgers */
    });
    /* left at -1 on purpose when nothing is marked current: the first left swipe then opens
       item ONE rather than skipping to item two. 21 Sep 2026, for Study's chapter list. */
    var next = cur + d;
    if (next < 0) { say("First one"); return; }
    if (next >= list.length) { say("Last one"); return; }
    /* the <em> holds a size or a note, not the name, and it runs straight into the title with no
       space ("The shelfstart here") - so take it out rather than trying to split on whitespace */
    var name = String(list[next].textContent || "");
    var em = list[next].querySelector("em");
    if (em) name = name.replace(String(em.textContent || ""), "");
    say(name.replace(/\s+/g, " ").trim().slice(0, 40));
    list[next].click();
    if (scrollY > 5) scrollTo({ top: 0, behavior: "smooth" });
  }

  var act = cfg.sections ? sections : cfg.select ? select : cfg.chips ? chips
          : cfg.pages ? pages : cfg.links ? links : null;
  if (!act) return;

  /* ---------- a hint, once ----------
     Her words, 21 Sep 2026, looking at four apps that had just been given swipe: "Where is the buttons".
     Swipe has nothing on screen, so she could not tell it was there. Now each app says so ONCE per
     device, on a touch screen only, and the hint is gone at the first touch or after 3.5 s.
     ⛔ ITS WORDS COME FROM CSS content:, NOT FROM TEXT IN THE PAGE, AND THAT IS THE WHOLE POINT.
     status/app_kit_behave.py decides a swipe WORKED by whether document.body.innerText changed, and
     generated content is not part of innerText. A hint written as real text would appear by itself,
     change the text, and score "Swipe: yes" on an app whose swipe does nothing - a false pass on every
     app at once, which is the exact fault that check was built to catch. Control-tested 21 Sep 2026:
     a page whose swipe does nothing still reads MISSING with this hint showing. */
  (function () {
    var key = "swipeHint:" + location.pathname;
    try { if (localStorage.getItem(key)) return; } catch (e) { return; }
    if (!(window.matchMedia && matchMedia("(pointer: coarse)").matches)) return;
    var st = document.createElement("style");
    st.textContent =
      ".sw-hint{position:fixed;left:50%;bottom:calc(24px + env(safe-area-inset-bottom));transform:translateX(-50%);" +
      "z-index:2147483645;padding:9px 16px;border-radius:999px;background:#1c1c1e;" +
      "box-shadow:0 4px 14px rgba(0,0,0,.28);" +   /* solid: at .92 the page text showed THROUGH the words (looked at, 21 Sep) */
      "pointer-events:none;opacity:0;transition:opacity .3s}" +
      ".sw-hint::after{content:attr(data-hint);color:#fff;white-space:nowrap;" +
      "font:600 13px/1.3 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}" +
      ".sw-hint.on{opacity:1}";
    var h = document.createElement("div");
    h.className = "sw-hint";
    h.setAttribute("aria-hidden", "true");
    h.setAttribute("data-hint", "Swipe \u2190 \u2192 to move");
    function gone() {
      removeEventListener("touchstart", gone, true);
      h.classList.remove("on");
      setTimeout(function () { h.remove(); st.remove(); }, 400);
    }
    function show() {
      document.head.appendChild(st);
      document.body.appendChild(h);
      requestAnimationFrame(function () { h.classList.add("on"); });
      try { localStorage.setItem(key, "1"); } catch (e) {}
      addEventListener("touchstart", gone, true);
      setTimeout(gone, 3500);
    }
    if (document.body) setTimeout(show, 700);
    else addEventListener("DOMContentLoaded", function () { setTimeout(show, 700); });
  })();

  /* ---------- the gesture ---------- */
  function skip(el) {
    for (; el && el.nodeType === 1; el = el.parentElement) {
      if (el.matches("input,textarea,select,iframe,.sa-fab,.sa-panel,.ts-fab,.ts-panel,.fb-fab,.fb-panel") || el.isContentEditable) return true;
      if (el.scrollWidth > el.clientWidth) {
        var o = getComputedStyle(el).overflowX;
        if (o === "auto" || o === "scroll") return true;
      }
    }
    return false;
  }
  var x0 = null, y0 = 0, t0 = 0;
  document.addEventListener("touchstart", function (e) {
    x0 = null;
    if (e.touches.length !== 1 || skip(e.target)) return;
    x0 = e.touches[0].clientX; y0 = e.touches[0].clientY; t0 = Date.now();
  }, { passive: true });
  document.addEventListener("touchend", function (e) {
    if (x0 === null) return;
    var t = e.changedTouches[0], dx = t.clientX - x0, dy = t.clientY - y0;
    x0 = null;
    if (Math.abs(dx) <= 70 || Math.abs(dy) >= 50 || Date.now() - t0 >= 700) return;
    act(dx < 0 ? 1 : -1);
  }, { passive: true });
  document.addEventListener("touchcancel", function () { x0 = null; }, { passive: true });
})();
