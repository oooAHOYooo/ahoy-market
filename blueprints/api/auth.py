from flask import Blueprint, request, jsonify, session, current_app, redirect
from flask_login import login_user, logout_user, login_required, current_user
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os
import secrets
import base64
import hashlib
from urllib.parse import urlencode
import requests

from db import get_session
from models import User
from utils.security import hash_password, verify_password
from utils.posthog_client import get_posthog_client
from extensions import limiter, rate_limit_auth, login_manager
from services.emailer import send_email, can_send_email
from authlib.integrations.requests_client import OAuth2Session


bp = Blueprint("api_auth", __name__, url_prefix="/api/auth")

_USERNAME_MIN = 2
_USERNAME_MAX = 24
_USERNAME_ALLOWED = set("abcdefghijklmnopqrstuvwxyz0123456789_")
_USERNAME_RESERVED = {
    "admin", "root", "support", "help", "about", "terms", "privacy",
    "settings", "account", "auth", "login", "logout", "register", "me",
    "api", "static", "assets",
}


def _ahoy_config():
    issuer = (os.getenv("AHOY_ID_ISSUER") or "http://127.0.0.1:3005").rstrip("/")
    client_id = os.getenv("AHOY_ID_CLIENT_ID", "app.ahoy.local-platform")
    redirect_uri = os.getenv("AHOY_ID_REDIRECT_URI", "http://127.0.0.1:5002/api/auth/ahoy/callback")
    return issuer, client_id, redirect_uri


def _pkce_pair():
    verifier = secrets.token_urlsafe(64)[:96]
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return verifier, challenge


@bp.get("/ahoy/login")
def ahoy_login():
    """Start AHOY ID login; identity linking is explicit and existing users remain supported."""
    issuer, client_id, redirect_uri = _ahoy_config()
    state = secrets.token_urlsafe(32)
    verifier, challenge = _pkce_pair()
    session["ahoy_oauth_state"] = state
    session["ahoy_oauth_verifier"] = verifier
    session["ahoy_oauth_next"] = request.args.get("next", "/")
    query = urlencode({"response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri,
                       "scope": "openid profile", "state": state, "code_challenge": challenge,
                       "code_challenge_method": "S256"})
    return redirect(f"{issuer}/oauth/authorize?{query}")


@bp.get("/ahoy/callback")
def ahoy_callback():
    """Exchange the one-use code server-side and sign in an already-linked product user."""
    if request.args.get("state") != session.pop("ahoy_oauth_state", None):
        return redirect("/#/login?error=ahoy_state_mismatch")
    verifier = session.pop("ahoy_oauth_verifier", None)
    next_path = session.pop("ahoy_oauth_next", "/")
    if not verifier or request.args.get("error") or not request.args.get("code"):
        return redirect("/#/login?error=ahoy_auth_failed")
    issuer, client_id, redirect_uri = _ahoy_config()
    try:
        token = requests.post(f"{issuer}/api/v1/oauth/token", json={
            "grant_type": "authorization_code", "code": request.args["code"],
            "client_id": client_id, "redirect_uri": redirect_uri, "code_verifier": verifier,
        }, timeout=8)
        token.raise_for_status()
        access_token = token.json()["access_token"]
        identity = requests.get(f"{issuer}/api/v1/oauth/userinfo",
                                headers={"Authorization": f"Bearer {access_token}"}, timeout=8)
        identity.raise_for_status()
        subject = identity.json().get("sub")
        if not isinstance(subject, str) or not subject.startswith("ahoy_"):
            raise ValueError("invalid AHOY subject")
        with get_session() as db_session:
            user = db_session.query(User).filter(User.ahoy_id == subject).one_or_none()
            link_user_id = session.pop("ahoy_link_user_id", None)
            if link_user_id:
                link_user = db_session.get(User, link_user_id)
                if not link_user or not link_user.is_active:
                    return redirect("/#/login?error=account_disabled")
                if user and user.id != link_user.id:
                    return redirect("/#/login?error=ahoy_already_linked")
                if link_user.ahoy_id and link_user.ahoy_id != subject:
                    return redirect("/#/login?error=ahoy_already_linked")
                link_user.ahoy_id = subject
                user = link_user
            if not user:
                return redirect("/#/login?error=ahoy_link_required")
            if not user.is_active:
                return redirect("/#/login?error=account_disabled")
            login_user(user, remember=True)
        return redirect(next_path if next_path.startswith("/") and not next_path.startswith("//") else "/")
    except Exception:
        current_app.logger.exception("AHOY ID callback failed")
        return redirect("/#/login?error=ahoy_auth_failed")


