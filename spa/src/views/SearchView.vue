<template>
  <div class="search-page">
    <div class="search-topbar">
      <div class="search-topbar-inner">
        <div class="search-input-wrap">
          <input
            ref="searchInput"
            v-model="query"
            type="search"
            placeholder="Search music, artists, shows, podcasts..."
            class="search-input"
            autofocus
            autocomplete="off"
            @focus="catalogStore.ensureLoaded()"
            @keydown.enter.prevent="openFirstResult"
          />
          <button v-if="query" type="button" class="search-clear" aria-label="Clear" @click="clearSearch">
            <i class="fas fa-times"></i>
          </button>
        </div>
        <p v-if="showHint" class="search-help desktop-only">Search music, artists, shows, podcasts, and more.</p>
      </div>
    </div>

    <div class="search-layout">

      <!-- Left sidebar: recent searches + browse links -->
      <aside class="search-sidebar">
        <div class="search-logo-row mobile-only">
          <img src="/static/img/u_ahoy23.png" alt="Ahoy" class="search-logo" />
        </div>

        <section v-if="recentSearches.length" class="search-section search-section--recent">
          <h2 class="search-section-title">Recent</h2>
          <div class="search-recent-chips">
            <div v-for="s in recentSearches" :key="s" class="search-recent-chip-wrap">
              <button type="button" class="search-recent-chip" @click="query = s">
                <i class="fas fa-history" aria-hidden="true"></i>
                <span>{{ s }}</span>
              </button>
              <button type="button" class="search-recent-remove" @click.stop="removeRecentSearch(s)" aria-label="Remove recent search">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
        </section>

        <nav class="search-sidebar-nav">
          <h2 class="search-section-title desktop-only">Browse</h2>
          <router-link to="/music"    class="search-nav-link"><i class="fas fa-music"></i><span>Music</span></router-link>
          <router-link to="/artists"  class="search-nav-link"><i class="fas fa-user"></i><span>Artists</span></router-link>
          <router-link to="/videos"   class="search-nav-link"><i class="fas fa-film"></i><span>Videos</span></router-link>
          <router-link to="/podcasts" class="search-nav-link"><i class="fas fa-podcast"></i><span>Podcasts</span></router-link>
          <router-link to="/events"   class="search-nav-link"><i class="fas fa-calendar-alt"></i><span>Events</span></router-link>
          <router-link to="/radio"    class="search-nav-link"><i class="fas fa-broadcast-tower"></i><span>Radio</span></router-link>
        </nav>
      </aside>

      <!-- Right panel: results -->
      <div class="search-main">
        <div v-if="catalogStore.loading" class="search-loading">
          <i class="fas fa-spinner fa-spin"></i>
          <span>Loading catalog...</span>
        </div>

        <div v-else class="search-results">

          <!-- Browse mode (no query) -->
          <template v-if="!query.trim()">
            <SearchResultSection
              v-for="section in browseSections"
              :key="section.key"
              :title="section.title"
              :items="section.items"
              query=""
              @play="handlePlay"
            />
          </template>

          <!-- Search results -->
          <template v-else>
            <!-- Category filter tabs -->
            <div v-if="hasAny && filterTabs.length > 1" class="search-filter-tabs">
              <button
                class="search-filter-tab"
                :class="{ active: activeFilter === 'all' }"
                @click="activeFilter = 'all'"
              >All</button>
              <button
                v-for="tab in filterTabs"
                :key="tab.key"
                class="search-filter-tab"
                :class="{ active: activeFilter === tab.key }"
                @click="activeFilter = tab.key"
              >{{ tab.label }}</button>
            </div>

            <SearchResultSection
              v-for="section in visibleSections"
              :key="section.key"
              :title="section.title"
              :items="section.items"
              :query="query"
              @navigate="handleNavigate"
              @play="handlePlay"
            />

            <div v-if="!hasAny" class="search-no-results">
              <p>No results for "{{ query }}"</p>
              <div class="search-suggestions">
                <span>Browse:</span>
                <router-link to="/music" class="search-suggestion-chip"><i class="fas fa-music"></i> Music</router-link>
                <router-link to="/artists" class="search-suggestion-chip"><i class="fas fa-users"></i> Artists</router-link>
                <router-link to="/podcasts" class="search-suggestion-chip"><i class="fas fa-podcast"></i> Podcasts</router-link>
                <router-link to="/events" class="search-suggestion-chip"><i class="fas fa-calendar"></i> Events</router-link>
              </div>
            </div>
          </template>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { trackEvent } from '../composables/useAnalytics'
