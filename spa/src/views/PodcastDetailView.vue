<template>
  <div class="podcast-show-page" v-if="show">
    <nav class="ds-crumbs podcast-detail-crumbs" aria-label="Breadcrumb" style="padding:12px 16px 0">
      <span class="ds-crumbs__item">
        <router-link to="/podcasts" class="ds-crumbs__link" style="color:var(--accent-primary,#6ddcff);text-decoration:none">
          <i class="fas fa-chevron-left"></i> Podcasts
        </router-link>
      </span>
    </nav>

    <!-- Hero -->
    <section class="podcast-show-hero">
      <img
        class="podcast-show-hero-art"
        :src="show.artwork || '/static/img/default-cover.jpg'"
        :alt="show.title"
      />
      <div class="podcast-show-hero-meta">
        <div class="podcast-show-hero-kicker">Podcast</div>
        <h1 class="podcast-show-hero-title">{{ show.title }}</h1>
        <p class="podcast-show-hero-desc" v-if="show.description">{{ show.description }}</p>
        <div class="podcast-show-hero-actions">
          <button v-if="latestEpisodeVideoRoute" class="podcast-cta" @click="playLatest">
            <i class="fas fa-headphones"></i>
            Listen audio
          </button>
          <button v-if="latestEpisodeVideoRoute" class="podcast-cta secondary" @click="watchLatestVideo">
            <i class="fas fa-video"></i>
            Watch video
          </button>
          <button v-else class="podcast-cta" @click="playLatest">
            <i class="fas fa-play"></i>
            Play Newest
          </button>
          <button class="podcast-cta secondary" @click="bookmarks.toggle({ ...show, _type: 'podcast' })">
            <i :class="bookmarks.isBookmarked(show) ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
            {{ bookmarks.isBookmarked(show) ? 'Saved' : 'Save' }}
          </button>
        </div>
        <div class="podcast-show-hero-stats">
          <span>{{ episodes.length }} episodes</span>
          <span v-if="clips.length">{{ clips.length }} clips</span>
          <span v-if="comingSoonEpisodes.length">{{ comingSoonEpisodes.length }} coming soon</span>
        </div>
      </div>
    </section>

    <!-- Tabs -->
    <nav class="podcast-tabs">
      <button
        class="podcast-tab"
        :class="{ active: activeTab === 'episodes' }"
        @click="activeTab = 'episodes'"
      >
        Episodes
        <span class="tab-count">{{ episodes.length }}</span>
      </button>
      <button
        v-if="clips.length"
        class="podcast-tab"
        :class="{ active: activeTab === 'clips' }"
        @click="activeTab = 'clips'"
      >
        Clips
        <span class="tab-count">{{ clips.length }}</span>
      </button>
      <button
        class="podcast-tab"
        :class="{ active: activeTab === 'coming_soon' }"
        @click="activeTab = 'coming_soon'"
      >
        Coming Soon
        <span class="tab-count">{{ comingSoonEpisodes.length }}</span>
      </button>
    </nav>

    <!-- Episodes List -->
    <section class="podcasts-section" v-if="activeTab === 'episodes'" style="margin-top:16px">
      <div class="episode-list">
        <article
          v-for="(ep, idx) in episodes"
          :key="ep.id || ep.key || idx"
          class="episode-row"
          :class="{ playing: playerStore.currentTrack?.id === (ep.id || ep.key) }"
          @click="playEpisode(idx)"
        >
          <img class="episode-art" :src="ep.cover_art || ep.artwork || show.artwork || '/static/img/default-cover.jpg'" :alt="ep.title" loading="lazy" />
          <div class="episode-meta">
            <div class="episode-title">{{ ep.title }}</div>
            <div class="episode-subtitle">
              <span class="episode-time" v-if="ep.date">{{ ep.date }}</span>
              <span class="episode-dot" v-if="ep.date && ep.duration_seconds"> · </span>
              <span class="episode-time" v-if="ep.duration_seconds">{{ formatDuration(ep.duration_seconds) }}</span>
              <span v-if="ep.videoRoute" class="episode-video-pill" style="margin-left:6px">Video available</span>
            </div>
            <div class="episode-desc" v-if="ep.description">{{ truncate(ep.description, 120) }}</div>
          </div>
          <div class="episode-actions">
            <router-link
              v-if="ep.videoRoute && isInternalVideoRoute(ep.videoRoute)"
              :to="ep.videoRoute"
              class="episode-open"
              @click.stop
            >
              Watch video
            </router-link>
            <a
              v-else-if="ep.videoRoute"
              :href="ep.videoRoute"
              class="episode-open"
              target="_blank"
              rel="noopener noreferrer"
              @click.stop
            >
              Watch video
            </a>
            <router-link
              v-else-if="ep.episode_number"
              :to="`/podcasts/${show.slug}/${ep.episode_number}`"
              class="episode-open"
              @click.stop
            >
              View
            </router-link>
            <button class="episode-btn" @click.stop="playEpisode(idx)">
              <i :class="playerStore.currentTrack?.id === (ep.id || ep.key) && playerStore.isPlaying ? 'fas fa-pause' : 'fas fa-play'"></i>
            </button>
            <button class="episode-btn" title="Add to playlist" @click.stop="addToPlaylistModal.open({ ...ep, type: 'clip' })">
              <i class="fas fa-list-ul"></i>
            </button>
          </div>
        </article>
      </div>
    </section>

    <!-- Clips List -->
    <section class="podcasts-section" v-if="activeTab === 'clips'" style="margin-top:16px">
      <div class="episode-list">
        <article
          v-for="(ep, idx) in clips"
          :key="ep.id || ep.key || idx"
          class="episode-row"
          :class="{ playing: playerStore.currentTrack?.id === (ep.id || ep.key) }"
          @click="playClip(idx)"
        >
          <img class="episode-art" :src="ep.cover_art || ep.artwork || show.artwork || '/static/img/default-cover.jpg'" :alt="ep.title" loading="lazy" />
          <div class="episode-meta">
            <div class="episode-title">{{ ep.title }}</div>
            <div class="episode-subtitle">
              <span class="episode-time" v-if="ep.date">{{ ep.date }}</span>
              <span class="episode-dot" v-if="ep.date && ep.duration_seconds"> · </span>
              <span class="episode-time" v-if="ep.duration_seconds">{{ formatDuration(ep.duration_seconds) }}</span>
            </div>
            <div class="episode-desc" v-if="ep.description">{{ truncate(ep.description, 120) }}</div>
          </div>
          <div class="episode-actions">
            <button class="episode-btn" @click.stop="playClip(idx)">
              <i :class="playerStore.currentTrack?.id === (ep.id || ep.key) && playerStore.isPlaying ? 'fas fa-pause' : 'fas fa-play'"></i>
            </button>
            <button class="episode-btn" title="Add to playlist" @click.stop="addToPlaylistModal.open({ ...ep, type: 'clip' })">
              <i class="fas fa-list-ul"></i>
            </button>
          </div>
        </article>
      </div>
    </section>

    <!-- Coming Soon List -->
    <section class="podcasts-section" v-if="activeTab === 'coming_soon'" style="margin-top:16px">
      <div class="episode-list">
        <article
          v-for="(ep, idx) in comingSoonEpisodes"
          :key="ep.id || idx"
          class="episode-row coming-soon"
        >
          <img class="episode-art" :src="ep.cover_art || ep.artwork || show.artwork || '/static/img/default-cover.jpg'" :alt="ep.title" loading="lazy" />
          <div class="episode-meta">
            <div class="episode-title">{{ ep.title }}</div>
            <div class="episode-subtitle">
              <span class="episode-time" v-if="ep.date">Expected: {{ ep.date }}</span>
              <span class="coming-soon-badge">Coming Soon</span>
            </div>
            <div class="episode-desc" v-if="ep.description">{{ truncate(ep.description, 120) }}</div>
          </div>
          <div class="episode-actions" v-if="ep.episode_number">
            <router-link
              :to="`/podcasts/${show.slug}/${ep.episode_number}`"
              class="episode-open"
              @click.stop
            >
              View
            </router-link>
          </div>
        </article>
      </div>
      <div v-if="!comingSoonEpisodes.length" class="empty-state" style="text-align:center;padding:40px 20px;color:rgba(255,255,255,0.5)">
        <i class="fas fa-calendar-alt" style="font-size:48px;margin-bottom:16px;display:block"></i>
        <p>No episodes scheduled yet</p>
      </div>
    </section>

    <!-- Empty episodes state -->
    <section class="podcasts-section" v-if="activeTab === 'episodes' && !episodes.length" style="margin-top:16px">
      <div class="empty-state" style="text-align:center;padding:40px 20px;color:rgba(255,255,255,0.5)">
        <i class="fas fa-podcast" style="font-size:48px;margin-bottom:16px;display:block"></i>
        <p>No episodes available yet</p>
      </div>
    </section>
  </div>

  <!-- Loading -->
  <div class="podcast-show-page" v-else>
    <section class="podcast-show-hero">
      <div class="podcast-show-hero-art skeleton" style="aspect-ratio:1;width:100%"></div>
      <div class="podcast-show-hero-meta">
        <div class="skeleton" style="height:14px;width:30%;margin-bottom:8px"></div>
        <div class="skeleton" style="height:24px;width:60%;margin-bottom:8px"></div>
        <div class="skeleton" style="height:14px;width:80%"></div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiFetchCached } from '../composables/useApi'
