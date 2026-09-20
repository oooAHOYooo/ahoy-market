<template>
  <PullRefresh @refresh="onRefresh">
    <div class="music-container" :class="{ 'music-container--compact-hero': compactHero }">
      <ContentHeader
        kicker="Ahoy Indie Media"
        title="Music"
        subtitle="Independent tracks from the Ahoy community."
      />
      <section class="music-mobile-library-hero" aria-label="Music library controls">
        <div class="music-mobile-hero-copy">
          <span class="music-mobile-eyebrow">Library</span>
          <h1>Music</h1>
          <p>{{ filteredTracks.length }} song{{ filteredTracks.length === 1 ? '' : 's' }} from independent artists</p>
        </div>
        <button
          type="button"
          class="music-mobile-hero-play"
          :disabled="filteredTracks.length === 0"
          aria-label="Play all music"
          @click="playAll"
        >
          <i class="fas fa-play" aria-hidden="true"></i>
        </button>
      </section>
      <!-- COMMAND CENTER: 3 action buttons (split + solid) + filter drawer -->
      <section class="music-command-center">
        <div class="music-filter-row">
          <SubMenuFilter
            v-model="selectedArtist"
            filter-label="Filter music by artist"
            :filters="artistFilters"
            all-value=""
            filter-all-label="All Artists"
            :show-search="true"
            search-placeholder="Search tracks or artists"
            :search-query="searchQuery"
            :sort-options="sortOptions"
            sort-label="Sort music"
            :sort-by="sortBy"
            :show-favorites-toggle="true"
            :favorites-only="favoritesOnly"
            @update:searchQuery="searchQuery = $event"
            @update:sortBy="sortBy = $event"
            @update:favoritesOnly="favoritesOnly = $event"
          />
        </div>
        <div class="music-compact-tabs" aria-label="Library views">
          <button type="button" :class="{ active: !activeFilter }" @click="clearActiveFilter">All</button>
          <button type="button" :class="{ active: activeFilter === 'saved' }" @click="activeFilter = 'saved'">
            Saved <span>{{ savedTracks.length }}</span>
          </button>
          <button type="button" :class="{ active: activeFilter === 'new' }" @click="activeFilter = 'new'">
            New <span>{{ newTracks.length }}</span>
          </button>
        </div>

        <!-- Active filter drawer with right-aligned actions -->
        <div v-if="activeFilter" class="music-filter-drawer" :class="`music-filter-drawer--${activeFilter}`">
          <div class="music-filter-drawer-copy">
            <div class="music-filter-drawer-kicker">
              <i :class="activeFilterMeta.icon"></i>
              <span>{{ activeFilterMeta.label }}</span>
            </div>
            <div class="music-filter-drawer-title">
              {{ filteredTracks.length }} track{{ filteredTracks.length === 1 ? '' : 's' }}
            </div>
            <div class="music-filter-drawer-subtitle">
              {{ activeFilterMeta.subtitle }}
            </div>
          </div>
          <div class="music-filter-drawer-actions">
            <button
              v-if="filteredTracks.length > 0"
              type="button"
              @click="playAll"
              class="music-filter-drawer-play"
              title="Play all"
            >
              <i class="fas fa-play"></i>
              <span>Play all</span>
            </button>
            <button type="button" @click="clearActiveFilter" class="music-filter-drawer-close" title="Exit">
              <i class="fas fa-xmark"></i>
            </button>
          </div>
        </div>

        <!-- Sort drawer (collapsed by default) -->
        <div class="music-sort-drawer" :class="{ expanded: sortDrawerOpen }">
          <div class="music-sort-header">
            <button
              type="button"
              class="music-sort-toggle"
              @click="sortDrawerOpen = !sortDrawerOpen"
            >
              <i class="fas fa-arrow-down-wide-short"></i>
              <span class="music-sort-label">Sort</span>
              <span class="music-sort-current">{{ currentSortLabel }}</span>
              <span class="music-sort-sub">· {{ currentSortSub }}</span>
              <i class="fas fa-chevron-down" :class="{ rotated: sortDrawerOpen }"></i>
            </button>
            </div>
          <div v-if="sortDrawerOpen" class="music-sort-options">
            <button
              v-for="opt in sortOptions"
              :key="opt.value"
              type="button"
              :class="{ active: sortBy === opt.value }"
              @click="sortBy = opt.value; sortDrawerOpen = false"
            >
              <i :class="opt.icon || 'fas fa-music'"></i>
              <span class="music-opt-label">{{ opt.label }}</span>
              <span class="music-opt-sub">{{ opt.sub }}</span>
              <i v-if="sortBy === opt.value" class="fas fa-check"></i>
            </button>
          </div>
        </div>
      </section>

      <section v-if="!loading" class="music-for-you" aria-labelledby="music-for-you-title">
        <div class="music-for-you-head">
          <div>
            <span class="music-for-you-kicker">Made for right now</span>
            <h2 id="music-for-you-title">{{ recommendationTitle }}</h2>
            <p>{{ recommendationSubtitle }}</p>
          </div>
          <div v-if="recommendations.length" class="music-for-you-actions">
            <button type="button" class="primary" @click="playRecommendations(false)">
              <i class="fas fa-play" aria-hidden="true"></i> Play all
            </button>
            <button type="button" @click="playRecommendations(true)">
              <i class="fas fa-shuffle" aria-hidden="true"></i> Shuffle
            </button>
          </div>
        </div>
        <div v-if="recommendations.length" class="music-recommendation-rail" role="list" aria-label="Recommended tracks">
          <article v-for="(track, idx) in recommendations" :key="`rec-${track.id}`" class="music-recommendation" role="listitem">
            <button type="button" class="music-recommendation-art" :aria-label="`Play ${track.title}`" @click="playRecommendation(track)">
              <img :src="getTrackCover(track)" alt="" loading="lazy" @error="onRecommendationImageError($event, track)" />
              <span class="music-recommendation-play"><i class="fas fa-play" aria-hidden="true"></i></span>
            </button>
            <span class="music-recommendation-reason">{{ recommendationReason(track, idx) }}</span>
            <strong>{{ track.title }}</strong>
            <div><span>{{ track.artist || 'Ahoy artist' }}</span><time>{{ formatDuration(track.duration_seconds) }}</time></div>
          </article>
        </div>
      </section>

      <!-- Community Playlists -->
      <section v-if="publicPlaylists.length" class="community-playlists">
        <div class="section-header">
          <h2 class="section-title">Community Playlists</h2>
          <router-link to="/playlists" class="section-link">See yours</router-link>
        </div>
        <div class="community-playlist-row">
          <router-link
            v-for="pl in publicPlaylists"
            :key="pl.id"
            :to="`/playlists/${pl.id}`"
            class="community-playlist-card"
          >
            <div class="community-playlist-icon"><i class="fas fa-list-ul"></i></div>
            <div class="community-playlist-info">
              <span class="community-playlist-name">{{ pl.name }}</span>
              <span v-if="pl.description" class="community-playlist-desc">{{ pl.description }}</span>
            </div>
          </router-link>
        </div>
      </section>

      <div class="music-library-heading">
        <div><span>Full collection</span><h2>All tracks</h2></div>
        <small>{{ filteredTracks.length }} track{{ filteredTracks.length === 1 ? '' : 's' }}</small>
      </div>

      <!-- Track list -->
      <div v-show="!loading && filteredTracks.length > 0" class="music-list">
        <div class="music-table-wrap">
          <table class="music-table">
            <thead>
              <tr>
                <th class="col-num">#</th>
                <th class="col-title-artist">Title</th>
                <th class="col-duration" style="text-align:right">Time</th>
                <th class="col-action"></th>
              </tr>
            </thead>
            <tbody>
              <MusicTrackListRow
                v-for="(track, idx) in filteredTracks"
                :key="track.id"
                :index="idx"
                :track="track"
                :playing="playerStore.currentTrack?.id === track.id"
                :cover="getTrackCover(track)"
                :duration="formatDuration(track.duration_seconds)"
                :track-url="musicUrl(track)"
                :play-icon="playerStore.currentTrack?.id === track.id && playerStore.isPlaying ? 'fas fa-pause' : 'fas fa-play'"
                :play-title="playerStore.currentTrack?.id === track.id && playerStore.isPlaying ? 'Pause' : 'Play'"
                :bookmarked="bookmarks.isBookmarked({ id: track.id })"
                :bookmark-icon="bookmarks.isBookmarked({ id: track.id }) ? 'fas fa-bookmark' : 'far fa-bookmark'"
                :bookmark-title="bookmarks.isBookmarked({ id: track.id }) ? 'Unsave' : 'Save'"
                :loading-type="idx < 8 ? 'eager' : 'lazy'"
                @play="playTrackAtFilteredIndex(idx)"
                @queue="addToQueue(track)"
                @add-to-playlist="addToPlaylistModal.open({ ...track, type: 'music' })"
                @toggle-bookmark="toggleBookmark(track)"
              />
            </tbody>
          </table>
        </div>
        <div class="music-mobile-list">
          <MusicTrackMobileRow
            v-for="(track, idx) in filteredTracks"
            :key="'mobile-' + track.id"
            :track="track"
            :playing="playerStore.currentTrack?.id === track.id"
            :cover="getTrackCover(track)"
            :duration="formatDuration(track.duration_seconds)"
            :track-url="musicUrl(track)"
            :play-icon="playerStore.currentTrack?.id === track.id && playerStore.isPlaying ? 'fas fa-pause' : 'fas fa-play'"
            :play-title="playerStore.currentTrack?.id === track.id && playerStore.isPlaying ? 'Pause' : 'Play'"
            :bookmarked="bookmarks.isBookmarked({ id: track.id })"
            :bookmark-icon="bookmarks.isBookmarked({ id: track.id }) ? 'fas fa-bookmark' : 'far fa-bookmark'"
            :bookmark-title="bookmarks.isBookmarked({ id: track.id }) ? 'Unsave' : 'Save'"
            :loading-type="idx < 8 ? 'eager' : 'lazy'"
            @play="playTrackAtFilteredIndex(idx)"
            @queue="addToQueue(track)"
            @add-to-playlist="addToPlaylistModal.open({ ...track, type: 'music' })"
            @toggle-bookmark="toggleBookmark(track)"
            @more="openMobileTrackActions(track)"
          />
        </div>
      </div>

      <Teleport to="body">
        <div
          v-if="mobileActionTrack"
          class="music-mobile-action-layer"
          role="presentation"
          @click="closeMobileTrackActions"
        >
          <section
            class="music-mobile-action-sheet"
            role="dialog"
            aria-modal="true"
            aria-label="Track actions"
            @click.stop
          >
            <div class="music-mobile-action-track">
              <img
                class="music-mobile-action-art"
                :src="getTrackCover(mobileActionTrack)"
                :alt="mobileActionTrack.title"
                @error="onMobileActionImageError"
              />
              <div class="music-mobile-action-meta">
                <strong>{{ mobileActionTrack.title }}</strong>
                <span>{{ mobileActionTrack.artist }}</span>
              </div>
            </div>
            <div class="music-mobile-action-buttons">
              <button type="button" @click="playMobileActionTrack">
                <i class="fas fa-play" aria-hidden="true"></i>
                <span>Play</span>
              </button>
              <button type="button" @click="queueMobileActionTrack">
                <i class="fas fa-list-ul" aria-hidden="true"></i>
                <span>Add to queue</span>
              </button>
              <button type="button" @click="playlistMobileActionTrack">
                <i class="fas fa-plus" aria-hidden="true"></i>
                <span>Add to playlist</span>
              </button>
              <button type="button" @click="bookmarkMobileActionTrack">
                <i :class="bookmarks.isBookmarked({ id: mobileActionTrack.id }) ? 'fas fa-bookmark' : 'far fa-bookmark'" aria-hidden="true"></i>
                <span>{{ bookmarks.isBookmarked({ id: mobileActionTrack.id }) ? 'Unsave song' : 'Save song' }}</span>
              </button>
            </div>
          </section>
        </div>
      </Teleport>

      <!-- Loading skeletons -->
      <div v-if="loading" class="music-grid">
        <div v-for="i in 8" :key="i" class="track-card">
          <div class="track-cover skeleton"></div>
          <div class="track-info">
            <div class="skeleton" style="height:14px;width:60%;margin-bottom:6px"></div>
            <div class="skeleton" style="height:12px;width:40%;margin-bottom:4px"></div>
            <div class="skeleton" style="height:10px;width:36px"></div>
          </div>
        </div>
      </div>

      <!-- Empty state -->
      <div v-else-if="!loading && filteredTracks.length === 0" class="empty-state">
        <i class="fas fa-music"></i>
        <h3>No music found</h3>
        <p>Try adjusting your filters or search terms</p>
      </div>
    </div>
  </PullRefresh>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiFetch } from '../composables/useApi'
