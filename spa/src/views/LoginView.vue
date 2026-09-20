<template>
  <div class="auth-page">
    
    <!-- Rotating Animated GIFs Background -->
    <div class="auth-bg-container">
      <div 
        v-for="(gif, index) in gifs" 
        :key="index"
        class="auth-bg-item"
        :class="{ active: currentBgIndex === index }"
        :style="{ backgroundImage: `url(${gif})` }"
      ></div>
      <!-- Fog Overlays -->
      <div class="auth-fog-overlay-1"></div>
      <div class="auth-fog-overlay-2"></div>
      <div class="auth-fog-overlay-3"></div>
    </div>

    <div class="auth-card">
      <div class="auth-logo">
        <img :src="logoUrl" alt="Ahoy" class="auth-logo-img" />
      </div>

      <!-- Toggle login / signup -->
      <div class="auth-tabs">
        <button :class="{ active: mode === 'login' }" @click="mode = 'login'">Log In</button>
        <button :class="{ active: mode === 'signup' }" @click="mode = 'signup'">Sign Up</button>
      </div>

      <form @submit.prevent="onSubmit" class="auth-form">
        <div class="auth-field" v-if="mode === 'signup'">
          <label for="reg-username">Username</label>
          <input
            id="reg-username"
            v-model="username"
            type="text"
            placeholder="choose a username"
            autocomplete="username"
          />
        </div>
        <div class="auth-field">
          <label for="email">{{ mode === 'login' ? 'Email or username' : 'Email' }}</label>
          <input
            id="email"
            v-model="identifier"
            :type="mode === 'login' ? 'text' : 'email'"
            :placeholder="mode === 'login' ? 'Username' : 'you@example.com'"
            :autocomplete="mode === 'login' ? 'username' : 'email'"
            required
          />
        </div>
        <div class="auth-field">
          <label for="password">Password</label>
          <input id="password" v-model="password" :type="showPassword ? 'text' : 'password'" :placeholder="mode === 'login' ? 'Password' : '••••••••'" autocomplete="current-password" required />
        </div>
        <div class="auth-field" v-if="mode === 'signup'">
          <label for="phone">Phone Number (optional, for SMS notifications)</label>
          <input
            id="phone"
            v-model="phoneNumber"
            type="tel"
            placeholder="+1 (555) 000-0000"
            autocomplete="tel"
          />
        </div>
        <div class="field-show-password">
          <button type="button" class="show-password-toggle" @click="showPassword = !showPassword">
            {{ showPassword ? 'Hide' : 'Show' }} Password
          </button>
        </div>
        <p v-if="mode === 'login'" class="auth-forgot">
          <router-link to="/auth/forgot">Forgot password?</router-link>
        </p>

        <div class="auth-error" v-if="error">{{ error }}</div>

        <button type="submit" class="auth-submit" :disabled="loading">
          <i v-if="loading" class="fas fa-spinner fa-spin"></i>
          <span v-else>{{ mode === 'login' ? 'Log In' : 'Create Account' }}</span>
        </button>
      </form>

      <button class="auth-skip" @click="router.push('/')">
        Continue as Guest
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import logoUrl from '@/assets/u_ahoy23.png'

const router = useRouter()
const route = useRoute()
const auth = useAuth()

const gifs = [
  'https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExY3hvaWNndHFtOGVmdWFvYW01bDNlMjcwOGs0MG5tYWd5ZDF4NW92OCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/1JsSOW3M1y8xefYZAD/giphy.gif',
  'https://media2.giphy.com/media/v1.Y2lkPTc5MGI3NjExbTVwaGhobWVhNmh0Z2NwYWU3dDBtMDM5NHNqaDh2NXNzdWxsZTBoMCZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/xWC0BCZtkDxE869erD/giphy.gif',
  'https://media0.giphy.com/media/v1.Y2lkPTc5MGI3NjExbmRqeHF3NzRsdXlrZGQ5MmptazN4Y2dtdzkxNnFteG9rOGZoOXM0MiZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3og0ISzBpn0nNJE3Ac/giphy.gif'
]
const currentBgIndex = ref(0)
let bgInterval

onMounted(() => {
  bgInterval = setInterval(() => {
    currentBgIndex.value = (currentBgIndex.value + 1) % gifs.length
  }, 6000)
})

onUnmounted(() => {
  if (bgInterval) clearInterval(bgInterval)
})

const mode = ref(route.query.signup ? 'signup' : 'login')
watch(() => route.query.signup, (signup) => {
  if (signup) mode.value = 'signup'
})
const identifier = ref('')
const password = ref('')
const username = ref('')
const phoneNumber = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

async function onSubmit() {
  loading.value = true
  error.value = ''
  let result
  if (mode.value === 'login') {
    result = await auth.login(identifier.value, password.value)
  } else {
    result = await auth.signup(identifier.value, password.value, username.value, phoneNumber.value)
  }
  loading.value = false
  if (result.success) {
    window.dispatchEvent(new CustomEvent('ahoy:toast', {
      detail: { message: mode.value === 'login' ? 'Welcome back!' : 'Account created!', type: 'success' }
    }))
    if (mode.value === 'signup') {
      router.push('/onboarding')
    } else {
      router.push('/')
    }
  } else {
    error.value = result.error || 'An error occurred'
  }
}
</script>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 12px;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;
}

