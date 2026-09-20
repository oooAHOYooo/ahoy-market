<template>
  <div class="cast-receiver-page">
    <div class="receiver-container">
      <!-- Main content -->
      <div class="receiver-content">
        <!-- Album art / Artwork -->
        <div class="receiver-artwork">
          <img
            v-if="currentMedia.image"
            :src="currentMedia.image"
            :alt="currentMedia.title"
            class="receiver-artwork-img"
          />
          <div v-else class="receiver-artwork-placeholder">
            <i class="fas fa-tv"></i>
          </div>
        </div>

        <!-- Track/Show info -->
        <div class="receiver-info">
          <h1 class="receiver-title">{{ currentMedia.title || 'Legacy Receiver' }}</h1>
          <p class="receiver-status">
            <span v-if="isPlaying" class="status-badge playing">
              <i class="fas fa-play"></i> Playing
            </span>
            <span v-else class="status-badge paused">
              <i class="fas fa-pause"></i> Paused
            </span>
          </p>
        </div>

        <!-- Video/Audio player -->
        <div class="receiver-player">
          <!-- Watermark -->
          <div class="video-watermark">
            <img src="/static/img/ahoy_logo.png" alt="Ahoy" />
          </div>

          <video
            v-if="isVideo"
            ref="videoElement"
            class="receiver-video"
            controls
            autoplay
            @play="isPlaying = true"
            @pause="isPlaying = false"
            @timeupdate="currentTime = videoElement?.currentTime || 0"
            @loadedmetadata="duration = videoElement?.duration || 0"
          >
            <source :src="currentMedia.url" />
            Your browser does not support the video tag.
          </video>
          <audio
            v-else
            ref="audioElement"
            class="receiver-audio"
            controls
            autoplay
            @play="isPlaying = true"
            @pause="isPlaying = false"
            @timeupdate="currentTime = audioElement?.currentTime || 0"
            @loadedmetadata="duration = audioElement?.duration || 0"
          >
            <source :src="currentMedia.url" />
            Your browser does not support the audio element.
          </audio>
        </div>

        <!-- Progress bar -->
        <div v-if="duration > 0" class="receiver-progress">
          <span class="time">{{ formatTime(currentTime) }}</span>
          <div class="progress-bar" @click="seek">
            <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
          </div>
          <span class="time">{{ formatTime(duration) }}</span>
        </div>

        <!-- Controls -->
        <div class="receiver-controls">
          <button
            type="button"
            class="control-btn"
            :disabled="!currentMedia.url"
            @click="togglePlay"
            :title="isPlaying ? 'Pause' : 'Play'"
          >
            <i :class="isPlaying ? 'fas fa-pause' : 'fas fa-play'"></i>
          </button>
          <button
            type="button"
            class="control-btn"
            @click="stop"
            title="Stop"
          >
            <i class="fas fa-stop"></i>
          </button>
        </div>
      </div>

      <!-- Instructions -->
      <div class="receiver-instructions">
        <h2><i class="fas fa-info-circle"></i> Legacy receiver</h2>
        <ol>
          <li>This window is kept as an archived reference.</li>
          <li>The active app does not expose cast controls in v1.0.8.</li>
          <li>Any future receiver work should be feature-flagged before release.</li>
        </ol>
        <p class="hint">Do not treat this as a shipping user flow.</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const videoElement = ref(null)
const audioElement = ref(null)

const currentMedia = ref({
  url: '',
  title: 'Waiting for media...',
  image: '',
})

const isPlaying = ref(false)
const currentTime = ref(0)
const duration = ref(0)

const isVideo = computed(() => {
  const url = currentMedia.value.url || ''
  return /\.(mp4|webm|ogg|m3u8)$/i.test(url)
})

const progressPercent = computed(() => {
  if (duration.value <= 0) return 0
  return (currentTime.value / duration.value) * 100
})

function formatTime(seconds) {
  if (!Number.isFinite(seconds)) return '0:00'
  const s = Math.floor(seconds)
  const mins = Math.floor(s / 60)
  const secs = s % 60
  return `${mins}:${String(secs).padStart(2, '0')}`
}

function togglePlay() {
  if (isVideo.value) {
    if (videoElement.value) {
      if (isPlaying.value) {
        videoElement.value.pause()
      } else {
        videoElement.value.play()
      }
    }
  } else {
    if (audioElement.value) {
      if (isPlaying.value) {
        audioElement.value.pause()
      } else {
        audioElement.value.play()
      }
    }
  }
}

function stop() {
  if (isVideo.value && videoElement.value) {
    videoElement.value.pause()
    videoElement.value.currentTime = 0
  } else if (audioElement.value) {
    audioElement.value.pause()
    audioElement.value.currentTime = 0
  }
}

function seek(e) {
  const bar = e.currentTarget
  const rect = bar.getBoundingClientRect()
  const percent = (e.clientX - rect.left) / rect.width
  const time = percent * duration.value

  if (isVideo.value && videoElement.value) {
    videoElement.value.currentTime = time
  } else if (audioElement.value) {
    audioElement.value.currentTime = time
  }
}

