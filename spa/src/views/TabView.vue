<template>
  <div class="tab-page">

    <!-- Guest preview -->
    <div v-if="!auth.isLoggedIn.value" class="tab-guest-preview">

      <!-- Mock mobile hero -->
      <div class="tab-preview-hero">
        <span class="tab-hero-label">Your Tab</span>
        <span class="tab-hero-amount tab-preview-blur">$20.00</span>
        <div class="tab-hero-spend tab-preview-disabled">
          <i class="fas fa-bolt"></i> Tip an Artist
        </div>
      </div>

      <!-- Mock feed -->
      <div class="tab-preview-feed">
        <div class="tab-feed-header"><span>Recent</span></div>
        <div v-for="row in previewRows" :key="row.desc" class="tab-feed-row tab-preview-row">
          <div class="tab-feed-icon" :class="row.type"><i :class="row.icon"></i></div>
          <div class="tab-feed-meta">
            <span class="tab-feed-desc">{{ row.desc }}</span>
            <span class="tab-feed-date">{{ row.date }}</span>
          </div>
          <div class="tab-feed-right">
            <span class="tab-feed-amount" :class="row.type === 'fund' ? 'positive' : 'negative'">{{ row.amount }}</span>
            <span class="tab-feed-balance tab-preview-blur">{{ row.balance }}</span>
          </div>
        </div>
      </div>

      <!-- CTA overlay -->
      <div class="tab-preview-cta">
        <div class="tab-preview-cta-inner">
          <i class="fas fa-receipt"></i>
          <h2>Open your tab</h2>
          <p>Load once. Tip artists, buy merch, pay at shows — no card needed.</p>
          <router-link to="/login" class="tab-btn primary">Sign in to get started</router-link>
        </div>
      </div>

    </div>

    <template v-else>

      <!-- MOBILE LAYOUT -->
      <div class="tab-mobile">

        <!-- Hero balance -->
        <div class="tab-hero">
          <span class="tab-hero-label">Your Tab</span>
          <span class="tab-hero-amount">{{ formatCurrency(balance) }}</span>
          <router-link to="/support" class="tab-hero-spend">
            <i class="fas fa-bolt"></i> Tip an Artist
          </router-link>
        </div>

        <!-- Transaction feed -->
        <div class="tab-feed">
          <div class="tab-feed-header">
            <span>Recent</span>
            <button type="button" class="tab-refresh" :disabled="loading" @click="load">
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
            </button>
          </div>

          <div v-if="loading" class="tab-state">
            <i class="fas fa-spinner fa-spin"></i>
            <p>Loading...</p>
          </div>
          <div v-else-if="error" class="tab-state tab-state-error">
            <i class="fas fa-exclamation-triangle"></i>
            <p>{{ error }}</p>
            <button class="tab-btn primary" @click="load">Try Again</button>
          </div>
          <div v-else-if="transactions.length === 0" class="tab-state">
            <i class="fas fa-receipt"></i>
            <p>No transactions yet.</p>
          </div>
          <div v-else>
            <div v-for="tx in transactions" :key="tx.id" class="tab-feed-row">
              <div class="tab-feed-icon" :class="tx.type">
                <i :class="txIcon(tx.type)"></i>
              </div>
              <div class="tab-feed-meta">
                <span class="tab-feed-desc">{{ tx.description || txLabel(tx.type) }}</span>
                <span class="tab-feed-date">{{ formatDate(tx.created_at) }} · {{ formatTime(tx.created_at) }}</span>
              </div>
              <div class="tab-feed-right">
                <span class="tab-feed-amount" :class="tx.type === 'fund' ? 'positive' : tx.type === 'spend' ? 'negative' : 'neutral'">
                  {{ tx.type === 'fund' ? '+' : '-' }}{{ formatCurrency(Math.abs(tx.amount)) }}
                </span>
                <span class="tab-feed-balance">{{ formatCurrency(tx.balance_after) }}</span>
              </div>
            </div>
            <div v-if="transactions.length >= pageLimit" class="tab-feed-more">
              <button class="tab-btn secondary" :disabled="loadingMore" @click="loadMore">
                <i v-if="loadingMore" class="fas fa-spinner fa-spin"></i>
                {{ loadingMore ? 'Loading...' : 'Load more' }}
              </button>
            </div>
          </div>
        </div>

        <!-- Sticky load bar -->
        <div class="tab-sticky-load">
          <div class="tab-sticky-presets">
            <button
              v-for="preset in presets"
              :key="preset.pay"
              type="button"
              class="tab-amount-chip"
              :class="{ active: tabAmount === preset.pay }"
              @click="tabAmount = preset.pay"
            >
              <span class="chip-pay">${{ preset.pay }}</span>
              <span class="chip-wallet">${{ preset.wallet }} to spend</span>
            </button>
            <div class="tab-custom-amount">
              <span class="tab-custom-prefix">$</span>
              <input
                v-model.number="tabAmount"
                class="tab-custom-input"
                type="number"
                min="14"
                max="1000"
                step="1"
                inputmode="decimal"
                aria-label="Tab load amount"
              />
            </div>
          </div>
          <p v-if="amountError" class="tab-error-note">{{ amountError }}</p>
          <button type="button" class="tab-btn primary tab-sticky-cta" :disabled="loadingFund" @click="fundTab">
            <i v-if="loadingFund" class="fas fa-spinner fa-spin"></i>
            <i v-else class="fas fa-plus-circle"></i>
            Add {{ formatCurrency(normalizedAmount) }}
          </button>
        </div>
      </div>

      <!-- DESKTOP LAYOUT -->
      <div class="tab-desktop">
        <div class="tab-content">

          <!-- Balance -->
          <div class="tab-balance-card">
            <div class="tab-balance-left">
              <span class="tab-balance-label">Your Tab</span>
              <span class="tab-balance-amount">{{ formatCurrency(balance) }}</span>
            </div>
            <router-link to="/support" class="tab-spend-btn">
              <i class="fas fa-bolt"></i> Tip an Artist
            </router-link>
          </div>

          <!-- Load tab -->
          <div class="tab-load-card">
            <div class="tab-load-copy">
              <h2>Load your tab</h2>
              <p>$4/mo keeps Ahoy running. The rest goes straight to your tab to spend on artists and merch.</p>
            </div>
            <div class="tab-funding">
              <div class="tab-amount-presets">
                <button
                  v-for="preset in presets"
                  :key="preset"
                  type="button"
                  class="tab-amount-chip"
                  :class="{ active: tabAmount === preset }"
                  @click="tabAmount = preset"
                >
                  ${{ preset }}
                </button>
              </div>
              <div class="tab-custom-amount">
                <span class="tab-custom-prefix">$</span>
                <input
                  v-model.number="tabAmount"
                  class="tab-custom-input"
                  type="number"
                  min="14"
                  max="1000"
                  step="1"
                  inputmode="decimal"
                  aria-label="Tab load amount"
                />
              </div>
              <p v-if="amountError" class="tab-error-note">{{ amountError }}</p>
              <button type="button" class="tab-btn primary tab-load-btn" :disabled="loadingFund" @click="fundTab">
                <i v-if="loadingFund" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-plus-circle"></i>
                Add {{ formatCurrency(walletFromAmount) }} to tab · {{ formatCurrency(normalizedAmount) }}/mo
              </button>
            </div>
          </div>

          <!-- Transaction history table -->
          <div class="tab-history-card">
            <div class="tab-history-header">
              <h2>Tab History</h2>
              <button type="button" class="tab-refresh" :disabled="loading" @click="load" title="Refresh">
                <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
              </button>
            </div>
            <div class="tab-history-body">
              <div v-if="loading" class="tab-state">
                <i class="fas fa-spinner fa-spin"></i>
                <p>Loading history...</p>
              </div>
              <div v-else-if="error" class="tab-state tab-state-error">
                <i class="fas fa-exclamation-triangle"></i>
                <p>{{ error }}</p>
                <button class="tab-btn primary" @click="load">Try Again</button>
              </div>
              <div v-else-if="transactions.length === 0" class="tab-state">
                <i class="fas fa-receipt"></i>
                <p>No transactions yet. Load your tab to get started.</p>
              </div>
              <div v-else>
                <table class="tab-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Type</th>
                      <th>Description</th>
                      <th class="num">Amount</th>
                      <th class="num">Balance</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="tx in transactions" :key="tx.id">
                      <td>
                        <div>{{ formatDate(tx.created_at) }}</div>
                        <div class="tab-time">{{ formatTime(tx.created_at) }}</div>
                      </td>
                      <td><span class="tab-type-badge" :class="tx.type">{{ txLabel(tx.type) }}</span></td>
                      <td>{{ tx.description || '—' }}</td>
                      <td class="num" :class="tx.type === 'fund' ? 'positive' : tx.type === 'spend' ? 'negative' : 'neutral'">
                        {{ tx.type === 'fund' ? '+' : '-' }}{{ formatCurrency(Math.abs(tx.amount)) }}
                      </td>
                      <td class="num">{{ formatCurrency(tx.balance_after) }}</td>
                    </tr>
                  </tbody>
                </table>
                <div v-if="transactions.length >= pageLimit" class="tab-load-more">
                  <button class="tab-btn secondary" :disabled="loadingMore" @click="loadMore">
                    <i v-if="loadingMore" class="fas fa-spinner fa-spin"></i>
                    {{ loadingMore ? 'Loading...' : 'Load more' }}
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>

    </template>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth'
