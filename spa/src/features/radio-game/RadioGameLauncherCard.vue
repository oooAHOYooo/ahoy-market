<template>
  <button
    type="button"
    class="radio-game-card"
    :class="game.accentClass"
    @click="emit('select', game.id)"
  >
    <div class="radio-game-card__inner">
      <div class="radio-game-card__emoji">{{ game.emoji }}</div>
      <div class="radio-game-card__text">
        <div class="radio-game-card__name">{{ game.name }}</div>
        <div class="radio-game-card__desc">{{ game.description }}</div>
      </div>
      <div v-if="bestScore" class="radio-game-card__best">
        {{ game.bestText(bestScore) }}
      </div>
    </div>
  </button>
</template>

<script setup>
defineProps({
  game: {
    type: Object,
    required: true,
  },
  bestScore: {
    type: Number,
    default: 0,
  },
})

const emit = defineEmits(['select'])
</script>

<style scoped>
.radio-game-card {
  width: 100%;
  padding: 0.85rem 0.95rem;
  border: 1.5px solid rgba(255, 255, 255, 0.1);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.025);
  color: #fff;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease, background 0.18s ease, border-color 0.18s ease;
  -webkit-tap-highlight-color: transparent;
}

.radio-game-card:hover,
.radio-game-card:active {
  transform: translateY(-1px);
}

.radio-game-card__inner {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  text-align: left;
}

.radio-game-card__emoji {
  font-size: 1.5rem;
  flex-shrink: 0;
  line-height: 1;
}

.radio-game-card__text {
  flex: 1;
  min-width: 0;
}

.radio-game-card__best {
  font-size: 0.55rem;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(255, 255, 255, 0.35);
  flex-shrink: 0;
  white-space: nowrap;
}

.radio-game-card__name {
  font-size: 0.9rem;
  font-weight: 900;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  transition: color 0.18s;
}

.radio-game-card__desc {
  font-size: 0.58rem;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.45);
  margin-top: 0.2rem;
  letter-spacing: 0.01em;
  transition: color 0.18s;
}

.radio-game-card--garden {
  border-color: rgba(68, 204, 102, 0.28);
  background: rgba(68, 204, 102, 0.04);
}

.radio-game-card--garden .radio-game-card__name {
  color: #44cc66;
}

.radio-game-card--garden:hover,
.radio-game-card--garden:active {
  border-color: #44cc66;
  background: rgba(68, 204, 102, 0.13);
  box-shadow: 0 8px 24px rgba(68, 204, 102, 0.2);
}

.radio-game-card--trampoline {
  border-color: rgba(0, 215, 255, 0.28);
  background: rgba(0, 215, 255, 0.04);
}

.radio-game-card--trampoline .radio-game-card__name {
  color: #00d7ff;
}

.radio-game-card--trampoline:hover,
.radio-game-card--trampoline:active {
  border-color: #00d7ff;
  background: rgba(0, 215, 255, 0.14);
  box-shadow: 0 8px 24px rgba(0, 215, 255, 0.2);
}

.radio-game-card--birds {
  border-color: rgba(255, 47, 184, 0.28);
  background: rgba(255, 47, 184, 0.04);
}

.radio-game-card--birds .radio-game-card__name {
  color: #ff2fb8;
}

.radio-game-card--birds:hover,
.radio-game-card--birds:active {
  border-color: #ff2fb8;
  background: rgba(255, 47, 184, 0.14);
  box-shadow: 0 8px 24px rgba(255, 47, 184, 0.2);
}
</style>
