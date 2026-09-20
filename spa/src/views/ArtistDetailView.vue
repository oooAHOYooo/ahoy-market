<template>
  <div class="artist-page-container">


    <!-- Loading State -->
    <div v-if="loading" class="loading-state">
       <div class="text-center">
          <i class="fas fa-spinner fa-spin"></i> Loading Artist...
       </div>
    </div>

    <template v-else-if="artist">
      <!-- Artist Hero Section: Centered with circular image -->
      <section class="artist-hero" :style="{ backgroundImage: `url(${artist.image || '/static/img/default-avatar.png'})` }">
        <button class="back-btn" @click="goBack" aria-label="Back to artists">
          <i class="fas fa-chevron-left" aria-hidden="true"></i>
          <span class="sr-only">Back to artists</span>
        </button>
        <div class="hero-content">
          <!-- Circular Profile Image with Glow -->
          <div class="profile-image-wrapper">
            <div class="glow-background"></div>
            <img :src="artist.image || '/static/img/default-avatar.png'" :alt="artist.name" class="profile-image" />
          </div>

          <!-- Artist Info -->
          <div class="artist-info-center">
            <p class="artist-subtitle">{{ artist.genre || 'Artist' }}</p>
            <h1 class="artist-name-large">{{ artist.name }}</h1>
          </div>

          <!-- Action Buttons -->
          <div class="action-buttons">
            <button class="icon-btn" :class="{ 'btn-active': bookmarks.isBookmarked(artist) }" @click="onFollow" :title="bookmarks.isBookmarked(artist) ? 'Following' : 'Follow'">
              <i :class="bookmarks.isBookmarked(artist) ? 'fas fa-check-circle' : 'fas fa-circle-check'"></i>
            </button>
            <button class="icon-btn" @click="goToBoost" title="Boost">
              <i class="fas fa-bolt"></i>
            </button>
            <button class="icon-btn" @click="onShareArtist" title="Share">
              <i class="fas fa-share"></i>
            </button>
            <button class="icon-btn" @click="router.push({ path: '/search', query: { q: artist.name } })" title="Search">
              <i class="fas fa-search"></i>
            </button>
          </div>
        </div>
      </section>

      <!-- Videos Section -->
      <section class="videos-section" v-if="artistShows.length">
        <div class="section-header">
          <h2 class="section-title">Videos</h2>
          <router-link v-if="artistShows.length > 4" to="/videos" class="see-all-link">See all</router-link>
        </div>

        <div class="video-grid">
           <component
             v-for="show in artistShows.slice(0, 4)"
             :key="show.id"
             :is="getVideoCardComponent(show)"
             v-bind="getVideoCardAttrs(show)"
             class="video-card"
           >
              <div class="video-thumbnail">
                 <img :src="show.thumbnail || '/static/img/default-cover.jpg'" loading="lazy" :alt="show.title" />
                 <div class="video-overlay"></div>
              </div>
              <div class="video-info">
                <h3 class="video-title">{{ show.title }}</h3>
                <div class="video-meta">
                  <span class="upload-date">{{ formatDate(show.created_at) }}</span>
                </div>
              </div>
           </component>
        </div>
      </section>

      <!-- Music Section -->
      <section class="albums-section" v-if="artistAlbumGroups.length">
        <div class="section-header">
          <h2 class="section-title">Music</h2>
          <span class="section-count">{{ artistAlbumGroups.length }}</span>
        </div>

        <div class="album-group-list">
          <article v-for="album in artistAlbumGroups" :key="album.key" class="album-group">
            <button type="button" class="album-group-header" @click="playTracks(album.tracks, 0)">
              <div class="album-group-cover">
                <img :src="album.coverArt || '/static/img/default-cover.jpg'" loading="lazy" :alt="album.title" />
                <span class="album-group-play">
                  <i class="fas fa-play"></i>
                </span>
              </div>
              <div class="album-group-copy">
                <p class="album-group-kicker">Album</p>
                <h3 class="album-group-title">{{ album.title }}</h3>
                <p class="album-group-meta">
                  <span>{{ album.trackCount }} tracks</span>
                  <span v-if="album.releaseDate">{{ formatReleaseDate(album.releaseDate) }}</span>
                </p>
              </div>
            </button>

            <div class="album-track-list">
              <button
                v-for="(track, index) in album.tracks"
                :key="track.id"
                type="button"
                class="album-track-row"
                @click="playTracks(album.tracks, index)"
              >
                <span class="album-track-number">{{ index + 1 }}</span>
                <div class="album-track-copy">
                  <span class="album-track-title">{{ track.title }}</span>
                  <span class="album-track-subtitle">{{ track.genre || track.artist || 'Track' }}</span>
                </div>
                <span class="album-track-duration">{{ formatDuration(track.duration_seconds) }}</span>
              </button>
            </div>
          </article>
        </div>
      </section>

      <section class="singles-section" v-if="artistSingles.length">
        <div class="section-header">
          <h2 class="section-title">{{ artistAlbumGroups.length ? 'Other Tracks' : 'Music' }}</h2>
        </div>

        <div class="music-grid">
          <div
            v-for="(t, idx) in artistSingles"
            :key="t.id"
            class="album-card"
            @click="playTrack(t, artistSingles, idx)"
          >
            <div class="album-artwork">
              <img :src="t.cover_art || '/static/img/default-cover.jpg'" loading="lazy" :alt="t.title" />
              <div class="album-overlay">
                <div class="play-button">
                  <i class="fas fa-play"></i>
                </div>
              </div>
            </div>
            <h4 class="album-title">{{ t.title }}</h4>
          </div>
        </div>
      </section>

      <!-- Podcasts Section -->
      <section class="podcasts-section" v-if="artistPodcasts.length">
        <div class="section-header">
          <h2 class="section-title">Podcasts</h2>
          <router-link v-if="artistPodcasts.length > 4" to="/podcasts" class="see-all-link">See all</router-link>
        </div>
        <div class="video-grid">
           <router-link
             v-for="show in artistPodcasts.slice(0, 4)"
             :key="show.slug"
             :to="`/podcasts/${show.slug}`"
             class="video-card"
           >
              <div class="video-thumbnail">
                 <img :src="show.artwork || '/static/img/default-cover.jpg'" loading="lazy" :alt="show.title" />
                 <div class="video-overlay"></div>
              </div>
              <div class="video-info">
                <h3 class="video-title">{{ show.title }}</h3>
                <div class="video-meta">
                  <span>Podcast</span>
                </div>
              </div>
           </router-link>
        </div>
      </section>

      <!-- Poems Section -->
      <section class="poems-section" v-if="artistPoems.length">
        <div class="section-header">
          <h2 class="section-title">Poems</h2>
          <router-link v-if="artistPoems.length > 4" to="/poems" class="see-all-link">See all</router-link>
        </div>

        <div class="poem-grid">
          <router-link
            v-for="poem in artistPoems.slice(0, 4)"
            :key="poem.poem_id"
            :to="`/poems/${poem.poem_id}`"
            class="poem-card"
          >
            <div class="poem-card-kicker">Poem</div>
            <h3 class="poem-card-title">{{ poem.title }}</h3>
            <div class="poem-card-meta">
              <span>{{ formatPoemDate(poem.published_at) }}</span>
              <span v-if="poem.note">{{ poem.note }}</span>
            </div>
            <div class="poem-card-preview">{{ firstLines(poem.body_text) }}</div>
            <div class="poem-card-read">Read poem →</div>
          </router-link>
        </div>
      </section>

      <!-- Photography Section -->
      <section class="photography-section" v-if="artistPhotography.length">
        <div class="section-header">
          <h2 class="section-title">Photography</h2>
          <router-link v-if="artistPhotography.length > 4" to="/studio" class="see-all-link">See all</router-link>
        </div>

        <div class="photo-collection-grid">
          <router-link
            v-for="collection in artistPhotography.slice(0, 4)"
            :key="collection.id"
            :to="`/studio/${collection.collection_id}`"
            class="photo-collection-card"
          >
            <div class="photo-collection-thumbnail">
              <img :src="collection.cover || '/static/img/default-cover.jpg'" loading="lazy" :alt="collection.title" />
              <div class="photo-collection-overlay"></div>
              <div class="photo-collection-badge">{{ collection.photo_count }} photos</div>
            </div>
            <div class="photo-collection-info">
              <h3 class="photo-collection-title">{{ collection.title }}</h3>
              <div class="photo-collection-meta">
                <span>{{ formatDate(collection.date) }}</span>
              </div>
            </div>
          </router-link>
        </div>
      </section>

      <!-- Empty State -->
      <section class="empty-state" v-if="!artistTracks.length && !artistShows.length && !artistPodcasts.length && !artistPoems.length && !artistPhotography.length">
         <i class="fas fa-ghost"></i>
         <p>No content found for this artist yet.</p>
      </section>



    </template>
    
    <!-- Not Found -->
    <div v-else class="loading-state">
       <div class="glass-panel text-center">
          <i class="fas fa-exclamation-triangle"></i> Artist not found
       </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { trackEvent } from '../composables/useAnalytics'