import { apiFetch } from '../composables/useApi'

const auth = useAuth()

const previewRows = [
  { type: 'fund',  icon: 'fas fa-arrow-down', desc: 'Loaded tab',        date: 'May 29 · 2:14pm', amount: '+$20.00', balance: '$20.00' },
  { type: 'spend', icon: 'fas fa-bolt',        desc: 'Tip · Rob Meglio',  date: 'May 29 · 3:01pm', amount: '-$3.00',  balance: '$17.00' },
  { type: 'spend', icon: 'fas fa-bolt',        desc: 'Tip · The Hollows', date: 'May 28 · 7:45pm', amount: '-$5.00',  balance: '$12.00' },
]

const balance = ref(0)
const transactions = ref([])
const loading = ref(true)
const loadingMore = ref(false)
const loadingFund = ref(false)
const error = ref(null)
const pageLimit = 50
const offset = ref(0)
// [payment_amount, wallet_amount] — $4 flat goes to Ahoy
const presets = [
  { pay: 14, wallet: 10 },
  { pay: 24, wallet: 20 },
  { pay: 54, wallet: 50 },
]
const tabAmount = ref(14)
const amountError = ref('')
const storageKey = 'ahoy:lastTabAmount'

const normalizedAmount = computed(() => {
  const n = Number(tabAmount.value)
  if (!Number.isFinite(n)) return 1
  return Math.round(Math.min(1000, Math.max(1, n)) * 100) / 100
})