import { usePlayerStore } from '../stores/player'
import { useBookmarks } from '../composables/useBookmarks'
import { useAddToPlaylist } from '../composables/useAddToPlaylist'
import { usePlaylists } from '../composables/usePlaylists'
import { useOverlay } from '../composables/useOverlay'
import { musicUrl } from '../utils/urls'
import PullRefresh from '../components/PullRefresh.vue'
import ContentHeader from '../components/ContentHeader.vue'
import SubMenuFilter from '../components/SubMenuFilter.vue'
import MusicTrackListRow from '../components/music/MusicTrackListRow.vue'
import MusicTrackMobileRow from '../components/music/MusicTrackMobileRow.vue'

const router = useRouter()
const route = useRoute()
const playerStore = usePlayerStore()
const bookmarks = useBookmarks()
const addToPlaylistModal = useAddToPlaylist()
const playlistsApi = usePlaylists()
const { openNowPlaying } = useOverlay()
const publicPlaylists = ref([])
const compactHero = ref(false)

function toggleBookmark(track) {
  bookmarks.toggle({
    type: 'track',
    id: track.id,
    title: track.title,
    cover_art: track.cover_art,
  })
}

function getTrackCover(track) {
  const url = track && (track.cover_art || track.artwork)
  if (typeof url === 'string' && url.trim()) return url
  return '/static/img/default-cover.jpg'
}