import { apiFetch, apiFetchCached } from '../composables/useApi'
import { useBookmarks } from '../composables/useBookmarks'
import { useAuth } from '../composables/useAuth'
import { usePlayerStore } from '../stores/player'
import { useShare, useHaptics } from '../composables/useNative'
import { useStripe } from '../composables/useStripe'
import { videoUrl } from '../utils/urls'
import { setSeoMeta } from '../composables/useSeoMeta'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()
import { useCartStore } from '../stores/cart'
const cartStore = useCartStore()
const auth = useAuth()
const bookmarks = useBookmarks()
const { shareArtist } = useShare()
const haptics = useHaptics()
const { initStripe, createPaymentIntent, confirmBoost } = useStripe()

const loading = ref(true)
const artist = ref(null)
const allArtists = ref([])
const allTracks = ref([])
const allShows = ref([])
const allPodcastShows = ref([])
const allPoems = ref([])
const allStudioCollections = ref([])

const artistTracks = computed(() => {
  if (!artist.value) return []
  const artistKey = normalizeKey(artist.value.slug || artist.value.id || artist.value.name)
  return allTracks.value.filter(t =>
    normalizeKey(t.artist_slug || t.artist_id || t.artist || t.artist_name) === artistKey ||
    normalizeKey(t.artist) === normalizeKey(artist.value.name) ||
    normalizeKey(t.artist_id) === normalizeKey(artist.value.id)
  ).slice().sort(compareTrackOrder)
})

