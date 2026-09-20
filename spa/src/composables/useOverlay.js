import { ref } from 'vue'

const isNowPlayingOpen = ref(false)

function isIOSLargeViewport() {
  try {
    const platform = window.Capacitor?.getPlatform?.()
    const userAgent = navigator.userAgent || ''
    const isIPadOS = /iPad/.test(userAgent) || (navigator.platform === 'MacIntel' && navigator.maxTouchPoints > 1)
    const isIOS = platform === 'ios' || document.body.classList.contains('platform-ios') || isIPadOS
    return isIOS && window.innerWidth > 480
  } catch (_) {
    return false
  }
}

export function useOverlay() {
  const canOpenNowPlaying = () => !isIOSLargeViewport()

  const openNowPlaying = () => {
    if (!canOpenNowPlaying()) {
      isNowPlayingOpen.value = false
      return
    }
    isNowPlayingOpen.value = true
  }

  const closeNowPlaying = () => {
    isNowPlayingOpen.value = false
  }

  const toggleNowPlaying = () => {
    if (isNowPlayingOpen.value) {
      closeNowPlaying()
    } else {
      openNowPlaying()
    }
  }

  return {
    isNowPlayingOpen,
    canOpenNowPlaying,
    openNowPlaying,
    closeNowPlaying,
    toggleNowPlaying
  }
}
