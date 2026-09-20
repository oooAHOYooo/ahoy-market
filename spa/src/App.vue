<template>
  <div
    class="app"
    :class="{
      'pinned-player-active':
        route.name !== 'live-tv' &&
        playerStore.isWidescreenPinned &&
        playerStore.currentTrack &&
        playerStore.mode === 'video',
    }"
  >


    <!-- Toast notifications -->
    <Toast ref="toastRef" />
    <!-- Notification overlay (global) -->
    <NotificationOverlay :is-open="notificationOpen" @close="notificationOpen = false" />
    <!-- Add to queue modal (global) -->
    <AddToQueueModal />
    <!-- Add to playlist modal (global) -->
    <AddToPlaylistModal />
    <!-- Guest save prompt: "Create account to sync" when guest bookmarks -->
    <GuestSavePrompt />

    <!-- iOS "Add to Home Screen" nudge — shown once to Safari users who haven't installed -->
    <Transition name="slide-down">
      <div v-if="showIosBanner" class="ios-install-banner">
        <i class="fas fa-arrow-up-from-bracket ios-install-icon"></i>
        <div class="ios-install-text">
          <strong>Better on your home screen</strong> — tap <i class="fas fa-arrow-up-from-bracket"></i> then <em>Add to Home Screen</em> for lock-screen audio controls.
        </div>
        <button class="dismiss" @click="dismissIosBanner">&times;</button>
      </div>
    </Transition>

    <!-- Offline banner (matches base.html) -->
    <Transition name="slide-down">
      <div v-if="!online" class="offline-banner">
        <i class="fas fa-wifi" style="opacity:0.7"></i>
        <div class="offline-banner-text">
          <strong>You're offline</strong> — browsing cached content. Audio playback unavailable.
        </div>
        <button @click="online = true" class="dismiss">&times;</button>
      </div>
    </Transition>

    <!-- Top bar: mobile status bar + mobile-top-nav (8 tabs) + navbar (Flask layout order) -->
    <AppNavbar v-if="!hideRadioChrome && !shouldHideNavbar" :mobile-menu-open="mobileMenuOpen" @toggle-mobile-menu="mobileMenuOpen = !mobileMenuOpen" @toggle-notifications="notificationOpen = !notificationOpen" />
    <!-- Mobile hamburger menu (offcanvas drawer, same as Flask _nav_main.html) -->
    <MobileMenuDrawer v-if="!hideRadioChrome && !shouldHideNavbar" :open="mobileMenuOpen" @close="mobileMenuOpen = false" />

    <!-- Main content: app-shell + left sidebar + app-main (Flask: main.main-content) -->
    <main id="main-content" class="main-content" :class="{ 'no-navbar': shouldHideNavbar }">
      <div class="app-shell">
        <AppSidebar v-if="!hideRadioChrome && !shouldHideNavbar" />
        <div class="app-main">
          <div
            class="content-area content-pad-bottom app-content spa-main has-player"
            :class="{
              'flush-content':
                route.name === 'home' ||
                route.name === 'artists' ||
                route.name === 'support' ||
                route.name === 'events' ||
                route.name === 'videos' ||
                route.name === 'merch' ||
                route.name === 'music' ||
                route.name === 'podcasts' ||
                route.name === 'live-tv' ||
                route.name === 'my-saves' ||
                route.name === 'recently-played' ||
                route.name === 'radio' ||
                route.name === 'account' ||
                route.name === 'artist-detail' ||
                route.name === 'whats-new' ||
                route.name === 'whats-new-archive' ||
                route.name === 'tab' ||
                route.name === 'wallet' ||
                route.name === 'tip-artist' ||
                route.name === 'performances' ||
                route.name === 'studio' ||
                route.name === 'studio-collection' ||
                route.name === 'poem-detail',
              'poem-surface': route.name === 'poem-detail',
            }"
          >
            <router-view v-slot="{ Component, route: viewRoute }">
              <Transition :name="transitionName" mode="out-in">
                <keep-alive :include="['HomeView', 'MusicView', 'ShowsView', 'ArtistsView', 'PodcastsView', 'LiveTVView']">
                  <component :is="Component" :key="viewRoute.path" />
                </keep-alive>
              </Transition>
            </router-view>
            <!-- Footer and compact bar scroll with page content -->
            <AppFooter v-if="!hideGlobalFooters && !hideRadioChrome" />
            <CompactFooter v-if="!hideGlobalFooters && !hideRadioChrome" />
          </div>
        </div>
      </div>
    </main>

    <!-- Desktop: global now-playing bar fixed at bottom -->
    <div v-if="!hideRadioChrome" class="mini-player-desktop desktop-only">
      <MiniPlayer />
    </div>

    <MobileBottomBar @toggle-notifications="notificationOpen = !notificationOpen" />

    <!-- Global Video Player (TV / Shows) — hidden on live-tv page since video is embedded inline there -->
    <GlobalTvPlayer v-if="route.name !== 'live-tv'" />

    <!-- Custom desktop scrollbar overlay -->
    <CustomScrollbar />

    <!-- Global Now Playing Overlay -->
    <NowPlayingOverlay />
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { usePlayerStore } from './stores/player'
import { useTheme } from './composables/useTheme'
import { useWakeLock, useHaptics } from './composables/useNative'
import { restoreSession } from './composables/useAuth'
import { useMobileCollapse } from './composables/useMobileCollapse'
import { playTapChime } from './composables/useSaveChime'
import { useContentDropDetector } from './composables/useContentDropDetector'
import { useSync } from './composables/useSync'
import { apiFetchCached } from './composables/useApi'
import AppNavbar from './components/AppNavbar.vue'
import AppSidebar from './components/AppSidebar.vue'
import MiniPlayer from './components/MiniPlayer.vue'
import MobileBottomBar from './components/MobileBottomBar.vue'
import GlobalTvPlayer from './components/GlobalTvPlayer.vue'
import Toast from './components/Toast.vue'
import NotificationOverlay from './components/NotificationOverlay.vue'
import AddToQueueModal from './components/AddToQueueModal.vue'
import AddToPlaylistModal from './components/AddToPlaylistModal.vue'
import GuestSavePrompt from './components/GuestSavePrompt.vue'
import AppFooter from './components/AppFooter.vue'
import CompactFooter from './components/CompactFooter.vue'
import MobileMenuDrawer from './components/MobileMenuDrawer.vue'
import CustomScrollbar from './components/CustomScrollbar.vue'
import NowPlayingOverlay from './components/NowPlayingOverlay.vue'
import { useOverlay } from './composables/useOverlay'
import { useNotificationCenter } from './composables/useNotificationCenter'