const artistShows = computed(() => {
  if (!artist.value) return []
  const artistKey = normalizeKey(artist.value.slug || artist.value.id || artist.value.name)
  const seenIds = new Set()
  return allShows.value.filter(s => {
    const matches = (
      normalizeKey(s.host_slug || s.host_id || s.host || s.filmmaker_slug || s.filmmaker) === artistKey ||
      normalizeKey(s.host) === normalizeKey(artist.value.name) ||
      normalizeKey(s.filmmaker) === normalizeKey(artist.value.name)
    )
    if (matches && !seenIds.has(s.id)) {
      seenIds.add(s.id)
      return true
    }
    return false
  })
})

const artistPodcasts = computed(() => {
  if (!artist.value) return []
  const artistKey = normalizeKey(artist.value.slug || artist.value.id || artist.value.name)
  return allPodcastShows.value.filter(s =>
    (s.episodes || []).some(ep =>
      normalizeKey(ep.host_slug || ep.artist_slug || ep.host || ep.artist) === artistKey ||
      normalizeKey(ep.host) === normalizeKey(artist.value.name) ||
      normalizeKey(ep.artist) === normalizeKey(artist.value.name)
    ) ||
    normalizeKey(s.host_slug || s.host) === artistKey
  )
})

const artistPoems = computed(() => {
  if (!artist.value) return []
  const artistKey = normalizeKey(artist.value.slug || artist.value.id || artist.value.name)
  return allPoems.value.filter(poem =>
    normalizeKey(poem.poet_slug || poem.poet_name) === artistKey ||
    normalizeKey(poem.poet_name) === normalizeKey(artist.value.name)
  )
})

const artistPhotography = computed(() => {
  if (!artist.value) return []
  const artistKey = normalizeKey(artist.value.slug || artist.value.id || artist.value.name)
  return allStudioCollections.value.filter(collection =>
    normalizeKey(collection.photographer_slug) === artistKey
  )
})

const artistAlbumGroups = computed(() => {
  if (!artist.value) return []

  const tracks = artistTracks.value.slice()
  if (!tracks.length) return []

  const assignedTrackIds = new Set()
  const trackById = new Map()
  const trackByTitle = new Map()

  for (const track of tracks) {
    const idKey = String(track.id ?? track.track_id ?? '')
    if (idKey) trackById.set(idKey, track)
    trackByTitle.set(normalizeKey(track.title), track)
  }

  const groups = []
  const groupByKey = new Map()
  const artistAlbums = Array.isArray(artist.value.albums) ? artist.value.albums : []
  let albumOrder = 0

  const registerGroup = (source = {}) => {
    const key = normalizeKey(source.key || source.id || source.title || source.album || '')
    if (!key) return null
    if (groupByKey.has(key)) return groupByKey.get(key)

    const group = {
      key,
      title: source.title || source.album || 'Album',
      coverArt: source.coverArt || source.cover_art || source.image || '',
      releaseDate: source.releaseDate || source.release_date || '',
      tracks: [],
      order: source.order ?? albumOrder,
    }
    albumOrder += 1
    groupByKey.set(key, group)
    groups.push(group)
    return group
  }

  const addTrackToGroup = (group, track) => {
    if (!group || !track) return
    const trackId = String(track.id ?? track.track_id ?? '')
    if (trackId && assignedTrackIds.has(trackId)) return
    if (trackId) assignedTrackIds.add(trackId)
    group.tracks.push(track)
  }

  const isGroupedAlbumName = (value) => {
    const key = normalizeKey(value)
    if (!key) return false
    return !['single', 'singles', 'track', 'tracks', 'misc', 'miscellaneous', 'other', 'unknown', 'untitled'].includes(key)
  }

  for (const album of artistAlbums) {
    const albumTitle = album?.title || album?.album || album?.name || ''
    if (!isGroupedAlbumName(albumTitle)) continue

    const group = registerGroup({
      key: album.id || albumTitle,
      title: albumTitle,
      coverArt: album.cover_art || album.coverArt || album.image || '',
      releaseDate: album.release_date || album.releaseDate || '',
    })
    if (!group) continue

    const albumTracks = Array.isArray(album.tracks) ? album.tracks : []
    for (const ref of albumTracks) {
      const refId = String(ref?.id || ref?.track_id || ref || '')
      const matchedTrack = (refId && trackById.get(refId)) || trackByTitle.get(normalizeKey(ref?.title || ref?.name || ''))
      if (matchedTrack) addTrackToGroup(group, matchedTrack)
    }
  }

  for (const track of tracks) {
    const albumName = track.album || track.album_title || track.album_name || ''
    if (!isGroupedAlbumName(albumName)) continue

    const key = normalizeKey(albumName)
    let group = groupByKey.get(key)
    if (!group) {
      group = registerGroup({
        key: albumName,
        title: albumName,
        coverArt: track.cover_art || track.album_cover_art || track.album_art || artist.value.image || '',
        releaseDate: track.release_date || track.date_added || track.added_date || '',
      })
    }
    addTrackToGroup(group, track)
  }

  for (const group of groups) {
    group.tracks.sort(compareTrackOrder)
    group.trackCount = group.tracks.length
    if (!group.coverArt) {
      group.coverArt = group.tracks[0]?.cover_art || group.tracks[0]?.album_art || artist.value.image || ''
    }
    if (!group.releaseDate) {
      group.releaseDate = group.tracks[0]?.release_date || group.tracks[0]?.date_added || group.tracks[0]?.added_date || ''
    }
  }

  groups.sort((a, b) => {
    if (a.order !== b.order) return a.order - b.order
    return a.title.localeCompare(b.title, undefined, { sensitivity: 'base', numeric: true })
  })

  return groups.filter(group => group.tracks.length > 0)
})

