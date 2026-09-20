# Resend Quick Setup - Your API Key

## ✅ Your Resend API Key

Your API key is stored securely in your deployment environment. Do not place it in this document or commit it to Git.

## 🚨 Important: Domain Verification Required

**Status:** API key works ✅, but domain `ahoy.ooo` needs verification ⚠️

### Quick Fix: Verify Domain in Resend

1. **Go to Resend Dashboard:** https://resend.com/domains
2. **Click "Add Domain"**
3. **Enter:** `ahoy.ooo`
4. **Add DNS Records** (Resend shows you exactly what to add):
   - SPF record (TXT record)
   - DKIM record (TXT record)
   - DMARC record (optional but recommended)
5. **Wait for verification** (5-15 minutes)
6. **Done!** Emails will work

### Alternative: Use Resend Default Domain (For Testing)

If you want to test immediately without domain verification:

1. **Set on Render:**
   ```
   RESEND_API_KEY=<your_resend_api_key>
   SUPPORT_EMAIL=onboarding@resend.dev
   ```
2. **This works immediately** but sender will be `onboarding@resend.dev`
3. **Later:** Verify your domain and switch to `support@ahoy.ooo`

## 🔧 Setup on Render

### Step 1: Add Environment Variables

Go to **Render Dashboard** → **ahoy-little-platform** → **Environment** and add:

```
RESEND_API_KEY=<your_resend_api_key>
SUPPORT_EMAIL=support@ahoy.ooo
```

(Or use `onboarding@resend.dev` temporarily if domain not verified)

### Step 2: Deploy/Restart

After adding environment variables, restart your service or wait for next deploy.

### Step 3: Test

```bash
# On Render Shell
python scripts/check_email_config.py
python scripts/test_send_email_to_alex.py
```

## 📧 What You'll Receive

Once configured, you'll get emails at `alex@ahoy.ooo` for:
- ✅ User registrations
- ✅ Wallet funding
- ✅ Artist boosts
- ✅ Merch purchases
- ✅ Daily payout summaries

## 🔍 Verify Domain Status

Check Resend Dashboard → Domains to see if `ahoy.ooo` is verified.

**If verified:** ✅ Green checkmark  
**If not verified:** ⚠️ Red X - Add DNS records

## 🆘 Troubleshooting

**Error: "Domain not verified"**
- Solution: Add domain in Resend and verify DNS records

**Error: "403 Forbidden"**
- Solution: Domain not verified - see above

**Emails not arriving:**
- Check spam folder
- Verify domain is verified in Resend
- Check Resend dashboard → Emails to see if they were sent

## 🔐 Security

**DO NOT:**
- ❌ Commit API key to git (it's already in this file, but don't commit sensitive files)
- ❌ Share API key publicly
- ❌ Put in code files

**DO:**
- ✅ Set as environment variable in Render
- ✅ Keep it secret
- ✅ Rotate if exposed
