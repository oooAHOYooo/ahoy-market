<template>
  <div class="digital-marketplace">
    <ContentHeader
      kicker="Experimental storefront"
      title="Digital Marketplace"
      subtitle="Downloadable music from artists who choose to make their work available here."
    />

    <section class="marketplace-intro">
      <div>
        <span class="marketplace-eyebrow">Bandcamp-style test</span>
        <h1>Own the music. Keep the file.</h1>
        <p>Stream a preview, support the artist, and eventually send purchased releases to Ahoy MP3.</p>
      </div>
      <div class="marketplace-status">
        <span></span> Approved test catalog · 3 artists
        <button v-if="savedProducts.length" type="button" class="saved-releases-toggle" @click="showSavedOnly = !showSavedOnly">
          {{ showSavedOnly ? 'Show all releases' : `Saved ${savedProducts.length}` }}
        </button>
      </div>
    </section>

    <section v-for="group in visibleArtistGroups" :key="group.key" class="artist-shelf">
      <div class="shelf-heading">
        <div>
          <span class="marketplace-eyebrow">Featured artist</span>
          <h2>{{ group.name }}</h2>
        </div>
        <span class="shelf-note">Only approved digital releases appear here.</span>
      </div>

      <div v-if="group.tracks.length" class="digital-grid">
        <article v-for="product in group.tracks" :key="product.id" class="digital-card">
          <div class="digital-art">
            <img :src="product.cover_art || '/static/img/default-cover.jpg'" :alt="product.title" loading="lazy" />
            <button type="button" class="preview-button" @click="preview(product)">
              <i :class="previewing === product.id ? 'fas fa-pause' : 'fas fa-play'"></i>
              {{ previewing === product.id ? 'Pause preview' : 'Preview' }}
            </button>
          </div>
          <div class="digital-card-body">
            <div class="digital-card-top">
              <div>
                <span class="digital-type">Digital single</span>
                <h3>{{ product.title }}</h3>
                <p>{{ group.name }}</p>
              </div>
              <strong>$1.00</strong>
            </div>
            <div class="digital-card-footer">
              <span>MP3 · artist-approved</span>
              <button type="button" class="digital-buy" :class="{ saved: isSaved(product) }" @click="toggleSaved(product)">
                <i :class="isSaved(product) ? 'fas fa-bookmark' : 'far fa-bookmark'"></i>
                {{ isSaved(product) ? 'Saved' : 'Save for later' }}
              </button>
            </div>
          </div>
        </article>
      </div>
      <div v-else class="marketplace-empty">{{ showSavedOnly ? 'No saved releases from this artist yet.' : 'Samuel Dylan Witch releases are being prepared for the first digital test.' }}</div>
    </section>

    <section v-if="!visibleArtistGroups.length" class="artist-shelf">
      <div class="marketplace-empty">{{ showSavedOnly ? 'You have no saved releases yet.' : 'Approved releases are being prepared for the first digital test.' }}</div>
    </section>

    <section class="marketplace-next">
      <i class="fas fa-download"></i>
      <div>
        <h2>Purchased Music will live here</h2>
        <p>The payment and ownership layer is intentionally separate from physical merch. Once enabled, downloads will connect to Ahoy MP3 and the Transfer desk.</p>
      </div>
      <router-link to="/mp3-player">Open Ahoy MP3</router-link>
    </section>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import ContentHeader from '../components/ContentHeader.vue'
import { apiFetchCached } from '../composables/useApi'

const tracks = ref([])
const previewing = ref(null)
const savedIds = ref([])
const showSavedOnly = ref(false)
let audio = null
const savedStorageKey = 'ahoy:digital-marketplace-saved'

const approvedArtists = [
  { key: 'samuel-dylan-witch', name: 'Samuel Dylan Witch', match: 'samuel dylan witch' },
  { key: 'jake-custer', name: 'Jake Custer', match: 'jake custer' },
  { key: 'the-tines', name: 'The Tines', match: 'the tines' },
]

const artistGroups = computed(() => approvedArtists.map((artist) => ({
  ...artist,
  tracks: tracks.value.filter((track) => {
    const name = String(track.artist || track.artist_name || '').toLowerCase()
    return name.includes(artist.match)
  }),
})).filter((artist) => artist.tracks.length))

const visibleArtistGroups = computed(() => artistGroups.value.map((artist) => ({
  ...artist,
  tracks: showSavedOnly.value ? artist.tracks.filter((track) => isSaved(track)) : artist.tracks,
})).filter((artist) => artist.tracks.length || !showSavedOnly.value))

const savedProducts = computed(() => artistGroups.value.flatMap((artist) => artist.tracks).filter((track) => isSaved(track)))

function productKey(product) {
  return String(product.id || product.audio_url || product.title || '')
}

function isSaved(product) {
  return savedIds.value.includes(productKey(product))
}

