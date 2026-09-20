<template>
  <div class="events-page">
    <ContentHeader
      kicker="Ahoy Indie Media"
      title="Events"
      subtitle="Live performances and community gatherings."
    />
    <section class="page-mobile-hero" aria-label="Events">
      <div class="page-mobile-hero-copy">
        <span class="page-mobile-eyebrow">Live</span>
        <h1>Events</h1>
        <p>{{ rawEvents?.events?.length ? `${rawEvents.events.length} event${rawEvents.events.length === 1 ? '' : 's'} — live shows & community gatherings` : 'Live performances and community gatherings.' }}</p>
      </div>
    </section>
    <!-- Upcoming -->
    <section class="podcasts-section">
      <div class="podcasts-section-header">
        <h2>Upcoming</h2>
      </div>

      <!-- Featured event hero (first upcoming) -->
      <router-link
        v-if="featured"
        :to="getEventLink(featured)"
        class="podcast-show-hero featured-hero"
        :class="{ 'no-link': !getEventLink(featured) }"
      >
        <img
          class="podcast-show-hero-art"
          :src="featured.image || '/static/img/default-cover.jpg'"
          :alt="featured.title"
        />
        <div class="podcast-show-hero-meta">
          <div class="podcast-show-hero-kicker">Featured event</div>
          <h1 class="podcast-show-hero-title">{{ featured.title }}</h1>
          <p class="podcast-show-hero-desc">{{ featured.description }}</p>
          <div class="episode-subtitle featured-subtitle">
            <span>{{ formatDate(featured.date) }}</span>
            <span class="episode-dot">•</span>
            <span>{{ featured.time || '' }}</span>
            <span class="episode-dot" v-if="featured.venue">•</span>
            <span v-if="featured.venue">{{ featured.venue }}</span>
          </div>
          <div class="podcast-show-hero-actions">
            <div
              v-if="getEventLink(featured)"
              class="podcast-cta"
            >
              VIEW
            </div>
          </div>
        </div>
      </router-link>

      <div class="episode-list upcoming-list">
        <router-link
          v-for="evt in upcoming"
          :key="evt.id || evt.title"
          :to="getEventLink(evt)"
          class="episode-row"
          :class="{ 'no-link': !getEventLink(evt) }"
        >
          <img
            class="episode-art"
            :src="evt.image || '/static/img/default-cover.jpg'"
            :alt="evt.title"
            loading="lazy"
          />
          <div class="episode-meta">
            <div class="episode-title">{{ evt.title || 'Live Show' }}</div>
            <div class="episode-subtitle">
              <span>{{ formatDate(evt.date) }}</span>
              <span class="episode-dot">•</span>
              <span>{{ evt.time || '' }}</span>
              <span class="episode-dot" v-if="evt.venue">•</span>
              <span v-if="evt.venue">{{ evt.venue }}</span>
            </div>
            <div class="episode-desc" v-if="evt.description">{{ evt.description }}</div>
          </div>
          <div class="episode-actions">
            <div class="podcast-cta secondary">VIEW</div>
          </div>
        </router-link>
      </div>

      <div v-if="!loading && upcoming.length === 0" class="empty-state upcoming-empty">
        <i class="fas fa-calendar-times"></i>
        <h4>No upcoming events</h4>
        <p>Check back soon.</p>
      </div>
    </section>

    <!-- Past events -->
    <section class="podcasts-section">
      <div class="podcasts-section-header">
        <h2>Past events</h2>
      </div>

      <div class="episode-list">
        <router-link
          v-for="evt in past"
          :key="evt.id || evt.title"
          :to="getEventLink(evt)"
          class="episode-row"
          :class="{ 'no-link': !getEventLink(evt) }"
        >
          <img
            class="episode-art"
            :src="evt.image || '/static/img/default-cover.jpg'"
            :alt="evt.title"
            loading="lazy"
          />
          <div class="episode-meta">
            <div class="episode-title">{{ evt.title || 'Event' }}</div>
            <div class="episode-subtitle">
              <span>{{ formatDate(evt.date) }}</span>
              <span class="episode-dot">•</span>
              <span>{{ evt.venue || '' }}</span>
              <span class="episode-dot" v-if="evt.videoStatus">•</span>
              <span v-if="evt.videoStatus">{{ evt.videoStatus }}</span>
            </div>
            <div class="episode-desc" v-if="evt.description">{{ evt.description }}</div>
          </div>
          <div class="episode-actions" @click.stop>
            <a
              v-if="evt.videoUrl"
              class="episode-open"
              :href="evt.videoUrl"
              target="_blank"
              rel="noopener"
              @click.stop
              title="Watch video"
            >
              <i class="fas fa-play"></i>
            </a>
            <router-link
              v-if="evt.studio_url"
              :to="evt.studio_url"
              class="episode-open"
              @click.stop
            >
              Studio
            </router-link>
            <span
              v-if="!evt.videoUrl && evt.videoStatus"
              class="episode-open"
              style="opacity:0.7; cursor:default;"
            >
              {{ evt.videoStatus }}
            </span>
            <div class="podcast-cta secondary">VIEW</div>
          </div>
        </router-link>
      </div>
    </section>

    <!-- Loading -->
    <section v-if="loading" class="podcasts-section">
      <div class="episode-list">
        <div class="episode-row" v-for="i in 4" :key="i">
          <div class="episode-art skeleton" style="width:80px;height:80px;border-radius:8px"></div>
          <div class="episode-meta">
            <div class="skeleton" style="height:14px;width:60%;margin-bottom:6px"></div>
            <div class="skeleton" style="height:12px;width:40%"></div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { apiFetchCached } from '../composables/useApi'
