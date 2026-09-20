<template>
  <div class="rpw-widget">
    <div class="rpw-header">
      <div class="rpw-icon"><i class="fas fa-history"></i></div>
      <div class="rpw-text">
        <h3>Recently Played</h3>
        <p>Jump back in</p>
      </div>
      <button v-if="recentlyPlayed.length > 0" class="rpw-clear-btn" @click="clearHistory" title="Clear history">
        <i class="fas fa-times"></i>
      </button>
    </div>
    <div class="rpw-grid" v-if="recentlyPlayed.length > 0">
      <router-link
        v-for="item in recentlyPlayed"
        :key="item.key || item.id"
        :to="`/${item.type === 'show' ? 'shows' : 'music'}/${item.id}`"
        class="rpw-card"
      >
        <div class="rpw-card-image">
          <img :src="item.artwork || item.cover_art || '/static/img/default-cover.jpg'" :alt="item.title" loading="lazy" />
          <div class="rpw-play-icon"><i class="fas fa-play"></i></div>
        </div>
        <div class="rpw-card-title">{{ item.title }}</div>
      </router-link>
    </div>
    <div v-else class="rpw-empty">
      <div class="rpw-empty-text">
        <i class="fas fa-play-circle"></i>
        <span>Start listening — it'll show up here</span>
      </div>
      <div class="rpw-empty-links">
        <router-link to="/music" class="rpw-empty-link">Music</router-link>
        <router-link to="/podcasts" class="rpw-empty-link">Podcasts</router-link>
        <router-link to="/radio" class="rpw-empty-link">Radio</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const recentlyPlayed = ref([])

function load() {
  try {
    const raw = localStorage.getItem('ahoy.recentlyPlayed.v1')
    if (raw) recentlyPlayed.value = JSON.parse(raw).slice(0, 6)
  } catch (e) {
    console.error('Failed to load recently played', e)
  }
}

function clearHistory() {
  localStorage.removeItem('ahoy.recentlyPlayed.v1')
  recentlyPlayed.value = []
}

function onUpdate(e) {
  if (e.detail?.recent) recentlyPlayed.value = e.detail.recent.slice(0, 6)
}

onMounted(() => {
  load()
  window.addEventListener('recentlyPlayed:updated', onUpdate)
})

onUnmounted(() => {
  window.removeEventListener('recentlyPlayed:updated', onUpdate)
})
</script>

<style scoped>
.rpw-widget {
  background: rgba(0, 0, 0, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 32px;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  box-shadow: 0 20px 50px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.15);
}

.rpw-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
}

.rpw-clear-btn {
  margin-left: auto;
  background: none;
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 999px;
  color: rgba(255, 255, 255, 0.4);
  font-size: 0.75rem;
  padding: 0.35rem 0.75rem;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.rpw-clear-btn::after {
  content: 'Clear';
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.rpw-clear-btn:hover {
  border-color: rgba(255, 100, 100, 0.5);
  color: rgba(255, 100, 100, 0.8);
}

.rpw-icon {
  width: 56px;
  height: 56px;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  color: #fff;
  background: #3b1578;
}

.rpw-text h3 {
  font-size: 1.75rem;
  font-weight: 900;
  margin: 0;
  line-height: 0.9;
  text-transform: uppercase;
  letter-spacing: -0.03em;
  color: rgba(255, 255, 255, 0.95);
}

.rpw-text p {
  margin: 0.35rem 0 0 0;
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.6);
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.rpw-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 1.5rem;
}

@media (min-width: 1025px) {
  .rpw-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
}

.rpw-card {
  display: block;
  min-width: 0;
  text-decoration: none;
  color: inherit;
  cursor: pointer;
}

.rpw-card-image {
  aspect-ratio: 1 / 1;
  width: 100%;
  border-radius: 20px;
  overflow: hidden;
  margin-bottom: 0.85rem;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
  background: #000;
  position: relative;
}

.rpw-card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.rpw-play-icon {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.2);
  opacity: 0;
  transition: opacity 0.2s;
}

.rpw-card:hover .rpw-play-icon {
  opacity: 1;
}

.rpw-play-icon i {
  font-size: 3rem;
  color: #fff;
  filter: drop-shadow(0 4px 8px rgba(0, 0, 0, 0.5));
}

.rpw-card-title {
  font-weight: 700;
  font-size: 0.95rem;
  text-align: center;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  padding: 0 0.25rem;
  color: rgba(255, 255, 255, 0.9);
  opacity: 0.8;
  transition: opacity 0.2s;
}

.rpw-card:hover .rpw-card-title {
  opacity: 1;
}

.rpw-empty {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 16px;
}

.rpw-empty-text {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: rgba(255, 255, 255, 0.4);
  font-style: italic;
  font-size: 0.95rem;
}

.rpw-empty-text i {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.rpw-empty-links {
  display: flex;
  gap: 0.5rem;
  padding-left: calc(1.5rem + 0.75rem);
}

.rpw-empty-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.4rem 1rem;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: rgba(255, 255, 255, 0.7);
  text-decoration: none;
  font-size: 0.85rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  line-height: 1;
  transition: border-color 0.2s, color 0.2s;
}

.rpw-empty-link:hover {
  border-color: rgba(255, 255, 255, 0.6);
  color: #fff;
}

@media (max-width: 768px) {
  .rpw-widget {
    padding: 1rem;
    border-radius: 20px;
    gap: 1rem;
  }
  .rpw-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 0.5rem;
  }
  .rpw-grid .rpw-card:nth-child(n+5) {
    display: none;
  }
  .rpw-icon { width: 42px; height: 42px; font-size: 1.25rem; border-radius: 12px; }
  .rpw-text h3 { font-size: 1.4rem; }
  .rpw-card-title {
    font-size: 0.7rem;
    white-space: normal;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    line-height: 1.2;
    opacity: 1;
  }
}
</style>