const playerStore = usePlayerStore()
const mobileMenuOpen = ref(false)
const notificationOpen = ref(false)

// iOS Safari install nudge — only on iOS, only in browser (not standalone), only once
const isIosSafari = /iPad|iPhone|iPod/.test(navigator.userAgent) && !('MSStream' in window)
const isStandalone = window.matchMedia('(display-mode: standalone)').matches || !!navigator.standalone
const showIosBanner = ref(isIosSafari && !isStandalone && !localStorage.getItem('ahoy-ios-install-dismissed'))
function dismissIosBanner() {
  showIosBanner.value = false
  localStorage.setItem('ahoy-ios-install-dismissed', '1')
}
const route = useRoute()
const router = useRouter()
const wakeLock = useWakeLock()
const { light: hapticLight } = useHaptics()
const theme = useTheme()
const { resetDeckMode } = useMobileCollapse()
const { isNowPlayingOpen, closeNowPlaying } = useOverlay()
const { notifications, addNotification, markAllRead } = useNotificationCenter()

const toastRef = ref(null)
const online = ref(navigator.onLine)
const transitionName = ref('fade')
const { checkForNewContent } = useContentDropDetector()
useSync({ onReconnect: checkForNewContent })

const hideRadioChrome = computed(() => false)
const shouldHideNavbar = computed(() => route.name === 'tip-artist')
const hideGlobalFooters = computed(() => false)

function onOnline() {
  online.value = true
  addNotification('Back online', 'success', 8000)
}
function onOffline() { online.value = false }

function isWebsiteSurface() {
  const cap = window.Capacitor
  const isNative = !!(
    cap &&
    (
      (typeof cap.isNativePlatform === 'function' && cap.isNativePlatform()) ||
      ['ios', 'android'].includes(cap.getPlatform?.())
    )
  )
  const isElectron = !!window.electronAPI?.isElectron || /Electron/i.test(navigator.userAgent || '')
  return !isNative && !isElectron
}

async function seedWebsiteAnnouncements() {
  if (!isWebsiteSurface()) return
  try {
    const data = await apiFetchCached('/api/whats-new')
    const structured = data.structured || {}
    const now = new Date()
    const year = String(now.getFullYear())
    const monthKey = now.toLocaleString('en-US', { month: 'short' }).toLowerCase()
    const monthData = structured[year]?.[monthKey]
    let allItems = []
    if (monthData) {
      allItems = Object.values(monthData).flatMap(section => section?.items || [])
      allItems.sort((a, b) => (b.date || '').localeCompare(a.date || ''))
    }
    if (!allItems.length) return
    const existingLinks = new Set(notifications.value.map((n) => n.link).filter(Boolean))
    const existingMessages = new Set(notifications.value.map((n) => n.message))
    for (const item of allItems) {
      if (!item.title) continue
      const link = item.detail_path || item.month_path || '/whats-new'
      if (existingLinks.has(link) || existingMessages.has(item.title)) continue
      addNotification(item.title, 'info', false, link)
      existingLinks.add(link)
      existingMessages.add(item.title)
    }
  } catch {
    // silently skip — not critical
  }
}

