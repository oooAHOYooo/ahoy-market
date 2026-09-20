#!/usr/bin/env python3
"""
Sync signup data to a Google Sheet using gspread.
Requires: pip install gspread google-auth-oauthlib google-auth-httplib2

Usage:
  DATABASE_URL=<prod_url> python scripts/sync-signups-sheet.py --sheet-id <id>
"""
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

try:
    import gspread
    from google.oauth2.service_account import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("ERROR: Missing dependencies. Install with:")
    print("  pip install gspread google-auth-oauthlib google-auth-httplib2")
    sys.exit(1)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']

def get_gspread_client():
    """Get gspread client with OAuth."""
    token_path = Path.home() / '.claude' / 'gspread_token.json'
    credentials_path = Path.home() / '.claude' / 'google_credentials.json'

    creds = None

    # Try to load existing token
    if token_path.exists():
        from google.oauth2.credentials import Credentials as OAuthCredentials
        creds = OAuthCredentials.from_authorized_user_file(str(token_path), SCOPES)

    # If no valid token, run OAuth flow
    if not creds or not creds.valid:
        if not credentials_path.exists():
            print("ERROR: Google credentials not found.")
            print("\nSetup:")
            print("1. Go to: https://console.cloud.google.com/apis/credentials")
            print("2. Create 'OAuth 2.0 Desktop App' credentials")
            print("3. Download JSON and save to: ~/.claude/google_credentials.json")
            sys.exit(1)

        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)

        # Save token
        token_path.parent.mkdir(exist_ok=True)
        with open(token_path, 'w') as f:
            f.write(creds.to_json())

    return gspread.Spreadsheet(None, {'spreadsheetId': None}, None, None, auth=creds)._http_client or gspread.authorize(creds)

def get_signup_data():
    """Fetch signup data from production database."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL not set")
        sys.exit(1)

    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT username, email, created_at
            FROM users
            ORDER BY created_at DESC
        """))
        return result.fetchall()

def sync_sheet(sheet_id):
    """Sync signup data to Google Sheet."""
    try:
        gc = gspread.oauth(scopes=SCOPES, credentials_filename=str(Path.home() / '.claude' / 'google_credentials.json'))
    except Exception:
        # If oauth file approach fails, try direct auth
        token_path = Path.home() / '.claude' / 'gspread_token.json'
        credentials_path = Path.home() / '.claude' / 'google_credentials.json'

        if not credentials_path.exists():
            print("ERROR: Google credentials not found at ~/.claude/google_credentials.json")
            print("\nSetup:")
            print("1. Go to: https://console.cloud.google.com/apis/credentials")
            print("2. Create 'OAuth 2.0 Desktop App' credentials")
            print("3. Download JSON and save to: ~/.claude/google_credentials.json")
            sys.exit(1)

        from google.oauth2.credentials import Credentials
        creds = None

        if token_path.exists():
            creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, 'w') as f:
                f.write(creds.to_json())

        gc = gspread.authorize(creds)

    # Open sheet
    try:
        ws = gc.open_by_key(sheet_id).worksheet(0)
    except Exception as e:
        print(f"ERROR: Could not open sheet. Make sure it's shared with your Google account.")
        print(f"Details: {e}")
        sys.exit(1)

    # Get data
    rows = get_signup_data()

    # Format data
    values = [['Username', 'Email', 'Signed Up', 'Days Since']]

    today = datetime.now().date()
    for username, email, created_at in rows:
        days_since = (today - created_at.date()).days
        values.append([
            username or '(no username)',
            email,
            created_at.strftime('%Y-%m-%d %H:%M:%S'),
            days_since
        ])

    # Clear and write
    ws.clear()
    ws.append_rows(values)

    print(f"✓ Synced {len(rows)} signups to sheet")
    print(f"  Sheet: https://docs.google.com/spreadsheets/d/{sheet_id}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--sheet-id', required=True, help='Google Sheet ID')
    args = parser.parse_args()

    sync_sheet(args.sheet_id)
