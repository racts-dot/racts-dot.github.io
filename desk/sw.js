/* SELF-DESTRUCT, 13 September 2026.
   This worker used to cache the app for offline use. It cost more than it bought: it
   intercepted the byte-range requests iOS uses to play audio, which killed the recorded
   brief the moment she left the app, and it kept serving an old copy of the page so fixes
   did not appear. Both faults were invisible from the outside.
   It now removes itself and every cache it ever made. Left in place rather than deleted
   because a deleted file 404s and an already-installed worker would simply keep running. */
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    for (const k of await caches.keys()) await caches.delete(k);
    await self.registration.unregister();
    for (const c of await self.clients.matchAll({ type: "window" })) c.navigate(c.url);
  })());
});
/* No fetch handler at all: every request goes straight to the network. */
