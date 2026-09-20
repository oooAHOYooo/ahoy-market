<template>
  <section class="mobile-player-deck" aria-label="Player deck">
    <div v-if="playerStore.currentTrack" class="mobile-player-deck-track" @click="goToNowPlaying">
      <div class="mobile-player-deck-art" :class="{ 'is-playing': playerStore.isPlaying }">
        <img
          :src="playerStore.currentTrack.cover_art || playerStore.currentTrack.thumbnail || playerStore.currentTrack.artwork || '/static/img/default-cover.jpg'"
          :alt="playerStore.currentTrack.title || 'Now playing'"
        />
      </div>

      <div class="mobile-player-deck-copy">
        <div class="mobile-player-deck-title-row">
          <div class="mobile-player-deck-title">{{ displayTitle }}</div>
          <span v-if="playerStore.currentTrack?.type === 'live_tv' && playerStore.isPlaying" class="mobile-player-deck-live">
            LIVE
          </span>
        </div>
        <div class="mobile-player-deck-artist">{{ displayArtist }}</div>
        <div
          v-if="canScrubTimeline"
          class="mobile-player-deck-timeline"
          :title="`${formatTime(playerStore.currentTime)} / ${formatTime(playerStore.duration)}`"
        >
          <input
            type="range"
            class="mobile-player-deck-timeline-range"
            min="0"
            max="100"
            step="0.1"
            :value="timelineProgress"
            :style="{ '--scrub-progress': `${timelineProgress}%` }"
            aria-label="Playback timeline"
            @input="onTimelineInput"
          />
        </div>
        <div class="mobile-player-deck-meta">
          <span class="mobile-player-deck-pill">
            <i class="fas" :class="isRadioSource ? 'fa-broadcast-tower' : 'fa-music'"></i>
            {{ trackTypeLabel }}
          </span>
          <span v-if="playerStore.currentTrack?.artist_slug" class="mobile-player-deck-link" @click.stop="goToBoost">
            Boost artist
          </span>
        </div>
      </div>
      <button
        type="button"
        class="mobile-player-deck-open mobile-player-deck-toggle"
        :disabled="!playerStore.currentTrack"
        title="Eject"
        aria-label="Eject track"
        @click.stop="onEject"
      >
        <i class="fas fa-eject"></i>
      </button>
    </div>

    <div v-else class="mobile-player-deck-empty">
      <div class="mobile-player-deck-empty-icon">
        <i class="fas fa-circle-play"></i>
      </div>
      <div class="mobile-player-deck-empty-copy">
        <strong>Discover Music, Podcasts, & Radio</strong>
        <small>Start listening to unlock player controls</small>
      </div>
    </div>

    <div class="mobile-player-deck-controls">
      <button type="button" class="mobile-player-deck-btn" :disabled="!playerStore.currentTrack || isRadioSource" @click.stop="onSeekBack" title="Rewind">
        <i class="fas fa-step-backward"></i>
      </button>
      <button type="button" class="mobile-player-deck-btn mobile-player-deck-btn--play" :disabled="!playerStore.currentTrack" @click.stop="onTogglePlay" :title="playButtonTitle">
        <i :class="playButtonIcon"></i>
      </button>
      <button type="button" class="mobile-player-deck-btn" :disabled="!playerStore.currentTrack || isRadioSource" @click.stop="onSeekForward" title="Fast forward">
        <i class="fas fa-step-forward"></i>
      </button>
      <button type="button" class="mobile-player-deck-btn" :disabled="!playerStore.currentTrack" @click.stop="toggleBookmark" :class="{ active: isBookmarked }" title="Bookmark">
        <i :class="isBookmarked ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
      </button>
      <button type="button" class="mobile-player-deck-btn" @click.stop="onToggleMute" :title="playerStore.isMuted ? 'Unmute' : 'Mute'">
        <i :class="volumeIconClass"></i>
      </button>
      <button type="button" class="mobile-player-deck-btn" :disabled="!playerStore.currentTrack" @click.stop="onToggleFullscreen" title="Fullscreen">
        <i class="fas fa-expand"></i>
      </button>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { usePlayerStore } from '../stores/player'
import { useBookmarks } from '../composables/useBookmarks'
import { useHaptics } from '../composables/useNative'
import { useOverlay } from '../composables/useOverlay'

const router = useRouter()
const playerStore = usePlayerStore()
const bookmarks = useBookmarks()
const haptics = useHaptics()
const { openNowPlaying, closeNowPlaying } = useOverlay()

const isRadioSource = computed(() => playerStore.playbackSource === 'radio' && !!playerStore.currentTrack)

