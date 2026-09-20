# Tab Feature Plan

**Version:** 2.0  
**Created:** 2026-05-28  
**Updated:** 2026-05-29  
**Status:** Planning — experimental nav slot, full build pending  
**Priority:** High  

---

## The Concept: "Opening a Tab"

Tab is built around one mental model: **opening a tab at a bar**.

You load money in once (or subscribe so it auto-refills). That balance — your tab — is what you spend everywhere on Ahoy: tipping artists, buying merch online, paying at a physical booth or show. No repeated card entry. No separate checkouts. Just "put it on my tab."

The subscription makes the tab self-refilling. Load it once manually, or subscribe and it tops itself up every month.

---

## How the Tab Works

### Opening a tab
- User loads a balance: $14, $24, $54, or any custom amount (minimum $14)
- One Stripe transaction upfront — card goes away
- Balance lives in their Ahoy wallet

### Spending on the tab
- **Artist tips** — tap a heart/tip button on any artist page, amount deducted instantly
- **Online merch** — add to cart, check out with tab balance instead of card
- **In-person merch** — at a show or farmers market, scan a QR code / tap NFC → charges tab, no card out
- **Future:** event tickets, exclusive tracks, physical Ahoy Console purchases

### Tab auto-refill (subscription)
- User subscribes to a monthly tier
- Stripe charges them on a recurring basis
- On each successful charge, their wallet resets to their chosen amount
- Unused balance expires at cycle end (no rollover — keeps it simple in v1)

### Covering a friend's tab (v1.2+)
- Send wallet credit to another Ahoy user by username
- At in-person checkout: "Charge to [friend]'s tab" — they get a push notification to approve
- Gift subscriptions: pay for someone's monthly tab as a gift

---

## Subscription Tiers

**Fee model:** $4 flat to Ahoy per billing cycle. Stripe fee on top. Minimum $14/mo.
The $7 tier is dropped — economics don't work at flat $4 fee (would be 57% overhead).

| User Pays | Ahoy Fee | Stripe Fee | Total Charge | Wallet to Spend |
|---|---|---|---|---|
| $14/mo | $4.00 | $0.71 | $14.71 | $10.00 |
| $24/mo | $4.00 | $1.00 | $25.00 | $20.00 |
| $54/mo | $4.00 | $1.87 | $55.87 | $50.00 |
| Custom (≥$14) | $4.00 | calculated | shown live | pay − $4 |

Fee formula: `wallet = payment − $4.00` → `total_charge = payment + (payment × 2.9% + $0.30)`

**Framing:** Lead with wallet amount ("$10 to spend"), show price secondary ("$14/mo"). Users understand subscription pricing — they don't need to see the fee breakdown unless they ask.

Users who want a one-time load (no subscription) can top up manually — full amount goes to wallet, no $4 cut on one-time loads.

---

## In-Person Tab ("Leave it on my tab")

This is the differentiating feature. At a show, farmers market, or any physical Ahoy presence:

1. Merchant (artist, venue) displays a QR code or NFC tag per item or per booth
2. User scans / taps with phone
3. App confirms item + price, shows current tab balance
4. One tap: "Add to my tab"
5. Balance deducts, artist gets credit in real time
6. Receipt push notification

**If user has no tab open:** flow prompts them to load one right there (one-time top-up, no subscription required)

**Physical Ahoy Console** (Pi kiosk) can act as the in-person terminal — it already serves the app at a venue, and can display QR codes per item.

### Backend for in-person
- Merchant generates item QR codes via Studio (artist dashboard)
- QR resolves to `/tab/charge?item=<id>&merchant=<slug>&amount=<x>`
- App intercepts via deep link (Capacitor URL scheme), shows confirm screen
- POST `/api/tab/tab-charge` → deducts from wallet, records as `tab_purchase` type

---

## Online Merch + Tab

Current merch flow: separate Stripe Checkout session, card required.

With Tab:
- Cart shows "Pay with Tab ($X remaining)" as primary option alongside card
- If tab balance ≥ cart total: instant deduction, no Stripe transaction needed at checkout
- If tab balance < cart total: show split — "$X from tab + $Y card" — single Stripe charge for the delta

This means **most returning users never see a card form for merch again**.

---

## How This Unifies with Boosts

Boosts (current feature) are one-time direct Stripe PaymentIntents per tip. They work, but each one requires card entry and Stripe fees eat into small amounts.

**Tab replaces this at the transaction layer:**

| | Boosts (current) | Tab Tab (new) |
|---|---|---|
| Payment | Card per tip | Pre-loaded wallet |
| Stripe fees | Per tip (expensive on small amounts) | One fee on load, then free deductions |
| Friction | High (card each time) | Near-zero (one tap) |
| Recurring | No | Optional subscription |
| In-person | No | Yes |
| Merch | No | Yes |
| Friends | No | Planned v1.2 |

Boosts stay in the codebase as the fallback for non-subscribed users and one-off situations, but Tab is the primary path. The nav slot "Boosts" → "Tab" when Tab launches.

---

## All Stripe Usage — Unified View

Here's every way Stripe is used or will be used, and how they relate:

### 1. Boost PaymentIntent (existing — `boost_stripe.py`)
- **What:** One-time charge per artist tip or cart of tips
- **Stripe primitive:** `PaymentIntent`
- **Fee model:** User pays boost + 7.5% platform + Stripe fee on top
- **Status:** Live. Will be deprecated for subscribed users; kept for guests/one-offs.

### 2. Wallet Top-Up via Checkout (existing — `payments.py`)
- **What:** User loads balance via Stripe Checkout session (hosted page)
- **Stripe primitive:** `Checkout Session` (one-time payment)
- **Fee model:** User pays load amount; no explicit platform fee on top-ups (platform earns on artist payouts)
- **Status:** Live. This becomes the "open a tab" manual flow for Tab.

