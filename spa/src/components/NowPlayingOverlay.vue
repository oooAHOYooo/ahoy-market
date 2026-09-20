<template>
  <Transition name="overlay-slide">
    <div class="now-playing-overlay" v-if="canShowNowPlayingOverlay"
      :style="dragStyle"
      @touchstart="onTouchStart" @touchmove="onTouchMove" @touchend="onTouchEnd">
      <!-- Header / Handle -->
      <div class="np-header">
        <button class="np-minimize-btn" @click="closeNowPlaying" aria-label="Minimize">
          <i class="fas fa-chevron-down"></i>
        </button>
        <div class="np-header-center">
          <div class="np-header-handle"></div>
          <span class="np-header-label">
            <template v-if="videoMode">Watching</template>
            <template v-else-if="hasVideo">Now Playing · <button class="np-header-watch-btn" @click="enterVideoMode"><i class="fas fa-video"></i> Watch</button></template>
            <template v-else>Now Playing</template>
          </span>
        </div>
        <div class="np-header-spacer"></div>
      </div>

      <div class="np-content" :class="{ 'np-content--video': videoMode }">
        <template v-if="playerStore.currentTrack">
          <!-- Artwork / Video area -->
          <div class="np-artwork-container" :class="{ 'np-artwork-container--video': videoMode }">
            <!-- Video player -->
            <video
              v-if="videoMode && hasVideo"
              ref="videoEl"
              :src="playerStore.currentTrack.video_url"
              :poster="playerStore.currentTrack.cover_art || playerStore.currentTrack.thumbnail || playerStore.currentTrack.artwork || '/static/img/default-cover.jpg'"
              class="np-video"
              preload="metadata"
              playsinline
              @timeupdate="onVideoTimeUpdate"
              @ended="onVideoEnded"
              @click="toggleVideoPlay"
              @waiting="videoBuffering = true"
              @canplay="videoBuffering = false"
              @playing="videoBuffering = false"
              @touchstart.stop
              @touchmove.stop
              @touchend.stop
            ></video>
            <!-- Album art -->
            <img
              v-else
              :src="playerStore.currentTrack.cover_art || playerStore.currentTrack.thumbnail || playerStore.currentTrack.artwork || '/static/img/default-cover.jpg'"
              :alt="playerStore.currentTrack.title"
              class="np-artwork"
            />
            <!-- Video buffering spinner -->
            <div v-if="videoMode && videoBuffering" class="np-video-loading">
              <div class="loading-spinner"></div>
            </div>
          </div>

          <!-- Track info -->
          <div class="np-info" :class="{ 'np-info--compact': videoMode }">
            <h1 class="np-title">{{ playerStore.currentTrack.title }}</h1>
            <p v-if="!videoMode" class="np-artist"
              :class="{ 'np-artist--link': playerStore.currentTrack.artist_slug }"
              @click="goToArtist">{{ playerStore.currentTrack.artist || '' }}</p>
          </div>

          <!-- Seek bar -->
          <div class="np-seek">
            <div v-if="videoMode" class="np-seek-bar"
              @click="onVideoSeek"
              @touchstart.prevent="onVideoSeekTouchStart"
              @touchmove.prevent="onVideoSeekTouchMove"
              @touchend.prevent="onVideoSeekTouchEnd">
              <div class="np-seek-fill" :style="{ width: videoDuration ? (videoCurrentTime / videoDuration * 100) + '%' : '0%' }"></div>
              <div class="np-seek-thumb" :style="{ left: videoDuration ? (videoCurrentTime / videoDuration * 100) + '%' : '0%' }"></div>
            </div>
            <div v-else class="np-seek-bar" ref="seekBar"
              @click="onSeek"
              @touchstart.prevent="onSeekTouchStart"
              @touchmove.prevent="onSeekTouchMove"
              @touchend.prevent="onSeekTouchEnd">
              <div class="np-seek-fill" :style="{ width: seekDragProgress !== null ? seekDragProgress + '%' : playerStore.progress + '%' }"></div>
              <div class="np-seek-thumb" :style="{ left: seekDragProgress !== null ? seekDragProgress + '%' : playerStore.progress + '%' }"></div>
            </div>
            <div class="np-times">
              <span>{{ formatTime(videoMode ? videoCurrentTime : playerStore.currentTime) }}</span>
              <span>{{ formatTime(videoMode ? videoDuration : playerStore.duration) }}</span>
            </div>
          </div>

          <!-- Loading Status -->
          <div v-if="playerStore.loading && !videoMode" class="np-loading">
            <div class="loading-spinner"></div>
            <span class="loading-text">Loading...</span>
          </div>

          <!-- Controls -->
          <div class="np-secondary-controls">
            <button v-if="!videoMode" class="np-util-btn" @click="cyclePlaybackSpeed" :class="{ 'np-util-btn--active': playerStore.playbackRate !== 1 }">
              {{ playerStore.playbackRate }}x
            </button>
            <button v-if="videoMode" class="np-util-btn np-util-btn--active" @click="exitVideoMode">
              <i class="fas fa-headphones"></i> Audio
            </button>
            <div class="np-util-spacer"></div>
            <button v-if="!videoMode" class="np-util-btn" @click="toggleSleepTimer" :class="{ 'np-util-btn--active': sleepTimer.isActive() }">
              <i class="fas fa-moon"></i>
              <span v-if="sleepTimer.isActive()" class="sleep-dot"></span>
            </button>
          </div>

          <!-- Sleep Picker Popover -->
          <div v-if="showSleepPicker" class="np-popover np-sleep-picker">
            <div class="np-popover-title">Sleep Timer</div>
            <div class="np-popover-grid">
              <button v-for="m in sleepMinutes" :key="m" @click="startSleepTimer(m)">{{ m }}m</button>
            </div>
          </div>

          <!-- Video mode controls -->
          <div v-if="videoMode" class="np-controls">
            <button class="np-btn np-btn-secondary np-btn-skip" @click="skipVideo(-videoSeekStep)" :aria-label="`Skip Back ${videoSeekStep}s`">
              <i class="fas fa-undo"></i>
              <span class="skip-label">{{ videoSeekStep }}</span>
            </button>
            <button class="np-btn np-btn-play" @click="toggleVideoPlay" aria-label="Play/Pause">
              <i :class="videoPlaying ? 'fas fa-pause' : 'fas fa-play'" style="margin-left:2px"></i>
            </button>
            <button class="np-btn np-btn-secondary np-btn-skip" @click="skipVideo(videoSeekStep)" :aria-label="`Skip Forward ${videoSeekStep}s`">
              <i class="fas fa-redo"></i>
              <span class="skip-label">{{ videoSeekStep }}</span>
            </button>
          </div>

          <!-- Audio mode controls -->
          <div v-else class="np-controls">
            <button v-if="!isPodcast" class="np-btn np-btn-secondary" @click="playerStore.toggleShuffle()" aria-label="Shuffle"
              :class="{ 'np-btn--active': playerStore.shuffle }">
              <i class="fas fa-shuffle"></i>
            </button>
            <button class="np-btn np-btn-secondary" @click="playerStore.seekBackward?.()" aria-label="Rewind">
              <i class="fas fa-backward-step"></i>
            </button>

            <button class="np-btn np-btn-play" @click="playerStore.togglePlay()" aria-label="Play/Pause">
              <i :class="playerStore.isPlaying ? 'fas fa-pause' : 'fas fa-play'" style="margin-left:2px"></i>
            </button>

            <button class="np-btn np-btn-secondary" @click="playerStore.seekForward?.()" aria-label="Fast forward">
              <i class="fas fa-forward-step"></i>
            </button>

            <button v-if="!isPodcast" class="np-btn np-btn-secondary" @click="playerStore.toggleRepeat()" aria-label="Repeat"
              :class="{ 'np-btn--active': playerStore.repeat }">
              <i class="fas fa-repeat"></i>
            </button>
          </div>

          <!-- Actions row -->
          <div class="np-actions">
            <button class="np-action-btn np-action-btn--save" @click="onBookmark" :title="bookmarks.isBookmarked(playerStore.currentTrack) ? 'Saved' : 'Save'">
              <i :class="bookmarks.isBookmarked(playerStore.currentTrack) ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
              <span class="np-action-label">{{ bookmarks.isBookmarked(playerStore.currentTrack) ? 'Saved' : 'Save' }}</span>
            </button>
            <button class="np-action-btn np-action-btn--boost" @click="onBoost" title="Boost artist">
              <i class="fas fa-bolt"></i>
              <span class="np-action-label">Boost</span>
            </button>
            <button class="np-action-btn" @click="onShare">
              <i class="fas fa-share-alt"></i>
              <span class="np-action-label">Share</span>
            </button>
          </div>
        </template>

        <div v-else class="np-empty-state">
          <div class="np-empty-artwork">
            <i class="fas fa-play"></i>
          </div>
          <div class="np-info np-empty-info">
            <h1 class="np-title">Nothing playing</h1>
            <p class="np-artist">Choose something to start listening.</p>
          </div>
          <div class="np-empty-actions">
            <router-link to="/music" class="np-action-btn np-empty-link" @click="closeNowPlaying">Music</router-link>
            <router-link to="/podcasts" class="np-action-btn np-empty-link" @click="closeNowPlaying">Podcasts</router-link>
          </div>
        </div>

      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '../stores/player'
