<template>
  <div class="shows-page" v-if="show">
    <!-- Video Player Section (50vh) - Starts at top, flush with edges -->
    <section 
      class="video-player-section" 
      ref="playerSection"
      :class="{ 'hide-controls': !showControls }"
      @mousemove="resetControlsTimer"
      @touchstart="resetControlsTimer"
    >
      <!-- Watermark -->
      <div class="video-watermark video-watermark--detail">
        <img src="/static/img/u_ahoy23.png" alt="Ahoy" />
      </div>

      <!-- Back Button -->
      <button class="video-back-btn" @click="goBack" aria-label="Go back">
        <i class="fas fa-chevron-left"></i>
      </button>

      <!-- Thumbnail with play overlay (when video not loaded) -->
      <div v-if="!showPlayer" class="video-thumbnail-container">
        <img
          :src="show.thumbnail || '/static/img/default-cover.jpg'"
          :alt="show.title"
          class="video-thumbnail"
          @error="show.thumbnail = null"
        />
        <div class="video-overlay">
          <button class="play-btn-large" @click="playVideo" aria-label="Play video">
            <i class="fas fa-play"></i>
          </button>
        </div>
      </div>

      <!-- Video embed (YouTube/Vimeo) -->
      <div v-if="embedUrl && showPlayer" class="video-embed-container">
        <iframe
          :src="embedUrl"
          style="position:absolute;top:0;left:0;width:100%;height:100%;border:0"
          allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; fullscreen"
          allowfullscreen
        ></iframe>
      </div>

      <!-- Direct video (mp4/webm) -->
      <video
        v-if="directVideoUrl && showPlayer"
        :src="directVideoUrl"
        :poster="show.thumbnail || show.artwork || '/static/img/default-cover.jpg'"
        autoplay
        preload="metadata"
        playsinline
        class="direct-video"
        ref="videoRef"
      ></video>

      <!-- Video Controls Overlay (when playing) -->
      <div v-if="showPlayer" class="video-controls-overlay">
        <div class="progress-bar-container">
          <div
            class="progress-bar"
            @click="seekVideo"
            @mousedown="startDraggingProgress"
            @touchstart="startDraggingProgress"
          >
            <div class="progress-fill" :style="{ width: videoProgress + '%' }"></div>
            <div class="progress-thumb" :style="{ left: videoProgress + '%' }"></div>
          </div>
        </div>
        <div class="controls-bottom">
          <div class="controls-left">
            <button class="control-btn" title="Back 10s" aria-label="Rewind 10s">
              <i class="fas fa-backward"></i>
            </button>
            <button class="control-btn play-btn-control" @click="togglePlay" title="Play/Pause" aria-label="Play/Pause">
              <i :class="isPlaying ? 'fas fa-pause' : 'fas fa-play'"></i>
            </button>
            <button class="control-btn" title="Forward 10s" aria-label="Forward 10s">
              <i class="fas fa-forward"></i>
            </button>
            <span class="time-display">{{ currentTime }} / {{ videoDuration }}</span>
          </div>
          <div class="controls-right">
            <button
              v-if="isCastAvailable"
              type="button"
              class="control-btn"
              title="Cast"
              @click="showCastModal = true"
            >
              <i class="fas fa-tv"></i>
            </button>
            <button class="control-btn fullscreen-btn" @click="toggleFullscreen" title="Fullscreen" :aria-label="isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'">
              <i :class="isFullscreen ? 'fas fa-compress' : 'fas fa-expand'"></i>
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- Cast Modal -->
    <CastModal v-model="showCastModal" />

    <!-- Metadata & Actions Section -->
    <section class="video-content-section">
      <div class="content-inner">
        <!-- Eyebrow meta row -->
        <div class="metadata-badges video-meta-row" v-if="show.category || show.episode_number || show.duration">
          <span class="video-meta-eyebrow" v-if="currentCategoryLabel">{{ currentCategoryLabel }}</span>
          <span class="video-meta-dot" v-if="currentCategoryLabel && (show.episode_number || show.duration)"></span>
          <span class="video-meta-item" v-if="show.episode_number">Episode {{ show.episode_number }}</span>
          <span class="video-meta-dot" v-if="show.episode_number && show.duration"></span>
          <span class="video-meta-item" v-if="show.duration">{{ show.duration }}</span>
        </div>

        <!-- Title -->
        <h2 class="video-title">{{ show.title }}</h2>

        <!-- Byline -->
        <div class="video-host" v-if="show.host">
          <span class="host-avatar"><i class="fas fa-user"></i></span>
          <span class="host-name">{{ show.host }}</span>
        </div>

        <!-- Description -->
        <p class="video-description" v-if="show.description">{{ show.description }}</p>

        <!-- Film Credits -->
        <section v-if="filmDetails.premiered || filmDetails.filmedAndEditedBy || filmDetails.skaters.length" class="video-film-credits">
          <div class="video-film-credits-head">
            <span class="video-film-credits-kicker">Film Details</span>
            <p v-if="filmDetails.premiered">Premiered {{ filmDetails.premiered }}</p>
          </div>
          <div v-if="filmDetails.filmedAndEditedBy" class="video-film-credits-meta">
            <h3>Filmed and Edited by</h3>
            <p>{{ filmDetails.filmedAndEditedBy }}</p>
          </div>
          <div v-if="filmDetails.skaters.length" class="video-film-credits-skaters">
            <h3>Featured Skaters</h3>
            <ul>
              <li v-for="skater in filmDetails.skaters" :key="skater">{{ skater }}</li>
            </ul>
          </div>
        </section>

        <!-- Action Buttons -->
        <div class="video-actions">
          <button
            class="action-btn action-btn-primary"
            @click="boostArtist"
            v-if="show.host"
            aria-label="Boost this film"
            title="Boost this film"
          >
            <i class="fas fa-bolt"></i>
            <span>Boost this film</span>
          </button>
          <button
            class="action-btn action-btn-secondary"
            @click="shareVideo"
            aria-label="Share"
            title="Share"
          >
            <i class="fas fa-share"></i>
            <span>Share</span>
          </button>
          <button
            class="action-btn action-btn-secondary"
            @click="bookmarks.toggle({ ...show, _type: 'show' })"
            :class="{ 'is-bookmarked': bookmarks.isBookmarked(show) }"
            aria-label="Save"
            title="Save"
          >
            <i :class="bookmarks.isBookmarked(show) ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
            <span>Save</span>
          </button>
        </div>
      </div>
    </section>

    <!-- Stills Gallery -->
    <section class="screenshots-section" v-if="screenshotsGallery.length">
      <div class="screenshots-header">
        <div>
          <h3>Stills</h3>
          <p>{{ screenshotsGallery.length }} frame{{ screenshotsGallery.length === 1 ? '' : 's' }}</p>
        </div>
      </div>
      <div class="screenshots-grid">
        <button
          v-for="(screenshot, idx) in screenshotsGallery"
          :key="`screenshot-${idx}`"
          type="button"
          class="screenshot-card"
          @click="openScreenshotLightbox(idx)"
          :aria-label="`Open still ${idx + 1} of ${screenshotsGallery.length}`"
        >
          <img :src="screenshot" :alt="`${show.title} still ${idx + 1}`" loading="lazy" />
          <span class="screenshot-index">{{ idx + 1 }}</span>
        </button>
      </div>
    </section>

    <!-- More from artist - Horizontal Scroll -->
    <section class="more-from-artist-section" v-if="moreInCategoryShows.length">
      <div class="section-header-flex">
        <div class="header-left" @click="collapsedMoreInCategory = !collapsedMoreInCategory" style="cursor:pointer">
          <h3>More {{ currentCategoryRailLabel }}</h3>
          <i :class="collapsedMoreInCategory ? 'fas fa-chevron-down' : 'fas fa-chevron-up'" class="collapse-icon"></i>
        </div>
        <router-link to="/videos" class="view-all-btn">View All</router-link>
      </div>
      <Transition name="expand">
        <div class="vibes-scroll-container" v-show="!collapsedMoreInCategory">
          <component
            v-for="s in moreInCategoryShows"
            :key="`category-${s.id}`"
            :is="'router-link'"
            :to="videoUrl(s)"
            class="vibe-card"
          >
            <div class="vibe-thumbnail">
              <img :src="s.thumbnail || '/static/img/default-cover.jpg'" :alt="s.title" loading="lazy" />
              <div class="vibe-duration">{{ s.duration || '42:00' }}</div>
            </div>
            <h4>{{ s.title }}</h4>
            <p class="vibe-meta">{{ s.host || 'Video' }} • {{ currentCategoryRailLabel }}</p>
          </component>
        </div>
      </Transition>
    </section>

    <section class="more-from-artist-section" v-if="moreFromArtistShows.length">
      <div class="section-header-flex">
        <div class="header-left" @click="collapsedMoreFromArtist = !collapsedMoreFromArtist" style="cursor:pointer">
          <h3>More from {{ currentArtistName }}</h3>
          <i :class="collapsedMoreFromArtist ? 'fas fa-chevron-down' : 'fas fa-chevron-up'" class="collapse-icon"></i>
        </div>
        <router-link to="/videos" class="view-all-btn">View All</router-link>
      </div>
      <Transition name="expand">
        <div class="vibes-scroll-container" v-show="!collapsedMoreFromArtist">
          <component
            v-for="s in moreFromArtistShows"
            :key="s.id"
            :is="'router-link'"
            :to="videoUrl(s)"
            class="vibe-card"
          >
            <div class="vibe-thumbnail">
              <img :src="s.thumbnail || '/static/img/default-cover.jpg'" :alt="s.title" loading="lazy" />
              <div class="vibe-duration">{{ s.duration || '42:00' }}</div>
            </div>
            <h4>{{ s.title }}</h4>
            <p class="vibe-meta">{{ s.host }} • {{ s.episode_number ? `Episode ${s.episode_number}` : 'Video' }}</p>
          </component>
        </div>
      </Transition>
    </section>

    <!-- Screenshot Lightbox -->
    <Teleport to="body">
      <Transition name="screenshot-lightbox-fade">
        <div v-if="screenshotLightboxOpen" class="screenshot-lightbox" @click.self="closeScreenshotLightbox">
          <button class="screenshot-lightbox-close" @click="closeScreenshotLightbox" aria-label="Close lightbox">
            <i class="fas fa-times"></i>
          </button>

          <button
            v-if="screenshotsGallery.length > 1"
            class="screenshot-lightbox-arrow screenshot-lightbox-prev"
            @click="prevScreenshot"
            aria-label="Previous screenshot"
          >
            <i class="fas fa-chevron-left"></i>
          </button>

          <div class="screenshot-lightbox-frame" @click.stop>
            <Transition name="screenshot-lightbox-image" mode="out-in">
              <img
                :key="screenshotLightboxIndex"
                :src="screenshotsGallery[screenshotLightboxIndex]"
                :alt="`Still ${screenshotLightboxIndex + 1} of ${screenshotsGallery.length}`"
                class="screenshot-lightbox-image"
              />
            </Transition>
          </div>

          <button
            v-if="screenshotsGallery.length > 1"
            class="screenshot-lightbox-arrow screenshot-lightbox-next"
            @click="nextScreenshot"
            aria-label="Next screenshot"
          >
            <i class="fas fa-chevron-right"></i>
          </button>

          <div class="screenshot-lightbox-counter">
            {{ screenshotLightboxIndex + 1 }} / {{ screenshotsGallery.length }}
            <span v-if="screenshotsGallery.length > 1" class="screenshot-lightbox-hint">· swipe to navigate</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>

  <!-- Loading -->
  <div class="shows-page" v-else>
    <section class="podcast-show-hero">
      <div class="podcast-show-hero-art skeleton" style="aspect-ratio:16/9;width:100%"></div>
      <div class="podcast-show-hero-meta">
        <div class="skeleton" style="height:14px;width:40%;margin-bottom:8px"></div>
        <div class="skeleton" style="height:24px;width:70%;margin-bottom:8px"></div>
        <div class="skeleton" style="height:14px;width:50%"></div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiFetchCached } from '../composables/useApi'
