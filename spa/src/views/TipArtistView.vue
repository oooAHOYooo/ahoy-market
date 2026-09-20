<template>
  <div class="tip-artist-page">
    <!-- Mobile Top App Bar -->
    <header class="tip-app-bar">
      <button class="tip-back-btn" @click="$router.back()">
        <i class="fas fa-arrow-left"></i>
      </button>
      <h1 class="tip-app-title">Boost Artist</h1>
      <div class="tip-spacer"></div>
    </header>

    <main class="tip-main">
      <div class="tip-grid-layout">
        <!-- Left Column -->
        <div class="tip-left-column">
          <!-- Artist Context Section -->
          <section v-if="selectedArtistInfo" class="tip-artist-section">
            <div class="tip-artist-card">
              <div class="tip-artist-image-wrapper">
                <img v-if="selectedArtistInfo?.image" :src="selectedArtistInfo.image" alt="" class="tip-artist-image" @error="($event.target).style.display='none'" />
                <div v-else class="tip-artist-placeholder"><i class="fas fa-user-music"></i></div>
              </div>
              <div class="tip-artist-info">
                <p class="tip-label">SUPPORTING</p>
                <h2 class="tip-artist-name">{{ selectedArtist }}</h2>
              </div>
            </div>
          </section>

          <!-- Artist Selection (if not selected) -->
          <section v-if="!selectedArtistInfo" class="tip-section">
            <label class="tip-label-text">Select Artist</label>
            <select v-model="selectedArtist" @change="onArtistChange" class="tip-select">
              <option value="">-- Choose an artist --</option>
              <option v-for="a in artists" :key="a.id || a.name" :value="a.name">{{ a.name }}</option>
            </select>
          </section>

          <!-- Amount Selection -->
          <section v-if="selectedArtistInfo" class="tip-section">
            <div class="tip-section-header">
              <h3 class="tip-section-title">Select Amount</h3>
              <span class="tip-custom-link" @click="showCustomInput = !showCustomInput">Custom Amount</span>
            </div>

            <div class="tip-amount-grid">
              <button v-for="amt in [5, 10, 20, 50]" :key="amt" type="button" class="tip-amount-btn" :class="{ active: tipAmount === amt }" @click="setAmount(amt)">${{ amt }}</button>
            </div>

            <!-- Custom Amount Input -->
            <div v-if="showCustomInput || (tipAmount && ![5, 10, 20, 50].includes(tipAmount))" class="tip-custom-input-wrapper">
              <span class="tip-currency-symbol">$</span>
              <input v-model.number="tipAmount" type="number" min="1" step="0.01" class="tip-custom-input" placeholder="0.00" />
            </div>
          </section>


          <!-- Optional Message -->
          <section v-if="selectedArtistInfo" class="tip-section">
            <label class="tip-label-text">Optional Message</label>
            <textarea v-model="tipNote" class="tip-textarea" placeholder="Leave a message for the artist..." rows="2"></textarea>
          </section>

          <!-- Submit Button (Mobile only) -->
          <section v-if="selectedArtistInfo" class="tip-action tip-action-mobile">
            <button type="button" class="tip-submit-btn" :disabled="!selectedArtist || !tipAmount || tipAmount < 1 || loading" @click="submitTip">
              <span v-if="loading" class="tip-spinner">
                <i class="fas fa-spinner fa-spin"></i>
              </span>
              <span v-else>Confirm Boost</span>
            </button>
            <p class="tip-disclaimer">By confirming, you agree to our Terms of Service. Payments processed via Stripe.</p>
          </section>
        </div>

        <!-- Right Column (Sticky Summary - Desktop only) -->
        <div v-if="selectedArtistInfo" class="tip-right-column">
          <div class="tip-summary-sticky">
            <h3 class="tip-summary-title">Contribution Summary</h3>

            <div class="tip-summary-row">
              <span class="tip-summary-label">Boost Amount</span>
              <span class="tip-summary-value">${{ (tipAmount || 0).toFixed(2) }}</span>
            </div>
            <div class="tip-summary-row">
              <span class="tip-summary-label">Processing Fee</span>
              <span class="tip-summary-value">${{ calculateFee().toFixed(2) }}</span>
            </div>
            <div class="tip-summary-divider"></div>
            <div class="tip-summary-row tip-summary-total">
              <span class="tip-total-label">Total Charged</span>
              <div class="tip-total-amount-box">
                <span class="tip-total-symbol">$</span>
                <span class="tip-total-amount">{{ (tipAmount + calculateFee()).toFixed(2) }}</span>
              </div>
            </div>

            <!-- Submit Button (Desktop) -->
            <button type="button" class="tip-submit-btn tip-submit-desktop" :disabled="!selectedArtist || !tipAmount || tipAmount < 1 || loading" @click="submitTip">
              <span v-if="loading" class="tip-spinner">
                <i class="fas fa-spinner fa-spin"></i>
              </span>
              <span v-else>Confirm Boost</span>
            </button>

            <p class="tip-disclaimer">By confirming, you agree to our Terms of Service. Payments processed via Stripe.</p>

            <!-- Trust Signals -->
            <div class="tip-trust-signals">
              <div class="tip-trust-item">
                <i class="fas fa-shield-alt"></i>
                <span>Secure Payment via Stripe</span>
              </div>
              <div class="tip-trust-item">
                <i class="fas fa-heart"></i>
                <span>100% goes directly to the artist</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Tips Section -->
      <section v-if="recentTips.length > 0" class="tip-history-section">
        <h3 class="tip-section-title">Your Boosts</h3>
        <div class="tip-list">
          <div v-for="tip in recentTips" :key="tip.id" class="tip-history-item">
            <div>
              <h4 class="tip-history-artist">{{ tip.artist_name }}</h4>
              <p class="tip-history-date">{{ formatDate(tip.created_at) }}</p>
              <p v-if="tip.note" class="tip-history-note">"{{ tip.note }}"</p>
            </div>
            <div class="tip-history-amount">${{ (tip.amount / 100).toFixed(2) }}</div>
          </div>
        </div>
        <div v-if="recentTips.length > 0" class="tip-history-total">
          <span>Total Boosts</span>
          <span>${{ (totalTipsCents / 100).toFixed(2) }}</span>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuth } from '../composables/useAuth'
