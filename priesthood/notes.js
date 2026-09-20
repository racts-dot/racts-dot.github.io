/* Your notes - the priesthood teaching from Rachel's OWN library, inside the app.

   Her words, 16 Sep 2026: "Everything has to be from the resources like if it is not just mention
   reference. So I was wanting to get things from the Notion notes and to be here." And again on
   18 Sep: "I will need it from my own resource. All those information. Do not find it from
   elsewhere."

   Until now this app said, honestly, that none of it came from her notes. This is the first
   instalment of the other half: 100 entries read out of her own Video Knowledge Library in Notion
   on 20 September 2026 - every one of them a teaching SHE saved, summarised and filed, with the
   speaker, the date it was published, the scriptures it uses, and a way back to her Notion page
   and to the video itself.

   ⛔ NOTHING HERE IS WRITTEN BY AN AI ABOUT SCRIPTURE. Every line is her own record, copied
   unaltered: the one-line summary that is already on her page, and the fields beside it. Where a
   field is empty it is left empty rather than filled in.

   It is a skeleton on purpose - her instruction the same day: "just to get the skeletons right and
   add one after the other". What is not here yet, and is named rather than implied: the teaching
   points, the quotes worth keeping and the claims-to-check that live in the body of each Notion
   page. Those come next. */
