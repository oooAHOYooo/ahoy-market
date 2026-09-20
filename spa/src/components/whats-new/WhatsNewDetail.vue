<template>
  <div class="wn-detail">
    <router-link :to="monthPath" class="back-link"><i class="fas fa-arrow-left"></i> Back to month</router-link>
    <article v-if="detailUpdate" class="wn-detail-card">
      <div
        class="wn-detail-hero"
        :class="{ 'has-image': !!getThumbnail(detailUpdate), 'is-clickable': !!sourceLink }"
        @click="sourceLink && $router.push(sourceLink)"
      >
        <img v-if="heroImage" :src="heroImage" :alt="detailUpdate.title" />
        <div v-else class="wn-detail-placeholder">
          <span class="wn-detail-placeholder-kicker">{{ getSectionLabel(detailUpdate) || 'Update' }}</span>
          <h2>{{ detailUpdate.title }}</h2>
        </div>
      </div>
      <div class="wn-detail-header">
        <div class="wn-detail-meta">
          <span class="wn-pill section">{{ getSectionLabel(detailUpdate) }}</span>
          <time class="wn-date">{{ formatDate(detailUpdate.date) }}</time>
        </div>
        <h1>{{ detailUpdate.title }}</h1>
        <p class="wn-detail-lead">{{ detailUpdate.body || detailUpdate.description }}</p>
      </div>
      <section
        v-if="filmDetails.premiered || filmDetails.filmedAndEditedBy || filmDetails.skaters.length"
        class="wn-film-credits"
        aria-label="Film details"
      >
        <div class="wn-film-credits-head">
          <span class="wn-film-credits-kicker">Film Details</span>
          <p v-if="filmDetails.premiered">Premiered {{ filmDetails.premiered }}</p>
        </div>
        <div v-if="filmDetails.filmedAndEditedBy" class="wn-film-credits-meta">
          <h3>Filmed and Edited by</h3>
          <p>{{ filmDetails.filmedAndEditedBy }}</p>
        </div>
        <div v-if="filmDetails.skaters.length" class="wn-film-credits-skaters">
          <h3>Featured Skaters</h3>
          <ul>
            <li v-for="skater in filmDetails.skaters" :key="skater">{{ skater }}</li>
          </ul>
        </div>
      </section>
      <section v-if="thumbnailGallery.length" class="wn-thumbnail-section" aria-label="Update thumbnails">
        <div class="wn-thumbnail-head">
          <span class="wn-thumbnail-kicker">Thumbnails</span>
          <p>Tap a frame to browse the full set.</p>
        </div>
        <div class="wn-thumbnail-grid">
          <button
            v-for="(thumbnail, idx) in thumbnailGallery"
            :key="`${thumbnail}-${idx}`"
            type="button"
            class="wn-thumbnail-card"
            @click="openLightbox(idx)"
            :aria-label="`Open thumbnail ${idx + 1} of ${thumbnailGallery.length}`"
          >
            <img :src="thumbnail" :alt="`${detailUpdate.title} thumbnail ${idx + 1}`" loading="lazy" />
            <span class="wn-thumbnail-index">{{ idx + 1 }}</span>
          </button>
        </div>
      </section>
      <div v-if="relatedCards.length" class="wn-related">
        <div class="wn-related-head">
          <span class="wn-related-kicker">{{ relatedHeading }}</span>
          <p>{{ relatedSubhead }}</p>
        </div>
        <div class="wn-related-grid">
          <router-link
            v-for="video in relatedCards"
            :key="video.path"
            :to="video.path"
            class="wn-related-card"
            :class="{ fallback: video.isFallback }"
          >
            <div class="wn-related-thumb">
              <img v-if="video.thumbnail" :src="video.thumbnail" :alt="video.title" />
              <span v-else class="wn-related-fallback">{{ video.shortLabel || 'Video' }}</span>
            </div>
            <div class="wn-related-copy">
              <strong>{{ video.title }}</strong>
              <span>{{ video.description }}</span>
            </div>
          </router-link>
        </div>
      </div>
      <ul v-if="detailUpdate.features && detailUpdate.features.length" class="wn-bullet-list">
        <li v-for="(feature, fidx) in detailUpdate.features" :key="fidx">{{ feature }}</li>
      </ul>
      <div class="wn-detail-actions" :class="{ 'has-dual-cta': !!listenLink }">
        <template v-if="listenLink">
          <router-link :to="sourceLink" class="wn-cta primary">
            <i class="source-cta-icon fas fa-play" aria-hidden="true"></i>
            <span>Watch Video</span>
          </router-link>
          <router-link :to="listenLink" class="wn-cta secondary listen-cta">
            <i class="source-cta-icon fas fa-headphones" aria-hidden="true"></i>
            <span>Listen</span>
          </router-link>
        </template>
        <template v-else>
          <router-link v-if="monthPath" :to="monthPath" class="wn-cta secondary">Back to month</router-link>
          <router-link v-if="sourceLink" :to="sourceLink" class="wn-cta primary">
            <i class="source-cta-icon" :class="sourceCtaIcon" aria-hidden="true"></i>
            <span>{{ sourceCtaText }}</span>
          </router-link>
        </template>
      </div>
      <div class="wn-share-row">
        <button class="wn-share-btn" @click="copyLink" :class="{ copied }">
          <i :class="copied ? 'fas fa-check' : 'fas fa-link'" aria-hidden="true"></i>
          <span>{{ copied ? 'Copied!' : 'Copy link' }}</span>
        </button>
      </div>
      <nav v-if="previousUpdate || nextUpdate" class="wn-detail-neighbors" aria-label="Browse updates in this month">
        <router-link
          v-if="previousUpdate"
          :to="detailLinkFor(previousUpdate)"
          class="wn-neighbor-pill previous"
        >
          <i class="fas fa-arrow-left" aria-hidden="true"></i>
          <span>
            <small>Previous</small>
            <strong>{{ previousUpdate.title }}</strong>
          </span>
        </router-link>
        <span v-else class="wn-neighbor-spacer" aria-hidden="true"></span>
        <router-link
          v-if="nextUpdate"
          :to="detailLinkFor(nextUpdate)"
          class="wn-neighbor-pill next"
        >
          <span>
            <small>Next</small>
            <strong>{{ nextUpdate.title }}</strong>
          </span>
          <i class="fas fa-arrow-right" aria-hidden="true"></i>
        </router-link>
      </nav>
    </article>
    <div v-else class="wn-empty">
      <p>That update could not be found.</p>
      <router-link :to="monthPath" class="wn-cta">Back to month</router-link>
    </div>

    <Teleport to="body">
      <Transition name="wn-lb-fade">
        <div v-if="lightboxOpen" class="wn-lightbox" @click.self="closeLightbox">
          <button class="wn-lightbox-close" @click="closeLightbox" aria-label="Close lightbox">
            <i class="fas fa-times"></i>
          </button>

          <button
            v-if="thumbnailGallery.length > 1"
            class="wn-lightbox-arrow wn-lightbox-prev"
            @click="prevThumbnail"
            aria-label="Previous thumbnail"
          >
            <i class="fas fa-chevron-left"></i>
          </button>

          <div class="wn-lightbox-frame" @click.stop>
            <Transition name="wn-lb-image" mode="out-in">
              <img
                :key="lightboxIndex"
                :src="thumbnailGallery[lightboxIndex]"
                :alt="`Thumbnail ${lightboxIndex + 1} of ${thumbnailGallery.length}`"
                class="wn-lightbox-image"
              />
            </Transition>
          </div>

          <button
            v-if="thumbnailGallery.length > 1"
            class="wn-lightbox-arrow wn-lightbox-next"
            @click="nextThumbnail"
            aria-label="Next thumbnail"
          >
            <i class="fas fa-chevron-right"></i>
          </button>

          <div class="wn-lightbox-counter">
            {{ lightboxIndex + 1 }} / {{ thumbnailGallery.length }}
            <span v-if="thumbnailGallery.length > 1" class="wn-lightbox-hint">· swipe to navigate</span>
          </div>
        </div>
      </Transition>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue'