@bp.get("/ahoy/link")
@login_required
def ahoy_link():
    session["ahoy_link_user_id"] = current_user.id
    return ahoy_login()


def _normalize_username(raw: str) -> str:
    s = (raw or "").strip().lower()
    # Replace common separators with underscore, then strip invalid chars.
    s = s.replace(" ", "_").replace("-", "_").replace(".", "_")
    s = "".join(ch for ch in s if ch in _USERNAME_ALLOWED)
    # Collapse multiple underscores
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")


def _username_is_valid(u: str) -> bool:
    if not u:
        return False
    if len(u) < _USERNAME_MIN or len(u) > _USERNAME_MAX:
        return False
    if u in _USERNAME_RESERVED:
        return False
    return all(ch in _USERNAME_ALLOWED for ch in u)


def _derive_username_from_email(email: str) -> str:
    local = (email or "").split("@")[0]
    u = _normalize_username(local)
    return u[:_USERNAME_MAX]


def _suggest_usernames(base: str):
    base = _normalize_username(base)
    base = base[:_USERNAME_MAX]
    if not base:
        base = "user"
    # Keep suggestions short and tap-friendly on mobile.
    return [
        base,
        (base[: max(0, _USERNAME_MAX - 2)] + "01")[:_USERNAME_MAX],
        (base[: max(0, _USERNAME_MAX - 5)] + "_music")[:_USERNAME_MAX],
    ]


def _reset_serializer():
    from flask import current_app
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="ahoy-password-reset")


def _reset_token_for_user(user: User) -> str:
    # Include a stable “version” derived from password_hash so tokens are invalidated on password change.
    pwv = (user.password_hash or "")[:20]
    return _reset_serializer().dumps({"uid": int(user.id), "v": pwv})


def _verify_reset_token(token: str, max_age_seconds: int = 3600):
    data = _reset_serializer().loads(token, max_age=max_age_seconds)
    uid = int(data.get("uid"))
    v = str(data.get("v") or "")
    return uid, v


def _google_redirect_uri():
    """Get the Google OAuth redirect URI from env or derive from BASE_URL."""
    explicit = os.getenv("GOOGLE_REDIRECT_URI")
    if explicit:
        return explicit
    from config import public_url
    return public_url("/api/auth/google/callback")


