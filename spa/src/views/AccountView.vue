<template>
  <div class="account-page">
    <div v-if="auth.isLoggedIn.value" class="account-card">

      <!-- Profile Hero -->
      <div class="account-hero">
        <div class="account-hero-avatar-container">
          <div class="account-hero-avatar">
            <div class="account-hero-avatar-glow"></div>
            <img v-if="auth.user.value?.avatar_url" :src="auth.user.value.avatar_url" class="account-hero-avatar-img" alt="Profile" />
            <div v-else class="account-hero-initials">{{ userInitials }}</div>
            
            <!-- Upload trigger overlay -->
            <label class="account-avatar-upload-overlay" title="Upload new photo">
              <input type="file" accept="image/jpeg,image/png,image/webp" class="avatar-file-input" @change="onAvatarSelected" />
              <i class="fas fa-camera"></i>
            </label>
          </div>
          <div v-if="uploadingAvatar" class="avatar-upload-loading">
            <i class="fas fa-spinner fa-spin"></i> Uploading...
          </div>
        </div>
        <div class="account-hero-text">
          <div class="account-name-row">
            <template v-if="!editingName">
              <span class="account-name">{{ auth.user.value?.display_name || auth.user.value?.username || auth.user.value?.email }}</span>
              <button type="button" class="account-bio-edit-btn" aria-label="Edit name" @click="startEditName">
                <i class="fas fa-pen"></i>
              </button>
            </template>
            <template v-else>
              <input
                ref="nameInput"
                v-model="displayName"
                class="account-name-input"
                maxlength="60"
                placeholder="Your name"
                @keydown.enter.prevent="saveName"
                @keydown.escape="cancelEditName"
              />
              <div class="account-bio-actions">
                <button type="button" class="account-btn primary small" :disabled="nameSaving" @click="saveName">Save</button>
                <button type="button" class="account-btn secondary small" @click="cancelEditName">Cancel</button>
              </div>
            </template>
          </div>
          <div class="account-email">{{ auth.user.value?.email }}</div>
          <div v-if="memberSince" class="account-member-since">Member since {{ memberSince }}</div>
          <div class="account-bio-row">
            <template v-if="!editingBio">
              <span class="account-bio-text" :class="{ placeholder: !bio }" @click="startEditBio">
                {{ bio || 'Add a bio…' }}
              </span>
              <button type="button" class="account-bio-edit-btn" aria-label="Edit bio" @click="startEditBio">
                <i class="fas fa-pen"></i>
              </button>
            </template>
            <template v-else>
              <textarea
                ref="bioTextarea"
                v-model="bio"
                class="account-bio-input"
                maxlength="160"
                placeholder="e.g. Just here for the vibes…"
                rows="2"
                @keydown.enter.prevent="saveBio"
                @keydown.escape="cancelEditBio"
              ></textarea>
              <div class="account-bio-actions">
                <button type="button" class="account-btn primary small" :disabled="bioSaving" @click="saveBio">Save</button>
                <button type="button" class="account-btn secondary small" @click="cancelEditBio">Cancel</button>
              </div>
            </template>
          </div>
        </div>
      </div>

      <!-- Wallet Hero -->
      <section class="account-section wallet-hero-section">
        <div class="wallet-hero-card">
          <div class="wallet-hero-label">Your Balance</div>
          <div class="wallet-hero-amount">${{ (walletBalance ?? 0).toFixed(2) }}</div>
          <div class="wallet-hero-card-actions">
            <button type="button" class="wallet-hero-add-btn" @click="showFunding = !showFunding">
              <i class="fas fa-plus"></i> Add funds
            </button>
            <router-link to="/wallet" class="wallet-hero-history-btn">History</router-link>
          </div>
        </div>

        <div v-if="showFunding" class="wallet-funding">
          <p v-if="walletAmountError" class="wallet-error-note">{{ walletAmountError }}</p>
          <label class="wallet-funding-label" for="wallet-amount">Choose amount</label>
          <div class="wallet-amount-presets">
            <button
              v-for="preset in walletPresets"
              :key="preset"
              type="button"
              class="wallet-amount-chip"
              :class="{ active: walletAmount === preset }"
              @click="walletAmount = preset"
            >
              ${{ preset }}
            </button>
            <button
              v-if="lastWalletAmount"
              type="button"
              class="wallet-amount-chip last-used"
              :class="{ active: walletAmount === lastWalletAmount }"
              @click="walletAmount = lastWalletAmount"
            >
              Last used ${{ lastWalletAmount.toFixed(2) }}
            </button>
          </div>
          <div class="wallet-custom-amount">
            <span class="wallet-custom-prefix">$</span>
            <input
              id="wallet-amount"
              v-model.number="walletAmount"
              class="wallet-custom-input"
              type="number"
              min="1"
              max="1000"
              step="1"
              inputmode="decimal"
              aria-label="Wallet funding amount"
            />
          </div>
          <p class="wallet-hint">Starts at $1, up to $1,000 per checkout.</p>
          <button type="button" class="account-btn primary" style="margin-top:12px" :disabled="walletLoading" @click="addFunds">
            Add ${{ normalizedWalletAmount.toFixed(2) }}
          </button>
        </div>
      </section>

      <!-- Saved content widget -->
      <section class="account-section profile-widget-section">
        <div class="profile-widget-header">
          <h2 class="account-section-title">Saved</h2>
          <router-link to="/my-saves" class="profile-widget-see-all">See all</router-link>
        </div>
        <div v-if="savedItems.length" class="profile-strip">
          <router-link
            v-for="item in savedItems"
            :key="item.id || item.slug"
            :to="itemRoute(item)"
            class="profile-strip-tile"
          >
            <img :src="item.cover_art || item.thumbnail || item.artwork || '/static/img/default-cover.jpg'" :alt="item.title || item.name" loading="lazy" />
            <span class="profile-strip-label">{{ item.title || item.name }}</span>
          </router-link>
        </div>
        <p v-else class="profile-widget-empty">Nothing saved yet — bookmark tracks, shows, and artists to see them here.</p>
      </section>

      <!-- Recently played widget -->
      <section class="account-section profile-widget-section">
        <div class="profile-widget-header">
          <h2 class="account-section-title">Recently Played</h2>
          <router-link to="/recently-played" class="profile-widget-see-all">See all</router-link>
        </div>
        <div v-if="recentItems.length" class="profile-strip">
          <router-link
            v-for="item in recentItems"
            :key="item.key"
            :to="itemRoute(item)"
            class="profile-strip-tile"
          >
            <img :src="item.artwork || '/static/img/default-cover.jpg'" :alt="item.title" loading="lazy" />
            <span class="profile-strip-label">{{ item.title }}</span>
          </router-link>
        </div>
        <p v-else class="profile-widget-empty">Play anything to start building your history.</p>
      </section>

      <section class="account-section">
        <h2 class="account-section-title">Quick access</h2>
        <router-link to="/checkout?type=boost" class="account-link">
          <i class="fas fa-bolt account-link-icon"></i> Boost artists
        </router-link>
        <router-link to="/settings" class="account-link">
          <i class="fas fa-sliders-h account-link-icon"></i> Settings
        </router-link>
        <button type="button" class="account-link account-link-btn" @click="onLogout">
          <i class="fas fa-sign-out-alt account-link-icon"></i> Sign out
        </button>
      </section>

      <details class="account-section account-security-section">
        <summary class="account-security-summary">
          <div>
            <h2 class="account-section-title">Security</h2>
            <p class="account-security-summary-text">Using a temporary password? Change it here.</p>
          </div>
          <i class="fas fa-chevron-down account-security-chevron"></i>
        </summary>
        <div class="account-security-body">
          <p class="password-hint">Enter the password you were given, then choose a new one only you know.</p>
          <form class="password-form" @submit.prevent="changePassword">
            <label class="password-field">
              Current password
              <input
                v-model="passwordForm.current"
                type="password"
                autocomplete="current-password"
                minlength="8"
                required
              />
            </label>
            <label class="password-field">
              New password
              <input
                v-model="passwordForm.next"
                type="password"
                autocomplete="new-password"
                minlength="8"
                required
              />
            </label>
            <label class="password-field">
              Confirm new password
              <input
                v-model="passwordForm.confirm"
                type="password"
                autocomplete="new-password"
                minlength="8"
                required
              />
            </label>
            <p v-if="passwordMessage" class="password-message" :class="{ error: passwordError }">
              {{ passwordMessage }}
            </p>
            <button type="submit" class="account-btn secondary" :disabled="passwordSaving || !canChangePassword">
              <i v-if="passwordSaving" class="fas fa-spinner fa-spin"></i>
              <span v-else>Change password</span>
            </button>
          </form>

          <div class="account-danger-zone">
            <button v-if="!showDeleteConfirm" type="button" class="account-btn danger-link" @click="showDeleteConfirm = true">
              Delete account
            </button>
            <div v-else class="delete-confirm-box neu-card-inset">
              <p>Delete your account and all saved data? This cannot be undone.</p>
              <div class="delete-actions">
                <button class="account-btn danger" :disabled="deleteLoading" @click="onDeleteAccount">
                  Yes, delete everything
                </button>
                <button class="account-btn secondary" :disabled="deleteLoading" @click="showDeleteConfirm = false">
                  Cancel
                </button>
              </div>
            </div>
          </div>
        </div>
      </details>
    </div>

    <div v-else class="account-guest neon-profile">
      <!-- Hero Header -->
      <section class="neon-hero">
        <div class="neon-hero-left">
          <div class="neon-avatar-wrap">
            <div class="neon-avatar-glow"></div>
            <div class="neon-avatar">
              <i class="fas fa-user"></i>
              <div class="guest-avatar-camera-hint"><i class="fas fa-camera"></i></div>
            </div>
          </div>
          <div class="neon-hero-text">
            <h1 class="neon-title">Profile</h1>
            <div class="guest-ghost-name-bar shimmer"></div>
            <div class="guest-ghost-member-bar shimmer-text"></div>
            <div class="guest-ghost-bio-bar shimmer-text"></div>
          </div>
        </div>
        <router-link to="/login" class="neon-cta-btn">Log In / Sign Up</router-link>
      </section>

      <!-- Saved — real local bookmarks if present, shimmer if not -->
      <section class="account-section profile-widget-section">
        <div class="profile-widget-header">
          <h2 class="account-section-title">Saved</h2>
          <router-link to="/login" class="profile-widget-see-all">See all</router-link>
        </div>
        <router-link to="/login" class="profile-strip guest-strip">
          <template v-if="savedItems.length">
            <div v-for="item in savedItems.slice(0, 7)" :key="item.id || item.slug" class="profile-strip-tile">
              <img :src="item.cover_art || item.thumbnail || item.artwork || '/static/img/default-cover.jpg'" :alt="item.title || item.name" loading="lazy" class="guest-real-img" />
              <span class="profile-strip-label guest-real-label">{{ item.title || item.name }}</span>
            </div>
          </template>
          <template v-else>
            <div v-for="n in 7" :key="n" class="profile-strip-tile" :style="`--i:${n}`">
              <div class="guest-tile-img shimmer"></div>
              <div class="guest-tile-label shimmer-text"></div>
            </div>
          </template>
        </router-link>
      </section>

      <!-- Recently Played — real history if present, shimmer if not -->
      <section class="account-section profile-widget-section">
        <div class="profile-widget-header">
          <h2 class="account-section-title">Recently Played</h2>
          <router-link to="/login" class="profile-widget-see-all">See all</router-link>
        </div>
        <router-link to="/login" class="profile-strip guest-strip">
          <template v-if="recentItems.length">
            <div v-for="item in recentItems.slice(0, 7)" :key="item.key" class="profile-strip-tile">
              <img :src="item.artwork || '/static/img/default-cover.jpg'" :alt="item.title" loading="lazy" class="guest-real-img" />
              <span class="profile-strip-label guest-real-label">{{ item.title }}</span>
            </div>
          </template>
          <template v-else>
            <div v-for="n in 7" :key="n" class="profile-strip-tile" :style="`--i:${n}`">
              <div class="guest-tile-img shimmer"></div>
              <div class="guest-tile-label shimmer-text"></div>
            </div>
          </template>
        </router-link>
      </section>

      <!-- Ghost Wallet -->
      <section class="account-section wallet-hero-section">
        <router-link to="/login" class="wallet-hero-card guest-ghost-card">
          <div class="wallet-hero-label">Your Balance</div>
          <div class="wallet-hero-amount guest-ghost-amount">$—</div>
          <div class="wallet-hero-card-actions">
            <span class="wallet-hero-add-btn ghost-btn"><i class="fas fa-plus"></i> Add funds</span>
            <span class="wallet-hero-history-btn">History</span>
          </div>
        </router-link>
      </section>

      <!-- Quick access -->
      <section class="account-section">
        <h2 class="account-section-title">Quick access</h2>
        <router-link to="/login" class="account-link">
          <i class="fas fa-bolt account-link-icon"></i> Boost artists
        </router-link>
        <router-link to="/settings" class="account-link">
          <i class="fas fa-sliders-h account-link-icon"></i> Settings
        </router-link>
      </section>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { apiFetch } from '../composables/useApi'