import { useBookmarks } from '../composables/useBookmarks'
import { useCasting } from '../composables/useCasting'
import { trackEvent } from '../composables/useAnalytics'
import { useVideoWatchAnalytics } from '../composables/useVideoWatchAnalytics'
import { trackRecentPlay } from '../composables/useRecentlyPlayed'
import { videoUrl, videoDetailSlug } from '../utils/urls'
import { setSeoMeta } from '../composables/useSeoMeta'
import CastModal from '../components/CastModal.vue'

const route = useRoute()
const router = useRouter()
const bookmarks = useBookmarks()
const casting = useCasting()

const show = ref(null)
const allShows = ref([])
const showPlayer = ref(false)
const playerSection = ref(null)
const videoRef = ref(null)
const videoProgress = ref(0)
const currentTime = ref('0:00')
const videoDuration = ref('0:00')
const isPlaying = ref(false)
const isFullscreen = ref(false)
const isDraggingProgress = ref(false)
const showCastModal = ref(false)
const showControls = ref(true)
const collapsedMoreInCategory = ref(false)
const collapsedMoreFromArtist = ref(false)
const screenshotLightboxOpen = ref(false)
const screenshotLightboxIndex = ref(0)
let screenshotTouchStartX = 0
let screenshotTouchStartY = 0
const videoWatch = useVideoWatchAnalytics(trackEvent, () => ({
  video_id: show.value?.id || route.params.id || route.params.showId || null,
  video_title: show.value?.title || '',
  video_host: show.value?.host || '',
  video_type: show.value ? 'show' : '',
  route_path: route.fullPath,
  src: directVideoUrl.value || show.value?.video_url || show.value?.url || '',
}))

