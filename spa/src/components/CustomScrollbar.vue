<template>
  <Teleport to="body">
    <div
      v-if="!isMobile && isVisible"
      class="custom-scrollbar"
      :class="{ 'is-hovered': hovered, 'is-scrolling': scrolling }"
      :style="trackStyle"
      @mouseenter="hovered = true"
      @mouseleave="hovered = false"
      aria-hidden="true"
    >
      <!-- Section markers / dots -->
      <div
        v-for="marker in sectionMarkers"
        :key="marker.id"
        class="scrollbar-section-dot"
        :style="{ top: marker.trackPercent + '%' }"
        :class="{ 'is-active': marker.isActive }"
      >
        <span class="scrollbar-section-label">{{ marker.label }}</span>
      </div>

      <!-- Scroll thumb -->
      <div
        class="scrollbar-thumb"
        :style="thumbStyle"
        @mousedown.prevent="startDrag"
      ></div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const scrollEl = ref(null)
const scrollTop = ref(0)
const scrollHeight = ref(1)
const clientHeight = ref(1)
const hovered = ref(false)
const scrolling = ref(false)
const sectionMarkers = ref([])
const trackHeight = ref(0)
const trackTop = ref(0)
const isMobile = ref(window.innerWidth <= 1024)
const isVisible = computed(() => !isMobile.value)

// --- Thumb geometry calculations ---
const thumbHeightPercent = computed(() => {
  return Math.max(8, (clientHeight.value / scrollHeight.value) * 100)
})

const thumbTopPercent = computed(() => {
  const scrollable = scrollHeight.value - clientHeight.value
  if (scrollable <= 0) return 0
  const maxTop = 100 - thumbHeightPercent.value
  return (scrollTop.value / scrollable) * maxTop
})

const thumbStyle = computed(() => ({
  height: thumbHeightPercent.value + '%',
  top: thumbTopPercent.value + '%',
}))

const trackStyle = computed(() => ({
  '--track-top': trackTop.value + 'px',
  '--track-height': trackHeight.value + 'px',
}))

// --- Section scanning ---
function scanSections() {
  if (!scrollEl.value) return

  // Query for explicit markers first, then fallback to h2/h3
  const candidates = scrollEl.value.querySelectorAll(
    '[data-scrollbar-section]'
  )
  const headings =
    candidates.length > 0
      ? Array.from(candidates)
      : Array.from(scrollEl.value.querySelectorAll('h2, h3, section > header'))

  const total = scrollEl.value.scrollHeight

  sectionMarkers.value = headings
    .filter((el) => el.offsetHeight > 0) // only visible
    .map((el, i) => ({
      id: i,
      label:
        el.dataset.scrollbarSection ||
        el.textContent?.trim().slice(0, 20) ||
        '',
      trackPercent: (el.offsetTop / total) * 100,
      isActive: false,
    }))
    .filter((m) => m.label) // drop empty labels
}

// --- Active marker tracking ---
function updateActiveMarker() {
  if (!sectionMarkers.value.length) return

  const viewportMidpoint = scrollTop.value + clientHeight.value * 0.3
  const total = scrollHeight.value

  sectionMarkers.value = sectionMarkers.value.map((m, i) => {
    const nextPercent = sectionMarkers.value[i + 1]?.trackPercent ?? 100
    const posInScroll = (m.trackPercent / 100) * total
    const nextPosInScroll = (nextPercent / 100) * total

    return {
      ...m,
      isActive:
        viewportMidpoint >= posInScroll &&
        viewportMidpoint < nextPosInScroll,
    }
  })
}

// --- Scroll event handler ---
let scrollTimer = null
let scanTimer1 = null
let scanTimer2 = null

function onScroll() {
  if (!scrollEl.value) return

  scrollTop.value = scrollEl.value.scrollTop
  scrollHeight.value = scrollEl.value.scrollHeight
  clientHeight.value = scrollEl.value.clientHeight
  scrolling.value = true
  updateActiveMarker()

  clearTimeout(scrollTimer)
  scrollTimer = setTimeout(() => {
    scrolling.value = false
  }, 1200)
}

// --- Drag to scroll ---
let dragStartY = 0
let dragStartScrollTop = 0

function startDrag(e) {
  dragStartY = e.clientY
  dragStartScrollTop = scrollEl.value.scrollTop
  scrolling.value = true
  document.addEventListener('mousemove', onDrag)
  document.addEventListener('mouseup', stopDrag)
}