import { useBookmarks } from '../composables/useBookmarks'

const router = useRouter()
const route = useRoute()
const auth = useAuth()

const user = ref(null)
const loading = ref(true)
const walletBalance = ref(null)
const walletLoading = ref(false)
const walletAmount = ref(10)
// Bookmarks
const { bookmarks } = useBookmarks()
const savedItems = computed(() => Object.values(bookmarks.value || {}).reverse().slice(0, 8))

// Recently played
const RECENT_KEY = 'ahoy.recentlyPlayed.v1'
const recentItems = ref([])
function loadRecent() {
  try {
    const raw = localStorage.getItem(RECENT_KEY)
    recentItems.value = raw ? JSON.parse(raw).slice(0, 8) : []
  } catch { recentItems.value = [] }
}

function itemRoute(item) {
  const t = item.type || 'track'
  if (t === 'artist') return `/artists/${item.slug}`
  if (t === 'show' || t === 'video') return `/shows/${item.id || item.slug}`
  if (t === 'podcast' || t === 'episode') return `/podcasts/${item.id || item.slug}`
  return `/music/${item.id || item.slug}`
}

const uploadingAvatar = ref(false)

// Display name editing
const editingName = ref(false)
const displayName = ref('')
const displayNameOriginal = ref('')
const nameSaving = ref(false)
const nameInput = ref(null)

