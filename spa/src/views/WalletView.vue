<template>
  <div class="wallet-page">
    <div class="wallet-content">
      <div class="wallet-actions">
        <router-link to="/account" class="wallet-back">
          <i class="fas fa-arrow-left"></i> Back to Account
        </router-link>
      </div>

      <div v-if="!auth.isLoggedIn.value" class="wallet-guest">
        <p>Sign in to view your wallet.</p>
        <router-link to="/login" class="wallet-btn primary">Sign in</router-link>
      </div>

      <template v-else>
        <div class="wallet-balance-card">
          <span class="wallet-balance-label">Current Balance</span>
          <span class="wallet-balance-amount">{{ formatCurrency(balance) }}</span>
        </div>
        <p v-if="walletAmountError" class="wallet-error-note">{{ walletAmountError }}</p>

        <div class="wallet-topup-card">
          <div class="wallet-topup-copy">
            <h2>Fund Wallet</h2>
            <p>Pick a quick amount or enter your own before heading to Stripe.</p>
          </div>
          <div class="wallet-funding">
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
            </div>
            <div class="wallet-custom-amount">
              <span class="wallet-custom-prefix">$</span>
              <input
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
            <p v-if="walletAmountError" class="wallet-error-note">{{ walletAmountError }}</p>
            <button type="button" class="wallet-btn primary wallet-fund-btn" :disabled="fundingLoading" @click="fundWallet">
              <i v-if="fundingLoading" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-plus-circle"></i>
              Add {{ formatCurrency(normalizedWalletAmount) }}
            </button>
          </div>
        </div>

        <div class="wallet-card">
          <div class="wallet-card-header">
            <h2>Transaction History</h2>
            <button type="button" class="wallet-refresh" :disabled="loading" @click="load" title="Refresh">
              <i class="fas fa-sync-alt" :class="{ 'fa-spin': loading }"></i>
            </button>
          </div>
          <div class="wallet-card-body">
            <div v-if="loading" class="wallet-state">
              <i class="fas fa-spinner fa-spin"></i>
              <p>Loading transactions...</p>
            </div>
            <div v-else-if="error" class="wallet-state wallet-error">
              <i class="fas fa-exclamation-triangle"></i>
              <p>{{ error }}</p>
              <button type="button" class="wallet-btn primary" @click="load">Try Again</button>
            </div>
            <div v-else-if="transactions.length === 0" class="wallet-state">
              <i class="fas fa-wallet"></i>
              <p>No transactions yet</p>
              <router-link to="/account" class="wallet-btn primary">Add Funds</router-link>
            </div>
            <div v-else class="wallet-table-wrap">
              <table class="wallet-table">
                <thead>
                  <tr>
                    <th>Date & Time</th>
                    <th>Type</th>
                    <th>Description</th>
                    <th class="num">Amount</th>
                    <th class="num">Balance After</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="tx in transactions" :key="tx.id">
                    <td>
                      <div>{{ formatDate(tx.created_at) }}</div>
                      <div class="wallet-time">{{ formatTime(tx.created_at) }}</div>
                    </td>
                    <td>
                      <span class="wallet-type" :class="tx.type">{{ txTypeLabel(tx.type) }}</span>
                    </td>
                    <td>{{ tx.description || '—' }}</td>
                    <td class="num" :class="tx.type === 'fund' ? 'positive' : tx.type === 'spend' ? 'negative' : 'neutral'">
                      {{ tx.type === 'fund' ? '+' : '-' }}{{ formatCurrency(Math.abs(tx.amount)) }}
                    </td>
                    <td class="num">{{ formatCurrency(tx.balance_after) }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
            <div v-if="transactions.length >= limit && !loading" class="wallet-load-more">
              <button type="button" class="wallet-btn secondary" :disabled="loadingMore" @click="loadMore">
                <i v-if="loadingMore" class="fas fa-spinner fa-spin"></i>
                {{ loadingMore ? 'Loading...' : 'Load More' }}
              </button>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuth } from '../composables/useAuth'
