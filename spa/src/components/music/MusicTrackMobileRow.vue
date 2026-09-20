<template>
  <div class="music-mobile-row" :class="{ playing }" @click="$emit('play')">
    <div class="music-mobile-art">
      <img
        class="music-mobile-art-img image-placeholder"
        :src="cover"
        :alt="track.title"
        :loading="loadingType"
        @error="onImageError"
      />
      <button
        type="button"
        class="music-mobile-art-play"
        :aria-label="playTitle"
        @click.stop="$emit('play')"
      >
        <i :class="playIcon" aria-hidden="true"></i>
      </button>
    </div>

    <div class="music-mobile-meta">
      <span class="music-mobile-artist-line">{{ track.artist }}</span>
      <div class="music-mobile-title-row">
        <router-link :to="trackUrl" class="music-mobile-title-link" @click.stop>
          <span class="music-mobile-title-line">{{ track.title }}</span>
        </router-link>
        <span class="music-mobile-duration">{{ duration }}</span>
      </div>
    </div>

    <button
      type="button"
      class="music-mobile-more"
      aria-label="Track actions"
      @click.stop="$emit('more')"
    >
      <i class="fas fa-ellipsis" aria-hidden="true"></i>
    </button>
  </div>
</template>

<script setup>
defineProps({
  track: { type: Object, required: true },
  playing: { type: Boolean, default: false },
  cover: { type: String, required: true },
  duration: { type: String, required: true },
  trackUrl: { type: String, required: true },
  playIcon: { type: String, required: true },
  playTitle: { type: String, required: true },
  bookmarked: { type: Boolean, default: false },
  bookmarkIcon: { type: String, required: true },
  bookmarkTitle: { type: String, required: true },
  loadingType: { type: String, default: 'lazy' },
})

defineEmits(['play', 'queue', 'add-to-playlist', 'toggle-bookmark', 'more'])

function onImageError(event) {
  event.target.src = '/static/img/default-cover.jpg'
}
</script>

<style scoped>
.music-mobile-row {
  display: grid !important;
  grid-template-columns: 48px minmax(0, 1fr) 36px !important;
  align-items: center !important;
  gap: 11px !important;
  min-height: 58px !important;
  padding: 6px 8px 6px 10px !important;
}

.music-mobile-art {
  position: relative !important;
  width: 44px !important;
  height: 44px !important;
  border-radius: 8px !important;
  overflow: hidden !important;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.28) !important;
}

.music-mobile-art-img {
  display: block !important;
  width: 100% !important;
  height: 100% !important;
  object-fit: cover !important;
}

.music-mobile-art-play {
  position: absolute !important;
  inset: 0 !important;
  width: 100% !important;
  height: 100% !important;
  border: 0 !important;
  border-radius: 8px !important;
  display: grid !important;
  place-items: center !important;
  color: #fff !important;
  background:
    radial-gradient(circle at center, rgba(0, 0, 0, 0.34) 0 34%, rgba(0, 0, 0, 0.14) 35% 48%, rgba(0, 0, 0, 0.04) 49% 100%) !important;
  font-size: 13px !important;
  opacity: 1 !important;
}

.music-mobile-meta {
  min-width: 0 !important;
  display: grid !important;
  grid-template-rows: auto auto !important;
  align-content: center !important;
  gap: 4px !important;
}

.music-mobile-title-row {
  display: flex !important;
  align-items: baseline !important;
  gap: 6px !important;
  min-width: 0 !important;
}

.music-mobile-title-link {
  display: block !important;
  min-width: 0 !important;
  min-height: 0 !important;
  flex: 1 1 0 !important;
  color: inherit !important;
  text-decoration: none !important;
  line-height: 1 !important;
  overflow: hidden !important;
}

.music-mobile-duration {
  flex-shrink: 0 !important;
  font-size: 12px !important;
  color: rgba(255, 255, 255, 0.38) !important;
  font-variant-numeric: tabular-nums !important;
  line-height: 1 !important;
}

.music-mobile-artist-line,
.music-mobile-title-line {
  display: block !important;
  width: 100% !important;
  max-width: 100% !important;
  overflow: hidden !important;
  text-overflow: ellipsis !important;
  white-space: nowrap !important;
}

.music-mobile-artist-line {
  color: rgba(255, 255, 255, 0.96) !important;
  font-size: 15px !important;
  font-weight: 800 !important;
  line-height: 1.14 !important;
}

.music-mobile-title-line {
  color: rgba(255, 255, 255, 0.62) !important;
  font-size: 13px !important;
  font-weight: 500 !important;
  line-height: 1.18 !important;
}

.music-mobile-more {
  width: 36px !important;
  height: 36px !important;
  border: 0 !important;
  border-radius: 999px !important;
  background: transparent !important;
  color: rgba(255, 255, 255, 0.72) !important;
  display: inline-grid !important;
  place-items: center !important;
  font-size: 16px !important;
}
</style>
