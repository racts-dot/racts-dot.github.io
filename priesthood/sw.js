/* Priest Hood service worker (written by site_shell.py).
   The page is fetched fresh first and kept for when there is no signal; everything else on this site is served
   from the cache first. Bump CACHE whenever index.html changes. */
const CACHE = "priesthood-v7";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./shell.js", "./pull.js", "./notes.js", "./notes.json", "../textsize.js", "../feedback.js", "../speak.js"];

self.addEventListener("install", function (event) {
  // cache: "reload" skips the browser's HTTP cache, so a new CACHE never stores the previous shell.js
  event.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(SHELL.map(function (u) { return new Request(u, { cache: "reload" }); })); }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener("activate", function (event) {
  event.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k.indexOf("priesthood-") === 0 && k !== CACHE; })
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
