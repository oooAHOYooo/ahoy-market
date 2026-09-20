<template>
  <div class="spinner-container">
    <div class="spinner">
      <svg viewBox="0 0 50 50">
        <circle cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="3" stroke-dasharray="31.4 94.2"></circle>
      </svg>
    </div>
    <p v-if="label" class="spinner-label">{{ label }}</p>
  </div>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    default: 'Loading...'
  }
})
</script>

<style scoped>
.spinner-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  min-height: 200px;
}

.spinner {
  width: 40px;
  height: 40px;
  color: var(--accent-primary, #6ddcff);
  margin-bottom: 1rem;
}

.spinner svg {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.spinner-label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
  margin: 0;
}
</style>
