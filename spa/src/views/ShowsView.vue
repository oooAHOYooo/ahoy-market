<template>
  <div class="shows-page videos-page">
    <ContentHeader
      kicker="Ahoy Indie Media"
      title="Videos"
      :subtitle="shows.length ? `${shows.length} video${shows.length === 1 ? '' : 's'} — films, performances, and digital shorts.` : 'Films, performances, and digital shorts.'"
    />
    <section class="videos-mobile-hero" aria-label="Video library">
      <div class="videos-mobile-hero-copy">
        <span class="videos-mobile-eyebrow">Library</span>
        <h1>Videos</h1>
        <p>{{ shows.length }} video{{ shows.length === 1 ? '' : 's' }} from independent creators</p>
      </div>
      <button
        type="button"
        class="videos-mobile-hero-play"
        :disabled="sortedShows.length === 0"
        aria-label="Browse videos"
        @click="sortedShows.length && goToVideo(sortedShows[Math.floor(Math.random() * sortedShows.length)])"
      >
        <i class="fas fa-play" aria-hidden="true"></i>
      </button>
    </section>
    <div class="shows-container">
      <!-- Featured Carousel Hero -->
      <section class="featured-carousel-section">
        <div class="featured-carousel-wrapper" @mouseenter="pauseCarousel" @mouseleave="resumeCarousel">
          <div class="featured-carousel-container">
            <div class="carousel-track" :style="{ transform: `translateX(-${carouselIndex * 100}%)` }">
              <div v-for="(video, index) in featuredVideos" :key="video.id" class="carousel-slide">
                <div class="cinematic-backdrop">
                  <img :src="video.thumbnail || '/static/img/default-cover.jpg'" :alt="video.title">
                  <div class="glass-overlay"></div>
                </div>
                <div class="carousel-content liquid-glass-plate">
                  <h2>{{ video.title }}</h2>
                  <p class="carousel-host">{{ video.host }}</p>
                  <div class="carousel-actions">
                    <button @click="goToVideo(video)" class="btn-glass-play">
                      <i class="fas fa-play"></i> Watch Now
                    </button>
                  </div>
                </div>
              </div>
            </div>
            <!-- Navigation Arrows -->
            <button class="carousel-nav prev" @click.stop="prevCarousel" aria-label="Previous slide"><i class="fas fa-chevron-left"></i></button>
            <button class="carousel-nav next" @click.stop="nextCarousel" aria-label="Next slide"><i class="fas fa-chevron-right"></i></button>

            <!-- Controls -->
            <div class="carousel-indicators" v-if="featuredVideos.length > 1">
              <button
                v-for="(_, i) in featuredVideos"
                :key="'ind-'+i"
                class="indicator"
                :class="{ active: i === carouselIndex }"
                @click.stop="setCarousel(i)"
                :aria-label="'Go to slide ' + (i + 1)"
              ></button>
            </div>
          </div>
        </div>
      </section>

      <!-- Filter bar -->
      <SubMenuFilter
        v-model="selectedHost"
        :filters="hostFilters"
        all-value=""
        filter-all-label="All Hosts"
        filter-label="Filter by Host"
        :show-search="true"
        search-placeholder="Search videos…"
        :search-query="searchQuery"
        @update:searchQuery="searchQuery = $event"
      />

      <!-- Sort buttons -->
      <div class="sort-controls">
        <button
          v-for="option in sortOptions"
          :key="option.value"
          :class="['sort-btn', 'beautiful-tooltip-container', { active: sortMode === option.value }]"
          @click="sortMode = option.value"
          :aria-label="option.label"
        >
          <i :class="option.icon"></i>
          <span class="sort-btn-label">{{ option.label }}</span>
          <span class="beautiful-tooltip">{{ option.label }}</span>
        </button>
      </div>

      <!-- Videos grid organized by type -->
      <section class="shows-grid-section">
        <article
          v-for="section in videoSections"
          :key="section.id"
          class="video-section-group"
        >
          <div class="video-section-group-header">
            <div>
              <h3>{{ section.title }}</h3>
              <p>{{ section.items.length }} video{{ section.items.length === 1 ? '' : 's' }}</p>
              <span v-if="section.updatedLabel" class="video-section-updated">{{ section.updatedLabel }}</span>
            </div>
          </div>

          <div class="shows-grid shows-grid-16x9">
            <div
              v-for="(show, idx) in section.items"
              :key="`${section.id}-${show.id}`"
              class="show-card"
              @click="goToVideo(show)"
            >
              <div class="show-thumbnail">
                <img
                  :src="show.thumbnail || '/static/img/default-cover.jpg'"
                  :alt="show.title"
                  :loading="idx < 4 ? 'eager' : 'lazy'"
                  decoding="async"
                  class="image-placeholder"
                />
                <div v-if="isNewVideo(show)" class="new-tag">NEW</div>
                <div class="show-overlay video-card-overlay">
                  <button
                    type="button"
                    class="show-overlay-save action-btn bm-btn"
                    :aria-pressed="isShowBookmarked(show)"
                    :class="{ bookmarked: isShowBookmarked(show) }"
                    title="Bookmark"
                    @click.stop="toggleShowBookmark(show)"
                  >
                    <i :class="isShowBookmarked(show) ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
                    <span class="sr-only">{{ isShowBookmarked(show) ? 'Remove bookmark' : 'Add bookmark' }}</span>
                  </button>
                  <button type="button" class="play-btn" @click.stop="goToVideo(show)">
                    <i class="fas fa-play"></i>
                  </button>
                </div>
              </div>
              <div class="show-info">
                <h4>{{ show.title }}</h4>
                <p class="show-host">{{ show.host }}</p>
                <span v-if="sectionLabel(show)" class="show-series-tag">{{ sectionLabel(show) }}</span>
              </div>
            </div>
          </div>
        </article>
      </section>

      <!-- Loading State -->
      <section v-show="isLoading" class="loading-section">
        <div class="spinner"></div>
        <p>Loading videos...</p>
      </section>

      <!-- Empty State -->
      <section v-show="!isLoading && filteredShows.length === 0" class="empty-section">
        <div class="empty-content">
          <i class="fas fa-play-circle"></i>
          <h3>No videos found</h3>
          <p>Try a different search or check back later.</p>
          <button type="button" class="btn btn-primary" @click="clearFilters">Clear search</button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import ContentHeader from '../components/ContentHeader.vue'
