<template>
  <section class="ltv-control-panel" aria-label="AHOY TV controls">
    <div class="ltv-control-panel-desktop">
      <div class="ltv-control-copy">
        <span class="ltv-control-kicker">Now Playing</span>
        <h2 class="ltv-control-title">{{ displayTitle }}</h2>
        <p v-if="displayDescription" class="ltv-control-description">
          {{ displayDescription }}
        </p>
        <p v-if="upNextTitle" class="ltv-control-up-next">
          <span class="ltv-control-up-next-label">Up next</span>
          <span class="ltv-control-up-next-title">{{ upNextTitle }}</span>
        </p>
        <div class="ltv-control-meta">
          <span class="ltv-control-channel">{{ channelLabel }}</span>
          <span class="ltv-control-status">{{ statusLabel }}</span>
        </div>
      </div>

      <div class="ltv-control-rail" role="tablist" aria-label="Channel selector">
        <button
          v-for="(channel, rowIdx) in channels"
          :key="channel.id"
          type="button"
          class="ltv-control-chip"
          :class="{ active: selectedRow === rowIdx }"
          :aria-selected="selectedRow === rowIdx"
          :title="`Switch to ${channel.name}`"
          @click="$emit('select', rowIdx)"
        >
          <span class="ltv-control-chip-icon" :style="getChannelBg(rowIdx)"></span>
          <span class="ltv-control-chip-copy">
            <span class="ltv-control-chip-name">{{ channel.name }}</span>
            <span class="ltv-control-chip-now">{{ channelNowTitle(rowIdx) }}</span>
          </span>
        </button>
      </div>

      <div class="ltv-control-actions">
        <button type="button" class="ltv-control-btn" title="Previous channel" @click="$emit('prev')">
          <i class="fas fa-chevron-left"></i>
        </button>
        <button type="button" class="ltv-control-btn" title="Next channel" @click="$emit('next')">
          <i class="fas fa-chevron-right"></i>
        </button>
        <button type="button" class="ltv-control-btn ltv-control-btn--wide" title="Open channels" @click="$emit('open-drawer')">
          <i class="fas fa-list"></i>
          <span>All Channels</span>
        </button>
        <button
          type="button"
          class="ltv-control-btn ltv-control-btn--play"
          :class="{ active: hasVideoTrack && isWatching && isPlaying }"
          @click="handlePrimaryAction"
        >
          <i :class="primaryIcon"></i>
          <span>{{ primaryLabel }}</span>
        </button>
        <button type="button" class="ltv-control-btn" title="Mute/Unmute" @click="$emit('toggle-mute')">
          <i :class="isMuted ? 'fas fa-volume-mute' : 'fas fa-volume-up'"></i>
        </button>
        <button
          v-if="isCastAvailable"
          type="button"
          class="ltv-control-btn"
          title="Cast"
          @click="$emit('cast')"
        >
          <i class="fas fa-tv"></i>
        </button>
      </div>
    </div>

    <div class="ltv-control-panel-mobile">
      <div class="ltv-mobile-topline">
        <button
          type="button"
          class="ltv-mobile-channel-trigger"
          :class="{ open: mobileChannelMenuOpen }"
          aria-haspopup="listbox"
          :aria-expanded="mobileChannelMenuOpen"
          aria-controls="mobile-channel-menu"
          @click="$emit('toggle-channel-menu')"
        >
          <span class="ltv-mobile-channel-trigger-icon" :style="getChannelBg(selectedRow)"></span>
          <span class="ltv-mobile-channel-text">{{ channelLabel }}</span>
          <i :class="mobileChannelMenuOpen ? 'fas fa-chevron-up' : 'fas fa-chevron-down'"></i>
        </button>
        <span class="ltv-mobile-status-pill">{{ statusLabel }}</span>
      </div>

      <Transition name="mobile-channel-menu">
        <button
          v-if="mobileChannelMenuOpen"
          type="button"
          class="ltv-mobile-menu-backdrop"
          aria-label="Close channel menu"
          @click="$emit('toggle-channel-menu')"
        ></button>
      </Transition>

      <Transition name="mobile-channel-menu">
        <div
          v-if="mobileChannelMenuOpen"
          id="mobile-channel-menu"
          class="ltv-mobile-channel-menu"
          role="listbox"
          aria-label="Channels"
        >
          <div class="ltv-mobile-channel-menu-header">Switch channel</div>
          <button
            v-for="(channel, rowIdx) in channels"
            :key="channel.id"
            type="button"
            class="ltv-mobile-channel-menu-item"
            :class="{ active: selectedRow === rowIdx }"
            :aria-selected="selectedRow === rowIdx"
            @click="$emit('select', rowIdx)"
          >
            <span class="ltv-mobile-channel-menu-icon" :style="getChannelBg(rowIdx)"></span>
            <span class="ltv-mobile-channel-menu-copy">
              <span class="ltv-mobile-channel-menu-name">{{ channel.name }}</span>
              <span class="ltv-mobile-channel-menu-now">{{ channelNowTitle(rowIdx) }}</span>
            </span>
            <i v-if="selectedRow === rowIdx" class="fas fa-check ltv-mobile-channel-menu-check"></i>
          </button>
        </div>
      </Transition>

      <div class="ltv-mobile-pinned-chip">
        <span class="ltv-mobile-pinned-label">Now Playing</span>
        <span class="ltv-mobile-pinned-title">{{ pinnedChannelTitle || channelLabel }}</span>
        <template v-if="upNextTitle">
          <span class="ltv-mobile-pinned-label ltv-mobile-pinned-upnext-label">Up Next</span>
          <span class="ltv-mobile-pinned-upnext">{{ upNextTitle }}</span>
        </template>
      </div>

      <div class="ltv-mobile-actions">
        <button
          type="button"
          class="ltv-mobile-primary"
          :class="{ active: hasVideoTrack && isWatching && isPlaying }"
          @click="handlePrimaryAction"
        >
          <i :class="primaryIcon"></i>
          <span>{{ primaryLabel }}</span>
        </button>
        <button v-if="isWatching" type="button" class="ltv-mobile-icon-btn" title="Mute/Unmute" @click="$emit('toggle-mute')">
          <i :class="isMuted ? 'fas fa-volume-mute' : 'fas fa-volume-up'"></i>
        </button>
        <button
          v-if="isCastAvailable"
          type="button"
          class="ltv-mobile-icon-btn"
          title="Cast"
          @click="$emit('cast')"
        >
          <i class="fas fa-tv"></i>
        </button>
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  channels: {
    type: Array,
    default: () => [],
  },
  selectedRow: {
    type: Number,
    default: 0,
  },
  channelLabel: {
    type: String,
    default: 'AHOY TV',
  },
  displayTitle: {
    type: String,
    default: '',
  },
  displayDescription: {
    type: String,
    default: '',
  },
  pinnedChannelTitle: {
    type: String,
    default: '',
  },
  mobileChannelMenuOpen: {
    type: Boolean,
    default: false,
  },
  upNextTitle: {
    type: String,
    default: '',
  },
  statusLabel: {
    type: String,
    default: 'Ready',
  },
  getChannelBg: {
    type: Function,
    required: true,
  },
  channelNowTitle: {
    type: Function,
    required: true,
  },
  hasVideoTrack: {
    type: Boolean,
    default: false,
  },
  isWatching: {
    type: Boolean,
    default: false,
  },
  isPlaying: {
    type: Boolean,
    default: false,
  },
  isMuted: {
    type: Boolean,
    default: false,
  },
  isCastAvailable: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['select', 'prev', 'next', 'open-drawer', 'toggle-play', 'toggle-mute', 'cast', 'toggle-channel-menu'])

