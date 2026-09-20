<template>
  <div class="settings-page">
    <div class="settings-container">
      <!-- Desktop header -->
      <div class="settings-header desktop-only">
        <div class="settings-header-icon">
          <i class="fas fa-cog"></i>
        </div>
        <h1>Settings</h1>
        <p>Customize your Ahoy experience</p>
      </div>

      <div class="settings-content">
        <!-- Account section -->
        <div class="settings-section neu-card">
          <h2><i class="fas fa-user"></i> Account</h2>
          <template v-if="auth.isLoggedIn.value">
            <div class="settings-account-header">
              <div class="settings-avatar-container">
                <div class="settings-avatar-wrapper">
                  <img v-if="auth.user.value?.avatar_url" :src="auth.user.value.avatar_url" class="settings-avatar-img" alt="Profile" />
                  <div v-else class="settings-avatar-initials">{{ userInitials }}</div>
                  
                  <!-- Upload trigger overlay -->
                  <label class="settings-avatar-upload-overlay" title="Upload new photo">
                    <input type="file" accept="image/jpeg" class="avatar-file-input" @change="onAvatarSelected" />
                    <i class="fas fa-camera"></i>
                  </label>
                </div>
                <div v-if="uploadingAvatar" class="avatar-upload-loading">
                  <i class="fas fa-spinner fa-spin"></i>
                </div>
              </div>
              <div class="settings-profile">
                <span class="settings-label">Logged in as</span>
                <span class="settings-value">{{ auth.user.value?.email }}</span>
              </div>
            </div>
            <div class="settings-links">
              <router-link to="/account" class="settings-link">
                <i class="fas fa-user-circle"></i>
                Account &amp; wallet
              </router-link>
              <router-link to="/my-saves" class="settings-link">
                <i class="fas fa-bookmark"></i>
                Saved
              </router-link>
            </div>
            <button type="button" class="neu-btn neu-btn-secondary logout-btn" @click="onLogout">
              <i class="fas fa-sign-out-alt"></i>
              Sign out
            </button>
          </template>
          <div v-else class="settings-guest">
            <p>Sign in to manage your preferences.</p>
            <router-link to="/login" class="neu-btn neu-btn-primary">Sign in</router-link>
          </div>
        </div>

        <!-- Audio Settings -->
        <div class="settings-section neu-card">
          <h2><i class="fas fa-volume-up"></i> Audio</h2>
          <div class="settings-row setting-toggle-row">
            <div class="setting-toggle-label">
              <span class="setting-toggle-title">Save chime</span>
              <span class="setting-toggle-desc">Play a short sound when you save a track or show</span>
            </div>
            <button
              type="button"
              class="setting-toggle-btn"
              :class="{ on: saveChimeEnabled }"
              :aria-pressed="saveChimeEnabled"
              @click="toggleSaveChime"
            >
              <span class="setting-toggle-thumb"></span>
            </button>
          </div>
          <div class="settings-row setting-toggle-row">
            <div class="setting-toggle-label">
              <span class="setting-toggle-title">Tap sound</span>
              <span class="setting-toggle-desc">A tiny chime when you tap buttons and links</span>
            </div>
            <button
              type="button"
              class="setting-toggle-btn"
              :class="{ on: tapChimeEnabled }"
              :aria-pressed="tapChimeEnabled"
              @click="toggleTapChime"
            >
              <span class="setting-toggle-thumb"></span>
            </button>
          </div>
          <div class="settings-grid">
            <div class="setting-item">
              <label>Master Volume</label>
              <div class="dial-container">
                <div
                  ref="dialEl"
                  class="neu-dial"
                  :style="{ transform: `rotate(${audioSettings.masterVolume * 1.8 - 90}deg)` }"
                  @mousedown.prevent="startDialDrag($event, 'masterVolume')"
                  @touchstart.prevent="startDialDrag($event, 'masterVolume')"
                >
                  <div class="dial-handle"></div>
                </div>
                <span class="dial-value">{{ Math.round(audioSettings.masterVolume) }}</span>
              </div>
            </div>
          </div>
        </div>

        <div class="settings-section neu-card">
          <h2><i class="fas fa-palette"></i> Appearance</h2>
          <div class="settings-row setting-toggle-row">
            <div class="setting-toggle-label">
              <span class="setting-toggle-title">Theme</span>
              <span class="setting-toggle-desc">Dark themes only</span>
            </div>
            <div class="theme-options">
              <select v-model="themeChoice" class="settings-select" aria-label="Theme">
                <option value="ayu-night">Ayu Night</option>
                <option value="default">Dark Blue</option>
              </select>
            </div>
          </div>
          <div class="settings-row accent-row">
            <div class="setting-toggle-label">
              <span class="setting-toggle-title">Accent Color</span>
              <span class="setting-toggle-desc">Slide to dial in your vibe — {{ accentName }}</span>
            </div>
            <div
              class="accent-swatch"
              :style="{ background: accentHex, boxShadow: `0 0 18px ${accentHex}66` }"
              :title="accentHex"
            ></div>
          </div>
          <div class="settings-row accent-slider-row">
            <input
              type="range"
              v-model.number="accentPos"
              min="0"
              max="100"
              step="1"
              class="accent-slider"
              @input="applyCustomizationSettings"
              aria-label="Accent color"
            />
          </div>
        </div>

        <!-- Playback Settings -->
        <div class="settings-section neu-card">
          <h2><i class="fas fa-play-circle"></i> Playback</h2>
          <div class="settings-row setting-toggle-row">
            <div class="setting-toggle-label">
              <span class="setting-toggle-title">Autoplay next</span>
              <span class="setting-toggle-desc">Automatically play the next track in the queue</span>
            </div>
            <button
              type="button"
              class="setting-toggle-btn"
              :class="{ on: autoplayEnabled }"
              @click="autoplayEnabled = !autoplayEnabled"
            >
              <span class="setting-toggle-thumb"></span>
            </button>
          </div>
        </div>

        <div class="settings-section neu-card">
          <h2><i class="fas fa-broadcast-tower"></i> Bonus</h2>
          <p class="settings-helper-text">A tucked-away shortcut to the live radio station.</p>
          <div class="settings-links">
            <router-link to="/radio" class="settings-link">
              <i class="fas fa-broadcast-tower"></i>
              Open Radio
            </router-link>
          </div>
        </div>

        <div class="settings-section neu-card">
          <h2><i class="fas fa-flask"></i> Experimental</h2>
          <p class="settings-helper-text">Try out early, work-in-progress features.</p>
          <div class="settings-links">
            <router-link to="/marketplace" class="settings-link settings-link-subtle settings-link-nested">
              <span class="settings-link-leading">
                <i class="fas fa-compact-disc"></i>
                Digital Marketplace
                <span class="settings-link-tag">Test</span>
              </span>
              <i class="fas fa-angle-right settings-link-chevron"></i>
            </router-link>
            <router-link to="/merch" class="settings-link settings-link-subtle settings-link-nested">
              <span class="settings-link-leading">
                <i class="fas fa-shirt"></i>
                Physical Merch
                <span class="settings-link-tag">Moved</span>
              </span>
              <i class="fas fa-angle-right settings-link-chevron"></i>
            </router-link>
            <router-link to="/tab" class="settings-link settings-link-subtle settings-link-nested">
              <span class="settings-link-leading">
                <i class="fas fa-receipt"></i>
                Tab
                <span class="settings-link-tag">Preview</span>
              </span>
              <i class="fas fa-angle-right settings-link-chevron"></i>
            </router-link>
            <router-link to="/games" class="settings-link settings-link-subtle settings-link-nested">
              <span class="settings-link-leading">
                <i class="fas fa-gamepad"></i>
                Games Lab
              </span>
              <i class="fas fa-angle-right settings-link-chevron"></i>
            </router-link>
            <router-link to="/poems" class="settings-link settings-link-subtle settings-link-nested">
              <span class="settings-link-leading">
                <i class="fas fa-feather-alt"></i>
                Poems
              </span>
              <i class="fas fa-angle-right settings-link-chevron"></i>
            </router-link>
            <router-link to="/support" class="settings-link settings-link-subtle settings-link-nested">
              <span class="settings-link-leading">
                <i class="fas fa-hand-holding-heart"></i>
                Support Hub
                <span class="settings-link-tag">Legacy</span>
              </span>
              <i class="fas fa-angle-right settings-link-chevron"></i>
            </router-link>
            <router-link to="/mp3-player" class="settings-link">
              <i class="fas fa-download"></i>
              Downloads
            </router-link>
          </div>
        </div>

        <!-- Danger Zone -->
        <div v-if="auth.isLoggedIn.value" class="settings-section neu-card danger-zone">
          <h2><i class="fas fa-exclamation-triangle"></i> Danger Zone</h2>
          <p class="danger-desc">Once you delete your account, there is no going back. Please be certain.</p>
          
          <button 
            v-if="!confirmDelete"
            type="button" 
            class="neu-btn delete-btn-init" 
            @click="confirmDelete = true"
          >
            <i class="fas fa-trash-alt"></i>
            Delete account
          </button>
          
          <div v-else class="delete-confirmation">
            <p>Are you <strong>absolutely sure</strong>? This will permanently delete your profile, saved tracks, and wallet history.</p>
            <div class="delete-confirm-actions">
              <button type="button" class="neu-btn neu-btn-secondary" @click="confirmDelete = false">Cancel</button>
              <button 
                type="button" 
                class="neu-btn delete-btn-final" 
                :disabled="isDeleting"
                @click="onDeleteAccount"
              >
                <i v-if="isDeleting" class="fas fa-spinner fa-spin"></i>
                <span v-else>Yes, delete my account</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Build Information -->
        <div class="settings-section neu-card">
          <h2><i class="fas fa-info-circle"></i> Build Info</h2>
          <div class="build-info-grid">
            <div class="build-info-item">
              <span class="settings-label">Version</span>
              <span class="settings-value">{{ buildInfo.version }}</span>
            </div>
            <div class="build-info-item" v-if="buildInfo.buildDate">
              <span class="settings-label">Build Date</span>
              <span class="settings-value">{{ buildInfo.buildDate }}</span>
            </div>
          </div>
          <p v-if="buildInfo.loading" class="build-info-loading">Loading build info...</p>
        </div>

        <!-- Actions -->
        <div class="settings-actions">
          <button type="button" class="neu-btn neu-btn-secondary" @click="resetSettings">
            <i class="fas fa-undo"></i>
            Reset to Defaults
          </button>
          <button type="button" class="neu-btn neu-btn-primary" @click="saveSettings">
            <i class="fas fa-save"></i>
            Save Settings
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { apiFetch } from '../composables/useApi'
import { useTheme } from '../composables/useTheme'
import { usePlayerStore } from '../stores/player'
import { isSaveChimeEnabled, setSaveChimeEnabled, playSaveChime, isTapChimeEnabled, setTapChimeEnabled, playTapChime } from '../composables/useSaveChime'