import SubMenuFilter from '../components/SubMenuFilter.vue'
import { apiFetchCached } from '../composables/useApi'
import { useBookmarks } from '../composables/useBookmarks'
import { trackRecentPlay } from '../composables/useRecentlyPlayed'

const route = useRoute()
const router = useRouter()
const bookmarks = useBookmarks()

const shows = ref([])
const searchQuery = ref(typeof route.query.q === 'string' ? route.query.q : '')
const selectedHost = ref(typeof route.query.host === 'string' ? route.query.host : '')
const isLoading = ref(true)
const sortMode = ref(typeof route.query.sort === 'string' ? route.query.sort : 'newest')

const sortOptions = [
  { value: 'newest', label: 'Latest', icon: 'fas fa-clock' },
  { value: 'random', label: 'Random', icon: 'fas fa-random' },
  { value: 'artist', label: 'Artists', icon: 'fas fa-user' },
  { value: 'title', label: 'Title', icon: 'fas fa-sort-alpha-down' },
]

const VIDEO_SECTION_ORDER = ['music-videos', 'live-shows', 'films', 'misc']

function normalizeKey(value) {
  return String(value || '').trim().toLowerCase()
}

function normalizeQueryValue(value) {
  return typeof value === 'string' ? value : ''
}

function buildVideoQuery() {
  const query = { ...route.query }
  const q = searchQuery.value.trim()
  const host = selectedHost.value.trim()
  const sort = sortMode.value || 'newest'

  if (q) query.q = q
  else delete query.q

  if (host) query.host = host
  else delete query.host

  if (sort && sort !== 'newest') query.sort = sort
  else delete query.sort

  return query
}

function areVideoQueriesEqual(a, b) {
  return normalizeQueryValue(a.q) === normalizeQueryValue(b.q) &&
    normalizeQueryValue(a.host) === normalizeQueryValue(b.host) &&
    normalizeQueryValue(a.sort) === normalizeQueryValue(b.sort)
}

