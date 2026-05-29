const CACHE_NAME = 'sem-express-v1';
const API_URL = '/v1';

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll(['/inspector/'])));
});

self.addEventListener('fetch', (e) => {
  if (e.request.url.includes('/v1/')) {
    e.respondWith(
      fetch(e.request).catch(() => {
        return new Response(JSON.stringify({error: 'offline', detail: 'Sin conexion. Los datos se sincronizaran al reconectar.'}), {
          status: 503,
          headers: {'Content-Type': 'application/json'}
        });
      })
    );
  } else {
    e.respondWith(caches.match(e.request).then(r => r || fetch(e.request)));
  }
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))));
});
