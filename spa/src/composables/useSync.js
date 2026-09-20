/**
 * Sync status tracker for offline support.
 * Monitors online/offline state and triggers re-sync when coming back online.
 *
 * Status values:
 *   'synced' (🟢) — online, data is current
 *   'syncing' (🟡) — coming back online, refetching data
 *   'offline' (🔴) — no internet connection
 */

import { ref, watch, onMounted, onUnmounted } from 'vue'
import { apiFetchCached } from './useApi'

export function useSync({ onReconnect } = {}) {
  const status = ref('synced')
  const isOnline = ref(typeof navigator !== 'undefined' ? navigator.onLine : true)

  // Key endpoints to re-sync when coming back online
  const SYNC_ENDPOINTS = [
    '/api/artists',
    '/api/shows',
    '/api/podcasts',
    '/api/whats-new',
    '/api/music',
    '/api/studio',
    '/api/events'
  ]

  async function performSync() {
    status.value = 'syncing'
    let syncedCount = 0

    // Attempt to refresh key data sources in parallel
    const syncPromises = SYNC_ENDPOINTS.map(endpoint =>
      apiFetchCached(endpoint)
        .then(() => { syncedCount++ })
        .catch(() => { /* sync failed for this endpoint, but continue */ })
    )

    try {
      await Promise.all(syncPromises)
      status.value = 'synced'
    } catch (e) {
      // Even if some syncs fail, mark as synced if we got any data
      status.value = syncedCount > 0 ? 'synced' : 'offline'
    }
    onReconnect?.()
  }

  let reconnectTimer = null
  function onOnline() {
    isOnline.value = true
    clearTimeout(reconnectTimer)
    reconnectTimer = setTimeout(performSync, 1000)
  }

  function onOffline() {
    isOnline.value = false
    status.value = 'offline'
  }

  onMounted(() => {
    isOnline.value = navigator.onLine
    status.value = navigator.onLine ? 'synced' : 'offline'
    window.addEventListener('online', onOnline)
    window.addEventListener('offline', onOffline)
  })

  onUnmounted(() => {
    window.removeEventListener('online', onOnline)
    window.removeEventListener('offline', onOffline)
  })

  return {
    status,
    isOnline
  }
}