import { useBookmarks } from '../composables/useBookmarks'
import { useShare, useHaptics, useSleepTimer } from '../composables/useNative'
import { useOverlay } from '../composables/useOverlay'

const router = useRouter()
const playerStore = usePlayerStore()
const bookmarks = useBookmarks()
const { shareTrack } = useShare()
const haptics = useHaptics()
const { isNowPlayingOpen, canOpenNowPlaying, closeNowPlaying } = useOverlay()
const sleepTimer = useSleepTimer()

const isPodcast = computed(() => {
  const t = playerStore.currentTrack
  if (!t) return false
  return t.type === 'podcast' || t._type === 'podcast' || t.type === 'podcast-episode' || t.type === 'podcastEpisode'
})

// Video podcast mode
const videoMode = ref(false)
const videoEl = ref(null)
const videoCurrentTime = ref(0)
const videoDuration = ref(0)
const videoPlaying = ref(false)
const videoBuffering = ref(false)

const hasVideo = computed(() => !!playerStore.currentTrack?.video_url?.trim())
const videoSeekStep = computed(() => {
  if (!videoDuration.value || !isFinite(videoDuration.value)) return 5
  const step = Math.round(videoDuration.value * 0.05)
  return Math.max(5, Math.min(30, step))
})

// Reset video mode when track changes without trying to resume audio
watch(() => playerStore.currentTrack?.id, () => {
  if (videoMode.value && videoEl.value) videoEl.value.pause()
  videoMode.value = false
  videoBuffering.value = false
  videoCurrentTime.value = 0
  videoDuration.value = 0
  videoPlaying.value = false
})

