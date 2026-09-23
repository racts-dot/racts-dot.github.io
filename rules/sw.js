/* Rule Shelf service worker.

   The whole shelf is ONE file - index.html carries every rule book inside it as
   data - so the app shell IS the content. Cache first, so it opens with no
   internet at all, which is the point of having it on the home screen.

   BUMP CACHE whenever index.html changes, or phones keep serving the old rules.
   status/rule_shelf/refresh.py rebuilds and pushes that file, so the version
   below is bumped by hand when the shelf's shape changes - not on every rule
   edit, because the network-first rule for index.html already picks those up.

   Added 19 Sep 2026 on her word, "even though it is not app, I want app."
*/
/* v2, 20 Sep 2026: three of the seven shared scripts the page loads were never in the
   list below - marks.js, notion-sync.js and pull.js - so on a phone with no signal the
   shelf opened without highlights, without notes, without Notion and without pull to
   refresh, and nothing said so. Found by the cache serving a stale marks.js during a
   change to it. The list is now derived from what index.html actually loads; if a script
   is added to the page, add it here too, or it silently stops working offline. */
/* v7, 21 Sep 2026: TWO things, and the first is why a fix to a shared script would never have
   reached her phone on its own. Everything below except index.html is served CACHE FIRST, so a
   corrected ../swipe.js can sit on GitHub for ever while the installed shelf keeps running the
   copy taken at install. MEASURED today: the swipe fix was live on the public URL and a browser
   that had opened the shelf before was still running the OLD file - old script tag, swipe still
   dead. A push is not a published page, and for anything in this list it is not even a served
   file until this number moves. Second: hearsel.js is on the page and was NOT in the list - the
   identical fault the v2 note above describes, back again, so with no signal she loses "hear the
   bit you picked" and nothing says so. */
/* v9, 23 Sep 2026: marks.js gained ".am-bar[hidden]{display:none}" - without it the author
   rule display:flex beat the browser's own [hidden] rule, so the Highlight/Note bar sat on
   screen with nothing selected. MEASURED on the live shelf the same day: the corrected
   marks.js was already being served (fetch with a cache-buster returned it) while the OPEN
   page still drew the bar 216x56, because this cache serves it first. Bumping the version is
   what actually reaches a phone. */
/* v11, 23 Sep 2026: the activate step below deleted EVERY cache on the site that was not the
   shelf's own - and every app on racts-dot.github.io shares one cache store, so installing the
   shelf wiped the Daily Chapter, the Day and the others' offline copies. It now deletes only
   old "rule-shelf-" caches. The version moves so phones fetch this corrected worker. */
const CACHE = "rule-shelf-v11";
const SHELL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./apple-touch-icon.png",
  "./icon-192.png",
  "./icon-512.png",
  "../textsize.js",
  "../speak.js",
  "../feedback.js",
  "../swipe.js",
  "../marks.js",
  "../notion-sync.js",
  "../pull.js",
  "../hearsel.js"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (c) {
      // addAll fails the whole install if ONE file 404s, and the kit scripts sit
      // a level up where a path can drift. Add them one at a time so a missing
      // script costs that script, not the entire offline copy.
      return Promise.all(SHELL.map(function (u) {
        // cache:"reload" or the fetch behind c.add can be answered from the BROWSER's
        // own HTTP cache, which is how v9 first installed carrying the OLD marks.js
        // even though the corrected file was already being served. MEASURED 23 Sep 2026:
        // cache rule-shelf-v9 held marks.js WITHOUT the fix while a no-store fetch of the
        // same URL returned it WITH the fix. Bumping the version is not enough on its own.
        return c.add(new Request(u, { cache: "reload" })).catch(function () {
          return c.add(u).catch(function () {});
        });
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) {
        return k.indexOf("rule-shelf-") === 0 && k !== CACHE;
      }).map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (event) {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;

  // index.html network first: a rule change must reach her the next time she
  // opens it online, not whenever the cache happens to be bumped. Falls back to
  // the cached copy the moment there is no signal.
  if (url.pathname.endsWith("/rules/") || url.pathname.endsWith("/index.html")) {
    event.respondWith(
      fetch(req).then(function (res) {
        const copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copy); });
        return res;
      }).catch(function () {
        return caches.match(req).then(function (hit) {
          return hit || caches.match("./index.html");
        });
      })
    );
    return;
  }

  event.respondWith(
    caches.match(req).then(function (hit) {
      return hit || fetch(req).then(function (res) {
        const copy = res.clone();
        caches.open(CACHE).then(function (c) { c.put(req, copy); });
        return res;
      });
    }).catch(function () { return caches.match("./index.html"); })
  );
});
