<template>
  <div class="events-page event-detail-page" v-if="event">
    <!-- Breadcrumb -->
    <nav class="ds-crumbs event-detail-crumbs" aria-label="Breadcrumb">
      <span class="ds-crumbs__item">
        <router-link to="/events" class="ds-crumbs__link">
          <i class="fas fa-chevron-left"></i> Events
        </router-link>
        <span class="ds-crumbs__sep">›</span>
      </span>
      <span v-if="event.series" class="ds-crumbs__item">
        <router-link :to="`/events/${event.series}`" class="ds-crumbs__link">{{ seriesTitle }}</router-link>
        <span class="ds-crumbs__sep">›</span>
      </span>
      <span class="ds-crumbs__item">
        <span class="ds-crumbs__current">{{ event.title }}</span>
      </span>
    </nav>

    <!-- Hero -->
    <section class="podcast-show-hero" style="margin-top:12px">
      <img
        class="podcast-show-hero-art"
        :src="event.image || '/static/img/default-cover.jpg'"
        :alt="event.title"
      />
      <div class="podcast-show-hero-meta">
        <div class="podcast-show-hero-kicker">{{ event.series ? seriesTitle : 'Event' }}</div>
        <h1 class="podcast-show-hero-title">{{ event.title }}</h1>
        <p class="podcast-show-hero-desc" v-if="event.description">{{ event.description }}</p>
        <div class="episode-subtitle" style="margin-bottom:10px">
          <span v-if="event.date">{{ formatDate(event.date) }}</span>
          <span class="episode-dot" v-if="event.date && event.time"> · </span>
          <span v-if="event.time">{{ event.time }}</span>
          <span class="episode-dot" v-if="(event.date || event.time) && event.venue"> · </span>
          <span v-if="event.venue">{{ event.venue }}</span>
        </div>
        <div class="episode-desc" v-if="event.venue_address" style="color:rgba(255,255,255,0.5);font-size:13px">
          {{ event.venue_address }}
        </div>
        <div class="event-detail-actions" style="margin-top:16px">
          <button class="event-action-btn" @click="bookmarks.toggle({ ...event, _type: 'event' })">
            <i :class="bookmarks.isBookmarked(event) ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
            {{ bookmarks.isBookmarked(event) ? 'Saved' : 'Save' }}
          </button>
          <a
            v-if="event.rsvp_external_url || event.rsvp_url || event.link"
            :href="event.rsvp_external_url || event.rsvp_url || event.link"
            target="_blank"
            class="event-action-btn primary"
            style="text-decoration:none"
          >
            <i class="fas fa-external-link-alt"></i>
            RSVP
          </a>
          <router-link
            v-if="event.studio_url"
            :to="event.studio_url"
            class="event-action-btn"
            style="text-decoration:none"
          >
            <i class="fas fa-camera"></i>
            Behind the Scenes
          </router-link>
        </div>
      </div>
    </section>

    <!-- Photos -->
    <section class="podcasts-section" v-if="event.photos && event.photos.length" style="margin-top:16px">
      <div class="podcasts-section-header">
        <h2>Photos</h2>
      </div>
      <div class="shows-grid" style="grid-template-columns:repeat(auto-fill,minmax(200px,1fr))">
        <div v-for="(photo, idx) in event.photos" :key="idx" style="border-radius:12px;overflow:hidden">
          <img :src="photo" :alt="`${event.title} photo`" loading="lazy" style="width:100%;display:block" />
        </div>
      </div>
    </section>
  </div>

  <!-- Loading -->
  <div class="events-page" v-else>
    <section class="podcast-show-hero" style="margin-top:24px">
      <div class="podcast-show-hero-art skeleton" style="aspect-ratio:16/9;width:100%"></div>
      <div class="podcast-show-hero-meta">
        <div class="skeleton" style="height:14px;width:30%;margin-bottom:8px"></div>
        <div class="skeleton" style="height:24px;width:60%;margin-bottom:8px"></div>
        <div class="skeleton" style="height:14px;width:80%"></div>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiFetchCached } from '../composables/useApi'
import { useBookmarks } from '../composables/useBookmarks'
import { setSeoMeta } from '../composables/useSeoMeta'

const route = useRoute()
const bookmarks = useBookmarks()

const event = ref(null)
const seriesInfo = ref({})

const seriesTitle = computed(() => {
  if (!event.value?.series) return ''
  return seriesInfo.value[event.value.series]?.title || event.value.series
})

function formatDate(ds) {
  if (!ds) return ''
  const parts = String(ds).split('T')[0].split('-')
  const d = parts.length === 3
    ? new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
    : new Date(ds)
  if (isNaN(d.getTime())) return String(ds)
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', year: 'numeric' })
}

function updateMeta(evt) {
  if (!evt) return
  setSeoMeta({
    title: evt.title,
    description: evt.description || `${evt.title} on Ahoy Indie Media.`,
    image: evt.image || '/static/img/ahoy_logo.png',
    type: 'article',
    url: window.location.pathname,
  })
}

async function loadEvent() {
  const { series, number, id } = route.params
  const data = await apiFetchCached('/api/events').catch(() => ({ events: [], series_info: {} }))
  const events = data.events || []
  seriesInfo.value = data.series_info || {}

  if (id) {
    event.value = events.find(e => String(e.id) === String(id)) || null
  } else {
    event.value = events.find(e =>
      e.series === series && String(e.number) === String(number)
    ) || null
  }
  updateMeta(event.value)
}

onMounted(loadEvent)
watch(() => route.params, loadEvent)
</script>

<style scoped>
.ds-crumbs__link {
  color: var(--accent-primary, #6ddcff);
  text-decoration: none;
}

.ds-crumbs__link:hover {
  text-decoration: underline;
}

@media (min-width: 1200px) {
  .podcast-show-hero-art {
    max-height: 400px;
  }
}

/* Adjust hero padding for full-width image */
.event-detail-page .podcast-show-hero {
  padding: 0;
  margin-bottom: 24px;
}

.event-detail-page .podcast-show-hero-art {
  width: 100%;
  object-fit: cover;
  display: block;
}

@media (min-width: 1200px) {
  .event-detail-page .podcast-show-hero-art {
    max-height: 400px;
  }
}
</style>
