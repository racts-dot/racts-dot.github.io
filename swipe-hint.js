/* swipe-hint.js - "Swipe <- -> to move", once, so she knows a page has swipe.
 *
 * Her words, 21 Sep 2026, looking at apps that had just been given swipe: "Where is the buttons".
 * Swipe has nothing on screen, so she could not tell it was there. Then: "do todo tripshare and
 * notion reader too" - the three whose swipe is their OWN code rather than swipe.js.
 *
 * ONE COPY. swipe.js loads this file from beside itself, and the pages with their own swipe load it
 * directly, so the hint is written once. The Notion Reader keeps a local copy because its security
 * policy admits a single file from this site (feedback.js) - the same reason it copies pull.js.
 *
 * Shown once per app per device, on a touch screen only, gone at the first touch or after 3.5 s.
 *
 * ⛔ ITS WORDS COME FROM CSS content:, NOT FROM TEXT IN THE PAGE, AND THAT IS THE WHOLE POINT.
 * status/app_kit_behave.py decides a swipe WORKED by whether document.body.innerText changed, and
 * generated content is not part of innerText. A hint written as real text would appear by itself,
 * change the text, and score "Swipe: yes" on an app whose swipe does nothing - a false pass on every
 * app at once, which is the exact fault that check was built to catch. Control-tested 21 Sep 2026:
 * a page whose swipe does nothing still reads MISSING with this hint on screen.
 *
 * Solid, not see-through: at .92 opacity the page text showed THROUGH the words (looked at, 21 Sep).
 */
(function () {
  "use strict";
  if (window.__swipeHint) return;          // swipe.js and a direct tag must not show it twice
  window.__swipeHint = true;
  var key = "swipeHint:" + location.pathname;
  try { if (localStorage.getItem(key)) return; } catch (e) { return; }
  if (!(window.matchMedia && matchMedia("(pointer: coarse)").matches)) return;
  var st = document.createElement("style");
  st.textContent =
    ".sw-hint{position:fixed;left:50%;bottom:calc(24px + env(safe-area-inset-bottom));transform:translateX(-50%);" +
    "z-index:2147483645;padding:9px 16px;border-radius:999px;background:#1c1c1e;" +
    "box-shadow:0 4px 14px rgba(0,0,0,.28);pointer-events:none;opacity:0;transition:opacity .3s}" +
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
