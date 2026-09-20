<template>
  <!-- Same structure as Flask base.html: mobile-dock (unified two-row bar) -->
  <!-- Bottom mobile dock nav — always visible (no collapse) -->
  <div class="mobile-only dock-wrapper">
    <div class="mobile-footer-logo mobile-only">
      <img :src="logoUrl" alt="Ahoy" class="mobile-footer-logo-img" />
    </div>
    <div class="mobile-dock mobile-only" role="navigation" aria-label="Mobile Navigation">
      <nav class="mobile-dock-row mobile-dock-row-secondary" aria-label="Secondary Navigation">
        <router-link to="/artists" class="mobile-tab" :class="{ active: route.path === '/artists' }">
          <i class="fas fa-users"></i>
          <span>Artists</span>
        </router-link>
        <router-link
          to="/whats-new"
          class="mobile-tab mobile-tab--whats-new"
          :class="{ active: route.path.startsWith('/whats-new') }"
          aria-label="What's New"
        >
          <span class="mobile-tab-icon-wrap">
            <i class="fas fa-bullhorn"></i>
            <span v-if="hasWhatsNewDot" class="mobile-tab-dot" aria-hidden="true"></span>
          </span>
          <span>What's New</span>
        </router-link>
        <router-link to="/studio" class="mobile-tab" :class="{ active: route.path.startsWith('/studio') }">
          <i class="fas fa-camera"></i>
          <span>Studio</span>
        </router-link>
        <router-link to="/account" class="mobile-tab" :class="{ active: route.path === '/account' || route.path === '/settings' }">
          <i class="fas fa-user-circle" style="position: relative;">
            <span :class="`sync-indicator sync-${syncStatus}`" :title="`Sync status: ${syncStatus}`"></span>
          </i>
          <span>Profile</span>
        </router-link>
        <router-link to="/my-saves" class="mobile-tab" :class="{ active: route.path === '/my-saves' || route.path === '/recently-played' }">
          <i class="fas fa-bookmark"></i>
          <span>Saved</span>
        </router-link>
      </nav>
      <nav class="mobile-dock-row mobile-dock-row-primary" aria-label="Media Navigation">
        <router-link to="/" class="mobile-tab" :class="{ active: route.path === '/' }">
          <i class="fas fa-home"></i>
          <span>Home</span>
        </router-link>
        <router-link to="/music" class="mobile-tab" :class="{ active: route.path === '/music' }">
          <i class="fas fa-music"></i>
          <span>Music</span>
        </router-link>
        <router-link to="/podcasts" class="mobile-tab" :class="{ active: route.path.startsWith('/podcasts') }">
          <i class="fas fa-podcast"></i>
          <span>Podcasts</span>
        </router-link>
        <router-link to="/live-tv" class="mobile-tab" :class="{ active: route.path === '/live-tv' }">
          <i class="fas fa-tv"></i>
          <span>AHOY TV</span>
        </router-link>
        <router-link to="/videos" class="mobile-tab" :class="{ active: route.path === '/shows' || route.path === '/videos' }">
          <i class="fas fa-video"></i>
          <span>Videos</span>
        </router-link>
        <router-link to="/radio" class="mobile-tab" :class="{ active: route.path === '/radio' }">
          <i class="fas fa-broadcast-tower"></i>
          <span>Radio</span>
        </router-link>
      </nav>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useSync } from '../composables/useSync'
import { useNotificationCenter } from '../composables/useNotificationCenter'
const route = useRoute()
const { status: syncStatus } = useSync()
const { notifications } = useNotificationCenter()
const logoUrl = '/static/img/u_ahoy23.png'
const whatsNewDotTypes = new Set(['info', 'video', 'podcast', 'artist', 'music', 'events'])

const hasWhatsNewDot = computed(() => (
  !route.path.startsWith('/whats-new') &&
  notifications.value.some((notification) => !notification.read && whatsNewDotTypes.has(notification.type))
))

const dockEl = ref(null)
let activeTab = null
let leaveTimer = null

function setSpotlight(tab, x, y) {
  if (!tab) return
  tab.style.setProperty('--mx', `${x}px`)
  tab.style.setProperty('--my', `${y}px`)
}

function onPointerMove(e) {
  const tab = e.target.closest?.('.mobile-tab')
  if (!tab) return
  if (activeTab && activeTab !== tab) {
    activeTab.classList.remove('is-tracking')
  }
  const r = tab.getBoundingClientRect()
  setSpotlight(tab, e.clientX - r.left, e.clientY - r.top)
  tab.classList.add('is-tracking')
  activeTab = tab
  if (leaveTimer) { clearTimeout(leaveTimer); leaveTimer = null }
}

function onPointerLeave() {
  leaveTimer = setTimeout(() => {
    if (activeTab) {
      activeTab.classList.remove('is-tracking')
      activeTab = null
    }
  }, 120)
}

onMounted(() => {
  const dock = document.querySelector('.mobile-dock')
  if (!dock) return
  dockEl.value = dock
  dock.addEventListener('pointermove', onPointerMove, { passive: true })
  dock.addEventListener('pointerleave', onPointerLeave, { passive: true })
  dock.addEventListener('touchend', onPointerLeave, { passive: true })
})

onBeforeUnmount(() => {
  const dock = dockEl.value
  if (!dock) return
  dock.removeEventListener('pointermove', onPointerMove)
  dock.removeEventListener('pointerleave', onPointerLeave)
  dock.removeEventListener('touchend', onPointerLeave)
  if (leaveTimer) clearTimeout(leaveTimer)
})
</script>

<style scoped>
.dock-wrapper {
  position: relative;
}

.sync-indicator {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  transition: background-color 0.3s ease;
}

.mobile-tab-icon-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.mobile-tab-dot {
  position: absolute;
  top: -4px;
  right: -5px;
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--primary-color, #ff0060) 74%, #ffffff);
  box-shadow:
    0 0 0 2px rgba(5, 7, 10, 0.88),
    0 0 10px color-mix(in srgb, var(--primary-color, #ff0060) 55%, transparent);
}

.sync-synced {
  background-color: #22c55e; /* 🟢 green */
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.6);
}

.sync-syncing {
  background-color: #eab308; /* 🟡 amber */
  box-shadow: 0 0 6px rgba(234, 179, 8, 0.6);
  animation: pulse 1.5s ease-in-out infinite;
}

.sync-offline {
  background-color: #ef4444; /* 🔴 red */
  box-shadow: 0 0 6px rgba(239, 68, 68, 0.4);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

@media (max-width: 430px) {
  .mobile-tab--whats-new span {
    font-size: 7px;
    letter-spacing: 0;
  }
}
</style>