function onDrag(e) {
  if (!scrollEl.value) return
  const dy = e.clientY - dragStartY
  const scrollable = scrollEl.value.scrollHeight - scrollEl.value.clientHeight
  const trackH = trackHeight.value

  if (trackH > 0) {
    const ratio = dy / trackH
    scrollEl.value.scrollTop =
      dragStartScrollTop + ratio * scrollEl.value.scrollHeight
  }
}

function stopDrag() {
  scrolling.value = false
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
}

// --- Track geometry ---
function recalcTrackGeometry() {
  if (!scrollEl.value) return
  const rect = scrollEl.value.getBoundingClientRect()
  trackTop.value = rect.top
  trackHeight.value = rect.height
}

// --- Resize & mobile guard ---
function onResize() {
  isMobile.value = window.innerWidth <= 1024
  recalcTrackGeometry()
}

// --- Lifecycle ---
onMounted(() => {
  scrollEl.value = document.querySelector('.content-area.app-content')
  if (!scrollEl.value) return

  onScroll()
  scrollEl.value.addEventListener('scroll', onScroll, { passive: true })
  window.addEventListener('resize', onResize)
  recalcTrackGeometry()

  // Scan sections after DOM has fully painted
  scanTimer1 = setTimeout(scanSections, 300)
})

onUnmounted(() => {
  if (scrollEl.value) {
    scrollEl.value.removeEventListener('scroll', onScroll)
  }
  window.removeEventListener('resize', onResize)
  document.removeEventListener('mousemove', onDrag)
  document.removeEventListener('mouseup', stopDrag)
  clearTimeout(scrollTimer)
  clearTimeout(scanTimer1)
  clearTimeout(scanTimer2)
})

// Re-scan when route changes (new page = new headings)
watch(
  () => route.path,
  () => {
    sectionMarkers.value = [] // clear old markers immediately
    nextTick(() => {
      scanTimer2 = setTimeout(scanSections, 400) // wait for keep-alive render
      onScroll() // reset scroll position tracking
    })
  }
)
</script>

<style scoped>
/* === Custom Scrollbar Track === */
.custom-scrollbar {
  position: fixed;
  right: 4px;
  top: var(--track-top);
  height: var(--track-height);
  width: 6px;
  z-index: 50;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.4s ease, width 0.25s cubic-bezier(0.16, 1, 0.3, 1);
}

/* Show when scrolling or hovered */
.custom-scrollbar.is-scrolling,
.custom-scrollbar.is-hovered {
  opacity: 1;
  pointer-events: auto;
}

/* Hover: grow the track width */
.custom-scrollbar.is-hovered {
  width: 10px;
}

/* Track visual (thin line behind thumb) */
.custom-scrollbar::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(255, 255, 255, 0.06);
  border-radius: 99px;
  transition: background 0.25s ease;
}

.custom-scrollbar.is-hovered::before {
  background: rgba(255, 255, 255, 0.1);
}

/* === Scroll Thumb === */
.scrollbar-thumb {
  position: absolute;
  left: 0;
  right: 0;
  border-radius: 99px;
  background: rgba(109, 220, 255, 0.45);
  cursor: grab;
  pointer-events: auto;
  transition:
    top 0.08s linear,
    height 0.08s linear,
    background 0.25s ease,
    box-shadow 0.25s ease;
  min-height: 32px;
}

.custom-scrollbar.is-hovered .scrollbar-thumb {
  background: rgba(109, 220, 255, 0.7);
  box-shadow: 0 0 8px rgba(109, 220, 255, 0.35);
}

.scrollbar-thumb:active {
  cursor: grabbing;
  background: rgba(109, 220, 255, 0.9);
}

/* === Section Dots === */
.scrollbar-section-dot {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  transition: background 0.2s ease, width 0.2s ease, height 0.2s ease;
  pointer-events: auto;
  cursor: pointer;
}

.scrollbar-section-dot.is-active {
  width: 6px;
  height: 6px;
  background: #9b8cff;
  box-shadow: 0 0 6px rgba(155, 140, 255, 0.5);
}

/* Section label tooltip */
.scrollbar-section-label {
  position: absolute;
  right: calc(100% + 8px);
  top: 50%;
  transform: translateY(-50%);
  background: rgba(12, 14, 18, 0.85);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.8);
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.02em;
  padding: 3px 7px;
  border-radius: 6px;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.custom-scrollbar.is-hovered .scrollbar-section-label {
  opacity: 1;
}

/* === Mobile guard === */
@media (max-width: 1024px) {
  .custom-scrollbar {
    display: none !important;
  }
}
</style>
