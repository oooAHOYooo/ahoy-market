<template>
  <div class="now-playing-wrapper" :class="{ 'has-player': !!playerStore.currentTrack, 'ejecting': ejecting, 'is-idle': isIdle }">
    <div
      class="now-playing-glass now-playing-sticky"
      :class="{ 'now-playing-is-playing': playerStore.currentTrack && playerStore.isPlaying }"
    >
      <div class="desktop-layout-wrapper" style="width: 100%;">


      <div class="now-playing-container">
        <!-- Left: Album art + track info -->
        <div class="now-playing-left">
          <div
            class="now-playing-album-art"
            @click="playerStore.currentTrack ? goToNowPlaying() : null"
          >
            <template v-if="playerStore.currentTrack">
              <img
                :src="playerStore.currentTrack.cover_art || playerStore.currentTrack.thumbnail || playerStore.currentTrack.artwork || '/static/img/default-cover.jpg'"
                :alt="playerStore.currentTrack.title"
                class="now-playing-album-img"
                :class="{ spinning: playerStore.isPlaying, 'art-playing-glow': playerStore.isPlaying }"
              />
              <div v-if="!playerStore.isPlaying" class="now-playing-album-overlay">
                <i class="fas fa-play"></i>
              </div>
            </template>
            <template v-else>
              <div class="now-playing-empty-art">
                <i class="fas fa-music"></i>
              </div>
            </template>
          </div>
          
          <div class="now-playing-info">
            <template v-if="playerStore.currentTrack">
              <div class="now-playing-title-row">
                <button
                  type="button"
                  class="now-playing-btn now-playing-expand-btn mobile-only"
                  title="Full player"
                  @click="goToNowPlaying"
                  v-if="playerStore.currentTrack"
                >
                  <i class="fas fa-chevron-up"></i>
                </button>
                <div
                  class="now-playing-title now-playing-title-link"
                  :title="displayTitle"
                  @click="goToNowPlaying"
                >{{ displayTitle }}</div>
                <div v-if="(playerStore.currentTrack?.type === 'live_tv' || isRadioSource) && playerStore.isPlaying" class="now-playing-live-tag" :class="{ 'live-tag-radio': isRadioSource }">
                   <span class="live-dot"></span> LIVE
                </div>
              </div>

              <div class="now-playing-secondary">
                <span
                  class="now-playing-artist now-playing-artist-link"
                  :title="displayArtist"
                  @click="goToNowPlaying"
                >{{ displayArtist }}</span>
                <span class="category-pill" :class="{ 'radio-pill': isRadioSource }">
                  <i class="fas" :class="isRadioSource ? 'fa-broadcast-tower' : 'fa-music'"></i> {{ trackTypeLabel }}
                </span>
                <span v-if="playerStore.currentTrack?.video_url" class="category-pill video-pill" @click.stop="goToNowPlaying" title="Video available">
                  <i class="fas fa-video"></i> Watch
                </span>
              </div>
            </template>
            <template v-else>
              <div class="now-playing-title now-playing-empty-title">Start listening</div>
              <div class="now-playing-artist now-playing-empty-artist">
                Pick <router-link to="/music" class="now-playing-empty-link">music</router-link>,
                <router-link to="/podcasts" class="now-playing-empty-link">podcasts</router-link>, or
                <router-link to="/radio" class="now-playing-empty-link">radio</router-link>
              </div>
            </template>
          </div>

          </div>

        <!-- Center: Transport (Spotify-style) -->
        <div class="now-playing-transport">
          <div class="now-playing-transport-controls">
            <button
              v-if="!isRadioSource"
              type="button"
              class="now-playing-btn"
              :class="{ disabled: !playerStore.currentTrack }"
              :disabled="!playerStore.currentTrack"
              title="Rewind"
              @click="onSeekBack"
            >
              <i class="fas fa-step-backward"></i>
            </button>
            <button
              type="button"
              class="now-playing-btn now-playing-play-btn"
              :class="{ disabled: !playerStore.currentTrack, loading: playerStore.loading, 'radio-play-btn': isRadioSource }"
              :disabled="!playerStore.currentTrack"
              :title="playButtonTitle"
              @click="onTogglePlay"
            >
              <i v-if="playerStore.loading" class="fas fa-spinner fa-spin"></i>
              <i v-else :class="playButtonIcon"></i>
            </button>
            <button
              v-if="!isRadioSource"
              type="button"
              class="now-playing-btn"
              :class="{ disabled: !playerStore.currentTrack }"
              :disabled="!playerStore.currentTrack"
              title="Fast forward"
              @click="onSeekForward"
            >
              <i class="fas fa-step-forward"></i>
            </button>
          </div>
          <div
            v-if="canScrubTimeline"
            class="now-playing-scrub"
            :title="`${formatTime(playerStore.currentTime)} / ${formatTime(playerStore.duration)}`"
          >
            <span class="now-playing-scrub-time">{{ formatTime(playerStore.currentTime) }}</span>
            <input
              type="range"
              class="now-playing-scrub-range"
              min="0"
              max="100"
              step="0.1"
              :value="timelineProgress"
              :style="{ '--scrub-progress': `${timelineProgress}%` }"
              aria-label="Playback timeline"
              @input="onTimelineInput"
            />
            <span class="now-playing-scrub-time">{{ formatTime(playerStore.duration) }}</span>
          </div>
        </div>

        <!-- Right: Action buttons + master volume -->
        <div class="now-playing-actions-wrap">
          <div class="now-playing-actions">
            <button
              v-if="!isRadioSource"
              type="button"
              class="now-playing-btn"
              :class="{ active: playerStore.shuffle, disabled: !playerStore.currentTrack }"
              :disabled="!playerStore.currentTrack"
              title="Shuffle"
              @click="onToggleShuffle"
            >
              <i class="fas fa-random"></i>
            </button>
            <button
              v-if="!isRadioSource"
              type="button"
              class="now-playing-btn"
              :class="{ active: playerStore.repeat, disabled: !playerStore.currentTrack }"
              :disabled="!playerStore.currentTrack"
              title="Repeat"
              @click="onToggleRepeat"
            >
              <i class="fas fa-redo"></i>
            </button>
            <button
              type="button"
              class="now-playing-btn now-playing-action-btn boost-btn-mini"
              :class="{ disabled: !playerStore.currentTrack }"
              :disabled="!playerStore.currentTrack"
              title="Boost artist"
              @click="goToBoost()"
            >
              <i class="fas fa-bolt"></i>
            </button>
            <button
              type="button"
              class="now-playing-btn now-playing-action-btn save-btn-mini"
              :class="{ active: isBookmarked, disabled: !playerStore.currentTrack }"
              :disabled="!playerStore.currentTrack"
              title="Bookmark"
              @click="toggleBookmark"
            >
              <i :class="isBookmarked ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
            </button>
            <button
              type="button"
              class="now-playing-btn now-playing-action-btn"
              :class="{ disabled: !playerStore.currentTrack }"
              :disabled="!playerStore.currentTrack"
              title="Fullscreen"
              @click="onToggleFullscreen"
            >
              <i class="fas fa-expand"></i>
            </button>
            <button
              type="button"
              class="now-playing-btn now-playing-action-btn now-playing-volume-mobile-btn"
              :title="playerStore.isMuted ? 'Unmute' : 'Volume'"
              @click="onToggleMute"
            >
              <i :class="volumeIconClass"></i>
            </button>
            <div v-if="!isRadioSource" class="now-playing-queue-wrap">
              <button
              type="button"
              class="now-playing-btn now-playing-action-btn now-playing-queue-btn queue-btn-mini"
              :class="{ active: showQueue }"
              title="Queue"
              @click="showQueue = !showQueue"
              >
                <i class="fas fa-list"></i>
                <span v-if="playerStore.queue.length" class="queue-badge">{{ playerStore.queue.length }}</span>
              </button>
              <!-- Queue panel -->
            <div v-if="showQueue" class="queue-panel-backdrop" @click="showQueue = false"></div>
            <Transition name="slide-up">
            <div
              v-if="showQueue"
              class="now-playing-queue-panel"
              @click.stop
            >
              <div class="queue-header">
                <div class="queue-header-left">
                  <h4>Up Next</h4>
                </div>
                <div class="queue-header-actions">
                  <button
                    v-if="playerStore.queue.length"
                    type="button"
                    class="queue-play-all-btn"
                    title="Play all from start"
                    @click="playerStore.setQueue(playerStore.queue, 0); showQueue = false"
                  >
                    <i class="fas fa-play"></i> Play All
                  </button>
                  <button
                    v-if="playerStore.queue.length"
                    type="button"
                    class="queue-clear-btn"
                    title="Clear queue"
                    @click="playerStore.clearQueue()"
                  >
                    <i class="fas fa-trash-alt"></i>
                  </button>
                </div>
              </div>
              <div v-if="playerStore.queue.length" class="queue-list">
                <div
                  v-for="(item, index) in playerStore.queue"
                  :key="index"
                  class="queue-item"
                  @click="playFromQueue(index)"
                >
                  <img
                    :src="item.cover_art || item.thumbnail || item.artwork || '/static/img/default-cover.jpg'"
                    :alt="item.title"
                    class="queue-item-art"
                  />
                  <div class="queue-item-info">
                    <div class="queue-item-title">{{ item.title }}</div>
                    <div class="queue-item-artist">{{ item.artist || item.host || '' }}</div>
                  </div>
                  <button
                    type="button"
                    class="queue-item-remove"
                    title="Remove"
                    @click.stop="onRemoveFromQueue(index)"
                  >
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
              <div v-else class="queue-empty">
                <i class="fas fa-music"></i>
                <p>Queue is empty</p>
              </div>
            </div>
            </Transition>
          </div>
            <button
              v-if="playerStore.currentTrack"
              type="button"
              class="now-playing-btn now-playing-action-btn now-playing-eject-btn"
              :class="{ 'active-glow': playerStore.isPlaying }"
              title="Eject"
              aria-label="Eject track"
              @click.stop="onEject"
            >
              <i class="fas fa-eject"></i>
            </button>
          </div>
          <!-- Minimize toggle (always visible) -->
          <div class="now-playing-volume-wrap">
            <button
              type="button"
              class="now-playing-btn now-playing-volume-btn"
              :title="playerStore.isMuted ? 'Unmute' : 'Mute'"
              @click="onToggleMute"
            >
              <i :class="volumeIconClass"></i>
            </button>
            <input
              type="range"
              class="now-playing-volume"
              min="0"
              max="100"
              :value="playerStore.volume"
              @input="onVolumeChange($event.target.value)"
              title="Volume"
            />
          </div>
        </div>
      </div>
      </div>

      <!-- Mobile Player -->
      <div class="mobile-layout-wrapper" style="width: 100%;">


      <div class="now-playing-container mobile-slot-2">
        <!-- ROW 2: Meta Row / Empty State CTA -->
        <div class="slot-2-meta" @click="goToNowPlaying">
          <div class="slot-2-art" :class="{ 'playing-glow': playerStore.isPlaying }">
            <img
              v-if="playerStore.currentTrack"
              :src="playerStore.currentTrack.cover_art || playerStore.currentTrack.thumbnail || '/static/img/default-cover.jpg'"
              class="slot-2-img"
            />
            <div v-else class="slot-2-empty-art"><i class="fas fa-play-circle"></i></div>
          </div>
          <div class="slot-2-info">
            <template v-if="playerStore.currentTrack">
              <div class="slot-2-title-row">
                <div class="slot-2-title neon-text">{{ displayTitle }}</div>
                <div
                  v-if="canScrubTimeline"
                  class="slot-2-scrub"
                  :title="`${formatTime(playerStore.currentTime)} / ${formatTime(playerStore.duration)}`"
                  @click.stop
                >
                  <input
                    type="range"
                    class="slot-2-scrub-range"
                    min="0"
                    max="100"
                    step="0.1"
                    :value="timelineProgress"
                    :style="{ '--scrub-progress': `${timelineProgress}%` }"
                    aria-label="Playback timeline"
                    @input="onTimelineInput"
                  />
                </div>
                <button
                  type="button"
                  class="now-playing-btn now-playing-open-player-btn"
                  title="Open full player"
                  aria-label="Open full player"
                  @click.stop="goToNowPlaying"
                >
                  <i class="fas fa-chevron-up"></i>
                </button>
              </div>
              <div class="slot-2-secondary-row">
                <div class="slot-2-artist">{{ displayArtist }}</div>
              </div>
              <div v-if="isRadioSource" class="slot-2-live-row">
                <span class="slot-2-live-pill"><i class="fas fa-broadcast-tower"></i> Live Radio</span>
              </div>
            </template>
            <template v-else>
              <div class="slot-2-explore neon-text">
                Discover
                <router-link to="/music" class="slot-2-explore-link" @click.stop>Music</router-link>,
                <router-link to="/podcasts" class="slot-2-explore-link" @click.stop>Podcasts</router-link>,
                &
                <router-link to="/radio" class="slot-2-explore-link" @click.stop>Radio</router-link>
              </div>
              <div class="slot-2-sub-prompt">Select a track to start listening</div>
            </template>
          </div>
        </div>

        <!-- ROW 3: Dense Control Board -->
        <div class="slot-2-controls">
          <div class="control-group-left">
            <button v-if="!isRadioSource" type="button" class="now-playing-btn" :disabled="!playerStore.currentTrack" @click="onSeekBack" :style="{ opacity: playerStore.currentTrack ? 1 : 0.4 }">
              <i class="fas fa-step-backward"></i>
            </button>
            <button type="button" class="now-playing-btn neon-play-liquid" :class="{ 'is-playing': playerStore.isPlaying, 'radio-play-btn': isRadioSource }" @click="onTogglePlay" :disabled="!playerStore.currentTrack" :style="{ opacity: playerStore.currentTrack ? 1 : 0.6 }">
              <i :class="playButtonIcon"></i>
            </button>
            <button v-if="!isRadioSource" type="button" class="now-playing-btn" :disabled="!playerStore.currentTrack" @click="onSeekForward" :style="{ opacity: playerStore.currentTrack ? 1 : 0.4 }">
              <i class="fas fa-step-forward"></i>
            </button>
            <button type="button" class="now-playing-btn save-btn-mini" :class="{ active: isBookmarked }" @click="toggleBookmark" :disabled="!playerStore.currentTrack" :style="{ opacity: playerStore.currentTrack ? 1 : 0.4 }">
              <i :class="isBookmarked ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
            </button>
            <button type="button" class="now-playing-btn" @click="onToggleMute">
              <i :class="volumeIconClass"></i>
            </button>
            <button type="button" class="now-playing-btn" :disabled="!playerStore.currentTrack" @click.stop="onToggleFullscreen" :style="{ opacity: playerStore.currentTrack ? 1 : 0.4 }" title="Fullscreen">
              <i class="fas fa-expand"></i>
            </button>
            <button v-if="playerStore.currentTrack" type="button" class="now-playing-btn neon-eject-dynamic" :class="{ 'active-playing': playerStore.isPlaying }" @click.stop="onEject">
              <i class="fas fa-eject"></i>
            </button>
          </div>

        </div>
      </div>
      </div>

        </div>
    <!-- Cast Modal -->
    <CastModal v-model="showCastModal" />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '../stores/player'
