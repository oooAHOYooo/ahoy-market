<template>
  <div class="wn-video-source">
    <router-link :to="detailPath" class="back-link">
      <i class="fas fa-arrow-left"></i> Back to update
    </router-link>

    <section v-if="detailUpdate" class="wn-video-source-card">
      <div class="wn-video-source-head">
        <span class="wn-pill section">Videos</span>
        <h1>{{ detailUpdate.title }}</h1>
        <p>{{ detailUpdate.description || detailUpdate.body }}</p>
      </div>

      <div class="wn-video-source-grid">
        <router-link
          v-for="video in relatedVideos"
          :key="video.path"
          :to="video.path"
          class="wn-video-source-item"
        >
          <div class="thumb">
            <img v-if="video.thumbnail" :src="video.thumbnail" :alt="video.title" loading="lazy" />
            <span v-else>{{ video.shortLabel || 'Video' }}</span>
          </div>
          <div class="copy">
            <strong>{{ video.title }}</strong>
            <span>{{ video.description }}</span>
          </div>
        </router-link>
      </div>

      <div class="wn-video-source-actions">
        <router-link :to="detailPath" class="wn-cta secondary">Back to update</router-link>
      </div>
    </section>

    <div v-else class="wn-empty">
      <p>That video source page could not be found.</p>
      <router-link to="/whats-new" class="wn-cta">Back to archive</router-link>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  detailUpdate: { type: Object, default: null },
  detailPath: { type: String, default: '/whats-new' },
})

const relatedVideos = computed(() => Array.isArray(props.detailUpdate?.related_videos) ? props.detailUpdate.related_videos : [])
</script>

<style scoped>
.wn-video-source {
  max-width: 980px;
  margin: 0 auto;
}

.wn-video-source-card {
  margin-top: 1.25rem;
  padding: 1.5rem;
  border-radius: 28px;
  border: 1px solid rgba(255,255,255,0.08);
  background: rgba(18,18,20,0.84);
}

.wn-video-source-head h1 {
  margin: 0.75rem 0 0;
  font-size: clamp(2rem, 4vw, 3.5rem);
}

.wn-video-source-head p {
  margin: 0.75rem 0 0;
  color: rgba(255,255,255,0.72);
}

.wn-video-source-grid {
  display: grid;
  gap: 1rem;
  margin-top: 1.5rem;
}

.wn-video-source-item {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  gap: 1rem;
  align-items: center;
  padding: 0.9rem;
  border-radius: 20px;
  background: rgba(255,255,255,0.04);
  text-decoration: none;
  color: inherit;
}

.thumb {
  aspect-ratio: 16 / 9;
  border-radius: 14px;
  overflow: hidden;
  background: rgba(255,255,255,0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(255,255,255,0.75);
  font-weight: 800;
}

.thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.copy {
  display: grid;
  gap: 0.35rem;
}

.copy span {
  color: rgba(255,255,255,0.68);
}

.wn-video-source-actions {
  margin-top: 1.5rem;
}
</style>
