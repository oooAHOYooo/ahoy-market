<template>
  <div ref="pageEl" class="poem-detail-page" :class="{ 'is-fullscreen': isFullscreen }">
    <div v-if="loading" class="poem-state-center">
      <i class="fas fa-spinner fa-spin"></i>
    </div>

    <div v-else-if="!poem" class="poem-state-center">
      <i class="fas fa-feather-alt"></i>
      <p>Poem not found.</p>
      <router-link to="/poems" class="poem-back-plain">← Back to Poems</router-link>
    </div>

    <template v-else>
      <div class="poem-top-bar">
        <router-link to="/poems" class="poem-back-link">
          <i class="fas fa-arrow-left"></i>
          Poems
        </router-link>
        <div class="poem-font-controls">
          <button
            type="button"
            class="font-btn poem-fullscreen-btn"
            @click="toggleFullscreen"
            :aria-label="isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'"
          >
            <i class="fas" :class="isFullscreen ? 'fa-compress' : 'fa-expand'"></i>
            <span>{{ isFullscreen ? 'Exit' : 'Full screen' }}</span>
          </button>
          <button
            type="button"
            class="font-btn"
            :disabled="fontIdx === 0"
            @click="changeFont(-1)"
            aria-label="Decrease font size"
          >A−</button>
          <button
            type="button"
            class="font-btn"
            :disabled="fontIdx === fontSizes.length - 1"
            @click="changeFont(1)"
            aria-label="Increase font size"
          >A+</button>
        </div>
      </div>

      <article class="poem-paper">
        <header class="poem-header">
          <div class="poem-header-poet">
            <router-link
              v-if="poem.poet_slug"
              :to="`/artists/${poem.poet_slug}`"
              class="poem-poet-link"
            >{{ poem.poet_name }}</router-link>
            <span v-else>{{ poem.poet_name }}</span>
          </div>
          <h1 class="poem-title">{{ poem.title }}</h1>
          <div v-if="poem.published_at" class="poem-date">{{ formatDate(poem.published_at) }}</div>
          <div class="poem-ornament">◆</div>
        </header>

        <div class="poem-body">
          <pre
            class="poem-text"
            :style="{ fontSize: fontSizes[fontIdx] + 'px', lineHeight: lineHeights[fontIdx] }"
          >{{ poem.body_text }}</pre>
        </div>

        <div v-if="poem.note" class="poem-note">
          <div class="poem-note-label">Poet's note</div>
          <p class="poem-note-text">{{ poem.note }}</p>
        </div>

        <div v-if="poem.handwriting_image_url" class="poem-scan-section">
          <button type="button" class="poem-scan-toggle" @click="showScan = !showScan">
            <i class="fas" :class="showScan ? 'fa-eye-slash' : 'fa-eye'"></i>
            {{ showScan ? 'Hide' : 'View' }} handwritten original
          </button>
          <transition name="scan-fade">
            <div v-if="showScan" class="poem-scan-wrapper">
              <img
                :src="poem.handwriting_image_url"
                :alt="`Handwritten original — ${poem.title}`"
                class="poem-scan-img"
              />
            </div>
          </transition>
        </div>

        <nav v-if="poem.prev || poem.next" class="poem-prev-next">
          <router-link
            v-if="poem.prev"
            :to="`/poems/${poem.prev.poem_id}`"
            class="poem-nav-link poem-nav-prev"
          >
            <span class="poem-nav-dir">← Previous</span>
            <span class="poem-nav-title">{{ poem.prev.title }}</span>
          </router-link>
          <span v-else class="poem-nav-spacer" />
          <router-link
            v-if="poem.next"
            :to="`/poems/${poem.next.poem_id}`"
            class="poem-nav-link poem-nav-next"
          >
            <span class="poem-nav-dir">Next →</span>
            <span class="poem-nav-title">{{ poem.next.title }}</span>
          </router-link>
          <span v-else class="poem-nav-spacer" />
        </nav>
      </article>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import { setSeoMeta } from '../composables/useSeoMeta'

const route = useRoute()
const poem = ref(null)
const loading = ref(true)
const showScan = ref(false)
const pageEl = ref(null)
const isFullscreen = ref(false)