import { useBookmarks } from '../composables/useBookmarks'
import { usePlayerStore } from '../stores/player'
import { useAddToPlaylist } from '../composables/useAddToPlaylist'
import { useOverlay } from '../composables/useOverlay'
import { setSeoMeta } from '../composables/useSeoMeta'
import { getPodcastVideoRoute } from '../composables/usePodcastVideo'

const route = useRoute()
const router = useRouter()
const playerStore = usePlayerStore()
const bookmarks = useBookmarks()
const addToPlaylistModal = useAddToPlaylist()
const { openNowPlaying } = useOverlay()

const show = ref(null)
const activeTab = ref('episodes')

const episodes = computed(() => {
  if (!show.value) return []
  return (show.value.episodes || [])
    .filter(ep => !ep.is_clip && (ep.audio_url || ep.url)) // full episodes with audio only
    .map(ep => ({
      ...ep,
      id: ep.id || ep.key || `${show.value.slug}-${ep.title}`,
      artist: show.value.title,
      cover_art: ep.cover_art || ep.artwork || show.value.artwork,
      audio_url: ep.audio_url || ep.url || '',
      videoRoute: getPodcastVideoRoute(show.value.slug, ep),
    }))
    .sort((a, b) =>
      String(b.date || '').localeCompare(String(a.date || '')) ||
      Number(b.episode_number || 0) - Number(a.episode_number || 0) ||
      String(b.id || '').localeCompare(String(a.id || ''))
    )
})

