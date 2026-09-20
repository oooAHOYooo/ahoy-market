<template>
  <div class="checkout-page">
    <div class="checkout-card">
      <!-- Step Indicator -->
      <div class="checkout-steps">
        <div :class="{ 'step': true, 'active': currentStep === 'review', 'done': currentStep === 'pay' || currentStep === 'complete' }">
          <i v-if="currentStep !== 'review'" class="fas fa-check"></i><span v-else>Review</span>
        </div>
        <div class="step-divider"></div>
        <div :class="{ 'step': true, 'active': currentStep === 'pay', 'done': currentStep === 'complete' }">
          <i v-if="currentStep === 'complete'" class="fas fa-check"></i><span v-else>Pay</span>
        </div>
        <div class="step-divider"></div>
        <div :class="{ 'step': true, 'active': currentStep === 'complete' }">Complete</div>
      </div>

      <h1 class="checkout-title">Checkout</h1>

      <!-- Error Display -->
      <div v-if="error" class="checkout-error">{{ error }}</div>

      <!-- Cancel link -->
      <div class="checkout-cancel-row">
        <router-link :to="cancelTarget" class="checkout-cancel-link">
          <i class="fas fa-arrow-left"></i> Cancel
        </router-link>
      </div>

      <!-- Boost Type -->
      <template v-if="checkoutType === 'boost'">
        <!-- Artist Info -->
        <div class="checkout-section">
          <p class="checkout-section-label">{{ recipientLabel }}</p>
          <div v-if="!artistId && artists.length > 0" class="artist-select-wrap">
            <select v-model="selectedArtistName" class="checkout-select">
              <option value="">-- Select Artist --</option>
              <option v-for="a in artists" :key="a.name" :value="a.name">{{ a.name }}</option>
            </select>
          </div>
          <p v-else class="checkout-section-value">{{ artistDisplayName }}</p>
        </div>

        <!-- Amount Selector -->
        <div class="checkout-section">
          <p class="checkout-section-label">{{ amountLabel }}</p>
          <div class="boost-amount-selector">
            <button
              v-for="amt in [0.05, 0.50, 1, 5]"
              :key="amt"
              @click="selectPresetAmount(amt)"
              :class="{ 'active': !isCustomAmount && boostAmount === amt }"
              class="amount-btn"
            >
              ${{ amt }}
            </button>
          </div>
          <div class="custom-amount-input">
            <span class="prefix">$</span>
            <input
              :value="boostAmount"
              @input="onCustomAmountInput"
              type="number"
              min="0.05"
              step="0.01"
              placeholder="Custom amount"
              class="amount-input"
              :class="{ 'active': isCustomAmount }"
            />
          </div>
        </div>

        <!-- Fee Breakdown -->
        <div class="checkout-section">
          <p class="breakdown-title">Breakdown</p>
          <div class="breakdown-row">
            <span>{{ breakdownAmountLabel }}</span>
            <span>${{ (boostAmount || 0).toFixed(2) }}</span>
          </div>
          <div class="breakdown-row">
            <span class="breakdown-fee-label">Processing fee <i class="fas fa-info-circle breakdown-fee-info" title="5% to help run the platform"></i></span>
            <span>${{ ahoyServiceFee.toFixed(2) }}</span>
          </div>
          <div class="breakdown-row">
            <span class="breakdown-fee-label">Stripe fee <i class="fas fa-info-circle breakdown-fee-info" title="2.9% + $0.30"></i></span>
            <span>${{ stripeFee.toFixed(2) }}</span>
          </div>
          <div class="breakdown-row">
            <span class="breakdown-fee-label">Est. Tax <i class="fas fa-info-circle breakdown-fee-info" title="Estimated at 8%"></i></span>
            <span>${{ taxEstimate.toFixed(2) }}</span>
          </div>
          <div class="breakdown-total">
            <span>Total</span>
            <span>${{ totalCharged.toFixed(2) }}</span>
          </div>
        </div>

        <!-- Guest note -->
        <p v-if="isGuest" class="guest-note">
          <i class="fas fa-user-slash"></i> Checking out as guest
        </p>

        <!-- Support Ahoy Section -->
        <div v-if="shouldOfferAhoyMatch" class="support-ahoy-section">
          <div class="support-ahoy-header">
            <i class="fas fa-heart"></i>
            <div>
              <p class="support-ahoy-title">Support Ahoy</p>
              <p class="support-ahoy-sub">Help keep the platform running for independent artists</p>
            </div>
          </div>
          <div class="support-ahoy-options">
            <button
              type="button"
              :class="{ 'active': ahoyMatch === 0 }"
              @click="ahoyMatch = 0"
              class="support-btn"
            >None</button>
            <button
              type="button"
              :class="{ 'active': ahoyMatch === 0.5 }"
              @click="ahoyMatch = 0.5"
              class="support-btn"
            >50%</button>
            <button
              type="button"
              :class="{ 'active': ahoyMatch === 1.0 }"
              @click="ahoyMatch = 1.0"
              class="support-btn"
            >100%</button>
          </div>
          <p v-if="ahoyMatch > 0" class="support-ahoy-amount">
            +${{ (boostAmount * ahoyMatch).toFixed(2) }} to Ahoy
          </p>
        </div>

        <!-- Wallet Balance Section -->
        <div v-if="!isGuest && walletBalance !== null" class="wallet-section">
          <div class="wallet-header">
            <div>
              <p class="wallet-label">Wallet Balance</p>
              <p class="wallet-balance">${{ walletBalance.toFixed(2) }}</p>
              <p v-if="walletBalance < totalCharged" class="wallet-need">
                Need ${{ (totalCharged - walletBalance).toFixed(2) }} more
              </p>
              <p v-else class="wallet-perfect">Perfect amount already in your wallet.</p>
            </div>
            <i class="fas fa-wallet wallet-icon"></i>
          </div>

          <template v-if="walletBalance >= totalCharged">
            <label class="wallet-option-label">
              <input
                v-model="useWallet"
                type="checkbox"
                class="wallet-checkbox"
              />
              <div class="wallet-option-text">
                <strong>Pay instantly from wallet</strong>
                <small>No card entry needed • Instant checkout</small>
              </div>
            </label>
            <p class="wallet-hint"><i class="fas fa-bolt"></i> No redirect to payment page</p>
          </template>
          <template v-else>
            <p class="wallet-insufficient-note">Add funds for instant checkout, or pay with card below.</p>
            <div class="wallet-topup-shortcuts">
              <button
                v-if="lastWalletAmount"
                type="button"
                class="wallet-topup-chip"
                :disabled="walletTopupLoading"
                @click="prefillTopUp(lastWalletAmount)"
              >
                Use last ${{ lastWalletAmount.toFixed(2) }}
              </button>
              <button
                type="button"
                class="wallet-topup-chip"
                :disabled="walletTopupLoading"
                @click="prefillTopUp(Math.max(totalCharged - walletBalance, 1))"
              >
                Use shortfall ${{ (totalCharged - walletBalance).toFixed(2) }}
              </button>
            </div>
            <button type="button" class="wallet-topup-btn" :disabled="walletTopupLoading" @click="topUpWallet">
              <i v-if="walletTopupLoading" class="fas fa-spinner fa-spin"></i>
              <i v-else class="fas fa-plus-circle"></i>
              {{ walletTopupLoading ? 'Redirecting...' : `Top up $${(totalCharged - walletBalance).toFixed(2)} →` }}
            </button>
            <p v-if="walletTopupError" class="wallet-topup-error">{{ walletTopupError }}</p>
          </template>
        </div>

        <!-- Stripe Card Element (only show if not using wallet) -->
        <div v-if="!useWallet" class="stripe-section">
          <div id="stripe-card-element" class="stripe-element"></div>
        </div>

        <!-- Error Message -->
        <div v-if="paymentError" class="checkout-error">{{ paymentError }}</div>

        <!-- Submit Button -->
        <div class="checkout-submit-wrap">
          <button
            @click="confirmCheckout"
            :disabled="isProcessing || boostAmount < 0.05 || (!artistId && !selectedArtistName)"
            class="btn-checkout"
          >
            <span class="btn-checkout-inner">
              <i v-if="isProcessing" class="fas fa-spinner fa-spin"></i>
              <i v-else :class="useWallet ? 'fas fa-wallet' : 'fas fa-lock'"></i>
              <span v-if="isProcessing">Processing...</span>
              <span v-else>{{ submitLabel }} — ${{ totalCharged.toFixed(2) }}</span>
            </span>
          </button>
        </div>
      </template>

      <!-- Cart Type -->
      <template v-else-if="checkoutType === 'cart'">
        <!-- Empty Cart -->
        <div v-if="cartStore.items.length === 0" class="cart-empty">
          <i class="fas fa-shopping-cart"></i>
          <p>Your boost cart is empty.</p>
          <router-link to="/artists" class="cart-browse-link">Browse Artists</router-link>
        </div>

        <!-- Cart Items -->
        <div v-else>
          <div class="checkout-section">
            <p class="checkout-section-label">Boost Cart ({{ cartStore.itemCount }} artist{{ cartStore.itemCount !== 1 ? 's' : '' }})</p>
            <p class="cart-suggest-hint"><i class="fas fa-lightbulb"></i> Suggested: $0.05 per artist — adjust any amount below</p>
            <div class="cart-item-list">
              <div v-for="item in cartStore.items" :key="item.artist_id" class="cart-item">
                <div class="cart-item-info">
                  <i class="fas fa-bolt cart-item-icon"></i>
                  <span class="cart-item-name">{{ item.artist_name }}</span>
                </div>
                <div class="cart-item-controls">
                  <button type="button" class="cart-qty-btn" @click="cartStore.updateAmount(item.artist_id, Math.max(0.05, parseFloat((item.amount - 0.05).toFixed(2))))">
                    <i class="fas fa-minus"></i>
                  </button>
                  <span class="cart-item-amount">${{ (item.amount || 0).toFixed(2) }}</span>
                  <button type="button" class="cart-qty-btn" @click="cartStore.updateAmount(item.artist_id, parseFloat((item.amount + 0.05).toFixed(2)))">
                    <i class="fas fa-plus"></i>
                  </button>
                  <button type="button" class="cart-remove-btn" @click="cartStore.removeBoost(item.artist_id)" title="Remove">
                    <i class="fas fa-times"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- Cart Fee Breakdown -->
          <div class="checkout-section">
            <p class="breakdown-title">Breakdown</p>
            <div class="breakdown-row">
              <span>Total Boosts</span>
              <span>${{ cartStore.cartTotal.toFixed(2) }}</span>
            </div>
            <div class="breakdown-row">
              <span class="breakdown-fee-label">Processing fee <i class="fas fa-info-circle breakdown-fee-info" title="5% to help run the platform"></i></span>
              <span>${{ cartAhoyServiceFee.toFixed(2) }}</span>
            </div>
            <div class="breakdown-row">
              <span class="breakdown-fee-label">Stripe fee <i class="fas fa-info-circle breakdown-fee-info" title="2.9% + $0.30 (once for the whole cart)"></i></span>
              <span>${{ cartStripeFee.toFixed(2) }}</span>
            </div>
            <div class="breakdown-row">
              <span class="breakdown-fee-label">Est. Tax <i class="fas fa-info-circle breakdown-fee-info" title="Estimated at 8%"></i></span>
              <span>${{ cartTaxEstimate.toFixed(2) }}</span>
            </div>
            <div class="breakdown-total">
              <span>Total</span>
              <span>${{ cartTotalCharged.toFixed(2) }}</span>
            </div>
          </div>

          <!-- Guest note -->
          <p v-if="isGuest" class="guest-note">
            <i class="fas fa-user-slash"></i> Checking out as guest
          </p>

          <!-- Wallet Balance Section -->
          <div v-if="!isGuest && walletBalance !== null" class="wallet-section">
            <div class="wallet-header">
              <div>
                <p class="wallet-label">Wallet Balance</p>
                <p class="wallet-balance">${{ walletBalance.toFixed(2) }}</p>
                <p v-if="walletBalance < cartTotalCharged" class="wallet-need">
                  Need ${{ (cartTotalCharged - walletBalance).toFixed(2) }} more
                </p>
                <p v-else class="wallet-perfect">Perfect amount already in your wallet.</p>
              </div>
              <i class="fas fa-wallet wallet-icon"></i>
            </div>
            <template v-if="walletBalance >= cartTotalCharged">
              <label class="wallet-option-label">
                <input v-model="useWallet" type="checkbox" class="wallet-checkbox" />
                <div class="wallet-option-text">
                  <strong>Pay instantly from wallet</strong>
                  <small>No card entry needed • Instant checkout</small>
                </div>
              </label>
              <p class="wallet-hint"><i class="fas fa-bolt"></i> No redirect to payment page</p>
            </template>
            <template v-else>
              <p class="wallet-insufficient-note">Add funds for instant checkout, or pay with card below.</p>
              <button type="button" class="wallet-topup-btn" :disabled="walletTopupLoading" @click="topUpWallet">
                <i v-if="walletTopupLoading" class="fas fa-spinner fa-spin"></i>
                <i v-else class="fas fa-plus-circle"></i>
                {{ walletTopupLoading ? 'Redirecting...' : `Top up $${(cartTotalCharged - walletBalance).toFixed(2)} →` }}
              </button>
              <p v-if="walletTopupError" class="wallet-topup-error">{{ walletTopupError }}</p>
            </template>
          </div>

          <!-- Stripe Card Element -->
          <div v-if="!useWallet" class="stripe-section">
            <div id="stripe-card-element" class="stripe-element"></div>
          </div>

          <!-- Error Message -->
          <div v-if="paymentError" class="checkout-error">{{ paymentError }}</div>

          <!-- Submit Button -->
          <div class="checkout-submit-wrap">
            <button
              @click="confirmCheckout"
              :disabled="isProcessing || cartStore.items.length === 0"
              class="btn-checkout"
            >
              <span class="btn-checkout-inner">
                <i v-if="isProcessing" class="fas fa-spinner fa-spin"></i>
                <i v-else :class="useWallet ? 'fas fa-wallet' : 'fas fa-lock'"></i>
                <span v-if="isProcessing">Processing...</span>
                <span v-else>{{ useWallet ? 'Pay from Wallet' : 'Complete Checkout' }} — ${{ cartTotalCharged.toFixed(2) }}</span>
              </span>
            </button>
          </div>
        </div>
      </template>

      <!-- Non-boost types: fallback to Flask template -->
      <template v-else>
        <div class="checkout-fallback">
          <p>Redirecting to checkout...</p>
          <p class="fallback-note">{{ checkoutType }} checkout will open in a moment.</p>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiFetch, apiUrl } from '../composables/useApi'
