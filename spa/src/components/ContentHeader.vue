<template>
  <header class="content-header" :class="{ 'has-actions': $slots.actions }">
    <div class="header-main">
      <span v-if="kicker" class="header-kicker">{{ kicker }}</span>
      <h1 class="header-title">{{ title }}</h1>
      <p v-if="subtitle" class="header-subtitle">{{ truncatedSubtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="header-actions">
      <slot name="actions"></slot>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  kicker: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  }
})

const truncatedSubtitle = computed(() =>
  props.subtitle.length > 70 ? props.subtitle.slice(0, 67) + '...' : props.subtitle
)
</script>

<style scoped>
.content-header {
  padding: 3rem 0 2.5rem 6px;
  margin-bottom: 1.5rem;
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  align-items: flex-start;
  text-align: left;

  /* Subtle glass effect — matches bottom now-playing bar aesthetic */
  background: rgba(0, 0, 0, 0.15);

  /* Soft blur for glass effect (Safari + modern browsers) */
  backdrop-filter: blur(20px) saturate(120%);
  -webkit-backdrop-filter: blur(20px) saturate(120%);

  border-bottom: 1px solid rgba(255, 255, 255, 0.08);

  /* Subtle depth shadow */
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2);

  /* Entrance animation */
  animation: header-in 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes header-in {
  from {
    opacity: 0;
    transform: translateY(15px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.header-main {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  align-items: flex-start;
  width: 100%;
}


.header-kicker {
  display: block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: #6ddcff;
  margin-bottom: -0.5rem;
}

.header-title {
  font-size: clamp(2.8rem, 8vw, 4.2rem);
  font-weight: 900;
  letter-spacing: -0.04em;
  color: #fff;
  line-height: 1;
  margin: 0;
}

.header-subtitle {
  font-size: 15px;
  font-weight: 300;
  color: var(--text-muted, rgba(255, 255, 255, 0.5));
  margin: 0;
  line-height: 1.6;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

/* Mobile adjustments */
@media (max-width: 768px) {
  .content-header {
    padding: 2.5rem 0 1.25rem 6px;
    margin-bottom: 1.5rem;
    align-items: flex-start;
  }

  .header-main {
    align-items: flex-start;
  }

  .header-title {
    font-size: 2.2rem;
  }

  .header-subtitle {
    font-size: 13px;
    line-height: 1.4;
  }

  .header-actions {
    gap: 12px;
  }
}

/* Desktop layout: full column with actions below */
@media (min-width: 769px) {
  .content-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1.5rem;
    padding: 2rem 0 1.5rem 24px;
    margin-bottom: 1.75rem;
  }

  .header-main {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }


  .header-title {
    font-size: clamp(2.2rem, 3.5vw, 2.8rem);
  }

  .header-subtitle {
    font-size: 14px;
    font-weight: 300;
    color: rgba(255, 255, 255, 0.65);
    line-height: 1.4;
  }

  .header-actions {
    margin-left: 0;
  }
}
</style>