let videoListenersBound = false
let videoListenersElement = null
let controlsTimer = null

function resetControlsTimer() {
  showControls.value = true
  if (controlsTimer) clearTimeout(controlsTimer)
  controlsTimer = setTimeout(() => {
    if (isPlaying.value || isFullscreen.value) {
      showControls.value = false
    }
  }, 1500)
}

function goBack() {
  router.push('/videos')
}

const isCastAvailable = computed(() => casting.isCastingAvailable.value)

async function loadShow() {
  const data = await apiFetchCached('/api/shows').catch(() => ({ shows: [] }))
  allShows.value = data.shows || []
  const id = route.params.id
  const hostSlug = route.params.hostSlug
  const showId = route.params.showId
  const routeSlug = String(id || showId || '').trim().toLowerCase()
  show.value = allShows.value.find(s =>
    id
      ? String(s.id) === String(id) ||
        String(s.show_id) === String(id) ||
        videoDetailSlug(s) === routeSlug
      : (
        (s.host_slug === hostSlug && String(s.id) === String(showId)) ||
        videoDetailSlug(s) === routeSlug ||
        String(s.id) === String(showId)
      )
  ) || null
  if (show.value) {
    setSeoMeta({
      title: show.value.title,
      description: show.value.description || `Watch ${show.value.title} on Ahoy Indie Media.`,
      image: show.value.thumbnail || '/static/img/ahoy_logo.png',
      type: 'video.other',
      url: window.location.pathname,
    })
  }
}

function normalizeKey(value) {
  return String(value || '').trim().toLowerCase()
}

