<template>
  <Teleport to="body">
    <TransitionGroup name="toast" tag="div" class="toast-container">
      <div
        v-for="toast in toasts"
        :key="toast.id"
        class="toast-item"
        :class="[toast.type, { 'has-link': toast.link }]"
        @click="navigate(toast)"
      >
        <i :class="iconFor(toast.type)" class="toast-icon"></i>
        <span class="toast-message">{{ toast.message }}</span>
        <i v-if="toast.link" class="fas fa-chevron-right toast-link-arrow"></i>
      </div>
    </TransitionGroup>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'

const toasts = ref([])
let nextId = 0
const router = useRouter()

function iconFor(type) {
  switch (type) {
    case 'success': return 'fas fa-check-circle'
    case 'error': return 'fas fa-exclamation-circle'
    case 'bookmark': return 'fas fa-bookmark'
    case 'share': return 'fas fa-share-alt'
    case 'play': return 'fas fa-play'
    case 'update': return 'fas fa-arrow-up-circle'
    case 'podcast': return 'fas fa-microphone'
    case 'video': return 'fas fa-film'
    case 'artist': return 'fas fa-user-music'
    default: return 'fas fa-info-circle'
  }
}

function show(message, type = 'info', durationMs = 2500, link = null) {
  const id = ++nextId
  toasts.value.push({ id, message, type, link })
  setTimeout(() => {
    toasts.value = toasts.value.filter(t => t.id !== id)
  }, durationMs)
}

function navigate(toast) {
  if (!toast.link) return
  toasts.value = toasts.value.filter(t => t.id !== toast.id)
  router.push(toast.link)
}

defineExpose({ show })

// Also make it available via a custom event for non-component code
function onToastEvent(e) {
  const { message, type, duration, link } = e.detail || {}
  show(message || '', type, duration, link)
}

onMounted(() => window.addEventListener('ahoy:toast', onToastEvent))
onUnmounted(() => window.removeEventListener('ahoy:toast', onToastEvent))
</script>

<style scoped>
:root {
  --system-red: #ff3b30;
  --system-orange: #ff9500;
  --system-blue: #007aff;
  --system-teal: #30b0c0;
  --system-green: #34c759;
  --toast-bg-primary: rgba(0,0,0,0.8);
  --toast-bg-secondary: rgba(20,20,20,0.85);
  --toast-text-primary: #ffffff;
  --toast-text-secondary: rgba(255,255,255,0.7);
  --toast-border: rgba(255,255,255,0.1);
}

@media (prefers-color-scheme: light) {
  :root {
    --toast-bg-primary: rgba(242,242,247,0.95);
    --toast-bg-secondary: rgba(255,255,255,0.9);
    --toast-text-primary: #000000;
    --toast-text-secondary: rgba(0,0,0,0.6);
    --toast-border: rgba(0,0,0,0.08);
  }
}

.toast-container {
  position: fixed;
  top: env(safe-area-inset-top, 12px);
  left: 16px;
  right: 16px;
  z-index: 100000;
  display: flex;
  flex-direction: column;
  gap: 8px;
  pointer-events: none;
  padding-top: 12px;
}

.toast-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 16px;
  border-radius: 12px;
  font-size: 15px;
  line-height: 1.4;
  font-weight: 500;
  color: var(--toast-text-primary);
  background: var(--toast-bg-primary);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--toast-border);
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  pointer-events: auto;
  overflow: hidden;
}

@media (prefers-color-scheme: light) {
  .toast-item {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }
}

.toast-icon {
  font-size: 18px;
  flex-shrink: 0;
}

.toast-item.success .toast-icon { color: #34c759; }
.toast-item.error .toast-icon { color: #ff3b30; }
.toast-item.bookmark .toast-icon { color: #30b0c0; }
.toast-item.share .toast-icon { color: #007aff; }
.toast-item.play .toast-icon { color: #30b0c0; }

.toast-item.update {
  background: var(--toast-bg-secondary);
  border-left: 4px solid var(--system-orange);
}
.toast-item.update .toast-icon { color: var(--system-orange); }

.toast-item.podcast {
  background: var(--toast-bg-secondary);
  border-left: 4px solid var(--system-blue);
}
.toast-item.podcast .toast-icon { color: var(--system-blue); }

.toast-item.video {
  background: var(--toast-bg-secondary);
  border-left: 4px solid var(--system-teal);
}
.toast-item.video .toast-icon { color: var(--system-teal); }

.toast-item.artist {
  background: var(--toast-bg-secondary);
  border-left: 4px solid var(--system-green);
}
.toast-item.artist .toast-icon { color: var(--system-green); }

.toast-message { flex: 1; }

.toast-item.has-link { cursor: pointer; transition: background 0.15s ease, box-shadow 0.15s ease; }

.toast-item.has-link:hover {
  background: color-mix(in srgb, var(--toast-bg-primary) 85%, white 15%);
  box-shadow: 0 10px 28px rgba(0,0,0,0.2);
}

.toast-item.has-link:active {
  transform: scale(0.985);
}

.toast-item.has-link:hover .toast-link-arrow {
  opacity: 1;
  transform: translateX(2px);
}

.toast-link-arrow {
  font-size: 12px;
  opacity: 0.5;
  flex-shrink: 0;
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.toast-enter-active { animation: toast-slide-in 0.3s ease-out; }
.toast-leave-active { transition: all 0.25s ease; }
.toast-leave-to { opacity: 0; transform: translateY(-10px) scale(0.98); }

@keyframes toast-slide-in {
  from {
    opacity: 0;
    transform: translateY(-16px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .toast-enter-active {
    animation: none;
    opacity: 1;
  }
}
</style>