import { useBookmarks } from '../composables/useBookmarks'
import { useHaptics } from '../composables/useNative'
import { useCasting } from '../composables/useCasting'
import { useOverlay } from '../composables/useOverlay'
import CastModal from './CastModal.vue'

const router = useRouter()
const playerStore = usePlayerStore()
const bookmarks = useBookmarks()
const haptics = useHaptics()
const casting = useCasting()
const { openNowPlaying, closeNowPlaying } = useOverlay()

const showQueue = ref(false)
const showCastModal = ref(false)

const isCastAvailable = computed(() => casting.isCastingAvailable.value)
const ejecting = ref(false)
const isIdle = ref(false)
let idleTimer = null

function resetIdleTimer() {
  isIdle.value = false
  if (idleTimer) clearTimeout(idleTimer)
  // Disabled auto-hide for better persistent visibility
}

watch(() => playerStore.isPlaying, (playing) => {
  if (playing) {
    isIdle.value = false
    if (idleTimer) clearTimeout(idleTimer)
  } else {
    resetIdleTimer()
  }
}, { immediate: true })

watch(() => playerStore.currentTrack, (track) => {
  if (!track) {
    isIdle.value = false
    if (idleTimer) {
      clearTimeout(idleTimer)
      idleTimer = null
    }
  }
})