function classifyVideo(showItem) {
  const category = normalizeKey(showItem?.category)
  const tags = Array.isArray(showItem?.tags) ? showItem.tags.map(normalizeKey) : []
  const title = normalizeKey(showItem?.title)

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

function categoryLabel(key) {
  if (key === 'music-videos') return 'Music Videos'
  if (key === 'live-shows') return 'Live Shows'
  if (key === 'films') return 'Films / Shorts'
  return ''
}

function categoryRailLabel(key) {
  if (key === 'music-videos') return 'music videos'
  if (key === 'live-shows') return 'live shows'
  if (key === 'films') return 'films / shorts'
  return ''
}

function showArtistKey(item) {
  return (
    normalizeKey(item?.host_slug) ||
    normalizeKey(item?.host_id) ||
    normalizeKey(item?.host)
  )
}

const currentArtistName = computed(() => show.value?.host || '')
const currentCategoryKey = computed(() => (show.value ? classifyVideo(show.value) : 'misc'))
const currentCategoryLabel = computed(() => categoryLabel(currentCategoryKey.value))
const currentCategoryRailLabel = computed(() => categoryRailLabel(currentCategoryKey.value))

const moreInCategoryShows = computed(() => {
  if (!show.value) return []
  if (currentCategoryKey.value === 'misc') return []

  return allShows.value
    .filter(s => s.id !== show.value.id && classifyVideo(s) === currentCategoryKey.value)
    .slice(0, 6)
})

const moreFromArtistShows = computed(() => {
  if (!show.value) return []
  if (!currentArtistName.value) return []
  const artistKey = showArtistKey(show.value)
  if (!artistKey) return []

  return allShows.value
    .filter(s => s.id !== show.value.id && showArtistKey(s) === artistKey)
    .slice(0, 6)
})

const screenshotsGallery = computed(() => {
  if (!show.value) return []
  const thumbnails = show.value.thumbnails || show.value.extra_fields?.thumbnails || []
  return Array.isArray(thumbnails) ? thumbnails : []
})

const filmDetails = computed(() => {
  const item = show.value || {}
  const extra = item.extra_fields || {}
  return {
    premiered: item.premiered || extra.premiered || '',
    filmedAndEditedBy: item.filmed_and_edited_by || extra.filmed_and_edited_by || item.filmed_by || extra.filmed_by || '',
    skaters: Array.isArray(item.featured_skaters)
      ? item.featured_skaters
      : Array.isArray(extra.featured_skaters)
        ? extra.featured_skaters
        : [],
  }
})

const embedUrl = computed(() => {
  if (!show.value) return null
  const url = show.value.video_url || show.value.url || ''
  const ytMatch = url.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&]+)/)
  if (ytMatch) return `https://www.youtube.com/embed/${ytMatch[1]}`
  const vimeoMatch = url.match(/vimeo\.com\/(\d+)/)
  if (vimeoMatch) return `https://player.vimeo.com/video/${vimeoMatch[1]}`
  return null
})

const directVideoUrl = computed(() => {
  if (!show.value || embedUrl.value) return null
  const url = show.value.video_url || show.value.url || ''
  if (/\.(mp4|webm|ogg|mov)(\?|$)/i.test(url) || url.includes('storage.googleapis.com') || url.includes('s3.amazonaws.com')) {
    return url
  }
  return null
})

function boostArtist() {
  const artistId = show.value.host_slug || show.value.host || show.value.host_id || ''
  const artistName = show.value.host || ''
  router.push({
    path: '/checkout',
    query: { type: 'boost', artist_id: artistId, artist_name: artistName }
  })
}

function shareVideo() {
  const url = window.location.href
  const text = `Check out "${show.value.title}" on Ahoy`

  if (navigator.share) {
    navigator.share({ title: show.value.title, text, url }).catch(() => {})
  } else {
    // Fallback: copy to clipboard
    navigator.clipboard.writeText(url).then(() => {
      alert('Link copied to clipboard!')
    })
  }
}

function openScreenshotLightbox(index) {
  if (!screenshotsGallery.value.length) return
  screenshotLightboxIndex.value = index
  screenshotLightboxOpen.value = true
  document.body.style.overflow = 'hidden'
}

function closeScreenshotLightbox() {
  screenshotLightboxOpen.value = false
  document.body.style.overflow = ''
}

function prevScreenshot() {
  if (!screenshotsGallery.value.length) return
  screenshotLightboxIndex.value = (screenshotLightboxIndex.value - 1 + screenshotsGallery.value.length) % screenshotsGallery.value.length
}

function nextScreenshot() {
  if (!screenshotsGallery.value.length) return
  screenshotLightboxIndex.value = (screenshotLightboxIndex.value + 1) % screenshotsGallery.value.length
}

function onScreenshotKeyDown(event) {
  if (!screenshotLightboxOpen.value) return
  if (event.key === 'Escape') closeScreenshotLightbox()
  if (event.key === 'ArrowLeft') prevScreenshot()
  if (event.key === 'ArrowRight') nextScreenshot()
}

function onScreenshotTouchStart(event) {
  if (!screenshotLightboxOpen.value) return
  screenshotTouchStartX = event.touches[0].clientX
  screenshotTouchStartY = event.touches[0].clientY
}

function onScreenshotTouchEnd(event) {
  if (!screenshotLightboxOpen.value) return
  const dx = event.changedTouches[0].clientX - screenshotTouchStartX
  const dy = event.changedTouches[0].clientY - screenshotTouchStartY
  if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
    if (dx < 0) nextScreenshot()
    else prevScreenshot()
  }
}

function togglePlay() {
  if (videoRef.value) {
    if (videoRef.value.paused) {
      videoRef.value.play()
    } else {
      videoRef.value.pause()
    }
  }
}

