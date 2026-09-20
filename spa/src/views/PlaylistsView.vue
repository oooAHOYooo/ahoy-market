<template>
  <div class="playlists-container">
    <ContentHeader
      kicker="Your Library"
      title="Playlists"
      subtitle="Curated collections and your custom mixes."
    />

    <div v-if="!auth.isLoggedIn.value" class="playlists-guest">
      <!-- Ghost create row -->
      <router-link to="/login" class="create-form guest-create-ghost">
        <div class="create-row">
          <div class="guest-input-shimmer shimmer"></div>
          <div class="guest-btn-shimmer shimmer"></div>
        </div>
      </router-link>

      <!-- Ghost playlist rows -->
      <div class="playlists-list">
        <router-link v-for="n in 4" :key="n" to="/login" class="playlist-card guest-playlist-card" :style="`--i:${n}`">
          <div class="playlist-card-link">
            <i class="fas fa-list-ul playlist-icon guest-icon"></i>
            <div class="playlist-info">
              <div class="guest-name-shimmer shimmer" :style="`width:${50 + n * 18}px`"></div>
            </div>
            <div class="guest-badge-shimmer shimmer"></div>
          </div>
        </router-link>
      </div>
    </div>

    <template v-else>
      <div class="create-form">
        <div class="create-row">
          <input
            v-model="newName"
            type="text"
            placeholder="New playlist name"
            class="playlist-input"
            @keyup.enter="createPlaylist"
          />
          <button
            type="button"
            class="playlist-btn primary"
            :disabled="!newName.trim() || playlistsApi.loading.value"
            @click="createPlaylist"
          >
            <i v-if="playlistsApi.loading.value" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-plus"></i>
            Create
          </button>
        </div>
        <div class="create-meta">
          <input
            v-model="newDescription"
            type="text"
            placeholder="Description (optional)"
            class="playlist-input desc-input"
          />
          <div class="visibility-select-wrap">
            <i :class="visibilityIcon(newVisibility)" class="vis-icon"></i>
            <select v-model="newVisibility" class="visibility-select">
              <option value="private">Private</option>
              <option value="unlisted">Unlisted</option>
              <option value="public">Public</option>
            </select>
          </div>
        </div>
      </div>

      <div v-if="playlistsApi.error.value" class="playlists-error">{{ playlistsApi.error.value }}</div>

      <div v-if="undoState" class="undo-banner">
        <span>Playlist deleted.</span>
        <button type="button" class="undo-btn" @click="undoDelete">Undo</button>
      </div>

      <div v-if="playlists.length === 0" class="playlists-empty-state">
        <div class="playlists-empty-card">
          <i class="fas fa-list-ul"></i>
          <h3>No playlists yet</h3>
          <p>Create one above, or start from the Add to playlist button on any track.</p>
        </div>
      </div>

      <div v-else class="playlists-list">
        <div v-for="p in playlists" :key="p.id" class="playlist-card">
          <router-link v-if="editingId !== p.id" :to="`/playlists/${p.id}`" class="playlist-card-link">
            <i class="fas fa-list-ul playlist-icon"></i>
            <div class="playlist-info">
              <span class="playlist-name">{{ p.name }}</span>
              <span v-if="p.description" class="playlist-desc">{{ p.description }}</span>
            </div>
            <span class="playlist-count-badge">{{ playlistCounts[p.id] ?? '...' }}</span>
          </router-link>
          <div v-else class="playlist-card-link playlist-editing">
            <i class="fas fa-list-ul playlist-icon"></i>
            <div class="playlist-info">
              <input
                v-model="editName"
                type="text"
                class="playlist-edit-input"
                placeholder="Playlist name"
                @keydown.enter.prevent="saveRename(p)"
              />
              <span v-if="p.description" class="playlist-desc">{{ p.description }}</span>
            </div>
            <div class="playlist-edit-actions">
              <button type="button" class="inline-action-btn save" @click.stop="saveRename(p)">
                Save
              </button>
              <button type="button" class="inline-action-btn cancel" @click.stop="cancelRename">
                Cancel
              </button>
            </div>
          </div>
          <div class="playlist-card-actions">
            <button
              type="button"
              class="visibility-btn edit-btn"
              :title="editingId === p.id ? 'Save playlist name' : 'Edit playlist name'"
              @click.stop="editingId === p.id ? saveRename(p) : startRename(p)"
            >
              <i :class="editingId === p.id ? 'fas fa-check' : 'fas fa-pen'"></i>
            </button>
            <button
              type="button"
              class="visibility-btn"
              :class="p.visibility || 'private'"
              :title="visibilityTitle(p.visibility)"
              @click.stop="cycleVisibility(p)"
            >
              <i :class="visibilityIcon(p.visibility)"></i>
            </button>
            <button
              type="button"
              class="visibility-btn delete-btn"
              title="Delete playlist"
              @click.stop="deletePlaylist(p)"
            >
              <i class="fas fa-trash"></i>
            </button>
            <i class="fas fa-chevron-right chevron"></i>
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuth } from '../composables/useAuth'
import { usePlaylists } from '../composables/usePlaylists'
import ContentHeader from '../components/ContentHeader.vue'

