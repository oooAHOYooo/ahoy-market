import { createApp, watch } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import { useAuth } from './composables/useAuth'
import { initAnalytics, identifyUser } from './composables/useAnalytics'
import { usePlayerStore } from './stores/player'
import './assets/app.css'
import './assets/tailwind.css'
import './assets/platform-android.css'
import './assets/platform-ios.css'
import './assets/themes/ayu-night.css'

// Fresh-deploy marker so each SPA rebuild produces a new bundle and is easy to verify.
window.__AHOY_SPA_BUILD__ = '2026-05-21-ayu-night'

// Platform detection for native-only styles (Capacitor sets this global)
try {
  const cap = (typeof window !== 'undefined') && (window.Capacitor || null)
  const platform = cap && typeof cap.getPlatform === 'function' ? cap.getPlatform() : null
  const ua = navigator.userAgent || ''
  const isNativeMobile = platform === 'android' || platform === 'ios'
  const isIpadBrowser = /iPad/i.test(ua) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
  const isMobileBrowser = /iPhone|iPod|Android/i.test(ua)

  if (platform === 'android') document.body.classList.add('platform-android')
  else if (platform === 'ios') document.body.classList.add('platform-ios')

  if (isNativeMobile || isIpadBrowser || isMobileBrowser) {
    document.body.classList.add('force-mobile-shell')
  }
} catch (_) { /* non-Capacitor web build */ }

const app = createApp(App)
const pinia = createPinia()
app.use(pinia)
app.use(router)

const auth = useAuth()
initAnalytics(router)
watch(
  () => auth.user.value,
  (user) => identifyUser(user),
  { immediate: true },
)

app.mount('#app')

// Restore last played track so mini player shows immediately
const playerStore = usePlayerStore()
playerStore.restoreLastPlayed()
