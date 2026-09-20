<template>
  <aside class="app-sidebar" :class="{ 'is-collapsed': collapsed }" aria-label="Primary">
    <div class="app-sidebar-header" :class="{ 'is-collapsed': collapsed }">
      <router-link class="app-sidebar-logo" to="/" aria-label="Ahoy Home">
        <img :src="logoUrl" alt="Ahoy Indie Media" @error="logoError = true" />
        <span v-if="logoError" class="app-sidebar-logo-text">Ahoy</span>
      </router-link>
      <div class="app-sidebar-header-spacer"></div>
      <button
        type="button"
        class="app-sidebar-toggle"
        :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        @click="toggleSidebar"
      >
        <i :class="collapsed ? 'fas fa-angles-right' : 'fas fa-angles-left'" aria-hidden="true"></i>
      </button>
    </div>

    <div class="app-sidebar-divider-line"></div>

    <div class="app-sidebar-scroll-wrap">
      <nav class="app-sidebar-nav" aria-label="Primary navigation">
        <div
          v-for="(group, idx) in navGroups"
          :key="group.label"
          class="app-sidebar-group"
          :class="{ 'has-divider': idx < navGroups.length - 1 }"
        >
          <div v-if="!collapsed" class="app-sidebar-group-label">{{ group.label }}</div>
          <router-link
            v-for="item in group.items"
            :key="item.to"
            :to="item.to"
            class="app-sidebar-item"
            :class="{ active: item.active }"
            :title="item.label"
            @mouseenter="startHover"
            @mouseleave="clearHover"
          >
            <span class="app-sidebar-chip">
              <i :class="item.icon" aria-hidden="true"></i>
            </span>
            <span v-if="!collapsed" class="app-sidebar-item-label">{{ item.label }}</span>
            <span v-if="!collapsed && item.badge" class="app-sidebar-badge">{{ item.badge }}</span>
          </router-link>
        </div>
      </nav>
      <div class="app-sidebar-fade app-sidebar-fade-top"></div>
      <div class="app-sidebar-fade app-sidebar-fade-bottom"></div>
    </div>

    <div class="app-sidebar-footer">
      <router-link to="/settings" class="app-sidebar-item app-sidebar-footer-item" :class="{ active: route.path === '/settings' }" title="Settings">
        <span class="app-sidebar-chip"><i class="fas fa-gear" aria-hidden="true"></i></span>
        <span v-if="!collapsed" class="app-sidebar-item-label">Settings</span>
      </router-link>
      <router-link to="/account" class="app-sidebar-item app-sidebar-footer-item app-sidebar-account" :class="{ active: route.path === '/account' }" title="Account">
        <span class="app-sidebar-avatar">
          <img v-if="avatarUrl" :src="avatarUrl" alt="" />
          <i v-else class="fas fa-user" aria-hidden="true"></i>
        </span>
        <template v-if="!collapsed">
          <span class="app-sidebar-item-label app-sidebar-account-name">{{ displayName }}</span>
          <i class="fas fa-chevron-up app-sidebar-account-chevron" aria-hidden="true"></i>
        </template>
      </router-link>
    </div>
  </aside>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useNotificationCenter } from '../composables/useNotificationCenter'
import { useSidebarCollapse } from '../composables/useSidebarCollapse'
import { useAuth } from '../composables/useAuth'

const route = useRoute()
const { notifications } = useNotificationCenter()
const { collapsed, toggleSidebar } = useSidebarCollapse()
const auth = useAuth()

const whatsNewDotTypes = new Set(['info', 'video', 'podcast', 'artist', 'music', 'events'])
const whatsNewUnreadCount = computed(() => (
  route.path.startsWith('/whats-new')
    ? 0
    : notifications.value.filter((n) => !n.read && whatsNewDotTypes.has(n.type)).length
))

const displayName = computed(() => auth.isLoggedIn.value ? auth.username.value : 'Guest')
const avatarUrl = computed(() => auth.user?.value?.avatar_url || '')

const logoUrl = '/static/img/ahoy-logo.png'
const logoError = ref(false)