(function () {
  "use strict";
  if (window.__phNotes) return;
  window.__phNotes = true;

  var DATA = null, wrap = null, listEl = null, q = "";

  var css = document.createElement("style");
  css.textContent =
    "#phnotes{margin:2rem 0 1rem}" +
    "#phnotes h2{margin:0 0 .25rem}" +
    "#phnotes .nsub{margin:0 0 .75rem;opacity:.75;font-size:.9rem}" +
    "#phnotes .nfind{width:100%;padding:.6rem .8rem;border:1px solid var(--line,#d9cebd);" +
      "border-radius:.7rem;background:var(--panel,#fff);color:inherit;font:inherit}" +
    "#phnotes .ncount{font-size:.8rem;opacity:.7;margin:.5rem 0}" +
    "#phnotes ol{list-style:none;margin:0;padding:0}" +
    "#phnotes li{padding:.7rem 0;border-top:1px solid var(--line,#d9cebd)}" +
    "#phnotes .nt{font-weight:650;line-height:1.3}" +
    "#phnotes .ns{margin:.25rem 0 0;font-size:.92rem}" +
    "#phnotes .nm{margin-top:.35rem;font-size:.78rem;opacity:.75;display:flex;flex-wrap:wrap;gap:.5rem}" +
    "#phnotes .nm a{text-decoration:underline}" +
    "#phnotes .nmore{margin-top:.8rem}" +
    "#phnotes .nopen{margin-top:.5rem}" +
    "#phnotes .nopen>summary{cursor:pointer;font-size:.82rem;opacity:.85}" +
    "#phnotes .nh{margin:.7rem 0 .25rem;font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;font-weight:700;opacity:.8}" +
    "#phnotes .nh span{display:block;text-transform:none;letter-spacing:0;font-weight:500;opacity:.75}" +
    "#phnotes .npts,#phnotes .nchk{margin:.2rem 0 0 1.1rem;padding:0}" +
    "#phnotes .npts li,#phnotes .nchk li{margin:.25rem 0}" +
    "#phnotes .nq{margin:.35rem 0;padding-left:.7rem;border-left:3px solid var(--line,#d9cebd);font-style:italic}";
  document.head.appendChild(css);

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>\"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function words(d) {
    if (!d) return "";
    var p = /^(\d{4})-(\d{2})-(\d{2})$/.exec(d);
    if (!p) return d;
    var M = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    return (+p[3]) + " " + M[(+p[2]) - 1] + " " + p[1];
  }

  var shown = 20;
  function matches(n) {
    if (!q) return true;
    var hay = (n.t + " " + n.w + " " + n.s + " " + n.r + " " + n.c + " " +
               (n.pts || []).join(" ") + " " + (n.qs || []).join(" ")).toLowerCase();
    return hay.indexOf(q) >= 0;
  }
  function paint() {
    if (!DATA) return;
    var hits = DATA.filter(matches);
    listEl.innerHTML = hits.slice(0, shown).map(function (n) {
      var bits = [];
      if (n.w) bits.push(esc(n.w));
      if (n.y) bits.push(esc(words(n.y)));
      if (n.r) bits.push(esc(n.r));
      if (n.n) bits.push('<a href="' + esc(n.n) + '" target="_blank" rel="noopener">your note</a>');
      if (n.v) bits.push('<a href="' + esc(n.v) + '" target="_blank" rel="noopener">the video</a>');
      var body = "";
      if ((n.pts && n.pts.length) || (n.qs && n.qs.length) || (n.chk && n.chk.length)) {
        body += '<details class="nopen"><summary>The teaching, the quotes, and what to check</summary>';
        if (n.pts && n.pts.length) {
          body += '<p class="nh">The teaching, in order <span>summary, written by Gemini</span></p><ol class="npts">' +
            n.pts.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ol>";
        }
        if (n.qs && n.qs.length) {
          body += '<p class="nh">Worth keeping, word for word <span>the speaker&rsquo;s own words</span></p>' +
            n.qs.map(function (x) { return '<blockquote class="nq">' + esc(x) + "</blockquote>"; }).join("");
        }
        if (n.chk && n.chk.length) {
          body += '<p class="nh">Check before you act on it <span>claims, not facts</span></p><ul class="nchk">' +
            n.chk.map(function (x) { return "<li>" + esc(x) + "</li>"; }).join("") + "</ul>";
        }
        body += "</details>";
      }
      return '<li><p class="nt">' + esc(n.t) + '</p>' +
             (n.s ? '<p class="ns">' + esc(n.s) + '</p>' : "") +
             '<p class="nm">' + bits.join('<span aria-hidden="true">·</span>') + '</p>' + body + '</li>';
    }).join("");
    wrap.querySelector(".ncount").textContent =
      hits.length + (hits.length === 1 ? " note" : " notes") + (q ? " matching" : " from your library") +
      (hits.length > shown ? ", showing " + shown : "");
    var more = wrap.querySelector(".nmore");
    more.hidden = hits.length <= shown;
    more.textContent = "Show more";
  }

  function build() {
    wrap = document.createElement("section");
    wrap.id = "phnotes";
    wrap.setAttribute("aria-label", "Your notes");
    wrap.innerHTML =
      "<h2>Your notes</h2>" +
      '<p class="nsub">From your own Video Knowledge Library in Notion, read 20 September 2026. ' +
      "You chose these videos, saved them and filed them. " +
      "<b>The quotes are the speaker's own words</b>, checked against the transcript. " +
      "<b>The summaries and the points were written by Gemini from the transcript</b>, not by you and not by a person - " +
      "which is what your own Notion page says at the foot of each one. Nothing here is Scripture; " +
      "the Bible text in this app comes from the translations, not from these notes.</p>" +
      '<input class="nfind" type="search" placeholder="Search your notes" aria-label="Search your notes">' +
      '<p class="ncount"></p><ol></ol>' +
      '<button type="button" class="nmore" hidden>Show more</button>';
    var main = document.querySelector("main") || document.querySelector(".wrap") || document.body;
    main.appendChild(wrap);
    listEl = wrap.querySelector("ol");
    wrap.querySelector(".nfind").addEventListener("input", function (e) {
      q = (e.target.value || "").trim().toLowerCase(); shown = 20; paint();
    });
    wrap.querySelector(".nmore").addEventListener("click", function () { shown += 20; paint(); });
  }

  // Fetched rather than inlined so the page itself stays the size it was, and so the notes can be
  // refreshed on their own. It is in the service worker's shell list, so it works offline too.
  fetch("notes.json", { cache: "no-cache" })
    .then(function (r) { return r.ok ? r.json() : null; })
    .then(function (d) {
      if (!d || !d.length) return;      // nothing to show is better than an empty heading
      DATA = d; build(); paint();
    })
    .catch(function () {});
})();
