/* Hear the bit you picked - the shared one for every app on this site.
   Her note in the App feedback database, 19 Sep 2026 (Recipes): "Like the daily reads i want the
   select to hear the specitic part."

   The daily reads had this and nothing else did, because it was written inline against that page's
   own #passage element. This is the same behaviour, lifted out and made to attach anywhere, so the
   next app gets it by loading one file instead of by somebody copying seventy lines.

   Select some words -> a small "Hear this" button appears under them -> tap it and only those words
   are read. Deliberately NOT a tap: in several of these apps a tap on a line already means
   something (keep this verse, open this recipe), so the gesture has to be a different one.

   Where it listens: anything marked data-speak-root, else <main>, <article> or #view. Selecting
   inside a text box, a menu or a button does nothing - that is the browser's own selection and she
   is editing, not reading.

   It uses the phone's own voice through speechSynthesis, at the speed and voice the page already
   chose if the page exposes them (window.speakRate / window.speakVoice, both optional). It never
   touches a page's own player, and it cancels any speech already running so two voices cannot talk
   over each other. */
(function () {
  "use strict";
  if (window.__hearSel) return;
  window.__hearSel = true;
  if (!("speechSynthesis" in window)) return;

  var MIN = 3;                                   // shorter than this is a stray tap, not a choice
  var ROOTS = "[data-speak-root],main,article,#view";

  var css = document.createElement("style");
  css.textContent =
    "#hearsel{position:absolute;z-index:70;display:none;padding:.45rem .8rem;border-radius:999rem;" +
    "border:1px solid var(--line,#d9cebd);background:var(--panel,#fff);color:var(--ink,#1f1a14);" +
    "box-shadow:0 4px 14px rgba(0,0,0,.16);cursor:pointer;" +
    "font:600 .875rem/1.2 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}" +
    "@media print{#hearsel{display:none!important}}";
  document.head.appendChild(css);

  var b = document.createElement("button");
  b.type = "button"; b.id = "hearsel"; b.textContent = "🔊 Hear this";
  document.body.appendChild(b);

  function hide() { b.style.display = "none"; }

  function inReading(node) {
    for (; node && node !== document; node = node.parentNode || node.host) {
      if (node.nodeType !== 1) continue;
      if (node.matches("input,textarea,select,button,[contenteditable]")) return false;
      if (node.matches(ROOTS)) return true;
    }
    return false;
  }

  function place() {
    var sel = window.getSelection();
    if (!sel || sel.isCollapsed) return hide();
    var text = sel.toString().trim();
    if (text.length < MIN || !inReading(sel.anchorNode)) return hide();
    var r = sel.getRangeAt(0).getBoundingClientRect();
    if (!r || (!r.width && !r.height)) return hide();
    b.style.display = "block";
    b.style.top = (r.bottom + window.scrollY + 8) + "px";
    // Kept on screen at phone width: the button is about 120px and the page can be narrow.
    b.style.left = Math.max(10, Math.min(r.left + window.scrollX, window.innerWidth - 130)) + "px";
  }

  document.addEventListener("selectionchange", function () { setTimeout(place, 10); });
  document.addEventListener("scroll", hide, { passive: true });

  b.addEventListener("click", function (ev) {
    ev.preventDefault();
    var text = String(window.getSelection() || "").trim();
    if (!text) return hide();
    try {
      window.speechSynthesis.cancel();
      var say = new SpeechSynthesisUtterance(text);
      if (typeof window.speakRate === "number") say.rate = window.speakRate;
      if (window.speakVoice) { say.voice = window.speakVoice; say.lang = window.speakVoice.lang; }
      window.speechSynthesis.speak(say);
    } catch (e) {}
    hide();
  });
})();