const fontSizes = [15, 18, 22]
const lineHeights = ['1.8', '1.85', '1.95']
const FONT_KEY = 'poem_font_size'
const fontIdx = ref(1)

function syncFullscreenState() {
  isFullscreen.value = document.fullscreenElement === pageEl.value
}

async function toggleFullscreen() {
  const el = pageEl.value
  if (!el) return

  try {
    if (document.fullscreenElement === el) {
      await document.exitFullscreen?.()
      return
    }

    await el.requestFullscreen?.()
  } catch (err) {
    console.error('Failed to toggle poem fullscreen', err)
  }
}

onMounted(() => {
  const saved = parseInt(localStorage.getItem(FONT_KEY))
  if (!isNaN(saved) && saved >= 0 && saved < fontSizes.length) fontIdx.value = saved
  syncFullscreenState()
  document.addEventListener('fullscreenchange', syncFullscreenState)
  loadPoem(route.params.poem_id)
})

onBeforeUnmount(() => {
  document.removeEventListener('fullscreenchange', syncFullscreenState)
})

watch(() => route.params.poem_id, (id) => {
  if (id) {
    showScan.value = false
    window.scrollTo({ top: 0, behavior: 'instant' })
    loadPoem(id)
  }
})

async function loadPoem(id) {
  loading.value = true
  poem.value = null
  try {
    const res = await fetch(`/api/poems/${id}`)
    if (res.ok) {
      poem.value = await res.json()
      updateSeoMeta()
    }
  } catch (e) {
    console.error('Failed to load poem', e)
  } finally {
    loading.value = false
  }
}

async function updateSeoMeta() {
  if (!poem.value) return

  try {
    const artistRes = await fetch(`/api/artists/${poem.value.poet_slug}`)
    const artistData = artistRes.ok ? await artistRes.json() : null
    const artistImage = artistData?.image || '/static/img/ahoy_logo.png'

    setSeoMeta({
      title: poem.value.title,
      description: `A poem by ${poem.value.poet_name}`,
      image: artistImage,
      url: `/poems/${poem.value.poem_id}`,
    })
  } catch (e) {
    console.error('Failed to update SEO meta', e)
    setSeoMeta({
      title: poem.value.title,
      description: `A poem by ${poem.value.poet_name}`,
      url: `/poems/${poem.value.poem_id}`,
    })
  }
}

function changeFont(delta) {
  const next = fontIdx.value + delta
  if (next >= 0 && next < fontSizes.length) {
    fontIdx.value = next
    localStorage.setItem(FONT_KEY, next)
  }
}

function formatDate(iso) {
  if (!iso) return ''
  return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })
}
</script>

<style scoped>
.poem-detail-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.08), transparent 34%),
    linear-gradient(180deg, #111215 0%, #0a0b0d 100%);
  color: #f5f2ea;
}

.poem-state-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  padding: 80px 0;
  color: rgba(245, 242, 234, 0.56);
  font-size: 15px;
}

.poem-state-center i {
  font-size: 28px;
  opacity: 0.4;
}

.poem-back-plain {
  font-size: 13px;
  color: rgba(245, 242, 234, 0.7);
  text-decoration: none;
}

.poem-back-plain:hover {
  color: #fff;
}

/* ── Sticky top bar ── */
.poem-top-bar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 18px;
  background: rgba(8, 9, 12, 0.82);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.poem-back-link {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  font-weight: 500;
  color: rgba(245, 242, 234, 0.7);
  text-decoration: none;
  letter-spacing: 0.02em;
  transition: color 0.15s;
}

.poem-back-link:hover {
  color: #fff;
}

.poem-font-controls {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.font-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: rgba(245, 242, 234, 0.82);
  font-family: Georgia, serif;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.02em;
  padding: 5px 10px;
  border-radius: 999px;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s, background 0.15s, transform 0.15s;
  line-height: 1.4;
}

.font-btn:hover:not(:disabled) {
  border-color: rgba(255, 255, 255, 0.28);
  color: #fff;
  background: rgba(255, 255, 255, 0.08);
  transform: translateY(-1px);
}

.font-btn:disabled {
  opacity: 0.28;
  cursor: default;
}

.poem-fullscreen-btn {
  min-width: 112px;
  justify-content: center;
}

/* ── Paper article ── */
.poem-paper {
  max-width: 560px;
  margin: 0 auto;
  padding: 36px 24px 72px;
}