def _google_client():
    """Create an OAuth2Session for Google authentication."""
    return OAuth2Session(
        client_id=os.getenv("GOOGLE_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        redirect_uri=_google_redirect_uri(),
        scope="openid email profile",
    )


@login_manager.user_loader
def load_user(user_id):
    """Load user for Flask-Login"""
    with get_session() as db_session:
        user = db_session.get(User, int(user_id))
        return user


@bp.post("/register")
@limiter.limit(rate_limit_auth)
def register():
    """Register new user with Flask sessions"""
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    username_raw = (data.get("username") or "").strip()
    username = _normalize_username(username_raw) if username_raw else _derive_username_from_email(email)
    password = data.get("password") or ""
    phone_number = (data.get("phone_number") or "").strip()

    if not email or not password:
        return jsonify({"error": "email_and_password_required"}), 400
    if not username:
        username = "user"
    if not _username_is_valid(username):
        return jsonify({
            "error": "invalid_username",
            "message": f"Username must be {_USERNAME_MIN}-{_USERNAME_MAX} chars, using letters/numbers/underscore.",
            "suggestions": _suggest_usernames(username or email.split("@")[0])
        }), 400

    pw_hash = hash_password(password)

    try:
        with get_session() as db_session:
            # Ensure uniqueness (case-insensitive) with a small suffix loop.
            base = username
            if base in _USERNAME_RESERVED or not _username_is_valid(base):
                base = _derive_username_from_email(email) or "user"
                base = base[:_USERNAME_MAX]

            candidate = base
            n = 0
            while True:
                exists = db_session.query(User.id).filter(func.lower(User.username) == candidate.lower()).first()
                if not exists:
                    break
                n += 1
                suffix = str(n)
                candidate = (base[: max(0, _USERNAME_MAX - len(suffix))] + suffix)[:_USERNAME_MAX]
                if n > 999:
                    return jsonify({"error": "username_unavailable"}), 409

            user = User(
                email=email,
                password_hash=pw_hash,
                username=candidate,
                display_name=(data.get("display_name") or "").strip() or candidate,
                phone_number=phone_number or None
            )
            db_session.add(user)
            db_session.flush()  # get user.id

            # Create Stripe Customer for normalized signup process
            stripe_customer_id = None
            try:
                import stripe
                stripe_api_key = current_app.config.get("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY_TEST")
                if stripe_api_key:
                    stripe.api_key = stripe_api_key
                    stripe_customer = stripe.Customer.create(
                        email=email,
                        name=user.display_name or candidate,
                        metadata={
                            "user_id": str(user.id),
                            "username": candidate,
                            "platform": "ahoy"
                        }
                    )
                    stripe_customer_id = stripe_customer.id
                    user.stripe_customer_id = stripe_customer_id
                    db_session.commit()
                    current_app.logger.info(f"Created Stripe customer {stripe_customer_id} for user {user.id}")
            except Exception as stripe_err:
                # Non-fatal: log but don't fail registration
                current_app.logger.warning(f"Failed to create Stripe customer for user {user.id}: {stripe_err}")
                db_session.commit()  # Commit user even if Stripe fails

            # Log user in with Flask-Login
            login_user(user, remember=True)

            # PostHog: track signup
            try:
                ph = get_posthog_client()
                if ph:
                    ph.capture(
                        distinct_id=str(user.id),
                        event="user_signed_up",
                        properties={"signup_method": "password", "has_stripe_customer": bool(stripe_customer_id)},
                    )
            except Exception:
                pass

            # Notify admin and user of new registration (unified)
            try:
                from services.notifications import notify_user_registered
                notify_user_registered(
                    user_id=user.id,
                    email=user.email,
                    username=user.username,
                    display_name=user.display_name
                )
            except Exception as notify_error:
                # Don't fail registration if notification fails
                current_app.logger.error(f"Failed to send user registration notification: {notify_error}", exc_info=True)

            return jsonify({
                "success": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "display_name": user.display_name,
                    "avatar_url": user.avatar_url
                }
            }), 201
    except IntegrityError:
        # Could be email or username uniqueness
        return jsonify({"error": "account_already_exists"}), 409
    except Exception as e:
        current_app.logger.exception("Registration failed")
        return jsonify({"error": "registration_failed", "detail": str(e)}), 500


@bp.post("/password-reset/request")
@limiter.limit("5/minute")
def password_reset_request():
    """Request a password reset email.

    Security:
    - Always returns success to avoid user enumeration.
    - Rate limited.
    """
    data = request.get_json(silent=True) or {}
    email = (data.get("email") or "").strip().lower()
    # Always respond success (do not leak whether the email exists).
    ok_resp = jsonify({"success": True, "message": "If that email exists, we sent a reset link."})
    if not email or "@" not in email:
        return ok_resp, 200

    if not can_send_email():
        # Still return success; operator can enable RESEND_API_KEY/SMTP later.
        current_app.logger.error(
            "Password reset email requested but email is not configured. "
            "Set RESEND_API_KEY + SUPPORT_EMAIL, or SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASS + SUPPORT_EMAIL."
        )
        return ok_resp, 200

    try:
        with get_session() as db_session:
            user = db_session.query(User).filter(User.email == email).first()
            if not user:
                return ok_resp, 200

            token = _reset_token_for_user(user)
            from config import public_url
            reset_link = public_url(f"/auth/reset?token={token}")

            subject = "Reset your Ahoy password"
            text = (
                "We got a request to reset your Ahoy password.\n\n"
                f"Reset it here (link expires in 1 hour):\n{reset_link}\n\n"
                "If you didn’t request this, you can ignore this email."
            )
            # Notify user
            from services.notifications import notify_user
            notify_user(user.email, subject=subject, text=text)
            
            # Optional: Notify admin (non-blocking)
            try:
                from services.notifications import notify_admin
                notify_admin(
                    f"Password reset requested for {user.email}",
                    f"Password reset link requested for user {user.email} (ID: {user.id})"
                )
            except Exception:
                pass  # Don't fail password reset if admin notification fails
    except Exception:
        # Never leak details; keep response stable.
        pass

    return ok_resp, 200