const props = defineProps({
  monthPath: String,
  detailUpdate: Object,
  previousUpdate: Object,
  nextUpdate: Object,
  getThumbnail: Function,
  getTypeLabel: Function,
  getSectionLabel: Function,
  getFeatureIcon: Function,
  detailLinkFor: { type: Function, default: () => '/whats-new' },
  formatDate: Function,
})

const normalizeThumbnail = (entry) => {
  if (!entry) return ''
  if (typeof entry === 'string') return entry
  if (typeof entry !== 'object') return ''
  return entry.url || entry.src || entry.thumbnail || entry.image || entry.path || ''
}

const thumbnailGallery = computed(() => {
  const update = props.detailUpdate || {}
  const raw = Array.isArray(update.thumbnails)
    ? update.thumbnails
    : Array.isArray(update.thumbnail_grid)
      ? update.thumbnail_grid
    : Array.isArray(update.extra_fields?.thumbnails)
      ? update.extra_fields.thumbnails
      : Array.isArray(update.extra_fields?.thumbnail_grid)
        ? update.extra_fields.thumbnail_grid
      : []
  const images = []
  const primary = props.getThumbnail?.(update) || update.thumbnail || ''
  if (primary) images.push(primary)
  raw.forEach((entry) => {
    const normalized = normalizeThumbnail(entry)
    if (normalized) images.push(normalized)
  })
  return [...new Set(images)]
})

