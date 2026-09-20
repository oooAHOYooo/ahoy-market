/**
 * Playlists — list, create, get, update, delete, list items, add item, reorder, remove item.
 * Write ops require login. Reads work for public/unlisted playlists without auth.
 *
 * visibility: 'private' | 'public' | 'unlisted'
 *   private   — owner only
 *   public    — readable by anyone, appears in /playlists/public discovery feed
 *   unlisted  — readable by anyone with the link, not listed publicly
 */
import { ref } from 'vue'
import { apiFetch } from './useApi'

export function usePlaylists() {
  const loading = ref(false)
  const error = ref(null)

  async function list() {
    loading.value = true
    error.value = null
    try {
      const data = await apiFetch('/api/playlists')
      return data.items || []
    } catch (e) {
      error.value = e.message
      return []
    } finally {
      loading.value = false
    }
  }

  async function listPublic() {
    try {
      const data = await apiFetch('/api/playlists/public')
      return data.items || []
    } catch (e) {
      error.value = e.message
      return []
    }
  }

  async function create(name, { description = '', visibility = 'private' } = {}) {
    loading.value = true
    error.value = null
    try {
      return await apiFetch('/api/playlists', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: String(name).trim(), description, visibility }),
      })
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function get(playlistId) {
    try {
      return await apiFetch(`/api/playlists/${playlistId}`)
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  async function update(playlistId, patch) {
    // patch: { name?, description?, visibility? }
    try {
      return await apiFetch(`/api/playlists/${playlistId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(patch),
      })
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function remove(playlistId) {
    try {
      await apiFetch(`/api/playlists/${playlistId}`, { method: 'DELETE' })
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function listItems(playlistId) {
    try {
      const data = await apiFetch(`/api/playlists/${playlistId}/items`)
      return data.items || []
    } catch (e) {
      error.value = e.message
      return []
    }
  }

  /**
   * Resolve a list of playlist items to full media metadata in one call.
   * Returns a map keyed by "media_type:media_id".
   */
  async function resolveMedia(items) {
    if (!items.length) return {}
    try {
      const data = await apiFetch('/api/media/resolve', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ items: items.map((i) => ({ media_type: i.media_type, media_id: i.media_id })) }),
      })
      return data.resolved || {}
    } catch {
      return {}
    }
  }

  async function addItem(playlistId, mediaId, mediaType, position) {
    const body = { media_id: String(mediaId), media_type: mediaType }
    if (position != null) body.position = position
    try {
      return await apiFetch(`/api/playlists/${playlistId}/items`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      })
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  async function removeItem(playlistId, itemId) {
    try {
      await apiFetch(`/api/playlists/${playlistId}/items/${itemId}`, { method: 'DELETE' })
    } catch (e) {
      error.value = e.message
      throw e
    }
  }

  return {
    loading,
    error,
    list,
    listPublic,
    create,
    get,
    update,
    remove,
    listItems,
    resolveMedia,
    addItem,
    removeItem,
  }
}
