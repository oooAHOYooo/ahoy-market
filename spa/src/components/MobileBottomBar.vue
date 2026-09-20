<template>
  <section
    class="mobile-bottom-bar mobile-only"
    aria-label="Mobile bottom bar"
  >
    <header class="mobile-bottom-bar-switcher" aria-label="Mobile deck switcher">
      <button
        type="button"
        class="mobile-bottom-bar-switcher-btn"
        :class="{ active: deckMode === 'nav' }"
        @click="setDeckMode('nav')"
        aria-label="Open browse deck"
      >
        <i class="fas fa-th-large" aria-hidden="true"></i>
        <span>Browse</span>
      </button>
      <button
        type="button"
        class="mobile-bottom-bar-switcher-btn"
        :class="{ active: deckMode === 'player' }"
        @click="setDeckMode('player')"
        aria-label="Open player deck"
      >
        <i class="fas fa-compact-disc" aria-hidden="true"></i>
        <span>Player</span>
      </button>
      <button
        type="button"
        class="mobile-bottom-bar-switcher-btn"
        :class="{ active: deckMode === 'utility' }"
        @click="setDeckMode('utility')"
        aria-label="Open tools deck"
      >
        <i class="fas fa-sliders-h" aria-hidden="true"></i>
        <span>Tools</span>
      </button>
    </header>

    <div class="mobile-bottom-bar-stage">
      <Transition name="mobile-bottom-bar-panel" mode="out-in">
        <section
          v-if="deckMode === 'nav'"
          key="nav"
          class="mobile-bottom-bar-panel mobile-bottom-bar-panel--nav"
          aria-label="Browse deck"
        >
          <nav class="mobile-bottom-bar-nav" aria-label="Mobile navigation">
            <router-link to="/" class="mobile-bottom-bar-tab" :class="{ active: route.path === '/' }">
              <i class="fas fa-home"></i>
              <span>Home</span>
            </router-link>
            <router-link to="/search" class="mobile-bottom-bar-tab" :class="{ active: route.path === '/search' }">
              <i class="fas fa-search"></i>
              <span>Search</span>
            </router-link>
            <router-link to="/music" class="mobile-bottom-bar-tab" :class="{ active: route.path === '/music' }">
              <i class="fas fa-music"></i>
              <span>Music</span>
            </router-link>
            <router-link to="/podcasts" class="mobile-bottom-bar-tab" :class="{ active: route.path.startsWith('/podcasts') }">
              <i class="fas fa-podcast"></i>
              <span>Podcasts</span>
            </router-link>
            <router-link to="/live-tv" class="mobile-bottom-bar-tab" :class="{ active: route.path === '/live-tv' }">
              <i class="fas fa-tv"></i>
              <span>AHOY TV</span>
            </router-link>
            <router-link to="/videos" class="mobile-bottom-bar-tab" :class="{ active: route.path === '/shows' || route.path === '/videos' }">
              <i class="fas fa-video"></i>
              <span>Videos</span>
            </router-link>
            <router-link to="/radio" class="mobile-bottom-bar-tab" :class="{ active: route.path === '/radio' }">
              <i class="fas fa-broadcast-tower"></i>
              <span>Radio</span>
            </router-link>
            <router-link to="/artists" class="mobile-bottom-bar-tab" :class="{ active: route.path === '/artists' }">
              <i class="fas fa-users"></i>
              <span>Artists</span>
            </router-link>
            <router-link
              to="/whats-new"
              class="mobile-bottom-bar-tab mobile-bottom-bar-tab--whats-new"
              :class="{ active: route.path.startsWith('/whats-new') }"
              aria-label="What's New"
            >
              <span class="mobile-bottom-bar-tab-icon-wrap">
                <i class="fas fa-bullhorn"></i>
                <span v-if="hasWhatsNewDot" class="mobile-bottom-bar-tab-dot" aria-hidden="true"></span>
              </span>
              <span>What's New</span>
            </router-link>
            <router-link to="/studio" class="mobile-bottom-bar-tab" :class="{ active: route.path.startsWith('/studio') }">
              <i class="fas fa-camera"></i>
              <span>Studio</span>
            </router-link>
            <router-link to="/support" class="mobile-bottom-bar-tab" :class="{ active: route.path === '/support' }">
              <i class="fas fa-bolt"></i>
              <span>Boosts</span>
            </router-link>
            <router-link to="/account" class="mobile-bottom-bar-tab" :class="{ active: route.path === '/account' || route.path === '/settings' }">
              <span class="mobile-bottom-bar-tab-icon-wrap">
                <i class="fas fa-user-circle"></i>
                <span :class="`sync-indicator sync-${syncStatus}`" :title="`Sync status: ${syncStatus}`"></span>
              </span>
              <span>Profile</span>
            </router-link>
          </nav>
        </section>

        <section
          v-else-if="deckMode === 'player'"
          key="player"
          class="mobile-bottom-bar-panel mobile-bottom-bar-panel--player"
          aria-label="Player deck"
        >
          <MobilePlayerDeck />
        </section>

        <section
          v-else
          key="utility"
          class="mobile-bottom-bar-panel mobile-bottom-bar-panel--utility"
          aria-label="Tools deck"
        >
          <UtilityDeck @toggle-notifications="$emit('toggle-notifications')" />
        </section>
      </Transition>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import MobilePlayerDeck from './MobilePlayerDeck.vue'