const canScrubTimeline = computed(() => (
  !!playerStore.currentTrack &&
  !isRadioSource.value &&
  playerStore.currentTrack?.type !== 'live_tv' &&
  playerStore.currentTrack?.type !== 'show' &&
  playerStore.currentTrack?._type !== 'show' &&
  Number.isFinite(playerStore.duration) &&
  playerStore.duration > 0
))

const timelineProgress = computed(() => {
  if (!canScrubTimeline.value) return 0
  return Math.max(0, Math.min(100, (playerStore.currentTime / playerStore.duration) * 100))
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

function onToggleMute() {
  haptics.onToggle()
  playerStore.toggleMute()
}

function onTimelineInput(event) {
  if (!canScrubTimeline.value) return
  playerStore.seek(Math.max(0, Math.min(100, Number(event.target.value) || 0)))
}

function onEject() {
  if (!playerStore.currentTrack) return
  haptics.medium?.()
  playerStore.eject()
}

function toggleBookmark() {
  if (!playerStore.currentTrack) return
  bookmarks.toggle(playerStore.currentTrack)
  haptics.success?.()
  haptics.onBookmark?.()
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

function formatTime(seconds) {
  if (!Number.isFinite(seconds) || seconds <= 0) return '0:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

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
  if (playerStore.playbackSource === 'radio') return
  if (t && (t.type === 'live_tv' || t.type === 'show' || t._type === 'show')) return
  openNowPlaying()
}
</script>

<style scoped>
.mobile-player-deck {
  height: 100%;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 0;
  justify-content: flex-start;
}

.mobile-player-deck-track,
.mobile-player-deck-empty {
  flex: 0 0 auto;
  min-height: 0;
  display: grid;
  grid-template-columns: 26px minmax(0, 1fr) 22px;
  align-items: center;
  gap: 3px;
  padding: 2px 5px;
  border: 1px solid color-mix(in srgb, var(--primary-color, #00a2ff) 14%, rgba(255, 255, 255, 0.055));
  border-radius: 14px;
  background:
    linear-gradient(135deg,
      color-mix(in srgb, var(--primary-color, #00a2ff) 10%, rgba(10, 12, 16, 0.72)),
      color-mix(in srgb, var(--secondary-color, #0066ff) 6%, rgba(7, 10, 14, 0.8)));
  backdrop-filter: blur(12px) saturate(130%);
  -webkit-backdrop-filter: blur(12px) saturate(130%);
  overflow: hidden;
}

.mobile-player-deck-art {
  width: 26px;
  height: 26px;
  flex: 0 0 auto;
  border-radius: 9px;
  overflow: hidden;
  background: color-mix(in srgb, var(--primary-color, #00a2ff) 14%, rgba(255, 255, 255, 0.04));
}

.mobile-player-deck-art.is-playing {
  box-shadow:
    0 0 0 1px color-mix(in srgb, var(--primary-color, #00a2ff) 26%, rgba(255, 255, 255, 0.12)),
    0 0 14px color-mix(in srgb, var(--primary-color, #00a2ff) 16%, transparent);
}

.mobile-player-deck-art img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mobile-player-deck-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.mobile-player-deck-title-row {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.mobile-player-deck-title {
  min-width: 0;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.96);
  font-size: 9.5px;
  font-weight: 700;
  line-height: 1.1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-player-deck-live {
  flex: 0 0 auto;
  padding: 1px 3px;
  border-radius: 999px;
  background: color-mix(in srgb, #ef4444 16%, rgba(255, 255, 255, 0.06));
  color: rgba(255, 255, 255, 0.9);
  font-size: 5px;
  font-weight: 700;
  letter-spacing: 0.08em;
}

.mobile-player-deck-artist {
  overflow: hidden;
  color: rgba(255, 255, 255, 0.58);
  font-size: 6.75px;
  line-height: 1.1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-player-deck-meta {
  display: flex;
  align-items: center;
  gap: 3px;
  min-width: 0;
}

.mobile-player-deck-timeline {
  min-width: 0;
  margin-top: 2px;
}

.mobile-player-deck-timeline-range {
  width: 100%;
  height: 12px;
  margin: 0;
  appearance: none;
  -webkit-appearance: none;
  background: transparent;
  cursor: pointer;
}

.mobile-player-deck-timeline-range::-webkit-slider-runnable-track {
  height: 4px;
  border-radius: 999px;
  background:
    linear-gradient(90deg,
      color-mix(in srgb, var(--primary-color, #00a2ff) 82%, #ffffff) 0%,
      color-mix(in srgb, var(--primary-color, #00a2ff) 82%, #ffffff) var(--scrub-progress, 0%),
      rgba(255, 255, 255, 0.08) var(--scrub-progress, 0%),
      rgba(255, 255, 255, 0.08) 100%);
}

.mobile-player-deck-timeline-range::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 10px;
  height: 10px;
  margin-top: -3px;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.28);
}

.mobile-player-deck-timeline-range::-moz-range-track {
  height: 4px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
}

.mobile-player-deck-timeline-range::-moz-range-progress {
  height: 4px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--primary-color, #00a2ff) 82%, #ffffff);
}

.mobile-player-deck-timeline-range::-moz-range-thumb {
  width: 10px;
  height: 10px;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.28);
}

.mobile-player-deck-pill {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 1px 4px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--primary-color, #00a2ff) 8%, rgba(255, 255, 255, 0.04));
  color: rgba(255, 255, 255, 0.7);
  font-size: 7px;
  line-height: 1;
  white-space: nowrap;
}

.mobile-player-deck-pill i {
  font-size: 7px;
}

.mobile-player-deck-link {
  overflow: hidden;
  color: color-mix(in srgb, var(--primary-color, #00a2ff) 62%, var(--secondary-color, #0066ff) 38%);
  font-size: 6px;
  font-weight: 600;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-player-deck-open {
  flex: 0 0 auto;
  width: 26px;
  height: 26px;
  border: 1px solid color-mix(in srgb, var(--primary-color, #00a2ff) 12%, rgba(255, 255, 255, 0.08));
  border-radius: 12px;
  background:
    linear-gradient(180deg,
      color-mix(in srgb, var(--primary-color, #00a2ff) 8%, rgba(255, 255, 255, 0.04)),
      color-mix(in srgb, var(--secondary-color, #0066ff) 5%, rgba(255, 255, 255, 0.02)));
  color: rgba(255, 255, 255, 0.82);
  margin-right: 4px;
}

.mobile-player-deck-empty {
  grid-template-columns: 26px minmax(0, 1fr);
  gap: 5px;
}

.mobile-player-deck-empty-icon {
  width: 26px;
  height: 26px;
  flex: 0 0 auto;
  border-radius: 9px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background:
    linear-gradient(180deg,
      color-mix(in srgb, var(--primary-color, #00a2ff) 14%, rgba(255, 255, 255, 0.05)),
      color-mix(in srgb, var(--secondary-color, #0066ff) 8%, rgba(255, 255, 255, 0.025)));
  color: rgba(255, 255, 255, 0.72);
}

.mobile-player-deck-empty-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.mobile-player-deck-empty-copy strong {
  color: rgba(255, 255, 255, 0.94);
  font-size: 8px;
  line-height: 1.1;
}

.mobile-player-deck-empty-copy small {
  color: rgba(255, 255, 255, 0.58);
  font-size: 6px;
  line-height: 1.2;
}

.mobile-player-deck-toggle i {
  font-size: 10px;
  line-height: 1;
}

.mobile-player-deck-controls {
  flex: 0 0 auto;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 2px;
}

.mobile-player-deck-btn {
  height: 22px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid color-mix(in srgb, var(--primary-color, #00a2ff) 12%, rgba(255, 255, 255, 0.055));
  border-radius: 10px;
  background:
    linear-gradient(180deg,
      color-mix(in srgb, var(--primary-color, #00a2ff) 6%, rgba(255, 255, 255, 0.035)),
      color-mix(in srgb, var(--secondary-color, #0066ff) 3%, rgba(255, 255, 255, 0.015)));
  color: rgba(255, 255, 255, 0.7);
  font: inherit;
}

.mobile-player-deck-btn--play {
  border-color: color-mix(in srgb, var(--primary-color, #00a2ff) 50%, rgba(255, 255, 255, 0.15));
  background:
    linear-gradient(180deg,
      color-mix(in srgb, var(--primary-color, #00a2ff) 22%, rgba(255, 255, 255, 0.06)),
      color-mix(in srgb, var(--secondary-color, #0066ff) 14%, rgba(255, 255, 255, 0.02)));
  color: rgba(255, 255, 255, 0.98);
  box-shadow: 0 0 8px color-mix(in srgb, var(--primary-color, #00a2ff) 22%, transparent);
}

.mobile-player-deck-btn.active {
  border-color: color-mix(in srgb, var(--primary-color, #00a2ff) 16%, rgba(255, 255, 255, 0.14));
}

.mobile-player-deck-btn:disabled {
  opacity: 0.42;
}

.mobile-player-deck-btn i {
  font-size: 8px;
  line-height: 1;
}


@media (max-width: 430px) {
  .mobile-player-deck-track,
  .mobile-player-deck-empty {
    padding-inline: 8px;
  }

  .mobile-player-deck-title {
    font-size: 7px;
  }

  .mobile-player-deck-artist {
    font-size: 5px;
  }

  .mobile-player-deck-timeline {
    margin-top: 1px;
  }

  .mobile-player-deck-toggle {
    width: 24px;
    height: 24px;
  }

  .mobile-player-deck-controls {
    gap: 2px;
  }

  .mobile-player-deck-btn {
    height: 22px;
  }
}
</style>