### 3. Tab Subscription (new — `tab_stripe.py`)
- **What:** Monthly recurring charge that resets wallet balance
- **Stripe primitive:** `Subscription` + `Invoice`
- **Fee model:** Wallet amount + $3.00 Ahoy fee + Stripe fee on total
- **Webhooks needed:** `invoice.payment_succeeded` (reset wallet), `customer.subscription.deleted` (cancel)
- **Status:** To build.

### 4. In-Person Tab Charge (new)
- **What:** QR/NFC scan at venue deducts from wallet — no new Stripe charge
- **Stripe primitive:** None (pure wallet deduction, Stripe already captured on load)
- **Status:** To build. Depends on wallet + merchant QR generation in Studio.

### 5. Merch Checkout — Tab Split (new)
- **What:** Merch cart paid from wallet; overflow charged to card
- **Stripe primitive:** `PaymentIntent` for delta only (if any)
- **Status:** To build. Depends on wallet deduction logic already in `payments.py`.

### 6. Artist Payouts (existing — `send_artist_payout.py`, `batch_process_payouts.py`)
- **What:** Stripe transfers to artists from platform account
- **Stripe primitive:** `Transfer` to connected accounts
- **Status:** Live (scripts). Daily payout processor runs via cron.

### 7. Gift / Friend Tab (future — v1.2)
- **What:** Transfer wallet credit between users, or pay for a friend's tab
- **Stripe primitive:** Internal wallet transfer (no new Stripe charge — credit moves between user records)
- **Status:** Design only.

### Key insight: Stripe is only the money-in layer
Once money is in the wallet, all spending (tips, in-person, merch, friend tabs) is pure database math. Stripe only fires when a user loads or subscribes. This makes in-person and micro-tips economically viable — no per-transaction Stripe fees eating $0.50 tips.

---

## Navigation Changes

### Now (experimental slot)
- Remove "Boosts" from desktop sidebar and mobile dock
- Add "Tab" under `/games`-style hidden experimental route
- Mobile dock: replace Boosts slot with Saved

### At launch
- Tab takes the Boosts nav slot in sidebar + mobile dock
- SupportView either redirects to Tab or keeps a reduced "one-time boost" option for non-subscribers

---

## Data Model

### `Subscription` (new table)
```python
class Subscription(Base):
    id, user_id (unique FK), wallet_amount, status (active/paused/cancelled)
    stripe_subscription_id, stripe_customer_id
    current_balance, balance_as_of
    billing_cycle_start, next_billing_date
    created_at, updated_at, cancelled_at
```

### `Tip` model updates
- Add `subscription_id` FK (nullable) — links tip to which subscription month
- Add `source_type` field: `boost` | `tab` | `subscription` | `in_person`

### `WalletTransaction` (existing — extend)
- Add `source_type`: `top_up` | `subscription_reset` | `tip` | `merch` | `in_person` | `gift_sent` | `gift_received`
- Add `merchant_id` (nullable) — for in-person charges
- Add `item_ref` (nullable) — QR item identifier

### `MerchItem` / `TabItem` (new, lightweight)
- Merchant-defined items with price and QR code
- Linked to artist/studio account
- Used for in-person tab scanning

---

## Implementation Phases

### Phase 0 (now)
- Move Tab to experimental nav (hidden route, no sidebar/dock entry)
- Remove Boosts from sidebar + mobile dock
- Replace mobile dock Boosts slot with Saved

### Phase 1: Wallet as unified rail
- Ensure wallet top-up flow is clean and prominent
- Add `source_type` to WalletTransaction
- Wire merch checkout to offer tab payment option

### Phase 2: Subscription
- Add Subscription model + migration
- `POST /api/tab/create-subscription` + confirm + webhooks
- TabView.vue with tier picker + wallet status
- Subscription management (pause/resume/cancel)

### Phase 3: In-person tab
- Studio: artist can create items with QR codes
- Deep link handler in Capacitor: `ahoy://tab/charge?...`
- `POST /api/tab/tab-charge` endpoint
- Confirm screen in app

### Phase 4: Merch tab integration
- Cart detects wallet balance
- Shows "Pay with Tab" / split UI
- Delta-only Stripe charge if needed

### Phase 5: Friend tabs (v1.2)
- Wallet-to-wallet transfer
- In-person "charge to friend" with approval notification

---

## Open Questions

- Minimum custom wallet amount? (Suggested: $3 — covers Ahoy fee + $0 wallet makes no sense)
- Wallet rollover: yes or no for v1? (Currently: no — expires monthly)
- Do non-subscribers get a "one-time tab" option (load once, spend freely, no recurring)?
- In-person: who manages the QR items — artist only, or any venue?
- Merch split charge: require card on file, or prompt at checkout?

---

## Files to Create/Modify

### New
- `routes/tab_stripe.py` — subscription endpoints
- `spa/src/views/TabView.vue`
- `spa/src/components/TierPicker.vue`
- `spa/src/components/WalletStatus.vue`
- `spa/src/components/TabChargeConfirm.vue` — in-person confirm screen
- `alembic/versions/xxxx_add_subscription_model.py`

### Modify
- `models.py` — Subscription, Tip.source_type, WalletTransaction.source_type
- `utils/fees.py` — add `calculate_subscription_fees()`
- `blueprints/payments.py` — tab-split merch checkout
- `spa/src/components/AppSidebar.vue` — remove Boosts, add Tab (at launch)
- `spa/src/components/NavBar.vue` — remove Boosts from mobile dock, add Saved
- `spa/src/router.js` — add /tab route (experimental for now)
