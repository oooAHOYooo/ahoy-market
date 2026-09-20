/**
 * API client for the Ahoy backend.
 *
 * Resolution order:
 * - VITE_API_BASE (explicit override, can be "" for same-origin)
 * - Dev on Vite port: use local Flask (same host, port VITE_API_PORT or 5002)
 * - Otherwise: same-origin (production/Flask-served SPA)
 */

const ENV_API_BASE = import.meta.env.VITE_API_BASE
const ENV_API_PORT = import.meta.env.VITE_API_PORT
const PRODUCTION_API_BASE = 'https://app.ahoy.ooo'

function resolveApiBase() {
  if (ENV_API_BASE !== undefined) return ENV_API_BASE
  if (typeof window === 'undefined') return ''
  const cap = window.Capacitor
  if (cap && typeof cap.isNativePlatform === 'function' && cap.isNativePlatform()) {
    return PRODUCTION_API_BASE
  }
  const { hostname, port, protocol } = window.location
  if (import.meta.env.DEV && (port === '5173' || port === '4173')) {
    const apiPort = ENV_API_PORT || '5002'
    return `${protocol}//${hostname}:${apiPort}`
  }
  return ''
}

const API_BASE = resolveApiBase()

/**
 * Resolve a path against the configured API base. Use for raw fetch()/XHR
 * calls that can't go through apiFetch (FormData uploads, streams, etc.).
 * Relative paths would hit capacitor://localhost in bundled Capacitor builds
 * and fail silently — always route through this.
 */
export function apiUrl(path) {
  const base = (API_BASE === '' || API_BASE === undefined) ? '' : API_BASE.replace(/\/$/, '')
  return base ? `${base}${path}` : path
}

/**
 * Fetch JSON from an API endpoint with caching support.
 * @param {string} path - API path like '/api/music'
 * @param {object} options - fetch options
 * @returns {Promise<any>} parsed JSON
 */
export async function apiFetch(path, options = {}) {
  const url = apiUrl(path)
  const noStorePath = path === '/api/shows' || path.startsWith('/api/show/')

  const response = await fetch(url, {
    ...options,
    cache: options.cache ?? (noStorePath ? 'no-store' : 'default'),
    credentials: 'include', // send/receive session cookies for auth
    headers: {
      'Accept': 'application/json',
      ...options.headers,
    },
  })

  if (!response.ok) {
    if (response.status === 401 && !path.startsWith('/api/auth/') && !path.startsWith('/api/listening/')) {
      // Session expired or invalid (auth/listening endpoints handle their own state)
      if (typeof window !== 'undefined') {
        window.dispatchEvent(new CustomEvent('ahoy:session-expired'))
      }
    }
    
    // Try to parse error body
    let errorData = null
    try {
      errorData = await response.json()
    } catch { /* not json */ }

    const error = new Error(errorData?.message || errorData?.error || `API ${path}: ${response.status}`)
    error.status = response.status
    error.data = errorData
    throw error
  }

  return response.json()
}

/**
 * Map of API endpoints to their static JSON file fallbacks.
 * Used when offline and localStorage cache is unavailable.
 */
const STATIC_FALLBACKS = {
  '/api/artists': '/static/data/artists.json',
  '/api/shows': '/static/data/events.json',
  '/api/podcasts': '/static/data/podcastCollection.json',
  '/api/events': '/static/data/events.json',
  '/api/whats-new': '/static/data/whats_new.json',
  '/api/music': '/static/data/music.json',
  '/api/studio': '/static/data/studio.json',
}

const CACHE_TTLS = {
  '/api/whats-new': 0,
  '/api/artists': 60 * 1000,
  '/api/music': 60 * 1000,
  '/api/shows': 0,
  '/api/events': 120 * 1000,
  '/api/podcasts': 120 * 1000,
  '/api/studio': 300 * 1000,
}

/**
 * Fetch with multi-tier offline support and TTL cache.
 * Tier 1: Fresh cache (within TTL)
 * Tier 2: Network (live API)
 * Tier 3: Stale localStorage cache (when offline)
 * Tier 4: Static JSON fallback (baked into app for offline browsing)
 */
export async function apiFetchCached(path, cacheKey = null, ttlMs = 300000) { // 5 min default
  const effectiveTtl = CACHE_TTLS[path] ?? ttlMs
  const key = cacheKey || `ahoy:${path}`

  // Tier 1: Check for fresh cache
  try {
    if (effectiveTtl <= 0) throw new Error('cache disabled')
    const cached = localStorage.getItem(key)
    if (cached) {
      const { data, ts } = JSON.parse(cached)
      const now = Date.now()
      if (ts && (now - ts) < effectiveTtl) {
        // Cache is fresh, return it
        return data
      }
    }
  } catch (e) { /* parse error, ignore cache */ }

  try {
    // Tier 2: Network fetch
    const data = await apiFetch(path)
    
    // Save to cache for next time
    try {
      if (effectiveTtl > 0) {
        localStorage.setItem(key, JSON.stringify({ data, ts: Date.now() }))
      }
    } catch (e) { /* storage full, ignore */ }
    
    return data
  } catch (e) {
    // Tier 3: Network failed — return any available cache (even if stale)
    const cached = localStorage.getItem(key)
    if (cached) {
      const { data } = JSON.parse(cached)
      return data
    }

    // Tier 4: Try static JSON fallback (offline browsing)
    const staticPath = STATIC_FALLBACKS[path]
    if (staticPath) {
      try {
        const res = await fetch(staticPath)
        if (res.ok) {
          const data = await res.json()
          return data
        }
      } catch (e) { /* static fallback fetch failed, continue */ }
    }

    throw e
  }
}
