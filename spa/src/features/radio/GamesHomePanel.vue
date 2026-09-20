<template>
  <div class="games-home">
    <section class="games-home-card">
      <div class="games-home-head">
        <div class="games-home-copy">
          <div class="games-home-kicker">Hidden feature</div>
          <div class="games-home-title">Games Lab</div>
          <p class="games-home-desc">Experimental radio-adjacent games, parked off the main route for now.</p>
        </div>
      </div>

      <div class="games-home-list">
        <RadioGameLauncherCard
          v-for="game in gameOptions"
          :key="game.id"
          :game="game"
          :best-score="bestScores[game.scoreKey]"
          @select="(selected) => emit('launch-game', selected)"
        />
      </div>
    </section>
  </div>
</template>

<script setup>
import RadioGameLauncherCard from '../radio-game/RadioGameLauncherCard.vue'

defineProps({
  bestScores: {
    type: Object,
    required: true,
  },
  gameOptions: {
    type: Array,
    required: true,
  },
})

const emit = defineEmits(['launch-game'])
</script>

<style scoped>
.games-home {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
  padding: 0.95rem;
  overflow-y: auto;
}

.games-home-card {
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 18px;
  background: rgba(11, 11, 18, 0.74);
  backdrop-filter: blur(14px) saturate(150%);
  -webkit-backdrop-filter: blur(14px) saturate(150%);
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.26);
  padding: 0.95rem;
}

.games-home-kicker {
  font-size: 0.62rem;
  font-weight: 800;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(0, 215, 255, 0.82);
}

.games-home-title {
  margin-top: 0.25rem;
  color: #ffd400;
  font-size: 1rem;
  font-weight: 900;
  line-height: 1.12;
  letter-spacing: 0.02em;
}

.games-home-desc {
  margin: 0.3rem 0 0;
  color: rgba(255, 255, 255, 0.72);
  font-size: 0.84rem;
  line-height: 1.45;
}

.games-home-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
  margin-top: 0.85rem;
}
</style>
