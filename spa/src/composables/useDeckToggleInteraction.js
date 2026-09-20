import { ref } from 'vue'

export function useDeckToggleInteraction({ onToggle, onSwipeToggle } = {}) {
  const pointerActive = ref(false)
  const swipeTriggered = ref(false)
  const suppressClick = ref(false)
  const startX = ref(0)
  const startY = ref(0)

  function runToggle(btn) {
    if (!btn) return
    btn.classList.add('switching')
    window.setTimeout(() => btn.classList.remove('switching'), 140)
    onToggle?.()
  }

  function onClick(e) {
    if (suppressClick.value) {
      suppressClick.value = false
      return
    }
    runToggle(e.currentTarget)
  }

  function onPointerDown(e) {
    pointerActive.value = true
    startX.value = e.clientX
    startY.value = e.clientY
  }

  function onPointerMove(e) {
    if (!pointerActive.value) return
    const dx = e.clientX - startX.value
    const dy = e.clientY - startY.value
    if (Math.abs(dx) < 12 || Math.abs(dx) < Math.abs(dy)) return
    pointerActive.value = false
    swipeTriggered.value = true
    suppressClick.value = true
    onSwipeToggle?.()
  }

  function onPointerUp(e) {
    if (!swipeTriggered.value) {
      runToggle(e.currentTarget)
      suppressClick.value = true
    }
    pointerActive.value = false
    swipeTriggered.value = false
  }

  function onPointerCancel() {
    pointerActive.value = false
    swipeTriggered.value = false
  }

  return {
    onClick,
    onPointerDown,
    onPointerMove,
    onPointerUp,
    onPointerCancel,
  }
}