import { trackEvent } from '../composables/useAnalytics'
import { apiFetch } from '../composables/useApi'
import { useCartStore } from '../stores/cart'

const router = useRouter()
const route = useRoute()
const auth = useAuth()

const artists = ref([])
const selectedArtist = ref('')
const selectedArtistInfo = computed(() => selectedArtist.value ? artists.value.find(a => a.name === selectedArtist.value) || null : null)
const tipAmount = ref(10)
const tipNote = ref('')
const loading = ref(false)
const recentTips = ref([])
const showCustomInput = ref(false)
const totalTipsCents = computed(() => recentTips.value.reduce((s, t) => s + (t.amount || 0), 0))

const cartStore = useCartStore()

onMounted(() => {
  if (!auth.isLoggedIn.value) {
    router.replace('/login')
    return
  }
  const artistId = route.query.artist || route.query.artist_id || ''
  const artistName = route.query.artist_name || String(artistId).replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  if (artistId) {
    cartStore.addBoost(String(artistId), artistName, String(artistId), 0.05)
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: `Added $0.05 boost for ${artistName} to cart!`, type: 'success' } }))
  }
  router.replace({ path: '/checkout', query: { type: 'cart' } })
})

function onArtistChange() {
  // selectedArtistInfo is computed
}

function setAmount(amount) {
  tipAmount.value = amount
  showCustomInput.value = false
}

