# SMS Notifications Setup - Complete Summary

All SMS notification infrastructure is now in place. Here's what was added:

## Files Created

### Core SMS Service
- **`services/sms.py`** — Twilio SMS integration
  - `send_sms(phone, message)` — Send individual SMS
  - `notify_whats_new_sms(title, description, recipients, link)` — Batch send
  - `can_send_sms()` — Check if configured

### Scripts for Management
- **`scripts/quick_assign_phones.py`** — Quick phone number assignment
  ```bash
  python scripts/quick_assign_phones.py conmanrogster01 +15551234567
  python scripts/quick_assign_phones.py --list
  ```

- **`scripts/assign_phone_numbers.py`** — Interactive phone assignment (menu-driven)
  ```bash
  python scripts/assign_phone_numbers.py
  ```

- **`scripts/send_whats_new_sms.py`** — Send SMS notifications for new content
  ```bash
  python scripts/send_whats_new_sms.py --title "New Video" --description "Check it"
  ```

- **`scripts/setup_sms_prod.py`** — Complete production setup wizard
  ```bash
  python scripts/setup_sms_prod.py
  ```

### Documentation
- **`docs/SMS_TESTING_GUIDE.md`** — Quick start guide (READ THIS FIRST)
- **`docs/SMS_NOTIFICATIONS_SETUP.md`** — Technical setup reference

### Database
- **`models.py`** — Added `phone_number` field to User
- **Migration** — Applied to PostgreSQL (production ready)
- **Signup Form** — Updated Vue form to collect phone numbers (optional)

## Quick Start (5 minutes)

1. **Get Twilio credentials:**
   - Sign up at https://www.twilio.com
   - Get Account SID, Auth Token, Phone Number

2. **Set environment variables:**
   ```bash
   export TWILIO_ACCOUNT_SID="..."
   export TWILIO_AUTH_TOKEN="..."
   export TWILIO_PHONE_NUMBER="+1234567890"
   ```

3. **Assign phone numbers to your 15 friends:**
   ```bash
   python scripts/quick_assign_phones.py conmanrogster01 +15551234567
   python scripts/quick_assign_phones.py alex +15559876543
   # etc...
   ```

4. **Test SMS:**
   ```bash
   python scripts/send_whats_new_sms.py \
     --title "Test" \
     --description "Hello from Ahoy"
   ```

5. **Send to all users with what's new:**
   ```bash
   python scripts/send_whats_new_sms.py \
     --title "New Music" \
     --description "Check out latest tracks"
   ```

## What's Connected

### Frontend (Signup Form)
- Users can optionally provide phone number during signup
- Field: `LoginView.vue` (optional, labeled for SMS notifications)
- Stored in database: `users.phone_number`

### Backend API
- `/api/auth/register` now accepts `phone_number` parameter
- Uses `useAuth.js` composable to send phone data

### Database (PostgreSQL)
- `users.phone_number` — String(20), nullable
- Connected to production: `ahoy_postgres_user:...@dpg-d5l90...`
- 15 existing users ready for testing

### SMS Service
- Uses Twilio API (third-party provider)
- Automatic link to `https://ahoy.ooo/whats-new`
- Rate limiting + error handling included
- No external SMS database — phones stored locally only

## Your 15 Test Users

```
conmanrogster01, alex, clairec, deven, alexMaster,
daddy, agbabbby, gdub_dg, agonzalez729, ahoymrag12126,
elluuhnn, mrgstem, alex63, ahoy_mr_ag25, [unnamed guest]
```

List anytime: `python scripts/quick_assign_phones.py --list`

## Next Steps

1. Read: `docs/SMS_TESTING_GUIDE.md` (has all examples)
2. Get Twilio account + credentials
3. Assign phone numbers to friends
4. Test with one SMS first
5. Integrate with your content workflow

## Files to Review

- **For usage**: `docs/SMS_TESTING_GUIDE.md`
- **For technical details**: `docs/SMS_NOTIFICATIONS_SETUP.md`
- **For code**: `services/sms.py` and scripts

## Environment Variables Needed

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxx
TWILIO_PHONE_NUMBER=+1234567890
DATABASE_URL=postgresql://...  # Already set in production
```

## Testing Checklist

- [ ] Get Twilio account
- [ ] Set environment variables
- [ ] Run `python scripts/quick_assign_phones.py --list` (verify users)
- [ ] Assign 3-5 phone numbers
- [ ] Send one test SMS with `--test-phone`
- [ ] Verify SMS arrives
- [ ] Send to all users with SMS
- [ ] Check delivery in Twilio dashboard

That's it! SMS is fully set up and ready to test.
