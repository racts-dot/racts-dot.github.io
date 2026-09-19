(function(){
  "use strict";
  var $ = function(id){ return document.getElementById(id); };
  var POLL = 60 * 1000;
  function esc(s){ return String(s == null ? "" : s).replace(/[&<>"]/g, function(m){
    return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[m]; }); }
  /* two digits. NOT named "pad": the textarea below has id="pad", and the browser
     publishes every id on window, which shadowed this and stopped the clock. */
  function two(n){ return (n < 10 ? "0" : "") + n; }

  /* ---- clock and greeting: the machine's own clock, nothing fetched ---- */
  function tick(){
    var d = new Date(), h = d.getHours();
    $("clock").innerHTML = two(h % 12 || 12) + ":" + two(d.getMinutes()) + "<small>" + (h < 12 ? "am" : "pm") + "</small>";
    $("greet").textContent = (h < 5 ? "Still up, Rachel." : h < 12 ? "Good morning, Rachel." :
                              h < 17 ? "Good afternoon, Rachel." : h < 22 ? "Good evening, Rachel." : "Late one, Rachel.");
    $("date").textContent = d.toLocaleDateString("en-AU", {weekday:"long", day:"numeric", month:"long", year:"numeric"});
  }
  tick(); setInterval(tick, 15 * 1000);

  /* ---- today's focus: hers, on THIS device only. localStorage never crosses machines,
         so the label names the machine rather than letting a blank field look like lost text. ---- */
  var MACHINE = /Mac/i.test(navigator.platform + " " + navigator.userAgent) ? "Mac"
              : /Win/i.test(navigator.platform + " " + navigator.userAgent) ? "Windows" : "this device";
  $("focusLabel").textContent = "Today on " + MACHINE;
  var KEY = "start.focus." + new Date().toISOString().slice(0,10);
  var focus = $("focus"), clear = $("focusClear");
  try { focus.value = localStorage.getItem(KEY) || ""; } catch(e){}
  clear.hidden = !focus.value;
  focus.addEventListener("input", function(){
    try { localStorage.setItem(KEY, focus.value); } catch(e){}
    clear.hidden = !focus.value;
  });
  clear.addEventListener("click", function(){ focus.value = ""; focus.dispatchEvent(new Event("input")); });

  /* ---- The Day: the count and the stream ---- */
  function ago(iso){
    var t = Date.parse(iso); if (isNaN(t)) return "";
    var m = Math.round((Date.now() - t) / 60000);
    return m < 1 ? "just now" : m < 60 ? m + " min ago" : m < 1440 ? Math.round(m/60) + " h ago" : Math.round(m/1440) + " d ago";
  }
  function hhmm(iso){ var d = new Date(iso); return isNaN(d) ? "" : two(d.getHours()) + ":" + two(d.getMinutes()); }
  function kindOf(e){
    var k = (e.kind || "").toLowerCase(), s = (e.stage || "").toLowerCase();
    if (s === "live" || k === "live") return "live";
    if (k === "commit") return "commit";
    if (k === "slip") return "slip";
    if (k === "stage" || k === "queue" || s) return "stage";
    return "register";
  }
  function renderDay(d){
    var c = d.counts || {}, p = d.pace || {}, live = c.live_today != null ? c.live_today : "–";
    $("liveToday").textContent = live;
    $("target").textContent = "of " + (d.target || 30) + " today";
    $("bar").style.width = (d.target ? Math.min(100, 100 * (c.live_today || 0) / d.target) : 0) + "%";
    var made = d.made_iso || d.made, age = made ? Date.now() - Date.parse(made) : 0;
    var stale = made && age > 3 * 3600 * 1000;
    $("dot").className = "dot " + (stale ? "cold" : "beat");
    /* The calm view stays calm unless something is genuinely wrong. 40 minutes is two missed
       runs of a 20-minute timer, so it means the timer stopped, not that it is between runs. */
    var warn = $("stale");
    if (made && age > 40 * 60 * 1000){
      warn.textContent = "The day's feed has not been rebuilt for " + ago(made).replace(" ago", "") + ". The timer may be down.";
      warn.className = "stale on";
    } else { warn.className = "stale"; warn.textContent = ""; }
    var bits = [];
    if (c.ready_to_list != null) bits.push(c.ready_to_list + " ready to list");
    if (c.in_build != null) bits.push(c.in_build + " in build");
    if (c.published_not_read_back) bits.push(c.published_not_read_back + " published, not read back");
    bits.push("feed " + (made ? ago(made) : "undated") + (stale ? " · timer may be down" : ""));
    $("pace").textContent = bits.join(" · ");

    var today = d.day || new Date().toISOString().slice(0,10);
    /* The timers' own commits ("The Day: ...", "Desk: ...", "Hourly backup ...") are not work she
       did; The Day app shows them, a start page does not need to. */
    var noise = /^(The Day: tasks done today|Desk: where we're up to|Hourly backup |The Day: |Desk card)/i;
    var evs = (d.events || []).filter(function(e){
      return (e.at || "").slice(0,10) === today && !(e.kind === "commit" && noise.test(e.title || "")); }).slice(0, 18);
    if (!evs.length){
      var y = (d.events || []).slice(0, 8);
      $("events").innerHTML = '<li class="empty">Nothing recorded yet today' + (y.length ? " · the last things that happened:" : ".") + "</li>" +
        y.map(row).join("");
      return;
    }
    $("events").innerHTML = evs.map(row).join("");
  }
  function row(e){
    var k = kindOf(e), where = e.detail && e.detail !== e.title ? "<small>" + esc(e.detail) + "</small>" : "";
    var lane = e.lane ? "<small>lane " + esc(e.lane) + "</small>" : "";
    return '<li class="ev ' + k + '"><span class="t">' + hhmm(e.at) + '</span><span class="k"></span>' +
           '<span class="w">' + esc(e.title) + where + lane + "</span></li>";
  }

  /* ---- the Desk: what is waiting on her ---- */
  function renderDesk(d){
    var all = (d.items || []).filter(function(i){ return !/^j_/.test(i.id || ""); });
    /* THE ONE THING THE REVIEW INSISTED ON. Hiding the list is fine; hiding the NOTICE is not,
       or a decision waiting on her is never seen again. The dot is the notice; the list stays behind
       the button. Gemini 3.1 Pro, 19 Sep 2026: "decouple the notification from the information". */
    $("trigger").classList.toggle("has", all.length > 0);
    $("trigger").setAttribute("aria-label", all.length
      ? all.length + " thing(s) waiting on you. Show the day, what is waiting, and every link"
      : "Show the day, what is waiting, and every link");
    var items = all.slice(0, 6);
    if (!items.length){ $("wait").innerHTML = '<li class="empty">Nothing waiting on you.</li>'; return; }
    $("wait").innerHTML = items.map(function(i){
      var note = i.note && !/^No next action/.test(i.note) ? '<div class="d">' + esc(i.note.slice(0, 160)) + "</div>" : "";
      return "<li>" + esc(i.name) + note + "</li>";
    }).join("") + '<li class="empty" style="border-top:1px solid var(--line)">Desk card ' + (d.made ? "made " + esc(d.made) : "undated") + "</li>";
  }

  /* ---- chats, only if the file has been published ---- */
  function renderChats(d){
    var rows = (d.chats || []).slice(0, 10);
    var m = Object.keys(d.machines || {}).map(function(k){
      var i = d.machines[k]; return k + (i.stale ? " quiet " + i.hours_ago + "h" : " ok"); }).join(" · ");
    $("chatsWhen").textContent = (d.counts ? d.counts.working + " working · " : "") + (m || "") + (d.made ? " · read " + d.made : "");
    if (!rows.length){ $("chats").innerHTML = '<li class="empty">No chat has written in the window.</li>'; return; }
    $("chats").innerHTML = rows.map(function(c){
      var mc = (c.machine || "this").toLowerCase();
      return '<li class="' + esc(c.state || "") + '"><span class="m ' + esc(mc) + '">' + esc(mc === "this" ? "here" : mc) + "</span>" +
             '<span class="w" title="' + esc(c.did || "") + '">' + esc(c.folder) + (c.did ? " · " + esc(c.did.slice(0, 120)) : "") + "</span>" +
             '<span class="a">' + esc((c.when || "").slice(11)) + "</span></li>";
    }).join("");
  }

  /* ================= the scratch pad: one pad, every device =================
     Her ask, 19 Sep 2026: "do you have anything like a scratch pad that synchronises?",
     then "can it be for every device i own". So the text does NOT live in this browser.
     It goes to a Notion database through apps-notion-relay - the same road twenty of her
     apps already use - and every device reads that same row back.
        this device  --NotionSync.save-->  relay  -->  Notion "Scratch pad"
        any device   <--NotionSync.list--  relay  <--
     A localStorage copy is kept too, but only so the pad works offline and before the
     relay password has been entered on a new device. Notion is what is true.
     IT NEVER OVERWRITES WHAT SHE IS TYPING. If another device saved something newer and
     different, it SAYS SO and she chooses. Silently replacing her words would be the
     worst possible bug in a notepad. ========================================== */
  var PAD_APP = "scratch", PAD_ID = "pad", PAD_LOCAL = "start.pad";
  var padBox = $("pad"), padState = $("padState"), padClash = $("padClash");
  var padSaved = "", padTimer = null, padBusy = false;

  function padSay(m){ padState.textContent = m; }
  function padStamp(){ return new Date().toISOString(); }
  function padKeepLocal(){
    try { localStorage.setItem(PAD_LOCAL, JSON.stringify({
      text: padBox.value, sent: padSaved, at: padStamp(), machine: MACHINE })); } catch(e){}
  }
  try {
    var praw = localStorage.getItem(PAD_LOCAL);
    if (praw){ var po = JSON.parse(praw); padBox.value = po.text || ""; padSaved = po.sent || ""; }
  } catch(e){}

  function padSend(){
    padKeepLocal();
    if (padBox.value === padSaved){ return; }
    if (!window.NotionSync){ padSay("on this device only - the sync script did not load"); return; }
    if (padBusy) return;
    padBusy = true; padSay("saving...");
    var text = padBox.value, now = padStamp();
    var first = (text.split("\n")[0] || "").trim().slice(0, 80) || "(empty)";
    try {
      NotionSync.save(PAD_APP, PAD_ID, { title: first, detail: text, when: now,
                                         data: { machine: MACHINE, at: now } });
      padSaved = text; padKeepLocal();
      setTimeout(function(){
        padBusy = false;
        var n = NotionSync.pending ? NotionSync.pending() : 0;
        padSay(n ? "waiting to send (" + n + ") - it will go when the relay answers"
                 : "saved to every device, " + new Date().toLocaleTimeString("en-AU",
                     { hour: "2-digit", minute: "2-digit" }));
      }, 900);
    } catch(e){ padBusy = false; padSay("could not save: " + e.message); }
  }

  function padPull(){
    if (!window.NotionSync || !NotionSync.list) return;
    NotionSync.list(PAD_APP).then(function(rows){
      var row = (rows || []).filter(function(r){ return r.id === PAD_ID; })[0];
      if (!row){ padSay(padBox.value ? "not sent yet" : "empty - type anything"); return; }
      var who = (row.data && row.data.machine) || "another device";
      var when = row.when ? ago(row.when) : "";
      if (row.detail === padBox.value){
        padSaved = row.detail; padKeepLocal();
        padClash.className = "clash";
        padSay("in step everywhere, last written on " + who + " " + when);
        return;
      }
      /* Nothing of hers is at risk only if she has not typed since the last send. */
      if (padBox.value === padSaved || padBox.value === ""){
        padBox.value = row.detail; padSaved = row.detail; padKeepLocal();
        padClash.className = "clash";
        padSay("picked up from " + who + " " + when);
      } else {
        padClash.className = "clash on";
        padClash.innerHTML = "<b>" + esc(who) + "</b> saved a different copy " + esc(when) +
          ", and you have words here that have not been sent. Nothing has been changed." +
          "<div><button id='padTake' type='button'>use theirs</button>" +
          "<button id='padKeep' type='button'>keep mine and send it</button></div>";
        $("padTake").onclick = function(){
          padBox.value = row.detail; padSaved = row.detail; padKeepLocal();
          padClash.className = "clash"; padSay("took the copy from " + who);
        };
        $("padKeep").onclick = function(){ padClash.className = "clash"; padSend(); };
      }
    }).catch(function(e){
      padSay(/password/i.test(e.message || "")
        ? "on this device only - press Connect to share it with your others"
        : "could not read the shared copy: " + (e.message || e));
    });
  }

  $("padWho").textContent = "every device, this is " + MACHINE;
  padSay("on this device");
  padBox.addEventListener("input", function(){
    padKeepLocal(); padSay("typing...");
    clearTimeout(padTimer); padTimer = setTimeout(padSend, 1500);
  });
  padBox.addEventListener("blur", function(){ clearTimeout(padTimer); padSend(); });
  $("padSync").addEventListener("click", function(){ clearTimeout(padTimer); padSend(); padPull(); });
  window.addEventListener("pagehide", function(){ if (padBox.value !== padSaved) padSend(); });

  /* ---- searching the tiles. Her note on the feedback board, 19 Sep: "left search bar
     for the websites". It filters what is already on the page: no network, no second
     list to keep up to date, and Enter opens the first thing still showing. ---- */
  function tileFilter(){
    var q = ($("tileq").value || "").trim().toLowerCase();
    var groups = document.querySelectorAll(".group"), all = 0, shown = 0;
    for (var i = 0; i < groups.length; i++){
      var tiles = groups[i].querySelectorAll(".tile"), any = 0;
      for (var j = 0; j < tiles.length; j++){
        all++;
        var hit = !q || tiles[j].textContent.toLowerCase().indexOf(q) >= 0;
        tiles[j].style.display = hit ? "" : "none";
        if (hit){ any++; shown++; }
      }
      groups[i].className = "group" + (any ? "" : " hide");
    }
    $("tilecount").textContent = q ? shown + " of " + all : "";
  }
  $("tileq").addEventListener("input", tileFilter);
  $("tileq").addEventListener("keydown", function(e){
    if (e.key !== "Enter") return;
    var first = null, tiles = document.querySelectorAll(".tile");
    for (var i = 0; i < tiles.length && !first; i++) if (tiles[i].style.display !== "none") first = tiles[i];
    if (first) location.href = first.getAttribute("href");
  });

  function renderLinks(d){
    $("groups").innerHTML = (d.groups || []).map(function(g){
      return '<div class="group"><h3>' + esc(g.name) + '</h3><div class="tiles">' + (g.links || []).map(function(l){
        return '<a class="tile" href="' + esc(l.url) + '"><div class="n">' + esc(l.name) + "</div>" +
               (l.hint ? '<div class="h">' + esc(l.hint) + "</div>" : "") + "</a>";
      }).join("") + "</div></div>";
    }).join("");
  }

  function get(url, ok, fail){
    fetch(url + (url.indexOf("?") < 0 ? "?" : "&") + "t=" + Date.now(), {cache:"no-store"})
      .then(function(r){ if (!r.ok) throw new Error(r.status); return r.json(); }).then(ok).catch(fail || function(){});
  }
  function pull(){
    get("https://racts-dot.github.io/day/stream.json", renderDay, function(e){
      $("pace").textContent = "The Day feed could not be read (" + e.message + ")"; $("dot").className = "dot cold";
      $("events").innerHTML = '<li class="empty">/day/stream.json did not load.</li>';
    });
    get("https://racts-dot.github.io/desk/progress.json", renderDesk, function(e){
      $("wait").innerHTML = '<li class="empty">/desk/progress.json did not load (' + esc(e.message) + ").</li>";
    });
    get("https://racts-dot.github.io/start/chats.json", renderChats, function(e){
      $("chatsWhen").textContent = "";
      $("chats").innerHTML = '<li class="empty">Not published. <code>status/chat_activity.py</code> writes chats.json but puts it on the site only on your word, because it quotes what each chat was asked. Say yes and this panel fills.</li>';
    });
  }
  /* The 35 tiles are ~35 elements she does not see until she asks, so they are built on the
     FIRST open, not on load. A new tab is opened dozens of times a day and must paint at once. */
  var tilesBuilt = false;
  function buildTiles(){
    if (tilesBuilt) return; tilesBuilt = true;
    get("https://racts-dot.github.io/start/links.json", function(d){ renderLinks(d); tileFilter(); }, function(e){
      tilesBuilt = false;
      $("groups").innerHTML = '<p class="empty">links.json did not load (' + esc(e.message) + ").</p>";
    });
  }

  /* ---- open and close: one button, Esc, the scrim, and the browser Back key ---- */
  var lastFocus = null;
  function open(){
    buildTiles(); pull(); padPull();
    document.body.classList.add("open");
    $("trigger").setAttribute("aria-expanded", "true");
    lastFocus = document.activeElement;
    $("close").focus();
  }
  function shut(){
    document.body.classList.remove("open");
    $("trigger").setAttribute("aria-expanded", "false");
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function toggle(){ document.body.classList.contains("open") ? shut() : open(); }
  $("trigger").addEventListener("click", toggle);
  $("close").addEventListener("click", shut);
  $("scrim").addEventListener("click", shut);
  document.addEventListener("keydown", function(e){
    if (e.key === "Escape" && document.body.classList.contains("open")){ e.preventDefault(); shut(); return; }
    /* Nothing is typed into the focus field by accident: only when she is NOT in a field. */
    var t = e.target, typing = t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable);
    if (!typing && !e.metaKey && !e.ctrlKey && !e.altKey && (e.key === "d" || e.key === "D")){ e.preventDefault(); toggle(); }
  });
  /* Six weeks from now she will not remember a corner button exists, so the first three
     times this page is opened the label sits beside it for four seconds, then stops for good. */
  try {
    var seen = parseInt(localStorage.getItem("start.seen") || "0", 10);
    if (seen < 3){
      localStorage.setItem("start.seen", String(seen + 1));
      $("hint").classList.add("show");
      setTimeout(function(){ $("hint").classList.remove("show"); }, 4000);
    }
  } catch(e){}

  pull();
  setInterval(pull, POLL);
  document.addEventListener("visibilitychange", function(){ if (!document.hidden) pull(); });
  /* The shared /pull.js clicks #refresh on a drag-down; this is what it triggers. */
  $("refresh").addEventListener("click", pull);
})();