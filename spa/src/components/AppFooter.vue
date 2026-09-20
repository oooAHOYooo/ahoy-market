<template>
  <footer class="app-footer">
    <div class="footer-content">
      <!-- Column 1: Brand / Logo -->
      <div class="footer-column footer-brand-column">
        <div class="footer-logo">
          <img :src="logoUrl" alt="Ahoy Indie Media" class="retro-logo-img primary-footer-logo" />
        </div>
        <p class="footer-tagline">Your gateway to independent music discovery and organization</p>
      </div>

      <!-- Column 2: App Navigation -->
      <div class="footer-column">
        <h4 class="footer-column-title footer-nav-title">App Navigation</h4>
        <nav class="footer-nav" aria-label="App navigation">
          <router-link
            v-for="item in appNavItems"
            :key="item.to"
            :to="item.to"
            class="footer-nav-link"
            :class="{ active: isActive(item) }"
          >
            <i :class="item.icon" aria-hidden="true"></i>
            <span>{{ item.label }}</span>
          </router-link>
        </nav>
      </div>

      <!-- Column 3: Legal -->
      <div class="footer-column">
        <h4 class="footer-column-title">Legal</h4>
        <ul>
          <li><router-link to="/about">About</router-link></li>
          <li><router-link to="/privacy">Privacy Policy</router-link></li>
          <li><router-link to="/terms">Terms of Service</router-link></li>
          <li><router-link to="/security">Security</router-link></li>
        </ul>
      </div>

      <!-- Column 4: Developer -->
      <div class="footer-column">
        <h4 class="footer-column-title">Developer</h4>
        <ul>
          <li><router-link to="/sitemap">Sitemap</router-link></li>
        </ul>
      </div>
    </div>

    <div class="footer-bottom">
      <p class="footer-copyright">&copy; 2026 Ahoy Indie Media. All rights reserved.</p>
      <div v-if="showTimeline" class="footer-timeline" @click="onSeek">
        <div class="footer-timeline-meta">
          <span class="footer-timeline-label">{{ timelineLabel }}</span>
          <span class="footer-timeline-time">{{ formatTime(playerStore.currentTime) }} / {{ formatTime(playerStore.duration) }}</span>
        </div>
        <div class="footer-timeline-track" aria-hidden="true">
          <div class="footer-timeline-fill" :style="{ width: `${timelineProgress}%` }"></div>
        </div>
      </div>
      <p class="footer-refresh mobile-only" style="margin-top: 8px; font-size: 0.85rem; opacity: 0.85;">
        Having trouble? <a href="/refresh">Get the latest version</a>
      </p>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { usePlayerStore } from '../stores/player'

const playerStore = usePlayerStore()
const route = useRoute()

// Retro logo path
const logoUrl = '/static/img/u_ahoy23.png'

const appNavItems = [
  { to: '/', label: 'Explore', icon: 'fas fa-compass', exact: true },
  { to: '/search', label: 'Search', icon: 'fas fa-search', exact: true },
  { to: '/whats-new', label: "What's New", icon: 'fas fa-bullhorn', startsWith: true },
  { to: '/music', label: 'Music', icon: 'fas fa-music' },
  { to: '/podcasts', label: 'Podcasts', icon: 'fas fa-podcast' },
  { to: '/live-tv', label: 'AHOY TV', icon: 'fas fa-tv' },
  { to: '/videos', label: 'Videos', icon: 'fas fa-video', activePaths: ['/videos', '/shows'] },
  { to: '/radio', label: 'Radio', icon: 'fas fa-broadcast-tower' },
  { to: '/artists', label: 'Artists', icon: 'fas fa-users' },
  { to: '/studio', label: 'Studio', icon: 'fas fa-camera', startsWith: true },
  { to: '/my-saves', label: 'Saved', icon: 'fas fa-bookmark', activePaths: ['/my-saves', '/recently-played'] },
  { to: '/settings', label: 'Settings', icon: 'fas fa-cog' },
]

