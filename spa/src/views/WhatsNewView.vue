<template>
  <div class="whats-new-page" :class="`wn-${viewMode}-mode`">
    <ContentHeader
      kicker="Platform Updates"
      :title="pageTitle"
      :subtitle="pageSubtitle"
    />

    <div class="wn-content">
      <!-- Loading State -->
      <div v-if="loading" class="wn-loading">
        <i class="fas fa-circle-notch fa-spin"></i> Loading updates...
      </div>

      <!-- Error / Empty State -->
      <div v-else-if="error" class="wn-empty">
        <p>{{ error }}</p>
        <button @click="loadData" class="wn-cta">Try Again</button>
      </div>

      <!-- Archive View (Grid of Months) -->
      <WhatsNewArchive
        v-else-if="viewMode === 'archive'"
        :archive="archiveWithSections"
        :latest-updates="latestUpdates"
        :get-thumbnail="getThumbnail"
        :format-date="formatDate"
        :get-section-label="getSectionLabel"
        :detail-link-for="detailLinkFor"
      />

      <!-- Month View (Feed with Tabs) -->
      <WhatsNewMonth
        v-else-if="viewMode === 'month'"
        :title="pageTitle"
        :subtitle="pageSubtitle"
        :active-section="activeSection"
        :month-updates="monthUpdates"
        :available-sections="availableSections"
        :filtered-updates="filteredUpdates"
        :get-thumbnail="getThumbnail"
        :get-icon="getIcon"
        :format-date="formatDate"
        :get-type-label="getTypeLabel"
        :get-section-label="getSectionLabel"
        :get-feature-icon="getFeatureIcon"
        :get-cta-icon="getCtaIcon"
        :get-cta-text="getCtaText"
        :detail-link-for="detailLinkFor"
        @set-section="activeSection = $event"
      />

      <WhatsNewDetail
        v-else-if="viewMode === 'detail'"
        :month-path="monthPath"
        :detail-update="detailUpdate"
        :previous-update="previousUpdate"
        :next-update="nextUpdate"
        :get-thumbnail="getThumbnail"
        :get-type-label="getTypeLabel"
        :get-section-label="getSectionLabel"
        :get-cta-icon="getCtaIcon"
        :get-cta-text="getCtaText"
        :get-feature-icon="getFeatureIcon"
        :detail-link-for="detailLinkFor"
        :format-date="formatDate"
      />
      <WhatsNewVideoSourceView
        v-else-if="viewMode === 'video-source'"
        :detail-path="detailLinkPath"
        :detail-update="detailUpdate"
      />

      <!-- Defensive fallback: if the route is a month page but data has not hydrated yet, still render visible shell. -->
      <div v-else class="wn-empty">
        <p>Loading archive details...</p>
        <button @click="loadData" class="wn-cta">Reload</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { apiFetchCached } from '../composables/useApi'
import ContentHeader from '../components/ContentHeader.vue'
import WhatsNewArchive from '../components/whats-new/WhatsNewArchive.vue'
import WhatsNewMonth from '../components/whats-new/WhatsNewMonth.vue'
import WhatsNewDetail from '../components/whats-new/WhatsNewDetail.vue'
import WhatsNewVideoSourceView from './WhatsNewVideoSourceView.vue'
import { makeWhatsNewSlug, getWhatsNewDetailPath, getWhatsNewMonthPath } from '../utils/whatsNew'
import { setSeoMeta } from '../composables/useSeoMeta'

const route = useRoute()
const loading = ref(true)
const error = ref(null)
const archive = ref([])
const structured = ref({})
const allUpdates = ref([])
const activeSection = ref('all')

const viewMode = computed(() => {
  if (route.params.year && route.params.month && route.params.slug && route.path.endsWith('/videos')) return 'video-source'
  if (route.params.year && route.params.month && route.params.slug) return 'detail'
  return (route.params.year && route.params.month) ? 'month' : 'archive'
})

const detailLinkPath = computed(() => {
  if (!route.params.year || !route.params.month || !route.params.section || !route.params.slug) return '/whats-new'
  return `/whats-new/${route.params.year}/${route.params.month}/${route.params.section}/${route.params.slug}`
})

const monthPath = computed(() => {
  if (!route.params.year || !route.params.month) return '/whats-new'
  return `/whats-new/${route.params.year}/${route.params.month}`
})

