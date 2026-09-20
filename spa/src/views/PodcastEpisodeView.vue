<template>
  <div class="podcast-show-page event-detail-page" v-if="episode">
    <!-- Breadcrumb -->
    <nav class="ds-crumbs event-detail-crumbs" aria-label="Breadcrumb" style="padding:12px 16px 0">
      <span class="ds-crumbs__item">
        <router-link to="/podcasts" class="ds-crumbs__link" style="color:var(--accent-primary,#6ddcff);text-decoration:none">Podcasts</router-link>
        <span class="ds-crumbs__sep" style="margin:0 6px;color:rgba(255,255,255,0.4)">›</span>
      </span>
      <span class="ds-crumbs__item">
        <router-link :to="`/podcasts/${slug}`" class="ds-crumbs__link" style="color:var(--accent-primary,#6ddcff);text-decoration:none">{{ show?.title || slug }}</router-link>
        <span class="ds-crumbs__sep" style="margin:0 6px;color:rgba(255,255,255,0.4)">›</span>
      </span>
      <span class="ds-crumbs__item">
        <span class="ds-crumbs__current" style="color:rgba(255,255,255,0.7)">{{ episode.title }}</span>
      </span>
    </nav>

    <!-- Hero -->
    <section class="podcast-show-hero" style="margin-top:12px">
      <img
        class="podcast-show-hero-art"
        :src="episode.artwork || show?.artwork || '/static/img/default-cover.jpg'"
        :alt="episode.title"
      />
      <div class="podcast-show-hero-meta">
        <div class="podcast-show-hero-kicker">{{ show?.title || 'Podcast' }}</div>
        <h1 class="podcast-show-hero-title">{{ episode.title }}</h1>
        <p class="podcast-show-hero-desc" v-if="episode.description">{{ episode.description }}</p>
        <div class="episode-subtitle" style="margin-bottom:10px">
          <span v-if="episode.date">{{ episode.date }}</span>
          <span class="episode-dot" v-if="episode.date && episode.duration_seconds"> · </span>
          <span v-if="episode.duration_seconds">{{ formatDuration(episode.duration_seconds) }}</span>
        </div>
        <div v-if="!episode.audio_url && !episode.video_url" style="margin-bottom:12px">
          <span class="coming-soon-badge">Coming Soon</span>
        </div>
        <div class="podcast-show-hero-actions" style="margin-top:12px">
          <button
            v-if="episode.audio_url"
            class="podcast-cta"
            @click="playEpisode"
          >
            <i :class="isPlaying ? 'fas fa-pause' : 'fas fa-headphones'"></i>
            {{ isPlaying ? 'Pause audio' : 'Listen audio' }}
          </button>
          <router-link
            v-if="videoRoute && isInternalVideoRoute(videoRoute)"
            class="podcast-cta secondary"
            :to="videoRoute"
          >
            <i class="fas fa-video"></i>
            Watch video
          </router-link>
          <a
            v-else-if="videoRoute"
            class="podcast-cta secondary"
            :href="videoRoute"
            target="_blank"
            rel="noopener noreferrer"
          >
            <i class="fas fa-video"></i>
            Watch video
          </a>
          <button class="podcast-cta secondary" @click="bookmarks.toggle({ ...episode, _type: 'podcast' })">
            <i :class="bookmarks.isBookmarked(episode) ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
            {{ bookmarks.isBookmarked(episode) ? 'Saved' : 'Save' }}
          </button>
        </div>
      </div>
    </section>

    <!-- Other episodes in show -->
    <section class="podcasts-section" v-if="otherEpisodes.length" style="margin-top:16px">
      <div class="podcasts-section-header">
        <h2>More episodes</h2>
      </div>
      <div class="episode-list">
        <article
          v-for="ep in otherEpisodes"
          :key="ep.id"
          class="episode-row"
          :class="{ 'coming-soon': !ep.audio_url }"
        >
          <img
            class="episode-art"
            :src="ep.artwork || show?.artwork || '/static/img/default-cover.jpg'"
            :alt="ep.title"
            loading="lazy"
          />
          <div class="episode-meta">
            <div class="episode-title">{{ ep.title }}</div>
            <div class="episode-subtitle">
              <span v-if="ep.date">{{ ep.date }}</span>
              <span class="coming-soon-badge" v-if="!ep.audio_url" style="margin-left:6px">Coming Soon</span>
            </div>
            <div class="episode-desc" v-if="ep.description">{{ truncate(ep.description, 100) }}</div>
          </div>
          <div class="episode-actions">
            <router-link
              v-if="ep.episode_number"
              :to="`/podcasts/${slug}/${ep.episode_number}`"
              class="episode-open"
              @click.stop
            >
              View
            </router-link>
          </div>
        </article>
      </div>
    </section>

  </div>

  <!-- Loading -->
  <div class="podcast-show-page" v-else>
    <section class="podcast-show-hero" style="margin-top:24px">
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiFetchCached } from '../composables/useApi'
import { useBookmarks } from '../composables/useBookmarks'
import { usePlayerStore } from '../stores/player'
import { setSeoMeta } from '../composables/useSeoMeta'
import { getPodcastVideoRoute } from '../composables/usePodcastVideo'

