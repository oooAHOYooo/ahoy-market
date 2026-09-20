<template>
  <div class="radio-page">
    <!-- Blurred art backdrop — fixed to viewport, z-index 0, under all content -->
    <div
      v-if="stationArt"
      class="radio-bg"
      :style="{ backgroundImage: `url(${stationArt})` }"
      aria-hidden="true"
    />
    <!-- Content sits above backdrop at z-index 1 -->
    <div class="radio-content">
      <RadioHomePanel
        :is-radio-audible="isRadioAudible"
        :radio-button-icon="radioButtonIcon"
        :radio-toggle-label="radioToggleLabel"
        :station-art="stationArt"
        :station-artist="stationArtist"
        :station-current="stationCurrent"
        :station-title="stationTitle"
        :elapsed="elapsed"
        :just-played="justPlayed"
        :is-loading="isLoading"
        :load-failed="loadFailed"
        @toggle-radio="handleRadioAudioToggle"
        @retry="loadManifest(true)"
      />
    </div>
  </div>
</template>

<script setup>
import { watch, onMounted, onUnmounted } from 'vue'
import { useRadioStation } from '../composables/useRadioStation'
import { useRadioPage } from '../composables/useRadioPage'
import { usePlayerStore } from '../stores/player'
import { useOverlay } from '../composables/useOverlay'
import RadioHomePanel from '../features/radio/RadioHomePanel.vue'

const playerStore = usePlayerStore()
const { closeNowPlaying } = useOverlay()

const {
  currentTrack: stationCurrent,
  isRadioContext,
  isRadioAudible,
  toggleRadioAudio,
  elapsed,
  justPlayed,
  isLoading,
  loadFailed,
  loadManifest,
} = useRadioStation(playerStore)

const savedTitle = document.title
watch(() => stationCurrent.value?.id, () => {
  const t = stationCurrent.value
  document.title = t?.title
    ? `${t.title}${t.artist ? ` · ${t.artist}` : ''} — Ahoy Radio`
    : 'Ahoy Radio'
}, { immediate: true })

function onKeyDown(e) {
  if (e.code !== 'Space') return
  const tag = document.activeElement?.tagName
  if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || document.activeElement?.isContentEditable) return
  e.preventDefault()
  handleRadioAudioToggle()
}

onMounted(() => window.addEventListener('keydown', onKeyDown))
onUnmounted(() => {
  window.removeEventListener('keydown', onKeyDown)
  document.title = savedTitle
})

const {
  stationArt,
  stationArtist,
  stationTitle,
  radioToggleLabel,
  radioButtonIcon,
  handleRadioAudioToggle,
} = useRadioPage({
  playerStore,
  stationCurrent,
  isRadioContext,
  isRadioAudible,
  toggleRadioAudio,
  closeNowPlaying,
})
</script>

<style scoped>
.radio-page {
  position: relative;
  width: 100%;
  min-height: 100%;
}

/* Full-viewport blurred art backdrop */
.radio-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  background-size: cover;
  background-position: center;
  /* Heavy blur + desaturate + darken so text stays readable */
  filter: blur(72px) saturate(110%) brightness(0.18);
  /* Scale slightly past edges to hide blur fringe */
  transform: scale(1.12);
  pointer-events: none;
  will-change: transform;
}

/* Content layer above backdrop */
.radio-content {
  position: relative;
  z-index: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: var(--mobile-top-offset, 36px) var(--mobile-gutter, 4px) var(--mobile-bottom-clear, 100px);
  box-sizing: border-box;
}

@media (min-width: 1025px) {
  .radio-content {
    align-items: center;
    padding: 0.5rem 1.5rem 1.5rem;
  }
}
</style>