const pageTitle = computed(() => {
  if (viewMode.value === 'detail') {
    return detailUpdate.value ? `${detailUpdate.value.title} — What's New` : "What's New — Ahoy"
  }
  if (viewMode.value === 'month') {
    const monthName = archive.value.find(m => m.year === String(route.params.year) && m.month === String(route.params.month).toLowerCase())?.month_name || route.params.month
    return `What's New — ${monthName} ${route.params.year}`
  }
  return "What's New at Ahoy"
})

const pageSubtitle = computed(() => {
  if (viewMode.value === 'detail') {
    return detailUpdate.value?.description || ''
  }
  if (viewMode.value === 'month') {
    return `Browse updates for ${route.params.month} ${route.params.year}`
  }
  return "Explore our archive of platform updates, new music, videos, and more."
})

function updateSeoMeta() {
  const detail = detailUpdate.value
  const latest = latestUpdates.value[0] || archive.value[0] || null

  if (viewMode.value === 'detail' && detail) {
    setSeoMeta({
      title: detail.title,
      description: detail.body || detail.description || pageSubtitle.value,
      image: [getThumbnail(detail), detail.thumbnail, detail.related_videos?.[0]?.thumbnail, '/static/img/ahoy_logo.png'],
      type: 'article',
      url: window.location.pathname,
    })
    return
  }

  setSeoMeta({
    title: pageTitle.value,
    description: pageSubtitle.value,
    image: [getThumbnail(latest), latest?.thumbnail, '/static/img/ahoy_logo.png'],
    type: 'website',
    url: window.location.pathname,
  })
}

const detailUpdate = computed(() => {
  if (viewMode.value !== 'detail' && viewMode.value !== 'video-source') return null
  const year = String(route.params.year)
  const month = String(route.params.month).toLowerCase()
  const section = String(route.params.section || '').toLowerCase()
  const slug = String(route.params.slug || '').toLowerCase()
  const yearData = structured.value[year]
  const monthData = yearData?.[month]
  const sectionData = monthData?.[section]
  const items = sectionData?.items || []
  return items.find((item) => makeUpdateSlug(item) === slug) || null
})

const routeMonthUpdates = computed(() => {
  if (!route.params.year || !route.params.month) return []
  const year = String(route.params.year)
  const month = String(route.params.month).toLowerCase()
  
  const yearData = structured.value[year]
  if (!yearData) return []
  
  const monthData = yearData[month]
  if (!monthData) return []
  
  const items = []
  const sectionOrder = ['music', 'videos', 'artists', 'platform', 'merch', 'events']
  
  sectionOrder.forEach(secKey => {
    const secData = monthData[secKey]
    if (secData && secData.items) {
      secData.items.forEach(item => {
        items.push({
          ...item,
          year,
          month,
          section: secKey
        })
      })
    }
  })
  
  return items.sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0))
})

const monthUpdates = computed(() => {
  if (viewMode.value !== 'month') return []
  return routeMonthUpdates.value
})

const detailIndex = computed(() => {
  if (viewMode.value !== 'detail' || !detailUpdate.value) return -1
  const slug = makeUpdateSlug(detailUpdate.value)
  return routeMonthUpdates.value.findIndex((item) => makeUpdateSlug(item) === slug)
})

const previousUpdate = computed(() => {
  if (detailIndex.value < 0) return null
  return routeMonthUpdates.value[detailIndex.value - 1] || null
})

const nextUpdate = computed(() => {
  if (detailIndex.value < 0) return null
  return routeMonthUpdates.value[detailIndex.value + 1] || null
})

const archiveWithSections = computed(() => {
  return archive.value.map((monthItem) => {
    const monthData = structured.value?.[monthItem.year]?.[monthItem.month]
    const sectionCounts = {}
    if (monthData) {
      Object.entries(monthData).forEach(([section, data]) => {
        const count = Array.isArray(data?.items) ? data.items.length : 0
        if (count > 0) sectionCounts[section] = count
      })
    }
    return {
      ...monthItem,
      section_counts: sectionCounts,
      section_keys: Object.keys(sectionCounts),
    }
  })
})

const availableSections = computed(() => {
  const sections = [
    { key: 'music', label: 'Music' },
    { key: 'videos', label: 'Videos' },
    { key: 'artists', label: 'Artists' },
    { key: 'platform', label: 'Platform' },
    { key: 'merch', label: 'Merch' },
    { key: 'events', label: 'Events' }
  ]
  
  return sections.map(s => {
    const count = monthUpdates.value.filter(u => u.section === s.key).length
    return { ...s, count }
  }).filter(s => s.count > 0)
})