const artistSingles = computed(() => {
  if (!artist.value) return []
  const groupedTrackIds = new Set(
    artistAlbumGroups.value.flatMap(group => group.tracks.map(track => String(track.id ?? track.track_id ?? '')))
  )

  return artistTracks.value
    .filter(track => !groupedTrackIds.has(String(track.id ?? track.track_id ?? '')))
    .sort(compareTrackOrder)
})




function normalizeKey(value) {
  return String(value || '').trim().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '')
}

function compareTrackOrder(a, b) {
  const aPos = Number(a?.position ?? a?.track_number ?? a?.track ?? a?.track_order)
  const bPos = Number(b?.position ?? b?.track_number ?? b?.track ?? b?.track_order)
  const aHasPos = Number.isFinite(aPos)
  const bHasPos = Number.isFinite(bPos)

  if (aHasPos && bHasPos && aPos !== bPos) return aPos - bPos
  if (aHasPos !== bHasPos) return aHasPos ? -1 : 1

  const aDate = Number(new Date(a?.date_added || a?.added_date || a?.release_date || 0))
  const bDate = Number(new Date(b?.date_added || b?.added_date || b?.release_date || 0))
  if (Number.isFinite(aDate) && Number.isFinite(bDate) && aDate !== bDate) return aDate - bDate

  return String(a?.title || '').localeCompare(String(b?.title || ''), undefined, { sensitivity: 'base', numeric: true })
}

function formatDuration(seconds) {
  const total = Number(seconds)
  if (!Number.isFinite(total) || total <= 0) return ''
  const m = Math.floor(total / 60)
  const s = Math.floor(total % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatReleaseDate(value) {
  if (!value) return ''
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return String(value)
  return parsed.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
}

function formatPoemDate(value) {
  if (!value) return 'Poem'
  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) return 'Poem'
  return parsed.toLocaleDateString(undefined, { month: 'short', year: 'numeric' })
}

function firstLines(text, n = 3) {
  if (!text) return ''
  return text
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean)
    .slice(0, n)
    .join(' / ')
}

function formatVideoDuration(seconds) {
  const total = Number(seconds)
  if (!Number.isFinite(total) || total <= 0) return '00:00'
  const h = Math.floor(total / 3600)
  const m = Math.floor((total % 3600) / 60)
  const s = Math.floor(total % 60)
  if (h > 0) return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  return `${m}:${s.toString().padStart(2, '0')}`
}

function formatDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

  if (diffDays === 0) return 'Today'
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  if (diffDays < 365) return `${Math.floor(diffDays / 30)} months ago`
  return `${Math.floor(diffDays / 365)} years ago`
}

function getShowVideoHref(show) {
  return videoUrl(show)
}

function getVideoCardComponent(show) {
  return 'router-link'
}

function getVideoCardAttrs(show) {
  return {
    to: getShowVideoHref(show),
  }
}

function goBack() {
  router.push('/artists')
}

function onFollow() {
  haptics.onBookmark()
  bookmarks.toggle({ ...artist.value, _type: 'artist' })
}

function onShareArtist() {
  haptics.light()
  shareArtist(artist.value)
}

function playTracks(queue, idx = 0) {
  if (!Array.isArray(queue) || !queue.length) return
  playerStore.setQueue(queue, idx)
}

function playTrack(track, queue = artistTracks.value, idx = 0) {
  if (!track) return
  playTracks(queue, idx)
}

function goToBoost() {
  if (!artist.value) return
  if (!auth.isLoggedIn.value) { router.push('/login'); return }
  haptics.light()
  cartStore.addBoost(artist.value.name, artist.value.name, artist.value.slug, 0.50)
  window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: `Added $0.50 boost for ${artist.value.name} to cart!`, type: 'success' } }))
}