function handleGlobalInteraction() {
  resetIdleTimer()
}

onMounted(() => {
  window.addEventListener('mousemove', handleGlobalInteraction)
  window.addEventListener('touchstart', handleGlobalInteraction)
  window.addEventListener('keydown', handleGlobalInteraction)
})

onUnmounted(() => {
  window.removeEventListener('mousemove', handleGlobalInteraction)
  window.removeEventListener('touchstart', handleGlobalInteraction)
  window.removeEventListener('keydown', handleGlobalInteraction)
  if (idleTimer) clearTimeout(idleTimer)
})

const isMobile = computed(() => window.innerWidth <= 1024)

const isVideo = computed(() => {
  const t = playerStore.currentTrack
  if (!t) return false
  return t.type === 'show' || t._type === 'show' || t.type === 'live_tv'
})

const videoRoute = computed(() => {
  const t = playerStore.currentTrack
  if (!t) return null
  if (t.host_slug && t.id) return `/videos/${t.host_slug}/${t.id}`
  if (t.id) return `/videos/${t.id}`
  return null
})



const displayTitle = computed(() => {
  const t = playerStore.currentTrack
  if (!t) return ''
  return t.title || t.name || 'Unknown track'
})

const displayArtist = computed(() => {
  const t = playerStore.currentTrack
  if (!t) return ''
  return t.artist || t.artist_name || t.artistName || t.creator || t.author || t.host || t.performer || t.metadata?.artist || 'Unknown Artist'
})

const trackTypeLabel = computed(() => {
  const t = playerStore.currentTrack
  if (!t) return 'Music'
  if (playerStore.playbackSource === 'radio') return 'Live Radio'
  if (t.type === 'podcast' || t._type === 'podcast') return 'Podcast'
  if (t.type === 'show' || t._type === 'show') return 'Video'
  return 'Music'
})

const isRadioSource = computed(() => playerStore.playbackSource === 'radio' && !!playerStore.currentTrack)

const canScrubTimeline = computed(() => (
  !!playerStore.currentTrack &&
  Number.isFinite(playerStore.duration) &&
  playerStore.duration > 0
))

const timelineProgress = computed(() => {
  if (!canScrubTimeline.value) return 0
  return Math.max(0, Math.min(100, (playerStore.currentTime / playerStore.duration) * 100))
})

const playButtonIcon = computed(() => {
  if (playerStore.loading) return 'fas fa-spinner fa-spin'
  if (isRadioSource.value) return playerStore.isMuted ? 'fas fa-volume-xmark' : 'fas fa-volume-high'
  return playerStore.isPlaying ? 'fas fa-pause' : 'fas fa-play'
})

const playButtonTitle = computed(() => {
  if (playerStore.loading) return 'Loading...'
  if (isRadioSource.value) return playerStore.isMuted ? 'Unmute radio' : 'Mute radio'
  return playerStore.isPlaying ? 'Pause' : 'Play'
})