function calculateFee() {
  const amount = tipAmount.value || 0
  // Stripe fee: 2.9% + $0.30
  return Math.round((amount * 0.029 + 0.30) * 100) / 100
}

async function loadArtists() {
  try {
    const data = await apiFetch('/api/artists')
    const list = data.artists || []
    try {
      const music = await apiFetch('/api/music')
      const names = new Set(list.map(a => a.name))
      ;(music.tracks || []).forEach(t => { if (t.artist && !names.has(t.artist)) { list.push({ name: t.artist, id: `artist_${t.artist}`, description: 'Indie artist' }); names.add(t.artist) } })
    } catch {}
    list.sort((a, b) => (a.name || '').localeCompare(b.name || ''))
    artists.value = list
  } catch (e) {
    console.error(e)
  }
}

async function loadRecentTips() {
  try {
    const data = await apiFetch('/api/tips')
    if (data && typeof data === 'object' && 'tips' in data) {
      recentTips.value = data.tips || []
    }
  } catch (e) {
    console.warn('Failed to load recent tips:', e)
    recentTips.value = []
  }
}

async function submitTip() {
  if (!selectedArtist.value || !tipAmount.value || tipAmount.value < 1) return
  loading.value = true
  try {
    trackEvent('support_intent', {
      context: 'tip_artist',
      artist_name: selectedArtist.value,
      amount: Number(tipAmount.value),
    })
    await apiFetch('/api/tips', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        artist_name: selectedArtist.value,
        amount: Math.round(Number(tipAmount.value) * 100),
        note: (tipNote.value || '').slice(0, 500),
      }),
    })
    selectedArtist.value = ''
    tipAmount.value = 10
    tipNote.value = ''
    showCustomInput.value = false
    await loadRecentTips()
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Boost sent!', type: 'success' } }))
  } catch (e) {
    const msg = e.message || 'Failed to send boost'
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: msg, type: 'error' } }))
  } finally {
    loading.value = false
  }
}

function formatDate(dateString) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
</script>

<style scoped>
/* Color palette from Material Design 3 */
:root {
  --surface: #060e20;
  --surface-dim: #060e20;
  --surface-bright: #1f2b49;
  --surface-container: #0f1930;
  --surface-container-low: #091328;
  --surface-container-high: #141f38;
  --surface-container-highest: #192540;
  --on-surface: #dee5ff;
  --on-surface-variant: #a3aac4;
  --primary: #69daff;
  --secondary: #17c0fd;
  --outline: #6d758c;
  --outline-variant: #40485d;
}

.tip-artist-page {
  min-height: 100dvh;
  background: var(--surface);
  padding-top: 64px;
  padding-bottom: 120px;
}

/* Top App Bar */
.tip-app-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  height: 64px;
  background: rgba(6, 14, 32, 0.7);
  backdrop-filter: blur(12px);
  box-shadow: 0 0 32px rgba(222, 229, 255, 0.06);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.tip-back-btn {
  background: none;
  border: none;
  color: var(--primary);
  font-size: 24px;
  cursor: pointer;
  padding: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.2s;
}

.tip-back-btn:active {
  transform: scale(0.95);
}

.tip-app-title {
  flex: 1;
  text-align: center;
  font-size: 18px;
  font-weight: 600;
  color: var(--on-surface);
  margin: 0;
  letter-spacing: -0.5px;
}

.tip-spacer {
  width: 40px;
}

/* Main content */
.tip-main {
  width: 100%;
  max-width: 1280px;
  margin: 0 auto;
  padding: 0 24px;
  display: flex;
  flex-direction: column;
  gap: 32px;
}

/* Grid Layout for Desktop */
.tip-grid-layout {
  display: grid;
  grid-template-columns: 1fr;
  gap: 48px;
}