import { useStripe } from '../composables/useStripe'
import { useCartStore } from '../stores/cart'
import { useAuth } from '../composables/useAuth'

const route = useRoute()
const router = useRouter()
const auth = useAuth()
const { initStripe, createPaymentIntent, confirmBoost } = useStripe()
const cartStore = useCartStore()

// Query params
const checkoutType = ref(route.query.type || 'boost')
const artistId = ref(route.query.artist_id || '')
const selectedArtistName = ref('')
const artists = ref([])
const boostAmount = ref(parseFloat(route.query.amount) || 5)
const itemId = ref(route.query.item_id || '')
const qty = ref(parseInt(route.query.qty) || 1)
const title = ref(route.query.title || '')
const isAhoySupport = computed(() => route.query.support_target === 'ahoy')
const shouldOfferAhoyMatch = computed(() => isAhoySupport.value)

// Display name: prefer query param 'artist_name', fall back to artistId slug, then fallback text
const artistDisplayName = computed(() => {
  if (route.query.artist_name) return route.query.artist_name
  if (artistId.value) {
    let name = artistId.value
    if (name.includes('%')) {
      try {
        name = decodeURIComponent(name)
      } catch (e) {
        console.warn('[checkout] Failed to decode artistId:', name)
      }
    }
    return name.replace(/-/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
  }
  return 'Unknown Artist'
})
const isPatronDonation = computed(() => checkoutType.value === 'boost' && !isAhoySupport.value)

// Cancel goes back to artist page if artist_id known, otherwise home
const cancelTarget = computed(() => {
  if (isAhoySupport.value) return '/support'
  if (artistId.value) return `/artists/${artistId.value}`
  return '/'
})

const recipientLabel = computed(() => {
  if (isAhoySupport.value) return 'Supporting'
  if (isPatronDonation.value) return 'Donating to Artist'
  return 'Boost for Artist'
})
const amountLabel = computed(() => {
  if (isAhoySupport.value) return 'Support Amount'
  if (isPatronDonation.value) return 'Donation Amount'
  return 'Select Amount'
})
const breakdownAmountLabel = computed(() => {
  if (isAhoySupport.value) return 'Support Amount'
  if (isPatronDonation.value) return 'Donation Amount'
  return 'Boost Amount'
})
const submitLabel = computed(() => {
  const base = useWallet.value ? 'Pay from Wallet' : 'Complete Checkout'
  if (isAhoySupport.value) return `Support Ahoy • ${base}`
  if (isPatronDonation.value) return `Donate • ${base}`
  return base
})

// Custom amount tracking
const isCustomAmount = ref(![0.05, 0.50, 1, 5].includes(parseFloat(route.query.amount) || 5))

function selectPresetAmount(amt) {
  boostAmount.value = amt
  isCustomAmount.value = false
}

function onCustomAmountInput(e) {
  const val = parseFloat(e.target.value)
  boostAmount.value = isNaN(val) ? 0 : val
  isCustomAmount.value = true
}

// Boost state
const stripeFee = computed(() => {
  const amount = boostAmount.value || 0
  return Math.round(((amount * 0.029) + 0.30) * 100) / 100
})

const taxEstimate = computed(() => {
  const amount = boostAmount.value || 0
  return Math.round((amount * 0.08) * 100) / 100
})

const ahoyServiceFee = computed(() => {
  const amount = boostAmount.value || 0
  return Math.round((amount * 0.05) * 100) / 100
})

const totalCharged = computed(() => {
  const amount = boostAmount.value || 0
  const match = shouldOfferAhoyMatch.value ? amount * ahoyMatch.value : 0
  return Math.round((amount + stripeFee.value + taxEstimate.value + ahoyServiceFee.value + match) * 100) / 100
})

// Cart computed fees (one Stripe fee for the whole cart)
const cartStripeFee = computed(() => {
  const total = cartStore.cartTotal || 0
  return Math.round(((total * 0.029) + 0.30) * 100) / 100
})
const cartTaxEstimate = computed(() => Math.round((cartStore.cartTotal * 0.08) * 100) / 100)
const cartAhoyServiceFee = computed(() => Math.round((cartStore.cartTotal * 0.05) * 100) / 100)
const cartTotalCharged = computed(() => {
  const total = cartStore.cartTotal || 0
  return Math.round((total + cartStripeFee.value + cartTaxEstimate.value + cartAhoyServiceFee.value) * 100) / 100
})

const ahoyMatch = ref(shouldOfferAhoyMatch.value ? 0.5 : 0)
const currentStep = ref('review')

// Payment state
const isProcessing = ref(false)
const error = ref('')
const paymentError = ref('')
const isGuest = ref(false)
const walletBalance = ref(null)
const useWallet = ref(false)
const walletTopupLoading = ref(false)
const walletTopupError = ref('')
const cardElement = ref(null)
let stripeInstance = null
const walletAmountStorageKey = 'ahoy:lastWalletFundAmount'
const lastWalletAmount = ref(null)

// Check auth state on mount
onMounted(async () => {
  const savedAmount = Number(window.localStorage.getItem(walletAmountStorageKey))
  if (Number.isFinite(savedAmount) && savedAmount >= 1 && savedAmount <= 1000) {
    lastWalletAmount.value = Math.round(savedAmount * 100) / 100
  }

  // Silently check if user is logged in
  try {
    await apiFetch('/api/auth/me')
    isGuest.value = false
  } catch (e) {
    if (e.status === 401) {
      isGuest.value = true
    }
  }

  // Fetch wallet balance only for logged-in users
  if (!isGuest.value) {
    try {
      const data = await apiFetch('/payments/wallet')
      walletBalance.value = data.balance || 0
    } catch (e) {
      console.warn('Failed to fetch wallet balance:', e)
      walletBalance.value = 0
    }
  }

  // Fetch artists for selection if missing
  if (checkoutType.value === 'boost' && !artistId.value) {
    try {
      const data = await apiFetch('/api/artists')
      artists.value = data.artists || []
    } catch (e) {
      console.warn('Failed to fetch artists:', e)
    }
  }

  // Handle non-boost/non-cart types: redirect to Flask template
  if (checkoutType.value !== 'boost' && checkoutType.value !== 'cart') {
    const query = route.fullPath.substring(route.fullPath.indexOf('?')) || ''
    setTimeout(() => {
      window.location.href = '/checkout' + query
    }, 500)
    return
  }

  if (shouldOfferAhoyMatch.value && ahoyMatch.value === 0) {
    ahoyMatch.value = 0.5
  }

  // Mount Stripe card element if user won't auto-switch to wallet
  if (!useWallet.value && (checkoutType.value === 'boost' || checkoutType.value === 'cart')) {
    await ensureCardElement()
  }
})

// Auto-check wallet pay when balance is sufficient
watch(walletBalance, (bal) => {
  if (bal !== null && bal >= totalCharged.value) {
    useWallet.value = true
  }
})

async function ensureCardElement() {
  if (checkoutType.value !== 'boost' && checkoutType.value !== 'cart') return
  await nextTick()
  const stripe = await initStripe()
  if (!stripe || cardElement.value) return
  stripeInstance = stripe
  const elements = stripe.elements()
  cardElement.value = elements.create('card', {
    style: {
      base: {
        color: '#ffffff',
        fontFamily: 'Inter, sans-serif',
        fontSize: '16px',
        '::placeholder': { color: 'rgba(255,255,255,0.4)' }
      }
    }
  })
  const el = document.getElementById('stripe-card-element')
  if (el) cardElement.value.mount('#stripe-card-element')
}

// Mount card element when user opts out of wallet (or on init for guests)
watch(useWallet, async (checked) => {
  if (!checked) await ensureCardElement()
})

async function confirmCheckout() {
  if (!auth.isLoggedIn.value) { router.push('/login'); return }
  const isCart = checkoutType.value === 'cart'

  if (isCart) {
    if (cartStore.items.length === 0) {
      paymentError.value = 'Your cart is empty'
      return
    }
  } else if (boostAmount.value < 0.25) {
    paymentError.value = 'Minimum boost amount is $0.05'
    return
  }

  isProcessing.value = true
  paymentError.value = ''

  try {
    currentStep.value = 'pay'

    if (useWallet.value) {
      await walletPayment()
    } else {
      await cardPayment()
    }

    // Clear cart on successful payment
    if (isCart) cartStore.clearCart()

    currentStep.value = 'complete'
    router.push({
      name: 'success',
      query: {
        status: 'paid',
        artist_id: isCart ? 'cart' : artistId.value,
        amount: isCart ? cartTotalCharged.value : boostAmount.value,
        pid: 'cart_payment'
      }
    })
  } catch (e) {
    console.error('[checkout] payment failed', {
      message: e?.message,
      status: e?.status,
      data: e?.data,
      stack: e?.stack,
      error: e,
    })
    paymentError.value = e.message || 'Payment failed. Please try again.'
    currentStep.value = 'review'
  } finally {
    isProcessing.value = false
  }
}

async function walletPayment() {
  // POST to /checkout/process with wallet payment
  const formData = new FormData()
  formData.append('type', 'boost')
  formData.append('artist_id', artistId.value || selectedArtistName.value)
  formData.append('amount', boostAmount.value.toString())
  formData.append('use_wallet', 'true')
  formData.append('ahoy_match', ahoyMatch.value.toString())

  // Try to get CSRF token
  try {
    const csrfRes = await apiFetch('/api/csrf-token')
    formData.append('csrf_token', csrfRes.token || '')
  } catch (e) {
    console.warn('Could not fetch CSRF token:', e)
  }

  const response = await fetch(apiUrl('/checkout/process'), {
    method: 'POST',
    body: formData,
    credentials: 'include'
  })

  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    throw new Error(data.error || 'Wallet payment failed')
  }

  const result = await response.json()
  if (result.success || result.status === 'ok') {
    // Success - confirm boost in our system
    if (result.payment_intent_id) {
      await confirmBoost(result.payment_intent_id)
    }
  } else {
    throw new Error(result.error || 'Payment processing failed')
  }
}