function classifyVideo(show) {
  const category = normalizeKey(show?.category)
  const tags = Array.isArray(show?.tags) ? show.tags.map(normalizeKey) : []
  const title = normalizeKey(show?.title)

  if (
    category === 'music video' ||
    category === 'music-video' ||
    tags.includes('music-video') ||
    tags.includes('musicvideos') ||
    title.includes('music video')
  ) {
    return 'music-videos'
  }

  if (
    category === 'short film' ||
    category === 'film' ||
    tags.includes('film') ||
    tags.includes('movie') ||
    title.includes('short')
  ) {
    return 'films'
  }

  if (
    category === 'broadcast' ||
    category === 'live show' ||
    category === 'live-show' ||
    category === 'episode' ||
    tags.includes('live') ||
    title.includes('live')
  ) {
    return 'live-shows'
  }

  return 'misc'
}

function sectionTitle(key) {
  if (key === 'music-videos') return 'Music Videos'
  if (key === 'live-shows') return 'Live Shows'
  if (key === 'films') return 'Films'
  return 'Everything Else'
}

function sectionLabel(show) {
  const key = classifyVideo(show)
  if (key === 'music-videos') return 'Music Video'
  if (key === 'live-shows') return 'Live Show'
  if (key === 'films') return 'Film'
  return show?.category ? String(show.category).replace(/_/g, ' ') : ''
}

const hostFilters = computed(() => {
  const seen = new Map()
  for (const s of shows.value) {
    if (!s.host) continue
    if (!seen.has(s.host)) seen.set(s.host, { value: s.host, label: s.host })
  }
  return Array.from(seen.values()).sort((a, b) => a.label.localeCompare(b.label))
})

const filteredShows = computed(() => {
  let list = [...shows.value]
  const q = searchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(
      s =>
        (s.title || '').toLowerCase().includes(q) ||
        (s.host || '').toLowerCase().includes(q) ||
        (s.description || '').toLowerCase().includes(q)
    )
  }
  if (selectedHost.value) {
    list = list.filter(s => s.host === selectedHost.value)
  }
  return list
})

function getShowDateValue(show) {
  const raw =
    show?.release_date ||
    show?.released_at ||
    show?.published_date ||
    show?.published_at ||
    show?.created_at ||
    show?.date ||
    ''
  const time = Date.parse(raw)
  return Number.isNaN(time) ? 0 : time
}

function getSectionLatestDateValue(items) {
  return items.reduce((latest, item) => {
    const value = getShowDateValue(item)
    return value > latest ? value : latest
  }, 0)
}

