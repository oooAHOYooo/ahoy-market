<template>
  <div class="home-page">
    <!-- Global subpage hero (one line on mobile: Home · Explore) -->
    <section class="explore-hero">
      <div
        class="explore-hero-inner"
        :style="{
          backgroundImage: `url(${selectedGif})`,
          backgroundPosition: `${parallaxX}% ${parallaxY}%`
        }"
        @mouseenter="enableParallax = true"
        @mouseleave="resetParallax"
        @mousemove="handleParallaxMove"
      >
        <router-link to="/about" class="hero-logo-container">
          <img :src="logoUrl" alt="Ahoy Logo" class="hero-logo" />
        </router-link>
        
        <!-- Search Bar -->
        <div class="hero-search-wrapper" :class="{ 'has-results': showResults && (searchResults.length > 0 || searchQuery.trim()), 'expanded': searchExpanded }">
          <input
            type="text"
            class="hero-search-input"
            :placeholder="currentPlaceholder"
            v-model="searchQuery"
            @input="handleSearchInput"
            @keydown.enter="handleSearch"
            @keydown.down.prevent="moveSearchSelection(1)"
            @keydown.up.prevent="moveSearchSelection(-1)"
            @keydown.esc="clearSearch"
            @focus="isSearchFocused = true"
            @blur="handleSearchBlur"
          />

          <!-- Recent Searches List (when empty and focused) -->
          <div v-if="isSearchFocused && !searchQuery && recentSearches.length > 0" class="search-results-container recent-searches">
            <div class="search-results-header">
              <span class="results-metadata">Recent Searches</span>
              <button type="button" class="search-action-btn" @click.stop="clearRecentSearches">Clear All</button>
            </div>
            <div class="search-results-list">
              <div
                v-for="(item, i) in recentSearches"
                :key="i"
                class="search-result-item recent-item"
                @mousedown="selectRecentSearch(item)"
              >
                <div class="result-icon"><i class="fas fa-history"></i></div>
                <div class="result-info">
                  <div class="result-title">{{ item }}</div>
                </div>
                <button type="button" class="remove-recent" @mousedown.stop="removeRecentSearch(item)">
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>
          </div>

          <!-- Search Results -->
          <div v-if="showResults && searchResults.length > 0" class="search-results-container">
            <div class="search-results-header">
              <span class="results-count">{{ searchResults.length }} {{ searchResults.length === 1 ? 'result' : 'results' }}</span>
              <div class="search-actions">
                <button
                  type="button"
                  class="search-action-btn"
                  :class="{ active: searchExpanded }"
                  @click="searchExpanded = !searchExpanded"
                  :title="searchExpanded ? 'Collapse' : 'Expand'"
                >
                  <i :class="searchExpanded ? 'fas fa-compress-alt' : 'fas fa-expand-alt'"></i>
                </button>
                <button
                  type="button"
                  class="search-action-btn"
                  @click="saveSearch"
                  title="Save Search"
                >
                  <i class="fas fa-bookmark"></i>
                </button>
                <button
                  type="button"
                  class="search-action-btn close-btn"
                  @click="clearSearch"
                  title="Clear"
                >
                  <i class="fas fa-times"></i>
                </button>
              </div>
            </div>

            <div class="search-results-list">
              <a
                v-for="result in displayedResults"
                :key="`${result.type}-${result.id || result.slug || result.title || result.name}`"
                :href="getResultUrl(result)"
                class="search-result-item"
                :class="{ selected: displayedResults[selectedSearchIndex] === result }"
                @click.prevent="navigateToResult(result)"
                @mouseenter="selectedSearchIndex = displayedResults.indexOf(result)"
              >
                <div class="result-image">
                  <img
                    :src="result.image || result.cover_art || result.artwork || result.thumbnail || '/static/img/default-cover.jpg'"
                    :alt="result.title || result.name"
                    loading="lazy"
                  />
                  <div class="result-type-badge">{{ getSearchResultBadgeLabel(result) }}</div>
                </div>
                <div class="result-info">
                  <div class="result-title" v-html="highlightSearchText(result.title || result.name, searchQuery)"></div>
                  <div class="result-subtitle" v-html="highlightSearchText(getSearchResultSubtitle(result), searchQuery)"></div>
                </div>
                <div class="result-arrow">
                  <i class="fas fa-chevron-right"></i>
                </div>
              </a>
            </div>
            <button
              v-if="searchResults.length > displayedResults.length"
              type="button"
              class="search-view-all"
              @mousedown.prevent="openFullSearch"
            >
              View all results for "{{ searchQuery }}"
            </button>
          </div>

          <div v-else-if="showResults && searchQuery.trim() && searchCatalogLoading" class="search-results-container search-no-results">
            Searching...
          </div>

          <div v-else-if="showResults && searchQuery.trim()" class="search-results-container search-no-results">
            No results for "{{ searchQuery }}"
          </div>
        </div>
      </div>
    </section>

    <!-- Recently Played -->
    <RecentlyPlayedWidget />

    <!-- What's New at Ahoy -->
    <section class="whats-new-section">
      <div class="whats-new-container">
        <div class="whats-new-header">
          <div class="whats-new-title-group">
            <div class="whats-new-icon"><i class="fas fa-bullhorn"></i></div>
            <div class="whats-new-text">
              <h2>What's New at Ahoy</h2>
              <p>Platform & Content Updates</p>
            </div>
          </div>
          <a href="/whats-new" class="view-all-link">
            View Archive <i class="fas fa-arrow-right"></i>
          </a>
        </div>

        <!-- Loading skeleton -->
        <div v-if="whatsNewLoading" class="wn-skeleton">
          <div class="wn-spotlight-skeleton skeleton"></div>
          <div class="wn-chips-skeleton">
            <div v-for="i in 3" :key="i" class="skeleton wn-chip-skeleton"></div>
          </div>
        </div>

        <!-- Spotlight + month chips -->
        <div v-else-if="whatsNewSpotlight" class="wn-body">
          <!-- Featured spotlight card -->
          <a :href="getUpdateUrl(whatsNewSpotlight)" class="wn-spotlight">
            <div class="wn-spotlight-image">
              <img
                v-if="getUpdateThumb(whatsNewSpotlight)"
                :src="getUpdateThumb(whatsNewSpotlight)"
                :alt="whatsNewSpotlight.title"
                loading="lazy"
              />
              <div v-else class="wn-spotlight-placeholder">
                <i :class="getSectionIcon(whatsNewSpotlight.section)"></i>
              </div>
            </div>
            <div class="wn-spotlight-content">
              <div class="wn-spotlight-meta">
                <span class="wn-section-badge">
                  <i :class="getSectionIcon(whatsNewSpotlight.section)"></i>
                  {{ whatsNewSpotlight.section || 'Update' }}
                </span>
                <span class="wn-spotlight-date">{{ formatWhatsNewDate(whatsNewSpotlight.date) }}</span>
              </div>
              <h3>{{ whatsNewSpotlight.title }}</h3>
              <p>{{ whatsNewSpotlight.description }}</p>
            </div>
            <div class="wn-spotlight-arrow"><i class="fas fa-arrow-right"></i></div>
          </a>

          <!-- Secondary items -->
          <div v-if="whatsNewRest.length" class="wn-rest">
            <a
              v-for="(update, i) in whatsNewRest"
              :key="update.title || i"
              :href="getUpdateUrl(update)"
              class="wn-rest-item"
            >
              <div class="wn-rest-thumb">
                <img v-if="getUpdateThumb(update)" :src="getUpdateThumb(update)" :alt="update.title" loading="lazy" />
                <i v-else :class="getSectionIcon(update.section)"></i>
              </div>
              <div class="wn-rest-content">
                <span class="wn-rest-title">{{ update.title }}</span>
                <span class="wn-rest-date">{{ formatWhatsNewDate(update.date) }}</span>
              </div>
              <i class="fas fa-chevron-right wn-rest-arrow"></i>
            </a>
          </div>

          <!-- Month chips -->
          <div v-if="whatsNewArchive.length" class="wn-month-chips">
            <a
              v-for="month in whatsNewArchive"
              :key="`${month.year}-${month.month}`"
              :href="`/whats-new/${month.year}/${month.month}`"
              class="wn-month-chip"
            >
              {{ month.month_name }}
              <span class="wn-chip-count">{{ month.total_items }}</span>
            </a>
          </div>
        </div>

        <!-- Empty state -->
        <div v-else class="whats-new-empty">
          <p>No updates available at this time.</p>
          <a href="/whats-new" class="view-archive-link">View Archive</a>
        </div>
      </div>
    </section>

    <!-- My Saves -->
    <MySavesWidget />

    <!-- Explore Widgets -->
    <ExploreWidgets />

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiUrl } from '../composables/useApi'
import { usePlayerStore } from '../stores/player'
import { useRadioStation } from '../composables/useRadioStation'
import {
  getSearchResultBadgeLabel,
  getSearchResultSubtitle,
  getSearchResultUrl,
  highlightSearchText,
  loadSearchCatalog,
  runFlatSearch
} from '../composables/useSearch'
import { getWhatsNewDetailPath, getWhatsNewMonthPath } from '../utils/whatsNew'
import ExploreWidgets from '../components/ExploreWidgets.vue'
import MySavesWidget from '../components/MySavesWidget.vue'
import RecentlyPlayedWidget from '../components/RecentlyPlayedWidget.vue'
import logoUrl from '@/assets/u_ahoy23.png'