function seekVideo(e) {
  if (!videoRef.value || !directVideoUrl.value) return
  const rect = e.currentTarget.getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  videoRef.value.currentTime = percent * videoRef.value.duration
}

function startDraggingProgress(e) {
  isDraggingProgress.value = true
  updateVideoProgress(e)

  const handleMove = (moveEvent) => {
    if (isDraggingProgress.value) {
      updateVideoProgress(moveEvent)
    }
  }

  const handleEnd = () => {
    isDraggingProgress.value = false
    document.removeEventListener('mousemove', handleMove)
    document.removeEventListener('touchmove', handleMove)
    document.removeEventListener('mouseup', handleEnd)
    document.removeEventListener('touchend', handleEnd)
  }

  document.addEventListener('mousemove', handleMove)
  document.addEventListener('touchmove', handleMove)
  document.addEventListener('mouseup', handleEnd)
  document.addEventListener('touchend', handleEnd)
}

function updateVideoProgress(e) {
  if (!videoRef.value || !directVideoUrl.value) return
  const progressBar = document.querySelector('.progress-bar')
  if (!progressBar) return

  const rect = progressBar.getBoundingClientRect()
  const clientX = e.touches ? e.touches[0].clientX : e.clientX
  const percent = Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
  videoRef.value.currentTime = percent * videoRef.value.duration
}

