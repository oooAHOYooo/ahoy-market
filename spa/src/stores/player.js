import { defineStore } from 'pinia'
import { ref, computed, watch, onUnmounted } from 'vue'
import { apiFetch } from '../composables/useApi'
import { trackRecentPlay } from '../composables/useRecentlyPlayed'
import { useOverlay } from '../composables/useOverlay'
import { trackEvent } from '../composables/useAnalytics'
import { useVideoWatchAnalytics } from '../composables/useVideoWatchAnalytics'
import { setDynamicFavicon, resetFavicon } from '../utils/favicon'

export const usePlayerStore = defineStore('player', () => {
  // State
  const currentTrack = ref(null)
  const isPlaying = ref(false)
  const _countedTracks = new Set() // track IDs already counted this session
  const queue = ref([])
  const currentTime = ref(0)
  const duration = ref(0)
  const loading = ref(false)
  const shuffle = ref(false)
  const repeat = ref(false)
  const volume = ref(JSON.parse(localStorage.getItem('player-volume') || '0.8') * 100) // Initialize from localStorage, convert to 0-100
  const playbackRate = ref(1.0)
  const isMuted = ref(false)
  const sessionId = ref(null)
  const autoplayEnabled = ref(JSON.parse(localStorage.getItem('ahoySettings') || '{}')?.customization?.autoplayEnabled ?? true)
  const playbackSource = ref('manual')

  // Progress tracking for podcasts
  const podcastProgress = ref(JSON.parse(localStorage.getItem('ahoy.podcastProgress') || '{}'))

  function savePodcastProgress(trackId, time) {
    if (!trackId) return
    podcastProgress.value[trackId] = time
    localStorage.setItem('ahoy.podcastProgress', JSON.stringify(podcastProgress.value))
  }

  function getPodcastProgress(trackId) {
    return podcastProgress.value[trackId] || 0
  }

  // Unified Player State
  const mode = ref('audio') // 'audio' or 'video'
  const heroBounds = ref(null) // { top, left, width, height }
  const videoElement = ref(null) // DOM reference to the global video tag
  const isWidescreenPinned = ref(false)
  const audioLoadStartedAt = ref(0)
  const playbackDiagnostics = ref({
    sourceType: 'unknown',
    src: '',
    trackId: null,
    trackTitle: '',
  })
  const videoWatch = useVideoWatchAnalytics(trackEvent, () => ({
    video_id: currentTrack.value?.id || currentTrack.value?.key || currentTrack.value?.slug || null,
    video_title: currentTrack.value?.title || '',
    video_host: currentTrack.value?.host || currentTrack.value?.artist || currentTrack.value?.author || '',
    video_type: currentTrack.value?.type || currentTrack.value?._type || '',
    playback_source: playbackSource.value || 'manual',
    mode: mode.value,
    src: videoElement.value?.currentSrc || videoElement.value?.src || currentTrack.value?.video_url || currentTrack.value?.url || '',
  }))

  function classifyAudioSource(src) {
    if (!src) return 'missing'
    const lower = String(src).toLowerCase()
    if (lower.includes('storage.googleapis.com') || lower.includes('googleapis.com')) return 'gcs'
    if (lower.includes('s3.') || lower.includes('amazonaws.com')) return 's3'
    if (lower.includes('/proxy/audio')) return 'proxy'
    return 'other'
  }

  function pushPlaybackDiagnostic(event, extra = {}) {
    const payload = {
      event,
      at: Date.now(),
      sourceType: playbackDiagnostics.value.sourceType,
      src: playbackDiagnostics.value.src,
      trackId: playbackDiagnostics.value.trackId,
      trackTitle: playbackDiagnostics.value.trackTitle,
      loadMs: audioLoadStartedAt.value ? Math.max(0, Date.now() - audioLoadStartedAt.value) : null,
      ...extra,
    }

    try {
      const raw = localStorage.getItem('ahoy.audioDiagnostics')
      const entries = raw ? JSON.parse(raw) : []
      entries.push(payload)
      localStorage.setItem('ahoy.audioDiagnostics', JSON.stringify(entries.slice(-40)))
    } catch {
      // ignore storage issues; console + event still provide signal
    }

    window.dispatchEvent(new CustomEvent('ahoy:audio-diagnostic', { detail: payload }))
    console.info('[AudioDiagnostic]', payload)
  }

  function mediaAnalyticsProps(extra = {}) {
    return {
      track_id: currentTrack.value?.id || currentTrack.value?.key || currentTrack.value?.slug || null,
      track_title: currentTrack.value?.title || '',
      artist: currentTrack.value?.artist || currentTrack.value?.host || currentTrack.value?.author || '',
      show_title: currentTrack.value?.show_title || currentTrack.value?.showTitle || currentTrack.value?.series || currentTrack.value?.podcast_title || '',
      track_type: currentTrack.value?.type || currentTrack.value?._type || '',
      playback_source: playbackSource.value || 'manual',
      mode: mode.value,
      ...extra,
    }
  }

  // Audio element (singleton)
  let audio = null
  const prefetchSlots = [null, null]
  const prefetchedSrcs = new Set()

  function resolveMediaSrc(src) {
    if (!src) return ''
    if (src.startsWith('http://') || src.startsWith('https://')) return src
    if (src.startsWith('/')) return `${window.location.origin}${src}`
    return `${window.location.origin}/${src}`
  }

  function getPrefetchAudio(slotIndex) {
    if (!prefetchSlots[slotIndex]) {
      prefetchSlots[slotIndex] = new Audio()
      prefetchSlots[slotIndex].preload = 'metadata'
    }
    return prefetchSlots[slotIndex]
  }

  function prefetchUpcoming(lookahead = 2) {
    if (!currentTrack.value || !queue.value.length) return
    const idx = queue.value.findIndex(t => (t.id === currentTrack.value.id) || (t.id === currentTrack.value.slug))
    if (idx < 0) return
    for (let offset = 1; offset <= lookahead; offset += 1) {
      const nextIdx = idx + offset
      if (nextIdx >= queue.value.length) break
      const nextTrack = queue.value[nextIdx]
      const src = resolveMediaSrc(nextTrack.audio_url || nextTrack.url || '')
      if (!src || prefetchedSrcs.has(src)) continue
      const pa = getPrefetchAudio((offset - 1) % prefetchSlots.length)
      pa.src = src
      pa.load()
      prefetchedSrcs.add(src)
    }
  }

  function getAudio() {
    if (!audio) {
      audio = new Audio()
      audio.preload = 'metadata'

      audio.addEventListener('timeupdate', () => {
        if (mode.value === 'audio') {
          currentTime.value = audio.currentTime
          updatePositionState()

          // Save podcast progress every 10 seconds
          if (
            currentTrack.value &&
            (currentTrack.value.type === 'podcast' || currentTrack.value._type === 'podcast' || currentTrack.value.type === 'podcast-episode' || currentTrack.value.type === 'podcastEpisode') &&
            Math.floor(audio.currentTime) % 10 === 0
          ) {
            savePodcastProgress(currentTrack.value.id || currentTrack.value.key, audio.currentTime)
          }

          // Prefetch the next couple of tracks a little earlier so the cache is warm.
          const remaining = audio.duration - audio.currentTime
          if (remaining > 0 && remaining <= 45 && queue.value.length > 0) {
            prefetchUpcoming(2)
          }
          // Record play count after 5 seconds
          if (
            audio.currentTime >= 5 &&
            currentTrack.value?.id &&
            currentTrack.value?.type === 'track' &&
            !_countedTracks.has(currentTrack.value.id)
          ) {
            const trackId = currentTrack.value.id
            _countedTracks.add(trackId)
            apiFetch('/api/music/play', { method: 'POST', body: JSON.stringify({ track_id: trackId }) })
              .then(data => {
                if (data?.play_count != null) {
                  window.dispatchEvent(new CustomEvent('ahoy:play-counted', { detail: { trackId, count: data.play_count } }))
                }
              })
              .catch(() => { /* non-critical */ })
          }
        }
      })
      audio.addEventListener('loadedmetadata', () => {
        if (mode.value === 'audio') {
          duration.value = audio.duration
          loading.value = false
          audio.playbackRate = playbackRate.value
          pushPlaybackDiagnostic('loadedmetadata', {
            durationSec: Number.isFinite(audio.duration) ? Math.round(audio.duration) : null,
          })
        }
      })
      audio.addEventListener('ended', () => {
        if (mode.value === 'audio' && repeat.value) { audio.currentTime = 0; audio.play(); return }
        if (mode.value === 'audio' && autoplayEnabled.value) next()
        else if (mode.value === 'audio') isPlaying.value = false
      })
      audio.addEventListener('pause', () => {
        if (mode.value === 'audio') isPlaying.value = false
      })
      audio.addEventListener('play', () => {
        if (mode.value === 'audio') {
          isPlaying.value = true
          loading.value = false
          audio.playbackRate = playbackRate.value
        }
      })
      audio.addEventListener('waiting', () => {
        if (mode.value === 'audio') {
          loading.value = true
          pushPlaybackDiagnostic('waiting')
          if (queue.value.length > 0) prefetchUpcoming(2)
        }
      })
      audio.addEventListener('canplay', () => {
        if (mode.value === 'audio') {
          loading.value = false
          pushPlaybackDiagnostic('canplay')
        }
      })
      audio.addEventListener('canplaythrough', () => {
        if (mode.value === 'audio') loading.value = false
      })
      audio.addEventListener('error', (e) => {
        if (mode.value === 'audio') {
          console.warn('Audio error:', e)
          loading.value = false
          isPlaying.value = false
          pushPlaybackDiagnostic('error', {
            mediaErrorCode: audio.error?.code || null,
            mediaErrorMessage: audio.error?.message || null,
          })
        }
      })
      audio.addEventListener('loadstart', () => {
        if (mode.value === 'audio') {
          audioLoadStartedAt.value = Date.now()
          pushPlaybackDiagnostic('loadstart')
        }
      })
      audio.addEventListener('stalled', () => {
        if (mode.value === 'audio') pushPlaybackDiagnostic('stalled')
      })

      // iOS: phone calls and other audio interruptions pause the element without
      // firing our 'pause' handler reliably. Resume when the page comes back visible.
      document.addEventListener('visibilitychange', async () => {
        if (document.visibilityState === 'visible' && isPlaying.value && mode.value === 'audio') {
          if (audio.paused) {
            try { await audio.play() } catch (_) {}
          }
        }
      })

      audio.volume = Math.max(0, Math.min(1, volume.value / 100))
      audio.muted = isMuted.value
      audio.playbackRate = playbackRate.value

      if ('mediaSession' in navigator) {
        navigator.mediaSession.setActionHandler('play', () => play())
        navigator.mediaSession.setActionHandler('pause', () => pause())
        navigator.mediaSession.setActionHandler('previoustrack', () => previous())
        navigator.mediaSession.setActionHandler('nexttrack', () => next())
        navigator.mediaSession.setActionHandler('seekbackward', () => seekBackward())
        navigator.mediaSession.setActionHandler('seekforward', () => seekForward())
        navigator.mediaSession.setActionHandler('seekto', (details) => {
          if (details.seekTime != null) {
            if (mode.value === 'audio') audio.currentTime = details.seekTime
            else if (videoElement.value) videoElement.value.currentTime = details.seekTime
          }
        })
        navigator.mediaSession.setActionHandler('stop', () => pause())
      }
    }
    return audio
  }

  let _volumeSoundTimer = null
  function _playVolumeSound(goingUp) {
    clearTimeout(_volumeSoundTimer)
    _volumeSoundTimer = setTimeout(() => {
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)()
        const osc = ctx.createOscillator()
        const gain = ctx.createGain()
        osc.connect(gain)
        gain.connect(ctx.destination)
        osc.type = 'sine'
        if (goingUp) {
          // slide whistle going up: "wheee!"
          osc.frequency.setValueAtTime(280, ctx.currentTime)
          osc.frequency.exponentialRampToValueAtTime(900, ctx.currentTime + 0.18)
          gain.gain.setValueAtTime(0.7, ctx.currentTime)
          gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.22)
          osc.stop(ctx.currentTime + 0.22)
        } else {
          // sad trombone womp going down
          osc.type = 'sawtooth'
          osc.frequency.setValueAtTime(520, ctx.currentTime)
          osc.frequency.exponentialRampToValueAtTime(120, ctx.currentTime + 0.28)
          gain.gain.setValueAtTime(0.6, ctx.currentTime)
          gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.32)
          osc.stop(ctx.currentTime + 0.32)
        }
        osc.start(ctx.currentTime)
        osc.onended = () => ctx.close()
      } catch (_) { /* Web Audio unavailable */ }
    }, 80)
  }

  function setVolume(value) {
    const v = Math.max(0, Math.min(100, Number(value)))
    const goingUp = v > volume.value
    _playVolumeSound(goingUp)
    volume.value = Math.round(v)
    const a = getAudio()
    a.volume = v / 100
    if (videoElement.value) videoElement.value.volume = v / 100
    if (isMuted.value && v > 0) isMuted.value = false
    a.muted = isMuted.value
    if (videoElement.value) videoElement.value.muted = isMuted.value
    localStorage.setItem('player-volume', JSON.stringify(v / 100))
  }

  function setPlaybackRate(rate) {
    const r = Number(rate) || 1.0
    playbackRate.value = r
    const a = getAudio()
    if (a) a.playbackRate = r
    if (videoElement.value) videoElement.value.playbackRate = r
    updatePositionState()
  }

  function toggleMute() {
    isMuted.value = !isMuted.value
    getAudio().muted = isMuted.value
    if (videoElement.value) videoElement.value.muted = isMuted.value
  }

  function getSeekStep() {
    const media = mode.value === 'audio' ? getAudio() : videoElement.value
    const dur = media?.duration || duration.value
    if (!dur || !isFinite(dur)) return 5
    const step = Math.round(dur * 0.05)
    return Math.max(5, Math.min(30, step))
  }

  function skipBackward(seconds) {
    const media = mode.value === 'audio' ? getAudio() : videoElement.value
    if (!media || !media.src) return
    const amount = Number(seconds) || getSeekStep()
    trackEvent('media_seek', mediaAnalyticsProps({ direction: 'backward', seconds: amount }))
    media.currentTime = Math.max(0, (media.currentTime || 0) - amount)
  }

  function skipForward(seconds) {
    const media = mode.value === 'audio' ? getAudio() : videoElement.value
    if (!media || !media.src) return
    const amount = Number(seconds) || getSeekStep()
    trackEvent('media_seek', mediaAnalyticsProps({ direction: 'forward', seconds: amount }))
    const dur = duration.value || media.duration
    const now = media.currentTime || 0
    media.currentTime = Math.min(dur && isFinite(dur) ? dur : now + amount, now + amount)
  }

  function seekBackward() { skipBackward(getSeekStep()) }
  function seekForward() { skipForward(getSeekStep()) }
  function seekBackward5() { seekBackward() }
  function seekForward5() { seekForward() }

  function toggleFullscreen() {
    const isFullscreen = !!(
      document.fullscreenElement
      || document.webkitFullscreenElement
      || document.mozFullScreenElement
      || document.msFullscreenElement
    )

    if (mode.value === 'video' && videoElement.value) {
      const target = videoElement.value.parentElement || videoElement.value
      const requestFs =
        target?.requestFullscreen
        || target?.webkitRequestFullscreen
        || target?.mozRequestFullScreen
        || target?.msRequestFullscreen
      const exitFs =
        document.exitFullscreen
        || document.webkitExitFullscreen
        || document.mozCancelFullScreen
        || document.msExitFullscreen

      if (!isFullscreen) {
        if (requestFs) {
          const maybePromise = requestFs.call(target)
          maybePromise?.catch?.(() => {})
        } else if (videoElement.value.webkitEnterFullscreen) {
          videoElement.value.webkitEnterFullscreen()
        }
      } else {
        exitFs?.call(document)
      }
      return
    }

    const { isNowPlayingOpen, openNowPlaying, closeNowPlaying } = useOverlay()
    if (currentTrack.value) {
      if (isNowPlayingOpen.value) closeNowPlaying()
      else openNowPlaying()
    }
  }

  function updateMediaSession(track) {
    if (!('mediaSession' in navigator) || !track) return

    const getAbsoluteUrl = (url) => {
      if (!url) return window.location.origin + '/static/img/default-cover.jpg'
      if (url.startsWith('http')) return url
      return window.location.origin + (url.startsWith('/') ? '' : '/') + url
    }

    const artistName = track.artist || track.host || track.author || 'Ahoy Artist'
    const albumName = track.album || 
                      track.show_title || 
                      track.series || 
                      (track.type === 'live_tv' ? 'Ahoy Radio' : 
                      (track._type === 'show' ? 'Ahoy Shows' : 'Ahoy Indie Media'))

    navigator.mediaSession.metadata = new MediaMetadata({
      title: track.title || 'Unknown',
      artist: artistName,
      album: albumName,
      artwork: [
        { src: getAbsoluteUrl(track.cover_art || track.thumbnail || track.artwork), sizes: '512x512', type: 'image/jpeg' },
      ],
    })
  }

  function updatePositionState() {
    const media = mode.value === 'audio' ? audio : videoElement.value
    if (!('mediaSession' in navigator) || !media) return
    try {
      if (media.duration && isFinite(media.duration)) {
        navigator.mediaSession.setPositionState({
          duration: media.duration,
          playbackRate: media.playbackRate,
          position: media.currentTime,
        })
      }
    } catch { /* ignore */ }
  }

  const progress = computed(() => {
    if (!duration.value) return 0
    return (currentTime.value / duration.value) * 100
  })

  const hasQueue = computed(() => queue.value.length > 0)

  // Combined Play Action
  function play(track, options = {}) {
    const source = options.source || playbackSource.value || 'manual'
    if (track) {
      const isVideo = !!(track.video_url || track.url?.endsWith('.mp4') || track._type === 'show' || track.type === 'live_tv')
      playbackSource.value = source
      trackEvent('media_play_requested', {
        track_id: track.id || track.key || track.slug || null,
        track_title: track.title || '',
        artist: track.artist || track.host || track.author || '',
        show_title: track.show_title || track.showTitle || track.series || track.podcast_title || '',
        track_type: track.type || track._type || '',
        playback_source: source,
        mode: isVideo ? 'video' : 'audio',
      })

      if (isVideo) {
        // Switch to video mode
        pause() // Pause existing medium
        mode.value = 'video'
        currentTrack.value = track
        // Video element in GlobalTvPlayer will watch currentTrack and load it
      } else {
        // Switch to audio mode
        if (mode.value === 'video' && videoElement.value) {
          videoElement.value.pause()
        }
        mode.value = 'audio'
        currentTrack.value = track
        const a = getAudio()
        const src = resolveMediaSrc(track.audio_url || track.url || '')
        if (src) {
          playbackDiagnostics.value = {
            sourceType: classifyAudioSource(src),
            src,
            trackId: track.id || track.key || null,
            trackTitle: track.title || '',
          }
          loading.value = true
          a.src = src
          a.load()

          // Restore podcast progress
          if (track.type === 'podcast' || track._type === 'podcast' || track.type === 'podcast-episode' || track.type === 'podcastEpisode') {
            const savedTime = getPodcastProgress(track.id || track.key)
            if (savedTime > 10) { // Only resume if past 10 seconds
              a.currentTime = savedTime
            }
          }

          a.play().catch(() => { loading.value = false })
          prefetchUpcoming(2)
        }
        a.playbackRate = playbackRate.value
      }
      // updateMediaSession moved to watcher
      saveLastPlayed(track)
      trackRecentPlay(track)
    } else {
      // Resume current
      if (options.source) playbackSource.value = source
      trackEvent('media_resume', mediaAnalyticsProps())
      if (mode.value === 'audio') getAudio().play().catch(() => { })
      else if (videoElement.value) {
        videoElement.value.play().catch(() => { })
        isPlaying.value = true
      }
    }
    // Start listening session
    startListeningSession()

    // Auto-expand on mobile for first play
    if (window.innerWidth <= 480 && !localStorage.getItem('ahoy.firstPlayExpanded') && !window.location.pathname.includes('/radio')) {
      const { openNowPlaying } = useOverlay()
      openNowPlaying()
      localStorage.setItem('ahoy.firstPlayExpanded', 'true')
    }
  }

  async function startListeningSession() {
    if (!currentTrack.value) return

    // End existing session if any
    if (sessionId.value) {
      await endListeningSession()
    }

    try {
      const resp = await apiFetch('/api/listening/start', {
        method: 'POST',
        body: JSON.stringify({
          media_id: currentTrack.value.id || currentTrack.value.key,
          media_type: currentTrack.value.type || 'track',
          source: playbackSource.value || 'manual'
        })
      })
      if (resp && resp.session_id) {
        sessionId.value = resp.session_id
      }
    } catch (e) {
      console.error('Failed to start listening session:', e)
    }
  }

  async function endListeningSession() {
    if (!sessionId.value) return

    const sid = sessionId.value
    sessionId.value = null // Clear immediately to avoid re-entry

    try {
      await apiFetch('/api/listening/end', {
        method: 'POST',
        body: JSON.stringify({ session_id: sid })
      })
    } catch (e) {
      console.error('Failed to end listening session:', e)
    }
  }

  function pause() {
    isPlaying.value = false
    trackEvent('media_pause', mediaAnalyticsProps())
    getAudio().pause()
    if (videoElement.value) videoElement.value.pause()

    // Save progress on pause
    if (currentTrack.value && (currentTrack.value.type === 'podcast' || currentTrack.value._type === 'podcast' || currentTrack.value.type === 'podcast-episode' || currentTrack.value.type === 'podcastEpisode')) {
      const a = getAudio()
      savePodcastProgress(currentTrack.value.id || currentTrack.value.key, a.currentTime)
    }

    endListeningSession()
  }

  function stop() {
    pause() // Pause and end session
    if (mode.value === 'audio') {
      const a = getAudio()
      a.currentTime = 0
    } else if (videoElement.value) {
      videoElement.value.currentTime = 0
    }
  }

  function togglePlay() {
    if (isPlaying.value) pause()
    else play()
  }

  function resume() { play() }

  function seek(percent) {
    const media = mode.value === 'audio' ? getAudio() : videoElement.value
    if (media && media.duration && isFinite(media.duration)) {
      trackEvent('media_seek', mediaAnalyticsProps({ percent }))
      media.currentTime = (percent / 100) * media.duration
    }
  }

  function seekTo(seconds) {
    const media = mode.value === 'audio' ? getAudio() : videoElement.value
    if (!media) return
    const target = Math.max(0, Number(seconds) || 0)
    trackEvent('media_seek', mediaAnalyticsProps({ seconds: target, mode: mode.value }))
    if (media.duration && isFinite(media.duration)) {
      media.currentTime = Math.min(target, media.duration)
    } else {
      media.currentTime = target
    }
  }

  function setQueue(tracks, startIndex = 0, options = {}) {
    queue.value = tracks
    if (options.source) playbackSource.value = options.source
    prefetchedSrcs.clear()
    if (tracks.length > startIndex) play(tracks[startIndex], options)
    prefetchUpcoming(2)
  }

  function toggleShuffle() { shuffle.value = !shuffle.value }
  function toggleRepeat() { repeat.value = !repeat.value }

  async function buildAutoplayQueue() {
    if (!currentTrack.value) return

    try {
      // Try to fetch same artist tracks
      const artistId = currentTrack.value.artist_id || currentTrack.value.artist
      if (artistId) {
        const resp = await apiFetch(`/api/artists/${artistId}/tracks`)
        const tracks = resp?.tracks || resp || []
        if (Array.isArray(tracks) && tracks.length > 0) {
          return tracks
        }
      }
    } catch (e) {
      console.warn('Failed to load artist tracks:', e)
    }

    // Fallback: fetch random tracks from library
    try {
      const resp = await apiFetch('/api/music?limit=50&random=true')
      const tracks = resp?.tracks || resp || []
      return Array.isArray(tracks) ? tracks : []
    } catch (e) {
      console.warn('Failed to load random tracks:', e)
      return []
    }
  }

  function next() {
    if (!currentTrack.value) return
    if (playbackSource.value === 'radio') return
    trackEvent('media_next', mediaAnalyticsProps())

    // If queue is empty, try autoplay
    if (!queue.value.length) {
      if (autoplayEnabled.value) {
        buildAutoplayQueue().then(tracks => {
          if (tracks.length > 0) {
            setQueue(tracks, 0)
          }
        })
      }
      return
    }

    const idx = queue.value.findIndex(t => (t.id === currentTrack.value.id) || (t.id === currentTrack.value.slug))
    if (shuffle.value && queue.value.length > 1) {
      let randomIdx
      do { randomIdx = Math.floor(Math.random() * queue.value.length) } while (randomIdx === idx)
      play(queue.value[randomIdx])
      return
    }
    if (idx < 0) {
      play(queue.value[0])
      return
    }
    const nextIdx = (idx + 1) % queue.value.length

    // Check if we're at the end of the queue
    if (nextIdx === 0) {
      // We've wrapped to the beginning — time to autoplay
      if (autoplayEnabled.value) {
        buildAutoplayQueue().then(tracks => {
          if (tracks.length > 0) {
            setQueue(tracks, 0)
          }
        })
      }
      return
    }

    play(queue.value[nextIdx])
  }

  function previous() {
    const media = mode.value === 'audio' ? getAudio() : videoElement.value
    if (!currentTrack.value) return
    if (playbackSource.value === 'radio') return
    trackEvent('media_previous', mediaAnalyticsProps())
    
    // Always rewind if past 3 seconds, or if there's no queue
    if ((media && media.currentTime > 3) || !queue.value || queue.value.length === 0) {
      if (media) media.currentTime = 0
      return
    }

    const idx = queue.value.findIndex(t => (t.id === currentTrack.value.id) || (t.id === currentTrack.value.slug))
    const prevIdx = idx > 0 ? idx - 1 : queue.value.length - 1
    play(queue.value[prevIdx])
  }

  function clearQueue() { queue.value = [] }

  function eject() {
    pause()
    if (mode.value === 'audio') {
      const a = getAudio()
      a.src = ''
      a.load()
    } else if (videoElement.value) {
      videoElement.value.src = ''
      videoElement.value.load()
    }
    currentTime.value = 0
    duration.value = 0
    loading.value = false
    currentTrack.value = null
    prefetchedSrcs.clear()
    if ('mediaSession' in navigator) navigator.mediaSession.metadata = null
  }

  function removeFromQueue(index) {
    queue.value = queue.value.filter((_, i) => i !== index)
  }

  function addToQueue(track) {
    queue.value = [...queue.value, track]
  }

  function isInQueue(track) {
    if (!track) return false
    const id = track.id ?? track.key
    return queue.value.some(t => (t.id ?? t.key) === id)
  }

  function saveLastPlayed(track) {
    try {
      localStorage.setItem('ahoy.lastPlayed', JSON.stringify({ track, timestamp: Date.now() }))
    } catch { /* ignore */ }
  }

  function restoreLastPlayed() {
    try {
      const raw = localStorage.getItem('ahoy.lastPlayed')
      if (raw) {
        const { track } = JSON.parse(raw)
        if (track && track.type !== 'live_tv') {
          const isVideo = !!(track.video_url || track.url?.endsWith('.mp4') || track._type === 'show' || track.type === 'live_tv')
          mode.value = isVideo ? 'video' : 'audio'
          currentTrack.value = track
          // Don't load audio on restore — wait until user hits play
          updateMediaSession(track)
        }
      }
    } catch { /* ignore */ }
  }

  // --- External Setters ---
  function setVideoElement(el) { 
    if (videoElement.value === el) return
    if (videoElement.value && videoElement.value !== el) {
      videoWatch.reset('video_element_replaced')
    }
    videoElement.value = el 
    if (el) {
      el.playbackRate = playbackRate.value
      videoWatch.bind(el)
      el.addEventListener('timeupdate', () => {
        if (mode.value === 'video') {
          currentTime.value = el.currentTime
          duration.value = el.duration
          updatePositionState()
        }
      })
    }
  }
  function setHeroBounds(bounds) { heroBounds.value = bounds }
  function toggleWidescreenPinned() { isWidescreenPinned.value = !isWidescreenPinned.value }

  function setAutoplay(enabled) {
    autoplayEnabled.value = enabled
  }

  // --- Global Watchers (Side Effects) ---
  watch([currentTrack, isPlaying], ([track, playing]) => {
    if (playing && track) {
      document.title = `${track.title || 'Track'} - ${track.artist || track.host || 'Unknown'}`
    } else {
      document.title = 'Ahoy Indie Media'
    }

    if (track) {
      updateMediaSession(track)
    }

    if ('mediaSession' in navigator) {
      navigator.mediaSession.playbackState = playing ? 'playing' : 'paused'
    }
  }, { immediate: true })

  return {
    currentTrack,
    isPlaying,
    loading,
    queue,
    currentTime,
    duration,
    progress,
    hasQueue,
    shuffle,
    repeat,
    volume,
    playbackRate,
    isMuted,
    mode,
    heroBounds,
    videoElement,
    autoplayEnabled,
    playbackSource,
    playbackDiagnostics,
    getAudio,
    play,
    pause,
    resume,
    togglePlay,
    seek,
    seekTo,
    setVolume,
    setPlaybackRate,
    toggleMute,
    skipBackward,
    skipForward,
    seekBackward,
    seekForward,
    seekBackward5,
    seekForward5,
    getSeekStep,
    setQueue,
    next,
    toggleShuffle,
    toggleRepeat,
    previous,
    clearQueue,
    removeFromQueue,
    addToQueue,
    isInQueue,
    eject,
    restoreLastPlayed,
    setVideoElement,
    setHeroBounds,
    isWidescreenPinned,
    toggleWidescreenPinned,
    setAutoplay,
    toggleFullscreen,
  }
})
