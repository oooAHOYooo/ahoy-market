import { ref, computed } from 'vue'

/**
 * Casting strategies - pluggable casting methods
 * Each strategy must implement: { name, icon, description, isAvailable(), cast(metadata), stop() }
 */

const LEGACY_CAST_ENABLED = false

export const ReceiverTabStrategy = {
  name: 'Receiver Tab',
  icon: 'fas fa-external-link-square-alt',
  description: 'Open in another window or device',

  isAvailable() {
    return true // Always available
  },

  async cast(metadata) {
    if (!metadata?.url) throw new Error('No stream URL provided')
    const params = new URLSearchParams({
      url: metadata.url,
      title: metadata.title || 'Playing',
      image: metadata.image || '',
      startTime: metadata.startTime || 0,
    })
    window.open(`/cast/receiver?${params.toString()}`, 'ahoy-receiver', 'width=800,height=600')
  },

  async stop() {
    // Nothing to do - receiver tab is independent
  },
}

export const GoogleCastStrategy = {
  name: 'Google Cast',
  icon: 'fas fa-tv',
  description: 'Chromecast, Android TV, Cast-enabled TV',

  isAvailable() {
    return typeof cast !== 'undefined' &&
           !!cast.framework &&
           !!cast.framework.CastContext
  },

  async cast(metadata) {
    const castContext = cast.framework.CastContext.getInstance()

    // Opens native Cast device picker dialog
    const result = await castContext.requestSession()
    if (result !== cast.framework.CastContextEventType.SESSION_STARTED) {
      throw new Error('Cast session not started')
    }

    const session = castContext.getCurrentSession()
    if (!session) throw new Error('No cast session')

    // Detect content type
    const url = metadata.url || ''
    const isVideo = /\.(mp4|webm|ogg|m3u8)(\?|$)/i.test(url)
    const contentType = isVideo ? 'video/mp4' : 'audio/mpeg'

    const mediaInfo = new chrome.cast.media.MediaInfo(url, contentType)

    const trackMeta = new chrome.cast.media.MusicTrackMediaMetadata()
    trackMeta.title = metadata.title || 'Playing'
    if (metadata.image) {
      trackMeta.images = [new chrome.cast.Image(metadata.image)]
    }
    mediaInfo.metadata = trackMeta

    const request = new chrome.cast.media.LoadRequest(mediaInfo)
    if (metadata.startTime) {
      request.currentTime = metadata.startTime
    }

    await session.loadMedia(request)
  },

  async stop() {
    const castContext = cast.framework.CastContext.getInstance()
    await castContext.endCurrentSession(true)
  },
}

export const AirPlayStrategy = {
  name: 'AirPlay',
  icon: 'fab fa-apple',
  description: 'Apple TV, Mac, iPhone',

  isAvailable() {
    // Check for Safari/WebKit AirPlay support
    if (typeof window === 'undefined') return false
    return !!window.WebKitPlaybackTargetAvailabilityEvent ||
           (window.safari && window.safari.messageHandlers)
  },

  async cast(metadata) {
    // AirPlay is handled by browser natively when video element has proper attributes
    // We just show a message to the user
    throw new Error('Use the native AirPlay button that appears on your device')
  },

  async stop() {
    // Browser handles this
  },
}

export const DirectDeviceStrategy = {
  name: 'Direct Device',
  icon: 'fas fa-qrcode',
  description: 'Open on Xbox, Smart TV, or any device',

  isAvailable() {
    return true // Always available
  },

  async cast(metadata) {
    // Return a special signal that UI should show QR code
    throw new Error('SHOW_QR_CODE')
  },

  async stop() {
    // Nothing to do
  },
}

/**
 * useCasting() - Main casting composable
 * Manages available casting methods and handles casting lifecycle
 */
export function useCasting() {
  const strategies = ref(LEGACY_CAST_ENABLED ? [
    ReceiverTabStrategy,
    GoogleCastStrategy,
    AirPlayStrategy,
    DirectDeviceStrategy,
  ] : [])

  const availableStrategies = computed(() => {
    return strategies.value.filter(s => s.isAvailable())
  })

  const isCastingAvailable = computed(() => {
    return LEGACY_CAST_ENABLED && availableStrategies.value.length > 0
  })

  const selectedStrategy = ref(null)
  const isCasting = ref(false)
  const castingError = ref(null)
  const currentMetadata = ref(null)

  async function startCast(strategy, metadata) {
    try {
      castingError.value = null
      if (metadata.url || metadata.title) {
        currentMetadata.value = metadata
      }
      await strategy.cast(metadata)
      selectedStrategy.value = strategy
      isCasting.value = true
    } catch (e) {
      const errorMsg = e.message || `${strategy.name} casting failed`
      if (errorMsg === 'SHOW_QR_CODE') {
        castingError.value = 'QR_CODE'
      } else {
        castingError.value = errorMsg
        console.error(`${strategy.name} casting failed:`, e)
      }
      throw e
    }
  }

  async function stopCast() {
    if (selectedStrategy.value) {
      await selectedStrategy.value.stop()
      selectedStrategy.value = null
      isCasting.value = false
      currentMetadata.value = null
      castingError.value = null
    }
  }

  function clearError() {
    castingError.value = null
  }

  return {
    strategies: computed(() => strategies.value),
    availableStrategies,
    isCastingAvailable,
    selectedStrategy,
    isCasting,
    castingError,
    currentMetadata,
    startCast,
    stopCast,
    clearError,
  }
}