import { usePlayerStore } from '../stores/player'
import { useCatalogStore } from '../stores/catalog'
import { useRecentSearches } from '../composables/useRecentSearches'
import { getSearchResultUrl, useSearch } from '../composables/useSearch'
import SearchResultSection from '../components/SearchResultSection.vue'

const route = useRoute()
const router = useRouter()
const catalogStore = useCatalogStore()
const playerStore = usePlayerStore()
const { searches: recentSearches, add: addRecentSearch, remove: removeRecentSearch } = useRecentSearches()
const { runSearch } = useSearch()

const query = ref(typeof route.query.q === 'string' ? route.query.q : '')
const searchInput = ref(null)
const showHint = ref(!query.value.trim())
const browseSections = ref([])
const activeFilter = ref('all')

// ── Browse mode ──────────────────────────────────────────────────────────────

function shuffleCopy(arr) {
  const copy = [...(arr || [])]
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[copy[i], copy[j]] = [copy[j], copy[i]]
  }
  return copy
}

function buildBrowseSections(cat) {
  const raw = [
    { key: 'tracks',   title: 'Music',    items: shuffleCopy(cat.tracks).slice(0, 6) },
    { key: 'artists',  title: 'Artists',  items: shuffleCopy(cat.artists).slice(0, 8) },
    { key: 'shows',    title: 'Videos',   items: shuffleCopy(cat.shows).slice(0, 6) },
    { key: 'podcasts', title: 'Podcasts', items: shuffleCopy(cat.podcasts.filter(p => p.type === 'podcast')).slice(0, 4) }
  ]
  return shuffleCopy(raw).filter(s => s.items.length)
}

watch(() => catalogStore.ready, (ready) => {
  if (ready && !browseSections.value.length) {
    browseSections.value = buildBrowseSections(catalogStore.catalog)
  }
}, { immediate: true })

// ── Search results ────────────────────────────────────────────────────────────

const results = computed(() => {
  const { tracks, artists, shows, podcasts, events } = catalogStore.catalog
  return runSearch(tracks, artists, shows, podcasts, events, query.value)
})

const resultSections = computed(() => [
  { key: 'tracks',   title: 'Tracks',   items: results.value.tracks },
  { key: 'artists',  title: 'Artists',  items: results.value.artists },
  { key: 'shows',    title: 'Videos',   items: results.value.shows },
  { key: 'podcasts', title: 'Podcasts', items: results.value.podcasts.filter(p => p.type === 'podcast') },
  { key: 'episodes', title: 'Episodes', items: results.value.podcasts.filter(p => p.type === 'podcastEpisode') },
  { key: 'events',   title: 'Events',   items: results.value.events }
].filter(s => s.items.length))

const hasAny = computed(() => resultSections.value.length > 0)

// ── Filter tabs ───────────────────────────────────────────────────────────────

const FILTER_GROUPS = {
  tracks:   ['tracks'],
  artists:  ['artists'],
  videos:   ['shows'],
  podcasts: ['podcasts', 'episodes'],
  events:   ['events']
}

const TAB_LABELS = {
  tracks: 'Tracks', artists: 'Artists', videos: 'Videos', podcasts: 'Podcasts', events: 'Events'
}

const filterTabs = computed(() =>
  Object.entries(FILTER_GROUPS)
    .filter(([, keys]) => keys.some(k => resultSections.value.find(s => s.key === k)))
    .map(([key]) => ({ key, label: TAB_LABELS[key] }))
)

const visibleSections = computed(() => {
  if (activeFilter.value === 'all') return resultSections.value
  const keys = FILTER_GROUPS[activeFilter.value] || []
  return resultSections.value.filter(s => keys.includes(s.key))
})

// ── Interactions ──────────────────────────────────────────────────────────────

function handleNavigate() {
  addRecentSearch(query.value)
  searchInput.value?.blur()
  query.value = ''
}

function handlePlay(track) {
  if (playerStore.currentTrack?.id === track.id) {
    playerStore.togglePlay()
  } else {
    playerStore.play(track)
  }
  searchInput.value?.blur()
}

function clearSearch() {
  query.value = ''
  searchInput.value?.blur()
}

const firstResult = computed(() =>
  results.value.tracks[0] ||
  results.value.artists[0] ||
  results.value.shows[0] ||
  results.value.podcasts[0] ||
  results.value.events[0]
)

