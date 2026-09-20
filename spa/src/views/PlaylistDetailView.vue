<template>
  <div class="playlist-detail-page">
    <div v-if="loading" class="loading">Loading...</div>
    <div v-else-if="!playlist" class="error">Playlist not found.</div>

    <template v-else>
      <div class="unified-header">
        <button class="detail-back-btn" @click="goBack">
          <i class="fas fa-chevron-left"></i> Back
        </button>
        <div class="header-content">
          <h1>{{ playlist.name }}</h1>
          <p v-if="playlist.description" class="playlist-description">{{ playlist.description }}</p>
          <span class="header-count">{{ items.length }} {{ items.length === 1 ? 'track' : 'tracks' }}</span>
        </div>
        <div v-if="playlist.is_owner" class="header-actions">
          <button
            v-if="playlist.visibility !== 'private'"
            type="button"
            class="action-btn"
            @click="copyShareLink"
            :title="shareCopied ? 'Link copied!' : 'Copy share link'"
          >
            <i :class="shareCopied ? 'fas fa-check' : 'fas fa-link'"></i>
            {{ shareCopied ? 'Copied!' : 'Share' }}
          </button>
          <button type="button" class="action-btn" :disabled="!playableItems.length" @click="playAll">
            <i class="fas fa-play"></i> Play all
          </button>
          <button
            type="button"
            class="action-btn visibility-toggle"
            :class="playlist.visibility"
            @click="cycleVisibility"
            :title="visibilityLabel"
          >
            <i :class="visibilityIcon"></i>
            {{ visibilityLabel }}
          </button>
        </div>
        <div v-else-if="playableItems.length" class="header-actions">
          <button type="button" class="action-btn" @click="playAll">
            <i class="fas fa-play"></i> Play all
          </button>
        </div>
      </div>

      <!-- Guest CTA — shown on public/unlisted playlists when not logged in -->
      <div v-if="!auth.isLoggedIn.value" class="guest-cta">
        <div class="guest-cta-inner">
          <i class="fas fa-music guest-cta-icon"></i>
          <div class="guest-cta-text">
            <strong>Save this playlist to your account</strong>
            <span>Create a free account to build playlists and support indie artists.</span>
          </div>
          <router-link to="/signup" class="cta-btn primary">Sign up free</router-link>
          <router-link to="/login" class="cta-btn secondary">Log in</router-link>
        </div>
      </div>

      <div class="playlist-items">
        <div
          v-for="(item, idx) in resolvedItems"
          :key="item.id"
          class="playlist-item-row"
          :class="{ playing: isCurrentlyPlaying(item) }"
          @click="playFrom(idx)"
        >
          <img v-if="item.artwork" :src="item.artwork" :alt="item.title" class="item-artwork" />
          <div v-else class="item-artwork-placeholder">
            <i :class="item.displayType === 'podcast' ? 'fas fa-podcast' : 'fas fa-music'"></i>
          </div>
          <div class="item-info">
            <span class="item-title">{{ item.title }}</span>
            <span class="item-meta">{{ item.artist || item.show_title || item.media_type }}</span>
          </div>
          <div class="item-actions">
            <span v-if="item.duration" class="item-duration">{{ formatDuration(item.duration) }}</span>
            <button
              v-if="playlist.is_owner"
              type="button"
              class="item-remove"
              aria-label="Remove from playlist"
              @click.stop="removeItem(item.id)"
            >
              <i class="fas fa-times"></i>
            </button>
          </div>
        </div>
        <p v-if="!items.length" class="empty">No tracks yet. Add from Music or Podcasts.</p>
      </div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlaylists } from '../composables/usePlaylists'
import { useAuth } from '../composables/useAuth'
import { usePlayerStore } from '../stores/player'
import { setSeoMeta } from '../composables/useSeoMeta'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const playlistsApi = usePlaylists()
const playerStore = usePlayerStore()

const playlist = ref(null)
const items = ref([])
const mediaMap = ref({})
const loading = ref(true)
const shareCopied = ref(false)

// Resolved items: merge playlist items with fetched metadata
const resolvedItems = computed(() =>
  items.value.map((item) => {
    const key = `${item.media_type}:${item.media_id}`
    const meta = mediaMap.value[key] || {}
    // Normalise type label for display (clip = podcast episode)
    const displayType = item.media_type === 'clip' ? 'podcast' : item.media_type
    return {
      ...item,
      displayType,
      title: meta.title || item.media_id,
      artist: meta.artist || meta.artist_name || '',
      show_title: meta.show_title || '',
      artwork: meta.cover_art || meta.artwork_url || meta.image || null,
      duration: meta.duration_seconds || null,
      audio_url: meta.audio_url || meta.preview_url || null,
    }
  })
)