.auth-bg-container {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
  pointer-events: none;
}

.auth-bg-item {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-size: cover;
  background-position: center;
  background-repeat: no-repeat;
  opacity: 0;
  filter: blur(8px);
  transform: scale(1.15);
  transition: opacity 3s ease-in-out, filter 3s ease-in-out, transform 6s linear;
  mix-blend-mode: screen;
}

.auth-bg-item.active {
  opacity: 0.35;
  filter: blur(4px);
  transform: scale(1.05);
}

.auth-fog-overlay-1 {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(to bottom, rgba(14, 14, 16, 0.6) 0%, transparent 50%, rgba(14, 14, 16, 0.95) 100%);
}

.auth-fog-overlay-2 {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: linear-gradient(to top, rgba(14, 14, 16, 1) 0%, rgba(14, 14, 16, 0.7) 30%, transparent 100%);
}

.auth-fog-overlay-3 {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  background: radial-gradient(ellipse at center, rgba(255, 255, 255, 0.05) 0%, rgba(14, 14, 16, 0.6) 50%, rgba(14, 14, 16, 1) 100%);
}

.auth-card {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 480px;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 32px;
  padding: 40px 32px;
  box-shadow: 
    0 20px 50px -10px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    inset 0 0 40px rgba(0, 0, 0, 0.2);
  transition: transform 0.5s ease, border-color 0.5s ease;
  overflow: hidden;
}

.auth-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 100%;
  background: linear-gradient(180deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0) 100%);
  pointer-events: none;
  z-index: 0;
}

.auth-card > * {
  position: relative;
  z-index: 1;
}

.auth-card:hover {
  border-color: rgba(255, 255, 255, 0.15);
  transform: scale(1.01);
}
.auth-logo {
  text-align: center;
  margin-bottom: 24px;
}
.auth-logo-img {
  display: block;
  margin: 0 auto;
  height: 48px;
  width: auto;
  object-fit: contain;
  filter: drop-shadow(0 0 20px rgba(255, 255, 255, 0.15));
}
.auth-logo h1 {
  font-size: 24px;
  font-weight: 700;
  color: #fff;
  margin: 8px 0 0;
}
.auth-tabs {
  display: flex;
  background: rgba(255,255,255,0.06);
  border-radius: 10px;
  padding: 3px;
  margin-bottom: 20px;
}
.auth-tabs button {
  flex: 1;
  background: none;
  border: none;
  color: rgba(255,255,255,0.5);
  font-size: 14px;
  font-weight: 600;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}
.auth-tabs button.active {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
}
.auth-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
.auth-field label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: rgba(255,255,255,0.5);
  margin-bottom: 6px;
}
.auth-field input {
  width: 100%;
  padding: 12px 14px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.2);
  background: rgba(255, 255, 255, 0.05);
  color: #fff;
  font-size: 15px;
  outline: none;
  transition: all 0.3s ease;
  box-sizing: border-box;
  backdrop-filter: blur(10px);
}
.auth-field input:focus {
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 
    0 0 20px rgba(0, 0, 0, 0.5),
    0 5px 15px rgba(0, 0, 0, 0.3);
}
.auth-field input::placeholder { color: rgba(255,255,255,0.25); }

.field-show-password {
  display: flex;
  justify-content: flex-end;
  margin: -10px 0 15px;
}

.show-password-toggle {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.4);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.show-password-toggle:hover {
  color: rgba(255, 255, 255, 0.8);
  background: rgba(255, 255, 255, 0.05);
}

.auth-forgot {
  text-align: center;
  margin: 8px 0 0;
  font-size: 14px;
}
.auth-forgot a {
  color: var(--accent-primary, #6ddcff);
  text-decoration: none;
}
.auth-forgot a:hover { text-decoration: underline; }
.auth-error {
  color: #f87171;
  font-size: 13px;
  text-align: center;
}
.auth-submit {
  width: 100%;
  padding: 14px;
  border-radius: 12px;
  border: none;
  background: var(--accent-primary, #6ddcff);
  color: #111;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s ease;
}
.auth-submit:not(:disabled):hover {
  transform: translateY(-2px);
  filter: brightness(1.1);
  box-shadow: 0 8px 20px rgba(109, 220, 255, 0.3);
}
.auth-submit:disabled { opacity: 0.5; cursor: not-allowed; }
.auth-submit:active { transform: translateY(0); }
.auth-skip {
  display: block;
  width: 100%;
  padding: 16px;
  border-radius: 12px;
  border: 2px solid rgba(255,255,255,0.2);
  background: rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.9);
  font-size: 16px;
  font-weight: 600;
  margin-top: 16px;
  cursor: pointer;
  text-align: center;
  transition: all 0.2s ease;
}
.auth-skip:hover {
  background: rgba(255,255,255,0.12);
  border-color: rgba(255,255,255,0.3);
  transform: translateY(-2px);
}
.auth-skip:active {
  transform: translateY(0);
  background: rgba(255,255,255,0.15);
}


</style>