const router = useRouter()
const playerStore = usePlayerStore()

const dynamicGreeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return 'Good Morning'
  if (hour < 18) return 'Good Afternoon'
  return 'Good Evening'
})

const showTransientGreeting = ref(true)
let transientGreetingTimer = null
const currentPlaceholder = computed(() => {
  if (showTransientGreeting.value && !searchQuery.value) {
    return `Ahoy, ${dynamicGreeting.value}...`
  }
  return 'Search artists, tracks, or shows...'
})

// Search GIF background
const searchGifs = [
  'https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExeGlreWRqaHZxc295NHNvZWs4MWJoeTIwdXk1NnNuN2syOTE4Z3JleSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/14hS1ZEmSfKdTW/giphy.gif',
  'https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExdnI2M2VxZmhkeTM1bHVoZmV0NmdmYzVjeWt3eHc1eGZtOWk4N3c0YyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/AS9LIFttYzkc0/giphy.gif',
  'https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExYjB3cjhjNXEwMXhrcTFvYnF4Zm5xamduNm8ycjB4ZnJneDhyb2IzNiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/wSYE7n6pk9dqRXzitR/giphy.gif',
  'https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExMWVkeG1sY3hvYTlwMjl0bWZrbTI3bXlqOGQ2cmYyZXVmZ2RuZWIwcCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xWC0BCZtkDxE869erD/giphy.gif',
  'https://media4.giphy.com/media/v1.Y2lkPTc5MGI3NjExdjJ4Mml1ajMzNGh1ODVrN3J3cnVtbjZkeXZnN29wNmQ2aHhncTJ0OCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/l1J9BYe5eZccC4Nck/giphy.gif',
  'https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExOWZnNnhxbjgzM3B1NXdzOWJwZjJnM3hveTJwNnE1bjZrb3ZicXU3bSZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3oGRFs7yHPDlB8JYsg/giphy.gif'
]
const selectedGif = ref('')

// Parallax effect
const enableParallax = ref(false)
const parallaxX = ref(50)
const parallaxY = ref(50)

function handleParallaxMove(event) {
  if (!enableParallax.value) return

  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  // Calculate percentage position (with subtle movement range)
  const xPercent = (x / rect.width) * 100
  const yPercent = (y / rect.height) * 100

  // Smoothly interpolate (40-60% range for subtle effect)
  parallaxX.value = 40 + (xPercent / 100) * 20
  parallaxY.value = 40 + (yPercent / 100) * 20
}

function resetParallax() {
  enableParallax.value = false
  parallaxX.value = 50
  parallaxY.value = 50
}