const router = useRouter()
const auth = useAuth()
const playerStore = usePlayerStore()
const { currentTheme, setTheme } = useTheme()
const dialEl = ref(null)

const audioSettings = reactive({ masterVolume: 75 })
const saveChimeEnabled = ref(isSaveChimeEnabled())
const tapChimeEnabled = ref(isTapChimeEnabled())

// Performance settings
const reducedMotion = ref(false)
const lowTransparency = ref(false)

// Customization & Playback
const autoplayEnabled = ref(true)

// Visual Customization
const accentPos = ref(15) // 0–100 along the hipster gradient

// Curated hipster gradient — muted, vintage-leaning hues. Slider position
// (0–100) interpolates between adjacent stops to land on a final accent hex.
const hipsterStops = [
  { pos: 0,   hex: '#C75D4A', name: 'Terracotta' },
  { pos: 14,  hex: '#D4A24C', name: 'Mustard' },
  { pos: 28,  hex: '#8AA67A', name: 'Sage' },
  { pos: 42,  hex: '#3F8E8A', name: 'Teal' },
  { pos: 58,  hex: '#4C5B8C', name: 'Indigo' },
  { pos: 72,  hex: '#8B5C8A', name: 'Plum' },
  { pos: 86,  hex: '#C58797', name: 'Dusty Rose' },
  { pos: 100, hex: '#C75D4A', name: 'Terracotta' }
]