function formatTime(seconds) {
  const total = Number(seconds)
  if (!Number.isFinite(total) || total <= 0) return '0:00'
  const mins = Math.floor(total / 60)
  const secs = Math.floor(total % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

function handleVideoPlay() {
  isPlaying.value = true
}

function handleVideoPause() {
  isPlaying.value = false
}

function handleVideoTimeUpdate() {
  if (videoRef.value?.duration) {
    videoProgress.value = (videoRef.value.currentTime / videoRef.value.duration) * 100
    currentTime.value = formatTime(videoRef.value.currentTime)
  }
}

function handleVideoLoadedMetadata() {
  if (videoRef.value) {
    videoDuration.value = formatTime(videoRef.value.duration)
  }
}

function bindVideoListeners() {
  if (!videoRef.value || !directVideoUrl.value || videoListenersBound) return
  const el = videoRef.value
  videoWatch.bind(el)
  el.addEventListener('play', handleVideoPlay)
  el.addEventListener('pause', handleVideoPause)
  el.addEventListener('timeupdate', handleVideoTimeUpdate)
  el.addEventListener('loadedmetadata', handleVideoLoadedMetadata)
  videoListenersElement = el
  videoListenersBound = true
}

function destroyVideoListeners() {
  if (!videoListenersElement) return
  videoListenersElement.removeEventListener('play', handleVideoPlay)
  videoListenersElement.removeEventListener('pause', handleVideoPause)
  videoListenersElement.removeEventListener('timeupdate', handleVideoTimeUpdate)
  videoListenersElement.removeEventListener('loadedmetadata', handleVideoLoadedMetadata)
  videoListenersElement = null
  videoListenersBound = false
}

async function playVideo() {
  if (show.value) {
    trackRecentPlay({
      id: show.value.id,
      type: 'show',
      title: show.value.title,
      host: show.value.host,
      thumbnail: show.value.thumbnail,
      url: show.value.video_url || show.value.url,
    })
  }
  showPlayer.value = true
  await nextTick()
  bindVideoListeners()

  playerSection.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
}

function toggleFullscreen() {
  const el = playerSection.value
  if (!el) return

  // Standard and prefixed versions
  const requestFs = el.requestFullscreen || el.webkitRequestFullscreen || el.mozRequestFullScreen || el.msRequestFullscreen
  const exitFs = document.exitFullscreen || document.webkitExitFullscreen || document.mozCancelFullScreen || document.msExitFullscreen
  const fsElement = document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement

  if (!fsElement && !el.classList.contains('fs-active')) {
    if (requestFs) {
      // Try native fullscreen
      const promise = requestFs.call(el)
      if (promise && promise.then) {
        promise.then(() => {
          isFullscreen.value = true
        }).catch(() => {
          activateCssFallback()
        })
      } else {
        // Fallback for browsers that don't return a promise
        isFullscreen.value = true
      }
    } else {
      activateCssFallback()
    }
  } else {
    // Exit fullscreen
    if (fsElement) {
      if (exitFs) exitFs.call(document)
    } else {
      deactivateCssFallback()
    }
  }
}

function activateCssFallback() {
  playerSection.value?.classList.add('fs-active')
  isFullscreen.value = true
  document.body.style.overflow = 'hidden'
}

function deactivateCssFallback() {
  playerSection.value?.classList.remove('fs-active')
  isFullscreen.value = false
  document.body.style.overflow = ''
}

onMounted(async () => {
  await loadShow()

  const handleFsChange = () => {
    const fsElement = document.fullscreenElement || document.webkitFullscreenElement || document.mozFullScreenElement || document.msFullscreenElement
    if (!fsElement) {
      isFullscreen.value = false
      playerSection.value?.classList.remove('fs-active')
      document.body.style.overflow = ''
    } else {
      isFullscreen.value = true
    }
  }

  document.addEventListener('fullscreenchange', handleFsChange)
  document.addEventListener('webkitfullscreenchange', handleFsChange)
  document.addEventListener('mozfullscreenchange', handleFsChange)
  document.addEventListener('MSFullscreenChange', handleFsChange)

  window.addEventListener('keydown', onScreenshotKeyDown)
  window.addEventListener('touchstart', onScreenshotTouchStart, { passive: true })
  window.addEventListener('touchend', onScreenshotTouchEnd, { passive: true })
})

// Refetch when route params change (old id or new hostSlug/showId)
watch(() => [route.params.id, route.params.hostSlug, route.params.showId], async () => {
  await loadShow()
})

watch(directVideoUrl, async (nextUrl, prevUrl) => {
  if (!nextUrl) {
    videoWatch.reset('direct_video_unavailable')
    destroyVideoListeners()
    return
  }
  if (nextUrl !== prevUrl) {
    destroyVideoListeners()
    await nextTick()
    bindVideoListeners()
  }
})

onUnmounted(() => {
  if (controlsTimer) clearTimeout(controlsTimer)
  destroyVideoListeners()
  videoWatch.destroy()
  window.removeEventListener('keydown', onScreenshotKeyDown)
  window.removeEventListener('touchstart', onScreenshotTouchStart)
  window.removeEventListener('touchend', onScreenshotTouchEnd)
  document.body.style.overflow = ''
})
</script>

<style scoped>
/* Main container - flush with edges like Studio pages */
.shows-page {
  width: 100%;
  min-height: 100vh;
  margin: 0;
  padding: 0;
}


/* Video Player Section - Flush to edges, starts at top */
.video-player-section {
  width: 100%;
  height: 50vh;
  background: #000;
  overflow: hidden;
  position: relative;
  margin: 0;
  margin-top: calc(-1 * max(0px, env(safe-area-inset-top)));
  padding-top: max(0px, env(safe-area-inset-top));
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

/* CSS fallback fullscreen (when native FS blocked, e.g. some iframe contexts) */
.video-player-section.fs-active {
  position: fixed !important;
  inset: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  height: 100dvh !important;
  z-index: 9999;
  margin: 0 !important;
  padding: 0 !important;
  border-radius: 0 !important;
}

/* Native fullscreen styles */
.video-player-section:fullscreen,
.video-player-section:-webkit-full-screen {
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  background: #000;
}

/* Desktop: rounded glass frame, inset from edges (mobile stays flush per app convention) */
@media (min-width: 1025px) {
  .video-player-section {
    max-width: 1100px;
    height: auto;
    aspect-ratio: 21 / 9;
    max-height: 58vh;
    margin: 18px auto 0;
    border-radius: var(--card-radius, 22px);
    box-shadow: 0 24px 70px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.07), inset 0 1px 0 rgba(255, 255, 255, 0.08);
  }

  .video-player-section.fs-active,
  .video-player-section:fullscreen,
  .video-player-section:-webkit-full-screen {
    max-width: none;
    aspect-ratio: auto;
    max-height: none;
    margin: 0;
    border-radius: 0;
  }
}

/* Fullscreen button pulse on entry */
.fullscreen-btn {
  transition: transform 0.2s, background 0.2s, box-shadow 0.3s !important;
}
.fullscreen-btn:active {
  transform: scale(0.85) !important;
  box-shadow: 0 0 0 6px rgba(189, 194, 255, 0.25);
}

.video-thumbnail-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.video-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
}

.play-btn-large {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: var(--primary-color, #ec4899);
  color: white;
  border: none;
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 4px 20px rgba(236, 72, 153, 0.4);
}

.play-btn-large:hover {
  transform: scale(1.1);
  box-shadow: 0 6px 30px rgba(236, 72, 153, 0.6);
}

.play-btn-large:active {
  transform: scale(0.95);
}

.video-embed-container {
  position: relative;
  width: 100%;
  height: 100%;
}

.direct-video {
  width: 100%;
  height: 100%;
  display: block;
}

/* Video Controls Overlay */
.video-controls-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.9), transparent);
  padding: 40px 16px 16px 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-bar-container {
  width: 100%;
}

.progress-bar {
  position: relative;
  width: 100%;
  height: 4px;
  background: rgba(255, 255, 255, 0.18);
  border-radius: var(--pill, 999px);
  overflow: visible;
  cursor: pointer;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--ahoy-indigo, #6366f1), var(--ahoy-magenta, #ff0060));
  border-radius: var(--pill, 999px);
  transition: width 0.1s linear;
}

.progress-thumb {
  position: absolute;
  top: 50%;
  transform: translate(-50%, -50%);
  width: 12px;
  height: 12px;
  background: #fff;
  border-radius: 50%;
  box-shadow: 0 0 0 4px rgba(255, 133, 162, 0.28), 0 1px 4px rgba(0, 0, 0, 0.4);
}

.controls-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.controls-left,
.controls-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(10, 14, 24, 0.4);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.18);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.12);
  transition: background 0.2s;
}

.control-btn:hover {
  background: rgba(10, 14, 24, 0.6);
  border-color: rgba(255, 255, 255, 0.28);
}