// Search
const searchQuery = ref('')
const searchResults = ref([])
const searchExpanded = ref(false)
const isSearchFocused = ref(false)
const showResults = ref(false)
const searchCatalogLoading = ref(false)
const selectedSearchIndex = ref(0)
const searchDebounceTimer = ref(null)
const recentSearches = ref([])
let allSearchableData = {
  tracks: [],
  albums: [],
  shows: [],
  podcasts: [],
  artists: [],
  events: []
}

const displayedResults = computed(() => {
  return searchExpanded.value ? searchResults.value : searchResults.value.slice(0, 6)
})

async function loadSearchableData() {
  searchCatalogLoading.value = true
  try {
    allSearchableData = await loadSearchCatalog()
    if (searchQuery.value.trim()) performSearch(searchQuery.value)
  } catch (e) {
    console.error('Error loading searchable data', e)
  } finally {
    searchCatalogLoading.value = false
  }
}

function performSearch(query) {
  if (!query || query.trim().length < 1) {
    searchResults.value = []
    showResults.value = false
    return
  }

  showResults.value = true

  // Add to recent searches if not already there
  if (query.length >= 3) {
    addRecentSearch(query.trim())
  }

  searchResults.value = runFlatSearch(allSearchableData, query, 50)
  selectedSearchIndex.value = 0
}

function handleSearchInput() {
  if (searchDebounceTimer.value) {
    clearTimeout(searchDebounceTimer.value)
  }

  searchDebounceTimer.value = setTimeout(() => {
    performSearch(searchQuery.value)
  }, 120)
}

function handleSearch() {
  if (!searchQuery.value.trim()) return
  if (searchDebounceTimer.value) {
    clearTimeout(searchDebounceTimer.value)
  }
  performSearch(searchQuery.value)
  if (searchResults.value.length > 0) {
    navigateToResult(displayedResults.value[selectedSearchIndex.value] || searchResults.value[0])
  }
}

function moveSearchSelection(delta) {
  if (!displayedResults.value.length) return
  selectedSearchIndex.value = (selectedSearchIndex.value + delta + displayedResults.value.length) % displayedResults.value.length
}

function clearSearch() {
  searchQuery.value = ''
  searchResults.value = []
  searchExpanded.value = false
  showResults.value = false
  selectedSearchIndex.value = 0
}

function saveSearch() {
  const query = searchQuery.value.trim()
  if (query) addRecentSearch(query)
}

// Search History Actions
function loadRecentSearches() {
  try {
    const saved = localStorage.getItem('ahoy.recentSearches')
    if (saved) recentSearches.value = JSON.parse(saved)
  } catch {}
}

function addRecentSearch(query) {
  if (!query) return
  const list = [query, ...recentSearches.value.filter(s => s !== query)].slice(0, 8)
  recentSearches.value = list
  localStorage.setItem('ahoy.recentSearches', JSON.stringify(list))
}

function removeRecentSearch(query) {
  const list = recentSearches.value.filter(s => s !== query)
  recentSearches.value = list
  localStorage.setItem('ahoy.recentSearches', JSON.stringify(list))
}

function clearRecentSearches() {
  recentSearches.value = []
  localStorage.setItem('ahoy.recentSearches', JSON.stringify([]))
}

function selectRecentSearch(query) {
  searchQuery.value = query
  performSearch(query)
}

function handleSearchBlur() {
  // Delay blur to allow clicking the list
  setTimeout(() => {
    isSearchFocused.value = false
  }, 200)
}

function getResultUrl(result) {
  return getSearchResultUrl(result)
}

function openFullSearch() {
  router.push({ path: '/search', query: { q: searchQuery.value.trim() } })
  clearSearch()
}

function navigateToResult(result) {
  router.push(getResultUrl(result))
  clearSearch()
}

// AHOY TV
const tvChannels = ref([])
const tvChannelIndex = ref(0)
const tvCurrent = ref(null)
const tvCurrentChannel = ref(null)
const tvNowByChannel = ref({})
const tvNextByChannel = ref({})
let tvScheduleInterval = null

const TV_CHANNEL_NAMES = {
  misc: 'Channel 01 — Shows',
  films: 'Channel 02 — Films',
  'music-videos': 'Channel 03 — Music',
  'live-shows': 'Channel 04 — Live Shows',
}

function getTVChannelName(ch, idx) {
  return TV_CHANNEL_NAMES[ch.id] || `Channel ${String(idx + 1).padStart(2, '0')} — ${ch.name || 'Unknown'}`
}

function computeTVSchedule() {
  const hour = new Date().getHours()
  const nowBy = {}
  const nextBy = {}
  for (let i = 0; i < tvChannels.value.length; i++) {
    const ch = tvChannels.value[i]
    if (ch?.items?.length) {
      const itemIndex = hour % ch.items.length
      nowBy[ch.id] = ch.items[itemIndex]
      nextBy[ch.id] = ch.items.length > itemIndex + 1 ? ch.items[itemIndex + 1] : ch.items[0]
    }
  }
  tvNowByChannel.value = nowBy
  tvNextByChannel.value = nextBy
  if (tvCurrentChannel.value?.id) {
    const id = tvCurrentChannel.value.id
    if (nowBy[id]) tvCurrent.value = nowBy[id]
  }
}

function selectTVChannel(index) {
  if (!tvChannels.value.length) return
  tvChannelIndex.value = (index + tvChannels.value.length) % tvChannels.value.length
  const ch = tvChannels.value[tvChannelIndex.value]
  tvCurrentChannel.value = { ...ch, name: getTVChannelName(ch, tvChannelIndex.value) }
  if (tvNowByChannel.value[ch.id]) {
    tvCurrent.value = tvNowByChannel.value[ch.id]
  } else if (ch.items?.length) {
    tvCurrent.value = ch.items[0]
  } else {
    tvCurrent.value = { id: 'placeholder', title: 'No content available', thumbnail: '/static/img/default-cover.jpg', host: ch.name }
  }
}

function switchTVChannel(direction) {
  if (!tvChannels.value.length) return
  selectTVChannel(tvChannelIndex.value + (direction === 'next' ? 1 : -1))
}

