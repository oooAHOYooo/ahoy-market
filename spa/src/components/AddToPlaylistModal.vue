<template>
  <Teleport to="body">
    <div v-if="addToPlaylist.showModal.value" class="modal-overlay" @click="addToPlaylist.close()">
      <div class="modal add-to-playlist-modal" role="dialog" aria-modal="true" aria-label="Add to playlist" tabindex="-1" @click.stop>
      <div class="modal-header">
        <h3>Add to playlist</h3>
        <button type="button" class="modal-close" aria-label="Close" @click="addToPlaylist.close()">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div v-if="track" class="modal-track">
        {{ track.title }}
        <span class="modal-track-artist">{{ track.artist || track.host }}</span>
      </div>
      <div v-if="!addToPlaylist.auth.isLoggedIn.value" class="modal-guest">
        <p>Sign in to add tracks to playlists.</p>
        <router-link to="/login" class="btn-primary" @click="addToPlaylist.close()">Sign in</router-link>
      </div>
      <div v-else class="modal-body">
        <div v-if="statusMessage" class="modal-status" :class="statusType">
          <i :class="statusType === 'success' ? 'fas fa-check' : 'fas fa-exclamation-triangle'"></i>
          <span>{{ statusMessage }}</span>
        </div>
        <div class="modal-create">
          <div class="modal-create-copy">
            <strong>New playlist</strong>
            <span>Create one from this track, then add more later.</span>
          </div>
          <div class="modal-create-form">
            <input
              v-model="newPlaylistName"
              type="text"
              class="playlist-name-input"
              placeholder="Playlist name"
              @keydown.enter.prevent="createPlaylist"
            />
            <button
              type="button"
              class="playlist-create-btn"
              :disabled="!newPlaylistName.trim() || creating"
              @click="createPlaylist"
            >
              <i v-if="creating" class="fas fa-spinner fa-spin" aria-hidden="true"></i>
              <i v-else class="fas fa-plus" aria-hidden="true"></i>
              Save playlist
            </button>
          </div>
          <p class="modal-create-hint">Press Enter to save, or pick an existing playlist below.</p>
        </div>
        <div v-if="loading" class="modal-loading"><i class="fas fa-spinner fa-spin"></i> Loading playlists…</div>
        <template v-else-if="playlists.length">
          <button
            v-for="p in playlists"
            :key="p.id"
            type="button"
            class="playlist-row"
            :class="{ 'is-selected': highlightedPlaylistId === p.id }"
            :aria-label="`Add to playlist: ${p.name}`"
            @click="addTo(p.id)"
          >
            <i class="fas fa-list-ul"></i>
            <span>{{ p.name }}</span>
          </button>
        </template>
        <p v-else class="modal-empty">No playlists yet. <router-link to="/playlists" @click="addToPlaylist.close()">Create one</router-link></p>
        <div class="modal-actions">
          <button type="button" class="modal-done-btn" @click="addToPlaylist.close()">Close</button>
        </div>
      </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useAddToPlaylist } from '../composables/useAddToPlaylist'

const addToPlaylist = useAddToPlaylist()
const playlists = ref([])
const loading = ref(false)
const creating = ref(false)
const newPlaylistName = ref('')
const statusMessage = ref('')
const statusType = ref('success')
const highlightedPlaylistId = ref(null)

const track = computed(() => addToPlaylist.trackToAdd.value)

function toMediaType(item) {
  const t = (item?.type || item?._type || 'track').toLowerCase()
  if (t === 'artist') return 'artist'
  if (t === 'show' || t === 'video') return 'show'
  if (t === 'podcast' || t === 'episode') return 'clip'
  return 'music'
}

async function loadPlaylists() {
  if (!addToPlaylist.auth.isLoggedIn.value) return
  loading.value = true
  try {
    playlists.value = await addToPlaylist.playlistsApi.list()
  } finally {
    loading.value = false
  }
}

async function createPlaylist() {
  const name = newPlaylistName.value.trim()
  if (!name || creating.value) return
  creating.value = true
  try {
    const created = await addToPlaylist.playlistsApi.create(name)
    playlists.value = [created, ...playlists.value.filter((p) => p.id !== created.id)]
    const t = track.value
    if (t) {
      const mediaId = String(t.id ?? t.slug ?? '')
      const mediaType = toMediaType(t)
      await addToPlaylist.playlistsApi.addItem(created.id, mediaId, mediaType)
    }
    highlightedPlaylistId.value = created.id
    newPlaylistName.value = ''
    statusType.value = 'success'
    statusMessage.value = 'Playlist saved and track added'
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Playlist saved', type: 'success' } }))
    setTimeout(() => addToPlaylist.close(), 700)
  } catch {
    statusType.value = 'error'
    statusMessage.value = 'Could not save playlist'
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Failed to save playlist', type: 'error' } }))
  } finally {
    creating.value = false
  }
}

