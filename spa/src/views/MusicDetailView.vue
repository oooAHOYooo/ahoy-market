<template>
  <div class="music-detail-view">
    <button class="detail-back-btn" @click="goBack">
      <i class="fas fa-chevron-left"></i> Back
    </button>
    <div class="music-container" v-if="track">
      <!-- Hero -->
      <section class="podcast-show-hero">
      <img
        class="podcast-show-hero-art"
        :src="track.cover_art || '/static/img/default-cover.jpg'"
        :alt="track.title"
      />
      <div class="podcast-show-hero-meta">
        <div class="podcast-show-hero-kicker">Track</div>
        <h1 class="podcast-show-hero-title">{{ track.title }}</h1>
        <p class="podcast-show-hero-desc" v-if="track.artist">{{ track.artist }}</p>
        <p class="episode-subtitle" v-if="track.duration_seconds">
          {{ formatDuration(track.duration_seconds) }}
        </p>
        <div class="podcast-show-hero-actions">
          <button class="podcast-cta" @click="playThis">
            <i :class="isCurrentAndPlaying ? 'fas fa-pause' : 'fas fa-play'"></i>
            {{ isCurrentAndPlaying ? 'Pause' : 'Play' }}
          </button>
          <button class="podcast-cta secondary" @click="onBookmark">
            <i :class="bookmarks.isBookmarked(track) ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
            {{ bookmarks.isBookmarked(track) ? 'Saved' : 'Save' }}
          </button>
          <button class="podcast-cta secondary" @click="openAddToQueue(track)">
            <i class="fas fa-plus"></i>
            Add to Queue
          </button>
          <button class="podcast-cta secondary" @click="onShareTrack">
            <i class="fas fa-share-alt"></i>
            Share
          </button>
        </div>
      </div>
    </section>

    <!-- More from this artist -->
    <section class="podcasts-section" v-if="relatedTracks.length">
      <div class="podcasts-section-header">
        <h2>More from {{ track.artist }}</h2>
      </div>
      <div class="episode-list">
        <article
          v-for="(t, idx) in relatedTracks"
          :key="t.id"
          class="episode-row"
          :class="{ playing: playerStore.currentTrack?.id === t.id }"
          @click="playRelated(idx)"
        >
          <img class="episode-art" :src="t.cover_art || '/static/img/default-cover.jpg'" :alt="t.title" loading="lazy" />
          <div class="episode-meta">
            <div class="episode-title">{{ t.title }}</div>
            <div class="episode-show">{{ t.artist }}</div>
          </div>
          <div class="episode-actions">
            <button class="episode-btn" title="Add to queue" @click.stop="openAddToQueue(t)">
              <i class="fas fa-plus"></i>
            </button>
            <button class="episode-btn" @click.stop="playRelated(idx)">
              <i :class="playerStore.currentTrack?.id === t.id && playerStore.isPlaying ? 'fas fa-pause' : 'fas fa-play'"></i>
            </button>
          </div>
        </article>
      </div>
    </section>
    </div>

    <!-- Loading -->
    <div class="music-container" v-else>
      <section class="podcast-show-hero">
        <div class="podcast-show-hero-art skeleton" style="aspect-ratio:1;width:100%"></div>
        <div class="podcast-show-hero-meta">
          <div class="skeleton" style="height:14px;width:40%;margin-bottom:8px"></div>
          <div class="skeleton" style="height:24px;width:70%;margin-bottom:8px"></div>
          <div class="skeleton" style="height:14px;width:50%"></div>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiFetchCached } from '../composables/useApi'
import { useBookmarks } from '../composables/useBookmarks'
import { usePlayerStore } from '../stores/player'
import { useShare, useHaptics } from '../composables/useNative'
import { useAddToQueue } from '../composables/useAddToQueue'
import { setSeoMeta } from '../composables/useSeoMeta'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()
const bookmarks = useBookmarks()
const { shareTrack } = useShare()
const haptics = useHaptics()
const addToQueue = useAddToQueue()
function openAddToQueue(t) {
  addToQueue.open(t)
}

const track = ref(null)
const allTracks = ref([])

const relatedTracks = computed(() => {
  if (!track.value) return []
  return allTracks.value.filter(t => t.artist === track.value.artist && t.id !== track.value.id)
})

const isCurrentAndPlaying = computed(() =>
  playerStore.currentTrack?.id === track.value?.id && playerStore.isPlaying
)

function formatDuration(seconds) {
  if (!seconds) return ''
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function playThis() {
  if (isCurrentAndPlaying.value) {
    playerStore.pause()
  } else {
    playerStore.play(track.value)
    playerStore.setQueue(allTracks.value, allTracks.value.findIndex(t => t.id === track.value.id))
  }
}

function onBookmark() {
  haptics.onBookmark()
  bookmarks.toggle({ ...track.value, _type: 'track' })
}

function onShareTrack() {
  haptics.light()
  shareTrack(track.value)
}

function playRelated(idx) {
  playerStore.setQueue(relatedTracks.value, idx)
}

function goBack() {
  router.push('/music')
}

onMounted(async () => {
  const data = await apiFetchCached('/api/music').catch(() => ({ tracks: [] }))
  allTracks.value = data.tracks || []
  const id = route.params.id
  const artistSlug = route.params.artistSlug
  const trackSlug = route.params.trackSlug
  track.value = allTracks.value.find(t =>
    id
      ? String(t.id) === String(id)
      : t.artist_slug === artistSlug && t.track_slug === trackSlug
  ) || null
  if (track.value) {
    setSeoMeta({
      title: track.value.title,
      description: track.value.artist ? `Listen to ${track.value.title} by ${track.value.artist} on Ahoy Indie Media.` : `Listen to ${track.value.title} on Ahoy Indie Media.`,
      image: track.value.cover_art || '/static/img/ahoy_logo.png',
      type: 'music.song',
      url: window.location.pathname,
    })
  }
})
</script>

<style scoped>
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
</style>
