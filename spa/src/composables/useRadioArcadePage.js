import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'

export function useRadioArcadePage({
  playerStore,
  stationCurrent,
  isRadioContext,
  isRadioAudible,
  syncLivePlayback,
  toggleRadioAudio,
  closeNowPlaying,
  haptics,
}) {
  const bestScores = reactive({ garden: 0, trampoline: 0, birds: 0 })
  const menuBeats = ref(0)
  const isFullscreen = ref(false)
  const consoleRef = ref(null)
  const activeGame = ref(null)
  const isRadioActive = ref(false)
  const showRotatePrompt = ref(false)
  const stageStatus = ref({ score: 0, combo: 1, signal: 0.48 })
  const activeTrick = ref(null)
  const trickNotification = ref('')
  const showHint = ref(false)
  const clickHint = ref('')

  let rotatePromptMediaQuery = null
  let hintTimeout = null
  let notificationTimeout = null
  let clickHintTimeout = null

  const gameOptions = [
    {
      id: 'garden',
      name: 'Pocket Garden',
      description: 'Grow crops and raise pets to the rhythm',
      emoji: '🌱',
      accentClass: 'game-card--garden',
      scoreKey: 'garden',
      bestText: (score) => `${score} harvested`,
    },
    {
      id: 'trampoline',
      name: 'Trampoline',
      description: 'Flip your ninja to the beat',
      emoji: '🥷',
      accentClass: 'game-card--trampoline',
      scoreKey: 'trampoline',
      bestText: (score) => `${score}× best flip`,
    },
    {
      id: 'birds',
      name: 'Space Seagulls',
      description: 'Launch seagulls, smash towers',
      emoji: '🦅',
      accentClass: 'game-card--birds',
      scoreKey: 'birds',
      bestText: (score) => `${score} pts best`,
    },
  ]

  function loadBestScores() {
    try {
      const garden = JSON.parse(localStorage.getItem('ahoy_garden_progress') || '{}')
      const trampolineBest = parseInt(localStorage.getItem('ahoy_trampoline_best') || '0', 10)
      const birdsBest = parseInt(localStorage.getItem('ahoy_birds_best') || '0', 10)
      bestScores.garden = garden.totalHarvested || 0
      bestScores.trampoline = trampolineBest
      bestScores.birds = birdsBest
      menuBeats.value = Math.floor(garden.beats || 0)
    } catch (e) {
      /* ignore local storage failures */
    }
  }

  function awardBeats(amount) {
    try {
      const saved = localStorage.getItem('ahoy_garden_progress')
      const data = saved ? JSON.parse(saved) : { totalHarvested: 0, beats: 10 }
      data.beats = (data.beats || 0) + amount
      localStorage.setItem('ahoy_garden_progress', JSON.stringify(data))
    } catch (e) {
      console.error(e)
    }
  }

  function onStageStatus(payload) {
    stageStatus.value = { ...stageStatus.value, ...payload }
    if (stageStatus.value.drift >= 2 && clickHint.value) clickHint.value = ''
  }

  function onStageCollect() {
    haptics.light?.()
    awardBeats(5)
  }

  function onBirdsScore(finalScore) {
    try {
      const prev = parseInt(localStorage.getItem('ahoy_birds_best') || '0', 10)
      if (finalScore > prev) localStorage.setItem('ahoy_birds_best', String(finalScore))
    } catch (e) {
      /* ignore */
    }
  }

  function onStageLock() {
    haptics.medium?.()
  }

  function onStagePop() {
    haptics.light?.()
    awardBeats(1)
  }

  function triggerPulse(intent = {}) {
    haptics.medium?.()
    activeTrick.value = `flip:${Date.now()}`
    trickNotification.value = 'FLIP'
    if (intent.clickX != null) {
      const x = intent.clickX
      const y = intent.clickY ?? 0.5
      const charge = intent.charge ?? 0
      const label =
        x < 0.33 ? 'left spin' :
        x > 0.67 ? 'right spin' :
        y < 0.42 ? 'high pop' :
        charge > 0.35 ? 'charged jump' :
        'center pop'
      clickHint.value = label
      if (clickHintTimeout) window.clearTimeout(clickHintTimeout)
      clickHintTimeout = window.setTimeout(() => { clickHint.value = '' }, 900)
    }
    if (notificationTimeout) window.clearTimeout(notificationTimeout)
    notificationTimeout = window.setTimeout(() => { trickNotification.value = '' }, 520)
    window.setTimeout(() => { activeTrick.value = null }, 240)
  }

  function handleRadioAudioToggle() {
    closeNowPlaying()
    toggleRadioAudio()
    window.setTimeout(closeNowPlaying, 120)
  }

  function launchGame(game) {
    activeGame.value = game
    isRadioActive.value = true
    if (game === 'trampoline') {
      showHint.value = true
      if (hintTimeout) window.clearTimeout(hintTimeout)
      hintTimeout = window.setTimeout(() => { showHint.value = false }, 2400)
    }
  }

  function exitGame() {
    activeGame.value = null
    loadBestScores()
  }

  function toggleFullscreen() {
    if (!consoleRef.value) return
    if (!document.fullscreenElement) {
      consoleRef.value.requestFullscreen().catch((err) => {
        console.error('Error enabling fullscreen:', err)
      })
    } else {
      document.exitFullscreen()
    }
  }

  function onFullscreenChange() {
    isFullscreen.value = !!document.fullscreenElement
  }

  function updateRotatePrompt() {
    showRotatePrompt.value = !!rotatePromptMediaQuery?.matches
  }

  watch(
    () => stationCurrent.value?.id,
    (newId, oldId) => {
      if (!newId || newId === oldId || !isRadioActive.value || !isRadioContext.value) return
      syncLivePlayback(!playerStore.isMuted)
    },
  )

  onMounted(() => {
    document.addEventListener('fullscreenchange', onFullscreenChange)
    document.addEventListener('webkitfullscreenchange', onFullscreenChange)
    if (window.matchMedia) {
      rotatePromptMediaQuery = window.matchMedia('(hover: none) and (pointer: coarse) and (orientation: landscape)')
      updateRotatePrompt()
      if (rotatePromptMediaQuery.addEventListener) {
        rotatePromptMediaQuery.addEventListener('change', updateRotatePrompt)
      } else if (rotatePromptMediaQuery.addListener) {
        rotatePromptMediaQuery.addListener(updateRotatePrompt)
      }
    }
    loadBestScores()
  })

  onUnmounted(() => {
    document.removeEventListener('fullscreenchange', onFullscreenChange)
    document.removeEventListener('webkitfullscreenchange', onFullscreenChange)
    if (rotatePromptMediaQuery?.removeEventListener) {
      rotatePromptMediaQuery.removeEventListener('change', updateRotatePrompt)
    } else if (rotatePromptMediaQuery?.removeListener) {
      rotatePromptMediaQuery.removeListener(updateRotatePrompt)
    }
    if (hintTimeout) window.clearTimeout(hintTimeout)
    if (notificationTimeout) window.clearTimeout(notificationTimeout)
    if (clickHintTimeout) window.clearTimeout(clickHintTimeout)
  })

  const audioDrive = computed(() => {
    const audible = isRadioAudible.value ? 0.48 : 0.18
    const playing = playerStore.isPlaying ? 0.14 : 0
    const volume = Math.max(0, Math.min(1, (playerStore.volume ?? 80) / 100)) * 0.12
    const progress = playerStore.duration > 0 ? (playerStore.currentTime || 0) / playerStore.duration : 0
    const progressLift = 0.08 + (Math.sin(progress * Math.PI * 2) + 1) * 0.05
    return Math.max(0.08, Math.min(1, audible + playing + volume + progressLift))
  })

  const audioPhase = computed(() => (playerStore.currentTime || 0) / 6)
  const stationArt = computed(() => stationCurrent.value?.cover_art || stationCurrent.value?.thumbnail || stationCurrent.value?.artwork || '')
  const stationTitle = computed(() => stationCurrent.value?.title || stationCurrent.value?.name || 'Live radio')

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

  return {
    bestScores,
    menuBeats,
    isFullscreen,
    consoleRef,
    activeGame,
    isRadioActive,
    showRotatePrompt,
    activeTrick,
    trickNotification,
    showHint,
    clickHint,
    gameOptions,
    audioDrive,
    audioPhase,
    stationArt,
    stationTitle,
    radioToggleLabel,
    radioButtonIcon,
    launchGame,
    exitGame,
    handleRadioAudioToggle,
    onStageStatus,
    onStageCollect,
    onStageLock,
    onStagePop,
    onBirdsScore,
    onPulse: triggerPulse,
    toggleFullscreen,
  }
}