async function topUpWallet() {
  walletTopupLoading.value = true
  walletTopupError.value = ''
  const shortfall = Math.max(totalCharged.value - (walletBalance.value || 0), 1)
  const amount = Math.ceil(shortfall * 100) / 100
  const returnTo = route.fullPath
  try {
    const data = await apiFetch('/payments/wallet/fund', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ amount, return_to: returnTo }),
    })
    if (data.checkout_url) {
      window.localStorage.setItem(walletAmountStorageKey, String(amount))
      window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: `Opening wallet top-up for $${amount.toFixed(2)}`, type: 'success' } }))
      window.location.href = data.checkout_url
      return
    }
    walletTopupError.value = data.error || 'Could not start checkout'
  } catch (e) {
    walletTopupError.value = e.message || 'Failed to start top-up'
  } finally {
    walletTopupLoading.value = false
  }
}

function prefillTopUp(amount) {
  const normalized = Math.max(1, Math.ceil(Number(amount) * 100) / 100)
  lastWalletAmount.value = normalized
  window.localStorage.setItem(walletAmountStorageKey, String(normalized))
  window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: `Prepared wallet top-up for $${normalized.toFixed(2)}`, type: 'success' } }))
}

async function cardPayment() {
  const stripe = await initStripe()
  if (!stripe) throw new Error('Stripe not configured')

  const isCart = checkoutType.value === 'cart'

  // Create payment intent — cart sends items array, boost sends single artist
  let intentPayload
  if (isCart) {
    intentPayload = await apiFetch('/api/boost/stripe/create-intent', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        items: cartStore.items.map(i => ({ artist_id: i.artist_id, artist_name: i.artist_name, amount: i.amount })),
        source: 'web-cart-checkout'
      })
    })
  } else {
    intentPayload = await createPaymentIntent(
      artistId.value || selectedArtistName.value,
      boostAmount.value,
      ahoyMatch.value,
      { artistName: artistDisplayName.value, source: 'web-checkout' }
    )
  }

  const { client_secret } = intentPayload

  const { error: stripeError, paymentIntent } = await stripe.confirmCardPayment(client_secret, {
    payment_method: { card: cardElement.value }
  })

  if (stripeError) throw new Error(stripeError.message || 'Card payment failed')

  if (paymentIntent.status === 'succeeded') {
    await confirmBoost(paymentIntent.id)
  } else {
    throw new Error('Payment not completed')
  }
}
</script>