function hexToRgb(hex) {
  const h = hex.replace('#', '')
  return [parseInt(h.slice(0, 2), 16), parseInt(h.slice(2, 4), 16), parseInt(h.slice(4, 6), 16)]
}
function rgbToHex(r, g, b) {
  return '#' + [r, g, b].map(v => Math.round(v).toString(16).padStart(2, '0')).join('').toUpperCase()
}
function accentColorFromPos(pos) {
  const p = Math.max(0, Math.min(100, Number(pos) || 0))
  let lo = hipsterStops[0]
  let hi = hipsterStops[hipsterStops.length - 1]
  for (let i = 0; i < hipsterStops.length - 1; i++) {
    if (p >= hipsterStops[i].pos && p <= hipsterStops[i + 1].pos) {
      lo = hipsterStops[i]
      hi = hipsterStops[i + 1]
      break
    }
  }
  const span = hi.pos - lo.pos || 1
  const t = (p - lo.pos) / span
  const [r1, g1, b1] = hexToRgb(lo.hex)
  const [r2, g2, b2] = hexToRgb(hi.hex)
  return {
    hex: rgbToHex(r1 + (r2 - r1) * t, g1 + (g2 - g1) * t, b1 + (b2 - b1) * t),
    name: t < 0.5 ? lo.name : hi.name
  }
}

