<template>
  <router-link
    :to="getSearchResultUrl(item)"
    class="search-card"
    :class="[`search-card--${kind}`, { 'search-card--no-image': !image }]"
    @click="$emit('navigate', item)"
  >
    <img v-if="image" :src="image" :alt="label" class="search-card-bg" loading="lazy" decoding="async" />
    <span class="search-card-type-icon"><i :class="icon"></i></span>
    <div class="search-card-overlay">
      <span class="search-card-title" v-html="highlightSearchText(label, query)"></span>
    </div>
    <button
      v-if="item.type === 'track'"
      class="search-card-play"
      @click.stop.prevent="$emit('play', item)"
      aria-label="Play"
    >
      <i :class="isPlaying ? 'fas fa-pause' : 'fas fa-play'"></i>
    </button>
    <span v-if="isNewItem" class="search-card-new-badge">New</span>
  </router-link>
</template>

<script setup>
import { computed } from 'vue'
import { getSearchResultUrl, highlightSearchText } from '../composables/useSearch'

const props = defineProps({
  item: { type: Object, required: true },
  query: { type: String, default: '' },
  isPlaying: { type: Boolean, default: false }
})

defineEmits(['navigate', 'play'])

const KIND_MAP = {
  track: 'track',
  album: 'album',
  video: 'show',
  show: 'show',
  podcast: 'podcast',
  podcastEpisode: 'episode',
  artist: 'artist',
  event: 'event'
}

const ICON_MAP = {
  track: 'fas fa-music',
  album: 'fas fa-compact-disc',
  video: 'fas fa-film',
  show: 'fas fa-film',
  podcast: 'fas fa-podcast',
  podcastEpisode: 'fas fa-headphones',
  artist: 'fas fa-user',
  event: 'fas fa-calendar-alt'
}

const kind = computed(() => KIND_MAP[props.item.type] || 'track')
const icon = computed(() => ICON_MAP[props.item.type] || 'fas fa-music')
const label = computed(() => props.item.name || props.item.title || '')
const image = computed(() => props.item.cover_art || props.item.thumbnail || props.item.image || props.item.artwork || null)

const isNewItem = computed(() => {
  if (props.item.type !== 'event' || !props.item.date) return false
  const cutoff = new Date()
  cutoff.setMonth(cutoff.getMonth() - 2)
  return new Date(props.item.date) >= cutoff
})
</script>

<style scoped>
.search-card {
  width: 150px;
  height: 150px;
  position: relative;
  border-radius: 8px;
  overflow: hidden;
  background: transparent;
  display: block;
  text-decoration: none;
  color: inherit;
  transition: transform 0.18s, box-shadow 0.18s;
  will-change: transform;
}
.search-card:hover {
  transform: scale(1.015);
  box-shadow: 0 6px 22px rgba(0,0,0,0.4);
  z-index: 2;
}
.search-card:active {
  transform: scale(0.95);
}

.search-card-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.search-card-type-icon {
  position: absolute;
  top: 5px;
  left: 5px;
  z-index: 4;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0,0,0,0.45);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  font-size: 8px;
  color: rgba(255,255,255,0.9);
}

.search-card-overlay {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 5px 6px 6px;
  backdrop-filter: blur(16px) saturate(1.25);
  -webkit-backdrop-filter: blur(16px) saturate(1.25);
  display: flex;
  flex-direction: column;
  background:
    linear-gradient(180deg, rgba(12, 14, 18, 0.36), rgba(8, 10, 14, 0.82)),
    rgba(0,0,0,0.6);
  border-top: 1px solid rgba(255,255,255,0.06);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
}

.search-card--track .search-card-overlay {
  background:
    linear-gradient(180deg, rgba(12, 14, 18, 0.34), rgba(8, 10, 14, 0.84)),
    linear-gradient(135deg, rgba(65, 85, 210, 0.34), rgba(65, 85, 210, 0.18));
}
.search-card--artist .search-card-overlay {
  background:
    linear-gradient(180deg, rgba(12, 14, 18, 0.34), rgba(8, 10, 14, 0.84)),
    linear-gradient(135deg, rgba(200, 80, 25, 0.34), rgba(200, 80, 25, 0.18));
}
.search-card--show .search-card-overlay {
  background:
    linear-gradient(180deg, rgba(12, 14, 18, 0.34), rgba(8, 10, 14, 0.84)),
    linear-gradient(135deg, rgba(185, 30, 55, 0.34), rgba(185, 30, 55, 0.18));
}
.search-card--podcast .search-card-overlay {
  background:
    linear-gradient(180deg, rgba(12, 14, 18, 0.34), rgba(8, 10, 14, 0.84)),
    linear-gradient(135deg, rgba(20, 155, 115, 0.34), rgba(20, 155, 115, 0.18));
}
.search-card--episode .search-card-overlay {
  background:
    linear-gradient(180deg, rgba(12, 14, 18, 0.34), rgba(8, 10, 14, 0.84)),
    linear-gradient(135deg, rgba(15, 130, 185, 0.34), rgba(15, 130, 185, 0.18));
}
.search-card--event .search-card-overlay {
  background:
    linear-gradient(180deg, rgba(12, 14, 18, 0.34), rgba(8, 10, 14, 0.84)),
    linear-gradient(135deg, rgba(160, 110, 10, 0.34), rgba(160, 110, 10, 0.18));
}

.search-card--no-image {
  border: 1px solid rgba(255,255,255,0.12);
}
.search-card--no-image .search-card-overlay {
  inset: 0;
  background:
    linear-gradient(180deg, rgba(12, 14, 18, 0.46), rgba(8, 10, 14, 0.88)),
    rgba(0,0,0,0.55) !important;
  backdrop-filter: blur(16px) saturate(1.15);
  -webkit-backdrop-filter: blur(16px) saturate(1.15);
  justify-content: center;
  align-items: center;
  padding: 8px;
  text-align: center;
}

.search-card-title {
  color: #fff;
  font-size: 10px;
  font-weight: 600;
  line-height: 1.25;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.search-card--no-image .search-card-title {
  color: var(--text-primary);
  font-size: 11px;
  white-space: normal;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
  text-overflow: unset;
  text-align: center;
}

.search-card-play {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -58%);
  background: rgba(0,0,0,0.6);
  border: none;
  cursor: pointer;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.18s, transform 0.18s;
  z-index: 3;
  padding-left: 2px;
}
.search-card:hover .search-card-play {
  opacity: 1;
  transform: translate(-50%, -50%);
}

.search-card-new-badge {
  position: absolute;
  top: 5px;
  right: 5px;
  font-size: 8px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #002a35;
  background: linear-gradient(135deg, #69daff, #00cffc);
  border-radius: 3px;
  padding: 2px 4px;
  z-index: 4;
}

:deep(.search-highlight) {
  background: rgba(255,255,255,0.25);
  color: #fff;
  border-radius: 3px;
  padding: 0 0.08em;
}
</style>
