# Stripe + Mercury Consolidation Plan
**Date:** 2026-03-31
**Status:** Planning Phase
**Objective:** Consolidate to Little Market brand with clean financials and tax compliance

---

## 🎯 PHASE 1: CURRENT STATE INVENTORY

### What You Need to Know Right Now

You currently have **multiple financial accounts scattered across Stripe and Mercury**. Before making any moves, you need to inventory exactly what you own and what's charging you.

**Your immediate to-do list (before reading options):**

1. **Log into Stripe Dashboard** → https://dashboard.stripe.com
   - Count how many Stripe accounts you own
   - For each, note: account name, bank connection, monthly activity
   - Look for the $3/week charge in account statements

2. **Log into Mercury** → Two accounts?
   - alex@ahoy.ooo (old)
   - alex@littlemarket.org (new)
   - Check transaction history on each
   - Identify: where is Stripe sending payouts? Which account has the $3/week charge?

3. **Run Stripe CLI to list accounts** (optional, but helpful):
   ```bash
   brew install stripe/stripe-cli/stripe
   stripe login
   stripe accounts list
   ```

4. **Find the $3/week charge mystery** — check:
   - Stripe subscription (look in Stripe Billing → Subscriptions)
   - Third-party service charging Stripe (e.g., payment gateway fee, subscription service)
   - Monthly fee from Stripe Connect setup (if you have that enabled)
   - Stray test charge or webhook retry loop

---

## 📋 CURRENT CODE STATE (What I Found)

### How Stripe is Integrated

Your app uses **environment variables to switch between TEST and LIVE keys**:

| Layer | Location | Details |
|-------|----------|---------|
| **Config** | `config.py` | Reads `STRIPE_SECRET_KEY_TEST` or `STRIPE_SECRET_KEY` based on `AHOY_ENV` |
| **Dev** | `.env` | Contains only TEST keys |
| **Production** | Render.com dashboard | Contains LIVE keys (set manually via UI) |
| **Webhook Handler** | `routes/stripe_webhooks.py` | Processes checkout & boost payments |
| **Charges** | Merch purchases, Boosts/Tips, Artist payouts |

### What's Currently Running

**Active integrations:**
- ✅ Merch store (Purchase model)
- ✅ Boost/Tip system (Tip model)
- ✅ Artist payouts (daily/monthly payout processor)
- ✅ Stripe webhooks (checkout.session.completed)

**NOT in code yet:**
- Stripe Connect accounts (for artist direct deposits)
- Multiple Stripe account switching
- Account-specific routing

**Key insight:** Your code doesn't care which Stripe account is active — it just uses whatever keys are in the environment. So switching Stripe accounts is an **environment variable swap**, not a code change.

---

## 💰 THE MYSTERY $3/WEEK CHARGE

**This is critical to solve first.** Here's how to track it down:

### Where to Look

1. **Stripe Dashboard → Billing**
   - Go to: https://dashboard.stripe.com/billing
   - Check "Subscriptions" — is anything recurring charged to you?
   - Check "Invoices" — what's the pattern? (Same amount, same day?)

2. **Mercury Transaction History** (alex@ahoy.ooo)
   - Filter by "Stripe"
   - Look for recurring $3 charges
   - Check the description — what is it from?

3. **Stripe Account Details**
   - Settings → Account → Statements
   - Look for "Stripe Connect", "API fee", "subscription"

### Common Causes

| Cause | What to Do |
|-------|-----------|
| **Stripe subscription** (e.g., you signed up for Stripe Sigma or Atlas) | Cancel in Stripe Dashboard → Billing |
| **Payment gateway test charge stuck in loop** | Delete webhook endpoint or contact Stripe support |
| **Monthly Stripe Connect fee** | Normal cost of using Connect (only if you have Connect) — would show in Stripe statements |
| **Third-party service billing to Stripe** | Find the service in Stripe Dashboard → Connected Apps → revoke access |
| **Stray test charge that's recurring** | Refund via Stripe Dashboard → Payments, then investigate root cause |

---

## 🏦 YOUR OPTIONS

### Decision Framework

You're deciding between **3 consolidation paths**, each with different complexity and risk.

**Key variables that matter:**
- How much active revenue/transactions? (Low = safer to migrate)
- How many Stripe accounts do you actually have? (Fewer = simpler)
- Do you need artist direct-deposit payouts? (No = simpler consolidation)
- Tax year impact? (Mid-year = need to reconcile two accounts for taxes)

---

## **OPTION 1: The Conservative Path — Pause & Clean First**

**TL;DR:** Stop the bleeding, understand what you have, then consolidate later.

### What You Do

1. **Disable the $3/week charge immediately**
   - Cancel any Stripe subscriptions you own (Sigma, Atlas, etc.)
   - Disable old Stripe account from accepting new charges
   - Document what it was paying for (for taxes/records)

2. **Keep both accounts running** for now
   - Don't consolidate yet
   - Let old Stripe-old drain to $0
   - New Stripe-new processes all future charges