const memberSince = computed(() => {
  const raw = auth.user.value?.created_at
  if (!raw) return null
  const d = new Date(raw)
  return d.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
})

const bio = ref('')
const bioOriginal = ref('')
const editingBio = ref(false)
const bioSaving = ref(false)
const bioTextarea = ref(null)
const showFunding = ref(false)
const showDeleteConfirm = ref(false)
const deleteLoading = ref(false)
const walletPresets = [5, 10, 25, 50]
const walletAmountError = ref('')
const walletAmountStorageKey = 'ahoy:lastWalletFundAmount'
const lastWalletAmount = ref(null)
const passwordSaving = ref(false)
const passwordMessage = ref('')
const passwordError = ref(false)
const passwordForm = ref({
  current: '',
  next: '',
  confirm: '',
})

const userInitials = computed(() => {
  const u = auth.user.value
  const name = u?.display_name || u?.username || u?.email || ''
  const parts = name.trim().split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return name.slice(0, 2).toUpperCase()
})

const normalizedWalletAmount = computed(() => {
  const amount = Number(walletAmount.value)
  if (!Number.isFinite(amount)) return 1
  return Math.round(Math.min(1000, Math.max(1, amount)) * 100) / 100
})

const isWalletAmountValid = computed(() => {
  const amount = Number(walletAmount.value)
  return Number.isFinite(amount) && amount >= 1 && amount <= 1000
})