const filteredUpdates = computed(() => {
  if (activeSection.value === 'all') return monthUpdates.value
  return monthUpdates.value.filter(u => u.section === activeSection.value)
})

const latestUpdates = computed(() => {
  return [...allUpdates.value]
    .filter(update => update?.date)
    .sort((a, b) => new Date(b.date || 0) - new Date(a.date || 0))
    .slice(0, 6)
})

const getIcon = (update) => {
  if (update.section === 'music') return 'fas fa-music'
  if (update.section === 'videos') return 'fas fa-play-circle'
  if (update.section === 'events') return 'fas fa-calendar-alt'
  return 'fas fa-sparkles'
}

const getThumbnail = (update) => {
  if (!update) return null
  if (update.thumbnail) return update.thumbnail
  if (Array.isArray(update.thumbnails) && update.thumbnails.length) {
    for (const thumb of update.thumbnails) {
      if (typeof thumb === 'string' && thumb) return thumb
      if (thumb && typeof thumb === 'object') {
        const url = thumb.url || thumb.src || thumb.thumbnail || thumb.image || thumb.path
        if (url) return url
      }
    }
  }
  if (Array.isArray(update.thumbnail_grid) && update.thumbnail_grid.length) {
    for (const thumb of update.thumbnail_grid) {
      if (typeof thumb === 'string' && thumb) return thumb
      if (thumb && typeof thumb === 'object') {
        const url = thumb.url || thumb.src || thumb.thumbnail || thumb.image || thumb.path
        if (url) return url
      }
    }
  }
  if (update.section === 'platform' && update.title?.toLowerCase().includes('desktop')) {
     return '/static/img/favicon_ahoy.png'
  }
  return null
}

const getTypeLabel = (update) => {
  const t = (update?.type || '').toLowerCase()
  if (t === 'content') return 'Content'
  if (t === 'feature') return 'Feature'
  if (t === 'technical') return 'Technical'
  if (t === 'improvement') return 'Improvement'
  return t ? t.charAt(0).toUpperCase() + t.slice(1) : ''
}

const getSectionLabel = (update) => {
  const s = (update?.section || '').toLowerCase()
  if (!s) return ''
  const labels = {
    'music': 'Music',
    'videos': 'Video',
    'artists': 'Artist',
    'platform': 'Platform',
    'merch': 'Merch',
    'events': 'Event'
  }
  return labels[s] || s.charAt(0).toUpperCase() + s.slice(1)
}

const getFeatureIcon = (feature) => {
  const f = feature.toLowerCase()
  if (f.includes('linux')) return 'fab fa-linux'
  if (f.includes('windows')) return 'fab fa-windows'
  if (f.includes('mac')) return 'fab fa-apple'
  if (f.includes('terminal')) return 'fas fa-terminal'
  return 'fas fa-check'
}

const getCtaIcon = (update) => {
  if (viewMode.value === 'month') return 'fas fa-arrow-right'
  if (update.link?.includes('download')) return 'fas fa-download'
  if (update.section === 'videos') return 'fas fa-play'
  if (update.section === 'music') return 'fas fa-music'
  if (update.section === 'events') return 'fas fa-calendar'
  return 'fas fa-arrow-right'
}

const getCtaText = (update) => {
  if (route.params.slug && viewMode.value === 'month') return 'View Details'
  if (update.link?.includes('download')) return 'Go to Downloads'
  if (update.section === 'videos') return 'Watch Now'
  if (update.section === 'music') return 'Open Music'
  if (update.section === 'events') return 'Open Event'
  if (update.section === 'platform') return 'Open Update'
  return 'View Details'
}

function makeUpdateSlug(update) {
  return makeWhatsNewSlug(update)
}

function detailLinkFor(update) {
  return getWhatsNewDetailPath(update)
}

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  try {
    const d = new Date(dateStr)
    return d.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
  } catch {
    return dateStr
  }
}

async function loadData() {
  loading.value = true
  error.value = null
  try {
    const data = await apiFetchCached('/api/whats-new')
    allUpdates.value = data.updates || []
    archive.value = data.archive || []
    structured.value = data.structured || {}
  } catch (e) {
    console.error('Error loading What\'s New data:', e)
    error.value = "Failed to load updates. Please try again."
  } finally {
    loading.value = false
  }
}

