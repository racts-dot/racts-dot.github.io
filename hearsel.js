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

   ⭐ 21 Sep 2026: IT READS IN THE NATURAL VOICE NOW. Her rule "READ ALOUD USES A NATURAL VOICE", and
   her 21 Sep ask "make sure all the voice over is done there on the apps". Until today this file used
   the phone's own voice (speechSynthesis) on all 22 apps that load it, while the page's own Read
   aloud button (speak.js) already used the natural one - two voices on one page. It now uses the
   same route, keys and voice as speak.js: her relay's /tts, the apps password saved on this device
   (notionSync.pass), the voice picked in the read-aloud panel (speak.nvoice, default aoede) and the
   speed (speak.rate). Same as speak.js and the daily reads since 19 Sep ("get rid of karen"): if the
   natural voice cannot be reached it SAYS why - it never drops back to the phone voice.
   A page whose speak.js tag carries data-no-natural keeps its words on the phone: nothing is sent.
   It stops the page's Read aloud first, so two voices cannot talk over each other. */
(function () {
  "use strict";
  if (window.__hearSel) return;
  window.__hearSel = true;

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

  /* 23 Sep 2026: a page with NONE of those containers used to get no Hear button anywhere - the file
     loaded, the word check scored it present, and selecting did nothing. Measured on recipes, todo and
     tripshare (app_kit_behave's new Hear piece). Such a page is read as one whole: listen on its body.
     A page that does mark a reading area keeps its boundary exactly as before. */
  function inReading(node) {
    var whole = !document.querySelector(ROOTS);
    for (; node && node !== document; node = node.parentNode || node.host) {
      if (node.nodeType !== 1) continue;
      if (node.matches("input,textarea,select,button,[contenteditable]")) return false;
      if (node.matches(ROOTS) || (whole && node === document.body)) return true;
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

  var RELAY = "https://apps-notion-relay.apps-notion-relay.workers.dev";
  var audio = null;
  function get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }
  function pass() {                              // notion-sync.js stores it JSON-encoded
    var raw = get("notionSync.pass");
    if (!raw) return null;
    try { var p = JSON.parse(raw); if (typeof p === "string" && p) return p; } catch (e) {}
    return raw.charAt(0) !== "{" && raw.charAt(0) !== "[" ? raw : null;
  }
  function noNatural() { return !!document.querySelector('script[src*="speak.js"][data-no-natural]'); }
  function note(msg) {                           // a short line under the button, gone in 4 s
    var n = document.getElementById("hearsel-note");
    if (!n) {
      n = document.createElement("div"); n.id = "hearsel-note"; n.setAttribute("role", "status");
      n.style.cssText = "position:fixed;left:50%;bottom:calc(90px + env(safe-area-inset-bottom,0px));" +
        "transform:translateX(-50%);z-index:71;max-width:90vw;padding:.55rem .9rem;border-radius:.8rem;" +
        "background:#1f1a14;color:#fff;font:500 .875rem/1.35 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif";
      document.body.appendChild(n);
    }
    n.textContent = msg; n.style.display = "block";
    clearTimeout(note.t); note.t = setTimeout(function () { n.style.display = "none"; }, 4000);
  }
  async function connect() {                     // the daily reads' way: ask once, check, keep
    var pw = null;
    try { pw = window.prompt("Enter your apps password once to turn on the natural voice on this device:"); } catch (e) { return null; }
    pw = (pw || "").trim(); if (!pw) return null;
    try {
      var r = await fetch(RELAY + "/ping", { headers: { "X-Pass": pw } });
      if (!r.ok) { note(r.status === 401 ? "That password was not right" : "Could not check the password just now"); return null; }
    } catch (e) { note("No internet, so the password cannot be checked"); return null; }
    try { localStorage.setItem("notionSync.pass", JSON.stringify(pw)); } catch (e) { return null; }
    return pw;
  }
  async function say(text) {
    if (noNatural()) { note("This app keeps its words on your phone, so it has no natural voice."); return; }
    if (get("speak.natural") === "0") { note("The natural voice is switched off here — turn it back on in Read aloud."); return; }
    var pw = pass() || await connect();
    if (!pw) return;
    try { if (window.SpeakAloud) window.SpeakAloud.stop(); } catch (e) {}
    try { window.speechSynthesis && window.speechSynthesis.cancel(); } catch (e) {}
    if (audio) { try { audio.pause(); } catch (e) {} }
    try {
      var r = await fetch(RELAY + "/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Pass": pw },
        body: JSON.stringify({ text: text.slice(0, 1500), voice: ((text.match(/[\uAC00-\uD7A3]/g) || []).length > (text.match(/[A-Za-z]/g) || []).length) ? "korean" : (get("speak.nvoice") || "aoede") })   // 23 Sep: Korean selections to the Korean voice
      });
      if (!r.ok) { note(r.status === 401 ? "The saved apps password is out of date — enter it again in Read aloud." : "The natural voice could not be reached just now. Try again in a moment."); return; }
      var blob = await r.blob();
      audio = new Audio(URL.createObjectURL(blob));
      audio.setAttribute("playsinline", "");
      var rate = parseFloat(get("speak.rate") || "1");
      audio.playbackRate = rate >= 0.5 && rate <= 2 ? rate : 1;
      await audio.play();
      if (text.length > 1500) note("Reading the first 1,500 letters of what you picked.");
    } catch (e) { note("The natural voice could not be reached just now. Try again in a moment."); }
  }

  b.addEventListener("click", function (ev) {
    ev.preventDefault();
    var text = String(window.getSelection() || "").trim();
    hide();
    if (text) say(text);
  });
})();
