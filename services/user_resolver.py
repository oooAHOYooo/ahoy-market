from typing import Optional

import os

from flask import session
from flask_login import current_user

from db import get_session
from models import User

GUEST_USER_EMAIL = (os.getenv("AHOY_GUEST_EMAIL") or "guest@ahoy.local").strip().lower()


def resolve_db_user_id() -> Optional[int]:
    """Best-effort mapping of current session/login to DB user id.

    - If Flask-Login id is an int, use it
    - Else, try session['user_data']['profile']['email'] to find User by email
    """
    try:
        rid = current_user.get_id() if hasattr(current_user, "get_id") else None
        if rid is not None and str(rid).isdigit():
            return int(rid)
    except Exception:
        pass

    try:
        email = (session.get('user_data') or {}).get('profile', {}).get('email')
        if email:
            with get_session() as s:
                u = s.query(User).filter(User.email == email).first()
                if u:
                    return int(u.id)
    except Exception:
        pass
    return None


def guest_user_email() -> str:
    return GUEST_USER_EMAIL


def get_guest_db_user_id() -> int:
    """Return a stable internal guest user id, creating the row if needed."""
    with get_session() as s:
        user = s.query(User).filter(User.email == GUEST_USER_EMAIL).first()
        if user:
            return int(user.id)

        user = User(
            email=GUEST_USER_EMAIL,
            username=None,
            password_hash=None,
            display_name="Guest",
            preferences={},
            is_admin=False,
            disabled=False,
        )
        s.add(user)
        s.flush()
        return int(user.id)


def resolve_playback_user_id() -> int:
    """Resolve a playback target user, falling back to the internal guest account."""
    uid = resolve_db_user_id()
    if uid:
        return uid
    return get_guest_db_user_id()