onMounted(async () => {
  const slug = route.params.slug
  try {
    const [artistsData, musicData, showsData, podcastsData, poemsData, studioData] = await Promise.all([
        apiFetchCached('/api/artists').catch(() => ({ artists: [] })),
        apiFetchCached('/api/music').catch(() => ({ tracks: [] })),
        apiFetchCached('/api/shows').catch(() => ({ shows: [] })),
        apiFetchCached('/api/podcasts').catch(() => ({ shows: [] })),
        apiFetchCached('/api/poems').catch(() => ({ poems: [] })),
        apiFetchCached('/api/studio').catch(() => ({ collections: [] })),
    ])
    allArtists.value = artistsData.artists || []
    allTracks.value = musicData.tracks || []
    allShows.value = showsData.shows || []
    allPodcastShows.value = podcastsData.shows || []
    allPoems.value = poemsData.poems || []
    allStudioCollections.value = studioData.collections || []

    const normalizedSlug = normalizeKey(slug)
    artist.value = allArtists.value.find(a =>
        normalizeKey(a.slug) === normalizedSlug || String(a.id) === String(slug)
    ) || null

    if (!artist.value) {
      const matchingTrack = allTracks.value.find(t =>
        normalizeKey(t.artist_slug || t.artist_id || t.artist || t.artist_name) === normalizedSlug
      )
      if (matchingTrack) {
        artist.value = {
          id: matchingTrack.artist_id || matchingTrack.artist_slug || matchingTrack.artist || slug,
          slug: matchingTrack.artist_slug || normalizeKey(matchingTrack.artist || slug),
          name: matchingTrack.artist || matchingTrack.artist_name || slug,
          image: matchingTrack.artist_image || matchingTrack.cover_art || null,
          genre: matchingTrack.genre || matchingTrack.genres?.[0] || 'Artist',
        }
      }
    }
    if (artist.value) {
      setSeoMeta({
        title: artist.value.name,
        description: artist.value.bio || `Listen to ${artist.value.name} on Ahoy Indie Media.`,
        image: artist.value.image || '/static/img/ahoy_logo.png',
        type: 'profile',
        url: window.location.pathname,
      })
      trackEvent('artist_page_viewed', {
        artist_id: artist.value.id || artist.value.slug || null,
        artist_name: artist.value.name || '',
        artist_genre: artist.value.genre || '',
        track_count: artistTracks.value.length,
      })
    }
  } catch (e) {
      console.error(e)
  } finally {
      loading.value = false
  }
})
</script>

<style scoped>
/* Root Styles */
.artist-page-container {
  width: 100%;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
  min-height: 100dvh;
  background: #0e0e0f;
  color: #e7e5e8;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Artist Hero Section */
.artist-hero {
  margin-top: 20px;
  padding: 48px 24px 28px;
  display: flex;
  justify-content: center;
  align-items: center;
  background-size: cover;
  background-position: center;
  background-attachment: fixed;
  position: relative;
  overflow: hidden;
  min-height: 380px;
  box-shadow: inset 0 0 40px rgba(0, 0, 0, 0.4);
  filter: saturate(2);
}

.artist-hero::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(0, 0, 0, 0.6) 0%, rgba(0, 0, 0, 0.4) 100%);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  pointer-events: none;
}

.hero-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24px;
  max-width: 100%;
  position: relative;
  z-index: 1;
}

/* Profile Image */
.profile-image-wrapper {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
}

.glow-background {
  position: absolute;
  width: 240px;
  height: 240px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(189, 194, 255, 0.2) 0%, transparent 70%);
  filter: blur(40px);
  animation: pulse-glow 3s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% { transform: scale(1); opacity: 0.6; }
  50% { transform: scale(1.1); opacity: 0.8; }
}

@media (max-width: 768px) {
  .glow-background {
    display: none;
  }

  .artist-hero {
    background-attachment: scroll;
  }
}

.profile-image {
  width: 160px;
  height: 160px;
  border-radius: 50%;
  object-fit: cover;
  border: 3px solid rgba(189, 194, 255, 0.2);
  box-shadow: 0 0 32px rgba(189, 194, 255, 0.15);
  filter: saturate(0.52) brightness(1);
  transition: all 0.7s ease;
  position: relative;
  z-index: 1;
}

.profile-image:hover {
  filter: grayscale(0%) brightness(1.05);
  box-shadow: 0 0 48px rgba(189, 194, 255, 0.25);
}

