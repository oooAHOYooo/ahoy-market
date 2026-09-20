const WATCH_MILESTONES = [25, 50, 75]

function safeRoundSeconds(value) {
  const n = Number(value)
  return Number.isFinite(n) ? Math.max(0, Math.round(n)) : null
}

function makeSessionId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `watch-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`
}

function buildSourceKey(meta = {}, media = null) {
  return [
    meta.video_id || meta.content_id || meta.track_id || meta.media_id || '',
    meta.path || meta.route || '',
    meta.video_title || meta.title || '',
    meta.video_url || meta.src || media?.currentSrc || media?.src || '',
  ].join('|')
}

export function useVideoWatchAnalytics(trackEvent, getMeta = () => ({})) {
  const state = {
    sessionId: '',
    started: false,
    startedAt: 0,
    lastTickAt: 0,
    watchedMs: 0,
    milestones: new Set(),
    sourceKey: '',
    cleanup: null,
    attachedEl: null,
  }

  function snapshot(media, extra = {}) {
    const meta = typeof getMeta === 'function' ? (getMeta(media) || {}) : {}
    const durationSeconds = safeRoundSeconds(media?.duration ?? meta.duration_seconds)
    const currentTimeSeconds = safeRoundSeconds(media?.currentTime) ?? 0
    const progressPercent = durationSeconds && durationSeconds > 0
      ? Math.max(0, Math.min(100, Math.round((currentTimeSeconds / durationSeconds) * 100)))
      : null

    return {
      ...meta,
      watch_session_id: state.sessionId || null,
      duration_seconds: durationSeconds,
      current_time_seconds: currentTimeSeconds,
      progress_percent: progressPercent,
      watched_seconds: Math.max(0, Math.round(state.watchedMs / 1000)),
      watched_ms: Math.max(0, Math.round(state.watchedMs)),
      ...extra,
    }
  }

  function clearSession() {
    state.sessionId = ''
    state.started = false
    state.startedAt = 0
    state.lastTickAt = 0
    state.watchedMs = 0
    state.milestones = new Set()
    state.sourceKey = ''
  }

  function accumulate(media) {
    if (!state.started) return
    const now = Date.now()
    if (state.lastTickAt) {
      state.watchedMs += Math.max(0, now - state.lastTickAt)
    }
    state.lastTickAt = now

    const snap = snapshot(media)
    const percent = snap.progress_percent
    if (percent == null) return

    for (const milestone of WATCH_MILESTONES) {
      if (percent >= milestone && !state.milestones.has(milestone)) {
        state.milestones.add(milestone)
        trackEvent('video_watch_progress', {
          ...snap,
          milestone_percent: milestone,
        })
      }
    }
  }

  function begin(media) {
    const meta = typeof getMeta === 'function' ? (getMeta(media) || {}) : {}
    const sourceKey = buildSourceKey(meta, media)

    if (state.started && state.sourceKey && state.sourceKey !== sourceKey) {
      finish(media, 'source_change', false)
    }

    if (state.started && state.sourceKey === sourceKey) {
      state.lastTickAt = Date.now()
      return
    }

    state.sessionId = makeSessionId()
    state.started = true
    state.startedAt = Date.now()
    state.lastTickAt = state.startedAt
    state.watchedMs = 0
    state.milestones = new Set()
    state.sourceKey = sourceKey

    trackEvent('video_watch_start', {
      ...snapshot(media, { watch_reason: 'start' }),
      watch_source: 'video',
    })
  }

  function finish(media, reason = 'pause', completed = false) {
    if (!state.started) return

    accumulate(media)
    const eventName = completed ? 'video_watch_complete' : 'video_watch_stop'

    trackEvent(eventName, {
      ...snapshot(media, {
        watch_reason: reason,
        watch_completed: completed,
      }),
      watch_source: 'video',
    })

    clearSession()
  }

  function onPlay(media) {
    begin(media)
  }

  function onTimeUpdate(media) {
    accumulate(media)
  }

  function onPause(media) {
    finish(media, 'pause', false)
  }

  function onEnded(media) {
    finish(media, 'ended', true)
  }

  function bind(mediaElement) {
    if (state.cleanup) {
      state.cleanup()
      state.cleanup = null
    }

    state.attachedEl = mediaElement || null
    if (!mediaElement) return

    const handlePlay = () => onPlay(mediaElement)
    const handleTimeUpdate = () => onTimeUpdate(mediaElement)
    const handlePause = () => onPause(mediaElement)
    const handleEnded = () => onEnded(mediaElement)
    const handleSeeking = () => accumulate(mediaElement)

    mediaElement.addEventListener('play', handlePlay)
    mediaElement.addEventListener('timeupdate', handleTimeUpdate)
    mediaElement.addEventListener('pause', handlePause)
    mediaElement.addEventListener('ended', handleEnded)
    mediaElement.addEventListener('seeking', handleSeeking)

    state.cleanup = () => {
      mediaElement.removeEventListener('play', handlePlay)
      mediaElement.removeEventListener('timeupdate', handleTimeUpdate)
      mediaElement.removeEventListener('pause', handlePause)
      mediaElement.removeEventListener('ended', handleEnded)
      mediaElement.removeEventListener('seeking', handleSeeking)
      if (state.started) {
        finish(mediaElement, 'detach', false)
      }
    }
  }

  function reset(reason = 'reset') {
    if (state.started) {
      finish(state.attachedEl, reason, false)
    } else {
      clearSession()
    }
  }

  return {
    bind,
    reset,
    destroy() {
      if (state.cleanup) {
        state.cleanup()
        state.cleanup = null
      }
      state.attachedEl = null
      clearSession()
    },
    onPlay,
    onTimeUpdate,
    onPause,
    onEnded,
  }
}
