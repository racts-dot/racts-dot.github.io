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
const CACHE = "rule-shelf-v2";
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
  "../pull.js"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (c) {
      // addAll fails the whole install if ONE file 404s, and the kit scripts sit
      // a level up where a path can drift. Add them one at a time so a missing
      // script costs that script, not the entire offline copy.
      return Promise.all(SHELL.map(function (u) {
        return c.add(u).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) {
        return k !== CACHE;
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
