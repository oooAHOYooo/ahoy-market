<template>
  <div class="onboarding-page">
    <div class="onboarding-container">
      <Transition name="onboarding-card" mode="out-in">
        <!-- Step 1: Welcome & Name -->
        <div v-if="step === 1" :key="1" class="onboarding-card glass-morphism">
          <div class="onboarding-header">
            <span class="step-indicator">Step 1 of 3</span>
            <h1>Welcome aboard!</h1>
            <p>What should we call you on Ahoy? You can use your real name or a nickname.</p>
          </div>
          
          <div class="onboarding-body">
            <div class="field-group">
              <label for="display_name">Display Name</label>
              <input 
                id="display_name"
                v-model="displayName" 
                type="text" 
                placeholder="e.g. Space Cowboy"
                @keydown.enter="nextStep"
              >
            </div>
          </div>

          <div class="onboarding-footer">
            <button class="btn-primary" :disabled="!displayName" @click="nextStep">
              Next Step <i class="fas fa-arrow-right"></i>
            </button>
          </div>
        </div>

        <!-- Step 2: Choose your Badge -->
        <div v-else-if="step === 2" :key="2" class="onboarding-card glass-morphism">
          <div class="onboarding-header">
            <span class="step-indicator">Step 2 of 3</span>
            <h1>Choose your Badge</h1>
            <p>Pick an icon that represents your vibe. This will be your profile picture for now.</p>
          </div>

          <div class="onboarding-body">
            <div class="badge-grid">
              <button 
                v-for="badge in badges" 
                :key="badge.id"
                class="badge-item"
                :class="{ active: selectedBadge === badge.id }"
                :style="{ '--badge-color': badge.color }"
                @click="selectBadge(badge.id)"
              >
                <div class="badge-icon-wrapper">
                  <i :class="badge.icon"></i>
                </div>
                <span class="badge-label">{{ badge.name }}</span>
              </button>
            </div>
          </div>

          <div class="onboarding-footer">
            <button class="btn-secondary" @click="prevStep">Back</button>
            <button class="btn-primary" :disabled="!selectedBadge" @click="nextStep">
              Looking good! <i class="fas fa-arrow-right"></i>
            </button>
          </div>
        </div>

        <!-- Step 3: Bio -->
        <div v-else-if="step === 3" :key="3" class="onboarding-card glass-morphism">
          <div class="onboarding-header">
            <span class="step-indicator">Step 3 of 3</span>
            <h1>The final touch</h1>
            <p>Tell the community a little about yourself in one sentence.</p>
          </div>

          <div class="onboarding-body">
            <div class="field-group">
              <label for="bio">Your Bio</label>
              <textarea 
                id="bio"
                v-model="bio" 
                placeholder="e.g. Just here for the vibes and lo-fi beats..."
                rows="3"
                maxlength="160"
              ></textarea>
              <span class="char-count">{{ bio.length }} / 160</span>
            </div>
          </div>

          <div class="onboarding-footer">
            <button class="btn-secondary" @click="prevStep">Back</button>
            <button class="btn-primary" :disabled="loading" @click="finishOnboarding">
              {{ loading ? 'Saving...' : 'Start Exploring!' }}
            </button>
          </div>
        </div>
      </Transition>
      
      <div v-if="step < 4" class="skip-onboarding">
        <button @click="skip">Skip for now</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { playTapChime, playSaveChime } from '../composables/useSaveChime'

const router = useRouter()
const auth = useAuth()

const step = ref(1)
const loading = ref(false)
const displayName = ref(auth.user.value?.display_name || '')
const bio = ref('')
const selectedBadge = ref(null)

const badges = [
  { id: 'star', icon: 'fas fa-star', name: 'Scout', color: 'linear-gradient(135deg, #FF00CC, #3333FF)' },
  { id: 'record', icon: 'fas fa-compact-disc', name: 'Collector', color: 'linear-gradient(135deg, #00F2FF, #0062FF)' },
  { id: 'cassette', icon: 'fas fa-tape', name: 'Lover', color: 'linear-gradient(135deg, #FFF200, #FF9000)' },
  { id: 'bolt', icon: 'fas fa-bolt', name: 'Energetic', color: 'linear-gradient(135deg, #00FF88, #00A2FF)' },
  { id: 'heart', icon: 'fas fa-heart', name: 'Vibrant', color: 'linear-gradient(135deg, #FF0080, #7928CA)' },
  { id: 'camera', icon: 'fas fa-camera', name: 'Visual', color: 'linear-gradient(135deg, #7928CA, #FF00CC)' },
  { id: 'headphones', icon: 'fas fa-headphones', name: 'Listener', color: 'linear-gradient(135deg, #0070F3, #00DFD8)' },
  { id: 'crown', icon: 'fas fa-crown', name: 'Classic', color: 'linear-gradient(135deg, #F5A623, #F8E71C)' },
  { id: 'rocket', icon: 'fas fa-rocket', name: 'Pioneer', color: 'linear-gradient(135deg, #FF4D4D, #F9CB28)' },
  { id: 'palette', icon: 'fas fa-palette', name: 'Creator', color: 'linear-gradient(135deg, #7B2FF7, #F107A3)' },
  { id: 'moon', icon: 'fas fa-moon', name: 'Dreamer', color: 'linear-gradient(135deg, #2D3436, #000000)' },
  { id: 'alien', icon: 'fas fa-alien', name: 'Unique', color: 'linear-gradient(135deg, #00FF00, #008000)' },
]

function nextStep() {
  playTapChime()
  step.value++
}

function prevStep() {
  playTapChime()
  step.value--
}