const route = useRoute()
const bookmarks = useBookmarks()
const playerStore = usePlayerStore()

const show = ref(null)
const episode = ref(null)

const slug = computed(() => route.params.slug)
const number = computed(() => route.params.number)

const isPlaying = computed(() => {
  return playerStore.currentTrack?.id === episode.value?.id && playerStore.isPlaying
})

const videoRoute = computed(() => getPodcastVideoRoute(show.value?.slug, episode.value))

function isInternalVideoRoute(route) {
  return String(route || '').startsWith('/videos/')
}

const otherEpisodes = computed(() => {
  if (!show.value || !episode.value) return []
  return (show.value.episodes || []).filter(ep =>
    String(ep.episode_number) !== String(number.value) &&
    String(ep.id) !== String(number.value)
  ).map(ep => ({
    ...ep,
    videoRoute: getPodcastVideoRoute(show.value.slug, ep),
  }))
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

function playEpisode() {
  if (!episode.value?.audio_url) return
  if (playerStore.currentTrack?.id === episode.value.id) {
    playerStore.togglePlay()
  } else {
    const allEps = (show.value?.episodes || []).filter(ep => ep.audio_url)
    const idx = allEps.findIndex(ep => ep.id === episode.value.id)
    playerStore.setQueue(allEps.map(ep => ({
      ...ep,
      artist: show.value?.title,
      cover_art: ep.artwork || show.value?.artwork,
    })), Math.max(0, idx))
  }
}

function updateMeta() {
  if (!episode.value) return
  setSeoMeta({
    title: episode.value.title,
    description: episode.value.description || show.value?.description || `Listen to ${episode.value.title} on Ahoy Indie Media.`,
    image: episode.value.artwork || show.value?.artwork || '/static/img/ahoy_logo.png',
    type: 'article',
    url: window.location.pathname,
  })
}

async function load() {
  const data = await apiFetchCached('/api/podcasts').catch(() => ({ shows: [] }))
  const shows = data.shows || []
  const foundShow = shows.find(s => s.slug === slug.value) || null
  show.value = foundShow
  episode.value = (foundShow?.episodes || []).find(ep =>
    String(ep.episode_number) === String(number.value) ||
    String(ep.id) === String(number.value)
  ) || null
  updateMeta()
}

onMounted(load)
watch(() => route.params, load)
</script>

<style scoped>
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

.episode-row.coming-soon {
  cursor: default;
  opacity: 0.8;
}

.episode-row.coming-soon:hover {
  background: rgba(255, 255, 255, 0.03);
  transform: none;
}

/* Glassmorphism format picker modal */
.format-picker-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1100;
  padding: 20px;
}

.format-picker-modal {
  background: rgba(20, 20, 28, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  border-radius: 20px;
  padding: 32px 24px;
  max-width: 420px;
  width: 100%;
  text-align: center;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.7);
  animation: modalEnter 0.35s cubic-bezier(0.34, 1.56, 0.64, 1);
}

@keyframes modalEnter {
  from {
    opacity: 0;
    transform: scale(0.92) translateY(30px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

.format-picker-header h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 8px;
  color: #fff;
  letter-spacing: -0.02em;
}

.format-picker-header p {
  font-size: 0.88rem;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 24px;
  line-height: 1.4;
}

.format-picker-options {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.picker-option-btn {
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  padding: 16px;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 16px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  text-align: left;
  width: 100%;
}

.picker-option-btn:hover {
  background: rgba(0, 212, 255, 0.08);
  border-color: rgba(0, 212, 255, 0.35);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 212, 255, 0.15);
}

.picker-option-btn i {
  font-size: 1.4rem;
  color: var(--accent-primary, #6ddcff);
  width: 32px;
  text-align: center;
}

.picker-option-text {
  display: flex;
  flex-direction: column;
}

.option-title {
  font-weight: 600;
  font-size: 1rem;
}

.option-desc {
  font-size: 0.78rem;
  color: rgba(255, 255, 255, 0.45);
  margin-top: 2px;
  line-height: 1.3;
}

.picker-cancel-btn {
  background: transparent;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: color 0.2s;
  padding: 8px;
}

.picker-cancel-btn:hover {
  color: #fff;
}

/* Video container */
.podcast-video-container {
  aspect-ratio: 16/9;
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  background: #000;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
}

.podcast-inline-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.25s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (min-width: 768px) {
  .podcast-video-container {
    max-width: 480px;
    width: 480px;
  }
}
</style>