import UtilityDeck from './UtilityDeck.vue'
import { useMobileCollapse } from '../composables/useMobileCollapse'
import { useNotificationCenter } from '../composables/useNotificationCenter'
import { useSync } from '../composables/useSync'

defineEmits(['toggle-notifications'])

const route = useRoute()
const { deckMode, setDeckMode } = useMobileCollapse()
const { status: syncStatus } = useSync()
const { notifications } = useNotificationCenter()
const whatsNewDotTypes = new Set(['info', 'video', 'podcast', 'artist', 'music', 'events'])

const hasWhatsNewDot = computed(() => (
  !route.path.startsWith('/whats-new') &&
  notifications.value.some((notification) => !notification.read && whatsNewDotTypes.has(notification.type))
))
</script>

<style scoped>
.mobile-bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 11200;
  display: block !important;
  width: 100%;
  max-width: 100vw;
  height: calc(var(--mobile-bottom-bar-height, 152px) + env(safe-area-inset-bottom, 0px));
  padding: 0;
  margin: 0;
  overflow: hidden;
  background:
    linear-gradient(180deg,
      color-mix(in srgb, var(--primary-color, #00a2ff) 12%, rgba(10, 12, 16, 0.96)) 0%,
      rgba(6, 8, 12, 0.98) 100%);
  border-top: 1px solid color-mix(in srgb, var(--primary-color, #00a2ff) 18%, rgba(255, 255, 255, 0.08));
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, var(--primary-color, #00a2ff) 18%, rgba(255, 255, 255, 0.05)),
    0 -10px 28px rgba(0, 0, 0, 0.36);
  backdrop-filter: blur(24px) saturate(140%);
  -webkit-backdrop-filter: blur(24px) saturate(140%);
}

.mobile-bottom-bar-switcher {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 4px;
  padding: 4px 7px 2px;
  position: absolute;
  left: 0;
  right: 0;
  top: 0;
  z-index: 3;
}

.mobile-bottom-bar-switcher-btn {
  min-height: 28px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  border: 1px solid rgba(255, 255, 255, 0.045);
  border-radius: 12px;
  background:
    radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 0.05), transparent 54%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), rgba(255, 255, 255, 0.014));
  backdrop-filter: blur(12px) saturate(125%);
  -webkit-backdrop-filter: blur(12px) saturate(125%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.06),
    0 2px 6px rgba(0, 0, 0, 0.16);
  color: rgba(255, 255, 255, 0.55);
  font: inherit;
  font-size: 8.5px;
  font-weight: 500;
  letter-spacing: 0.01em;
  -webkit-tap-highlight-color: transparent;
  transition: all 0.2s ease;
}

.mobile-bottom-bar-switcher-btn.active {
  border-color: color-mix(in srgb, var(--primary-color, #00a2ff) 15%, rgba(255, 255, 255, 0.16));
  background:
    radial-gradient(circle at 50% 0%, color-mix(in srgb, var(--primary-color, #00a2ff) 10%, rgba(255, 255, 255, 0.08)), transparent 54%),
    linear-gradient(180deg, color-mix(in srgb, var(--primary-color, #00a2ff) 8%, rgba(255, 255, 255, 0.05)), rgba(255, 255, 255, 0.015));
  color: rgba(255, 255, 255, 0.9);
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, var(--primary-color, #00a2ff) 25%, rgba(255, 255, 255, 0.1)),
    0 2px 8px rgba(0, 0, 0, 0.25);
}

.mobile-bottom-bar-switcher-btn i {
  font-size: 10px;
}

.mobile-bottom-bar-stage {
  position: absolute;
  left: 0;
  right: 0;
  top: 32px;
  bottom: 0;
  z-index: 1;
  min-height: 0;
  overflow: hidden;
}

.mobile-bottom-bar-panel {
  height: 100%;
  min-height: 0;
}

.mobile-bottom-bar-panel--nav {
  padding: 3px 6px calc(6px + env(safe-area-inset-bottom, 0px));
}

.mobile-bottom-bar-panel--player {
  padding: 0 6px calc(6px + env(safe-area-inset-bottom, 0px));
}

.mobile-bottom-bar-panel--utility {
  padding: 0 6px calc(6px + env(safe-area-inset-bottom, 0px));
}

.mobile-bottom-bar-nav {
  height: 100%;
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  grid-auto-rows: 40px;
  gap: 4px;
}

.mobile-bottom-bar-tab {
  min-width: 0;
  min-height: 0;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 4px 2px 5px;
  border: 1px solid rgba(255, 255, 255, 0.035);
  border-radius: 12px;
  background:
    radial-gradient(circle at 50% 0%, rgba(255, 255, 255, 0.04), transparent 54%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.025), rgba(255, 255, 255, 0.005));
  backdrop-filter: blur(10px) saturate(125%);
  -webkit-backdrop-filter: blur(10px) saturate(125%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.05),
    0 2px 5px rgba(0, 0, 0, 0.12);
  color: rgba(255, 255, 255, 0.55);
  text-decoration: none;
  -webkit-tap-highlight-color: transparent;
  transition: all 0.2s ease;
}

.mobile-bottom-bar-tab.active {
  color: rgba(255, 255, 255, 0.9);
  border-color: color-mix(in srgb, var(--primary-color, #00a2ff) 12%, rgba(255, 255, 255, 0.14));
  background:
    radial-gradient(circle at 50% 0%, color-mix(in srgb, var(--primary-color, #00a2ff) 8%, rgba(255, 255, 255, 0.06)), transparent 54%),
    linear-gradient(180deg, color-mix(in srgb, var(--primary-color, #00a2ff) 6%, rgba(255, 255, 255, 0.04)), rgba(255, 255, 255, 0.01));
  box-shadow:
    inset 0 1px 0 color-mix(in srgb, var(--primary-color, #00a2ff) 20%, rgba(255, 255, 255, 0.08)),
    0 4px 12px rgba(0, 0, 0, 0.2);
}

.mobile-bottom-bar-tab:active {
  background: rgba(255, 255, 255, 0.1);
  transform: scale(0.9);
}

.mobile-bottom-bar-tab i {
  position: relative;
  font-size: 15px;
  line-height: 1;
}

.mobile-bottom-bar-tab span {
  max-width: 100%;
  overflow: hidden;
  font-size: 7.25px;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mobile-bottom-bar-tab-icon-wrap {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.mobile-bottom-bar-tab-dot {
  position: absolute;
  top: -3px;
  right: -4px;
  width: 7px;
  height: 7px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--primary-color, #00a2ff) 74%, #ffffff);
  box-shadow:
    0 0 0 1px rgba(5, 7, 10, 0.88),
    0 0 8px color-mix(in srgb, var(--primary-color, #00a2ff) 34%, transparent);
}

.sync-indicator {
  position: absolute;
  top: -2px;
  right: -2px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
}

.sync-synced {
  background-color: #22c55e;
}

.sync-syncing {
  background-color: #eab308;
  animation: pulse 1.5s ease-in-out infinite;
}

.sync-offline {
  background-color: #ef4444;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.mobile-bottom-bar-panel-enter-active,
.mobile-bottom-bar-panel-leave-active {
  transition: opacity 0.12s ease, transform 0.14s ease;
}

.mobile-bottom-bar-panel-enter-from,
.mobile-bottom-bar-panel-leave-to {
  opacity: 0;
  transform: translateY(4px);
}

@media (max-width: 430px) {
  .mobile-bottom-bar-switcher {
    gap: 3px;
    padding-inline: 6px;
  }

  .mobile-bottom-bar-switcher-btn {
    font-size: 8.5px;
    gap: 3px;
  }

  .mobile-bottom-bar-nav {
    gap: 4px;
  }

  .mobile-bottom-bar-tab {
    padding: 4px 2px 5px;
  }

  .mobile-bottom-bar-tab span {
    font-size: 7.25px;
  }
}
</style>
