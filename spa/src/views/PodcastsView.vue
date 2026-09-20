<template>
  <div class="podcasts-page" :class="{ 'podcasts-page--compact-hero': compactHero }">
    <ContentHeader
      kicker="Ahoy Indie Media"
      title="Podcasts"
      subtitle="Original series, interviews, and community stories."
    />
    <section class="podcasts-mobile-library-hero" aria-label="Podcast library controls">
      <div class="podcasts-mobile-hero-copy">
        <span class="podcasts-mobile-eyebrow">Library</span>
        <h1>Podcasts</h1>
        <p>{{ visibleEpisodes.length }} episode{{ visibleEpisodes.length === 1 ? '' : 's' }} from {{ visibleShows.length }} show{{ visibleShows.length === 1 ? '' : 's' }}</p>
      </div>
    </section>
    <section class="podcasts-mobile-command-center" aria-label="Podcast quick controls">
      <div class="podcasts-mobile-action-buttons">
        <button
          v-if="continueEpisode"
          type="button"
          class="podcasts-mobile-action-btn podcasts-mobile-action-btn-continue"
          @click="playContinueEpisode"
        >
          <i class="fas fa-rotate-left" aria-hidden="true"></i>
          <span>Continue</span>
        </button>
        <button
          type="button"
          class="podcasts-mobile-action-btn"
          :class="{ active: activeShowSlug === 'all' && !searchQuery }"
          @click="activeShowSlug = 'all'; searchQuery = ''"
        >
          <i class="fas fa-layer-group" aria-hidden="true"></i>
          <span>All Shows</span>
        </button>
        <button
          type="button"
          class="podcasts-mobile-action-btn"
          :disabled="visibleEpisodes.length === 0"
          @click="playNewestEpisode"
        >
          <i class="fas fa-sparkles" aria-hidden="true"></i>
          <span>Newest</span>
        </button>
        <button
          type="button"
          class="podcasts-mobile-action-btn podcasts-mobile-action-btn-random"
          :disabled="visibleEpisodes.length === 0"
          @click="goRandomEpisode"
        >
          <i class="fas fa-shuffle" aria-hidden="true"></i>
          <span>Random</span>
        </button>
      </div>
      <label class="podcasts-mobile-search">
        <i class="fas fa-search" aria-hidden="true"></i>
        <input
          v-model="searchQuery"
          type="search"
          placeholder="Search shows or episodes"
          aria-label="Search shows or episodes"
          autocomplete="off"
          autocorrect="off"
          autocapitalize="off"
          spellcheck="false"
          enterkeyhint="search"
        />
        <button
          v-if="searchQuery"
          type="button"
          aria-label="Clear podcast search"
          @click="searchQuery = ''"
        >
          <i class="fas fa-xmark" aria-hidden="true"></i>
        </button>
      </label>
    </section>
    <section v-if="newestEpisode" class="podcasts-latest-spotlight" aria-label="Newest podcast episode">
      <div class="podcasts-latest-spotlight-art-wrap">
        <img
          class="podcasts-latest-spotlight-art"
          :src="newestEpisode.artwork || '/static/img/default-cover.jpg'"
          :alt="newestEpisode.title"
        />
      </div>
      <div class="podcasts-latest-spotlight-copy">
        <div class="podcasts-latest-spotlight-kicker">Newest episode</div>
        <h2 class="podcasts-latest-spotlight-title">{{ newestEpisode.title }}</h2>
        <p class="podcasts-latest-spotlight-meta">
          <span>{{ newestEpisode.showTitle }}</span>
          <span v-if="newestEpisode.date">{{ newestEpisode.date }}</span>
        </p>
        <span v-if="newestEpisode.videoRoute" class="episode-video-pill">Video available</span>
      </div>
      <div v-if="newestEpisode.videoRoute" class="podcasts-latest-spotlight-actions">
        <button
          type="button"
          class="podcast-section-cta primary"
          :disabled="visibleEpisodes.length === 0"
          aria-label="Listen to newest podcast episode"
          @click="playNewestEpisode"
        >
          <i class="fas fa-headphones" aria-hidden="true"></i>
          <span>Listen audio</span>
        </button>
        <button
          type="button"
          class="podcast-section-cta secondary"
          aria-label="Watch newest podcast video"
          @click="watchEpisodeVideo(newestEpisode)"
        >
          <i class="fas fa-video" aria-hidden="true"></i>
          <span>Watch video</span>
        </button>
      </div>
      <button
        v-else
        type="button"
        class="podcasts-latest-spotlight-play"
        :disabled="visibleEpisodes.length === 0"
        aria-label="Play newest podcast episode"
        @click="playNewestEpisode"
      >
        <i class="fas fa-play" aria-hidden="true"></i>
      </button>
    </section>
    <!-- Sub-menu filter (design parity with Music Library) -->
    <section class="podcasts-section">
      <SubMenuFilter
        v-model="activeShowSlug"
        :filters="showFilters"
        all-value="all"
        filter-all-label="All Shows"
        :show-search="true"
        search-placeholder="Search shows or episodes…"
        :search-query="searchQuery"
        @update:searchQuery="searchQuery = $event"
        action-label="Random Episode"
        action-icon="fas fa-random"
        @action="goRandomEpisode"
      />
    </section>

    <!-- Featured section: Shows + show cards (Desktop Only) -->
    <section class="podcasts-section podcasts-featured-section">
      <div class="podcasts-section-header podcasts-featured-header">
        <div>
          <h2>Shows</h2>
          <p class="podcasts-section-subtitle">Pick a show to filter the newest episodes.</p>
        </div>
        <div class="podcast-filter-chips">
          <button
            type="button"
            class="podcast-filter-chip"
            :class="{ active: activeShowSlug === 'all' }"
            @click="activeShowSlug = 'all'"
          >
            All
          </button>
          <button
            v-for="show in featuredShows"
            :key="show.slug"
            type="button"
            class="podcast-filter-chip"
            :class="{ active: activeShowSlug === show.slug }"
            @click="activeShowSlug = show.slug"
          >
            {{ show.title }}
          </button>
        </div>
      </div>

      <!-- Mobile: horizontal show scroll -->
      <div class="podcast-shows-mobile-scroll">
        <div
          v-for="show in orderedShows"
          :key="show.slug"
          class="podcast-mobile-show-card"
          :class="{ active: activeShowSlug === show.slug }"
          @click="activeShowSlug = show.slug"
        >
          <img :src="show.artwork || '/static/img/default-cover.jpg'" :alt="show.title" class="podcast-mobile-show-art" />
          <div class="podcast-mobile-show-title">{{ show.title }}</div>
        </div>
      </div>

      <!-- Desktop: show cards grid (Flask: podcast-shows podcast-shows-preview podcast-shows-desktop) -->
      <div class="podcast-shows podcast-shows-preview podcast-shows-desktop">
        <div
          v-for="show in featuredShows"
          :key="show.slug"
          class="podcast-show-preview-card podcast-show-card podcast-show-card--filter"
          :class="{ active: activeShowSlug === show.slug }"
          role="button"
          tabindex="0"
          @click="activeShowSlug = show.slug"
          @keydown.enter.prevent="activeShowSlug = show.slug"
          @keydown.space.prevent="activeShowSlug = show.slug"
        >
          <img
            :src="show.artwork || '/static/img/default-cover.jpg'"
            :alt="show.title"
            class="podcast-show-art"
            loading="lazy"
          />
          <div class="podcast-show-title">{{ show.title }}</div>
          <div class="podcast-show-desc" v-if="show.description">{{ show.description }}</div>
          <div class="podcast-show-updated" v-if="show.last_updated">
            Updated {{ show.last_updated }}
          </div>
          <div class="podcast-show-card-actions">
            <button type="button" class="podcast-section-cta primary" @click.stop="playLatestForShow(show)">
              <i class="fas fa-play" aria-hidden="true"></i>
              <span>Play newest</span>
            </button>
            <router-link :to="`/podcasts/${show.slug}`" class="podcast-section-cta secondary" @click.stop>
              Open show
            </router-link>
          </div>
        </div>
      </div>
    </section>

    <!-- Show-first episode sections -->
    <section class="podcasts-section">
      <div class="podcasts-section-header podcasts-show-sections-header">
        <div>
          <h2>Newest by Show</h2>
          <p class="podcasts-section-subtitle">Ten newest episodes from each show.</p>
        </div>
      </div>

      <div v-if="showSections.length" class="podcast-show-sections">
        <article v-for="show in showSections" :key="show.slug" class="podcast-show-section">
          <div class="podcast-show-section-header">
            <div class="podcast-show-section-copy">
              <router-link :to="`/podcasts/${show.slug}`" class="podcast-show-section-title">
                {{ show.title }}
              </router-link>
              <span v-if="show.updatedLabel" class="podcast-show-section-updated">{{ show.updatedLabel }}</span>
              <p class="podcast-show-section-desc" v-if="show.description">{{ show.description }}</p>
              <div class="podcast-show-section-meta">
                <span v-if="show.latestEpisode">{{ show.latestEpisode.title }}</span>
                <span v-if="show.totalEpisodes"> {{ show.totalEpisodes }} episodes</span>
              </div>
            </div>
            <div class="podcast-show-section-actions">
              <button type="button" class="podcast-section-cta primary" @click="playLatestForShow(show)">
                <i class="fas fa-play" aria-hidden="true"></i>
                <span>Play latest</span>
              </button>
              <router-link :to="`/podcasts/${show.slug}`" class="podcast-section-cta secondary">
                View all
              </router-link>
            </div>
          </div>

          <div class="podcast-show-episode-list">
            <article
              v-for="ep in show.latestEpisodes"
              :key="ep.key"
              class="episode-row podcast-show-episode-row"
              :class="{ playing: playerStore.currentTrack && (playerStore.currentTrack.id === ep.id || playerStore.currentTrack.key === ep.key) }"
              @click="playShowEpisode(show, ep)"
            >
              <img
                class="episode-art"
                :src="ep.artwork || '/static/img/default-cover.jpg'"
                :alt="ep.title"
                loading="lazy"
              />
              <button
                type="button"
                class="episode-art-play"
                title="Play"
                @click.stop="playShowEpisode(show, ep)"
              >
                <i
                  :class="playerStore.currentTrack && (playerStore.currentTrack.id === ep.id || playerStore.currentTrack.key === ep.key) && playerStore.isPlaying ? 'fas fa-pause' : 'fas fa-play'"
                  aria-hidden="true"
                ></i>
                <span class="sr-only">Play</span>
              </button>
              <div class="episode-meta">
                <div class="episode-title">{{ ep.title }}</div>
                <div class="episode-subtitle">
                  <span class="episode-time" v-if="ep.date">{{ ep.date }}</span>
                  <span class="episode-dot" v-if="ep.date && ep.duration">•</span>
                  <span class="episode-time">{{ ep.duration }}</span>
                  <span v-if="isRecentEpisode(ep)" class="episode-recent-pill">New</span>
                  <span v-if="ep.videoRoute" class="episode-video-pill">Video available</span>
                </div>
                <div class="episode-desc" v-if="ep.description">{{ ep.description }}</div>
              </div>

              <div class="podcast-episode-format-actions">
                <button
                  type="button"
                  class="podcast-section-cta primary"
                  @click.stop="playShowEpisode(show, ep)"
                >
                  <i class="fas fa-headphones" aria-hidden="true"></i>
                  <span>Listen audio</span>
                </button>
                <button
                  v-if="ep.videoRoute"
                  type="button"
                  class="podcast-section-cta secondary podcast-watch-cta"
                  @click.stop="watchEpisodeVideo(ep)"
                >
                  <i class="fas fa-video" aria-hidden="true"></i>
                  <span>Watch video</span>
                </button>
                <button
                  type="button"
                  class="podcast-section-cta secondary podcast-save-cta"
                  :class="{ bookmarked: bookmarks.isBookmarked({ id: ep.key }) }"
                  :aria-pressed="bookmarks.isBookmarked({ id: ep.key })"
                  :title="bookmarks.isBookmarked({ id: ep.key }) ? 'Saved for later' : 'Save for later'"
                  @click.stop="toggleBookmark(ep)"
                >
                  <i :class="bookmarks.isBookmarked({ id: ep.key }) ? 'fas fa-bookmark' : 'far fa-bookmark'" aria-hidden="true"></i>
                  <span>{{ bookmarks.isBookmarked({ id: ep.key }) ? 'Saved' : 'Save for later' }}</span>
                </button>
              </div>
            </article>
            <button
              v-if="show.hasMoreEpisodes"
              type="button"
              class="podcast-show-more-btn"
              @click="showMoreEpisodes(show)"
            >
              <span>Show 10 more · {{ show.remainingEpisodes }} left</span>
              <i class="fas fa-chevron-down" aria-hidden="true"></i>
            </button>
          </div>
        </article>
      </div>

      <div v-else-if="!loading" class="empty-state podcasts-empty-state">
        <i class="fas fa-podcast" aria-hidden="true"></i>
        <p>No podcasts match your current filters.</p>
      </div>
    </section>

    <!-- Loading -->
    <section v-if="loading" class="podcasts-section">
      <div class="podcast-shows podcast-shows-preview">
        <div v-for="i in 4" :key="i" class="podcast-show-preview-card">
          <div class="podcast-show-art skeleton" style="aspect-ratio:1;width:100%"></div>
          <div class="skeleton" style="height:14px;width:80%;margin-top:8px"></div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch, provide } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { apiFetchCached } from '../composables/useApi'
