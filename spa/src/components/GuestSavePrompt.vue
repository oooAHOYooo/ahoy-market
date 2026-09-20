<template>
  <Teleport to="body">
    <Transition name="slide-up">
      <!-- Toast-style notification (softer than modal) -->
      <div v-if="visible && style === 'toast'" class="guest-save-toast" role="alert">
        <div class="toast-content">
          <p class="toast-text">
            <i class="fas fa-bookmark"></i>
            Saved to this device. Create an account to sync everywhere.
          </p>
          <div class="toast-actions">
            <button type="button" class="toast-btn secondary" @click="dismiss">Not now</button>
            <router-link to="/login?signup=1" class="toast-btn primary" @click="() => { trackEvent('signup_prompt_cta_clicked', { prompt_style: 'toast' }); dismiss() }">Create account</router-link>
          </div>
        </div>
        <button type="button" class="toast-close" aria-label="Close" @click="dismiss">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <!-- Modal-style notification (for critical saves) -->
      <div v-else-if="visible && style === 'modal'" class="guest-save-modal" role="dialog" aria-label="Create account to sync saves">
        <div class="modal-inner">
          <p class="modal-text">
            <i class="fas fa-bookmark"></i>
            Saved to this device. Create an account to sync everywhere.
          </p>
          <div class="modal-actions">
            <button type="button" class="modal-dismiss" @click="dismissSessionOnly">Not now</button>
            <router-link to="/login?signup=1" class="modal-cta" @click="() => { trackEvent('signup_prompt_cta_clicked', { prompt_style: 'modal' }); dismiss() }">Create account</router-link>
          </div>
          <label class="modal-checkbox">
            <input type="checkbox" v-model="dontShowWeek" @change="updateDismissal">
            Don't show for 7 days
          </label>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useAuth } from '../composables/useAuth'
import { trackEvent } from '../composables/useAnalytics'

const auth = useAuth()
const visible = ref(false)
const style = ref('toast') // 'toast' or 'modal'
const dontShowWeek = ref(false)

const STORAGE_KEY_PROMPT = 'ahoy:guest-prompt'
const STORAGE_KEY_7DAY = 'ahoy:guest-prompt-7day'
const HOUR_24_MS = 24 * 60 * 60 * 1000
const DAYS_7_MS = 7 * 24 * 60 * 60 * 1000

function isPromptDismissed() {
  // Check 7-day dismissal
  const sevenDay = localStorage.getItem(STORAGE_KEY_7DAY)
  if (sevenDay) {
    const expiry = parseInt(sevenDay, 10)
    if (Date.now() < expiry) return true
  }

  // Check 24-hour dismissal
  const dismissed = localStorage.getItem(STORAGE_KEY_PROMPT)
  if (dismissed) {
    const expiry = parseInt(dismissed, 10)
    if (Date.now() < expiry) return true
  }

  return false
}

function show() {
  if (!isPromptDismissed()) {
    visible.value = true
    trackEvent('signup_prompted', { prompt_style: style.value })
  }
}

function dismiss() {
  trackEvent('signup_prompt_dismissed', { prompt_style: style.value, suppress_days: dontShowWeek.value ? 7 : 1 })
  visible.value = false
  dismiss24Hour()
  if (dontShowWeek.value) {
    dismiss7Day()
  }
}

function dismissSessionOnly() {
  trackEvent('signup_prompt_dismissed', { prompt_style: style.value, suppress_days: 0 })
  visible.value = false
  dismiss24Hour()
}

function dismiss24Hour() {
  const expiry = Date.now() + HOUR_24_MS
  localStorage.setItem(STORAGE_KEY_PROMPT, String(expiry))
}

function dismiss7Day() {
  const expiry = Date.now() + DAYS_7_MS
  localStorage.setItem(STORAGE_KEY_7DAY, String(expiry))
}

function updateDismissal() {
  if (dontShowWeek.value) {
    dismiss7Day()
  } else {
    localStorage.removeItem(STORAGE_KEY_7DAY)
  }
}

function onContextualEvent(event) {
  // Show prompt when guest tries to save data — style comes from the event detail
  if (!auth.isLoggedIn.value && !isPromptDismissed()) {
    style.value = event?.detail?.style || 'toast'
    show()
  }
}

onMounted(() => {
  window.addEventListener('ahoy:guest-needs-login', onContextualEvent)
})
onUnmounted(() => {
  window.removeEventListener('ahoy:guest-needs-login', onContextualEvent)
})
</script>

<style scoped>
/* Strategy 4: Toast notification (softer, less obtrusive than modal) */
.guest-save-toast {
  position: fixed;
  bottom: max(16px, calc(16px + env(safe-area-inset-bottom)));
  left: 16px;
  right: 16px;
  max-width: 480px;
  margin: 0 auto;
  z-index: 9999;
  background: rgba(20, 20, 28, 0.95);
  border: 1px solid rgba(109, 220, 255, 0.2);
  border-radius: 12px;
  padding: 12px 14px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.toast-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.toast-text {
  margin: 0;
  font-size: 13px;
  color: var(--text-primary, #fff);
  display: flex;
  align-items: center;
  gap: 8px;
}

.toast-text i {
  color: var(--accent-primary, #6ddcff);
  flex-shrink: 0;
}

.toast-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toast-btn {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 8px;
  font-size: 12px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  text-decoration: none;
  transition: all 0.2s ease;
}

.toast-btn.secondary {
  background: transparent;
  color: var(--text-secondary);
}

.toast-btn.secondary:hover {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.08);
}

.toast-btn.primary {
  background: var(--accent-primary, #6ddcff);
  color: #111;
}

.toast-btn.primary:hover {
  filter: brightness(1.15);
}

.toast-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  font-size: 14px;
  flex-shrink: 0;
  transition: color 0.2s ease;
}

.toast-close:hover {
  color: var(--text-primary);
}

/* Modal style (for critical saves) */
.guest-save-modal {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
  padding: 20px;
}

.modal-inner {
  background: rgba(20, 20, 28, 0.98);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 16px;
  padding: 24px;
  max-width: 360px;
  width: 100%;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
}

.modal-text {
  margin: 0 0 16px 0;
  font-size: 15px;
  color: var(--text-primary, #fff);
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-text i {
  color: var(--accent-primary, #6ddcff);
  font-size: 18px;
}

.modal-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 12px;
}

.modal-dismiss {
  flex: 1;
  padding: 10px 16px;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: var(--text-primary);
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.modal-dismiss:hover {
  background: rgba(255, 255, 255, 0.08);
  border-color: rgba(255, 255, 255, 0.24);
}

.modal-cta {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 10px 16px;
  background: var(--accent-primary, #6ddcff);
  color: #111;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: filter 0.2s ease;
}

.modal-cta:hover {
  filter: brightness(1.1);
}

.modal-checkbox {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-secondary);
  cursor: pointer;
  user-select: none;
}

.modal-checkbox input {
  cursor: pointer;
  accent-color: var(--accent-primary, #6ddcff);
}

.modal-checkbox:hover {
  color: var(--text-primary);
}

/* Animations */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: transform 0.25s ease, opacity 0.2s ease;
}

.slide-up-enter-from,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}

/* Responsive */
@media (max-width: 480px) {
  .guest-save-toast {
    bottom: max(12px, calc(12px + env(safe-area-inset-bottom)));
    left: 12px;
    right: 12px;
  }

  .toast-content {
    min-width: 0;
  }

  .toast-text {
    font-size: 12px;
  }

  .modal-inner {
    padding: 20px;
  }

  .modal-actions {
    flex-direction: column;
  }
}
</style>
