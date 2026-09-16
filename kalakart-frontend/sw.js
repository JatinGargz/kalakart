/* SHILP AI PWA — offline shell cache */
const CACHE = 'shilp-ai-v1';
const ASSETS = ['./index.html', './style.css', './app.js', './manifest.json'];
self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)).then(() => self.skipWaiting()));
});
self.addEventListener('activate', e => { e.waitUntil(self.clients.claim()); });
self.addEventListener('fetch', e => {
  if (e.request.url.includes('127.0.0.1:8000') || e.request.url.includes('/api/')) return; // never cache API
  e.respondWith(caches.match(e.request).then(hit => hit || fetch(e.request).catch(() => caches.match('./index.html'))));
});