const auth = useAuth()
const playlistsApi = usePlaylists()
const playlists = ref([])
const newName = ref('')
const newDescription = ref('')
const newVisibility = ref('private')
const editingId = ref(null)
const editName = ref('')
const undoState = ref(null)
const playlistCounts = ref({})
let undoTimer = null

async function load() {
  const rows = await playlistsApi.list()
  playlists.value = rows
  const counts = await Promise.all(rows.map(async (playlist) => {
    const items = await playlistsApi.listItems(playlist.id)
    return [playlist.id, items.length]
  }))
  playlistCounts.value = Object.fromEntries(counts)
}

async function createPlaylist() {
  const name = newName.value.trim()
  if (!name) return
  try {
    const created = await playlistsApi.create(name, {
      description: newDescription.value.trim(),
      visibility: newVisibility.value,
    })
    playlists.value = [...playlists.value, created]
    playlistCounts.value = { ...playlistCounts.value, [created.id]: 0 }
    newName.value = ''
    newDescription.value = ''
    newVisibility.value = 'private'
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Playlist created', type: 'success' } }))
  } catch {
    //
  }
}

const VISIBILITY_CYCLE = ['private', 'unlisted', 'public']
const VISIBILITY_ICONS = { private: 'fas fa-lock', unlisted: 'fas fa-link', public: 'fas fa-globe' }
const VISIBILITY_TITLES = {
  private: 'Private — click for unlisted',
  unlisted: 'Unlisted (link only) — click for public',
  public: 'Public — click for private',
}

function visibilityIcon(v) { return VISIBILITY_ICONS[v] || VISIBILITY_ICONS.private }
function visibilityTitle(v) { return VISIBILITY_TITLES[v] || VISIBILITY_TITLES.private }

async function cycleVisibility(playlist) {
  const current = playlist.visibility || 'private'
  const next = VISIBILITY_CYCLE[(VISIBILITY_CYCLE.indexOf(current) + 1) % VISIBILITY_CYCLE.length]
  try {
    const updated = await playlistsApi.update(playlist.id, { visibility: next })
    const idx = playlists.value.findIndex((p) => p.id === playlist.id)
    if (idx !== -1) playlists.value[idx] = { ...playlists.value[idx], ...updated }
    const labels = { private: 'private', unlisted: 'unlisted (link only)', public: 'public' }
    window.dispatchEvent(new CustomEvent('ahoy:toast', {
      detail: { message: `Playlist is now ${labels[next]}`, type: 'success' }
    }))
  } catch {
    //
  }
}

function startRename(playlist) {
  editingId.value = playlist.id
  editName.value = playlist.name || ''
}

function cancelRename() {
  editingId.value = null
  editName.value = ''
}

