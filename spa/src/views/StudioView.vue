<template>
  <div class="studio-page">
    <ContentHeader
      kicker="Ahoy Indie Media"
      title="Studio"
      subtitle="In-house productions, live events & behind the scenes."
    />
    <section class="page-mobile-hero" aria-label="Studio">
      <div class="page-mobile-hero-copy">
        <span class="page-mobile-eyebrow">In-house</span>
        <h1>Studio</h1>
        <p>{{ collections.length ? `${collections.length} collection${collections.length === 1 ? '' : 's'} — productions, live events & behind the scenes` : 'In-house productions, live events & behind the scenes.' }}</p>
      </div>
    </section>

    <!-- Grid of collections -->
    <div v-if="!loading && collections.length" class="studio-grid">
      <router-link
        v-for="(col, idx) in collections"
        :key="col.collection_id"
        :to="`/studio/${col.collection_id}`"
        class="studio-card"
      >
        <div class="studio-card-media">
          <img
            :src="col.cover || '/static/img/default-cover.jpg'"
            :alt="col.title"
            loading="lazy"
          />
          <div class="studio-card-overlay" />
          <div v-if="idx === 0" class="studio-card-new">New</div>
          <div v-if="col.photo_count" class="studio-card-badge">
            <i class="fas fa-images"></i>
            {{ col.photo_count }}
          </div>
        </div>
        <div class="studio-card-body">
          <div v-if="col.tag" class="studio-card-tag">{{ col.tag }}</div>
          <div class="studio-card-title">{{ col.title }}</div>
          <div v-if="col.date" class="studio-card-date">{{ formatDate(col.date) }}</div>
        </div>
      </router-link>
    </div>

    <!-- Skeleton -->
    <div v-else-if="loading" class="studio-grid">
      <div v-for="i in 6" :key="i" class="studio-card-skel">
        <div class="skeleton studio-skel-media"></div>
        <div class="studio-card-skel-content">
          <div class="skeleton" style="height:10px;width:40%;margin-bottom:8px;border-radius:4px"></div>
          <div class="skeleton" style="height:14px;width:70%;border-radius:4px"></div>
        </div>
      </div>
    </div>

    <!-- Empty -->
    <div v-else class="studio-empty">
      <i class="fas fa-camera"></i>
      <h4>No collections yet</h4>
      <p>Check back soon.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { apiFetchCached } from '../composables/useApi'
import ContentHeader from '../components/ContentHeader.vue'

const items = ref([])
const loading = ref(true)
const collections = ref([])

function formatDate(ds) {
  if (!ds) return ''
  const d = new Date(ds)
  if (isNaN(d.getTime())) return String(ds)
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })
}

onMounted(async () => {
  loading.value = true
  try {
    const data = await apiFetchCached('/api/studio')
    collections.value = data.collections || []
  } catch {
    collections.value = []
  }
  loading.value = false
})
</script>

<style scoped>
.page-mobile-hero { display: none; }
@media (max-width: 768px) {
  :deep(.content-header) { display: none !important; }
  .page-mobile-hero { display: block; }
}

.studio-page {
  min-height: 60vh;
  width: 100%;
  padding: 0 1.5rem 100px;
}

/* Header removed, now using ContentHeader.vue component */

/* Grid */
.studio-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 16px;
}

/* Card */
.studio-card {
  display: block;
  text-decoration: none;
  color: inherit;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: transform 0.22s ease, box-shadow 0.22s ease, border-color 0.22s ease;
  cursor: pointer;
}
.studio-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.55);
  border-color: rgba(255, 255, 255, 0.15);
}
.studio-card:hover .studio-card-overlay {
  background: rgba(0, 0, 0, 0.5);
}
.studio-card:hover img {
  transform: scale(1.04);
}

.studio-card-media {
  position: relative;
  aspect-ratio: 4 / 3;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.06);
}
.studio-card-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.45s ease;
}
.studio-card-overlay {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.2);
  transition: background 0.22s ease;
}
.studio-card-badge {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(0, 0, 0, 0.72);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  color: rgba(255, 255, 255, 0.95);
  font-size: 11px;
  font-weight: 700;
  padding: 5px 10px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.24);
  display: flex;
  align-items: center;
  gap: 5px;
}
.studio-card-new {
  position: absolute;
  top: 10px;
  left: 10px;
  z-index: 2;
  background: rgba(0, 0, 0, 0.68);
  color: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(255, 255, 255, 0.16);
  border-radius: 999px;
  padding: 4px 9px;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 6px 18px rgba(0, 0, 0, 0.28);
}

.studio-card-body {
  padding: 11px 14px 14px;
}
.studio-card-tag {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.13em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.35);
  margin-bottom: 4px;
}
.studio-card-title {
  font-size: 15px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.92);
  line-height: 1.3;
  margin-bottom: 4px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  min-height: calc(1.3em * 2);
}
.studio-card-date {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.42);
  line-height: 1.2;
}

/* Skeleton */
.studio-card-skel {
  border-radius: 12px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.07);
}
.studio-skel-media {
  aspect-ratio: 4 / 3;
  width: 100%;
}

/* Empty */
.studio-empty {
  text-align: center;
  padding: 80px 20px;
  color: rgba(255, 255, 255, 0.25);
}
.studio-empty i {
  font-size: 2.8rem;
  display: block;
  margin-bottom: 14px;
}
.studio-empty h4 {
  font-size: 1.1rem;
  font-weight: 600;
  margin: 0 0 6px;
  color: rgba(255, 255, 255, 0.4);
}
.studio-empty p {
  font-size: 13px;
  margin: 0;
}

@media (max-width: 768px) {
  .studio-page {
    padding: 0 0 var(--mobile-bottom-clear, 100px) !important;
  }
  .studio-header {
    /* Using ContentHeader padding now */
  }
  .studio-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }
  .studio-card-body {
    padding: 10px 12px 12px;
  }
  .studio-card-title {
    font-size: 13px;
  }
  .studio-card-badge {
    top: auto;
    right: 8px;
    bottom: 8px;
    background: rgba(0, 0, 0, 0.76);
    color: rgba(255, 255, 255, 0.96);
    border-color: rgba(255, 255, 255, 0.18);
  }
  .studio-card-new {
    top: 8px;
    left: 8px;
  }
}

.studio-card-skel-content {
  padding: var(--mobile-card-pad, 12px) 14px;
}
</style>