@bp.post("/password-reset/confirm")
@limiter.limit("10/minute")
def password_reset_confirm():
    """Confirm password reset with token + new password."""
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    new_password = data.get("password") or ""
    if not token or len(new_password) < 8:
        return jsonify({"error": "invalid_request"}), 400

    try:
        uid, v = _verify_reset_token(token, max_age_seconds=3600)
    except SignatureExpired:
        return jsonify({"error": "token_expired"}), 400
    except BadSignature:
        return jsonify({"error": "invalid_token"}), 400
    except Exception:
        return jsonify({"error": "invalid_token"}), 400

    with get_session() as db_session:
        user = db_session.get(User, uid)
        if not user:
            return jsonify({"error": "invalid_token"}), 400
        pwv = (user.password_hash or "")[:20]
        if pwv != v:
            # Password already changed (or token invalidated)
            return jsonify({"error": "invalid_token"}), 400

        user.password_hash = hash_password(new_password)
        db_session.commit()

    return jsonify({"success": True})


@bp.post("/login")
@limiter.limit(rate_limit_auth)
def login():
    """Login with Flask sessions"""
    try:
        data = request.get_json(silent=True) or {}
        identifier = (data.get("identifier") or data.get("email") or data.get("username") or "").strip()
        password = data.get("password") or ""

        if not identifier or not password:
            return jsonify({"error": "identifier_and_password_required"}), 400

        with get_session() as db_session:
            ident_l = identifier.strip().lower()
            if "@" in ident_l:
                user = db_session.query(User).filter(User.email == ident_l).first()
            else:
                uname = _normalize_username(ident_l)
                # Prefer username match; if user hasn't been backfilled yet, fall back to email-local-part match.
                user = db_session.query(User).filter(func.lower(User.username) == uname).first()
                if not user:
                    user = db_session.query(User).filter(User.email.like(f"{uname}@%")).first()
            if not user or not user.password_hash or not verify_password(password, user.password_hash):
                return jsonify({"error": "invalid_credentials"}), 401

            # Log user in with Flask-Login
            login_user(user, remember=True)

            # PostHog: track login
            try:
                ph = get_posthog_client()
                if ph:
                    ph.capture(
                        distinct_id=str(user.id),
                        event="user_logged_in",
                        properties={"login_method": "password"},
                    )
            except Exception:
                pass

            return jsonify({
                "success": True,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "display_name": user.display_name,
                    "avatar_url": user.avatar_url
                }
            })
    except Exception as e:
        current_app.logger.exception("Login failed")
        return jsonify({"error": "login_failed", "message": "An error occurred during login. Please try again."}), 500


@bp.post("/logout")
@login_required
def logout():
    """Logout user"""
    logout_user()
    return jsonify({"success": True})


@bp.post("/change-password")
@login_required
@limiter.limit("10/minute")
def change_password():
    """Change the current user's password after verifying the current password."""
    data = request.get_json(silent=True) or {}
    current_password = data.get("current_password") or ""
    new_password = data.get("new_password") or data.get("password") or ""

    if not current_password or len(new_password) < 8:
        return jsonify({"error": "invalid_request"}), 400

    if current_password == new_password:
        return jsonify({"error": "password_unchanged"}), 400

    with get_session() as db_session:
        user = db_session.get(User, current_user.id)
        if not user:
            return jsonify({"error": "user_not_found"}), 404
        if not user.password_hash:
            return jsonify({"error": "password_login_not_enabled"}), 400
        if not verify_password(current_password, user.password_hash):
            return jsonify({"error": "invalid_current_password"}), 401

        user.password_hash = hash_password(new_password)
        db_session.commit()

    return jsonify({"success": True})


@bp.post("/delete-account")
@login_required
def delete_account():
    """Delete current user account and data (REQUIRED for App Store compliance)"""
    try:
        user_id = current_user.id
        email = current_user.email
        
        with get_session() as db_session:
            user = db_session.get(User, user_id)
            if not user:
                return jsonify({"error": "user_not_found"}), 404
            
            # PostHog: track account deletion before data is gone
            try:
                ph = get_posthog_client()
                if ph:
                    ph.capture(
                        distinct_id=str(user_id),
                        event="user_account_deleted",
                        properties={},
                    )
            except Exception:
                pass

            # Perform deletion (Cascae in models.py handles related personal data)
            db_session.delete(user)
            db_session.commit()

            # Logout after deletion
            logout_user()
            
            # Log the event for admin (anonymized/indirectly)
            current_app.logger.info(f"User deleted account: {user_id} ({email})")
            
            return jsonify({"success": True, "message": "Account deleted successfully."})
    except Exception as e:
        current_app.logger.exception(f"Failed to delete account for user {current_user.id}")
        return jsonify({"error": "deletion_failed", "detail": str(e)}), 500


