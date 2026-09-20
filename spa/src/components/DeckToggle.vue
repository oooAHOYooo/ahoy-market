<template>
  <button
    class="deck-toggle"
    :class="{
      'is-player-mode': deckMode === 'player',
      'is-utility-mode': deckMode === 'utility',
      'has-active-media': deckMode === 'nav' && playerStore.currentTrack && playerStore.isPlaying
    }"
    :aria-label="`Switch to ${nextDeckLabel}`"
    :title="`Switch to ${nextDeckLabel}`"
    @click="onClick"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerCancel"
  >
    <span class="deck-toggle-icon">
      <i v-if="deckMode === 'nav'" class="fas fa-th-large"></i>
      <i v-else-if="deckMode === 'player'" class="fas fa-compact-disc"></i>
      <i v-else class="fas fa-sliders-h"></i>
    </span>
    <span class="deck-toggle-dots" aria-hidden="true">
      <span :class="{ active: deckMode === 'nav' }"></span>
      <span :class="{ active: deckMode === 'player' }"></span>
      <span :class="{ active: deckMode === 'utility' }"></span>
    </span>
  </button>
</template>

<script setup>
import { computed } from 'vue'
import { useMobileCollapse } from '../composables/useMobileCollapse'
import { useDeckToggleInteraction } from '../composables/useDeckToggleInteraction'
import { usePlayerStore } from '../stores/player'

const { deckMode, toggleDeckMode } = useMobileCollapse()
const playerStore = usePlayerStore()

const nextDeckLabel = computed(() => {
  if (deckMode.value === 'nav') return 'player'
  if (deckMode.value === 'player') return 'utility'
  return 'navigation'
})

const { onClick, onPointerDown, onPointerMove, onPointerUp, onPointerCancel } = useDeckToggleInteraction({
  onToggle: () => toggleDeckMode(),
  onSwipeToggle: () => toggleDeckMode(),
})
</script>
