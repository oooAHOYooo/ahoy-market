"""
SMS notification service using Twilio.
Send SMS notifications for new "what's new" items and other events.
"""
import os
import logging
from typing import Optional, Dict, Any, List
from decimal import Decimal

log = logging.getLogger(__name__)


def _get_twilio_credentials() -> tuple[Optional[str], Optional[str], Optional[str]]:
    """Get Twilio credentials from environment variables."""
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    phone_from = os.getenv("TWILIO_PHONE_NUMBER")
    return account_sid, auth_token, phone_from


def can_send_sms() -> bool:
    """Check if SMS is configured."""
    account_sid, auth_token, phone_from = _get_twilio_credentials()
    return bool(account_sid and auth_token and phone_from)


def send_sms(to_phone: str, message: str) -> Dict[str, Any]:
    """
    Send SMS message via Twilio.

    Args:
        to_phone: Recipient phone number (should include country code, e.g. +1234567890)
        message: Message text (max 160 chars recommended for single SMS)

    Returns:
        Dict with keys: ok (bool), provider (str), detail (str|dict)
    """
    to_phone = (to_phone or "").strip()
    if not to_phone:
        log.warning("send_sms: missing to_phone")
        return {"ok": False, "provider": "twilio", "detail": "missing_to_phone"}

    account_sid, auth_token, phone_from = _get_twilio_credentials()
    if not can_send_sms():
        log.warning("SMS not configured (missing TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE_NUMBER)")
        return {"ok": False, "provider": "twilio", "detail": "sms_not_configured"}

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)
        sms = client.messages.create(
            body=message,
            from_=phone_from,
            to=to_phone,
        )
        log.info(f"SMS sent to {to_phone}: {sms.sid}")
        return {"ok": True, "provider": "twilio", "detail": {"sid": sms.sid, "status": sms.status}}
    except Exception as e:
        log.error(f"Failed to send SMS to {to_phone}: {e}")
        return {"ok": False, "provider": "twilio", "detail": str(e)}


def notify_whats_new_sms(
    item_title: str,
    item_description: str,
    recipients: List[str],
    link: Optional[str] = None,
    use_art: bool = True
) -> Dict[str, Any]:
    """
    Send SMS notification for a new "what's new" item to multiple recipients.

    Args:
        item_title: Title of the new item
        item_description: Brief description of the item
        recipients: List of phone numbers to send to
        link: Optional link to view the item
        use_art: Include ASCII art header (default: True)

    Returns:
        Dict with keys: sent (int), failed (int), errors (list)
    """
    if not can_send_sms():
        log.warning("SMS not configured, skipping what's new notification")
        return {"sent": 0, "failed": len(recipients), "errors": ["sms_not_configured"]}

    results = {"sent": 0, "failed": 0, "errors": []}

    # Construct message with optional ASCII art
    if use_art:
        message = "⚓ AHOY ⚓\n"
    else:
        message = "Ahoy: "

    message += f"{item_title}\n"
    message += f"{item_description[:50]}..."

    if link:
        message += f"\n{link}"

    for phone in recipients:
        phone = (phone or "").strip()
        if not phone:
            results["failed"] += 1
            results["errors"].append("empty_phone")
            continue

        result = send_sms(phone, message)
        if result["ok"]:
            results["sent"] += 1
        else:
            results["failed"] += 1
            results["errors"].append(result["detail"])

    return results


def notify_boost_received_sms(
    artist_name: str,
    boost_amount: Decimal,
    recipient_phone: str
) -> Dict[str, Any]:
    """Send SMS notification when an artist receives a boost."""
    if not can_send_sms():
        return {"ok": False, "provider": "twilio", "detail": "sms_not_configured"}

    message = f"Ahoy: You received a ${boost_amount:.2f} boost for {artist_name}! Check your wallet."
    return send_sms(recipient_phone, message)


def notify_merch_purchase_sms(
    item_name: str,
    total: Decimal,
    buyer_phone: str
) -> Dict[str, Any]:
    """Send SMS order confirmation for merch purchase."""
    if not can_send_sms():
        return {"ok": False, "provider": "twilio", "detail": "sms_not_configured"}

    message = f"Ahoy: Order confirmed for {item_name} - ${total:.2f}. You'll receive tracking soon."
    return send_sms(buyer_phone, message)