const primaryLabel = computed(() => {
  if (!props.hasVideoTrack) return 'Browse Channels'
  if (props.isWatching && props.isPlaying) return 'Pause Live'
  return 'Watch Live'
})

const primaryIcon = computed(() => {
  if (!props.hasVideoTrack) return 'fas fa-list'
  if (props.isWatching && props.isPlaying) return 'fas fa-pause'
  return 'fas fa-play'
})

function handlePrimaryAction() {
  if (!props.hasVideoTrack) {
    emit('open-drawer')
    return
  }

  if (props.isWatching) {
    emit('toggle-play')
    return
  }

  emit('toggle-play')
}
</script>

<style scoped>
.ltv-control-panel {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.ltv-control-panel-desktop {
  display: grid;
  grid-template-columns: minmax(220px, 1.3fr) minmax(0, 1.7fr) auto;
  gap: 14px;
  align-items: stretch;
}

.ltv-control-copy {
  padding: 18px 18px 16px;
  border-radius: 22px;
  background:
    radial-gradient(circle at top left, rgba(64, 134, 255, 0.18), transparent 42%),
    linear-gradient(180deg, rgba(9, 16, 32, 0.95), rgba(6, 10, 19, 0.98));
  border: 1px solid rgba(118, 156, 255, 0.12);
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.28);
}

.ltv-control-kicker {
  display: inline-flex;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: rgba(154, 193, 255, 0.88);
  margin-bottom: 8px;
}

.ltv-control-title {
  margin: 0;
  font-size: 1.35rem;
  line-height: 1.15;
  font-weight: 800;
  color: #f7f9ff;
}