3. **At month-end, reconcile manually:**
   - Export old Stripe account statements
   - Export new Stripe account statements
   - Save copies for tax prep
   - Optionally: request old Stripe account history export

4. **Consolidate next quarter** (after tax clarity)
   - Once you understand the full year's picture
   - Merge Mercury accounts when convenient
   - No rush = lower risk

### Why Choose This

✅ **Lowest risk** — no breaking changes mid-stream
✅ **Tax-safe** — separates old year from new
✅ **Time to plan** — you can think this through properly
✅ **Reversible** — nothing is deleted or permanently changed

### Why Not Choose This

❌ **Not a real solution** — still have duplicate accounts later
❌ **Bookkeeping pain** — two accounts to reconcile every month
❌ **Slow** — delays the actual consolidation

### Tax Implications

- **2 separate 1099 forms** (if you get paid via Stripe)
- **2 separate schedules** in your tax return (old vs new brand)
- **Reconciliation challenge** — harder to track annual revenue across accounts

### Effort

- **Immediate:** 30 min (disable $3 charge)
- **Ongoing:** 15 min/month (reconcile statements)
- **Consolidation:** Deferred to Q3

---

## **OPTION 2: The Fast Path — Immediate Consolidation**

**TL;DR:** Go all-in on Little Market. Swap keys, test, and go.

### What You Do

1. **Solve the $3/week mystery** (MUST DO FIRST)
   - Find what it's for
   - Cancel it if stray, document if legitimate
   - Stop the bleeding immediately

2. **Export old Stripe account history** (for tax/audit)
   ```bash
   # Use Stripe CLI to pull reports
   stripe reports
   ```
   - Save all transaction CSVs
   - Back up invoice PDFs
   - Timestamp the export

3. **Update production Stripe keys** (one-time change)
   - Go to Render.com dashboard
   - Update STRIPE_SECRET_KEY → new Little Market key
   - Update STRIPE_PUBLISHABLE_KEY → new Little Market key
   - Save & deploy (auto-redeploy triggered)

4. **Monitor for 48 hours post-deploy**
   - Watch Render logs for errors
   - Test a small transaction ($1 boost)
   - Verify webhook delivery in Stripe Dashboard

5. **Close old Stripe account** (wait 1 month)
   - Let old account sit idle for 30 days
   - Then request account closure via Stripe support
   - Keep historical data for 7 years for tax purposes

6. **Consolidate Mercury accounts**
   - Transfer remaining balance from alex@ahoy.ooo → alex@littlemarket.org
   - Close old Mercury account
   - Update all vendor/payment profiles to new email

### Why Choose This

✅ **Clean cutover** — one day of work, then done
✅ **Future-proof** — single account going forward
✅ **Simple bookkeeping** — one Stripe, one Mercury, one brand
✅ **Professional** — aligns with Little Market rebrand

### Why Not Choose This

❌ **Higher risk** — any issues during swap affect live customers
❌ **Needs a quiet window** — must deploy during low-traffic time
❌ **Webhook risk** — if endpoints configured wrong, transactions fail
❌ **Timing matters** — need to coordinate with any active campaigns

### Tax Implications

- **Single 1099** (from new account only)
- **Account transition year** — may need to file amended 1040-ES or document mid-year account change
- **Cleaner for 2026 taxes** — all activity on one account

### Effort

- **Prep:** 1 hour (export old data, verify keys)
- **Execution:** 15 min (update Render env vars + deploy)
- **Monitoring:** 1 hour over 48 hours post-deploy
- **Cleanup:** 30 min (Mercury transfer + account closure)
- **Total:** ~2.5-3 hours

### Risk Factors

| Risk | Severity | Mitigation |
|------|----------|-----------|
| **Webhook signature fails** | High | Test in staging first; verify secret matches |
| **New keys invalid** | High | Copy-paste carefully; test in dev environment |
| **Transaction in flight** | Medium | Deploy during known slow hours (weekend night) |
| **Customer not notified** | Low | No customer-facing change; still same URL |
| **Old account still has active subscribers** | Medium | Verify no recurring charges before swap |

---

## **OPTION 3: The Hybrid Path — Staged Cutover**

**TL;DR:** Move new revenue to Little Market now, archive old account later.

### What You Do

1. **Immediately:** Solve the $3/week charge (same as Option 2)

2. **Create a new Stripe account** specifically for "Little Market"
   - Sign up fresh if you don't have one
   - Verify bank account (takes 1-2 business days)
   - Get new API keys

3. **Run BOTH Stripe accounts in parallel** (advanced)
   - **New transactions** → Route to Little Market Stripe
   - **Old transactions** → Keep processing on Ahoy Stripe
   - **Code change:** Add logic to switch accounts based on transaction date or product type

4. **Over 2 months, migrate gradually:**
   - Week 1: New boosts go to Little Market
   - Week 2: Merch purchases go to Little Market
   - Week 3: Artist payouts configured for Little Market
   - Week 4+: Monitor old account for edge cases