const navGroups = computed(() => ([
  {
    label: 'Discover',
    items: [
      { to: '/', icon: 'fas fa-compass', label: 'Explore', active: route.path === '/' },
      { to: '/search', icon: 'fas fa-magnifying-glass', label: 'Search', active: route.path === '/search' },
      {
        to: '/whats-new',
        icon: 'fas fa-bullhorn',
        label: "What's New",
        active: route.path.startsWith('/whats-new'),
        badge: whatsNewUnreadCount.value > 0 ? whatsNewUnreadCount.value : null,
      },
    ],
  },
  {
    label: 'Play',
    items: [
      { to: '/music', icon: 'fas fa-music', label: 'Music', active: route.path === '/music' },
      { to: '/podcasts', icon: 'fas fa-podcast', label: 'Podcasts', active: route.path.startsWith('/podcasts') },
      { to: '/live-tv', icon: 'fas fa-tv', label: 'AHOY TV', active: route.path === '/live-tv' },
      { to: '/videos', icon: 'fas fa-video', label: 'Videos', active: route.path === '/shows' || route.path === '/videos' },
      { to: '/poems', icon: 'fas fa-feather', label: 'Poems', active: route.path === '/poems' },
      { to: '/radio', icon: 'fas fa-tower-broadcast', label: 'Radio', active: route.path === '/radio' },
      { to: '/my-saves', icon: 'fas fa-bookmark', label: 'Saved', active: route.path === '/my-saves' || route.path === '/recently-played' },
    ],
  },
  {
    label: 'Community',
    items: [
      { to: '/artists', icon: 'fas fa-users', label: 'Artists', active: route.path === '/artists' },
      { to: '/studio', icon: 'fas fa-camera', label: 'Studio', active: route.path.startsWith('/studio') },
    ],
  },
]))

const hoverTimers = new WeakMap()

function clearHover(event) {
  const el = event.currentTarget
  const timers = hoverTimers.get(el)
  if (timers) {
    window.clearTimeout(timers.tint)
    window.clearTimeout(timers.shimmer)
    hoverTimers.delete(el)
  }
  el.style.setProperty('--hover-fill', '0')
  el.style.setProperty('--hover-shimmer', '0')
}

function startHover(event) {
  const el = event.currentTarget
  clearHover(event)
  const timers = {
    tint: window.setTimeout(() => {
      el.style.setProperty('--hover-fill', '1')
    }, 160),
    shimmer: window.setTimeout(() => {
      el.style.setProperty('--hover-shimmer', '1')
    }, 620),
  }
  hoverTimers.set(el, timers)
}
</script>

<style scoped>
.app-sidebar {
  display: flex;
  flex-direction: column;
  width: 208px;
  flex: 0 0 208px;
  padding: 18px 10px 14px;
  background: rgba(14, 18, 28, 0.42);
  backdrop-filter: blur(30px) saturate(180%);
  -webkit-backdrop-filter: blur(30px) saturate(180%);
  border-right: 1px solid rgba(255, 255, 255, 0.07);
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.03);
  position: sticky;
  top: var(--ds-topbar-height, 44px);
  height: calc(100vh - var(--ds-topbar-height, 44px));
  transition: width 0.22s var(--ease-out, cubic-bezier(0.4, 0, 0.2, 1));
}

.app-sidebar.is-collapsed {
  width: 68px;
  flex: 0 0 68px;
  padding: 18px 8px 14px;
}

.app-sidebar-header {
  display: flex;
  align-items: center;
  gap: 9px;
  padding: 2px 4px 16px;
}

.app-sidebar-header.is-collapsed {
  justify-content: center;
}

.app-sidebar-logo {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.app-sidebar-logo img {
  width: 104px;
  height: auto;
  max-height: 32px;
  object-fit: contain;
  border-radius: 0;
  filter: drop-shadow(0 2px 7px rgba(0, 0, 0, 0.28));
  transition: opacity 0.15s var(--ease-out, cubic-bezier(0.4, 0, 0.2, 1));
}

.app-sidebar-logo:hover img {
  opacity: 0.82;
}

.app-sidebar.is-collapsed .app-sidebar-logo img {
  width: 42px;
  max-height: 22px;
}

.app-sidebar-logo-text {
  font-size: 1.1rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.95);
}

