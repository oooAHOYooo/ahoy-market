#!/usr/bin/env python3
"""
Create a Google Sheet with signup data and share it with a user.
Requires: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client

Usage:
  python scripts/create-signup-sheet.py --share alex@ahoy.ooo
"""
import os
import sys
import argparse
from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.service_account import Credentials
from google.oauth2 import service_account
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.googleapis import Request as GoogleRequest
import googleapiclient.discovery
from googleapiclient.errors import HttpError

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']

def get_google_credentials():
    """Get Google credentials with OAuth flow."""
    creds = None
    token_path = Path.home() / '.claude' / 'google_token.json'
    credentials_path = Path.home() / '.claude' / 'google_credentials.json'

    # Check if stored token exists
    if token_path.exists():
        from google.oauth2.credentials import Credentials as OAuthCredentials
        creds = OAuthCredentials.from_authorized_user_file(str(token_path), SCOPES)

    # If not, run OAuth flow
    if not creds or not creds.valid:
        if not credentials_path.exists():
            print("ERROR: Google credentials JSON not found.")
            print("1. Go to: https://console.cloud.google.com/apis/credentials")
            print("2. Create OAuth 2.0 Desktop App credentials")
            print("3. Download JSON and save to: ~/.claude/google_credentials.json")
            sys.exit(1)

        flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
        creds = flow.run_local_server(port=0)

        # Save token for next time
        token_path.parent.mkdir(exist_ok=True)
        with open(token_path, 'w') as f:
            f.write(creds.to_json())

    return creds

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

def create_and_share_sheet(share_email):
    """Create a Google Sheet, populate with data, and share."""
    creds = get_google_credentials()

    sheets_service = googleapiclient.discovery.build('sheets', 'v4', credentials=creds)
    drive_service = googleapiclient.discovery.build('drive', 'v3', credentials=creds)

    # Create sheet
    spreadsheet_body = {
        'properties': {
            'title': f'Ahoy Signups ({datetime.now().strftime("%Y-%m-%d")})'
        }
    }

    sheet = sheets_service.spreadsheets().create(body=spreadsheet_body, fields='spreadsheetId').execute()
    sheet_id = sheet['spreadsheetId']

    # Get signup data
    rows = get_signup_data()

    # Format data for sheet
    values = [
        ['Username', 'Email', 'Signed Up', 'Days Since'],
    ]

    today = datetime.now().date()
    for username, email, created_at in rows:
        days_since = (today - created_at.date()).days
        values.append([
            username or '(no username)',
            email,
            created_at.strftime('%Y-%m-%d %H:%M:%S'),
            days_since
        ])

    # Write data
    body = {'values': values}
    sheets_service.spreadsheets().values().update(
        spreadsheetId=sheet_id,
        range='Sheet1!A1',
        valueInputOption='RAW',
        body=body
    ).execute()

    # Format header row
    requests = [
        {
            'repeatCell': {
                'range': {
                    'sheetId': 0,
                    'startRowIndex': 0,
                    'endRowIndex': 1,
                },
                'cell': {
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 0.2, 'green': 0.2, 'blue': 0.2},
                        'textFormat': {'bold': True, 'foregroundColor': {'red': 1, 'green': 1, 'blue': 1}},
                    }
                },
                'fields': 'userEnteredFormat'
            }
        },
        {
            'autoResizeDimensions': {
                'dimensions': {
                    'sheetId': 0,
                    'dimension': 'COLUMNS',
                    'startIndex': 0,
                    'endIndex': 4,
                }
            }
        }
    ]

    sheets_service.spreadsheets().batchUpdate(
        spreadsheetId=sheet_id,
        body={'requests': requests}
    ).execute()

    # Share with user
    try:
        drive_service.permissions().create(
            fileId=sheet_id,
            body={'type': 'user', 'role': 'owner', 'emailAddress': share_email},
            transferOwnership=True,
            fields='id'
        ).execute()
        print(f"✓ Sheet created and transferred to {share_email}")
    except HttpError as e:
        print(f"Warning: Could not transfer ownership: {e}")
        print(f"  But you can access the sheet and change ownership manually")

    sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/edit"
    print(f"\n✓ Sheet URL: {sheet_url}")
    print(f"✓ {len(rows)} users exported")

    return sheet_url

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--share', default='alex@ahoy.ooo', help='Email to share sheet with')
    args = parser.parse_args()

    create_and_share_sheet(args.share)