import ContentHeader from '../components/ContentHeader.vue'
import SubMenuFilter from '../components/SubMenuFilter.vue'
import { usePlayerStore } from '../stores/player'
import { useBookmarks } from '../composables/useBookmarks'
import { useOverlay } from '../composables/useOverlay'
import { getPodcastVideoRoute } from '../composables/usePodcastVideo'

const router = useRouter()
const route = useRoute()
const playerStore = usePlayerStore()
const bookmarks = useBookmarks()
const { openNowPlaying } = useOverlay()

const shows = ref([])
const loading = ref(true)
const searchQuery = ref(typeof route.query.q === 'string' ? route.query.q : '')
const activeShowSlug = ref('all')
const showEpisodeLimits = ref({})
const podcastProgress = ref({})
const compactHero = ref(false)
const EPISODES_PER_SHOW = 10

function normalizeText(value) {
  return String(value || '').toLowerCase()
}

function sortEpisodesByDate(a, b) {
  return String(b.date || '').localeCompare(String(a.date || '')) ||
    String(b.id || '').localeCompare(String(a.id || ''))
}

function getEpisodeDateValue(ep) {
  const value = Date.parse(ep?.date || '')
  return Number.isFinite(value) ? value : 0
}

function getLatestPlayableEpisodeValue(show) {
  return (show.episodes || [])
    .filter(ep => !ep.is_clip && (ep.audio_url || ep.url))
    .reduce((latest, ep) => Math.max(latest, getEpisodeDateValue(ep)), 0)
}