.tip-left-column {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.tip-right-column {
  display: none;
}

@media (min-width: 1024px) {
  .tip-grid-layout {
    grid-template-columns: 1fr 380px;
  }

  .tip-right-column {
    display: block;
  }

  .tip-action-mobile {
    display: none;
  }
}

/* Artist Card Section */
.tip-artist-section {
  margin-top: 32px;
}

.tip-artist-card {
  background: var(--surface-container-high);
  border-radius: 24px;
  padding: 24px;
  display: flex;
  align-items: center;
  gap: 16px;
  position: relative;
  overflow: hidden;
}

.tip-artist-image-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 16px;
  overflow: hidden;
  flex-shrink: 0;
}

.tip-artist-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.tip-artist-placeholder {
  width: 100%;
  height: 100%;
  background: rgba(105, 218, 255, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  color: rgba(105, 218, 255, 0.4);
  font-size: 28px;
}

.tip-artist-info {
  flex: 1;
}

.tip-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--on-surface-variant);
  letter-spacing: 1.5px;
  text-transform: uppercase;
  margin-bottom: 4px;
}

.tip-artist-name {
  font-size: 20px;
  font-weight: 700;
  color: var(--on-surface);
  margin: 0;
  letter-spacing: -0.5px;
}

/* Sections */
.tip-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-label-text {
  font-size: 16px;
  font-weight: 600;
  color: var(--on-surface);
  letter-spacing: -0.5px;
}

/* Select dropdown */
.tip-select {
  width: 100%;
  padding: 12px 16px;
  background: var(--surface-container);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  color: var(--on-surface);
  font-size: 16px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s;
}

.tip-select:focus {
  outline: none;
  border-color: var(--primary);
  background: var(--surface-container-high);
}

/* Section header with custom link */
.tip-section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tip-section-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--on-surface);
  margin: 0;
  letter-spacing: -0.5px;
}

.tip-custom-link {
  font-size: 13px;
  font-weight: 500;
  color: var(--primary);
  cursor: pointer;
  transition: opacity 0.2s;
}

.tip-custom-link:active {
  opacity: 0.7;
}

/* Amount Grid */
.tip-amount-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.tip-amount-btn {
  padding: 16px 8px;
  background: var(--surface-container-highest);
  border: none;
  border-radius: 12px;
  color: var(--on-surface);
  font-size: 18px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
  text-align: center;
}

.tip-amount-btn:active {
  transform: scale(0.95);
}

.tip-amount-btn.active {
  background: var(--secondary);
  color: #002a35;
  font-weight: 700;
}

.tip-amount-btn:not(.active):hover {
  background: var(--surface-bright);
}

/* Custom Input */
.tip-custom-input-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding-top: 16px;
}

.tip-currency-symbol {
  font-size: 36px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: -1px;
}

.tip-custom-input {
  background: transparent;
  border: none;
  color: var(--on-surface);
  font-size: 36px;
  font-weight: 700;
  width: 128px;
  text-align: center;
  outline: none;
  font-family: inherit;
  letter-spacing: -1px;
}

.tip-custom-input::placeholder {
  color: var(--surface-bright);
}

/* Support Ahoy Section */
.tip-support-buttons {
  display: flex;
  gap: 8px;
  justify-content: space-between;
}

.tip-support-btn {
  flex: 1;
  padding: 10px 8px;
  background: var(--surface-container);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  color: var(--on-surface-variant);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.tip-support-btn:hover {
  background: var(--surface-container-high);
  border-color: rgba(255, 255, 255, 0.2);
  color: var(--on-surface);
}

.tip-support-btn.active {
  background: var(--secondary);
  border-color: var(--secondary);
  color: #002a35;
  font-weight: 700;
}

.tip-support-note {
  font-size: 12px;
  color: var(--on-surface-variant);
  margin: 8px 0 0;
}

/* Textarea */
.tip-textarea {
  width: 100%;
  padding: 12px 16px;
  background: var(--surface-container);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  color: var(--on-surface);
  font-size: 14px;
  font-family: inherit;
  resize: vertical;
  min-height: 56px;
  box-sizing: border-box;
  transition: all 0.2s;
}

.tip-textarea:focus {
  outline: none;
  border-color: var(--primary);
  background: var(--surface-container-high);
}

/* Summary Section (Mobile) */
.tip-summary {
  background: var(--surface-container-high);
  border-radius: 24px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Summary Sticky (Desktop) */
.tip-summary-sticky {
  position: sticky;
  top: 100px;
  background: var(--surface-container-high);
  border-radius: 16px;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.tip-summary-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--on-surface);
  margin: 0;
  letter-spacing: -0.5px;
}

.tip-summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.tip-summary-label {
  font-size: 14px;
  color: var(--on-surface-variant);
}

.tip-summary-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--on-surface);
}