/* Artist Info */
.artist-info-center {
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.artist-subtitle {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: rgba(172, 170, 174, 0.8);
  margin: 0;
}

.artist-name-large {
  font-size: 48px;
  font-weight: 900;
  letter-spacing: -1.5px;
  text-transform: uppercase;
  margin: 0;
  color: #e7e5e8;
}

@media (max-width: 768px) {
  .artist-name-large {
    font-size: 36px;
  }
}

/* Action Buttons */
.action-buttons {
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: center;
}

.icon-btn {
  width: 48px;
  height: 48px;
  border: none;
  background: rgba(189, 194, 255, 0.08);
  border: 1px solid rgba(189, 194, 255, 0.15);
  color: #bdc2ff;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  transition: all 0.2s ease;
}

.icon-btn:hover {
  background: rgba(189, 194, 255, 0.15);
  border-color: rgba(189, 194, 255, 0.3);
  transform: scale(1.05);
}

.icon-btn:active {
  transform: scale(0.95);
}

.icon-btn.btn-active {
  background: rgba(0, 220, 100, 0.15);
  border-color: rgba(0, 220, 100, 0.3);
  color: #00dc6a;
}

/* Back Button */
.back-btn {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;
  width: 40px;
  height: 40px;
  border: none;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: rgba(255, 255, 255, 0.85);
  cursor: pointer;
  font-size: 15px;
  font-weight: 600;
  border-radius: 12px;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: center;
  padding: 0;
  box-sizing: border-box;
}

.back-btn:hover {
  background: rgba(0, 0, 0, 0.6);
  color: #fff;
  transform: translateX(-2px);
}

.back-btn:active {
  transform: scale(0.95);
}

.back-btn i {
  line-height: 1;
}

@media (max-width: 768px) {
  .back-btn {
    top: 12px;
    left: 12px;
    width: 38px;
    height: 38px;
    border-radius: 11px;
  }
}

/* Stats Section */
.stats-section {
  border-top: none;
  border-bottom: none;
  padding: 16px 24px;
}

.stats-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  max-width: 500px;
  margin: 0 auto;
}

.stat-item {
  text-align: center;
  padding: 0;
  background: transparent;
}

.stat-label {
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(231, 229, 232, 0.35);
  margin: 0 0 4px 0;
}

.stat-value {
  font-size: 13px;
  font-weight: 500;
  color: rgba(231, 229, 232, 0.5);
  margin: 0;
}

.stat-divider {
  display: none;
}

/* Sections */
.videos-section,
.albums-section,
.singles-section,
.music-section,
.podcasts-section {
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 16px;
}

.section-title {
  font-size: 24px;
  font-weight: 800;
  letter-spacing: -0.5px;
  text-transform: uppercase;
  margin: 0;
}

.section-count {
  font-size: 12px;
  font-weight: 700;
  color: rgba(172, 170, 174, 0.8);
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.see-all-link {
  font-size: 13px;
  font-weight: 600;
  color: rgba(189, 194, 255, 0.6);
  text-decoration: none;
  letter-spacing: 0.05em;
  transition: color 0.2s;
}

.see-all-link:hover {
  color: #bdc2ff;
}

/* Video Grid */
.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 24px;
}

@media (max-width: 768px) {
  .video-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
}

.video-card {
  text-decoration: none;
  cursor: pointer;
  transition: transform 0.3s;
}

.video-card:hover {
  transform: translateY(-4px);
}

.video-thumbnail {
  position: relative;
  aspect-ratio: 16/9;
  border-radius: 16px;
  overflow: hidden;
  background: #000;
  margin-bottom: 12px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
}

.video-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.video-card:hover .video-thumbnail img {
  transform: scale(1.05);
}

.video-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.2);
  transition: background 0.3s;
}

.video-card:hover .video-overlay {
  background: rgba(0, 0, 0, 0);
}

.video-duration {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(12px);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.1em;
}

.video-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.video-title {
  font-size: 16px;
  font-weight: 700;
  color: #e7e5e8;
  margin: 0;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.video-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: rgba(172, 170, 174, 0.8);
}

.view-count {
  white-space: nowrap;
}

.upload-date {
  white-space: nowrap;
}

.meta-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
}

/* Poem Grid */
.poems-section {
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.poem-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 20px;
}

.poem-card {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 20px;
  border-radius: 16px;
  text-decoration: none;
  color: inherit;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.05), rgba(255, 255, 255, 0.02)),
    rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.18);
  transition: transform 0.25s ease, border-color 0.25s ease, background 0.25s ease;
}

.poem-card:hover {
  transform: translateY(-4px);
  border-color: rgba(189, 194, 255, 0.28);
  background:
    linear-gradient(180deg, rgba(189, 194, 255, 0.08), rgba(255, 255, 255, 0.03)),
    rgba(255, 255, 255, 0.03);
}

.poem-card-kicker {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(172, 170, 174, 0.8);
}

.poem-card-title {
  margin: 0;
  font-size: 20px;
  line-height: 1.15;
  font-weight: 800;
  color: #e7e5e8;
}

.poem-card-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 10px;
  font-size: 12px;
  color: rgba(172, 170, 174, 0.8);
}

.poem-card-meta span + span::before {
  content: '•';
  margin-right: 10px;
  color: rgba(172, 170, 174, 0.45);
}

.poem-card-preview {
  font-size: 14px;
  line-height: 1.6;
  color: rgba(231, 229, 232, 0.84);
  min-height: 4.8em;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.poem-card-read {
  margin-top: auto;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(189, 194, 255, 0.78);
}

/* Photography Section */
.photography-section {
  padding: 40px 24px;
  background: #0e0e0f;
}

.photo-collection-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.photo-collection-card {
  text-decoration: none;
  color: inherit;
  overflow: hidden;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  height: 100%;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.photo-collection-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4);
}

.photo-collection-thumbnail {
  position: relative;
  width: 100%;
  aspect-ratio: 1;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
}

