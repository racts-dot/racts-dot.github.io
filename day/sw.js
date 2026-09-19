/* The Day — offline shell only. The FEED is never served from the cache, because a
 * stale number looks exactly like a fresh one and that mistake is in the lessons file.
 * The page itself, its icons and the shared scripts are cached so it opens on a train. */
var CACHE = "day-v1";
var SHELL = ["/day/", "/day/index.html", "/day/manifest.webmanifest",
             "/day/icon-192.png", "/textsize.js", "/feedback.js"];
self.addEventListener("install", function(e){
  e.waitUntil(caches.open(CACHE).then(function(c){ return c.addAll(SHELL); }).then(function(){
    return self.skipWaiting(); }));
});
self.addEventListener("activate", function(e){
  e.waitUntil(caches.keys().then(function(ks){
    return Promise.all(ks.map(function(k){ return k === CACHE ? null : caches.delete(k); }));
  }).then(function(){ return self.clients.claim(); }));
});
self.addEventListener("fetch", function(e){
  var url = new URL(e.request.url);
  if(e.request.method !== "GET" || url.origin !== location.origin) return;
  if(url.pathname.indexOf("/day/stream.json") === 0) return;      // always the network
  e.respondWith(
    fetch(e.request).then(function(r){
      var copy = r.clone();
      caches.open(CACHE).then(function(c){ c.put(e.request, copy); });
      return r;
    }).catch(function(){ return caches.match(e.request); })
  );
});
