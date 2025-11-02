// Service Worker for Earplugs & Memories PWA
// Version: 1.0.18

const CACHE_NAME = 'earplugs-memories-v18';
const DATA_CACHE_NAME = 'earplugs-memories-data-v18';

// Files to cache immediately on install
const STATIC_CACHE_URLS = [
  '/',
  '/index.html',
  '/concerts.html',
  '/concert.html',
  '/artists.html',
  '/artist.html',
  '/venues.html',
  '/venue.html',
  '/songs.html',
  '/help.html',
  '/add-concert.html',
  '/admin-setlists.html',
  '/privacy.html',
  '/data-deletion.html',
  '/js/firebase-config.js',
  '/js/auth.js',
  '/js/main.js',
  '/js/concerts.js',
  '/js/concert.js',
  '/js/concert-photos.js',
  '/js/concert-notes.js',
  '/js/artist.js',
  '/js/venue.js',
  '/js/songs.js',
  '/js/setlist-submission.js',
  '/favicon.svg',
  '/manifest.json'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[ServiceWorker] Installing...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[ServiceWorker] Caching static assets');
        return cache.addAll(STATIC_CACHE_URLS);
      })
      .then(() => {
        console.log('[ServiceWorker] Skip waiting');
        return self.skipWaiting();
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[ServiceWorker] Activating...');

  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME && cacheName !== DATA_CACHE_NAME) {
            console.log('[ServiceWorker] Removing old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => {
      console.log('[ServiceWorker] Claiming clients');
      return self.clients.claim();
    })
  );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // Handle data JSON files with network-first strategy (always try to get fresh data)
  if (url.pathname.startsWith('/data/')) {
    event.respondWith(
      caches.open(DATA_CACHE_NAME).then((cache) => {
        return fetch(request)
          .then((response) => {
            // Cache the fresh data
            if (response.status === 200) {
              cache.put(request, response.clone());
            }
            return response;
          })
          .catch(() => {
            // If network fails, try to serve from cache
            return cache.match(request).then((cachedResponse) => {
              if (cachedResponse) {
                console.log('[ServiceWorker] Serving data from cache (offline):', url.pathname);
                return cachedResponse;
              }
              // Return offline page or error response
              return new Response(
                JSON.stringify({ error: 'Offline', message: 'Data not available offline' }),
                {
                  headers: { 'Content-Type': 'application/json' },
                  status: 503
                }
              );
            });
          });
      })
    );
    return;
  }

  // Handle Firebase/external API calls
  if (
    url.hostname.includes('firebase') ||
    url.hostname.includes('google') ||
    url.hostname.includes('gstatic')
  ) {
    event.respondWith(
      fetch(request).catch(() => {
        // If Firebase is offline, return error
        return new Response('Service Unavailable', { status: 503 });
      })
    );
    return;
  }

  // For all other requests, use cache-first strategy
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        // Return cached version and update cache in background
        fetch(request).then((response) => {
          if (response.status === 200) {
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, response);
            });
          }
        }).catch(() => {
          // Silently fail background update
        });
        return cachedResponse;
      }

      // Not in cache, fetch from network
      return fetch(request).then((response) => {
        // Cache successful responses
        if (response.status === 200) {
          const responseToCache = response.clone();
          caches.open(CACHE_NAME).then((cache) => {
            cache.put(request, responseToCache);
          });
        }
        return response;
      }).catch(() => {
        // Return offline page for HTML requests
        if (request.headers.get('accept').includes('text/html')) {
          return caches.match('/index.html');
        }
        return new Response('Offline', { status: 503 });
      });
    })
  );
});

// Handle messages from clients
self.addEventListener('message', (event) => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      }).then(() => {
        return self.clients.matchAll();
      }).then((clients) => {
        clients.forEach((client) => {
          client.postMessage({ type: 'CACHE_CLEARED' });
        });
      })
    );
  }
});

// Background sync for offline actions (future enhancement)
self.addEventListener('sync', (event) => {
  console.log('[ServiceWorker] Background sync:', event.tag);

  if (event.tag === 'sync-photos') {
    event.waitUntil(syncPhotos());
  }

  if (event.tag === 'sync-comments') {
    event.waitUntil(syncComments());
  }
});

// Placeholder functions for future offline sync
async function syncPhotos() {
  console.log('[ServiceWorker] Syncing offline photos...');
  // TODO: Implement offline photo upload queue
}

async function syncComments() {
  console.log('[ServiceWorker] Syncing offline comments...');
  // TODO: Implement offline comment queue
}