const canChangePassword = computed(() => {
  const form = passwordForm.value
  return form.current.length >= 8 && form.next.length >= 8 && form.next === form.confirm && form.current !== form.next
})

const greetingWords = [
  'champ', 'legend', 'pal', 'buckaroo', 'amigo', 'boss',
  'chief', 'stranger', 'friend', 'kiddo', 'hotshot', 'ace',
  'sport', 'comrade', 'captain', 'sunshine', 'trooper', 'chum',
  'homeslice', 'rockstar', 'goofball', 'rascal', 'nerd',
  'pilgrim', 'señor', 'dude', 'cowboy', 'sparky', 'slick',
  'wizard', 'skipper', 'cupcake', 'muffin', 'potato',
  'biscuit', 'turnip', 'nugget', 'pickle', 'waffle',
]
const randomGreeting = ref(greetingWords[Math.floor(Math.random() * greetingWords.length)])

onMounted(async () => {
  loadRecent()
  window.addEventListener('recentlyPlayed:updated', loadRecent)

  if (route.query.wallet_funded === 'true') {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Wallet funded successfully', type: 'success' } }))
  }
  const savedAmount = Number(window.localStorage.getItem(walletAmountStorageKey))
  if (Number.isFinite(savedAmount) && savedAmount >= 1 && savedAmount <= 1000) {
    const normalized = Math.round(savedAmount * 100) / 100
    walletAmount.value = normalized
    lastWalletAmount.value = normalized
  }

  if (!auth.isLoggedIn.value) {
    loading.value = false
    return
  }
  try {
    const userData = await apiFetch('/api/me')
    user.value = userData
    // Merge created_at into auth.user so memberSince computed can read it
    if (userData?.user?.created_at && auth.user.value) {
      auth.user.value = { ...auth.user.value, created_at: userData.user.created_at }
    }
  } catch (e) {
    console.error('Failed to load account data', e)
  } finally {
    loading.value = false
  }

  try {
    const profileData = await apiFetch('/api/user/profile')
    bio.value = profileData?.preferences?.bio || ''
    bioOriginal.value = bio.value
  } catch { /* ignore */ }

  try {
    const data = await apiFetch('/payments/wallet')
    walletBalance.value = data.balance ?? 0
  } catch {
    walletBalance.value = 0
  }
})

onUnmounted(() => {
  window.removeEventListener('recentlyPlayed:updated', loadRecent)
})

async function startEditName() {
  displayName.value = auth.user.value?.display_name || auth.user.value?.username || ''
  displayNameOriginal.value = displayName.value
  editingName.value = true
  await nextTick()
  nameInput.value?.focus()
}
function cancelEditName() {
  displayName.value = displayNameOriginal.value
  editingName.value = false
}
async function saveName() {
  const val = displayName.value.trim()
  if (!val) return
  nameSaving.value = true
  try {
    await auth.updateProfile({ display_name: val })
    auth.user.value = { ...auth.user.value, display_name: val }
    try { localStorage.setItem('ahoy.auth.user', JSON.stringify(auth.user.value)) } catch { /* ignore */ }
    displayNameOriginal.value = val
    editingName.value = false
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Name updated', type: 'success' } }))
  } catch {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Could not update name', type: 'error' } }))
  } finally {
    nameSaving.value = false
  }
}

async function startEditBio() {
  editingBio.value = true
  await nextTick()
  bioTextarea.value?.focus()
}
function cancelEditBio() {
  bio.value = bioOriginal.value
  editingBio.value = false
}
async function saveBio() {
  bioSaving.value = true
  try {
    await auth.updateProfile({ bio: bio.value })
    bioOriginal.value = bio.value
    editingBio.value = false
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Bio saved', type: 'success' } }))
  } catch {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Could not save bio', type: 'error' } }))
  } finally {
    bioSaving.value = false
  }
}

async function addFunds() {
  if (!auth.isLoggedIn.value) {
    router.push('/login')
    return
  }
  if (!isWalletAmountValid.value) {
    walletAmountError.value = 'Choose an amount between $1 and $1,000.'
    return
  }
  walletAmountError.value = ''
  const amount = normalizedWalletAmount.value
  window.localStorage.setItem(walletAmountStorageKey, String(amount))
  lastWalletAmount.value = amount
  walletLoading.value = true
  try {
    const data = await apiFetch('/payments/wallet/fund', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount }),
    })
    if (data.checkout_url) {
      window.location.href = data.checkout_url
      return
    }
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: data.error || 'Could not start checkout', type: 'error' } }))
  } catch (e) {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: e.message || 'Failed to add funds', type: 'error' } }))
  } finally {
    walletLoading.value = false
  }
}

