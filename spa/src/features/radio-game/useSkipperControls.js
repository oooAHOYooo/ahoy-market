import { onMounted, onUnmounted, reactive } from 'vue'

const HOLD_CHARGE_MS = 520

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

export function useSkipperControls(surfaceRef, { enabled, onPulse } = {}) {
  const controlIntent = reactive({
    source: 'mouse',
    jumpToken: 0,
    isActive: false,
    clickX: 0.5,
    clickY: 0.5,
    charge: 0,
  })

  let activeTimer = null
  let chargeFrame = 0
  let pointerDownAt = 0
  let isPointerDown = false

  function isEnabled() {
    return typeof enabled?.value === 'boolean' ? enabled.value : true
  }

  function getBounds() {
    return surfaceRef.value?.getBoundingClientRect?.() || null
  }

  function trigger(source = 'mouse', event = null) {
    if (!isEnabled()) return
    controlIntent.source = source
    controlIntent.jumpToken += 1
    controlIntent.isActive = true
    const bounds = getBounds()
    if (bounds && event) {
      controlIntent.clickX = clamp((event.clientX - bounds.left) / bounds.width, 0, 1)
      controlIntent.clickY = clamp((event.clientY - bounds.top) / bounds.height, 0, 1)
    }
    onPulse?.('flip', { source })

    if (activeTimer) window.clearTimeout(activeTimer)
    activeTimer = window.setTimeout(() => {
      controlIntent.isActive = false
    }, 180)
  }

  function startCharge() {
    if (chargeFrame) window.cancelAnimationFrame(chargeFrame)
    const startedAt = pointerDownAt
    const tick = () => {
      if (!isPointerDown || startedAt !== pointerDownAt) return
      const elapsed = performance.now() - pointerDownAt
      controlIntent.charge = clamp(elapsed / HOLD_CHARGE_MS, 0, 1)
      chargeFrame = window.requestAnimationFrame(tick)
    }
    chargeFrame = window.requestAnimationFrame(tick)
  }

  function endCharge() {
    isPointerDown = false
    if (chargeFrame) window.cancelAnimationFrame(chargeFrame)
    chargeFrame = 0
    controlIntent.charge = 0
  }

  function handlePointerDown(event) {
    if (event.button != null && event.button !== 0) return
    event.preventDefault()
    isPointerDown = true
    pointerDownAt = performance.now()
    const source = event.pointerType === 'touch' ? 'touch' : 'mouse'
    trigger(source, event)
    startCharge()
  }

  function handlePointerMove() {}
  function handlePointerUp() { endCharge() }
  function handlePointerCancel() { endCharge() }
  function handlePointerLeave() {}

  function handleKeyDown(event) {
    if (event.code !== 'Space' && event.key !== 'Enter') return
    event.preventDefault()
    trigger('keyboard')
  }

  onMounted(() => {
    window.addEventListener('keydown', handleKeyDown, { passive: false })
  })

  onUnmounted(() => {
    if (activeTimer) window.clearTimeout(activeTimer)
    if (chargeFrame) window.cancelAnimationFrame(chargeFrame)
    window.removeEventListener('keydown', handleKeyDown)
  })

  return {
    controlIntent,
    handlePointerDown,
    handlePointerMove,
    handlePointerUp,
    handlePointerCancel,
    handlePointerLeave,
  }
}
