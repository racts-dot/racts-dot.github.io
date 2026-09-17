/* Priest Hood: bottom navigation bar and sideways swipe between sections (written by site_shell.py).
   Rachel, 17 Sep 2026: "I'd like the bottom thing to be able to navigate the sections that I need to navigate".
   The sections come from the page itself (D.sections), in the order the home screen lists them. */
(function () {
  "use strict";
  if (typeof D === "undefined" || !D.sections || document.querySelector("nav.ph-bar")) return;
  var SHORT = { names: "Names", angels: "Angels", demons: "Demons", elements: "Elements", ordinances: "Ordinances" };
  var TABS = [{ id: "", label: "Home" }].concat(D.sections.map(function (s) {
    return { id: s.id, label: SHORT[s.id] || s.title.split(" ")[0], title: s.title };
  }));

  var css = document.createElement("style");
  css.textContent =
    "body{padding-bottom:calc(4.25rem + env(safe-area-inset-bottom))}" +
    "nav.ph-bar{position:fixed;left:0;right:0;bottom:0;z-index:40;background:var(--panel);border-top:1px solid var(--line);" +
    "padding:0 .25rem env(safe-area-inset-bottom);display:flex;overflow-x:auto;scrollbar-width:none;" +
    "box-shadow:0 -2px 10px rgba(0,0,0,.06)}" +
    "nav.ph-bar::-webkit-scrollbar{display:none}" +
    "nav.ph-bar a{flex:1 0 auto;min-width:3.5rem;min-height:3.5rem;display:flex;align-items:center;justify-content:center;" +
    "padding:.25rem .375rem;font-size:.75rem;font-weight:600;color:var(--soft);text-decoration:none;white-space:nowrap;" +
    "border-top:3px solid transparent;-webkit-tap-highlight-color:transparent}" +
    "nav.ph-bar a[aria-current=page]{color:var(--accent);border-top-color:var(--accent)}" +
    "nav.ph-bar a:focus-visible{outline-offset:-3px}";
  document.head.appendChild(css);

  var nav = document.createElement("nav");
  nav.className = "ph-bar";
  nav.setAttribute("aria-label", "Sections");
  TABS.forEach(function (t) {
    var a = document.createElement("a");
    a.href = "#" + t.id;
    a.textContent = t.label;
    if (t.title) a.title = t.title;
    a.addEventListener("click", function () { setTimeout(function () { window.scrollTo(0, 0); }, 0); });
    nav.appendChild(a);
  });
  document.body.appendChild(nav);

  function current() {
    var id = decodeURIComponent(location.hash.replace(/^#/, ""));
    for (var i = 1; i < TABS.length; i++) if (TABS[i].id === id) return i;
    return 0;
  }
  function mark() {
    var k = current(), links = nav.querySelectorAll("a");
    for (var i = 0; i < links.length; i++) {
      if (i === k) links[i].setAttribute("aria-current", "page"); else links[i].removeAttribute("aria-current");
    }
    var on = links[k];
    if (on && nav.scrollWidth > nav.clientWidth) on.scrollIntoView({ block: "nearest", inline: "center" });
  }
  function go(step) {
    var k = current() + step;
    if (k < 0 || k >= TABS.length) return;
    location.hash = TABS[k].id;
    window.scrollTo(0, 0);
  }
  window.addEventListener("hashchange", mark);
  mark();

  // A sideways swipe moves to the next or previous section, in the order of the bar.
  // Not while a card is open, not from the phone's own edge-swipe zone, not while selecting words,
  // not on a text box, the bar or the bubbles, and not on something that scrolls sideways itself.
  // A swipe that starts on an entry still counts: the entries are most of each section screen.
  function scrollsSideways(node) {
    for (; node && node !== document.body; node = node.parentElement) {
      var ox = getComputedStyle(node).overflowX;
      if ((ox === "auto" || ox === "scroll") && node.scrollWidth > node.clientWidth + 2) return true;
    }
    return false;
  }
  var sx = 0, sy = 0, st = 0, armed = false;
  document.addEventListener("touchstart", function (e) {
    armed = false;
    if (e.touches.length !== 1) return;
    if (window.visualViewport && window.visualViewport.scale > 1.01) return;   // pinch-zoomed: a pan, not a swipe
    var t = e.touches[0], tg = e.target;
    if (document.querySelector("dialog[open]")) return;
    if (t.clientX < 28 || t.clientX > window.innerWidth - 28) return;
    if (tg.closest && tg.closest("input,textarea,select,nav.ph-bar,.ts-fab,.fb-fab,.sa-fab,.ts-panel,.fb-panel,.sa-panel")) return;
    if (scrollsSideways(tg)) return;
    sx = t.clientX; sy = t.clientY; st = Date.now(); armed = true;
  }, { passive: true });
  document.addEventListener("touchend", function (e) {
    if (!armed) return;
    armed = false;
    if (window.visualViewport && window.visualViewport.scale > 1.01) return;
    var t = e.changedTouches[0], dx = t.clientX - sx, dy = t.clientY - sy;
    if (Date.now() - st > 800 || Math.abs(dx) < 70 || Math.abs(dy) > Math.abs(dx) * 0.5) return;
    var sel = window.getSelection && window.getSelection();
    if (sel && !sel.isCollapsed) return;
    go(dx < 0 ? 1 : -1);
  }, { passive: true });
})();
/* Priest Hood: read any cited verse in the New Living Translation (written by site_shell.py).

   Rachel, 16 Sep 2026, on the Ordinances page: "And do the NLT."

   The NLT is Tyndale's, not public domain, so its words are never built into this app and never stored in git.
   The published copy asks api.nlt.to for the one verse being read, exactly as Daily Chapter already does, and
   shows Tyndale's copyright line with it. The single-file build stays as it was: World English Bible and King
   James Version only, and no network request of any kind (check_app.py still proves that).

   With no signal, or if the service does not answer, the verse stays in the translation underneath and says why.
*/
(function () {
  "use strict";
  var W = window, D_ = document;
  if (W.__phNlt) return;
  W.__phNlt = 1;

  var ON_KEY = "priesthood.nlt", CACHE_KEY = "priesthood.nltText";
  var COPYRIGHT = "Holy Bible, New Living Translation, copyright \u00a9 1996, 2004, 2015 by Tyndale House " +
                  "Foundation. Used by permission of Tyndale House Publishers, Carol Stream, Illinois 60188. " +
                  "All rights reserved.";
  /* the service names one book differently from the app */
  var BOOK_NAMES = { "Song of Solomon": "Song of Songs" };

  function readOn() { try { return localStorage.getItem(ON_KEY) === "1"; } catch (e) { return false; } }
  function writeOn(v) { try { localStorage.setItem(ON_KEY, v ? "1" : "0"); } catch (e) {} }
  var on = readOn();

  var mem = {};
  try { mem = JSON.parse(localStorage.getItem(CACHE_KEY) || "{}") || {}; } catch (e) { mem = {}; }
  function remember(ref, parts) {
    mem[ref] = parts;
    try { localStorage.setItem(CACHE_KEY, JSON.stringify(mem)); } catch (e) {}   /* full or blocked: memory only */
  }

  /* "1 Samuel 14:3" -> "1 Samuel.14.3" ; "Genesis 1:1-3" -> "Genesis.1.1-3" */
  function apiRef(ref) {
    var m = /^(.*?)\s+(\d+):(\d+(?:-\d+)?)$/.exec(ref.trim());
    if (!m) return null;
    return (BOOK_NAMES[m[1]] || m[1]) + "." + m[2] + "." + m[3];
  }

  /* Take the verse words out of the service's HTML: verse numbers kept, headings and footnotes dropped. */
  function parseVerses(html) {
    var doc = new DOMParser().parseFromString(html, "text/html");
    var body = doc.querySelector("#bibletext");
    if (!body) return null;
    Array.prototype.forEach.call(body.querySelectorAll("h2, h3, .tn, .a-tn, .bk_ch_vs_header, .chapter-number, .subhead"),
      function (n) { n.parentNode.removeChild(n); });
    var out = [], numbers = body.querySelectorAll(".vn");
    if (!numbers.length) {
      var only = body.textContent.replace(/\s+/g, " ").trim();
      return only ? [[0, only]] : null;
    }
    Array.prototype.forEach.call(numbers, function (vn) {
      var n = parseInt(vn.textContent, 10);
      var words = "", node = vn;
      /* everything after this verse number until the next one */
      while ((node = nextNode(node, body))) {
        if (node.nodeType === 1 && node.classList && node.classList.contains("vn")) break;
        if (node.nodeType === 3) words += node.nodeValue;
      }
      words = words.replace(/\s+/g, " ").trim();
      if (words) out.push([isNaN(n) ? 0 : n, words]);
    });
    return out.length ? out : null;
  }
  function nextNode(node, root) {
    if (node.firstChild && !(node.classList && node.classList.contains("vn"))) return node.firstChild;
    while (node && node !== root) {
      if (node.nextSibling) return node.nextSibling;
      node = node.parentNode;
    }
    return null;
  }

  var inflight = {};
  function load(ref) {
    if (mem[ref]) return Promise.resolve(mem[ref]);
    if (inflight[ref]) return inflight[ref];
    var r = apiRef(ref);
    if (!r) return Promise.reject(new Error("reference not understood"));
    var url = "https://api.nlt.to/api/passages?ref=" + encodeURIComponent(r) + "&version=NLT&key=TEST";
    inflight[ref] = fetch(url).then(function (res) {
      if (!res.ok) throw new Error("HTTP " + res.status);
      return res.text();
    }).then(function (text) {
      var parts = parseVerses(text);
      if (!parts) throw new Error("no verse came back");
      remember(ref, parts);
      delete inflight[ref];
      return parts;
    }).catch(function (err) { delete inflight[ref]; throw err; });
    return inflight[ref];
  }

  /* ---------------------------------------------------------------- the card
     Everything below writes into the card, and the card is watched for the app rebuilding it, so every write
     goes through quiet(): the watcher is off while we write, or it would call us back on our own changes. */
  var obs = null, cardEl = null;
  function watch() { if (obs && cardEl) obs.observe(cardEl, { childList: true, subtree: true }); }
  function quiet(fn) {
    if (obs) { obs.disconnect(); }
    try { fn(); } finally { if (obs) { obs.takeRecords(); } watch(); }
  }

  function refOf(q) {
    var cite = q.querySelector("cite");
    if (!cite) return null;
    return cite.textContent.split("\u00b7")[0].trim();
  }
  function keep(q) {
    if (!q.__phKept) q.__phKept = q.innerHTML;     /* the built-in WEB/KJV text, to put back */
    return q.__phKept;
  }
  function restore(q) {
    if (q.__phKept) { q.innerHTML = q.__phKept; q.__phNlt = 0; }
  }
  function note(q, words) {
    var p = D_.createElement("p");
    p.className = "note";
    p.style.cssText = "margin:.25rem 0 0;font-size:.8125rem;opacity:.8";
    p.textContent = words;
    q.appendChild(p);
  }
  function show(q, ref, parts) {
    keep(q);
    q.innerHTML = "";
    var p = D_.createElement("p");
    parts.forEach(function (pair, i) {
      if (parts.length > 1 && pair[0]) {
        var s = D_.createElement("sup");
        s.textContent = String(pair[0]);
        p.appendChild(s);
      }
      p.appendChild(D_.createTextNode(pair[1] + (i < parts.length - 1 ? " " : "")));
    });
    q.appendChild(p);
    var cite = D_.createElement("cite");
    cite.textContent = ref + " \u00b7 New Living Translation";
    q.appendChild(cite);
    note(q, COPYRIGHT);
    q.__phNlt = 1;
  }

  function fill(q) {
    if (!on || q.hidden || q.__phNlt || q.__phBusy) return;
    var ref = refOf(q);
    if (!ref) return;
    keep(q);
    if (mem[ref]) { show(q, ref, mem[ref]); return; }
    var waiting = q.querySelector("cite");
    if (waiting) waiting.textContent = ref + " \u00b7 asking for the New Living Translation\u2026";
    q.__phBusy = 1;
    load(ref).then(function (parts) {
      q.__phBusy = 0;
      quiet(function () { if (on) show(q, ref, parts); else restore(q); });
    }).catch(function () {
      q.__phBusy = 0;
      quiet(function () {
        restore(q);
        note(q, navigator.onLine === false
          ? "The New Living Translation needs a signal. Showing the translation above instead."
          : "The New Living Translation did not answer. Showing the translation above instead.");
      });
    });
  }
  function sweep() {
    Array.prototype.forEach.call(D_.querySelectorAll("#card blockquote"), function (q) {
      if (on) fill(q); else restore(q);
    });
  }

  /* The card is rebuilt by the app whenever WEB or KJV is pressed, so the button is added by watching for it. */
  function addButton(seg) {
    if (seg.querySelector("button[data-ph-nlt]")) return;
    var b = D_.createElement("button");
    b.type = "button";
    b.textContent = "NLT";
    b.setAttribute("data-ph-nlt", "1");
    b.setAttribute("aria-label", "New Living Translation");
    b.setAttribute("aria-pressed", String(on));
    b.addEventListener("click", function () {
      on = !on;
      writeOn(on);
      quiet(function () { markButtons(); sweep(); });
    });
    seg.appendChild(b);
    markButtons();
  }
  function markButtons() {
    Array.prototype.forEach.call(D_.querySelectorAll('#card div.seg[aria-label="Verse text translation"] button'), function (b) {
      if (b.hasAttribute("data-ph-nlt")) b.setAttribute("aria-pressed", String(on));
      else if (on) b.setAttribute("aria-pressed", "false");
    });
  }

  /* Capture, not bubble: pressing WEB or KJV makes the app rebuild the whole card, so by the time a
     bubbling listener ran the button it was told about would already be off the page. */
  D_.addEventListener("click", function (e) {
    var t = e.target;
    if (!t || !t.closest) return;
    var seg = t.closest('#card div.seg[aria-label="Verse text translation"] button');
    if (seg && !seg.hasAttribute("data-ph-nlt") && on) { on = false; writeOn(false); setTimeout(function () { quiet(markButtons); }, 0); }
    if (t.closest("#card button.ref")) setTimeout(function () { quiet(sweep); }, 0);
  }, true);

  cardEl = D_.getElementById("card");
  if (!cardEl) return;
  obs = new MutationObserver(function () {
    quiet(function () {
      var seg = cardEl.querySelector('div.seg[aria-label="Verse text translation"]');
      if (seg) addButton(seg);
      sweep();
    });
  });
  watch();
})();