const filmDetails = computed(() => {
  const update = props.detailUpdate || {}
  return {
    premiered: update.premiered || '',
    filmedAndEditedBy: update.filmed_and_edited_by || update.filmed_by || '',
    skaters: Array.isArray(update.featured_skaters)
      ? update.featured_skaters.map((skater) => String(skater || '').trim()).filter(Boolean)
      : [],
  }
})

const heroImage = computed(() => {
  return props.getThumbnail?.(props.detailUpdate || {}) || thumbnailGallery.value[0] || ''
})

const sourceCtaText = computed(() => {
  const update = props.detailUpdate || {}
  if (update.link?.includes('download')) return 'Downloads'
  if (update.section === 'videos' && (Array.isArray(update.related_videos) && update.related_videos.length > 1)) return 'Open playlist'
  if (update.section === 'videos') return 'Watch Video'
  if (update.section === 'music') return 'Open Music'
  if (update.section === 'events') return 'Open Event'
  if (update.section === 'platform') return 'Open Update'
  return 'Open Link'
})

const sourceCtaIcon = computed(() => {
  const update = props.detailUpdate || {}
  if (update.link?.includes('download')) return 'fas fa-download'
  if (update.section === 'videos' && (Array.isArray(update.related_videos) && update.related_videos.length > 1)) return 'fas fa-list'
  if (update.section === 'videos') return 'fas fa-play'
  if (update.section === 'music') return 'fas fa-music'
  if (update.section === 'events') return 'fas fa-calendar'
  return 'fas fa-arrow-up-right-from-square'
})

const sourceLink = computed(() => {
  const update = props.detailUpdate || {}
  if (update.section === 'videos' && update.source_playlist_link) {
    return update.source_playlist_link
  }
  if (update.section === 'videos' && update.source_link) {
    return update.source_link
  }
  if (update.section === 'videos') {
    const firstVideo = Array.isArray(update.related_videos) ? update.related_videos.find((video) => video?.path) : null
    if (firstVideo?.path) return firstVideo.path
  }
  return update.link || null
})

const relatedHeading = computed(() => {
  const update = props.detailUpdate || {}
  const title = String(update.title || '').toLowerCase()
  if (update.section === 'videos' && title.includes('tallboyz')) return 'More from Tallboyz'
  if (update.section === 'videos') return 'Featured videos'
  return 'Related videos'
})

const relatedSubhead = computed(() => {
  const update = props.detailUpdate || {}
  const title = String(update.title || '').toLowerCase()
  if (update.section === 'videos' && title.includes('tallboyz')) {
    return 'One direct match and a quick path back to the full Tallboyz video library.'
  }
  return 'Direct links to the videos behind this update.'
})

const listenLink = computed(() => {
  return props.detailUpdate?.listen_link || null
})

const relatedCards = computed(() => {
  const update = props.detailUpdate || {}
  const cards = Array.isArray(update.related_videos) ? [...update.related_videos] : []
  if (update.section === 'videos' && cards.length < 2) {
    cards.push({
      title: 'Browse the video library',
      description: 'Open the full videos page to keep going.',
      path: '/videos',
      shortLabel: 'Library',
      isFallback: true,
    })
  }
  return cards
})