const playableItems = computed(() => resolvedItems.value.filter((i) => i.audio_url))

const VISIBILITY_CYCLE = ['private', 'unlisted', 'public']
const VISIBILITY_ICONS = { private: 'fas fa-lock', unlisted: 'fas fa-link', public: 'fas fa-globe' }
const VISIBILITY_LABELS = { private: 'Private', unlisted: 'Unlisted', public: 'Public' }

const visibilityIcon = computed(() => VISIBILITY_ICONS[playlist.value?.visibility] || 'fas fa-lock')
const visibilityLabel = computed(() => VISIBILITY_LABELS[playlist.value?.visibility] || 'Private')

function updateSeoMeta() {
  if (!playlist.value || playlist.value.visibility === 'private') return
  const firstArtwork = resolvedItems.value.find((item) => item.artwork)?.artwork || ''
  setSeoMeta({
    title: playlist.value.name,
    description: playlist.value.description || `${resolvedItems.value.length} tracks in this playlist on Ahoy Indie Media.`,
    image: [firstArtwork, '/static/img/ahoy_logo.png'],
    type: 'website',
    url: window.location.pathname,
  })
}

function goBack() {
  router.push('/playlists')
}

function isCurrentlyPlaying(item) {
  const current = playerStore.currentTrack
  return current && String(current.id) === String(item.media_id)
}

function playFrom(startIndex) {
  const playable = playableItems.value
  if (!playable.length) return
  // Find the index within the playable subset closest to startIndex
  const clicked = resolvedItems.value[startIndex]
  const queueIndex = playable.findIndex((i) => i.id === clicked?.id)
  const tracks = playable.map((i) => ({
    id: i.media_id,
    title: i.title,
    artist: i.artist || i.show_title,
    audio_url: i.audio_url,
    cover_art: i.artwork,
    _type: i.media_type,
  }))
  playerStore.setQueue(tracks, queueIndex >= 0 ? queueIndex : 0, { source: 'playlist' })
}

function playAll() {
  playFrom(0)
}

async function cycleVisibility() {
  if (!playlist.value) return
  const current = playlist.value.visibility || 'private'
  const next = VISIBILITY_CYCLE[(VISIBILITY_CYCLE.indexOf(current) + 1) % VISIBILITY_CYCLE.length]
  try {
    const updated = await playlistsApi.update(playlist.value.id, { visibility: next })
    playlist.value = { ...playlist.value, ...updated }
    updateSeoMeta()
    window.dispatchEvent(new CustomEvent('ahoy:toast', {
      detail: { message: `Playlist is now ${VISIBILITY_LABELS[next].toLowerCase()}`, type: 'success' }
    }))
  } catch {
    //
  }
}

async function removeItem(itemId) {
  try {
    await playlistsApi.removeItem(Number(route.params.id), itemId)
    items.value = items.value.filter((i) => i.id !== itemId)
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Removed', type: 'success' } }))
  } catch {
    //
  }
}

async function copyShareLink() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    shareCopied.value = true
    setTimeout(() => { shareCopied.value = false }, 2500)
  } catch {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Could not copy link', type: 'error' } }))
  }
}

function formatDuration(seconds) {
  if (!seconds) return ''
  const m = Math.floor(seconds / 60)
  const s = String(seconds % 60).padStart(2, '0')
  return `${m}:${s}`
}

async function load() {
  const id = route.params.id
  if (!id) return
  loading.value = true
  try {
    const [pl, its] = await Promise.all([
      playlistsApi.get(Number(id)),
      playlistsApi.listItems(Number(id)),
    ])
    playlist.value = pl
    items.value = its
    if (its.length) {
      mediaMap.value = await playlistsApi.resolveMedia(its)
    }
    await nextTick()
    updateSeoMeta()
  } finally {
    loading.value = false
  }
}

onMounted(load)
watch(() => route.params.id, load)
watch(
  () => [playlist.value?.name, playlist.value?.description, playlist.value?.visibility, resolvedItems.value.length, resolvedItems.value[0]?.artwork],
  updateSeoMeta,
  { immediate: true }
)
</script>