const accentHex = computed(() => accentColorFromPos(accentPos.value).hex)
const accentName = computed(() => accentColorFromPos(accentPos.value).name)
const themeChoice = computed({
  get: () => currentTheme.value,
  set: (value) => setTheme(value, { explicit: true })
})

// Deletion states
const isDeleting = ref(false)
const confirmDelete = ref(false)
const uploadingAvatar = ref(false)
const userInitials = computed(() => {
  const u = auth.user.value
  const name = u?.display_name || u?.username || u?.email || ''
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
})


const buildInfo = reactive({
  version: '1.1.0',
  buildDate: '',
  loading: true
})

function toggleSaveChime() {
  saveChimeEnabled.value = !saveChimeEnabled.value
  setSaveChimeEnabled(saveChimeEnabled.value)
  if (saveChimeEnabled.value) playSaveChime()
}

function toggleTapChime() {
  tapChimeEnabled.value = !tapChimeEnabled.value
  setTapChimeEnabled(tapChimeEnabled.value)
  if (tapChimeEnabled.value) playTapChime()
}

let isDragging = false
let dragProperty = null
let moveHandler = null
let upHandler = null

const STORAGE_KEY = 'ahoySettings'

function loadSettings() {
  if (auth.isLoggedIn.value) {
    apiFetch('/api/user/profile', { credentials: 'include' })
      .then((data) => {
        if (data?.preferences?.audioSettings) {
          audioSettings.masterVolume = Math.max(0, Math.min(100, data.preferences.audioSettings.masterVolume ?? 75))
        }
        if (data?.preferences?.performance) {
          reducedMotion.value = !!data.preferences.performance.reducedMotion
          lowTransparency.value = !!data.preferences.performance.lowTransparency
        }
        if (data?.preferences?.customization) {
          autoplayEnabled.value = data.preferences.customization.autoplayEnabled ?? true
          accentPos.value = data.preferences.customization.accentPos ?? 15
        }
        applyFromStorage()
      })
      .catch(() => applyFromStorage())
  } else {
    applyFromStorage()
  }
}

function applyFromStorage() {
  try {
    const saved = localStorage.getItem(STORAGE_KEY)
    if (saved) {
      const settings = JSON.parse(saved)
      if (settings.audioSettings?.masterVolume != null) {
        audioSettings.masterVolume = Math.max(0, Math.min(100, settings.audioSettings.masterVolume))
      }
      if (settings.performance) {
        reducedMotion.value = !!settings.performance.reducedMotion
        lowTransparency.value = !!settings.performance.lowTransparency
      }
      if (settings.customization) {
        autoplayEnabled.value = settings.customization.autoplayEnabled ?? true
        accentPos.value = settings.customization.accentPos ?? 15
      }
    }
  } catch {}
  applyAudioSettings()
  applyPerformanceSettings()
  applyCustomizationSettings()
}

function saveSettings() {
  const settings = { 
    audioSettings: { ...audioSettings },
    performance: {
      reducedMotion: reducedMotion.value,
      lowTransparency: lowTransparency.value
    },
    customization: {
      autoplayEnabled: autoplayEnabled.value,
      accentPos: accentPos.value
    }
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  if (auth.isLoggedIn.value) {
    auth.updateProfile({
      preferences: {
        audioSettings: audioSettings,
        performance: settings.performance,
        customization: settings.customization
      } 
    }).catch(() => {})
  }
  applyAudioSettings()
  applyPerformanceSettings()
  applyCustomizationSettings()
  window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Settings saved!', type: 'success' } }))
}

function applyPerformanceSettings() {
  if (reducedMotion.value) document.documentElement.classList.add('reduced-motion')
  else document.documentElement.classList.remove('reduced-motion')
  
  if (lowTransparency.value) document.documentElement.classList.add('low-transparency')
  else document.documentElement.classList.remove('low-transparency')
}

function applyCustomizationSettings() {
  playerStore.setAutoplay?.(autoplayEnabled.value)

  const root = document.documentElement

  const accent = accentColorFromPos(accentPos.value).hex
  root.style.setProperty('--accent-primary', accent)

}

function resetSettings() {
  audioSettings.masterVolume = 75
  setTheme('ayu-night', { explicit: false })
  const settings = { audioSettings: { ...audioSettings } }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(settings))
  if (auth.isLoggedIn.value) {
    apiFetch('/api/user/profile', {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ preferences: { audioSettings: audioSettings } }),
    }).catch(() => {})
  }
  applyAudioSettings()
  window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Settings reset to defaults', type: 'info' } }))
}