function playShow(show) {
  if (!show?.id || show.id === 'placeholder' || show.id === 'error') return
  router.push({ path: '/videos', query: { play: show.id } })
}

// Live Radio (sync with player store)
const {
  currentTrack: radioCurrent,
  upNext: radioUpNext,
  isRadioAudible: radioIsPlaying,
  syncLivePlayback: syncHomeRadio,
  toggleRadioAudio,
} = useRadioStation(playerStore)

function toggleRadio() {
  if (radioIsPlaying.value) {
    toggleRadioAudio()
  } else {
    syncHomeRadio(true)
  }
}

// What's New
const whatsNew = ref([])
const whatsNewArchive = ref([])
const whatsNewLoading = ref(true)

const whatsNewSpotlight = computed(() => whatsNew.value[0] || null)
const HOMEPAGE_WHATS_NEW_LIMIT = 14
const whatsNewRest = computed(() => {
  const spotlight = whatsNewSpotlight.value
  return whatsNew.value
    .slice(1, HOMEPAGE_WHATS_NEW_LIMIT)
    .filter((update) => {
      if (!spotlight) return true
      return !(
        String(update?.title || '').trim().toLowerCase() === String(spotlight.title || '').trim().toLowerCase() &&
        String(update?.section || '').trim().toLowerCase() === String(spotlight.section || '').trim().toLowerCase()
      )
    })
})

function formatWhatsNewDate(dateString) {
  if (!dateString) return ''
  try {
    const d = new Date(dateString)
    return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
  } catch {
    return dateString
  }
}

function getUpdateUrl(update) {
  if (update.year && update.month && update.section) return getWhatsNewDetailPath(update)
  if (update.year && update.month) return getWhatsNewMonthPath(update)
  if (update.link) return update.link
  return '/whats-new'
}

function getWhatsNewUrl(update) {
  return getUpdateUrl(update)
}

function getUpdateThumb(update) {
  if (!update) return ''
  if (update.thumbnail_url || update.thumbnail || update.image_url) {
    return update.thumbnail_url || update.thumbnail || update.image_url || ''
  }
  if (Array.isArray(update.thumbnails) && update.thumbnails.length) {
    for (const thumb of update.thumbnails) {
      if (typeof thumb === 'string' && thumb) return thumb
      if (thumb && typeof thumb === 'object') {
        const url = thumb.url || thumb.src || thumb.thumbnail || thumb.image || thumb.path
        if (url) return url
      }
    }
  }
  if (Array.isArray(update.thumbnail_grid) && update.thumbnail_grid.length) {
    for (const thumb of update.thumbnail_grid) {
      if (typeof thumb === 'string' && thumb) return thumb
      if (thumb && typeof thumb === 'object') {
        const url = thumb.url || thumb.src || thumb.thumbnail || thumb.image || thumb.path
        if (url) return url
      }
    }
  }
  return ''
}

const SECTION_ICONS = {
  music: 'fas fa-music',
  videos: 'fas fa-play-circle',
  events: 'fas fa-calendar-alt',
  platform: 'fas fa-rocket',
  merch: 'fas fa-tag',
  artists: 'fas fa-user',
}

function getSectionIcon(section) {
  return SECTION_ICONS[section] || 'fas fa-bullhorn'
}

// Parse live-tv API response (same shape as Flask: { channels: [ { id, name, items }, ... ] })
function parseLiveTvChannels(data) {
  const raw = data?.channels ?? data?.data?.channels ?? []
  if (!Array.isArray(raw)) return []
  return raw.map((c) => ({
    ...c,
    id: c?.id ?? 'misc',
    name: c?.name ?? 'Channel',
    items: Array.isArray(c?.items) ? c.items : [],
  }))
}

onMounted(async () => {
  // Transient greeting timer
  transientGreetingTimer = setTimeout(() => {
    showTransientGreeting.value = false
  }, 3000)

  // Randomly select search background GIF
  selectedGif.value = searchGifs[Math.floor(Math.random() * searchGifs.length)]

  // Load searchable data for instant search
  loadSearchableData()
  loadRecentSearches()

  // AHOY TV channels — network first with cache-bust to avoid stale empty response, then cache fallback
  try {
    let data = null
    try {
      const response = await fetch(apiUrl('/api/live-tv/channels?_=' + Date.now()), { credentials: 'include' })
      data = await response.json()
    } catch {
      data = await apiFetchCached('/api/live-tv/channels').catch(() => null)
    }
    const channels = data ? parseLiveTvChannels(data) : []
    tvChannels.value = channels
    if (channels.length) {
      const ch = channels.find((c) => c.id === 'misc') || channels[0]
      tvChannelIndex.value = channels.findIndex((c) => c.id === ch.id)
      computeTVSchedule()
      selectTVChannel(tvChannelIndex.value)
    } else {
      tvCurrent.value = { id: 'placeholder', title: 'Loading AHOY TV...', thumbnail: '/static/img/default-cover.jpg', host: 'Ahoy TV' }
      tvCurrentChannel.value = { id: 'misc', name: 'Channel 01 — Misc' }
    }
    tvScheduleInterval = setInterval(computeTVSchedule, 60 * 1000)
  } catch {
    tvCurrent.value = { id: 'error', title: 'AHOY TV', thumbnail: '/static/img/default-cover.jpg', host: 'Ahoy TV' }
    tvCurrentChannel.value = { id: 'misc', name: 'Channel 01 — Misc' }
  }

  // What's New — plain fetch, no localStorage cache so it's always fresh
  whatsNewLoading.value = true
  try {
    const res = await fetch(apiUrl('/api/whats-new'), { credentials: 'include' })
    const data = res.ok ? await res.json() : { updates: [], archive: [] }
    whatsNew.value = Array.isArray(data.updates) ? data.updates.slice(0, HOMEPAGE_WHATS_NEW_LIMIT) : []
    whatsNewArchive.value = Array.isArray(data.archive) ? data.archive.slice(0, 5) : []
  } catch {
    whatsNew.value = []
    whatsNewArchive.value = []
  } finally {
    whatsNewLoading.value = false
  }
})