.tip-summary-divider {
  height: 1px;
  background: rgba(109, 117, 140, 0.2);
  margin: 4px 0;
}

.tip-summary-total {
  padding-top: 8px;
  padding-bottom: 0;
}

.tip-total-label {
  font-size: 18px;
  font-weight: 700;
  color: var(--on-surface);
  letter-spacing: -0.5px;
}

.tip-total-amount-box {
  background: var(--surface-bright);
  padding: 8px 16px;
  border-radius: 12px;
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.tip-total-symbol {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
  letter-spacing: -0.5px;
}

.tip-total-amount {
  font-size: 20px;
  font-weight: 800;
  color: var(--primary);
  letter-spacing: -1px;
}

/* Action Section */
.tip-action {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-submit-btn {
  width: 100%;
  padding: 16px;
  height: 56px;
  border-radius: 24px;
  background: linear-gradient(135deg, #69daff, #00cffc);
  border: none;
  color: #002a35;
  font-size: 13px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 1.6px;
  cursor: pointer;
  transition: all 0.2s;
  box-shadow: 0 8px 24px rgba(105, 218, 255, 0.2);
}

.tip-submit-btn:hover:not(:disabled) {
  box-shadow: 0 12px 32px rgba(105, 218, 255, 0.3);
}

.tip-submit-btn:active {
  transform: scale(0.95);
}

.tip-submit-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.tip-submit-desktop {
  margin-top: 8px;
  margin-bottom: 12px;
}

.tip-spinner {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.tip-disclaimer {
  font-size: 10px;
  color: var(--on-surface-variant);
  opacity: 0.6;
  text-align: center;
  margin: 0;
  line-height: 1.4;
  padding: 0 16px;
}

/* Trust Signals */
.tip-trust-signals {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 8px;
  padding-top: 12px;
  border-top: 1px solid rgba(109, 117, 140, 0.2);
}

.tip-trust-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
  color: var(--on-surface-variant);
}

.tip-trust-item i {
  color: #89a5ff;
  font-size: 14px;
}

/* History Section */
.tip-history-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tip-history-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 12px 16px;
  background: var(--surface-container);
  border-radius: 12px;
}

.tip-history-artist {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--on-surface);
}

.tip-history-date {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--on-surface-variant);
}

.tip-history-note {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--on-surface);
  font-style: italic;
}

.tip-history-amount {
  font-size: 16px;
  font-weight: 700;
  color: var(--primary);
}

.tip-history-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 12px;
  border-top: 1px solid rgba(109, 117, 140, 0.2);
  font-weight: 600;
  color: var(--on-surface);
  font-size: 14px;
}

.tip-history-total span:last-child {
  font-size: 16px;
  color: var(--primary);
}

/* Mobile responsive */
@media (max-width: 768px) {
  .tip-artist-page {
    padding-top: 64px;
    padding-bottom: 100px;
  }

  .tip-main {
    padding: 0 16px;
    gap: 24px;
  }

  .tip-artist-section {
    margin-top: 16px;
  }

  .tip-amount-grid {
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
  }

  .tip-amount-btn {
    padding: 12px 4px;
    font-size: 16px;
  }
}
</style>
