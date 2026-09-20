<template>
  <Teleport to="body">
    <Transition name="overlay-fade">
      <div v-if="isOpen" class="notification-overlay" @click.self="close">
        <div class="notification-panel">
          <div class="notification-header">
            <h3>Notifications</h3>
            <button class="close-btn" @click="close" aria-label="Close">
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="notification-list">
            <div v-if="notifications.length === 0" class="notification-empty">
              No notifications yet
            </div>
            <div
              v-for="notif in notifications"
              :key="notif.id"
              class="notification-item"
              :class="[notif.type, { unread: !notif.read }, { 'has-link': notif.link }]"
              @click="navigate(notif)"
            >
              <i :class="iconFor(notif.type)" class="notif-icon"></i>
              <div class="notif-content">
                <p class="notif-message">{{ notif.message }}</p>
                <span class="notif-time">{{ formatTime(notif.timestamp) }}</span>
              </div>
              <i v-if="notif.link" class="fas fa-chevron-right notif-link-arrow" aria-hidden="true"></i>
              <button class="notif-dismiss" @click.stop="remove(notif.id)" aria-label="Dismiss">
                <i class="fas fa-times"></i>
              </button>
            </div>
          </div>
          <div v-if="notifications.length > 0" class="notification-footer">
            <button @click="clearAll" class="clear-all-btn">Clear all</button>
          </div>
          <button
            class="notification-grabber"
            type="button"
            aria-label="Close notifications"
            @click="close"
            @touchstart.passive="startSwipe"
            @touchend.passive="endSwipe"
          >
            <span aria-hidden="true"></span>
          </button>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { watch } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationCenter } from '../composables/useNotificationCenter'

const { notifications, removeNotification, clearAll: centerClearAll, markAllRead } = useNotificationCenter()
const router = useRouter()

const props = defineProps({
  isOpen: { type: Boolean, default: false },
})

const emit = defineEmits(['close'])
let swipeStartY = 0
let swipeStartX = 0

watch(() => props.isOpen, (isOpen) => {
  if (isOpen) markAllRead()
})

function close() {
  emit('close')
}

function navigate(notif) {
  if (!notif.link) return
  close()
  router.push(notif.link)
}

function remove(id) {
  removeNotification(id)
}

function clearAll() {
  centerClearAll()
  close()
}

function startSwipe(event) {
  const touch = event.changedTouches?.[0]
  if (!touch) return
  swipeStartY = touch.clientY
  swipeStartX = touch.clientX
}

function endSwipe(event) {
  const touch = event.changedTouches?.[0]
  if (!touch) return
  const deltaY = touch.clientY - swipeStartY
  const deltaX = touch.clientX - swipeStartX

  if (deltaY < -36 && Math.abs(deltaY) > Math.abs(deltaX) * 1.2) {
    close()
  }
}

function iconFor(type) {
  switch (type) {
    case 'success': return 'fas fa-check-circle'
    case 'error': return 'fas fa-exclamation-circle'
    case 'video': return 'fas fa-film'
    case 'podcast': return 'fas fa-microphone'
    case 'artist': return 'fas fa-user-music'
    case 'music': return 'fas fa-music'
    case 'events': return 'fas fa-calendar'
    default: return 'fas fa-bell'
  }
}

function formatTime(timestamp) {
  const now = new Date()
  const diff = now - timestamp
  const minutes = Math.floor(diff / 60000)
  const hours = Math.floor(diff / 3600000)
  const days = Math.floor(diff / 86400000)

  if (minutes < 1) return 'just now'
  if (minutes < 60) return `${minutes}m ago`
  if (hours < 24) return `${hours}h ago`
  return `${days}d ago`
}
</script>

<style scoped>
.notification-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 50000;
  display: flex;
  align-items: flex-start;
  justify-content: flex-end;
}