onUnmounted(() => {
  if (transientGreetingTimer) clearTimeout(transientGreetingTimer)
  if (tvScheduleInterval) clearInterval(tvScheduleInterval)
})
</script>

<!-- Styles from Flask home.html inline block so SPA home matches main branch -->
<style>
.home-page .live-dashboard { margin-bottom: 2rem; }
.home-page .dashboard-grid {
  display: grid;
  grid-template-columns: 220px 1.55fr 1fr;
  gap: 1.5rem;
  height: 420px;
  min-height: 420px;
}
.home-page .dashboard-left .sidebar-content { gap: 0.75rem; }
.home-page .dashboard-left .whats-new-item.compact { padding: 0.85rem 0.9rem; }
.home-page .dashboard-left .whats-new-content h3 { font-size: 0.88rem; }
.home-page .dashboard-left .whats-new-content p { font-size: 0.78rem; -webkit-line-clamp: 2; }
.home-page .dashboard-left .whats-new-date { font-size: 0.72rem; }
/*.explore-hero-inner needs flex column for search bar*/
.home-page .explore-hero-inner {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1.5rem;
    padding: 2.5rem 2.5rem;
    min-height: 357px;
    text-align: center;
    border-radius: 28px;
    background-size: 110%;
    background-position: center;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
    position: relative;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: background-position 2s cubic-bezier(0.4, 0, 0.2, 1);
    animation: hero-drift 60s infinite alternate ease-in-out;
}

@keyframes hero-drift {
    0% { background-size: 110%; }
    100% { background-size: 130%; }
}

/* Dark overlay to ensure text readability */
.home-page .explore-hero-inner::before {
    content: '';
    position: absolute;
    inset: 0;
    background: linear-gradient(135deg, rgba(0, 0, 0, 0.8) 0%, rgba(0, 0, 0, 0.5) 100%);
    backdrop-filter: blur(6px);
    z-index: 0;
}

.home-page .explore-hero-inner > * {
    position: relative;
    z-index: 1;
}

.hero-logo-container {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 1.5rem;
    width: 100%;
}

.hero-logo {
    height: 160px;
    width: auto;
    filter: drop-shadow(0 0 36px rgba(0, 162, 255, 0.72));
    transition: all 0.5s cubic-bezier(0.19, 1, 0.22, 1);
    mix-blend-mode: screen;
}

.hero-logo:hover {
    transform: scale(1.05);
}

.hero-greeting {
    margin-bottom: 2rem;
    text-align: center;
    color: #fff;
    animation: fadeIn 0.8s ease-out;
    mix-blend-mode: overlay;
}

.hero-greeting h1 {
    font-size: 2.5rem;
    font-weight: 900;
    margin: 0;
    letter-spacing: -0.02em;
    text-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
}

.hero-greeting p {
    font-size: 1.1rem;
    opacity: 0.8;
    margin: 0.5rem 0 0;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.hero-search-wrapper {
  position: relative;
  width: 100%;
  max-width: 600px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.hero-search-wrapper.has-results {
  max-width: 900px;
}

.hero-search-wrapper.expanded {
  max-width: 100%;
}

.hero-search-input {
  width: 100%;
  padding: 0.9rem 1.5rem;
  border-radius: 99px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(16px) saturate(180%);
  -webkit-backdrop-filter: blur(16px) saturate(180%);
  color: #fff;
  font-size: 1rem;
  font-weight: 500;
  outline: none;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  text-align: center;
}

.hero-search-input::placeholder {
  color: rgba(255, 255, 255, 0.6);
  text-align: center;
}

.hero-search-input:focus {
  background: rgba(0, 0, 0, 0.5);
  border-color: rgba(255, 255, 255, 0.5);
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.5);
  transform: scale(1.01);
}

.hero-search-wrapper.has-results .hero-search-input {
  border-radius: 20px 20px 0 0;
  border-bottom: none;
}

/* Search Results Container - Glass Neumorphism */
.search-results-container {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-top: none;
  border-radius: 0 0 24px 24px;
  box-shadow:
    0 20px 60px -10px rgba(0, 0, 0, 0.6),
    inset 0 1px 0 rgba(255, 255, 255, 0.1),
    inset 0 -1px 40px rgba(0, 0, 0, 0.2);
  animation: slideDown 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.search-no-results {
  padding: 1rem;
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.95rem;
  text-align: center;
}

@keyframes slideDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.search-results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  background: linear-gradient(180deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0) 100%);
}

.results-count {
  font-size: 0.85rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.search-actions {
  display: flex;
  gap: 0.5rem;
}

.search-action-btn {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  font-size: 0.85rem;
}

@media (pointer: coarse) {
  .search-action-btn {
    width: 44px;
    height: 44px;
  }
}

.search-action-btn:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
  color: #fff;
  transform: scale(1.1);
  box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
}

.search-action-btn:active {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(0.92);
  box-shadow: none;
}

.search-action-btn.active {
  background: rgba(99, 102, 241, 0.3);
  border-color: rgba(99, 102, 241, 0.5);
  color: #fff;
}

.search-action-btn.close-btn:hover {
  background: rgba(255, 0, 0, 0.2);
  border-color: rgba(255, 0, 0, 0.4);
  color: #ff6b6b;
}

.search-results-list {
  max-height: 480px;
  overflow-y: auto;
  padding: 0.75rem;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 0.75rem;
}

.hero-search-wrapper.expanded .search-results-list {
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  max-height: 600px;
}

.search-results-list::-webkit-scrollbar {
  width: 8px;
}

.search-results-list::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
}

.search-results-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.search-results-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.search-result-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.85rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 16px;
  text-decoration: none;
  color: inherit;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
}

.search-result-item:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateX(4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

.search-result-item:active {
  background: rgba(255, 255, 255, 0.14);
  transform: scale(0.98);
  box-shadow: none;
}

.search-result-item.selected {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.32);
}

.search-view-all {
  width: 100%;
  padding: 0.85rem 1rem 1rem;
  border: 0;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.78);
  font-weight: 700;
  cursor: pointer;
}

.search-view-all:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

