/**
 * Native feature composables — things that were impossible with Flask/Jinja.
 * Uses Web APIs that work in both browsers and Capacitor WebViews.
 * When Capacitor plugins are installed later, these can be swapped to native calls.
 */

import { musicUrl, videoUrl } from '../utils/urls'
import { publicOrigin } from './useSeoMeta'

// ── Native Share ────────────────────────────────────────────────────
// Flask couldn't do this: the OS share sheet (contacts, messages, AirDrop, etc.)
export function useShare() {
  const canShare = 'share' in navigator
  const origin = publicOrigin()

  async function share({ title, text, url }) {
    if (!canShare) {
      // Fallback: copy to clipboard
      try {
        await navigator.clipboard.writeText(url || text || title)
        return { shared: false, copied: true }
      } catch {
        return { shared: false, copied: false }
      }
    }
    try {
      await navigator.share({ title, text, url })
      return { shared: true }
    } catch (err) {
      if (err.name === 'AbortError') return { shared: false, cancelled: true }
      return { shared: false }
    }
  }

  function shareTrack(track) {
    return share({
      title: `${track.title} — ${track.artist || 'Ahoy Indie Media'}`,
      text: `Listen to "${track.title}" on Ahoy Indie Media`,
      url: `${origin}${musicUrl(track)}`,
    })
  }

  function shareArtist(artist) {
    return share({
      title: `${artist.name} on Ahoy Indie Media`,
      text: `Check out ${artist.name} on Ahoy Indie Media`,
      url: `${origin}/artists/${artist.slug || artist.id}`,
    })
  }

  function shareShow(show) {
    return share({
      title: `${show.title} — Ahoy Indie Media`,
      text: `Watch "${show.title}" on Ahoy Indie Media`,
      url: `${origin}${videoUrl(show)}`,
    })
  }

  function sharePodcast(show) {
    return share({
      title: `${show.title} — Ahoy Indie Media`,
      text: `Listen to "${show.title}" podcast on Ahoy Indie Media`,
      url: `${origin}/podcasts/${show.slug}`,
    })
  }

  function shareEvent(event) {
    return share({
      title: `${event.title} — Ahoy Indie Media`,
      text: `${event.title}${event.date ? ' · ' + event.date : ''}${event.venue ? ' · ' + event.venue : ''}`,
      url: `${origin}/events/${event.id}`,
    })
  }

  return { canShare, share, shareTrack, shareArtist, shareShow, sharePodcast, shareEvent }
}

// ── Haptic Feedback ─────────────────────────────────────────────────
// Flask had zero haptics. Now taps feel physical.
export function useHaptics() {
  const canVibrate = 'vibrate' in navigator

  function light() {
    if (canVibrate) navigator.vibrate(10)
  }

  function medium() {
    if (canVibrate) navigator.vibrate(25)
  }

  function heavy() {
    if (canVibrate) navigator.vibrate([30, 20, 50])
  }

  // Specific interaction haptics
  function onPlay() { light() }
  function onBookmark() { medium() }
  function onNavigate() { light() }
  function onError() { heavy() }
  function onQueue() { if (canVibrate) navigator.vibrate(8) }      // lighter than bookmark
  function onSkip() { if (canVibrate) navigator.vibrate(15) }      // next/previous
  function onRemove() { if (canVibrate) navigator.vibrate([10, 10, 10]) } // double-tap pattern
  function onToggle() { light() }      // shuffle, repeat, mute
  function onBoost() { medium() }      // boost button
  function onVolumeChange() { if (canVibrate) navigator.vibrate(5) } // subtle volume feedback

  return { canVibrate, light, medium, heavy, onPlay, onBookmark, onNavigate, onError, onQueue, onSkip, onRemove, onToggle, onBoost, onVolumeChange }
}

// ── Screen Wake Lock ────────────────────────────────────────────────
// Flask: screen would dim and lock during playback. Now it stays on.
let wakeLock = null

export function useWakeLock() {
  const isSupported = 'wakeLock' in navigator

  async function request() {
    if (!isSupported) return false
    try {
      wakeLock = await navigator.wakeLock.request('screen')
      wakeLock.addEventListener('release', () => { wakeLock = null })
      return true
    } catch {
      return false
    }
  }

  async function release() {
    if (wakeLock) {
      await wakeLock.release()
      wakeLock = null
    }
  }

  // Re-acquire on visibility change (screen locks release when tab is hidden)
  function autoReacquire() {
    document.addEventListener('visibilitychange', async () => {
      if (document.visibilityState === 'visible' && !wakeLock) {
        await request()
      }
    })
  }

  return { isSupported, request, release, autoReacquire }
}

// ── Sleep Timer ─────────────────────────────────────────────────────
// Flask couldn't do this. Stop playback after N minutes (bedtime listening).
let sleepTimerId = null
let sleepCallback = null

export function useSleepTimer() {
  function start(minutes, onSleep) {
    clear()
    sleepCallback = onSleep
    sleepTimerId = setTimeout(() => {
      if (sleepCallback) sleepCallback()
      sleepTimerId = null
    }, minutes * 60 * 1000)
  }

  function clear() {
    if (sleepTimerId) {
      clearTimeout(sleepTimerId)
      sleepTimerId = null
    }
    sleepCallback = null
  }

  function isActive() {
    return sleepTimerId !== null
  }

  return { start, clear, isActive }
}

// ── Orientation ──────────────────────────────────────────────────────
// Lock the app to portrait so phones never fall into the desktop-like
// landscape layout. Requires @capacitor/screen-orientation plugin.

export function useOrientation() {
  const isCapacitor = window.Capacitor !== undefined

  function getWebOrientationApi() {
    if (typeof screen === 'undefined') return null
    return screen.orientation || screen.mozOrientation || screen.msOrientation || null
  }

  async function lockPortrait() {
    const webOrientation = getWebOrientationApi()
    if (!isCapacitor && !webOrientation?.lock) return
    try {
      if (isCapacitor) {
        const { ScreenOrientation } = await import('@capacitor/screen-orientation')
        await ScreenOrientation.lock({ orientation: 'portrait' })
        return
      }

      await webOrientation.lock('portrait')
    } catch (e) {
      console.warn('[Orientation] Lock portrait failed:', e)
    }
  }

  async function unlock() {
    const webOrientation = getWebOrientationApi()
    if (!isCapacitor && !webOrientation?.unlock) return
    try {
      if (isCapacitor) {
        const { ScreenOrientation } = await import('@capacitor/screen-orientation')
        // Unlocks and lets the OS handle rotation via sensors
        await ScreenOrientation.unlock()
        return
      }

      webOrientation.unlock()
    } catch (e) {
      console.warn('[Orientation] Unlock failed:', e)
    }
  }

  return { lockPortrait, unlock }
}
