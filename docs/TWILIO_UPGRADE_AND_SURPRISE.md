# Upgrade Twilio & Surprise Your Friends

Time to upgrade past trial and start delightfully surprising your friends with SMS!

## Step 1: Upgrade Your Account

1. Go to: https://www.twilio.com/console
2. Top left, click **Upgrade** button
3. Add a payment method (credit/debit card)
4. Confirm

**Cost:** Only $0.0075 per SMS
- 10 friends per broadcast = $0.11
- 10 broadcasts/month = $1.10/month

## Step 2: Get Your Auth Token

1. In Twilio console, click account name (top right) → **Account**
2. Scroll to **API Credentials**
3. Click eye icon next to **Auth Token**
4. Copy the full token

## Step 3: Set Environment Variables

In your terminal (or `.env` file):

```bash
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="paste_your_full_auth_token_here"
export TWILIO_PHONE_NUMBER="+1XXXXXXXXXX"
```

## Step 4: Test It Works

```bash
python scripts/test_twilio.py
```

Should say: `✓ Connected to Twilio`

## Step 5: Add Your Friends' Numbers

**After upgrade, NO verification needed!** Just add their numbers directly:

```bash
python scripts/quick_assign_phones.py conmanrogster01 +15551234567
python scripts/quick_assign_phones.py alex +15559876543
python scripts/quick_assign_phones.py clairec +15558765432
python scripts/quick_assign_phones.py deven +15557654321
python scripts/quick_assign_phones.py gdub_dg +15556543210
```

Check who's added:
```bash
python scripts/quick_assign_phones.py --list
```

## Step 6: Send the First Surprise

Craft a message for your friends:

```bash
python scripts/send_whats_new_sms.py \
  --title "Ahoy! New Content" \
  --description "Something fresh just dropped on Ahoy"
```

Preview will show:
```
⚓ AHOY ⚓
Ahoy! New Content
Something fresh just dropped on Ahoy...
https://ahoy.ooo/whats-new
```

Then confirm: `yes` and watch the magic happen! 🎉

## Examples for Different Content Types

### New Music Release
```bash
python scripts/send_whats_new_sms.py \
  --title "New Music on Ahoy" \
  --description "Fresh tracks just released"
```

### New Video/Show
```bash
python scripts/send_whats_new_sms.py \
  --title "New Video: The Rob Show" \
  --description "Dominic Jace interview now live"
```

### Artist Spotlight
```bash
python scripts/send_whats_new_sms.py \
  --title "New Artist: Cherrie Cherrie" \
  --description "Check out debut track 'Waiting for the Long Days'"
```

### Behind-the-Scenes
```bash
python scripts/send_whats_new_sms.py \
  --title "Poets & Friends BTS Gallery" \
  --description "Exclusive behind-the-scenes photos dropped"
```

## Friends Will See

Your friends' phones will buzz with:

```
⚓ AHOY ⚓
New Music on Ahoy
Fresh tracks just released...
https://ahoy.ooo/whats-new
```

They tap the link → boom, they're on Ahoy discovering new stuff.

## Workflow

1. **Something new added to Ahoy**
   - New music, video, artist, etc.
   - You update `whats_new.json` or wherever

2. **Send SMS to friends**
   ```bash
   python scripts/send_whats_new_sms.py \
     --title "Whatever's new" \
     --description "Brief description"
   ```

3. **They get surprised** 📱
   - Tap link
   - See new content
   - Tell you they loved it ✨

## Pro Tips

### Test with Just Yourself First
```bash
python scripts/send_whats_new_sms.py \
  --title "Test" \
  --description "Testing..." \
  --test-phone "+1XXXXXXXXXX"  # Your number
```

### Check Who's in Your List
```bash
python scripts/quick_assign_phones.py --list
```

### Add More Friends Anytime
```bash
python scripts/quick_assign_phones.py newuser +15551234567
```

### No Art Version (Optional)
```bash
python scripts/send_whats_new_sms.py \
  --title "New Music" \
  --description "Check it" \
  --no-art
```

## Cost Breakdown

| Usage | Cost |
|-------|------|
| 5 friends, 1x/month | $0.04/month |
| 10 friends, 2x/month | $0.15/month |
| 15 friends, 4x/month | $0.45/month |
| 15 friends, 10x/month | $1.10/month |

Basically: **free to super cheap** 💰

## Their Reaction Chain

1. 📱 SMS arrives: "⚓ AHOY ⚓ New Music on Ahoy..."
2. 🔗 They tap link
3. 😍 They discover new content
4. 💬 They text back: "Yo this is fire!"
5. ✨ Repeat!

---

Ready? Go surprise them! 🎉
