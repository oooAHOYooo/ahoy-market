const SHELL_CACHE = 'ahoy-market-shell-v1';
const VAULT_CACHE = 'ahoy-vault-audio-v1';

const SHELL_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  '/ahoy-wordmark.png',
  '/icon-192.png',
  '/icon-512.png',
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

// Helper: Handle Range requests for cached audio in CacheStorage
// Enables Safari/iOS WebKit and Chrome to stream, scrub, and play offline audio cleanly
async function handleAudioRangeRequest(request, cachedResponse) {
  const rangeHeader = request.headers.get('Range');
  if (!rangeHeader) {
    return cachedResponse;
  }

  const arrayBuffer = await cachedResponse.arrayBuffer();
  const total = arrayBuffer.byteLength;
  const bytesMatch = /^bytes\s*=\s*(\d*)\s*-\s*(\d*)$/i.exec(rangeHeader);

  if (!bytesMatch) {
    return cachedResponse;
  }

  let start = bytesMatch[1] ? parseInt(bytesMatch[1], 10) : 0;
  let end = bytesMatch[2] ? parseInt(bytesMatch[2], 10) : total - 1;

  if (start >= total || end >= total || start > end) {
    return new Response(null, {
      status: 416,
      statusText: 'Range Not Satisfiable',
      headers: {
        'Content-Range': `bytes */${total}`,
        'Accept-Ranges': 'bytes',
      },
    });
  }

  const sliced = arrayBuffer.slice(start, end + 1);
  const contentType = cachedResponse.headers.get('Content-Type') || 'audio/mpeg';

  return new Response(sliced, {
    status: 206,
    statusText: 'Partial Content',
    headers: {
      'Content-Type': contentType,
      'Content-Range': `bytes ${start}-${end}/${total}`,
      'Content-Length': String(sliced.byteLength),
      'Accept-Ranges': 'bytes',
      'Cache-Control': 'public, max-age=31536000',
    },
  });
}

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
        // Try exact match, then match ignoring search query (?ahoy_id=...), then pathname
        const cachedAudio = (await vault.match(request, { ignoreSearch: true })) ||
                            (await vault.match(url.pathname, { ignoreSearch: true }));
        if (cachedAudio) {
          return handleAudioRangeRequest(request, cachedAudio);
        }
        return fetch(request).catch(() => {
          return new Response('Audio file not found in offline vault', { status: 404 });
        });
      })
    );
    return;
  }

  // 3. API market latest state: Network-first with shell cache fallback
  if (url.pathname === '/api/market/latest') {
    event.respondWith(
      fetch(request).then((response) => {
        if (response && response.status === 200) {
          const clone = response.clone();
          caches.open(SHELL_CACHE).then((cache) => cache.put(request, clone));
        }
        return response;
      }).catch(async () => {
        const cached = await caches.match(request);
        if (cached) return cached;
        return new Response(JSON.stringify({ error: 'offline', releases: [], artists: [] }), {
          status: 200,
          headers: { 'Content-Type': 'application/json' },
        });
      })
    );
    return;
  }

  // 4. Static assets: Cache-first with background network update
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

  // 5. Default: Fetch directly from network
  event.respondWith(fetch(request));
});