const isAmountValid = computed(() => {
  const n = Number(tabAmount.value)
  return Number.isFinite(n) && n >= 14 && n <= 1000
})

const walletFromAmount = computed(() => {
  const n = normalizedAmount.value
  return Math.max(0, Math.round((n - 4) * 100) / 100)
})

async function load() {
  if (!auth.isLoggedIn.value) return
  loading.value = true
  error.value = null
  try {
    const [balRes, txRes] = await Promise.all([
      apiFetch('/payments/wallet'),
      apiFetch(`/payments/wallet/transactions?limit=${pageLimit}`),
    ])
    balance.value = balRes.balance ?? 0
    transactions.value = txRes.transactions ?? []
    offset.value = transactions.value.length
  } catch (e) {
    error.value = 'Failed to load. Please try again.'
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value) return
  loadingMore.value = true
  try {
    const data = await apiFetch(`/payments/wallet/transactions?limit=${pageLimit}&offset=${offset.value}`)
    const list = data.transactions || []
    if (list.length) {
      transactions.value = [...transactions.value, ...list]
      offset.value = transactions.value.length
    }
  } catch (e) {
    console.error(e)
  } finally {
    loadingMore.value = false
  }
}

async function fundTab() {
  if (!isAmountValid.value) {
    amountError.value = 'Minimum is $14 ($10 to your tab, $4 to Ahoy).'
    return
  }
  amountError.value = ''
  loadingFund.value = true
  try {
    window.localStorage.setItem(storageKey, String(normalizedAmount.value))
    const data = await apiFetch('/payments/wallet/fund', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: normalizedAmount.value }),
    })
    if (data.checkout_url) {
      window.location.href = data.checkout_url
      return
    }
    amountError.value = data.error || 'Could not start checkout.'
  } catch (e) {
    amountError.value = e.message || 'Failed to start checkout.'
  } finally {
    loadingFund.value = false
  }
}

