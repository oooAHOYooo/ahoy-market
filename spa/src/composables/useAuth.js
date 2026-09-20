/**
 * Auth composable — session-based auth with Flask /api/auth/*.
 *
 * Uses cookies (credentials: 'include' in useApi). No token storage.
 * Restores session on load via GET /api/auth/me.
 */
import { ref, computed } from 'vue'
import { apiFetch } from './useApi'
import { trackEvent, resetIdentity } from './useAnalytics'
import { Preferences } from '@capacitor/preferences'

const USER_KEY = 'ahoy.auth.user'

async function saveUserPref(userData) {
  try { localStorage.setItem(USER_KEY, JSON.stringify(userData)) } catch { /* ignore */ }
  try { await Preferences.set({ key: USER_KEY, value: JSON.stringify(userData) }) } catch { /* ignore */ }
}

async function removeUserPref() {
  try { localStorage.removeItem(USER_KEY) } catch { /* ignore */ }
  try { await Preferences.remove({ key: USER_KEY }) } catch { /* ignore */ }
}

// Shared state (singleton)
const user = ref(null)
const loading = ref(false)
const error = ref(null)
let mePromise = null

function _pickUserFields(u) {
  const { id, username, email, display_name, avatar_url } = u || {}
  return { id, username, email, display_name, avatar_url }
}

// Hydrate from localStorage immediately for synchronous startup,
// then follow up with async capacitor preferences for native mobile resilience.
try {
  const _saved = localStorage.getItem(USER_KEY)
  if (_saved) user.value = JSON.parse(_saved)
  Preferences.get({ key: USER_KEY }).then(({ value }) => {
    if (value && !user.value) user.value = JSON.parse(value)
  }).catch(() => {})
} catch { /* ignore */ }

async function fetchMe() {
  if (mePromise) return mePromise
  mePromise = apiFetch('/api/auth/me').then((data) => {
    if (data?.user) {
      user.value = data.user
      saveUserPref(_pickUserFields(data.user))
    } else {
      user.value = null
    }
    return data
  }).catch(() => {
    user.value = null
    removeUserPref()
    return null
  }).finally(() => { mePromise = null })
  return mePromise
}

// Run once on first composable use (e.g. when app mounts) to validate with server
function restoreSession() {
  fetchMe()
}

export function useAuth() {
  const isLoggedIn = computed(() => !!user.value)
  const username = computed(() => user.value?.username || user.value?.email || '')

  async function login(email, password) {
    loading.value = true
    error.value = null
    try {
      const data = await apiFetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ identifier: email, password }),
      })
      if (data.success && data.user) {
        user.value = data.user
        saveUserPref(_pickUserFields(data.user))
        trackEvent('auth_login', { method: 'password' })
        return { success: true }
      }
      return { success: false, error: data.error || 'Login failed' }
    } catch (e) {
      const data = e.data || {}
      const msg = data.error === 'invalid_credentials' ? 'Invalid email or password.' : (e.message || data.error || 'Login failed')
      error.value = msg
      return { success: false, error: msg }
    } finally {
      loading.value = false
    }
  }

  async function signup(email, password, username, phoneNumber) {
    loading.value = true
    error.value = null
    try {
      const data = await apiFetch('/api/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, username: username || undefined, phone_number: phoneNumber || undefined }),
      })
      if (data.success && data.user) {
        user.value = data.user
        saveUserPref(_pickUserFields(data.user))
        trackEvent('auth_signup', { method: 'password' })
        return { success: true }
      }
      return { success: false, error: data.error || 'Signup failed' }
    } catch (e) {
      const data = e.data || {}
      const msg = data.error === 'invalid_username' && data.suggestions?.length
        ? `Username invalid. Try: ${data.suggestions.slice(0, 2).join(', ')}`
        : (data.error === 'account_already_exists' ? 'An account with this email already exists.' : (e.message || data.error || 'Signup failed'))
      error.value = msg
      return { success: false, error: msg }
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    loading.value = true
    error.value = null
    try {
      await apiFetch('/api/auth/logout', { method: 'POST' })
    } catch { /* ignore */ }
    trackEvent('auth_logout')
    resetIdentity()
    user.value = null
    removeUserPref()
    loading.value = false
  }

  async function updateProfile(data) {
    loading.value = true
    error.value = null
    try {
      const resp = await apiFetch('/api/auth/update', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      })
      if (resp.success && resp.user) {
        user.value = resp.user
        saveUserPref(_pickUserFields(resp.user))
        return { success: true }
      }
      error.value = resp.message || resp.error || 'Update failed'
      return { success: false, error: error.value }
    } catch (e) {
      error.value = e.message || 'Network error'
      return { success: false, error: error.value }
    } finally {
      loading.value = false
    }
  }

  // For callers that expect auth headers (e.g. future API that uses Bearer). Session uses cookies.
  function authHeaders() {
    return {}
  }

  return {
    user,
    loading,
    error,
    isLoggedIn,
    username,
    login,
    signup,
    logout,
    updateProfile,
    authHeaders,
    restoreSession,
  }
}

// Call once on app load (e.g. from App.vue onMounted) to restore session from cookie
// fetchMe is exported so views that need auth can await session validation before acting
export { restoreSession, fetchMe }
