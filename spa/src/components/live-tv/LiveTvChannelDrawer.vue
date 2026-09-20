<template>
  <div v-if="open" class="ltv-overlay" @click="$emit('close')" aria-hidden="true"></div>
  <Transition name="mobile-drawer">
    <div v-if="open" class="mobile-channel-drawer" role="dialog" aria-modal="true" aria-label="Channels" tabindex="-1" @keydown.esc="$emit('close')">
      <div class="mobile-channel-drawer-header">
        <div>
          <h3 class="mobile-channel-drawer-title">Channels</h3>
          <p class="mobile-channel-drawer-hint">Tap a channel to switch.</p>
        </div>
        <button type="button" class="mobile-channel-drawer-close" aria-label="Close" @click="$emit('close')">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <ul class="mobile-channel-drawer-list" role="listbox">
        <li
          v-for="(channel, rowIdx) in channels"
          :key="channel.id"
          role="option"
          :aria-selected="selectedRow === rowIdx"
          class="mobile-channel-drawer-item"
          :class="{ active: selectedRow === rowIdx }"
          @click="$emit('select', rowIdx)"
        >
          <div class="mobile-channel-drawer-icon" :style="getChannelBg(rowIdx)"></div>
          <span class="mobile-channel-drawer-copy">
            <span class="mobile-channel-drawer-name">{{ channel.name }}</span>
            <span class="mobile-channel-drawer-now">{{ channelNowTitle(rowIdx) }}</span>
          </span>
          <i v-if="selectedRow === rowIdx" class="fas fa-check mobile-channel-drawer-check"></i>
        </li>
      </ul>
    </div>
  </Transition>
</template>

<script setup>
defineProps({
  open: {
    type: Boolean,
    default: false,
  },
  channels: {
    type: Array,
    default: () => [],
  },
  selectedRow: {
    type: Number,
    default: 0,
  },
  getChannelBg: {
    type: Function,
    required: true,
  },
  channelNowTitle: {
    type: Function,
    required: true,
  },
})

defineEmits(['close', 'select'])
</script>

<style scoped>
.ltv-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 99;
}

.mobile-channel-drawer {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  max-height: 60vh;
  background: #0f0f0f;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
  box-shadow: 0 -8px 32px rgba(0, 0, 0, 0.5);
  z-index: 100;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.mobile-channel-drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 16px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  flex-shrink: 0;
}

.mobile-channel-drawer-title {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: #e5e7eb;
}

.mobile-channel-drawer-hint {
  margin: 4px 0 0;
  color: rgba(229, 231, 235, 0.64);
  font-size: 12px;
  line-height: 1.3;
}

.mobile-channel-drawer-close {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
  color: #e5e7eb;
  cursor: pointer;
  font-size: 18px;
}

.mobile-channel-drawer-list {
  list-style: none;
  margin: 0;
  padding: 8px 0 max(24px, env(safe-area-inset-bottom));
  overflow-y: auto;
  -webkit-overflow-scrolling: touch;
}

.mobile-channel-drawer-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  cursor: pointer;
  color: #e5e7eb;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  transition: background 0.15s;
}

.mobile-channel-drawer-item:active {
  background: rgba(255, 255, 255, 0.1);
}

.mobile-channel-drawer-item.active {
  background: rgba(66, 100, 206, 0.22);
  border-left: 3px solid rgba(109, 149, 255, 0.8);
}

.mobile-channel-drawer-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background-size: cover;
  background-position: center;
  flex-shrink: 0;
}

.mobile-channel-drawer-name {
  font-size: 15px;
  font-weight: 600;
}

.mobile-channel-drawer-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.mobile-channel-drawer-now {
  font-size: 12px;
  color: rgba(229, 231, 235, 0.68);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mobile-channel-drawer-check {
  color: #3b82f6;
  font-size: 14px;
}

.mobile-drawer-enter-active,
.mobile-drawer-leave-active {
  transition: transform 0.25s ease, opacity 0.2s ease;
}

.mobile-drawer-enter-from,
.mobile-drawer-leave-to {
  transform: translateY(100%);
  opacity: 0.8;
}
</style>
