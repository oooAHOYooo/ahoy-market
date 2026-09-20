<template>
  <div class="auth-page">
    <div class="auth-card" style="text-align: center">
      <div v-if="!error" class="spinner-wrap">
        <i class="fas fa-spinner fa-spin" style="font-size: 40px; color: var(--accent-primary)"></i>
        <p style="margin-top: 16px; color: rgba(255,255,255,0.7); font-size: 14px">
          Completing sign-in...
        </p>
      </div>
      <div v-else class="error-wrap">
        <p style="color: #f87171; margin: 0; font-size: 14px">{{ error }}</p>
        <p style="color: rgba(255,255,255,0.5); margin-top: 12px; font-size: 12px">
          Redirecting to sign-in page...
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchMe } from '../composables/useAuth'

const router = useRouter()
const error = ref('')

onMounted(async () => {
  try {
    // Fetch current user session (server set the cookie already)
    await fetchMe()

    // Dispatch success toast
    window.dispatchEvent(new CustomEvent('ahoy:toast', {
      detail: { message: 'Signed in with Google!', type: 'success' }
    }))

    // Redirect to home
    router.push('/')
  } catch (err) {
    error.value = 'Sign-in failed. Please try again.'
    // Redirect to login after a brief delay
    setTimeout(() => router.push('/login'), 2000)
  }
})
</script>

<style scoped>
.auth-page {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 20px;
}

.auth-card {
  border-radius: 16px;
  border: 1px solid rgba(255,255,255,0.10);
  background: rgba(255,255,255,0.03);
  padding: 40px 32px;
  max-width: 400px;
  width: 100%;
}

.spinner-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.error-wrap {
  display: flex;
  flex-direction: column;
}
</style>
