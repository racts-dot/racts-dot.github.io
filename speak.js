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
    ".sa-fab:focus-visible,.sa-panel button:focus-visible,.sa-panel select:focus-visible{outline:2px solid #6c8cff;outline-offset:2px}" +
    ".sa-panel{position:fixed;left:12px;right:12px;bottom:calc(84px + env(safe-area-inset-bottom));z-index:2147483645;max-width:420px;" +
    "background:#fff;color:#1c1c1e;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.3);padding:14px;" +
    "font:14px/1.4 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;display:grid;gap:10px}" +
    ".sa-panel[hidden]{display:none}" +
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
      var tag = GOOD.test(v.name) ? " ★" : "";
      return '<option value="' + v.voiceURI.replace(/"/g, "&quot;") + '"' + (cur && v.voiceURI === cur.voiceURI ? " selected" : "") + ">" +
        v.name.replace(/</g, "") + " (" + v.lang + ")" + tag + "</option>";
    }).join("") || "<option>Default voice</option>";
  }

  /* ---------- what to read ---------- */
  var BLOCKS = "h1,h2,h3,h4,h5,h6,p,li,blockquote,figcaption,dt,dd,th,td,summary,caption,legend";
  function visible(el) {
    if (!el.getClientRects().length) return false;
    var st = getComputedStyle(el);
    return st.visibility !== "hidden" && st.display !== "none" && Number(st.opacity) !== 0;
  }
  function skip(el) {
    return !!el.closest("script,style,template,noscript,nav,button,select,option,input,textarea,svg,[aria-hidden='true'],[hidden],.sa-panel,.sa-fab,[data-speak-skip]");
  }
  function clean(t) {
    return String(t || "").replace(/[←-⇿⌀-➿⬀-⯿️\u{1F000}-\u{1FAFF}]/gu, " ")
      .replace(/\s*[|·•]\s*/g, ", ").replace(/\s+/g, " ").trim();
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
      var bits = t.match(/[^.!?。！？\n]+[.!?。！？]*\s*/g) || [t], buf = "";
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
    mainBtn.textContent = !playing ? "▶ Read this page" : paused ? "▶ Resume" : "⏸ Pause";
    stopBtn.hidden = !playing;
    fab.textContent = playing && !paused ? "⏸ Reading…" : "🔊 Read aloud";
    barEl.style.width = parts.length ? Math.round(idx / parts.length * 100) + "%" : "0";
  }
  function step() {
    if (!playing || paused) return;
    if (idx >= parts.length) { finish("Finished."); return; }
    var p = parts[idx], u = new SpeechSynthesisUtterance(p.text);
    var v = /[가-힣]/.test(p.text) ? (koreanVoice() || chosenVoice()) : chosenVoice();
    if (v) { u.voice = v; u.lang = v.lang; }
    u.rate = parseFloat(store.get(K_RATE) || "1") || 1;
    u.onend = function () { if (playing && !paused) { idx++; step(); } };
    u.onerror = function (e) { if (playing && !paused && e.error !== "interrupted" && e.error !== "canceled") { idx++; step(); } };
    mark(p.el);
    nowEl.textContent = p.text.length > 90 ? p.text.slice(0, 88) + "…" : p.text;
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

  /* ---------- the button and panel ---------- */
  function build() {
    document.head.appendChild(css);
    fab = document.createElement("button");
    fab.type = "button"; fab.className = "sa-fab"; fab.setAttribute("aria-haspopup", "dialog");
    fab.textContent = "🔊 Read aloud";
    panel = document.createElement("div");
    panel.className = "sa-panel"; panel.hidden = true; panel.setAttribute("role", "dialog"); panel.setAttribute("aria-label", "Read aloud");
    panel.innerHTML =
      '<div class="sa-row"><button type="button" class="sa-main">▶ Read this page</button>' +
      '<button type="button" class="sa-stop" hidden>■ Stop</button><button type="button" class="sa-close" aria-label="Close">✕</button></div>' +
      '<div class="sa-bar"><i></i></div><div class="sa-now" aria-live="polite"></div>' +
      '<div class="sa-row"><label>Speed <select class="sa-rate"><option value="0.85">Slow</option><option value="1">Normal</option>' +
      '<option value="1.15">Brisk</option><option value="1.3">Fast</option></select></label></div>' +
      '<div class="sa-row"><label style="flex:1">Voice <select class="sa-voice" style="width:100%"></select></label></div>' +
      '<div class="sa-now">★ = a higher-quality voice. On iPhone, more voices: Settings → Accessibility → Spoken Content → Voices → English.</div>';
    document.body.appendChild(fab); document.body.appendChild(panel);
    mainBtn = panel.querySelector(".sa-main"); stopBtn = panel.querySelector(".sa-stop");
    rateSel = panel.querySelector(".sa-rate"); voiceSel = panel.querySelector(".sa-voice");
    nowEl = panel.querySelector(".sa-now"); barEl = panel.querySelector(".sa-bar i");
    rateSel.value = store.get(K_RATE) || "1";
    fillVoices();
    fab.addEventListener("click", function () { panel.hidden = !panel.hidden; if (!panel.hidden) fillVoices(); });
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

  window.SpeakAloud = { start: function () { start(); }, stop: function () { finish(""); } };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build); else build();
})();