function enterVideoMode() {
  haptics.light()
  const startTime = playerStore.currentTime
  playerStore.pause()
  videoMode.value = true
  // Seek video after DOM update
  setTimeout(() => {
    if (videoEl.value) {
      videoEl.value.currentTime = startTime
      videoEl.value.play()
      videoPlaying.value = true
    }
  }, 50)
}

function exitVideoMode() {
  if (videoEl.value) {
    const t = videoEl.value.currentTime
    videoEl.value.pause()
    videoPlaying.value = false
    // Resume audio from same position
    if (videoDuration.value > 0) {
      playerStore.seek((t / videoDuration.value) * 100)
    }
    playerStore.play()
  }
  videoMode.value = false
}

function onVideoTimeUpdate() {
  if (!videoEl.value) return
  videoCurrentTime.value = videoEl.value.currentTime
  videoDuration.value = videoEl.value.duration || 0
}

function onVideoEnded() {
  videoPlaying.value = false
  exitVideoMode()
}

function onVideoSeek(e) {
  if (!videoEl.value || !videoDuration.value) return
  const rect = e.currentTarget.getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  videoEl.value.currentTime = percent * videoDuration.value
}

function toggleVideoPlay() {
  if (!videoEl.value) return
  if (videoEl.value.paused) {
    videoEl.value.play()
    videoPlaying.value = true
  } else {
    videoEl.value.pause()
    videoPlaying.value = false
  }
}

function skipVideo(seconds) {
  if (!videoEl.value) return
  videoEl.value.currentTime = Math.max(0, Math.min(videoDuration.value, videoEl.value.currentTime + seconds))
}

onBeforeUnmount(() => {
  if (videoEl.value) videoEl.value.pause()
})

// Seek drag state
const seekDragProgress = ref(null)
const seekWasPlaying = ref(false)

function seekPercentFromEvent(e, el) {
  const rect = el.getBoundingClientRect()
  const clientX = e.touches ? e.touches[0].clientX : e.changedTouches[0].clientX
  return Math.max(0, Math.min(100, ((clientX - rect.left) / rect.width) * 100))
}

function onSeekTouchStart(e) {
  seekWasPlaying.value = playerStore.isPlaying
  if (seekWasPlaying.value) playerStore.pause()
  seekDragProgress.value = seekPercentFromEvent(e, e.currentTarget)
}
function onSeekTouchMove(e) {
  seekDragProgress.value = seekPercentFromEvent(e, e.currentTarget)
}
function onSeekTouchEnd(e) {
  const pct = seekPercentFromEvent(e, e.currentTarget)
  playerStore.seek(pct)
  seekDragProgress.value = null
  if (seekWasPlaying.value) playerStore.play()
}

