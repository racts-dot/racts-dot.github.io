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
 *  - it keeps reading when you switch away or the screen locks (her 15 Sep: "I can have it play
 *    in the background") - real audio, not the phone's robot voice, which iOS suspends;
 *  - it stops when you QUIT the app (her 16 Sep: "the voice gets out of it when I quit").
 *
 * ⛔ WHAT IT SENDS, 19 Sep 2026 - this line used to read "Nothing is recorded or sent anywhere",
 * and that is no longer true. With the natural voice ON, the words on the screen are sent to her
 * own relay and on to Google Text-to-Speech, which returns the audio. The clip is then kept in
 * her own Cloudflare KV so re-reading the same page costs nothing. With it OFF - the tick box in
 * the panel - nothing leaves the device and the phone's own voice reads, as before.
 * Her call on which apps carry it: an app can opt out with data-no-natural on the script tag.
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

  /* ---------- THE NATURAL VOICE. Her ask, 19 Sep 2026 ----------
   * "with every app that I deploy, you will have Natural Voice already there.
   *  So I don't have to download anything."
   *
   * ⛔ THE DEVICE CANNOT DO THIS, AND THAT IS MEASURED, NOT ASSUMED - 19 Sep 2026:
   *   Windows 11: speechSynthesis offers FIVE voices, all legacy SAPI5 (James, Catherine,
   *               David, Mark, Zira). None matches Siri/Enhanced/Premium/Natural/Neural.
   *               No Korean voice AT ALL - so Hangul was being read by an English voice.
   *   macOS     : 184 voices installed, ZERO matching those words, exactly one en_AU
   *               (Karen, the old compact one).
   * On Apple the natural voices ARE the download. So no amount of better voice-picking in
   * this file can meet her ask; the audio has to come from the relay. The device voice stays
   * as the fallback for when she is offline or this device has never been connected.
   *
   * It is also the only way her 15 Sep ask - "I can have it play in the background" - can
   * ever work on a phone: iOS suspends speechSynthesis when the screen locks, and only a
   * real <audio> element with MediaSession keeps going.
   */
  var RELAY = "https://apps-notion-relay.apps-notion-relay.workers.dev";
  var PASS_KEY = "notionSync.pass";        // she types it once per device; shared with notion-sync.js
  var K_CLOUD = "speak.natural";           // "0" = she turned the natural voice off on this device
  var K_NVOICE = "speak.nvoice";
  // ⚠ 19 Sep 2026: Aoede is the DEFAULT because Prayer Points picked it on 15 Sep and the recipes
  // and AFR copied it - NOT because she chose it. She asked "did i chose aoede?" and the record
  // says no: her only words there were "Everything.", agreeing to have a natural voice at all.
  // Do not describe it to her as her pick until she has actually made one.
  var NATURAL = [["aoede", "Aoede - the one in use today"], ["achernar", "Achernar"], ["kore", "Kore"],
                 ["charon", "Charon"], ["puck", "Puck"]];
  function pass() {
    // notion-sync.js writes it JSON-encoded; tolerate a raw string too, because guessing wrong
    // here would silently drop back to the robot voice and look like the feature never shipped.
    var raw = store.get(PASS_KEY);
    if (!raw) return null;
    try { var p = JSON.parse(raw); if (typeof p === "string" && p) return p; } catch (e) {}
    return typeof raw === "string" && raw.charAt(0) !== "{" && raw.charAt(0) !== "[" ? raw : null;
  }
  // An app whose words should never leave the phone puts data-no-natural on its script tag, and
  // then nothing on that page is ever sent anywhere - whatever the tick box on other apps says.
  var NO_NATURAL = !!(document.currentScript && document.currentScript.hasAttribute("data-no-natural"));
  function cloudOn() { return !NO_NATURAL && store.get(K_CLOUD) !== "0" && !!pass(); }
  var audioEl = null, cloudBroken = false, playToken = 0;
  function getAudio() {
    if (audioEl) return audioEl;
    audioEl = document.createElement("audio");
    audioEl.preload = "auto";
    audioEl.setAttribute("playsinline", "");           // iOS: play in place, never full-screen
    audioEl.style.display = "none";
    document.body.appendChild(audioEl);
    return audioEl;
  }

  /* 19 Sep 2026, her note on Prayer Points: "Voice on top not at the bottom". The three bubbles
     stack up the left edge - speak, textsize Aa at 140, feedback - and the voice one was lowest.
     Moved to 192 so it sits on top. Taken from the Mac's commit b61bdbc; the REST of that commit
     is NOT taken, because it was written from a copy that had lost her 17 Sep drag-anywhere and
     resize-height work, and merging it would have quietly undone both. */
  var css = document.createElement("style");
  css.textContent =
    ".sa-fab{position:fixed;left:12px;bottom:calc(192px + env(safe-area-inset-bottom));z-index:2147483644;" +
    "display:flex;align-items:center;gap:6px;font:600 13px/1 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;" +
    "padding:10px 14px;border-radius:999px;border:0;background:#1c1c1e;color:#fff;box-shadow:0 4px 16px rgba(0,0,0,.25);cursor:pointer}" +
    /* 17 Sep 2026, her words: the mic "should look like exactly what it is for the speaker, as well as AA floating" -
       so the icon-only bubble is the same 44 px circle as the Aa (textsize.js) and 🎙 (feedback.js) bubbles */
    ".sa-fab.sa-icon{width:44px;height:44px;box-sizing:border-box;padding:0;justify-content:center;font-size:18px}" +
    ".sa-fab:focus-visible,.sa-panel button:focus-visible,.sa-panel select:focus-visible{outline:2px solid #6c8cff;outline-offset:2px}" +
    ".sa-panel{position:fixed;left:12px;right:12px;bottom:calc(192px + env(safe-area-inset-bottom));z-index:2147483645;max-width:420px;" +
    "background:#fff;color:#1c1c1e;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.3);padding:10px 10px 16px;overflow:auto;box-sizing:border-box;" +
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

  /* ---------- voices (the fallback, for when the natural voice is off or unreachable) ---------- */
  var GOOD = /(Siri|Enhanced|Premium|Natural|Neural|Wavenet|Google)/i;
  /* ⛔ HER REPORT, 19 Sep 2026: "the albert thing is reading the bible. its very bad dont hire
     albert for voice over." Albert is one of Apple's joke voices and the old penalty list did not
     name it - nor Fred, Junior, Bahh, Ralph or Kathy, and her Mac has several of them (measured
     19 Sep: 184 voices, ZERO Enhanced/Premium/Siri/Natural, one en_AU). So Albert scored the same
     as any ordinary American voice and the sort order decided.
     ⭐ A BLOCKLIST OF SILLY NAMES IS ALWAYS MISSING THE NEXT ONE. So an unrecognised name now
     scores BELOW every voice known to be a real speaking voice; the blocklist is the second line,
     not the only one. */
  var REAL = /(samantha|karen|daniel|moira|tessa|rishi|fiona|alex|ava|allison|susan|nicky|aaron|serena|martha|arthur|gordon|catherine|james|hazel|george|zira|david|mark|jenny|aria|guy|google|siri|natural|neural|enhanced|premium|wavenet|chirp|polyglot)/i;
  var JOKE = /(albert|bad news|good news|bahh|bells|boing|bubbles|cellos|deranged|hysterical|jester|junior|kathy|organ|princess|ralph|superstar|trinoids|whisper|wobble|zarvox|fred|bruce|agnes|victoria|novelty|eloquence|compact|espeak)/i;
  function score(v) {
    var s = 0, lang = (v.lang || "").replace("_", "-");
    if (/^en-AU/i.test(lang)) s += 40; else if (/^en-GB/i.test(lang)) s += 30; else if (/^en-US/i.test(lang)) s += 20; else if (/^en/i.test(lang)) s += 10;
    if (GOOD.test(v.name)) s += 25;
    if (v.localService) s += 3;
    if (JOKE.test(v.name)) s -= 90;
    else if (!REAL.test(v.name)) s -= 25;    // never heard of it: below anything known to be real
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
    var saved = list.filter(function (v) { return v.voiceURI === want; })[0];
    // Better scoring alone would NOT have fixed her phone: a joke voice already saved here wins
    // over any scoring for ever. So a saved joke voice is dropped and re-picked. Anything else
    // she chose is left alone.
    if (saved && JOKE.test(saved.name)) { store.set(K_VOICE, ""); saved = null; }
    return saved || list[0] || null;
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
  function rate() { var r = parseFloat(store.get(K_RATE) || "1"); return r >= 0.5 && r <= 2 ? r : 1; }

  /* Speed is applied by the PLAYER, not by Google, so every speed shares one cached clip and
     changing speed is instant and costs nothing. */
  function clip(i) {
    var p = parts[i];
    if (!p) return Promise.resolve(null);
    if (p.url) return Promise.resolve(p.url);
    if (p.pending) return p.pending;
    var pw = pass();
    if (!pw) return Promise.reject(new Error("this device is not connected"));
    p.pending = fetch(RELAY + "/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Pass": pw },
      body: JSON.stringify({ text: p.text, voice: store.get(K_NVOICE) || "aoede" })
    }).then(function (r) {
      if (!r.ok) return r.json()["catch"](function () { return {}; }).then(function (j) {
        // 404 = the relay has not been redeployed with /tts yet; 503 = no Google key in Cloudflare.
        // Both are "not switched on", not a fault, and she should not be shown a bare status code.
        if (!j.error && (r.status === 404 || r.status === 503)) throw new Error("The natural voice is not switched on yet - using the phone voice.");
        throw new Error(j.error || ("the voice server said " + r.status));
      });
      return r.blob();
    }).then(function (b) { p.url = URL.createObjectURL(b); p.pending = null; return p.url; },
      function (e) { p.pending = null; throw e; });
    return p.pending;
  }

  function media() {
    if (!("mediaSession" in navigator)) return;
    try {
      navigator.mediaSession.metadata = new window.MediaMetadata({ title: document.title || "Read aloud", artist: location.hostname });
      navigator.mediaSession.setActionHandler("play", function () { if (paused) { paused = false; resume(); } });
      navigator.mediaSession.setActionHandler("pause", function () { holdOn(); });
      navigator.mediaSession.setActionHandler("stop", function () { finish(""); });
    } catch (e) {}
  }

  // Never silent: if the natural voice cannot be reached she is TOLD - and since
  // 19 Sep 2026 ("get rid of karen") reading STOPS there rather than dropping to
  // the phone voice, so a fault is heard as a fault and not as a bad voice.
  function toPhone(why) {
    cloudBroken = true;
    finish(why || whyNoNatural());
  }

  /* ---- 19 Sep 2026, her words: "how about you get rid of karen" -------------
     Karen is the phone's own voice. It used to be the SILENT fallback whenever
     the natural voice could not be reached, which is exactly why she pressed
     Read aloud, heard the robot, and concluded nothing had shipped. It now says
     what is wrong instead, so a fault looks like a fault.
     ⚠ The cost of this: with no internet there is no read aloud at all.
     sayOnDevice is kept, unused, so turning Karen back on is one line.
  --------------------------------------------------------------------------- */
  function whyNoNatural() {
    if (NO_NATURAL) return "This app keeps its words on your phone, so it has no natural voice.";
    if (store.get(K_CLOUD) === "0") return "The natural voice is switched off here \u2014 turn it back on above.";
    if (!pass()) return "The natural voice needs this device connected \u2014 enter the apps password once.";
    return "The natural voice could not be reached just now. Try again in a moment.";
  }

  function sayOnDevice(p) {   /* kept, no longer called - see the note above */
    if (!p) return;
    var u = new SpeechSynthesisUtterance(p.text);
    var v = /[\uAC00-\uD7A3]/.test(p.text) ? (koreanVoice() || chosenVoice()) : chosenVoice();
    if (v) { u.voice = v; u.lang = v.lang; }
    u.rate = rate();
    u.onend = function () { if (playing && !paused) { idx++; step(); } };
    u.onerror = function (e) { if (playing && !paused && e.error !== "interrupted" && e.error !== "canceled") { idx++; step(); } };
    SS.speak(u);
  }

  function sayFromRelay(p) {
    var a = getAudio(), mine = ++playToken;
    clip(idx).then(function (url) {
      if (!playing || paused || mine !== playToken) return;
      a.src = url;
      a.playbackRate = rate();
      a.onended = function () { if (playing && !paused && mine === playToken) { idx++; step(); } };
      a.onerror = function () { toPhone("That clip would not play - using the phone voice."); };
      var pr = a.play();
      if (pr && pr["catch"]) pr["catch"](function () { toPhone("The phone blocked the audio. Press Read again."); });
      media();
      clip(idx + 1);          // the next piece is fetched while this one plays, so there is no gap
    })["catch"](function (e) {
      // The relay writes its own full sentence (allowance used up, not connected, ...). Show it
      // whole - cutting it at 80 characters produced "and the phone vo - using the phone voice."
      var m = String(e && e.message || e);
      toPhone(/phone voice/i.test(m) ? m : m.replace(/\s*$/, "").slice(0, 120) + " - using the phone voice.");
    });
  }

  function step() {
    if (!playing || paused) return;
    if (idx >= parts.length) { finish("Finished."); return; }
    var p = parts[idx];
    mark(p.el);
    nowEl.textContent = p.text.length > 90 ? p.text.slice(0, 88) + "\u2026" : p.text;
    paint();
    if (cloudOn() && !cloudBroken) sayFromRelay(p); else finish(whyNoNatural());
  }
  function holdOn() {
    paused = true;
    try { SS.cancel(); } catch (e) {}
    if (audioEl) { try { audioEl.pause(); } catch (e) {} }
    paint();
  }
  function resume() {
    // a part-played clip carries on where it stopped; the phone voice has to redo the sentence
    if (audioEl && audioEl.src && audioEl.currentTime > 0 && !audioEl.ended && cloudOn() && !cloudBroken) {
      var pr = audioEl.play();
      if (pr && pr["catch"]) pr["catch"](function () { step(); });
      paint();
      return;
    }
    step();
  }
  function start() {
    SS.cancel();
    parts = collect(); idx = 0; paused = false; cloudBroken = false; playToken++;
    if (!parts.length) { nowEl.textContent = "Nothing to read on this screen."; return; }
    playing = true;
    if (!cloudOn()) { playing = false; nowEl.textContent = whyNoNatural(); paint(); return; }
    nowEl.textContent = "Fetching the natural voice\u2026";
    step();
  }
  function finish(msg) {
    playing = false; paused = false; playToken++;
    SS.cancel(); mark(null);
    if (audioEl) { try { audioEl.pause(); audioEl.removeAttribute("src"); audioEl.load(); } catch (e) {} }
    parts.forEach(function (p) { if (p.url) { try { URL.revokeObjectURL(p.url); } catch (e) {} p.url = null; } });
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
      /* Her feedback 17 Sep 2026: "all the floating things should be movable, no matter where
         you're dragging." The panel used to drag only by its grip. Now the whole card is the
         handle, so the guard has to skip the controls INSIDE it - while still letting the fab
         itself be dragged, since the fab IS a button. */
      if (e.button > 0) return;
      var hit = e.target.closest("button,select,input,textarea,a,.sa-rsz");
      if (hit && hit !== el) return;
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
      /* 19 Sep 2026: the line that used to sit here sent her into iPhone Settings to DOWNLOAD a
         voice. That is the exact thing she asked to be rid of, and it is now handled by the relay. */
      '<div class="sa-row"><label style="flex:1">Voice <select class="sa-nvoice" style="width:100%"></select></label></div>' +
      '<div class="sa-row"><label style="flex:1"><input type="checkbox" class="sa-cloud"> Natural voice</label></div>' +
      '<div class="sa-row sa-phonerow" hidden><label style="flex:1">Phone voice (used when the natural one is off) ' +
      '<select class="sa-voice" style="width:100%"></select></label></div>' +
      '<div class="sa-now sa-note"></div>';
    document.body.appendChild(fab); document.body.appendChild(panel);
    makeDraggable(fab, "speak.pos");
    makeDraggable(panel, "speak.panel.pos");   /* whole card, not just .sa-grip - her 17 Sep feedback */
    (function (grip) {   /* 17 Sep: "everything is resizable the boxes and movable" - drag the corner */
      /* her 17 Sep (Sales Tracker): "cannot be resized to the smaller version as much. It just stays big."
         Width AND height now, down to 180 x 110; what does not fit scrolls inside the panel. */
      var on = false, sx = 0, sy = 0, w0 = 0, h0 = 0;
      function setW(w) { panel.style.setProperty("max-width", "none", "important");
        panel.style.setProperty("width", Math.max(180, Math.min(w, window.innerWidth - 8)) + "px", "important");
        panel.style.setProperty("right", "auto", "important"); }
      function setH(h) { var t = panel.getBoundingClientRect().top;
        panel.style.setProperty("height", Math.max(110, Math.min(h, window.innerHeight - Math.max(t, 0) - 4)) + "px", "important");
        panel.style.setProperty("bottom", "auto", "important"); panel.style.setProperty("top", Math.max(t, 4) + "px", "important"); }
      panel.restoreSize = function () { var f = +store.get("speak.panel.w"); if (f) setW(f * window.innerWidth);
        var g = +store.get("speak.panel.h"); if (g) setH(g * window.innerHeight); };
      grip.addEventListener("pointerdown", function (e) { on = true; sx = e.clientX; sy = e.clientY; var r = panel.getBoundingClientRect(); w0 = r.width; h0 = r.height;
        panel.style.setProperty("left", r.left + "px", "important"); panel.style.setProperty("top", r.top + "px", "important");
        panel.style.setProperty("bottom", "auto", "important"); try { grip.setPointerCapture(e.pointerId); } catch (x) {} e.preventDefault(); e.stopPropagation(); });
      grip.addEventListener("pointermove", function (e) { if (on) { setW(w0 + e.clientX - sx); setH(h0 + e.clientY - sy); e.preventDefault(); } });
      function end() { if (!on) return; on = false; var r = panel.getBoundingClientRect();
        store.set("speak.panel.w", String(r.width / window.innerWidth)); store.set("speak.panel.h", String(r.height / window.innerHeight)); }
      grip.addEventListener("pointerup", end); grip.addEventListener("pointercancel", end);
    })(panel.querySelector(".sa-rsz"));
    mainBtn = panel.querySelector(".sa-main"); stopBtn = panel.querySelector(".sa-stop");
    rateSel = panel.querySelector(".sa-rate"); voiceSel = panel.querySelector(".sa-voice");
    nowEl = panel.querySelector(".sa-now"); barEl = panel.querySelector(".sa-bar i");
    var nvoiceSel = panel.querySelector(".sa-nvoice"), cloudBox = panel.querySelector(".sa-cloud");
    var phoneRow = panel.querySelector(".sa-phonerow"), noteEl = panel.querySelector(".sa-note");
    rateSel.value = store.get(K_RATE) || "1";
    nvoiceSel.innerHTML = NATURAL.map(function (v) {
      return '<option value="' + v[0] + '"' + ((store.get(K_NVOICE) || "aoede") === v[0] ? " selected" : "") + ">" + v[1] + "</option>";
    }).join("");
    function paintNote() {
      var on = !NO_NATURAL && store.get(K_CLOUD) !== "0";
      cloudBox.checked = on;
      cloudBox.disabled = NO_NATURAL;
      nvoiceSel.disabled = !on;
      phoneRow.hidden = on && !!pass();
      noteEl.textContent = NO_NATURAL
        ? "This app is set to keep its words on the phone, so it uses the phone's own voice."
        : !on
        ? "Natural voice is off on this device - using the phone's own voice."
        : (pass() ? "Australian, and it keeps reading when the screen locks. Korean is read by a Korean voice."
                  : "Tap Connect on this app first - the natural voice uses the same apps password. Until then, the phone voice.");
    }
    paintNote();
    fillVoices();
    fab.addEventListener("click", function () { panel.hidden = !panel.hidden; if (!panel.hidden) { fillVoices(); paintNote(); panel.restoreSize(); panel.restorePos(); } });
    panel.querySelector(".sa-close").addEventListener("click", function () { panel.hidden = true; });
    mainBtn.addEventListener("click", function () {
      if (!playing) { start(); return; }
      if (!paused) { holdOn(); return; }
      paused = false; resume();
    });
    stopBtn.addEventListener("click", function () { finish(""); });
    // Speed is the player's, not Google's, so it changes mid-sentence for free on the natural voice.
    rateSel.addEventListener("change", function () {
      store.set(K_RATE, rateSel.value);
      if (audioEl) audioEl.playbackRate = rate();
      if (playing && !paused && (!cloudOn() || cloudBroken)) { SS.cancel(); step(); }
    });
    cloudBox.addEventListener("change", function () {
      store.set(K_CLOUD, cloudBox.checked ? "1" : "0");
      cloudBroken = false; paintNote();
      if (playing) { var at = idx; finish(""); parts = collect(); idx = Math.min(at, Math.max(parts.length - 1, 0)); playing = true; step(); }
    });
    nvoiceSel.addEventListener("change", function () {
      store.set(K_NVOICE, nvoiceSel.value);
      parts.forEach(function (p) { if (p.url) { try { URL.revokeObjectURL(p.url); } catch (e) {} } p.url = null; p.pending = null; });
      if (playing && !paused) { playToken++; if (audioEl) { try { audioEl.pause(); } catch (e) {} } step(); }
    });
    voiceSel.addEventListener("change", function () { store.set(K_VOICE, voiceSel.value); if (playing && !paused) { SS.cancel(); step(); } });
    if ("onvoiceschanged" in SS) SS.addEventListener("voiceschanged", fillVoices);
    paint();
  }

  // ⛔ STOP TALKING WHEN THE APP IS CLOSED OR BACKGROUNDED.
  // Her feedback, 16 Sep 2026, Rachie's Desk: "So the voice gets out of it when
  // I quit. So it has been fixed but hasn't." It had been fixed on the Desk page
  // ONLY, inline, and the Desk is one of eight apps that load this shared file -
  // measured 18 Sep 2026: the live speak.js had no pagehide, no beforeunload, no
  // visibilitychange and no cancel of any kind, so every other app kept speaking.
  //
  // pagehide is the one that matters and the one the Desk's inline fix missed: on
  // iOS, closing or swiping away an installed web app fires pagehide, and does not
  // reliably fire beforeunload. visibilitychange covers backgrounding, and
  // beforeunload covers a desktop tab close. All three, because no single event
  // fires on every platform.
  // ⚠ 19 Sep 2026 - TWO OF HER ASKS MEET HERE, AND THE SPLIT IS DELIBERATE.
  //   15 Sep: "I can have it play in the background."
  //   16 Sep: "So the voice gets out of it when I quit."
  // Quitting is not backgrounding. The old code treated them the same and hushed on both, which
  // honoured the newer ask by breaking the older one. Now:
  //   QUIT (pagehide / beforeunload) -> everything stops. Her 16 Sep ask, untouched.
  //   BACKGROUND (tab hidden)        -> the natural voice KEEPS READING, which is her 15 Sep ask
  //                                     and the whole reason the audio comes from a server;
  //                                     the phone's own voice is still stopped, because iOS
  //                                     suspends it anyway and a half-suspended robot voice was
  //                                     what made this feel broken.
  function hush(quit) {
    try { SS.cancel(); } catch (e) {}
    if (quit && audioEl) { try { audioEl.pause(); } catch (e) {} }
  }
  window.addEventListener("pagehide", function () { hush(true); });
  window.addEventListener("beforeunload", function () { hush(true); });
  document.addEventListener("visibilitychange", function () {
    if (document.visibilityState === "hidden") hush(false);
  });

  // hush() from outside means STOP, so it passes quit=true - a caller asking for silence and
  // getting audio that keeps playing is the bug this whole split is meant to avoid.
  window.SpeakAloud = { start: function () { start(); }, stop: function () { finish(""); },
                        draggable: makeDraggable, hush: function () { hush(true); } };
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", build); else build();
})();
