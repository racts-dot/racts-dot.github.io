/* notion-sync.js — shared by Rachel's apps on racts-dot.github.io.
 *
 * Each app keeps saving the way it always has. This adds a copy to Notion:
 *   NotionSync.save("desk", id, { title, detail, when, data })
 *   NotionSync.remove("desk", id)       // ticks Deleted in Notion, never erases
 *
 * No Notion key is in this file. Writes go to apps-notion-relay (Cloudflare),
 * which holds the key and only touches the app databases it was given.
 * The relay password is asked for once per device and kept in this browser.
 *
 * Offline or relay down: writes wait in a queue (localStorage) and are sent
 * on the next page load or when the connection comes back. Several edits to
 * the same record collapse into the latest one.
 *
 * 14 Sep 2026, after an independent check ran this file against a fake browser:
 *  - "already in Notion" is remembered as a short fingerprint, not a second copy
 *    of every record, so the apps' own storage allowance is not eaten;
 *  - a record's fingerprint is forgotten the moment a newer version is queued,
 *    so undoing an edit while it is still being sent is no longer lost;
 *  - every record ever queued is remembered, so deleting it mid-send still
 *    ticks Deleted in Notion;
 *  - a record that keeps failing moves to the back of the queue, so it never
 *    blocks the rest, and it is kept (the pill says so after 8 tries);
 *  - a send gives up after 20 s, so a hung request cannot freeze a tab;
 *  - two open tabs no longer send the same queue at once.
 */
