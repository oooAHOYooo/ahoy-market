/**
 * Add to queue — singleton modal state. Call open(track) from anywhere to show the modal.
 */
import { ref, readonly } from 'vue'
import { usePlayerStore } from '../stores/player'

const showModal = ref(false)
const trackToAdd = ref(null)

export function useAddToQueue() {
  const playerStore = usePlayerStore()

  function open(track) {
    if (!track) return
    trackToAdd.value = track
    showModal.value = true
  }

  function close() {
    showModal.value = false
    trackToAdd.value = null
  }

  function addToQueue() {
    if (!trackToAdd.value) return
    playerStore.addToQueue(trackToAdd.value)
    close()
    // Show toast notification
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: `Added "${trackToAdd.value.title}" to queue` } }))
  }

  return {
    showModal: readonly(showModal),
    trackToAdd: readonly(trackToAdd),
    open,
    close,
    addToQueue,
    playerStore,
  }
}
