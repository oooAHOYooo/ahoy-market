<template>
  <div class="events-page">
    <!-- Breadcrumb -->
    <nav class="ds-crumbs event-detail-crumbs" aria-label="Breadcrumb">
      <span class="ds-crumbs__item">
        <router-link to="/events" class="ds-crumbs__link">Events</router-link>
        <span class="ds-crumbs__sep">›</span>
      </span>
      <span class="ds-crumbs__item">
        <span class="ds-crumbs__current">{{ info.title || series }}</span>
      </span>
    </nav>

    <!-- Series Hero -->
    <section class="podcasts-section" v-if="!loading">
      <router-link
        v-if="heroEvent"
        :to="heroEvent.series && heroEvent.number ? `/events/${series}/${heroEvent.number}` : `/events/v/${encodeURIComponent(heroEvent.id)}`"
        class="podcast-show-hero featured-hero"
        style="margin-top:10px; text-decoration: none; color: inherit; display: block;"
      >
        <img
          class="podcast-show-hero-art"
          :src="heroEvent.image || '/static/img/default-cover.jpg'"
          :alt="heroEvent.title"
        />
        <div class="podcast-show-hero-meta">
          <div class="podcast-show-hero-kicker">{{ upcoming.length ? 'Next up' : 'Event series' }}</div>
          <h1 class="podcast-show-hero-title">{{ info.title || series }}</h1>
          <p class="podcast-show-hero-desc" v-if="info.description">{{ info.description }}</p>
          <div class="episode-subtitle" style="margin-bottom:10px" v-if="info.venue">
            <span>{{ info.venue }}</span>
            <span class="episode-dot" v-if="info.venue_address">•</span>
            <span v-if="info.venue_address">{{ info.venue_address }}</span>
          </div>
          <div class="podcast-show-hero-actions" v-if="upcoming.length">
            <a
              v-if="upcoming[0].rsvp_external_url"
              class="podcast-cta"
              :href="upcoming[0].rsvp_external_url"
              @click.stop
            >
              RSVP
            </a>
            <div class="podcast-cta secondary">
              VIEW #{{ upcoming[0].number }}
            </div>
          </div>
        </div>
      </router-link>

      <!-- No events found -->
      <div v-else-if="allSeriesEvents.length === 0" class="empty-state" style="margin-top:24px">
        <i class="fas fa-calendar-times"></i>
        <h4>Series not found</h4>
        <p><router-link to="/events" style="color:var(--accent-primary,#6ddcff)">See all events</router-link></p>
      </div>
    </section>

    <!-- Upcoming -->
    <section class="podcasts-section" v-if="!loading && upcoming.length">
      <div class="podcasts-section-header">
        <h2>Upcoming</h2>
      </div>
      <div class="episode-list" style="margin-top:12px">
        <router-link
          v-for="evt in upcoming"
          :key="evt.id || evt.title"
          :to="`/events/${series}/${evt.number}`"
          class="episode-row"
          style="text-decoration: none; color: inherit;"
        >
          <img
            class="episode-art"
            :src="evt.image || '/static/img/default-cover.jpg'"
            :alt="evt.title"
            loading="lazy"
          />
          <div class="episode-meta">
            <div class="episode-title">{{ evt.title }}</div>
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
            <a
              v-if="evt.rsvp_external_url"
              class="episode-open"
              :href="evt.rsvp_external_url"
              @click.stop
            >
              RSVP
            </a>
            <div class="podcast-cta secondary">VIEW</div>
          </div>
        </router-link>
      </div>
    </section>

    <!-- Past events -->
    <section class="podcasts-section" v-if="!loading && past.length">
      <div class="podcasts-section-header">
        <h2>Past events</h2>
      </div>
      <div class="episode-list">
        <router-link
          v-for="evt in past"
          :key="evt.id || evt.title"
          :to="`/events/${series}/${evt.number}`"
          class="episode-row"
          style="text-decoration: none; color: inherit;"
        >
          <img
            class="episode-art"
            :src="evt.image || '/static/img/default-cover.jpg'"
            :alt="evt.title"
            loading="lazy"
          />
          <div class="episode-meta">
            <div class="episode-title">{{ evt.title }}</div>
            <div class="episode-subtitle">
              <span>{{ formatDate(evt.date) }}</span>
              <span class="episode-dot">•</span>
              <span>{{ evt.venue || '' }}</span>
            </div>
            <div class="episode-desc" v-if="evt.description">{{ evt.description }}</div>
          </div>
          <div class="episode-actions">
            <div
              v-if="evt.studio_url"
              class="episode-open"
              @click.prevent="router.push(evt.studio_url)"
            >
              Studio
            </div>
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
import { useRoute, useRouter } from 'vue-router'
import { apiFetchCached } from '../composables/useApi'

const route = useRoute()
const router = useRouter()
const loading = ref(true)
const allEvents = ref([])
const seriesInfoMap = ref({})

const series = computed(() => route.params.series)

const info = computed(() => seriesInfoMap.value[series.value] || {})

const allSeriesEvents = computed(() =>
  allEvents.value.filter(e => e.series === series.value)
)

const upcoming = computed(() => {
  const list = allSeriesEvents.value.filter(e => String(e.status || '').toLowerCase() === 'upcoming')
  list.sort((a, b) => String(a.date || '').localeCompare(String(b.date || '')))
  return list
})

const past = computed(() => {
  const list = allSeriesEvents.value.filter(e => String(e.status || '').toLowerCase() === 'past')
  list.sort((a, b) => String(b.date || '').localeCompare(String(a.date || '')))
  return list
})

const heroEvent = computed(() => upcoming.value[0] || past.value[0] || null)

function formatDate(ds) {
  if (!ds) return ''
  const parts = String(ds).split('T')[0].split('-')
  const d = parts.length === 3
    ? new Date(Number(parts[0]), Number(parts[1]) - 1, Number(parts[2]))
    : new Date(ds)
  if (isNaN(d.getTime())) return String(ds)
  return d.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })
}

function updateMeta() {
  const title = info.value.title || series.value
  document.title = `${title} — Ahoy Indie Media`
  const desc = document.querySelector('meta[name="description"]')
  if (desc && info.value.description) desc.setAttribute('content', info.value.description.slice(0, 160))
}

async function load() {
  loading.value = true
  try {
    const data = await apiFetchCached('/api/events')
    allEvents.value = data.events || []
    seriesInfoMap.value = data.series_info || {}
  } catch {
    allEvents.value = []
    seriesInfoMap.value = {}
  }
  loading.value = false
  updateMeta()
}

onMounted(load)
watch(() => route.params.series, load)
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
</style>