.photo-collection-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s ease;
}

.photo-collection-card:hover .photo-collection-thumbnail img {
  transform: scale(1.05);
}

.photo-collection-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.photo-collection-card:hover .photo-collection-overlay {
  opacity: 1;
}

.photo-collection-badge {
  position: absolute;
  bottom: 12px;
  right: 12px;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
  z-index: 1;
}

.photo-collection-info {
  padding: 16px;
  flex-grow: 1;
  display: flex;
  flex-direction: column;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-top: none;
  border-radius: 0 0 12px 12px;
}

.photo-collection-title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 700;
  color: #e7e5e8;
  line-height: 1.4;
}

.photo-collection-meta {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  margin-top: auto;
}

/* Track List */
.track-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.track-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  cursor: pointer;
  transition: all 0.2s;
}

.track-row:hover {
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.1);
}

.track-row.playing {
  background: rgba(0, 255, 0, 0.1);
  border-color: rgba(0, 255, 0, 0.2);
}

.track-art {
  position: relative;
  width: 48px;
  height: 48px;
  border-radius: 8px;
  overflow: hidden;
  flex-shrink: 0;
  background: #000;
}

.track-art img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.track-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  opacity: 0;
  transition: opacity 0.2s;
}

.track-row:hover .track-overlay {
  opacity: 1;
}

