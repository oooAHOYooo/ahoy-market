<template>
  <div class="artists-page">
    <ContentHeader
      kicker="Ahoy Indie Media"
      title="Artists"
      :subtitle="artists.length ? `${artists.length} artist${artists.length === 1 ? '' : 's'} — musicians, hosts, filmmakers, and more.` : 'Discover indie musicians, show hosts, athletes, filmmakers, and more.'"
    />
    <section class="page-mobile-hero" aria-label="Artists">
      <div class="page-mobile-hero-copy">
        <span class="page-mobile-eyebrow">Community</span>
        <h1>Artists</h1>
        <p>{{ artists.length ? `${artists.length} artist${artists.length === 1 ? '' : 's'} — musicians, hosts, filmmakers & more` : 'Indie musicians, hosts, and filmmakers.' }}</p>
      </div>
    </section>

    <SubMenuFilter
      v-model="selectedType"
      :filters="typeFilters"
      all-value="all"
      filter-all-label="All Artists"
      filter-label="Filter by Type"
      :show-search="true"
      search-placeholder="Search artists, genres, or descriptions…"
      :search-query="searchQuery"
      @update:searchQuery="searchQuery = $event"
      :sort-options="sortOptions"
      sort-label="Sort artists"
      :sort-by="sortBy"
      @update:sortBy="sortBy = $event"
    />

    <nav class="artist-smart-scroller" aria-label="Jump to artists">
      <button type="button" aria-label="Scroll to top" @click="scrollToTop">↑</button>
      <div class="artist-smart-letters">
        <button v-for="letter in availableLetters" :key="letter" type="button" :aria-label="`Jump to artists starting with ${letter}`" @click="jumpToLetter(letter)">{{ letter }}</button>
      </div>
      <button type="button" aria-label="Scroll to bottom" @click="scrollToBottom">↓</button>
    </nav>

    <div class="artists-grid">
      <template v-if="filteredArtists.length">
        <router-link
          v-for="(artist, idx) in filteredArtists"
          :key="artist.id || artist.slug"
          :to="`/artists/${artist.slug || artist.id}`"
          class="artist-card"
          :data-artist-letter="(artist.name || '').charAt(0).toUpperCase()"
          style="text-decoration:none;color:inherit"
        >
          <div class="artist-cover">
            <img
              :src="artist.image || '/static/img/default-avatar.png'"
              :alt="artist.name"
              class="artist-image image-placeholder"
              :loading="idx < 8 ? 'eager' : 'lazy'"
            />
            <div class="artist-cover-gradient"></div>
            <div v-if="artist.type" class="artist-type-badge ahoy-subheader">{{ (artist.type || '').toUpperCase() }}</div>
            <div class="artist-cover-text">
              <h4>{{ artist.name }}</h4>
            </div>
          </div>
        </router-link>
      </template>
      <template v-else-if="!loading">
        <div class="empty-section">
          <div class="empty-content">
            <i class="fas fa-users"></i>
            <h3>No artists found</h3>
            <p>Try adjusting your search or filters</p>
            <button type="button" class="btn btn-primary" @click="clearFilters">Clear Filters</button>
          </div>
        </div>
      </template>
      <template v-else>
        <div v-for="i in 6" :key="i" class="artist-card">
          <div class="artist-cover skeleton"></div>
        </div>
      </template>
    </div>

    <!-- Loading -->
    <section v-if="loading" class="loading-section">
      <div class="spinner"></div>
      <p>Loading artists...</p>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiFetchCached } from '../composables/useApi'
import ContentHeader from '../components/ContentHeader.vue'
import SubMenuFilter from '../components/SubMenuFilter.vue'

const artists = ref([])
const loading = ref(true)
const searchQuery = ref('')
const selectedType = ref('all')
const sortBy = ref('newest')
const availableLetters = computed(() => [...new Set(
  filteredArtists.value.map((artist) => (artist.name || '').trim().charAt(0).toUpperCase()).filter(Boolean)
)].sort())

function scrollToTop() { window.scrollTo({ top: 0, behavior: 'smooth' }) }
function scrollToBottom() { window.scrollTo({ top: document.documentElement.scrollHeight, behavior: 'smooth' }) }
function jumpToLetter(letter) {
  const target = document.querySelector(`[data-artist-letter="${letter}"]`)
  if (target) target.scrollIntoView({ behavior: 'smooth', block: 'center' })
}

const typeFilters = [
  { value: 'musician', label: 'Musicians' },
  { value: 'host', label: 'Hosts' },
  { value: 'filmmaker', label: 'Filmmakers' },
  { value: 'athlete', label: 'Athletes' },
  { value: 'poet', label: 'Poets' },
]

const sortOptions = [
  { value: 'newest', label: 'Newest First' },
  { value: 'az', label: 'A–Z' },
  { value: 'random', label: 'Random' },
]