function formatRelativeTimeFromTimestamp(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
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

const sortedShows = computed(() => {
  const list = [...filteredShows.value]

  if (sortMode.value === 'newest') {
    // Sort by the newest available timestamp first.
    list.sort((a, b) => {
      return getShowDateValue(b) - getShowDateValue(a)
    })
  } else if (sortMode.value === 'random') {
    // Fisher-Yates shuffle
    for (let i = list.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [list[i], list[j]] = [list[j], list[i]]
    }
  } else if (sortMode.value === 'artist') {
    // Sort alphabetically by host/artist
    list.sort((a, b) => (a.host || '').localeCompare(b.host || ''))
  } else if (sortMode.value === 'title') {
    // Sort alphabetically by title
    list.sort((a, b) => (a.title || '').localeCompare(b.title || ''))
  }

  return list
})

const videoSections = computed(() => {
  const grouped = new Map(VIDEO_SECTION_ORDER.map(key => [key, []]))
  for (const show of sortedShows.value) {
    const key = classifyVideo(show)
    grouped.get(key)?.push(show)
  }

  return VIDEO_SECTION_ORDER
    .map((key, index) => {
      const items = grouped.get(key) || []
      const latestValue = getSectionLatestDateValue(items)
      return {
        id: key,
        title: sectionTitle(key),
        items,
        latestValue,
        updatedLabel: latestValue ? formatRelativeTimeFromTimestamp(latestValue) : '',
        order: index,
      }
    })
    .sort((a, b) => {
      if (b.latestValue !== a.latestValue) return b.latestValue - a.latestValue
      return a.order - b.order
    })
    .map(({ latestValue, order, ...section }) => section)
    .filter(section => section.items.length > 0)
})

watch(
  () => [route.query.q, route.query.host, route.query.sort],
  ([q, host, sort]) => {
    const nextSearch = typeof q === 'string' ? q : ''
    const nextHost = typeof host === 'string' ? host : ''
    const nextSort = typeof sort === 'string' && sortOptions.some(option => option.value === sort) ? sort : 'newest'

    if (searchQuery.value !== nextSearch) searchQuery.value = nextSearch
    if (selectedHost.value !== nextHost) selectedHost.value = nextHost
    if (sortMode.value !== nextSort) sortMode.value = nextSort
  },
  { immediate: true }
)

watch(
  [searchQuery, selectedHost, sortMode],
  () => {
    const nextQuery = buildVideoQuery()
    const currentQuery = {
      q: normalizeQueryValue(route.query.q),
      host: normalizeQueryValue(route.query.host),
      sort: normalizeQueryValue(route.query.sort),
    }

    if (areVideoQueriesEqual(nextQuery, currentQuery)) return

    router.replace({ path: '/videos', query: nextQuery }).catch(() => {})
  },
  { deep: false }
)

// Carousel Logic
const carouselIndex = ref(0)
let carouselInterval = null
const isCarouselPaused = ref(false)

const featuredVideos = computed(() => {
  return [...filteredShows.value]
    .filter(show => show.thumbnail && show.title)
    .sort((a, b) => getShowDateValue(b) - getShowDateValue(a))
    .slice(0, 5)
})

watch(
  featuredVideos,
  () => {
    carouselIndex.value = 0
  },
  { immediate: true }
)

function startCarousel() {
  if (carouselInterval) clearInterval(carouselInterval)
  carouselInterval = setInterval(() => {
    if (!isCarouselPaused.value && featuredVideos.value.length > 0) {
      carouselIndex.value = (carouselIndex.value + 1) % featuredVideos.value.length
    }
  }, 6000)
}

function pauseCarousel() {
  isCarouselPaused.value = true
}

function resumeCarousel() {
  isCarouselPaused.value = false
}

function setCarousel(i) {
  carouselIndex.value = i
  startCarousel() // reset timer
}

function prevCarousel() {
  if (featuredVideos.value.length === 0) return
  carouselIndex.value = (carouselIndex.value - 1 + featuredVideos.value.length) % featuredVideos.value.length
  startCarousel()
}

function nextCarousel() {
  if (featuredVideos.value.length === 0) return
  carouselIndex.value = (carouselIndex.value + 1) % featuredVideos.value.length
  startCarousel()
}

function handleKeydown(e) {
  if (featuredVideos.value.length > 0) {
    if (e.key === 'ArrowLeft') {
      prevCarousel()
    } else if (e.key === 'ArrowRight') {
      nextCarousel()
    }
  }
}



function clearFilters() {
  searchQuery.value = ''
  selectedHost.value = ''
}

function goToVideo(show) {
  trackRecentPlay({
    id: show.id,
    type: 'show',
    title: show.title,
    host: show.host,
    thumbnail: show.thumbnail,
    url: show.video_url || show.mp4_link || show.trailer_url || show.url,
  })
  router.push(`/videos/${show.id}`)
}

function toBookmarkItem(show) {
  return {
    type: 'show',
    _type: 'show',
    id: show.id,
    title: show.title,
    thumbnail: show.thumbnail,
    artwork: show.thumbnail,
  }
}

function isShowBookmarked(show) {
  if (!show) return false
  return bookmarks.isBookmarked(toBookmarkItem(show))
}

function toggleShowBookmark(show) {
  if (!show) return
  bookmarks.toggle(toBookmarkItem(show))
}

function isNewVideo(show) {
  // Rule: Videos from last 2 months get "new" tag
  if (!show.release_date && !show.released_at && !show.published_date && !show.date) return false

  const releaseDate = new Date(show.release_date || show.released_at || show.published_date || show.date)
  const today = new Date()
  const twoMonthsAgo = new Date(today)
  twoMonthsAgo.setMonth(twoMonthsAgo.getMonth() - 2)

  return releaseDate >= twoMonthsAgo && releaseDate <= today
}

onMounted(async () => {
  isLoading.value = true
  try {
    const data = await apiFetchCached('/api/shows').catch(() => ({ shows: [] }))
    const list = data.shows || []
    shows.value = list

    startCarousel()

    window.addEventListener('keydown', handleKeydown)
  } finally {
    isLoading.value = false
  }
})

onUnmounted(() => {
  if (carouselInterval) clearInterval(carouselInterval)
  window.removeEventListener('keydown', handleKeydown)
})

</script>

<style scoped>
/* ── Mobile hero (hidden on desktop, shown on mobile like Music page) ── */
.videos-mobile-hero {
  display: none;
}

@media (max-width: 768px) {
  :deep(.content-header) {
    display: none !important;
  }

  .videos-mobile-hero {
    display: grid;
    grid-template-columns: minmax(0, 1fr) 58px;
    align-items: end;
    gap: 14px;
    margin: 2px var(--mobile-gutter, 10px) 12px !important;
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
  }

  .videos-mobile-hero-copy {
    min-width: 0;
  }

  .videos-mobile-eyebrow {
    display: block;
    margin-bottom: 8px;
    color: rgba(255, 255, 255, 0.52);
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.18em;
    text-transform: uppercase;
  }

  .videos-mobile-hero-copy h1 {
    margin: 0;
    color: #fff;
    font-size: 38px;
    font-weight: 900;
    letter-spacing: -0.06em;
    line-height: 0.95;
  }

  .videos-mobile-hero-copy p {
    margin: 8px 0 0;
    color: rgba(255, 255, 255, 0.58);
    font-size: 12px;
    line-height: 1.3;
  }

  .videos-mobile-hero-play {
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

  .videos-mobile-hero-play i {
    margin-left: 3px;
    font-size: 18px;
  }

  .videos-mobile-hero-play:disabled {
    opacity: 0.45;
  }
}

.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border-width: 0;
}

.video-section-group {
  display: grid;
  gap: 14px;
  margin-bottom: 22px;
}

.video-section-group-header {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
  padding: 0 2px 0 14px;
  position: relative;
}

.video-section-group-header::before {
  content: '';
  position: absolute;
  left: 0;
  top: 3px;
  bottom: 5px;
  width: 2px;
  border-radius: 999px;
  background: linear-gradient(180deg, rgba(109, 220, 255, 0.9), rgba(255, 255, 255, 0.15));
  opacity: 0.38;
}

.video-section-group-header h3 {
  margin: 0;
  color: #fff;
  font-size: 18px;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

.video-section-group-header p {
  margin: 4px 0 0;
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.12em;
}

.video-section-updated {
  display: inline-block;
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.62);
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
}

/* Video card overlay: Bookmark top-right, Play center */
.video-card-overlay {
  display: flex;
  align-items: center;
  justify-content: center;
}
.video-card-overlay .show-overlay-save {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 2;
  width: 32px;
  height: 32px;
  padding: 0;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(0, 0, 0, 0.5);
  color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s;
}
.video-card-overlay .show-overlay-save:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.35);
}
.video-card-overlay .show-overlay-save.bookmarked {
  color: var(--accent-color, #00d4ff);
  border-color: rgba(0, 212, 255, 0.5);
}
.video-card-overlay .play-btn {
  position: relative;
  z-index: 1;
}

/* 16:9 video grid – enforce ratio on all videos page cards */
.videos-page .show-card {
  transition: transform 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  border-radius: 8px;
}
.videos-page .show-card:hover {
  transform: translateY(-4px);
}

.videos-page .shows-grid .show-thumbnail,
.shows-grid-16x9 .show-thumbnail {
  aspect-ratio: 16 / 9;
  overflow: hidden;
  position: relative;
  border-radius: 8px;
  transition: box-shadow 0.3s ease;
}
.videos-page .show-card:hover .show-thumbnail {
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.4), 0 0 0 1px rgba(255,255,255,0.1);
}