5. **After 30 days of zero activity on old account:**
   - Close old account
   - Merge Mercury accounts

### Why Choose This

✅ **Zero customer impact** — transactions never pause
✅ **Gradualist approach** — catch issues early on new account
✅ **Parallel audit** — compare old vs new account behavior
✅ **Safe testing** — can see if webhooks/payouts work on new account first

### Why Not Choose This

❌ **Most complex** — requires code changes and logic branching
❌ **Longest timeline** — takes 2+ months start to finish
❌ **Bookkeeping headache** — tracking transactions across accounts during migration
❌ **Ongoing maintenance** — dual-account logic until fully migrated

### Tax Implications

- **Partial-year split** — revenue on two 1099s (old account Jan-May, new account Jun-Dec)
- **More reconciliation** — need to split revenue by account in tax return
- **Cleaner next year** — 2027 is fully on Little Market

### Effort

- **Setup:** 1.5 hours (new Stripe account, code changes)
- **Monitoring:** 15 min/day for 2 weeks during migration
- **Testing:** 2-3 hours (verify parallel charges don't double-bill)
- **Cleanup:** 1 hour (close old account after parallel run ends)
- **Total:** ~10-15 hours over 2 months

---

## 🎯 DECISION MATRIX

| Factor | Option 1: Conservative | Option 2: Fast | Option 3: Hybrid |
|--------|------------------------|----------------|------------------|
| **Risk Level** | 🟢 Low | 🟡 Medium | 🟡 Medium |
| **Speed** | 🔴 Slow | 🟢 Fast | 🟡 Slow |
| **Code Changes** | None | None | Major |
| **Bookkeeping** | 🔴 Complex | 🟢 Simple | 🟡 Complex |
| **Customer Impact** | None | Minimal (if done right) | None |
| **Tax Complexity** | High | Medium | High |
| **"When are you done?"** | Q3 2026 | 1 week | Mid-May 2026 |
| **Best If...** | Low revenue, unsure | Active revenue, confident | Want zero customer risk |

---

## 🚨 CRITICAL PRE-REQUISITES (All Options)

**Before you choose, you MUST:**

1. ✅ **Identify the $3/week charge**
   - What is it?
   - Is it still happening?
   - Can you stop it?

2. ✅ **Verify your Stripe account count**
   - Log into Stripe Dashboard
   - How many accounts do you see?
   - Do any show "Ahoy" in the name?

3. ✅ **Confirm Mercury accounts**
   - Can you log into both alex@ahoy.ooo and alex@littlemarket.org?
   - Which has active payouts from Stripe?
   - Which has the $3/week charge?

4. ✅ **Check current revenue**
   - Is anyone actively buying merch or tipping artists RIGHT NOW?
   - Or is it mostly quiet?
   - This determines if you can afford a maintenance window

**Once you have these 4 answers, you'll know which option is right.**

---

## 💼 TAX & ACCOUNTING NOTES

### General Rules (Consult Your Accountant!)

1. **Stripe 1099-K Reporting:**
   - Stripe issues separate 1099-K for each account
   - You'll need to report both on your tax return
   - IRS wants all payment processor accounts listed

2. **Mid-Year Account Change:**
   - If you switch accounts mid-year, document the transition date
   - Your accountant may need to file amended ES (estimated tax) form
   - Keep all Stripe statements from both accounts for audit trail

3. **Bank Account vs Merchant Account:**
   - Your Stripe account connects to a Mercury bank account
   - Mercury is just the bank; Stripe is the processor
   - You can have multiple Stripe accounts → same Mercury account (not ideal)
   - Or multiple Stripe accounts → multiple Mercury accounts (what you have now)

4. **Recommended Recordkeeping:**
   - Export all old Stripe account statements NOW (before closing)
   - Save all invoices/receipts (7-year IRS requirement)
   - Keep copies of account closure confirmations
   - Document the transition date and why

5. **Schedule C (Self-Employment)**
   - Report all business income, regardless of account
   - Stripe 1099-K is informational (IRS also gets a copy)
   - You're responsible for accurate totals across accounts

---

## ✅ YOUR NEXT STEP

**Pick your option, then tell me:**

1. Which option appeals to you? (1, 2, or 3)
2. What's blocking you from choosing?
3. Once I know, I'll help you execute with a detailed playbook.

---

## 📞 REFERENCE: Key Contacts & Links

### Your Accounts

- **Stripe Dashboard:** https://dashboard.stripe.com
- **Mercury (alex@ahoy.ooo):** https://mercury.com
- **Mercury (alex@littlemarket.org):** https://mercury.com
- **Render Deployment:** https://dashboard.render.com → ahoy-little-platform

### Documentation

- **App Stripe Integration:** `docs/setup/STRIPE_INTEGRATION_SUMMARY.md`
- **Payouts System:** `docs/features/ARTIST_PAYOUTS_GUIDE.md`
- **Webhook Handler:** `routes/stripe_webhooks.py`

---

**Last updated:** 2026-03-31
**Next review:** After you've inventoried accounts and chosen your option
