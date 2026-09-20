<template>
  <section class="search-section">
    <h2 class="search-section-title">{{ title }}</h2>
    <div class="search-grid">
      <SearchCard
        v-for="item in items"
        :key="itemKey(item)"
        :item="item"
        :query="query"
        :is-playing="isItemPlaying(item)"
        @navigate="$emit('navigate', item)"
        @play="$emit('play', item)"
      />
    </div>
  </section>
</template>

<script setup>
import SearchCard from './SearchCard.vue'
import { usePlayerStore } from '../stores/player'

const props = defineProps({
  title: { type: String, required: true },
  items: { type: Array, required: true },
  query: { type: String, default: '' }
})

defineEmits(['navigate', 'play'])

const playerStore = usePlayerStore()

function itemKey(item) {
  return item.id || item.slug || item.title
}

function isItemPlaying(item) {
  return playerStore.currentTrack?.id === item.id && playerStore.isPlaying
}
</script>

<style scoped>
.search-section {
  margin-bottom: 14px;
}

.search-section-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.8px;
  color: var(--text-secondary);
  margin: 0 0 6px;
  padding: 0 14px;
}

.search-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, 150px);
  justify-content: start;
  width: 100%;
  gap: 8px;
  padding: 0 14px;
  box-sizing: border-box;
}

@media (max-width: 420px) {
  .search-section-title {
    padding: 0 10px;
  }
  .search-grid {
    gap: 6px;
    padding: 0 10px;
  }
}
</style>