async function changePassword() {
  passwordMessage.value = ''
  passwordError.value = false
  const form = passwordForm.value
  if (form.next !== form.confirm) {
    passwordMessage.value = 'New passwords do not match.'
    passwordError.value = true
    return
  }
  if (form.next.length < 8) {
    passwordMessage.value = 'Use at least 8 characters.'
    passwordError.value = true
    return
  }
  if (form.current === form.next) {
    passwordMessage.value = 'Choose a new password that is different from the temporary one.'
    passwordError.value = true
    return
  }

  passwordSaving.value = true
  try {
    await apiFetch('/api/auth/change-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        current_password: form.current,
        new_password: form.next,
      }),
    })
    passwordForm.value = { current: '', next: '', confirm: '' }
    passwordMessage.value = 'Password changed.'
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Password changed', type: 'success' } }))
  } catch (err) {
    const message = err?.message || ''
    if (message.includes('invalid_current_password')) {
      passwordMessage.value = 'Current password is not correct.'
    } else if (message.includes('password_login_not_enabled')) {
      passwordMessage.value = 'This account signs in with Google. Use Google to manage your password.'
    } else {
      passwordMessage.value = 'Could not change password.'
    }
    passwordError.value = true
  } finally {
    passwordSaving.value = false
  }
}

async function onLogout() {
  await auth.logout()
  window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Signed out', type: 'success' } }))
  router.push('/')
}

async function onDeleteAccount() {
  deleteLoading.value = true
  try {
    const data = await apiFetch('/api/auth/delete-account', {
      method: 'POST'
    })
    if (data.success) {
      window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Account deleted', type: 'success' } }))
      router.push('/')
      await auth.logout()
    } else {
      window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: data.error || 'Deletion failed', type: 'error' } }))
    }
  } catch (err) {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Failed to delete account', type: 'error' } }))
  } finally {
    deleteLoading.value = false
  }
}

async function onAvatarSelected(event) {
  const file = event.target.files?.[0]
  if (!file) return

  const allowedTypes = ['image/jpeg', 'image/png', 'image/webp']
  if (!allowedTypes.includes(file.type)) {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Only JPEG, PNG, or WebP images are allowed', type: 'error' } }))
    return
  }

  uploadingAvatar.value = true
  const formData = new FormData()
  formData.append('file', file)

  try {
    const data = await apiFetch('/api/user/avatar', {
      method: 'POST',
      body: formData,
    })

    if (data.success && data.avatar_url) {
      // Update user in local ref / session cache
      auth.user.value = {
        ...auth.user.value,
        avatar_url: data.avatar_url
      }
      try {
        localStorage.setItem('ahoy.auth.user', JSON.stringify(auth.user.value))
      } catch (err) { /* ignore */ }
      
      window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Profile photo updated successfully', type: 'success' } }))
    } else {
      window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: data.error || 'Failed to upload photo', type: 'error' } }))
    }
  } catch (err) {
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: err?.message || 'Failed to upload photo', type: 'error' } }))
  } finally {
    uploadingAvatar.value = false
  }
}
</script>

<style scoped>
.account-page {
  padding: 0 0 100px 0;
  width: 100%;
}
.account-card {
  width: 100%;
  margin: 0;
  background:
    radial-gradient(ellipse at 5% 0%, rgba(89, 26, 220, 0.1) 0%, transparent 45%),
    radial-gradient(ellipse at 95% 5%, rgba(0, 212, 255, 0.07) 0%, transparent 40%),
    rgba(14, 14, 20, 0.7);
  border: none;
  border-radius: 0;
  padding: 3rem 3rem;
  min-height: calc(100vh - 150px);
}
@media (max-width: 768px) {
  .account-card { padding: 1.75rem 1.25rem; }
  .account-security-summary,
  .account-security-body {
    padding-left: 16px;
    padding-right: 16px;
  }
}
/* ── Profile Hero ── */
.account-hero {
  display: flex;
  align-items: center;
  gap: 1.25rem;
  margin-bottom: 2.5rem;
  max-width: 800px;
}
.account-hero-avatar {
  position: relative;
  flex-shrink: 0;
}
.account-hero-avatar-glow {
  position: absolute;
  inset: -6px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 212, 255, 0.35), rgba(130, 100, 255, 0.25));
  filter: blur(14px);
}
.account-hero-initials {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.18), rgba(130, 100, 255, 0.18));
  border: 1.5px solid rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -1px;
}
.account-hero-text { display: flex; flex-direction: column; gap: 4px; min-width: 0; }
.account-name-row {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}
.account-name-input {
  font-size: 20px;
  font-weight: 700;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(0, 212, 255, 0.4);
  border-radius: 8px;
  color: var(--text-primary, #fff);
  padding: 4px 10px;
  outline: none;
  max-width: 260px;
}
.account-member-since {
  font-size: 11px;
  color: rgba(255,255,255,0.3);
  margin-top: 2px;
}
.account-link-btn {
  background: none;
  border: none;
  width: 100%;
  text-align: left;
  cursor: pointer;
  font-size: 15px;
}
.account-bio-row {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  margin-top: 6px;
  flex-wrap: wrap;
}
.account-bio-text {
  font-size: 13px;
  color: rgba(255,255,255,0.6);
  line-height: 1.5;
  cursor: pointer;
  border-bottom: 1px dashed rgba(255,255,255,0.15);
}
.account-bio-text.placeholder {
  color: rgba(255,255,255,0.25);
  font-style: italic;
}
.account-bio-text:hover { color: rgba(255,255,255,0.8); border-color: rgba(255,255,255,0.3); }
.account-bio-edit-btn {
  background: none;
  border: none;
  color: rgba(255,255,255,0.25);
  cursor: pointer;
  font-size: 10px;
  padding: 2px 4px;
  line-height: 1;
  margin-top: 2px;
}
.account-bio-edit-btn:hover { color: rgba(255,255,255,0.6); }
.account-bio-input {
  width: 100%;
  max-width: 360px;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.12);
  border-radius: 8px;
  color: var(--text-primary);
  font-size: 13px;
  padding: 8px 10px;
  resize: none;
  line-height: 1.5;
  outline: none;
}
.account-bio-input:focus { border-color: rgba(0, 212, 255, 0.4); }
.account-bio-actions { display: flex; gap: 8px; margin-top: 6px; width: 100%; }
.account-btn.small { padding: 6px 12px; font-size: 12px; }
.account-name {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary, #fff);
}
.account-email {
  font-size: 13px;
  color: var(--text-secondary, rgba(255,255,255,0.55));
}