import ContentHeader from '../components/ContentHeader.vue'

const loading = ref(true)
const rawEvents = ref([])
const rawVideos = ref([])

const origin = typeof window !== 'undefined' ? window.location.origin : ''

function isRemoteUrl(u) {
  return typeof u === 'string' && /^https?:\/\//i.test(u)
}

function pickFirstRemote(arr) {
  if (!Array.isArray(arr)) return null
  for (const u of arr) {
    if (isRemoteUrl(u)) return u
  }
  return null
}

const normalizedEvents = computed(() => {
  const events = Array.isArray(rawEvents.value?.events) ? rawEvents.value.events : []
  const videos = Array.isArray(rawVideos.value?.videos) ? rawVideos.value.videos : []
  const videoByEventId = new Map()
  for (const v of videos) {
    if (!v?.event_id) continue
    videoByEventId.set(String(v.event_id), v)
  }
  return events.map((e) => {
    const vid = videoByEventId.get(String(e.id || ''))
    const remotePhoto = pickFirstRemote(e?.photos)
    const remoteImage = isRemoteUrl(e?.image) ? e.image : null
    const remoteThumb = isRemoteUrl(vid?.thumbnail) ? vid.thumbnail : null
    return {
      ...e,
      image: remotePhoto || remoteImage || remoteThumb || null,
      photos: Array.isArray(e?.photos) ? e.photos.filter(isRemoteUrl) : [],
      videoUrl: vid?.url || null,
      videoStatus:
        vid?.status === 'available'
          ? 'Recording available'
          : vid?.status === 'coming_soon'
            ? 'Recording coming soon'
            : '',
    }
  })
})

const upcoming = computed(() => {
  const list = normalizedEvents.value.filter((e) => String(e.status || '').toLowerCase() === 'upcoming')
  const unknown = normalizedEvents.value.filter(
    (e) => !['upcoming', 'past'].includes(String(e.status || '').toLowerCase())
  )
  const now = new Date()
  for (const e of unknown) {
    const d = e.date ? new Date(e.date) : null
    if (!d || isNaN(d.getTime())) list.push(e)
    else if (d >= now) list.push(e)
  }
  list.sort((a, b) => String(a.date || '').localeCompare(String(b.date || '')))
  return list.slice(0, 12)
})