@media (max-width: 640px) {
  .poem-paper {
    padding: 24px 16px 56px;
  }
  .poem-top-bar {
    padding: 10px 14px;
  }
  .poem-fullscreen-btn span {
    display: none;
  }
}

/* ── Header ── */
.poem-header {
  text-align: center;
  margin-bottom: 28px;
}

.poem-header-poet {
  font-size: 11px;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(245, 242, 234, 0.56);
  margin-bottom: 12px;
}

.poem-poet-link {
  color: rgba(245, 242, 234, 0.78);
  text-decoration: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  padding-bottom: 1px;
  transition: color 0.15s, border-color 0.15s;
}

.poem-poet-link:hover {
  color: #fff;
  border-color: rgba(255, 255, 255, 0.5);
}

.poem-title {
  font-family: Georgia, 'Times New Roman', serif;
  font-size: clamp(24px, 4.4vw, 34px);
  font-weight: 400;
  line-height: 1.15;
  margin: 0 0 10px;
  color: #faf7ef;
  letter-spacing: -0.01em;
}

.poem-date {
  font-size: 11px;
  color: rgba(245, 242, 234, 0.42);
  letter-spacing: 0.06em;
  margin-bottom: 14px;
}

.poem-ornament {
  font-size: 9px;
  color: rgba(245, 242, 234, 0.24);
  letter-spacing: 0.3em;
}

/* ── Body ── */
.poem-body {
  margin-bottom: 32px;
}

.poem-text {
  font-family: Georgia, 'Times New Roman', serif;
  color: #f3efe5;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  text-align: left;
  transition: font-size 0.2s;
}

/* ── Poet's note ── */
.poem-note {
  border-left: 2px solid rgba(255, 255, 255, 0.12);
  padding-left: 18px;
  margin-bottom: 28px;
}

.poem-note-label {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(245, 242, 234, 0.44);
  margin-bottom: 7px;
}

.poem-note-text {
  font-size: 14px;
  line-height: 1.65;
  color: rgba(245, 242, 234, 0.72);
  font-style: italic;
  margin: 0;
}

/* ── Handwritten scan ── */
.poem-scan-section {
  margin-bottom: 28px;
}

.poem-scan-toggle {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.14);
  color: rgba(245, 242, 234, 0.74);
  font-size: 13px;
  font-weight: 500;
  padding: 7px 14px;
  border-radius: 999px;
  cursor: pointer;
  transition: border-color 0.15s, color 0.15s;
}

.poem-scan-toggle:hover {
  border-color: rgba(255, 255, 255, 0.28);
  color: #fff;
}

.poem-scan-wrapper {
  margin-top: 14px;
}

.poem-scan-img {
  width: 100%;
  max-width: 480px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  display: block;
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.3);
}

/* ── Prev / Next ── */
.poem-prev-next {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  margin-top: 32px;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.poem-nav-link {
  display: flex;
  flex-direction: column;
  gap: 6px;
  text-decoration: none;
  max-width: 44%;
  transition: opacity 0.15s;
}

.poem-nav-link:hover {
  opacity: 0.7;
}

.poem-nav-prev {
  align-items: flex-start;
}

.poem-nav-next {
  align-items: flex-end;
  text-align: right;
}

.poem-nav-spacer {
  flex: 1;
}

.poem-nav-dir {
  font-size: 10px;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: rgba(245, 242, 234, 0.5);
  font-weight: 700;
}

.poem-nav-title {
  font-family: Georgia, serif;
  font-size: 14px;
  color: rgba(245, 242, 234, 0.82);
  font-style: italic;
}

.poem-detail-page.is-fullscreen {
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.1), transparent 30%),
    linear-gradient(180deg, #0d0e11 0%, #050607 100%);
}

.poem-detail-page.is-fullscreen .poem-top-bar {
  padding-top: 14px;
  padding-bottom: 14px;
}

.poem-detail-page.is-fullscreen .poem-paper {
  max-width: 520px;
  padding-top: 28px;
}

/* ── Transitions ── */
.scan-fade-enter-active,
.scan-fade-leave-active {
  transition: opacity 0.3s, transform 0.3s;
}

.scan-fade-enter-from,
.scan-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