.notification-panel {
  background: var(--bg-primary, #1a1a1a);
  width: 100%;
  max-width: 400px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  box-shadow: -2px 0 12px rgba(0, 0, 0, 0.3);
  animation: slide-in 0.3s ease-out;
  z-index: 50001;
}

@keyframes slide-in {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.notification-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.notification-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary, #fff);
}

.close-btn {
  background: none;
  border: none;
  color: var(--text-secondary, rgba(255, 255, 255, 0.6));
  font-size: 20px;
  cursor: pointer;
  padding: 4px 8px;
}

.close-btn:hover {
  color: var(--text-primary, #fff);
}

.notification-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
  scroll-behavior: smooth;
}

.notification-list::-webkit-scrollbar {
  width: 6px;
}

.notification-list::-webkit-scrollbar-track {
  background: transparent;
}

.notification-list::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 3px;
}

.notification-list::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.25);
}

.notification-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.5));
  font-size: 14px;
}

.notification-item {
  position: relative;
  display: grid;
  grid-template-columns: 24px minmax(0, 1fr) 28px;
  align-items: start;
  gap: 12px;
  padding: 12px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: var(--text-primary, #fff);
  transition: background 0.2s, border-color 0.2s;
}

.notification-item:hover {
  background: rgba(255, 255, 255, 0.05);
}

.notification-item.has-link {
  cursor: pointer;
  grid-template-columns: 24px minmax(0, 1fr) 14px 28px;
}

.notif-link-arrow {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.28);
  align-self: center;
  transition: color 0.15s ease, transform 0.15s ease;
}

.notification-item.has-link:hover .notif-link-arrow {
  color: rgba(255, 255, 255, 0.7);
  transform: translateX(2px);
}