function sortShowsByLatestEpisode(a, b) {
  return getLatestPlayableEpisodeValue(b) - getLatestPlayableEpisodeValue(a) ||
    String(b.last_updated || '').localeCompare(String(a.last_updated || '')) ||
    String(a.title || '').localeCompare(String(b.title || ''), undefined, { sensitivity: 'base' })
}

function formatRelativeTimeFromDate(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  if (Number.isNaN(date.getTime())) return ''

  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Updated just now'
  if (diffMins < 60) return `Updated ${diffMins}m ago`
  if (diffHours < 24) return `Updated ${diffHours}h ago`
  if (diffDays < 7) return `Updated ${diffDays}d ago`
  return `Updated ${date.toLocaleDateString()}`
}

function episodeMatchesQuery(ep, q) {
  return [
    ep.title,
    ep.description,
    ep.date,
  ].some(value => normalizeText(value).includes(q))
}

function showMatchesQuery(show, q) {
  if (
    normalizeText(show.title).includes(q) ||
    normalizeText(show.description).includes(q)
  ) {
    return true
  }
  return (show.episodes || []).some(ep => episodeMatchesQuery(ep, q))
}

function mapPlayableEpisodes(show) {
  return (show.episodes || [])
    .filter(ep => !ep.is_clip && (ep.audio_url || ep.url))
    .map(ep => ({
      key: `${show.slug}:${ep.id}`,
      showSlug: show.slug,
      showTitle: show.title || show.slug,
      id: ep.id,
      title: ep.title || 'Untitled',
      description: ep.description || '',
      date: ep.date || '',
      duration: ep.duration || formatDuration(ep.duration_seconds),
      duration_seconds: ep.duration_seconds || 0,
      artwork: ep.artwork || ep.cover_art || show.artwork || '/static/img/default-cover.jpg',
      audio_url: ep.audio_url || ep.url || '',
      videoRoute: getPodcastVideoRoute(show.slug, ep),
      type: 'podcast',
      artist: show.title || show.slug,
      cover_art: ep.artwork || ep.cover_art || show.artwork || '/static/img/default-cover.jpg',
    }))
    .sort(sortEpisodesByDate)
}