const isBookmarked = computed(() =>
  playerStore.currentTrack ? bookmarks.isBookmarked(playerStore.currentTrack) : false
)

const volumeIconClass = computed(() => {
  if (playerStore.isMuted) return 'fas fa-volume-mute'
  if (playerStore.volume > 50) return 'fas fa-volume-up'
  if (playerStore.volume > 0) return 'fas fa-volume-down'
  return 'fas fa-volume-off'
})

function onTogglePlay() {
  haptics.onPlay()
  if (isRadioSource.value) {
    playerStore.toggleMute()
    return
  }
  playerStore.togglePlay()
}

function toggleBookmark() {
  if (playerStore.currentTrack) {
    bookmarks.toggle(playerStore.currentTrack)
    haptics.success?.() // Easy win: subtle vibration on bookmark
    haptics.onBookmark?.()
  }
}

function onToggleMute() {
  haptics.onToggle()
  playerStore.toggleMute()
}

function onVolumeChange(value) {
  haptics.onVolumeChange()
  playerStore.setVolume(parseInt(value, 10))
}

function formatTime(seconds) {
  if (!Number.isFinite(seconds) || seconds <= 0) return '0:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

function onTimelineInput(event) {
  if (!canScrubTimeline.value) return
  playerStore.seek(Math.max(0, Math.min(100, Number(event.target.value) || 0)))
}

const API_BASE = import.meta.env.VITE_API_BASE || 'https://app.ahoy.ooo'

function goToBoost() {
  if (!playerStore.currentTrack) return
  haptics.onBoost()
  const slug = playerStore.currentTrack?.artist_slug
  if (!slug) return
  closeNowPlaying()
  router.push({ name: 'artist-detail', params: { slug } })
}

function goToNowPlaying() {
  const t = playerStore.currentTrack
  // Radio, AHOY TV, and video shows stay in their own surfaces.
  if (playerStore.playbackSource === 'radio') return
  if (t && (t.type === 'live_tv' || t.type === 'show' || t._type === 'show')) return
  openNowPlaying()
}

function goToArtist() {
  const t = playerStore.currentTrack
  if (!t) return
  const slug = t.artist_slug || t.artist_name_slug || t.host_slug
  if (slug) {
    router.push(`/artists/${slug}`)
  }
}

function onShare() {
  if (!playerStore.currentTrack) return
  const track = playerStore.currentTrack
  const url = `${window.location.origin}/#/music?track=${track.id}`
  
  navigator.clipboard.writeText(url).then(() => {
    haptics.light()
    window.dispatchEvent(new CustomEvent('ahoy:toast', {
      detail: { message: 'Link copied to clipboard!', type: 'success' }
    }))
  })
}

function onEject() {
  if (!playerStore.currentTrack || ejecting.value) return
  haptics.medium()
  ejecting.value = true
  setTimeout(() => {
    playerStore.eject()
    ejecting.value = false
  }, 160)
}

function playFromQueue(index) {
  const list = playerStore.queue
  if (list[index]) playerStore.play(list[index])
  showQueue.value = false
}

function onPrevious() {
  haptics.onSkip()
  playerStore.seekBackward?.()
}

function onNext() {
  haptics.onSkip()
  playerStore.seekForward?.()
}

function onSeekBack() {
  haptics.onSkip()
  playerStore.seekBackward?.()
}

function onSeekForward() {
  haptics.onSkip()
  playerStore.seekForward?.()
}

function onToggleFullscreen() {
  haptics.light?.()
  playerStore.toggleFullscreen?.()
}

function onToggleShuffle() {
  haptics.onToggle()
  playerStore.shuffle = !playerStore.shuffle
}

function onToggleRepeat() {
  haptics.onToggle()
  playerStore.repeat = !playerStore.repeat
}

function onRemoveFromQueue(index) {
  haptics.onRemove()
  playerStore.removeFromQueue(index)
}

// Click-outside to close queue: overlay when panel is open
</script>

<style scoped>
.now-playing-queue-wrap {
  position: relative;
  z-index: 1001;
}

:deep(.now-playing-queue-btn) {
  position: relative;
  z-index: 1002;
}
.queue-panel-backdrop {
  position: fixed;
  inset: 0;
  z-index: 998;
}
.now-playing-queue-panel {
  z-index: 1000;
}

/* Minimize button built into the now-playing bar */
.now-playing-glass {
  position: relative;
}



/* Title / artist: click to open Now Playing */
.now-playing-title-link,
.now-playing-artist-link {
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.now-playing-title-link:hover,
.now-playing-artist-link:hover {
  color: var(--accent-primary, #6ddcff);
  text-shadow: 0 0 8px rgba(109, 220, 255, 0.4);
  opacity: 1;
}

@keyframes timeline-pulse {
  0% { box-shadow: 0 0 8px rgba(139, 123, 168, 0.4); }
  50% { box-shadow: 0 0 16px rgba(139, 123, 168, 0.8); }
  100% { box-shadow: 0 0 8px rgba(139, 123, 168, 0.4); }
}

.now-playing-is-playing .np-timeline-fill {
  animation: timeline-pulse 2.5s infinite ease-in-out;
}

/* Eject: Nintendo cartridge pop — track “pops out” then clears */
.now-playing-wrapper.ejecting .now-playing-left {
  animation: cartridge-eject 0.16s cubic-bezier(0.34, 1.56, 0.64, 1) forwards;
}

@keyframes cartridge-eject {
  0% {
    transform: translateY(0) scale(1);
    opacity: 1;
  }
  100% {
    transform: translateY(12px) scale(0.9);
    opacity: 0;
  }
}

/* Collapsed state: handled in app.css on mobile (strip on top of dock). Desktop never collapsed. */
.now-playing-wrapper {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease;
}

.now-playing-wrapper.is-idle {
  transform: translateY(100%);
  opacity: 0;
  pointer-events: none;
}

/* Hide cast button on desktop */
@media (min-width: 1025px) {
  :deep(.now-playing-cast-btn) {
    display: none !important;
  }
}





@media (max-width: 1024px) {
  .np-timeline {
    display: none !important;
  }
}

/* Timeline scrubber */
.np-timeline {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  padding: 0 !important;
  user-select: none !important;
  -webkit-user-select: none !important;
  flex-shrink: 0 !important;
  height: 6px !important;
  background: rgba(255, 255, 255, 0.05) !important;
  z-index: 10 !important;
}

.np-time {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.5);
  font-variant-numeric: tabular-nums;
  min-width: 32px;
  flex-shrink: 0;
}

.np-time-current {
  text-align: right;
}

.np-time-duration {
  text-align: left;
}

.np-timeline-track {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.12);
  border-radius: 2px;
  position: relative;
  cursor: pointer;
}

.np-timeline-track:hover {
  height: 6px;
}

.np-timeline-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--snes-purple, #6b5b95), var(--snes-purple-bright, #8b7ba8));
  border-radius: 2px;
  pointer-events: none;
  box-shadow: 0 0 8px rgba(139, 123, 168, 0.4);
}