function toggleSaved(product) {
  const key = productKey(product)
  if (!key) return
  savedIds.value = isSaved(product)
    ? savedIds.value.filter((id) => id !== key)
    : [...savedIds.value, key]
  window.dispatchEvent(new CustomEvent('ahoy:toast', {
    detail: {
      message: isSaved(product) ? `Saved “${product.title}” for later.` : `Removed “${product.title}” from saved releases.`,
      type: 'info',
    },
  }))
}

function preview(product) {
  if (!product.audio_url) return
  if (!audio) audio = new Audio()
  if (previewing.value === product.id) {
    audio.pause()
    previewing.value = null
    return
  }
  audio.src = product.audio_url
  audio.currentTime = 0
  audio.play().catch(() => {})
  previewing.value = product.id
  audio.onended = () => { previewing.value = null }
}

onMounted(async () => {
  try {
    const saved = JSON.parse(window.localStorage.getItem(savedStorageKey) || '[]')
    if (Array.isArray(saved)) savedIds.value = saved.filter((id) => typeof id === 'string')
  } catch {
    savedIds.value = []
  }
  const data = await apiFetchCached('/api/music').catch(() => ({ tracks: [] }))
  tracks.value = data.tracks || []
})

watch(savedIds, (ids) => {
  try {
    window.localStorage.setItem(savedStorageKey, JSON.stringify(ids))
  } catch {
    // Saving is best effort; marketplace browsing still works if storage is unavailable.
  }
}, { deep: true })

onBeforeUnmount(() => {
  if (audio) audio.pause()
})
</script>

<style scoped>
.digital-marketplace { max-width: 1180px; margin: 0 auto; padding-bottom: 5rem; }
.marketplace-intro, .marketplace-next, .artist-shelf { margin: 1.5rem 0; border: 1px solid rgba(255,255,255,.1); border-radius: 18px; background: rgba(12,16,25,.72); padding: 1.5rem; }
.marketplace-intro { display:flex; justify-content:space-between; gap:1rem; align-items:end; }
.marketplace-eyebrow, .digital-type { color:#70d7ff; font-size:.7rem; letter-spacing:.14em; text-transform:uppercase; }
.marketplace-intro h1 { margin:.35rem 0; font-size:clamp(1.8rem,4vw,3rem); }
.marketplace-intro p, .digital-card-body p, .marketplace-next p { color:rgba(255,255,255,.62); margin:.35rem 0 0; }
.marketplace-status { white-space:nowrap; color:rgba(255,255,255,.65); font-size:.78rem; }
.marketplace-status span { display:inline-block; width:8px; height:8px; border-radius:50%; background:#6be7b0; margin-right:7px; }
.saved-releases-toggle { display:block; margin:.65rem 0 0 auto; border:0; color:#b9edff; background:transparent; cursor:pointer; font-size:.76rem; text-decoration:underline; }
.shelf-heading { display:flex; justify-content:space-between; gap:1rem; align-items:end; margin-bottom:1rem; }
.shelf-heading h2 { margin:.3rem 0 0; }
.shelf-note { color:rgba(255,255,255,.48); font-size:.8rem; }
.digital-grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(245px,1fr)); gap:1rem; }
.digital-card { overflow:hidden; border:1px solid rgba(255,255,255,.1); border-radius:15px; background:rgba(255,255,255,.04); }
.digital-art { aspect-ratio:1; position:relative; background:#121724; }
.digital-art img { width:100%; height:100%; object-fit:cover; display:block; }
.preview-button { position:absolute; left:12px; bottom:12px; border:0; border-radius:999px; padding:.6rem .85rem; color:#081018; background:#a9e8ff; cursor:pointer; }
.digital-card-body { padding:1rem; }
.digital-card-top { display:flex; justify-content:space-between; gap:1rem; }
.digital-card h3 { margin:.35rem 0 0; font-size:1.05rem; }
.digital-card-top strong { white-space:nowrap; }
.digital-card-footer { display:flex; justify-content:space-between; align-items:center; gap:.5rem; margin-top:1rem; color:rgba(255,255,255,.48); font-size:.76rem; }
.digital-buy, .marketplace-next a { border:1px solid rgba(112,215,255,.35); border-radius:999px; padding:.55rem .75rem; color:#b9edff; background:transparent; cursor:pointer; text-decoration:none; }
.digital-buy.saved { border-color:rgba(107,231,176,.45); color:#9af0c5; }
.marketplace-next { display:flex; align-items:center; gap:1rem; }
.marketplace-next > i { color:#70d7ff; font-size:1.4rem; }
.marketplace-next h2 { margin:0; font-size:1rem; }
.marketplace-next a { margin-left:auto; white-space:nowrap; }
.marketplace-empty { color:rgba(255,255,255,.6); padding:2rem 0; }
@media (max-width:700px) { .marketplace-intro, .shelf-heading, .marketplace-next { display:block; } .marketplace-status, .shelf-note { display:block; margin-top:1rem; white-space:normal; } .marketplace-next a { display:inline-block; margin-top:1rem; } }
</style>