@bp.get("/me")
def me():
    """Get current user info. Returns 401 when not authenticated (no redirect)."""
    if not current_user.is_authenticated:
        return jsonify({"error": "not_authenticated"}), 401
    return jsonify({
        "user": {
            "id": current_user.id,
            "username": getattr(current_user, "username", None),
            "email": current_user.email,
            "display_name": current_user.display_name,
            "avatar_url": getattr(current_user, "avatar_url", None),
            "created_at": current_user.created_at.isoformat() if getattr(current_user, "created_at", None) else None,
        }
    })


@bp.put("/update")
@login_required
def update_profile():
    """Update current user profile and preferences"""
    data = request.get_json(silent=True) or {}

    with get_session() as db_session:
        # Re-fetch user in this session context to ensure we can commit changes
        user = db_session.get(User, current_user.id)
        if not user:
            return jsonify({"error": "user_not_found"}), 404

        # Update display_name
        if "display_name" in data:
            val = (data["display_name"] or "").strip()
            if val:
                user.display_name = val[:255]

        # Update avatar_url (badge name or URL)
        if "avatar_url" in data:
            user.avatar_url = data["avatar_url"]

        # Sync preferences (merge existing with new)
        # Bio is also stored in here to avoid a DB migration for now
        current_prefs = dict(user.preferences or {})
        
        if "preferences" in data and isinstance(data["preferences"], dict):
            current_prefs.update(data["preferences"])
            
        if "bio" in data:
            current_prefs["bio"] = (data["bio"] or "").strip()[:160]
            
        user.preferences = current_prefs
        db_session.commit()

        return jsonify({
            "success": True,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "display_name": user.display_name,
                "avatar_url": user.avatar_url,
                "preferences": user.preferences
            }
        })


@bp.get("/username-available")
@limiter.limit("2/minute")
def username_available():
    """Lightweight username availability check for the UI."""
    try:
        username = _normalize_username(request.args.get("username", ""))
        if not _username_is_valid(username):
            return jsonify({
                "available": False,
                "username": username,
                "error": "invalid_username",
                "suggestions": _suggest_usernames(username),
            }), 200
        try:
            with get_session() as db_session:
                exists = db_session.query(User.id).filter(func.lower(User.username) == username.lower()).first()
                return jsonify({
                    "available": not bool(exists),
                    "username": username,
                    "suggestions": _suggest_usernames(username),
                }), 200
        except Exception as e:
            current_app.logger.exception("Username availability check failed")
            # Return 200 with error flag instead of 500 to avoid breaking the UI
            return jsonify({
                "available": False,
                "username": username,
                "error": "server_error",
                "suggestions": _suggest_usernames(username),
            }), 200
    except Exception as e:
        current_app.logger.exception("Username availability endpoint error")
        # Return 200 with error flag instead of 500 to avoid breaking the UI
        return jsonify({
            "available": False,
            "username": request.args.get("username", ""),
            "error": "server_error",
            "suggestions": [],
        }), 200


@bp.get("/google/login")
@limiter.limit(rate_limit_auth)
def google_login():
    """Initiate Google OAuth flow.

    Saves CSRF state token to session and redirects user to Google's authorization endpoint.
    """
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        return jsonify({"error": "google_auth_not_configured"}), 503

    state = secrets.token_urlsafe(32)
    session["oauth_state"] = state

    client = _google_client()
    uri, _ = client.create_authorization_url(
        "https://accounts.google.com/o/oauth2/v2/auth",
        state=state,
        prompt="select_account",
    )
    return redirect(uri)


