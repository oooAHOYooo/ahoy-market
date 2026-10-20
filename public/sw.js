const SHELL_CACHE = 'ahoy-market-shell-v1';
const VAULT_CACHE = 'ahoy-vault-audio-v1';

const SHELL_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/ahoy-wordmark.png',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => {
      return cache.addAll(SHELL_ASSETS).catch((err) => {
        console.warn('[SW] Pre-caching partial failure:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== SHELL_CACHE && key !== VAULT_CACHE) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // 1. Navigation requests: Network-first, fallback to cached index.html shell
  if (request.mode === 'navigate') {
    event.respondWith(
      fetch(request).catch(async () => {
        const cached = await caches.match('/index.html') || await caches.match('/');
        return cached || new Response('Offline', { status: 503, statusText: 'Offline' });
      })
    );
    return;
  }

  // 2. Audio Vault: Check if audio track is cached in local offline vault
  if (url.pathname.startsWith('/api/download/') || url.pathname.endsWith('.mp3')) {
    event.respondWith(
      caches.open(VAULT_CACHE).then(async (vault) => {
        const cachedAudio = await vault.match(request);
        if (cachedAudio) {
          return cachedAudio;
        }
        return fetch(request).catch(() => {
          return new Response('Audio file not found in offline vault', { status: 404 });
        });
      })
    );
    return;
  }

  // 3. Static assets: Cache-first with background network update
  if (
    url.pathname.endsWith('.png') ||
    url.pathname.endsWith('.jpg') ||
    url.pathname.endsWith('.svg') ||
    url.pathname.endsWith('.ico') ||
    url.hostname.includes('fonts.gstatic.com') ||
    url.hostname.includes('fonts.googleapis.com')
  ) {
    event.respondWith(
      caches.match(request).then((cached) => {
        if (cached) return cached;
        return fetch(request).then((response) => {
          if (response && response.status === 200) {
            const clone = response.clone();
            caches.open(SHELL_CACHE).then((cache) => cache.put(request, clone));
          }
          return response;
        }).catch(() => cached);
      })
    );
    return;
  }

  // 4. Default: Fetch directly from network
  event.respondWith(fetch(request));
});
