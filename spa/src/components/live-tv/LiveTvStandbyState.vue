<template>
  <div class="ltv-empty-state">
    <div class="ltv-empty-art" aria-hidden="true">
      <div class="ltv-empty-ring"></div>
      <div class="ltv-empty-core">
        <i class="fas fa-broadcast-tower"></i>
      </div>
    </div>
    <span class="ltv-empty-kicker">{{ kicker }}</span>
    <h3 class="ltv-empty-title">{{ title }}</h3>
    <p class="ltv-empty-copy">{{ body }}</p>
    <button v-if="showRetry" type="button" class="ltv-empty-retry" @click="$emit('retry')">
      {{ retryLabel }}
    </button>
  </div>
</template>

<script setup>
defineProps({
  kicker: {
    type: String,
    default: 'Stand By',
  },
  title: {
    type: String,
    default: 'Choose a channel to start watching',
  },
  body: {
    type: String,
    default: 'AHOY TV will appear here when a channel is ready.',
  },
  showRetry: {
    type: Boolean,
    default: false,
  },
  retryLabel: {
    type: String,
    default: 'Retry',
  },
})

defineEmits(['retry'])
</script>

<style scoped>
.ltv-empty-state {
  width: min(100%, 420px);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 10px;
}

.ltv-empty-art {
  position: relative;
  width: 120px;
  height: 120px;
  display: grid;
  place-items: center;
  margin-bottom: 8px;
}

.ltv-empty-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  border: 1px solid rgba(137, 180, 255, 0.26);
  background:
    radial-gradient(circle, rgba(76, 132, 255, 0.2) 0%, rgba(76, 132, 255, 0) 68%),
    linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02));
  box-shadow:
    inset 0 0 30px rgba(86, 150, 255, 0.16),
    0 12px 30px rgba(0, 0, 0, 0.35);
}

.ltv-empty-core {
  position: relative;
  width: 76px;
  height: 76px;
  border-radius: 22px;
  display: grid;
  place-items: center;
  color: #f5f7ff;
  font-size: 30px;
  background: linear-gradient(180deg, rgba(88, 120, 232, 0.92), rgba(48, 75, 168, 0.92));
  box-shadow:
    0 14px 28px rgba(33, 52, 120, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.18);
}

.ltv-empty-kicker {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: rgba(154, 193, 255, 0.88);
}

.ltv-empty-title {
  margin: 0;
  font-size: 26px;
  line-height: 1.08;
  font-weight: 800;
  color: #f7f9ff;
}

.ltv-empty-copy {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: rgba(220, 227, 242, 0.72);
  max-width: 32ch;
}

.ltv-empty-retry {
  margin-top: 6px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 999px;
  padding: 10px 16px;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  font-weight: 700;
  cursor: pointer;
}

@media (max-width: 768px), (pointer: coarse) {
  .ltv-empty-state {
    width: min(100%, 340px);
  }

  .ltv-empty-art {
    width: 96px;
    height: 96px;
  }

  .ltv-empty-core {
    width: 64px;
    height: 64px;
    font-size: 24px;
  }

  .ltv-empty-title {
    font-size: 22px;
  }

  .ltv-empty-copy {
    font-size: 13px;
  }

  .ltv-empty-retry {
    padding: 9px 14px;
    font-size: 13px;
  }
}
</style>
