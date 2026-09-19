/* Highlights and notes - the shared one for every app on this site.
   Her words 19 Sep 2026 (Rule Shelf): "Just like the creators reading - make highlights and notes for you to
   know which needs to be ammeded", and "The edit. It will be done by you. I am just to comment." So she MARKS;
   a session reads the marks and makes the edit. Nothing here changes the rule text.
   Behaviour copied from the Creator Reading Room's own bar (#hlpop): select words -> a draggable bar with
   Highlight and Note; tap an existing highlight -> Note and Delete.
   Marks are saved on the device first, then sent to the Notion "App feedback" database through notion-sync.js,
   so they reach whoever does the editing even if she never mentions them in a chat. */
(function () {
  "use strict";
  if (window.__appMarks) return;
  window.__appMarks = true;

  var APP = "feedback";                                   // the only database that exists for "tell the editor"
  var PAGE = location.pathname.replace(/\/$/, "") || "/";
  var KEY = "marks:" + PAGE;
  var ROOT_SEL = "main,article,#view,body";

  var css = document.createElement("style");
  css.textContent =
    "mark.am{background:#fff3a3;color:inherit;border-radius:.15em;padding:0 .05em;cursor:pointer}" +
    "@media (prefers-color-scheme:dark){mark.am{background:#6b5d16;color:#fff}}" +
    "mark.am.noted{box-shadow:inset 0 -.28em 0 rgba(255,150,0,.45)}" +
    ".am-bar{position:fixed;z-index:2147483000;display:flex;align-items:center;gap:.25rem;padding:.3rem;" +
    "border-radius:.7rem;background:#fff;color:#15181e;border:1px solid rgba(0,0,0,.18);" +
    "box-shadow:0 6px 20px rgba(0,0,0,.22);font:600 .9rem/1 -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif}" +
    "@media (prefers-color-scheme:dark){.am-bar{background:#22242a;color:#f2f4f8;border-color:rgba(255,255,255,.22)}}" +
    ".am-bar button{font:inherit;padding:.5rem .7rem;border:0;border-radius:.5rem;background:transparent;color:inherit;cursor:pointer;min-height:44px}" +
    ".am-bar button:active{background:rgba(127,127,127,.25)}" +
    ".am-grip{width:1.1rem;height:2.2rem;cursor:grab;touch-action:none;display:flex;align-items:center;justify-content:center;opacity:.5}" +
    ".am-grip::before{content:'';width:.25rem;height:1.2rem;border-radius:.2rem;background:currentColor}" +
    ".am-note{position:fixed;inset:auto .6rem 1rem .6rem;z-index:2147483001;max-width:34rem;margin:0 auto;padding:.8rem;" +
    "border-radius:.9rem;background:#fff;color:#15181e;border:1px solid rgba(0,0,0,.18);box-shadow:0 10px 30px rgba(0,0,0,.3)}" +
    "@media (prefers-color-scheme:dark){.am-note{background:#22242a;color:#f2f4f8}}" +
    ".am-note textarea{width:100%;box-sizing:border-box;min-height:5.5rem;font:400 1rem/1.4 inherit;padding:.5rem;" +
    "border-radius:.5rem;border:1px solid rgba(127,127,127,.5);background:transparent;color:inherit}" +
    ".am-note .row{display:flex;gap:.5rem;justify-content:flex-end;margin-top:.5rem}" +
    ".am-note button{font:600 .95rem/1 inherit;padding:.6rem .9rem;border-radius:.5rem;border:1px solid rgba(127,127,127,.45);" +
    "background:transparent;color:inherit;min-height:44px;cursor:pointer}" +
    ".am-note button.go{background:#2b6cb0;border-color:#2b6cb0;color:#fff}" +
    /* Her three asks, 20 Sep 2026: the note must move, the delete must not be missed,
       and the bar must retract so it stops eating the page. */
    ".am-bar button.del{color:#c0392b}" +
    "@media (prefers-color-scheme:dark){.am-bar button.del{color:#ff8a7a}}" +
    ".am-bar .sep{width:1px;align-self:stretch;margin:.35rem .15rem;background:rgba(127,127,127,.35)}" +
    ".am-bar .fold{padding:.5rem .55rem;opacity:.6;min-height:44px}" +
    ".am-bar.shut .fold{opacity:.9}" +
    ".am-bar.shut button:not(.fold){display:none}" +
    ".am-bar.shut .sep{display:none}" +
    ".am-note{touch-action:none}" +
    ".am-note .nhead{display:flex;align-items:center;gap:.5rem;margin:-.2rem 0 .5rem;cursor:grab;opacity:.75}" +
    ".am-note .nhead::before{content:'';width:2.2rem;height:.25rem;border-radius:.2rem;background:currentColor}" +
    ".am-note .nhead span{font:600 .8rem/1 inherit}" +
    ".am-note textarea{touch-action:auto}" +
    ".am-said{position:fixed;left:50%;bottom:1.2rem;transform:translateX(-50%);z-index:2147483002;padding:.55rem .9rem;" +
    "border-radius:999rem;background:rgba(20,20,22,.92);color:#fff;font:600 .85rem/1 sans-serif;pointer-events:none}";
  document.head.appendChild(css);

  function store() { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (e) { return []; } }
  function keep(list) { try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) {} }
  function said(t) {
    var d = document.createElement("div"); d.className = "am-said"; d.textContent = t;
    document.body.appendChild(d); setTimeout(function () { d.remove(); }, 1800);
  }

  // Send it where the person doing the edit will see it. Local storage is the copy that always works;
  // Notion is how it leaves her phone. notion-sync.js queues it by itself if she is offline.
  function send(m) {
    if (!window.NotionSync || !NotionSync.save) return;
    try {
      NotionSync.save(APP, "mark-" + m.id, {
        title: (m.text || "").slice(0, 80) || "(highlight)",
        detail: (m.note ? "NOTE: " + m.note + "\n\n" : "") + "HIGHLIGHTED: " + (m.text || "") + "\non " + PAGE,
        when: new Date(m.at).toISOString().slice(0, 10),
        data: { kind: "mark", page: PAGE, text: m.text, note: m.note || "", at: m.at }
      });
    } catch (e) {}
  }
  function unsend(id) { try { if (window.NotionSync && NotionSync.remove) NotionSync.remove(APP, "mark-" + id); } catch (e) {} }

  /* --- painting a saved mark back onto the page -------------------------------------------------
     Marks are stored by their exact words plus which occurrence, not by a DOM path: the Rule Shelf
     redraws itself, and a path would point at nothing after that. */
  function walker() {
    var root = document.querySelector(ROOT_SEL) || document.body;
    return document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode: function (n) {
        if (!n.nodeValue) return NodeFilter.FILTER_REJECT;
        var pe = n.parentElement;
        if (!pe || pe.closest("script,style,textarea,input,.am-bar,.am-note")) return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
  }

  function wrap(node, at, text, m) {
    try {
      var r = document.createRange();
      r.setStart(node, at); r.setEnd(node, at + text.length);
      var el = document.createElement("mark");
      el.className = "am" + (m.note ? " noted" : "");
      el.dataset.am = m.id;
      if (m.note) el.title = m.note;
      r.surroundContents(el);
      return true;
    } catch (e) { return false; }
  }

  /* Find a saved mark again. Prefer the occurrence it was made on; if the page has changed enough that
     the count no longer lines up, take the first one rather than showing nothing - a highlight in the
     right words and the wrong copy of them still points at the rule she meant. */
  function paintOne(m) {
    if (!m.text) return false;
    var w = walk_collect(m.text);
    if (!w.length) return false;
    var hit = w[m.nth] || w[0];
    return wrap(hit.node, hit.at, m.text, m);
  }

  function walk_collect(text) {
    var out = [], wk = walker(), n;
    while ((n = wk.nextNode())) {
      if (n.parentElement && n.parentElement.closest("mark.am")) continue;
      var i = n.nodeValue.indexOf(text);
      while (i >= 0) { out.push({ node: n, at: i }); i = n.nodeValue.indexOf(text, i + 1); }
    }
    return out;
  }
  function paintAll() {
    var list = store(), n = 0;
    for (var i = 0; i < list.length; i++) {
      if (!document.querySelector('mark.am[data-am="' + list[i].id + '"]')) { if (paintOne(list[i])) n++; }
    }
    return n;
  }

  /* --- the bar ---------------------------------------------------------------------------------- */
  var bar = document.createElement("div");
  bar.className = "am-bar"; bar.hidden = true;
  bar.innerHTML = '<div class="am-grip" title="Drag me"></div>' +
    '<button type="button" class="fold" data-a="fold" title="Fold this away" aria-label="Fold this bar away">▾</button>' +
    '<button type="button" data-a="hl">🖍 Highlight</button>' +
    '<button type="button" data-a="note">📝 Note</button>' +
    '<span class="sep" aria-hidden="true"></span>' +
    '<button type="button" class="del" data-a="del" hidden>🗑 Delete</button>';
  document.body.appendChild(bar);

  var pending = null, current = null, moved = false;

  function place(x, y) {
    bar.hidden = false;
    var w = bar.offsetWidth || 220, h = bar.offsetHeight || 46;
    var L = Math.max(8, Math.min(x - w / 2, innerWidth - w - 8));
    var T = Math.max(8, Math.min(y - h - 12, innerHeight - h - 8));
    bar.style.left = L + "px"; bar.style.top = T + "px";
  }
  function hideBar() { bar.hidden = true; pending = null; current = null; }

  /* Folded away, the bar is just its grip and an arrow, so it stops covering the words
     underneath. Her words, 20 Sep 2026: "the highlight thing can retract to save the
     space". The choice is remembered, because a control you must re-fold every time is
     the same annoyance in a different shape. */
  var SHUT = "marks.shut";
  function shutNow() { try { return localStorage.getItem(SHUT) === "1"; } catch (e) { return false; } }
  function paintFold() {
    bar.classList.toggle("shut", shutNow());
    var f = bar.querySelector('[data-a="fold"]');
    f.textContent = shutNow() ? "▸" : "▾";
    f.title = shutNow() ? "Open the highlight buttons" : "Fold this away";
  }
  function show(which) {
    bar.querySelector('[data-a="hl"]').hidden = which !== "sel";
    /* ⛔ Delete is the one that must never be missed, so it is red, it has a rule beside
       it, and folding never hides it while a highlight is actually selected. */
    var del = bar.querySelector('[data-a="del"]');
    del.hidden = which !== "mark";
    bar.querySelector(".sep").hidden = which !== "mark";
    if (which === "mark" && shutNow()) { try { localStorage.setItem(SHUT, "0"); } catch (e) {} }
    paintFold();
  }

  // Her rule 17 Sep: every floating box drags, from anywhere on it. The grip is for the case where
  // the whole bar is buttons - dragging a button would otherwise just press it.
  (function draggable() {
    var sx = 0, sy = 0, ox = 0, oy = 0, on = false;
    function down(e) {
      var p = e.touches ? e.touches[0] : e;
      on = true; moved = false; sx = p.clientX; sy = p.clientY;
      ox = bar.offsetLeft; oy = bar.offsetTop;
      document.addEventListener("pointermove", move, { passive: false });
      document.addEventListener("pointerup", up, { passive: true });
    }
    function move(e) {
      if (!on) return;
      var dx = e.clientX - sx, dy = e.clientY - sy;
      if (Math.abs(dx) + Math.abs(dy) > 4) moved = true;
      if (e.cancelable) e.preventDefault();
      bar.style.left = Math.max(4, Math.min(ox + dx, innerWidth - bar.offsetWidth - 4)) + "px";
      bar.style.top = Math.max(4, Math.min(oy + dy, innerHeight - bar.offsetHeight - 4)) + "px";
    }
    function up() {
      on = false;
      document.removeEventListener("pointermove", move);
      document.removeEventListener("pointerup", up);
    }
    bar.querySelector(".am-grip").addEventListener("pointerdown", down);
  })();

  /* Her rule of 17 Sep, and asked again for this box on 20 Sep: every floating box
     moves, and it drags from ANYWHERE on it - not only a handle. The two exceptions
     are the typing area and the buttons, because dragging those would mean she could
     never type or press them. The box starts pinned to the bottom; the first drag
     unpins it, and where she leaves it is where it opens next time. */
  var NPOS = "marks.notepos";
  function dragBox(box) {
    var sx = 0, sy = 0, ox = 0, oy = 0, on = false, went = false;
    try {
      var saved = JSON.parse(localStorage.getItem(NPOS) || "null");
      if (saved && saved.l != null) {
        if (saved.w) { box.style.width = Math.min(saved.w, innerWidth - 8) + "px"; box.style.maxWidth = "none"; }
        box.style.inset = "auto";
        box.style.left = Math.max(4, Math.min(saved.l, innerWidth - 60)) + "px";
        box.style.top = Math.max(4, Math.min(saved.t, innerHeight - 60)) + "px";
      }
    } catch (e) {}
    function down(e) {
      var t = e.target;
      if (t.closest && t.closest("textarea,button")) return;
      var r = box.getBoundingClientRect();
      /* Unpin from the bottom edge the moment she takes hold of it, or left/top would
         fight the original inset rule and the box would jump. */
      /* The box got its WIDTH from being pinned to both edges. Dropping inset without
         pinning the width first made it collapse to the size of its own buttons the
         moment she picked it up - measured, 400px down to 150px. */
      box.style.width = r.width + "px";
      box.style.maxWidth = "none";
      box.style.inset = "auto";
      box.style.left = r.left + "px"; box.style.top = r.top + "px";
      box.style.margin = "0";
      on = true; went = false; sx = e.clientX; sy = e.clientY; ox = r.left; oy = r.top;
      document.addEventListener("pointermove", move, { passive: false });
      document.addEventListener("pointerup", up, { passive: true });
    }
    function move(e) {
      if (!on) return;
      var dx = e.clientX - sx, dy = e.clientY - sy;
      if (Math.abs(dx) + Math.abs(dy) > 4) went = true;
      if (e.cancelable) e.preventDefault();
      box.style.left = Math.max(4, Math.min(ox + dx, innerWidth - box.offsetWidth - 4)) + "px";
      box.style.top = Math.max(4, Math.min(oy + dy, innerHeight - box.offsetHeight - 4)) + "px";
    }
    function up() {
      on = false;
      document.removeEventListener("pointermove", move);
      document.removeEventListener("pointerup", up);
      if (went) { try { localStorage.setItem(NPOS,
        JSON.stringify({ l: box.offsetLeft, t: box.offsetTop, w: box.offsetWidth })); } catch (e) {} }
    }
    box.addEventListener("pointerdown", down);
  }

  function noteBox(initial, onSave) {
    var box = document.createElement("div");
    box.className = "am-note";
    box.innerHTML = '<div class="nhead"><span>drag me anywhere</span></div>' +
      '<textarea placeholder="What needs changing here?"></textarea>' +
      '<div class="row"><button type="button" data-c="x">Cancel</button><button type="button" class="go" data-c="ok">Save note</button></div>';
    document.body.appendChild(box);
    dragBox(box);
    var ta = box.querySelector("textarea");
    ta.value = initial || ""; ta.focus();
    box.addEventListener("click", function (e) {
      var c = e.target.getAttribute && e.target.getAttribute("data-c");
      if (!c) return;
      if (c === "ok") onSave(ta.value.trim());
      box.remove();
    });
  }

  function addFromSelection(note) {
    var sel = getSelection();
    if (!sel || sel.isCollapsed) return null;
    var text = String(sel).trim();
    if (!text) return null;
    // which occurrence of these words this is, counted the same way paintOne counts
    var rng = sel.getRangeAt(0);
    var all = walk_collect(text), before = 0;
    for (var k = 0; k < all.length; k++) {
      var probe = document.createRange();
      probe.setStart(all[k].node, all[k].at);
      if (probe.compareBoundaryPoints(Range.START_TO_START, rng) < 0) before++;
    }
    var m = { id: String(Date.now()) + String(Math.random()).slice(2, 6), text: text, nth: before, note: note || "", at: Date.now() };
    var list = store(); list.push(m); keep(list);
    // Paint the words she actually selected. Anything else re-finds them, and re-finding was the bug.
    var painted = false;
    if (all[before]) painted = wrap(all[before].node, all[before].at, text, m);
    sel.removeAllRanges();
    if (!painted) paintOne(m);
    send(m);
    said(note ? "Note saved" : "Highlighted");
    return m;
  }

  bar.addEventListener("click", function (e) {
    if (moved) { moved = false; return; }
    var a = e.target.getAttribute && e.target.getAttribute("data-a");
    if (!a) return;
    if (a === "fold") {
      try { localStorage.setItem(SHUT, shutNow() ? "0" : "1"); } catch (e) {}
      paintFold(); return;
    }
    if (a === "hl") { addFromSelection(""); hideBar(); return; }
    if (a === "note") {
      if (current) {
        var id = current.dataset.am, list = store();
        var m = list.filter(function (x) { return x.id === id; })[0];
        noteBox(m && m.note, function (v) {
          if (!m) return;
          m.note = v; keep(list);
          current.classList.toggle("noted", !!v);
          if (v) current.title = v; else current.removeAttribute("title");
          send(m); said("Note saved");
        });
      } else {
        var saved = addFromSelection("");
        if (saved) noteBox("", function (v) {
          var list2 = store(), m2 = list2.filter(function (x) { return x.id === saved.id; })[0];
          if (!m2) return;
          m2.note = v; keep(list2);
          var el = document.querySelector('mark.am[data-am="' + saved.id + '"]');
          if (el) { el.classList.toggle("noted", !!v); if (v) el.title = v; }
          send(m2); said("Note saved");
        });
      }
      hideBar(); return;
    }
    if (a === "del" && current) {
      var did = current.dataset.am;
      keep(store().filter(function (x) { return x.id !== did; }));
      unsend(did);
      var p = current.parentNode;
      while (current.firstChild) p.insertBefore(current.firstChild, current);
      current.remove(); p.normalize();
      said("Deleted"); hideBar(); return;
    }
  });

  document.addEventListener("click", function (e) {
    var m = e.target.closest && e.target.closest("mark.am");
    if (m) {
      current = m; pending = null; show("mark");
      var r = m.getBoundingClientRect();
      place(r.left + r.width / 2, r.top);
      return;
    }
    if (!e.target.closest || !e.target.closest(".am-bar,.am-note")) hideBar();
  });

  function afterSelect() {
    setTimeout(function () {
      var sel = getSelection();
      if (!sel || sel.isCollapsed || !String(sel).trim()) return;
      if (sel.anchorNode && sel.anchorNode.parentElement &&
          sel.anchorNode.parentElement.closest("input,textarea,[contenteditable],.am-bar,.am-note")) return;
      current = null; pending = true; show("sel");
      var r = sel.getRangeAt(0).getBoundingClientRect();
      place(r.left + r.width / 2, r.top);
    }, 10);
  }
  document.addEventListener("mouseup", afterSelect);
  document.addEventListener("touchend", afterSelect);

  function start() {
    paintAll();
    // The Rule Shelf and several apps redraw their own contents; repaint when they do.
    try {
      var root = document.querySelector(ROOT_SEL);
      if (root && window.MutationObserver) {
        var t = null;
        new MutationObserver(function () {
          clearTimeout(t); t = setTimeout(paintAll, 250);
        }).observe(root, { childList: true, subtree: true });
      }
    } catch (e) {}
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", start);
  else start();
})();