onMounted(() => {
  const saved = Number(window.localStorage.getItem(storageKey))
  if (Number.isFinite(saved) && saved >= 1 && saved <= 1000) {
    tabAmount.value = Math.round(saved * 100) / 100
  }
  if (auth.isLoggedIn.value) load()
})

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount ?? 0)
}
function formatDate(d) {
  if (!d) return '—'
  return new Date(d).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
function formatTime(d) {
  if (!d) return ''
  return new Date(d).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })
}
function txLabel(type) {
  const map = { fund: 'Load', spend: 'Spend', refund: 'Refund' }
  return map[type] || (type ? type.charAt(0).toUpperCase() + type.slice(1) : '—')
}
function txIcon(type) {
  const map = { fund: 'fas fa-arrow-down', spend: 'fas fa-bolt', refund: 'fas fa-undo' }
  return map[type] || 'fas fa-circle'
}
</script>

<style scoped>
.tab-page { min-height: 100vh; background: var(--page-bg, #0a0a0a); }

/* Guest preview */
.tab-guest-preview {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}
.tab-preview-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2.5rem 1.5rem 2rem;
  background: linear-gradient(180deg, rgba(109,220,255,0.1) 0%, transparent 100%);
  text-align: center;
}
.tab-preview-blur {
  filter: blur(6px);
  user-select: none;
}
.tab-preview-disabled {
  opacity: 0.4;
  pointer-events: none;
}
.tab-preview-feed {
  opacity: 0.5;
  pointer-events: none;
}
.tab-preview-row { opacity: 0.7; }
.tab-preview-cta {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(10,10,10,0.98) 60%, transparent);
  padding: 3rem 1.5rem calc(2rem + env(safe-area-inset-bottom, 0px));
  display: flex;
  justify-content: center;
  z-index: 10;
}
.tab-preview-cta-inner {
  text-align: center;
  max-width: 320px;
}
.tab-preview-cta-inner i {
  font-size: 2rem;
  color: var(--accent-primary, #6ddcff);
  margin-bottom: 0.75rem;
  display: block;
}
.tab-preview-cta-inner h2 {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}
.tab-preview-cta-inner p {
  color: rgba(255,255,255,0.6);
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 1.25rem;
}
.tab-preview-cta-inner .tab-btn {
  width: 100%;
  justify-content: center;
  padding: 0.85rem;
  font-size: 1rem;
}
@media (min-width: 769px) {
  .tab-preview-cta {
    position: static;
    background: none;
    padding: 0;
    margin-top: 2rem;
  }
  .tab-guest-preview { min-height: auto; }
}

/* ── MOBILE ── */
.tab-mobile { display: none; flex-direction: column; height: 100%; }

.tab-hero {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2.5rem 1.5rem 2rem;
  background: linear-gradient(180deg, rgba(109,220,255,0.1) 0%, transparent 100%);
  text-align: center;
}
.tab-hero-label {
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.5);
  margin-bottom: 0.4rem;
}
.tab-hero-amount {
  font-size: 3.5rem;
  font-weight: 800;
  color: #fff;
  line-height: 1;
  margin-bottom: 1.25rem;
}
.tab-hero-spend {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--accent-primary, #6ddcff);
  color: #111;
  border-radius: 999px;
  padding: 0.55rem 1.25rem;
  font-weight: 700;
  font-size: 0.9rem;
  text-decoration: none;
}