const latestEpisodeVideoRoute = computed(() => {
  if (!show.value || !episodes.value.length) return ''
  return getPodcastVideoRoute(show.value.slug, episodes.value[0])
})

const clips = computed(() => {
  if (!show.value) return []
  return (show.value.episodes || [])
    .filter(ep => ep.is_clip && (ep.audio_url || ep.url))
    .map(ep => ({
      ...ep,
      id: ep.id || ep.key || `${show.value.slug}-${ep.title}`,
      artist: show.value.title,
      cover_art: ep.cover_art || ep.artwork || show.value.artwork,
      audio_url: ep.audio_url || ep.url || '',
    }))
    .sort((a, b) =>
      String(b.date || '').localeCompare(String(a.date || '')) ||
      String(b.id || '').localeCompare(String(a.id || ''))
    )
})

const comingSoonEpisodes = computed(() => {
  if (!show.value) return []
  return (show.value.episodes || [])
    .filter(ep => !ep.is_clip && !ep.audio_url && !ep.url) // Only show episodes WITHOUT audio
    .map(ep => ({
      ...ep,
      cover_art: ep.cover_art || ep.artwork || show.value.artwork,
    }))
    .sort((a, b) =>
      String(b.date || '').localeCompare(String(a.date || '')) ||
      String(b.id || '').localeCompare(String(a.id || ''))
    )
})