const orderedShows = computed(() => {
  return [...(shows.value || [])].sort(sortShowsByLatestEpisode)
})

const visibleShows = computed(() => {
  let list = orderedShows.value
  if (activeShowSlug.value !== 'all') {
    list = list.filter(show => show.slug === activeShowSlug.value)
  }
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    list = list.filter(show => showMatchesQuery(show, q))
  }
  return list
})

const featuredShows = computed(() => visibleShows.value.slice(0, 4))

const showSections = computed(() => {
  return visibleShows.value
    .map(show => {
      const playableEpisodes = mapPlayableEpisodes(show)
      const visibleLimit = showEpisodeLimits.value[show.slug] || EPISODES_PER_SHOW
      const latestEpisodes = playableEpisodes.slice(0, visibleLimit)
      return {
        ...show,
        latestEpisodes,
        latestEpisode: latestEpisodes[0] || null,
        totalEpisodes: playableEpisodes.length,
        hasMoreEpisodes: playableEpisodes.length > latestEpisodes.length,
        remainingEpisodes: Math.max(0, playableEpisodes.length - latestEpisodes.length),
        latestValue: getEpisodeDateValue(latestEpisodes[0]),
        updatedLabel: latestEpisodes[0]?.date ? formatRelativeTimeFromDate(latestEpisodes[0].date) : '',
      }
    })
    .sort((a, b) => b.latestValue - a.latestValue || sortShowsByLatestEpisode(a, b))
    .filter(show => show.latestEpisodes.length || show.description || show.title)
})

const visibleEpisodes = computed(() => {
  return visibleShows.value.flatMap(show => mapPlayableEpisodes(show))
})

const newestEpisode = computed(() => {
  return [...visibleEpisodes.value].sort(sortEpisodesByDate)[0] || null
})

const continueEpisode = computed(() => {
  return visibleEpisodes.value.find(ep => {
    const progress = podcastProgress.value[ep.id] || podcastProgress.value[ep.key] || 0
    if (progress < 30) return false
    if (!ep.duration_seconds) return true
    return progress < Math.max(30, ep.duration_seconds - 30)
  }) || null
})

const showFilters = computed(() => {
  return orderedShows.value.map(s => ({
    value: s.slug,
    label: s.title,
    image: s.artwork || null
  }))
})

function goRandomEpisode() {
  if (visibleEpisodes.value.length === 0) return
  const pick = visibleEpisodes.value[Math.floor(Math.random() * visibleEpisodes.value.length)]
  playTrack(pick.showSlug, pick)
  openNowPlaying()
}