.videos-page .shows-grid .show-thumbnail img,
.shows-grid-16x9 .show-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.6s cubic-bezier(0.25, 1, 0.5, 1);
}
.videos-page .show-card:hover .show-thumbnail img {
  transform: scale(1.06);
}

/* CAROUSEL & LIQUID GLASS STYLES */
.liquid-glass-wrap {
  position: relative;
  width: 100%;
  overflow: hidden;
  border-radius: 20px;
  background: rgba(0,0,0,0.5);
  box-shadow: 0 10px 40px rgba(0,0,0,0.6);
}

.featured-carousel-wrapper {
  position: relative;
  width: 100%;
  padding: 1.5rem;
  background: rgba(0,0,0,0.4);
  /* Use same border aesthetic as plates for cohesion */
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
}

.featured-carousel-container {
  position: relative;
  width: 100%;
  aspect-ratio: 21/9;
  min-height: 250px;
  overflow: hidden;
  border-radius: 16px;
  box-shadow: 0 10px 30px rgba(0,0,0,0.5);
}

.carousel-track {
  display: flex;
  height: 100%;
  transition: transform 0.8s cubic-bezier(0.25, 1, 0.5, 1);
}

.carousel-slide {
  flex: 0 0 100%;
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.cinematic-backdrop {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.cinematic-backdrop img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transform: scale(1.05); /* Slight zoom for dramatic effect */
}

.glass-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(0,0,0,0.2) 0%, rgba(0,0,0,0.8) 100%);
}

