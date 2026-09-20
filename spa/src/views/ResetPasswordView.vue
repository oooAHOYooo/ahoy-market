<template>
  <div class="pw-wrap">
    <div class="pw-card">
      <h1 class="pw-title">New password time 🔐</h1>
      <p class="pw-sub">Make it strong-ish. Your future self will high-five you.</p>

      <form class="pw-form" @submit.prevent="submit">
        <label class="pw-label">
          New password
          <input v-model="password" class="pw-input" :type="show ? 'text' : 'password'" autocomplete="new-password" minlength="8" required />
        </label>
        <label class="pw-label">
          Confirm
          <input v-model="confirm" class="pw-input" :type="show ? 'text' : 'password'" autocomplete="new-password" minlength="8" required />
        </label>
        <label class="pw-show">
          <input v-model="show" type="checkbox" /> show password
        </label>
        <button type="submit" class="btn btn-primary" :disabled="loading || !canSubmit">
          <span v-if="!loading">Reset password 🎉</span>
          <span v-else>Resetting…</span>
        </button>
      </form>

      <div v-if="message" class="pw-msg" :class="{ 'pw-err': isError }">{{ message }}</div>
      <div class="pw-note"><router-link to="/login">Back to sign in</router-link></div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const token = ref('')
const password = ref('')
const confirm = ref('')
const show = ref(false)
const loading = ref(false)
const message = ref('')
const isError = ref(false)

const canSubmit = computed(() =>
  password.value && password.value.length >= 8 && password.value === confirm.value && !!token.value
)

onMounted(() => {
  token.value = route.query.token || ''
  if (!token.value) {
    message.value = 'Missing reset token. Please request a new link.'
    isError.value = true
  }
})

async function submit() {
  if (password.value !== confirm.value) {
    message.value = 'Passwords do not match.'
    isError.value = true
    return
  }
  loading.value = true
  message.value = ''
  isError.value = false
  try {
    const base = import.meta.env.VITE_API_BASE || ''
    const r = await fetch(base + '/api/auth/password-reset/confirm', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ token: token.value, password: password.value }),
    })
    const data = await r.json().catch(() => ({}))
    if (!r.ok) {
      isError.value = true
      message.value = data.error === 'token_expired' ? 'That link expired. Request a new one?' : 'Reset failed. Try requesting a new link.'
      return
    }
    message.value = 'Password reset! Redirecting to sign in...'
    setTimeout(() => { window.location.href = '/login' }, 2000)
  } catch {
    isError.value = true
    message.value = 'Reset failed. Try requesting a new link.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.pw-wrap {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
}
.pw-card {
  width: 100%;
  max-width: 480px;
  background: rgba(20, 20, 28, 0.85);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 20px;
  padding: 32px 24px;
}
.pw-title {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 8px;
  text-align: center;
}
.pw-sub {
  margin: 0 0 24px;
  color: rgba(255,255,255,0.6);
  text-align: center;
  font-size: 14px;
  line-height: 1.5;
}
.pw-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.pw-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: rgba(255,255,255,0.5);
  margin-bottom: 6px;
}
.pw-input {
  width: 100%;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.06);
  color: #fff;
  font-size: 15px;
  outline: none;
  transition: border-color 0.2s;
  box-sizing: border-box;
}
.pw-input:focus {
  border-color: var(--accent-primary, #6ddcff);
}
.pw-show {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: rgba(255,255,255,0.5);
  cursor: pointer;
}
.pw-note {
  margin-top: 16px;
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  text-align: center;
}
.pw-note a {
  color: var(--accent-primary, #6ddcff);
  text-decoration: none;
}
.pw-note a:hover { text-decoration: underline; }
.pw-msg {
  margin-top: 16px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(16, 185, 129, 0.2);
  background: rgba(16, 185, 129, 0.05);
  color: #fff;
  font-size: 14px;
  text-align: center;
}
.pw-msg.pw-err {
  border-color: rgba(239, 68, 68, 0.2);
  background: rgba(239, 68, 68, 0.05);
  color: #f87171;
}
.btn {
  width: 100%;
  padding: 14px;
  border-radius: 12px;
  border: none;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: opacity 0.2s;
}
.btn-primary {
  background: var(--accent-primary, #6ddcff);
  color: #111;
}
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

</style>