.notification-item.unread {
  background: color-mix(in srgb, var(--primary-color, #ff0060) 7%, transparent);
  border-bottom-color: color-mix(in srgb, var(--primary-color, #ff0060) 18%, rgba(255, 255, 255, 0.05));
}

.notification-item.unread::before {
  content: "";
  position: absolute;
  left: 0;
  top: 12px;
  bottom: 12px;
  width: 2px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--primary-color, #ff0060) 52%, transparent);
}

.notif-icon {
  font-size: 20px;
  flex-shrink: 0;
  margin-top: 2px;
}

.notification-item.success .notif-icon { color: #34c759; }
.notification-item.error .notif-icon { color: #ff3b30; }
.notification-item.video .notif-icon { color: #30b0c0; }
.notification-item.podcast .notif-icon { color: #007aff; }
.notification-item.artist .notif-icon { color: #34c759; }
.notification-item.music .notif-icon { color: #30b0c0; }
.notification-item.events .notif-icon { color: #ff9500; }

.notif-content {
  flex: 1;
  min-width: 0;
}

.notif-message {
  margin: 0 0 4px 0;
  font-size: 14px;
  font-weight: 500;
  line-height: 1.4;
}

.notif-time {
  display: block;
  font-size: 12px;
  color: var(--text-secondary, rgba(255, 255, 255, 0.5));
}

.notif-dismiss {
  background: none;
  border: none;
  color: var(--text-secondary, rgba(255, 255, 255, 0.4));
  font-size: 16px;
  cursor: pointer;
  padding: 4px;
  flex-shrink: 0;
  opacity: 0;
  transition: opacity 0.2s;
  justify-self: end;
}

.notification-item:hover .notif-dismiss {
  opacity: 1;
}

.notif-dismiss:hover {
  color: var(--text-primary, #fff);
}

.notification-footer {
  padding: 12px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.notification-grabber {
  display: none;
}

.clear-all-btn {
  width: 100%;
  padding: 10px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  color: var(--text-primary, #fff);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.clear-all-btn:hover {
  background: rgba(255, 255, 255, 0.15);
}

.overlay-fade-enter-active, .overlay-fade-leave-active {
  transition: opacity 0.2s ease;
}

.overlay-fade-enter-from, .overlay-fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .notification-overlay {
    bottom: calc(var(--np-mobile-dock-height, 152px) + var(--android-nav-reserve, 0px) + env(safe-area-inset-bottom, 0px));
    align-items: flex-start;
    justify-content: stretch;
    background: rgba(0, 0, 0, 0.48);
    backdrop-filter: blur(18px) saturate(1.25);
    -webkit-backdrop-filter: blur(18px) saturate(1.25);
  }

  .notification-panel {
    width: 100%;
    max-width: none;
    height: min(55dvh, 460px);
    max-height: calc(100dvh - var(--np-mobile-dock-height, 152px) - var(--android-nav-reserve, 0px) - env(safe-area-inset-top, 0px) - env(safe-area-inset-bottom, 0px));
    padding-top: env(safe-area-inset-top, 0px);
    border-radius: 0 0 20px 20px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-top: 0;
    background:
      linear-gradient(180deg, rgba(255, 255, 255, 0.07), rgba(255, 255, 255, 0.025)),
      rgba(16, 16, 18, 0.95);
    box-shadow: 0 18px 42px rgba(0, 0, 0, 0.42);
    animation: slide-down-panel 0.32s cubic-bezier(0.2, 0.85, 0.25, 1);
    overflow: hidden;
  }

  @keyframes slide-down-panel {
    from {
      transform: translateY(-100%);
    }
    to {
      transform: translateY(0);
    }
  }

  .notification-header {
    min-height: 62px;
    padding: 14px max(18px, env(safe-area-inset-right)) 12px max(18px, env(safe-area-inset-left));
  }

  .notification-header h3 {
    font-size: 19px;
  }

  .close-btn {
    width: 42px;
    height: 42px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(255, 255, 255, 0.07);
    color: rgba(255, 255, 255, 0.82);
  }

  .notification-list {
    padding: 6px 0;
  }

  .notification-item {
    grid-template-columns: 32px minmax(0, 1fr) 36px;
  }

  .notification-item.has-link {
    grid-template-columns: 32px minmax(0, 1fr) 14px 36px;
    gap: 10px;
    padding: 14px max(16px, env(safe-area-inset-right)) 14px max(16px, env(safe-area-inset-left));
  }

  .notif-icon {
    width: 32px;
    height: 32px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    margin-top: 0;
    border-radius: 12px;
    background: rgba(255, 255, 255, 0.07);
    font-size: 15px;
  }

  .notif-message {
    font-size: 14px;
    line-height: 1.35;
    overflow-wrap: anywhere;
  }

  .notif-dismiss {
    width: 36px;
    height: 36px;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    border-radius: 12px;
    opacity: 1;
    background: rgba(255, 255, 255, 0.045);
    color: rgba(255, 255, 255, 0.74);
  }

  .notification-footer {
    padding: 12px max(16px, env(safe-area-inset-right)) 14px max(16px, env(safe-area-inset-left));
  }

  .notification-grabber {
    width: 100%;
    height: 22px;
    display: inline-flex;
    align-items: flex-start;
    justify-content: center;
    padding: 5px 0 9px;
    border: 0;
    border-top: 1px solid rgba(255, 255, 255, 0.07);
    background: transparent;
    cursor: pointer;
    touch-action: pan-y;
  }

  .notification-grabber span {
    width: 46px;
    height: 4px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.28);
    box-shadow: 0 1px 0 rgba(0, 0, 0, 0.24);
  }

  .clear-all-btn {
    min-height: 44px;
    border-radius: 14px;
  }
}

@media (min-width: 769px) {
  .notification-panel {
    width: 380px;
    height: auto;
    max-height: 500px;
    border-radius: 12px;
    margin: 70px 12px 0 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
  }

  .notification-overlay {
    background: transparent;
    align-items: flex-start;
    justify-content: flex-end;
    pointer-events: none;
  }

  .notification-overlay .notification-panel {
    pointer-events: auto;
  }
}
</style>