watch(() => route.params, () => {
  activeSection.value = 'all'
})

watch(
  () => [route.params.year, route.params.month, route.params.section],
  () => {
    activeSection.value = 'all'
    if (!loading.value && !archive.value.length) {
      loadData()
    }
  }
)

watch(
  () => [route.params.year, route.params.month, route.params.section, route.params.slug],
  () => {
    activeSection.value = 'all'
  }
)

onMounted(() => {
  loadData()
})

watch(detailUpdate, (val, prev) => {
  if (val && !prev) {
    nextTick(() => window.scrollTo({ top: 0, behavior: 'instant' }))
  }
})

watch(
  () => [viewMode.value, pageTitle.value, pageSubtitle.value, detailUpdate.value?.title, detailUpdate.value?.slug, archive.value[0]?.year, archive.value[0]?.month, latestUpdates.value[0]?.title],
  updateSeoMeta,
  { immediate: true }
)
</script>

<style scoped>
.whats-new-page {
  min-height: 100vh;
  background: var(--background-dark, #0c0c0e);
  color: var(--text-primary, #e5e7eb);
  padding: 0;
  padding-bottom: 5rem;
}

.wn-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

.wn-loading, .wn-empty {
  text-align: center;
  padding: 5rem 2rem;
  color: rgba(255, 255, 255, 0.5);
  background: rgba(19, 19, 22, 0.4);
  border-radius: 24px;
  border: 1px dashed rgba(255, 255, 255, 0.1);
}

.wn-detail {
  max-width: 900px;
  margin: 0 auto;
}

.wn-detail-card {
  margin-top: 1.5rem;
  padding: 0;
  background: rgba(20, 20, 22, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 28px;
  overflow: hidden;
}

.wn-detail-hero img {
  width: 100%;
  display: block;
  aspect-ratio: 16 / 9;
  object-fit: cover;
}

.wn-detail-header {
  padding: 2rem;
}

.wn-detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 1rem;
}

.wn-detail-header h1 {
  margin: 0;
  font-size: clamp(2rem, 5vw, 3.4rem);
  line-height: 1.05;
}

.wn-detail-lead {
  margin: 1rem 0 0;
  color: rgba(255, 255, 255, 0.78);
  font-size: 1.05rem;
  line-height: 1.7;
}

.wn-detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 0 2rem 2rem;
}

.wn-cta.secondary {
  background: rgba(255, 255, 255, 0.08);
}

/* Archive Grid */
.months-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
}

.month-card {
  display: flex;
  flex-direction: column;
  background: rgba(20, 20, 20, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 1.5rem;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  overflow: hidden;
}

.month-card:hover {
  background: rgba(30, 30, 30, 0.8);
  border-color: rgba(255, 255, 255, 0.15);
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
}

.month-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.month-card-header h3 {
  font-size: 1.5rem;
  font-weight: 700;
  color: #fff;
  margin: 0;
}

.month-year {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  font-weight: 500;
}

.month-items-count {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.7);
}

.month-card-arrow {
  position: absolute;
  bottom: 1.5rem;
  right: 1.5rem;
  color: rgba(255, 255, 255, 0.4);
  transition: all 0.3s ease;
}

.month-card:hover .month-card-arrow {
  color: #fff;
  transform: translateX(4px);
}

/* Month View */
.month-header-nav {
  margin-bottom: 2rem;
}

.back-link {
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  font-size: 0.9rem;
  display: inline-flex;
  align-items: center;
  gap: 0.6rem;
  transition: color 0.2s;
}

.back-link:hover {
  color: #fff;
}

.section-tabs {
  display: flex;
  gap: 0.75rem;
  margin-bottom: 2.5rem;
  flex-wrap: nowrap;
  justify-content: flex-start;
  overflow-x: auto;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 1.5rem;
  scrollbar-width: none;
}

.section-tabs::-webkit-scrollbar {
  display: none;
}

.section-tab {
  padding: 0.6rem 1.25rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 999px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  font-weight: 600;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  cursor: pointer;
  flex-shrink: 0;
  width: auto;
}

.section-tab:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.section-tab.active {
  background: rgba(255, 255, 255, 0.9);
  color: #000;
  border-color: #fff;
}

.tab-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  background: rgba(255, 255, 255, 0.15);
  color: inherit;
  border-radius: 10px;
  font-size: 0.75rem;
  font-weight: 700;
}

.section-tab.active .tab-badge {
  background: rgba(0, 0, 0, 0.1);
}

