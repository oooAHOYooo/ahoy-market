<template>
  <div class="my-saves-container saved-page" :class="{ 'saved-page--recent': isRecentPage }">
    <ContentHeader
      :kicker="isRecentPage ? 'Your History' : 'Your Library'"
      :title="isRecentPage ? 'Recently Played' : (savedItems.length >= 3 ? 'My Collection' : 'Saved')"
      subtitle="Bookmarks and recently played history."
    />
    <section class="page-mobile-hero" aria-label="Saved">
      <div class="page-mobile-hero-copy">
        <span class="page-mobile-eyebrow">{{ isRecentPage ? 'Your History' : 'Your Library' }}</span>
        <h1>{{ isRecentPage ? 'Recently Played' : (savedItems.length >= 3 ? 'My Collection' : 'Saved') }}</h1>
        <p>{{ isRecentPage ? `${recentlyPlayed.length} recently played item${recentlyPlayed.length === 1 ? '' : 's'}` : `${savedItems.length} saved item${savedItems.length === 1 ? '' : 's'}` }}</p>
      </div>
    </section>

    <!-- Tabs: Bookmarks (→ /my-saves) | Recently Played (→ /recently-played) -->
    <div class="saves-tabs-glass">
      <router-link
        :to="{ path: '/my-saves' }"
        class="saves-tab-btn"
        :class="{ active: !isRecentPage }"
      >
        <i class="fas fa-bookmark"></i>
        <span>Bookmarks</span>
        <span class="saves-tab-count">{{ savedItems.length }}</span>
      </router-link>
      <router-link
        :to="{ path: '/recently-played' }"
        class="saves-tab-btn"
        :class="{ active: isRecentPage }"
      >
        <i class="fas fa-history"></i>
        <span>Recently Played</span>
        <span class="saves-tab-count">{{ recentlyPlayed.length }}</span>
      </router-link>
    </div>

    <!-- Guest banner: shown below tabs so content is visible first -->
    <div v-if="!auth.isLoggedIn.value" class="saves-guest-banner">
      <p>Bookmarks and recently played are stored on this device. <router-link to="/login?signup=1">Create an account</router-link> to sync across devices.</p>
    </div>

    <!-- Bookmarks tab (visible on /my-saves) -->
    <div v-show="!isRecentPage" class="saves-content-glass">
      <div v-if="savedItems.length" class="saves-bookmarks-tab">
        <div v-for="type in organizedTypes" :key="type" class="saves-section">
          <div class="saves-section-header-row">
            <h2 class="saves-section-header">{{ typeSectionLabel(type) }}</h2>
            <button
              v-if="(type === 'track' || type === 'episode') && itemsByType(type).length > 1"
              type="button"
              class="saves-play-all-btn"
              @click="playerStore.setQueue(itemsByType(type), 0)"
            >
              <i class="fas fa-play"></i> Play All
            </button>
          </div>
          <div class="saves-grid">
            <div
              v-for="item in itemsByType(type)"
              :key="itemKey(item)"
              class="saves-card"
              @click="playContent(item)"
            >
              <div class="saves-card-art">
                <img
                  :src="item.cover_art || item.thumbnail || item.artwork || '/static/img/default-cover.jpg'"
                  :alt="item.title || item.name"
                  loading="lazy"
                />
                <div class="saves-card-overlay">
                  <button type="button" class="saves-play-btn" @click.stop="playContent(item)">
                    <i class="fas fa-play"></i>
                  </button>
                </div>
                <button
                  type="button"
                  class="saves-remove-btn"
                  title="Remove from saves"
                  @click.stop="unsaveContent(item)"
                >
                  <i class="fas fa-bookmark"></i>
                </button>
                <div class="saves-type-badge">
                  <i :class="typeIcon(item.type)"></i>
                </div>
              </div>
              <div class="saves-card-info">
                <h3>{{ item.title || item.name || '—' }}</h3>
                <p>{{ item.artist || item.host || '' }}</p>
                <span v-if="item.added_at" class="saves-date">{{ formatDate(item.added_at) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="saves-empty-glass">
        <div class="saves-empty-icon">
          <i class="fas fa-bookmark"></i>
        </div>
        <h3>No saves yet</h3>
        <p>Save tracks, podcasts, shows, and artists to access them later.</p>
        <router-link to="/videos" class="saves-cta-btn">Discover Videos</router-link>
      </div>
    </div>

    <!-- Recently Played (visible on /recently-played) -->
    <div v-show="isRecentPage" class="saves-content-glass saves-content--recent">
      <div v-if="recentlyPlayed.length" class="saves-recent-play-all-row">
        <button type="button" class="saves-play-all-btn" @click="playerStore.setQueue(recentlyPlayed.filter(i => i.type !== 'show' && i.type !== 'live_tv'), 0)">
          <i class="fas fa-play"></i> Play All
        </button>
      </div>
      <div v-if="recentlyPlayed.length" class="saves-recent-list">
        <div
          v-for="item in recentlyPlayed"
          :key="recentKey(item)"
          class="saves-recent-item"
          @click="playContent(item)"
        >
          <div class="saves-recent-art">
            <img
              :src="item.artwork || item.cover_art || item.thumbnail || '/static/img/default-cover.jpg'"
              :alt="item.title || item.name"
              loading="lazy"
            />
            <div class="saves-recent-play">
              <i class="fas fa-play"></i>
            </div>
          </div>
          <div class="saves-recent-info">
            <h3>{{ item.title || item.name || '—' }}</h3>
            <p>{{ item.artist || item.host || '' }}</p>
            <span class="saves-recent-meta">
              <span class="saves-recent-type">{{ recentTypeLabel(item.type) }}</span>
              <span class="saves-recent-time">{{ formatRelativeTime(item.played_at) }}</span>
            </span>
          </div>
          <div class="saves-recent-actions">
            <button
              type="button"
              class="saves-action-btn"
              :class="{ bookmarked: bookmarkHelper.isBookmarked(item) }"
              :title="bookmarkHelper.isBookmarked(item) ? 'Remove bookmark' : 'Add bookmark'"
              @click.stop="toggleBookmark(item)"
            >
              <i class="fas fa-bookmark"></i>
            </button>
          </div>
        </div>
      </div>
      <div v-else class="saves-empty-glass">
        <div class="saves-empty-icon">
          <i class="fas fa-history"></i>
        </div>
        <h3>No recent plays</h3>
        <p>Content you listen to will appear here so you can easily find it again.</p>
        <router-link to="/music" class="saves-cta-btn">Browse Music</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useBookmarks } from '../composables/useBookmarks'
import ContentHeader from '../components/ContentHeader.vue'
import { usePlayerStore } from '../stores/player'
import { useAuth } from '../composables/useAuth'

const RECENT_STORAGE_KEY = 'ahoy.recentlyPlayed.v1'
const MAX_RECENT_ITEMS = 50

const router = useRouter()
const route = useRoute()
const bookmarkHelper = useBookmarks()
const playerStore = usePlayerStore()
const auth = useAuth()

const recentlyPlayed = ref([])

const isRecentPage = computed(() => route.path === '/recently-played')

const savedItems = computed(() => Object.values(bookmarkHelper.bookmarks.value))

const heroTitle = computed(() => {
  const n = savedItems.value.length
  if (n >= 3) return 'My Collection'
  return auth.user.value?.display_name || auth.user.value?.email?.split('@')[0] || 'Saved'
})

const organizedTypes = computed(() => {
  const types = new Set(savedItems.value.map((i) => i.type || 'track').filter(Boolean))
  const order = ['podcast', 'episode', 'track', 'show', 'artist']
  return order.filter(t => types.has(t))
})

function typeIcon(type) {
  const icons = {
    podcast: 'fas fa-podcast',
    episode: 'fas fa-podcast',
    track: 'fas fa-music',
    show: 'fas fa-film',
    artist: 'fas fa-user',
  }
  return icons[type] || 'fas fa-music'
}

function typeSectionLabel(type) {
  const labels = {
    podcast: 'Listen Later — Podcasts',
    episode: 'Listen Later — Episodes',
    track: 'Tracks',
    show: 'Shows',
    artist: 'Artists',
  }
  return labels[type] || type.charAt(0).toUpperCase() + type.slice(1)
}

function itemsByType(type) {
  return savedItems.value.filter((i) => (i.type || 'track') === type)
}

function itemKey(item) {
  return item.id ?? item.slug ?? `${item.type}:${item.title}`
}

function recentKey(item) {
  return item.key ?? `${item.type || 'track'}:${item.id}:${item.played_at || 0}`
}

function formatDate(dateString) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString()
}