/* Feed */
.tab-feed { flex: 1; overflow-y: auto; padding: 0 0 1rem; }
.tab-feed-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1.25rem 0.5rem;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: rgba(255,255,255,0.4);
}
.tab-feed-row {
  display: flex;
  align-items: center;
  gap: 0.85rem;
  padding: 0.85rem 1.25rem;
  border-bottom: 1px solid rgba(255,255,255,0.05);
}
.tab-feed-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 0.85rem;
}
.tab-feed-icon.fund { background: rgba(34,197,94,0.15); color: #86efac; }
.tab-feed-icon.spend { background: rgba(109,220,255,0.12); color: var(--accent-primary, #6ddcff); }
.tab-feed-icon.refund { background: rgba(59,130,246,0.15); color: #93c5fd; }
.tab-feed-meta { flex: 1; min-width: 0; }
.tab-feed-desc {
  display: block;
  font-size: 0.9rem;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.tab-feed-date { display: block; font-size: 0.75rem; color: rgba(255,255,255,0.4); margin-top: 2px; }
.tab-feed-right { text-align: right; flex-shrink: 0; }
.tab-feed-amount { display: block; font-size: 0.95rem; font-weight: 700; }
.tab-feed-balance { display: block; font-size: 0.72rem; color: rgba(255,255,255,0.4); margin-top: 2px; }
.tab-feed-more { text-align: center; padding: 1rem; }

/* Sticky load bar */
.tab-sticky-load {
  position: sticky;
  bottom: 0;
  background: rgba(10,10,10,0.95);
  backdrop-filter: blur(12px);
  border-top: 1px solid rgba(255,255,255,0.08);
  padding: 0.85rem 1.25rem calc(0.85rem + env(safe-area-inset-bottom, 0px));
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
}
.tab-sticky-presets {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-wrap: nowrap;
  overflow-x: auto;
  scrollbar-width: none;
}
.tab-sticky-presets::-webkit-scrollbar { display: none; }
.tab-sticky-cta { width: 100%; justify-content: center; padding: 0.75rem; font-size: 1rem; }

/* ── DESKTOP ── */
.tab-desktop { display: block; }
.tab-content { width: 100%; max-width: 720px; margin: 0 auto; padding: 1.5rem 1.5rem 120px; }

.tab-balance-card {
  background: linear-gradient(135deg, rgba(109,220,255,0.12), rgba(109,220,255,0.04));
  border: 1px solid rgba(109,220,255,0.25);
  border-radius: 16px;
  padding: 1.5rem;
  margin-bottom: 1.25rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}
.tab-balance-label { display: block; color: rgba(255,255,255,0.6); font-size: 0.85rem; font-weight: 500; margin-bottom: 4px; }
.tab-balance-amount { font-size: 2.25rem; font-weight: 700; color: #fff; }
.tab-spend-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: var(--accent-primary, #6ddcff);
  color: #111;
  border-radius: 8px;
  padding: 0.55rem 1rem;
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
  white-space: nowrap;
  flex-shrink: 0;
}
.tab-spend-btn:hover { opacity: 0.9; }

.tab-load-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 14px;
  padding: 1.25rem;
  margin-bottom: 1.25rem;
}
.tab-load-copy h2 { margin: 0 0 0.3rem; font-size: 1rem; color: #fff; }
.tab-load-copy p { margin: 0 0 1rem; color: rgba(255,255,255,0.6); font-size: 0.88rem; }
.tab-funding { display: grid; gap: 0.75rem; }
.tab-load-btn { justify-content: center; }

.tab-history-card {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 14px;
  overflow: hidden;
}
.tab-history-header {
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.tab-history-header h2 { margin: 0; font-size: 1rem; color: #fff; }
.tab-history-body { padding: 1.25rem; }
.tab-table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
.tab-table th, .tab-table td { padding: 0.7rem 0.5rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.06); }
.tab-table th { color: rgba(255,255,255,0.55); font-weight: 600; }
.tab-table td { color: rgba(255,255,255,0.9); }
.tab-table th.num, .tab-table td.num { text-align: right; }
.tab-time { font-size: 0.72rem; color: rgba(255,255,255,0.45); }
.tab-load-more { text-align: center; margin-top: 1rem; }

/* Shared */
.tab-amount-presets { display: flex; flex-wrap: wrap; gap: 0.5rem; }
.tab-amount-chip {
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.05);
  color: #fff;
  border-radius: 999px;
  padding: 0.4rem 0.9rem;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  white-space: nowrap;
  flex-shrink: 0;
}
.tab-amount-chip.active { background: var(--accent-primary, #6ddcff); color: #111; border-color: transparent; }
.tab-amount-chip { display: flex; flex-direction: column; align-items: center; padding: 0.45rem 0.9rem; line-height: 1.2; }
.chip-pay { font-size: 0.95rem; font-weight: 700; }
.chip-wallet { font-size: 0.7rem; font-weight: 500; opacity: 0.7; }
.tab-amount-chip.active .chip-wallet { opacity: 0.75; }
.tab-custom-amount {
  display: flex;
  align-items: center;
  width: 90px;
  flex-shrink: 0;
  border-radius: 999px;
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(0,0,0,0.25);
  overflow: hidden;
}
.tab-custom-prefix { padding: 0 6px 0 10px; color: rgba(255,255,255,0.5); font-size: 0.9rem; }
.tab-custom-input {
  width: 100%;
  border: 0;
  outline: none;
  background: transparent;
  color: #fff;
  padding: 8px 8px 8px 0;
  font-size: 0.9rem;
}
.tab-error-note { margin: 0; color: #fca5a5; font-size: 0.85rem; }
.tab-type-badge {
  display: inline-block;
  padding: 0.18rem 0.5rem;
  border-radius: 6px;
  font-size: 0.78rem;
  font-weight: 500;
}
.tab-type-badge.fund { background: rgba(34,197,94,0.2); color: #86efac; }
.tab-type-badge.spend { background: rgba(239,68,68,0.2); color: #fca5a5; }
.tab-type-badge.refund { background: rgba(59,130,246,0.2); color: #93c5fd; }
.tab-table td.positive { color: #86efac; }
.tab-table td.negative { color: #fca5a5; }
.tab-table td.neutral { color: #93c5fd; }
.tab-feed-amount.positive { color: #86efac; }
.tab-feed-amount.negative { color: #fca5a5; }
.tab-feed-amount.neutral { color: #93c5fd; }
.tab-state { text-align: center; padding: 2.5rem 1rem; color: rgba(255,255,255,0.5); }
.tab-state i { font-size: 2rem; display: block; margin-bottom: 0.5rem; opacity: 0.6; }
.tab-state p { margin: 0 0 1rem; }
.tab-state-error i { color: #f59e0b; opacity: 1; }
.tab-refresh { background: none; border: none; color: rgba(255,255,255,0.5); cursor: pointer; padding: 0.4rem; }
.tab-refresh:hover { color: #fff; }
.tab-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  border: none;
  cursor: pointer;
  font-size: 0.92rem;
}
.tab-btn.primary { background: var(--accent-primary, #6ddcff); color: #111; }
.tab-btn.secondary { background: rgba(255,255,255,0.08); color: #fff; border: 1px solid rgba(255,255,255,0.18); }
.tab-btn:disabled { opacity: 0.55; cursor: not-allowed; }
.tab-btn:focus-visible, .tab-amount-chip:focus-visible, .tab-custom-input:focus-visible {
  outline: 2px solid var(--accent-primary, #6ddcff);
  outline-offset: 2px;
}

@media (max-width: 768px) {
  .tab-mobile { display: flex; }
  .tab-desktop { display: none; }
}
</style>
