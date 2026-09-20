<template>
  <div class="pw-wrap">
    <div class="pw-card">
      <h1 class="pw-title">Forgot your password? No stress 🥳</h1>
      <p class="pw-sub">Drop your email and we'll send you a magic reset link (expires in 1 hour).</p>

      <form class="pw-form" @submit.prevent="submit">
        <label class="pw-label">
          Email
          <input v-model.trim="email" class="pw-input" type="email" autocomplete="email" placeholder="you@example.com" required />
        </label>
        <button type="submit" class="btn btn-primary" :disabled="loading">
          <span v-if="!loading">Send reset link 🎉</span>
          <span v-else>Sending…</span>
        </button>
      </form>

      <div v-if="message" class="pw-msg">{{ message }}</div>
      <div class="pw-note">Tip: We'll always show success here (even if the email isn't registered) to keep accounts private.</div>
      <div class="pw-note"><router-link to="/login">Back to sign in</router-link></div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { apiFetch } from '../composables/useApi'

const email = ref('')
const loading = ref(false)
const message = ref('')

async function submit() {
  loading.value = true
  message.value = ''
  try {
    const data = await apiFetch('/api/auth/password-reset/request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value }),
    }).catch(() => ({}))
    message.value = data?.message || "If that email exists, we sent a reset link."
  } catch {
    message.value = "If that email exists, we sent a reset link."
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
.pw-note {
  margin-top: 16px;
  font-size: 12px;
  color: rgba(255,255,255,0.4);
  text-align: center;
  line-height: 1.4;
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
  border: 1px solid rgba(109, 220, 255, 0.2);
  background: rgba(109, 220, 255, 0.05);
  color: #fff;
  font-size: 14px;
  text-align: center;
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