// Keep screen on while playing
watch(() => playerStore.isPlaying, async (playing) => {
  if (playing) {
    await wakeLock.request()
    // Open overlay when playback starts (mobile only)
    if (window.innerWidth <= 480 && playerStore.currentTrack && route.name !== 'radio' && playerStore.playbackSource !== 'radio') {
      isNowPlayingOpen.value = true
    }
  } else {
    await wakeLock.release()
  }
})

function syncFullscreenVideoState() {
  const fullscreenEl = document.fullscreenElement
    || document.webkitFullscreenElement
    || document.mozFullScreenElement
    || document.msFullscreenElement

  const hasFullscreenVideo = !!(
    fullscreenEl &&
    (fullscreenEl.tagName === 'VIDEO' || fullscreenEl.querySelector?.('video'))
  )

  document.body.classList.toggle('video-fullscreen-active', hasFullscreenVideo)
}

// Body class for Flask-style padding when mini player bar is visible (always shown)
watch(() => route.name, () => {
  document.body.classList.add('has-player')
}, { immediate: true })

// Route changes should collapse the audio overlay so navigation never lands behind it.
watch(() => route.fullPath, () => {
  if (isNowPlayingOpen.value) closeNowPlaying()
})

watch(() => route.path, (path) => {
  if (path.startsWith('/whats-new')) markAllRead()
}, { immediate: true })


watch(isNowPlayingOpen, (open) => {
  if (open) resetDeckMode()
})

watch(() => route.name, (name) => {
  if (name === 'now-playing') resetDeckMode()
})

// Favicon animation when playing
let faviconAnimationId = null
function updateFavicon() {
  const favicon = document.querySelector('link[rel="icon"]')
  if (!favicon) return

  if (playerStore.isPlaying) {
    const pulse = Math.sin(Date.now() * 0.005) * 0.3 + 0.7
    favicon.style.opacity = pulse
    faviconAnimationId = requestAnimationFrame(updateFavicon)
  } else {
    favicon.style.opacity = '1'
    if (faviconAnimationId) cancelAnimationFrame(faviconAnimationId)
  }
}

watch(() => playerStore.isPlaying, () => {
  updateFavicon()
})

// Tiny tap chime on button/link click (optional: add data-no-tap-chime to opt out)
const TAP_CHIME_SELECTOR = [
  'button:not([disabled])',
  '[role="button"]:not([disabled])',
  'a[href]',
  'input[type="submit"]:not([disabled])',
  'input[type="button"]:not([disabled])',
  '.mobile-tab',
  '.neu-btn',
  '.episode-btn',
  '.bm-btn',
  '.action-btn',
  '.podcast-cta',
  '.settings-link',
  '.app-sidebar-item',
  '.experimental-card',
  '.download-table-link',
  '.quicklink',
  '.dismiss',
].join(', ')

function onGlobalClick(e) {
  const el = e.target?.closest?.(TAP_CHIME_SELECTOR)
  if (!el || el.closest('[data-no-tap-chime]')) return
  playTapChime()
  hapticLight()
}

function handleGlobalKeydown(e) {
  // Ignore if typing in an input/textarea
  if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName) || e.target.isContentEditable) {
    return
  }

  const key = e.key.toLowerCase()
  
  // Space: Play/Pause
  if (e.code === 'Space') {
    e.preventDefault()
    playerStore.togglePlay()
    return
  }

  // M: Mute
  if (key === 'm') {
    playerStore.toggleMute?.() || (playerStore.volume = playerStore.volume > 0 ? 0 : 0.5)
    return
  }

  // Arrows: Seek & Volume (or Skip with Shift)
  if (e.shiftKey) {
    if (key === 'arrowleft') {
      e.preventDefault()
      playerStore.previous()
      return
    }
    if (key === 'arrowright') {
      e.preventDefault()
      playerStore.next()
      return
    }
  }

  if (key === 'arrowleft') {
    e.preventDefault()
    playerStore.seekBackward?.()
    return
  }
  if (key === 'arrowright') {
    e.preventDefault()
    playerStore.seekForward?.()
    return
  }
  if (key === 'arrowup') {
    e.preventDefault()
    playerStore.setVolume(Math.min(100, playerStore.volume + 10))
    return
  }
  if (key === 'arrowdown') {
    e.preventDefault()
    playerStore.setVolume(Math.max(0, playerStore.volume - 10))
    return
  }

  // /: Search Focus
  if (key === '/') {
    e.preventDefault()
    const searchInput = document.querySelector('.search-input, input[type="search"]')
    if (searchInput) {
      searchInput.focus()
      searchInput.select()
    } else if (route.path !== '/search') {
      router.push('/search')
    }
    return
  }

  // L: Cycle Theme
  if (key === 'l') {
    const nextTheme = theme.currentTheme.value === 'ayu-night' ? 'default' : 'ayu-night'
    theme.setTheme(nextTheme, { explicit: true })
    return
  }

  if (key === 'f') {
    e.preventDefault()
    playerStore.toggleFullscreen?.()
    return
  }
}

