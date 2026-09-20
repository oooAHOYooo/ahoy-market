import { computed } from 'vue'

export function useRadioPage({ playerStore, stationCurrent, isRadioContext, isRadioAudible, toggleRadioAudio, closeNowPlaying }) {
  const audioDrive = computed(() => {
    const audible = isRadioAudible.value ? 0.48 : 0.18
    const playing = playerStore.isPlaying ? 0.14 : 0
    const volume = Math.max(0, Math.min(1, (playerStore.volume ?? 80) / 100)) * 0.12
    const progress = playerStore.duration > 0 ? (playerStore.currentTime || 0) / playerStore.duration : 0
    const progressLift = 0.08 + (Math.sin(progress * Math.PI * 2) + 1) * 0.05
    return Math.max(0.08, Math.min(1, audible + playing + volume + progressLift))
  })

  const stationArt = computed(() => stationCurrent.value?.cover_art || stationCurrent.value?.thumbnail || stationCurrent.value?.artwork || '')
  const stationTitle = computed(() => stationCurrent.value?.title || stationCurrent.value?.name || 'Live radio')
  const stationArtist = computed(() => stationCurrent.value?.artist || stationCurrent.value?.artist_name || stationCurrent.value?.creator || '')

  const radioToggleLabel = computed(() => {
    if (!stationCurrent.value) return 'Loading radio'
    if (!isRadioContext.value) return 'Tune in to radio'
    return playerStore.isMuted ? 'Unmute radio' : 'Mute radio'
  })

  const radioButtonIcon = computed(() => {
    if (!stationCurrent.value) return 'fa-circle-notch fa-spin'
    if (!isRadioContext.value) return 'fa-play'
    return playerStore.isMuted ? 'fa-volume-xmark' : 'fa-volume-high'
  })

  function handleRadioAudioToggle() {
    closeNowPlaying()
    toggleRadioAudio()
    window.setTimeout(closeNowPlaying, 120)
  }

  return {
    audioDrive,
    stationArt,
    stationArtist,
    stationTitle,
    radioToggleLabel,
    radioButtonIcon,
    handleRadioAudioToggle,
  }
}
