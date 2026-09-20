#!/bin/bash
# Apply migrations to production database and test SMS setup

set -e

echo "=== Production Database Migration & SMS Setup ==="
echo ""

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL environment variable not set"
    echo "Example:"
    echo '  export DATABASE_URL="postgresql://user:password@host/dbname"'
    exit 1
fi

echo "Database: $DATABASE_URL"
echo ""

# Run migrations
echo "1. Applying database migrations..."
alembic upgrade head
echo "   ✓ Migrations applied"
echo ""

# Check users
echo "2. Existing users:"
python << 'EOF'
from db import get_session
from models import User

with get_session() as session:
    users = session.query(User.id, User.username, User.email).order_by(User.created_at.desc()).all()
    if not users:
        print("   No users found")
    else:
        print(f"   Found {len(users)} users:\n")
        for user_id, username, email in users:
            print(f"   - ID {user_id}: @{username} ({email})")
EOF

echo ""
echo "3. Assign phone numbers:"
echo "   Run: python scripts/assign_phone_numbers.py"
echo ""
echo "4. Send test SMS:"
echo "   First, set Twilio credentials:"
echo '     export TWILIO_ACCOUNT_SID="..."'
echo '     export TWILIO_AUTH_TOKEN="..."'
echo '     export TWILIO_PHONE_NUMBER="+1234567890"'
echo ""
echo "   Then test with:"
echo '     python scripts/send_whats_new_sms.py --title "Test" --description "Hello" --test-phone "+15551234567"'
