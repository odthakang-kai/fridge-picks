/* Floor Copilot service worker. Built by tools/build.py; do not edit app/sw.js by hand.
   The page itself is network-first (fresh prices when online, cached copy when not).
   Everything else is cache-first. */
const VERSION = "__VERSION__";
const CACHE = "fc-" + VERSION;
const SHELL = ["./", "manifest.webmanifest", "icon-192.png", "icon-512.png", "icon-maskable-512.png",
               "apple-touch-icon.png", "vendor/zxing-reader.js", "vendor/zxing_reader.wasm"];

self.addEventListener("install", e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL.map(u => new Request(u, {cache: "reload"})))).then(() => self.skipWaiting()));
});

self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("fc-") && k !== CACHE).map(k => caches.delete(k))))
    .then(() => self.clients.claim()));
});

function isPage(req) {
  if (req.mode === "navigate") return true;
  const p = new URL(req.url).pathname;
  return p.endsWith("/app/") || p.endsWith("/app/index.html");
}

async function pageFirst(req) {
  const cache = await caches.open(CACHE);
  const net = fetch(req, {cache: "no-store"}).then(r => {
    if (r && r.ok) cache.put("./", r.clone());
    return r;
  });
  const timeout = new Promise(res => setTimeout(() => res(null), 3500));
  try {
    const r = await Promise.race([net, timeout]);
    if (r && r.ok) return r;
  } catch (e) {}
  const hit = await cache.match("./");
  if (hit) return hit;
  return net;
}

async function cacheFirst(req) {
  const hit = await caches.match(req, {ignoreSearch: true});
  if (hit) return hit;
  const r = await fetch(req);
  if (r && r.ok && new URL(req.url).origin === location.origin) {
    const c = await caches.open(CACHE);
    c.put(req, r.clone());
  }
  return r;
}

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET") return;
  if (new URL(req.url).origin !== location.origin) return;
  e.respondWith(isPage(req) ? pageFirst(req) : cacheFirst(req));
});
