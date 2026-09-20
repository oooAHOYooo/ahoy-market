<template>
  <template v-if="activeGame === 'trampoline'">
    <section
      ref="heroRef"
      class="game-inner"
      @pointerdown="handlePointerDown"
      @pointermove="handlePointerMove"
      @pointerup="handlePointerUp"
      @pointercancel="handlePointerCancel"
      @pointerleave="handlePointerLeave"
    >
      <SkipperStage
        :is-playing="isRadioActive"
        :control-intent="controlIntent"
        :active-trick="activeTrick"
        :audio-drive="audioDrive"
        :audio-phase="audioPhase"
        @status="onStageStatus"
        @collect="onStageCollect"
        @lock="onStageLock"
        @pop="onStagePop"
      />

      <div class="game-hud game-hud-top-left">
        <div class="game-menu-header-stack">
          <button type="button" class="radio-icon-button" aria-label="Game menu" @pointerdown.stop @click="emit('exit-game')">
            <i class="fas fa-th-large"></i>
          </button>
          <button
            type="button"
            class="radio-toggle small"
            :class="{ 'is-active': isRadioAudible }"
            :disabled="!stationCurrent"
            :aria-label="radioToggleLabel"
            @pointerdown.stop
            @click="emit('toggle-radio')"
          >
            <img v-if="stationArt" :src="stationArt" alt="" aria-hidden="true" class="radio-toggle-art" />
            <span class="radio-toggle-icon">
              <i class="fas" :class="radioButtonIcon"></i>
            </span>
          </button>
        </div>
      </div>

      <div class="game-hud game-hud-bottom-left">
        <div class="radio-track-pill">
          <span class="radio-track-kicker">{{ brandLabel }}</span>
          <span class="radio-track-title">{{ stationTitle }}</span>
        </div>
      </div>

      <Transition name="hint-fade">
        <div v-if="showHint" class="control-hint" aria-hidden="true">click to flip</div>
      </Transition>
      <Transition name="hint-fade">
        <div v-if="clickHint" class="click-hint" aria-hidden="true">{{ clickHint }}</div>
      </Transition>
    </section>
  </template>

  <div v-else-if="activeGame === 'garden'" class="game-inner">
    <GardenGame
      :audio-drive="audioDrive"
      :station-title="stationTitle"
      :is-radio-audible="isRadioAudible"
      :radio-button-icon="radioButtonIcon"
      :station-art="stationArt"
      @back="emit('exit-game')"
      @toggle-radio="emit('toggle-radio')"
    />
  </div>

  <div v-else-if="activeGame === 'birds'" class="game-inner">
    <AngryBirdsGame
      :audio-drive="audioDrive"
      :is-radio-audible="isRadioAudible"
      :radio-button-icon="radioButtonIcon"
      :station-art="stationArt"
      @back="emit('exit-game')"
      @collect="onStageCollect"
      @toggle-radio="emit('toggle-radio')"
      @score="onBirdsScore"
    />
  </div>

  <Transition name="trick-pop">
    <div v-if="trickNotification" class="trick-notification" aria-hidden="true">
      <span>{{ trickNotification }}</span>
    </div>
  </Transition>
</template>

<script setup>
import { computed, defineAsyncComponent, ref } from 'vue'
import { useSkipperControls } from '../radio-game/useSkipperControls'

const SkipperStage = defineAsyncComponent(() => import('../radio-game/SkipperStage.vue'))
const GardenGame = defineAsyncComponent(() => import('../radio-game/GardenGame.vue'))
const AngryBirdsGame = defineAsyncComponent(() => import('../radio-game/AngryBirdsGame.vue'))

const props = defineProps({
  activeGame: {
    type: String,
    default: null,
  },
  activeTrick: {
    type: String,
    default: null,
  },
  audioDrive: {
    type: Number,
    required: true,
  },
  audioPhase: {
    type: Number,
    required: true,
  },
  clickHint: {
    type: String,
    default: '',
  },
  isRadioActive: {
    type: Boolean,
    required: true,
  },
  isRadioAudible: {
    type: Boolean,
    required: true,
  },
  onBirdsScore: {
    type: Function,
    required: true,
  },
  onPulse: {
    type: Function,
    required: true,
  },
  onStageCollect: {
    type: Function,
    required: true,
  },
  onStageLock: {
    type: Function,
    required: true,
  },
  onStagePop: {
    type: Function,
    required: true,
  },
  onStageStatus: {
    type: Function,
    required: true,
  },
  radioButtonIcon: {
    type: String,
    required: true,
  },
  brandLabel: {
    type: String,
    default: 'Ahoy Radio',
  },
  radioToggleLabel: {
    type: String,
    required: true,
  },
  showHint: {
    type: Boolean,
    required: true,
  },
  stationArt: {
    type: String,
    default: '',
  },
  stationCurrent: {
    type: Object,
    default: null,
  },
  stationTitle: {
    type: String,
    required: true,
  },
  trickNotification: {
    type: String,
    default: '',
  },
})

