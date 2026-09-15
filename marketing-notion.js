/* marketing-notion.js — Notion for the Hormozi recipes and Doser workflows pages (15 Sep 2026).
 *
 * Both pages were claude.ai artifacts. Moved here on her pick "Public only", so they open on any
 * account. Loaded after notion-sync.js with data-app="hormozi" or data-app="workflows".
 *
 *  1. Her yes/no answers on each card (localStorage "hmr-checks") are copied to Notion,
 *     one row per card. A card with every answer cleared ticks Deleted in Notion.
 *  2. The Hormozi "Try this in Notion" button used the claude.ai Notion connector, which only
 *     exists inside claude.ai. Here it sends the same recipe through the apps relay instead.
 *
 * The page's own saving is untouched; nothing here can stop a tick from saving on the phone.
 */
(function () {
  "use strict";
  var me = document.currentScript;
  var APP = me && me.dataset.app;
  var DB_URL = me && me.dataset.notion;
  if (!APP) return;
  var CHECKS = "hmr-checks";

  function cardTitle(key) {
    var h = document.querySelector('.card[data-key="' + key + '"] h3');
    return h ? h.textContent.trim() : key;
  }

  function readChecks() {
    try { return JSON.parse(localStorage.getItem(CHECKS) || "{}") || {}; } catch (e) { return {}; }
  }

  var lastSent = {};
  function syncChecks() {
    if (!window.NotionSync) return;
    try {
      var checks = readChecks();
      var live = {};
      Object.keys(checks).forEach(function (key) {
        var ans = checks[key] || {};
        var given = Object.keys(ans).filter(function (i) { return ans[i] != null; }).sort();
        if (!given.length) return;
        live["answers-" + key] = 1;
        var clean = {};
        given.forEach(function (i) { clean[i] = ans[i]; });
        var sig = JSON.stringify(clean);
        if (lastSent["answers-" + key] === sig) return;
        lastSent["answers-" + key] = sig;
        window.NotionSync.save(APP, "answers-" + key, {
          title: cardTitle(key),
          detail: given.map(function (i) {
            return "Question " + (Number(i) + 1) + ": " + ({ y: "yes", n: "no", x: "not for me" }[clean[i]] || clean[i]);
          }).join(" · "),
          data: { card: key, answers: clean },
        });
      });
      window.NotionSync.knownIds(APP).forEach(function (id) {
        if (id.indexOf("answers-") === 0 && !live[id]) {
          delete lastSent[id];
          window.NotionSync.remove(APP, id);
        }
      });
    } catch (e) { /* Notion must never break the page */ }
  }

  // Catch every write of the answers, whichever code path makes it.
  try {
    var proto = Object.getPrototypeOf(window.localStorage);
    var original = proto.setItem;
    proto.setItem = function (k, v) {
      var out = original.apply(this, arguments);
      if (k === CHECKS) setTimeout(syncChecks, 0);
      return out;
    };
  } catch (e) {}
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", function () { setTimeout(syncChecks, 500); });
  else setTimeout(syncChecks, 500);

  // "Try this in Notion": stand in for the claude.ai connector the page expects.
  if (!window.claude) {
    window.claude = {
      use: function () {
        return Promise.resolve({
          callTool: function (server, tool, args) {
            if (!window.NotionSync) return Promise.reject(new Error("Notion is not loaded on this page"));
            var page = (args && args.pages && args.pages[0]) || {};
            var props = page.properties || {};
            var name = String(props.Name || "Recipe");
            var id = "try-" + name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 80);
            window.NotionSync.save(APP, id, {
              title: name,
              detail: String(page.content || ""),
              when: new Date().toISOString(),
              data: { doThis: props["Do this"] || "", watchFor: props["Watch for"] || "", source: props.Source || "" },
            });
            return Promise.resolve({ payload: { pages: [{ url: DB_URL || "https://app.notion.com/p/3dbd360cea838182bb98df626533c40b" }] } });
          },
        });
      },
    };
  }
})();
