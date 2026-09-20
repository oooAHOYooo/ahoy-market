<template>
  <button
    class="fractal-toggle"
    :class="{ 'is-active': isFractal }"
    type="button"
    :aria-pressed="isFractal"
    aria-label="Toggle Fractal Glass theme"
    title="Toggle Fractal Glass theme"
    @click="toggle"
  >
    <span class="fractal-toggle__dot"></span>
    <span class="fractal-toggle__label">{{ isFractal ? 'Fractal' : 'FX' }}</span>
  </button>
</template>

<script setup>
import { ref, watch, onMounted, onBeforeUnmount } from 'vue'

const STORAGE_KEY = 'ahoyFractalTheme'
const isFractal = ref(false)

function apply(active) {
  const root = document.documentElement
  if (active) {
    root.setAttribute('data-theme', 'fractal')
  } else if (root.getAttribute('data-theme') === 'fractal') {
    root.removeAttribute('data-theme')
  }
}

function toggle() {
  isFractal.value = !isFractal.value
}

watch(isFractal, (active) => {
  apply(active)
  try { localStorage.setItem(STORAGE_KEY, active ? '1' : '0') } catch (_) { /* private mode */ }
})

onMounted(() => {
  let saved = '0'
  try { saved = localStorage.getItem(STORAGE_KEY) || '0' } catch (_) { /* private mode */ }
  if (saved === '1') {
    isFractal.value = true
    apply(true)
  }
})

onBeforeUnmount(() => {
  apply(false)
})
</script>

<style scoped>
.fractal-toggle {
  position: fixed;
  top: 12px;
  right: 12px;
  z-index: 9999;

  display: inline-flex;
  align-items: center;
  gap: 6px;

  padding: 6px 10px;
  border-radius: 999px;

  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;

  background: rgba(12, 14, 18, 0.55);
  color: rgba(255, 255, 255, 0.85);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35);

  cursor: pointer;
  user-select: none;
  transition: background 0.2s ease, border-color 0.2s ease, transform 0.15s ease;
}

.fractal-toggle:hover {
  transform: translateY(-1px);
}

.fractal-toggle.is-active {
  background: rgba(36, 47, 73, 0.78);
  color: #FFA586;
  border-color: rgba(255, 165, 134, 0.55);
  box-shadow: 0 6px 24px rgba(181, 26, 43, 0.28);
}

.fractal-toggle__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.4);
  transition: background 0.2s ease, box-shadow 0.2s ease;
}

.fractal-toggle.is-active .fractal-toggle__dot {
  background: #FFA586;
  box-shadow: 0 0 8px rgba(255, 165, 134, 0.65);
}

@media (max-width: 480px) {
  .fractal-toggle {
    top: 8px;
    right: 8px;
    padding: 5px 8px;
    font-size: 10px;
  }
}
</style>