function loadMediaFromParams() {
  const params = new URLSearchParams(window.location.search)
  const url = params.get('url')
  const title = params.get('title')
  const image = params.get('image')
  const startTime = parseFloat(params.get('startTime')) || 0

  if (url) {
    currentMedia.value = { url, title, image }
    // Auto-play after media loads
    setTimeout(() => {
      if (isVideo.value && videoElement.value) {
        videoElement.value.currentTime = startTime
        videoElement.value.play()
      } else if (audioElement.value) {
        audioElement.value.currentTime = startTime
        audioElement.value.play()
      }
    }, 500)
  }
}

function listenForCommands() {
  // Try BroadcastChannel first (same-origin, works across tabs)
  if (typeof BroadcastChannel !== 'undefined') {
    try {
      const channel = new BroadcastChannel('ahoy-cast')
      channel.onmessage = (event) => {
        handleCastMessage(event.data)
      }
    } catch (e) {
      console.warn('BroadcastChannel not available, falling back to localStorage', e)
      // Fallback to localStorage events
      window.addEventListener('storage', (e) => {
        if (e.key === 'ahoy-cast-command' && e.newValue) {
          try {
            const data = JSON.parse(e.newValue)
            handleCastMessage(data)
          } catch (e2) {
            console.error('Failed to parse cast command:', e2)
          }
        }
      })
    }
  }
}

function handleCastMessage(data) {
  if (!data.type) return

  switch (data.type) {
    case 'play':
      if (data.payload) {
        currentMedia.value = data.payload
      }
      setTimeout(() => {
        if (isVideo.value && videoElement.value) {
          videoElement.value.play()
        } else if (audioElement.value) {
          audioElement.value.play()
        }
      }, 100)
      break

    case 'pause':
      if (isVideo.value && videoElement.value) {
        videoElement.value.pause()
      } else if (audioElement.value) {
        audioElement.value.pause()
      }
      break

    case 'seek':
      if (data.time !== undefined) {
        if (isVideo.value && videoElement.value) {
          videoElement.value.currentTime = data.time
        } else if (audioElement.value) {
          audioElement.value.currentTime = data.time
        }
      }
      break

    case 'stop':
      stop()
      currentMedia.value = { url: '', title: 'Waiting for media...' }
      break
  }
}

onMounted(() => {
  loadMediaFromParams()
  listenForCommands()
})
</script>

<style scoped>
.cast-receiver-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1d23 0%, #0d0f14 100%);
  color: white;
  padding: 2rem;
}

.receiver-container {
  width: 100%;
  max-width: 900px;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 3rem;
  align-items: center;
}

.receiver-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.receiver-artwork {
  width: 100%;
  aspect-ratio: 1;
  border-radius: 1.5rem;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.receiver-artwork-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.receiver-artwork-placeholder {
  font-size: 4rem;
  opacity: 0.5;
}

.receiver-info {
  text-align: center;
  width: 100%;
}

.receiver-title {
  font-size: 2rem;
  font-weight: 700;
  margin: 0 0 1rem;
  line-height: 1.2;
}

.receiver-status {
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 999px;
  font-size: 0.9rem;
}

.status-badge.playing {
  background: rgba(109, 220, 255, 0.2);
  color: #6ddcff;
}

.status-badge.paused {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.6);
}

.receiver-player {
  width: 100%;
}

.receiver-video,
.receiver-audio {
  width: 100%;
  border-radius: 0.75rem;
  background: black;
}

.receiver-progress {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
  margin-top: 1rem;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  cursor: pointer;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6ddcff, #00d4ff);
  transition: width 0.1s linear;
}

.time {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
  font-variant-numeric: tabular-nums;
}

.receiver-controls {
  display: flex;
  gap: 1rem;
}

.control-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(109, 220, 255, 0.2);
  border: 1px solid rgba(109, 220, 255, 0.3);
  color: #6ddcff;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 1.2rem;
}

.control-btn:hover:not(:disabled) {
  background: rgba(109, 220, 255, 0.3);
  color: #fff;
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.receiver-instructions {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1.25rem;
  padding: 2rem;
}

.receiver-instructions h2 {
  font-size: 1.3rem;
  margin: 0 0 1.5rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.receiver-instructions ol {
  margin: 0 0 1.5rem;
  padding-left: 1.5rem;
  line-height: 1.8;
}

.receiver-instructions li {
  margin-bottom: 0.75rem;
}

.hint {
  margin: 0;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.7);
  font-style: italic;
}

@media (max-width: 768px) {
  .receiver-container {
    grid-template-columns: 1fr;
    gap: 2rem;
  }

  .receiver-title {
    font-size: 1.5rem;
  }

  .receiver-instructions {
    padding: 1.5rem;
  }
}
</style>
