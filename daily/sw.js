/* Daily Chapter has moved to /daily-chapter/ (her pick, 23 Sep 2026: "You open
   racts-dot.github.io/daily/ and land on /daily-chapter/").

   This file replaces the old /daily/ worker, which kept the old page in its cache.
   A phone that still has the old worker installed fetches this one on its next
   visit. It then:
     1. takes over at once (skipWaiting), without waiting for every tab to close;
     2. deletes the caches that belonged to /daily/ - and ONLY those. The cache
        store is shared with /daily-chapter/ (same site, and both apps name their
        caches "daily-chapter-vNN"), so a cache that holds /daily-chapter/ files
        loses just its /daily/ entries and is otherwise left alone;
     3. unregisters itself, so nothing is cached for /daily/ ever again;
     4. sends every open /daily/ window to /daily-chapter/, keeping ?query and #hash.
   It has no fetch handler, so while it lives every request goes to the network.
   Her writing is in localStorage, which this does not touch; both apps read the
   same "bibleDaily.v1." keys, so it is all there in /daily-chapter/. */

const TARGET = "/daily-chapter/";

self.addEventListener("install", function () {
  self.skipWaiting();
});

function under(path, prefix) { return path === prefix.slice(0, -1) || path.indexOf(prefix) === 0; }

function clearOwnCaches() {
  const mine = new URL(self.registration.scope).pathname;   /* "/daily/" */
  return caches.keys().then(function (names) {
    return Promise.all(names.map(function (name) {
      return caches.open(name).then(function (cache) {
        return cache.keys().then(function (reqs) {
          const other = reqs.some(function (r) { return under(new URL(r.url).pathname, TARGET); });
          if (!other) {
            /* Nothing of /daily-chapter/ in it. Delete it only if it is /daily/'s. */
            const ours = reqs.some(function (r) { const u = new URL(r.url); return u.origin === self.location.origin && under(u.pathname, mine); });
            return ours ? caches.delete(name) : false;
          }
          /* Shared cache: remove only the /daily/ pages and files. */
          return Promise.all(reqs.filter(function (r) {
            const u = new URL(r.url);
            return u.origin === self.location.origin && under(u.pathname, mine);
          }).map(function (r) { return cache.delete(r); }));
        });
      });
    }));
  });
}

function destination(clientUrl) {
  const from = new URL(clientUrl);
  return new URL(TARGET + from.search + from.hash, self.location.origin).href;
}

self.addEventListener("activate", function (event) {
  event.waitUntil(
    self.clients.claim().catch(function () {})
      .then(clearOwnCaches).catch(function () {})
      .then(function () { return self.clients.matchAll({ type: "window", includeUncontrolled: true }); })
      .then(function (wins) {
        return self.registration.unregister().catch(function () {}).then(function () {
          const mine = new URL(self.registration.scope).pathname;
          return Promise.all(wins.filter(function (w) {
            return under(new URL(w.url).pathname, mine);
          }).map(function (w) {
            return w.navigate(destination(w.url)).catch(function () {});
          }));
        });
      })
      .catch(function () {})
  );
});