// Video seek touch
function videoSeekPercentFromEvent(e, el) {
  const rect = el.getBoundingClientRect()
  const clientX = e.touches ? e.touches[0].clientX : e.changedTouches[0].clientX
  return Math.max(0, Math.min(1, (clientX - rect.left) / rect.width))
}
function onVideoSeekTouchStart(e) {
  if (!videoEl.value || !videoDuration.value) return
  videoEl.value.currentTime = videoSeekPercentFromEvent(e, e.currentTarget) * videoDuration.value
}
function onVideoSeekTouchMove(e) {
  if (!videoEl.value || !videoDuration.value) return
  videoEl.value.currentTime = videoSeekPercentFromEvent(e, e.currentTarget) * videoDuration.value
}
function onVideoSeekTouchEnd(e) {
  if (!videoEl.value || !videoDuration.value) return
  videoEl.value.currentTime = videoSeekPercentFromEvent(e, e.currentTarget) * videoDuration.value
}

const playbackSpeeds = [0.5, 0.75, 1, 1.25, 1.5, 2]

function cyclePlaybackSpeed() {
  haptics.light()
  const current = playerStore.playbackRate
  const idx = playbackSpeeds.indexOf(current)
  const nextIdx = (idx + 1) % playbackSpeeds.length
  playerStore.setPlaybackRate(playbackSpeeds[nextIdx])
}

const sleepMinutes = [15, 30, 45, 60]
const showSleepPicker = ref(false)

function toggleSleepTimer() {
  haptics.medium()
  if (sleepTimer.isActive()) {
    sleepTimer.clear()
    window.dispatchEvent(new CustomEvent('ahoy:toast', {
      detail: { message: 'Sleep timer cleared', type: 'info' }
    }))
  } else {
    showSleepPicker.value = !showSleepPicker.value
  }
}

function startSleepTimer(mins) {
  sleepTimer.start(mins, () => {
    playerStore.pause()
  })
  showSleepPicker.value = false
  window.dispatchEvent(new CustomEvent('ahoy:toast', {
    detail: { message: `Sleep timer set for ${mins} minutes`, type: 'success' }
  }))
}

const canShowNowPlayingOverlay = computed(() => {
  if (!canOpenNowPlaying()) return false
  const track = playerStore.currentTrack
  if (!isNowPlayingOpen.value) return false
  if (!track) return true
  return track.type !== 'live_tv' && track.type !== 'show' && track._type !== 'show'
})

