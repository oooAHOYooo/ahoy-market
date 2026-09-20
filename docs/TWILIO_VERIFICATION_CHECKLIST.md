# Twilio Trial Account - Verification Checklist

On Twilio's **trial account**, you can only SMS **verified phone numbers**.

## Your Twilio Setup

```
Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Phone Number: +1XXXXXXXXXX
Trial Balance: $15.50
```

## Verification Steps

### Step 1: Set Environment Variables

Get your Auth Token first:
1. Go to: https://www.twilio.com/console
2. Click your name (top right) → **Account**
3. Under **API Credentials**, find **Auth Token**
4. Click eye icon to reveal
5. Copy and paste here:

```bash
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="paste_your_auth_token_here"
export TWILIO_PHONE_NUMBER="+1XXXXXXXXXX"
```

### Step 2: Verify Your Own Phone First

1. Go to: https://www.twilio.com/console/phone-numbers/verified
2. Click **Add a Caller ID**
3. Enter YOUR phone number
4. Choose: **Get a voice call** or **Text me**
5. Confirm the code they send you
6. Your number is now verified ✓

### Step 3: Verify Your Friends (They Do This)

For each friend you want to SMS:

1. In Twilio console, go to **Verified Caller IDs** again
2. Click **Add a Caller ID**
3. Enter their phone number (e.g., +15551234567)
4. Twilio will call/text THEM with a code
5. They read/reply with the code
6. Their number is now verified ✓

**Note:** Friend only needs to do this once. After they verify, you can SMS them as much as you want.

### Step 4: Assign Numbers in Your Database

Once verified, add them:

```bash
python scripts/quick_assign_phones.py conmanrogster01 +15551234567
python scripts/quick_assign_phones.py alex +15559876543
# etc...
```

### Step 5: Test with Your Own Number

```bash
python scripts/send_whats_new_sms.py \
  --title "Test SMS" \
  --description "Hello from Ahoy!"
```

## Verification Checklist

Use this to track who's verified:

```
☐ Your phone number verified
☐ conmanrogster01 verified (+15551234567)
☐ alex verified (+15559876543)
☐ clairec verified
☐ deven verified
☐ alexMaster verified
☐ daddy verified
☐ agbabbby verified
☐ gdub_dg verified
☐ agonzalez729 verified
☐ ahoymrag12126 verified
☐ elluuhnn verified
☐ mrgstem verified
☐ alex63 verified
☐ ahoy_mr_ag25 verified
```

## How Trial Account Verification Works

**Before verification:**
```
You → Twilio → Friend's phone
❌ Blocked (unverified number)
```

**After friend verifies:**
```
You → Twilio → Friend's phone
✓ Delivered (verified number)
```

**Important:** Friend only needs to verify ONCE. After that, you can text them unlimited times during your trial (and after if you upgrade).

## Quick Test (All At Once)

```bash
# 1. Set credentials
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_PHONE_NUMBER="+1XXXXXXXXXX"

# 2. Verify YOUR number in dashboard first

# 3. Test to yourself
python scripts/send_whats_new_sms.py \
  --title "Test" \
  --description "If you got this, it works!"

# 4. Ask 2-3 friends to verify their numbers
# (They just need to confirm the code Twilio sends)

# 5. Add their numbers once verified
python scripts/quick_assign_phones.py conmanrogster01 +15551234567

# 6. Send to all verified
python scripts/send_whats_new_sms.py \
  --title "New Music" \
  --description "Check it out"
```

## Troubleshooting

**"Recipient must be verified"**
→ The number hasn't confirmed Twilio's verification code yet

**Friend says they didn't get the code**
→ Check SMS spam folder, or Twilio will offer a call instead

**Auth Token is wrong**
→ Double-check you copied the whole token (it's long)

**Need to verify more people?**
→ Just keep adding to **Verified Caller IDs** in Twilio

## After Trial Ends

Once you upgrade past trial:
- ✓ No verification needed
- ✓ Can SMS any number
- ✓ Only costs $0.0075 per SMS

But for now, just verify the ~5-10 friends you want to test with.

## Links

- **Twilio Console:** https://www.twilio.com/console
- **Phone Numbers:** https://www.twilio.com/console/phone-numbers/verified
- **Messaging Settings:** https://www.twilio.com/console/sms/settings/general