const copied = ref(false)
const lightboxOpen = ref(false)
const lightboxIndex = ref(0)
let touchStartX = 0
let touchStartY = 0

function openLightbox(index) {
  if (!thumbnailGallery.value.length) return
  lightboxIndex.value = index
  lightboxOpen.value = true
  document.body.style.overflow = 'hidden'
}

function closeLightbox() {
  lightboxOpen.value = false
  document.body.style.overflow = ''
}

function prevThumbnail() {
  if (!thumbnailGallery.value.length) return
  lightboxIndex.value = (lightboxIndex.value - 1 + thumbnailGallery.value.length) % thumbnailGallery.value.length
}

function nextThumbnail() {
  if (!thumbnailGallery.value.length) return
  lightboxIndex.value = (lightboxIndex.value + 1) % thumbnailGallery.value.length
}

function onKeyDown(event) {
  if (!lightboxOpen.value) return
  if (event.key === 'Escape') closeLightbox()
  if (event.key === 'ArrowLeft') prevThumbnail()
  if (event.key === 'ArrowRight') nextThumbnail()
}

function onTouchStart(event) {
  if (!lightboxOpen.value) return
  touchStartX = event.touches[0].clientX
  touchStartY = event.touches[0].clientY
}

function onTouchEnd(event) {
  if (!lightboxOpen.value) return
  const dx = event.changedTouches[0].clientX - touchStartX
  const dy = event.changedTouches[0].clientY - touchStartY
  if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(dy) * 1.5) {
    if (dx < 0) nextThumbnail()
    else prevThumbnail()
  }
}

async function copyLink() {
  try {
    await navigator.clipboard.writeText(window.location.href)
    copied.value = true
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Link copied!', type: 'success', duration: 2000 } }))
    setTimeout(() => { copied.value = false }, 2000)
  } catch {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Could not copy link', type: 'error' } }))
  }
}

onMounted(() => {
  window.addEventListener('keydown', onKeyDown)
  window.addEventListener('touchstart', onTouchStart, { passive: true })
  window.addEventListener('touchend', onTouchEnd, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  window.removeEventListener('touchstart', onTouchStart)
  window.removeEventListener('touchend', onTouchEnd)
  document.body.style.overflow = ''
})
</script>

<style scoped>
.wn-detail {
  max-width: 980px;
  margin: 0 auto;
}

.wn-detail-card {
  margin-top: 1.25rem;
  overflow: hidden;
  border-radius: 28px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(18, 18, 20, 0.84);
}

.wn-detail-hero {
  min-height: 260px;
  background:
    radial-gradient(circle at 20% 20%, rgba(255, 0, 96, 0.14), transparent 38%),
    radial-gradient(circle at 80% 30%, rgba(109, 220, 255, 0.14), transparent 34%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.02));
}

.wn-detail-hero.is-clickable {
  cursor: pointer;
}

.wn-detail-hero.is-clickable img {
  transition: transform 0.2s ease;
}

.wn-detail-hero.is-clickable:hover img {
  transform: scale(1.02);
}

.wn-detail-hero.has-image {
  background: transparent;
}

.wn-detail-hero img {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 9;
  object-fit: cover;
}

.wn-detail-hero.has-image {
  position: relative;
}

.wn-detail-hero.has-image::after {
  content: '';
  position: absolute;
  inset: 0;
  background:
    linear-gradient(180deg, rgba(0, 0, 0, 0.08), rgba(0, 0, 0, 0.42)),
    linear-gradient(135deg, rgba(255, 0, 96, 0.12), transparent 45%);
  pointer-events: none;
}

.wn-detail-placeholder {
  min-height: 260px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  padding: 2rem;
}

.wn-detail-placeholder-kicker {
  display: inline-flex;
  width: fit-content;
  padding: 0.35rem 0.7rem;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.72rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}

.wn-detail-placeholder h2 {
  margin: 0.9rem 0 0;
  max-width: 18ch;
  font-size: clamp(1.8rem, 4vw, 3rem);
  line-height: 1.02;
}

.wn-detail-header {
  padding: 1.9rem 2rem 0;
}

.wn-detail-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 0.65rem;
  align-items: center;
  margin-bottom: 0.9rem;
}

