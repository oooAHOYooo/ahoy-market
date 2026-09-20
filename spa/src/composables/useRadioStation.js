import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { apiFetchCached } from './useApi'

const DEFAULT_EPOCH_MS = Date.UTC(2026, 0, 1, 0, 0, 0)

export function useRadioStation(playerStore) {
  const tracks = ref([])
  const isLoading = ref(false)
  const loadFailed = ref(false)
  const epochMs = ref(DEFAULT_EPOCH_MS)
  const serverClockOffsetMs = ref(0)
  const stationNow = ref(Date.now())

  let clockInterval = null
  let manifestInterval = null
  let wakeLock = null
  let visibilityHandler = null

  function normalizeItem(track) {
    return {
      ...track,
      kind: track.kind || track.type || 'track',
      type: track.type || track.kind || 'track',
      duration_seconds: Number(track.duration_seconds) > 0 ? Number(track.duration_seconds) : 180,
    }
  }

  const stationClockSeconds = computed(() => Math.floor((stationNow.value - epochMs.value) / 1000))
  const totalDuration = computed(() => tracks.value.reduce((sum, track) => sum + (track.duration_seconds || 180), 0))

  const stationState = computed(() => {
    if (!tracks.value.length || totalDuration.value <= 0) {
      return { currentTrack: null, currentIndex: -1, elapsed: 0 }
    }

    const total = totalDuration.value
    const clock = ((stationClockSeconds.value % total) + total) % total
    let cursor = 0

    for (let index = 0; index < tracks.value.length; index += 1) {
      const track = tracks.value[index]
      const duration = track.duration_seconds || 180
      if (clock < cursor + duration) {
        const upNext = []
        for (let offset = 1; offset <= 3; offset += 1) {
          upNext.push(tracks.value[(index + offset) % tracks.value.length])
        }
        return { currentTrack: track, currentIndex: index, elapsed: clock - cursor }
      }
      cursor += duration
    }

    return { currentTrack: tracks.value[0], currentIndex: 0, elapsed: 0 }
  })

  const currentTrack = computed(() => stationState.value.currentTrack)
  const elapsed = computed(() => stationState.value.elapsed)

  // The 2 tracks that played before the current one — shown as "Just Played".
  // Looking backward is fine for radio; looking forward (Up Next) implies on-demand.
  const justPlayed = computed(() => {
    const { currentIndex } = stationState.value
    if (currentIndex < 0 || !tracks.value.length) return []
    const result = []
    for (let offset = 1; offset <= 2; offset += 1) {
      const idx = (currentIndex - offset + tracks.value.length) % tracks.value.length
      result.push(tracks.value[idx])
    }
    return result
  })

  const isRadioContext = computed(() => {
    if (!currentTrack.value || !playerStore?.currentTrack || !playerStore?.isPlaying) return false
    return playerStore.playbackSource === 'radio'
  })

  const isRadioAudible = computed(() => isRadioContext.value && !playerStore?.isMuted)

  // ── Media Session API ─────────────────────────────────────────────
  // Sets lock-screen / head-unit / Bluetooth metadata so car infotainment
  // and iOS/Android system controls show what's playing on Ahoy Radio.

  function updateMediaSession(track) {
    if (!('mediaSession' in navigator) || !track) return
    try {
      const artwork = track.cover_art
        ? [
            { src: track.cover_art, sizes: '512x512', type: 'image/jpeg' },
            { src: track.cover_art, sizes: '256x256', type: 'image/jpeg' },
          ]
        : []
      navigator.mediaSession.metadata = new MediaMetadata({
        title: track.title || 'Ahoy Radio',
        artist: track.artist || 'Live Station',
        album: 'Ahoy Radio',
        artwork,
      })
    } catch (_) {}
  }

  function registerMediaSessionHandlers() {
    if (!('mediaSession' in navigator)) return
    try {
      navigator.mediaSession.setActionHandler('play', () => {
        if (!isRadioContext.value) syncLivePlayback(true)
        else if (playerStore.isMuted) playerStore.toggleMute()
      })
      navigator.mediaSession.setActionHandler('pause', () => {
        if (!playerStore.isMuted) playerStore.toggleMute()
      })
      navigator.mediaSession.setActionHandler('stop', () => {
        if (!playerStore.isMuted) playerStore.toggleMute()
      })
      // Radio is a live station — disable seek/skip controls
      navigator.mediaSession.setActionHandler('seekto', null)
      navigator.mediaSession.setActionHandler('seekbackward', null)
      navigator.mediaSession.setActionHandler('seekforward', null)
      navigator.mediaSession.setActionHandler('nexttrack', null)
      navigator.mediaSession.setActionHandler('previoustrack', null)
    } catch (_) {}
  }

  function clearMediaSessionHandlers() {
    if (!('mediaSession' in navigator)) return
    try {
      ;['play', 'pause', 'stop'].forEach(action => {
        navigator.mediaSession.setActionHandler(action, null)
      })
      navigator.mediaSession.playbackState = 'none'
    } catch (_) {}
  }

  // ── Screen Wake Lock ──────────────────────────────────────────────
  // Keeps the screen on while tuned in — useful in car/dashboard mode.

  async function requestWakeLock() {
    if (!('wakeLock' in navigator) || wakeLock) return
    try {
      wakeLock = await navigator.wakeLock.request('screen')
    } catch (_) {}
  }

  function releaseWakeLock() {
    if (wakeLock) {
      wakeLock.release().catch(() => {})
      wakeLock = null
    }
  }

  // ── Manifest loading ──────────────────────────────────────────────

  async function loadManifest(force = false) {
    if (tracks.value.length > 0 && !force) return

    isLoading.value = true
    try {
      const data = await apiFetchCached('/api/radio/live', 'ahoy:radio:manifest')
      tracks.value = (data.items || data.tracks || []).map(normalizeItem)
      epochMs.value = Number(data.station?.epoch_ms) || epochMs.value
      serverClockOffsetMs.value = (Number(data.server_time_ms) || Date.now()) - Date.now()
      stationNow.value = Date.now() + serverClockOffsetMs.value
      loadFailed.value = false
    } catch {
      loadFailed.value = true
    } finally {
      isLoading.value = false
    }
  }

  function syncLivePlayback(unmute = true) {
    if (!currentTrack.value || stationState.value.currentIndex < 0) return
    playerStore.setQueue(tracks.value, stationState.value.currentIndex, { source: 'radio' })
    window.setTimeout(() => {
      playerStore.seekTo(stationState.value.elapsed)
      if (playerStore.isMuted === unmute) playerStore.toggleMute()
    }, 80)
  }

  function toggleRadioAudio() {
    if (!currentTrack.value) return
    if (!isRadioContext.value) {
      syncLivePlayback(true)
      return
    }
    playerStore.toggleMute()
  }

  // ── Lifecycle ─────────────────────────────────────────────────────

  onMounted(async () => {
    await loadManifest()

    // Auto-resume if user was tuned in before page refresh
    if (localStorage.getItem('radio:wasAudible') === '1' && !isRadioContext.value) {
      syncLivePlayback(true)
    }

    // Silently refresh track list every 30 min so new additions appear without reload
    manifestInterval = window.setInterval(() => loadManifest(true), 30 * 60 * 1000)

    registerMediaSessionHandlers()

    // Update lock-screen / head-unit metadata when track changes
    watch(() => stationState.value.currentIndex, (newIdx, oldIdx) => {
      if (newIdx !== oldIdx && newIdx >= 0 && tracks.value[newIdx]) {
        updateMediaSession(tracks.value[newIdx])
      }
    })

    // Persist tuned-in state so we can auto-resume after page refresh
    watch(isRadioAudible, (audible) => {
      localStorage.setItem('radio:wasAudible', audible ? '1' : '0')
    })

    // Wake lock follows audible state; re-request on tab visibility restore
    watch(isRadioAudible, async (audible) => {
      if (audible) {
        await requestWakeLock()
        if ('mediaSession' in navigator) {
          navigator.mediaSession.playbackState = 'playing'
        }
      } else {
        releaseWakeLock()
        if ('mediaSession' in navigator) {
          navigator.mediaSession.playbackState = 'paused'
        }
      }
    })

    visibilityHandler = () => {
      if (document.visibilityState === 'visible') {
        if (isRadioAudible.value) requestWakeLock()
        // Correct drift from browser throttling while tab was hidden
        if (isRadioContext.value) playerStore.seekTo(stationState.value.elapsed)
      }
    }
    document.addEventListener('visibilitychange', visibilityHandler)

    clockInterval = window.setInterval(() => {
      stationNow.value = Date.now() + serverClockOffsetMs.value
    }, 1000)
  })

  onUnmounted(() => {
    if (clockInterval) window.clearInterval(clockInterval)
    if (manifestInterval) window.clearInterval(manifestInterval)
    releaseWakeLock()
    clearMediaSessionHandlers()
    if (visibilityHandler) {
      document.removeEventListener('visibilitychange', visibilityHandler)
    }
  })

  return {
    tracks,
    isLoading,
    loadFailed,
    stationClockSeconds,
    currentTrack,
    elapsed,
    justPlayed,
    isRadioContext,
    isRadioAudible,
    loadManifest,
    syncLivePlayback,
    toggleRadioAudio,
  }
}