.np-timeline-thumb {
  position: absolute;
  top: 50%;
  width: 12px;
  height: 12px;
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
  transform: translate(-50%, -50%);
  opacity: 0;
  transition: opacity 0.15s ease;
  pointer-events: none;
}

.np-timeline:hover .np-timeline-thumb,
.np-timeline:active .np-timeline-thumb {
  opacity: 1;
}

.np-video-link {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.6);
  font-size: 10px;
  text-decoration: none;
  transition: all 0.2s ease;
  margin-left: 2px;
}

.np-video-link:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #fff;
  transform: translateY(-1px);
}

/* Enhancing global play and action buttons inside scoped context */
:deep(.now-playing-btn) {
  width: 44px !important;
  height: 44px !important;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03)) !important;
  backdrop-filter: blur(25px) !important;
  -webkit-backdrop-filter: blur(25px) !important;
  border: 1px solid rgba(255, 255, 255, 0.18) !important;
  color: #fff !important;
  border-radius: 12px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 16px !important;
  transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4), inset 0 0 1px rgba(255,255,255,0.2) !important;
}

:deep(.now-playing-btn:not(:disabled):hover) {
  transform: translateY(-4px) scale(1.1);
  background: rgba(255, 255, 255, 0.14) !important;
  border-color: rgba(255, 255, 255, 0.4) !important;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5), 0 0 15px rgba(255,255,255,0.1) !important;
}

:deep(.now-playing-btn:not(:disabled):active) {
  transform: scale(0.92);
  transition-duration: 0.1s !important;
}

/* Distinct Action Button Styles */
:deep(.boost-btn-mini) {
  border-color: rgba(255, 200, 0, 0.3) !important;
  color: rgba(255, 200, 0, 0.8) !important;
}
:deep(.boost-btn-mini:not(:disabled):hover) {
  border-color: rgba(255, 200, 0, 0.5) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.18) !important;
  background: rgba(255, 200, 0, 0.1) !important;
  color: rgba(255, 200, 0, 1) !important;
}

:deep(.save-btn-mini) {
  border-color: rgba(255, 0, 96, 0.3) !important;
  color: rgba(255, 0, 96, 0.8) !important;
  mix-blend-mode: screen;
}
:deep(.save-btn-mini.active),
:deep(.save-btn-mini:not(:disabled):hover) {
  border-color: rgba(255, 0, 96, 0.5) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.4), inset 0 1px 0 rgba(255,255,255,0.18) !important;
  background: rgba(255, 0, 96, 0.1) !important;
  color: rgba(255, 0, 96, 1) !important;
}

:deep(.queue-btn-mini) {
  border-color: rgba(0, 229, 255, 0.3) !important;
  color: #00e5ff !important;
}
:deep(.queue-btn-mini.active),
:deep(.queue-btn-mini:not(:disabled):hover) {
  border-color: #00e5ff !important;
  box-shadow: 0 0 20px rgba(0, 229, 255, 0.4), 0 0 10px rgba(0, 229, 255, 0.2) !important;
  background: rgba(0, 229, 255, 0.1) !important;
  color: #fff !important;
}

:deep(.now-playing-play-btn:not(:disabled):hover) {
  transform: translateY(-4px) scale(1.15);
  color: #fff !important;
  background: rgba(255,255,255,0.2) !important;
  border-color: var(--accent-primary, #6ddcff) !important;
  box-shadow: 0 0 25px rgba(109, 220, 255, 0.4), 0 0 15px rgba(255,255,255,0.15) !important;
}

/* Album Art Lift Effect */
.now-playing-album-art {
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
  cursor: pointer;
}

.now-playing-album-art:hover {
  transform: translateY(-4px) scale(1.05);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.6);
  z-index: 2;
}

/* Mobile expand button — chevron-up for opening full player overlay */
.now-playing-expand-btn {
  flex-shrink: 0;
  width: 28px !important;
  height: 28px !important;
  padding: 0 !important;
  margin-left: 8px !important;
  margin-right: 0 !important;
  font-size: 14px !important;
  border-radius: 6px !important;
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.1) !important;
  color: rgba(255, 255, 255, 0.6) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
}

@keyframes neon-pulse-anim {
  0% { transform: scale(1); box-shadow: 0 0 10px rgba(0, 255, 255, 0.5), inset 0 0 5px rgba(0, 255, 255, 0.2); }
  50% { transform: scale(1.03); box-shadow: 0 0 25px rgba(0, 255, 255, 0.8), inset 0 0 10px rgba(0, 255, 255, 0.4); }
  100% { transform: scale(1); box-shadow: 0 0 10px rgba(0, 255, 255, 0.5), inset 0 0 5px rgba(0, 255, 255, 0.2); }
}

/* Meta Group & Text */
.now-playing-info-text {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
}

.now-playing-meta-group {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
  cursor: pointer;
}

.live-tag-radio {
  color: #ff2fb8 !important;
}
.live-tag-radio .live-dot {
  background: #ff2fb8 !important;
  box-shadow: 0 0 6px rgba(255, 47, 184, 0.8) !important;
}

.radio-pill {
  color: #9dfcff !important;
  border-color: rgba(109, 220, 255, 0.28) !important;
  background: rgba(109, 220, 255, 0.08);
}

.video-pill {
  color: #c4aaff !important;
  border-color: rgba(180, 140, 255, 0.28) !important;
  background: rgba(160, 120, 255, 0.08);
  cursor: pointer;
}

.radio-play-btn {
  border-color: rgba(109, 220, 255, 0.4) !important;
  color: #9dfcff !important;
  background: linear-gradient(135deg, rgba(109, 220, 255, 0.12), rgba(109, 220, 255, 0.04)) !important;
  box-shadow: 0 0 18px rgba(109, 220, 255, 0.18) !important;
}

/* Sharp Neon Styles */
.neon-text {
  color: #fff;
}

.neon-active {
  border: 2px solid #00ffff !important;
  color: #00ffff !important;
}