function applyAudioSettings() {
  const vol = audioSettings.masterVolume / 100
  document.querySelectorAll('audio').forEach((a) => { a.volume = vol })
  try {
    const el = playerStore.getAudioElement?.()
    if (el) el.volume = vol
  } catch {}
}

function startDialDrag(event, property) {
  isDragging = true
  dragProperty = property
  const dial = event.currentTarget
  moveHandler = (e) => handleDialDrag(e, dial)
  upHandler = () => stopDialDrag()
  document.addEventListener('mousemove', moveHandler)
  document.addEventListener('mouseup', upHandler)
  document.addEventListener('touchmove', moveHandler, { passive: false })
  document.addEventListener('touchend', upHandler)
}

function handleDialDrag(event, dial) {
  if (!isDragging || !dial) return
  const clientX = event.touches ? event.touches[0].clientX : event.clientX
  const clientY = event.touches ? event.touches[0].clientY : event.clientY
  const rect = dial.getBoundingClientRect()
  const centerX = rect.left + rect.width / 2
  const centerY = rect.top + rect.height / 2
  const angle = Math.atan2(clientY - centerY, clientX - centerX)
  const degrees = (angle * (180 / Math.PI) + 90 + 360) % 360
  const value = Math.max(0, Math.min(100, degrees / 1.8))
  if (dragProperty === 'masterVolume') audioSettings.masterVolume = value
  applyAudioSettings()
}

function stopDialDrag() {
  isDragging = false
  dragProperty = null
  if (moveHandler) {
    document.removeEventListener('mousemove', moveHandler)
    document.removeEventListener('touchmove', moveHandler)
  }
  if (upHandler) {
    document.removeEventListener('mouseup', upHandler)
    document.removeEventListener('touchend', upHandler)
  }
  moveHandler = null
  upHandler = null
}

async function fetchBuildInfo() {
  try {
    const data = await apiFetch('/api/build-info')
    if (data) {
      buildInfo.version = data.version || '1.1.0'
      buildInfo.buildDate = data.buildDate || ''
    }
  } catch (err) {
    console.error('Failed to fetch build info:', err)
  } finally {
    buildInfo.loading = false
  }
}



async function onLogout() {
  await auth.logout()
  window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Signed out', type: 'success' } }))
  router.push('/')
}

async function onDeleteAccount() {
  if (isDeleting.value) return
  isDeleting.value = true
  
  try {
    const response = await apiFetch('/api/auth/delete-account', {
      method: 'POST',
      credentials: 'include'
    })
    
    if (response.success) {
      window.dispatchEvent(new CustomEvent('ahoy:toast', { 
        detail: { message: 'Account deleted forever. Sorry to see you go.', type: 'info' } 
      }))
      // Wait a moment for toast then go home
      setTimeout(() => {
        window.location.href = '/'
      }, 2000)
    } else {
      throw new Error(response.error || 'Deletion failed')
    }
  } catch (err) {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { 
      detail: { message: err.message || 'Could not delete account. Contact support.', type: 'error' } 
    }))
  } finally {
    isDeleting.value = false
    confirmDelete.value = false
  }
}

async function onAvatarSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return

  if (file.type !== 'image/jpeg' && !file.name.toLowerCase().endsWith('.jpg') && !file.name.toLowerCase().endsWith('.jpeg')) {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Only JPEG (.jpg) files are allowed', type: 'error' } }))
    return
  }

  uploadingAvatar.value = true
  const formData = new FormData()
  formData.append('file', file)

  try {
    const data = await apiFetch('/api/user/avatar', {
      method: 'POST',
      body: formData,
    })

    if (data.success && data.avatar_url) {
      // Update user in local ref / session cache
      auth.user.value = {
        ...auth.user.value,
        avatar_url: data.avatar_url
      }
      try {
        localStorage.setItem('ahoy.auth.user', JSON.stringify(auth.user.value))
      } catch (err) { /* ignore */ }
      
      window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Profile photo updated successfully', type: 'success' } }))
    } else {
      window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: data.error || 'Failed to upload photo', type: 'error' } }))
    }
  } catch (err) {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: err?.message || 'Failed to upload photo', type: 'error' } }))
  } finally {
    uploadingAvatar.value = false
  }
}