.wn-detail-header h1 {
  margin: 0;
  font-size: clamp(2.2rem, 5vw, 4rem);
  line-height: 1.04;
  letter-spacing: -0.05em;
}

.wn-detail-lead {
  margin: 1rem 0 0;
  max-width: 72ch;
  color: rgba(255, 255, 255, 0.78);
  font-size: 1.02rem;
  line-height: 1.7;
}

.wn-film-credits {
  margin: 1.5rem 2rem 0;
  padding: 1.1rem 1.2rem;
  border-radius: 22px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.wn-film-credits-head {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 1rem;
}

.wn-film-credits-kicker {
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.wn-film-credits-head p,
.wn-film-credits-meta p {
  margin: 0;
  color: rgba(255, 255, 255, 0.84);
  line-height: 1.6;
}

.wn-film-credits-meta + .wn-film-credits-skaters {
  margin-top: 1rem;
}

.wn-film-credits-meta h3,
.wn-film-credits-skaters h3 {
  margin: 0 0 0.45rem;
  font-size: 0.92rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(255, 255, 255, 0.72);
}

.wn-film-credits-skaters ul {
  margin: 0;
  padding-left: 1.1rem;
  columns: 2;
  column-gap: 2rem;
}

.wn-film-credits-skaters li {
  margin: 0 0 0.35rem;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.45;
}

.wn-thumbnail-section {
  padding: 0 2rem 0.4rem;
}

.wn-thumbnail-head {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 0.9rem;
}

.wn-thumbnail-kicker {
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.wn-thumbnail-head p {
  margin: 0;
  color: rgba(255, 255, 255, 0.52);
  font-size: 0.92rem;
}

.wn-thumbnail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 0.75rem;
}

.wn-thumbnail-card {
  position: relative;
  padding: 0;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 18px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.04);
  cursor: zoom-in;
  aspect-ratio: 1 / 1;
}

.wn-thumbnail-card img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
  transition: transform 0.25s ease;
}

.wn-thumbnail-card:hover img {
  transform: scale(1.03);
}

.wn-thumbnail-card::after {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(180deg, transparent 45%, rgba(0, 0, 0, 0.45));
  pointer-events: none;
}

.wn-thumbnail-index {
  position: absolute;
  right: 0.55rem;
  bottom: 0.45rem;
  z-index: 1;
  min-width: 1.5rem;
  height: 1.5rem;
  padding: 0 0.35rem;
  border-radius: 999px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: rgba(10, 10, 12, 0.7);
  color: rgba(255, 255, 255, 0.92);
  font-size: 0.75rem;
  font-weight: 800;
}

.wn-related {
  padding: 0 2rem 0.2rem;
}

.wn-related-head {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
  margin-bottom: 0.9rem;
}

.wn-related-kicker {
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.wn-related-head p {
  margin: 0;
  color: rgba(255, 255, 255, 0.52);
  font-size: 0.92rem;
}

.wn-related-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 0.85rem;
}

.wn-related-card {
  display: grid;
  gap: 0.7rem;
  align-items: stretch;
  text-decoration: none;
  color: inherit;
  border-radius: 22px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.03));
  border: 1px solid rgba(255, 255, 255, 0.08);
  padding: 0.8rem;
  transition: transform 0.2s ease, border-color 0.2s ease, background 0.2s ease;
}

.wn-related-card:hover {
  transform: translateY(-2px);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.045));
  border-color: rgba(255, 255, 255, 0.16);
}

.wn-related-card.fallback {
  background:
    linear-gradient(180deg, rgba(109, 220, 255, 0.08), rgba(255, 255, 255, 0.025));
  border-style: dashed;
}

.wn-related-thumb {
  aspect-ratio: 16 / 10;
  border-radius: 16px;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(255, 0, 96, 0.16), rgba(109, 220, 255, 0.16));
  display: flex;
  align-items: center;
  justify-content: center;
}

.wn-related-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.wn-related-fallback {
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.72);
}

.wn-related-copy {
  display: grid;
  gap: 0.35rem;
  min-width: 0;
}

.wn-related-copy strong {
  font-size: 1rem;
  line-height: 1.15;
}

.wn-related-copy span {
  color: rgba(255, 255, 255, 0.58);
  font-size: 0.88rem;
  line-height: 1.35;
}