const tracks = ref([])
const loading = ref(true)
const searchQuery = ref(typeof route.query.q === 'string' ? route.query.q : '')
const selectedArtist = ref('')
const favoritesOnly = ref(false)

const sortBy = ref(localStorage.getItem('ahoy_music_sort_by') || 'added_date')
watch(sortBy, (newVal) => {
  localStorage.setItem('ahoy_music_sort_by', newVal)
})

watch(searchQuery, (q) => {
  const query = { ...route.query }
  if (q.trim()) query.q = q.trim()
  else delete query.q
  router.replace({ query })
}, { flush: 'post' })

watch(() => route.query.q, (q) => {
  const next = typeof q === 'string' ? q : ''
  if (searchQuery.value !== next) searchQuery.value = next
})

const shuffledOrder = ref(JSON.parse(localStorage.getItem('ahoy_music_shuffled_order') || '[]'))

function ensureShuffledOrder() {
  if (!shuffledOrder.value || shuffledOrder.value.length === 0) {
    const ids = tracks.value.map(t => t.id)
    shuffledOrder.value = [...ids].sort(() => Math.random() - 0.5)
    localStorage.setItem('ahoy_music_shuffled_order', JSON.stringify(shuffledOrder.value))
  }
}
const sortDrawerOpen = ref(false)
const activeFilter = ref(null) // null | 'saved' | 'new'
const mobileActionTrack = ref(null)

function clearActiveFilter() {
  activeFilter.value = null
}

function isNewMusicTrack(track) {
  const tags = Array.isArray(track?.tags) ? track.tags.map((tag) => String(tag).toLowerCase()) : []
  if (tags.includes('new music')) return true
  if (track?.new || track?.is_new) return true

  const addedTime = new Date(track?.added_date || 0).getTime()
  if (Number.isFinite(addedTime) && addedTime > 0) {
    const thirtyDaysAgo = Date.now() - 30 * 24 * 60 * 60 * 1000
    return addedTime > thirtyDaysAgo
  }
  return false
}


const artists = computed(() => {
  const set = new Set()
  for (const t of tracks.value) {
    if (t.artist) set.add(t.artist)
  }
  return Array.from(set).sort()
})


// For SubMenuFilter: { value, label, image }
const artistFilters = computed(() => {
  const byName = new Map()
  for (const t of tracks.value) {
    if (!t.artist) continue
    if (!byName.has(t.artist)) {
      byName.set(t.artist, {
        value: t.artist,
        label: t.artist,
        image: t.cover_art || t.artwork || null
      })
    }
  }
  return Array.from(byName.values()).sort((a, b) => (a.label || '').localeCompare(b.label || ''))
})

const sortOptions = [
  { value: 'title', label: 'Song Name', sub: 'A–Z', icon: 'fas fa-music' },
  { value: 'artist', label: 'Artist Name', sub: 'A–Z', icon: 'fas fa-user' },
  { value: 'added_date', label: 'Recently Added', sub: 'Newest first', icon: 'fas fa-clock' },
  { value: 'shuffle', label: 'Shuffled', sub: 'Random order', icon: 'fas fa-shuffle' }
]

function getTrackDateValue(track) {
  const rawDate = track?.date_added || track?.added_date || track?.release_date
  if (!rawDate) return 0

  if (rawDate instanceof Date) {
    const timestamp = rawDate.getTime()
    return Number.isFinite(timestamp) ? timestamp : 0
  }

  if (typeof rawDate === 'number') {
    return Number.isFinite(rawDate) ? rawDate : 0
  }

  const parsed = Date.parse(rawDate)
  if (Number.isFinite(parsed)) return parsed

  const normalized = String(rawDate).trim().match(/^(\d{1,2})-(\d{1,2})-(\d{2}|\d{4})$/)
  if (!normalized) return 0

  const month = Number(normalized[1])
  const day = Number(normalized[2])
  const year = Number(normalized[3].length === 2 ? `20${normalized[3]}` : normalized[3])
  if (!month || !day || !year) return 0

  return Date.UTC(year, month - 1, day)
}

const filteredTracks = computed(() => {
  let list = [...tracks.value]

  // 1. Filter: Active filter (Saved Songs / New Music)
  if (activeFilter.value === 'saved') {
    list = list.filter((t) => bookmarks.isBookmarked({ id: t.id }))
  } else if (activeFilter.value === 'new') {
    list = list.filter((t) => isNewMusicTrack(t))
  }

  // 2. Filter: Search
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(
      (t) =>
        (t.title || '').toLowerCase().includes(q) ||
        (t.artist || '').toLowerCase().includes(q) ||
        (t.album || '').toLowerCase().includes(q)
    )
  }

  // 3. Filter: Artist (Chip)
  if (selectedArtist.value) {
    list = list.filter((t) => t.artist === selectedArtist.value)
  }

  // 4. Filter: Favorites (Toggle)
  if (favoritesOnly.value) {
    list = list.filter((t) => bookmarks.isBookmarked({ id: t.id }))
  }

  // 5. Sort
  list.sort((a, b) => {
    switch (sortBy.value) {
      case 'shuffle':
        ensureShuffledOrder()
        const idxA = shuffledOrder.value.indexOf(a.id)
        const idxB = shuffledOrder.value.indexOf(b.id)
        if (idxA === -1 && idxB === -1) return 0
        if (idxA === -1) return 1
        if (idxB === -1) return -1
        return idxA - idxB
      case 'title':
        return (a.title || '').localeCompare(b.title || '')
      case 'artist':
        return (a.artist || '').localeCompare(b.artist || '')
      case 'added_date':
        return getTrackDateValue(b) - getTrackDateValue(a) || (a.title || '').localeCompare(b.title || '')
      default:
        return 0
    }
  })
  return list
})

// Saved tracks (bookmarked)
const savedTracks = computed(() => {
  return tracks.value.filter((t) => bookmarks.isBookmarked({ id: t.id }))
})

// New tracks: recent adds plus anything explicitly tagged as new music
const newTracks = computed(() => {
  return tracks.value.filter((t) => isNewMusicTrack(t))
})

const recommendations = computed(() => {
  const unplayed = tracks.value.filter((track) => !(Number(track.play_count) > 0))
  const source = unplayed.length
    ? unplayed
    : [...tracks.value].sort((a, b) => getTrackDateValue(b) - getTrackDateValue(a))
  return source.slice(0, 8)
})