import { apiFetch } from '../composables/useApi'

const auth = useAuth()
const balance = ref(0)
const transactions = ref([])
const loading = ref(true)
const loadingMore = ref(false)
const fundingLoading = ref(false)
const error = ref(null)
const limit = 50
const offset = ref(0)
const walletPresets = [5, 10, 25, 50]
const walletAmount = ref(10)
const walletAmountError = ref('')
const walletAmountStorageKey = 'ahoy:lastWalletFundAmount'

const normalizedWalletAmount = computed(() => {
  const amount = Number(walletAmount.value)
  if (!Number.isFinite(amount)) return 1
  return Math.round(Math.min(1000, Math.max(1, amount)) * 100) / 100
})

const isWalletAmountValid = computed(() => {
  const amount = Number(walletAmount.value)
  return Number.isFinite(amount) && amount >= 1 && amount <= 1000
})

async function load() {
  if (!auth.isLoggedIn.value) return
  loading.value = true
  error.value = null
  try {
    const [balRes, txRes] = await Promise.all([
      apiFetch('/payments/wallet'),
      apiFetch(`/payments/wallet/transactions?limit=${limit}`),
    ])
    balance.value = balRes.balance ?? 0
    transactions.value = txRes.transactions ?? []
    offset.value = transactions.value.length
  } catch (e) {
    error.value = 'Failed to load transactions. Please try again.'
    console.error(e)
  } finally {
    loading.value = false
  }
}

async function loadMore() {
  if (loadingMore.value || transactions.value.length < offset.value) return
  loadingMore.value = true
  try {
    const data = await apiFetch(`/payments/wallet/transactions?limit=${limit}&offset=${offset.value}`)
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

async function fundWallet() {
  if (!isWalletAmountValid.value) {
    walletAmountError.value = 'Choose an amount between $1 and $1,000.'
    return
  }
  walletAmountError.value = ''
  fundingLoading.value = true
  try {
    window.localStorage.setItem(walletAmountStorageKey, String(normalizedWalletAmount.value))
    const data = await apiFetch('/payments/wallet/fund', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount: normalizedWalletAmount.value }),
    })
    if (data.checkout_url) {
      window.location.href = data.checkout_url
      return
    }
    walletAmountError.value = data.error || 'Could not start checkout.'
  } catch (e) {
    walletAmountError.value = e.message || 'Failed to start checkout.'
  } finally {
    fundingLoading.value = false
  }
}

onMounted(() => {
  const savedAmount = Number(window.localStorage.getItem(walletAmountStorageKey))
  if (Number.isFinite(savedAmount) && savedAmount >= 1 && savedAmount <= 1000) {
    walletAmount.value = Math.round(savedAmount * 100) / 100
  }
  if (auth.isLoggedIn.value) load()
})

function formatCurrency(amount) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(amount ?? 0)
}
function formatDate(dateString) {
  if (!dateString) return '—'
  return new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' })
}
function formatTime(dateString) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', hour12: true })
}
function txTypeLabel(type) {
  if (!type) return '—'
  return type.charAt(0).toUpperCase() + type.slice(1)
}
</script>