.track-info {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.track-title {
  font-size: 14px;
  font-weight: 600;
  color: #e7e5e8;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.track-meta {
  font-size: 12px;
  color: rgba(172, 170, 174, 0.7);
}

.track-action {
  background: none;
  border: none;
  color: rgba(189, 194, 255, 0.6);
  cursor: pointer;
  font-size: 16px;
  transition: color 0.2s;
}

.track-action:hover {
  color: #bdc2ff;
}

/* Loading & Empty States */
.loading-state {
  padding: 64px 24px;
  text-align: center;
  color: rgba(231, 229, 232, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  margin-top: 56px;
}

.empty-state {
  padding: 64px 24px;
  text-align: center;
  color: rgba(231, 229, 232, 0.5);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  min-height: 40vh;
}

.empty-state i {
  font-size: 48px;
  opacity: 0.4;
}

.empty-state p {
  margin: 0;
  font-size: 16px;
}

/* Boost Modal */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  z-index: 999999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}

.boost-modal {
  width: 100%;
  max-width: 480px;
  background: #141f38;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 32px;
  position: relative;
  pointer-events: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.boost-modal h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 700;
  color: #dee5ff;
  letter-spacing: -0.5px;
}

.boost-modal > p {
  margin: 0 0 24px 0;
  font-size: 14px;
  color: #a3aac4;
}

.close-modal {
  position: absolute;
  top: 16px;
  right: 16px;
  background: none;
  border: none;
  color: #69daff;
  font-size: 24px;
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.close-modal:hover {
  color: #17c0fd;
}

.close-modal:active {
  transform: scale(0.95);
}

.boost-amount-selector {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin: 24px 0;
}

.boost-amount-selector button {
  background: #192540;
  border: none;
  color: #dee5ff;
  padding: 12px 8px;
  border-radius: 12px;
  font-weight: 700;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s;
}

.boost-amount-selector button:hover {
  background: #1f2b49;
}

.boost-amount-selector button:active {
  transform: scale(0.95);
}

.boost-amount-selector button.active {
  background: #17c0fd;
  color: #002a35;
  font-weight: 700;
}

.custom-amount {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  margin: 20px 0;
}

.custom-amount span {
  font-size: 28px;
  font-weight: 700;
  color: #69daff;
}

.custom-amount input {
  background: transparent;
  border: none;
  color: #dee5ff;
  font-size: 28px;
  font-weight: 700;
  width: 80px;
  text-align: center;
  outline: none;
  font-family: inherit;
}

.custom-amount input::placeholder {
  color: #1f2b49;
}

.fee-breakdown {
  margin: 24px 0;
  padding: 20px;
  background: #192540;
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.fee-item {
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #a3aac4;
}

.fee-item.total {
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(109, 117, 140, 0.2);
  color: #dee5ff;
  font-weight: 700;
  font-size: 16px;
}

.stripe-element {
  background: #0f1930;
  padding: 16px;
  border-radius: 12px;
  border: 1px solid rgba(109, 117, 140, 0.2);
  margin-bottom: 20px;
  color: #dee5ff;
}

.btn-boost-submit {
  width: 100%;
  padding: 14px;
  background: linear-gradient(135deg, #69daff, #00cffc);
  border: none;
  color: #002a35;
  border-radius: 12px;
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 16px rgba(105, 218, 255, 0.2);
}

.btn-boost-submit:hover {
  box-shadow: 0 6px 24px rgba(105, 218, 255, 0.3);
}

.btn-boost-submit:active {
  transform: scale(0.95);
}

.btn-boost-submit:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.boost-error {
  color: #ff716c;
  background: rgba(255, 113, 108, 0.1);
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 16px;
  font-size: 13px;
}

.boost-note {
  font-size: 11px;
  color: #a3aac4;
  margin: 16px 0 0 0;
  line-height: 1.4;
}

/* Music Grid */
.music-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 20px;
}

/* Album Card */
.album-card {
  cursor: pointer;
  transition: transform 0.3s ease;
}

.album-card:hover {
  transform: translateY(-4px);
}

.album-artwork {
  position: relative;
  aspect-ratio: 1/1;
  border-radius: 12px;
  overflow: hidden;
  background: #1a1a1d;
  margin-bottom: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.album-artwork img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.5s ease;
}

.album-card:hover .album-artwork img {
  transform: scale(1.05);
}

.album-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}

.album-card:hover .album-overlay {
  opacity: 1;
}

.play-button {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(189, 194, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0e0e0f;
  font-size: 20px;
  box-shadow: 0 8px 16px rgba(189, 194, 255, 0.3);
  transition: all 0.3s ease;
}

.album-card:hover .play-button {
  transform: scale(1.1);
  background: #bdc2ff;
}

.album-title {
  font-size: 14px;
  font-weight: 700;
  color: #e7e5e8;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.album-meta {
  font-size: 12px;
  color: rgba(172, 170, 174, 0.8);
  margin: 4px 0 0 0;
}

.album-group-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.album-group {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.02);
}

.album-group-header {
  width: 100%;
  display: grid;
  grid-template-columns: 88px minmax(0, 1fr);
  gap: 16px;
  align-items: center;
  padding: 16px;
  border: 0;
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.album-group-cover {
  position: relative;
  aspect-ratio: 1 / 1;
  border-radius: 12px;
  overflow: hidden;
  background: #1a1a1d;
}

.album-group-cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.album-group-play {
  position: absolute;
  inset: auto 8px 8px auto;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: rgba(189, 194, 255, 0.92);
  color: #0e0e0f;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 16px rgba(189, 194, 255, 0.28);
}

.album-group-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.album-group-kicker {
  margin: 0;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(172, 170, 174, 0.7);
}

.album-group-title {
  margin: 0;
  font-size: 20px;
  font-weight: 800;
  color: #e7e5e8;
  line-height: 1.2;
}

.album-group-meta {
  margin: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px 12px;
  font-size: 12px;
  color: rgba(172, 170, 174, 0.85);
}

.album-track-list {
  display: flex;
  flex-direction: column;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
}

.album-track-row {
  width: 100%;
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
  padding: 12px 16px;
  border: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.album-track-row:first-child {
  border-top: 0;
}

.album-track-number {
  font-size: 12px;
  font-weight: 700;
  color: rgba(172, 170, 174, 0.75);
  text-align: center;
}

.album-track-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.album-track-title {
  font-size: 14px;
  font-weight: 700;
  color: #e7e5e8;
  line-height: 1.25;
}

.album-track-subtitle {
  font-size: 12px;
  color: rgba(172, 170, 174, 0.8);
}

.album-track-duration {
  font-size: 12px;
  font-weight: 700;
  color: rgba(231, 229, 232, 0.7);
  white-space: nowrap;
}

.album-group-header:hover,
.album-track-row:hover {
  background: rgba(255, 255, 255, 0.03);
}

/* Single Card */
.single-card {
  flex: 0 0 auto;
  width: 140px;
  cursor: pointer;
  transition: transform 0.3s ease;
}

.single-card:hover {
  transform: translateY(-4px);
}

.single-artwork {
  position: relative;
  aspect-ratio: 1/1;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1d;
  margin-bottom: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.single-artwork img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.7s ease;
}

.single-card:hover .single-artwork img {
  transform: scale(1.1);
}

.single-title {
  font-size: 13px;
  font-weight: 700;
  color: #e7e5e8;
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
}

.single-meta {
  font-size: 11px;
  color: rgba(172, 170, 174, 0.8);
  margin: 3px 0 0 0;
}

.singles-scroll {
  gap: 16px;
  padding: 0 -24px;
  margin: 0 -24px;
  padding-left: 24px;
  padding-right: 24px;
}

/* Responsive */
@media (max-width: 768px) {
  .artist-page-container {
    padding: 0;
  }

  .profile-image {
    width: 140px;
    height: 140px;
  }

  .glow-background {
    width: 200px;
    height: 200px;
  }

  .artist-name-large {
    font-size: 32px;
  }

  .action-buttons {
    gap: 8px;
  }

  .btn-action {
    padding: 8px 12px;
    font-size: 12px;
  }

  .btn-action-icon {
    width: 36px;
    height: 36px;
  }

  .stat-item {
    padding: 0 16px;
  }

  .section-header {
    padding-bottom: 12px;
  }

  .section-title {
    font-size: 20px;
  }

  .album-group-header {
    grid-template-columns: 72px minmax(0, 1fr);
    gap: 12px;
    padding: 14px;
  }

  .album-group-title {
    font-size: 18px;
  }

  .album-track-row {
    padding: 11px 14px;
  }

  .video-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .poem-grid {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .album-card {
    width: 140px;
  }

  .single-card {
    width: 120px;
  }
}
</style>