.wn-bullet-list {
  margin: 0;
  padding: 1.2rem 2rem 0 3.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
  list-style: disc;
}

.wn-bullet-list li {
  color: rgba(255, 255, 255, 0.88);
  font-size: 0.95rem;
  line-height: 1.5;
  padding-left: 0.25rem;
}

.wn-detail-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
  padding: 1.4rem 2rem 1rem;
}

.wn-detail-actions.has-dual-cta {
  align-items: stretch;
}

.wn-detail-actions.has-dual-cta .wn-cta {
  flex: 1 1 220px;
}

.wn-cta.primary {
  background: linear-gradient(135deg, #ffffff, #dbeafe);
  color: #050505;
}

.wn-cta.secondary {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.88);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.wn-detail-actions .wn-cta {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 0.55rem;
  min-height: 44px;
  padding: 0 1rem;
  border-radius: 14px;
  font-size: 0.92rem;
  font-weight: 800;
  letter-spacing: 0.01em;
  text-decoration: none;
  box-shadow: 0 10px 28px rgba(0, 0, 0, 0.18);
}

.wn-detail-actions .wn-cta.primary {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.08)),
    rgba(16, 18, 24, 0.56);
  color: rgba(255, 255, 255, 0.92);
  border: 1px solid rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(18px) saturate(160%);
  -webkit-backdrop-filter: blur(18px) saturate(160%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    0 14px 30px rgba(0, 0, 0, 0.24);
}

.wn-detail-actions.has-dual-cta .wn-cta.primary {
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.1)),
    rgba(18, 20, 28, 0.52);
  color: rgba(255, 255, 255, 0.94);
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    0 14px 30px rgba(0, 0, 0, 0.24);
}

.wn-detail-actions .wn-cta.secondary {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.9);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.listen-cta {
  background: rgba(109, 220, 255, 0.12) !important;
  border-color: rgba(109, 220, 255, 0.2) !important;
  color: rgba(156, 234, 255, 0.95) !important;
}

.source-cta-icon {
  display: inline-flex;
  font-size: 0.88rem;
}

.wn-share-row {
  display: flex;
  justify-content: flex-start;
  padding: 0.25rem 2rem 0;
}

.wn-share-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0.7rem 0.95rem;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.78);
  font-size: 0.82rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s, color 0.15s, border-color 0.15s, transform 0.15s ease;
}

.wn-share-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.94);
  border-color: rgba(255, 255, 255, 0.22);
  transform: translateY(-1px);
}

.wn-share-btn.copied {
  color: #8df0ab;
  background: rgba(52, 199, 89, 0.12);
  border-color: rgba(52, 199, 89, 0.35);
}

.wn-detail-neighbors {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 10px;
  padding: 1.4rem 2rem 1.1rem;
  max-width: 980px;
  margin: 0 auto;
}

.wn-detail-neighbors .wn-neighbor-pill,
.wn-detail-neighbors .wn-neighbor-spacer {
  min-width: 0;
  min-height: 52px;
}

.wn-detail-neighbors .wn-neighbor-pill {
  display: grid;
  align-items: center;
  gap: 10px;
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.045);
  color: rgba(255, 255, 255, 0.86);
  text-decoration: none;
  min-height: 60px;
  padding: 0.85rem 1rem;
  transition: background 0.18s ease, border-color 0.18s ease, transform 0.18s ease;
}

.wn-detail-neighbors .wn-neighbor-pill:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.15);
}

.wn-detail-neighbors .wn-neighbor-pill.previous {
  grid-template-columns: 16px minmax(0, 1fr);
}

.wn-detail-neighbors .wn-neighbor-pill.next {
  grid-template-columns: minmax(0, 1fr) 16px;
  text-align: right;
}

.wn-detail-neighbors .wn-neighbor-pill i {
  color: rgba(109, 220, 255, 0.82);
  font-size: 0.82rem;
}

.wn-detail-neighbors .wn-neighbor-pill span {
  min-width: 0;
  display: grid;
  gap: 2px;
}

.wn-detail-neighbors .wn-neighbor-pill small {
  color: rgba(255, 255, 255, 0.48);
  font-size: 0.62rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.08em;
}

