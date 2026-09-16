/* feedback.js - a 🎙 bubble on every app: speak or type feedback, and it lands in Notion.
 *
 * Her words, 16 Sep 2026: "So I want you to just add everything, every app, the mic button for me to give you
 * the feedback." and "It should look like exactly what it is for the speaker, as well as AA floating."
 *
 *  - The bubble looks and moves like the Aa (textsize.js) and Read aloud (speak.js) bubbles: drag it anywhere,
 *    it stays there on this device; a tap opens the sheet next to it.
 *  - Speaking uses the browser's own speech-to-text where there is one, and the words appear live in a box she
 *    can edit. Where there is none (or the phone blocks it), the box says to use the 🎤 on the keyboard.
 *    Nothing here records or uploads audio: only the words in the box are sent.
 *  - Send saves on this device first, then sends to Notion ("💬 App feedback") through apps-notion-relay with the
 *    same apps password as notion-sync.js. Offline, or before the password is in, it waits and says so, and it
 *    sends by itself when it can. It never fails silently and never drops her words.
 *
 *   <script src="/feedback.js" defer></script>      optional: data-app="Name of the app"
 */
(function () {
  "use strict";
  if (window.AppFeedback) return;
  var D = document, W = window;
  var RELAY = "https://apps-notion-relay.apps-notion-relay.workers.dev";
  var PASS_KEY = "notionSync.pass";          // shared with notion-sync.js: one password per device
  var QUEUE_KEY = "feedback.queue", DRAFT_KEY = "feedback.draft", POS_KEY = "feedback.pos";
  var me = D.currentScript;
  var APP_NAME = (me && me.getAttribute("data-app")) || "";
  var store = {
    get: function (k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { localStorage.setItem(k, v); return true; } catch (e) { return false; } },
    del: function (k) { try { localStorage.removeItem(k); } catch (e) {} },
    json: function (k, v) {
      try {
        if (v === undefined) return JSON.parse(localStorage.getItem(k) || "null");
        if (v === null) localStorage.removeItem(k); else localStorage.setItem(k, JSON.stringify(v));
        return true;
      } catch (e) { return v === undefined ? null : false; }
    }
  };
  function pass() { var p = store.json(PASS_KEY); return typeof p === "string" && p ? p : null; }
  function queue() { var q = store.json(QUEUE_KEY); return Array.isArray(q) ? q : []; }

  /* ---------- drag the bubble anywhere, position kept per device (same as speak.js / textsize.js) ---------- */
  function makeDraggable(el, key) {
    var sx = 0, sy = 0, ox = 0, oy = 0, moved = false, down = false, pid = null;
    function place(x, y) {
      var w = el.offsetWidth, h = el.offsetHeight;
      x = Math.max(4, Math.min(W.innerWidth - w - 4, x));
      y = Math.max(4, Math.min(W.innerHeight - h - 4, y));
      el.style.setProperty("left", x + "px", "important"); el.style.setProperty("top", y + "px", "important");
      el.style.setProperty("right", "auto", "important"); el.style.setProperty("bottom", "auto", "important");
    }
    function restore() {
      var v = store.get(key); if (!v || !el.offsetWidth) return;
      try { var p = JSON.parse(v); place(p[0] * W.innerWidth, p[1] * W.innerHeight); } catch (e) {}
    }
    el.style.touchAction = "none";
    el.addEventListener("pointerdown", function (e) {
      if (e.button > 0) return;
      down = true; moved = false; pid = e.pointerId;
      var r = el.getBoundingClientRect(); sx = e.clientX; sy = e.clientY; ox = r.left; oy = r.top;
    });
    el.addEventListener("pointermove", function (e) {
      if (!down || e.pointerId !== pid) return;
      var dx = e.clientX - sx, dy = e.clientY - sy;
      if (!moved && Math.abs(dx) + Math.abs(dy) < 8) return;
      if (!moved) { moved = true; try { el.setPointerCapture(pid); } catch (x) {} }
      place(ox + dx, oy + dy); e.preventDefault();
    });
    function up() {
      if (!down) return; down = false;
      if (moved) { var r = el.getBoundingClientRect(); store.set(key, JSON.stringify([r.left / W.innerWidth, r.top / W.innerHeight])); }
    }
    el.addEventListener("pointerup", up); el.addEventListener("pointercancel", up);
    el.addEventListener("click", function (e) { if (moved) { e.stopImmediatePropagation(); e.preventDefault(); moved = false; } }, true);
    W.addEventListener("resize", restore);
    restore(); setTimeout(restore, 300);   /* not requestAnimationFrame: it never fires in a hidden tab */
    return restore;
  }

  /* ---------- what gets sent ---------- */
  function device() {
    var ua = navigator.userAgent || "", coarse = W.matchMedia && W.matchMedia("(pointer: coarse)").matches;
    if (/iPad/.test(ua) || (/Macintosh/.test(ua) && navigator.maxTouchPoints > 1)) return "tablet";
    if (/iPhone|iPod|Android.+Mobile|Mobile/.test(ua)) return "phone";
    if (coarse) return Math.min(screen.width, screen.height) < 600 ? "phone" : "tablet";
    return "desktop";
  }
  function textSize() {
    try {
      var t = W.TextSize && W.TextSize.get();
      if (t) return Math.round(t.scale * 100) + "%" + (t.bold ? ", Bold" : "");
    } catch (e) {}
    return "";
  }
  function appName() {
    if (APP_NAME) return APP_NAME;
    var t = (D.title || "").split(/\s[|—–-]\s/)[0].trim();
    return t || location.hostname + location.pathname;
  }
  function newId() { return "fb-" + Date.now().toString(36) + "-" + Math.random().toString(36).slice(2, 8); }

  /* ---------- sending ---------- */
  var flushing = false, lastNote = "";
  function send(item, p) {
    var ctrl = typeof AbortController === "function" ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, 20000) : null;
    return fetch(RELAY + "/feedback", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Pass": p },
      body: JSON.stringify(item),
      signal: ctrl ? ctrl.signal : undefined
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (out) { clearTimeout(timer); return { status: r.status, ok: r.ok, out: out || {} }; });
    }, function (e) { clearTimeout(timer); throw e; });
  }
  // Tells the sheet (if open) where things stand. tone: ok | wait | bad
  function note(text, tone) { lastNote = text; if (statusEl) { statusEl.textContent = text; statusEl.className = "fb-status fb-" + (tone || "ok"); } paintQueue(); }

  function flush() {
    var q = queue();
    paintQueue();
    if (flushing || !q.length) return Promise.resolve();
    var p = pass();
    if (!p) { note(q.length === 1 ? "Saved on this phone. Tap Connect to send it to Notion." : "Saved on this phone (" + q.length + "). Tap Connect to send them to Notion.", "wait"); return Promise.resolve(); }
    if (navigator.onLine === false) { note("Saved on this phone, will send when online.", "wait"); return Promise.resolve(); }
    flushing = true;
    var item = q[0];
    return send(item, p).then(function (r) {
      flushing = false;
      if (r.status === 401) { store.del(PASS_KEY); note("The apps password didn't work. Saved on this phone - tap Connect.", "bad"); return; }
      if (r.ok && r.out.ok) {
        store.json(QUEUE_KEY, queue().filter(function (x) { return x.id !== item.id; }));
        if (queue().length) return flush();
        note("Sent ✓", "ok");
        return;
      }
      bump(item);
      if (r.status === 404) note("Saved on this phone. Sending to Notion isn't switched on yet - it will send by itself once it is.", "wait");
      else note("Notion didn't take it yet (" + (r.out.error || "error " + r.status) + "). Saved on this phone, will try again.", "bad");
    }, function () {
      flushing = false;
      bump(item);
      note("Saved on this phone, will send when online.", "wait");
    });
  }
  function bump(item) {                                  // to the back, so one stuck item never blocks the rest
    var q = queue().filter(function (x) { return x.id !== item.id; });
    item.tries = (item.tries || 0) + 1; q.push(item); store.json(QUEUE_KEY, q);
  }

  /* ---------- the one-time password sheet (same as notion-sync.js; stored the same way) ---------- */
  function connect() {
    if (W.NotionSync && W.NotionSync.connect) return W.NotionSync.connect().then(function (ok) { if (ok) flush(); return ok; });
    return new Promise(function (resolve) {
      var wrap = D.createElement("div");
      wrap.setAttribute("data-speak-skip", "");
      wrap.style.cssText = "position:fixed;inset:0;z-index:2147483647;background:rgba(20,20,25,.45);display:flex;align-items:flex-end;justify-content:center;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif";
      wrap.innerHTML =
        '<form style="background:#fff;color:#1c1c1e;width:100%;max-width:420px;border-radius:18px 18px 0 0;padding:22px 20px calc(20px + env(safe-area-inset-bottom));box-shadow:0 -6px 30px rgba(0,0,0,.2)">' +
        '<div style="font-size:17px;font-weight:600;margin-bottom:6px">Connect to Notion</div>' +
        '<div style="font-size:14px;color:#555;margin-bottom:14px;line-height:1.4">Enter the apps password once on this device. Your feedback will be sent to Notion.</div>' +
        '<input type="password" autocomplete="current-password" placeholder="Apps password" style="width:100%;box-sizing:border-box;font-size:16px;padding:12px 14px;border:1px solid #d1d1d6;color:#1c1c1e;background:#fff;font-family:inherit;border-radius:12px;margin-bottom:12px">' +
        '<div style="display:flex;gap:10px"><button type="button" class="fb-later" style="flex:1;padding:12px;border-radius:12px;border:0;background:#f2f2f7;color:#1c1c1e;font-size:15px;font-weight:500;font-family:inherit">Later</button>' +
        '<button type="submit" style="flex:2;padding:12px;border-radius:12px;border:0;background:#1c1c1e;color:#fff;font-size:15px;font-weight:600;font-family:inherit">Connect</button></div></form>';
      D.body.appendChild(wrap);
      var input = wrap.querySelector("input");
      setTimeout(function () { input.focus(); }, 50);
      wrap.querySelector(".fb-later").onclick = function () { wrap.remove(); resolve(false); };
      wrap.querySelector("form").onsubmit = function (e) {
        e.preventDefault();
        var v = input.value.trim();
        if (!v) return;
        store.json(PASS_KEY, v); wrap.remove(); resolve(true); flush();
      };
    });
  }

  /* ---------- speech ---------- */
  var SR = W.SpeechRecognition || W.webkitSpeechRecognition || null;
  var rec = null, listening = false, baseText = "", finals = "";
  function startListening() {
    if (!SR) { showHint(); return; }
    try {
      rec = new SR();
      rec.lang = navigator.language || "en-AU";
      rec.continuous = true; rec.interimResults = true;
      baseText = box.value ? box.value.replace(/\s*$/, " ") : ""; finals = "";
      rec.onresult = function (e) {
        var interim = "";
        for (var i = e.resultIndex; i < e.results.length; i++) {
          var t = e.results[i][0].transcript;
          if (e.results[i].isFinal) finals += t; else interim += t;
        }
        box.value = baseText + finals + interim;
        saveDraft();
      };
      rec.onerror = function (e) {
        if (e.error === "no-speech" || e.error === "aborted") return;
        showHint(e.error === "not-allowed" || e.error === "service-not-allowed" ? "The microphone is blocked here." : "Speech didn't start.");
      };
      rec.onend = function () { listening = false; paintMic(); };
      rec.start(); listening = true; paintMic();
    } catch (e) { listening = false; paintMic(); showHint(); }
  }
  function stopListening() { try { rec && rec.stop(); } catch (e) {} listening = false; paintMic(); }
  function showHint(prefix) {
    hint.hidden = false;
    hint.textContent = (prefix ? prefix + " " : "") + "Tap the box, then the 🎤 on your keyboard to speak.";
    if (!SR) micBtn.hidden = true;
    try { box.focus({ preventScroll: true }); } catch (e) {}
    paintMic();
  }
  function saveDraft() { if (box.value) store.set(DRAFT_KEY, box.value); else store.del(DRAFT_KEY); }

  /* ---------- the bubble and sheet (styled like textsize.js's Aa) ---------- */
  var fab, panel, box, micBtn, sendBtn, hint, statusEl, queueEl, connectBtn;
  function paintMic() {
    if (!micBtn) return;
    micBtn.classList.toggle("fb-on", listening);
    micBtn.setAttribute("aria-pressed", listening ? "true" : "false");
    micBtn.innerHTML = listening ? '<span class="fb-big">⏹</span><span>Listening… tap to stop</span>' : '<span class="fb-big">🎙</span><span>Tap to speak</span>';
  }
  function paintQueue() {
    if (!queueEl) return;
    var n = queue().length, need = n && !pass();
    queueEl.hidden = !n;
    queueEl.textContent = n ? (n === 1 ? "1 feedback waiting to send" : n + " feedback waiting to send") : "";
    connectBtn.hidden = !need;
    fab.classList.toggle("fb-set", !!n);
  }
  function build() {
    if (fab || !D.body) return;
    var css = D.createElement("style");
    css.setAttribute("data-ts-own", "");
    css.textContent =
      ".fb-fab{position:fixed;left:12px;bottom:calc(192px + env(safe-area-inset-bottom));z-index:2147483643;" +
      "width:44px;height:44px;box-sizing:border-box;display:flex;align-items:center;justify-content:center;text-align:center;padding:0;margin:0;-webkit-appearance:none;appearance:none;" +
      "font:700 18px/1 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:0;" +
      "border-radius:999px;border:0;background:#1c1c1e;color:#fff;box-shadow:0 4px 16px rgba(0,0,0,.25);cursor:pointer}" +
      ".fb-fab[hidden]{display:none}" +
      ".fb-fab.fb-set::after{content:'';position:absolute;top:5px;right:5px;width:8px;height:8px;border-radius:50%;background:#ff9f0a}" +
      ".fb-fab:focus-visible,.fb-panel button:focus-visible,.fb-panel textarea:focus-visible{outline:2px solid #6c8cff;outline-offset:2px}" +
      ".fb-panel{position:fixed;left:12px;bottom:calc(192px + env(safe-area-inset-bottom));z-index:2147483646;" +
      "width:min(320px,calc(100vw - 24px));box-sizing:border-box;background:#fff;color:#1c1c1e;border-radius:16px;" +
      "box-shadow:0 10px 40px rgba(0,0,0,.3);padding:12px;display:grid;gap:8px;" +
      "font:400 14px/1.3 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;text-align:left}" +
      ".fb-panel[hidden],.fb-panel [hidden]{display:none}" +
      ".fb-panel .fb-row{display:flex;gap:8px;align-items:center}" +
      ".fb-panel .fb-title{flex:1;font:600 14px/1.2 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif}" +
      ".fb-panel button{flex:1;min-height:44px;min-width:44px;box-sizing:border-box;margin:0;display:flex;align-items:center;justify-content:center;gap:8px;text-align:center;-webkit-appearance:none;appearance:none;" +
      "font:600 15px/1.1 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:0;text-transform:none;" +
      "border:0;border-radius:10px;padding:0 12px;background:#f2f2f7;color:#1c1c1e;cursor:pointer;box-shadow:none}" +
      ".fb-panel button:disabled{opacity:.35;cursor:default}" +
      ".fb-panel button.fb-close{flex:0 0 44px;background:transparent;font-size:18px}" +
      ".fb-panel button.fb-mic{min-height:64px;font-size:16px}.fb-panel .fb-big{font-size:26px;line-height:1}" +
      ".fb-panel button.fb-mic.fb-on{background:#ff3b30;color:#fff}" +
      ".fb-panel button.fb-send{background:#1c1c1e;color:#fff}" +
      ".fb-panel textarea{display:block;width:100%;box-sizing:border-box;min-height:96px;max-height:40vh;resize:vertical;margin:0;" +
      "font:400 16px/1.35 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;letter-spacing:0;text-transform:none;" +
      "padding:10px 12px;border-radius:10px;border:1px solid #d1d1d6;background:#fff;color:#1c1c1e;box-shadow:none}" +
      ".fb-panel .fb-hint,.fb-panel .fb-queue{font:400 13px/1.35 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#636366}" +
      ".fb-panel .fb-status{font:600 13px/1.35 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;min-height:1.35em}" +
      ".fb-panel .fb-ok{color:#1d6b43}.fb-panel .fb-wait{color:#7a5200}.fb-panel .fb-bad{color:#9b1c1c}" +
      "@media (prefers-color-scheme: dark){.fb-panel{background:#1c1c1e;color:#f2f2f7}.fb-panel button{background:#2c2c2e;color:#f2f2f7}" +
      ".fb-panel button.fb-close{background:transparent}.fb-panel button.fb-send{background:#f2f2f7;color:#1c1c1e}" +
      ".fb-panel textarea{background:#2c2c2e;color:#f2f2f7;border-color:#3a3a3c}.fb-panel .fb-hint,.fb-panel .fb-queue{color:#aeaeb2}" +
      ".fb-panel .fb-ok{color:#63d98e}.fb-panel .fb-wait{color:#ffd60a}.fb-panel .fb-bad{color:#ff8a80}}";
    (D.head || D.documentElement).appendChild(css);

    fab = D.createElement("button");
    fab.type = "button"; fab.className = "fb-fab"; fab.textContent = "🎙";
    fab.setAttribute("aria-label", "Give feedback"); fab.title = "Give feedback"; fab.setAttribute("aria-haspopup", "dialog");
    fab.setAttribute("data-speak-skip", ""); fab.setAttribute("data-ts-own", "");
    panel = D.createElement("div");
    panel.className = "fb-panel"; panel.hidden = true;
    panel.setAttribute("role", "dialog"); panel.setAttribute("aria-label", "Feedback");
    panel.setAttribute("data-speak-skip", ""); panel.setAttribute("data-ts-own", "");
    panel.innerHTML =
      '<div class="fb-row"><span class="fb-title">Feedback for this app</span>' +
      '<button type="button" class="fb-close" aria-label="Close">✕</button></div>' +
      '<button type="button" class="fb-mic" aria-pressed="false"></button>' +
      '<textarea class="fb-box" rows="4" placeholder="What would you change here?" aria-label="Your feedback"></textarea>' +
      '<div class="fb-hint" hidden></div>' +
      '<div class="fb-row"><button type="button" class="fb-send">Send</button></div>' +
      '<div class="fb-status" role="status" aria-live="polite"></div>' +
      '<div class="fb-row"><span class="fb-queue" hidden style="flex:1"></span><button type="button" class="fb-connect" hidden style="flex:0 0 auto">Connect</button></div>';
    D.body.appendChild(fab); D.body.appendChild(panel);
    box = panel.querySelector(".fb-box"); micBtn = panel.querySelector(".fb-mic"); sendBtn = panel.querySelector(".fb-send");
    hint = panel.querySelector(".fb-hint"); statusEl = panel.querySelector(".fb-status");
    queueEl = panel.querySelector(".fb-queue"); connectBtn = panel.querySelector(".fb-connect");
    box.value = store.get(DRAFT_KEY) || "";
    if (!SR) showHint();
    paintMic(); paintQueue();

    var restoreFab = makeDraggable(fab, POS_KEY), fabRect = null;
    function setBox(el, x, y) {
      el.style.setProperty("left", x + "px", "important"); el.style.setProperty("top", y + "px", "important");
      el.style.setProperty("right", "auto", "important"); el.style.setProperty("bottom", "auto", "important");
    }
    function clearBox(el) { ["left", "top", "right", "bottom"].forEach(function (k) { el.style.removeProperty(k); }); }
    function placePanel() {                                 // same rule as the Aa panel: next to the bubble, fully on screen
      if (panel.hidden || !fabRect) return;
      var vw = W.innerWidth, vh = W.innerHeight, w = panel.offsetWidth, h = panel.offsetHeight, m = 8;
      var x = fabRect.left;
      if (x + w > vw - m) x = fabRect.right - w;
      x = Math.max(m, Math.min(vw - w - m, x));
      var y = fabRect.bottom - h;
      if (y < m) y = fabRect.top;
      y = Math.max(m, Math.min(vh - h - m, y));
      setBox(panel, x, y);
    }
    /* by default, sit just above the Aa bubble (or the Read aloud one), never on top of either */
    function hits(a, list) {
      return list.some(function (b) { return a.left < b.right + 8 && a.right > b.left - 8 && a.top < b.bottom + 8 && a.bottom > b.top - 8; });
    }
    function avoid() {
      if (store.get(POS_KEY) || fab.hidden) return;
      var others = [".ts-fab", ".sa-fab"].map(function (s) { return D.querySelector(s); })
        .filter(function (el) { return el && !el.hidden && el.getClientRects().length; });
      var rects = others.map(function (el) { return el.getBoundingClientRect(); });
      var size = 44, vw = W.innerWidth, vh = W.innerHeight, spots = [];
      rects.slice().sort(function (a, b) { return a.top - b.top; }).forEach(function (r) {
        spots.push([r.left, r.top - size - 12], [r.left, r.bottom + 12]);
      });
      clearBox(fab);
      var d = fab.getBoundingClientRect();
      spots.unshift([d.left, d.top]);
      for (var i = 0; i < spots.length; i++) {
        var x = Math.max(4, Math.min(vw - size - 4, spots[i][0])), y = Math.max(4, Math.min(vh - size - 4, spots[i][1]));
        if (!hits({ left: x, top: y, right: x + size, bottom: y + size }, rects)) {
          if (i > 0) setBox(fab, x, y);
          return;
        }
      }
    }
    avoid(); setTimeout(avoid, 400); setTimeout(avoid, 1700);
    W.addEventListener("resize", function () { avoid(); placePanel(); });

    fab.addEventListener("click", function () {
      fabRect = fab.getBoundingClientRect();
      panel.hidden = false; fab.hidden = true;
      statusEl.textContent = lastNote && queue().length ? lastNote : "";
      paintQueue(); placePanel();
      if (!SR) try { box.focus({ preventScroll: true }); } catch (e) {}
      flush();
    });
    function close() { stopListening(); panel.hidden = true; fab.hidden = false; restoreFab(); avoid(); }
    panel.querySelector(".fb-close").addEventListener("click", close);
    D.addEventListener("keydown", function (e) { if (e.key === "Escape" && !panel.hidden) close(); });
    micBtn.addEventListener("click", function () { if (listening) stopListening(); else startListening(); });
    box.addEventListener("input", saveDraft);
    connectBtn.addEventListener("click", function () { connect().then(function () { paintQueue(); flush(); }); });
    sendBtn.addEventListener("click", function () {
      if (listening) stopListening();
      var text = box.value.trim();
      if (!text) { note("Say or type something first.", "bad"); try { box.focus(); } catch (e) {} return; }
      var item = {
        id: newId(), text: text.slice(0, 20000), app: appName(), url: location.href, title: D.title || "",
        when: new Date().toISOString(), device: device(), textSize: textSize()
      };
      var q = queue(); q.push(item);
      if (!store.json(QUEUE_KEY, q)) { note("This phone couldn't save it (storage is full or blocked). Copy the text before closing.", "bad"); return; }
      box.value = ""; store.del(DRAFT_KEY);
      note(pass() && navigator.onLine !== false ? "Sending…" : "Saved on this phone.", "wait");
      flush();
    });
  }

  W.addEventListener("online", flush);
  setInterval(flush, 60000);
  W.AppFeedback = { flush: flush, pending: function () { return queue().length; }, connect: connect };
  if (D.readyState === "loading") D.addEventListener("DOMContentLoaded", function () { build(); flush(); });
  else { build(); flush(); }
})();