.play-btn-control {
  width: 52px;
  height: 52px;
  font-size: 18px;
  background: var(--ahoy-magenta, #ff0060);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 8px 20px rgba(255, 0, 96, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.25);
}

.play-btn-control:hover {
  background: var(--ahoy-magenta, #ff0060);
  filter: brightness(1.08);
}

.time-display {
  color: var(--fg-2, rgba(255, 255, 255, 0.85));
  font-size: 13px;
  font-family: var(--font-mono, ui-monospace, 'SF Mono', Menlo, monospace);
  letter-spacing: 0.03em;
  font-variant-numeric: tabular-nums;
  margin-left: 8px;
  padding: 6px 12px;
  border-radius: var(--pill, 999px);
  background: rgba(10, 14, 24, 0.45);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.12);
}

/* Content Section - Flush layout */
.video-content-section {
  width: 100%;
  padding: 24px 16px;
  background: transparent;
  box-sizing: border-box;
}

.content-inner {
  max-width: 100%;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

@media (min-width: 1025px) {
  .video-content-section {
    padding: 26px 32px 40px;
  }

  .content-inner {
    max-width: 900px;
    margin: 0 auto;
  }
}

/* Eyebrow meta row */
.metadata-badges {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.video-meta-eyebrow {
  font-size: 11px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--fg-3, rgba(255, 255, 255, 0.55));
  font-weight: 700;
}

.video-meta-item {
  font-size: 11px;
  color: var(--fg-3, rgba(255, 255, 255, 0.55));
}

.video-meta-dot {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.3);
  flex-shrink: 0;
}

.video-title {
  font-size: clamp(24px, 5vw, 30px);
  font-weight: 800;
  letter-spacing: -0.02em;
  color: var(--fg-1, white);
  margin: 0;
  line-height: 1.15;
}

.video-host {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 4px;
}

.host-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ahoy-pink-soft, #ff85a2);
  font-size: 12px;
  flex-shrink: 0;
}

.host-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--fg-1, rgba(255, 255, 255, 0.9));
  margin: 0;
}

.video-description {
  font-size: 14.4px;
  line-height: 1.55;
  color: var(--fg-2, rgba(255, 255, 255, 0.8));
  margin: 8px 0 0 0;
  max-width: 640px;
}

.video-film-credits {
  margin-top: 16px;
  max-width: 720px;
  padding: 14px 16px;
  border-radius: 18px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.video-film-credits-head {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-bottom: 12px;
}

.video-film-credits-kicker {
  color: rgba(255, 255, 255, 0.72);
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.video-film-credits-head p,
.video-film-credits-meta p {
  margin: 0;
  color: rgba(255, 255, 255, 0.82);
  line-height: 1.55;
}

.video-film-credits-meta + .video-film-credits-skaters {
  margin-top: 12px;
}

.video-film-credits-meta h3,
.video-film-credits-skaters h3 {
  margin: 0 0 6px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 12px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.video-film-credits-skaters ul {
  margin: 0;
  padding-left: 18px;
  columns: 2;
  column-gap: 24px;
}

.video-film-credits-skaters li {
  margin: 0 0 5px;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.4;
}

/* Action pills: Boost (primary, solid magenta) + Share/Save (secondary, glass outline) */
.video-actions {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 18px;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: var(--pill, 999px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.045);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  color: var(--fg-2, rgba(255, 255, 255, 0.85));
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.15s var(--ease-out, cubic-bezier(0.4, 0, 0.2, 1));
}

.action-btn-secondary:hover {
  background: rgba(255, 255, 255, 0.08);
}

.action-btn:active {
  transform: scale(0.97);
}

.action-btn-primary {
  border-color: rgba(255, 255, 255, 0.15);
  background: var(--ahoy-magenta, #ff0060);
  color: #fff;
  box-shadow: 0 4px 16px rgba(255, 0, 96, 0.32);
}

.action-btn-primary:hover {
  background: var(--ahoy-magenta, #ff0060);
  filter: brightness(1.08);
}

.action-btn.is-bookmarked {
  border-color: rgba(255, 133, 162, 0.35);
  background: rgba(255, 0, 96, 0.12);
  color: #fff;
}

/* More From Artist Section */
.more-from-artist-section {
  width: 100%;
  margin-top: 32px;
  padding: 32px 16px 64px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  box-sizing: border-box;
}

.section-header-flex {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
  padding-top: 24px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
  transition: opacity 0.2s;
}

.header-left:hover {
  opacity: 0.8;
}

.collapse-icon {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.4);
}

.section-header-flex h3 {
  font-size: 1.25rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0;
}

.view-all-btn {
  color: rgba(189, 194, 255, 0.9);
  text-decoration: none;
  font-size: 14px;
  font-weight: 600;
  transition: color 0.2s;
}

.view-all-btn:hover {
  color: rgba(189, 194, 255, 1);
  text-decoration: underline;
}

.vibes-scroll-container {
  display: flex;
  gap: 24px;
  overflow-x: auto;
  padding-bottom: 12px;
  scroll-behavior: smooth;
  scrollbar-width: thin;
}

.vibes-scroll-container::-webkit-scrollbar {
  display: none;
}

/* Expand Transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  max-height: 400px;
  overflow: hidden;
}

.expand-enter-from,
.expand-leave-to {
  max-height: 0;
  opacity: 0;
  transform: translateY(-10px);
}

.vibe-card {
  flex: 0 0 288px;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
  transition: transform 0.2s;
}

.vibe-card:hover {
  transform: translateY(-4px);
}

.vibe-thumbnail {
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  border-radius: 12px;
  overflow: hidden;
  margin-bottom: 12px;
  background: rgba(31, 31, 34, 0.5);
}

.vibe-thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.3s;
}

.vibe-card:hover .vibe-thumbnail img {
  transform: scale(1.05);
}

.vibe-duration {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0, 0, 0, 0.7);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
}

.vibe-card h4 {
  font-size: 14px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
  margin: 0 0 4px 0;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.vibe-meta {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
  margin: 0;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* Screenshots Section */
.screenshots-section {
  padding: 2.5rem 2rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.screenshots-header {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 1.5rem;
}

.screenshots-header h3 {
  margin: 0;
  font-size: 1.4rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
}

.screenshots-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
}

.screenshots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
  gap: 0.75rem;
}

.screenshot-card {
  position: relative;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.04);
  cursor: zoom-in;
  aspect-ratio: 16 / 9;
  transition: all 0.2s ease;
}

.screenshot-card:hover {
  border-color: rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.08);
  transform: scale(1.02);
}

.screenshot-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.25s ease;
}