.wn-detail-neighbors .wn-neighbor-pill strong {
  overflow: hidden;
  color: rgba(255, 255, 255, 0.88);
  font-size: 0.82rem;
  font-weight: 700;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wn-lightbox {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: grid;
  place-items: center;
  padding: 1rem;
  background: rgba(4, 5, 8, 0.9);
  backdrop-filter: blur(22px) saturate(150%);
  -webkit-backdrop-filter: blur(22px) saturate(150%);
}

.wn-lightbox-frame {
  width: min(96vw, 1080px);
  max-height: 84vh;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
}

.wn-lightbox-image {
  max-width: 100%;
  max-height: 84vh;
  object-fit: contain;
  border-radius: 18px;
  box-shadow: 0 24px 80px rgba(0, 0, 0, 0.45);
}

.wn-lightbox-close,
.wn-lightbox-arrow {
  position: absolute;
  z-index: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.92);
  cursor: pointer;
}

.wn-lightbox-close {
  top: 1rem;
  right: 1rem;
}

.wn-lightbox-arrow {
  top: 50%;
  transform: translateY(-50%);
}

.wn-lightbox-prev {
  left: 1rem;
}

.wn-lightbox-next {
  right: 1rem;
}

.wn-lightbox-counter {
  position: absolute;
  bottom: 1rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.6rem 0.9rem;
  border-radius: 999px;
  background: rgba(10, 10, 12, 0.72);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.88rem;
  font-weight: 700;
  letter-spacing: 0.01em;
}

.wn-lightbox-hint {
  color: rgba(255, 255, 255, 0.6);
  font-weight: 600;
}

.wn-lb-fade-enter-active,
.wn-lb-fade-leave-active {
  transition: opacity 0.18s ease;
}

.wn-lb-fade-enter-from,
.wn-lb-fade-leave-to {
  opacity: 0;
}

.wn-lb-image-enter-active,
.wn-lb-image-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.wn-lb-image-enter-from,
.wn-lb-image-leave-to {
  opacity: 0;
  transform: scale(0.985);
}

