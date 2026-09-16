/* speak.js - a "Read aloud" button for every app on this site that has none.
 *
 * Her words, 15 Sep 2026: "everything that doesn't have the read aloud button, it has to be there"
 * and "Make sure they're good quality."
 *
 * Quality, concretely:
 *  - picks the best voice on the device (Siri / Enhanced / Premium / Natural first), Australian
 *    English first, then British, then American; Korean text is read with a Korean voice;
 *  - reads in sentence-sized pieces, so phones never cut a long paragraph off half way;
 *  - highlights what it is reading and keeps it on screen;
 *  - reads only what is visible on the page you are looking at - no menus, buttons or hidden screens;
 *  - you can pick the voice and speed once; both are remembered on this device;
 *  - it is not stopped when you leave the app (her 15 Sep: "I can have it play in the background");
 *    the phone itself may pause the robot voice in the background - only a recorded voice gets round that.
 * Free: it is the phone's own voice. Nothing is recorded or sent anywhere.
 */
(function () {
  "use strict";
  if (window.SpeakAloud || !("speechSynthesis" in window)) return;
  var SS = window.speechSynthesis;
  /* her 16 Sep ask: on the recipe apps the bubble is the speaker icon only (script tag has data-icon-only) */
  // 16 Sep 2026, her second ask ("still have text for read aloud"): the icon only, on every app. data-with-label brings the words back.
  var ICON_ONLY = !(document.currentScript && document.currentScript.hasAttribute("data-with-label"));
  var K_VOICE = "speak.voice", K_RATE = "speak.rate";
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); } catch (e) {} }
  };

  var css = document.createElement("style");
  css.textContent =
    ".sa-fab{position:fixed;left:12px;bottom:calc(84px + env(safe-area-inset-bottom));z-index:2147483644;" +
    "display:flex;align-items:center;gap:6px;font:600 13px/1 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;" +
    "padding:10px 14px;border-radius:999px;border:0;background:#1c1c1e;color:#fff;box-shadow:0 4px 16px rgba(0,0,0,.25);cursor:pointer}" +
    /* 17 Sep 2026, her words: the mic "should look like exactly what it is for the speaker, as well as AA floating" -
       so the icon-only bubble is the same 44 px circle as the Aa (textsize.js) and 🎙 (feedback.js) bubbles */
    ".sa-fab.sa-icon{width:44px;height:44px;box-sizing:border-box;padding:0;justify-content:center;font-size:18px}" +
    ".sa-fab:focus-visible,.sa-panel button:focus-visible,.sa-panel select:focus-visible{outline:2px solid #6c8cff;outline-offset:2px}" +
    ".sa-panel{position:fixed;left:12px;right:12px;bottom:calc(84px + env(safe-area-inset-bottom));z-index:2147483645;max-width:420px;" +
    "background:#fff;color:#1c1c1e;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.3);padding:14px;" +
    "font:14px/1.4 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;display:grid;gap:10px}" +
    ".sa-panel[hidden]{display:none}" +
    ".sa-grip{cursor:grab;user-select:none;-webkit-user-select:none;font:600 12px/1 inherit;opacity:.6;padding:0 0 8px;touch-action:none}" +
    ".sa-rsz{position:absolute;right:0;bottom:0;width:28px;height:28px;cursor:nwse-resize;touch-action:none;border-radius:0 0 14px 0;" +
    "background:linear-gradient(135deg,transparent 55%,rgba(128,128,128,.7) 55%,rgba(128,128,128,.7) 63%,transparent 63%,transparent 72%,rgba(128,128,128,.7) 72%,rgba(128,128,128,.7) 80%,transparent 80%)}" +
    ".sa-row{display:flex;gap:8px;align-items:center;flex-wrap:wrap}" +
    ".sa-panel button{font:600 14px/1 inherit;border:0;border-radius:10px;padding:11px 14px;background:#f2f2f7;color:#1c1c1e;cursor:pointer}" +
    ".sa-panel button.sa-main{background:#1c1c1e;color:#fff;flex:1}" +
    ".sa-panel select{font:14px inherit;padding:8px;border-radius:10px;border:1px solid #d1d1d6;background:#fff;color:#1c1c1e;max-width:100%}" +
    ".sa-bar{height:4px;background:#e5e5ea;border-radius:4px;overflow:hidden}.sa-bar i{display:block;height:100%;width:0;background:#1c1c1e}" +
    ".sa-now{font-size:12.5px;color:#636366;min-height:1.2em}" +
    ".sa-reading{outline:3px solid #6c8cff !important;outline-offset:3px;border-radius:6px;background-color:rgba(108,140,255,.10) !important}" +
    "@media (prefers-color-scheme: dark){.sa-panel{background:#1c1c1e;color:#f2f2f7}.sa-panel button{background:#2c2c2e;color:#f2f2f7}" +
    ".sa-panel button.sa-main{background:#f2f2f7;color:#1c1c1e}.sa-panel select{background:#2c2c2e;color:#f2f2f7;border-color:#3a3a3c}" +
    ".sa-bar{background:#3a3a3c}.sa-bar i{background:#f2f2f7}.sa-now{color:#aeaeb2}}";

  var fab, panel, mainBtn, stopBtn, rateSel, voiceSel, nowEl, barEl;
  var parts = [], idx = 0, playing = false, paused = false, voices = [];

  /* ---------- voices ---------- */
  var GOOD = /(Siri|Enhanced|Premium|Natural|Neural|Wavenet|Google)/i;
  function score(v) {
    var s = 0, lang = (v.lang || "").replace("_", "-");
    if (/^en-AU/i.test(lang)) s += 40; else if (/^en-GB/i.test(lang)) s += 30; else if (/^en-US/i.test(lang)) s += 20; else if (/^en/i.test(lang)) s += 10;
    if (GOOD.test(v.name)) s += 25;
    if (v.localService) s += 3;
    if (/(Compact|eSpeak|Zarvox|Bells|Bad News|Bubbles|Cellos|Organ|Trinoids|Whisper|Jester|Superstar|Boing|Wobble)/i.test(v.name)) s -= 60;
    return s;
  }
  function englishVoices() {
    return SS.getVoices().filter(function (v) { return /^en/i.test(v.lang || ""); }).sort(function (a, b) { return score(b) - score(a); });
  }
  function koreanVoice() {
    var k = SS.getVoices().filter(function (v) { return /^ko/i.test(v.lang || ""); });
    return k.sort(function (a, b) { return (GOOD.test(b.name) ? 1 : 0) - (GOOD.test(a.name) ? 1 : 0); })[0] || null;
  }
  function chosenVoice() {
    var want = store.get(K_VOICE), list = englishVoices();
    return list.filter(function (v) { return v.voiceURI === want; })[0] || list[0] || null;
  }
  function fillVoices() {
    if (!voiceSel) return;
    voices = englishVoices();
    var cur = chosenVoice();
    voiceSel.innerHTML = voices.slice(0, 25).map(function (v) {
      var tag = GOOD.test(v.name) ? " \u2605" : "";
      return '<option value="' + v.voiceURI.replace(/"/g, "&quot;") + '"' + (cur && v.voiceURI === cur.voiceURI ? " selected" : "") + ">" +
        v.name.replace(/</g, "") + " (" + v.lang + ")" + tag + "</option>";
    }).join("") || "<option>Default voice</option>";
  }

  /* ---------- what to read ---------- */
  var BLOCKS = "h1,h2,h3,h4,h5,h6,p,li,blockquote,figcaption,dt,dd,th,td,summary,caption,legend";
  function visible(el) {
    if (!el.getClientRects().length) return false;
    var r = el.getBoundingClientRect();   // swiped aside: a card moved off the side of the screen is not read
    if (r.right <= 0 || r.left >= innerWidth) return false;
    var st = getComputedStyle(el);
    return st.visibility !== "hidden" && st.display !== "none" && Number(st.opacity) !== 0;
  }
  function skip(el) {
    return !!el.closest("script,style,template,noscript,nav,button,select,option,input,textarea,svg,[aria-hidden='true'],[hidden],.sa-panel,.sa-fab,[data-speak-skip]");
  }
  function clean(t) {
    return String(t || "").replace(/[\u{2190}-\u{21FF}\u{2300}-\u{27BF}\u{2B00}-\u{2BFF}\u{FE0F}\u{1F000}-\u{1FAFF}]/gu, " ")
      .replace(/\s*[|\u00B7\u2022]\s*/g, ", ").replace(/\s+/g, " ").trim();
  }
  function collect() {
    var roots = Array.prototype.filter.call(document.querySelectorAll("[data-speak-root]"), visible);
    var root = roots[0] || document.querySelector("main") || document.body;   // the open reader wins when one is showing
    var picked = [];
    root.querySelectorAll(BLOCKS).forEach(function (el) {
      if (skip(el) || !visible(el)) return;
      if (el.querySelector(BLOCKS)) return;                       // keep the innermost block only
      picked.push(el);
    });
    // text sitting in plain divs/spans that no block above covers (cards, tiles, list rows)
    root.querySelectorAll("div,span,a,strong,b,em,small,time,label").forEach(function (el) {
      if (skip(el) || el.closest(BLOCKS)) return;
      if (el.querySelector("div,p,li,ul,ol,table," + BLOCKS)) return;
      var own = Array.prototype.some.call(el.childNodes, function (n) { return n.nodeType === 3 && n.textContent.trim(); });
      if (!own || !visible(el)) return;
      if (el.parentElement && picked.indexOf(el.parentElement) !== -1) return;
      picked.push(el);
    });
    // form fields she has filled in are part of the page too
    root.querySelectorAll("textarea,input[type=text],input:not([type])").forEach(function (el) {
      if (el.closest(".sa-panel,[data-speak-skip]") || !visible(el) || !String(el.value || "").trim()) return;
      picked.push(el);
    });
    picked.sort(function (a, b) { return a.compareDocumentPosition(b) & Node.DOCUMENT_POSITION_FOLLOWING ? -1 : 1; });
    var out = [], seen = "";
    picked.forEach(function (el) {
      var t = el.matches("textarea,input") ? clean(el.value) : clean(el.innerText);
      if (t.length < 2 || t === seen) return;
      seen = t;
      var bits = t.match(/[^.!?\u3002\uFF01\uFF1F\n]+[.!?\u3002\uFF01\uFF1F]*\s*/g) || [t], buf = "";
      bits.forEach(function (s) {
        if ((buf + s).length > 200 && buf) { out.push({ el: el, text: buf.trim() }); buf = ""; }
        buf += s;
      });
      if (buf.trim()) out.push({ el: el, text: buf.trim() });
    });
    return out;
  }

  /* ---------- playing ---------- */
  function mark(el) {
    document.querySelectorAll(".sa-reading").forEach(function (x) { x.classList.remove("sa-reading"); });
    if (!el) return;
    el.classList.add("sa-reading");
    var r = el.getBoundingClientRect();
    if (r.top < 60 || r.bottom > innerHeight - 160) el.scrollIntoView({ behavior: "smooth", block: "center" });
  }
  function paint() {
    if (!mainBtn) return;
    mainBtn.textContent = !playing ? "\u25B6 Read this page" : paused ? "\u25B6 Resume" : "\u23F8 Pause";
    stopBtn.hidden = !playing;
    fab.textContent = playing && !paused ? (ICON_ONLY ? "\u23F8" : "\u23F8 Reading\u2026") : (ICON_ONLY ? "\uD83D\uDD0A" : "\uD83D\uDD0A Read aloud");
    barEl.style.width = parts.length ? Math.round(idx / parts.length * 100) + "%" : "0";
  }
  function step() {
    if (!playing || paused) return;
    if (idx >= parts.length) { finish("Finished."); return; }
    var p = parts[idx], u = new SpeechSynthesisUtterance(p.text);
    var v = /[\uAC00-\uD7A3]/.test(p.text) ? (koreanVoice() || chosenVoice()) : chosenVoice();
    if (v) { u.voice = v; u.lang = v.lang; }
    u.rate = parseFloat(store.get(K_RATE) || "1") || 1;
    u.onend = function () { if (playing && !paused) { idx++; step(); } };
    u.onerror = function (e) { if (playing && !paused && e.error !== "interrupted" && e.error !== "canceled") { idx++; step(); } };
    mark(p.el);
    nowEl.textContent = p.text.length > 90 ? p.text.slice(0, 88) + "\u2026" : p.text;
    paint();
    SS.speak(u);
  }
  function start() {
    SS.cancel();
    parts = collect(); idx = 0; paused = false;
    if (!parts.length) { nowEl.textContent = "Nothing to read on this screen."; return; }
    playing = true; step();
  }
  function finish(msg) {
    playing = false; paused = false; SS.cancel(); mark(null);
    if (nowEl) nowEl.textContent = msg || "";
    idx = 0; paint();
  }

  /* ---------- drag the bubble anywhere (her 16 Sep ask), position kept per device ---------- */
  function makeDraggable(el, key, handle) {
    handle = handle || el;
    var sx = 0, sy = 0, ox = 0, oy = 0, moved = false, down = false, pid = null;
    function place(x, y) {
      var w = el.offsetWidth, h = el.offsetHeight;
      x = Math.max(4, Math.min(window.innerWidth - w - 4, x));
      y = Math.max(4, Math.min(window.innerHeight - h - 4, y));
      el.style.setProperty("left", x + "px", "important"); el.style.setProperty("top", y + "px", "important");
      el.style.setProperty("right", "auto", "important"); el.style.setProperty("bottom", "auto", "important");
    }
    function restore() {
      var v = store.get(key); if (!v) return;
      try { var p = JSON.parse(v); place(p[0] * window.innerWidth, p[1] * window.innerHeight); } catch (e) {}
    }
    handle.style.touchAction = "none";
    handle.addEventListener("pointerdown", function (e) {
      if (e.button > 0 || (handle !== el && e.target.closest("button,select,.sa-rsz"))) return;
      down = true; moved = false; pid = e.pointerId;
      var r = el.getBoundingClientRect(); sx = e.clientX; sy = e.clientY; ox = r.left; oy = r.top;
    });
    handle.addEventListener("pointermove", function (e) {
      if (!down || e.pointerId !== pid) return;
      var dx = e.clientX - sx, dy = e.clientY - sy;
      if (!moved && Math.abs(dx) + Math.abs(dy) < 8) return;
      if (!moved) { moved = true; try { handle.setPointerCapture(pid); } catch (x) {} }
      place(ox + dx, oy + dy); e.preventDefault();
    });
    function up() {
      if (!down) return; down = false;
      if (moved) { var r = el.getBoundingClientRect(); store.set(key, JSON.stringify([r.left / window.innerWidth, r.top / window.innerHeight])); }
    }
    handle.addEventListener("pointerup", up); handle.addEventListener("pointercancel", up);
    el.restorePos = restore;
    handle.addEventListener("click", function (e) { if (moved) { e.stopImmediatePropagation(); e.preventDefault(); moved = false; } }, true);
    window.addEventListener("resize", restore);
    restore(); setTimeout(restore, 300);   /* not requestAnimationFrame: it never fires in a hidden tab */
  }

  /* ---------- the button and panel ---------- */
  function build() {
    document.head.appendChild(css);
    fab = document.createElement("button");
    fab.type = "button"; fab.className = ICON_ONLY ? "sa-fab sa-icon" : "sa-fab"; fab.setAttribute("aria-haspopup", "dialog");
    fab.textContent = ICON_ONLY ? "\uD83D\uDD0A" : "\uD83D\uDD0A Read aloud";
    fab.setAttribute("aria-label", "Read aloud"); fab.title = "Read aloud";
    panel = document.createElement("div");
    panel.className = "sa-panel"; panel.hidden = true; panel.setAttribute("role", "dialog"); panel.setAttribute("aria-label", "Read aloud");
    panel.innerHTML =
      '<div class="sa-grip" title="Drag to move">\u283F Read aloud</div><div class="sa-rsz" title="Drag to resize" aria-label="Resize"></div>' +
      '<div class="sa-row"><button type="button" class="sa-main">\u25B6 Read this page</button>' +
      '<button type="button" class="sa-stop" hidden>\u25A0 Stop</button><button type="button" class="sa-close" aria-label="Close">\u2715</button></div>' +
      '<div class="sa-bar"><i></i></div><div class="sa-now" aria-live="polite"></div>' +
      '<div class="sa-row"><label>Speed <select class="sa-rate"><option value="0.85">Slow</option><option value="1">Normal</option>' +
      '<option value="1.15">Brisk</option><option value="1.3">Fast</option></select></label></div>' +
      '<div class="sa-row"><label style="flex:1">Voice <select class="sa-voice" style="width:100%"></select></label></div>' +
      '<div class="sa-now">\u2605 = a higher-quality voice. On iPhone, more voices: Settings \u2192 Accessibility \u2192 Spoken Content \u2192 Voices \u2192 English.</div>';
    document.body.appendChild(fab); document.body.appendChild(panel);
    makeDraggable(fab, "speak.pos");
    makeDraggable(panel, "speak.panel.pos", panel.querySelector(".sa-grip"));
    (function (grip) {   /* 17 Sep: "everything is resizable the boxes and movable" - drag the corner */
      var on = false, sx = 0, w0 = 0;
      function setW(w) { panel.style.setProperty("max-width", "none", "important");
        panel.style.setProperty("width", Math.max(260, Math.min(w, window.innerWidth - 8)) + "px", "important");
        panel.style.setProperty("right", "auto", "important"); }
      panel.restoreSize = function () { var f = +store.get("speak.panel.w"); if (f) setW(f * window.innerWidth); };
      grip.addEventListener("pointerdown", function (e) { on = true; sx = e.clientX; var r = panel.getBoundingClientRect(); w0 = r.width;
        panel.style.setProperty("left", r.left + "px", "important"); try { grip.setPointerCapture(e.pointerId); } catch (x) {} e.preventDefault(); e.stopPropagation(); });
      grip.addEventListener("pointermove", function (e) { if (on) { setW(w0 + e.clientX - sx); e.preventDefault(); } });
      function end() { if (!on) return; on = false; store.set("speak.panel.w", String(panel.getBoundingClientRect().width / window.innerWidth)); }
      grip.addEventListener("pointerup", end); grip.addEventListener("pointercancel", end);
    })(panel.querySelector(".sa-rsz"));
    mainBtn = panel.querySelector(".sa-main"); stopBtn = panel.querySelector(".sa-stop");
    rateSel = panel.querySelector(".sa-rate"); voiceSel = panel.querySelector(".sa-voice");
    nowEl = panel.querySelector(".sa-now"); barEl = panel.querySelector(".sa-bar i");
    rateSel.value = store.get(K_RATE) || "1";
    fillVoices();
    fab.addEventListener("click", function () { panel.hidden = !panel.hidden; if (!panel.hidden) { fillVoices(); panel.restoreSize(); panel.restorePos(); } });
    panel.querySelector(".sa-close").addEventListener("click", function () { panel.hidden = true; });
    mainBtn.addEventListener("click", function () {
      if (!playing) { start(); return; }
      if (!paused) { paused = true; SS.cancel(); paint(); return; }
      paused = false; step();
    });
    stopBtn.addEventListener("click", function () { finish(""); });
    rateSel.addEventListener("change", function () { store.set(K_RATE, rateSel.value); if (playing && !paused) { SS.cancel(); step(); } });
    voiceSel.addEventListener("change", function () { store.set(K_VOICE, voiceSel.value); if (playing && !paused) { SS.cancel(); step(); } });
    if ("onvoiceschanged" in SS) SS.addEventListener("voiceschanged", fillVoices);
    paint();
  }

  window.SpeakAloud = { start: function () { start(); }, stop: function () { finish(""); }, draggable: makeDraggable };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build); else build();
})();