const showTimeline = computed(() => playerStore.currentTrack && playerStore.duration > 0)
const timelineProgress = computed(() => {
  if (!playerStore.duration) return 0
  return Math.max(0, Math.min(100, (playerStore.currentTime / playerStore.duration) * 100))
})
const timelineLabel = computed(() => playerStore.currentTrack?.title || 'Nothing playing')

function formatTime(seconds) {
  if (!seconds || !isFinite(seconds)) return '0:00'
  const m = Math.floor(seconds / 60)
  const s = Math.floor(seconds % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}

function isActive(item) {
  if (item.exact) return route.path === item.to
  if (item.activePaths) return item.activePaths.includes(route.path) || item.activePaths.some((path) => route.path.startsWith(`${path}/`))
  if (item.startsWith) return route.path.startsWith(item.to)
  return route.path === item.to || route.path.startsWith(`${item.to}/`)
}

function onSeek(event) {
  if (!playerStore.duration) return
  const rect = event.currentTarget.getBoundingClientRect()
  const percent = ((event.clientX - rect.left) / rect.width) * 100
  playerStore.seek(Math.max(0, Math.min(100, percent)))
}
</script>

<style scoped>
.primary-footer-logo {
  max-width: 220px;
  filter: none;
  transition: none;
}

.retro-logo-img {
  width: 100%;
  height: auto;
  display: block;
  object-fit: contain;
}

/* Ensure consistent spacing with tagline */
.footer-tagline {
  margin-top: 15px;
}

.footer-nav-title {
  margin-bottom: 14px;
}

.footer-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.footer-nav-link {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 2px 10px;
  padding: 9px 16px;
  border-radius: 12px;
  color: #b0b0b0;
  text-decoration: none;
  position: relative;
  isolation: isolate;
  overflow: hidden;
  transition: background 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease, color 0.2s ease;
}

.footer-nav-link i {
  width: 1.25rem;
  flex: 0 0 1.25rem;
  text-align: center;
  font-size: 1rem;
  line-height: 1;
  color: rgba(255, 255, 255, 0.62);
  transition: color 0.3s ease, transform 0.3s ease;
}

.footer-nav-link span {
  font-size: 0.74rem;
  line-height: 1.05;
  white-space: nowrap;
}

.footer-nav:hover .footer-nav-link {
  opacity: 0.985;
}

.footer-nav:hover .footer-nav-link:hover {
  opacity: 1;
  background: rgba(255, 255, 255, calc(0.03 + (0.04 * var(--hover-fill, 0))));
  box-shadow: 0 3px 10px rgba(0, 0, 0, calc(0.08 + (0.04 * var(--hover-fill, 0))));
  color: rgba(255, 255, 255, 0.95);
}

.footer-nav-link:hover i {
  color: #ffffff;
}

.footer-nav-link:hover span {
  color: rgba(255, 255, 255, 0.94);
  text-shadow: 0 0 6px rgba(255, 255, 255, 0.04);
}

.footer-nav-link.active {
  background: rgba(255, 255, 255, 0.12);
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
  color: #ffffff;
}

.footer-nav-link.active i {
  color: rgba(255, 255, 255, 0.95);
}

.footer-nav-link::after {
  content: '';
  position: absolute;
  left: 0;
  top: 24%;
  bottom: 24%;
  width: 2px;
  border-radius: 999px;
  background: transparent;
  pointer-events: none;
  transition: background 0.2s ease;
}

.footer-nav-link:hover::after,
.footer-nav-link.active::after {
  background: rgba(255, 255, 255, 0.18);
}

.footer-bottom {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.footer-timeline {
  cursor: pointer;
}

.footer-timeline-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
  font-size: 0.8rem;
  color: rgba(255, 255, 255, 0.82);
}

.footer-timeline-label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  min-width: 0;
}

.footer-timeline-time {
  flex-shrink: 0;
  opacity: 0.85;
}

.footer-timeline-track {
  height: 7px;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.footer-timeline-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #6ddcff, #ff3d8e);
}

@media (max-width: 768px) {
  .footer-retro-brand {
    margin: 15px auto 20px;
  }
}
</style>