const filteredArtists = computed(() => {
  let list = [...artists.value]
  const q = (searchQuery.value || '').toLowerCase()
  if (q) {
    list = list.filter(
      (a) =>
        (a.name || '').toLowerCase().includes(q) ||
        (a.description || '').toLowerCase().includes(q) ||
        (Array.isArray(a.genres) && a.genres.some((g) => String(g).toLowerCase().includes(q)))
    )
  }
  if (selectedType.value !== 'all') {
    list = list.filter((a) => (a.type || '').toLowerCase() === selectedType.value)
  }
  switch (sortBy.value) {
    case 'newest':
      list = list.slice().reverse()
      break
    case 'az':
      list = list.slice().sort((a, b) => (a.name || '').localeCompare(b.name || ''))
      break
    case 'random':
      list = list.slice().sort(() => Math.random() - 0.5)
      break
  }
  return list
})

function clearFilters() {
  searchQuery.value = ''
  selectedType.value = 'all'
  sortBy.value = 'newest'
}


onMounted(async () => {
  loading.value = true
  const data = await apiFetchCached('/api/artists').catch(() => ({ artists: [] }))
  artists.value = data.artists || []
  loading.value = false
})
</script>

<style scoped>
.artists-page { padding: 0; }
.page-mobile-hero { display: none; }

.artist-smart-scroller {
  position: fixed; left: max(8px, calc(var(--sidebar-width, 0px) + 8px)); top: 50%; z-index: 20;
  display: flex; flex-direction: column; align-items: center; gap: 3px; padding: 6px 4px;
  border: 1px solid rgba(255,255,255,.12); border-radius: 14px; background: rgba(16,12,18,.78);
  backdrop-filter: blur(14px); transform: translateY(-50%);
}
.artist-smart-letters { display: flex; flex-direction: column; max-height: 55vh; overflow: auto; }
.artist-smart-scroller button { width: 26px; height: 23px; padding: 0; border: 0; border-radius: 6px; color: rgba(255,255,255,.65); background: transparent; font: inherit; font-size: 11px; cursor: pointer; }
.artist-smart-scroller button:hover { color: var(--primary-color); background: rgba(255,255,255,.09); }

@media (max-width: 768px) {
  .artist-smart-scroller {
    position: sticky; left: auto; top: 8px; z-index: 10; width: fit-content; max-width: calc(100% - 24px);
    margin: 0 auto 12px; padding: 4px 6px; flex-direction: row; transform: none;
  }
  .artist-smart-letters { flex-direction: row; max-width: calc(100vw - 88px); max-height: none; overflow-x: auto; }
  .artist-smart-scroller button { width: 27px; height: 27px; flex: 0 0 27px; }
  :deep(.content-header) { display: none !important; }
  .page-mobile-hero { display: block; }
  .artist-card:active {
    transform: scale(0.985);
    transition: transform 0.1s cubic-bezier(0.4, 0, 0.2, 1);
  }

  .artists-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 10px;
    padding: 0 10px;
  }

  .artists-grid .artist-card {
    display: block;
    min-height: 0;
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.10);
    border-radius: 18px;
    box-shadow: none;
  }

  .artists-grid .artist-cover {
    width: 100%;
    height: auto;
    aspect-ratio: 4 / 5;
    border-radius: inherit;
    background: rgba(255, 255, 255, 0.035);
  }

  .artist-image {
    opacity: 0;
    transition: opacity 0.3s ease-out;
  }

  .artists-grid .artist-cover .artist-image {
    display: block;
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .artists-grid .artist-cover-gradient {
    height: 68%;
    background: linear-gradient(to top, rgba(0, 0, 0, 0.78) 0%, rgba(0, 0, 0, 0.36) 46%, transparent 100%);
  }

  .artists-grid .artist-cover-text {
    padding: 1rem 0.9rem 0.95rem;
  }

  .artists-grid .artist-cover-text h4 {
    font-size: clamp(0.92rem, 4vw, 1.08rem);
    line-height: 1.08;
    letter-spacing: -0.01em;
    text-shadow: 0 1px 8px rgba(0, 0, 0, 0.72);
  }

  .artists-grid .artist-cover .artist-type-badge {
    top: 0.7rem;
    right: 0.7rem;
    max-width: calc(100% - 1.4rem);
    padding: 0.38rem 0.62rem;
    overflow: hidden;
    border-radius: 7px;
    background: rgba(18, 19, 22, 0.68);
    font-size: 0.62rem;
    line-height: 1;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .artist-image[src],
  .artist-image.image-placeholder {
    opacity: 1;
  }

  .artists-page {
    padding-left: 0;
    padding-right: 0;
  }
}

/* The app can be rendered in its mobile shell at a desktop-sized viewport
   (for example in the desktop wrapper). Keep the card treatment consistent
   with that shell instead of letting the legacy 16:9 rule win. */
:global(body.force-mobile-shell) .artists-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  padding: 0 10px;
}

:global(body.force-mobile-shell) .artists-grid .artist-card {
  display: block;
  aspect-ratio: auto;
  min-height: 0;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.10);
  border-radius: 18px;
  box-shadow: none;
}

:global(body.force-mobile-shell) .artists-grid .artist-cover {
  width: 100%;
  height: auto;
  aspect-ratio: 4 / 5;
  border-radius: inherit;
}

/* The desktop wrapper reports a 975px CSS viewport while showing the mobile
   navigation, so cover this responsive range as well. */
@media (max-width: 1024px) {
  .artists-grid .artist-card {
    display: block;
    aspect-ratio: auto;
    min-height: 0;
  }

  .artists-grid .artist-cover {
    height: auto;
    aspect-ratio: 4 / 5;
  }
}
</style>