onMounted(() => {
  saveChimeEnabled.value = isSaveChimeEnabled()
  tapChimeEnabled.value = isTapChimeEnabled()
  loadSettings()
  fetchBuildInfo()
})
onUnmounted(() => {
  stopDialDrag()
})
</script>

<style scoped>
.settings-page {
  min-height: 100vh;
  background: #0e0e10;
  padding: 24px 16px 80px;
}
.settings-container {
  max-width: 640px;
  margin: 0 auto;
}
.settings-page-header.podcasts-hero .podcasts-hero-inner h1 {
  margin: 0 0 6px 0;
  font-size: 28px;
  font-weight: 700;
}
.settings-page-header.podcasts-hero .podcasts-hero-inner p {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
}

.settings-header {
  text-align: center;
  margin-bottom: 40px;
}
.settings-header-icon {
  width: 64px;
  height: 64px;
  margin: 0 auto 16px;
  border-radius: 20px;
  background: #18181b;
  box-shadow: 6px 6px 14px rgba(0, 0, 0, 0.7), -6px -6px 14px rgba(255, 255, 255, 0.03);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: rgba(255, 255, 255, 0.5);
}
.settings-header h1 {
  font-size: 1.8rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  margin: 0 0 6px;
}
.settings-header p {
  color: rgba(255, 255, 255, 0.35);
  font-size: 0.95rem;
  margin: 0;
}

.settings-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.neu-card {
  background: #18181b;
  border-radius: 16px;
  padding: 24px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  box-shadow: 8px 8px 20px rgba(0, 0, 0, 0.6), -4px -4px 12px rgba(255, 255, 255, 0.02);
}
.neu-card h2 {
  font-size: 1.1rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}
.neu-card h2 i {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.3);
}

.settings-profile { margin-bottom: 12px; }
.settings-label {
  display: block;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 4px;
}
.settings-value {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.9);
}
.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 24px;
}
.settings-textarea {
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  font-size: 14px;
  outline: none;
  resize: vertical;
  min-height: 80px;
  transition: all 0.2s ease;
}
.settings-textarea:focus {
  border-color: rgba(0, 162, 255, 0.55);
  background: rgba(255, 255, 255, 0.08);
}
.settings-links { display: flex; flex-direction: column; gap: 0; }
.settings-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 0;
  color: rgba(255, 255, 255, 0.9);
  text-decoration: none;
  font-size: 15px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.settings-link:hover { color: rgba(0, 162, 255, 0.9); }
.settings-link-subtle {
  padding: 10px 0 10px 10px;
  color: rgba(255, 255, 255, 0.72);
  font-size: 14px;
}
.settings-link-nested {
  justify-content: space-between;
}
.settings-link-leading {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}
.settings-link-chevron {
  opacity: 0.76;
  font-size: 0.9em;
}
.settings-link-subtle:hover { color: rgba(0, 162, 255, 0.82); }
.settings-link-tag {
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(255, 180, 60, 0.85);
  border: 1px solid rgba(255, 180, 60, 0.3);
  border-radius: 4px;
  padding: 1px 5px;
  line-height: 1.4;
}
.settings-helper-text {
  margin: -8px 0 18px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 0.85rem;
  line-height: 1.45;
}
.settings-password-form {
  display: grid;
  gap: 12px;
}
.settings-password-field {
  display: grid;
  gap: 6px;
  color: rgba(255, 255, 255, 0.58);
  font-size: 12px;
  font-weight: 600;
}
.settings-password-field input {
  width: 100%;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.18);
  color: rgba(255, 255, 255, 0.92);
  font-size: 14px;
  padding: 12px 14px;
  outline: none;
  box-sizing: border-box;
}
.settings-password-field input:focus {
  border-color: rgba(0, 162, 255, 0.55);
}
.settings-password-message {
  margin: 0;
  color: rgba(134, 239, 172, 0.9);
  font-size: 13px;
}
.settings-password-message.error {
  color: #fca5a5;
}
.settings-password-submit {
  width: 100%;
  justify-content: center;
}
.logout-btn {
  margin-top: 20px;
  width: 100%;
  justify-content: center;
}
.settings-guest {
  text-align: center;
  padding: 12px 0;
}
.settings-guest p {
  color: rgba(255, 255, 255, 0.5);
  margin: 0 0 16px;
  font-size: 0.95rem;
}