<style scoped>
.wallet-page { min-height: 100vh; background: var(--page-bg, #0a0a0a); }
.wallet-hero.podcasts-hero .podcasts-hero-inner h1 { margin: 0 0 6px 0; }
.wallet-content { width: 100%; padding: 1.5rem 1.5rem 100px; }
.wallet-actions { margin-bottom: 1rem; }
.wallet-back {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--accent-primary, #6ddcff);
  text-decoration: none;
  font-size: 0.95rem;
}
.wallet-back:hover { text-decoration: underline; }
.wallet-back:focus-visible,
.wallet-btn:focus-visible,
.wallet-amount-chip:focus-visible,
.wallet-custom-input:focus-visible {
  outline: 2px solid var(--accent-primary, #6ddcff);
  outline-offset: 2px;
}
.wallet-balance-card {
  background: rgba(255,255,255,0.06);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.wallet-topup-card {
  margin-bottom: 1.5rem;
  padding: 1.25rem;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  background: rgba(255,255,255,0.04);
}
.wallet-topup-copy h2 {
  margin: 0 0 0.35rem;
  font-size: 1.05rem;
  color: #fff;
}
.wallet-topup-copy p {
  margin: 0 0 1rem;
  color: rgba(255,255,255,0.65);
  font-size: 0.92rem;
}
.wallet-funding { display: grid; gap: 0.75rem; }
.wallet-amount-presets {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}
.wallet-amount-chip {
  border: 1px solid rgba(255,255,255,0.12);
  background: rgba(255,255,255,0.05);
  color: #fff;
  border-radius: 999px;
  padding: 0.45rem 0.8rem;
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
  color: rgba(255,255,255,0.7);
}
.wallet-custom-input {
  width: 100%;
  border: 0;
  outline: none;
  background: transparent;
  color: #fff;
  padding: 10px 12px 10px 0;
  font-size: 0.95rem;
}
.wallet-error-note {
  margin: 0;
  color: #fca5a5;
  font-size: 0.85rem;
}
.wallet-fund-btn {
  justify-content: center;
}
.wallet-balance-label { color: rgba(255,255,255,0.7); font-weight: 500; }
.wallet-balance-amount { font-size: 1.75rem; font-weight: 700; color: #fff; }
.wallet-card {
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 12px;
  overflow: hidden;
}
.wallet-card-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid rgba(255,255,255,0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.wallet-card-header h2 { margin: 0; font-size: 1.1rem; color: #fff; }
.wallet-refresh {
  background: none;
  border: none;
  color: rgba(255,255,255,0.7);
  cursor: pointer;
  padding: 0.5rem;
}
.wallet-refresh:hover { color: #fff; }
.wallet-card-body { padding: 1.5rem; }
.wallet-state {
  text-align: center;
  padding: 2rem;
  color: rgba(255,255,255,0.6);
}
.wallet-state i { font-size: 2rem; display: block; margin-bottom: 0.5rem; opacity: 0.7; }
.wallet-state p { margin: 0 0 1rem; }
.wallet-error i { color: #f59e0b; }
.wallet-table-wrap { overflow-x: auto; }
.wallet-table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.wallet-table th, .wallet-table td { padding: 0.75rem; text-align: left; border-bottom: 1px solid rgba(255,255,255,0.06); }
.wallet-table th { color: rgba(255,255,255,0.6); font-weight: 600; }
.wallet-table td { color: rgba(255,255,255,0.9); }
.wallet-table th.num, .wallet-table td.num { text-align: right; }
.wallet-time { font-size: 0.75rem; color: rgba(255,255,255,0.5); }
.wallet-type {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 500;
}
.wallet-type.fund { background: rgba(34,197,94,0.2); color: #86efac; }
.wallet-type.spend { background: rgba(239,68,68,0.2); color: #fca5a5; }
.wallet-type.refund { background: rgba(59,130,246,0.2); color: #93c5fd; }
.wallet-table td.positive { color: #86efac; }
.wallet-table td.negative { color: #fca5a5; }
.wallet-table td.neutral { color: #93c5fd; }
.wallet-load-more { text-align: center; margin-top: 1rem; }
.wallet-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.2rem;
  border-radius: 8px;
  font-weight: 600;
  text-decoration: none;
  border: none;
  cursor: pointer;
  font-size: 0.95rem;
}
.wallet-btn.primary { background: var(--accent-primary, #6ddcff); color: #111; }
.wallet-btn.secondary { background: rgba(255,255,255,0.1); color: #fff; border: 1px solid rgba(255,255,255,0.2); }
.wallet-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.wallet-guest { text-align: center; padding: 3rem 1rem; color: rgba(255,255,255,0.7); }
.wallet-guest p { margin-bottom: 1rem; }
@media (max-width: 768px) {
  .wallet-table th:nth-child(3), .wallet-table td:nth-child(3) { display: none; }
  .wallet-content { padding: 1rem 0 100px; }
}
</style>