async function saveRename(playlist) {
  const name = editName.value.trim()
  if (!name) return
  try {
    const updated = await playlistsApi.update(playlist.id, { name })
    const idx = playlists.value.findIndex((p) => p.id === playlist.id)
    if (idx !== -1) playlists.value[idx] = { ...playlists.value[idx], ...updated }
    cancelRename()
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Playlist updated', type: 'success' } }))
  } catch {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Failed to update playlist', type: 'error' } }))
  }
}

function onRenameKeydown(event) {
  if (event.key === 'Escape' && editingId.value) {
    cancelRename()
  }
}

async function deletePlaylist(playlist) {
  const ok = window.confirm(`Delete playlist "${playlist.name}"? This cannot be undone.`)
  if (!ok) return
  try {
    const idx = playlists.value.findIndex((p) => p.id === playlist.id)
    const removed = idx !== -1 ? playlists.value[idx] : playlist
    await playlistsApi.remove(playlist.id)
    playlists.value = playlists.value.filter((p) => p.id !== playlist.id)
    const nextCounts = { ...playlistCounts.value }
    delete nextCounts[playlist.id]
    playlistCounts.value = nextCounts
    undoState.value = { playlist: removed, index: idx }
    if (undoTimer) clearTimeout(undoTimer)
    undoTimer = setTimeout(() => {
      undoState.value = null
      undoTimer = null
    }, 5000)
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Playlist deleted', type: 'success' } }))
  } catch {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Failed to delete playlist', type: 'error' } }))
  }
}

async function undoDelete() {
  const state = undoState.value
  if (!state?.playlist) return
  try {
    const restored = await playlistsApi.create(state.playlist.name, {
      description: state.playlist.description || '',
      visibility: state.playlist.visibility || 'private',
    })
    const next = [...playlists.value]
    const insertAt = state.index >= 0 ? Math.min(state.index, next.length) : next.length
    next.splice(insertAt, 0, restored)
    playlists.value = next
    playlistCounts.value = { ...playlistCounts.value, [restored.id]: state.playlist.id ? 0 : 0 }
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Playlist restored', type: 'success' } }))
  } catch {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Could not restore playlist', type: 'error' } }))
  } finally {
    undoState.value = null
    if (undoTimer) clearTimeout(undoTimer)
    undoTimer = null
  }
}

