// Pakistan Fast News — service worker.
// HTML pages: network-first (fresh headlines when online, cached copy offline).
// Static assets (CSS/JS/logos): stale-while-revalidate. External APIs are never cached.
var CACHE = "pfn-v1";
var ASSETS = ["styles.css", "script.js", "favicon.svg", "logo-dawn.png", "logo-ary.svg", "logo-bbc.gif", "logo-thenews.svg", "logo-urdu-dawn.png", "logo-urdu-ary.png", "logo-urdu-express.png", "logo-urdu-bbc.png"];
self.addEventListener("install", function (e) {
  e.waitUntil(caches.open(CACHE).then(function (c) { return c.addAll(ASSETS); }).then(function () { return self.skipWaiting(); }));
});
self.addEventListener("activate", function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});
self.addEventListener("fetch", function (e) {
  if (e.request.method !== "GET") return;
  var url = new URL(e.request.url);
  if (url.origin !== self.location.origin) return;
  var isPage = e.request.mode === "navigate" || url.pathname.endsWith(".html") || url.pathname.endsWith("/");
  if (isPage) {
    e.respondWith(fetch(e.request).then(function (r) {
      var c = r.clone();
      caches.open(CACHE).then(function (cache) { cache.put(e.request, c); });
      return r;
    }).catch(function () { return caches.match(e.request); }));
  } else {
    e.respondWith(caches.match(e.request).then(function (hit) {
      var net = fetch(e.request).then(function (r) {
        if (r.ok) {
          var c = r.clone();
          caches.open(CACHE).then(function (cache) { cache.put(e.request, c); });
        }
        return r;
      }).catch(function () { return hit; });
      return hit || net;
    }));
  }
});