(function () {
  "use strict";
  if (window.NotionSync) return;
  // 16 Sep 2026: pages that only read (recipes) load this with data-quiet: no password sheet pops up on its own,
  // only the Connect chip, so opening a recipe never covers the page.
  var QUIET = !!(document.currentScript && document.currentScript.hasAttribute("data-quiet"));

  var RELAY = "https://apps-notion-relay.apps-notion-relay.workers.dev";
  var PASS_KEY = "notionSync.pass";
  var QUEUE_KEY = "notionSync.queue";
  var SENT_KEY = "notionSync.sent2";   // key -> fingerprint of the version Notion has
  var KNOWN_KEY = "notionSync.known";  // key -> 1 for every record ever queued to save
  var LOCK_KEY = "notionSync.lock";
  var MAX_TRIES = 8; // after this many failures the pill says so; the entry is still kept
  var TAB = Math.random().toString(36).slice(2);
  var flushing = false;
  var asking = null;
  var declined = QUIET; // "Later" was tapped (or a quiet page): stop asking until the page is opened again

  try { localStorage.removeItem("notionSync.sent"); } catch (e) {} // old full-copy store

  function store(key, value) {
    try {
      if (value === undefined) return JSON.parse(localStorage.getItem(key) || "null");
      if (value === null) localStorage.removeItem(key);
      else localStorage.setItem(key, JSON.stringify(value));
    } catch (e) { return null; }
  }

  // 53-bit string fingerprint (cyrb53). Collisions are astronomically unlikely for this use.
  function fingerprint(str) {
    var h1 = 0xdeadbeef, h2 = 0x41c6ce57;
    for (var i = 0; i < str.length; i++) {
      var ch = str.charCodeAt(i);
      h1 = Math.imul(h1 ^ ch, 2654435761);
      h2 = Math.imul(h2 ^ ch, 1597334677);
    }
    h1 = Math.imul(h1 ^ (h1 >>> 16), 2246822507) ^ Math.imul(h2 ^ (h2 >>> 13), 3266489909);
    h2 = Math.imul(h2 ^ (h2 >>> 16), 2246822507) ^ Math.imul(h1 ^ (h1 >>> 13), 3266489909);
    return (4294967296 * (2097151 & h2) + (h1 >>> 0)).toString(36);
  }

  function keyOf(app, id) { return app + "|" + id; }
  function queue() { return store(QUEUE_KEY) || []; }
  function sentMap() { return store(SENT_KEY) || {}; }
  function knownMap() { return store(KNOWN_KEY) || {}; }
  function setIn(mapKey, k, v) {
    var m = store(mapKey) || {};
    if (v == null) delete m[k]; else m[k] = v;
    store(mapKey, m);
  }

  function enqueue(path, body, hash) {
    var k = keyOf(body.app, body.id);
    var q = queue().filter(function (item) { return keyOf(item.body.app, item.body.id) !== k; });
    q.push({ path: path, body: body, t: Date.now() + Math.random(), hash: hash || null, tries: 0 });
    store(QUEUE_KEY, q);
    // Until Notion confirms this version, we no longer know what it holds for this record.
    setIn(SENT_KEY, k, null);
    if (path === "/save") setIn(KNOWN_KEY, k, 1);
    flush();
  }

  /* ---------- small status pill ---------- */
  var pill, pillTimer;
  function status(text, tone, stay) {
    if (!document.body) return;
    if (!pill) {
      pill = document.createElement("div");
      pill.setAttribute("role", "status");
      pill.style.cssText =
        "position:fixed;left:12px;bottom:12px;z-index:2147483646;" +
        "font:500 12px/1 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;" +
        "padding:7px 10px;border-radius:999px;box-shadow:0 2px 10px rgba(0,0,0,.15);" +
        "transition:opacity .3s;opacity:0;pointer-events:none";
      document.body.appendChild(pill);
    }
    var tones = {
      ok: ["#e8f5ee", "#1d6b43"],
      wait: ["#fff6e0", "#7a5200"],
      bad: ["#fdecec", "#9b1c1c"],
    }[tone || "ok"];
    pill.style.background = tones[0];
    pill.style.color = tones[1];
    pill.textContent = text;
    pill.style.opacity = "1";
    clearTimeout(pillTimer);
    if (!stay) pillTimer = setTimeout(function () { pill.style.opacity = "0"; }, 2200);
  }

  /* ---------- one-time password sheet ---------- */
  function askPassword(message) {
    if (asking) return asking;
    asking = new Promise(function (resolve) {
      var wrap = document.createElement("div");
      wrap.style.cssText =
        "position:fixed;inset:0;z-index:2147483647;background:rgba(20,20,25,.45);" +
        "display:flex;align-items:flex-end;justify-content:center;" +
        "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif";
      wrap.innerHTML =
        '<form style="background:#fff;color:#1c1c1e;width:100%;max-width:420px;' +
        'border-radius:18px 18px 0 0;padding:22px 20px calc(20px + env(safe-area-inset-bottom));' +
        'box-shadow:0 -6px 30px rgba(0,0,0,.2)">' +
        '<div style="font-size:17px;font-weight:600;margin-bottom:6px">Connect to Notion</div>' +
        '<div class="ns-msg" style="font-size:14px;color:#555;margin-bottom:14px;line-height:1.4"></div>' +
        '<input type="password" autocomplete="current-password" placeholder="Apps password" ' +
        'style="width:100%;box-sizing:border-box;font-size:16px;padding:12px 14px;border:1px solid #d1d1d6;' +
        'color:#1c1c1e;background:#fff;font-family:inherit;' +
        'border-radius:12px;margin-bottom:12px">' +
        '<div style="display:flex;gap:10px">' +
        '<button type="button" class="ns-later" style="flex:1;padding:12px;border-radius:12px;border:0;' +
        'background:#f2f2f7;color:#1c1c1e;font-size:15px;font-weight:500;font-family:inherit">Later</button>' +
        '<button type="submit" style="flex:2;padding:12px;border-radius:12px;border:0;' +
        'background:#1c1c1e;color:#fff;font-size:15px;font-weight:600;font-family:inherit">Connect</button></div></form>';
      wrap.querySelector(".ns-msg").textContent =
        message || "Enter the apps password once on this device. Your entries will also be saved to Notion.";
      document.body.appendChild(wrap);
      var input = wrap.querySelector("input");
      setTimeout(function () { input.focus(); }, 50);
      function done(value) {
        wrap.remove();
        asking = null;
        resolve(value);
      }
      wrap.querySelector(".ns-later").onclick = function () { declined = true; done(null); };
      wrap.querySelector("form").onsubmit = function (e) {
        e.preventDefault();
        var v = input.value.trim();
        if (v) { store(PASS_KEY, v); done(v); }
      };
    });
    return asking;
  }

  // Resolves to {status, ok, out}. The 20 s limit covers the whole reply, body included,
  // so neither a hung request nor a hung body can freeze a tab's sync.
  function send(path, body, pass) {
    var ctrl = typeof AbortController === "function" ? new AbortController() : null;
    var timer = ctrl ? setTimeout(function () { ctrl.abort(); }, 20000) : null;
    return fetch(RELAY + path, {
      method: body ? "POST" : "GET",
      headers: { "Content-Type": "application/json", "X-Pass": pass },
      body: body ? JSON.stringify(body) : undefined,
      signal: ctrl ? ctrl.signal : undefined,
    }).then(function (r) {
      return r.json().catch(function (e) {
        if (ctrl && ctrl.signal.aborted) throw e; // timed out mid-body: a network failure
        return {};
      }).then(function (out) {
        clearTimeout(timer);
        return { status: r.status, ok: r.ok, out: out || {} };
      });
    }).catch(function (e) { clearTimeout(timer); throw e; });
  }

  // One tab sends at a time. A lock older than 90 s belongs to a closed or frozen tab.
  // 90 s, not 30: a background tab's timers can be slowed to once a minute, and the lock
  // must outlast any send that tab has started.
  function takeLock() {
    var l = store(LOCK_KEY);
    if (l && l.tab !== TAB && Date.now() - l.at < 90000) return false;
    store(LOCK_KEY, { tab: TAB, at: Date.now() });
    var mine = store(LOCK_KEY);
    return !!(mine && mine.tab === TAB); // another tab wrote at the same moment: let it go first
  }
  function dropLock() {
    var l = store(LOCK_KEY);
    if (l && l.tab === TAB) store(LOCK_KEY, null);
  }

  function removeItem(item) {
    store(QUEUE_KEY, queue().filter(function (x) { return x.t !== item.t; }));
  }

  function retryLater(item) {
    var q = queue(), found = false;
    q = q.filter(function (x) {
      if (x.t !== item.t) return true;
      found = true;
      return false;
    });
    if (found) {
      item.tries = (item.tries || 0) + 1;
      q.push(item); // to the back, so one failing record never blocks the rest
      store(QUEUE_KEY, q);
    }
    showWaiting();
  }

  // Never thrown away: her entry waits. Once any entry has failed MAX_TRIES times, the pill
  // says so and stays up - no later "waiting" message may cover it.
  function showWaiting() {
    var q = queue();
    var stuck = q.filter(function (x) { return (x.tries || 0) >= MAX_TRIES; }).length;
    if (stuck) status(stuck + (stuck === 1 ? " entry has" : " entries have") + " not reached Notion after " + MAX_TRIES + " tries - kept, still retrying", "bad", true);
    else if (q.length) status("Notion · " + q.length + " waiting, will retry", "wait");
  }

  function flush() {
    if (flushing) return;
    var q = queue();
    if (!q.length) return;
    var pass = store(PASS_KEY);
    if (!pass) {
      if (!document.body) return;
      status("Notion · " + q.length + " waiting", "wait", true);
      /* 20 Sep 2026. Her word, on opening her own rule book and being asked for a
         password: "Nooooooo". This used to raise the modal OVER whatever page she
         had just opened, on all twelve apps that load this file. It never asks by
         itself now: it shows the Connect chip and waits to be tapped. The modal is
         raised only by NotionSync.connect(), which is her own tap. */
      paintConnect();
      return;
    }
    if (navigator.onLine === false) {
      var stuckNow = q.some(function (x) { return (x.tries || 0) >= MAX_TRIES; });
      if (stuckNow) showWaiting(); // never cover the "not reached Notion" warning
      else status("Notion · " + q.length + " waiting for connection", "wait");
      return;
    }
    if (!takeLock()) return;
    flushing = true;
    var item = q[0];
    var done = false;
    var finish = function () { if (!done) { done = true; flushing = false; dropLock(); } };
    send(item.path, item.body, pass)
      .then(function (r) {
        var out = r.out;
        if (r.status === 401) {
          store(PASS_KEY, null);
          finish();
          /* Same rule on a rejected password: say so in the status line and put the
             chip back. Re-opening the box over her page was the other half of the
             fault - a wrong password used to mean a modal on every load after it. */
          status("Notion · password needed - tap Connect", "wait", true);
          paintConnect();
          return;
        }
        var k = keyOf(item.body.app, item.body.id);
        if (r.ok && out.ok) {
          var stillQueued = queue().some(function (x) { return x.t === item.t; });
          var newer = queue().some(function (x) { return x.t !== item.t && keyOf(x.body.app, x.body.id) === k; });
          removeItem(item);
          if (!newer && stillQueued) {
            if (item.path === "/save") setIn(SENT_KEY, k, item.hash);
            else { setIn(SENT_KEY, k, null); setIn(KNOWN_KEY, k, null); }
          }
          finish();
          if (queue().length) flush();
          else status("Saved to Notion ✓", "ok");
        } else if (r.status >= 400 && r.status < 500 && r.status !== 429 && out.ok === false && out.error) {
          // The relay itself says this request can never be accepted (unknown app, no id, too
          // large). A 4xx page that is not the relay's own reply is retried, never dropped.
          removeItem(item);
          finish();
          status("Notion refused one entry: " + out.error, "bad");
          setTimeout(showWaiting, 2600); // then bring back any "not reached Notion" warning
          flush();
        } else {
          retryLater(item);
          finish();
        }
      })
      .catch(function () {
        if (done) return; // an error after the reply was handled: nothing to retry
        retryLater(item); // network error or time-out: to the back, so the rest still go
        finish();
      });
  }

  function body(app, id, rec) {
    rec = rec || {};
    return {
      app: app,
      id: String(id),
      title: rec.title == null ? "" : String(rec.title),
      detail: rec.detail == null ? "" : String(rec.detail),
      when: rec.when || null,
      data: rec.data === undefined ? null : rec.data,
    };
  }

  window.NotionSync = {
    // Sends only if this exact version has not already reached Notion from this device.
    save: function (app, id, rec) {
      var b = body(app, id, rec), hash = fingerprint(JSON.stringify(b)), k = keyOf(app, b.id);
      var q = queue();
      var waiting = q.some(function (x) { return keyOf(x.body.app, x.body.id) === k && x.hash === hash; });
      if (waiting) return false;
      var inQueue = q.some(function (x) { return keyOf(x.body.app, x.body.id) === k; });
      if (!inQueue && sentMap()[k] === hash) return false;
      enqueue("/save", b, hash);
      return true;
    },
    remove: function (app, id) {
      var k = keyOf(app, String(id));
      if (!knownMap()[k]) return; // never queued from this device: nothing in Notion to tick
      enqueue("/delete", { app: app, id: String(id) });
    },
    // Records this device has put in Notion for one app - lets an app notice ones that vanished.
    knownIds: function (app) {
      return Object.keys(knownMap()).filter(function (k) { return k.indexOf(app + "|") === 0; })
        .map(function (k) { return k.slice(app.length + 1); });
    },
    list: function (app) {
      var pass = store(PASS_KEY);
      if (!pass) return Promise.reject(new Error("no password yet"));
      return send("/list?app=" + encodeURIComponent(app), null, pass).then(function (r) { return r.out; });
    },
    pending: function () { return queue().length; },
    // 16 Sep 2026: a direct call that is not a Notion copy (the recipe coach). Asks for the password once if needed.
    post: function (path, payload) {
      var pass = store(PASS_KEY);
      var go = function (p) {
        if (!p) return Promise.reject(new Error("no password"));
        return send(path, payload, p).then(function (r) {
          if (r.status === 401) { store(PASS_KEY, null); paintConnect(); }
          return r;
        });
      };
      return pass ? go(pass) : askPassword().then(go);
    },
    flush: flush,
    connected: function () { return !!store(PASS_KEY); },
    // 15 Sep 2026: a button she can always press, instead of waiting for the sheet to appear.
    connect: function () {
      declined = false;
      return askPassword().then(function (p) {
        if (p) { status("Notion · connected", "ok"); paintConnect(); flush(); }
        return !!p;
      });
    },
  };

  /* ---------- the Connect to Notion chip (15 Sep 2026) ----------
     Her words: "where is the connect button?" The sheet used to appear only when something was
     waiting to send, and "Later" hid it until the page was reopened. The chip stays until the
     password is in, on every app that loads this file. */
  var chip = null;
  function paintConnect() {
    if (!document.body) return;
    var need = !store(PASS_KEY);
    if (!need) { if (chip) { chip.remove(); chip = null; } return; }
    if (chip) return;
    chip = document.createElement("button");
    chip.type = "button";
    chip.textContent = "Connect to Notion";
    chip.setAttribute("aria-label", "Connect this app to Notion");
    chip.style.cssText =
      "position:fixed;right:12px;bottom:calc(84px + env(safe-area-inset-bottom));z-index:2147483645;" +
      "font:600 13px/1 -apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;" +
      "padding:10px 14px;border-radius:999px;border:0;background:#1c1c1e;color:#fff;" +
      "box-shadow:0 4px 16px rgba(0,0,0,.25);cursor:pointer";
    chip.onclick = function () { window.NotionSync.connect(); };
    document.body.appendChild(chip);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", paintConnect);
  else paintConnect();

  window.addEventListener("online", flush);
  window.addEventListener("pagehide", dropLock);
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", flush);
  else flush();
  setInterval(flush, 60000);
})();