const past = computed(() => {
  const list = normalizedEvents.value.filter((e) => String(e.status || '').toLowerCase() === 'past')
  const unknown = normalizedEvents.value.filter(
    (e) => !['upcoming', 'past'].includes(String(e.status || '').toLowerCase())
  )
  const now = new Date()
  for (const e of unknown) {
    const d = e.date ? new Date(e.date) : null
    if (d && !isNaN(d.getTime()) && d < now) list.push(e)
  }
  list.sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')))
  return list
})

const featured = computed(() => upcoming.value[0] || null)

watch(featured, (newFeatured) => {
  if (newFeatured) {
    document.title = `Events: ${newFeatured.title} | Ahoy Indie Media`
  } else {
    document.title = 'Events | Ahoy Indie Media'
  }
}, { immediate: true })

function formatDate(ds) {
  if (!ds) return ''
  // Parse YYYY-MM-DD as local time (not UTC) to avoid off-by-one-day timezone shift
  const parts = String(ds).split('T')[0].split('-')
  const d = parts.length === 3
    ? new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
    : new Date(ds)
  if (isNaN(d.getTime())) return String(ds)
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

function getEventLink(evt) {
  if (!evt) return null
  if (evt.series && evt.number) return `/events/${evt.series}/${evt.number}`
  if (evt.id) return `/events/v/${encodeURIComponent(evt.id)}`
  return null
}

async function copyLink(url) {
  try {
    await navigator.clipboard.writeText(url)
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Link copied.' } }))
  } catch (_) {}
}

onMounted(async () => {
  loading.value = true
  try {
    const data = await apiFetchCached('/api/events')
    rawEvents.value = { events: data.events || [] }
    rawVideos.value = { videos: data.videos || [] }
  } catch {
    rawEvents.value = { events: [] }
    rawVideos.value = { videos: [] }
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

.events-page {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem 5rem;
}

.podcasts-section {
  margin-top: 2rem;
}

.podcasts-section-header h2 {
  font-size: 1.8rem;
  font-weight: 800;
  margin-bottom: 1.5rem;
  letter-spacing: -0.02em;
}

.featured-hero {
  margin-top: 1rem;
  border-radius: 24px;
  overflow: hidden;
  background: rgba(20, 20, 24, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(20px);
  transition: transform 0.3s ease, border-color 0.3s ease;
  text-decoration: none;
  color: inherit;
  display: block;
}

.featured-hero:hover {
  border-color: rgba(255, 255, 255, 0.2);
}

.featured-hero .podcast-show-hero-art {
  width: 100%;
  object-fit: cover;
  display: block;
}

@media (min-width: 1200px) {
  .featured-hero .podcast-show-hero-art {
    max-height: 400px;
  }
}

.episode-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.episode-row {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  padding: 1.25rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 20px;
  text-decoration: none;
  color: inherit;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.episode-row:hover {
  background: rgba(255, 255, 255, 0.07);
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
}

.episode-row:active {
  transform: translateY(0);
}

.episode-row.no-link {
  cursor: default;
  opacity: 0.8;
}

.episode-row.no-link:hover {
  transform: none;
  border-color: rgba(255, 255, 255, 0.05);
  background: rgba(255, 255, 255, 0.03);
}

.episode-art {
  width: 100px;
  height: 100px;
  border-radius: 12px;
  object-fit: cover;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.episode-meta {
  flex-grow: 1;
}

.episode-title {
  font-size: 1.25rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
  color: #fff;
}

.episode-subtitle {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 0.75rem;
  flex-wrap: wrap;
}

.episode-dot {
  opacity: 0.3;
}

.episode-desc {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.episode-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.episode-open {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  transition: all 0.2s ease;
  font-size: 0.9rem;
  text-decoration: none;
}

.episode-open:hover {
  background: #fff;
  color: #000;
  transform: scale(1.1);
}

@media (max-width: 768px) {
  .events-page {
    padding: 0 0 var(--mobile-bottom-clear, 100px);
  }

  .episode-row {
    padding: 1rem;
    gap: 1rem;
  }

  .episode-art {
    width: 80px;
    height: 80px;
  }

  .episode-title {
    font-size: 1.1rem;
  }

  .episode-desc {
    -webkit-line-clamp: 2;
  }
}
</style>