@media (max-width: 768px) {
  .wn-detail {
    max-width: none;
    padding-bottom: 18px;
  }

  .wn-detail > .back-link {
    min-height: 34px;
    padding: 0 12px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.045);
    border: 1px solid rgba(255, 255, 255, 0.07);
    color: rgba(255, 255, 255, 0.74);
    font-size: 0.78rem;
    font-weight: 800;
  }

  .wn-detail-card {
    margin-top: 0.75rem;
    border-radius: 20px;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.016));
    box-shadow:
      inset 0 1px 0 rgba(255, 255, 255, 0.07),
      0 10px 22px rgba(0, 0, 0, 0.14);
  }

  .wn-thumbnail-section,
  .wn-detail-header,
  .wn-related,
  .wn-bullet-list,
  .wn-detail-actions,
  .wn-detail-placeholder {
    padding-left: 1rem;
    padding-right: 1rem;
  }

  .wn-detail-hero {
    min-height: 0;
    background:
      radial-gradient(circle at 16% 0%, rgba(109, 220, 255, 0.1), transparent 34%),
      radial-gradient(circle at 92% 18%, rgba(255, 0, 96, 0.08), transparent 36%),
      linear-gradient(180deg, rgba(255, 255, 255, 0.052), rgba(255, 255, 255, 0.014));
  }

  .wn-detail-hero.has-image {
    padding: 12px 12px 0;
  }

  .wn-detail-hero img {
    aspect-ratio: 16 / 10;
    border-radius: 14px;
  }

  .wn-detail-placeholder {
    min-height: 0;
    padding-top: 1.05rem;
    padding-bottom: 0.95rem;
  }

  .wn-detail-placeholder-kicker {
    padding: 0;
    background: transparent;
    color: rgba(255, 255, 255, 0.52);
    font-size: 0.68rem;
    letter-spacing: 0.18em;
  }

  .wn-detail-placeholder h2 {
    display: none;
  }

  .wn-detail-header {
    padding-top: 1rem;
  }

  .wn-detail-meta {
    gap: 0.45rem;
    margin-bottom: 0.65rem;
  }

  .wn-detail-meta .wn-pill {
    padding: 2px 8px;
    font-size: 0.62rem;
  }

  .wn-detail-meta .wn-date {
    font-size: 0.78rem;
    color: rgba(255, 255, 255, 0.58);
  }

  .wn-detail-header h1 {
    font-size: 1.95rem;
    line-height: 1.04;
    letter-spacing: 0;
  }

  .wn-detail-lead {
    margin-top: 0.75rem;
    font-size: 0.94rem;
    line-height: 1.5;
    color: rgba(255, 255, 255, 0.74);
  }

  .wn-film-credits {
    margin: 1.25rem 1rem 0;
    padding: 1rem;
  }

  .wn-film-credits-skaters ul {
    columns: 1;
  }

  .wn-related {
    padding-top: 0;
  }

  .wn-related-grid {
    grid-template-columns: 1fr;
  }

  .wn-thumbnail-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .wn-related-card {
    gap: 0.55rem;
    padding: 0.7rem;
    border-radius: 18px;
  }

  .wn-bullet-list {
    padding: 1rem 1rem 0 2.25rem;
    gap: 0.4rem;
  }

  .wn-bullet-list li {
    font-size: 0.88rem;
  }

  .wn-detail-actions {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
    padding: 1rem 1rem 0.9rem;
  }

  .wn-detail-actions.has-dual-cta {
    grid-template-columns: minmax(0, 1fr);
  }

  .wn-detail-actions .wn-cta {
    min-height: 42px;
    justify-content: center;
    width: 100%;
    padding: 0 14px;
    border-radius: 16px;
    font-size: 0.88rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .wn-detail-actions .wn-cta i {
    display: inline-flex;
    flex-shrink: 0;
  }

  .source-cta-desktop {
    display: none;
  }

  .wn-detail-actions .wn-cta.secondary {
    background: rgba(255, 255, 255, 0.075);
    color: rgba(255, 255, 255, 0.88);
    border: 1px solid rgba(255, 255, 255, 0.1);
  }

  .wn-detail-actions .wn-cta.primary {
    background:
      linear-gradient(135deg, rgba(255, 255, 255, 0.14), rgba(255, 255, 255, 0.08)),
      rgba(16, 18, 24, 0.56);
    color: rgba(255, 255, 255, 0.92);
  }

  .wn-detail-actions.has-dual-cta .wn-cta.primary {
    background:
      linear-gradient(135deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.1)),
      rgba(18, 20, 28, 0.52);
    color: rgba(255, 255, 255, 0.94);
  }

  .wn-detail-actions .wn-cta:hover {
    transform: none;
    box-shadow: none;
  }

  .wn-share-row {
    padding: 0.1rem 1rem 0;
  }

  .wn-share-btn {
    width: 100%;
    justify-content: center;
  }

  .wn-detail-neighbors {
    grid-template-columns: minmax(0, 1fr);
    gap: 8px;
    padding: 0.75rem 1rem 1.2rem;
  }

  .wn-neighbor-pill,
  .wn-neighbor-spacer {
    min-width: 0;
    min-height: 46px;
  }

  .wn-neighbor-pill {
    display: grid;
    align-items: center;
    gap: 8px;
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.045);
    color: rgba(255, 255, 255, 0.86);
    text-decoration: none;
    padding: 10px 12px;
  }

  .wn-neighbor-pill.previous {
    grid-template-columns: 16px minmax(0, 1fr);
  }

  .wn-neighbor-pill.next {
    grid-template-columns: minmax(0, 1fr) 16px;
    text-align: left;
  }

  .wn-neighbor-pill i {
    color: rgba(109, 220, 255, 0.82);
    font-size: 0.78rem;
  }

  .wn-neighbor-pill span {
    min-width: 0;
    display: grid;
    gap: 2px;
  }

  .wn-neighbor-pill small {
    color: rgba(255, 255, 255, 0.48);
    font-size: 0.62rem;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }

  .wn-neighbor-pill strong {
    overflow: hidden;
    color: rgba(255, 255, 255, 0.9);
    font-size: 0.8rem;
    font-weight: 850;
    line-height: 1.15;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .wn-lightbox {
    padding: 0.75rem;
  }

  .wn-lightbox-close {
    top: 0.75rem;
    right: 0.75rem;
  }

  .wn-lightbox-prev {
    left: 0.75rem;
  }

  .wn-lightbox-next {
    right: 0.75rem;
  }
}
</style>