function formatDuration(seconds) {
  if (!seconds) return ''
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function isRecentEpisode(ep, days = 7) {
  const value = Date.parse(ep?.date || '')
  if (!Number.isFinite(value)) return false
  return (Date.now() - value) <= (days * 86400000)
}

function toTrack(ep) {
  return {
    id: ep.id,
    key: ep.key,
    title: ep.title,
    artist: ep.showTitle,
    cover_art: ep.artwork,
    audio_url: ep.audio_url,
    type: 'podcast',
  }
}

function playTrack(showSlug, ep) {
  const show = visibleShows.value.find(item => item.slug === showSlug) || shows.value.find(item => item.slug === showSlug)
  if (!show) return
  const sorted = mapPlayableEpisodes(show)
  const tracks = sorted.map(e => toTrack(e))
  const idx = sorted.findIndex(e => e.key === ep.key)
  playerStore.setQueue(tracks, idx >= 0 ? idx : 0)
}

function playLatestForShow(show) {
  const sorted = mapPlayableEpisodes(show)
  if (!sorted.length) {
    router.push(`/podcasts/${show.slug}`)
    return
  }
  playerStore.setQueue(sorted.map(e => toTrack(e)), 0)
  openNowPlaying()
}

function playShowEpisode(show, ep) {
  playTrack(show.slug, ep)
  openNowPlaying()
}

function watchEpisodeVideo(ep) {
  if (!ep?.videoRoute) return
  if (String(ep.videoRoute).startsWith('/videos/')) {
    router.push(ep.videoRoute)
    return
  }
  window.open(ep.videoRoute, '_blank', 'noopener,noreferrer')
}

function playNewestEpisode() {
  if (!newestEpisode.value) return
  playTrack(newestEpisode.value.showSlug, newestEpisode.value)
  openNowPlaying()
}

function playContinueEpisode() {
  if (!continueEpisode.value) return
  playTrack(continueEpisode.value.showSlug, continueEpisode.value)
  openNowPlaying()
}

function showMoreEpisodes(show) {
  showEpisodeLimits.value = {
    ...showEpisodeLimits.value,
    [show.slug]: (showEpisodeLimits.value[show.slug] || EPISODES_PER_SHOW) + EPISODES_PER_SHOW,
  }
}

function readPodcastProgress() {
  try {
    podcastProgress.value = JSON.parse(localStorage.getItem('ahoy.podcastProgress') || '{}')
  } catch {
    podcastProgress.value = {}
  }
}

function updateCompactHero() {
  compactHero.value = window.scrollY > 72
}

function addToQueue(ep) {
  playerStore.addToQueue(toTrack(ep))
}

function toggleBookmark(ep) {
  bookmarks.toggle({
    type: 'podcast-episode',
    id: ep.key,
    title: ep.title,
    artwork: ep.artwork,
    _type: 'podcast-episode',
  })
}

function openShow(slug) {
  router.push(`/podcasts/${slug}`)
}

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

onMounted(async () => {
  readPodcastProgress()
  updateCompactHero()
  window.addEventListener('scroll', updateCompactHero, { passive: true })
  window.addEventListener('storage', readPodcastProgress)
  loading.value = true
  const data = await apiFetchCached('/api/podcasts').catch(() => ({ shows: [] }))
  shows.value = data.shows || []
  loading.value = false
})

onUnmounted(() => {
  window.removeEventListener('scroll', updateCompactHero)
  window.removeEventListener('storage', readPodcastProgress)
})
</script>

<style scoped>
.podcasts-page {
  padding: 0;
}

.podcasts-mobile-library-hero,
.podcasts-mobile-command-center,
.episode-art-play {
  display: none;
}

.podcasts-section {
  padding: 0 16px;
  margin-bottom: 32px;
}

.podcasts-section-header {
  margin-bottom: 20px;
}

.podcasts-section-subtitle {
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.9rem;
  margin-top: 4px;
}

.podcasts-latest-spotlight {
  margin: 0 16px 24px;
  padding: 14px 16px;
  border-radius: 22px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background:
    linear-gradient(135deg, rgba(0, 212, 255, 0.12), rgba(255, 255, 255, 0.03)),
    rgba(255, 255, 255, 0.03);
  display: grid;
  grid-template-columns: 62px minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
}

.podcasts-latest-spotlight-art-wrap {
  position: relative;
  width: 62px;
  height: 62px;
}

.podcasts-latest-spotlight-art {
  width: 62px;
  height: 62px;
  border-radius: 14px;
  object-fit: cover;
}

.episode-recent-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.podcasts-latest-spotlight-copy {
  min-width: 0;
}

.podcasts-latest-spotlight-kicker {
  color: rgba(255, 255, 255, 0.58);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.podcasts-latest-spotlight-title {
  margin: 0;
  font-size: 1rem;
  line-height: 1.3;
  color: #fff;
}

.podcasts-latest-spotlight-meta {
  margin: 6px 0 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: rgba(255, 255, 255, 0.62);
  font-size: 0.86rem;
}

.episode-video-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 3px 7px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(8, 16, 24, 0.88);
  background: rgba(143, 240, 255, 0.48);
  box-shadow: 0 4px 10px rgba(109, 220, 255, 0.12);
}

.podcasts-latest-spotlight-actions {
  display: flex;
  flex-direction: row;
  gap: 8px;
  min-width: 0;
  grid-column: 1 / -1;
}

.podcasts-latest-spotlight-play {
  width: 48px;
  height: 48px;
  border: 0;
  border-radius: 50%;
  background: #6ddcff;
  color: #081018;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 10px 24px rgba(109, 220, 255, 0.22);
}

.podcasts-latest-spotlight-play:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.podcast-episode-format-actions {
  display: flex;
  flex-wrap: nowrap;
  gap: 8px;
  justify-content: flex-start;
  align-items: center;
  margin-left: 0;
  grid-column: 1 / -1;
  grid-row: 2;
}

/* Featured Shows Grid */
.podcast-shows {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}

.podcast-show-preview-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 16px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  cursor: pointer;
  transition: all 0.2s;
  position: relative;
}

.podcast-show-preview-card:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-2px);
}

.podcast-show-preview-card.active {
  border-color: var(--accent-color, #00d4ff);
  background: rgba(0, 212, 255, 0.05);
}

.podcast-show-card-art {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 8px;
  object-fit: cover;
  margin-bottom: 12px;
}

.podcast-show-card-title {
  font-weight: 600;
  margin-bottom: 4px;
}

.podcast-show-card-meta {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.5);
}

.podcast-show-card--filter {
  display: flex;
  flex-direction: column;
  gap: 10px;
  text-align: left;
}

.podcast-show-badge {
  top: 10px;
  right: 10px;
}

.podcast-show-card-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: auto;
}

.podcast-section-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: 999px;
  padding: 9px 14px;
  font-size: 0.85rem;
  font-weight: 700;
  text-decoration: none;
  border: 1px solid transparent;
  transition: all 0.2s ease;
  cursor: pointer;
}

.podcast-section-cta.primary {
  background: rgba(0, 212, 255, 0.12);
  color: #fff;
  border-color: rgba(0, 212, 255, 0.22);
}

.podcast-section-cta.primary:hover {
  background: rgba(0, 212, 255, 0.18);
  transform: translateY(-1px);
}

.podcast-section-cta.secondary {
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.9);
  border-color: rgba(255, 255, 255, 0.08);
}

.podcast-section-cta.secondary:hover {
  background: rgba(255, 255, 255, 0.09);
  color: #fff;
}

.podcast-watch-cta {
  background: rgba(255, 176, 64, 0.1);
  border-color: rgba(255, 176, 64, 0.22);
  color: #fff;
}

.podcast-watch-cta i {
  color: #ffb040;
}

.podcast-save-cta.bookmarked {
  background: rgba(30, 215, 96, 0.1);
  border-color: rgba(30, 215, 96, 0.24);
  color: #fff;
}

.podcast-save-cta.bookmarked i {
  color: #1ed760;
}

.podcasts-show-sections-header {
  margin-bottom: 16px;
}