:deep(.search-highlight) {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  border-radius: 3px;
  padding: 0 0.08em;
}

.result-image {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  overflow: hidden;
  flex-shrink: 0;
  position: relative;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
}

.result-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.result-type-badge {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: #fff;
  font-size: 0.65rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.result-info {
  flex: 1;
  min-width: 0;
}

.result-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #fff;
  margin-bottom: 0.25rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-subtitle {
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.6);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.result-arrow {
  color: rgba(255, 255, 255, 0.3);
  font-size: 0.85rem;
  transition: all 0.2s;
  flex-shrink: 0;
}

.search-result-item:hover .result-arrow {
  color: rgba(255, 255, 255, 0.8);
  transform: translateX(4px);
}

@media (max-width: 768px) {
  .home-page .podcasts-hero-inner {
    min-height: 234px;
    padding: 1.5rem 1.5rem;
  }

  .home-page .explore-hero-inner {
    min-height: 260px;
    padding: 1.5rem 1.25rem;
    gap: 0.85rem;
  }

  .hero-logo {
    height: 92px;
  }

  .hero-search-wrapper {
    max-width: 100%;
  }

  .hero-search-input {
    padding: 0.8rem 1rem;
    font-size: 0.95rem;
  }

  .search-results-container {
    border-radius: 0 0 18px 18px;
  }

  .search-results-list {
    grid-template-columns: 1fr;
    max-height: 300px;
  }

  .hero-search-wrapper.expanded .search-results-list {
    grid-template-columns: 1fr;
    max-height: 360px;
  }

  .search-action-btn {
    width: 30px;
    height: 30px;
    font-size: 0.72rem;
  }
}

/* Recent Searches Expansion */
.recent-searches {
  border-top: none;
  border-radius: 0 0 24px 24px;
  background: rgba(10, 10, 15, 0.98) !important;
  box-shadow: 0 30px 60px rgba(0, 0, 0, 0.8) !important;
}

.results-metadata {
  font-size: 0.75rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  color: rgba(255, 255, 255, 0.4);
}

.recent-item {
  padding: 0.75rem 1rem !important;
  gap: 0.8rem !important;
}

.recent-item .result-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.3);
  font-size: 0.9rem;
}

.remove-recent {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.2);
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
}

@media (pointer: coarse) {
  .remove-recent {
    width: 44px;
    height: 44px;
  }
}

.remove-recent:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #ff4b2b;
}

.remove-recent:active {
  background: rgba(255, 80, 50, 0.18);
  color: #ff4b2b;
  transform: scale(0.88);
}

.compact-mode .search-results-list {
  padding: 0.5rem;
  gap: 0.5rem;
}