/* ── Wallet Hero ── */
.wallet-hero-section { max-width: 800px; }
.wallet-hero-card {
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.15) 0%, rgba(130, 100, 255, 0.12) 60%, rgba(107, 253, 224, 0.08) 100%);
  border: 1px solid rgba(0, 212, 255, 0.2);
  border-radius: 20px;
  padding: 2rem 1.75rem;
  margin-bottom: 1.25rem;
  text-align: center;
  position: relative;
  overflow: hidden;
  box-shadow: 0 0 40px rgba(0, 212, 255, 0.08), inset 0 1px 0 rgba(255,255,255,0.06);
}
.wallet-hero-card::before {
  content: '';
  position: absolute;
  top: -40%;
  left: 50%;
  transform: translateX(-50%);
  width: 200%;
  height: 200%;
  background: radial-gradient(ellipse, rgba(0, 212, 255, 0.06) 0%, transparent 60%);
  pointer-events: none;
}
.wallet-hero-label {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 3px;
  color: rgba(255,255,255,0.45);
  margin-bottom: 0.5rem;
}
.wallet-hero-amount {
  font-size: 52px;
  font-weight: 800;
  color: #fff;
  letter-spacing: -2px;
  line-height: 1;
  margin-bottom: 0.5rem;
  text-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
}
.wallet-hero-card-actions {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-top: 1.25rem;
}
.wallet-hero-add-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  border-radius: 999px;
  background: rgba(255,255,255,0.12);
  border: 1px solid rgba(255,255,255,0.15);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: background 0.2s;
}
.wallet-hero-add-btn:hover { background: rgba(255,255,255,0.2); }
.wallet-hero-history-btn {
  font-size: 13px;
  color: rgba(255,255,255,0.45);
  text-decoration: none;
  padding: 9px 4px;
}
.wallet-hero-history-btn:hover { color: rgba(255,255,255,0.75); }
.account-section {
  margin-bottom: 3rem;
  max-width: 800px;
}
.account-section-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 2.5px;
  color: rgba(255,255,255,0.4);
  margin: 0 0 12px;
}
.wallet-funding {
  padding: 14px 16px;
  border-radius: 12px;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.06);
  margin-bottom: 12px;
}
.wallet-funding-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
}
.wallet-amount-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}
.wallet-amount-chip {
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.05);
  color: var(--text-primary);
  border-radius: 999px;
  padding: 8px 12px;
  font-weight: 600;
  cursor: pointer;
}
.wallet-amount-chip.active {
  background: var(--accent-primary, #6ddcff);
  color: #111;
  border-color: transparent;
}
.wallet-custom-amount {
  display: flex;
  align-items: center;
  max-width: 150px;
  border-radius: 12px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(0,0,0,0.18);
  overflow: hidden;
}
.wallet-custom-prefix {
  padding: 0 10px;
  color: var(--text-secondary);
}
.wallet-custom-input {
  width: 100%;
  border: 0;
  outline: none;
  background: transparent;
  color: var(--text-primary);
  padding: 10px 12px 10px 0;
  font-size: 14px;
}
.wallet-hint {
  margin: 10px 0 0;
  font-size: 12px;
  color: var(--text-secondary);
}
.wallet-error-note {
  margin: 0 0 10px;
  font-size: 12px;
  color: #fca5a5;
}
.account-btn.secondary {
  background: rgba(255,255,255,0.08);
  color: var(--text-primary);
  text-decoration: none;
}
.account-btn.secondary:hover {
  background: rgba(255,255,255,0.12);
}
.account-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}
.account-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  border-radius: 12px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  border: none;
  transition: background 0.2s;
}
.account-btn.primary {
  background: var(--accent-primary, #6ddcff);
  color: #111;
}
.account-btn.primary:hover:not(:disabled) {
  filter: brightness(1.1);
}
.account-btn.logout {
  background: rgba(255,255,255,0.08);
  color: var(--text-secondary);
  width: 100%;
  justify-content: center;
}
.account-btn.logout:hover {
  background: rgba(255,255,255,0.12);
}
.account-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 0;
  color: var(--text-primary);
  text-decoration: none;
  font-size: 15px;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.account-link:last-of-type { border-bottom: none; }
.account-link:hover { color: var(--accent-primary, #6ddcff); }
.account-link-icon {
  width: 18px;
  text-align: center;
  color: rgba(255,255,255,0.35);
  font-size: 13px;
}
/* ── Neon Profile (guest view) ── */
.neon-profile {
  width: 100%;
  margin: 0;
  padding: 2rem 2rem 6rem;
  min-height: calc(100vh - 150px);
  background:
    radial-gradient(ellipse at 0% 0%, rgba(89, 26, 220, 0.12) 0%, transparent 50%),
    radial-gradient(ellipse at 100% 0%, rgba(0, 227, 253, 0.08) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 100%, rgba(107, 253, 224, 0.04) 0%, transparent 50%);
}
@media (min-width: 769px) {
  .neon-profile { padding: 3rem 3rem 6rem; }
}

/* Hero */
.neon-hero {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-bottom: 3rem;
}
@media (min-width: 769px) {
  .neon-hero {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}
.neon-hero-left {
  display: flex;
  align-items: center;
  gap: 1.5rem;
}
.neon-avatar-wrap {
  position: relative;
  flex-shrink: 0;
}
.neon-avatar-glow {
  position: absolute;
  inset: -4px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(0, 212, 255, 0.4), rgba(130, 100, 255, 0.3));
  filter: blur(12px);
  opacity: 0.5;
}
.neon-avatar {
  position: relative;
  width: 100px;
  height: 100px;
  border-radius: 50%;
  background: rgba(30, 31, 38, 0.9);
  border: 2px solid rgba(255, 255, 255, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40px;
  color: rgba(255, 255, 255, 0.5);
}
@media (min-width: 769px) {
  .neon-avatar { width: 130px; height: 130px; font-size: 50px; }
}
.neon-title {
  font-size: 36px;
  font-weight: 800;
  color: #fff;
  margin: 0;
  letter-spacing: -1px;
}
@media (min-width: 769px) {
  .neon-title { font-size: 56px; letter-spacing: -2px; }
}
.neon-subtitle {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.55);
  margin: 4px 0 0;
}
.neon-cta-btn {
  display: inline-flex;
  align-items: center;
  padding: 12px 28px;
  background: linear-gradient(135deg, #00d4ec, #00e3fd);
  color: #003840;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  border-radius: 14px;
  text-decoration: none;
  box-shadow: 0 0 20px rgba(0, 227, 253, 0.25);
  transition: transform 0.2s, box-shadow 0.2s;
  white-space: nowrap;
}
.neon-cta-btn:hover {
  transform: scale(1.05);
  box-shadow: 0 0 30px rgba(0, 227, 253, 0.4);
}

/* Ghost hero skeleton fields */
.guest-ghost-name-bar {
  height: 16px;
  width: 130px;
  border-radius: 8px;
  margin-top: 10px;
}
.guest-ghost-member-bar {
  height: 10px;
  width: 90px;
  border-radius: 5px;
  margin-top: 6px;
}
.guest-ghost-bio-bar {
  height: 11px;
  width: 190px;
  border-radius: 6px;
  margin-top: 8px;
}

/* Camera hint badge on guest avatar */
.neon-avatar {
  position: relative;
}
.guest-avatar-camera-hint {
  position: absolute;
  bottom: 2px;
  right: 2px;
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: rgba(255,255,255,0.07);
  border: 1.5px solid rgba(255,255,255,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
  color: rgba(255,255,255,0.2);
}

/* Ghost wallet card */
.guest-ghost-card {
  display: block;
  text-decoration: none;
  cursor: pointer;
  opacity: 0.55;
  transition: opacity 0.2s;
}
.guest-ghost-card:hover { opacity: 0.75; }
.guest-ghost-amount {
  color: rgba(255,255,255,0.3);
  text-shadow: none;
  letter-spacing: 2px;
}
.ghost-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 20px;
  border-radius: 999px;
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.3);
  font-size: 13px;
  font-weight: 600;
  pointer-events: none;
}

/* Ghost strips */
.guest-strip {
  display: flex;
  gap: 10px;
  overflow: hidden;
  text-decoration: none;
  cursor: pointer;
  padding-bottom: 4px;
}
.guest-tile-img {
  width: 76px;
  height: 76px;
  border-radius: 10px;
  background: rgba(255,255,255,0.06);
  flex-shrink: 0;
}
.guest-tile-label {
  height: 10px;
  border-radius: 5px;
  background: rgba(255,255,255,0.05);
  margin-top: 7px;
  width: 60%;
  margin-left: auto;
  margin-right: auto;
}

/* Shimmer animation */
@keyframes shimmer {
  0% { background-position: -200% 0; }
  100% { background-position: 200% 0; }
}
.shimmer {
  background: linear-gradient(
    90deg,
    rgba(255,255,255,0.05) 25%,
    rgba(255,255,255,0.1) 50%,
    rgba(255,255,255,0.05) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 2s infinite linear;
}
.shimmer-text {
  background: linear-gradient(
    90deg,
    rgba(255,255,255,0.03) 25%,
    rgba(255,255,255,0.07) 50%,
    rgba(255,255,255,0.03) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 2s infinite linear;
}
/* Stagger each tile's shimmer so it waves left-to-right */
.profile-strip-tile .shimmer,
.profile-strip-tile .shimmer-text {
  animation-delay: calc(var(--i, 0) * 0.12s);
}

/* Real history tiles (guest has played content) */
.guest-real-img {
  width: 76px;
  height: 76px;
  border-radius: 10px;
  object-fit: cover;
  display: block;
  filter: saturate(0.25) brightness(0.65);
  transition: filter 0.25s;
}
.guest-strip:hover .guest-real-img {
  filter: saturate(0.4) brightness(0.75);
}
.guest-real-label {
  opacity: 0.35;
}

/* ── Profile Content Widgets ── */
.profile-widget-section { max-width: 800px; }
.profile-widget-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}
.profile-widget-see-all {
  font-size: 12px;
  font-weight: 600;
  color: var(--accent-primary, #6ddcff);
  text-decoration: none;
  opacity: 0.8;
}
.profile-widget-see-all:hover { opacity: 1; }
.profile-widget-empty {
  font-size: 13px;
  color: rgba(255,255,255,0.3);
  font-style: italic;
  margin: 0;
  padding: 16px 0;
}
.profile-strip {
  display: flex;
  gap: 10px;
  overflow-x: auto;
  padding-bottom: 4px;
  scrollbar-width: none;
}
.profile-strip::-webkit-scrollbar { display: none; }
.profile-strip-tile {
  flex-shrink: 0;
  width: 76px;
  text-decoration: none;
  color: inherit;
}
.profile-strip-tile img {
  width: 76px;
  height: 76px;
  border-radius: 10px;
  object-fit: cover;
  display: block;
  background: rgba(255,255,255,0.06);
  transition: transform 0.2s, opacity 0.2s;
}
.profile-strip-tile:hover img { transform: scale(1.05); opacity: 0.9; }
.profile-strip-label {
  display: block;
  font-size: 11px;
  color: rgba(255,255,255,0.55);
  margin-top: 5px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  text-align: center;
}

.account-security-section {
  max-width: 520px;
  padding: 0;
  overflow: hidden;
}
.account-security-section[open] .account-security-chevron {
  transform: rotate(180deg);
}
.account-security-summary {
  list-style: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 20px 18px;
  cursor: pointer;
  user-select: none;
}
.account-security-summary::-webkit-details-marker {
  display: none;
}
.account-security-summary h2 {
  margin: 0;
}
.account-security-summary-text {
  margin: 4px 0 0;
  color: rgba(255,255,255,0.55);
  font-size: 13px;
  line-height: 1.4;
}
.account-security-chevron {
  color: rgba(255,255,255,0.45);
  transition: transform 0.2s ease;
  flex-shrink: 0;
}
.account-security-body {
  padding: 0 20px 20px;
  display: grid;
  gap: 18px;
}
.password-hint {
  margin: 0;
  color: rgba(255,255,255,0.55);
  font-size: 13px;
  line-height: 1.45;
}
.password-form {
  display: grid;
  gap: 12px;
}
.password-field {
  display: grid;
  gap: 6px;
  color: rgba(255,255,255,0.58);
  font-size: 12px;
  font-weight: 600;
}
.password-field input {
  width: 100%;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  background: rgba(0,0,0,0.18);
  color: var(--text-primary);
  font-size: 14px;
  padding: 12px 14px;
  outline: none;
}
.password-field input:focus {
  border-color: rgba(109, 220, 255, 0.5);
}
.password-message {
  margin: 0;
  color: rgba(134, 239, 172, 0.9);
  font-size: 13px;
}
.password-message.error {
  color: #fca5a5;
}

/* Danger Zone */
.account-danger-zone {
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  text-align: center;
}
.account-btn.danger-link {
  background: transparent;
  color: rgba(255, 82, 82, 0.7);
  font-size: 13px;
  font-weight: 500;
  text-decoration: underline;
  padding: 4px 8px;
}
.account-btn.danger-link:hover {
  color: #ff5252;
}
.delete-confirm-box {
  padding: 16px;
  background: rgba(255, 82, 82, 0.05);
  border: 1px solid rgba(255, 82, 82, 0.2);
  border-radius: 12px;
}
.delete-confirm-box p {
  color: #ff8a80;
  font-size: 14px;
  margin: 0 0 16px;
  line-height: 1.4;
}
.delete-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.account-btn.danger {
  background: #ff5252;
  color: white;
  justify-content: center;
}
.account-btn.danger:hover {
  background: #ff1744;
}

/* Avatar Upload styling */
.account-hero-avatar-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}
.account-avatar-upload-overlay {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 18px;
  opacity: 0;
  cursor: pointer;
  transition: opacity 0.2s ease;
  z-index: 5;
}
.account-hero-avatar:hover .account-avatar-upload-overlay {
  opacity: 1;
}
.avatar-file-input {
  display: none;
}
.avatar-upload-loading {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.6);
  display: flex;
  align-items: center;
  gap: 4px;
}
.account-hero-avatar-img {
  position: relative;
  width: 72px;
  height: 72px;
  border-radius: 50%;
  border: 1.5px solid rgba(255, 255, 255, 0.12);
  object-fit: cover;
}
</style>