.app-sidebar-header-spacer {
  flex: 1;
}

.app-sidebar-toggle {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  border-radius: 6px;
  border: 1px solid rgba(255, 255, 255, 0.09);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.5);
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 9px;
  transition: background 0.15s var(--ease-out, cubic-bezier(0.4, 0, 0.2, 1));
}

.app-sidebar-toggle:hover {
  background: rgba(255, 255, 255, 0.09);
}

.app-sidebar-divider-line {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.12), transparent);
  margin: 0 2px 14px;
  flex-shrink: 0;
}

.app-sidebar-scroll-wrap {
  position: relative;
  flex: 1 1 auto;
  min-height: 0;
}

.app-sidebar-nav {
  height: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}

.app-sidebar-fade {
  position: absolute;
  left: 0;
  right: 0;
  height: 18px;
  pointer-events: none;
}

.app-sidebar-fade-top {
  top: 0;
  background: linear-gradient(rgba(15, 17, 24, 0.55), transparent);
}

.app-sidebar-fade-bottom {
  bottom: 0;
  background: linear-gradient(transparent, rgba(15, 17, 24, 0.55));
}

.app-sidebar-group {
  margin-bottom: 16px;
  padding-bottom: 16px;
}

.app-sidebar-group.has-divider {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.app-sidebar-group-label {
  font-size: 10px;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(180, 200, 255, 0.4);
  font-weight: 700;
  padding: 0 10px 8px;
  white-space: nowrap;
}

.app-sidebar-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 9px;
  height: 36px;
  padding: 0 10px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.8);
  border: 1px solid transparent;
  cursor: pointer;
  font-size: 13px;
  font-weight: 500;
  width: 100%;
  margin-bottom: 2px;
  text-decoration: none;
  transition: background 0.15s var(--ease-out, cubic-bezier(0.4, 0, 0.2, 1));
  --hover-fill: 0;
  --hover-shimmer: 0;
}

.app-sidebar.is-collapsed .app-sidebar-item {
  padding: 0;
  justify-content: center;
}

.app-sidebar-item:hover {
  background: rgba(255, 255, 255, calc(0.045 + (0.02 * var(--hover-fill))));
}

.app-sidebar-item:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(255, 0, 96, 0.15);
}

.app-sidebar-chip {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  flex-shrink: 0;
  border-radius: 8px;
  background: transparent;
  transition: background 0.15s var(--ease-out, cubic-bezier(0.4, 0, 0.2, 1));
}

.app-sidebar-chip i {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
}

.app-sidebar-item-label {
  flex: 1;
  min-width: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  letter-spacing: -0.005em;
}

.app-sidebar-badge {
  flex-shrink: 0;
  padding: 2px 7px;
  border-radius: var(--pill, 999px);
  background: rgba(255, 0, 96, 0.9);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 1.4;
}

/* Active state: tinted row background + icon chip highlight */
.app-sidebar-item.active {
  background: rgba(255, 0, 96, 0.12);
  border-color: rgba(255, 133, 162, 0.2);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.app-sidebar-item.active .app-sidebar-chip {
  background: rgba(255, 255, 255, 0.1);
}

.app-sidebar-item.active .app-sidebar-chip i {
  color: #ff9ab7;
}

.app-sidebar-item.active .app-sidebar-item-label {
  color: #fff;
  font-weight: 600;
}

.app-sidebar-footer {
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.06);
  margin-top: 2px;
  flex-shrink: 0;
}

.app-sidebar-account {
  height: 40px;
  margin-top: 2px;
}

.app-sidebar-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  flex-shrink: 0;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.app-sidebar-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.app-sidebar-account-name {
  font-size: 13px;
  font-weight: 600;
}

.app-sidebar-account-chevron {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.4);
  flex-shrink: 0;
}

/* Hide the desktop cart shortcut; checkout remains reachable through boost flows. */
.app-sidebar-item[href*="/checkout?type=cart"],
.app-sidebar-item[href*="/checkout&type=cart"],
.app-sidebar-item[href*="type=cart"] {
  display: none !important;
}
</style>
