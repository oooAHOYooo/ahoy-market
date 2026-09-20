# SMS Notifications for "What's New" Items

This guide explains how to set up and use SMS notifications when adding new "what's new" content to Ahoy.

## Architecture

- **Phone Number Field**: Users can optionally add their phone number during signup
- **SMS Service**: Uses Twilio to send SMS messages
- **Command-Line Tool**: `send_whats_new_sms.py` script to broadcast SMS notifications

## Setup

### 1. Install Twilio SDK

```bash
pip install twilio
```

### 2. Get Twilio Credentials

1. Sign up at [Twilio](https://www.twilio.com)
2. Create a project and get:
   - **Account SID** — Your account identifier
   - **Auth Token** — Your authentication token
   - **Phone Number** — A Twilio phone number to send SMS from (e.g., +1234567890)

### 3. Set Environment Variables

```bash
export TWILIO_ACCOUNT_SID="your_account_sid"
export TWILIO_AUTH_TOKEN="your_auth_token"
export TWILIO_PHONE_NUMBER="+1234567890"  # Twilio-assigned number
```

For production (`.env` or deployment config), add:
```
TWILIO_ACCOUNT_SID=...
TWILIO_AUTH_TOKEN=...
TWILIO_PHONE_NUMBER=+1234567890
```

## Usage

### For Users: Signup with Phone Number

Users can optionally add their phone number during signup:
- Phone field appears in the signup form (LoginView.vue)
- Stored in the `users.phone_number` database field
- Users won't receive SMS if they don't provide a number

### For You: Send SMS Notifications

When you add a new "what's new" item, send SMS to subscribers:

```bash
# Show a preview without sending
python scripts/send_whats_new_sms.py \
  --title "New Music Release" \
  --description "Check out our latest tracks" \
  --link "https://ahoy.ooo/music" \
  --dry-run

# Send to all subscribers with phone numbers
python scripts/send_whats_new_sms.py \
  --title "New Music Release" \
  --description "Check out our latest tracks" \
  --link "https://ahoy.ooo/music"

# Test with a single phone number first
python scripts/send_whats_new_sms.py \
  --title "New Music Release" \
  --description "Check out our latest tracks" \
  --test-phone "+1234567890"
```

### Script Options

```
--title TEXT          Title of the new item (required)
--description TEXT    Brief description (required)
--link URL            Link to view the item (optional)
--test-phone +1234567890   Send only to this number for testing
--dry-run             Preview without sending
```

### Example Workflow

1. Add a new item to `static/data/whats_new.json` (or sync from elsewhere)
2. Test SMS with one number:
   ```bash
   python scripts/send_whats_new_sms.py \
     --title "New Video: The Rob Show" \
     --description "Check out Dominic Jace interview" \
     --link "https://ahoy.ooo/player?id=rob-show-dominic" \
     --test-phone "+15551234567"
   ```
3. If preview looks good, send to all:
   ```bash
   python scripts/send_whats_new_sms.py \
     --title "New Video: The Rob Show" \
     --description "Check out Dominic Jace interview" \
     --link "https://ahoy.ooo/player?id=rob-show-dominic"
   ```

## Message Format

SMS messages are automatically formatted to fit within typical SMS length:

```
Ahoy: [Title]
[First 50 chars of description]...
[Link if provided]
```

Example:
```
Ahoy: New Music Release
Check out our latest tracks...
https://ahoy.ooo/music
```

## Database Queries

### Check how many users have phone numbers

```bash
python -c "
from db import get_session
from models import User
with get_session() as session:
    count = session.query(User).filter(User.phone_number.isnot(None)).count()
    print(f'Users with phone numbers: {count}')
"
```

### Get list of subscribers

```bash
python -c "
from db import get_session
from models import User
with get_session() as session:
    users = session.query(User.username, User.phone_number).filter(
        User.phone_number.isnot(None)
    ).all()
    for username, phone in users:
        print(f'{username}: {phone}')
"
```

## SMS Service API

The SMS service is in `services/sms.py`. Key functions:

```python
# Check if SMS is configured
from services.sms import can_send_sms
if can_send_sms():
    print("SMS is ready")

# Send a single SMS
from services.sms import send_sms
result = send_sms("+1234567890", "Hello!")
print(result)  # {'ok': True, 'provider': 'twilio', 'detail': {...}}

# Send batch for what's new
from services.sms import notify_whats_new_sms
result = notify_whats_new_sms(
    item_title="New Video",
    item_description="Amazing content",
    recipients=["+1234567890", "+1987654321"],
    link="https://ahoy.ooo"
)
```

## Troubleshooting

**"SMS not configured"**
- Check that `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE_NUMBER` are set
- Run: `python -c "from services.sms import can_send_sms; print(can_send_sms())"`

**"Invalid phone number"**
- Ensure phone numbers include country code (e.g., +1 for US)
- Format: `+[country code][area code][number]`

**"Rate limiting"**
- Twilio has rate limits on free/trial accounts
- The service batches requests; test with small recipient lists first

**"Twilio not installed"**
- Run: `pip install twilio`

## Security Notes

- Never commit Twilio credentials to git
- Use environment variables or `.env` files (gitignored)
- Phone numbers are only sent to Twilio API; not stored elsewhere
- Keep `TWILIO_AUTH_TOKEN` secret

## Future Enhancements

- [ ] Opt-out mechanism for users
- [ ] SMS preference on user profile
- [ ] Scheduled batch notifications
- [ ] Track SMS delivery status
- [ ] Integration with admin dashboard for sending