const recommendationTitle = computed(() => recommendations.value.length
  ? (tracks.value.some((track) => !(Number(track.play_count) > 0)) ? 'For You' : 'You’re caught up')
  : 'Start exploring Ahoy')

const recommendationSubtitle = computed(() => recommendations.value.length
  ? (tracks.value.some((track) => !(Number(track.play_count) > 0))
      ? 'A fresh set of tracks from the Ahoy community.'
      : 'Check out the newest tracks from Ahoy artists.')
  : 'Community favorites will appear here as the library grows.')

const activeFilterMeta = computed(() => {
  if (activeFilter.value === 'saved') {
    return {
      label: 'Saved Songs',
      subtitle: 'Tracks you bookmarked for later',
      icon: 'fas fa-bookmark',
    }
  }
  if (activeFilter.value === 'new') {
    return {
      label: 'New Music',
      subtitle: 'Fresh drops and hidden new-music tags',
      icon: 'fas fa-sparkles',
    }
  }
  return {
    label: 'Library',
    subtitle: 'Browse the full music catalog',
    icon: 'fas fa-music',
  }
})

// Current sort label and sub for drawer header
const currentSortLabel = computed(() => {
  const opt = sortOptions.find((o) => o.value === sortBy.value)
  return opt ? opt.label : 'Song Name'
})

const currentSortSub = computed(() => {
  const opt = sortOptions.find((o) => o.value === sortBy.value)
  return opt ? opt.sub : 'A–Z'
})