.liquid-glass-plate {
  position: absolute;
  bottom: 10%;
  left: 5%;
  width: 40%;
  max-width: 500px;
  min-width: 300px;
  padding: 2rem;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(20px) saturate(150%);
  -webkit-backdrop-filter: blur(20px) saturate(150%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 40px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.2);
  transform: translateZ(0); /* Hardware accel */
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.liquid-glass-plate h2 {
  font-size: 2rem;
  font-weight: 900;
  margin: 0;
  line-height: 1.1;
  color: #fff;
  text-shadow: 0 4px 10px rgba(0,0,0,0.4);
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.carousel-host {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255,255,255,0.9);
  margin: 0;
}

.carousel-actions {
  margin-top: 0.25rem;
}

.btn-glass-play {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.3);
  color: white;
  padding: 0.8rem 1.8rem;
  border-radius: 30px;
  font-size: 1.1rem;
  font-weight: 800;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 10px;
  backdrop-filter: blur(10px);
  transition: all 0.3s cubic-bezier(0.25, 1, 0.5, 1);
  box-shadow: 0 4px 15px rgba(0,0,0,0.2);
}

.btn-glass-play:hover {
  background: rgba(255,255,255,0.95);
  color: #000;
  box-shadow: 0 10px 30px rgba(255,255,255,0.3);
  transform: translateY(-2px) scale(1.02);
}

.carousel-indicators {
  position: absolute;
  bottom: 20px;
  right: 20px;
  display: flex;
  gap: 8px;
  z-index: 10;
}

.indicator {
  box-sizing: content-box; /* padding expands tap area, not shrinks content */
  width: 30px;
  height: 4px;
  padding: 10px 0;
  background: rgba(255,255,255,0.3);
  background-clip: content-box;
  border: none;
  border-radius: 2px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.indicator.active {
  background: #fff;
  width: 40px;
  box-shadow: 0 0 10px rgba(255,255,255,0.5);
}

.indicator:hover {
  background: rgba(255,255,255,0.8);
}

.carousel-nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0,0,0,0.4);
  color: white;
  border: 1px solid rgba(255,255,255,0.1);
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  cursor: pointer;
  z-index: 20;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
  opacity: 0;
}

.featured-carousel-wrapper:hover .carousel-nav {
  opacity: 1;
}

.carousel-nav:hover {
  background: rgba(255,255,255,0.95);
  color: black;
  transform: translateY(-50%) scale(1.1);
}

.carousel-nav.prev {
  left: 30px;
}

.carousel-nav.next {
  right: 30px;
}

/* Hide carousel on mobile — mobile hero card serves as the entry point */
@media (max-width: 768px) {
  .featured-carousel-section {
    display: none;
  }
}

/* Tooltip is hover-only; suppress on touch devices since labels are shown */
@media (hover: none) {
  .beautiful-tooltip {
    display: none;
  }
}