<style scoped>
.checkout-page {
  display: flex;
  justify-content: center;
  padding: 2rem 1.5rem;
  min-height: 100%;
}

.checkout-card {
  width: 100%;
  max-width: 560px;
  border-radius: 1.5rem;
  color: white;
  backdrop-filter: blur(24px) saturate(160%);
  -webkit-backdrop-filter: blur(24px) saturate(160%);
  background: linear-gradient(180deg, rgba(255,255,255,0.06) 0%, rgba(255,255,255,0.01) 100%), rgba(12,14,18,0.55);
  border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 20px 60px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.05);
  padding: 2rem;
  height: fit-content;
}

.checkout-steps {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 2rem;
  position: relative;
}

.checkout-steps .step {
  padding: 0.5rem 1.25rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 500;
  background: rgba(255,255,255,0.08);
  color: rgba(255,255,255,0.6);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  border: 1px solid rgba(255,255,255,0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 80px;
}

.checkout-steps .step.active {
  background: var(--primary-color, #ff0060);
  color: white;
  font-weight: 700;
  box-shadow: 0 0 20px rgba(255, 0, 96, 0.4);
  transform: scale(1.05);
  border-color: var(--primary-color, #ff0060);
}

.checkout-steps .step.done {
  background: rgba(34, 197, 94, 0.25);
  color: #86efac;
  border-color: rgba(34, 197, 94, 0.4);
  font-weight: 600;
}

.checkout-steps .step.done i {
  margin-right: 4px;
}

.step-divider {
  flex: 1;
  height: 2px;
  background: linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.2) 50%, rgba(255,255,255,0.1) 100%);
  max-width: 2rem;
  transition: background 0.3s;
}

.checkout-cancel-row {
  margin-bottom: 1rem;
}
.checkout-cancel-link {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  color: rgba(255,255,255,0.5);
  text-decoration: none;
  font-size: 0.85rem;
}
.checkout-cancel-link:hover { color: rgba(255,255,255,0.85); }
.checkout-title {
  font-size: 1.5rem;
  font-weight: 700;
  margin: 0 0 1.25rem;
}

.checkout-error {
  background: rgba(239,68,68,0.1);
  border: 1px solid rgba(239,68,68,0.3);
  color: #fca5a5;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.checkout-section {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 0.75rem;
  padding: 1rem;
  margin-bottom: 0.75rem;
}

.checkout-section-label {
  font-size: 0.8rem;
  color: rgba(255,255,255,0.5);
  margin: 0 0 0.25rem;
}

.checkout-section-value {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0;
}

.checkout-select {
  width: 100%;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 8px;
  color: #fff;
  padding: 8px 12px;
  font-size: 1rem;
  outline: none;
  cursor: pointer;
}

.checkout-select:focus {
  border-color: var(--primary-color, #ff0060);
}

.breakdown-title {
  font-size: 1.05rem;
  font-weight: 600;
  margin: 0 0 0.75rem;
}

.breakdown-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.25rem 0;
  font-size: 0.9rem;
  color: rgba(255,255,255,0.8);
}

.breakdown-total {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 0 0;
  margin-top: 0.5rem;
  border-top: 1px solid rgba(255,255,255,0.1);
  font-weight: 700;
  font-size: 1rem;
}
.breakdown-fee-label {
  display: inline-flex;
  align-items: center;
  gap: 0.3rem;
}
.breakdown-fee-info {
  font-size: 0.75rem;
  color: rgba(255,255,255,0.35);
  cursor: help;
}

.boost-amount-selector {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
  margin-bottom: 1rem;
}

.amount-btn {
  padding: 10px;
  border-radius: 10px;
  border: 1px solid rgba(255,255,255,0.15);
  background: rgba(255,255,255,0.05);
  color: #fff;
  font-size: 0.95rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.amount-btn:hover {
  background: rgba(255,255,255,0.1);
  border-color: rgba(255,255,255,0.25);
}

.amount-btn.active {
  background: rgba(255,0,110,0.2);
  border-color: rgba(255,0,110,0.5);
  color: #ff006e;
}

.custom-amount-input {
  display: flex;
  align-items: center;
  background: rgba(255,255,255,0.05);
  border: 1px solid rgba(255,255,255,0.15);
  border-radius: 10px;
  padding: 8px 12px;
  transition: border-color 0.15s;
}
.custom-amount-input:focus-within,
.custom-amount-input:has(.amount-input.active) {
  border-color: var(--primary-color, #ff0060);
}

.prefix {
  color: rgba(255,255,255,0.5);
  font-weight: 600;
  margin-right: 4px;
}

.amount-input {
  flex: 1;
  background: transparent;
  border: none;
  color: #fff;
  font-size: 1rem;
  outline: none;
}

.amount-input::placeholder {
  color: rgba(255,255,255,0.3);
}

.support-ahoy-section {
  background: linear-gradient(135deg, rgba(255,0,96,0.08) 0%, rgba(255,61,127,0.05) 100%);
  border: 1px solid rgba(255,0,96,0.2);
  border-radius: 1rem;
  padding: 1rem 1.25rem;
  margin-bottom: 1rem;
}

.support-ahoy-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.support-ahoy-header i {
  font-size: 1.25rem;
  color: #ff0060;
}

.support-ahoy-title {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: white;
}

.support-ahoy-sub {
  margin: 0;
  font-size: 0.8rem;
  color: rgba(255,255,255,0.5);
}

.support-ahoy-options {
  display: flex;
  gap: 0.5rem;
}

.support-btn {
  flex: 1;
  padding: 0.6rem 0.8rem;
  border-radius: 0.75rem;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.7);
  font-size: 0.85rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.support-btn:hover {
  background: rgba(255,255,255,0.12);
  color: rgba(255,255,255,0.9);
}

.support-btn.active {
  background: var(--primary-color, #ff0060);
  border-color: var(--primary-color, #ff0060);
  color: white;
  font-weight: 600;
}

.support-ahoy-amount {
  margin: 0.5rem 0 0;
  font-size: 0.85rem;
  color: #ff3d7f;
  font-weight: 600;
  text-align: right;
}

.guest-note {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.25);
  border-radius: 0.75rem;
  font-size: 0.9rem;
  color: rgba(199, 210, 254, 0.9);
  margin: 0.5rem 0;
}

.wallet-section {
  background: linear-gradient(135deg, rgba(147,51,234,0.12) 0%, rgba(59,130,246,0.1) 100%);
  border: 1px solid rgba(147,51,234,0.25);
  border-radius: 0.75rem;
  padding: 1rem;
  margin-bottom: 0.75rem;
}

.wallet-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.75rem;
}

.wallet-label {
  font-size: 0.8rem;
  color: rgba(255,255,255,0.6);
  margin: 0 0 0.2rem;
}

.wallet-balance {
  font-size: 1.25rem;
  font-weight: 600;
  color: #c4b5fd;
  margin: 0;
}

.wallet-need {
  font-size: 0.75rem;
  color: rgba(255,255,255,0.5);
  margin: 0.1rem 0 0;
}

.wallet-perfect {
  font-size: 0.75rem;
  color: #86efac;
  margin: 0.1rem 0 0;
}

.wallet-icon {
  color: #a78bfa;
  font-size: 1.5rem;
}

.wallet-option-label {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 0.5rem;
  transition: background 0.15s;
}

.wallet-option-label:hover {
  background: rgba(255,255,255,0.05);
}

.wallet-checkbox {
  width: 1.1rem;
  height: 1.1rem;
  accent-color: var(--primary-color, #ff0060);
  cursor: pointer;
  flex-shrink: 0;
}

.wallet-option-text strong {
  display: block;
  font-size: 0.9rem;
  color: rgba(255,255,255,0.9);
}

.wallet-option-text small {
  font-size: 0.75rem;
  color: rgba(255,255,255,0.5);
}

.wallet-hint {
  font-size: 0.75rem;
  color: #c4b5fd;
  margin: 0.5rem 0 0;
}

.wallet-insufficient-note {
  font-size: 0.85rem;
  color: rgba(255,255,255,0.65);
  margin: 0 0 0.75rem;
}

.wallet-topup-shortcuts {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.wallet-topup-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 0.8rem;
  border-radius: 999px;
  background: rgba(255,255,255,0.08);
  border: 1px solid rgba(255,255,255,0.14);
  color: #fff;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
}

.wallet-topup-chip:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.wallet-topup-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.6rem 1.1rem;
  background: var(--accent-primary, #6ddcff);
  color: #111;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  font-size: 0.9rem;
  cursor: pointer;
  margin-bottom: 0.5rem;
}
.wallet-topup-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.wallet-topup-error {
  font-size: 0.8rem;
  color: #fca5a5;
  margin: 0.25rem 0 0;
}

.stripe-section {
  margin-bottom: 0.75rem;
}

.stripe-element {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 0.5rem;
  padding: 12px;
}

.checkout-submit-wrap {
  margin-top: 1.5rem;
}

.btn-checkout {
  width: 100%;
  padding: 1rem;
  border-radius: 1rem;
  background: linear-gradient(135deg, var(--primary-color, #ff0060), #ff3d7f);
  border: none;
  color: white;
  font-size: 1.1rem;
  font-weight: 700;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
  box-shadow: 0 8px 28px rgba(var(--primary-rgb, 255, 0, 96), 0.4);
  letter-spacing: 0.01em;
}

.btn-checkout:hover:not(:disabled) {
  transform: translateY(-1px) scale(1.01);
  box-shadow: 0 12px 36px rgba(var(--primary-rgb, 255, 0, 96), 0.55);
}

.btn-checkout:active:not(:disabled) {
  transform: scale(0.99);
}

.btn-checkout:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-checkout-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
}

.checkout-fallback {
  text-align: center;
  padding: 2rem 1rem;
}

.fallback-note {
  font-size: 0.9rem;
  color: rgba(255,255,255,0.6);
}

/* ---- Cart styles ---- */
.cart-empty {
  text-align: center;
  padding: 2.5rem 1rem;
  color: rgba(255,255,255,0.5);
}
.cart-empty i {
  font-size: 2.5rem;
  margin-bottom: 0.75rem;
  display: block;
  opacity: 0.4;
}
.cart-empty p { margin: 0 0 1rem; }
.cart-browse-link {
  color: var(--primary-color, #ff0060);
  text-decoration: none;
  font-weight: 600;
  font-size: 0.9rem;
}

.cart-suggest-hint {
  font-size: 0.78rem;
  color: rgba(255,255,255,0.4);
  margin: 0.25rem 0 0.5rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}
.cart-suggest-hint i { color: rgba(255, 200, 60, 0.6); font-size: 0.72rem; }

.cart-item-list {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  margin-top: 0.5rem;
}
.cart-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(255,255,255,0.06);
}
.cart-item:last-child { border-bottom: none; }
.cart-item-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
  min-width: 0;
}
.cart-item-icon {
  color: rgba(255, 165, 0, 0.8);
  font-size: 0.8rem;
  flex-shrink: 0;
}
.cart-item-name {
  font-size: 0.9rem;
  font-weight: 600;
  color: rgba(255,255,255,0.9);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cart-item-controls {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  flex-shrink: 0;
}
.cart-qty-btn {
  width: 24px;
  height: 24px;
  border: 1px solid rgba(255,255,255,0.2);
  background: rgba(255,255,255,0.06);
  color: white;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.65rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.cart-qty-btn:hover { background: rgba(255,255,255,0.12); }
.cart-item-amount {
  font-size: 0.9rem;
  font-weight: 700;
  color: rgba(255,255,255,0.9);
  min-width: 3rem;
  text-align: center;
}
.cart-remove-btn {
  width: 24px;
  height: 24px;
  border: 1px solid rgba(239,68,68,0.3);
  background: rgba(239,68,68,0.08);
  color: #fca5a5;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.65rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.15s;
}
.cart-remove-btn:hover { background: rgba(239,68,68,0.2); }
</style>