function formatTime(seconds) {
  if (!seconds || !isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function onSeek(e) {
  const rect = e.currentTarget.getBoundingClientRect()
  const percent = ((e.clientX - rect.left) / rect.width) * 100
  playerStore.seek(Math.max(0, Math.min(100, percent)))
}

function onBookmark() {
  if (!playerStore.currentTrack) return
  haptics.onBookmark()
  bookmarks.toggle({ ...playerStore.currentTrack, _type: 'track' })
  const saved = bookmarks.isBookmarked(playerStore.currentTrack)
  window.dispatchEvent(new CustomEvent('ahoy:toast', {
    detail: { message: saved ? 'Saved to library' : 'Removed from library', type: 'bookmark' }
  }))
}

function onShare() {
  if (!playerStore.currentTrack) return
  haptics.light()
  shareTrack(playerStore.currentTrack)
}

function goToArtist() {
  const slug = playerStore.currentTrack?.artist_slug
  if (!slug) return
  closeNowPlaying()
  router.push({ name: 'artist-detail', params: { slug } })
}

function onBoost() {
  haptics.medium()
  const slug = playerStore.currentTrack?.artist_slug
  if (!slug) return
  closeNowPlaying()
  router.push({ name: 'artist-detail', params: { slug } })
}


// Swipe to close with live drag feedback
let touchStartY = 0
const dragOffset = ref(0)

const dragStyle = computed(() => {
  if (dragOffset.value <= 0) return {}
  const progress = Math.min(dragOffset.value / 220, 1)
  return {
    transform: `translateY(${dragOffset.value}px)`,
    opacity: 1 - progress * 0.4,
    transition: 'none',
  }
})

function onTouchStart(e) {
  touchStartY = e.touches[0].clientY
  dragOffset.value = 0
}
function onTouchMove(e) {
  const dy = e.touches[0].clientY - touchStartY
  dragOffset.value = Math.max(0, dy)
}
function onTouchEnd(e) {
  const dy = e.changedTouches[0].clientY - touchStartY
  if (dy > 100) {
    closeNowPlaying()
    dragOffset.value = 0
  } else {
    dragOffset.value = 0
  }
}
</script>

<style scoped>
.now-playing-overlay {
  --np-ice-bg:
    linear-gradient(118deg, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0.045) 24%, transparent 25%),
    linear-gradient(242deg, rgba(130, 210, 255, 0.08) 0%, rgba(130, 210, 255, 0.025) 38%, transparent 39%),
    linear-gradient(315deg, rgba(210, 190, 255, 0.07) 0%, rgba(210, 190, 255, 0.02) 44%, transparent 45%),
    linear-gradient(180deg, rgba(245,252,255,0.08), rgba(190,210,235,0.018)),
    rgba(14, 18, 28, 0.12);
  --np-ice-bg-hover:
    linear-gradient(118deg, rgba(255,255,255,0.23) 0%, rgba(255,255,255,0.06) 24%, transparent 25%),
    linear-gradient(242deg, rgba(130, 210, 255, 0.11) 0%, rgba(130, 210, 255, 0.035) 38%, transparent 39%),
    linear-gradient(315deg, rgba(210, 190, 255, 0.1) 0%, rgba(210, 190, 255, 0.03) 44%, transparent 45%),
    linear-gradient(180deg, rgba(245,252,255,0.11), rgba(190,210,235,0.026)),
    rgba(18, 22, 32, 0.16);
  --np-ice-border: rgba(235, 248, 255, 0.14);
  --np-ice-border-hover: rgba(245, 252, 255, 0.24);
  --np-ice-shadow:
    8px 12px 24px rgba(0, 0, 0, 0.22),
    -4px -6px 16px rgba(255, 255, 255, 0.018),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    inset 0 -1px 0 rgba(255, 255, 255, 0.04),
    inset 1px 0 0 rgba(255, 255, 255, 0.055);
  --np-ice-shadow-hover:
    10px 14px 28px rgba(0, 0, 0, 0.25),
    -5px -7px 18px rgba(255, 255, 255, 0.026),
    inset 0 1px 0 rgba(255, 255, 255, 0.25),
    inset 0 -1px 0 rgba(255, 255, 255, 0.05),
    inset 1px 0 0 rgba(255, 255, 255, 0.07);
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(8, 8, 12, 0.82);
  backdrop-filter: blur(48px) saturate(1.8) brightness(0.7);
  -webkit-backdrop-filter: blur(48px) saturate(1.8) brightness(0.7);
  z-index: 10000;
  display: flex;
  flex-direction: column;
  padding: 24px 20px calc(32px + env(safe-area-inset-bottom, 0px));
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

@media (min-width: 769px) {
  .now-playing-overlay {
    padding: 2vh 20px;
    overflow-y: hidden; /* Prevent scrolling on desktop */
    display: flex;
    justify-content: center;
    align-items: center;
  }
}

/* Crank it up further on devices that handle it well */
@supports (backdrop-filter: blur(80px)) {
  .now-playing-overlay {
    background: rgba(6, 6, 10, 0.72);
    backdrop-filter: blur(80px) saturate(2.2) brightness(0.6);
    -webkit-backdrop-filter: blur(80px) saturate(2.2) brightness(0.6);
  }
}

/* Mobile: leave room at bottom for navigation dock */
@media (max-width: 768px) {
  .now-playing-overlay {
    bottom: calc(138px + env(safe-area-inset-bottom, 0px));
  }
}

.np-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  position: relative;
  margin-bottom: 24px;
  width: 100%;
}

@media (min-width: 769px) {
  .np-header {
    margin-bottom: 16px;
    height: 40px;
  }
}

.np-header-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex: 1;
}

.np-header-label {
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 2px;
  color: rgba(255, 255, 255, 0.28);
  font-weight: 700;
}

.np-header-spacer {
  width: 44px; /* Matches minimize btn width for centering */
}

.np-minimize-btn {
  background: var(--np-ice-bg);
  border: 1px solid var(--np-ice-border);
  backdrop-filter: blur(34px) saturate(1.75);
  -webkit-backdrop-filter: blur(34px) saturate(1.75);
  box-shadow: var(--np-ice-shadow);
  border-radius: 12px;
  color: white;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
}

.np-minimize-btn:hover {
  background: var(--np-ice-bg-hover);
  border-color: var(--np-ice-border-hover);
  transform: translateY(-1px) scale(1.025);
  box-shadow: var(--np-ice-shadow-hover);
}

.np-header-handle {
  width: 40px;
  height: 4px;
  background: rgba(255, 255, 255, 0.22);
  border-radius: 2px;
}

.np-content {
  max-width: 600px;
  margin: 0 auto;
  width: 100%;
}

@media (min-width: 769px) {
  .np-content {
    display: flex;
    flex-direction: column;
    justify-content: center;
    min-height: 0;
    max-height: 85vh;
    padding-bottom: 20px;
  }
}

