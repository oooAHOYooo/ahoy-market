/**
 * Keyboard shortcuts for player control
 * Space: play/pause
 * Arrow Right: seek forward
 * Arrow Left: seek backward
 * Shift + Arrow keys: track navigation
 * F: fullscreen / player overlay
 */

import { usePlayerStore } from '../stores/player'

export function useKeyboard() {
  const playerStore = usePlayerStore()

  function handleKeyDown(e) {
    // Don't trigger if focused on input/textarea
    if (e.target.matches('input, textarea')) return

    if (e.shiftKey && e.code === 'ArrowLeft') {
      e.preventDefault()
      playerStore.previous()
      return
    }
    if (e.shiftKey && e.code === 'ArrowRight') {
      e.preventDefault()
      playerStore.next()
      return
    }

    switch (e.code) {
      case 'Space':
        e.preventDefault()
        playerStore.togglePlay()
        break
      case 'KeyF':
        e.preventDefault()
        playerStore.toggleFullscreen?.()
        break
      case 'ArrowRight':
        e.preventDefault()
        playerStore.seekForward?.()
        break
      case 'ArrowLeft':
        e.preventDefault()
        playerStore.seekBackward?.()
        break
    }
  }

  function enable() {
    window.addEventListener('keydown', handleKeyDown)
  }

  function disable() {
    window.removeEventListener('keydown', handleKeyDown)
  }

  return { enable, disable }
}