.ltv-control-description {
  margin: 10px 0 0;
  color: rgba(220, 227, 242, 0.75);
  font-size: 0.92rem;
  line-height: 1.55;
}

.ltv-control-up-next {
  margin: 10px 0 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.ltv-control-up-next-label {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(154, 193, 255, 0.84);
}

.ltv-control-up-next-title {
  color: rgba(235, 241, 255, 0.88);
  font-size: 0.92rem;
  line-height: 1.4;
}

.ltv-control-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.ltv-control-channel,
.ltv-control-status,
.ltv-mobile-status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 30px;
  padding: 0 12px;
  border-radius: 999px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.ltv-control-channel {
  background: rgba(71, 103, 194, 0.16);
  border: 1px solid rgba(127, 165, 255, 0.24);
  color: rgba(223, 234, 255, 0.92);
}

.ltv-control-status {
  background: rgba(34, 52, 125, 0.34);
  border: 1px solid rgba(109, 149, 255, 0.24);
  color: #dce7ff;
}

.ltv-control-rail {
  min-width: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 10px;
}

.ltv-control-chip {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.06), rgba(255, 255, 255, 0.03));
  color: rgba(245, 247, 255, 0.9);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.03);
  text-align: left;
}

.ltv-control-chip.active {
  border-color: rgba(109, 149, 255, 0.34);
  background: linear-gradient(180deg, rgba(66, 100, 206, 0.45), rgba(34, 52, 125, 0.55));
  box-shadow: 0 12px 30px rgba(25, 38, 89, 0.24);
}

.ltv-control-chip-icon {
  width: 38px;
  height: 38px;
  flex-shrink: 0;
  border-radius: 12px;
  background-size: cover;
  background-position: center;
}

.ltv-control-chip-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.ltv-control-chip-name,
.ltv-control-chip-now {
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.ltv-control-chip-name {
  font-size: 0.88rem;
  font-weight: 700;
  white-space: normal;
  line-height: 1.2;
}

.ltv-control-chip-now {
  font-size: 0.76rem;
  color: rgba(206, 217, 239, 0.78);
}

.ltv-control-actions {
  display: flex;
  align-items: stretch;
  gap: 8px;
  justify-content: flex-end;
  flex-wrap: wrap;
}

.ltv-control-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  min-height: 46px;
  padding: 0 14px;
  border-radius: 14px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.06);
  color: #f5f7ff;
  font-weight: 700;
}

.ltv-control-btn--wide {
  min-width: 130px;
}

.ltv-control-btn--play {
  min-width: 140px;
  border-color: rgba(109, 149, 255, 0.28);
  background: linear-gradient(180deg, rgba(98, 130, 238, 0.95), rgba(59, 88, 190, 0.95));
  box-shadow: 0 14px 28px rgba(32, 48, 113, 0.28);
}