.podcast-show-sections {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.podcast-show-section {
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 18px;
  padding: 16px;
}

.podcast-show-section-header {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 14px;
}

.podcast-show-section-copy {
  min-width: 0;
  flex: 1;
}

.podcast-show-section-title {
  color: #fff;
  font-size: 1.1rem;
  font-weight: 700;
  text-decoration: none;
}

.podcast-show-section-title:hover {
  color: var(--accent-color, #00d4ff);
}

.podcast-show-section-badge {
  display: inline-flex;
  margin-top: 6px;
  padding: 5px 8px;
  color: #081018;
  background: #6ddcff;
}

.podcast-show-section-updated {
  display: inline-block;
  margin-top: 6px;
  padding-left: 8px;
  margin-left: 8px;
  border-left: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.62);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

.podcast-show-section-desc {
  margin: 6px 0 0;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.92rem;
  line-height: 1.45;
}

.podcast-show-section-meta {
  margin-top: 8px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  color: rgba(255, 255, 255, 0.45);
  font-size: 0.82rem;
}

.podcast-show-section-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  justify-content: flex-end;
}

.podcast-show-episode-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.podcast-show-more-btn {
  align-self: stretch;
  min-height: 42px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.82);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-family: inherit;
  font-weight: 700;
  cursor: pointer;
}

.podcast-show-episode-row {
  grid-template-columns: 80px minmax(0, 1fr) auto;
  grid-template-rows: auto auto;
  align-items: start;
  cursor: pointer;
}

.podcast-show-episode-row .podcast-episode-format-actions {
  grid-column: 3;
  grid-row: 1 / span 2;
  align-self: center;
  justify-content: flex-end;
  margin-left: auto;
  width: max-content;
}

.podcast-show-episode-row:hover {
  background: rgba(255, 255, 255, 0.06);
}

.podcasts-empty-state {
  text-align: center;
  padding: 36px 20px;
  color: rgba(255, 255, 255, 0.55);
}

.podcasts-empty-state i {
  display: block;
  font-size: 42px;
  margin-bottom: 12px;
}

/* Mobile Horizontal Scroll */
.podcast-shows-mobile-scroll {
  display: none;
  overflow-x: auto;
  gap: 12px;
  padding: 8px 16px 20px;
  margin: 0 -16px;
  scroll-snap-type: x mandatory;
  -webkit-overflow-scrolling: touch;
}

.podcast-shows-mobile-scroll::-webkit-scrollbar {
  display: none;
}

.podcast-mobile-show-card {
  flex: 0 0 100px;
  scroll-snap-align: start;
  display: flex;
  flex-direction: column;
  gap: 8px;
  cursor: pointer;
  transition: opacity 0.2s;
  position: relative;
}