function openFirstResult() {
  if (!firstResult.value) return
  addRecentSearch(query.value)
  router.push(getSearchResultUrl(firstResult.value))
  query.value = ''
}

// ── URL sync + analytics ──────────────────────────────────────────────────────

watch(() => route.query.q, (value) => {
  query.value = typeof value === 'string' ? value : ''
  if (query.value.trim()) {
    showHint.value = false
    catalogStore.ensureLoaded()
  }
})

let analyticsTimer = null
watch(query, (value) => {
  const q = value.trim()
  if (q) {
    showHint.value = false
    activeFilter.value = 'all'
    catalogStore.ensureLoaded()
  }
  if (!q) return
  clearTimeout(analyticsTimer)
  analyticsTimer = setTimeout(() => {
    const r = results.value
    trackEvent('search_performed', {
      query: q,
      results_tracks: r.tracks.length,
      results_artists: r.artists.length,
      results_shows: r.shows.length,
      results_podcasts: r.podcasts.length,
      results_total: r.tracks.length + r.artists.length + r.shows.length + r.podcasts.length
    })
  }, 600)
})

onMounted(() => {
  catalogStore.ensureLoaded()
})
</script>

<style scoped>
.search-page {
  min-height: 100%;
  background: rgba(0,0,0,0.18);
}

/* ── Topbar ── */
.search-topbar {
  position: sticky;
  top: 0;
  z-index: 5;
  padding: 12px 14px 6px;
  background: linear-gradient(180deg, rgba(4, 5, 7, 0.98), rgba(5, 6, 9, 0.92));
  backdrop-filter: blur(22px);
  -webkit-backdrop-filter: blur(22px);
  border-bottom: 1px solid rgba(255,255,255,0.05);
}

.search-topbar-inner {
  display: flex;
  align-items: center;
  gap: 14px;
  width: 100%;
}

.search-topbar .search-input-wrap {
  flex: 1;
  margin-top: 0;
}

.search-topbar .search-help {
  margin: 0;
  max-width: 260px;
  flex-shrink: 0;
}

/* ── Split layout ── */
.search-layout {
  display: flex;
  align-items: flex-start;
  min-height: 100%;
}

/* ── Sidebar ── */
.search-sidebar {
  width: 255px;
  flex-shrink: 0;
  padding: 16px 10px 16px;
  position: sticky;
  top: 62px;
  max-height: 100vh;
  overflow-y: auto;
  border-right: 1px solid rgba(255,255,255,0.05);
  background: rgba(0,0,0,0.28);
}

.search-logo-row {
  display: flex;
  justify-content: center;
  padding-bottom: 12px;
}
.search-logo {
  height: 28px;
  width: auto;
  opacity: 0.85;
}

/* ── Input ── */
.search-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
  gap: 10px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.09);
  border-radius: 14px;
  padding: 9px 12px;
  padding-right: 42px;
  width: 100%;
  box-sizing: border-box;
  margin-top: 2px;
}
.search-input {
  flex: 1;
  background: none;
  border: none;
  color: var(--text-primary);
  font-size: 15px;
  outline: none !important;
  min-width: 0;
}
.search-input:focus-visible {
  outline: none !important;
}
.search-input-wrap:focus-within {
  border-color: rgba(255,255,255,0.22);
  background: rgba(255,255,255,0.08);
}
.search-input::placeholder {
  color: var(--text-secondary);
}
.search-input::-webkit-search-cancel-button {
  display: none;
}
.search-clear {
  position: absolute;
  right: 10px;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  width: 28px;
  height: 28px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  opacity: 0.62;
}
.search-clear:hover {
  color: #f2eadc;
  background: rgba(255,255,255,0.08);
  opacity: 1;
}

.search-help {
  margin: 8px 0 0;
  color: rgba(206, 194, 173, 0.6);
  font-size: 10px;
  line-height: 1.25;
}

/* ── Main panel ── */
.search-main {
  flex: 1;
  min-width: 0;
  padding-bottom: 100px;
  background: rgba(0,0,0,0.12);
}

.search-loading {
  padding: 48px 24px;
  text-align: center;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.search-results {
  padding: 12px 0 8px;
}

/* ── Filter tabs ── */
.search-filter-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0 14px 10px;
}

.search-filter-tab {
  padding: 5px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.06);
  color: var(--text-secondary);
  font: inherit;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s;
  line-height: 1;
}
.search-filter-tab:hover {
  background: rgba(255,255,255,0.1);
  color: var(--text-primary);
}
.search-filter-tab.active {
  background: rgba(255,255,255,0.14);
  border-color: rgba(255,255,255,0.28);
  color: #fff;
  font-weight: 600;
}

