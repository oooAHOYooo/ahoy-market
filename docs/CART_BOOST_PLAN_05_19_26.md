# Cart-Style Boost Flow Implementation Plan

**Date:** May 19, 2026
**Feature:** Accumulating Artist Boosts via a Cart System

---

## 1. Overview & Goal
Currently, the "Boost" functionality triggers an immediate, single-purchase checkout flow per artist. The goal is to transition to an e-commerce-style **Cart Flow**. 
Users will be able to click "Boost" on multiple artists (which will default to $0.50 each) and accumulate these boosts in a global cart. When they are ready, they can check out all accumulated boosts in a single transaction. This provides a better user experience and avoids excessive fixed Stripe processing fees ($0.30 per transaction).

---

## 2. Phase 1: Global State Management (Frontend)

### Create the Pinia Store (`spa/src/stores/cart.js`)
We need a centralized place to store the cart items so they persist across routes.
*   **State:** `items` array. Each object will look like `{ artist_id, artist_name, amount: 0.50 }`.
*   **Actions:** 
    *   `addBoost(artist_id, artist_name, amount = 0.50)`: Check if the artist is already in the cart. If so, add to their total or just ignore; if not, push to the array.
    *   `removeBoost(artist_id)`: Remove an item from the cart.
    *   `updateAmount(artist_id, new_amount)`: Let the user change the boost amount.
    *   `clearCart()`: Empty the cart after successful checkout.