.settings-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.setting-toggle-row {
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.setting-toggle-label {
  flex: 1;
  min-width: 0;
}
.setting-toggle-title {
  display: block;
  font-weight: 600;
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.85);
  margin-bottom: 2px;
}
.setting-toggle-desc {
  display: block;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.4);
}
.setting-toggle-btn {
  flex-shrink: 0;
  width: 48px;
  height: 26px;
  border-radius: 13px;
  border: none;
  background: #0e0e10;
  box-shadow: inset 2px 2px 6px rgba(0, 0, 0, 0.5), inset -1px -1px 3px rgba(255, 255, 255, 0.03);
  cursor: pointer;
  position: relative;
  transition: background 0.2s ease, box-shadow 0.2s ease;
}
.setting-toggle-btn:hover {
  box-shadow: inset 2px 2px 6px rgba(0, 0, 0, 0.5), inset -1px -1px 3px rgba(255, 255, 255, 0.05), 0 0 12px rgba(0, 162, 255, 0.08);
}
.setting-toggle-btn.on {
  background: linear-gradient(135deg, rgba(0, 162, 255, 0.35), rgba(59, 130, 246, 0.3));
  box-shadow: inset 0 0 0 1px rgba(0, 162, 255, 0.25), 0 0 12px rgba(0, 162, 255, 0.15);
}
.setting-toggle-thumb {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.4);
  transition: transform 0.2s ease;
}
.setting-toggle-btn.on .setting-toggle-thumb {
  transform: translateX(22px);
}

.theme-options {
  flex-shrink: 0;
}

.settings-select {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.9rem;
  cursor: pointer;
  outline: none;
  width: 140px;
}
.settings-select:focus {
  border-color: rgba(0, 162, 255, 0.5);
}
.settings-select option {
  background: #18181b;
  color: #fff;
}

.accent-row {
  margin-bottom: 12px;
}
.accent-swatch {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 2px solid rgba(255, 255, 255, 0.18);
  transition: background 0.25s ease, box-shadow 0.25s ease;
}
.accent-slider-row {
  margin-top: 4px;
}
.accent-slider {
  width: 100%;
  height: 14px;
  border-radius: 999px;
  appearance: none;
  outline: none;
  cursor: pointer;
  background: linear-gradient(
    to right,
    #C75D4A 0%,
    #D4A24C 14%,
    #8AA67A 28%,
    #3F8E8A 42%,
    #4C5B8C 58%,
    #8B5C8A 72%,
    #C58797 86%,
    #C75D4A 100%
  );
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.06);
}
.accent-slider::-webkit-slider-thumb {
  appearance: none;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fff;
  border: 3px solid var(--accent-primary, #C75D4A);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5), 0 0 12px var(--accent-primary, #C75D4A);
  cursor: grab;
}
.accent-slider::-moz-range-thumb {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: #fff;
  border: 3px solid var(--accent-primary, #C75D4A);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.5), 0 0 12px var(--accent-primary, #C75D4A);
  cursor: grab;
}
.accent-slider:active::-webkit-slider-thumb { cursor: grabbing; }

.setting-slider-group {
  width: 100%;
}
.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
  gap: 20px;
}
.setting-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}
.setting-item label {
  font-weight: 500;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.dial-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.neu-dial {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  position: relative;
  cursor: pointer;
  background: #18181b;
  border: none;
  box-shadow: 6px 6px 16px rgba(0, 0, 0, 0.7), -4px -4px 10px rgba(255, 255, 255, 0.025), inset 0 0 0 1px rgba(255, 255, 255, 0.04);
  transition: box-shadow 0.2s ease;
}
.neu-dial:hover {
  box-shadow: 6px 6px 16px rgba(0, 0, 0, 0.7), -4px -4px 10px rgba(255, 255, 255, 0.025), inset 0 0 0 1px rgba(255, 255, 255, 0.08), 0 0 20px rgba(0, 162, 255, 0.08);
}
.neu-dial .dial-handle {
  position: absolute;
  top: 8px;
  left: 50%;
  width: 3px;
  height: 24px;
  background: linear-gradient(180deg, rgba(0, 162, 255, 0.9), rgba(59, 130, 246, 0.6));
  border-radius: 2px;
  transform: translateX(-50%);
  box-shadow: 0 0 8px rgba(0, 162, 255, 0.3);
}
.dial-value {
  font-weight: 600;
  color: rgba(255, 255, 255, 0.6);
  font-size: 1rem;
  font-variant-numeric: tabular-nums;
}

.neu-card-inset {
  background: #131316;
  box-shadow: inset 4px 4px 10px rgba(0, 0, 0, 0.5), inset -2px -2px 6px rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.03);
}

