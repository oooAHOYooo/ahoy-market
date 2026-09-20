<template>
  <header class="app-header">
    <!-- Mobile top nav — minimal, notifications only -->
    <nav class="mobile-top-nav" :class="{ 'mobile-top-nav--forced': forceMobileShell }">
      <div class="mobile-nav-spacer"></div>
      <button
        class="mobile-notification-btn"
        @click="$emit('toggle-notifications')"
        :aria-label="`Notifications ${notificationCount > 0 ? notificationCount : ''}`"
        :title="`Notifications ${notificationCount > 0 ? notificationCount : ''}`"
      >
        <i class="fas fa-bell"></i>
        <span v-if="notificationCount > 0" class="notification-badge">{{ notificationCount }}</span>
      </button>
    </nav>

    <!-- Navbar (desktop: breadcrumbs + account; mobile: nothing) -->
    <nav class="navbar desktop-nav">
      <div class="nav-container ds-statusbar" :class="{ 'has-channel-switcher': isLiveTv && liveTvStore.channels.length }">
        <div class="ds-statusbar__left">
          <div class="nav-history desktop-only flex" aria-label="History navigation">
            <button type="button" class="nav-history-btn" title="Back" aria-label="Back" @click="goBack">
              <i class="fas fa-chevron-left" aria-hidden="true"></i>
            </button>
            <button type="button" class="nav-history-btn" title="Forward" aria-label="Forward" @click="goForward">
              <i class="fas fa-chevron-right" aria-hidden="true"></i>
            </button>
          </div>
          <nav class="ds-crumbs" aria-label="Location">
            <template v-for="(c, idx) in breadcrumbs" :key="idx">
              <span class="ds-crumbs__item">
                <router-link v-if="c.href && idx < breadcrumbs.length - 1" :to="c.href" class="ds-crumbs__link">{{ c.label }}</router-link>
                <span v-else :class="idx === breadcrumbs.length - 1 ? 'ds-crumbs__current' : 'ds-crumbs__muted'">{{ c.label }}</span>
              </span>
              <span v-if="idx < breadcrumbs.length - 1" class="ds-crumbs__sep">›</span>
            </template>
          </nav>
        </div>
        <!-- Center: AHOY TV channel switcher (contextual) -->
        <div v-if="isLiveTv && liveTvStore.channels.length" class="ds-statusbar__center">
          <div class="ltv-nav-switcher">
            <template v-for="(ch, idx) in liveTvStore.channels" :key="ch.id">
              <span class="ltv-nav-pipe">|</span>
              <button
                class="ltv-nav-ch"
                :class="{ active: liveTvStore.selectedChannelIdx === idx }"
                :style="liveTvStore.selectedChannelIdx === idx ? { '--ch-color': channelColors[idx % 4] } : {}"
                @click="liveTvStore.selectChannel(idx)"
                :title="ch.name"
              >{{ ch.name }}</button>
            </template>
            <span class="ltv-nav-pipe">|</span>
          </div>
        </div>

        <div class="ds-statusbar__right" :class="{ 'has-notifications': unreadCount > 0 }">
          <!-- Account username + settings gear live in the sidebar footer now (AppSidebar.vue) -->
          <button
            class="notification-btn desktop-only flex"
            @click="$emit('toggle-notifications')"
            :aria-label="`Notifications ${unreadCount > 0 ? unreadCount : ''}`"
            :title="`Notifications ${unreadCount > 0 ? unreadCount : ''}`"
          >
            <i class="fas fa-bell"></i>
            <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount }}</span>
          </button>
        </div>
      </div>
    </nav>
  </header>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useNotificationCenter } from '../composables/useNotificationCenter'
import { useLiveTvStore } from '../stores/liveTv'
defineProps({
  mobileMenuOpen: { type: Boolean, default: false },
})
defineEmits(['toggle-mobile-menu', 'toggle-notifications'])

const route = useRoute()
const { notifications } = useNotificationCenter()
const liveTvStore = useLiveTvStore()
const isLiveTv = computed(() => route.name === 'live-tv')
const notificationCount = computed(() => notifications.value.length)
const unreadCount = computed(() => notifications.value.filter((notification) => !notification.read).length)
const channelColors = ['#00a2ff', '#00e5ff', '#0066ff', '#7c3aed']

const forceMobileShell = ref(false)