.home-page .dashboard-main {
  position: relative;
  border-radius: 24px;
  overflow: hidden;
  cursor: pointer;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: #000;
  box-shadow: 0 20px 40px -10px rgba(0, 0, 0, 0.5);
  transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1), border-color 0.3s;
}
.home-page .dashboard-main:hover { border-color: rgba(255, 255, 255, 0.2); transform: scale(1.005); }
.home-page .dash-preview { height: 100%; width: 100%; position: relative; }
.home-page .dash-bg {
  width: 100%; height: 100%; object-fit: cover;
  transition: transform 0.6s cubic-bezier(0.25, 0.8, 0.25, 1); opacity: 0.85;
}
.home-page .dashboard-main:hover .dash-bg { transform: scale(1.03); opacity: 0.6; }
.home-page .dash-overlay {
  position: absolute; inset: 0;
  background: linear-gradient(to top, rgba(0,0,0,0.95) 0%, rgba(0,0,0,0.6) 40%, rgba(0,0,0,0.1) 100%);
  padding: 2.5rem; display: flex; flex-direction: column; justify-content: flex-end;
}
.home-page .dash-badges { position: absolute; top: 1.5rem; left: 1.5rem; display: flex; gap: 0.75rem; z-index: 2; }
.home-page .channel-nav { position: absolute; top: 1.5rem; right: 1.5rem; display: flex; gap: 0.5rem; z-index: 2; }
.home-page .channel-nav-btn {
  width: 36px; height: 36px; border-radius: 50%;
  background: rgba(0,0,0,0.6); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(255,255,255,0.2); color: white;
  display: flex; align-items: center; justify-content: center; cursor: pointer; font-size: 0.875rem;
}
.home-page .channel-nav-btn:hover { background: rgba(0,0,0,0.8); border-color: rgba(255,255,255,0.4); transform: scale(1.1); }
.home-page .live-badge {
  background: #ff0000; color: white; padding: 0.35rem 0.85rem; border-radius: 8px;
  font-weight: 800; font-size: 0.75rem; letter-spacing: 0.08em;
  box-shadow: 0 4px 12px rgba(255,0,0,0.4); text-transform: uppercase;
}
.home-page .channel-badge {
  background: rgba(20,20,20,0.75); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
  color: rgba(255,255,255,0.9); padding: 0.35rem 0.85rem; border-radius: 8px;
  font-weight: 600; font-size: 0.75rem; border: 1px solid rgba(255,255,255,0.1);
}
.home-page .dash-content { position: relative; z-index: 2; }
.home-page .dash-content h2 {
  font-size: 2.5rem; font-weight: 800; margin: 0 0 0.5rem 0; line-height: 1.1; letter-spacing: -0.02em;
  text-shadow: 0 2px 10px rgba(0,0,0,0.8);
  display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.home-page .dash-content p { font-size: 1.1rem; color: rgba(255,255,255,0.8); margin: 0 0 1.75rem 0; font-weight: 500; }
.home-page .dash-actions { display: flex; gap: 0.75rem; align-items: center; flex-wrap: wrap; }
.home-page .dash-play-btn {
  background: rgba(20,20,20,0.6); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  color: #fff; border: 1px solid rgba(255,255,255,0.1); padding: 0.85rem 1.75rem; border-radius: 99px;
  font-weight: 700; font-size: 0.95rem; display: inline-flex; align-items: center; gap: 0.6rem;
  cursor: pointer; transition: all 0.2s; box-shadow: 0 4px 20px rgba(255,255,255,0.2); text-decoration: none;
}
.home-page .dash-play-btn:hover { background: #f0f0f0; color: #111; transform: translateY(-2px); }
.home-page .dash-guide-btn {
  background: rgba(255,255,255,0.1); color: white; border: 1px solid rgba(255,255,255,0.2);
  padding: 0.85rem 1.75rem; border-radius: 99px; font-weight: 700; font-size: 0.95rem;
  display: inline-flex; align-items: center; gap: 0.6rem; text-decoration: none;
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
}
.home-page .dash-guide-btn:hover { background: rgba(255,255,255,0.2); border-color: rgba(255,255,255,0.3); transform: translateY(-2px); }
.home-page .dashboard-sidebar {
  display: flex; flex-direction: column; gap: 1rem;
  background: rgba(20,20,20,0.6); backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-radius: 24px; border: 1px solid rgba(255,255,255,0.08); padding: 1.5rem; height: 100%;
  overflow-y: auto; overflow-x: hidden;
  overscroll-behavior-y: contain;
  -webkit-overflow-scrolling: touch;
  scroll-behavior: smooth;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.24) transparent;
  scrollbar-gutter: stable;
}
.home-page .sidebar-header { border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 1rem; margin-bottom: 0.5rem; }
.home-page .sidebar-header h3 { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.15em; color: rgba(255,255,255,0.5); margin: 0; font-weight: 700; }
.home-page .dash-item {
  display: flex; align-items: center; gap: 1.25rem; padding: 1rem; border-radius: 16px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); transition: all 0.2s ease;
}
.home-page .dash-item:hover { background: rgba(255,255,255,0.08); border-color: rgba(255,255,255,0.1); transform: translateX(4px); }
.home-page .dash-item.active { background: rgba(99,102,241,0.15); border-color: rgba(99,102,241,0.3); }
.home-page .dash-thumb { width: 72px; height: 72px; border-radius: 12px; overflow: hidden; position: relative; flex-shrink: 0; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
.home-page .dash-thumb img { width: 100%; height: 100%; object-fit: cover; }
.home-page .dash-icon { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; background: rgba(0,0,0,0.4); opacity: 0; transition: opacity 0.2s; }
.home-page .dash-item:hover .dash-icon, .home-page .dash-item.active .dash-icon { opacity: 1; }
.home-page .dash-icon i { font-size: 1.2rem; color: white; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.5)); }
.home-page .dash-info { flex: 1; min-width: 0; display: flex; flex-direction: column; justify-content: center; }
.home-page .dash-label { font-size: 0.65rem; color: var(--accent-color, #6366f1); text-transform: uppercase; font-weight: 800; letter-spacing: 0.05em; margin-bottom: 0.35rem; }
.home-page .dash-info h4 { margin: 0 0 0.25rem 0; font-size: 1.1rem; font-weight: 700; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; color: #fff; }
.home-page .dash-info p { margin: 0; font-size: 0.9rem; color: rgba(255,255,255,0.6); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-page .dash-action-btn {
  width: 42px; height: 42px; border-radius: 50%; background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.1);
  color: white; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0;
}
.home-page .dash-action-btn:hover { background: rgba(30,30,30,0.8); border-color: rgba(255,255,255,0.2); transform: scale(1.1); }
.home-page .radio-next-list { margin-top: auto; padding-top: 1rem; }
.home-page .list-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: rgba(255,255,255,0.4); margin-bottom: 0.75rem; font-weight: 600; }
.home-page .mini-track { display: flex; gap: 0.5rem; padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); font-size: 0.85rem; }
.home-page .mini-track:last-child { border-bottom: none; }
.home-page .track-title { color: rgba(255,255,255,0.9); font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; flex: 1; }
.home-page .track-artist { color: rgba(255,255,255,0.5); max-width: 40%; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-align: right; }
/* What's New at Ahoy (from Flask home.html) */
/* ── What's New section ── */
.home-page .whats-new-section {
  margin: 1.5rem 0 0;
  padding: 0;
  position: relative;
  clear: both;
}
.home-page .whats-new-container {
  background: rgba(20,20,20,0.92);
  border-radius: 24px;
  border: 1px solid rgba(255,255,255,0.08);
  padding: 2rem;
  max-width: 1800px; margin: 0;
}
.home-page .whats-new-header {
  margin-bottom: 1.5rem; border-bottom: 1px solid rgba(255,255,255,0.08); padding-bottom: 1rem;
  display: flex; justify-content: space-between; align-items: flex-end;
}
.home-page .whats-new-title-group { display: flex; align-items: center; gap: 1.25rem; }
.home-page .whats-new-icon {
  width: 56px; height: 56px; border-radius: 16px; display: flex; align-items: center; justify-content: center;
  font-size: 1.75rem; background: #fbbf24; box-shadow: 0 0 25px rgba(251,191,36,0.4); color: #000;
}
.home-page .whats-new-text h2 {
  font-size: 1.75rem; font-weight: 900; margin: 0; line-height: 0.9;
  text-transform: uppercase; letter-spacing: -0.03em; color: rgba(255,255,255,0.95);
}
.home-page .whats-new-text p {
  margin: 0.35rem 0 0; font-size: 0.85rem; color: rgba(255,255,255,0.6);
  font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
}
.home-page .view-all-link {
  color: rgba(255,255,255,0.7); text-decoration: none; font-size: 0.9rem;
  display: flex; align-items: center; gap: 0.5rem; transition: color 0.2s, gap 0.2s; margin-bottom: 0.25rem;
}
.home-page .view-all-link:hover { color: #fff; gap: 0.75rem; }

/* Loading skeleton */
.home-page .wn-skeleton { display: flex; flex-direction: column; gap: 1rem; }
.home-page .wn-spotlight-skeleton { height: 180px; border-radius: 16px; }
.home-page .wn-chips-skeleton { display: flex; gap: 0.5rem; }
.home-page .wn-chip-skeleton { height: 32px; width: 80px; border-radius: 20px; }

/* Body layout */
.home-page .wn-body { display: flex; flex-direction: column; gap: 1rem; }

/* Spotlight card */
.home-page .wn-spotlight {
  display: flex; align-items: stretch; gap: 0; border-radius: 16px; overflow: hidden;
  border: 1px solid rgba(255,255,255,0.1); text-decoration: none; color: inherit;
  background: rgba(255,255,255,0.04); transition: background 0.2s, border-color 0.2s; min-height: 140px;
}
.home-page .wn-spotlight:hover { background: rgba(255,255,255,0.06); border-color: rgba(255,255,255,0.18); }
.home-page .wn-spotlight-image {
  flex-shrink: 0; width: 220px; background: rgba(255,255,255,0.05);
  display: flex; align-items: center; justify-content: center; overflow: hidden;
}
.home-page .wn-spotlight-image img { width: 100%; height: 100%; object-fit: cover; display: block; }
.home-page .wn-spotlight-placeholder { font-size: 2.5rem; color: rgba(255,255,255,0.2); }
.home-page .wn-spotlight-content { flex: 1; min-width: 0; padding: 1.25rem 1rem 1.25rem 1.5rem; display: flex; flex-direction: column; justify-content: center; gap: 0.5rem; }
.home-page .wn-spotlight-meta { display: flex; align-items: center; gap: 0.75rem; }
.home-page .wn-section-badge {
  display: inline-flex; align-items: center; gap: 0.4rem; padding: 3px 10px;
  border-radius: 20px; font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em;
  background: rgba(251,191,36,0.15); color: #fbbf24; border: 1px solid rgba(251,191,36,0.25);
}
.home-page .wn-spotlight-date { font-size: 0.75rem; color: rgba(255,255,255,0.4); }
.home-page .wn-spotlight-content h3 { font-size: 1.1rem; font-weight: 800; margin: 0; color: #fff; line-height: 1.3; }
.home-page .wn-spotlight-content p {
  font-size: 0.85rem; color: rgba(255,255,255,0.6); margin: 0; line-height: 1.5;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}
.home-page .wn-spotlight-arrow {
  display: flex; align-items: center; padding: 0 1.25rem; color: rgba(255,255,255,0.3);
  transition: color 0.2s, padding 0.2s; flex-shrink: 0;
}
.home-page .wn-spotlight:hover .wn-spotlight-arrow { color: #fff; padding-right: 1rem; padding-left: 1.5rem; }

/* Secondary items */
.home-page .wn-rest { display: flex; flex-direction: column; gap: 0.4rem; }
.home-page .wn-rest-item {
  display: flex; align-items: center; gap: 0.75rem; padding: 0.6rem 0.85rem;
  background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05);
  border-radius: 12px; text-decoration: none; color: inherit; transition: all 0.2s;
}
.home-page .wn-rest-item:hover { background: rgba(255,255,255,0.07); border-color: rgba(255,255,255,0.1); transform: translateX(3px); }
.home-page .wn-rest-thumb {
  flex-shrink: 0; width: 52px; height: 34px; border-radius: 8px; overflow: hidden;
  background: rgba(255,255,255,0.06); display: flex; align-items: center; justify-content: center; color: rgba(255,255,255,0.3);
}
.home-page .wn-rest-thumb img { width: 100%; height: 100%; object-fit: cover; }
.home-page .wn-rest-content { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 0.15rem; }
.home-page .wn-rest-title { font-size: 0.83rem; font-weight: 700; color: #fff; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-page .wn-rest-date { font-size: 0.7rem; color: rgba(255,255,255,0.4); text-transform: uppercase; letter-spacing: 0.04em; }
.home-page .wn-rest-arrow { color: rgba(255,255,255,0.3); flex-shrink: 0; font-size: 0.75rem; transition: color 0.2s; }
.home-page .wn-rest-item:hover .wn-rest-arrow { color: rgba(255,255,255,0.8); }

/* Month chips */
.home-page .wn-month-chips { display: flex; gap: 0.5rem; flex-wrap: wrap; padding-top: 0.25rem; }
.home-page .wn-month-chip {
  display: inline-flex; align-items: center; gap: 0.5rem; padding: 0.4rem 1rem;
  border-radius: 20px; font-size: 0.8rem; font-weight: 600; text-decoration: none; color: rgba(255,255,255,0.7);
  background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); transition: all 0.2s;
}
.home-page .wn-month-chip:hover { background: rgba(255,255,255,0.12); color: #fff; border-color: rgba(255,255,255,0.18); }
.home-page .wn-chip-count {
  display: inline-flex; align-items: center; justify-content: center;
  min-width: 18px; height: 18px; padding: 0 5px; border-radius: 9px;
  background: rgba(255,255,255,0.12); font-size: 0.7rem; font-weight: 700; color: rgba(255,255,255,0.8);
}

/* Empty state */
.home-page .whats-new-empty { text-align: center; padding: 2rem; color: rgba(255,255,255,0.5); }
.home-page .view-archive-link { display: inline-block; margin-top: 1rem; color: rgba(99,102,241,1); text-decoration: none; font-weight: 500; }

@media (max-width: 768px) {
  .home-page { padding: var(--mobile-top-offset, 36px) var(--mobile-gutter, 4px) var(--mobile-bottom-clear, 100px) !important; }
  .home-page .whats-new-section { margin-top: 1rem; }
  .home-page .whats-new-container { padding: 1rem; border-radius: 20px; }
  .home-page .whats-new-title-group { gap: 1rem; }
  .home-page .whats-new-icon { width: 42px; height: 42px; font-size: 1.25rem; border-radius: 12px; }
  .home-page .whats-new-text h2 { font-size: 1.4rem; }
  .home-page .whats-new-text p { font-size: 0.75rem; }
  .home-page .whats-new-header { align-items: flex-end; }
  .home-page .wn-spotlight { flex-direction: column; min-height: unset; }
  .home-page .wn-spotlight-image { width: 100%; height: 140px; }
  .home-page .wn-spotlight-content { padding: 1rem; }
  .home-page .wn-spotlight-arrow { display: none; }
  .home-page .wn-spotlight-content h3 { font-size: 1rem; }
}
</style>