/* Feed & Cards */
.wn-feed {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  max-width: 800px;
  margin: 0 auto;
}

.wn-card {
  background: rgba(20, 20, 22, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  padding: 2rem;
  position: relative;
  transition: all 0.3s ease;
  overflow: hidden;
}

.wn-card:hover {
  border-color: rgba(255, 255, 255, 0.15);
  background: rgba(25, 25, 28, 0.8);
}

.wn-card-badge {
  position: absolute;
  top: 2rem;
  right: 2rem;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.7rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: rgba(52, 211, 153, 0.15);
  color: #34d399;
  border: 1px solid rgba(52, 211, 153, 0.2);
  z-index: 10;
}

.wn-card-hero {
  margin: -2rem -2rem 1.5rem -2rem;
  aspect-ratio: 21 / 9;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  background: #000;
  overflow: hidden;
}

.wn-card-hero a {
  display: block;
  width: 100%;
  height: 100%;
}

.wn-card-hero img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.4s ease;
}

.wn-card-hero a:hover img {
  transform: scale(1.05);
}

.wn-card-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.wn-card-icon {
  width: 56px;
  height: 56px;
  flex-shrink: 0;
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.wn-card-icon.music { color: #ec4899; background: rgba(236, 72, 153, 0.1); border-color: rgba(236, 72, 153, 0.2); }
.wn-card-icon.videos { color: #38bdf8; background: rgba(56, 189, 248, 0.1); border-color: rgba(56, 189, 248, 0.2); }
.wn-card-icon.platform { color: #a78bfa; background: rgba(167, 139, 250, 0.1); border-color: rgba(167, 139, 250, 0.2); }

.wn-card-favicon {
  width: 100%;
  height: 100%;
  object-fit: contain;
  padding: 8px;
}

.wn-card-header h2 {
  margin: 0 0 6px;
  font-size: 1.4rem;
  font-weight: 800;
  color: #fff;
  letter-spacing: -0.01em;
}

.wn-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.wn-date {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.4);
  font-weight: 500;
}

.wn-pill {
  display: inline-flex;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.6);
}

.wn-pill.t-content { color: #34d399; background: rgba(52, 211, 153, 0.1); border-color: rgba(52, 211, 153, 0.2); }
.wn-pill.t-feature { color: #6366f1; background: rgba(99, 102, 241, 0.1); border-color: rgba(99, 102, 241, 0.2); }
.wn-pill.t-improvement { color: #f59e0b; background: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.2); }

.wn-pill.section { opacity: 0.8; }

.wn-body {
  margin: 0 0 1.5rem;
  font-size: 1.05rem;
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.6;
  white-space: pre-line;
}

.wn-install-list {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 16px;
  padding: 1.25rem;
  margin-bottom: 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.wn-install-row {
  display: flex;
  align-items: center;
}

.wn-install-label {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.wn-install-label i {
  color: #a78bfa;
  width: 16px;
  text-align: center;
}

.wn-cta {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1.5rem;
  border-radius: 12px;
  font-size: 0.95rem;
  font-weight: 700;
  text-decoration: none;
  background: #fff;
  color: #000;
  transition: all 0.2s ease;
  border: none;
  cursor: pointer;
}

.wn-cta:hover {
  transform: scale(1.02);
  box-shadow: 0 8px 24px rgba(255, 255, 255, 0.2);
}

@media (max-width: 768px) {
  .whats-new-page {
    padding-bottom: var(--mobile-bottom-clear, 120px);
  }

  .wn-archive-mode :deep(.content-header),
  .wn-month-mode :deep(.content-header),
  .wn-detail-mode :deep(.content-header) {
    display: none;
  }

  .wn-content {
    padding: 0 var(--mobile-gutter, 10px);
  }

  .section-tabs { gap: 0.5rem; }
  .section-tab { padding: 0.5rem 1rem; font-size: 0.85rem; }
  .wn-card { padding: 1.5rem; }
  .wn-card-hero { margin: -1.5rem -1.5rem 1.5rem -1.5rem; aspect-ratio: 4 / 3; }
  .wn-card-header { gap: 1rem; }
  .wn-card-icon { width: 48px; height: 48px; border-radius: 12px; font-size: 1.2rem; }
  .wn-card-header h2 { font-size: 1.2rem; }
  .wn-card-badge { top: 1.5rem; right: 1.5rem; }
}
</style>