@media (max-width: 768px) {
  .show-card:active {
    transform: scale(0.985);
    background: rgba(255, 255, 255, 0.05);
    transition: transform 0.1s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .show-thumbnail img {
    opacity: 0;
    transition: opacity 0.3s ease-out;
  }

  .show-thumbnail img[src],
  .show-thumbnail img.image-placeholder {
    opacity: 1;
  }

  .shows-page {
    padding: var(--mobile-top-offset, 36px) var(--mobile-gutter, 0px) var(--mobile-bottom-clear, 100px) !important;
  }
  .featured-carousel-wrapper {
    padding: 0.75rem;
  }
  .featured-carousel-container {
    aspect-ratio: 16/9; /* Taller on mobile to fit content */
    border-radius: 12px;
  }
  .carousel-nav {
    width: 44px;
    height: 44px;
    font-size: 1rem;
    opacity: 1; /* Always show arrows on mobile */
  }

  .carousel-nav:active {
    background: rgba(255, 255, 255, 0.85);
    color: black;
    transform: translateY(-50%) scale(0.93);
  }
  .carousel-nav.prev {
    left: 15px;
  }
  .carousel-nav.next {
    right: 15px;
  }
  .liquid-glass-plate {
    width: 85%;
    left: 7.5%;
    bottom: 5%;
    padding: 1rem;
    min-width: 0;
    gap: 0.25rem;
  }
  .liquid-glass-plate h2 {
    font-size: 1.15rem;
  }
  .carousel-host {
    font-size: 0.95rem;
  }
  .btn-glass-play {
    padding: 0.5rem 1rem;
    font-size: 0.9rem;
  }
  .carousel-indicators {
    display: none;
  }
}

.show-series-tag {
  display: inline-block;
  margin-top: 4px;
  font-size: 0.7rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--accent-primary, #6ddcff);
  background: rgba(109, 220, 255, 0.08);
  border: 1px solid rgba(109, 220, 255, 0.18);
  border-radius: 4px;
  padding: 2px 6px;
}

.new-tag {
  position: absolute;
  top: 8px;
  left: 8px;
  z-index: 3;
  font-size: 0.65rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #fff;
  background: linear-gradient(135deg, #ff6b6b, #ff8e53);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 3px;
  padding: 3px 6px;
  box-shadow: 0 2px 8px rgba(255, 107, 107, 0.4);
}

/* Sort controls */
.sort-controls {
  display: flex;
  flex-direction: row;
  flex-wrap: nowrap;
  gap: 8px;
  margin: 1rem 0;
  width: 100%;
}

.sort-btn-label {
  display: none;
  font-size: 0.65rem;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

@media (max-width: 768px) {
  .sort-btn-label {
    display: block;
  }

  .sort-btn {
    flex-direction: column;
    gap: 5px;
    padding: 10px 0;
  }
}

.sort-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px 0;
  min-width: 0;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  font-size: 1.25rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.sort-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
  color: rgba(255, 255, 255, 0.9);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}

.sort-btn.active {
  background: var(--accent-primary, #6ddcff);
  border-color: var(--accent-primary, #6ddcff);
  color: #000;
  box-shadow: 0 4px 12px rgba(109, 220, 255, 0.3);
}

/* Beautiful Tooltips */
.beautiful-tooltip-container {
  position: relative;
  overflow: visible;
}

.beautiful-tooltip {
  position: absolute;
  top: -40px;
  left: 50%;
  transform: translateX(-50%) translateY(10px) scale(0.85);
  opacity: 0;
  pointer-events: none;
  background-color: #0b0c10; /* Pure dark background */
  color: #fff;
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-family: inherit;
  font-weight: 600;
  white-space: nowrap;
  letter-spacing: 0.03em;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.08);

  /* Super beautiful bouncy animation */
  transition: opacity 0.3s ease, transform 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  z-index: 100;
}

.beautiful-tooltip::after {
  content: '';
  position: absolute;
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%);
  border-width: 5px 5px 0;
  border-style: solid;
  border-color: #0b0c10 transparent transparent transparent;
}

.beautiful-tooltip-container:hover .beautiful-tooltip {
  opacity: 1;
  transform: translateX(-50%) translateY(0) scale(1);
}

</style>