function formatDuration(seconds) {
  const total = Number(seconds)
  if (!Number.isFinite(total) || total <= 0) return ''
  const m = Math.floor(total / 60)
  const s = Math.floor(total % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function truncate(str, len) {
  if (!str) return ''
  return str.length > len ? str.slice(0, len) + '...' : str
}

function playLatest() {
  const ep = episodes.value[0]
  if (!ep) return
  playerStore.setQueue(episodes.value, 0)
  openNowPlaying()
}

function watchLatestVideo() {
  if (!latestEpisodeVideoRoute.value) return
  openVideoTarget(latestEpisodeVideoRoute.value)
}

function playEpisode(idx) {
  const ep = episodes.value[idx]
  if (!ep) return
  playerStore.setQueue(episodes.value, idx)
  openNowPlaying()
}

function playClip(idx) {
  const ep = clips.value[idx]
  if (!ep) return
  playerStore.setQueue(clips.value, idx)
  openNowPlaying()
}

function isInternalVideoRoute(route) {
  return String(route || '').startsWith('/videos/')
}

function openVideoTarget(target) {
  if (!target) return
  if (isInternalVideoRoute(target)) {
    router.push(target)
    return
  }
  window.open(target, '_blank', 'noopener,noreferrer')
}

onMounted(async () => {
  const slug = route.params.slug
  const data = await apiFetchCached('/api/podcasts').catch(() => ({ shows: [] }))
  const shows = data.shows || []
  show.value = shows.find(s => s.slug === slug) || null
  if (show.value) {
    setSeoMeta({
      title: show.value.title,
      description: show.value.description || `Listen to ${show.value.title} on Ahoy Indie Media.`,
      image: show.value.artwork || '/static/img/ahoy_logo.png',
      type: 'website',
      url: window.location.pathname,
    })
  }

  // Auto-play if 'play' query param is present
  const epId = route.query.play
  if (epId && show.value) {
    const idx = episodes.value.findIndex(ep => (ep.id || ep.title) === epId)
    if (idx !== -1) {
      setTimeout(() => {
        playEpisode(idx)
      }, 500) // Small delay to ensure player is ready and UX is smooth
    }
  }
})
</script>

<style scoped>
.podcast-tabs {
  display: flex;
  gap: 2rem;
  margin: 1.5rem 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 0 1rem;
}

.podcast-tab {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  font-size: 1.1rem;
  font-weight: 600;
  padding: 0.75rem 0;
  cursor: pointer;
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: color 0.2s;
}

.podcast-tab:hover {
  color: #fff;
}

.podcast-tab.active {
  color: #fff;
}

.podcast-tab.active::after {
  content: '';
  position: absolute;
  bottom: -1px;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent-color, #00d4ff);
}

.tab-count {
  font-size: 0.8rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 2px 6px;
  border-radius: 99px;
  min-width: 1.5rem;
  text-align: center;
}

.coming-soon-badge {
  background: rgba(0, 212, 255, 0.1);
  color: var(--accent-color, #00d4ff);
  font-size: 0.75rem;
  font-weight: 700;
  text-transform: uppercase;
  padding: 2px 8px;
  border-radius: 4px;
  border: 1px solid rgba(0, 212, 255, 0.2);
}

.episode-video-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 0.7rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: #081018;
  background: #8ff0ff;
}

.episode-row.coming-soon {
  cursor: default;
  opacity: 0.8;
}

.episode-row.coming-soon:hover {
  background: rgba(255, 255, 255, 0.03);
  transform: none;
}

.podcast-detail-crumbs {
  margin-bottom: 8px;
}

.podcast-show-hero-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
  color: rgba(255, 255, 255, 0.55);
  font-size: 0.82rem;
}

.podcast-show-hero-stats span {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 999px;
  padding: 4px 10px;
}
</style>
