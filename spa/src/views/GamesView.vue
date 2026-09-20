<template>
  <div class="games-page">
    <div
      ref="consoleRef"
      class="games-shell"
      :class="{ 'is-fullscreen': isFullscreen, 'is-rotate-prompt': showRotatePrompt }"
      :style="{
        borderColor: `rgb(${Math.floor(audioDrive * 120)}, ${Math.min(255, 150 + Math.floor(audioDrive * 90))}, 255)`,
        boxShadow: `0 0 ${16 + audioDrive * 36}px rgba(0, 215, 255, ${0.12 + audioDrive * 0.22}), 0 20px 44px rgba(0, 0, 0, 0.48)`
      }"
    >
      <button
        type="button"
        class="persistent-fs-toggle"
        @pointerdown.stop
        @pointerup.stop
        @click="toggleFullscreen"
        :title="isFullscreen ? 'Exit Fullscreen' : 'Immersive Fullscreen'"
      >
        <i class="fa-solid" :class="isFullscreen ? 'fa-compress' : 'fa-expand'"></i>
      </button>

      <div v-if="showRotatePrompt" class="games-rotate-prompt" aria-live="polite">
        <div class="games-rotate-kicker">Games Lab</div>
        <div class="games-rotate-title">Rotate to portrait</div>
        <div class="games-rotate-copy">The hidden games fit best upright. Turn the phone back for the full view.</div>
      </div>

      <template v-else>
        <GamesHomePanel v-if="!activeGame"
          :best-scores="bestScores"
          :game-options="gameOptions"
          @launch-game="launchGame"
        />

        <RadioGameSurface
          :active-game="activeGame"
          :active-trick="activeTrick"
          :audio-drive="audioDrive"
          :audio-phase="audioPhase"
          :brand-label="'Games Lab'"
          :click-hint="clickHint"
          :on-pulse="onPulse"
          :is-radio-active="isRadioActive"
          :is-radio-audible="isRadioAudible"
          :on-birds-score="onBirdsScore"
          :on-stage-collect="onStageCollect"
          :on-stage-lock="onStageLock"
          :on-stage-pop="onStagePop"
          :on-stage-status="onStageStatus"
          :radio-button-icon="radioButtonIcon"
          :radio-toggle-label="radioToggleLabel"
          :show-hint="showHint"
          :station-art="stationArt"
          :station-current="stationCurrent"
          :station-title="stationTitle"
          :trick-notification="trickNotification"
          @exit-game="exitGame"
          @toggle-radio="handleRadioAudioToggle"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { useGamesPage } from '../composables/useGamesPage'
import GamesHomePanel from '../features/radio/GamesHomePanel.vue'
import RadioGameSurface from '../features/radio/RadioGameSurface.vue'

const {
  bestScores,
  audioDrive,
  audioPhase,
  stationArt,
  stationTitle,
  radioToggleLabel,
  radioButtonIcon,
  handleRadioAudioToggle,
  isFullscreen,
  consoleRef,
  activeGame,
  isRadioActive,
  showRotatePrompt,
  activeTrick,
  trickNotification,
  showHint,
  clickHint,
  gameOptions,
  stationCurrent,
  launchGame,
  exitGame,
  onStageStatus,
  onStageCollect,
  onStageLock,
  onStagePop,
  onBirdsScore,
  onPulse,
  toggleFullscreen,
} = useGamesPage()
</script>

<style scoped>
.games-page {
  display: flex;
  align-items: flex-start;
  justify-content: center;
  width: 100%;
  padding: 1.5rem 1.5rem 2rem;
  box-sizing: border-box;
}

.games-shell {
  position: relative;
  width: 100%;
  max-width: min(520px, calc(100vw - 2rem));
  aspect-ratio: 9 / 16;
  border: 1.5px solid rgba(0, 215, 255, 0.32);
  border-radius: 24px;
  background: rgba(12, 12, 22, 0.64);
  backdrop-filter: blur(18px) saturate(180%);
  -webkit-backdrop-filter: blur(18px) saturate(180%);
  overflow: hidden;
  color: #ffd400;
  transition: box-shadow 0.3s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.3s cubic-bezier(0.16, 1, 0.3, 1);
}

.games-shell.is-rotate-prompt {
  max-width: min(640px, calc(100vw - 2rem));
  aspect-ratio: 16 / 9;
}

.games-rotate-prompt {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  padding: 1.25rem;
  text-align: center;
  background: radial-gradient(circle at top, rgba(0, 215, 255, 0.16), transparent 42%), rgba(8, 8, 16, 0.92);
}

.games-rotate-kicker {
  margin-bottom: 0.55rem;
  color: #00d7ff;
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.18em;
  text-transform: uppercase;
}

.games-rotate-title {
  color: #ffd400;
  font-size: 1.05rem;
  font-weight: 900;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.games-rotate-copy {
  max-width: 18rem;
  margin-top: 0.45rem;
  color: rgba(255, 255, 255, 0.62);
  font-size: 0.78rem;
  line-height: 1.45;
}
</style>
