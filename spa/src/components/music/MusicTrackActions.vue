<template>
  <div class="music-track-actions" ref="rootRef">
    <button
      type="button"
      class="episode-btn bm-btn music-track-bookmark-btn"
      :class="{ bookmarked }"
      :aria-pressed="bookmarked"
      :title="bookmarkTitle"
      @click.stop="$emit('toggle-bookmark')"
    >
      <i :class="bookmarkIcon" aria-hidden="true"></i>
    </button>
    <button
      type="button"
      class="episode-btn music-track-more-btn"
      aria-label="More options"
      title="More options"
      @click.stop="toggleMenu"
    >
      <i class="fas fa-ellipsis" aria-hidden="true"></i>
    </button>
    <div v-if="menuOpen" class="music-more-menu" @click.stop>
      <button type="button" @click="emit('queue'); closeMenu()">
        <i class="fas fa-plus" aria-hidden="true"></i>
        <span>Add to queue</span>
      </button>
      <button type="button" @click="emit('add-to-playlist'); closeMenu()">
        <i class="fas fa-list-plus" aria-hidden="true"></i>
        <span>Add to playlist</span>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

defineProps({
  playIcon: { type: String, required: true },
  playTitle: { type: String, required: true },
  bookmarked: { type: Boolean, default: false },
  bookmarkIcon: { type: String, required: true },
  bookmarkTitle: { type: String, required: true },
})

const emit = defineEmits(['play', 'queue', 'add-to-playlist', 'toggle-bookmark'])

const menuOpen = ref(false)
const rootRef = ref(null)

function toggleMenu() {
  menuOpen.value = !menuOpen.value
}

function closeMenu() {
  menuOpen.value = false
}

function onDocClick(e) {
  if (rootRef.value && !rootRef.value.contains(e.target)) {
    menuOpen.value = false
  }
}

onMounted(() => document.addEventListener('click', onDocClick, true))
onUnmounted(() => document.removeEventListener('click', onDocClick, true))
</script>

<style scoped>
.music-track-actions {
  position: relative;
  display: flex;
  align-items: center;
  gap: 6px;
}

.music-more-menu {
  position: absolute;
  right: 0;
  top: calc(100% + 6px);
  background: #1a1a1a;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  padding: 4px;
  min-width: 160px;
  z-index: 100;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
}

.music-more-menu button {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 12px;
  background: none;
  border: none;
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.85);
  font-size: 13px;
  cursor: pointer;
  text-align: left;
  transition: background 0.12s;
}

.music-more-menu button:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.music-more-menu button i {
  width: 16px;
  text-align: center;
  opacity: 0.7;
}
</style>
