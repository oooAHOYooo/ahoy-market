<template>
  <div class="track-card" :class="{ playing }">
    <div class="track-cover" @click="$emit('play')">
      <img
        :src="cover"
        :alt="track.title"
        loading="lazy"
        @error="onImageError"
      />
      <div class="track-overlay">
        <button type="button" class="play-btn" @click.stop="$emit('play')">
          <i :class="playIcon"></i>
        </button>
        <button
          type="button"
          class="track-overlay-btn add-to-playlist-btn"
          title="Add to playlist"
          @click.stop="$emit('add-to-playlist')"
        >
          <i class="fas fa-list-ul"></i>
        </button>
        <button
          type="button"
          class="track-overlay-btn bm-btn"
          :title="bookmarkTitle"
          @click.stop="$emit('toggle-bookmark')"
        >
          <i :class="bookmarkIcon" aria-hidden="true"></i>
        </button>
      </div>
    </div>
    <router-link :to="trackUrl" class="track-info" style="text-decoration:none;color:inherit">
      <div class="track-title">{{ track.title }}</div>
      <div class="track-artist">{{ track.artist }}</div>
      <div class="track-duration">{{ duration }}</div>
    </router-link>
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
  bookmarkIcon: { type: String, required: true },
  bookmarkTitle: { type: String, required: true },
})

defineEmits(['play', 'add-to-playlist', 'toggle-bookmark'])

function onImageError(event) {
  event.target.src = '/static/img/default-cover.jpg'
}
</script>