.neon-play-sharp {
  background: #00ffff !important;
  color: #000 !important;
  border: none !important;
}

.neon-play-sharp.is-playing {
  background: transparent !important;
  color: #00ffff !important;
  border: 2px solid #00ffff !important;
}

.neon-green {
  color: #39ff14 !important;
}

.neon-border {
  border: 2px solid #00ffff !important;
}

.neon-purple {
  border: 2px solid #bf00ff !important;
  color: #bf00ff !important;
}

.now-playing-controls-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.now-playing-transport {
  flex-direction: row !important;
  gap: 12px !important;
  min-width: 430px !important;
}

.now-playing-transport-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 40px;
}

.now-playing-scrub {
  display: grid;
  grid-template-columns: 34px minmax(160px, 320px) 34px;
  align-items: center;
  gap: 8px;
  width: min(300px, 100%);
  height: 16px;
  color: rgba(255, 255, 255, 0.64);
  user-select: none;
}

.now-playing-scrub-time {
  font-size: 10px;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  text-align: center;
}

.now-playing-scrub-range {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 14px;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  cursor: pointer;
}

.now-playing-scrub-range::-webkit-slider-runnable-track {
  height: 4px;
  border-radius: 999px;
  background: linear-gradient(
    90deg,
    var(--accent-primary, #6ddcff) 0%,
    var(--accent-primary, #6ddcff) var(--scrub-progress),
    rgba(255, 255, 255, 0.18) var(--scrub-progress),
    rgba(255, 255, 255, 0.18) 100%
  );
}

.now-playing-scrub-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 10px;
  height: 10px;
  margin-top: -3px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid var(--accent-primary, #6ddcff);
  box-shadow: 0 0 10px rgba(109, 220, 255, 0.42);
}

.now-playing-scrub-range::-moz-range-track {
  height: 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.18);
}

.now-playing-scrub-range::-moz-range-progress {
  height: 4px;
  border-radius: 999px;
  background: var(--accent-primary, #6ddcff);
}

.now-playing-scrub-range::-moz-range-thumb {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #fff;
  border: 2px solid var(--accent-primary, #6ddcff);
  box-shadow: 0 0 10px rgba(109, 220, 255, 0.42);
}

@media (max-width: 1024px) {
  :deep(.now-playing-container) {
    display: flex !important;
    flex-direction: column !important;
    gap: 6px !important;
    padding: 10px 16px calc(14px + env(safe-area-inset-bottom, 0px)) !important;
    height: auto !important;
    background: rgba(8, 8, 12, 0.99) !important;
  }

  .now-playing-left.mobile-reorg {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: flex-start !important;
    gap: 12px !important;
    width: 100% !important;
  }

  .now-playing-album-art {
    width: 52px !important;
    height: 52px !important;
    border-radius: 8px !important;
  }
}

/* Mobile Slot 2 Styles Refined & Globalized */
.now-playing-container.mobile-slot-2 {
  display: flex !important;
  flex-direction: row !important;
  justify-content: space-between !important;
  align-items: center !important;
  padding: 10px 24px !important;
  height: 80px !important;
}

@media (max-width: 1024px) {
  .now-playing-container.mobile-slot-2 {
    flex-direction: column !important;
    padding: 10px 0 16px 0 !important;
    background: rgba(12, 12, 18, 0.7) !important;
    backdrop-filter: blur(25px) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.1) !important;
    height: auto !important;
  }
}

.slot-2-timeline {
  width: 100% !important;
  display: flex !important;
  flex-direction: column !important;
  gap: 2px !important;
  margin-bottom: 12px !important;
}

.timeline-bar {
  width: 100% !important;
  height: 4px !important;
  background: rgba(255, 255, 255, 0.08) !important;
}

.timeline-fill {
  height: 100% !important;
  background: #00ffff !important;
  box-shadow: 0 0 12px #00ffff !important;
}

.timeline-text {
  display: flex !important;
  justify-content: center !important;
  gap: 6px !important;
  font-size: 10px !important;
  color: #00ffff !important;
  font-family: 'JetBrains Mono', monospace !important;
  opacity: 0.9 !important;
  letter-spacing: 0.5px !important;
}

.slot-2-scrub {
  display: none;
}

.slot-2-meta {
  display: flex !important;
  align-items: center !important;
  gap: 14px !important;
  cursor: pointer !important;
  flex: 1 !important;
}

@media (max-width: 1024px) {
  .slot-2-meta {
    padding: 0 18px !important;
    margin-bottom: 2px !important;
    width: 100% !important;
    flex: unset !important;
  }

  .slot-2-scrub {
    display: block !important;
    flex: 0 0 96px !important;
    align-items: center !important;
    width: 96px !important;
    height: 8px !important;
    padding: 0 !important;
    margin: -1px 0 0 !important;
    color: rgba(255, 255, 255, 0.62) !important;
    user-select: none !important;
  }

  .slot-2-scrub-time {
    display: none !important;
  }

  .slot-2-scrub-range {
    -webkit-appearance: none !important;
    appearance: none !important;
    width: 100% !important;
    height: 8px !important;
    margin: 0 !important;
    padding: 0 !important;
    border: 0 !important;
    background: transparent !important;
    cursor: pointer !important;
  }

  .slot-2-scrub-range::-webkit-slider-runnable-track {
    height: 2px !important;
    border-radius: 999px !important;
    background: linear-gradient(
      90deg,
      var(--accent-primary, #6ddcff) 0%,
      var(--accent-primary, #6ddcff) var(--scrub-progress),
      rgba(255, 255, 255, 0.2) var(--scrub-progress),
      rgba(255, 255, 255, 0.2) 100%
    ) !important;
  }

  .slot-2-scrub-range::-webkit-slider-thumb {
    -webkit-appearance: none !important;
    appearance: none !important;
    width: 8px !important;
    height: 8px !important;
    margin-top: -3px !important;
    border-radius: 50% !important;
    background: #fff !important;
    border: 2px solid var(--accent-primary, #6ddcff) !important;
    box-shadow: 0 0 10px rgba(109, 220, 255, 0.42) !important;
  }

  .slot-2-scrub-range::-moz-range-track {
    height: 2px !important;
    border-radius: 999px !important;
    background: rgba(255, 255, 255, 0.2) !important;
  }

  .slot-2-scrub-range::-moz-range-progress {
    height: 2px !important;
    border-radius: 999px !important;
    background: var(--accent-primary, #6ddcff) !important;
  }

  .slot-2-scrub-range::-moz-range-thumb {
    width: 8px !important;
    height: 8px !important;
    border-radius: 50% !important;
    background: #fff !important;
    border: 2px solid var(--accent-primary, #6ddcff) !important;
    box-shadow: 0 0 10px rgba(109, 220, 255, 0.42) !important;
  }
}

.slot-2-art {
  width: 52px !important;
  height: 52px !important;
  border-radius: 12px !important;
  overflow: hidden !important;
  flex-shrink: 0 !important;
  border: 1px solid rgba(255, 255, 255, 0.15) !important;
  background: rgba(255, 255, 255, 0.02) !important;
}

@media (min-width: 1025px) {
  .slot-2-art {
    width: 60px !important;
    height: 60px !important;
  }
}

.playing-glow {
  border-color: #00ffff !important;
  box-shadow: 0 0 10px rgba(0, 255, 255, 0.3) !important;
}

.slot-2-img {
  width: 100% !important;
  height: 100% !important;
  object-fit: cover !important;
}

.slot-2-info {
  min-width: 0 !important;
  flex: 1 !important;
}

.slot-2-secondary-row {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  justify-content: flex-start !important;
  min-width: 0 !important;
}

.slot-2-title-row {
  display: flex !important;
  align-items: center !important;
  gap: 10px !important;
  min-width: 0 !important;
}

.slot-2-title {
  font-size: 18px !important;
  font-weight: 800 !important;
  white-space: nowrap !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  color: #fff !important;
  flex: 0 1 auto !important;
  max-width: min(54vw, 260px) !important;
}

.slot-2-artist {
  font-size: 13px !important;
  opacity: 0.8 !important;
  color: #ccc !important;
  min-width: 0 !important;
  max-width: min(48vw, 190px) !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
  flex: 0 1 auto !important;
}

.slot-2-live-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.slot-2-live-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(109, 220, 255, 0.12);
  color: #9dfcff;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.slot-2-explore {
  font-size: 15px !important;
  font-weight: 700 !important;
  color: #00ffff !important;
  opacity: 0.9 !important;
}

.slot-2-explore-link {
  color: inherit !important;
  text-decoration: none !important;
  border-bottom: 1px solid rgba(0, 255, 255, 0.18);
  padding-bottom: 1px;
  transition: color 0.18s ease, border-color 0.18s ease, opacity 0.18s ease;
}

.slot-2-explore-link:hover,
.slot-2-explore-link:active {
  color: rgba(157, 252, 255, 0.96) !important;
  border-color: rgba(157, 252, 255, 0.5);
}

.slot-2-sub-prompt {
  font-size: 11px !important;
  opacity: 0.6 !important;
  color: #fff !important;
}

.slot-2-empty-art {
  width: 100% !important;
  height: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 20px !important;
  color: rgba(255, 255, 255, 0.2) !important;
}

.slot-2-controls {
  display: flex !important;
  flex-direction: row !important;
  gap: 12px !important;
  align-items: center !important;
}

@media (max-width: 1024px) {
  .slot-2-controls {
    padding: 0 18px !important;
    transform: translateY(-6px) !important;
    width: 100% !important;
  }
}

.now-playing-open-player-btn {
  width: 30px !important;
  height: 30px !important;
  flex-shrink: 0 !important;
  border-radius: 8px !important;
  background: rgba(255, 255, 255, 0.08) !important;
  border: 1px solid rgba(255, 255, 255, 0.14) !important;
  color: rgba(255, 255, 255, 0.78) !important;
  box-shadow: 0 4px 14px rgba(0, 0, 0, 0.18) !important;
}

.now-playing-open-player-btn:hover,
.now-playing-open-player-btn:active {
  background: rgba(255, 255, 255, 0.12) !important;
  color: #fff !important;
}

.control-group-left {
  display: flex !important;
  gap: 8px !important;
}

@media (max-width: 1024px) {
  .control-group-left {
    flex: 1 !important;
  }
}

.now-playing-btn {
  width: 44px !important;
  height: 44px !important;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.03)) !important;
  backdrop-filter: blur(25px) !important;
  -webkit-backdrop-filter: blur(25px) !important;
  border: 1px solid rgba(255, 255, 255, 0.18) !important;
  color: #fff !important;
  border-radius: 12px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  font-size: 16px !important;
  transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1) !important;
  cursor: pointer !important;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4), inset 0 0 1px rgba(255,255,255,0.2) !important;
}

.now-playing-btn:hover {
  background: rgba(255, 255, 255, 0.1) !important;
}

.neon-play-liquid {
  border: 2px solid var(--accent-primary, #6ddcff) !important;
  color: var(--accent-primary, #6ddcff) !important;
  background: linear-gradient(135deg, rgba(109, 220, 255, 0.15), rgba(109, 220, 255, 0.05)) !important;
  box-shadow: 0 0 20px rgba(109, 220, 255, 0.3) !important;
}

.art-playing-glow {
  box-shadow: 0 0 30px rgba(191, 0, 255, 0.4) !important;
  transition: box-shadow 1s ease-in-out !important;
}

/* Volume Slider Premium Refinement */
.now-playing-volume {
  -webkit-appearance: none !important;
  appearance: none !important;
  width: 100px !important;
  height: 6px !important;
  background: rgba(255, 255, 255, 0.1) !important;
  border-radius: 3px !important;
  outline: none !important;
  cursor: pointer !important;
  transition: all 0.3s ease !important;
  border: none !important;
  padding: 0 !important;
}

/* Webkit browsers (Chrome, Safari) */
.now-playing-volume::-webkit-slider-thumb {
  -webkit-appearance: none !important;
  appearance: none !important;
  width: 14px !important;
  height: 14px !important;
  background: #fff !important;
  border: 2px solid #6ddcff !important;
  border-radius: 50% !important;
  box-shadow: 0 0 10px rgba(109, 220, 255, 0.6) !important;
  transition: transform 0.2s ease !important;
  cursor: pointer !important;
}

.now-playing-volume::-webkit-slider-runnable-track {
  background: rgba(255, 255, 255, 0.1) !important;
  border-radius: 3px !important;
  height: 6px !important;
  border: none !important;
}

.now-playing-volume:hover::-webkit-slider-thumb {
  transform: scale(1.2);
  background: #6ddcff !important;
}

.now-playing-volume:active::-webkit-slider-thumb {
  transform: scale(0.9);
}

/* Firefox */
.now-playing-volume::-moz-range-thumb {
  width: 14px !important;
  height: 14px !important;
  background: #fff !important;
  border: 2px solid #6ddcff !important;
  border-radius: 50% !important;
  box-shadow: 0 0 10px rgba(109, 220, 255, 0.6) !important;
  cursor: pointer !important;
  transition: transform 0.2s ease !important;
}

.now-playing-volume::-moz-range-track {
  background: transparent !important;
  border: none !important;
}

.now-playing-volume::-moz-range-progress {
  background: rgba(109, 220, 255, 0.3) !important;
  border-radius: 3px !important;
}

.now-playing-volume:hover::-moz-range-thumb {
  transform: scale(1.2);
  background: #6ddcff !important;
}

.now-playing-volume:active::-moz-range-thumb {
  transform: scale(0.9);
}

.neon-eject-dynamic.active-playing {
  border: 2px solid #ffff00 !important;
  color: #ffff00 !important;
  background: linear-gradient(135deg, rgba(255, 255, 0, 0.15), rgba(255, 255, 0, 0.05)) !important;
  box-shadow: 0 0 12px rgba(255, 255, 0, 0.3) !important;
}

.separate-right-slot {
  margin-left: auto !important;
  border-color: rgba(191, 0, 255, 0.4) !important;
  color: #bf00ff !important;
  background: linear-gradient(135deg, rgba(191, 0, 255, 0.1), rgba(191, 0, 255, 0.02)) !important;
  box-shadow: 0 0 12px rgba(191, 0, 255, 0.2) !important;
}

@media (min-width: 1025px) {
  .now-playing-expand-btn {
    display: none !important;
  }
}

.desktop-layout-wrapper { display: block; }
.mobile-layout-wrapper { display: none; }
@media (max-width: 1024px) {
  .desktop-layout-wrapper { display: none !important; }
  .mobile-layout-wrapper { display: block !important; }
}
</style>

<style>
/* Global style fixes for the desktop */
@media (min-width: 1025px) {
  .mini-player-desktop .now-playing-wrapper {
    height: 73px !important;
    min-height: 73px !important;
    background: linear-gradient(180deg, rgba(20, 20, 30, 0.85), rgba(10, 10, 15, 0.95)) !important;
    backdrop-filter: blur(45px) saturate(2) !important;
    -webkit-backdrop-filter: blur(45px) saturate(2) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.15) !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: flex-start !important;
    z-index: 10020 !important;
    box-shadow: 0 -8px 30px rgba(0, 0, 0, 0.4) !important;
    overflow: hidden !important;
  }
  
  .mini-player-desktop .now-playing-glass {
    height: 100% !important;
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
  }

  .mini-player-desktop .now-playing-container {
    display: flex !important;
    flex-direction: row !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 0 32px !important; /* Refined spacing */
    height: 73px !important;
    flex: none !important;
  }

  .mini-player-desktop .now-playing-btn {
    width: 40px !important;
    height: 40px !important;
    border-radius: 10px !important;
    margin: 0 1px !important;
  }

  .mini-player-desktop .now-playing-transport {
    display: flex !important;
    flex-direction: row !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 12px !important;
    min-width: 430px !important;
  }

  .mini-player-desktop .now-playing-transport-controls {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    gap: 8px !important;
    height: 40px !important;
  }

  .mini-player-desktop .now-playing-scrub {
    width: min(300px, 24vw) !important;
    height: 16px !important;
  }

  .now-playing-btn:hover {
    border-color: rgba(191, 0, 255, 0.6) !important;
    box-shadow: 0 0 15px rgba(191, 0, 255, 0.2), inset 0 0 10px rgba(255, 255, 255, 0.05) !important;
    transform: translateY(-1px) !important;
  }

  .np-timeline {
    padding: 6px 32px 0 !important; /* Added side and top margin for floating look */
    margin: 0 !important;
    width: 100% !important;
    height: 12px !important;
    position: relative !important;
    top: 0 !important;
    z-index: 100 !important;
  }

  .np-timeline-track {
    height: 4px !important;
    background: rgba(255, 255, 255, 0.12) !important;
    border-radius: 2px !important;
    overflow: hidden !important;
  }

  .np-timeline-fill {
    background: linear-gradient(90deg, #bf00ff, #ff00de) !important;
    box-shadow: 0 0 15px rgba(238, 130, 238, 0.5) !important;
    height: 100% !important;
    border-radius: 0 !important;
  }

  .np-timeline-thumb {
    width: 12px !important;
    height: 12px !important;
    background: #fff !important;
    border: 2px solid #bf00ff !important;
    box-shadow: 0 0 10px rgba(191, 0, 255, 0.6) !important;
    top: 50% !important;
    transform: translate(-50%, -50%) !important;
    opacity: 1 !important;
  }

  .np-time {
    display: none !important;
  }
  
  .now-playing-container.mobile-slot-2 {
    display: flex !important;
    flex-direction: row !important;
    justify-content: space-between !important;
    align-items: center !important;
    padding: 0 24px !important;
    height: 80px !important;
  }
  
  .slot-2-meta {
    display: flex !important;
    align-items: center !important;
    gap: 12px !important;
    flex: 1 !important;
    max-width: 400px;
  }
  
  .slot-2-art {
    width: 48px !important;
    height: 48px !important;
    border-radius: 8px !important;
    overflow: hidden !important;
    flex-shrink: 0 !important;
    border: 1px solid rgba(255,255,255,0.2) !important;
  }
  
  .slot-2-img {
    width: 100% !important;
    height: 100% !important;
    object-fit: cover !important;
  }
  
  .slot-2-info {
    display: flex !important;
    flex-direction: column !important;
    justify-content: center !important;
    min-width: 0 !important;
  }
  
  .slot-2-controls {
    display: flex !important;
    align-items: center !important;
    gap: 14px !important;
    flex: 2 !important;
    justify-content: center !important;
  }

  .now-playing-left {
    gap: 12px !important;
  }

  .now-playing-album-art {
    width: 54px !important;
    height: 54px !important;
    border-radius: 8px !important;
  }

  .now-playing-info {
    justify-content: center !important;
  }

  .now-playing-title {
    font-size: 14px !important;
    font-weight: 400 !important;
    color: #fff !important;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3) !important;
  }

  .now-playing-artist {
    font-size: 11px !important;
    color: var(--accent-primary, #6ddcff) !important;
    opacity: 0.9 !important;
    font-weight: 500 !important;
  }

  /* Micro-glow for active transport */
  .now-playing-play-btn.is-playing {
    border-color: #ff00de !important;
    color: #ff00de !important;
    box-shadow: 0 0 20px rgba(255, 0, 222, 0.3) !important;
  }
}
</style>
