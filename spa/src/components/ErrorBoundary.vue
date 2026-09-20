<template>
  <div v-if="hasError" class="error-boundary">
    <div class="error-container">
      <i class="fas fa-exclamation-triangle error-icon"></i>
      <h2>Something went wrong</h2>
      <p>{{ errorMessage }}</p>
      <div class="error-actions">
        <button @click="reset" class="error-btn">Try Again</button>
        <router-link to="/" class="error-btn secondary">Go Home</router-link>
      </div>
      <details v-if="isDev" class="error-details">
        <summary>Technical Details</summary>
        <pre>{{ fullError }}</pre>
      </details>
    </div>
  </div>
  <slot v-else />
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const hasError = ref(false)
const errorMessage = ref('An unexpected error occurred. Please try again.')
const fullError = ref('')
const isDev = import.meta.env.DEV

const router = useRouter()

function reset() {
  hasError.value = false
  errorMessage.value = 'An unexpected error occurred. Please try again.'
  fullError.value = ''
}

// Vue 3 error handler pattern (use at root App.vue)
const errorHandler = (err) => {
  console.error('Error caught:', err)
  hasError.value = true
  fullError.value = err.toString()

  // Determine user-friendly message
  if (err.message.includes('network') || err.message.includes('fetch')) {
    errorMessage.value = 'Network error. Check your connection and try again.'
  } else if (err.message.includes('404')) {
    errorMessage.value = 'Page or resource not found.'
  } else {
    errorMessage.value = 'An unexpected error occurred. Please try again.'
  }
}

defineExpose({ errorHandler, reset })
</script>

<style scoped>
.error-boundary {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(20,20,28,0.95), rgba(10,10,15,0.98));
  padding: 2rem;
}

.error-container {
  text-align: center;
  max-width: 500px;
  padding: 2rem;
  background: rgba(255,255,255,0.02);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 1.5rem;
  backdrop-filter: blur(10px);
}

.error-icon {
  font-size: 3rem;
  color: #ef4444;
  margin-bottom: 1rem;
  display: block;
}

.error-container h2 {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 0.75rem;
  color: white;
}

.error-container p {
  color: rgba(255,255,255,0.7);
  margin: 0 0 1.5rem;
  line-height: 1.5;
}

.error-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.error-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  border: none;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  text-decoration: none;
  display: inline-block;
}

.error-btn {
  background: #ef4444;
  color: white;
}

.error-btn:hover {
  background: #dc2626;
  transform: translateY(-2px);
}

.error-btn.secondary {
  background: rgba(255,255,255,0.1);
  color: #6ddcff;
  border: 1px solid rgba(109,220,255,0.2);
}

.error-btn.secondary:hover {
  background: rgba(109,220,255,0.1);
}

.error-details {
  margin-top: 1rem;
  text-align: left;
  border-top: 1px solid rgba(255,255,255,0.1);
  padding-top: 1rem;
}

.error-details summary {
  cursor: pointer;
  color: rgba(255,255,255,0.6);
  font-size: 0.85rem;
  font-weight: 600;
}

.error-details pre {
  margin-top: 0.75rem;
  padding: 0.75rem;
  background: rgba(0,0,0,0.3);
  border-radius: 0.5rem;
  color: #fca5a5;
  font-size: 0.75rem;
  overflow-x: auto;
}
</style>