onMounted(() => {
  restoreSession()
  theme.initTheme()
  syncFullscreenVideoState()
  checkForNewContent()
  seedWebsiteAnnouncements()
  window.addEventListener('online', onOnline)
  window.addEventListener('offline', onOffline)
  window.addEventListener('keydown', handleGlobalKeydown)
  document.addEventListener('click', onGlobalClick, true)
  document.addEventListener('fullscreenchange', syncFullscreenVideoState)
  document.addEventListener('webkitfullscreenchange', syncFullscreenVideoState)
  document.addEventListener('mozfullscreenchange', syncFullscreenVideoState)
  document.addEventListener('MSFullscreenChange', syncFullscreenVideoState)
  window.addEventListener('ahoy:session-expired', () => {
    // Prevent redirect loop if already on login page
    if (route.path !== '/login') {
      router.push('/login')
      window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Session expired', type: 'error' } }))
    }
  })
  wakeLock.autoReacquire()
})

onUnmounted(() => {
  document.body.classList.remove('has-player')
  document.body.classList.remove('video-fullscreen-active')
  document.removeEventListener('click', onGlobalClick, true)
  document.removeEventListener('fullscreenchange', syncFullscreenVideoState)
  document.removeEventListener('webkitfullscreenchange', syncFullscreenVideoState)
  document.removeEventListener('mozfullscreenchange', syncFullscreenVideoState)
  document.removeEventListener('MSFullscreenChange', syncFullscreenVideoState)
  window.removeEventListener('online', onOnline)
  window.removeEventListener('offline', onOffline)
  window.removeEventListener('keydown', handleGlobalKeydown)
})
</script>

<style>
/* Pinned player top padding - push down ONLY the app-main content, not the whole shell/dashboard */
.app.pinned-player-active .app-main {
  /* Using padding ensures the background isn't cut off */
  position: relative;
  padding-top: min(calc((100vw - 182px) / (16 / 9)), 500px); 
  transition: padding-top 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@media (max-width: 1024px) {
  .app.pinned-player-active .app-main {
      padding-top: min(calc(100vw / (16 / 9)), 500px);
  }
}

/* AHOY TV: allow full-bleed — remove overflow-x clip on content area */
.app .content-area.app-content:has(.tv-container) {
  overflow: hidden;
  padding: 0 0 32px !important;
}

.app .content-area.app-content:has(.tv-container) > .tv-container {
  flex: 1 1 auto;
  min-height: 0;
}

.app .content-area.app-content:has(.tv-container) .app-footer {
  display: none;
}

.app .content-area.app-content:has(.tv-container) .compact-footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
}


/* Update banner: native OS style */
.update-banner {
  position: fixed;
  top: env(safe-area-inset-top, 0px);
  left: 0; right: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(0,0,0,0.85);
  border-bottom: 1px solid rgba(255,153,0,0.3);
  font-size: 13px;
  line-height: 1.4;
  color: #ffffff;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.2);
  font-weight: 500;
}

@media (prefers-color-scheme: light) {
  .update-banner {
    background: rgba(242,242,247,0.95);
    border-bottom: 1px solid rgba(255,153,0,0.2);
    color: #000000;
  }
}

.update-banner-text {
  flex: 1;
}

.update-banner strong {
  display: block;
  font-weight: 600;
}

.update-banner i {
  color: #ff9500;
  font-size: 16px;
  flex-shrink: 0;
}

.update-banner-dismiss {
  background: transparent;
  border: none;
  color: rgba(255,255,255,0.6);
  font-size: 20px;
  cursor: pointer;
  padding: 0 8px;
  line-height: 1;
  border-radius: 6px;
  transition: color 0.15s ease;
  flex-shrink: 0;
  -webkit-tap-highlight-color: transparent;
  min-width: 44px;
  min-height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.update-banner-dismiss:active {
  color: rgba(255,255,255,0.9);
  background: rgba(255,255,255,0.08);
}

@media (prefers-color-scheme: light) {
  .update-banner-dismiss {
    color: rgba(0,0,0,0.5);
  }
  .update-banner-dismiss:active {
    color: rgba(0,0,0,0.7);
    background: rgba(0,0,0,0.05);
  }
}

@media (prefers-reduced-motion: reduce) {
  .update-banner-dismiss {
    transition: none;
  }
}
</style>