.build-info-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 0;
}

.build-info-loading {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.4);
  text-align: center;
}

.settings-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  flex-wrap: wrap;
}
.neu-btn {
  padding: 12px 24px;
  border-radius: 12px;
  border: none;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  transition: box-shadow 0.2s ease, background 0.2s ease;
  text-decoration: none;
  color: inherit;
}
.neu-btn-secondary {
  background: #18181b;
  color: rgba(255, 255, 255, 0.5);
  box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.5), -3px -3px 8px rgba(255, 255, 255, 0.02);
}
.neu-btn-secondary:hover {
  color: rgba(255, 255, 255, 0.7);
  box-shadow: 2px 2px 6px rgba(0, 0, 0, 0.4), -2px -2px 4px rgba(255, 255, 255, 0.02);
}
.neu-btn-primary {
  background: linear-gradient(135deg, #1e1b2e, #1a1730);
  color: rgba(0, 162, 255, 0.9);
  box-shadow: 4px 4px 12px rgba(0, 0, 0, 0.5), -3px -3px 8px rgba(255, 255, 255, 0.02), 0 0 12px rgba(0, 162, 255, 0.06);
}
.neu-btn-primary:hover {
  color: rgba(0, 162, 255, 1);
  box-shadow: 2px 2px 6px rgba(0, 0, 0, 0.4), -2px -2px 4px rgba(255, 255, 255, 0.02), 0 0 20px rgba(0, 162, 255, 0.1);
}
.neu-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.danger-zone {
  border: 1px solid rgba(239, 68, 68, 0.15);
  background: rgba(239, 68, 68, 0.02);
}
.danger-zone h2 {
  color: rgba(239, 68, 68, 0.8);
}
.danger-zone h2 i {
  color: rgba(239, 68, 68, 0.4);
}
.danger-desc {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.4);
  margin-bottom: 20px;
}
.delete-btn-init {
  background: rgba(239, 68, 68, 0.1);
  color: rgba(239, 68, 68, 0.9);
  border: 1px solid rgba(239, 68, 68, 0.2);
  width: 100%;
  justify-content: center;
}
.delete-btn-init:hover {
  background: rgba(239, 68, 68, 0.15);
  box-shadow: 0 0 15px rgba(239, 68, 68, 0.1);
}
.delete-confirmation {
  padding: 16px;
  background: rgba(0, 0, 0, 0.2);
  border-radius: 12px;
  border-left: 3px solid #ef4444;
}
.delete-confirmation p {
  margin: 0 0 16px;
  font-size: 0.9rem;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.8);
}
.delete-confirm-actions {
  display: flex;
  gap: 12px;
}
.delete-btn-final {
  background: #ef4444;
  color: #fff;
  flex: 1;
  justify-content: center;
}
.delete-btn-final:hover {
  background: #dc2626;
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.2);
}
.delete-btn-final:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .settings-page { padding: 16px 12px 100px; }
}

/* Settings Page Profile Avatar Styling */
.settings-account-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 20px;
}
.settings-avatar-container {
  position: relative;
  flex-shrink: 0;
}
.settings-avatar-wrapper {
  position: relative;
  width: 64px;
  height: 64px;
  border-radius: 50%;
  border: 1.5px solid rgba(255, 255, 255, 0.12);
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.18), rgba(130, 100, 255, 0.18));
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}
.settings-avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.settings-avatar-initials {
  font-size: 22px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -1px;
}
.settings-avatar-upload-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 16px;
  opacity: 0;
  cursor: pointer;
  transition: opacity 0.2s ease;
  z-index: 5;
}
.settings-avatar-wrapper:hover .settings-avatar-upload-overlay {
  opacity: 1;
}
.settings-avatar-container .avatar-file-input {
  display: none;
}
.settings-avatar-container .avatar-upload-loading {
  position: absolute;
  bottom: -4px;
  right: -4px;
  background: rgba(0, 212, 255, 0.9);
  color: #fff;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  box-shadow: 0 0 10px rgba(0, 212, 255, 0.5);
}
</style>