function formatDuration(seconds) {
  const total = Number(seconds)
  if (!Number.isFinite(total) || total <= 0) return '0:00'
  const m = Math.floor(total / 60)
  const s = Math.floor(total % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function playTrackAtFilteredIndex(idx) {
  const list = filteredTracks.value
  const track = list[idx]
  if (!track) return
  if (playerStore.currentTrack?.id === track.id && playerStore.isPlaying) {
    openNowPlaying()
    return
  }
  playerStore.setQueue(list, idx)
  openNowPlaying()
}

function addToQueue(track) {
  playerStore.addToQueue({
    type: 'track',
    id: track.id,
    title: track.title,
    artist: track.artist,
    cover_art: track.cover_art,
    audio_url: track.audio_url,
    duration_seconds: track.duration_seconds,
  })
}

function openMobileTrackActions(track) {
  mobileActionTrack.value = track
}

function closeMobileTrackActions() {
  mobileActionTrack.value = null
}

function playMobileActionTrack() {
  const idx = filteredTracks.value.findIndex((track) => track.id === mobileActionTrack.value?.id)
  closeMobileTrackActions()
  if (idx >= 0) playTrackAtFilteredIndex(idx)
}

function queueMobileActionTrack() {
  if (!mobileActionTrack.value) return
  addToQueue(mobileActionTrack.value)
  closeMobileTrackActions()
}

function playlistMobileActionTrack() {
  if (!mobileActionTrack.value) return
  addToPlaylistModal.open({ ...mobileActionTrack.value, type: 'music' })
  closeMobileTrackActions()
}

function bookmarkMobileActionTrack() {
  if (!mobileActionTrack.value) return
  toggleBookmark(mobileActionTrack.value)
  closeMobileTrackActions()
}

function onMobileActionImageError(event) {
  event.target.src = '/static/img/default-cover.jpg'
}

function playRandomTrack() {
  if (filteredTracks.value.length === 0) return
  const idx = Math.floor(Math.random() * filteredTracks.value.length)
  playTrackAtFilteredIndex(idx)
}

// Command center actions
function playSavedTracks() {
  if (savedTracks.value.length === 0) return
  playerStore.setQueue(savedTracks.value, 0)
  openNowPlaying()
}

function playNewTracks() {
  if (newTracks.value.length === 0) return
  playerStore.setQueue(newTracks.value, 0)
  openNowPlaying()
}

function playShuffled() {
  if (filteredTracks.value.length === 0) return
  
  // 1. Generate new shuffled order for current filtered tracks
  const currentIds = filteredTracks.value.map(t => t.id)
  const shuffledIds = [...currentIds].sort(() => Math.random() - 0.5)
  shuffledOrder.value = shuffledIds
  localStorage.setItem('ahoy_music_shuffled_order', JSON.stringify(shuffledIds))
  
  // 2. Set sort mode to 'shuffle'
  sortBy.value = 'shuffle'
  
  // 3. Play the reordered list from the beginning
  playerStore.setQueue(filteredTracks.value, 0)
  openNowPlaying()
}

function recommendationReason(track, index) {
  if (!(Number(track.play_count) > 0)) return 'Not played yet'
  if (track.added_date || track.date_added) return index < 2 ? 'New this week' : 'Recently added'
  return 'Community pick'
}

function playRecommendations(shuffle = false) {
  const list = [...recommendations.value]
  if (!list.length) return
  if (shuffle) {
    for (let i = list.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[list[i], list[j]] = [list[j], list[i]]
    }
  }
  playerStore.setQueue(list, 0)
  openNowPlaying()
}

function playRecommendation(track) {
  const list = [track, ...recommendations.value.filter((item) => item.id !== track.id)]
  playerStore.setQueue(list, 0)
  openNowPlaying()
}

function onRecommendationImageError(event, track) {
  const seed = `${track?.artist || ''}${track?.title || ''}`
  let hash = 0
  for (let i = 0; i < seed.length; i += 1) hash = seed.charCodeAt(i) + ((hash << 5) - hash)
  const hue = Math.abs(hash) % 360
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="480" height="480"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="hsl(${hue} 55% 30%)"/><stop offset="1" stop-color="hsl(${(hue + 55) % 360} 60% 13%)"/></linearGradient></defs><rect width="100%" height="100%" fill="url(%23g)"/><text x="50%" y="54%" text-anchor="middle" fill="white" fill-opacity=".7" font-size="96">♫</text></svg>`
  event.target.src = `data:image/svg+xml,${encodeURIComponent(svg)}`
}

function playAll() {
  if (filteredTracks.value.length === 0) return
  playerStore.setQueue(filteredTracks.value, 0)
  openNowPlaying()
}

function updateCompactHero() {
  compactHero.value = window.scrollY > 72
}

async function loadTracks() {
  loading.value = true
  try {
    const data = await apiFetch('/api/music?t=' + Date.now())
    tracks.value = data.tracks || []
  } catch {
    tracks.value = []
  }
  loading.value = false
}

async function onRefresh(done) {
  try {
    const data = await apiFetch('/api/music?t=' + Date.now())
    tracks.value = data.tracks || []
  } catch { /* keep existing */ }
  done()
}

onMounted(() => {
  loadTracks()
  playlistsApi.listPublic().then((items) => { publicPlaylists.value = items.slice(0, 6) })
  updateCompactHero()
  window.addEventListener('scroll', updateCompactHero, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('scroll', updateCompactHero)
})
</script>

<style scoped>
.music-filter-row {
  padding: 0 20px 4px;
}

/* Community Playlists */
.community-playlists {
  padding: 16px 20px 8px;
}
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.section-title {
  font-size: 15px;
  font-weight: 700;
  margin: 0;
  color: var(--text-primary);
}
.section-link {
  font-size: 13px;
  color: var(--accent-primary, #6ddcff);
  text-decoration: none;
}
.community-playlist-row {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: none;
}
.community-playlist-row::-webkit-scrollbar { display: none; }
.community-playlist-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: rgba(20, 20, 28, 0.85);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 12px;
  text-decoration: none;
  color: inherit;
  flex-shrink: 0;
  min-width: 160px;
  max-width: 220px;
  transition: background 0.15s;
}
.community-playlist-card:hover { background: rgba(255,255,255,0.06); }
.community-playlist-icon {
  font-size: 18px;
  color: var(--text-secondary);
  flex-shrink: 0;
}
.community-playlist-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.community-playlist-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.community-playlist-desc {
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Command center */
.music-command-center {
  padding: 0 20px 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.music-compact-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  width: fit-content;
  padding: 3px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.025);
}

.music-compact-tabs button {
  min-height: 34px;
  padding: 0 14px;
  border: 0;
  border-radius: 999px;
  background: transparent;
  color: rgba(255, 255, 255, 0.58);
  font: 700 12px/1 inherit;
  cursor: pointer;
}

.music-compact-tabs button.active {
  background: rgba(236, 72, 153, 0.14);
  color: #fff;
}

.music-compact-tabs button span { color: rgba(255, 255, 255, 0.42); margin-left: 4px; }

.music-for-you {
  margin: 12px 20px 22px;
  padding: 24px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 20px;
  background:
    radial-gradient(circle at 8% 0%, rgba(236, 72, 153, 0.17), transparent 38%),
    radial-gradient(circle at 88% 110%, rgba(77, 181, 213, 0.1), transparent 34%),
    rgba(15, 18, 27, 0.9);
}

.music-for-you-head { display: flex; align-items: flex-end; justify-content: space-between; gap: 24px; margin-bottom: 18px; }
.music-for-you-kicker { color: #e997bd; font-size: 10px; font-weight: 800; letter-spacing: .13em; text-transform: uppercase; }
.music-for-you-head h2 { margin: 3px 0 0; color: #fff; font-size: clamp(25px, 2.6vw, 36px); line-height: 1.05; }
.music-for-you-head p { margin: 7px 0 0; color: rgba(255, 255, 255, 0.56); font-size: 13px; }
.music-for-you-actions { display: flex; gap: 8px; }
.music-for-you-actions button { min-height: 40px; padding: 0 16px; border: 1px solid rgba(255, 255, 255, 0.12); border-radius: 999px; background: rgba(255, 255, 255, 0.05); color: #fff; font: 750 12px/1 inherit; cursor: pointer; }
.music-for-you-actions button.primary { border-color: transparent; background: #ec4899; color: #170812; }
.music-recommendation-rail { display: grid; grid-auto-flow: column; grid-auto-columns: minmax(170px, 1fr); gap: 14px; overflow-x: auto; padding: 2px 2px 10px; scrollbar-width: thin; overscroll-behavior-inline: contain; }
.music-recommendation { min-width: 0; transition: transform .18s ease; }
.music-recommendation:hover { transform: translateY(-3px); }
.music-recommendation-art { position: relative; display: block; width: 100%; padding: 0; overflow: hidden; aspect-ratio: 1; border: 1px solid rgba(255,255,255,.09); border-radius: 12px; background: #11141d; cursor: pointer; }
.music-recommendation-art img { display: block; width: 100%; height: 100%; object-fit: cover; }
.music-recommendation-play { position: absolute; right: 10px; bottom: 10px; display: grid; width: 40px; height: 40px; place-items: center; border-radius: 50%; background: #ec4899; color: #170812; opacity: 0; transform: translateY(4px); transition: .18s ease; }
.music-recommendation-art:hover .music-recommendation-play, .music-recommendation-art:focus-visible .music-recommendation-play { opacity: 1; transform: none; }
.music-recommendation-reason { display: block; margin-top: 10px; color: #dc8db2; font-size: 10px; font-weight: 750; }
.music-recommendation strong { display: block; overflow: hidden; margin-top: 4px; color: #fff; font-size: 14px; text-overflow: ellipsis; white-space: nowrap; }
.music-recommendation > div { display: flex; justify-content: space-between; gap: 8px; margin-top: 4px; color: rgba(255, 255, 255, 0.52); font-size: 11px; }

.music-library-heading { display: flex; align-items: flex-end; justify-content: space-between; padding: 2px 20px 12px; }
.music-library-heading span { color: #dc8db2; font-size: 10px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
.music-library-heading h2 { margin: 2px 0 0; color: #fff; font-size: 22px; }
.music-library-heading small { color: rgba(255,255,255,.42); font-size: 11px; }

@media (min-width: 769px) {
  .music-container :deep(.music-table) { border-collapse: separate; border-spacing: 0 4px; background: transparent; }
  .music-container :deep(.music-table thead) { background: transparent; }
  .music-container :deep(.music-table th) { height: 30px; border: 0; background: transparent; color: rgba(255,255,255,.38); font-size: 10px; letter-spacing: .08em; }
  .music-container :deep(.music-table-row) { height: 72px; background: rgba(255,255,255,.018); transition: background .16s ease, box-shadow .16s ease; }
  .music-container :deep(.music-table-row:hover) { background: rgba(255,255,255,.05); }
  .music-container :deep(.music-table-row.playing) { background: linear-gradient(90deg, rgba(236,72,153,.14), rgba(72,110,180,.07)); box-shadow: inset 2px 0 #ec4899; }
  .music-container :deep(.music-table-row td) { border-top: 1px solid rgba(255,255,255,.045); border-bottom: 1px solid rgba(255,255,255,.045); }
  .music-container :deep(.music-table-row td:first-child) { border-radius: 11px 0 0 11px; }
  .music-container :deep(.music-table-row td:last-child) { border-radius: 0 11px 11px 0; }
  .music-container :deep(.music-row-art) { width: 52px; height: 52px; border-radius: 8px; box-shadow: 0 6px 18px rgba(0,0,0,.28); }
  .music-container :deep(.title-text) { font-size: 14px; font-weight: 750; }
  .music-container :deep(.music-track-artist) { margin-top: 5px; color: rgba(255,255,255,.55); font-size: 12px; }
}

@media (max-width: 768px) {
  .music-for-you { margin: 8px 10px 16px; padding: 17px 14px; }
  .music-for-you-head { align-items: flex-start; flex-direction: column; gap: 14px; }
  .music-for-you-actions { width: 100%; }.music-for-you-actions button { flex: 1; }
  .music-recommendation-rail { grid-auto-columns: minmax(152px, 67vw); }
  .music-compact-tabs { margin-inline: 10px; }
  .music-library-heading { padding-inline: 12px; }
}

@media (prefers-reduced-motion: reduce) {
  .music-recommendation, .music-recommendation-play { transition: none; }
}

/* Action buttons row - 3 buttons */
.music-action-buttons {
  display: flex;
  gap: 8px;
  align-items: stretch;
}

/* Split button (Saved & New) */
.music-split-btn {
  flex: 1;
  display: flex;
  min-height: 64px;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(109, 220, 255, 0.15) 0%, rgba(109, 220, 255, 0.07) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 0 0 1px rgba(109, 220, 255, 0.2), 0 8px 24px -12px rgba(109, 220, 255, 0.3);
  overflow: hidden;
  border: none;
}

.music-split-btn-new {
  background: linear-gradient(180deg, rgba(155, 140, 255, 0.15) 0%, rgba(155, 140, 255, 0.07) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06), 0 0 0 1px rgba(155, 140, 255, 0.2), 0 8px 24px -12px rgba(155, 140, 255, 0.3);
}

.music-split-main {
  flex: 1;
  min-width: 0;
  border: none;
  background: transparent;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 6px 4px;
  color: #fff;
  cursor: pointer;
  font-family: inherit;
  position: relative;
  text-align: center;
}

.music-split-icon-play {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
}

.music-split-btn-new .music-split-main .music-split-icon-play {
  color: #9b8cff;
}

.music-split-main .music-split-icon-play i:last-child {
  font-size: 8px;
  color: rgba(255, 255, 255, 0.55);
}

.music-split-label {
  font-size: 10.5px;
  font-weight: 700;
  letter-spacing: 0.01em;
  white-space: nowrap;
  line-height: 1.1;
}

.music-split-sub {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
  white-space: nowrap;
}

.music-split-icon {
  width: 26px;
  flex-shrink: 0;
  border: none;
  border-left: 1px solid rgba(109, 220, 255, 0.15);
  background: rgba(0, 0, 0, 0.12);
  color: rgba(255, 255, 255, 0.75);
  cursor: pointer;
  font-family: inherit;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  transition: background 0.2s;
}

.music-split-btn-new .music-split-icon {
  border-left-color: rgba(155, 140, 255, 0.15);
}

.music-split-icon:hover {
  background: rgba(0, 0, 0, 0.2);
}

/* Solid button (Shuffle) */
.music-action-btn-solid {
  flex: 1;
  min-height: 64px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
  padding: 8px 4px;
  border: none;
  border-radius: 16px;
  background: linear-gradient(180deg, rgba(236, 72, 153, 0.2) 0%, rgba(236, 72, 153, 0.07) 100%);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.08), 0 0 0 1px rgba(236, 72, 153, 0.24), 0 8px 24px -10px rgba(236, 72, 153, 0.3);
  color: #fff;
  cursor: pointer;
  font-family: inherit;
  position: relative;
  overflow: hidden;
  transition: background 0.2s;
}

.music-action-btn-solid:hover:not(:disabled) {
  background: linear-gradient(180deg, rgba(236, 72, 153, 0.25) 0%, rgba(236, 72, 153, 0.12) 100%);
}

.music-action-btn-solid:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.music-action-btn-solid i {
  font-size: 16px;
  color: #ec4899;
  filter: drop-shadow(0 0 8px rgba(236, 72, 153, 0.45));
}

.music-action-label {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.01em;
  white-space: nowrap;
}

.music-action-sub {
  font-size: 9.5px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
  white-space: nowrap;
}

/* Active filter drawer */
.music-filter-drawer {
  margin: 0 20px;
  padding: 10px 12px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

.music-filter-drawer--saved {
  background: linear-gradient(180deg, rgba(109, 220, 255, 0.14) 0%, rgba(109, 220, 255, 0.06) 100%);
  border-color: rgba(109, 220, 255, 0.24);
}

.music-filter-drawer--new {
  background: linear-gradient(180deg, rgba(155, 140, 255, 0.14) 0%, rgba(155, 140, 255, 0.06) 100%);
  border-color: rgba(155, 140, 255, 0.24);
}

.music-filter-drawer-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.music-filter-drawer-kicker {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
}

.music-filter-drawer-kicker i {
  font-size: 10px;
  color: #6ddcff;
}

.music-filter-drawer--new .music-filter-drawer-kicker i {
  color: #9b8cff;
}

.music-filter-drawer-title {
  font-size: 12px;
  font-weight: 700;
  color: #fff;
}

.music-filter-drawer-subtitle {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.56);
  line-height: 1.2;
}

.music-filter-drawer-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.music-filter-drawer-play {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 0 12px;
  min-height: 34px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.16);
  color: #fff;
  font-family: inherit;
  font-size: 12px;
  font-weight: 700;
  cursor: pointer;
  line-height: 1;
}

.music-filter-drawer-play:hover {
  background: rgba(0, 0, 0, 0.24);
}

.music-filter-drawer-close {
  width: 34px;
  height: 34px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.16);
  color: #fff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  line-height: 1;
}

.music-filter-drawer-close:hover {
  background: rgba(0, 0, 0, 0.24);
}

/* Sort drawer */
.music-sort-drawer {
  margin: 0 20px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  overflow: hidden;
  transition: all 0.2s ease;
}

.music-sort-drawer.expanded {
  border-radius: 14px 14px 0 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.music-sort-header {
  width: 100%;
  display: flex;
  align-items: stretch;
  height: 40px;
  padding: 0;
}

.music-sort-toggle {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: none;
  padding: 0 10px 0 12px;
  color: #fff;
  font-family: inherit;
  cursor: pointer;
  text-align: left;
  white-space: nowrap;
  overflow: hidden;
}

.music-sort-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
  flex-shrink: 0;
}

.music-sort-current {
  font-size: 12px;
  color: #fff;
  font-weight: 600;
  flex-shrink: 0;
}

.music-sort-sub {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
}

.music-sort-toggle i:last-of-type {
  margin-left: auto;
  font-size: 9px;
  color: rgba(255, 255, 255, 0.45);
  flex-shrink: 0;
  transition: transform 0.2s;
}

.music-sort-toggle i.rotated {
  transform: rotate(180deg);
}

/* Divider in header */
.music-sort-divider {
  width: 1px;
  background: rgba(255, 255, 255, 0.06);
  margin: 8px 0;
  flex-shrink: 0;
}


/* Sort options (expanded) */
.music-sort-options {
  display: flex;
  flex-direction: column;
  padding: 4px 4px 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.music-sort-options button {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 12px;
  border: none;
  border-radius: 10px;
  background: transparent;
  color: #fff;
  font-family: inherit;
  cursor: pointer;
  text-align: left;
  font-size: 13px;
  font-weight: 600;
  transition: background 0.15s;
}

.music-sort-options button:hover {
  background: rgba(255, 255, 255, 0.05);
}

.music-sort-options button.active {
  background: rgba(109, 220, 255, 0.1);
  color: #6ddcff;
}

.music-sort-options button i:first-child {
  font-size: 11px;
  width: 14px;
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.45);
}

.music-sort-options button.active i:first-child {
  color: #6ddcff;
}

.music-opt-label {
  flex: 1;
}

.music-opt-sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 400;
}

.music-sort-options button i:last-child {
  font-size: 10px;
  color: #6ddcff;
}

.track-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}
.add-to-playlist-btn {
  position: absolute;
  top: 8px;
  right: 8px;
}

.add-to-playlist-btn {
  border-radius: 50%;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-size: 12px;
}
.add-to-playlist-btn:hover {
  background: rgba(0, 0, 0, 0.8);
}
.track-duration {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 4px;
}
.empty-state {
  text-align: center;
  padding: 2rem;
  color: rgba(255, 255, 255, 0.7);
}
.empty-state i {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  opacity: 0.6;
}
.empty-state h3 {
  margin: 0 0 0.25rem;
  font-size: 1.1rem;
}
.empty-state p {
  margin: 0;
  font-size: 0.9rem;
}


.music-mobile-list {
  display: none;
}

.music-mobile-library-hero {
  display: none;
}

@media (max-width: 768px) {
  .music-filter-row {
    padding: 0 16px 4px;
  }

  .music-container {
    padding-left: 0 !important;
    padding-right: 0 !important;
    margin: 0 !important;
  }

  /* Force content area to be flush for this view */
  :deep(.content-area) {
    padding-left: 0 !important;
    padding-right: 0 !important;
    margin: 0 !important;
  }

  .music-container :deep(.content-header) {
    display: none !important;
  }

  .music-mobile-library-hero {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 58px;
    align-items: end;
    gap: 14px;
    margin: 18px var(--mobile-gutter, 10px) 12px;
    padding: 22px 16px 16px;
    border: 1px solid rgba(255, 255, 255, 0.075);
    border-radius: 28px;
    background:
      radial-gradient(circle at 16% 0%, rgba(109, 220, 255, 0.11), transparent 34%),
      radial-gradient(circle at 92% 18%, rgba(255, 0, 96, 0.09), transparent 36%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.014));
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.09),
      0 18px 44px rgba(0, 0, 0, 0.22);
    backdrop-filter: blur(24px) saturate(145%);
    -webkit-backdrop-filter: blur(24px) saturate(145%);
    transition: margin 0.18s ease, padding 0.18s ease, border-radius 0.18s ease;
  }

  .music-container--compact-hero .music-mobile-library-hero {
    margin-top: 8px;
    padding-top: 14px;
    padding-bottom: 12px;
    border-radius: 22px;
  }

  .music-container--compact-hero .music-mobile-hero-copy h1 {
    font-size: 31px;
  }

  .music-container--compact-hero .music-mobile-hero-play {
    width: 48px;
    height: 48px;
  }

  .music-mobile-hero-copy {
    min-width: 0;
  }

  .music-mobile-eyebrow {
    display: block;
    margin-bottom: 8px;
    color: rgba(255, 255, 255, 0.52);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .music-mobile-hero-copy h1 {
    margin: 0;
    color: #fff;
    font-size: 38px;
    font-weight: 900;
    letter-spacing: -0.06em;
    line-height: 0.95;
  }

  .music-mobile-hero-copy p {
    margin: 8px 0 0;
    color: rgba(255, 255, 255, 0.58);
    font-size: 12px;
    line-height: 1.3;
  }

  .music-mobile-hero-play {
    width: 58px;
    height: 58px;
    border: 0;
    border-radius: 999px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    color: #031108;
    background: linear-gradient(180deg, #56f08c 0%, #1ed760 100%);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.42),
      0 16px 30px rgba(30, 215, 96, 0.24);
  }

  .music-mobile-hero-play i {
    margin-left: 3px;
    font-size: 18px;
  }

  .music-mobile-hero-play:disabled {
    opacity: 0.45;
  }

  .music-command-center {
    padding: 0 var(--mobile-gutter, 10px) 10px;
    margin-top: 0 !important;
    gap: 8px;
  }

  .music-action-buttons {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr) minmax(86px, .8fr);
    gap: 8px;
    overflow: visible;
    padding: 2px 0 3px;
  }

  .music-action-buttons::-webkit-scrollbar {
    display: none;
  }

  .music-split-btn,
  .music-action-btn-solid {
    flex: 1 1 0;
    min-width: 0;
    width: 100%;
    min-height: 42px;
    border-radius: 999px;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.018)) !important;
    border: 1px solid rgba(255, 255, 255, 0.075) !important;
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.075),
      0 10px 22px rgba(0, 0, 0, 0.16) !important;
    backdrop-filter: blur(18px) saturate(150%);
    -webkit-backdrop-filter: blur(18px) saturate(150%);
  }

  .music-split-main {
    min-height: 40px;
    padding: 0 10px;
    flex-direction: row;
    gap: 7px;
  }

  .music-split-label {
    font-size: 12px;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .music-split-sub {
    display: none;
  }

  .music-split-icon-play {
    font-size: 12px;
  }

  .music-split-main .music-split-icon-play i:last-child {
    display: none;
  }

  .music-split-icon {
    display: none;
  }

  .music-action-btn-solid {
    min-width: 0;
    padding: 0 10px;
    flex-direction: row;
    gap: 7px;
    color: #fff;
  }

  .music-action-label {
    font-size: 12px;
  }

  .music-action-sub {
    display: none;
  }

  .music-action-btn-solid i {
    color: #ff4b9b;
    filter: none;
  }

  .music-filter-drawer {
    margin: 0;
    padding: 10px 10px 10px 12px;
    gap: 8px;
    align-items: center;
    justify-content: space-between;
    border-radius: 20px;
    backdrop-filter: blur(18px) saturate(150%);
    -webkit-backdrop-filter: blur(18px) saturate(150%);
  }

  .music-sort-drawer {
    margin: 0;
    border-radius: 20px;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.016));
    border-color: rgba(255, 255, 255, 0.075);
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.075);
    backdrop-filter: blur(20px) saturate(145%);
    -webkit-backdrop-filter: blur(20px) saturate(145%);
  }

  .music-sort-header {
    height: 42px;
    padding: 0;
  }

  .music-sort-label {
    font-size: 11px;
  }

  .music-sort-current {
    font-size: 12px;
  }

  .music-sort-sub {
    font-size: 10px;
  }

  .music-sort-options button {
    padding: 11px 12px;
    font-size: 13px;
  }

  .music-sort-options button i:first-child {
    font-size: 11px;
  }

  .music-opt-sub {
    font-size: 11px;
  }

  .music-filter-drawer-actions {
    align-self: center;
    margin-left: 0;
    gap: 6px;
  }

  .music-filter-drawer-play span {
    display: none;
  }

  .music-filter-drawer-play {
    width: 36px;
    min-width: 36px;
    flex: 0 0 36px;
    justify-content: center;
    padding: 0;
    border-radius: 12px;
    font-size: 0;
  }

  .music-filter-drawer-close {
    width: 36px;
    min-width: 36px;
    flex: 0 0 36px;
    border-radius: 12px;
  }

  .music-filter-drawer-play i,
  .music-filter-drawer-close i {
    font-size: 13px;
    line-height: 1;
  }

  .music-table-wrap {
    display: none;
  }

  .music-list {
    margin: 4px var(--mobile-gutter, 10px) 0 !important;
    border-radius: 24px !important;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.035), rgba(255, 255, 255, 0.012)) !important;
    border: 1px solid rgba(255, 255, 255, 0.065) !important;
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.06),
      0 18px 36px rgba(0, 0, 0, 0.18) !important;
    backdrop-filter: blur(22px) saturate(140%);
    -webkit-backdrop-filter: blur(22px) saturate(140%);
  }

  .music-mobile-list {
    display: flex;
    flex-direction: column;
    gap: 0;
    padding: 6px 0 !important;
    margin: 0 !important; /* Vital for flush look */
    width: 100% !important;
  }

  .music-mobile-row {
    display: grid;
    grid-template-columns: 52px minmax(0, 1fr) 40px;
    align-items: center;
    gap: 11px;
    min-height: 64px;
    padding: 7px 8px 7px 10px;
    border-radius: 0 !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 1px solid rgba(255, 255, 255, 0.055) !important;
    width: 100% !important;
    margin: 0 !important;
    box-shadow: none !important;
  }

  .music-mobile-row.playing {
    background: linear-gradient(90deg, rgba(30, 215, 96, 0.09), rgba(255, 255, 255, 0.012)) !important;
  }

  .music-mobile-row.playing .music-mobile-art::after {
    content: '';
    position: absolute;
    inset: -3px;
    border-radius: 11px;
    border: 1px solid rgba(30, 215, 96, 0.38);
    animation: mobile-now-playing-pulse 1.8s ease-in-out infinite;
    pointer-events: none;
  }

  .music-mobile-art {
    position: relative;
    width: 50px;
    height: 50px;
    border-radius: 8px;
    overflow: hidden;
    flex-shrink: 0;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.26);
  }

  .music-mobile-row:active {
    background: rgba(255, 255, 255, 0.05) !important;
    transform: scale(0.985);
    transition: transform 0.1s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .music-mobile-art-img {
    width: 100%;
    height: 100%;
    object-fit: cover;
    display: block;
    /* Trick 4: Fade in images so the 'snap' is less jarring */
    opacity: 0;
    transition: opacity 0.3s ease-out;
  }

  .music-mobile-art-img[src],
  .music-mobile-art-img.image-placeholder {
    opacity: 1;
  }

  .music-mobile-art-play {
    position: absolute;
    inset: 0;
    border: none;
    background: linear-gradient(180deg, rgba(0, 0, 0, 0.08), rgba(0, 0, 0, 0.48));
    color: #fff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    opacity: 0;
  }

  .music-mobile-row.playing .music-mobile-art-play {
    opacity: 1;
  }

  @keyframes mobile-now-playing-pulse {
    0%, 100% {
      opacity: 0.35;
      transform: scale(1);
    }
    50% {
      opacity: 0.85;
      transform: scale(1.04);
    }
  }

  .music-mobile-meta {
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    gap: 0 !important;
  }

  .music-mobile-title-link {
    color: inherit;
    text-decoration: none;
    min-width: 0 !important;
    min-height: 0 !important; /* Override global mobile touch target size */
    display: block;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.1 !important;
  }

  .music-mobile-title {
    display: block;
    font-size: 13px;
    font-weight: 500;
    color: rgba(255, 255, 255, 0.62);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.18 !important;
    margin-top: 3px !important;
  }

  .music-mobile-artist {
    display: block;
    font-size: 15px;
    font-weight: 800;
    color: rgba(255, 255, 255, 0.96);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin: 0 !important;
    padding: 0 !important;
    line-height: 1.14 !important;
  }

  .music-mobile-more {
    width: 40px;
    height: 40px;
    border: 0;
    border-radius: 999px;
    background: transparent;
    color: rgba(255, 255, 255, 0.62);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    font-size: 17px;
  }

  .music-mobile-more:active {
    background: rgba(255, 255, 255, 0.08);
  }
}

.music-mobile-action-layer {
  position: fixed;
  inset: 0;
  z-index: 10000;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  padding: calc(18px + env(safe-area-inset-top)) 14px 14px;
  background:
    radial-gradient(circle at 50% 0%, rgba(109, 220, 255, 0.14), transparent 34%),
    rgba(0, 0, 0, 0.28);
  backdrop-filter: blur(5px);
  -webkit-backdrop-filter: blur(5px);
}

.music-mobile-action-sheet {
  width: min(440px, 100%);
  padding: 12px;
  border-radius: 24px;
  border: 1px solid rgba(255, 255, 255, 0.13);
  background:
    radial-gradient(circle at 18% 0%, rgba(109, 220, 255, 0.15), transparent 34%),
    linear-gradient(180deg, rgba(31, 32, 38, 0.92), rgba(9, 10, 14, 0.92));
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.14),
    0 18px 54px rgba(0, 0, 0, 0.48);
  backdrop-filter: blur(28px) saturate(150%);
  -webkit-backdrop-filter: blur(28px) saturate(150%);
}

.music-mobile-action-track {
  display: grid;
  grid-template-columns: 54px minmax(0, 1fr);
  gap: 12px;
  align-items: center;
  padding: 2px 2px 12px;
}

.music-mobile-action-art {
  width: 54px;
  height: 54px;
  border-radius: 10px;
  object-fit: cover;
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.32);
}

.music-mobile-action-meta {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.music-mobile-action-meta strong,
.music-mobile-action-meta span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.music-mobile-action-meta strong {
  color: #fff;
  font-size: 15px;
}

.music-mobile-action-meta span {
  color: rgba(255, 255, 255, 0.56);
  font-size: 13px;
}

.music-mobile-action-buttons {
  display: grid;
  gap: 6px;
}

.music-mobile-action-buttons button {
  min-height: 46px;
  border: 0;
  border-radius: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 14px;
  color: rgba(255, 255, 255, 0.92);
  background: rgba(255, 255, 255, 0.055);
  font: inherit;
  font-size: 14px;
  font-weight: 700;
  text-align: left;
}

.music-mobile-action-buttons button i {
  width: 18px;
  color: #6ddcff;
  text-align: center;
}


</style>
