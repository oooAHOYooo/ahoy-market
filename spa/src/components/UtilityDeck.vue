<template>
  <section class="utility-deck" :class="{ 'status-hidden': hideEmptyStatus }" aria-label="Utility Deck">
    <div v-if="!hideEmptyStatus" class="utility-deck-status">
      <button type="button" class="utility-status-pill" @click="$emit('toggle-notifications')">
        <span class="utility-status-icon">
          <i class="fas fa-bullhorn"></i>
          <span v-if="unreadCount > 0" class="utility-status-badge">{{ unreadCount }}</span>
        </span>
        <span class="utility-status-copy">
          <strong>What&apos;s New</strong>
          <small>{{ unreadCount > 0 ? `${unreadCount} unread • ${latestMessage}` : latestMessage }}</small>
        </span>
        <span class="utility-status-action">Open</span>
      </button>
    </div>

    <nav class="utility-deck-actions" aria-label="Utility actions">
      <router-link
        to="/my-saves"
        class="utility-action"
        :class="{ active: route.path === '/my-saves' || route.path === '/recently-played' }"
      >
        <i class="fas fa-bookmark"></i>
        <span>Saved</span>
      </router-link>
      <button
        type="button"
        class="utility-action"
        :class="{ active: isAyuNight }"
        @click="toggleTheme"
      >
        <i class="fas fa-moon"></i>
        <span>Theme</span>
      </button>
      <router-link to="/settings" class="utility-action" :class="{ active: route.path === '/settings' }">
        <i class="fas fa-cog"></i>
        <span>Settings</span>
      </router-link>
    </nav>
  </section>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useNotificationCenter } from '../composables/useNotificationCenter'
import { useTheme } from '../composables/useTheme'

defineEmits(['toggle-notifications'])

const { notifications } = useNotificationCenter()
const route = useRoute()
const theme = useTheme()

const unreadCount = computed(() => notifications.value.filter((notification) => !notification.read).length)
const latestMessage = computed(() => {
  if (unreadCount.value === 0) return 'No new updates'
  const message = notifications.value.find((notification) => !notification.read)?.message || 'New update'
  return message.length > 44 ? `${message.slice(0, 41).trim()}...` : message
})
const hideEmptyStatus = computed(() => route.path.startsWith('/whats-new') && unreadCount.value === 0)
const isAyuNight = computed(() => theme.currentTheme.value === 'ayu-night')

function toggleTheme() {
  theme.setTheme(isAyuNight.value ? 'default' : 'ayu-night', { explicit: true })
}

</script>

<style scoped>
.utility-deck {
  height: 100%;
  display: grid;
  grid-template-rows: auto auto;
  align-content: start;
  gap: 4px;
  padding: 4px max(8px, env(safe-area-inset-right)) calc(6px + env(safe-area-inset-bottom, 0px)) max(8px, env(safe-area-inset-left));
  background:
    linear-gradient(180deg,
      color-mix(in srgb, var(--primary-color, #00a2ff) 10%, rgba(255, 255, 255, 0.012)),
      rgba(255, 255, 255, 0.006));
  border-radius: 14px;
  border: 1px solid color-mix(in srgb, var(--primary-color, #00a2ff) 12%, rgba(255, 255, 255, 0.06));
}

.utility-deck.status-hidden {
  grid-template-rows: auto;
  align-content: start;
}

.utility-deck-status {
  min-height: 0;
  display: flex;
}

.utility-status-pill {
  width: 100%;
  min-height: 34px;
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 5px 8px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 12px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.03), rgba(255, 255, 255, 0.012));
  color: rgba(255, 255, 255, 0.84);
  text-align: left;
  overflow: hidden;
}

.utility-status-icon {
  position: relative;
  width: 26px;
  height: 26px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.045);
}

.utility-status-badge {
  position: absolute;
  right: 3px;
  bottom: 3px;
  min-width: 10px;
  height: 10px;
  padding: 0 3px;
  border-radius: 999px;
  background: color-mix(in srgb, var(--primary-color, #00a2ff) 38%, transparent);
  color: rgba(255, 255, 255, 0.86);
  font-size: 6px;
  line-height: 10px;
  text-align: center;
}

.utility-status-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.utility-status-copy strong {
  max-width: 100%;
  overflow: hidden;
  font-size: 9px;
  line-height: 1.1;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.utility-status-copy small {
  max-width: 100%;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.5);
  font-size: 7px;
  line-height: 1.2;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.utility-status-action {
  flex: 0 0 auto;
  margin-left: auto;
  padding: 3px 7px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.72);
  font-size: 7px;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.utility-deck-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  grid-auto-rows: 34px;
  gap: 4px;
}

.utility-action {
  min-height: 34px;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  padding: 6px 4px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.026), rgba(255, 255, 255, 0.010));
  color: rgba(255, 255, 255, 0.66);
  font: inherit;
  text-decoration: none;
  transition: border-color 0.16s ease, color 0.16s ease, background 0.16s ease;
}

.utility-action.active {
  border-color: color-mix(in srgb, var(--primary-color, #00a2ff) 18%, rgba(255, 255, 255, 0.12));
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--primary-color, #00a2ff) 8%, rgba(255, 255, 255, 0.042)), rgba(255, 255, 255, 0.015));
  color: rgba(255, 255, 255, 0.84);
}

.utility-action:active {
  transform: translateY(1px);
}

.utility-action:hover,
.utility-action:focus-visible {
  border-color: color-mix(in srgb, var(--primary-color, #00a2ff) 16%, rgba(255, 255, 255, 0.1));
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--primary-color, #00a2ff) 4%, rgba(255, 255, 255, 0.04)), rgba(255, 255, 255, 0.014));
  color: rgba(255, 255, 255, 0.82);
}

.utility-action i {
  font-size: 11px;
}

.utility-action span {
  max-width: 100%;
  overflow: hidden;
  font-size: 7px;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
