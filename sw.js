// Forkful service worker: keeps the app, the CIQUAL table and fonts available offline.
// Bump VERSION whenever a cached file changes so phones pick up the new copy.
const VERSION = "forkful-v3";
const SHELL = [
  "./",
  "index.html",
  "manifest.webmanifest",
  "data/ciqual.json",
  "icons/icon.svg",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "icons/icon-180.png"
];
// Third-party files that never change once loaded: cache on first use.
const RUNTIME_HOSTS = ["fonts.googleapis.com", "fonts.gstatic.com", "cdn.jsdelivr.net"];

self.addEventListener("install", event => {
  event.waitUntil(caches.open(VERSION).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", event => {
  event.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== VERSION).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", event => {
  const req = event.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);

  // App files: network first so updates show up, cache when offline
  if (url.origin === self.location.origin && !url.pathname.includes("/off/")) {
    event.respondWith(
      fetch(req)
        .then(res => {
          if (res.ok) { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
          return res;
        })
        .catch(() => caches.match(req, { ignoreSearch: true }).then(hit => hit || caches.match("index.html")))
    );
    return;
  }

  // Fonts and the barcode library: cache first
  if (RUNTIME_HOSTS.includes(url.hostname)) {
    event.respondWith(
      caches.match(req).then(hit => hit || fetch(req).then(res => {
        if (res.ok || res.type === "opaque") { const copy = res.clone(); caches.open(VERSION).then(c => c.put(req, copy)); }
        return res;
      }))
    );
  }
  // Everything else (USDA, Open Food Facts) goes straight to the network.
});