<style scoped>
.playlist-detail-page {
  padding: 0 0 100px;
}
.loading, .error, .empty {
  color: var(--text-secondary);
  padding: 24px var(--mobile-gutter, 6px);
}
.unified-header {
  padding: 20px var(--mobile-gutter, 6px) 16px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
}
.header-content h1 {
  font-size: 22px;
  font-weight: 700;
  margin: 0 0 4px;
}
.playlist-description {
  font-size: 14px;
  color: var(--text-secondary);
  margin: 0 0 6px;
}
.header-count {
  font-size: 13px;
  color: var(--text-secondary);
}
.header-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  flex-wrap: wrap;
}
.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.07);
  color: var(--text-primary);
  cursor: pointer;
  transition: background 0.15s;
}
.action-btn:hover { background: rgba(255,255,255,0.12); }
.action-btn:disabled { opacity: 0.4; cursor: default; }
.visibility-toggle.public { color: var(--accent-primary, #6ddcff); border-color: var(--accent-primary, #6ddcff); }
.visibility-toggle.unlisted { color: #f4c430; border-color: #f4c430; }
/* Guest CTA */
.guest-cta {
  margin: 0 var(--mobile-gutter, 6px) 20px;
  background: rgba(109, 220, 255, 0.08);
  border: 1px solid rgba(109, 220, 255, 0.2);
  border-radius: 14px;
  padding: 16px;
}
.guest-cta-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}
.guest-cta-icon { font-size: 24px; color: var(--accent-primary, #6ddcff); flex-shrink: 0; }
.guest-cta-text { flex: 1; min-width: 180px; display: flex; flex-direction: column; gap: 2px; }
.guest-cta-text strong { font-size: 14px; color: var(--text-primary); }
.guest-cta-text span { font-size: 12px; color: var(--text-secondary); }
.cta-btn {
  display: inline-flex;
  align-items: center;
  padding: 8px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: opacity 0.15s;
}
.cta-btn.primary { background: var(--accent-primary, #6ddcff); color: #111; }
.cta-btn.secondary { background: rgba(255,255,255,0.08); color: var(--text-primary); }
.cta-btn:hover { opacity: 0.85; }
/* Items */
.playlist-items {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0 var(--mobile-gutter, 6px);
}
.playlist-item-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 12px;
  cursor: pointer;
  transition: background 0.15s;
}
.playlist-item-row:hover { background: rgba(255,255,255,0.06); }
.playlist-item-row.playing { background: rgba(109, 220, 255, 0.08); }
.item-artwork { width: 44px; height: 44px; border-radius: 8px; object-fit: cover; flex-shrink: 0; }
.item-artwork-placeholder {
  width: 44px; height: 44px; border-radius: 8px;
  background: rgba(255,255,255,0.08);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0; font-size: 18px; color: var(--text-secondary);
}
.item-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.item-title {
  font-size: 14px; font-weight: 600; color: var(--text-primary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.item-meta {
  font-size: 12px; color: var(--text-secondary);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-transform: capitalize;
}
.item-actions { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
.item-duration { font-size: 12px; color: var(--text-secondary); font-variant-numeric: tabular-nums; }
.item-remove {
  background: none; border: none; color: var(--text-secondary);
  cursor: pointer; padding: 6px; border-radius: 6px; transition: color 0.15s, background 0.15s;
}
.item-remove:hover { color: #ff6b6b; background: rgba(255, 107, 107, 0.1); }

.detail-back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(0,0,0,0.35);
  border: none;
  color: #fff;
  font-size: 14px;
  padding: 8px 14px;
  border-radius: 20px;
  cursor: pointer;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  margin: 12px 0 0 12px;
  width: fit-content;
}

.detail-back-btn:hover {
  background: rgba(0,0,0,0.5);
}

@media (max-width: 768px) {
  .unified-header {
    flex-direction: column;
  }

  .detail-back-btn {
    margin: 8px 0 0;
  }

  .header-actions {
    width: 100%;
  }

  .action-btn {
    flex: 1 1 calc(50% - 4px);
    justify-content: center;
  }

  .playlist-item-row {
    padding: 8px 10px;
    gap: 10px;
  }

  .item-artwork,
  .item-artwork-placeholder {
    width: 40px;
    height: 40px;
  }

  .item-title {
    font-size: 13px;
  }

  .item-meta,
  .item-duration {
    font-size: 11px;
  }
}
</style>