onMounted(() => {
  if (auth.isLoggedIn.value) load()
  window.addEventListener('keydown', onRenameKeydown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', onRenameKeydown)
  if (undoTimer) clearTimeout(undoTimer)
})
</script>

<style scoped>
.playlists-guest {
  padding: 0 var(--mobile-gutter, 6px);
}
.guest-create-ghost {
  display: block;
  text-decoration: none;
  pointer-events: auto;
  margin-bottom: 20px;
}
.guest-input-shimmer {
  flex: 1;
  height: 40px;
  border-radius: 10px;
}
.guest-btn-shimmer {
  width: 80px;
  height: 40px;
  border-radius: 10px;
  flex-shrink: 0;
}
.guest-playlist-card {
  text-decoration: none;
  display: block;
  opacity: 0.55;
  animation-delay: calc(var(--i, 0) * 0.1s);
}
.guest-playlist-card .playlist-card-link {
  pointer-events: none;
}
.guest-icon {
  opacity: 0.2;
}
.guest-name-shimmer {
  height: 14px;
  border-radius: 7px;
}
.guest-badge-shimmer {
  width: 24px;
  height: 24px;
  border-radius: 12px;
  flex-shrink: 0;
}
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.shimmer {
  background: linear-gradient(
    90deg,
    rgba(255,255,255,0.05) 25%,
    rgba(255,255,255,0.1) 50%,
    rgba(255,255,255,0.05) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 2s infinite linear;
  animation-delay: calc(var(--i, 0) * 0.12s);
}
.account-btn.primary {
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
.create-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
  padding: 0 var(--mobile-gutter, 6px);
}
.create-row {
  display: flex;
  gap: 10px;
}
.create-meta {
  display: flex;
  gap: 8px;
}
.desc-input {
  flex: 1;
  font-size: 16px;
}
.visibility-select-wrap {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 0 12px;
}
.vis-icon {
  font-size: 13px;
  color: var(--text-secondary);
}
.visibility-select {
  background: none;
  border: none;
  color: var(--text-primary);
  font-size: 16px;
  cursor: pointer;
  padding: 10px 0;
  outline: none;
}
.playlist-input {
  flex: 1;
  padding: 10px 14px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 16px;
}
.playlist-btn {
  padding: 10px 18px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
.playlist-btn.primary {
  background: var(--accent-primary, #6ddcff);
  color: #111;
}
.playlists-error {
  color: #ff6b6b;
  font-size: 14px;
  margin-bottom: 12px;
  padding: 0 var(--mobile-gutter, 6px);
}
.undo-banner {
  margin: 0 var(--mobile-gutter, 6px) 12px;
  padding: 10px 12px;
  border-radius: 12px;
  background: rgba(109, 220, 255, 0.08);
  border: 1px solid rgba(109, 220, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--text-primary);
  font-size: 13px;
}
.undo-btn {
  border: none;
  border-radius: 999px;
  padding: 8px 12px;
  background: var(--accent-primary, #6ddcff);
  color: #111;
  font-weight: 700;
  cursor: pointer;
}
.playlists-empty-state {
  padding: 0 var(--mobile-gutter, 6px) 100px;
}
.playlists-empty-card {
  border: 1px dashed rgba(255,255,255,0.14);
  border-radius: 18px;
  padding: 28px 18px;
  text-align: center;
  background: rgba(255,255,255,0.03);
}
.playlists-empty-card i {
  font-size: 28px;
  color: #f4c430;
  margin-bottom: 10px;
}
.playlists-empty-card h3 {
  margin: 0 0 8px;
  color: var(--text-primary);
  font-size: 16px;
}
.playlists-empty-card p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
}
.playlists-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 0 var(--mobile-gutter, 6px) 100px;
}
.playlist-card {
  display: flex;
  align-items: center;
  background: rgba(20, 20, 28, 0.85);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 14px;
  overflow: hidden;
  transition: background 0.2s;
}
.playlist-card:hover {
  background: rgba(255,255,255,0.06);
}
.playlist-card-link {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 18px;
  text-decoration: none;
  color: inherit;
  min-width: 0;
}
.playlist-count-badge {
  margin-left: auto;
  flex-shrink: 0;
  font-size: 12px;
  font-weight: 700;
  color: #f4c430;
  background: rgba(244, 196, 48, 0.12);
  border: 1px solid rgba(244, 196, 48, 0.2);
  padding: 5px 9px;
  border-radius: 999px;
}
.playlist-icon {
  font-size: 20px;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.playlist-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.playlist-name {
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.playlist-desc {
  font-size: 12px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.playlist-editing {
  padding-right: 12px;
}
.playlist-edit-input {
  width: 100%;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 10px;
  color: var(--text-primary);
  padding: 8px 10px;
  font-size: 14px;
}
.playlist-edit-actions {
  display: flex;
  gap: 6px;
  margin-left: 10px;
  flex-shrink: 0;
}
.inline-action-btn {
  border: none;
  border-radius: 999px;
  padding: 8px 12px;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
}
.inline-action-btn.save {
  background: #f4c430;
  color: #1a1400;
}
.inline-action-btn.cancel {
  background: rgba(255,255,255,0.08);
  color: var(--text-primary);
}
.playlist-card-actions {
  display: flex;
  align-items: center;
  gap: 4px;
  padding-right: 14px;
}
.edit-btn {
  color: #f4c430;
}
.delete-btn {
  color: #ff6b6b;
}
.visibility-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 6px 8px;
  border-radius: 8px;
  font-size: 14px;
  transition: background 0.15s;
}
.visibility-btn.public {
  color: var(--accent-primary, #6ddcff);
}
.visibility-btn.unlisted {
  color: #f4c430;
}
.visibility-btn.private {
  color: var(--text-secondary);
}
.visibility-btn:hover {
  background: rgba(255,255,255,0.08);
}
.chevron {
  font-size: 14px;
  color: var(--text-secondary);
}
</style>
