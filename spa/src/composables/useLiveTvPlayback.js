import { computed, onUnmounted, ref, watch } from 'vue'

function classifyVideoSource(src) {
  if (!src) return 'missing'
  const lower = String(src).toLowerCase()
  if (lower.includes('storage.googleapis.com') || lower.includes('googleapis.com')) return 'gcs'
  if (lower.includes('s3.') || lower.includes('amazonaws.com')) return 's3'
  if (lower.includes('/proxy/video')) return 'proxy'
  return 'other'
}

export function useLiveTvPlayback({
  heroVideoRef,
  playerStore,
  channels,
  selectedRow,
  currentSlot,
  getSeekTime,
}) {
  const loading = ref(false)
  const heroVideoError = ref(false)
  const isWatching = ref(false)
  const videoLoadStartedAt = ref(0)
  const lastAppliedSlotKey = ref('')

  const activeChannel = computed(() => channels.value[selectedRow.value] || null)
  const hasPlayableSlot = computed(() => !!currentSlot.value?.src)
  const hasVideoTrack = computed(() => playerStore.mode === 'video' && !!playerStore.currentTrack?.video_url)

  const playbackState = computed(() => {
    if (heroVideoError.value) return 'error'
    if (loading.value) return 'loading'
    if (!hasPlayableSlot.value) return 'idle'
    if (playerStore.isPlaying) return isWatching.value ? 'playing' : 'preview'
    return 'ready'
  })

  function buildTrack(slot) {
    const channel = activeChannel.value
    return {
      type: 'live_tv',
      id: `live_tv-${channel?.id ?? selectedRow.value}`,
      title: slot?.title || 'AHOY TV',
      host: channel?.name || 'AHOY TV',
      thumbnail: slot?.thumb || '',
      video_url: slot?.src || '',
      duration_seconds: slot?.durationSec || 0,
    }
  }

  function pushVideoDiagnostic(event, extra = {}) {
    const slot = currentSlot.value
    const src = slot?.src || playerStore.currentTrack?.video_url || ''

    const payload = {
      event,
      at: Date.now(),
      src,
      sourceType: classifyVideoSource(src),
      channel: activeChannel.value?.name || null,
      slotStartUTC: slot?.startUTC || null,
      slotEndUTC: slot?.endUTC || null,
      loadMs: videoLoadStartedAt.value ? Math.max(0, Date.now() - videoLoadStartedAt.value) : null,
      ...extra,
    }

    try {
      const raw = localStorage.getItem('ahoy.videoDiagnostics')
      const entries = raw ? JSON.parse(raw) : []
      entries.push(payload)
      localStorage.setItem('ahoy.videoDiagnostics', JSON.stringify(entries.slice(-40)))
    } catch {
      // ignore storage failures
    }

    window.dispatchEvent(new CustomEvent('ahoy:video-diagnostic', { detail: payload }))
    console.info('[VideoDiagnostic]', payload)
  }

  function syncSlotToPlayer({ forceReload = false } = {}) {
    const slot = currentSlot.value
    const videoEl = heroVideoRef.value

    if (!slot || !slot.src) {
      loading.value = false
      heroVideoError.value = false
      lastAppliedSlotKey.value = ''
      playerStore.loading = false
      playerStore.mode = 'video'
      playerStore.currentTrack = buildTrack(null)
      return
    }

    const slotKey = `${selectedRow.value}:${slot.startUTC}:${slot.endUTC}:${slot.src}`
    const seekSec = getSeekTime(slot)

    playerStore.mode = 'video'
    playerStore.currentTrack = buildTrack(slot)

    if (!videoEl) {
      lastAppliedSlotKey.value = slotKey
      return
    }

    const isSameSource = videoEl.currentSrc === slot.src || videoEl.src === slot.src

    if (!forceReload && isSameSource && lastAppliedSlotKey.value && lastAppliedSlotKey.value !== slotKey) {
      try {
        if (seekSec > 0) videoEl.currentTime = seekSec
      } catch {
        // ignore seek issues on source rollover
      }
      lastAppliedSlotKey.value = slotKey
      return
    }

    if (!forceReload && lastAppliedSlotKey.value === slotKey) return

    loading.value = true
    heroVideoError.value = false
    playerStore.loading = true
    videoLoadStartedAt.value = Date.now()
    pushVideoDiagnostic('slot-sync', { forceReload, slotKey })

    videoEl.src = slot.src
    videoEl.load()
    videoEl.addEventListener(
      'loadedmetadata',
      () => {
        try {
          if (seekSec > 0) videoEl.currentTime = seekSec
        } catch {
          // ignore seek issues on first metadata load
        }
        if (!isWatching.value || playerStore.isPlaying) {
          videoEl.play().catch(() => {})
        } else {
          videoEl.pause()
          loading.value = false
          playerStore.loading = false
        }
      },
      { once: true },
    )

    if (!isWatching.value) {
      videoEl.muted = true
    } else {
      videoEl.muted = playerStore.isMuted
    }

    lastAppliedSlotKey.value = slotKey
  }

  function retryCurrentChannel() {
    lastAppliedSlotKey.value = ''
    heroVideoError.value = false
    loading.value = true
    syncSlotToPlayer({ forceReload: true })
  }

  function watchNow() {
    if (!hasPlayableSlot.value) return
    isWatching.value = true
    if (heroVideoRef.value) {
      heroVideoRef.value.muted = false
      playerStore.isMuted = false
      if (heroVideoRef.value.paused) heroVideoRef.value.play().catch(() => {})
    }
  }

  function resetToPreviewMode() {
    isWatching.value = false
    if (heroVideoRef.value) {
      heroVideoRef.value.muted = true
    }
  }

  function onHeroVideoMetadata() {
    if (!heroVideoRef.value) return
    playerStore.duration = heroVideoRef.value.duration
    playerStore.loading = false
    playerStore.setVideoElement(heroVideoRef.value)
    pushVideoDiagnostic('loadedmetadata', {
      durationSec: Number.isFinite(heroVideoRef.value.duration) ? Math.round(heroVideoRef.value.duration) : null,
    })
  }

  function onHeroVideoLoadStart() {
    loading.value = true
    heroVideoError.value = false
    playerStore.loading = true
    videoLoadStartedAt.value = Date.now()
    pushVideoDiagnostic('loadstart')
  }

  function onHeroVideoCanPlay() {
    loading.value = false
    heroVideoError.value = false
    playerStore.loading = false
    pushVideoDiagnostic('canplay')
  }

  function onHeroVideoError() {
    loading.value = false
    heroVideoError.value = true
    playerStore.loading = false
    playerStore.isPlaying = false
    pushVideoDiagnostic('error')
  }

  function onHeroClick() {
    if (!isWatching.value) return
    playerStore.togglePlay()
  }

  watch(heroVideoRef, (element) => {
    if (element) {
      playerStore.setVideoElement(element)
      syncSlotToPlayer({ forceReload: true })
    }
  })

  watch(
    () => playerStore.isPlaying,
    (playing) => {
      if (!heroVideoRef.value) return
      if (playing && heroVideoRef.value.paused) heroVideoRef.value.play().catch(() => {})
      else if (!playing && !heroVideoRef.value.paused) heroVideoRef.value.pause()
    },
  )

  watch(selectedRow, () => {
    resetToPreviewMode()
  })

  watch(
    () => currentSlot.value ? `${selectedRow.value}:${currentSlot.value.startUTC}:${currentSlot.value.endUTC}:${currentSlot.value.src}` : `empty:${selectedRow.value}`,
    () => {
      syncSlotToPlayer()
    },
    { immediate: true },
  )

  onUnmounted(() => {
    playerStore.loading = false
  })

  return {
    loading,
    heroVideoError,
    isWatching,
    hasVideoTrack,
    hasPlayableSlot,
    playbackState,
    retryCurrentChannel,
    watchNow,
    onHeroClick,
    onHeroVideoMetadata,
    onHeroVideoLoadStart,
    onHeroVideoCanPlay,
    onHeroVideoError,
    syncSlotToPlayer,
    resetToPreviewMode,
  }
}
