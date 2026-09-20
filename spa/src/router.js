import { createRouter, createWebHashHistory, createWebHistory } from 'vue-router'
import HomeView from './views/HomeView.vue'
import { routeSeoMeta } from './composables/useSeoMeta'

const SITE = 'Ahoy Indie Media'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomeView,
    meta: { title: `${SITE}`, description: 'Stream music, videos, and podcasts from independent artists. Send tips directly to creators.' },
  },
  {
    path: '/search',
    name: 'search',
    component: () => import('./views/SearchView.vue'),
    meta: { title: `Search — ${SITE}` },
  },
  {
    path: '/dashboard',
    name: 'dashboard',
    component: () => import('./views/DashboardView.vue'),
    meta: { title: `Dashboard — ${SITE}` },
  },
  {
    path: '/music',
    name: 'music',
    component: () => import('./views/MusicView.vue'),
    meta: { title: `Music — ${SITE}`, description: 'Browse and stream music from independent artists.' },
  },
  {
    path: '/music/:artistSlug/:trackSlug',
    name: 'music-detail',
    component: () => import('./views/MusicDetailView.vue'),
    meta: { title: `Music — ${SITE}`, description: 'Listen to indie music on Ahoy. Support independent artists directly.' },
  },
  {
    path: '/music/:id',
    name: 'music-detail-legacy',
    component: () => import('./views/MusicDetailView.vue'),
    meta: { title: `Music — ${SITE}`, description: 'Listen to indie music on Ahoy. Support independent artists directly.' },
  },
  {
    path: '/videos',
    name: 'videos',
    component: () => import('./views/ShowsView.vue'),
    meta: { title: `Videos — ${SITE}`, description: 'Watch music videos, live shows, and performances.' },
  },
  {
    path: '/videos/:hostSlug/:showId',
    name: 'video-detail',
    component: () => import('./views/ShowDetailView.vue'),
    meta: { title: `Video — ${SITE}`, description: 'Watch indie music videos, live performances, and original shows.' },
  },
  {
    path: '/videos/:id',
    name: 'video-detail-legacy',
    component: () => import('./views/ShowDetailView.vue'),
    meta: { title: `Video — ${SITE}`, description: 'Watch indie music videos, live performances, and original shows.' },
  },
  { path: '/shows', redirect: '/videos' },
  { path: '/shows/:id', redirect: to => `/videos/${to.params.id}` },
  {
    path: '/live-tv',
    name: 'live-tv',
    component: () => import('./views/LiveTVView.vue'),
    meta: { title: `AHOY TV — ${SITE}`, description: 'Watch live streams and broadcasts.' },
  },
  {
    path: '/podcasts',
    name: 'podcasts',
    component: () => import('./views/PodcastsView.vue'),
    meta: { title: `Podcasts — ${SITE}`, description: 'Listen to podcasts from independent creators.' },
  },
  {
    path: '/podcasts/:slug/:number',
    name: 'podcast-episode',
    component: () => import('./views/PodcastEpisodeView.vue'),
    meta: { title: `Podcast Episode — ${SITE}`, description: 'Listen to indie podcast episodes from independent creators.' },
  },
  {
    path: '/podcasts/:slug',
    name: 'podcast-detail',
    component: () => import('./views/PodcastDetailView.vue'),
    meta: { title: `Podcast — ${SITE}`, description: 'Listen to indie podcasts from independent creators and artists.' },
  },
  {
    path: '/artists',
    name: 'artists',
    component: () => import('./views/ArtistsView.vue'),
    meta: { title: `Artists — ${SITE}`, description: 'Browse independent artists. Stream their music and send tips.' },
  },
  {
    path: '/artists/:slug',
    name: 'artist-detail',
    component: () => import('./views/ArtistDetailView.vue'),
    meta: { title: `Artist — ${SITE}`, description: 'Listen to music and send tips directly to the artist.' },
  },
  {
    path: '/events',
    name: 'events',
    component: () => import('./views/EventsView.vue'),
    meta: { title: `Events — ${SITE}`, description: 'Browse music events and live shows.' },
  },
  {
    path: '/events/:series/:number',
    name: 'event-detail',
    component: () => import('./views/EventDetailView.vue'),
    meta: { title: `Event — ${SITE}`, description: 'Details for music event with artist lineup and tickets.' },
  },
  {
    path: '/events/v/:id',
    name: 'event-detail-by-id',
    component: () => import('./views/EventDetailView.vue'),
    meta: { title: `Event — ${SITE}`, description: 'Details for music event.' },
  },
  {
    path: '/events/:series',
    name: 'event-series',
    component: () => import('./views/EventSeriesView.vue'),
    meta: { title: `Event Series — ${SITE}`, description: 'Event series with multiple shows and performances.' },
  },
  {
    path: '/studio',
    name: 'studio',
    component: () => import('./views/StudioView.vue'),
    meta: { title: `Studio — ${SITE}` },
  },
  {
    path: '/studio/:id',
    name: 'studio-collection',
    component: () => import('./views/StudioCollectionView.vue'),
    meta: { title: `Studio Collection — ${SITE}`, description: 'Behind-the-scenes photos and content from studio sessions.' },
  },
  {
    path: '/merch',
    name: 'merch',
    component: () => import('./views/MerchView.vue'),
    meta: { title: `Merch — ${SITE}`, description: 'Browse and buy merchandise from independent artists.' },
  },
  {
    path: '/marketplace',
    name: 'marketplace',
    component: () => import('./views/DigitalMarketplaceView.vue'),
    meta: { title: `Digital Marketplace — ${SITE}`, description: 'Buy downloadable music directly from independent artists.' },
  },
  {
    path: '/radio',
    name: 'radio',
    component: () => import('./views/RadioView.vue'),
    meta: { title: `Radio — ${SITE}`, description: 'Listen to radio stations with independent music.' },
  },
  {
    path: '/games',
    name: 'games',
    component: () => import('./views/GamesView.vue'),
    meta: { title: `Games Lab — ${SITE}`, description: 'Hidden experimental radio-adjacent games.' },
  },
  {
    path: '/poems',
    name: 'poems',
    component: () => import('./views/PoemsView.vue'),
    meta: { title: `Poems — ${SITE}`, description: 'Original poems from Poets & Friends contributors.' },
  },
  {
    path: '/poems/:poem_id',
    name: 'poem-detail',
    component: () => import('./views/PoemDetailView.vue'),
    meta: { title: `Poem — ${SITE}` },
  },
  {
    path: '/my-saves',
    name: 'my-saves',
    component: () => import('./views/SavedView.vue'),
    meta: { title: `My Saves — ${SITE}` },
  },
  {
    path: '/recently-played',
    name: 'recently-played',
    component: () => import('./views/SavedView.vue'),
    meta: { title: `Recently Played — ${SITE}` },
  },
  {
    path: '/playlists',
    name: 'playlists',
    component: () => import('./views/PlaylistsView.vue'),
    meta: { title: `Playlists — ${SITE}` },
  },
  {
    path: '/support',
    name: 'support',
    component: () => import('./views/SupportView.vue'),
    meta: { title: `Support — ${SITE}`, description: 'Boost artists directly or support Ahoy to help keep the platform ad free.' },
  },
  {
    path: '/playlists/:id',
    name: 'playlist-detail',
    component: () => import('./views/PlaylistDetailView.vue'),
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('./views/LoginView.vue'),
    meta: { title: `Sign In — ${SITE}` },
  },
  {
    path: '/onboarding',
    name: 'onboarding',
    component: () => import('./views/OnboardingView.vue'),
    meta: { title: `Welcome to Ahoy — ${SITE}` },
  },
  {
    path: '/account',
    name: 'account',
    component: () => import('./views/AccountView.vue'),
    meta: { title: `Account — ${SITE}` },
  },
  {
    path: '/settings',
    name: 'settings',
    component: () => import('./views/SettingsView.vue'),
    meta: { title: `Settings — ${SITE}` },
  },
  {
    path: '/focus',
    name: 'focus',
    component: () => import('./views/FocusView.vue'),
    meta: { title: `Focus Mode — ${SITE}` },
  },
  {
    path: '/download',
    name: 'download',
    component: () => import('./views/DownloadView.vue'),
    meta: { title: `Download the App — ${SITE}`, description: 'Download Ahoy Indie Media for desktop (Mac, Windows, Linux) and mobile (iOS, Android).' },
  },
  {
    path: '/mp3-player',
    name: 'mp3-player',
    component: () => import('./views/Mp3PlayerView.vue'),
    meta: { title: `MP3 Player — ${SITE}` },
  },
  {
    path: '/auth/forgot',
    name: 'forgot-password',
    component: () => import('./views/ForgotPasswordView.vue'),
    meta: { title: `Forgot Password — ${SITE}` },
  },
  {
    path: '/auth/reset',
    name: 'reset-password',
    component: () => import('./views/ResetPasswordView.vue'),
    meta: { title: `Reset Password — ${SITE}` },
  },
  {
    path: '/auth/google/callback',
    name: 'google-callback',
    component: () => import('./views/GoogleCallbackView.vue'),
    meta: { title: `Signing in... — ${SITE}` },
  },
  {
    path: '/checkout',
    name: 'checkout',
    component: () => import('./views/CheckoutView.vue'),
    meta: { title: `Checkout — ${SITE}` },
  },
  {
    path: '/success',
    name: 'success',
    component: () => import('./views/SuccessView.vue'),
    meta: { title: `Success — ${SITE}` },
  },
  { path: '/downloads', redirect: '/download' },
  {
    path: '/offline',
    name: 'offline',
    component: () => import('./views/OfflineView.vue'),
    meta: { title: `Offline — ${SITE}` },
  },
  {
    path: '/privacy',
    name: 'privacy',
    component: () => import('./views/PrivacyView.vue'),
    meta: { title: `Privacy Policy — ${SITE}` },
  },
  {
    path: '/terms',
    name: 'terms',
    component: () => import('./views/TermsView.vue'),
    meta: { title: `Terms of Service — ${SITE}` },
  },
  {
    path: '/security',
    name: 'security',
    component: () => import('./views/SecurityView.vue'),
    meta: { title: `Security — ${SITE}` },
  },
  {
    path: '/performances',
    name: 'performances',
    component: () => import('./views/PerformancesView.vue'),
    meta: { title: `Performances — ${SITE}`, description: 'Watch indie live performances and concerts on Ahoy.' },
  },
  {
    path: '/feedback',
    name: 'feedback',
    component: () => import('./views/FeedbackView.vue'),
    meta: { title: `Feedback — ${SITE}` },
  },
  {
    path: '/contact',
    name: 'contact',
    component: () => import('./views/ContactView.vue'),
    meta: { title: `Contact — ${SITE}` },
  },
  {
    path: '/cast',
    name: 'cast',
    component: () => import('./views/CastView.vue'),
    meta: { title: `Legacy Cast — ${SITE}`, description: 'Archived cast surface kept for future review; not part of the active shipping app.' },
  },
  {
    path: '/cast/receiver',
    name: 'cast-receiver',
    component: () => import('./views/CastReceiverView.vue'),
    meta: { title: `Legacy Receiver — ${SITE}` },
  },
  {
    path: '/whats-new',
    name: 'whats-new',
    component: () => import('./views/WhatsNewView.vue'),
    meta: { title: `What's New — ${SITE}` },
  },
  {
    path: '/whats-new/:year/:month/:section?',
    name: 'whats-new-archive',
    component: () => import('./views/WhatsNewView.vue'),
    meta: { title: `What's New — ${SITE}` },
  },
  {
    path: '/whats-new/:year/:month/:section/:slug',
    name: 'whats-new-detail',
    component: () => import('./views/WhatsNewView.vue'),
    meta: { title: `What's New — ${SITE}` },
  },
  {
    path: '/whats-new/:year/:month/:section/:slug/videos',
    name: 'whats-new-video-source',
    component: () => import('./views/WhatsNewVideoSourceView.vue'),
    meta: { title: `What's New — ${SITE}` },
  },
  {
    path: '/beta-testers',
    name: 'beta-testers',
    component: () => import('./views/BetaTesterView.vue'),
    meta: { title: `Beta Testers — ${SITE}` },
  },
  {
    path: '/sitemap',
    name: 'sitemap',
    component: () => import('./views/SitemapView.vue'),
    meta: { title: `Sitemap — ${SITE}`, description: 'Browse all pages on Ahoy Indie Media.' },
  },
  {
    path: '/tip-artist',
    name: 'tip-artist',
    component: () => import('./views/TipArtistView.vue'),
    meta: { title: `Tip an Artist — ${SITE}` },
  },
  {
    path: '/tab',
    name: 'tab',
    component: () => import('./views/TabView.vue'),
    meta: { title: `Tab — ${SITE}`, description: 'Open a tab. Tip artists, buy merch, pay in person.' },
  },
  // Legacy URL redirects (Flask used these; SPA uses different paths)
  { path: '/wallet', redirect: '/tab' },
  { path: '/bookmarks', redirect: '/my-saves' },
  { path: '/recent', redirect: '/recently-played' },
  { path: '/auth', redirect: '/login' },
  { path: '/artist/:slug', redirect: to => `/artists/${to.params.slug}` },
  // 404 – dedicated page with “Oops” / funny graphic
  {
    path: '/:pathMatch(.*)*',
    name: 'not-found',
    component: () => import('./views/NotFoundView.vue'),
  },
  {
    path: '/about',
    name: 'about',
    component: () => import('./views/AboutView.vue'),
    meta: { title: `About — ${SITE}` },
  },
]

