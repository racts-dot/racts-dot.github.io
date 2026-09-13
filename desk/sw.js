/* Rachie's Desk - offline shell.
   Caches the app itself so it opens with no signal. It never caches her data:
   the desk contents live in this device's own storage, not in here. */
const CACHE = "desk-v6";
const SHELL = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icon-192.png",
  "./icon-512.png",
  "./apple-touch-icon.png"
];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;

  /* HANDS OFF MEDIA. iOS plays audio by asking for byte ranges, and a service worker that
     answers those itself breaks playback the moment the app is left or the screen locks -
     which is exactly the fault this was causing. Anything under /audio/, and any request
     carrying a Range header, goes straight to the network untouched. Caching a 206 would
     throw anyway. */
  if (req.headers.has("range")) return;
  if (new URL(req.url).pathname.includes("/audio/")) return;
  if (req.destination === "audio" || req.destination === "video") return;
  // Network first so a rebuilt app arrives; cache is the fallback when there is no signal.
  e.respondWith(
    fetch(req)
      .then(res => {
        if (res && res.ok && new URL(req.url).origin === location.origin) {
          const copy = res.clone();
          caches.open(CACHE).then(c => c.put(req, copy));
        }
        return res;
      })
      .catch(() => caches.match(req).then(hit => hit || caches.match("./index.html")))
  );
});
