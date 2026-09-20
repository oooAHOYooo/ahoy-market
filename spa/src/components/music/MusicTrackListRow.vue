<template>
  <tr class="music-table-row" :class="{ playing }" @click="$emit('play')">

    <!-- Col 1: track number / play indicator / animated bars -->
    <td class="col-num">
      <div class="track-num-wrap">
        <template v-if="playing && playIcon === 'fas fa-pause'">
          <!-- Actively playing: animated bars (hover swaps to pause) -->
          <div class="now-playing-bars" aria-label="Now playing">
            <span></span><span></span><span></span>
          </div>
          <button type="button" class="track-num-play-btn" :aria-label="playTitle" @click.stop="$emit('play')">
            <i class="fas fa-pause" aria-hidden="true"></i>
          </button>
        </template>
        <template v-else>
          <!-- Idle / paused: number → hover shows play -->
          <span class="track-num-default">{{ index + 1 }}</span>
          <button type="button" class="track-num-play-btn" :aria-label="playTitle" @click.stop="$emit('play')">
            <i :class="playIcon" aria-hidden="true"></i>
          </button>
        </template>
      </div>
    </td>

    <!-- Col 2: art + title + artist -->
    <td class="col-title-artist">
      <img
        class="music-row-art image-placeholder"
        :src="cover"
        :alt="track.title"
        :loading="loadingType"
        @error="onImageError"
      />
      <div class="music-track-meta">
        <router-link :to="trackUrl" class="title-link" @click.stop>
          <span class="title-text">{{ track.title }}</span>
        </router-link>
        <span class="music-track-artist">{{ track.artist }}</span>
      </div>
    </td>

    <!-- Col 3: duration -->
    <td class="col-duration">{{ duration }}</td>

    <!-- Col 4: bookmark + ··· menu -->
    <td class="col-action">
      <MusicTrackActions
        :play-icon="playIcon"
        :play-title="playTitle"
        :bookmarked="bookmarked"
        :bookmark-icon="bookmarkIcon"
        :bookmark-title="bookmarkTitle"
        @play="$emit('play')"
        @queue="$emit('queue')"
        @add-to-playlist="$emit('add-to-playlist')"
        @toggle-bookmark="$emit('toggle-bookmark')"
      />
    </td>
  </tr>
</template>

<script setup>
import MusicTrackActions from './MusicTrackActions.vue'

defineProps({
  track: { type: Object, required: true },
  index: { type: Number, required: true },
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

defineEmits(['play', 'queue', 'add-to-playlist', 'toggle-bookmark'])

function onImageError(event) {
  event.target.src = '/static/img/default-cover.jpg'
}
</script>