function selectBadge(id) {
  playTapChime()
  selectedBadge.value = id
}

async function finishOnboarding() {
  loading.value = true
  const badge = badges.find(b => b.id === selectedBadge.value)
  
  const result = await auth.updateProfile({
    display_name: displayName.value,
    avatar_url: badge?.icon || 'fas fa-user', // Store the icon class
    bio: bio.value,
    preferences: {
      onboarding_complete: true,
      selected_badge: selectedBadge.value
    }
  })

  if (result.success) {
    playSaveChime()
    window.dispatchEvent(new CustomEvent('ahoy:toast', {
      detail: { message: 'Setup complete!', type: 'success' }
    }))
    router.push('/')
  } else {
    window.dispatchEvent(new CustomEvent('ahoy:toast', {
      detail: { message: result.error || 'Something went wrong', type: 'error' }
    }))
  }
  loading.value = false
}

async function skip() {
  playTapChime()
  loading.value = true
  try {
    if (auth.isLoggedIn.value) {
      await auth.updateProfile({
        preferences: {
          onboarding_complete: true
        }
      })
    }
  } catch (err) {
    console.error('Failed to skip onboarding:', err)
  } finally {
    loading.value = false
    router.push('/')
  }
}

onMounted(() => {
  // Ensure user is logged in
  if (!auth.isLoggedIn.value) {
    router.push('/login')
  }
})
</script>

<style scoped>
.onboarding-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: #0e0e10;
}

.onboarding-container {
  width: 100%;
  max-width: 540px;
}

.onboarding-card {
  padding: 40px;
  border-radius: 32px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 
    0 20px 50px -10px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.15),
    inset 0 0 40px rgba(0, 0, 0, 0.2);
  position: relative;
  overflow: hidden;
}

.onboarding-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; height: 100%;
  background: linear-gradient(180deg, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0) 100%);
  pointer-events: none;
  z-index: 0;
}

.onboarding-card > * {
  position: relative;
  z-index: 1;
}

.glass-morphism {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(40px) saturate(180%);
  -webkit-backdrop-filter: blur(40px) saturate(180%);
}

.onboarding-header {
  margin-bottom: 32px;
}

.step-indicator {
  display: block;
  font-size: 13px;
  font-weight: 700;
  color: var(--accent-primary, #6ddcff);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 8px;
}

.onboarding-header h1 {
  font-size: 32px;
  font-weight: 800;
  color: #fff;
  margin: 0 0 12px;
  letter-spacing: -0.02em;
}

.onboarding-header p {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.6;
  margin: 0;
}

.onboarding-body {
  margin-bottom: 40px;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.field-group label {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.9);
}

.field-group input, 
.field-group textarea {
  width: 100%;
  padding: 16px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: #fff;
  font-size: 16px;
  outline: none;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.field-group input:focus,
.field-group textarea:focus {
  border-color: rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 
    0 0 20px rgba(0, 0, 0, 0.5),
    0 5px 15px rgba(0, 0, 0, 0.3);
}

.char-count {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
  text-align: right;
  margin-top: 4px;
}

/* Badge Grid */
.badge-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.badge-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 8px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 16px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.badge-item:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateY(-4px) scale(1.05);
}

.badge-item.active {
  background: rgba(109, 220, 255, 0.15);
  border-color: var(--accent-primary, #6ddcff);
  box-shadow: 0 8px 16px rgba(109, 220, 255, 0.2);
  transform: scale(1.1);
}

.badge-icon-wrapper {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--badge-color);
  border-radius: 50%;
  color: #fff;
  font-size: 20px;
  margin-bottom: 4px;
  position: relative;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  transition: all 0.3s ease;
}

.badge-item:hover .badge-icon-wrapper {
  box-shadow: 0 0 20px var(--badge-color);
  transform: scale(1.1);
}

.badge-item.active .badge-icon-wrapper {
  box-shadow: 0 0 25px var(--badge-color);
  transform: scale(1.15);
  border: 2px solid rgba(255, 255, 255, 0.5);
}

.badge-icon-wrapper::after {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  border-radius: 50%;
  background: linear-gradient(180deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0) 50%, rgba(0,0,0,0.1) 100%);
  pointer-events: none;
}

.badge-label {
  font-size: 11px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.badge-item.active .badge-label {
  color: var(--accent-primary, #6ddcff);
}

/* Footer Buttons */
.onboarding-footer {
  display: flex;
  gap: 12px;
}

.btn-primary {
  flex: 2;
  padding: 16px;
  border-radius: 14px;
  background: var(--accent-primary, #6ddcff);
  color: #111;
  font-size: 16px;
  font-weight: 700;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  transition: all 0.2s ease;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary:not(:disabled):hover {
  transform: translateY(-2px);
  filter: brightness(1.1);
  box-shadow: 0 8px 20px rgba(109, 220, 255, 0.3);
}

.btn-secondary {
  flex: 1;
  padding: 16px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  font-size: 16px;
  font-weight: 600;
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.12);
}

.skip-onboarding {
  text-align: center;
  margin-top: 24px;
}

.skip-onboarding button {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.3);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  padding: 8px 16px;
  border-radius: 8px;
  transition: color 0.2s ease;
}

.skip-onboarding button:hover {
  color: rgba(255, 255, 255, 0.6);
}

/* Nintendo-style transitions */
.onboarding-card-enter-active {
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}
.onboarding-card-leave-active {
  transition: all 0.2s ease;
}
.onboarding-card-enter-from {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}
.onboarding-card-leave-to {
  opacity: 0;
  transform: translateY(-20px) scale(0.95);
}

@media (max-width: 480px) {
  .badge-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