const emit = defineEmits(['exit-game', 'toggle-radio'])
const heroRef = ref(null)

const {
  controlIntent,
  handlePointerDown,
  handlePointerMove,
  handlePointerUp,
  handlePointerCancel,
  handlePointerLeave,
} = useSkipperControls(heroRef, {
  enabled: computed(() => props.activeGame === 'trampoline'),
  onPulse: () => props.onPulse({
    clickX: controlIntent.clickX,
    clickY: controlIntent.clickY,
    charge: controlIntent.charge,
  }),
})
</script>

<style scoped>
.game-inner {
  position: absolute;
  inset: 0;
  z-index: 1;
  cursor: pointer;
  pointer-events: auto;
  touch-action: manipulation;
  user-select: none;
  overscroll-behavior: none;
  overflow: hidden;
}

.game-hud {
  position: absolute;
  z-index: 3;
  pointer-events: none;
}

.game-hud-top-left { top: 0.75rem; left: 0.75rem; }
.game-hud-top-right { top: 0.75rem; right: 0.75rem; }
.game-hud-bottom-left { left: 0.75rem; bottom: 0.75rem; }

.game-menu-header-stack {
  display: flex;
  gap: 0.45rem;
  align-items: center;
}

.radio-icon-button,
.radio-toggle {
  position: relative;
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border: 2px solid #00d7ff;
  border-radius: 999px;
  background: rgba(11, 11, 11, 0.74);
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.34);
  color: #ffd400;
  cursor: pointer;
  pointer-events: auto;
  overflow: hidden;
  transition: transform .18s ease, box-shadow .18s ease, background .18s ease;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.radio-toggle.small { width: 40px; height: 40px; }

.radio-icon-button:hover,
.radio-toggle:hover {
  transform: translateY(-1px) scale(1.04);
  background: rgba(11, 11, 11, 0.9);
}

.radio-toggle.is-active { border-color: #ffd400; }
.radio-toggle:disabled { opacity: .62; cursor: wait; }

.radio-toggle-art {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: .72;
}

.radio-toggle-icon {
  position: relative;
  z-index: 1;
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 999px;
  background: rgba(255, 212, 0, 0.92);
  font-size: 0.75rem;
  color: #0b0b0b;
}

.radio-track-pill {
  display: grid;
  max-width: min(22rem, calc(100vw - 1.5rem));
  padding: 0.55rem 1rem;
  border: 2px solid #ff2fb8;
  border-radius: 0.6rem;
  background: rgba(11, 11, 11, 0.86);
  color: #ffd400;
  pointer-events: none;
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}

.radio-track-kicker {
  font-size: 0.6rem;
  font-weight: 800;
  letter-spacing: 0.1em;
  line-height: 1;
  text-transform: uppercase;
  color: rgba(0, 215, 255, 0.92);
}

.radio-track-title {
  margin-top: 0.18rem;
  font-size: 0.85rem;
  font-weight: 800;
  line-height: 1.2;
  word-break: break-word;
}

.control-hint {
  position: absolute;
  left: 50%;
  bottom: 3.5rem;
  z-index: 3;
  transform: translateX(-50%);
  padding: 0.4rem 0.7rem;
  border: 2px solid #00d7ff;
  border-radius: 999px;
  background: rgba(11, 11, 11, 0.78);
  color: #ffd400;
  font-size: 0.66rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  pointer-events: none;
  box-shadow: 0 10px 22px rgba(0, 0, 0, 0.34);
}

.click-hint {
  position: absolute;
  left: 50%;
  bottom: 5.5rem;
  z-index: 3;
  transform: translateX(-50%);
  padding: 0.28rem 0.55rem;
  border: 1px solid rgba(255, 47, 184, 0.6);
  border-radius: 999px;
  background: rgba(11, 11, 11, 0.65);
  color: #ff2fb8;
  font-size: 0.6rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  pointer-events: none;
}

.trick-notification {
  position: absolute;
  right: 1rem;
  top: 1rem;
  z-index: 4;
  padding: 0.45rem 0.7rem;
  border-radius: 999px;
  background: rgba(255, 47, 184, 0.14);
  color: #ff2fb8;
  font-size: 0.72rem;
  font-weight: 900;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  pointer-events: none;
}

.hint-fade-enter-active { transition: opacity .25s ease; }
.hint-fade-leave-active { transition: opacity .7s ease; }
.hint-fade-enter-from,
.hint-fade-leave-to { opacity: 0; }

.trick-pop-enter-active { transition: transform .18s ease, opacity .18s ease; }
.trick-pop-leave-active { transition: transform .25s ease, opacity .25s ease; }
.trick-pop-enter-from,
.trick-pop-leave-to { transform: translateY(-6px) scale(.98); opacity: 0; }
</style>
