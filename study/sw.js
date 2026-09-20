/* Study app service worker (written by publish_site.py).
   The page is fetched fresh first and kept for when there is no signal; the icons and shared bubbles are served from
   the cache first. CACHE changes whenever the page changes (it carries the page's hash), so phones pick up new cards. */
const CACHE = "study-92835598ee-n3";
const SHELL = ["./", "./index.html", "./manifest.webmanifest",
               "../textsize.js", "../feedback.js", "../speak.js", "../notion-sync.js"];

self.addEventListener("install", function (event) {
  event.waitUntil(caches.open(CACHE).then(function (c) {
    return c.addAll(SHELL.map(function (u) { return new Request(u, { cache: "reload" }); }));
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (event) {
  event.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k.indexOf("study-") === 0 && k !== CACHE; })
      .map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener("fetch", function (event) {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;
  const isPage = req.mode === "navigate" || req.destination === "document";
  if (isPage) {
    event.respondWith(fetch(req).then(function (res) {
      const copy = res.clone();
      caches.open(CACHE).then(function (c) { c.put(req, copy); });
      return res;
    }).catch(function () {
      return caches.match(req).then(function (hit) { return hit || caches.match("./index.html"); });
    }));
    return;
  }
  event.respondWith(caches.match(req).then(function (hit) {
    return hit || fetch(req).then(function (res) {
      const copy = res.clone();
      caches.open(CACHE).then(function (c) { c.put(req, copy); });
      return res;
    });
  }));
});