.np-artwork-container {
  aspect-ratio: 1;
  margin-bottom: 30px;
  box-shadow: 0 40px 100px rgba(0,0,0,0.8);
  border-radius: 12px;
  overflow: hidden;
  max-width: 100%;
}

@media (min-width: 769px) {
  .np-artwork-container {
    max-height: 30vh;
    width: auto;
    margin-left: auto;
    margin-right: auto;
    margin-bottom: 18px;
  }
}

.np-artwork {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.np-empty-state {
  min-height: min(520px, 62vh);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 24px;
  text-align: center;
}

.np-empty-artwork {
  width: min(220px, 54vw);
  aspect-ratio: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 24px;
  color: rgba(245, 250, 255, 0.86);
  font-size: 54px;
  background:
    linear-gradient(118deg, rgba(255,255,255,0.16) 0%, rgba(255,255,255,0.045) 24%, transparent 25%),
    linear-gradient(242deg, rgba(130, 210, 255, 0.075) 0%, rgba(130, 210, 255, 0.024) 38%, transparent 39%),
    linear-gradient(315deg, rgba(210, 190, 255, 0.07) 0%, rgba(210, 190, 255, 0.022) 44%, transparent 45%),
    rgba(18, 22, 32, 0.13);
  border: 1px solid rgba(235, 248, 255, 0.14);
  box-shadow:
    14px 20px 44px rgba(0, 0, 0, 0.26),
    -7px -9px 24px rgba(255, 255, 255, 0.018),
    inset 0 1px 0 rgba(255, 255, 255, 0.2),
    inset 0 -1px 0 rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(38px) saturate(1.85);
  -webkit-backdrop-filter: blur(38px) saturate(1.85);
}

.np-empty-info {
  margin-bottom: 0;
}

.np-empty-actions {
  display: flex;
  justify-content: center;
  gap: 10px;
}

.np-empty-link {
  min-width: 106px;
  color: rgba(245, 250, 255, 0.9);
  text-decoration: none;
}

.np-info {
  text-align: center;
  margin-bottom: 30px;
}

@media (min-width: 769px) {
  .np-info {
    margin-bottom: 16px;
  }
  .np-title {
    font-size: 24px;
    margin-bottom: 4px;
  }
  .np-artist {
    font-size: 16px;
  }
}

.np-title {
  font-size: 30px;
  font-weight: 700;
  margin-bottom: 8px;
  color: white;
}

.np-artist {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.7);
}

.np-artist--link {
  cursor: pointer;
  text-decoration: underline;
  text-decoration-color: rgba(255, 255, 255, 0.3);
  text-underline-offset: 3px;
}

.np-artist--link:hover {
  color: white;
  text-decoration-color: rgba(255, 255, 255, 0.7);
}

.np-seek {
  margin-bottom: 30px;
}

@media (min-width: 769px) {
  .np-seek {
    margin-bottom: 16px;
  }
}

.np-seek-bar {
  height: 4px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 2px;
  position: relative;
  cursor: pointer;
  padding: 14px 0;
  margin: -14px 0;
  box-sizing: content-box;
}

.np-seek-fill {
  position: absolute;
  height: 100%;
  background: var(--accent-primary, #6ddcff);
  border-radius: 2px;
}

.np-seek-thumb {
  position: absolute;
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  box-shadow: 0 0 10px rgba(0,0,0,0.5);
}

.np-times {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-top: 8px;
  margin-bottom: 20px;
}

/* Loading Status Indicator */
.np-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 28px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.6);
}

.np-secondary-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 12px;
}

.np-util-btn {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
  padding: 6px 14px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 6px;
  position: relative;
}