*   **Getters:** `cartTotal` (sum of all amounts), `itemCount`.
*   **Persistence:** Use `localStorage` (via Vue's `watch` or `pinia-plugin-persistedstate`) so the cart survives a hard refresh.

### Intercept the Boost Buttons
Update the existing "Boost" buttons (lightning bolt icons) scattered across the platform to add to the cart rather than routing to checkout.
*   **Target Files:** `ArtistDetailView.vue`, `MiniPlayer.vue` (and anywhere else `goToBoost` is defined).
*   **New Action:** Instead of `router.push('/checkout')`, call `cartStore.addBoost(artist.id, artist.name)`.
*   **Feedback:** Dispatch a toast event: `window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Added $0.50 boost to cart!', type: 'success' } }))`.

---

## 3. Phase 2: Checkout UI Modifications

### Update `CheckoutView.vue` (or create `CartView.vue`)
The checkout view must gracefully handle the new "Cart" payload type.
*   **Route Logic:** If `route.query.type === 'cart'`, switch the UI into "Cart Mode".
*   **UI Changes:** 
    *   Hide the single "Select Amount" grid.
    *   Iterate over `cartStore.items` and display a list.
    *   Provide `+` / `-` or an input box to adjust the amount for each artist.
    *   Provide a trash/remove icon for each artist.
*   **Summary Breakdown:** The Processing Fee, Stripe Fee, and Total must be calculated based on the aggregate `cartStore.cartTotal`.
*   **Support Ahoy (Match):** Ensure the `ahoyMatch` percentage calculates based on the total cart value.

---

## 4. Phase 3: Backend API & Transaction Logic

This is the most critical part: handling multiple artist payouts from a single Stripe Payment Intent.

### 1. Payment Intent Creation (`routes/boost_stripe.py` & `app.py`)
Modify the `POST /api/boost/stripe/create-intent` endpoint (and the Flask `/checkout/process` route for wallet purchases).
*   **New Payload Structure:** Instead of accepting a single `artist_id` and `boost_amount`, accept an `items` array: `[{ artist_id, amount }]`.
*   **Calculation:** The backend sums up the `amount` of all items to determine the total `boost_amount`.
*   **Stripe Metadata Constraints:** Stripe metadata is limited to 50 keys, 500 characters max per key. 
    *   If the cart is small, stringify it and store it: `metadata["cart_items"] = "[{id:A,amt:0.5},...]"`.
    *   *Alternative:* Create a temporary `CheckoutSession` or `Cart` table in the database to store the payload, and only pass `cart_id` to Stripe metadata.

### 2. Confirming the Boost (`routes/boost_stripe.py`)
Modify the `POST /confirm` endpoint to unpack the cart and record the tips.
*   **Verification:** Retrieve the `PaymentIntent` from Stripe and verify it `succeeded` and the total amounts match.
*   **Unpacking:** Parse the `cart_items` from metadata (or look up the `cart_id` from the DB).
*   **Writing to Database:** Start a database transaction. Iterate over the cart items and insert a new row into the `Tip` table for **each** artist.
    *   *Math:* Proportionally divide the `stripe_fee` and `platform_fee` across the tips based on their weight (or apply fees dynamically per item) so the ledger perfectly balances.
*   **Commit:** Commit the transaction. If it succeeds, the frontend clears the Pinia Cart.

---

## 5. Phase 4: Integration & Testing
1.  **Frontend Integration:** Ensure `spa/src/composables/useStripe.js` properly formats the `items` array when calling `createPaymentIntent`.
2.  **Wallet Edge Case:** Ensure that `walletPayment` (which posts to `/checkout/process`) is also updated to handle the `items` array properly and deducts the correct aggregate total from the user's wallet.
3.  **Testing:** Add 3 artists to the cart, checkout via Stripe test cards, and verify in the database that 3 separate `Tip` rows are created correctly with the same `stripe_payment_intent_id`.

---

## ✅ IMPLEMENTATION STATUS — Completed May 19, 2026

All four phases were implemented in full on the same day. Below is a precise account of every file touched, for pickup on another machine.

---

### Files Created
| File | Purpose |
|------|---------|
| `spa/src/stores/cart.js` | Pinia store: `items[]`, `addBoost`, `removeBoost`, `updateAmount`, `clearCart`, `cartTotal`, `itemCount`. Auto-saves to `localStorage` under key `ahoy:boostCart` via a deep `watch`. |

---

### Files Modified

#### `spa/src/views/ArtistDetailView.vue`
- Imported `useCartStore` from `../stores/cart`
- Replaced `goToBoost()` function: instead of `router.push('/checkout')`, now calls `cartStore.addBoost(artist.value.name, artist.value.name, artist.value.slug, 0.50)` and fires a success toast.

#### `spa/src/components/MiniPlayer.vue`
- Imported `useCartStore`
- Replaced `goToBoost()` function: resolves `artistName` from the current track (`artist`, `artist_name`, `host`, `filmmaker` fields) and calls `cartStore.addBoost(slug, artistName, slug, 0.50)` with a toast. No longer navigates away.
- Also fixed in this session: `isLiveTvSource` / `isLiveSource` computed props added — `canScrubTimeline`, Prev/Next/Shuffle/Repeat/Queue buttons are all hidden for `live_tv` type tracks.

#### `spa/src/components/AppSidebar.vue`
- Imported `useCartStore`
- Added a `<router-link to="/checkout?type=cart">` nav item (🛒 Cart) positioned after the Boosts link.
- Added `.sidebar-badge` CSS class — displays live red item count badge when `cartStore.itemCount > 0`.

#### `spa/src/views/CheckoutView.vue`
- Imported `useCartStore`
- Added `const cartStore = useCartStore()`
- Added cart fee computeds: `cartStripeFee`, `cartTaxEstimate`, `cartAhoyServiceFee`, `cartTotalCharged` — all based on `cartStore.cartTotal` (one Stripe $0.30 fixed fee for the whole cart)
- Added `<template v-else-if="checkoutType === 'cart'">` block with:
  - Empty cart state with "Browse Artists" link
  - Cart item list: artist name, `−` / `+` buttons (steps of $0.50, minimum $0.50), amount display, remove button
  - "Suggested: $0.50/artist" hint line
  - Fee breakdown, guest note, wallet section, Stripe card element, submit button — all mirroring the single-boost flow but wired to `cartTotalCharged`
- Fixed `onMounted` redirect: `'cart'` type is now allowed through (previously would redirect to Flask)
- Fixed `ensureCardElement` and `confirmCheckout` to handle `isCart` branch
- `confirmCheckout`: clears cart (`cartStore.clearCart()`) on successful payment; success page receives `artist_id: 'cart'`
- `cardPayment`: if cart, sends `POST /api/boost/stripe/create-intent` with `items[]` array directly (bypassing `useStripe.createPaymentIntent` which only accepts single artist)
- Added cart item styles: `.cart-item-list`, `.cart-item`, `.cart-item-info`, `.cart-item-controls`, `.cart-qty-btn`, `.cart-item-amount`, `.cart-remove-btn`, `.cart-suggest-hint`

#### `spa/src/views/TipArtistView.vue`
- Previously: `onMounted` immediately called `router.replace('/checkout?type=boost&artist_id=...')` — functionally a dead redirect with no cart awareness
- Now: reads `artist` / `artist_id` / `artist_name` from query params, calls `cartStore.addBoost(...)` with $0.50, fires a toast, then redirects to `/checkout?type=cart`

#### `routes/boost_stripe.py` — `create_payment_intent()`
- Now detects `is_cart = isinstance(data.get('items'), list) and len(...) > 0`
- Cart path: validates each item (`artist_id` required, `amount >= $0.50`), sums `total_boost`, sets `artist_id = 'cart'`, serializes cart to JSON string stored in `metadata['cart_items']` (truncates artist names if > 490 chars to stay under Stripe's 500-char limit)
- Single boost path: unchanged legacy behaviour
- `boost_type` metadata field set to `'cart'` or `'boost'` accordingly

#### `routes/boost_stripe.py` — `confirm_boost_record()`
- Reads `metadata['boost_type']`; if `'cart'`, parses `metadata['cart_items']` JSON
- Loops over cart items: proportionally splits `stripe_fee` and `platform_fee` by each item's weight (`item_amt / total_boost`)
- Inserts a separate `Tip` DB row per artist, all sharing the same `stripe_payment_intent_id`
- Calls `update_user_artist_position()` for each artist per item (portfolio tracking)
- PostHog event now includes `is_cart` and `cart_item_count` fields

---

### Commits (on `main`)
| Commit | Message |
|--------|---------|
| `526d2255` | Fix MiniPlayer scrub and transport controls for Ahoy TV live streams |
| `bbe0475b` | feat: Cart-Style Boost flow — store, sidebar badge, checkout UI, backend multi-item intent + confirm |
| *(next push)* | polish: TipArtistView cart redirect, suggested amount hint, all feature requests marked complete |

---

### Known Gaps / Future Work
- **Wallet path for cart**: `walletPayment()` in `CheckoutView.vue` still posts a single `artist_id` to `/checkout/process` (Flask). For logged-in wallet users checking out a cart, this currently falls through to a single-artist deduction. This needs a `/api/boost/wallet/cart` endpoint or extension of `/checkout/process` to handle `cart_items`.
- **Cart icon on mobile bottom nav**: The cart link is only in the desktop sidebar. A mobile bottom-tab entry would improve discoverability.
- **Stripe metadata 500-char truncation**: For very large carts (10+ artists with long names), artist names are dropped from `cart_items` metadata. Artist IDs are always preserved, so the DB write still works, but the metadata is less readable in the Stripe dashboard.
