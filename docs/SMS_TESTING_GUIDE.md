# SMS Notifications - Testing & Production Setup

Quick start guide for assigning phone numbers to your friends and testing SMS notifications.

## Your Database Users (15 total)

```
1.  conmanrogster01 (connorjrog@gmail.com)
2.  alex (alex@ahoy.ooo)
3.  clairec (cecooper03@gmail.com)
4.  deven (devenladson@pm.me)
5.  alexMaster (alexmaster@example.com)
6.  daddy (burtandi75@aol.com)
7.  agbabbby (agtechs@gmail.com)
8.  gdub_dg (weesegjw@gmail.com)
9.  agonzalez729 (alex@littlemarket.org)
10. ahoymrag12126 (alex@apeworx.io)
11. elluuhnn (ellenedgemartin@gmail.com)
12. mrgstem (agonzalez7@bridgeportedu.net)
13. alex63 (alex@cpcnewhaven.org)
14. ahoy_mr_ag25 (ahoy.mr.ag@gmail.com)
15. [unnamed guest]
```

## Step 1: Get Twilio Account

1. Sign up at https://www.twilio.com/
2. Create a new project
3. Get your:
   - **Account SID** (looks like `ACxxxxxxxxxxxxx`)
   - **Auth Token** (looks like `xxxxxxxxxxxxx`)
   - **Phone Number** (Twilio assigns you one, e.g., `+1234567890`)

## Step 2: Set Environment Variables

In your terminal (or `.env` for production):

```bash
export TWILIO_ACCOUNT_SID="ACxxxxxxxxxxxxx"
export TWILIO_AUTH_TOKEN="xxxxxxxxxxxxx"
export TWILIO_PHONE_NUMBER="+1234567890"
```

## Step 3: Assign Phone Numbers to Your Friends

Quick assignment command:

```bash
python scripts/quick_assign_phones.py USERNAME +1XXXXXXXXXX
```

Examples:

```bash
# Assign to your friends
python scripts/quick_assign_phones.py conmanrogster01 +15551234567
python scripts/quick_assign_phones.py alex +15559876543
python scripts/quick_assign_phones.py clairec +15558765432

# List all users anytime
python scripts/quick_assign_phones.py --list
```

## Step 4: Test SMS to One User

Before sending to all, test with one person:

```bash
python scripts/send_whats_new_sms.py \
  --title "Test Message from Ahoy" \
  --description "This is a test of the SMS system" \
  --test-phone "+15551234567"
```

This will show a preview and ask for confirmation before sending.

## Step 5: Send to All Subscribers

Once testing works, send to everyone with a phone number:

```bash
python scripts/send_whats_new_sms.py \
  --title "New Music Release" \
  --description "Check out our latest tracks" \
  --link "https://ahoy.ooo/whats-new"
```

The script will:
1. Show a preview of the message
2. Count how many people will receive it
3. Ask you to confirm with "yes"
4. Send and report results

### Message Format

SMS messages are automatically formatted to fit SMS length limits:

```
Ahoy: [Title]
[First 50 chars of description]...
[Link to what's new page]
```

Example output:
```
Ahoy: New Music Release
Check out our latest tracks...
https://ahoy.ooo/whats-new
```

## Management Commands

### List users and their phones

```bash
python scripts/quick_assign_phones.py --list
```

### Assign a single phone

```bash
python scripts/quick_assign_phones.py alex +15551234567
```

### Send SMS

```bash
# Preview only (no send)
python scripts/send_whats_new_sms.py \
  --title "Test" \
  --description "Hello" \
  --dry-run

# Send to specific test phone
python scripts/send_whats_new_sms.py \
  --title "Test" \
  --description "Hello" \
  --test-phone "+15551234567"

# Send to all users with phone numbers
python scripts/send_whats_new_sms.py \
  --title "New Content" \
  --description "Check it out"
```

## Workflow Example

```bash
# 1. Set Twilio credentials
export TWILIO_ACCOUNT_SID="..."
export TWILIO_AUTH_TOKEN="..."
export TWILIO_PHONE_NUMBER="+1234567890"

# 2. Assign phones to friends
python scripts/quick_assign_phones.py conmanrogster01 +15551234567
python scripts/quick_assign_phones.py alex +15559876543
python scripts/quick_assign_phones.py clairec +15558765432

# 3. Test with one person
python scripts/send_whats_new_sms.py \
  --title "Test Message" \
  --description "Testing SMS system"
# Confirm: yes

# 4. When you add new what's new content, send SMS
python scripts/send_whats_new_sms.py \
  --title "New Video: Rob Show" \
  --description "Dominic Jace interview"
# Confirm: yes
```

## SMS Content and Links

All SMS messages automatically link to your what's new page:
- **Default link**: `https://ahoy.ooo/whats-new`
- **Custom link**: Add `--link` parameter:
  ```bash
  python scripts/send_whats_new_sms.py \
    --title "New Video" \
    --description "Check it out" \
    --link "https://ahoy.ooo/player?id=rob-show-clip"
  ```

## Troubleshooting

### "User not found"
- Check username is correct: `python scripts/quick_assign_phones.py --list`
- Usernames are case-sensitive

### "SMS not configured"
- Verify environment variables are set:
  ```bash
  echo $TWILIO_ACCOUNT_SID
  echo $TWILIO_AUTH_TOKEN
  echo $TWILIO_PHONE_NUMBER
  ```

### "Invalid phone number"
- Must start with `+` and country code
- US format: `+1` + 10 digits (e.g., `+15551234567`)
- Include country codes for international numbers

### SMS not arriving
- Check Twilio account balance (free trial credits may be used)
- Verify the recipient's phone number format
- Check Twilio logs at twilio.com for delivery status

## For Production Deployment

When deploying to production, add environment variables to your deployment config:

```bash
TWILIO_ACCOUNT_SID=your_sid
TWILIO_AUTH_TOKEN=your_token  
TWILIO_PHONE_NUMBER=+1234567890
DATABASE_URL=postgresql://...  # Already set
```

The scripts automatically use the production database URL.

## Next Steps

1. Get Twilio credentials ✓
2. Assign phone numbers to friends ✓
3. Test SMS to one person ✓
4. Test workflow with a real what's new item ✓
5. Integrate with your content publishing workflow

After testing, you can:
- Add SMS notifications to admin dashboard
- Integrate with your content pipeline
- Allow users to opt-in/opt-out of notifications