async function addTo(playlistId) {
  const t = track.value
  if (!t) return
  const mediaId = String(t.id ?? t.slug ?? '')
  const mediaType = toMediaType(t)
  try {
    await addToPlaylist.playlistsApi.addItem(playlistId, mediaId, mediaType)
    const selected = playlists.value.find((p) => p.id === playlistId)
    highlightedPlaylistId.value = playlistId
    statusType.value = 'success'
    statusMessage.value = selected ? `Added to ${selected.name}` : 'Added to playlist'
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Added to playlist', type: 'success' } }))
    setTimeout(() => addToPlaylist.close(), 550)
  } catch (e) {
    statusType.value = 'error'
    statusMessage.value = 'Could not add to playlist'
    const msg = e?.status === 409 || (e?.message || '').includes('already_in_playlist')
      ? 'Already in this playlist'
      : 'Failed to add'
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: msg, type: 'error' } }))
  }
}

watch(() => addToPlaylist.showModal.value, (open) => {
  if (open) loadPlaylists()
  if (!open) {
    newPlaylistName.value = ''
    statusMessage.value = ''
    highlightedPlaylistId.value = null
  }
})

watch(() => addToPlaylist.showModal.value, async (open) => {
  if (open) {
    await nextTick()
    const el = document.querySelector('.playlist-name-input')
    if (el && typeof el.focus === 'function') el.focus()
  }
})

function onKeydown(event) {
  if (event.key === 'Escape' && addToPlaylist.showModal.value) {
    addToPlaylist.close()
  }
}

onMounted(() => window.addEventListener('keydown', onKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKeydown))
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 20px;
}
.add-to-playlist-modal {
  width: 100%;
  max-width: 360px;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  background: rgba(20, 20, 28, 0.98);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 16px;
}
.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(255,255,255,0.08);
}
.modal-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
}
.modal-close {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  color: var(--text-primary);
  width: 34px;
  height: 34px;
  border-radius: 10px;
  font-size: 16px;
  cursor: pointer;
}
.modal-close:hover { background: rgba(255,255,255,0.12); }
.modal-track {
  padding: 12px 20px;
  font-size: 14px;
  color: var(--text-primary);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.modal-track-artist {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 2px;
}
.modal-guest {
  padding: 24px 20px;
  text-align: center;
}
.modal-guest p {
  margin: 0 0 16px;
  color: var(--text-secondary);
}
.modal-body {
  padding: 12px 0;
  overflow-y: auto;
  flex: 1;
}
.modal-status {
  margin: 0 20px 10px;
  padding: 10px 12px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.modal-status.success {
  background: rgba(109, 220, 255, 0.12);
  color: #dff8ff;
  border: 1px solid rgba(109, 220, 255, 0.18);
}
.modal-status.error {
  background: rgba(255, 107, 107, 0.12);
  color: #ffdcdc;
  border: 1px solid rgba(255, 107, 107, 0.18);
}
.modal-create {
  margin: 0 20px 14px;
  padding: 14px;
  border-radius: 14px;
  background: linear-gradient(180deg, rgba(255, 214, 102, 0.12), rgba(255, 214, 102, 0.06));
  border: 1px solid rgba(255, 214, 102, 0.18);
}
.modal-create-copy {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: 12px;
}
.modal-create-copy strong {
  color: #f8d46b;
  font-size: 14px;
}
.modal-create-copy span {
  color: var(--text-secondary);
  font-size: 12px;
}
.modal-create-hint {
  margin: 10px 0 0;
  color: var(--text-secondary);
  font-size: 11px;
}
.modal-create-form {
  display: flex;
  gap: 8px;
}
.playlist-name-input {
  flex: 1;
  min-width: 0;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  color: var(--text-primary);
  padding: 10px 12px;
  font-size: 14px;
}
.playlist-create-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  border: none;
  border-radius: 12px;
  padding: 10px 14px;
  background: #f4c430;
  color: #1a1400;
  font-weight: 700;
  cursor: pointer;
}
.playlist-create-btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.btn-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  background: var(--accent-primary, #6ddcff);
  color: #111;
  text-decoration: none;
}
.modal-list {
  padding: 12px 0;
  overflow-y: auto;
  flex: 1;
}
.modal-loading, .modal-empty {
  padding: 20px;
  text-align: center;
  color: var(--text-secondary);
}
.modal-empty a {
  color: var(--accent-primary);
  text-decoration: none;
}
.modal-actions {
  padding: 0 20px 18px;
}
.modal-done-btn {
  width: 100%;
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.06);
  color: var(--text-primary);
  cursor: pointer;
}
.playlist-row {
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 20px;
  background: none;
  border: none;
  color: var(--text-primary);
  font-size: 15px;
  text-align: left;
  cursor: pointer;
  transition: background 0.2s;
}
.playlist-row:hover {
  background: rgba(255,255,255,0.06);
}
.playlist-row.is-selected {
  background: rgba(109, 220, 255, 0.12);
  border-left: 3px solid var(--accent-primary, #6ddcff);
  animation: row-pulse 0.35s ease-out;
}
.playlist-row i {
  color: #f4c430;
}

@keyframes row-pulse {
  from { transform: scale(0.99); }
  50% { transform: scale(1.01); }
  to { transform: scale(1); }
}
</style>
