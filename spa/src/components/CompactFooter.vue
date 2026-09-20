<template>
  <div id="compact-footer" class="compact-footer">
    <div class="compact-footer-content">
      <div class="compact-footer-brand">
        <img src="/static/img/ahoy_logo.png" alt="Ahoy Retro" class="compact-retro-logo" />
      </div>
      <div class="compact-footer-time-weather">
        <span class="compact-time">{{ currentTime }}</span>
      </div>
      <div class="compact-footer-ticker">
        <div class="ticker-wrapper" ref="tickerWrapperRef">
          <div
            class="ticker-content"
            ref="tickerContentRef"
            :style="{ transform: `translateX(${tickerOffset}px)` }"
          >
            <span
              v-for="(item, index) in announcements"
              :key="index"
              class="ticker-item"
            >{{ item }}</span>
            <!-- Duplicate for seamless loop -->
            <span
              v-for="(item, index) in announcements"
              :key="'dup-' + index"
              class="ticker-item"
            >{{ item }}</span>
          </div>
        </div>
      </div>
      <div class="compact-footer-quicklinks">
        <router-link to="/music" class="quicklink">Music</router-link>
        <span class="quicklink-sep">•</span>
        <router-link to="/videos" class="quicklink">Videos</router-link>
        <span class="quicklink-sep">•</span>
        <router-link to="/artists" class="quicklink">Artists</router-link>
        <span class="quicklink-sep">•</span>
        <router-link to="/my-saves" class="quicklink">Saved</router-link>
      </div>
      <div v-if="showTimeline" class="compact-footer-timeline" @click="onSeek">
        <div class="compact-footer-timeline-meta">
          <span class="compact-footer-timeline-label">{{ timelineLabel }}</span>
          <span class="compact-footer-timeline-time">{{ formatTime(playerStore.currentTime) }} / {{ formatTime(playerStore.duration) }}</span>
        </div>
        <div class="compact-footer-timeline-track" aria-hidden="true">
          <div class="compact-footer-timeline-fill" :style="{ width: `${timelineProgress}%` }"></div>
        </div>
      </div>
      <p class="compact-footer-refresh mobile-only" style="margin-top: 6px; font-size: 0.75rem; opacity: 0.8;">
        Having trouble? <a href="/refresh" style="color: rgba(255,255,255,0.9); text-decoration: underline;">Get the latest version</a>
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { usePlayerStore } from '../stores/player'

const announcements = [
  'Welcome to Ahoy Indie Media',
  'Discover new indie music and videos',
  'Create playlists and save your favorites',
  'Follow your favorite artists',
  'Explore videos and events',
]

const currentTime = ref('')
const tickerOffset = ref(0)
const tickerSpeed = 0.5
const tickerWrapperRef = ref(null)
const tickerContentRef = ref(null)
const playerStore = usePlayerStore()
const showTimeline = computed(() => playerStore.currentTrack && playerStore.duration > 0)
const timelineProgress = computed(() => {
  if (!playerStore.duration) return 0
  return Math.max(0, Math.min(100, (playerStore.currentTime / playerStore.duration) * 100))
})
const timelineLabel = computed(() => playerStore.currentTrack?.title || 'Nothing playing')

let timeInterval = null
let tickerAnimationId = null

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: true,
  })
}

function startTimeUpdate() {
  updateTime()
  if (timeInterval) return
  timeInterval = setInterval(() => {
    if (document.visibilityState === 'visible') {
      updateTime()
    }
  }, 1000)
}

function stopTimeUpdate() {
  if (timeInterval) {
    clearInterval(timeInterval)
    timeInterval = null
  }
}

function startTicker() {
  const tickerContent = tickerContentRef.value
  const tickerWrapper = tickerWrapperRef.value
  if (!tickerContent || !tickerWrapper) return

  const animate = () => {
    tickerOffset.value -= tickerSpeed
    const contentWidth = tickerContent.scrollWidth / 2
    if (Math.abs(tickerOffset.value) >= contentWidth) {
      tickerOffset.value = 0
    }
    tickerAnimationId = requestAnimationFrame(animate)
  }
  tickerAnimationId = requestAnimationFrame(animate)
}

function stopTicker() {
  if (tickerAnimationId) {
    cancelAnimationFrame(tickerAnimationId)
    tickerAnimationId = null
  }
}

function onVisibilityChange() {
  if (document.visibilityState === 'visible') {
    updateTime()
    startTimeUpdate()
  } else {
    stopTimeUpdate()
  }
}

function formatTime(seconds) {
  if (!seconds || !isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function onSeek(event) {
  if (!playerStore.duration) return
  const rect = event.currentTarget.getBoundingClientRect()
  const percent = ((event.clientX - rect.left) / rect.width) * 100
  playerStore.seek(Math.max(0, Math.min(100, percent)))
}

let tickerInitTimer = null

onMounted(() => {
  updateTime()
  if (document.visibilityState === 'visible') {
    startTimeUpdate()
  }
  document.addEventListener('visibilitychange', onVisibilityChange)
  tickerInitTimer = setTimeout(startTicker, 300)
})

onUnmounted(() => {
  clearTimeout(tickerInitTimer)
  stopTimeUpdate()
  stopTicker()
  document.removeEventListener('visibilitychange', onVisibilityChange)
})
</script>

<style scoped>
/* Compact Footer Layout */
.compact-footer-content {
  display: flex;
  align-items: center;
  gap: 15px;
  height: 100%;
}

.compact-footer-brand {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  padding-right: 10px;
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}

.compact-retro-logo {
  height: 24px;
  width: auto;
  image-rendering: pixelated;
  filter: drop-shadow(0 0 5px rgba(255, 0, 96, 0.4));
  transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
  cursor: help;
}

.compact-retro-logo:hover {
  transform: scale(1.2) rotate(-3deg);
  filter: drop-shadow(0 0 10px rgba(255, 0, 96, 0.8));
  animation: logo-glitch 0.3s infinite;
}

@keyframes logo-glitch {
  0% { transform: scale(1.2) rotate(-3deg) translate(0); }
  20% { transform: scale(1.2) rotate(-3deg) translate(-1px, 1px); filter: hue-rotate(90deg); }
  40% { transform: scale(1.2) rotate(-3deg) translate(1px, -1px); filter: hue-rotate(180deg); }
  60% { transform: scale(1.2) rotate(-3deg) translate(-1px, -1px); filter: hue-rotate(270deg); }
  80% { transform: scale(1.2) rotate(-3deg) translate(1px, 1px); filter: hue-rotate(0deg); }
  100% { transform: scale(1.2) rotate(-3deg) translate(0); }
}

.compact-footer-time-weather {
  min-width: 80px;
}

.compact-footer-timeline {
  width: 100%;
  cursor: pointer;
}

.compact-footer-timeline-meta {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 5px;
  font-size: 0.72rem;
  color: rgba(255, 255, 255, 0.84);
}

.compact-footer-timeline-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.compact-footer-timeline-time {
  flex-shrink: 0;
  opacity: 0.85;
}

.compact-footer-timeline-track {
  height: 6px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.09);
}

.compact-footer-timeline-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #6ddcff, #ff3d8e);
}
</style>