.podcast-mobile-show-card.active .podcast-mobile-show-art {
  border-color: var(--accent-color, #00d4ff);
  box-shadow: 0 0 12px rgba(0, 212, 255, 0.3);
}

.podcast-mobile-show-badge {
  top: -4px;
  right: -2px;
}

.podcast-mobile-show-art {
  width: 100px;
  height: 100px;
  border-radius: 12px;
  object-fit: cover;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.podcast-mobile-show-title {
  font-size: 0.75rem;
  font-weight: 600;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: rgba(255, 255, 255, 0.7);
}

.podcast-mobile-show-card.active .podcast-mobile-show-title {
  color: #fff;
}

/* Episode List (Desktop) */
.episode-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.episode-row {
  display: grid;
  grid-template-columns: 80px 1fr auto;
  gap: 20px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  align-items: center;
  cursor: pointer;
  transition: all 0.2s;
}

.episode-row:hover {
  background: rgba(255, 255, 255, 0.06);
}

.episode-row.playing {
  border-color: var(--accent-color, #00d4ff);
  background: rgba(0, 212, 255, 0.05);
}

.episode-art {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  object-fit: cover;
}

.episode-title {
  font-weight: 600;
  font-size: 1.1rem;
  margin-bottom: 6px;
}

.episode-subtitle {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.episode-recent-pill {
  padding: 4px 8px;
  color: #081018;
  background: #6ddcff;
}

.episode-desc {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.episode-actions {
  display: flex;
  gap: 10px;
  align-items: center;
}

.episode-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

.episode-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
}

.episode-open {
  color: rgba(255, 255, 255, 0.5);
  font-size: 1.2rem;
  margin-left: 10px;
}

.episode-open:hover {
  color: #fff;
}

/* Mobile Styles Parity with Music Library */
.podcast-mobile-list {
  display: none;
}

@media (max-width: 768px) {
  .podcasts-page {
    padding: 0 0 var(--mobile-bottom-clear, 100px) !important;
  }

  .podcasts-page :deep(.content-header) {
    display: none !important;
  }

  .podcasts-section {
    padding: 0 var(--mobile-gutter, 10px) !important;
    margin-bottom: 0;
  }

  .podcasts-section:has(.sub-menu-filter) {
    display: none;
  }

  .podcasts-mobile-library-hero {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    align-items: end;
    gap: 0;
    margin: 2px var(--mobile-gutter, 10px) 12px;
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

  .podcasts-page--compact-hero .podcasts-mobile-library-hero {
    margin-top: 8px;
    padding-top: 14px;
    padding-bottom: 12px;
    border-radius: 22px;
  }

  .podcasts-page--compact-hero .podcasts-mobile-hero-copy h1 {
    font-size: 31px;
  }

  .podcasts-latest-spotlight {
    margin: 0 var(--mobile-gutter, 10px) 20px;
    grid-template-columns: 56px minmax(0, 1fr) auto;
    padding: 12px 14px;
  }

  .podcasts-latest-spotlight-art-wrap,
  .podcasts-latest-spotlight-art {
    width: 56px;
    height: 56px;
  }

  .podcasts-latest-spotlight-title {
    font-size: 0.96rem;
  }

  .podcasts-latest-spotlight-actions {
    grid-column: 1 / -1;
    grid-row: 2;
    flex-direction: row;
    flex-wrap: nowrap;
    width: 100%;
    min-width: 0;
    gap: 6px;
  }

  .podcasts-latest-spotlight-actions .podcast-section-cta {
    flex: 1 1 0;
    min-width: 0;
    padding-inline: 8px;
    font-size: 0.74rem;
    white-space: nowrap;
  }

  .podcasts-latest-spotlight-actions .podcast-section-cta.secondary,
  .podcast-episode-format-actions .podcast-section-cta.secondary {
    display: inline-flex;
  }

  .podcast-show-episode-row {
    grid-template-columns: 56px minmax(0, 1fr) !important;
    grid-template-rows: auto auto !important;
    align-items: start !important;
  }

  .podcast-show-episode-row .episode-meta {
    grid-column: 2 !important;
    grid-row: 1 !important;
    min-width: 0;
  }

  .podcast-episode-format-actions {
    grid-column: 1 / -1;
    grid-row: 2;
    flex-direction: row;
    align-items: center;
    flex-wrap: nowrap;
    width: 100%;
    gap: 6px;
    margin-top: 6px;
    padding-left: 0;
    justify-content: space-between;
  }

  .podcast-episode-format-actions .podcast-section-cta {
    flex: 1 1 0;
    min-width: 0;
    padding-inline: 7px;
    font-size: 0.68rem;
    white-space: nowrap;
  }

  .episode-video-pill {
    padding: 3px 6px;
    font-size: 8px;
    box-shadow: 0 3px 8px rgba(109, 220, 255, 0.1);
  }

  .podcasts-mobile-hero-copy {
    min-width: 0;
  }

  .podcasts-mobile-eyebrow {
    display: block;
    margin-bottom: 8px;
    color: rgba(255, 255, 255, 0.52);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .podcasts-mobile-hero-copy h1 {
    margin: 0;
    color: #fff;
    font-size: 38px;
    font-weight: 900;
    letter-spacing: -0.06em;
    line-height: 0.95;
  }

  .podcasts-mobile-hero-copy p {
    margin: 8px 0 0;
    color: rgba(255, 255, 255, 0.58);
    font-size: 12px;
    line-height: 1.3;
  }

  .podcasts-mobile-command-center {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 0 var(--mobile-gutter, 10px) 14px;
  }

  .podcasts-mobile-action-buttons {
    display: grid;
    grid-template-columns: minmax(0, 1fr) minmax(0, 0.9fr) minmax(0, 0.9fr);
    gap: 8px;
  }

  .podcasts-mobile-action-btn {
    min-width: 0;
    min-height: 42px;
    border-radius: 999px;
    border: 1px solid rgba(255, 255, 255, 0.075);
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.018));
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.075),
      0 10px 22px rgba(0, 0, 0, 0.16);
    color: #fff;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    padding: 0 10px;
    font-family: inherit;
    font-size: 12px;
    font-weight: 800;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    backdrop-filter: blur(18px) saturate(150%);
    -webkit-backdrop-filter: blur(18px) saturate(150%);
  }

  .podcasts-mobile-action-btn.active {
    border-color: rgba(109, 220, 255, 0.18);
    background:
      linear-gradient(180deg, rgba(109, 220, 255, 0.105), rgba(109, 220, 255, 0.035));
  }

  .podcasts-mobile-action-btn:disabled {
    opacity: 0.48;
  }

  .podcasts-mobile-action-btn i {
    color: #6ddcff;
    flex-shrink: 0;
  }

  .podcasts-mobile-action-btn-random i {
    color: #ff4b9b;
  }

  .podcasts-mobile-action-btn-continue {
    grid-column: 1 / -1;
    justify-content: flex-start;
  }

  .podcasts-mobile-action-btn-continue i {
    color: #1ed760;
  }

  .podcasts-mobile-search {
    min-height: 42px;
    display: flex;
    align-items: center;
    gap: 9px;
    padding: 0 12px;
    border-radius: 18px;
    border: 1px solid rgba(255, 255, 255, 0.075);
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.055), rgba(255, 255, 255, 0.016));
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.075),
      0 10px 22px rgba(0, 0, 0, 0.15);
    color: rgba(255, 255, 255, 0.54);
    backdrop-filter: blur(18px) saturate(150%);
    -webkit-backdrop-filter: blur(18px) saturate(150%);
  }

  .podcasts-mobile-search input {
    flex: 1;
    min-width: 0;
    border: 0;
    outline: 0;
    background: transparent;
    color: #fff;
    font: inherit;
    font-size: 16px;
  }

  .podcasts-mobile-search button {
    width: 28px;
    height: 28px;
    border: 0;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
    color: rgba(255, 255, 255, 0.72);
  }

  .podcasts-featured-header {
    display: none;
  }

  .podcast-filter-chips {
    display: none;
  }

  .podcast-shows-desktop {
    display: none;
  }

  .podcast-shows-mobile-scroll {
    display: flex;
    gap: 8px;
    padding: 0 var(--mobile-gutter, 10px) 18px;
    margin: 0 calc(var(--mobile-gutter, 10px) * -1);
  }

  .podcast-show-section {
    padding: 0;
    border-radius: 26px;
    overflow: hidden;
    background:
      radial-gradient(circle at 0% 0%, rgba(30, 215, 96, 0.07), transparent 30%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.012));
    border-color: rgba(255, 255, 255, 0.07);
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.07),
      0 16px 36px rgba(0, 0, 0, 0.17);
    backdrop-filter: blur(18px) saturate(145%);
    -webkit-backdrop-filter: blur(18px) saturate(145%);
  }

  .podcast-show-section-header {
    padding: 14px 14px 12px;
    margin: 0;
    align-items: center;
    flex-direction: row;
    gap: 10px;
    position: sticky;
    top: 0;
    z-index: 2;
    background:
      linear-gradient(180deg, rgba(20, 24, 25, 0.56), rgba(20, 24, 25, 0.28));
    backdrop-filter: blur(18px) saturate(145%);
    -webkit-backdrop-filter: blur(18px) saturate(145%);
  }

  .podcast-show-section-actions {
    justify-content: flex-end;
    flex-shrink: 0;
  }

  .podcast-show-card-actions {
    width: 100%;
  }

  .podcast-section-cta {
    width: auto;
    min-height: 34px;
    padding: 0 12px;
    font-size: 12px;
  }

  .episode-row {
    grid-template-columns: 56px minmax(0, 1fr) auto !important;
    gap: 12px !important;
    padding: 10px 10px !important;
    min-height: 74px;
    align-items: center !important;
    border: 0 !important;
    border-radius: 0 !important;
    background: rgba(255, 255, 255, 0.015) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.055) !important;
    position: relative;
  }

  .episode-row:first-child {
    border-top: 0 !important;
  }

  .episode-row.playing {
    background:
      radial-gradient(circle at 4% 50%, rgba(30, 215, 96, 0.12), transparent 42%),
      rgba(255, 255, 255, 0.012) !important;
  }

  .episode-row.playing .episode-art-play::after {
    content: '';
    position: absolute;
    inset: -3px;
    border-radius: 13px;
    border: 1px solid rgba(30, 215, 96, 0.38);
    animation: podcast-now-playing-pulse 1.8s ease-in-out infinite;
    pointer-events: none;
  }

  .episode-art {
    grid-column: 1;
    grid-row: 1;
    width: 52px !important;
    height: 52px !important;
    border-radius: 10px !important;
    box-shadow: 0 12px 18px rgba(0, 0, 0, 0.25);
    z-index: 0;
  }

  .episode-art-play {
    grid-column: 1;
    grid-row: 1;
    align-self: stretch;
    justify-self: stretch;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 52px;
    height: 52px;
    border: 0;
    border-radius: 10px;
    color: #fff;
    background:
      radial-gradient(circle at center, rgba(0, 0, 0, 0.34) 0 32%, rgba(0, 0, 0, 0.12) 33% 100%);
    font-size: 15px;
    cursor: pointer;
    z-index: 1;
    position: relative;
  }

  .episode-title {
    margin: 0 0 4px !important;
    color: #fff;
    font-size: 15px !important;
    font-weight: 800;
    line-height: 1.18;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }

  .episode-subtitle {
    margin: 0 !important;
    gap: 6px;
    font-size: 12px !important;
    color: rgba(255, 255, 255, 0.54);
  }

  .episode-desc {
    display: none;
  }

  .episode-actions {
    grid-column: 3 !important;
    grid-row: 1 !important;
    gap: 6px !important;
    justify-content: flex-end !important;
    width: auto !important;
    margin-top: 0 !important;
    padding-top: 0 !important;
    border-top: 0 !important;
  }

  .episode-btn {
    width: 44px !important;
    height: 44px !important;
    background: rgba(255, 255, 255, 0.055) !important;
    border-color: rgba(255, 255, 255, 0.12) !important;
  }

  .episode-btn:active {
    background: rgba(255, 255, 255, 0.14) !important;
    transform: scale(0.92);
  }

  .episode-btn:first-child {
    display: none !important;
  }

  .episode-open {
    display: none;
  }

  .podcast-mobile-show-card {
    flex: 0 0 116px;
    gap: 7px;
    padding: 10px;
    border-radius: 20px;
    border: 1px solid rgba(255, 255, 255, 0.065);
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.016));
    box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.07);
    backdrop-filter: blur(16px) saturate(145%);
    -webkit-backdrop-filter: blur(16px) saturate(145%);
  }

  .podcast-mobile-show-card.active {
    border-color: rgba(109, 220, 255, 0.18);
    background:
      radial-gradient(circle at 20% 0%, rgba(109, 220, 255, 0.1), transparent 42%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.018));
  }

  .podcast-mobile-show-card.active .podcast-mobile-show-art {
    box-shadow: 0 0 0 2px rgba(109, 220, 255, 0.25), 0 12px 22px rgba(0, 0, 0, 0.24);
  }

  .podcast-mobile-show-art {
    width: 96px;
    height: 96px;
    border: 0;
    border-radius: 14px;
  }

  .podcast-mobile-show-title {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.82);
  }

  .podcasts-show-sections-header {
    display: none;
  }

  .podcast-show-sections {
    gap: 14px;
  }

  .podcast-show-section-title {
    font-size: 16px;
  }

  .podcast-show-section-desc {
    display: none;
  }

  .podcast-show-section-meta {
    margin-top: 3px;
    font-size: 12px;
  }

  .podcast-section-cta.secondary {
    display: none;
  }

  .podcast-show-more-btn {
    width: calc(100% - 20px);
    min-height: 40px;
    margin: 8px 10px 12px;
    border: 1px solid rgba(255, 255, 255, 0.075);
    border-radius: 16px;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.014));
    color: rgba(255, 255, 255, 0.82);
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    font-family: inherit;
    font-size: 12px;
    font-weight: 800;
    backdrop-filter: blur(16px) saturate(145%);
    -webkit-backdrop-filter: blur(16px) saturate(145%);
  }

  @keyframes podcast-now-playing-pulse {
    0%, 100% {
      opacity: 0.35;
      transform: scale(1);
    }
    50% {
      opacity: 0.85;
      transform: scale(1.04);
    }
  }
}
</style>