/* ── Sidebar: recent ── */
.search-section--recent {
  margin: 0 0 18px;
  padding-bottom: 14px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.search-section-title {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: rgba(206, 194, 173, 0.4);
  margin: 0 0 8px;
  padding: 0 4px;
}

/* ── Sidebar: browse nav ── */
.search-sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.search-nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 8px;
  color: rgba(206, 194, 173, 0.65);
  text-decoration: none;
  font-size: 13px;
  font-weight: 500;
  transition: background 0.14s, color 0.14s;
}
.search-nav-link:hover {
  background: rgba(255,255,255,0.06);
  color: rgba(242, 234, 220, 0.9);
}
.search-nav-link.router-link-active {
  background: rgba(255,255,255,0.08);
  color: #f2eadc;
}
.search-nav-link i {
  width: 16px;
  text-align: center;
  font-size: 12px;
  opacity: 0.75;
  flex-shrink: 0;
}

.search-recent-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  padding: 0;
}
.search-recent-chip-wrap {
  display: inline-flex;
  align-items: center;
  gap: 3px;
}
.search-recent-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.07);
  color: var(--text-primary);
  cursor: pointer;
  font: inherit;
  font-size: 12px;
  line-height: 1;
  transition: background 0.15s, border-color 0.15s;
}
.search-recent-chip:hover {
  background: rgba(255,255,255,0.12);
  border-color: rgba(255,255,255,0.22);
}
.search-recent-chip i {
  color: rgba(206, 194, 173, 0.7);
  font-size: 11px;
}
.search-recent-remove {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.1);
  color: rgba(206, 194, 173, 0.7);
  cursor: pointer;
  width: 22px;
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0;
  font-size: 10px;
  border-radius: 999px;
}
.search-recent-remove:hover {
  color: var(--text-primary);
  background: rgba(255,255,255,0.1);
}

/* ── No results ── */
.search-no-results {
  padding: 32px 14px;
  text-align: center;
  color: var(--text-secondary);
}
.search-no-results p {
  margin: 0 0 14px;
}
.search-suggestions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.search-suggestions span {
  color: var(--text-secondary);
}
.search-suggestion-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 12px;
  background: rgba(255,255,255,0.07);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 20px;
  color: var(--text-primary);
  text-decoration: none;
  font-size: 13px;
  transition: background 0.15s;
}
.search-suggestion-chip:hover {
  background: rgba(255,255,255,0.13);
}

/* ── Mobile ── */
@media (max-width: 700px) {
  .desktop-only { display: none !important; }

  .search-topbar {
    padding: 10px 12px 8px;
  }
  .search-topbar-inner {
    flex-direction: row;
    align-items: center;
    gap: 10px;
  }
  .search-layout {
    flex-direction: column;
  }

  /* Sidebar becomes a slim horizontal chip bar */
  .search-sidebar {
    width: 100%;
    position: static;
    max-height: none;
    padding: 4px 10px 0;
    border-right: none;
    border-bottom: 1px solid rgba(255,255,255,0.05);
    background: rgba(0,0,0,0.15);
  }

  /* Hide logo on mobile */
  .search-logo-row {
    display: none !important;
  }

  /* Recent searches stay inline */
  .search-section--recent {
    margin: 0 0 4px;
    padding-bottom: 4px;
    border-bottom: none;
  }

  /* Browse nav becomes horizontal scrollable chips */
  .search-sidebar-nav {
    flex-direction: row;
    flex-wrap: nowrap;
    overflow-x: auto;
    gap: 6px;
    padding-bottom: 8px;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
  }
  .search-sidebar-nav::-webkit-scrollbar { display: none; }

  .search-nav-link {
    flex-shrink: 0;
    flex-direction: row;
    padding: 5px 12px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.1);
    background: rgba(255,255,255,0.05);
    font-size: 12px;
    gap: 6px;
  }
  .search-nav-link i {
    font-size: 11px;
  }
  .search-nav-link.router-link-active {
    border-color: rgba(255,255,255,0.22);
    background: rgba(255,255,255,0.1);
  }

  .search-main {
    width: 100%;
    padding-bottom: 100px;
  }
  .search-results {
    padding-top: 4px;
  }
}

@media (max-width: 420px) {
  .search-topbar {
    padding: 8px 10px 7px;
  }
}
</style>