@bp.get("/google/callback")
def google_callback():
    """Handle Google OAuth callback.

    Validates state token, exchanges authorization code for tokens, fetches user profile,
    and either links to existing account or creates new one.
    """
    if not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        return redirect("/#/login?error=google_failed")

    # Check for OAuth error (user denied, etc.)
    error = request.args.get("error")
    if error:
        return redirect("/#/login?error=google_denied")

    # CSRF check
    state_in_session = session.pop("oauth_state", None)
    state_in_request = request.args.get("state")
    if not state_in_session or state_in_session != state_in_request:
        current_app.logger.warning("Google OAuth: CSRF state mismatch")
        return redirect("/#/login?error=google_failed")

    # Exchange authorization code for tokens
    client = _google_client()
    try:
        token = client.fetch_token(
            "https://oauth2.googleapis.com/token",
            authorization_response=request.url,
        )
    except Exception as e:
        current_app.logger.exception(f"Google token fetch failed: {e}")
        return redirect("/#/login?error=google_failed")

    # Fetch user profile from Google
    try:
        resp = client.get("https://www.googleapis.com/oauth2/v3/userinfo")
        profile = resp.json()
    except Exception as e:
        current_app.logger.exception(f"Google userinfo fetch failed: {e}")
        return redirect("/#/login?error=google_failed")

    google_id = profile.get("sub")
    email = (profile.get("email") or "").strip().lower()
    picture = profile.get("picture")
    name = profile.get("name") or ""

    if not google_id or not email:
        current_app.logger.warning(f"Google profile missing required fields: sub={google_id}, email={email}")
        return redirect("/#/login?error=google_failed")

    # Link or create user account
    is_new = False
    try:
        with get_session() as db_session:
            # 1. Look up by google_id (returning user)
            user = db_session.query(User).filter(User.google_id == google_id).first()

            # 2. Link by email match (existing email/password account)
            if not user:
                user = db_session.query(User).filter(User.email == email).first()
                if user:
                    user.google_id = google_id
                    if not user.avatar_url and picture:
                        user.avatar_url = picture
                    db_session.commit()

            # 3. Auto-create new account
            if not user:
                is_new = True
                base = _derive_username_from_email(email)
                username = base or "user"
                # Deduplicate username (reuse existing loop logic from register())
                candidate = username[:_USERNAME_MAX]
                n = 0
                while True:
                    exists = db_session.query(User.id).filter(
                        func.lower(User.username) == candidate.lower()
                    ).first()
                    if not exists:
                        break
                    n += 1
                    suffix = str(n)
                    candidate = (username[: max(0, _USERNAME_MAX - len(suffix))] + suffix)[:_USERNAME_MAX]
                    if n > 999:
                        return redirect("/#/login?error=google_failed")

                user = User(
                    email=email,
                    google_id=google_id,
                    username=candidate,
                    display_name=name or candidate,
                    avatar_url=picture,
                    password_hash=None,  # Google-only account, no password needed
                )
                db_session.add(user)
                db_session.flush()

                # Create Stripe customer (same pattern as register())
                stripe_customer_id = None
                try:
                    import stripe
                    stripe_api_key = current_app.config.get("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY_TEST")
                    if stripe_api_key:
                        stripe.api_key = stripe_api_key
                        stripe_customer = stripe.Customer.create(
                            email=email,
                            name=user.display_name or candidate,
                            metadata={
                                "user_id": str(user.id),
                                "username": candidate,
                                "platform": "ahoy"
                            }
                        )
                        stripe_customer_id = stripe_customer.id
                        user.stripe_customer_id = stripe_customer_id
                        db_session.commit()
                        current_app.logger.info(f"Created Stripe customer {stripe_customer_id} for user {user.id}")
                except Exception as stripe_err:
                    # Non-fatal: log but don't fail
                    current_app.logger.warning(f"Failed to create Stripe customer for user {user.id}: {stripe_err}")
                    db_session.commit()  # Commit user even if Stripe fails

        # Log in user with Flask-Login (session cookie)
        login_user(user, remember=True)

        # PostHog: track signup or login via Google
        try:
            ph = get_posthog_client()
            if ph:
                if is_new:
                    ph.capture(
                        distinct_id=str(user.id),
                        event="user_signed_up",
                        properties={"signup_method": "google"},
                    )
                else:
                    ph.capture(
                        distinct_id=str(user.id),
                        event="user_logged_in",
                        properties={"login_method": "google"},
                    )
        except Exception:
            pass

        # Notify admin and user of new registration (for new accounts only)
        if is_new:
            try:
                from services.notifications import notify_user_registered
                notify_user_registered(
                    user_id=user.id,
                    email=user.email,
                    username=user.username,
                    display_name=user.display_name
                )
            except Exception as notify_error:
                # Don't fail login if notification fails
                current_app.logger.error(f"Failed to send user registration notification: {notify_error}", exc_info=True)

        # Redirect to SPA callback route (which will call /api/auth/me and redirect to /)
        return redirect("/auth/google/callback")

    except Exception as e:
        current_app.logger.exception(f"Google OAuth account linking failed: {e}")
        return redirect("/#/login?error=google_failed")