.screenshot-card:hover img {
  transform: scale(1.05);
}

.screenshot-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 45%, rgba(0, 0, 0, 0.35));
  pointer-events: none;
}

.screenshot-index {
  position: absolute;
  right: 0.4rem;
  bottom: 0.35rem;
  z-index: 1;
  min-width: 1.25rem;
  height: 1.25rem;
  padding: 0 0.3rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 12, 0.7);
  color: rgba(255, 255, 255, 0.92);
  font-size: 0.65rem;
  font-weight: 800;
}

/* Screenshot Lightbox */
.screenshot-lightbox {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.92);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

.screenshot-lightbox-frame {
  position: relative;
  max-width: 90vw;
  max-height: 85vh;
  display: flex;
  align-items: center;
  justify-content: center;
}

.screenshot-lightbox-image {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  display: block;
}

.screenshot-lightbox-close {
  position: absolute;
  top: 1rem;
  right: 1rem;
  z-index: 10000;
  width: 44px;
  height: 44px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.4);
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  transition: all 0.2s;
}

.screenshot-lightbox-close:hover {
  background: rgba(0, 0, 0, 0.7);
  border-color: rgba(255, 255, 255, 0.4);
}

.screenshot-lightbox-arrow {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  z-index: 9999;
  width: 44px;
  height: 44px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.4);
  color: rgba(255, 255, 255, 0.9);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
  transition: all 0.2s;
}

.screenshot-lightbox-arrow:hover {
  background: rgba(0, 0, 0, 0.7);
  border-color: rgba(255, 255, 255, 0.4);
}

.screenshot-lightbox-prev {
  left: 1rem;
}

.screenshot-lightbox-next {
  right: 1rem;
}

.screenshot-lightbox-counter {
  position: absolute;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  padding: 0.6rem 1.2rem;
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.6);
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.screenshot-lightbox-hint {
  display: block;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.8rem;
  font-weight: 400;
  margin-top: 0.3rem;
}

/* Lightbox Transitions */
.screenshot-lightbox-fade-enter-active,
.screenshot-lightbox-fade-leave-active {
  transition: opacity 0.3s ease;
}

.screenshot-lightbox-fade-enter-from,
.screenshot-lightbox-fade-leave-to {
  opacity: 0;
}

.screenshot-lightbox-image-enter-active,
.screenshot-lightbox-image-leave-active {
  transition: opacity 0.2s ease;
}

.screenshot-lightbox-image-enter-from,
.screenshot-lightbox-image-leave-to {
  opacity: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .video-player-section {
    height: 60vh;
  }

  .content-inner {
    gap: 12px;
  }

  .metadata-badges {
    gap: 8px;
  }

  .video-title {
    font-size: 28px;
  }

  .video-actions {
    margin-top: 8px;
  }

  .video-film-credits {
    padding: 12px 14px;
  }

  .vibe-card {
    flex: 0 0 240px;
  }

  .vibes-scroll-container {
    gap: 16px;
  }
}

@media (max-width: 480px) {
  .video-detail-header {
    height: 48px;
    padding: 0 12px;
  }

  .header-title {
    font-size: 14px;
  }

  .video-content-section {
    padding: 20px 0;
  }

  .video-title {
    font-size: 20px;
  }

  .video-film-credits {
    margin-top: 12px;
  }

  .video-film-credits-skaters ul {
    columns: 1;
  }

  .action-btn {
    flex: 1;
    min-width: auto;
    height: 44px;
    font-size: 11px;
  }

  .action-btn span {
    display: none;
  }

  .bookmark-btn {
    flex: 0 0 44px;
  }

  .section-header-flex {
    margin-bottom: 16px;
  }

  .section-header-flex h3 {
    font-size: 1.1rem;
  }

  .vibe-card {
    flex: 0 0 200px;
  }

  .vibes-scroll-container {
    gap: 12px;
  }
}

.video-back-btn {
  position: absolute;
  top: 12px;
  left: 12px;
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: rgba(0,0,0,0.5);
  border: none;
  color: #fff;
  border-radius: 50%;
  cursor: pointer;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  font-size: 18px;
}

.video-back-btn:hover {
  background: rgba(0,0,0,0.7);
}

.video-watermark--detail {
  width: min(18vw, 88px);
  height: auto;
}

.video-watermark--detail img {
  filter: none;
}
</style>
