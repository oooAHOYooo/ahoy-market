<template>
  <div class="msw-widget">
    <div class="msw-header">
      <div class="msw-icon"><i class="fas fa-bookmark"></i></div>
      <div class="msw-text">
        <h3>My Saves</h3>
        <p>Your Favorites</p>
      </div>
    </div>
    <div class="msw-grid">
      <div v-if="mySaves.length === 0" class="msw-empty">
        Nothing saved yet
      </div>
      <router-link
        v-else
        v-for="item in mySaves"
        :key="item.id || item.slug"
        :to="item.type === 'artist' ? `/artists/${item.slug}` : `/${item.type === 'show' ? 'shows' : 'music'}/${item.id}`"
        class="msw-card"
      >
        <div class="msw-card-image">
          <img :src="item.cover_art || '/static/img/default-cover.jpg'" :alt="item.title" loading="lazy" />
        </div>
        <div class="msw-card-title">{{ item.title || item.name }}</div>
      </router-link>
    </div>
    <router-link to="/profile" class="msw-cta">View All Saves</router-link>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useBookmarks } from '../composables/useBookmarks'

const bookmarks = useBookmarks()
const mySaves = ref([])

function updateMySaves() {
  const all = Object.values(bookmarks.bookmarks.value || {})
  mySaves.value = all.reverse().slice(0, 6)
}

onMounted(() => {
  updateMySaves()
  window.addEventListener('bookmarks:changed', updateMySaves)
})

onUnmounted(() => {
  window.removeEventListener('bookmarks:changed', updateMySaves)
})
</script>

<style scoped>
.msw-widget {
  margin-bottom: 1.5rem;
  background: rgba(20, 20, 20, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 2rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  box-shadow: 0 20px 50px -10px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.15), inset 0 0 40px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
}
.msw-widget::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 100%;
  background: linear-gradient(180deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0) 100%);
  pointer-events: none;
  z-index: 0;
}
.msw-header {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  margin-bottom: 0;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255,255,255,0.08);
  position: relative;
  z-index: 1;
}
.msw-icon {
  width: 56px; height: 56px;
  border-radius: 16px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.75rem;
  background: #4c1d95;
  color: #fff;
  box-shadow: none;
  flex-shrink: 0;
}
.msw-text h3 {
  font-size: 1.75rem; font-weight: 900; margin: 0; line-height: 0.9;
  text-transform: uppercase; letter-spacing: -0.03em; color: rgba(255,255,255,0.95);
}
.msw-text p {
  margin: 0.35rem 0 0 0; font-size: 0.85rem; color: rgba(255,255,255,0.6);
  font-weight: 700; letter-spacing: 0.05em; text-transform: uppercase;
}
.msw-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 1.5rem;
  position: relative;
  z-index: 1;
}

@media (min-width: 1025px) {
  .msw-grid {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  }
}
.msw-empty {
  grid-column: span 3;
  text-align: center; padding: 2rem;
  color: rgba(255,255,255,0.4); font-style: italic;
  background: rgba(255,255,255,0.03); border-radius: 16px;
}
.msw-card {
  display: block; min-width: 0;
  text-decoration: none; color: inherit;
  cursor: pointer;
}
.msw-card-image {
  aspect-ratio: 1 / 1; width: 100%;
  border-radius: 16px; overflow: hidden;
  margin-bottom: 0.85rem;
  box-shadow: 0 10px 25px rgba(0,0,0,0.4);
  background: #000; position: relative;
}
.msw-card-image img {
  width: 100%; height: 100%; object-fit: cover;
}
.msw-card-title {
  font-weight: 700; font-size: 0.95rem; text-align: center;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  padding: 0 0.25rem; color: rgba(255,255,255,0.9);
  opacity: 0.9;
}
.msw-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  align-self: center;
  padding: 0;
  font-weight: 600;
  text-decoration: none;
  color: rgba(255,255,255,0.72);
  font-size: 0.9rem;
  position: relative;
  z-index: 1;
}
@media (max-width: 768px) {
  .msw-widget { margin-bottom: 1rem; padding: 1rem; border-radius: 20px; gap: 1rem; }
  .msw-grid { grid-template-columns: repeat(4, 1fr); gap: 0.5rem; }
  .msw-grid .msw-card:nth-child(n+5) { display: none; }
  .msw-card-title { font-size: 0.7rem; white-space: normal; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; line-height: 1.2; opacity: 1; }
  .msw-icon { width: 42px; height: 42px; font-size: 1.25rem; border-radius: 12px; }
  .msw-text h3 { font-size: 1.4rem; }
  .msw-cta { font-size: 0.85rem; }
}
</style>