function isCapacitorNative() {
  if (typeof window === 'undefined') return false
  const cap = window.Capacitor
  return !!(cap && typeof cap.isNativePlatform === 'function' && cap.isNativePlatform())
}

const router = createRouter({
  history: isCapacitorNative() ? createWebHashHistory() : createWebHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  },
})

router.onError((err) => {
  if (typeof window === 'undefined') return

  const message = String(err?.message || err || '')
  const chunkLoadFailed = /Failed to fetch dynamically imported module|Importing a module script failed|error loading dynamically imported module|Load failed/i.test(message)
  if (!chunkLoadFailed) return

  const key = 'ahoy:chunk-reload-at'
  const lastReload = Number(sessionStorage.getItem(key) || 0)
  const now = Date.now()
  if (now - lastReload < 10000) return

  sessionStorage.setItem(key, String(now))
  window.location.reload()
})

// Circuit Breaker: Prevent infinite redirect loops (flashing)
const historyStack = []
router.beforeEach((to, from, next) => {
  const now = Date.now()
  historyStack.push({ path: to.path, time: now })

  // Keep history manageable
  if (historyStack.length > 10) historyStack.shift()

  // Check for rapid oscillation pattern: A -> B -> A -> B within 2 seconds
  if (historyStack.length >= 4) {
    const [a, b, c, d] = historyStack.slice(-4)
    // Same paths alternating?
    if (a.path === c.path && b.path === d.path && a.path !== b.path) {
      // Is it happening fast?
      if (d.time - a.time < 2000) {
        console.error(`[Router] Redirect loop detected: ${a.path} <-> ${b.path}. Aborting navigation to /${to.name || 'path'}`)
        return next(false)
      }
    }
  }

  // Debug logging for troubleshooting
  if (import.meta.env.DEV || window.location.search.includes('debug=1')) {
    console.log(`[Router] ${from.path} -> ${to.path}`)
  }

  next()
})

// Update document title and meta description on navigation
router.afterEach((to) => {
  const title = to.meta?.title
  if (title) document.title = title

  const desc = to.meta?.description
  if (desc) {
    const el = document.querySelector('meta[name="description"]')
    if (el) el.setAttribute('content', desc)
  }
  routeSeoMeta(to)
})

export default router