const breadcrumbs = computed(() => {
  const name = route.name || 'home'
  const slug = (route.params.slug || '').replace(/-/g, ' ')
  const slugLabel = slug ? slug.charAt(0).toUpperCase() + slug.slice(1) : ''
  const map = {
    home: [{ label: 'Explore', href: '/' }, { label: 'Home', href: null }],
    music: [{ label: 'Music', href: '/music' }, { label: 'Browse', href: null }],
    'music-detail': [{ label: 'Music', href: '/music' }, { label: 'Track', href: null }],
    shows: [{ label: 'Videos', href: '/videos' }, { label: 'Browse', href: null }],
    videos: [{ label: 'Videos', href: '/videos' }, { label: 'Browse', href: null }],
    'show-detail': [{ label: 'Videos', href: '/videos' }, { label: slugLabel || 'Video', href: null }],
    'video-detail': [{ label: 'Videos', href: '/videos' }, { label: slugLabel || 'Video', href: null }],
    'live-tv': [{ label: 'AHOY TV', href: '/live-tv' }, { label: 'Watch', href: null }],
    artists: [{ label: 'Artists', href: '/artists' }, { label: 'Browse', href: null }],
    'artist-detail': [{ label: 'Artists', href: '/artists' }, { label: slugLabel || 'Artist', href: null }],
    podcasts: [{ label: 'Podcasts', href: '/podcasts' }, { label: 'Browse', href: null }],
    'podcast-detail': [{ label: 'Podcasts', href: '/podcasts' }, { label: slugLabel || 'Show', href: null }],
    events: [{ label: 'Events', href: '/events' }, { label: 'Upcoming', href: null }],
    'event-detail': [{ label: 'Events', href: '/events' }, { label: 'Event', href: null }],
    merch: [{ label: 'Merch', href: '/merch' }, { label: 'Shop', href: null }],
    radio: [{ label: 'Radio', href: '/radio' }, { label: 'Live', href: null }],
    support: [{ label: 'Support', href: '/support' }, { label: 'Boost', href: null }],
    tab: [{ label: 'Tab', href: '/tab' }, { label: 'Your Tab', href: null }],
    'my-saves': [{ label: 'Saved', href: '/my-saves' }, { label: 'Library', href: null }],
    'recently-played': [{ label: 'Saved', href: '/my-saves' }, { label: 'Recently Played', href: null }],
    login: [{ label: 'Profile', href: null }],
    account: [{ label: 'Account', href: '/account' }, { label: 'Profile', href: null }],
    settings: [{ label: 'Settings', href: '/settings' }, { label: 'Preferences', href: null }],
    search: [{ label: 'Search', href: null }],
    dashboard: [{ label: 'Dashboard', href: null }],
    playlists: [{ label: 'Playlists', href: '/playlists' }, { label: 'Browse', href: null }],
    'playlist-detail': [{ label: 'Playlists', href: '/playlists' }, { label: 'Playlist', href: null }],
  }
  const crumb = map[name]
  if (crumb) return crumb
  const path = route.path
  if (path === '/') return [{ label: 'Explore', href: '/' }, { label: 'Home', href: null }]
  const parts = path.split('/').filter(Boolean)
  const out = []
  let href = ''
  parts.forEach((p, i) => {
    href += '/' + p
    const label = (p.replace(/-/g, ' ') || (i === parts.length - 1 ? 'Page' : '')).replace(/^\w/, w => w.toUpperCase())
    out.push({ label, href: i < parts.length - 1 ? href : null })
  })
  return out.length ? out : [{ label: 'Explore', href: '/' }, { label: 'Home', href: null }]
})

function goBack() {
  window.history.back()
}
function goForward() {
  window.history.forward()
}

onMounted(() => {
  forceMobileShell.value = document.body.classList.contains('force-mobile-shell')
})
</script>

<style scoped>
/* Mobile top nav */
.mobile-top-nav {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 8px 12px;
  gap: 12px;
  background: var(--bg-primary, #1a1a1a);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  position: relative;
  z-index: 1000;
}

/* Hide on desktop unless the runtime forces the tablet/mobile shell. */
@media (min-width: 1025px) {
  .mobile-top-nav:not(.mobile-top-nav--forced) {
    display: none;
  }
}

.mobile-top-nav.mobile-top-nav--forced {
  display: flex;
}

/* Pulsing animation for notification badge */
@keyframes pulse-badge {
  0%, 100% {
    box-shadow: 0 0 0 0 rgba(255, 59, 48, 0.7);
  }
  50% {
    box-shadow: 0 0 0 6px rgba(255, 59, 48, 0);
  }
}

.notification-badge {
  animation: pulse-badge 2s infinite;
}

.mobile-nav-spacer {
  flex: 1;
}

.mobile-notification-btn,
.notification-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: none;
  border: none;
  color: inherit;
  font-size: 18px;
  cursor: pointer;
  position: relative;
  padding: 0;
  border-radius: 8px;
  transition: background 0.2s;
}

.account-icon-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: none;
  border: none;
  color: inherit;
  font-size: 18px;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s;
  text-decoration: none;
  padding: 0;
}

.account-icon-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.account-icon-btn i,
.notification-btn i,
.mobile-notification-btn i {
  display: block;
  line-height: 1;
}

.account-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px 4px 6px;
  border-radius: 8px;
  color: inherit;
  text-decoration: none;
  transition: background 0.2s;
  line-height: 1;
}

.account-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.account-btn i {
  font-size: 16px;
  line-height: 1;
  display: flex;
  align-items: center;
}

.account-btn-label {
  font-size: 12px;
  font-weight: 500;
  max-width: 90px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  opacity: 0.88;
}

.mobile-notification-btn:hover,
.notification-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.notification-badge {
  position: absolute;
  top: -4px;
  right: -4px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 18px;
  height: 18px;
  background: #ff3b30;
  border-radius: 50%;
  font-size: 10px;
  font-weight: 600;
  color: white;
}

/* Desktop navbar visibility */
.navbar.desktop-nav {
  display: flex;
  -webkit-app-region: drag;
}

.navbar.desktop-nav button,
.navbar.desktop-nav a,
.navbar.desktop-nav .ds-crumbs__link,
.navbar.desktop-nav .account-icon-btn,
.navbar.desktop-nav .account-btn {
  -webkit-app-region: no-drag;
}

@media (max-width: 1024px) {
  .navbar.desktop-nav {
    display: none;
  }
}
</style>