function recentTypeLabel(type) {
  const t = type || 'track'
  if (t === 'live_tv') return 'AHOY TV'
  if (t === 'show') return 'Video'
  if (t === 'podcast' || t === 'episode') return 'Podcast'
  return 'Music'
}

function formatRelativeTime(dateString) {
  if (!dateString) return ''
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now - date
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

function loadRecentlyPlayed() {
  try {
    const raw = localStorage.getItem(RECENT_STORAGE_KEY)
    recentlyPlayed.value = raw ? JSON.parse(raw) : []
  } catch {
    recentlyPlayed.value = []
  }
}

function playContent(item) {
  const type = item.type || 'track'
  if (type === 'show') {
    router.push({ path: '/videos', query: { play: item.id } })
    return
  }
  if (type === 'live_tv') {
    router.push('/live-tv')
    return
  }
  if (playerStore.currentTrack?.id === item.id && playerStore.isPlaying) {
    playerStore.pause()
  } else {
    playerStore.play(item)
  }
}

function unsaveContent(item) {
  bookmarkHelper.remove(item)
  window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Removed from bookmarks', type: 'success' } }))
}

function toggleBookmark(item) {
  bookmarkHelper.toggle(item)
  loadRecentlyPlayed()
}

onMounted(() => {
  loadRecentlyPlayed()
  window.addEventListener('recentlyPlayed:updated', loadRecentlyPlayed)
})
onUnmounted(() => {
  window.removeEventListener('recentlyPlayed:updated', loadRecentlyPlayed)
})
</script>

<style scoped>
.page-mobile-hero { display: none; }
@media (max-width: 768px) {
  :deep(.content-header) { display: none !important; }
  .page-mobile-hero { display: block; }
}

.saved-page {
  max-width: 100%;
  margin: 0;
  padding: 0 1.25rem 3rem;
}
.saved-page--recent .saves-content--recent {
  min-height: 200px;
}
@media (max-width: 768px) {
  .saved-page {
    padding: 0 0 var(--mobile-bottom-clear, 100px) !important;
  }
}
.saves-tabs-glass :deep(a.saves-tab-btn) {
  text-decoration: none;
  color: inherit;
}
.saves-hero--recent .saves-hero-content--recent {
  gap: var(--spacing-lg);
}
.saves-avatar--history {
  background: linear-gradient(135deg, rgba(123, 237, 159, 0.3) 0%, rgba(107, 203, 255, 0.25) 100%);
  color: rgba(255, 255, 255, 0.9);
}
@media (max-width: 768px) {
  .saves-hero--recent .saves-profile-content {
    padding: 10px 8px;
  }
}
.saves-guest-banner {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 12px 16px;
  margin: 15px;
  backdrop-filter: blur(8px);
}
.saves-guest-banner p {
  margin: 0;
  font-size: 14px;
  color: var(--text-primary);
}
.saves-guest-banner a {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  text-decoration: underline;
  text-decoration-color: rgba(255, 255, 255, 0.3);
}
.saves-guest-banner a:hover {
  text-decoration-color: rgba(255, 255, 255, 0.7);
}
.saves-recent-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 4px;
  font-size: 12px;
  color: var(--text-muted, rgba(255, 255, 255, 0.6));
}
.saves-recent-type {
  text-transform: capitalize;
}
.saves-recent-type::after {
  content: '·';
  margin-left: 0.5rem;
  margin-right: 0.25rem;
}

.saves-section {
  margin-bottom: 2.5rem;
}

.saves-section-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
  padding: 0 0.5rem;
}

.saves-section-header {
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--text-primary, #fff);
  margin: 0;
  text-transform: capitalize;
  letter-spacing: -0.5px;
}

.saves-play-all-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 14px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: rgba(255, 255, 255, 0.07);
  color: rgba(255, 255, 255, 0.75);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  backdrop-filter: blur(6px);
  transition: background 0.2s, border-color 0.2s, color 0.2s;
}

.saves-play-all-btn:hover {
  background: rgba(255, 255, 255, 0.13);
  border-color: rgba(255, 255, 255, 0.28);
  color: #fff;
}

.saves-recent-play-all-row {
  padding: 8px 16px 0;
  display: flex;
  justify-content: flex-end;
}
</style>