.np-util-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.np-util-btn--active {
  background: rgba(109, 220, 255, 0.1);
  border-color: rgba(109, 220, 255, 0.3);
  color: var(--accent-primary, #6ddcff);
}

.sleep-dot {
  width: 5px;
  height: 5px;
  background: var(--accent-primary, #6ddcff);
  border-radius: 50%;
  position: absolute;
  top: 4px;
  right: 6px;
}

.np-util-spacer {
  flex: 1;
  max-width: 40px;
}

.np-popover {
  position: absolute;
  bottom: 220px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(25, 28, 38, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
  padding: 16px;
  z-index: 10001;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  width: 200px;
}

.np-popover-title {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 12px;
  text-align: center;
}

.np-popover-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.np-popover-grid button {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  padding: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.np-popover-grid button:hover {
  background: rgba(109, 220, 255, 0.1);
  border-color: rgba(109, 220, 255, 0.3);
}

.np-btn-skip {
  position: relative;
}

.skip-label {
  position: absolute;
  font-size: 9px;
  font-weight: 800;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  margin-top: 2px;
  color: #fff;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(109, 220, 255, 0.2);
  border-top-color: var(--accent-primary, #6ddcff);
  border-radius: 50%;
  animation: spin-smooth 1s linear infinite;
}

@keyframes spin-smooth {
  to {
    transform: rotate(360deg);
  }
}

.loading-text {
  font-size: 12px;
  opacity: 0.7;
}

.np-controls {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 40px;
  margin-bottom: 40px;
}

@media (min-width: 769px) {
  .np-controls {
    gap: 28px;
    margin-bottom: 20px;
  }
  .np-btn {
    width: 44px;
    height: 44px;
    font-size: 18px;
  }
  .np-btn-play {
    width: 60px;
    height: 60px;
    font-size: 24px;
  }
}

.np-btn,
.np-action-btn {
  position: relative;
  overflow: hidden;
  isolation: isolate;
  background:
    linear-gradient(118deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.012) 24%, transparent 25%),
    linear-gradient(180deg, rgba(245,252,255,0.022), rgba(190,210,235,0.004)),
    rgba(14, 18, 28, 0.03);
  border: 1px solid rgba(235, 248, 255, 0.06);
  backdrop-filter: blur(14px) saturate(1.3);
  -webkit-backdrop-filter: blur(14px) saturate(1.3);
  box-shadow:
    0 6px 18px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  color: rgba(245, 250, 255, 0.7);
  cursor: pointer;
  transition:
    transform 0.18s cubic-bezier(0.2, 0.9, 0.2, 1),
    background 0.2s ease,
    box-shadow 0.2s ease,
    border-color 0.2s ease,
    color 0.2s ease;
}

.np-btn::before,
.np-action-btn::before {
  content: "";
  position: absolute;
  inset: 1px 3px auto;
  height: 38%;
  border-radius: inherit;
  background: linear-gradient(154deg, rgba(255,255,255,0.08), rgba(255,255,255,0.015) 48%, transparent 49%);
  opacity: 0.35;
  pointer-events: none;
  z-index: -1;
}

.np-minimize-btn::before {
  content: "";
  position: absolute;
  inset: 1px 3px auto;
  height: 38%;
  border-radius: inherit;
  background: linear-gradient(154deg, rgba(255,255,255,0.16), rgba(255,255,255,0.035) 48%, transparent 49%);
  opacity: 0.56;
  pointer-events: none;
  z-index: -1;
}

.np-btn {
  border-radius: 50%;
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
}

.np-btn:active {
  animation: ice-press 210ms cubic-bezier(0.2, 0.9, 0.2, 1);
}

.np-btn--active {
  color: #dff7ff;
  border-color: rgba(180, 235, 255, 0.38);
  box-shadow:
    var(--np-ice-shadow),
    0 0 20px rgba(118, 214, 255, 0.16);
}

.np-btn-play {
  font-size: 28px;
  width: 68px;
  height: 68px;
  background:
    linear-gradient(160deg, rgba(255,255,255,0.13) 0%, rgba(255,255,255,0.03) 50%, transparent 51%),
    rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.95);
  box-shadow:
    0 8px 28px rgba(0, 0, 0, 0.22),
    0 0 0 1px rgba(255, 255, 255, 0.06),
    inset 0 1px 0 rgba(255, 255, 255, 0.22),
    inset 0 -1px 0 rgba(0, 0, 0, 0.12);
}

.np-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 40px;
}

@media (min-width: 769px) {
  .np-actions {
    margin-bottom: 0;
  }
}

.np-action-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  min-width: 56px;
  height: 54px;
  padding: 0 14px;
  border-radius: 12px;
  font-size: 16px;
}

.np-action-label {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.4px;
  color: rgba(255, 255, 255, 0.45);
  text-transform: uppercase;
  line-height: 1;
}

.np-action-btn:hover .np-action-label {
  color: rgba(255, 255, 255, 0.7);
}

.np-btn:hover,
.np-action-btn:hover {
  background:
    linear-gradient(118deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.025) 24%, transparent 25%),
    linear-gradient(180deg, rgba(245,252,255,0.04), rgba(190,210,235,0.008)),
    rgba(18, 22, 32, 0.06);
  border-color: rgba(245, 252, 255, 0.14);
  color: rgba(255, 255, 255, 0.95);
  transform: translateY(-1px);
  box-shadow:
    0 10px 24px rgba(0, 0, 0, 0.16),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.np-action-btn:active {
  animation: ice-press 210ms cubic-bezier(0.2, 0.9, 0.2, 1);
  color: white;
}

.np-action-btn--boost {
  border-color: rgba(255, 226, 156, 0.24);
  color: rgba(255, 236, 190, 0.9);
}

.np-action-btn--boost:hover {
  border-color: rgba(255, 226, 156, 0.4);
  color: #fff5d5;
}

.np-action-btn--save {
  border-color: rgba(255, 180, 220, 0.24);
  color: rgba(255, 220, 240, 0.9);
}

.np-action-btn--save:hover {
  border-color: rgba(255, 180, 220, 0.4);
  color: #ffeaf5;
}

/* Transitions */
.overlay-slide-enter-active,
.overlay-slide-leave-active {
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.overlay-slide-enter-from,
.overlay-slide-leave-to {
  transform: translateY(100%);
}

@media (max-width: 768px) {
  .np-header {
    margin-bottom: 12px;
  }
  .np-content {
    display: flex;
    flex-direction: column;
  }
  .np-header-center {
    gap: 7px;
  }
  .np-header-label {
    color: rgba(255, 255, 255, 0.24);
  }
  .np-content {
    padding: 0 8px;
  }
  /* Compact artwork — cap size so everything fits without scrolling */
  .np-artwork-container {
    width: min(300px, 74vw);
    margin: -4px auto 14px;
  }
  .np-info {
    margin-bottom: 14px;
  }
  .np-title {
    font-size: 22px;
    margin-bottom: 4px;
  }
  .np-artist {
    font-size: 15px;
  }
  .np-seek {
    margin-bottom: 8px;
  }
  .np-times {
    margin-bottom: 12px;
  }
  .np-loading {
    margin-bottom: 16px;
    gap: 8px;
  }
  .loading-status-text {
    font-size: 11px;
  }
  .np-controls {
    gap: 8px;
    margin-bottom: 12px;
    order: 1;
  }
  .np-actions {
    gap: 8px;
    margin-bottom: 10px;
    order: 2;
  }
  .np-secondary-controls {
    gap: 8px;
    margin-bottom: 10px;
    order: 3;
  }
  .np-util-btn {
    padding: 4px 10px;
    font-size: 11px;
    min-height: 28px;
  }
  .np-util-spacer {
    display: none;
  }
  .np-btn {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  .np-btn-play {
    width: 54px;
    height: 54px;
    font-size: 22px;
  }
  .np-action-btn {
    min-width: 42px;
    height: 48px;
    padding: 0 8px;
    font-size: 13px;
  }
  .np-popover {
    bottom: 190px;
    width: 176px;
    padding: 12px;
  }
  .np-popover-grid {
    gap: 6px;
  }
  .np-popover-grid button {
    padding: 8px 6px;
    font-size: 12px;
  }
}

.np-btn-play:hover {
  transform: translateY(-1px);
  color: #ffffff;
  border-color: rgba(255, 255, 255, 0.3);
  background:
    linear-gradient(160deg, rgba(255,255,255,0.18) 0%, rgba(255,255,255,0.05) 50%, transparent 51%),
    rgba(255, 255, 255, 0.11);
  box-shadow:
    0 12px 32px rgba(0, 0, 0, 0.26),
    0 0 0 1px rgba(255, 255, 255, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.28),
    inset 0 -1px 0 rgba(0, 0, 0, 0.14);
}

@keyframes ice-press {
  0% {
    transform: translateY(0) scale(1);
    filter: brightness(1);
  }
  45% {
    transform: translateY(2px) scale(0.965, 0.94);
    filter: brightness(1.12);
  }
  100% {
    transform: translateY(0) scale(1);
    filter: brightness(1);
  }
}
.np-artwork-container {
  transition: transform 0.3s ease;
  position: relative;
}
.np-artwork-container:hover {
  transform: scale(1.02);
}
.np-artwork-container--video {
  aspect-ratio: 16/9;
  transform: none !important;
  border-radius: 12px;
  overflow: hidden;
  background: #000;
}
.np-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  cursor: pointer;
}
.np-video-loading {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.45);
  border-radius: 12px;
  pointer-events: none;
}
.np-info--compact {
  margin-bottom: 10px;
}
.np-info--compact .np-title {
  font-size: 16px;
  margin-bottom: 0;
}
.np-content--video .np-artwork-container {
  margin-bottom: 12px;
}
/* Header watch button — inline with "Now Playing ·" label */
.np-header-watch-btn {
  background: rgba(180, 140, 255, 0.15);
  border: 1px solid rgba(180, 140, 255, 0.3);
  color: #c4aaff;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 700;
  padding: 3px 9px;
  cursor: pointer;
  letter-spacing: 0.5px;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  vertical-align: middle;
}
.np-header-watch-btn:hover {
  background: rgba(180, 140, 255, 0.25);
  border-color: rgba(180, 140, 255, 0.5);
  color: #ddd0ff;
}
</style>