.ltv-control-btn--play.active {
  background: linear-gradient(180deg, rgba(55, 81, 179, 0.95), rgba(34, 52, 125, 0.95));
}

  .ltv-control-panel-mobile {
    display: none;
  }

  @media (max-width: 768px), (pointer: coarse) {
  .ltv-control-panel-desktop {
    display: none;
  }

  .ltv-control-panel-mobile {
    display: flex;
    flex-direction: column;
    gap: 12px;
    position: relative;
    padding: 16px;
    border-radius: 0 0 22px 22px;
    background:
      radial-gradient(circle at top, rgba(79, 140, 255, 0.22), transparent 40%),
      linear-gradient(180deg, rgba(7, 11, 20, 0.96) 0%, rgba(9, 14, 26, 0.98) 100%);
    border: 1px solid rgba(118, 156, 255, 0.14);
    box-shadow: 0 18px 48px rgba(0, 0, 0, 0.28);
  }

  .ltv-mobile-topline {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .ltv-mobile-channel-trigger {
    flex: 1;
    min-width: 0;
    display: inline-flex;
    align-items: center;
    justify-content: space-between;
    gap: 10px;
    min-height: 48px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 16px;
    background: rgba(255, 255, 255, 0.06);
    color: #f5f7ff;
    padding: 12px 14px;
  }

  .ltv-mobile-channel-trigger.open {
    border-color: rgba(109, 149, 255, 0.46);
    background: rgba(72, 106, 208, 0.16);
  }

  .ltv-mobile-channel-trigger-icon {
    width: 26px;
    height: 26px;
    flex-shrink: 0;
    border-radius: 8px;
    background-size: cover;
    background-position: center;
    background-color: rgba(255, 255, 255, 0.08);
  }

  .ltv-mobile-channel-text {
    flex: 1;
    min-width: 0;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
    font-weight: 700;
  }

  .ltv-mobile-status-pill {
    flex-shrink: 0;
    min-width: 78px;
    background: rgba(34, 52, 125, 0.34);
    border: 1px solid rgba(109, 149, 255, 0.24);
    color: #dce7ff;
  }

  .ltv-mobile-channel-menu {
    display: flex;
    flex-direction: column;
    gap: 8px;
    padding: 12px;
    border-radius: 18px;
    border: 1px solid rgba(109, 149, 255, 0.18);
    background: rgba(7, 11, 20, 0.96);
    max-height: min(320px, 50vh);
    overflow-y: auto;
    box-shadow: 0 18px 42px rgba(0, 0, 0, 0.32);
    position: relative;
    z-index: 2;
  }

  .ltv-mobile-channel-menu-header {
    padding: 2px 4px 4px;
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(154, 193, 255, 0.8);
  }

  .ltv-mobile-menu-backdrop {
    position: fixed;
    inset: 0;
    z-index: 1;
    border: 0;
    padding: 0;
    margin: 0;
    background: rgba(2, 4, 10, 0.38);
    backdrop-filter: blur(1px);
  }

  .ltv-mobile-channel-menu-item {
    display: flex;
    flex-direction: row;
    align-items: center;
    gap: 10px;
    width: 100%;
    box-sizing: border-box;
    min-height: 60px;
    padding: 10px 12px;
    border-radius: 14px;
    border: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(255, 255, 255, 0.04);
    color: #f5f7ff;
    text-align: left;
    cursor: pointer;
  }

  .ltv-mobile-channel-menu-item.active {
    border-color: rgba(109, 149, 255, 0.34);
    background: rgba(66, 100, 206, 0.18);
  }

  .ltv-mobile-channel-menu-icon {
    width: 34px;
    height: 34px;
    flex-shrink: 0;
    border-radius: 8px;
    background-size: cover;
    background-position: center;
    background-color: rgba(255, 255, 255, 0.08);
  }

  .ltv-mobile-channel-menu-copy {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .ltv-mobile-channel-menu-check {
    flex-shrink: 0;
    font-size: 13px;
    color: rgba(109, 149, 255, 0.9);
  }

  .ltv-mobile-channel-menu-name {
    font-size: 14px;
    font-weight: 700;
    line-height: 1.3;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .ltv-mobile-channel-menu-now {
    font-size: 12px;
    color: rgba(229, 231, 235, 0.7);
    line-height: 1.35;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
  }

  .ltv-mobile-pinned-chip {
    display: flex;
    flex-direction: column;
    gap: 3px;
    padding: 12px 14px;
    border-radius: 16px;
    border: 1px solid rgba(109, 149, 255, 0.22);
    background: rgba(255, 255, 255, 0.05);
  }

  .ltv-mobile-pinned-label {
    font-size: 10px;
    font-weight: 800;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: rgba(154, 193, 255, 0.8);
  }

  .ltv-mobile-pinned-title {
    font-size: 14px;
    font-weight: 700;
    color: #f7f9ff;
    line-height: 1.25;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .ltv-mobile-pinned-upnext-label {
    margin-top: 6px;
    opacity: 0.7;
  }

  .ltv-mobile-pinned-upnext {
    font-size: 13px;
    font-weight: 600;
    color: rgba(206, 217, 239, 0.78);
    line-height: 1.25;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .ltv-mobile-actions {
    display: flex;
    align-items: center;
    gap: 10px;
  }

  .ltv-mobile-primary,
  .ltv-mobile-icon-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    min-height: 48px;
    border-radius: 16px;
    border: 1px solid rgba(109, 149, 255, 0.28);
    background: linear-gradient(180deg, rgba(98, 130, 238, 0.95), rgba(59, 88, 190, 0.95));
    color: #fff;
    font-weight: 800;
    box-shadow: 0 14px 28px rgba(32, 48, 113, 0.28);
  }

  .ltv-mobile-primary {
    flex: 1;
    min-width: 0;
    padding: 0 16px;
  }

  .mobile-channel-menu-enter-active,
  .mobile-channel-menu-leave-active {
    transition: opacity 0.16s ease, transform 0.16s ease;
  }

  .mobile-channel-menu-enter-from,
  .mobile-channel-menu-leave-to {
    opacity: 0;
    transform: translateY(-6px);
  }

  .ltv-mobile-primary.active {
    background: linear-gradient(180deg, rgba(55, 81, 179, 0.95), rgba(34, 52, 125, 0.95));
  }

  .ltv-mobile-icon-btn {
    width: 48px;
    flex-shrink: 0;
    background: rgba(255, 255, 255, 0.06);
    border-color: rgba(255, 255, 255, 0.08);
    box-shadow: none;
  }
}
</style>
