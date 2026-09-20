from flask import Flask, render_template, jsonify, request, session, send_from_directory, make_response, redirect, url_for, current_app, abort, Response
try:
    from flask_session import Session as FlaskSession
except Exception:  # ImportError or env issues
    FlaskSession = None
from flask_login import current_user, login_required
from werkzeug.middleware.proxy_fix import ProxyFix
import os
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
import random
import hashlib
from functools import lru_cache, wraps
from typing import Optional
from html import escape as html_escape
# Removed: user_manager.py (consolidated to database-based auth)
from dotenv import load_dotenv
load_dotenv()
import re
from pathlib import Path

from config import get_config
from extensions import bcrypt, login_manager, limiter, init_cors, compress
from utils.auth import admin_required, get_effective_user
from utils.observability import init_sentry
from utils.posthog_client import init_posthog
from services.posthog_sync import validate_posthog_environment, build_posthog_sync_status
from utils.logging_init import init_logging, init_request_logging
from utils.security_headers import attach_security_headers, create_csp_report_blueprint
from utils.csrf_init import init_csrf
# Removed: blueprints/auth.py (consolidated into api/auth)
from services.content_db import (
    get_all_tracks, get_all_shows, get_all_artists, get_all_podcasts,
    get_all_events, get_all_merch, get_all_videos, get_all_whats_new,
    get_tracks_list, get_shows_list, get_artists_list, invalidate_cache as invalidate_content_cache,
    _PODCAST_SLUG_ALIASES,
)
from services.radio_station import build_radio_manifest as build_radio_station_manifest
from blueprints.api.auth import bp as api_auth_bp
from blueprints.activity import bp as activity_bp
# Removed: blueprints/playlists.py and blueprints/bookmarks.py (shadowed by API blueprints)
# Removed: blueprints/collections.py (feature removed)
from blueprints.gamification import bp as gamification_bp
from blueprints.payments import bp as payments_bp
from routes.boost_stripe import bp as boost_stripe_bp
from routes.boost_stripe import boost_api_bp
from routes.stripe_webhooks import bp as stripe_webhooks_bp
from services.listening import start_session as listening_start_session, end_session as listening_end_session
from services.user_resolver import resolve_db_user_id, resolve_playback_user_id
from db import get_session
from models import UserArtistFollow, Show
from models import Purchase, BetaSignup

# Initialize search index on app startup
def initialize_search_index():
    """Initialize the search index with all content, prioritizing DB"""
    try:
        from search_indexer import search_index
        from services.content_db import get_tracks_list, get_shows_list, get_artists_list
        
        # Try to pull from DB first
        try:
            music = get_tracks_list(ttl=0) # ttl=0 to force fresh load on startup
            shows = get_shows_list(ttl=0)
            artists = get_artists_list(ttl=0)
            
            if music or shows or artists:
                search_index.reindex_from_data(music, shows, artists)
                print(f"Search index initialized from DB with {search_index.total_docs} documents")
                return
        except Exception as e:
            print(f"DB search reindex failed: {e}. Falling back to JSON...")
        
        # Fallback to JSON
        data_sources = {
            'music': 'static/data/music.json',
            'shows': 'static/data/shows.json',
            'artists': 'static/data/artists.json'
        }
        search_index.reindex(data_sources)
        print(f"Search index initialized from JSON fallback with {search_index.total_docs} documents")
        
    except Exception as e:
        print(f"Error initializing search index: {e}")

def startup_logging(app):
    """Log startup configuration for operational visibility"""
    import structlog
    import os
    from utils.observability import get_release
    
    logger = structlog.get_logger()
    
    # Logging configuration
    flask_env = os.getenv("FLASK_ENV", "development")
    log_level = os.getenv("LOG_LEVEL", "INFO")
    logging_mode = "json" if flask_env == "production" else "console"
    
    # Sentry configuration
    sentry_dsn = os.getenv("SENTRY_DSN")
    sentry_enabled = bool(sentry_dsn)
    release = get_release()
    
    # Rate limiting configuration
    rate_limit_default = os.getenv("RATE_LIMIT_DEFAULT", "60 per minute")
    rate_limit_auth = os.getenv("RATE_LIMIT_AUTH", "10 per minute")
    
    # Security configuration
    csrf_enabled = True
    security_headers_enabled = flask_env == "production"
    
    # Emit single compact startup log
    logger.info("Ahoy ready",
               env=flask_env,
               release=release,
               sentry=sentry_enabled,
               csrf=csrf_enabled)


def _admin_session_required(fn):
    """Admin guard for browser/session-based admin routes (Flask-Login)."""
    from functools import wraps
    from flask import request as _request, jsonify as _jsonify, redirect as _redirect, url_for as _url_for, flash as _flash

    @wraps(fn)
    def wrapper(*args, **kwargs):
        wants_html = 'text/html' in (_request.headers.get('Accept') or '')
        if not getattr(current_user, "is_authenticated", False):
            if wants_html:
                _flash("Please log in as admin", "warning")
                return _redirect(_url_for('auth_page'))
            return _jsonify({"error": "forbidden"}), 403
        if not getattr(current_user, "is_admin", False):
            if wants_html:
                _flash("Admin access required", "danger")
                return _redirect(_url_for('home'))
            return _jsonify({"error": "forbidden"}), 403
        return fn(*args, **kwargs)

    return wrapper


def _owner_email():
    return (os.getenv("AHOY_ADMIN_EMAIL") or "alex@ahoy.ooo").strip().lower()


def _owner_session_required(fn):
    """Private owner-only guard for internal ops pages."""
    from functools import wraps
    from flask import request as _request, jsonify as _jsonify, redirect as _redirect

    @wraps(fn)
    def wrapper(*args, **kwargs):
        wants_html = 'text/html' in (_request.headers.get('Accept') or '')
        if not getattr(current_user, "is_authenticated", False):
            return _redirect("/") if wants_html else _jsonify({"error": "forbidden"}), 403

        email = (getattr(current_user, "email", "") or "").strip().lower()
        if email != _owner_email():
            return _redirect("/") if wants_html else _jsonify({"error": "forbidden"}), 403

        return fn(*args, **kwargs)

    return wrapper


def _bootstrap_admin_user_from_env():
    """
    Create/update an admin user from env without committing secrets.

    Set:
      - AHOY_ADMIN_EMAIL
      - AHOY_ADMIN_PASSWORD

    In development only: if either is unset, use hardcoded dev credentials
    (alex@ahoy.ooo / loveLOVElove) so you can hit /admin without configuring env.
    """
    email = (os.getenv("AHOY_ADMIN_EMAIL") or "").strip().lower()
    password = os.getenv("AHOY_ADMIN_PASSWORD") or ""
    # Dev-only fallback so /admin works without env (do not use in production)
    if (not email or not password) and os.getenv("AHOY_ENV", "").strip().lower() in ("development", "dev", "sandbox"):
        email = "alex@ahoy.ooo"
        password = "12345"
    if not email or not password:
        return
    try:
        from db import get_session
        from models import User
        from utils.security import hash_password

        with get_session() as s:
            u = s.query(User).filter(User.email == email).first()
            if not u:
                u = User(
                    email=email,
                    password_hash=hash_password(password),
                    is_admin=True,
                    display_name=email.split("@")[0],
                )
                s.add(u)
            else:
                u.password_hash = hash_password(password)
                u.is_admin = True
                if not u.display_name:
                    u.display_name = email.split("@")[0]
            s.commit()
    except Exception:
        # Never crash app startup if bootstrap fails.
        return

def _hide_podcast_shows(slugs: list):
    """Mark specific podcast shows as hidden on startup. Idempotent."""
    try:
        from models import PodcastShow
        with get_session() as s:
            s.query(PodcastShow).filter(PodcastShow.slug.in_(slugs)).update(
                {PodcastShow.is_hidden: True}, synchronize_session=False
            )
            s.commit()
    except Exception:
        pass


def _load_video_catalog_for_seo():
    """Load the current video/show catalog for server-side preview metadata."""
    try:
        data = get_all_shows(ttl=600)
        if isinstance(data, dict) and data.get('shows'):
            return data.get('shows') or []
    except Exception:
        pass

    try:
        data = load_json_data('shows.json', {'shows': []})
        if isinstance(data, dict) and data.get('shows'):
            return data.get('shows') or []
    except Exception:
        pass

    try:
        static_shows = Path('static/data/shows.json')
        if static_shows.exists():
            with open(static_shows, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data.get('shows') or []
    except Exception:
        pass

    return []


def _find_video_for_seo(request_path: str):
    """Resolve a videos route to its backing show record."""
    path = (request_path or '').strip().strip('/')
    if not path.startswith('videos/'):
        return None

    parts = path.split('/')
    shows = _load_video_catalog_for_seo()

    if len(parts) == 2:
        video_id = parts[1]
        for show in shows:
            if str(show.get('id')) == video_id:
                return show
        return None

    if len(parts) >= 3:
        host_slug = parts[1]
        show_id = parts[2]
        for show in shows:
            if str(show.get('host_slug') or '') == host_slug and str(show.get('id')) == show_id:
                return show

    return None


def _absolute_url(path_value: str) -> str:
    """Convert a relative asset path into an absolute URL for social crawlers."""
    value = str(path_value or '').strip()
    if not value:
        return ''
    if value.startswith('http://') or value.startswith('https://'):
        return value
    return request.url_root.rstrip('/') + '/' + value.lstrip('/')


def _render_spa_with_meta(title: str, description: str, image: str, og_type: str, request_path: str):
    """Return the SPA shell with custom Open Graph / Twitter tags injected."""
    if not _spa_dist_ready():
        abort(404)

    html = _spa_index_html()

    page_url = request.url_root.rstrip('/') + '/' + request_path.strip('/')

    replacements = {
        '<meta name="title" content="Ahoy Indie Media">': f'<meta name="title" content="{html_escape(title)} — Ahoy Indie Media">',
        '<meta name="description" content="Stream music, videos, and podcasts from independent artists. Send tips directly to creators.">': f'<meta name="description" content="{html_escape(description)}">',
        '<meta property="og:url" content="https://app.ahoy.ooo/">': f'<meta property="og:url" content="{html_escape(page_url)}">',
        '<meta property="og:type" content="website">': f'<meta property="og:type" content="{og_type}">',
        '<meta property="og:site_name" content="Ahoy Indie Media">': '<meta property="og:site_name" content="Ahoy Indie Media">',
        '<meta property="og:title" content="Ahoy Indie Media">': f'<meta property="og:title" content="{html_escape(title)} — Ahoy Indie Media">',
        '<meta property="og:description" content="Stream music, videos, and podcasts from independent artists. Send tips directly to creators.">': f'<meta property="og:description" content="{html_escape(description)}">',
        '<meta property="og:image" content="https://app.ahoy.ooo/static/img/ahoy_logo.png">': f'<meta property="og:image" content="{html_escape(image)}">',
        '<meta property="og:image:width" content="1200">': '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">': '<meta property="og:image:height" content="630">',
        '<link rel="canonical" href="https://app.ahoy.ooo/">': f'<link rel="canonical" href="{html_escape(page_url)}">',
        '<meta property="twitter:url" content="https://app.ahoy.ooo/">': f'<meta property="twitter:url" content="{html_escape(page_url)}">',
        '<meta property="twitter:title" content="Ahoy Indie Media">': f'<meta property="twitter:title" content="{html_escape(title)} — Ahoy Indie Media">',
        '<meta property="twitter:description" content="Stream music, videos, and podcasts from independent artists. Send tips directly to creators.">': f'<meta property="twitter:description" content="{html_escape(description)}">',
        '<meta property="twitter:image" content="https://app.ahoy.ooo/static/img/ahoy_logo.png">': f'<meta property="twitter:image" content="{html_escape(image)}">',
    }

    for old, new in replacements.items():
        html = html.replace(old, new)

    html = html.replace('<title>Ahoy Indie Media</title>', f'<title>{html_escape(title)} — Ahoy Indie Media</title>')
    config_script = _spa_posthog_config_script()
    if config_script and "window.__AHOY_POSTHOG__" not in html:
        html = html.replace("</head>", f"{config_script}</head>", 1)

    response = make_response(html)
    response.headers['Content-Type'] = 'text/html; charset=utf-8'
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return response


def _render_spa_with_video_meta(show: dict, request_path: str):
    title = str(show.get('title') or 'Video').strip()
    description = str(show.get('description') or f'Watch {title} on Ahoy Indie Media.').strip()
    image = _absolute_url(show.get('thumbnail') or '/static/img/ahoy_logo.png')
    return _render_spa_with_meta(title, description, image, 'video.other', request_path)


def _find_artist_for_seo(path: str):
    """Resolve /artists/:slug to its artist record."""
    parts = path.strip().strip('/').split('/')
    if len(parts) != 2 or parts[0] != 'artists':
        return None
    slug = parts[1]
    try:
        artists = get_all_artists(ttl=600).get('artists') or []
        for a in artists:
            if str(a.get('slug') or '') == slug:
                return a
    except Exception:
        pass
    return None


def _find_podcast_for_seo(path: str):
    """Resolve /podcasts/:slug (and /podcasts/:slug/:number) to a podcast show record."""
    parts = path.strip().strip('/').split('/')
    if len(parts) < 2 or parts[0] != 'podcasts':
        return None
    slug = parts[1]
    try:
        shows = get_all_podcasts(ttl=600).get('shows') or []
        for show in shows:
            if str(show.get('slug') or '') == slug:
                return show
    except Exception:
        pass
    return None


def _find_event_for_seo(path: str):
    """Resolve /events/:series/:number, /events/v/:id, or /events/:series to an event record."""
    parts = path.strip().strip('/').split('/')
    if len(parts) < 2 or parts[0] != 'events':
        return None
    try:
        events = get_all_events(ttl=600).get('events') or []
        if parts[1] == 'v' and len(parts) >= 3:
            event_id = parts[2]
            for e in events:
                if str(e.get('id') or '') == event_id:
                    return e
        elif len(parts) >= 3:
            series, number = parts[1], parts[2]
            for e in events:
                if str(e.get('series') or '') == series and str(e.get('number') or '') == number:
                    return e
        elif len(parts) == 2:
            # /events/:series — return the most recent event in that series
            series = parts[1]
            matches = [e for e in events if str(e.get('series') or '') == series]
            if matches:
                return matches[0]
    except Exception:
        pass
    return None


def _seo_slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").strip().lower()).strip("-")


def _find_track_for_seo(path: str):
    """Resolve /music/:artistSlug/:trackSlug or /music/:id to a track record."""
    parts = path.strip().strip('/').split('/')
    if len(parts) < 2 or parts[0] != 'music':
        return None
    try:
        tracks = get_all_tracks(ttl=600).get('tracks') or []
        if len(parts) == 2:
            track_id = parts[1]
            for t in tracks:
                if str(t.get('id') or t.get('track_id') or '') == track_id:
                    return t
        elif len(parts) >= 3:
            artist_slug, track_slug = parts[1], parts[2]
            for t in tracks:
                if (str(t.get('artist_slug') or '') == artist_slug
                        and _seo_slugify(t.get('title') or '') == track_slug):
                    return t
    except Exception:
        pass
    return None


def _load_whats_new_for_seo():
    try:
        data = get_all_whats_new(ttl=0)
        if isinstance(data, dict) and data.get('updates'):
            return data
    except Exception:
        pass
    return {}


def _find_whats_new_for_seo(path: str):
    """Resolve /whats-new/:year/:month/:section/:slug to the backing update item."""
    parts = path.strip().strip('/').split('/')
    if len(parts) < 5 or parts[0] != 'whats-new':
        return None

    year, month, section, slug = parts[1], parts[2], parts[3], parts[4]
    raw_data = _load_whats_new_for_seo()
    updates = raw_data.get('updates') or {}
    year_data = updates.get(year) or {}
    month_data = year_data.get(str(month).lower()) or {}
    section_data = month_data.get(section) or {}
    items = section_data.get('items') or []

    def _whats_new_slugify(text: str) -> str:
        s = (text or '').strip().lower()
        s = re.sub(r'[^a-z0-9]+', '-', s)
        return re.sub(r'-{2,}', '-', s).strip('-') or 'update'

    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            continue
        item_slug = item.get('slug') or _whats_new_slugify(f"{item.get('title', '')}-{item.get('date', '')}")
        if item_slug == slug:
            copy = item.copy()
            copy['year'] = year
            copy['month'] = month
            copy['section'] = section
            copy['slug'] = item_slug
            copy['month_path'] = f"/whats-new/{year}/{month}"
            copy['detail_path'] = f"/whats-new/{year}/{month}/{section}/{item_slug}"
            return copy

    return None


def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

    # Fast & flexible: accept both "/route" and "/route/" everywhere.
    # This prevents redirect surprises and keeps dev UX smooth.
    app.url_map.strict_slashes = False

    app.config.from_object(get_config())
    
    # Initialize structured logging
    init_logging()

    # minimal config safe for CI
    app.config.setdefault("JSON_SORT_KEYS", False)
    
    # If you use Flask-Limiter, this avoids scary warnings in CI logs.
    if os.getenv("CI"):
        app.config.setdefault("RATELIMIT_STORAGE_URI", "memory://")

    # SECRET_KEY is loaded from config.py (which enforces production requirement)
    # No need to override here - config.py handles it properly
    # Initialize server-side sessions (filesystem by default per config)
    if FlaskSession is not None:
        FlaskSession(app)
        st = (app.config.get("SESSION_TYPE") or "").lower()
        if st == "redis":
            app.logger.info("Redis sessions enabled")
        elif st == "filesystem":
            app.logger.info("Filesystem sessions enabled")
        elif st:
            app.logger.info("%s sessions enabled", st)
    else:
        print("WARN: Flask noted Flask-Session not available; using client-side cookies only. Activate venv or install Flask-Session.")
    bcrypt.init_app(app)
    login_manager.init_app(app)
    limiter.init_app(app)
    init_cors(app)
    compress.init_app(app)
    login_manager.login_view = "auth_page"

    @login_manager.unauthorized_handler
    def api_unauthorized():
        """Return 401 JSON only for /api/* requests; redirect all other (e.g. /admin) to login."""
        from flask import request
        if request.path.startswith("/api/"):
            return jsonify({"error": "not_authenticated"}), 401
        from flask import redirect, url_for
        return redirect(url_for("auth_page", next=request.url))

    # Initialize observability
    init_sentry(app)
    init_posthog(app)
    validate_posthog_environment(app)
    
    # Initialize request logging
    init_request_logging(app)
    
    # Initialize security headers
    attach_security_headers(app)

    # Register CSP report blueprint
    app.register_blueprint(create_csp_report_blueprint())
    
    # Initialize CSRF protection
    csrf = init_csrf(app)
    
    # Log startup configuration
    startup_logging(app)
    
    # Register blueprints
    # Removed: blueprints/auth.py (consolidated into api/auth)
    from blueprints.api.playlists import bp as api_playlists_bp
    from blueprints.api.bookmarks import bp as api_bookmarks_bp
    from blueprints.api.tips import bp as api_tips_bp
    from blueprints.api.feedback import bp as api_feedback_bp
    
    app.register_blueprint(api_auth_bp)  # Session-based API auth
    csrf.exempt(api_auth_bp) # Exempt from CSRF for SPA JSON requests
    app.register_blueprint(api_playlists_bp)  # Database-based playlists API (takes precedence)
    csrf.exempt(api_playlists_bp)  # SPA posts JSON without CSRF tokens
    app.register_blueprint(api_bookmarks_bp)  # Database-based bookmarks API (takes precedence)
    app.register_blueprint(api_tips_bp)  # Tips/boost API
    app.register_blueprint(api_feedback_bp)  # Feedback API
    app.register_blueprint(gamification_bp)  # Gamification API (XP, badges, leaderboard)
    app.register_blueprint(activity_bp)
    # Removed: playlists_bp and bookmarks_bp - shadowed by API blueprints, never reached
    # Use blueprints/api/playlists.py and blueprints/api/bookmarks.py instead
    # Removed: collections_bp (feature removed)
    # Removed: gamify_api_bp (feature removed)
    app.register_blueprint(payments_bp)
    app.register_blueprint(boost_stripe_bp)
    app.register_blueprint(boost_api_bp)
    app.register_blueprint(stripe_webhooks_bp)
    # Stripe posts webhooks without CSRF tokens — exempt the whole blueprint
    csrf.exempt(stripe_webhooks_bp)
    # SPA posts JSON to boost endpoints without CSRF tokens — exempt
    csrf.exempt(boost_stripe_bp)
    csrf.exempt(boost_api_bp)
    csrf.exempt(payments_bp)
    
    from blueprints.admin import bp as admin_bp
    app.register_blueprint(admin_bp)
    from blueprints.admin import track_event
    csrf.exempt(track_event)
    
    # Initialize search index
    with app.app_context():
        initialize_search_index()
        _bootstrap_admin_user_from_env()
        _hide_podcast_shows(['found-cassettes', 'g-dub-disc-golf'])


    # Register Click CLI commands
    # Removed: gamify CLI commands (feature removed)

    # Health check endpoint
    @app.get("/healthz")
    def healthz():
        from ahoy.version import __version__
        return jsonify({"ok": True, "version": __version__}), 200

    @app.get("/api/config/stripe")
    def get_stripe_config():
        """Expose only the publishable key for Stripe Elements in the SPA."""
        key = (
            app.config.get("STRIPE_PUBLISHABLE_KEY") or 
            os.getenv("STRIPE_PUBLISHABLE_KEY") or 
            os.getenv("STRIPE_PUBLISHABLE_KEY_TEST") or
            app.config.get("STRIPE_PUBLISHABLE_KEY_TEST")
        )
        return jsonify({"publishable_key": key}), 200

    # Readiness check that actually verifies DB connectivity
    @app.get("/readyz")
    def readyz():
        try:
            from db import get_session
            from sqlalchemy import text
            with get_session() as session:
                session.execute(text("SELECT 1"))
            return jsonify({"status": "ready"}), 200
        except Exception as e:
            app.logger.exception("readyz DB check failed")
            return jsonify({"status": "error"}), 500

    # Debug endpoints for payment and checkout systems
    @app.route('/ops/debug/payments', methods=['GET'])
    @_admin_session_required
    def debug_payments():
        """Debug endpoint for payment system status - use this to check Stripe/wallet configuration"""
        from flask_login import current_user
        from db import get_session
        from models import User, WalletTransaction, Purchase, Tip
        import stripe
        from datetime import datetime
        
        debug_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "stripe": {},
            "database": {},
            "user": {},
            "errors": []
        }
        
        # Check Stripe configuration
        try:
            # Check multiple sources for Stripe keys (config object, env vars, direct env)
            stripe_key = (
                app.config.get("STRIPE_SECRET_KEY") or 
                os.getenv("STRIPE_SECRET_KEY") or 
                os.getenv("STRIPE_SECRET_KEY_TEST") or
                app.config.get("STRIPE_SECRET_KEY_TEST")
            )
            
            webhook_secret = (
                app.config.get("STRIPE_WEBHOOK_SECRET") or 
                os.getenv("STRIPE_WEBHOOK_SECRET") or 
                os.getenv("STRIPE_WEBHOOK_SECRET_TEST") or
                app.config.get("STRIPE_WEBHOOK_SECRET_TEST")
            )
            
            publishable_key = (
                app.config.get("STRIPE_PUBLISHABLE_KEY") or 
                os.getenv("STRIPE_PUBLISHABLE_KEY") or 
                os.getenv("STRIPE_PUBLISHABLE_KEY_TEST") or
                app.config.get("STRIPE_PUBLISHABLE_KEY_TEST")
            )
            
            debug_info["stripe"]["configured"] = bool(stripe_key)
            debug_info["stripe"]["key_prefix"] = stripe_key[:7] + "..." if stripe_key else None
            debug_info["stripe"]["webhook_secret_set"] = bool(webhook_secret)
            debug_info["stripe"]["webhook_secret_prefix"] = webhook_secret[:7] + "..." if webhook_secret else None
            debug_info["stripe"]["publishable_key_set"] = bool(publishable_key)
            debug_info["stripe"]["ahoy_env"] = os.getenv("AHOY_ENV", "not_set")
            
            # Test Stripe API connection
            if stripe_key:
                try:
                    stripe.api_key = stripe_key
                    # Try to list customers (lightweight operation)
                    customers = stripe.Customer.list(limit=1)
                    debug_info["stripe"]["api_connection"] = "ok"
                    debug_info["stripe"]["api_version"] = stripe.api_version if hasattr(stripe, 'api_version') else "unknown"
                except Exception as e:
                    debug_info["stripe"]["api_connection"] = "error"
                    debug_info["stripe"]["api_error"] = str(e)
                    debug_info["errors"].append(f"Stripe API error: {e}")
            else:
                debug_info["stripe"]["api_connection"] = "not_configured"
                # Only add to errors if we're in production
                if os.getenv("AHOY_ENV") == "production":
                    debug_info["errors"].append("Stripe secret key not configured - check Render environment variables")
        except Exception as e:
            debug_info["stripe"]["error"] = str(e)
            debug_info["errors"].append(f"Stripe check error: {e}")
        
        # Check database connectivity and wallet tables
        try:
            with get_session() as s:
                # Check if wallet_balance column exists
                from sqlalchemy import inspect
                inspector = inspect(s.bind)
                users_columns = [col['name'] for col in inspector.get_columns('users')]
                debug_info["database"]["wallet_balance_column"] = 'wallet_balance' in users_columns
                
                # Check if wallet_transactions table exists
                tables = inspector.get_table_names()
                debug_info["database"]["wallet_transactions_table"] = 'wallet_transactions' in tables
                
                # Get counts (handle errors gracefully)
                user_count = s.query(User).count()
                wallet_tx_count = s.query(WalletTransaction).count() if 'wallet_transactions' in tables else 0
                purchase_count = s.query(Purchase).count()
                
                # Tip count may fail if schema is outdated
                try:
                    tip_count = s.query(Tip).count()
                except Exception as tip_error:
                    tip_count = None
                    debug_info["database"]["tip_count_error"] = str(tip_error)
                
                debug_info["database"]["counts"] = {
                    "users": user_count,
                    "wallet_transactions": wallet_tx_count,
                    "purchases": purchase_count,
                    "tips": tip_count
                }
                
                # Check current user's wallet if logged in
                if current_user.is_authenticated:
                    user = s.query(User).filter(User.id == current_user.id).first()
                    if user:
                        debug_info["user"]["logged_in"] = True
                        debug_info["user"]["user_id"] = user.id
                        debug_info["user"]["wallet_balance"] = float(user.wallet_balance or 0)
                        debug_info["user"]["stripe_customer_id"] = user.stripe_customer_id or None
                        
                        # Get recent wallet transactions
                        if 'wallet_transactions' in tables:
                            recent_tx = s.query(WalletTransaction).filter(
                                WalletTransaction.user_id == user.id
                            ).order_by(WalletTransaction.created_at.desc()).limit(5).all()
                            debug_info["user"]["recent_transactions"] = [
                                {
                                    "type": tx.type,
                                    "amount": float(tx.amount),
                                    "balance_after": float(tx.balance_after),
                                    "description": tx.description,
                                    "created_at": tx.created_at.isoformat()
                                } for tx in recent_tx
                            ]
                else:
                    debug_info["user"]["logged_in"] = False
        except Exception as e:
            debug_info["database"]["error"] = str(e)
            debug_info["errors"].append(f"Database error: {e}")
        
        # Overall status
        debug_info["status"] = "ok" if len(debug_info["errors"]) == 0 else "errors"
        
        return jsonify(debug_info), 200 if debug_info["status"] == "ok" else 500

    @app.route('/ops/debug/checkout', methods=['GET'])
    @_admin_session_required
    def debug_checkout():
        """Debug endpoint for checkout system - checks merch catalog"""
        from storage import read_json
        from datetime import datetime
        
        debug_info = {
            "timestamp": datetime.utcnow().isoformat(),
            "merch_catalog": {},
            "errors": []
        }
        
        # Check merch catalog (DB first, then JSON fallback)
        try:
            try:
                merch_catalog = get_all_merch(ttl=600)
            except Exception:
                merch_catalog = read_json("data/merch.json", {"items": []})
            if isinstance(merch_catalog, dict):
                items = merch_catalog.get("items", [])
                debug_info["merch_catalog"]["exists"] = True
                debug_info["merch_catalog"]["item_count"] = len(items) if isinstance(items, list) else 0
                debug_info["merch_catalog"]["items"] = [
                    {
                        "id": item.get("id"),
                        "name": item.get("name"),
                        "price_usd": item.get("price_usd"),
                        "available": item.get("available", True)
                    } for item in (items[:10] if isinstance(items, list) else [])  # First 10 items
                ]
            else:
                debug_info["merch_catalog"]["exists"] = False
                debug_info["errors"].append("Merch catalog is not a valid dictionary")
        except FileNotFoundError:
            debug_info["merch_catalog"]["exists"] = False
            debug_info["errors"].append("Merch catalog (DB and file) not available")
        except Exception as e:
            debug_info["merch_catalog"]["error"] = str(e)
            debug_info["errors"].append(f"Error reading merch catalog: {e}")
        
        debug_info["status"] = "ok" if len(debug_info["errors"]) == 0 else "errors"
        
        return jsonify(debug_info), 200 if debug_info["status"] == "ok" else 500

    @app.route('/ops/status/api', methods=['GET'])
    def status_api():
        """API endpoint for status checks - returns JSON with all status information"""
        from datetime import datetime
        from ahoy.version import __version__
        from db import get_session
        from sqlalchemy import text
        
        status = {
            "timestamp": datetime.utcnow().isoformat(),
            "server": {
                "running": True,  # If we're here, server is running
                "version": __version__,
                "ok": True
            },
            "database": {},
            "webhook_listener": {},
            "next_steps": []
        }
        
        # Check database connectivity
        try:
            with get_session() as s:
                s.execute(text("SELECT 1"))
                status["database"]["connected"] = True
        except Exception as e:
            status["database"]["connected"] = False
            status["database"]["error"] = str(e)
            status["next_steps"].append("Check database connection")
        
        # Webhook listener status (we can't directly check if CLI is running, but provide instructions)
        status["webhook_listener"]["instructions"] = "Run: ./scripts/start_stripe_listen.sh"
        status["webhook_listener"]["check_terminal"] = "Look for 'Ready! Your webhook signing secret is whsec_...'"
        status["webhook_listener"]["note"] = "Cannot auto-detect if Stripe CLI listener is running - check your terminal"
        
        # Next steps
        status["next_steps"] = [
            "Open webhook monitor: /ops/webhooks/monitor",
            "Test webhook: ./scripts/test_wallet_funding.sh",
            "Check debug endpoints: /ops/debug/payments"
        ]
        
        return jsonify(status), 200
    
    @app.route('/ops/webhooks/monitor', methods=['GET'])
    @_owner_session_required
    def webhook_monitor():
        """Simple webhook monitoring page - shows recent webhook events"""
        from db import get_session
        from models import WalletTransaction, Purchase, Tip
        from datetime import datetime
        
        monitor_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "recent_transactions": [],
            "recent_purchases": [],
            "recent_tips": [],
            "status": "ok"
        }
        
        try:
            with get_session() as s:
                # Get recent wallet transactions (last 10)
                recent_tx = s.query(WalletTransaction).order_by(
                    WalletTransaction.created_at.desc()
                ).limit(10).all()
                
                monitor_data["recent_transactions"] = [
                    {
                        "id": tx.id,
                        "user_id": tx.user_id,
                        "type": tx.type,
                        "amount": float(tx.amount),
                        "balance_after": float(tx.balance_after),
                        "description": tx.description,
                        "reference_id": tx.reference_id,
                        "created_at": tx.created_at.isoformat() if tx.created_at else None
                    } for tx in recent_tx
                ]
                
                # Get recent purchases (last 10)
                recent_purchases = s.query(Purchase).order_by(
                    Purchase.created_at.desc()
                ).limit(10).all()
                
                monitor_data["recent_purchases"] = [
                    {
                        "id": p.id,
                        "type": p.type,
                        "status": p.status,
                        "amount": float(p.amount) if p.amount else 0,
                        "total": float(p.total) if p.total else 0,
                        "stripe_id": p.stripe_id,
                        "created_at": p.created_at.isoformat() if p.created_at else None
                    } for p in recent_purchases
                ]
                
                # Get recent tips (last 10)
                recent_tips = s.query(Tip).order_by(
                    Tip.created_at.desc()
                ).limit(10).all()
                
                monitor_data["recent_tips"] = [
                    {
                        "id": t.id,
                        "artist_id": t.artist_id,
                        "amount": float(t.amount) if t.amount else 0,
                        "artist_payout": float(t.artist_payout) if t.artist_payout else 0,
                        "stripe_id": t.stripe_id,
                        "created_at": t.created_at.isoformat() if t.created_at else None
                    } for t in recent_tips
                ]
        except Exception as e:
            monitor_data["status"] = "error"
            monitor_data["error"] = str(e)
        
        return render_template('ops/webhook_monitor.html', data=monitor_data)

    @app.route('/ops/stats', methods=['GET'])
    @_owner_session_required
    def ops_stats():
        from services.analytics_snapshot import build_analytics_snapshot

        snapshot = build_analytics_snapshot(days=30, top_limit=10)
        posthog_sync = build_posthog_sync_status(app=current_app)
        return render_template('ops/stats.html', snapshot=snapshot, posthog_sync=posthog_sync, owner_email=_owner_email())

    # Operational self-test endpoint
    @app.get("/ops/selftest")
    def ops_selftest():
        try:
            from db import get_session
            from sqlalchemy import text
            from models import User
            from alembic.runtime.migration import MigrationContext

            with get_session() as session:
                # 1) Basic connectivity
                session.execute(text("SELECT 1"))

                # 2) ORM query
                users_count = session.query(User).count()

                # 3) Alembic current revision in DB
                connection = session.connection()
                context = MigrationContext.configure(connection)
                current_rev = context.get_current_revision()

            return jsonify({
                "ready": True,
                "alembic": current_rev or "unknown",
                "counts": {"users": int(users_count)}
            }), 200
        except Exception as e:
            return jsonify({
                "ready": False,
                "detail": str(e)
            }), 500

    # Sentry test route (production only)
    @app.get("/_boom")
    def sentry_test():
        """Test route for Sentry error tracking - only works in production"""
        import os
        if os.getenv("FLASK_ENV") == "production" or os.getenv("SENTRY_TEST_ROUTE") == "true":
            raise Exception("Sentry test exception - this is intentional")
        return jsonify({"error": "Not found"}), 404

    # Context processor to inject login flag into templates
    @app.context_processor
    def inject_login_flag():
        from flask_login import current_user
        return {"LOGGED_IN": current_user.is_authenticated}

    # Expose Stripe publishable key in templates
    @app.context_processor
    def inject_stripe_publishable_key():
        try:
            key = app.config.get("STRIPE_PUBLISHABLE_KEY", "")
        except Exception:
            key = ""
        return {"STRIPE_PUBLISHABLE_KEY": key}

    # Inject git commit hash for CSS cache busting
    @app.context_processor
    def inject_git_commit_hash():
        import subprocess
        try:
            commit_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'], cwd=os.path.dirname(__file__)).decode().strip()
        except Exception:
            commit_hash = 'local'
        return {"GIT_COMMIT_HASH": commit_hash}

    @app.context_processor
    def inject_owner_email():
        return {"AHOY_OWNER_EMAIL": _owner_email()}

    # Enable compression (configured at module level)
    # Downloads routes
    DOWNLOADS_DIR = Path("downloads")
    DIST_DIR = Path("dist")

    @app.route('/downloads/<path:filename>')
    def download_artifact(filename):
        """Serve built desktop artifacts from downloads/ directory."""
        if not DOWNLOADS_DIR.exists():
            return jsonify({'error': 'No downloads available'}), 404
        try:
            return send_from_directory(str(DOWNLOADS_DIR), filename, as_attachment=True)
        except Exception:
            return jsonify({'error': 'File not found'}), 404
    
    @app.route('/downloads/dist/<path:filename>')
    def download_dist_artifact(filename):
        """Serve built desktop artifacts from dist/ directory."""
        if not DIST_DIR.exists():
            return jsonify({'error': 'No builds available'}), 404
        try:
            return send_from_directory(str(DIST_DIR), filename, as_attachment=True)
        except Exception:
            return jsonify({'error': 'File not found'}), 404

    @app.route('/api/downloads/latest')
    def api_downloads_latest():
        """Return latest macOS release zip for Settings / downloads table (version, date, download link)."""
        import requests as requests_lib
        repo_owner = "oooAHOYooo"
        repo_name = "ahoy-little-platform"
        github_token = os.getenv('GITHUB_TOKEN')
        headers = {}
        if github_token:
            headers['Authorization'] = f'token {github_token}'
        try:
            url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
            response = requests_lib.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return jsonify({'error': 'No release found'}), 404
            data = response.json()
            version = data.get('tag_name', '').lstrip('v')
            published = data.get('published_at') or data.get('created_at') or ''
            # Prefer macOS zip: *-mac.zip or *arm64*.zip (arm64 first), then any .zip for mac
            assets = data.get('assets', [])
            mac_zip = None
            for a in assets:
                name = (a.get('name') or '').lower()
                if not name.endswith('.zip') or '.blockmap' in name:
                    continue
                if 'mac' in name or 'arm64' in name or 'darwin' in name:
                    mac_zip = a
                    if 'arm64' in name:
                        break
            if not mac_zip and assets:
                for a in assets:
                    if (a.get('name') or '').lower().endswith('.zip') and '.blockmap' not in (a.get('name') or ''):
                        mac_zip = a
                        break
            if not mac_zip:
                return jsonify({'error': 'No macOS zip in latest release'}), 404
            return jsonify({
                'version': version,
                'date': published[:10] if published else '',
                'download_url': mac_zip.get('browser_download_url'),
                'name': mac_zip.get('name'),
            })
        except Exception as e:
            print(f"Error in /api/downloads/latest: {e}")
            return jsonify({'error': 'Could not fetch latest release'}), 500

    @app.route('/offline')
    def offline():
        """Offline fallback page served by service worker when network is unavailable."""
        return render_template('offline.html')

    @app.route('/refresh')
    def refresh():
        """Escape hatch: clear SW + caches and redirect to /. Use when app won't update or scroll on mobile."""
        html = '''<!DOCTYPE html><html><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Refreshing…</title></head><body><p>Clearing cache and redirecting…</p>
<script>
(function(){
  if (window.caches && caches.keys) { caches.keys().then(function(n){ n.forEach(function(k){ caches.delete(k); }); }); }
  if (navigator.serviceWorker && navigator.serviceWorker.getRegistrations) {
    navigator.serviceWorker.getRegistrations().then(function(r){ r.forEach(function(reg){ reg.unregister(); }); });
  }
  window.location.replace('/?' + Date.now());
})();
</script></body></html>'''
        r = make_response(html)
        r.headers['Content-Type'] = 'text/html; charset=utf-8'
        r.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
        r.headers['Pragma'] = 'no-cache'
        r.headers['Expires'] = '0'
        return r

    # When spa-dist exists, serve SPA for all document GETs (Vue is the main web UI).
    _spa_dist_dir = Path(__file__).resolve().parent / "spa-dist"
    _server_path_prefixes = (
        "api/", "static/", "assets/", "payments/", "checkout", "success", "healthz", "readyz",
        "refresh", "robots.txt", "favicon.ico", "manifest.webmanifest",
        "googleb3a3eb3401de50dc.html",
    )

    @app.before_request
    def _maybe_serve_spa():
        if request.method != "GET":
            return
        if not _spa_dist_dir.exists() or not (_spa_dist_dir / "index.html").is_file():
            return
        path = (request.path or "").strip().strip("/")
        if any(path.startswith(p) or path == p.rstrip("/") for p in _server_path_prefixes):
            return
        if path.startswith("videos/"):
            show = _find_video_for_seo(request.path)
            if show:
                return _render_spa_with_video_meta(show, request.path)
        if path.startswith("artists/"):
            artist = _find_artist_for_seo(path)
            if artist:
                name = str(artist.get('name') or 'Artist').strip()
                bio = str(artist.get('bio') or f'Listen to {name} on Ahoy Indie Media.').strip()
                image = _absolute_url(artist.get('image') or '/static/img/ahoy_logo.png')
                return _render_spa_with_meta(name, bio, image, 'profile', request.path)
        if path.startswith("podcasts/"):
            podcast = _find_podcast_for_seo(path)
            if podcast:
                title = str(podcast.get('title') or 'Podcast').strip()
                description = str(podcast.get('description') or f'Listen to {title} on Ahoy Indie Media.').strip()
                image = _absolute_url(podcast.get('artwork') or '/static/img/ahoy_logo.png')
                return _render_spa_with_meta(title, description, image, 'website', request.path)
        if path.startswith("events/"):
            event = _find_event_for_seo(path)
            if event:
                title = str(event.get('title') or 'Event').strip()
                description = str(event.get('description') or f'{title} on Ahoy Indie Media.').strip()
                image = _absolute_url(event.get('image') or '/static/img/ahoy_logo.png')
                return _render_spa_with_meta(title, description, image, 'website', request.path)
        if path.startswith("whats-new/"):
            update = _find_whats_new_for_seo(path)
            if update:
                title = str(update.get('title') or "What's New").strip()
                description = str(update.get('body') or update.get('description') or f'{title} on Ahoy Indie Media.').strip()
                related_videos = update.get('related_videos') if isinstance(update.get('related_videos'), list) else []
                first_related = related_videos[0] if related_videos and isinstance(related_videos[0], dict) else {}
                image = _absolute_url(
                    update.get('thumbnail')
                    or first_related.get('thumbnail')
                    or '/static/img/ahoy_logo.png'
                )
                return _render_spa_with_meta(title, description, image, 'article', request.path)
        if path.startswith("music/"):
            track = _find_track_for_seo(path)
            if track:
                title = str(track.get('title') or 'Track').strip()
                artist = str(track.get('artist') or '').strip()
                description = f'{title} by {artist} — listen on Ahoy Indie Media.' if artist else f'Listen to {title} on Ahoy Indie Media.'
                image = _absolute_url(track.get('cover_art') or '/static/img/ahoy_logo.png')
                return _render_spa_with_meta(title, description, image, 'music.song', request.path)
        return _spa_index_response()

    return app

# Create the app instance for backward compatibility
app = create_app()
# ==== Forgiving Artist API (slug or case-insensitive name) ==================
ARTISTS_PATH = Path("static/data/artists.json")

def _slugify(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (s or "").strip().lower()).strip("-")

def _load_artists_flat():
    try:
        artists = get_artists_list(ttl=600)
        if artists:
            return artists
    except Exception:
        pass
    try:
        data = load_json_data('artists.json', {'artists': []})
        return data.get('artists', [])
    except Exception:
        return []

@app.get("/api/artist/<slug_or_name>")
def api_artist(slug_or_name):
    key = (slug_or_name or "").strip().lower()
    artists = _load_artists_flat()
    # slug match
    for a in artists:
        if _slugify(a.get("slug") or a.get("name", "")) == key:
            r = jsonify(a)
            r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return r
    # case-insensitive name match
    for a in artists:
        if (a.get("name", "").strip().lower()) == key:
            r = jsonify(a)
            r.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            return r
    return jsonify({"error": "not_found"}), 404
# ===========================================================================
# ==== JSON Sitemap: GET /api/_sitemap =======================================
from urllib.parse import unquote, quote
from flask import jsonify

def _generate_sitemap(flask_app):
    def is_method(m): return m in ("GET","POST","PUT","PATCH","DELETE")
    routes, seen = [], {}
    for rule in flask_app.url_map.iter_rules():
        if rule.endpoint == "static":  # skip static
            continue
        methods = tuple(sorted([m for m in rule.methods if is_method(m)]))
        info = {
            "rule": unquote(str(rule)),
            "endpoint": rule.endpoint,
            "methods": list(methods),
            "blueprint": rule.endpoint.split(".", 1)[0] if "." in rule.endpoint else None,
        }
        routes.append(info)
        seen.setdefault((info["rule"], methods), []).append(info["endpoint"])

    duplicates = [
        {"rule": r, "methods": list(m), "endpoints": eps}
        for (r, m), eps in seen.items() if len(eps) > 1
    ]
    routes.sort(key=lambda r: (r["rule"], r["methods"]))
    return {"routes": routes, "duplicates": duplicates}

# PWA Emergency Hatch: /refresh
@app.route('/refresh')
def pwa_refresh():
    """Nuclear option to clear caches and refresh the app."""
    response = make_response(render_template_string("""
        <!DOCTYPE html>
        <html>
        <head><title>Refreshing Ahoy...</title></head>
        <body style="background:#0e0e10; color:#fff; font-family:sans-serif; text-align:center; padding:50px;">
            <h2>⚓ Refreshing Ahoy...</h2>
            <p>Clearing legacy caches and updating to latest version.</p>
            <script>
                (async function() {
                    // Clear all caches
                    if ('caches' in window) {
                        const keys = await caches.keys();
                        for (let key of keys) await caches.delete(key);
                    }
                    // Unregister service workers
                    if ('serviceWorker' in navigator) {
                        const registrations = await navigator.serviceWorker.getRegistrations();
                        for (let r of registrations) await r.unregister();
                    }
                    // Clear localStorage API cache
                    try { localStorage.clear(); } catch(e) {}
                    // Redirect to home with cache buster
                    window.location.href = '/?refresh=' + Date.now();
                })();
            </script>
        </body>
        </html>
    """))
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    response.headers["Clear-Site-Data"] = '"cache", "storage", "executionContexts"'
    return response

# Global Error Handling for SPA Stability
@app.errorhandler(500)
def handle_500_error(e):
    app.logger.error(f"Server Error: {e}")
    if request.path.startswith('/api/') or request.headers.get('Accept') == 'application/json':
        return jsonify({"error": "server_error", "message": "The crew is working on it. Please try again soon."}), 500
    return render_template('base.html'), 500 # Fall back to SPA skeleton

@app.get("/api/_sitemap")
def api_sitemap():
    return jsonify(_generate_sitemap(app))
# ============================================================================


def render_checkout_template(**context):
    """Render checkout template with safe defaults across error paths."""
    context.setdefault('kind', 'boost')
    context.setdefault('artist_id', '')
    context.setdefault('amount', '')
    context.setdefault('item_id', '')
    context.setdefault('qty', 1)
    context.setdefault('title', '')
    context.setdefault('stripe_fee', None)
    context.setdefault('platform_fee', None)
    context.setdefault('total', None)
    context.setdefault('wallet_balance', None)
    return render_template('sawdust/checkout.html', **context)

@app.route('/checkout')
def checkout_page():
    """
    Universal checkout entrypoint (GET)
    Accepts query params:
      type, artist_id, amount, item_id, qty, title
    Renders a CSRF-protected form that POSTS to /checkout/process
    """
    from decimal import Decimal
    from utils.csrf import generate_csrf_token
    from blueprints.payments import calculate_boost_fees
    q = request.args
    kind = (q.get('type') or 'boost').strip()
    artist_id = q.get('artist_id') or ''
    amount = q.get('amount') or ''
    title = q.get('title') or ''
    item_id = q.get('item_id') or ''
    qty = int(q.get('qty') or '1')

    stripe_fee = platform_fee = total = None
    try:
        amt = Decimal(str(amount or '0'))
        if kind in ['boost', 'tip'] and amt > 0:
            stripe_fee, platform_fee, total, _, _ = calculate_boost_fees(amt)
        else:
            total = amt
    except Exception:
        total = None

    # For merch, ignore client-provided amount/title and look up from merch catalog.
    if kind == "merch" and item_id:
        try:
            try:
                merch_catalog = get_all_merch(ttl=600)
            except Exception:
                from storage import read_json
                merch_catalog = read_json("data/merch.json", {"items": []}) or {}
            items = merch_catalog.get("items") if isinstance(merch_catalog, dict) else []
            found = None
            if isinstance(items, list):
                for it in items:
                    if isinstance(it, dict) and str(it.get("id") or "") == str(item_id):
                        found = it
                        break
            if found:
                # Check if item has already been purchased (1:1 nature - only one in stock)
                try:
                    with get_session() as s:
                        existing_purchase = s.query(Purchase).filter(
                            Purchase.type == "merch",
                            Purchase.item_id == str(item_id)
                        ).first()
                        if existing_purchase:
                            return render_checkout_template(
                                                   error="This item has already been purchased and is no longer available.",
                                                   kind=kind,
                                                   item_id=item_id,
                                                   qty=qty,
                                                   csrf_token=generate_csrf_token()), 400
                except Exception as e:
                    current_app.logger.warning(f"Error checking for existing purchase: {e}")
                    # Continue with checkout if we can't check (fail open for availability)
                
                # Respect item availability flags if present.
                if found.get("available") is False:
                    return render_checkout_template(
                                           error="This item is not available.",
                                           kind=kind,
                                           item_id=item_id,
                                           qty=qty,
                                           csrf_token=generate_csrf_token()), 400
                unit = Decimal(str(found.get("price_usd") or "0")).quantize(Decimal("0.01"))
                if unit <= 0:
                    return render_checkout_template(
                                           error="Invalid item price.",
                                           kind=kind,
                                           item_id=item_id,
                                           qty=qty,
                                           csrf_token=generate_csrf_token()), 400
                amount = str(unit)  # unit price
                title = str(found.get("name") or "Merch")[:120]
                total = (unit * Decimal(str(max(1, qty)))).quantize(Decimal("0.01"))
            else:
                # Item not found in catalog
                current_app.logger.warning(f"Merch item not found: {item_id}")
                return render_checkout_template(
                                       error=f"Merch item '{item_id}' not found in catalog.",
                                       kind=kind,
                                       item_id=item_id,
                                       qty=qty,
                                       csrf_token=generate_csrf_token()), 404
        except Exception as e:
            current_app.logger.error(f"Error loading merch catalog: {e}", exc_info=True)
            return render_checkout_template(
                                   error="Unable to load merch catalog. Please try again later.",
                                   kind=kind,
                                   item_id=item_id,
                                   qty=qty,
                                   csrf_token=generate_csrf_token()), 500

    # Get wallet balance if user is logged in
    wallet_balance = None
    try:
        from flask_login import current_user
        from models import User
        if current_user.is_authenticated:
            with get_session() as s:
                user = s.query(User).filter(User.id == current_user.id).first()
                if user:
                    wallet_balance = float(user.wallet_balance or 0)
    except Exception:
        pass

    return render_checkout_template(
        kind=kind,
        artist_id=artist_id,
        amount=amount,
        item_id=item_id,
        qty=qty,
        title=title,
        stripe_fee=float(stripe_fee) if stripe_fee is not None else None,
        platform_fee=float(platform_fee) if platform_fee is not None else None,
        total=float(total) if total is not None else None,
        wallet_balance=wallet_balance,
        csrf_token=generate_csrf_token(),
    )


@app.route('/checkout/process', methods=['POST'])
def checkout_process():
    """
    Universal checkout processor (POST)
    Validates CSRF, records a Purchase, and (optionally) creates Stripe PI.
    Note: This route uses custom CSRF validation, not Flask-WTF's automatic validation.
    """
    from utils.csrf import validate_csrf, generate_csrf_token, CSRF_SESSION_KEY
    import structlog
    logger = structlog.get_logger()
    
    # Debug CSRF validation - log everything
    sent_token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    session_token = session.get(CSRF_SESSION_KEY)
    
    # Log all form data for debugging
    logger.info("CSRF validation attempt",
                sent_token_present=bool(sent_token),
                sent_token_preview=sent_token[:20] + "..." if sent_token and len(sent_token) > 20 else sent_token,
                session_token_present=bool(session_token),
                session_token_preview=str(session_token)[:20] + "..." if session_token and len(str(session_token)) > 20 else str(session_token),
                form_keys=list(request.form.keys()),
                session_keys=list(session.keys()) if session else [])
    
    # Check if session is working
    if not session_token:
        logger.error("No CSRF token in session! Session might not be persisting.")
        # Generate a new token and try again
        new_token = generate_csrf_token()
        logger.info("Generated new CSRF token", token_preview=new_token[:20] + "...")
        return render_checkout_template( 
                             error="Session expired. Please try again.", 
                             csrf_token=new_token,
                             kind=request.form.get('type', 'boost'),
                             artist_id=request.form.get('artist_id', ''),
                             amount=request.form.get('amount', ''),
                             item_id=request.form.get('item_id', ''),
                             qty=int(request.form.get('qty', '1'))), 400
    
    if not validate_csrf():
        logger.warning("CSRF validation failed",
                      sent_token_present=bool(sent_token),
                      session_token_present=bool(session_token),
                      tokens_match=(sent_token == str(session_token)) if (sent_token and session_token) else False)
        # Re-render checkout with a new token and error
        return render_checkout_template( 
                             error="Invalid CSRF token. Please refresh and try again.", 
                             csrf_token=generate_csrf_token(),
                             kind=request.form.get('type', 'boost'),
                             artist_id=request.form.get('artist_id', ''),
                             amount=request.form.get('amount', ''),
                             item_id=request.form.get('item_id', ''),
                             qty=int(request.form.get('qty', '1'))), 400

    form = request.form
    kind = (form.get('type') or 'boost').strip()
    artist_id = form.get('artist_id') or None
    item_id = form.get('item_id') or None
    qty = int(form.get('qty') or '1')
    use_wallet = form.get('use_wallet') == 'true'
    try:
        amount = float(form.get('amount') or '0')
    except Exception:
        amount = 0.0
    try:
        total = float(form.get('total') or form.get('computed_total') or amount)
    except Exception:
        total = amount

    # Read and validate ahoy_match (optional support contribution)
    ahoy_match = 0.0
    try:
        ahoy_match = float(form.get('ahoy_match') or '0')
        ahoy_match = max(0.0, min(ahoy_match, amount))  # Clamp to [0, boost_amount]
        ahoy_match = round(ahoy_match, 2)
    except Exception:
        ahoy_match = 0.0

    # Harden merch checkout: price/title must come from server-side merch catalog.
    if kind == "merch":
        try:
            try:
                merch_catalog = get_all_merch(ttl=600)
            except Exception:
                from storage import read_json
                merch_catalog = read_json("data/merch.json", {"items": []}) or {}
            items = merch_catalog.get("items") if isinstance(merch_catalog, dict) else []
            found = None
            if isinstance(items, list) and item_id:
                for it in items:
                    if isinstance(it, dict) and str(it.get("id") or "") == str(item_id):
                        found = it
                        break
            if not found:
                return render_checkout_template(
                                       error="Invalid merch item.",
                                       csrf_token=generate_csrf_token(),
                                       kind=kind,
                                       item_id=item_id or "",
                                       qty=max(1, qty)), 400
            
            # Check if item has already been purchased (1:1 nature - only one in stock)
            try:
                with get_session() as s:
                    existing_purchase = s.query(Purchase).filter(
                        Purchase.type == "merch",
                        Purchase.item_id == str(item_id)
                    ).first()
                    if existing_purchase:
                        return render_checkout_template(
                                               error="This item has already been purchased and is no longer available.",
                                               csrf_token=generate_csrf_token(),
                                               kind=kind,
                                               item_id=item_id or "",
                                               qty=max(1, qty)), 400
            except Exception as e:
                current_app.logger.warning(f"Error checking for existing purchase: {e}")
                # Continue with checkout if we can't check (fail open for availability)
            
            if found.get("available") is False:
                return render_checkout_template(
                                       error="This item is not available.",
                                       csrf_token=generate_csrf_token(),
                                       kind=kind,
                                       item_id=item_id or "",
                                       qty=max(1, qty)), 400

            # For one-of-a-kind merch items, enforce quantity = 1
            qty = 1
            unit = float(found.get("price_usd") or 0)
            if unit <= 0:
                return render_checkout_template(
                                       error="Invalid item price.",
                                       csrf_token=generate_csrf_token(),
                                       kind=kind,
                                       item_id=item_id or "",
                                       qty=qty), 400
            amount = float(unit)              # unit price (authoritative)
            total = float(unit * qty)         # total (authoritative) - always 1 for one-of-a-kind
        except Exception as e:
            current_app.logger.error(f"Error processing merch item {item_id}: {e}", exc_info=True)
            return render_checkout_template(
                                   error="Error processing merch item. Please try again.",
                                   csrf_token=generate_csrf_token(),
                                   kind=kind,
                                   item_id=item_id or "",
                                   qty=max(1, qty)), 500

    user_id = None
    try:
        user_id = session.get('user_id') or session.get('uid') or None
        if user_id:
            user_id = int(user_id)
    except Exception:
        user_id = None

    # Persist a pending purchase
    from db import get_session
    from models import Purchase
    purchase_id = None
    with get_session() as s:
        p = Purchase(
            type=kind,
            user_id=user_id,
            artist_id=str(artist_id) if artist_id else None,
            item_id=str(item_id) if item_id else None,
            qty=qty,
            amount=amount,
            total=total,
            status='pending',
        )
        s.add(p)
        s.flush()
        purchase_id = p.id
        s.commit()

    # Create a Stripe Checkout Session and redirect user to Stripe-hosted checkout
    try:
        import stripe
        from decimal import Decimal
        from blueprints.payments import calculate_boost_fees

        # Configure Stripe from config/env (prefer config)
        api_key = app.config.get("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY_TEST")
        stripe.api_key = api_key
        if not stripe.api_key:
            raise RuntimeError("Stripe not configured (missing STRIPE_SECRET_KEY)")

        # Compute authoritative totals for boost/tip (ignore client-provided totals)
        metadata = {
            "purchase_id": str(purchase_id),
            "type": str(kind),
            "user_id": str(user_id or ""),
            "artist_id": str(artist_id or ""),
            "item_id": str(item_id or ""),
            "qty": str(qty),
            "amount": str(amount),
            "total": str(total),
        }

        line_items = []
        if kind in ["boost", "tip"]:
            boost_amount_decimal = Decimal(str(amount or 0)).quantize(Decimal("0.01"))
            stripe_fee, platform_fee, total_charge, artist_payout, platform_revenue = calculate_boost_fees(boost_amount_decimal)

            # Add ahoy_match to total_charge if provided
            ahoy_match_decimal = Decimal(str(ahoy_match)).quantize(Decimal("0.01"))
            total_charge = total_charge + ahoy_match_decimal

            # Update Purchase.total to total_charge (authoritative)
            total = float(total_charge)
            with get_session() as s:
                p = s.query(Purchase).filter(Purchase.id == int(purchase_id)).first()
                if p:
                    p.total = total
                    s.commit()

            metadata.update({
                "boost_amount": str(boost_amount_decimal),
                "stripe_fee": str(stripe_fee),
                "platform_fee": str(platform_fee),
                "ahoy_match": str(ahoy_match_decimal),
                "total_paid": str(total_charge),
                "artist_payout": str(artist_payout),
                "platform_revenue": str(platform_revenue),
            })

            line_items = [
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Boost Amount",
                            "description": "100% goes directly to the artist",
                        },
                        "unit_amount": int(boost_amount_decimal * 100),
                    },
                    "quantity": 1,
                },
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Stripe Processing Fee",
                            "description": "2.9% + $0.30",
                        },
                        "unit_amount": int(Decimal(str(stripe_fee)) * 100),
                    },
                    "quantity": 1,
                },
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Ahoy Indie Media Platform Fee",
                            "description": "7.5% platform fee",
                        },
                        "unit_amount": int(Decimal(str(platform_fee)) * 100),
                    },
                    "quantity": 1,
                },
            ]

            # Add optional "Support Ahoy" line item if match amount > 0
            if ahoy_match_decimal > 0:
                line_items.append({
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": "Support Ahoy's Mission",
                            "description": "Optional contribution to keep Ahoy running",
                        },
                        "unit_amount": int(ahoy_match_decimal * 100),
                    },
                    "quantity": 1,
                })
        else:
            # One-time purchases (merch/theme/subscription MVP): treat as a simple one-time payment.
            # Validate amount before proceeding
            if not amount or float(amount or 0) <= 0:
                current_app.logger.error(f"Invalid amount for {kind} purchase: amount={amount}, item_id={item_id}, qty={qty}")
                return render_checkout_template(
                                       error="Invalid purchase amount. Please try again.",
                                       csrf_token=generate_csrf_token(),
                                       kind=kind,
                                       artist_id=artist_id or "",
                                       amount=amount,
                                       item_id=item_id or "",
                                       qty=qty), 400
            
            unit_amount_cents = int(max(0, float(amount)) * 100)
            if unit_amount_cents <= 0:
                current_app.logger.error(f"Invalid unit_amount_cents for {kind} purchase: {unit_amount_cents}")
                return render_checkout_template(
                                       error="Invalid purchase amount. Please try again.",
                                       csrf_token=generate_csrf_token(),
                                       kind=kind,
                                       artist_id=artist_id or "",
                                       amount=amount,
                                       item_id=item_id or "",
                                       qty=qty), 400
            # For merch, always derive title from the merch catalog item when possible.
            safe_title = (request.form.get("title") or "Ahoy Purchase").strip()[:120]
            if kind == "merch" and item_id:
                try:
                    try:
                        merch_catalog = get_all_merch(ttl=600)
                    except Exception:
                        from storage import read_json
                        merch_catalog = read_json("data/merch.json", {"items": []}) or {}
                    items = merch_catalog.get("items") if isinstance(merch_catalog, dict) else []
                    if isinstance(items, list):
                        for it in items:
                            if isinstance(it, dict) and str(it.get("id") or "") == str(item_id):
                                safe_title = str(it.get("name") or safe_title).strip()[:120]
                                break
                except Exception:
                    pass
            # For merch, quantity is always 1 (one-of-a-kind)
            merch_quantity = 1 if kind == "merch" else int(max(1, qty))
            line_items = [
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": safe_title},
                        "unit_amount": unit_amount_cents,
                    },
                    "quantity": merch_quantity,
                }
            ]

        # Handle wallet payment if requested
        if use_wallet:
            from flask_login import current_user
            if current_user.is_authenticated:
                try:
                    from blueprints.payments import deduct_wallet_balance
                    from decimal import Decimal
                    
                    # Calculate total charge
                    if kind in ["boost", "tip"]:
                        boost_amount_decimal = Decimal(str(amount or 0)).quantize(Decimal("0.01"))
                        _, _, total_charge, _, _ = calculate_boost_fees(boost_amount_decimal)
                    else:
                        # For merch, use the total from the purchase record
                        try:
                            total_charge = Decimal(str(total)) if total else Decimal("0.00")
                        except (ValueError, TypeError):
                            # Fallback: get total from purchase record
                            with get_session() as s:
                                from models import Purchase
                                p = s.query(Purchase).filter(Purchase.id == int(purchase_id)).first()
                                if p and p.total:
                                    total_charge = Decimal(str(p.total))
                                elif amount:
                                    total_charge = Decimal(str(amount))
                                else:
                                    current_app.logger.error(f"Wallet payment: Unable to determine total for purchase {purchase_id}, kind={kind}")
                                    # Get wallet balance for error page
                                    try:
                                        from models import User
                                        with get_session() as s2:
                                            user = s2.query(User).filter(User.id == current_user.id).first()
                                            wallet_balance = float(user.wallet_balance or 0) if user else 0.0
                                    except Exception as wb_err:
                                        logging.warning(f"Could not fetch wallet balance: {wb_err}")
                                        wallet_balance = None
                                    return render_checkout_template(
                                                         error="Unable to determine purchase total. Please try again.",
                                                         csrf_token=generate_csrf_token(),
                                                         kind=kind,
                                                         artist_id=artist_id or "",
                                                         amount=amount,
                                                         item_id=item_id or "",
                                                         qty=qty,
                                                         wallet_balance=wallet_balance), 400
                    
                    if total_charge <= 0:
                        current_app.logger.error(f"Wallet payment: Invalid total_charge {total_charge} for purchase {purchase_id}")
                        try:
                            from models import User
                            with get_session() as s2:
                                user = s2.query(User).filter(User.id == current_user.id).first()
                                wallet_balance = float(user.wallet_balance or 0) if user else 0.0
                        except Exception as wb_err:
                            logging.warning(f"Could not fetch wallet balance: {wb_err}")
                            wallet_balance = None
                        return render_checkout_template(
                                             error="Invalid purchase amount",
                                             csrf_token=generate_csrf_token(),
                                             kind=kind,
                                             artist_id=artist_id or "",
                                             amount=amount,
                                             item_id=item_id or "",
                                             qty=qty,
                                             wallet_balance=wallet_balance), 400
                    
                    # Try to deduct from wallet
                    success, error, balance_after = deduct_wallet_balance(
                        current_user.id,
                        total_charge,
                        f"{kind.title()} payment",
                        str(purchase_id),
                        kind
                    )
                    
                    if success:
                        # Wallet payment successful - mark purchase as paid
                        with get_session() as s:
                            from models import Purchase
                            p = s.query(Purchase).filter(Purchase.id == int(purchase_id)).first()
                            if p:
                                p.status = "paid"
                                p.stripe_id = f"wallet_{purchase_id}"
                                s.commit()
                            else:
                                current_app.logger.error(f"Wallet payment: Purchase {purchase_id} not found after wallet deduction")
                                # Wallet was deducted but purchase not found - this is bad
                                # Try to refund wallet (manual process needed)
                                try:
                                    from models import User, WalletTransaction
                                    with get_session() as s2:
                                        user = s2.query(User).filter(User.id == current_user.id).first()
                                        if user:
                                            user.wallet_balance += total_charge
                                            refund_tx = WalletTransaction(
                                                user_id=current_user.id,
                                                type="refund",
                                                amount=total_charge,
                                                balance_before=float(balance_after),
                                                balance_after=float(balance_after) + float(total_charge),
                                                description=f"Refund: Purchase {purchase_id} not found",
                                                reference_id=str(purchase_id),
                                                reference_type="purchase",
                                                created_at=datetime.utcnow(),
                                            )
                                            s2.add(refund_tx)
                                            s2.commit()
                                except Exception as refund_err:
                                    current_app.logger.error(f"Failed to refund wallet: {refund_err}")
                                
                                try:
                                    from models import User
                                    with get_session() as s2:
                                        user = s2.query(User).filter(User.id == current_user.id).first()
                                        wallet_balance = float(user.wallet_balance or 0) if user else 0.0
                                except Exception as wb_err:
                                    logging.warning(f"Could not fetch wallet balance: {wb_err}")
                                    wallet_balance = None
                                return render_checkout_template(
                                                     error="Purchase record not found. Wallet has been refunded. Please try again.",
                                                     csrf_token=generate_csrf_token(),
                                                     kind=kind,
                                                     artist_id=artist_id or "",
                                                     amount=amount,
                                                     item_id=item_id or "",
                                                     qty=qty,
                                                     wallet_balance=wallet_balance), 500
                    else:
                        # Wallet payment failed - fall through to Stripe
                        current_app.logger.warning(f"Wallet payment failed for user {current_user.id}: {error}")
                        try:
                            from models import User
                            with get_session() as s2:
                                user = s2.query(User).filter(User.id == current_user.id).first()
                                wallet_balance = float(user.wallet_balance or 0) if user else 0.0
                        except Exception as wb_err:
                            logging.warning(f"Could not fetch wallet balance: {wb_err}")
                            wallet_balance = None
                        return render_checkout_template(
                                             error=error or "Insufficient wallet balance",
                                             csrf_token=generate_csrf_token(),
                                             kind=kind,
                                             artist_id=artist_id or "",
                                             amount=amount,
                                             item_id=item_id or "",
                                             qty=qty,
                                             wallet_balance=wallet_balance), 400
                except Exception as e:
                    current_app.logger.error(f"Wallet payment error for user {current_user.id if current_user.is_authenticated else 'anonymous'}: {e}", exc_info=True)
                    try:
                        from models import User
                        with get_session() as s2:
                            user = s2.query(User).filter(User.id == current_user.id).first()
                            wallet_balance = float(user.wallet_balance or 0) if user else 0.0
                    except Exception as wb_err:
                        logging.warning(f"Could not fetch wallet balance: {wb_err}")
                        wallet_balance = None
                    return render_checkout_template(
                                         error=f"Wallet payment error: {str(e)}",
                                         csrf_token=generate_csrf_token(),
                                         kind=kind,
                                         artist_id=artist_id or "",
                                         amount=amount,
                                         item_id=item_id or "",
                                         qty=qty,
                                         wallet_balance=wallet_balance), 500

        success_url = url_for("checkout_success", pid=purchase_id, _external=True)
        cancel_url = url_for("checkout_page", type=kind, artist_id=artist_id or "", amount=amount, item_id=item_id or "", qty=qty, title=request.form.get("title") or "", _external=True)

        # For merch purchases, collect shipping address
        checkout_params = {
            "payment_method_types": ["card"],
            "line_items": line_items,
            "mode": "payment",
            "success_url": success_url,
            "cancel_url": cancel_url,
            "metadata": metadata,
        }
        
        # Add shipping address collection for merch purchases (US only)
        if kind == "merch":
            try:
                checkout_params["shipping_address_collection"] = {
                    "allowed_countries": ["US"],
                }
            except Exception as shipping_err:
                current_app.logger.warning(f"Error setting shipping address collection: {shipping_err}")
                # Continue without shipping collection if there's an error
        
        try:
            current_app.logger.info(f"Creating Stripe checkout session for {kind}, amount={amount}, qty={qty}")
            checkout_session = stripe.checkout.Session.create(**checkout_params)
            current_app.logger.info(f"Stripe checkout session created: {checkout_session.id}")
        except stripe.error.StripeError as stripe_err:
            current_app.logger.error(f"Stripe error creating checkout session: {stripe_err}", exc_info=True)
            return render_checkout_template(
                                   error=f"Payment processing error: {str(stripe_err)}",
                                   csrf_token=generate_csrf_token(),
                                   kind=kind,
                                   artist_id=artist_id or "",
                                   amount=amount,
                                   item_id=item_id or "",
                                   qty=qty), 500

        # Persist Stripe session id
        with get_session() as s:
            p = s.query(Purchase).filter(Purchase.id == int(purchase_id)).first()
            if p:
                p.stripe_id = checkout_session.id
                s.commit()

        return redirect(checkout_session.url)
    except Exception as e:
        # Log the full error with context for debugging
        import traceback
        error_trace = traceback.format_exc()
        current_app.logger.error(
            f"Checkout setup failed: {str(e)}\n"
            f"Kind: {kind}, Item ID: {item_id}, Amount: {amount}, Qty: {qty}\n"
            f"Traceback: {error_trace}",
            exc_info=True
        )
        # Fall back to success page with an error; keep purchase recorded for diagnostics
        return render_checkout_template(
                               error=f"Checkout setup failed: {str(e)}. Please try again or contact support.",
                               csrf_token=generate_csrf_token(),
                               kind=kind,
                               artist_id=artist_id or "",
                               amount=amount,
                               item_id=item_id or "",
                               qty=qty), 500

# Exempt checkout_process and wallet funding from Flask-WTF CSRF after route is registered
_csrf_ext = app.extensions.get('csrf')
if _csrf_ext is not None:
    _csrf_ext.exempt(checkout_process)
    # Exempt wallet funding endpoint (JSON API)
    try:
        from blueprints.payments import fund_wallet
        _csrf_ext.exempt(fund_wallet)
    except Exception as e:
        # Log but don't fail - endpoint will still work, just with CSRF check
        print(f"Warning: Could not exempt wallet funding from CSRF: {e}")
    
    # Exempt Stripe webhook endpoints - webhooks don't include CSRF tokens
    try:
        from routes.stripe_webhooks import bp as _stripe_webhooks_bp
        _csrf_ext.exempt(_stripe_webhooks_bp)
    except Exception as e:
        print(f"Warning: Could not exempt Stripe webhooks blueprint from CSRF: {e}")
    try:
        from blueprints.payments import stripe_webhook as _legacy_stripe_webhook
        _csrf_ext.exempt(_legacy_stripe_webhook)
    except Exception as e:
        print(f"Warning: Could not exempt legacy Stripe webhook from CSRF: {e}")

    # Exempt auth API endpoints - session-based JSON API
    try:
        from blueprints.api.auth import login, register, logout, change_password, password_reset_request, password_reset_confirm
        _csrf_ext.exempt(login)
        _csrf_ext.exempt(register)
        _csrf_ext.exempt(logout)
        _csrf_ext.exempt(change_password)
        _csrf_ext.exempt(password_reset_request)
        _csrf_ext.exempt(password_reset_confirm)
    except Exception as e:
        # Log but don't fail
        print(f"Warning: Could not exempt auth endpoints from CSRF: {e}")



@app.route('/success')
def checkout_success():
    pid = request.args.get('pid')
    artist_id = None
    amount = None
    status = None
    try:
        if pid:
            from db import get_session
            from models import Purchase
            with get_session() as s:
                p = s.query(Purchase).filter(Purchase.id == int(pid)).first()
                if p:
                    artist_id = p.artist_id
                    amount = p.amount
                    status = p.status
                    # Best-effort verification: if we have a Stripe session id, check if paid and update.
                    if p.stripe_id and p.status != "paid":
                        try:
                            import stripe
                            api_key = app.config.get("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY") or os.getenv("STRIPE_SECRET_KEY_TEST")
                            stripe.api_key = api_key
                            if stripe.api_key:
                                sess = stripe.checkout.Session.retrieve(p.stripe_id)
                                if getattr(sess, "payment_status", None) == "paid":
                                    p.status = "paid"
                                    status = "paid"
                                    s.commit()
                        except Exception:
                            pass
    except Exception:
        artist_id = None
        amount = None
        status = None
    return render_template('sawdust/success.html', pid=pid, artist_id=artist_id, amount=amount, status=status)


# Debug routes removed - debug functionality available via /debug endpoint

try:
    from flask_compress import Compress
    compress = Compress()
    compress.init_app(app)
    # Configure compression to work with all content types
    app.config['COMPRESS_MIMETYPES'] = [
        'text/html', 'text/css', 'text/xml', 'application/json',
        'application/javascript', 'text/javascript', 'image/svg+xml'
    ]
    app.config['COMPRESS_LEVEL'] = 6  # Good balance of speed vs compression
    app.config['COMPRESS_MIN_SIZE'] = 500  # Only compress files > 500 bytes
    print("Compression enabled")
except ImportError:
    print("WARN: Flask-Compress not available, compression disabled")

# Cache configuration
CACHE_TIMEOUT = 600  # 10 minutes (increased for better performance)

# In-memory cache for JSON data files (prevents repeated disk I/O)
_json_data_cache = {}
_json_file_mtimes = {}

# Removed: USERS_FILE, ACTIVITY_FILE, load_users(), save_users() - using database now

def load_json_data(filename, default=None, cache_duration=600):
    """Load JSON data from file with in-memory caching.

    For migrated content files (music, shows, artists, podcasts), reads from
    dev/legacy_json/ as a dev-only safety net. DB should be the primary source.
    For non-migrated files, reads from static/data/ as before.
    """
    import os
    from time import time

    # Migrated content files live in dev/legacy_json/ now
    _MIGRATED = {'music.json', 'shows.json', 'artists.json', 'podcasts.json'}
    if filename in _MIGRATED:
        filepath = f'dev/legacy_json/{filename}'
        # Legacy JSON fallback (dev-only safety net)
        _log = logging.getLogger('content.fallback')
        _log.warning('JSON fallback triggered for %s (DB should be primary source)', filename)
    else:
        filepath = f'static/data/{filename}'
    cache_key = filepath
    
    # Check if file exists
    if not os.path.exists(filepath):
        return default or {}
    
    # Get file modification time
    try:
        current_mtime = os.path.getmtime(filepath)
    except OSError:
        current_mtime = 0
    
    # Check cache validity
    if cache_key in _json_data_cache:
        cached_data, cached_time, cached_mtime = _json_data_cache[cache_key]
        # Cache is valid if:
        # 1. Not expired (within cache_duration seconds)
        # 2. File hasn't been modified
        if (time() - cached_time < cache_duration and 
            cached_mtime == current_mtime):
            return cached_data
    
    # Load from disk
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Update cache
        _json_data_cache[cache_key] = (data, time(), current_mtime)
        
        # Clean up old cache entries (older than 1 hour)
        cleanup_time = time() - 3600
        keys_to_remove = [
            k for k, (_, t, _) in _json_data_cache.items() 
            if t < cleanup_time
        ]
        for k in keys_to_remove:
            _json_data_cache.pop(k, None)
        
        return data
    except FileNotFoundError:
        return default or {}
    except json.JSONDecodeError as e:
        logging.error(f'JSON decode error in {filename}: {e}')
        return default or {}
    except Exception as e:
        logging.error(f'Error loading {filename}: {e}')
        return default or {}


def _etag_for_static_json(filename: str) -> Optional[str]:
    """Create a weak ETag for legacy JSON files based on mtime + size.

    Legacy JSON fallback (dev-only safety net).
    """
    try:
        p = Path("dev") / "legacy_json" / filename
        if not p.exists():
            p = Path("static") / "data" / filename
        st = p.stat()
        return f'W/"{int(st.st_mtime)}-{int(st.st_size)}"'
    except Exception:
        return None


def _cached_json_response(filename: str, default: dict, max_age_seconds: int = 300):
    """Return a JSON response with Cache-Control + ETag (conditional GET)."""
    etag = _etag_for_static_json(filename)
    cache_control = f"public, max-age={int(max_age_seconds)}"

    # Conditional GET
    inm = request.headers.get("If-None-Match")
    if etag and inm == etag:
        resp = make_response("", 304)
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = cache_control
        resp.headers["Vary"] = "Accept-Encoding"
        return resp

    data = load_json_data(filename, default, cache_duration=max_age_seconds)
    resp = jsonify(data)
    resp.headers["Cache-Control"] = cache_control
    resp.headers["Vary"] = "Accept-Encoding"
    if etag:
        resp.headers["ETag"] = etag
    return resp

# Replaced auth_required with Flask-Login's @login_required
# Use: from flask_login import login_required


# @app.route('/music')
# def music():
#     """Music library page"""
#     response = make_response(render_template('music.html'))
#     response.headers['Cache-Control'] = f'public, max-age={CACHE_TIMEOUT}'
#     return response

# @app.route('/focus')
# def focus():
#     """Focus/ambient audio page for background music"""
#     response = make_response(render_template('focus.html'))
#     response.headers['Cache-Control'] = f'public, max-age={CACHE_TIMEOUT}'
#     return response

# @app.route('/shows')
# def shows():
#     """Shows/video content page"""
#     # redirect to /videos in SPA
#     response = make_response(render_template('shows.html'))
#     response.headers['Cache-Control'] = f'public, max-age={CACHE_TIMEOUT}'
#     return response


# @app.route('/artists')
# def artists():
#     """Artists directory page"""
#     response = make_response(render_template('artists.html'))
#     response.headers['Cache-Control'] = f'public, max-age={CACHE_TIMEOUT}'
#     return response

# @app.route('/podcasts')
# def podcasts_page():
#     """Podcasts hub page"""
#     data = get_all_podcasts(ttl=600)
#     shows = data.get('shows', [])
#     episodes = []
#     for s in shows:
#         for ep in s.get('episodes', []):
#             episodes.append({**ep, 'show_slug': s['slug'], 'show_title': s.get('title', s['slug'])})
#     return render_template('podcasts.html', podcasts={'shows': shows, 'episodes': episodes})
# 
# @app.route('/podcasts/<show_slug>')
# def podcast_show_page(show_slug):
#     """Podcast show detail page"""
#     data = get_all_podcasts(ttl=600)
#     shows = data.get('shows', [])
#     s = next((x for x in shows if x.get('slug') == show_slug), None)
#     if s:
#         show = {
#             'slug': s['slug'],
#             'title': s.get('title', show_slug.replace('-', ' ').title()),
#             'description': s.get('description', ''),
#             'artwork': s.get('artwork') or '/static/img/default-cover.jpg',
#             'last_updated': s.get('last_updated', ''),
#             'episodes': s.get('episodes', []),
#         }
#         return render_template('podcast_show.html', show=show)
# 
#     known_slugs = set(_PODCAST_SLUG_ALIASES.values())
#     if show_slug not in known_slugs:
#         return render_template('404.html'), 404
#     show = {
#         'slug': show_slug,
#         'title': show_slug.replace('-', ' ').title(),
#         'description': '',
#         'artwork': '/static/img/default-cover.jpg',
#         'last_updated': '',
#         'episodes': [],
#     }
#     return render_template('podcast_show.html', show=show)

# @app.route('/events')
# def events_page():
#     """Upcoming live Ahoy events (separate from /dashboard and /performances)."""
#     try:
#         events_data = get_all_events(ttl=600)
#     except Exception:
#         events_data = load_json_data('events.json', {'events': []})
#     try:
#         videos_data = get_all_videos(ttl=600)
#     except Exception:
#         videos_data = load_json_data('videos.json', {'videos': []})
#     response = make_response(render_template('events.html', events=events_data, videos=videos_data))
#     response.headers['Cache-Control'] = f'public, max-age={CACHE_TIMEOUT}'
#     return response
# 
# @app.route('/events/<event_id>')
# def event_detail(event_id):
#     """Event detail page (past or upcoming)."""
#     try:
#         events_data = get_all_events(ttl=600)
#     except Exception:
#         events_data = load_json_data('events.json', {'events': []})
#     event_key = unquote(event_id or '')
#     event = None
#     for e in events_data.get('events', []):
#         if str(e.get('id', '')) == event_key:
#             event = e
#             break
#     if not event:
#         abort(404)
#     response = make_response(render_template('event_detail.html', event=event))
#     response.headers['Cache-Control'] = f'public, max-age={CACHE_TIMEOUT}'
#     return response


@app.route('/proxy/audio')
@limiter.exempt
def proxy_audio():
    """Proxy audio files to bypass CORS on localhost testing"""
    import requests as requests_lib
    from urllib.parse import unquote

    url = request.args.get('url')
    if not url:
        abort(400, 'Missing url parameter')

    # Decode the URL
    url = unquote(url)

    # Security: only allow S3 and Google Storage URLs
    if not (url.startswith('https://') and
            ('s3' in url or 'storage.googleapis.com' in url or 'ahoycollection' in url)):
        abort(403, 'Invalid audio source')

    try:
        # Fetch audio from external source
        resp = requests_lib.get(url, timeout=30, stream=True)
        resp.raise_for_status()

        # Create response with audio data
        response = make_response(resp.content)
        response.headers['Content-Type'] = 'audio/mpeg'
        response.headers['Content-Length'] = resp.headers.get('Content-Length', len(resp.content))
        response.headers['Cache-Control'] = 'public, max-age=3600'

        return response
    except requests_lib.exceptions.RequestException as e:
        abort(502, f'Failed to fetch audio: {str(e)}')

def _is_local_file_path(s):
    """True if string looks like a local filesystem path (do not use as public image URL). URLs and /static/ are safe."""
    if not s or not isinstance(s, str):
        return False
    s = s.strip()
    # Public URLs and same-origin static paths are valid image URLs; do not replace
    if s.startswith(('http://', 'https://', '/static/')):
        return False
    return any(s.startswith(p) or p in s for p in ('/var/', '/Users/', '/tmp/', 'TemporaryItems', 'Screenshot')) or s.endswith(('.png', '.jpg', '.jpeg'))

# @app.route('/merch')
# def merch():
#     """Merch store page"""
#     from utils.observability import get_release
#     merch_catalog, purchased_item_ids = _merch_catalog_and_purchased()
#     response = make_response(render_template(
#         'merch.html',
#         merch=merch_catalog,
#         release=get_release(),
#         purchased_item_ids=purchased_item_ids
#     ))
#     # Merch changes frequently; avoid serving stale HTML that can "stick" in app/webview caches.
#     response.headers['Cache-Control'] = 'no-store'
#     return response


def _merch_catalog_and_purchased():
    """Shared: load merch catalog (sanitized) and set of purchased item ids. Used by /merch and /api/merch."""
    from storage import read_json
    try:
        merch_catalog = get_all_merch(ttl=600)
    except Exception:
        merch_catalog = read_json('data/merch.json', {"items": []}) or {}
    items = merch_catalog.get('items') if isinstance(merch_catalog, dict) else []
    if isinstance(items, list):
        sanitized = []
        for it in items:
            if not isinstance(it, dict):
                continue
            it = dict(it)
            if _is_local_file_path(it.get('image_url')):
                it['image_url'] = '/static/img/default-cover.jpg'
            if _is_local_file_path(it.get('image_url_back')):
                it['image_url_back'] = None
            if _is_local_file_path(it.get('name')):
                it['name'] = it.get('id') or 'Item'
            sanitized.append(it)
        merch_catalog = dict(merch_catalog) if isinstance(merch_catalog, dict) else {}
        merch_catalog['items'] = sanitized
    purchased_item_ids = set()
    try:
        with get_session() as s:
            purchases = s.query(Purchase).filter(
                Purchase.type == "merch",
                Purchase.item_id.isnot(None)
            ).all()
            purchased_item_ids = {str(p.item_id) for p in purchases if p.item_id}
    except Exception as e:
        current_app.logger.warning(f"Error querying purchased merch items: {e}")
    return merch_catalog, purchased_item_ids


@app.route('/api/merch')
@limiter.exempt
def api_merch():
    """Get merch catalog and purchased item ids for SPA (same data as /merch page)."""
    merch_catalog, purchased_item_ids = _merch_catalog_and_purchased()
    return jsonify({
        'items': merch_catalog.get('items', []),
        'purchased_item_ids': list(purchased_item_ids),
    })


@app.route('/player')
def player():
    """Redirect to appropriate content page - full player replaced by persistent mini player"""
    media_type = request.args.get('type', 'music')
    # Redirect to the relevant content section instead of full player
    if media_type == 'show':
        return redirect(url_for('shows'))
    elif media_type == 'podcast':
        return redirect(url_for('podcasts'))
    else:
        return redirect(url_for('music'))


# @app.route('/artist/<artist_slug>')
# def artist_profile(artist_slug):
#     """Individual artist profile page (slug or case-insensitive name)"""
#     try:
#         artists_data = get_all_artists(ttl=600)
#     except Exception:
#         artists_data = load_json_data('artists.json', {'artists': []})
#     artist = None
#     
#     for a in artists_data.get('artists', []):
#         slug = (a.get('slug') or a.get('name', '').lower().replace(' ', '-'))
#         if slug == artist_slug or a.get('name', '').lower() == artist_slug.replace('-', ' ').lower():
#             artist = a
#             break
#     
#     if not artist:
#         return render_template('404.html'), 404
#     
#     # Get user's follow status if logged in
#     is_following = False
#     user_id = resolve_db_user_id()
#     if user_id and artist:
#         artist_id = artist.get('slug') or artist.get('id') or artist.get('name')
#         try:
#             with get_session() as db_session:
#                 follow = db_session.query(UserArtistFollow).filter(
#                     UserArtistFollow.user_id == user_id,
#                     UserArtistFollow.artist_id == str(artist_id)
#                 ).first()
#                 is_following = follow is not None
#         except Exception:
#             pass
#     
#     response = make_response(render_template('artist_detail.html', artist=artist, is_following=is_following))
#     response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#     response.headers['Pragma'] = 'no-cache'
#     return response

# @app.route('/my-saves')
# def my_saves():
#     """Saved page - main bookmarks/saves page"""
#     return render_template("my_saves.html")



# API Endpoints
@app.route('/api/now-playing')
@limiter.exempt
def api_now_playing():
    """Get curated now playing feed with 30s previews - randomized on each request"""
    # Use cached data (cache_duration=600 to match other endpoints - data is already cached)
    try:
        music_data = get_all_tracks(ttl=600)
        shows_data = get_all_shows(ttl=600)
    except Exception:
        music_data = load_json_data('music.json', {'tracks': []}, cache_duration=600)
        shows_data = load_json_data('shows.json', {'shows': []}, cache_duration=600)
    
    # Combine and curate content for discovery feed
    feed_items = []
    
    # Get all available tracks and shows
    all_tracks = music_data.get('tracks', [])
    all_shows = shows_data.get('shows', [])
    
    # Filter for content with preview URLs
    tracks_with_preview = [t for t in all_tracks if t.get('preview_url')]
    shows_with_preview = [s for s in all_shows if s.get('trailer_url')]
    
    # Randomly select tracks (up to 8)
    selected_tracks = random.sample(tracks_with_preview, min(len(tracks_with_preview), 8))
    for track in selected_tracks:
        feed_items.append({
            'id': track['id'],
            'type': 'music',
            'title': track['title'],
            'artist': track['artist'],
            'preview_url': track['preview_url'],
            'cover_art': track['cover_art'],
            'duration': 30,  # Preview length
            'full_url': track['audio_url'],
            'duration_seconds': track.get('duration_seconds', 180),
            'description': track.get('description', ''),
            'genre': track.get('genre', '')
        })
    
    # Randomly select shows (up to 5)
    selected_shows = random.sample(shows_with_preview, min(len(shows_with_preview), 5))
    for show in selected_shows:
        feed_items.append({
            'id': show['id'],
            'type': 'show',
            'title': show['title'],
            'artist': show.get('host', 'Ahoy Indie Media'),
            'preview_url': show['trailer_url'],
            'cover_art': show['thumbnail'],
            'duration': 30,
            'full_url': show['video_url'],
            'duration_seconds': show.get('duration_seconds', 300),
            'description': show.get('description', ''),
            'genre': show.get('genre', '')
        })
    
    # Shuffle for discovery - this will be different on each request
    random.shuffle(feed_items)
    
    # Limit to 12 items for better performance
    feed_items = feed_items[:12]
    
    response = jsonify({'feed': feed_items})
    # Cache for 1 minute (content is randomized per request, but structure is stable)
    response.headers['Cache-Control'] = 'public, max-age=60'
    return response

@app.post('/api/listening/start')
def api_listening_start():
    try:
        data = request.get_json(silent=True) or {}
        media_type = (data.get('media_type') or '').strip() or 'track'
        media_id = (data.get('media_id') or '').strip()
        source = (data.get('source') or 'manual').strip()
        uid = resolve_playback_user_id()
        sid = listening_start_session(uid, media_type, media_id, source)
        return jsonify({'session_id': sid})
    except Exception as e:
        return jsonify({'error': 'failed', 'detail': str(e)}), 400

@app.post('/api/listening/end')
def api_listening_end():
    try:
        data = request.get_json(silent=True) or {}
        sid = (data.get('session_id') or '').strip()
        if not sid:
            return jsonify({'error': 'missing_session_id'}), 400
        seconds = listening_end_session(sid)
        return jsonify({'seconds': int(seconds or 0)})
    except Exception as e:
        return jsonify({'error': 'failed', 'detail': str(e)}), 400

@app.get('/api/listening/stats')
def api_listening_stats():
    try:
        uid = resolve_db_user_id()
        if not uid:
            return jsonify({'error': 'not_authenticated'}), 401
        from models import ListeningTotal
        stats = ListeningTotal.query.filter_by(user_id=uid).first()
        if not stats:
            return jsonify({'total_seconds': 0, 'music_seconds': 0, 'podcast_seconds': 0, 'video_seconds': 0})
        return jsonify({
            'total_seconds': stats.total_seconds,
            'music_seconds': stats.music_seconds,
            'podcast_seconds': stats.podcast_seconds,
            'video_seconds': stats.video_seconds
        })
    except Exception as e:
        return jsonify({'error': 'failed', 'detail': str(e)}), 400

@app.route('/api/products')
@limiter.exempt
def api_products():
    """Get products data (subscriptions, themes, limits)"""
    from storage import read_json
    products = read_json('data/products.json', {})
    return jsonify(products)

@app.route('/api/agenda')
def api_agenda():
    """Get agenda data for the current day"""
    from datetime import datetime, timedelta
    import random
    
    today = datetime.now()
    
    # Mock agenda items
    agenda_items = [
        {
            'id': 1,
            'time': '09:00',
            'title': 'Morning Music Discovery',
            'description': 'Explore new indie tracks',
            'type': 'music',
            'priority': 'high'
        },
        {
            'id': 2,
            'time': '14:00',
            'title': 'Live Show: Indie Spotlight',
            'description': 'Watch today\'s featured performance',
            'type': 'show',
            'priority': 'medium'
        },
        {
            'id': 3,
            'time': '19:00',
            'title': 'Evening Playlist',
            'description': 'Wind down with curated tracks',
            'type': 'music',
            'priority': 'low'
        }
    ]
    
    # Add some random events
    random_events = [
        {'time': '11:30', 'title': 'Artist Interview', 'description': 'Exclusive artist chat', 'type': 'show'},
        {'time': '16:00', 'title': 'New Release Alert', 'description': 'Fresh tracks just dropped', 'type': 'music'},
        {'time': '20:30', 'title': 'Community Chat', 'description': 'Connect with other fans', 'type': 'community'}
    ]
    
    # Add 1-2 random events
    selected_events = random.sample(random_events, random.randint(1, 2))
    agenda_items.extend(selected_events)
    
    # Sort by time
    agenda_items.sort(key=lambda x: x['time'])
    
    return jsonify({
        'date': today.strftime('%A, %B %d, %Y'),
        'day_of_week': today.strftime('%A'),
        'items': agenda_items
    })

@app.route('/api/user/homepage-layout', methods=['GET', 'POST'])
def api_homepage_layout():
    """Get or save user's custom homepage layout"""
    if request.method == 'GET':
        # Return default layout for now
        default_layout = {
            'widgets': [
                {'id': 'weather', 'position': 0, 'enabled': True},
                {'id': 'agenda', 'position': 1, 'enabled': True},
                {'id': 'featured', 'position': 2, 'enabled': True},
                {'id': 'now_playing', 'position': 3, 'enabled': True},
                {'id': 'quick_actions', 'position': 4, 'enabled': True},
                {'id': 'recent_activity', 'position': 5, 'enabled': True}
            ]
        }
        return jsonify(default_layout)
    
    elif request.method == 'POST':
        # Save user's layout (in a real app, save to database)
        layout_data = request.get_json()
        # For demo, just return success
        return jsonify({'success': True, 'message': 'Layout saved successfully'})

@app.route('/api/music')
@limiter.exempt
def api_music():
    """Get all music data"""
    try:
        data = get_all_tracks(ttl=600)
        if data.get('tracks'):
            resp = jsonify(data)
            resp.headers['Cache-Control'] = 'public, max-age=60'
            resp.headers['Vary'] = 'Accept-Encoding'
            return resp
    except Exception:
        logging.getLogger(__name__).exception('DB music query failed, falling back to JSON')
    return _cached_json_response("music.json", {"tracks": []}, max_age_seconds=60)


@app.route('/api/media/resolve', methods=['POST'])
@limiter.exempt
def api_media_resolve():
    """Resolve a list of {media_type, media_id} pairs to full metadata objects.
    Used by PlaylistDetailView to avoid fetching the full music/podcast catalog.
    Body: {"items": [{"media_type": "music", "media_id": "abc123"}, ...]}
    Returns: {"resolved": {"music:abc123": {...track}, "podcast:xyz": {...episode}}}
    """
    body = request.get_json(silent=True) or {}
    requests_list = body.get("items") or []
    if not requests_list or not isinstance(requests_list, list):
        return jsonify({"resolved": {}})

    # Group by type for efficient lookup
    # 'music' is the canonical type for tracks; 'clip' is the canonical type for podcast episodes
    music_ids = {r["media_id"] for r in requests_list if r.get("media_type") in ("music", "track")}
    clip_ids = {r["media_id"] for r in requests_list if r.get("media_type") in ("clip", "podcast")}

    resolved = {}

    if music_ids:
        try:
            all_tracks = get_all_tracks(ttl=600).get("tracks", [])
            for t in all_tracks:
                tid = str(t.get("id") or t.get("track_id") or "")
                if tid in music_ids:
                    resolved[f"music:{tid}"] = t
        except Exception:
            pass

    if clip_ids:
        try:
            all_podcasts = get_all_podcasts(ttl=600)
            shows = all_podcasts.get("shows") or all_podcasts.get("podcasts") or []
            for show in shows:
                for ep in show.get("episodes") or []:
                    eid = str(ep.get("id") or ep.get("episode_id") or "")
                    if eid in clip_ids:
                        resolved[f"clip:{eid}"] = {**ep, "show_title": show.get("title", "")}
        except Exception:
            pass

    resp = jsonify({"resolved": resolved})
    resp.headers['Cache-Control'] = 'public, max-age=120'
    return resp


def _build_radio_manifest():
    return build_radio_station_manifest()


@app.route('/api/radio/live')
@limiter.exempt
def api_radio_live():
    """Return a small radio manifest for client-side live timeline computation."""
    try:
        manifest = _build_radio_manifest()
        resp = jsonify(manifest)
        resp.headers['Cache-Control'] = 'public, max-age=300'
        resp.headers['Vary'] = 'Accept-Encoding'
        return resp
    except Exception:
        logging.getLogger(__name__).exception('Radio manifest build failed')
        return jsonify({
            'station': {
                'key': 'ahoy-radio-main',
                'name': 'Ahoy Radio',
                'epoch_ms': int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1000),
                'computed_locally': True,
                'track_count': 0,
            },
            'server_time_ms': int(datetime.now(timezone.utc).timestamp() * 1000),
            'tracks': [],
        }), 200

@app.post('/api/music/play')
@limiter.limit("1 per 30 seconds per user")
def api_music_play():
    """Increment play count for a track (called after 5 seconds of listening).
    Rate limited to 1 play per track per 30 seconds per user to prevent spam."""
    from models import Track
    from services.content_db import invalidate_cache
    data = request.get_json(silent=True) or {}
    track_id = (data.get('track_id') or '').strip()
    if not track_id:
        return jsonify({'error': 'missing track_id'}), 400
    try:
        with get_session() as session:
            track = session.query(Track).filter_by(track_id=track_id).first()
            if not track:
                return jsonify({'error': 'not found'}), 404
            track.play_count = (track.play_count or 0) + 1
            count = track.play_count
        invalidate_cache('all_tracks')
        return jsonify({'play_count': count})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# @app.route('/radio')
# def radio_page():
#     """Ahoy Radio - continuous play from all music."""
#     return render_template('radio.html')


@app.route('/api/shows')
@limiter.exempt
def api_shows():
    """Get all shows/video content"""
    try:
        # Fresh reads keep newly imported videos visible without waiting on the
        # in-process content cache to expire.
        data = get_all_shows(ttl=0)
        if data.get('shows'):
            resp = jsonify(data)
            resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            resp.headers['Pragma'] = 'no-cache'
            resp.headers['Expires'] = '0'
            resp.headers['Vary'] = 'Accept-Encoding'
            return resp
    except Exception:
        logging.getLogger(__name__).exception('DB shows query failed, falling back to JSON')
    return _cached_json_response("shows.json", {"shows": []}, max_age_seconds=600)

@app.route('/api/live-tv/channels')
@limiter.exempt
def api_live_tv_channels():
    """Return four AHOY TV channels with pre-generated schedule (or fallback to daily shuffle)."""
    from services.live_tv_scheduler import get_today_schedule
    from datetime import date

    try:
        # Try to get pre-generated schedule
        try:
            schedule = get_today_schedule()
            if schedule:
                # Build channels from schedule
                with get_session() as session:
                    channels_dict = {'misc': {}, 'films': {}, 'music-videos': {}, 'live-shows': {}}
                    for (slot_id, channel_id), slot_data in schedule.items():
                        show_id = slot_data.get('show_id')
                        if show_id and channel_id in channels_dict:
                            show = session.query(Show).filter_by(id=show_id).first()
                            if show and show.video_url and show_id not in channels_dict[channel_id]:
                                channels_dict[channel_id][show_id] = {
                                    'id': show.show_id or str(show.id),
                                    'title': show.title,
                                    'video_url': show.video_url,
                                    'thumbnail': show.thumbnail,
                                    'duration_seconds': show.duration_seconds or 0,
                                    'category': show.category,
                                    'tags': show.tags or [],
                                }

                    channels = [
                        {'id': 'misc', 'name': 'Misc', 'items': list(channels_dict['misc'].values())},
                        {'id': 'films', 'name': 'Films', 'items': list(channels_dict['films'].values())},
                        {'id': 'music-videos', 'name': 'Music Videos', 'items': list(channels_dict['music-videos'].values())},
                        {'id': 'live-shows', 'name': 'Live Shows', 'items': list(channels_dict['live-shows'].values())},
                    ]

                response = jsonify({'channels': channels, 'scheduled': True})
                response.headers['Cache-Control'] = 'public, max-age=86400'  # 24 hours until next schedule
                return response
        except Exception as e:
            logging.getLogger(__name__).warning(f'AHOY TV scheduler failed, falling back to daily shuffle: {e}', exc_info=True)

        # FALLBACK: Use original daily_shuffle system
        try:
            shows_data = get_all_shows(ttl=600)
        except Exception:
            shows_data = load_json_data('shows.json', {'shows': []})

        if not shows_data.get('shows'):
            try:
                from pathlib import Path
                static_shows = Path('static/data/shows.json')
                if static_shows.exists():
                    import json
                    with open(static_shows, 'r', encoding='utf-8') as f:
                        shows_data = json.load(f)
            except Exception:
                pass

        if not shows_data.get('shows'):
            try:
                videos_data = load_json_data('videos.json', {'videos': []})
                videos = videos_data.get('videos') or []
                def _parse_duration_seconds(d):
                    if d is None:
                        return 300
                    if isinstance(d, (int, float)) and d > 0:
                        return int(d)
                    s = str(d).strip().lower()
                    import re
                    m = re.match(r'(\d+)\s*(?:min|minute|minutes?)?', s)
                    if m:
                        return int(m.group(1)) * 60
                    return 300
                for v in videos:
                    if not v.get('url'):
                        continue
                    shows_data.setdefault('shows', []).append({
                        'id': v.get('id') or str(uuid.uuid4()),
                        'title': v.get('title') or 'Untitled',
                        'video_url': v.get('url'),
                        'thumbnail': v.get('thumbnail'),
                        'duration_seconds': _parse_duration_seconds(v.get('duration')),
                        'category': 'live show' if 'live' in (v.get('title') or '').lower() else 'misc',
                        'tags': [],
                    })
            except Exception:
                pass

        def normalize_show(item):
            show_id = item.get('id')
            if not show_id:
                show_id = str(uuid.uuid4())
            tags = item.get('tags') or []
            if not isinstance(tags, list):
                tags = []
            tags = [str(t) for t in tags if t is not None]
            return {
                'id': show_id,
                'title': item.get('title') or 'Untitled',
                'type': 'show',
                'video_url': item.get('video_url') or item.get('mp4_link') or item.get('trailer_url'),
                'thumbnail': item.get('thumbnail'),
                'duration_seconds': item.get('duration_seconds') or 0,
                'description': item.get('description') or '',
                'category': (item.get('category') or '').lower(),
                'tags': tags,
            }

        shows = [normalize_show(s) for s in shows_data.get('shows', []) if s.get('video_url') or s.get('mp4_link') or s.get('trailer_url')]

        def safe_join_tags(tags):
            if not tags or not isinstance(tags, list):
                return ''
            return ' '.join(str(t) for t in tags if t is not None)

        music_videos = [s for s in shows if (
            s.get('category') in ('music video', 'music-video') or
            'music' in s.get('title', '').lower() or
            'music-video' in s.get('tags', []) or
            'musicvideos' in safe_join_tags(s.get('tags', []))
        ) and 'video-podcast' not in s.get('tags', [])]
        films = [s for s in shows if (
            s.get('category') in ('short film', 'film') or
            'film' in s.get('tags', []) or
            'movie' in s.get('tags', []) or
            'short' in s.get('title', '').lower()
        ) and 'video-podcast' not in s.get('tags', [])]
        live_shows = [s for s in shows if (
            s.get('category') in ('broadcast', 'live show', 'live-show', 'episode') or
            'live' in s.get('title', '').lower() or
            'live' in safe_join_tags(s.get('tags', []))
        ) and 'video-podcast' not in s.get('tags', [])]
        included_ids = {s.get('id') for s in music_videos + films + live_shows if s.get('id')}
        misc = [s for s in shows if s.get('id') and s.get('id') not in included_ids]

        def daily_shuffle(items, salt=''):
            today = datetime.now(timezone.utc).strftime('%Y-%m-%d')
            seed_src = f'{today}:{salt}'
            seed = int(hashlib.sha1(seed_src.encode('utf-8')).hexdigest()[:8], 16)
            rnd = random.Random(seed)
            items_copy = [i for i in items]
            rnd.shuffle(items_copy)
            return items_copy

        channels = [
            {'id': 'misc', 'name': 'Misc', 'items': daily_shuffle(misc, 'misc')},
            {'id': 'films', 'name': 'Films', 'items': daily_shuffle(films, 'films')},
            {'id': 'music-videos', 'name': 'Music Videos', 'items': daily_shuffle(music_videos, 'music')},
            {'id': 'live-shows', 'name': 'Live Shows', 'items': daily_shuffle(live_shows, 'live')},
        ]

        response = jsonify({'channels': channels, 'scheduled': False})
        response.headers['Cache-Control'] = 'public, max-age=300'
        return response

    except Exception as e:
        logging.error(f'Error in api_live_tv_channels: {e}', exc_info=True)
        response = jsonify({
            'channels': [
                {'id': 'misc', 'name': 'Misc', 'items': []},
                {'id': 'films', 'name': 'Films', 'items': []},
                {'id': 'music-videos', 'name': 'Music Videos', 'items': []},
                {'id': 'live-shows', 'name': 'Live Shows', 'items': []},
            ],
            'error': 'Failed to load channels'
        })
        response.headers['Cache-Control'] = 'no-cache'
        return response

@app.route('/api/show/<show_id>')
def api_show(show_id):
    """Get individual show by ID"""
    try:
        shows_data = get_all_shows(ttl=0)
    except Exception:
        shows_data = load_json_data('shows.json', {'shows': []})
    show = next((s for s in shows_data.get('shows', []) if s.get('id') == show_id), None)
    
    if not show:
        return jsonify({'error': 'Show not found'}), 404
    
    return jsonify(show)

@app.route('/api/artists')
@limiter.exempt
def api_artists():
    """Get artists directory"""
    try:
        data = get_all_artists(ttl=600)
        if data.get('artists'):
            resp = jsonify(data)
            resp.headers['Cache-Control'] = 'public, max-age=60'
            resp.headers['Vary'] = 'Accept-Encoding'
            return resp
    except Exception:
        logging.getLogger(__name__).exception('DB artists query failed, falling back to JSON')
    return _cached_json_response("artists.json", {"artists": []}, max_age_seconds=60)

@app.route('/api/artists/featured')
@limiter.exempt
def api_featured_artists():
    """Get featured artists"""
    try:
        all_artists = get_artists_list(ttl=600)
        if all_artists:
            featured = [a for a in all_artists if a.get('featured', False)]
            resp = jsonify({'artists': featured})
            resp.headers['Cache-Control'] = 'public, max-age=300'
            resp.headers['Vary'] = 'Accept-Encoding'
            return resp
    except Exception:
        logging.getLogger(__name__).exception('DB featured artists query failed')

    # Fallback to JSON file
    etag = _etag_for_static_json("artists.json")
    inm = request.headers.get("If-None-Match")
    if etag and inm == etag:
        resp = make_response("", 304)
        resp.headers["ETag"] = etag
        resp.headers["Cache-Control"] = "public, max-age=300"
        resp.headers["Vary"] = "Accept-Encoding"
        return resp

    artists_data = load_json_data('artists.json', {'artists': []})
    featured = [a for a in artists_data.get('artists', []) if a.get('featured', False)]
    resp = jsonify({'artists': featured})
    resp.headers["Cache-Control"] = "public, max-age=300"
    resp.headers["Vary"] = "Accept-Encoding"
    if etag:
        resp.headers["ETag"] = etag
    return resp

@app.route('/api/podcasts')
@limiter.exempt
def api_podcasts():
    """Get all podcast shows with episodes from database."""
    data = get_all_podcasts(ttl=600)
    resp = jsonify(data)
    resp.headers['Cache-Control'] = 'public, max-age=600'
    resp.headers['Vary'] = 'Accept-Encoding'
    return resp

@app.route('/api/events')
@limiter.exempt
def api_events():
    """Get all events and videos (same data as events page for SPA)."""
    try:
        events_data = get_all_events(ttl=600)
    except Exception:
        events_data = load_json_data('events.json', {'events': []})
    try:
        videos_data = get_all_videos(ttl=600)
    except Exception:
        videos_data = load_json_data('videos.json', {'videos': []})
    payload = {
        'events': events_data.get('events', []) if isinstance(events_data, dict) else [],
        'videos': videos_data.get('videos', []) if isinstance(videos_data, dict) else [],
        'series_info': events_data.get('series_info', {}) if isinstance(events_data, dict) else {},
    }
    resp = jsonify(payload)
    resp.headers['Cache-Control'] = 'public, max-age=600'
    resp.headers['Vary'] = 'Accept-Encoding'
    return resp

@app.route('/api/studio')
@limiter.exempt
def api_studio():
    """Get all studio collections (public)."""
    try:
        from models import StudioCollection
        with get_session() as session:
            cols = (session.query(StudioCollection)
                    .filter_by(is_hidden=False)
                    .order_by(StudioCollection.position.asc(), StudioCollection.id.desc())
                    .all())
            data = [{
                'id': c.id,
                'collection_id': c.collection_id,
                'title': c.title,
                'date': c.date,
                'tag': c.tag,
                'description': c.description,
                'cover': c.cover,
                'photo_count': len(c.photos) if c.photos else 0,
            } for c in cols]
        resp = jsonify({'collections': data})
        resp.headers['Cache-Control'] = 'public, max-age=300'
        return resp
    except Exception as e:
        return jsonify({'collections': [], 'error': str(e)})


@app.route('/api/studio/<collection_id>')
@limiter.exempt
def api_studio_collection(collection_id):
    """Get a single studio collection with all photos."""
    try:
        from models import StudioCollection
        with get_session() as session:
            c = (session.query(StudioCollection)
                 .filter_by(collection_id=collection_id, is_hidden=False)
                 .first())
            if not c:
                return jsonify({'error': 'Not found'}), 404
            data = {
                'id': c.id,
                'collection_id': c.collection_id,
                'title': c.title,
                'date': c.date,
                'tag': c.tag,
                'description': c.description,
                'cover': c.cover,
                'photos': c.photos or [],
            }
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/whats-new')
@limiter.exempt
def api_whats_new():
    """Get 'What's New at Ahoy' updates - returns structured data and full list"""
    try:
        raw_data = get_all_whats_new(ttl=0)
        
        # Ensure we have the updates structure
        if not isinstance(raw_data, dict) or "updates" not in raw_data:
            return jsonify({"updates": [], "archive": [], "structured": {}})
        
        def _whats_new_slugify(text: str) -> str:
            """URL-friendly slug for What's New items (stable enough for anchors)."""
            s = (text or "").strip().lower()
            s = re.sub(r"[^a-z0-9]+", "-", s)
            s = re.sub(r"-{2,}", "-", s).strip("-")
            return s or "update"

        def _whats_new_item_slug(item: dict) -> str:
            base = _whats_new_slugify(f"{item.get('title','')}-{item.get('date','')}")
            return base

        def _get_name_of_month(month_abbr):
            """Convert month abbreviation to full name"""
            month_abbr = str(month_abbr or "")
            months = {
                "jan": "January", "feb": "February", "mar": "March", "apr": "April",
                "may": "May", "jun": "June", "jul": "July", "aug": "August",
                "sep": "September", "oct": "October", "nov": "November", "dec": "December"
            }
            if month_abbr.isdigit():
                numeric_month = int(month_abbr)
                if 1 <= numeric_month <= 12:
                    return list(months.values())[numeric_month - 1]
            return months.get(month_abbr.lower(), month_abbr.capitalize())

        # Extract all items from monthly structure and flatten
        all_items = []
        updates = raw_data.get("updates", {})
        video_index = []

        try:
            videos_data = get_all_videos(ttl=600)
        except Exception:
            videos_data = load_json_data('videos.json', {'videos': []})

        if isinstance(videos_data, dict):
            for video in videos_data.get("videos", []):
                if isinstance(video, dict):
                    video_index.append(video)
        
        if isinstance(updates, dict):
            # Sort years descending
            for year in sorted(updates.keys(), reverse=True):
                months_data = updates[year]
                if not isinstance(months_data, dict):
                    continue
                
                # Sort months descending
                month_order = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
                sorted_months = sorted(months_data.keys(), key=lambda m: month_order.index(m.lower()) if m.lower() in month_order else -1, reverse=True)
                
                for month in sorted_months:
                    sections = months_data[month]
                    if not isinstance(sections, dict):
                        continue
                    
                    for section_name, section_data in sections.items():
                        if isinstance(section_data, dict) and "items" in section_data:
                            used_slugs = set()
                            for idx, item in enumerate(section_data.get("items", [])):
                                if isinstance(item, dict):
                                    item_copy = item.copy()
                                    item_copy["year"] = year
                                    item_copy["month"] = month
                                    item_copy["section"] = section_name
                                    base = _whats_new_item_slug(item_copy)
                                    slug = base
                                    if slug in used_slugs:
                                        slug = f"{base}-{idx+1}"
                                    used_slugs.add(slug)
                                    item_copy["slug"] = slug
                                    item_copy["month_path"] = f"/whats-new/{year}/{month}"
                                    item_copy["detail_path"] = f"/whats-new/{year}/{month}/{section_name}/{slug}"
                                    if "body" not in item_copy and item_copy.get("description"):
                                        item_copy["body"] = item_copy["description"]
                                    if section_name == "videos":
                                        related_videos = []
                                        item_title = f"{item_copy.get('title', '')} {item_copy.get('description', '')}".lower()
                                        for video in video_index:
                                            video_title = str(video.get("title") or "").lower()
                                            video_desc = str(video.get("description") or "").lower()
                                            host_slug = str(video.get("host_slug") or "").lower()
                                            filmmaker_slug = str(video.get("filmmaker_slug") or "").lower()
                                            video_id = str(video.get("id") or "").lower()
                                            if (
                                                host_slug and host_slug in item_title
                                                or filmmaker_slug and filmmaker_slug in item_title
                                                or video_id and video_id in item_title
                                                or any(token in item_title for token in video_title.split()[:3] if len(token) > 3)
                                                or any(token in item_title for token in video_desc.split()[:4] if len(token) > 3)
                                            ):
                                                related_videos.append({
                                                    "title": video.get("title") or video.get("id") or "Video",
                                                    "description": video.get("description") or "Open video",
                                                    "path": f"/videos/{video.get('id')}",
                                                    "thumbnail": video.get("thumbnail"),
                                                    "shortLabel": (video.get("host") or video.get("filmmaker") or "Video")
                                                })
                                        if related_videos:
                                            # Keep the most relevant matches first and avoid card overload.
                                            item_copy["related_videos"] = related_videos[:2]
                                            if len(related_videos) == 1:
                                                item_copy["source_link"] = related_videos[0]["path"]
                                            else:
                                                item_copy["source_playlist_link"] = f"/whats-new/{year}/{month}/{section_name}/{slug}/videos"
                                    all_items.append(item_copy)
        
        # Filter out future-dated items
        today = datetime.utcnow().date().isoformat()
        all_items = [x for x in all_items if (x.get("date") or "0") <= today]

        # Sort by date (newest first), then collapse accidental duplicate titles
        # within the same section so the newest version wins.
        all_items.sort(key=lambda x: x.get("date", ""), reverse=True)

        deduped_items = []
        seen_keys = set()
        for item in all_items:
            key = (
                str(item.get("title", "")).strip().lower(),
                str(item.get("section", "")).strip().lower(),
            )
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduped_items.append(item)

        all_items = deduped_items

        deduped_archive = []
        archive_seen = set()
        archive_counts = {}
        for item in all_items:
            month_key = (item.get("year"), item.get("month"))
            archive_counts[month_key] = archive_counts.get(month_key, 0) + 1
            if month_key not in archive_seen:
                archive_seen.add(month_key)
                deduped_archive.append({
                    "year": item.get("year"),
                    "month": item.get("month"),
                    "month_name": _get_name_of_month(item.get("month")),
                    "total_items": 0,
                })

        for month_item in deduped_archive:
            month_item["total_items"] = archive_counts.get((month_item["year"], month_item["month"]), 0)

        response = jsonify({
            "updates": all_items,       # Full list
            "archive": deduped_archive, # List of months for the grid
            "structured": updates       # Raw tree for lookup
        })
        response.headers['Cache-Control'] = 'public, max-age=0, must-revalidate'
        return response
    except Exception as e:
        import logging
        logging.error(f'Error in api_whats_new: {e}', exc_info=True)
        return jsonify({"updates": [], "archive": [], "structured": {}})

        return jsonify({"updates": [], "archive": [], "structured": {}})

def _get_month_name(month_abbr):
    """Convert month abbreviation to full name"""
    month_abbr = str(month_abbr or "")
    months = {
        "jan": "January", "feb": "February", "mar": "March", "apr": "April",
        "may": "May", "jun": "June", "jul": "July", "aug": "August",
        "sep": "September", "oct": "October", "nov": "November", "dec": "December"
    }
    if month_abbr.isdigit():
        numeric_month = int(month_abbr)
        if 1 <= numeric_month <= 12:
            return list(months.values())[numeric_month - 1]
    return months.get(month_abbr.lower(), month_abbr.capitalize())

def _handle_follow_artist(artist_id, user_id):
    """Helper function to handle follow/unfollow logic"""
    # Normalize artist_id (could be slug, id, or name)
    try:
        artists_data = get_all_artists(ttl=600)
    except Exception:
        artists_data = load_json_data('artists.json', {'artists': []})
    artist = None
    for a in artists_data.get('artists', []):
        a_slug = _slugify(a.get('slug') or a.get('name', ''))
        a_id = str(a.get('id') or '')
        a_name = (a.get('name') or '').strip().lower()
        artist_id_normalized = _slugify(artist_id)
        
        if (a_slug == artist_id_normalized or 
            a_id == artist_id or 
            a_name == artist_id.strip().lower()):
            artist = a
            break
    
    if not artist:
        return None, jsonify({'error': 'Artist not found'}), 404
    
    # Use slug, id, or name as the artist identifier
    artist_identifier = artist.get('slug') or artist.get('id') or artist.get('name')
    
    try:
        with get_session() as db_session:
            # Check if already following
            existing = db_session.query(UserArtistFollow).filter(
                UserArtistFollow.user_id == user_id,
                UserArtistFollow.artist_id == str(artist_identifier)
            ).first()
            
            if existing:
                # Unfollow
                db_session.delete(existing)
                db_session.commit()
                return artist, jsonify({'following': False, 'message': 'Unfollowed artist'}), 200
            else:
                # Follow
                follow = UserArtistFollow(
                    user_id=user_id,
                    artist_id=str(artist_identifier)
                )
                db_session.add(follow)
                db_session.commit()
                return artist, jsonify({'following': True, 'message': 'Following artist'}), 200
    except Exception as e:
        return None, jsonify({'error': str(e)}), 500

@app.route('/artists/<artist_id>/follow', methods=['POST'])
def follow_artist(artist_id):
    """Follow or unfollow an artist"""
    user_id = resolve_db_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    result = _handle_follow_artist(artist_id, user_id)
    if result[0] is None:  # Error case
        return result[1], result[2]
    return result[1], result[2]

@app.route('/api/artists/follow', methods=['POST'])
def api_follow_artist():
    """API endpoint to follow an artist"""
    user_id = resolve_db_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    artist_id = data.get('artist_id') if data else None
    if not artist_id:
        return jsonify({'error': 'artist_id is required'}), 400
    
    result = _handle_follow_artist(artist_id, user_id)
    if result[0] is None:  # Error case
        return result[1], result[2]
    return result[1], result[2]

@app.route('/api/artists/unfollow', methods=['POST'])
def api_unfollow_artist():
    """API endpoint to unfollow an artist"""
    user_id = resolve_db_user_id()
    if not user_id:
        return jsonify({'error': 'Authentication required'}), 401
    
    data = request.get_json()
    artist_id = data.get('artist_id') if data else None
    if not artist_id:
        return jsonify({'error': 'artist_id is required'}), 400
    
    result = _handle_follow_artist(artist_id, user_id)
    if result[0] is None:  # Error case
        return result[1], result[2]
    return result[1], result[2]

@app.route('/api/performances')
def api_performances():
    """Get performances data"""
    # For now, return shows data as performances
    try:
        shows_data = get_all_shows(ttl=600)
    except Exception:
        shows_data = load_json_data('shows.json', {'shows': []})
    performances = []

    for show in shows_data.get('shows', []):
        # Convert shows to performances format
        performance = {
            'id': show.get('id'),
            'title': show.get('title'),
            'artist': show.get('host') or show.get('artist'),
            'venue': show.get('venue', 'Unknown Venue'),
            'date': show.get('published_date'),
            'thumbnail': show.get('thumbnail'),
            'video_url': show.get('video_url') or show.get('mp4_link'),
            'description': show.get('description'),
            'category': show.get('category', 'concert'),
            'duration': show.get('duration_seconds', 0),
            'featured': show.get('featured', False)
        }
        performances.append(performance)
    
    return jsonify({'performances': performances})

@app.route('/api/artist/<artist_name>')
def api_artist_profile(artist_name):
    """Get specific artist data"""
    try:
        artists_data = get_all_artists(ttl=600)
        music_data = get_all_tracks(ttl=600)
        shows_data = get_all_shows(ttl=600)
    except Exception:
        artists_data = load_json_data('artists.json', {'artists': []})
        music_data = load_json_data('music.json', {'tracks': []})
        shows_data = load_json_data('shows.json', {'shows': []})

    # Normalize
    try:
        slug_from_param = _slugify(artist_name)
    except Exception:
        slug_from_param = (artist_name or '').strip().lower()

    # Find artist by slug or name (case-insensitive)
    artist = None
    for a in artists_data.get('artists', []):
        a_slug = _slugify(a.get('slug') or a.get('name', ''))
        if a_slug == slug_from_param or (a.get('name', '').strip().lower() == artist_name.strip().lower()):
            artist = a
            break

    if not artist:
        return jsonify({'error': 'Artist not found'}), 404

    artist_slug = _slugify(artist.get('slug') or artist.get('name', ''))
    artist_name_lc = (artist.get('name', '') or '').strip().lower()

    # Collect tracks: by slug, by name, or by tag match
    artist_tracks = []
    for t in music_data.get('tracks', []):
        t_slug = (t.get('artist_slug') or '').strip().lower()
        t_name = (t.get('artist') or '').strip().lower()
        tags = [str(x).strip().lower() for x in (t.get('tags') or [])]
        if t_slug == artist_slug or t_name == artist_name_lc or artist_slug in tags:
            artist_tracks.append(t)

    # Collect shows: by host_slug, by host name, or tag
    artist_shows = []
    for s in shows_data.get('shows', []):
        h_slug = (s.get('host_slug') or '').strip().lower()
        h_name = (s.get('host') or '').strip().lower()
        tags = [str(x).strip().lower() for x in (s.get('tags') or [])]
        if h_slug == artist_slug or h_name == artist_name_lc or artist_slug in tags:
            artist_shows.append(s)

    resp = jsonify({'artist': artist, 'tracks': artist_tracks, 'shows': artist_shows})
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    return resp

@app.route('/api/artists/<int:artist_id>/music')
def api_artist_music(artist_id):
    """Get artist's music tracks"""
    try:
        music_data = get_all_tracks(ttl=600)
        artists_data = get_all_artists(ttl=600)
    except Exception:
        music_data = load_json_data('music.json', {'tracks': []})
        artists_data = load_json_data('artists.json', {'artists': []})
    
    # Find artist by ID
    artist = None
    for a in artists_data.get('artists', []):
        if a.get('id') == artist_id:
            artist = a
            break
    
    if not artist:
        return jsonify({'error': 'Artist not found'}), 404
    
    # Get artist's tracks
    artist_tracks = [t for t in music_data.get('tracks', []) if t.get('artist_id') == artist_id or t.get('artist') == artist.get('name')]
    
    return jsonify(artist_tracks)

@app.route('/api/artists/<int:artist_id>/shows')
def api_artist_shows(artist_id):
    """Get artist's shows"""
    try:
        shows_data = get_all_shows(ttl=600)
        artists_data = get_all_artists(ttl=600)
    except Exception:
        shows_data = load_json_data('shows.json', {'shows': []})
        artists_data = load_json_data('artists.json', {'artists': []})
    
    # Find artist by ID
    artist = None
    for a in artists_data.get('artists', []):
        if a.get('id') == artist_id:
            artist = a
            break
    
    if not artist:
        return jsonify({'error': 'Artist not found'}), 404
    
    # Get artist's shows
    artist_shows = [s for s in shows_data.get('shows', []) if s.get('host_id') == artist_id or s.get('host') == artist.get('name')]
    
    return jsonify(artist_shows)

@app.route('/api/daily-playlist')
def api_daily_playlist():
    """Generate seeded daily playlist"""
    try:
        music_data = get_all_tracks(ttl=600)
    except Exception:
        music_data = load_json_data('music.json', {'tracks': []})
    
    # Get today's seed
    today_str = datetime.now().strftime('%Y%m%d')
    seed = int(today_str)
    random.seed(seed)
    
    tracks = music_data.get('tracks', [])
    if not tracks:
        return jsonify({'playlist': [], 'message': 'No tracks available'})
    
    # Create playlist aiming for ~1 hour
    shuffled_tracks = random.sample(tracks, min(len(tracks), 20))
    playlist = []
    total_duration = 0
    
    for track in shuffled_tracks:
        duration = track.get('duration_seconds', 180)
        if total_duration < 3600 or len(playlist) == 0:
            playlist.append(track)
            total_duration += duration
        else:
            break
    
    return jsonify({
        'playlist': playlist,
        'total_duration': total_duration,
        'date': datetime.now().strftime('%Y-%m-%d'),
        'seed': seed
    })

# Removed duplicate search route - using comprehensive_search instead

# Legacy playlist endpoints removed - use /api/playlists/ instead




# Removed: /api/user/likes - use bookmarks instead (not part of MVP)
# Removed: /api/user/history - use blueprints/activity.py instead  
# Removed: /api/user/recommendations - not part of MVP

# Auth routes moved to blueprints/api/auth.py (database-based, Flask sessions)

@app.route('/api/user/profile')
@login_required
def user_profile():
    """Get user profile (includes preferences for settings sync)."""
    # Source-of-truth is the DB user row (session['user_data'] may be absent).
    prefs = getattr(current_user, "preferences", None) or {}
    return jsonify({
        "id": current_user.id,
        "email": getattr(current_user, "email", None),
        "username": getattr(current_user, "username", None),
        "display_name": getattr(current_user, "display_name", None),
        "avatar_url": getattr(current_user, "avatar_url", None),
        "preferences": prefs,
        "bio": prefs.get("bio", ""),
    })

@app.route('/api/user/profile', methods=['PUT'])
@login_required
def update_user_profile():
    """Update user profile - uses database"""
    from db import get_session
    from models import User
    data = request.json
    
    with get_session() as db_session:
        user = db_session.get(User, current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        if 'display_name' in data:
            user.display_name = data['display_name']
        if 'avatar_url' in data:
            user.avatar_url = data['avatar_url']
        prefs = dict(user.preferences or {})
        if 'preferences' in data and isinstance(data['preferences'], dict):
            prefs.update(data['preferences'])
        if 'bio' in data:
            prefs['bio'] = (data['bio'] or '').strip()[:160]
        user.preferences = prefs
        
        db_session.commit()
        return jsonify({
            'success': True,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': getattr(user, "username", None),
                'display_name': user.display_name,
                'avatar_url': user.avatar_url,
                'preferences': user.preferences or {},
                'bio': (user.preferences or {}).get('bio', ''),
            }
        })

@app.route('/api/user/avatar', methods=['POST'])
@login_required
def upload_avatar():
    """Upload user profile photo (JPEG)."""
    try:
        from db import get_session
        from models import User
        import os
        from werkzeug.utils import secure_filename
        
        if 'file' not in request.files:
            return jsonify({'error': 'No file part in the request'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'}), 400
            
        # Verify file is an image (JPEG, PNG, WebP)
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        allowed_mimetypes = {'image/jpeg', 'image/png', 'image/webp'}
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in allowed_extensions or file.mimetype not in allowed_mimetypes:
            return jsonify({'error': 'Only JPEG, PNG, or WebP images are allowed'}), 400
            
        # Create upload directory
        upload_dir = os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'avatars')
        os.makedirs(upload_dir, exist_ok=True)
        
        filename = f"avatar_{current_user.id}.jpg"
        file_path = os.path.join(upload_dir, filename)
        
        # Save file
        file.save(file_path)
        
        avatar_url = f"/static/uploads/avatars/{filename}"
        
        with get_session() as db_session:
            user = db_session.get(User, current_user.id)
            if not user:
                return jsonify({'error': 'User not found'}), 404
            user.avatar_url = avatar_url
            db_session.commit()
            
        # Also update active user cache in current context if necessary
        current_user.avatar_url = avatar_url
            
        return jsonify({
            'success': True,
            'avatar_url': avatar_url
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/user/stats')
@login_required
def get_user_stats():
    """Get user statistics - uses database"""
    from db import get_session
    from models import User, Playlist, Bookmark, PlayHistory
    from sqlalchemy import func
    
    with get_session() as db_session:
        user = db_session.get(User, current_user.id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        stats = {
            'playlists_count': db_session.query(func.count(Playlist.id)).filter(Playlist.user_id == user.id).scalar() or 0,
            'bookmarks_count': db_session.query(func.count(Bookmark.id)).filter(Bookmark.user_id == user.id).scalar() or 0,
            'play_history_count': db_session.query(func.count(PlayHistory.id)).filter(PlayHistory.user_id == user.id).scalar() or 0,
        }
        return jsonify(stats)

# Note: Saves/bookmarks are handled by blueprints/bookmarks.py
# These legacy routes are removed - use /api/bookmarks instead

# Note: Likes/recently-played features removed - not part of MVP
# Use bookmarks and play history instead

# Note: Playlists are handled by blueprints/playlists.py
# These legacy routes are removed - use /api/playlists instead

@app.route('/api/guest-data', methods=['GET'])
def get_guest_data():
    """Get current guest data for migration"""
    if 'username' in session:
        return jsonify({'error': 'User is logged in'}), 400
    
    guest_data = {
        'saves': session.get('guest_saves', []),
        'playlists': session.get('guest_playlists', []),
        'likes': session.get('guest_likes', [])
    }
    
    return jsonify(guest_data)

# Removed: /api/user/favorites - was calling non-existent functions (like_content, get_liked_content)
# Use bookmarks API instead: /api/bookmarks

# Policy Routes

@app.route('/api/debug/logs')
def get_debug_logs():
    """Get debug logs"""
    # In a real app, you'd read from log files
    # For now, return some sample logs
    logs = [
        {
            'id': 1,
            'timestamp': '10:30:15',
            'level': 'info',
            'source': 'Server',
            'message': 'Server started successfully',
            'details': None
        },
        {
            'id': 2,
            'timestamp': '10:30:20',
            'level': 'error',
            'source': 'API',
            'message': 'Save operation failed',
            'details': 'Mock error for testing - This is not a real error'
        },
        {
            'id': 3,
            'timestamp': '10:30:25',
            'level': 'warning',
            'source': 'Database',
            'message': 'Session expired',
            'details': 'User session expired after 30 minutes of inactivity'
        }
    ]
    return jsonify({'logs': logs})

@app.route('/api/debug/users')
@admin_required
def get_debug_users():
    """Get user details for debug - uses database"""
    from db import get_session
    from models import User
    try:
        with get_session() as db_session:
            users = db_session.query(User).order_by(User.created_at.desc()).limit(500).all()
            user_list = []
            for user in users:
                user_list.append({
                    'id': user.id,
                    'email': user.email,
                    'display_name': user.display_name,
                    'created_at': user.created_at.isoformat() if user.created_at else '',
                    'last_active_at': user.last_active_at.isoformat() if user.last_active_at else '',
                    'is_admin': user.is_admin,
                    'disabled': user.disabled
                })
            
            # Sort by creation date (newest first)
            user_list.sort(key=lambda x: x['created_at'], reverse=True)
            
            return jsonify({
                'total_users': len(user_list),
                'users': user_list
            })
    except Exception as e:
        return jsonify({'users': [], 'error': str(e)})

@app.route('/api/debug/test-save', methods=['POST'])
def test_save():
    """Test save functionality"""
    try:
        data = request.json
        content_type = data.get('type', 'track')
        content_id = data.get('id', 'test_id')
        content_data = data.get('data', {})
        
        # Test the save functionality
        username = current_user.id if current_user.is_authenticated else None
        
        if not username:
            # Test guest save
            if 'guest_saves' not in session:
                session['guest_saves'] = []
            
            session['guest_saves'].append({
                'type': content_type,
                'id': content_id,
                'data': content_data,
                'saved_at': datetime.now().isoformat()
            })
            session.modified = True
            
            return jsonify({
                'success': True,
                'message': 'Guest save test successful',
                'guest': True
            })
        else:
            # Test user save - use bookmarks API instead
            from blueprints.bookmarks import bp as bookmarks_bp
            # Note: This test route is deprecated - use /api/bookmarks directly
            return jsonify({
                'success': True,
                'message': 'Use /api/bookmarks endpoint for saving content',
                'guest': False
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'message': 'Save test failed with error'
        }), 500

# Static files
@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory('static', filename)

def find_available_port(start_port=5001, end_port=5020):
    """Find an available port between start_port and end_port"""
    import socket
    for port in range(start_port, end_port + 1):
        try:
            # Try to bind to the port on all interfaces (0.0.0.0) to match gunicorn behavior
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))
                return port
        except OSError:
            # Port is in use, try next one
            continue
    return None

@app.route('/api/debug/sample-accounts')
def debug_sample_accounts():
    """Get sample accounts for testing"""
    sample_accounts = [
        {
            'username': 'musiclover',
            'password': 'music123',
            'display_name': 'Music Lover',
            'email': 'musiclover@ahoy.com',
            'avatar': '/static/img/default-avatar.png',
            'stats': {
                'saved_tracks': 45,
                'saved_shows': 12,
                'liked_content': 78,
                'playlists': 8
            }
        },
        {
            'username': 'indieexplorer',
            'password': 'indie123',
            'display_name': 'Indie Explorer',
            'email': 'indie@ahoy.com',
            'avatar': '/static/img/default-avatar.png',
            'stats': {
                'saved_tracks': 23,
                'saved_shows': 18,
                'liked_content': 56,
                'playlists': 5
            }
        },
        {
            'username': 'showbinger',
            'password': 'shows123',
            'display_name': 'Show Binger',
            'email': 'shows@ahoy.com',
            'avatar': '/static/img/default-avatar.png',
            'stats': {
                'saved_tracks': 12,
                'saved_shows': 35,
                'liked_content': 42,
                'playlists': 3
            }
        },
        {
            'username': 'newuser',
            'password': 'new123',
            'display_name': 'New User',
            'email': 'new@ahoy.com',
            'avatar': '/static/img/default-avatar.png',
            'stats': {
                'saved_tracks': 0,
                'saved_shows': 0,
                'liked_content': 0,
                'playlists': 0
            }
        }
    ]
    
    return jsonify({'accounts': sample_accounts})

@app.route('/api/debug/data/<data_type>')
@admin_required
def debug_data_viewer(data_type):
    """View application data for debugging"""
    if data_type == 'users':
        from db import get_session
        from models import User
        with get_session() as db_session:
            users = db_session.query(User).order_by(User.created_at.desc()).limit(500).all()
            return jsonify([{
                'id': u.id,
                'email': u.email,
                'display_name': u.display_name,
                'created_at': u.created_at.isoformat() if u.created_at else None
            } for u in users])
    elif data_type == 'music':
        try:
            return jsonify(get_all_tracks(ttl=600))
        except Exception:
            return jsonify(load_json_data('music.json', {'tracks': []}))
    elif data_type == 'shows':
        try:
            return jsonify(get_all_shows(ttl=600))
        except Exception:
            return jsonify(load_json_data('shows.json', {'shows': []}))
    elif data_type == 'artists':
        try:
            return jsonify(get_all_artists(ttl=600))
        except Exception:
            return jsonify(load_json_data('artists.json', {'artists': []}))
    else:
        return jsonify({'error': 'Unknown data type'}), 400

@app.route('/api/debug/status')
def debug_system_status():
    """Get system status for debugging"""
    import os

    from db import get_session
    from models import User
    from sqlalchemy import func
    
    with get_session() as db_session:
        user_count = db_session.query(func.count(User.id)).scalar() or 0
    
    status = {
        'timestamp': datetime.now().isoformat(),
        'app': {
            'users_count': user_count,
            'session_count': len(session),
            'cache_status': 'active'
        },
        'data_files': {
            'users_file': os.path.exists('data/users.json'),
            'music_file': os.path.exists('static/data/music.json'),
            'shows_file': os.path.exists('static/data/shows.json'),
            'artists_file': os.path.exists('static/data/artists.json')
        }
    }

    return jsonify(status)

# Legacy /auth routes removed - now handled by the SPA


@app.route('/googleb3a3eb3401de50dc.html')
def google_search_console_verification():
    """Google Search Console verification file."""
    return send_from_directory('static', 'googleb3a3eb3401de50dc.html', mimetype='text/html')

# Legacy server-side pages removed - now handled by the SPA

@app.route('/api/admin/stats', methods=['GET'])
@login_required
@_admin_session_required
def admin_stats():
    """Read-only admin stats (users + merch orders + analytics)."""
    from db import get_session
    from models import (
        User, Purchase, PlayHistory, ListeningSession, ListeningTotal,
        Bookmark, UserArtistFollow, Tip
    )
    from sqlalchemy import func
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    active_since = now - timedelta(days=30)
    week_ago = now - timedelta(days=7)
    day_ago = now - timedelta(days=1)

    with get_session() as s:
        # User stats
        total_users = int(s.query(func.count(User.id)).scalar() or 0)
        active_users = int(
            s.query(func.count(User.id))
            .filter(User.last_active_at.isnot(None))
            .filter(User.last_active_at >= active_since)
            .scalar()
            or 0
        )
        new_users_7d = int(
            s.query(func.count(User.id))
            .filter(User.created_at >= week_ago)
            .scalar() or 0
        )
        new_users_24h = int(
            s.query(func.count(User.id))
            .filter(User.created_at >= day_ago)
            .scalar() or 0
        )

        # Order stats
        total_orders = int(s.query(func.count(Purchase.id)).filter(Purchase.type == "merch").scalar() or 0)
        pending_orders = int(
            s.query(func.count(Purchase.id)).filter(Purchase.type == "merch", Purchase.status == "pending").scalar() or 0
        )
        paid_orders = int(
            s.query(func.count(Purchase.id)).filter(Purchase.type == "merch", Purchase.status == "paid").scalar() or 0
        )
        fulfilled_orders = int(
            s.query(func.count(Purchase.id)).filter(Purchase.type == "merch", Purchase.status == "fulfilled").scalar() or 0
        )

        # Play statistics
        total_plays = int(s.query(func.count(PlayHistory.id)).scalar() or 0)
        plays_7d = int(
            s.query(func.count(PlayHistory.id))
            .filter(PlayHistory.played_at >= week_ago)
            .scalar() or 0
        )
        plays_24h = int(
            s.query(func.count(PlayHistory.id))
            .filter(PlayHistory.played_at >= day_ago)
            .scalar() or 0
        )
        unique_tracks_played = int(
            s.query(func.count(func.distinct(PlayHistory.media_id)))
            .filter(PlayHistory.media_type == "track")
            .scalar() or 0
        )

        # Listening time statistics
        total_listening_seconds = int(
            s.query(func.sum(ListeningTotal.total_seconds)).scalar() or 0
        )
        total_listening_hours = round(total_listening_seconds / 3600, 1)
        
        # Listening sessions
        total_sessions = int(s.query(func.count(ListeningSession.id)).scalar() or 0)
        sessions_7d = int(
            s.query(func.count(ListeningSession.id))
            .filter(ListeningSession.started_at >= week_ago)
            .scalar() or 0
        )
        radio_sessions = int(
            s.query(func.count(ListeningSession.id))
            .filter(ListeningSession.source == "radio")
            .scalar() or 0
        )
        manual_sessions = int(
            s.query(func.count(ListeningSession.id))
            .filter(ListeningSession.source == "manual")
            .scalar() or 0
        )

        # Engagement stats
        total_bookmarks = int(s.query(func.count(Bookmark.id)).scalar() or 0)
        total_follows = int(s.query(func.count(UserArtistFollow.id)).scalar() or 0)
        total_tips = int(s.query(func.count(Tip.id)).scalar() or 0)
        total_tip_amount = float(
            s.query(func.sum(Tip.amount)).scalar() or 0
        )

    return jsonify({
        "users": {
            "total": total_users,
            "active_30d": active_users,
            "new_7d": new_users_7d,
            "new_24h": new_users_24h,
        },
        "orders": {
            "total": total_orders,
            "pending": pending_orders,
            "paid": paid_orders,
            "fulfilled": fulfilled_orders,
        },
        "plays": {
            "total": total_plays,
            "last_7d": plays_7d,
            "last_24h": plays_24h,
            "unique_tracks": unique_tracks_played,
        },
        "listening": {
            "total_hours": total_listening_hours,
            "total_seconds": total_listening_seconds,
            "total_sessions": total_sessions,
            "sessions_7d": sessions_7d,
            "radio_sessions": radio_sessions,
            "manual_sessions": manual_sessions,
        },
        "engagement": {
            "bookmarks": total_bookmarks,
            "follows": total_follows,
            "tips": total_tips,
            "tip_amount": round(total_tip_amount, 2),
        },
    })


@app.route('/api/admin/analytics', methods=['GET'])
@login_required
@_admin_session_required
def admin_analytics():
    """Detailed analytics for admin dashboard."""
    from db import get_session
    from models import (
        User, PlayHistory, ListeningSession, Bookmark,
        UserArtistFollow, Tip
    )
    from sqlalchemy import func
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    with get_session() as s:
        # Most active users (by play count)
        top_users_by_plays = s.query(
            User.id,
            User.username,
            User.email,
            func.count(PlayHistory.id).label('play_count')
        ).join(
            PlayHistory, User.id == PlayHistory.user_id
        ).group_by(
            User.id, User.username, User.email
        ).order_by(
            func.count(PlayHistory.id).desc()
        ).limit(10).all()

        # Most played tracks
        top_tracks = s.query(
            PlayHistory.media_id,
            func.count(PlayHistory.id).label('play_count')
        ).filter(
            PlayHistory.media_type == "track"
        ).group_by(
            PlayHistory.media_id
        ).order_by(
            func.count(PlayHistory.id).desc()
        ).limit(20).all()

        # Plays over time (last 7 days)
        daily_plays = []
        for i in range(7):
            day_start = (now - timedelta(days=6-i)).replace(hour=0, minute=0, second=0, microsecond=0)
            day_end = day_start + timedelta(days=1)
            count = int(
                s.query(func.count(PlayHistory.id))
                .filter(PlayHistory.played_at >= day_start)
                .filter(PlayHistory.played_at < day_end)
                .scalar() or 0
            )
            daily_plays.append({
                "date": day_start.isoformat(),
                "count": count
            })

        # Listening time by source
        radio_time = int(
            s.query(func.sum(ListeningSession.seconds))
            .filter(ListeningSession.source == "radio")
            .scalar() or 0
        )
        manual_time = int(
            s.query(func.sum(ListeningSession.seconds))
            .filter(ListeningSession.source == "manual")
            .scalar() or 0
        )

        # User engagement breakdown
        users_with_plays = int(
            s.query(func.count(func.distinct(PlayHistory.user_id))).scalar() or 0
        )
        users_with_bookmarks = int(
            s.query(func.count(func.distinct(Bookmark.user_id))).scalar() or 0
        )
        users_with_follows = int(
            s.query(func.count(func.distinct(UserArtistFollow.user_id))).scalar() or 0
        )
        users_with_tips = int(
            s.query(func.count(func.distinct(Tip.user_id))).scalar() or 0
        )

        # Recent activity (last 24h)
        recent_plays_24h = int(
            s.query(func.count(PlayHistory.id))
            .filter(PlayHistory.played_at >= (now - timedelta(days=1)))
            .scalar() or 0
        )
        recent_bookmarks_24h = int(
            s.query(func.count(Bookmark.id))
            .filter(Bookmark.created_at >= (now - timedelta(days=1)))
            .scalar() or 0
        )
        recent_follows_24h = int(
            s.query(func.count(UserArtistFollow.id))
            .filter(UserArtistFollow.created_at >= (now - timedelta(days=1)))
            .scalar() or 0
        )

    return jsonify({
        "top_users": [
            {
                "id": u.id,
                "username": u.username or u.email,
                "email": u.email,
                "play_count": u.play_count
            }
            for u in top_users_by_plays
        ],
        "top_tracks": [
            {
                "media_id": t.media_id,
                "play_count": t.play_count
            }
            for t in top_tracks
        ],
        "daily_plays": daily_plays,
        "listening_by_source": {
            "radio_hours": round(radio_time / 3600, 1),
            "manual_hours": round(manual_time / 3600, 1),
            "radio_seconds": radio_time,
            "manual_seconds": manual_time,
        },
        "user_engagement": {
            "users_with_plays": users_with_plays,
            "users_with_bookmarks": users_with_bookmarks,
            "users_with_follows": users_with_follows,
            "users_with_tips": users_with_tips,
        },
        "recent_24h": {
            "plays": recent_plays_24h,
            "bookmarks": recent_bookmarks_24h,
            "follows": recent_follows_24h,
        },
    })


@app.route('/api/admin/users', methods=['GET'])
@login_required
@_admin_session_required
def admin_users():
    """Get list of users for admin dashboard."""
    from db import get_session
    from models import User
    from sqlalchemy import func

    limit = 100
    try:
        limit = int(request.args.get("limit") or "100")
        limit = max(1, min(500, limit))
    except Exception:
        limit = 100

    with get_session() as s:
        rows = (
            s.query(User)
            .order_by(User.created_at.desc())
            .limit(limit)
            .all()
        )
        users = [{
            "id": u.id,
            "email": u.email,
            "username": u.username,
            "display_name": u.display_name,
            "created_at": u.created_at.isoformat() if u.created_at else None,
            "last_active_at": u.last_active_at.isoformat() if u.last_active_at else None,
            "is_admin": u.is_admin,
            "disabled": u.disabled,
        } for u in rows]

        # Get play counts for each user
        play_counts = {}
        if users:
            user_ids = [u["id"] for u in users]
            from models import PlayHistory
            counts = (
                s.query(
                    PlayHistory.user_id,
                    func.count(PlayHistory.id).label('count')
                )
                .filter(PlayHistory.user_id.in_(user_ids))
                .group_by(PlayHistory.user_id)
                .all()
            )
            play_counts = {user_id: count for user_id, count in counts}

        # Add play counts to users
        for user in users:
            user["play_count"] = play_counts.get(user["id"], 0)

    return jsonify({"users": users})


@app.route('/api/admin/orders', methods=['GET'])
@login_required
@_admin_session_required
def admin_orders():
    """Read-only list of merch orders."""
    from db import get_session
    from models import Purchase

    limit = 200
    try:
        limit = int(request.args.get("limit") or "200")
        limit = max(1, min(500, limit))
    except Exception:
        limit = 200

    with get_session() as s:
        rows = (
            s.query(Purchase)
            .filter(Purchase.type == "merch")
            .order_by(Purchase.created_at.desc())
            .limit(limit)
            .all()
        )
        orders = [{
            "id": p.id,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "status": p.status,
            "item_id": p.item_id,
            "qty": p.qty,
            "amount": p.amount,
            "total": p.total,
            "stripe_id": p.stripe_id,
            "tracking_number": p.tracking_number,
            "fulfilled_at": p.fulfilled_at.isoformat() if p.fulfilled_at else None,
            "shipping": {
                "name": p.shipping_name,
                "line1": p.shipping_line1,
                "line2": p.shipping_line2,
                "city": p.shipping_city,
                "state": p.shipping_state,
                "postal_code": p.shipping_postal_code,
                "country": p.shipping_country,
            } if p.shipping_name else None,
        } for p in rows]
    return jsonify({"orders": orders})


@app.route('/api/admin/orders/<int:order_id>/fulfill', methods=['PUT'])
@login_required
@_admin_session_required
def admin_fulfill_order(order_id):
    """Mark a merch order as fulfilled with optional tracking number."""
    from db import get_session
    from models import Purchase, User
    from utils.csrf import validate_csrf
    from datetime import datetime

    # Validate CSRF token from header
    csrf_token = request.headers.get("X-CSRF-Token")
    session_token = session.get("csrf_token")
    if not csrf_token or not session_token or csrf_token != session_token:
        return jsonify({"error": "Invalid CSRF token"}), 400

    data = request.json or {}
    tracking_number = (data.get("tracking_number") or "").strip()[:100] or None

    with get_session() as s:
        purchase = s.query(Purchase).filter(
            Purchase.id == order_id,
            Purchase.type == "merch"
        ).first()

        if not purchase:
            return jsonify({"error": "Order not found"}), 404

        if purchase.status == "fulfilled":
            return jsonify({"error": "Order already fulfilled"}), 400

        if purchase.status != "paid":
            return jsonify({"error": "Only paid orders can be fulfilled"}), 400

        # Update the purchase
        purchase.status = "fulfilled"
        purchase.fulfilled_at = datetime.utcnow()
        if tracking_number:
            purchase.tracking_number = tracking_number

        # Get buyer email if user exists
        buyer_email = None
        if purchase.user_id:
            user = s.query(User).filter(User.id == purchase.user_id).first()
            if user:
                buyer_email = user.email

        # Build shipping address string for email
        shipping_address = None
        if purchase.shipping_name:
            addr_parts = [purchase.shipping_name]
            if purchase.shipping_line1:
                addr_parts.append(purchase.shipping_line1)
            if purchase.shipping_line2:
                addr_parts.append(purchase.shipping_line2)
            city_line = ", ".join(filter(None, [
                purchase.shipping_city,
                purchase.shipping_state,
                purchase.shipping_postal_code
            ]))
            if city_line:
                addr_parts.append(city_line)
            if purchase.shipping_country:
                addr_parts.append(purchase.shipping_country)
            shipping_address = "\n".join(addr_parts)

        s.commit()

        # Send notification email
        try:
            from services.notifications import notify_order_fulfilled
            notify_order_fulfilled(
                purchase_id=purchase.id,
                item_name=purchase.item_id,
                buyer_email=buyer_email,
                tracking_number=tracking_number,
                shipping_address=shipping_address
            )
        except Exception as e:
            current_app.logger.warning(f"Failed to send fulfillment notification: {e}")

    return jsonify({
        "success": True,
        "message": "Order marked as fulfilled",
        "order_id": order_id,
        "tracking_number": tracking_number
    })


@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
@login_required
@_admin_session_required
def admin_delete_user(user_id):
    return jsonify({"error": "read_only_admin"}), 403


@app.route('/api/admin/users/<int:user_id>', methods=['PATCH'])
@login_required
@_admin_session_required
def admin_update_user(user_id):
    """Toggle user disabled flag (basic user management)."""
    from db import get_session
    from models import User

    data = request.get_json() or {}
    disabled = data.get('disabled')
    if disabled is None:
        return jsonify({"error": "Missing 'disabled' in body"}), 400

    # Don't allow disabling yourself
    if user_id == current_user.id:
        return jsonify({"error": "Cannot change your own account"}), 400

    with get_session() as s:
        user = s.query(User).filter(User.id == user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        user.disabled = bool(disabled)
        s.commit()
    return jsonify({"success": True, "disabled": bool(disabled)})


@app.route('/api/admin/users/<int:user_id>/reset-password', methods=['POST'])
@login_required
@_admin_session_required
def admin_reset_password(user_id):
    return jsonify({"error": "read_only_admin"}), 403

@app.route('/api/feedback', methods=['POST'])
@limiter.limit("5/minute")
def submit_feedback():
    """Submit user feedback"""
    try:
        data = request.json
        feedback_data = {
            'id': str(uuid.uuid4()),
            'timestamp': datetime.now().isoformat(),
            'user_agent': request.headers.get('User-Agent', ''),
            'ip_address': request.remote_addr,
            'username': session.get('username', 'anonymous'),
            'feedback_type': data.get('type', 'general'),
            'rating': data.get('rating', 0),
            'ui_rating': data.get('ui_rating', 0),
            'performance_rating': data.get('performance_rating', 0),
            'content_rating': data.get('content_rating', 0),
            'subject': data.get('subject', ''),
            'message': data.get('message', ''),
            'suggestions': data.get('suggestions', ''),
            'bugs': data.get('bugs', ''),
            'feature_requests': data.get('feature_requests', ''),
            'contact_email': data.get('contact_email', ''),
            'anonymous': data.get('anonymous', False),
            'status': 'new'
        }
        
        # Load existing feedback
        feedback_file = 'data/feedback.json'
        try:
            with open(feedback_file, 'r') as f:
                feedback_list = json.load(f)
        except FileNotFoundError:
            feedback_list = []
        
        # Add new feedback
        feedback_list.append(feedback_data)
        
        # Save feedback
        os.makedirs(os.path.dirname(feedback_file), exist_ok=True)
        with open(feedback_file, 'w') as f:
            json.dump(feedback_list, f, indent=2)
        
        return jsonify({'success': True, 'message': 'Thank you for your feedback!'})
        
    except Exception as e:
        print(f"Error submitting feedback: {e}")
        return jsonify({'error': 'Failed to submit feedback'}), 500

@app.route('/api/feedback', methods=['GET'])
@admin_required
def get_feedback():
    """Get feedback (admin only)"""
    
    try:
        feedback_file = 'data/feedback.json'
        with open(feedback_file, 'r') as f:
            feedback_list = json.load(f)
        
        # Sort by timestamp (newest first)
        feedback_list.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return jsonify({'feedback': feedback_list})
        
    except FileNotFoundError:
        return jsonify({'feedback': []})
    except Exception as e:
        print(f"Error loading feedback: {e}")
        return jsonify({'error': 'Failed to load feedback'}), 500

@app.route('/api/feedback/<feedback_id>/status', methods=['PUT'])
@admin_required
def update_feedback_status():
    """Update feedback status (admin only)"""
    
    try:
        data = request.json
        feedback_id = request.view_args['feedback_id']
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'error': 'Status required'}), 400
        
        feedback_file = 'data/feedback.json'
        with open(feedback_file, 'r') as f:
            feedback_list = json.load(f)
        
        # Find and update feedback
        for feedback in feedback_list:
            if feedback['id'] == feedback_id:
                feedback['status'] = new_status
                feedback['updated_at'] = datetime.now().isoformat()
                break
        else:
            return jsonify({'error': 'Feedback not found'}), 404
        
        # Save updated feedback
        with open(feedback_file, 'w') as f:
            json.dump(feedback_list, f, indent=2)
        
        return jsonify({'success': True, 'message': 'Status updated'})
        
    except Exception as e:
        print(f"Error updating feedback status: {e}")
        return jsonify({'error': 'Failed to update status'}), 500

# Removed duplicate search route - using comprehensive_search instead

# ========================================
# 🔍 COMPREHENSIVE SEARCH API
# ========================================

@app.route('/api/search', methods=['GET'])
def comprehensive_search():
    """Comprehensive search API with TF-IDF scoring and fuzzy matching"""
    try:
        from search_indexer import search_index
        
        # Get query parameters
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 20)), 100)  # Cap at 100
        offset = int(request.args.get('offset', 0))
        kinds = request.args.get('kinds', '').split(',') if request.args.get('kinds') else None
        sort = request.args.get('sort', 'relevance')
        
        # Validate sort parameter
        if sort not in ['relevance', 'recent']:
            sort = 'relevance'
        
        # Perform search
        results = search_index.search(
            query=query,
            limit=limit,
            offset=offset,
            kinds=kinds,
            sort=sort
        )
        
        return jsonify(results)
        
    except Exception as e:
        print(f"Error in comprehensive search: {e}")
        return jsonify({'error': 'Search failed', 'results': [], 'total': 0}), 500

@app.route('/api/search/reindex', methods=['POST'])
def reindex_search():
    """Reindex the search data (admin endpoint)"""
    try:
        from search_indexer import search_index
        
        data_sources = {
            'music': 'static/data/music.json',
            'shows': 'static/data/shows.json',
            'artists': 'static/data/artists.json'
        }
        
        search_index.reindex(data_sources)
        
        return jsonify({
            'success': True,
            'message': f'Search index rebuilt with {search_index.total_docs} documents'
        })
        
    except Exception as e:
        print(f"Error reindexing search: {e}")
        return jsonify({'error': 'Reindex failed'}), 500

@app.route('/api/suggest', methods=['GET'])
def search_suggestions():
    """Typeahead suggestions for search header"""
    try:
        from search_indexer import search_index
        
        query = request.args.get('q', '').strip()
        limit = min(int(request.args.get('limit', 8)), 20)  # Cap at 20
        
        if not query or len(query) < 2:
            return jsonify({
                'query': query,
                'items': []
            })
        
        suggestions = []
        query_lower = query.lower()
        
        # Get all documents for suggestion building
        all_docs = list(search_index.documents.values())
        
        # 1. Matching titles (prefix-boosted)
        title_matches = []
        for doc in all_docs:
            title = doc.get('title', '')
            if title.lower().startswith(query_lower):
                title_matches.append({
                    'label': f"{title} — {doc.get('fields', {}).get('artist', doc.get('fields', {}).get('host', ''))}",
                    'kind': doc.get('kind', ''),
                    'url': doc.get('url', '#'),
                    'score': 10.0  # High score for prefix matches
                })
            elif query_lower in title.lower():
                title_matches.append({
                    'label': f"{title} — {doc.get('fields', {}).get('artist', doc.get('fields', {}).get('host', ''))}",
                    'kind': doc.get('kind', ''),
                    'url': doc.get('url', '#'),
                    'score': 5.0  # Lower score for contains matches
                })
        
        # Sort by score and add to suggestions
        title_matches.sort(key=lambda x: x['score'], reverse=True)
        suggestions.extend(title_matches[:limit//2])
        
        # 2. Top tags/genres starting with query
        tag_matches = []
        seen_tags = set()
        
        for doc in all_docs:
            # Get tags
            tags = doc.get('tags', [])
            for tag in tags:
                if tag.lower().startswith(query_lower) and tag not in seen_tags:
                    tag_matches.append({
                        'label': f"#{tag}",
                        'kind': 'tag',
                        'url': f"/search?q=tag:{tag}",
                        'score': 8.0
                    })
                    seen_tags.add(tag)
            
            # Get genres
            genres = doc.get('genres', [])
            for genre in genres:
                if genre.lower().startswith(query_lower) and genre not in seen_tags:
                    tag_matches.append({
                        'label': f"#{genre}",
                        'kind': 'genre',
                        'url': f"/search?q=genre:{genre}",
                        'score': 7.0
                    })
                    seen_tags.add(genre)
        
        # Sort and add tag matches
        tag_matches.sort(key=lambda x: x['score'], reverse=True)
        suggestions.extend(tag_matches[:limit//4])
        
        # 3. Popular artists/shows where name starts with query
        artist_matches = []
        seen_artists = set()
        
        for doc in all_docs:
            artist_name = doc.get('fields', {}).get('artist', '') or doc.get('fields', {}).get('host', '')
            if artist_name and artist_name.lower().startswith(query_lower) and artist_name not in seen_artists:
                artist_matches.append({
                    'label': f"🎤 {artist_name}",
                    'kind': 'artist',
                    'url': doc.get('url', '#'),
                    'score': 6.0
                })
                seen_artists.add(artist_name)
        
        # Sort and add artist matches
        artist_matches.sort(key=lambda x: x['score'], reverse=True)
        suggestions.extend(artist_matches[:limit//4])
        
        # Sort all suggestions by score and limit
        suggestions.sort(key=lambda x: x['score'], reverse=True)
        suggestions = suggestions[:limit]
        
        # Add some fun suggestions for empty or short queries
        if len(query) < 3:
            fun_suggestions = [
                {'label': '🎵 New Releases', 'kind': 'new', 'url': '/search?q=recent', 'score': 8.0},
                {'label': '⭐ Staff Picks', 'kind': 'featured', 'url': '/search?q=featured', 'score': 7.0},
                {'label': '🎧 Discover', 'kind': 'discover', 'url': '/search?q=discover', 'score': 6.0}
            ]
            suggestions = fun_suggestions[:limit]
        
        return jsonify({
            'query': query,
            'items': suggestions
        })
        
    except Exception as e:
        print(f"Error in search suggestions: {e}")
        return jsonify({
            'query': query if 'query' in locals() else '',
            'items': []
        }), 500


@app.route('/api/build-info', methods=['GET'])
def get_build_info():
    """Return build information. Reads from electron/build-info.json when available (baked at build time)."""
    try:
        build_info_path = os.path.join(os.path.dirname(__file__), 'electron', 'build-info.json')
        if os.path.exists(build_info_path):
            with open(build_info_path, 'r') as f:
                return jsonify(json.load(f))

        version = None
        pkg_path = os.path.join(os.path.dirname(__file__), 'package.json')
        if os.path.exists(pkg_path):
            try:
                with open(pkg_path, 'r') as f:
                    version = json.load(f).get('version')
            except Exception:
                pass

        if not version:
            from ahoy.version import __version__
            version = __version__

        return jsonify({"version": version, "commits": []})
    except Exception as e:
        app.logger.exception("build-info failed")
        return jsonify({"error": "unavailable"}), 500


@app.route('/api/admin/distribute/android', methods=['POST'])
@_admin_session_required
def distribute_android():
    """Run Android build pipeline: npm build → cap sync → gradle bundleRelease."""
    import subprocess
    import threading

    root = os.path.dirname(os.path.abspath(__file__))
    spa_dir = os.path.join(root, 'spa')
    android_dir = os.path.join(root, 'android')

    steps = [
        {'label': 'SPA build', 'cmd': ['npm', 'run', 'build'], 'cwd': spa_dir},
        {'label': 'Capacitor sync', 'cmd': ['npx', 'cap', 'sync', 'android'], 'cwd': root},
        {'label': 'Gradle bundleRelease', 'cmd': ['./gradlew', 'bundleRelease'], 'cwd': android_dir},
    ]

    results = []
    for step in steps:
        try:
            proc = subprocess.run(
                step['cmd'],
                cwd=step['cwd'],
                capture_output=True,
                text=True,
                timeout=300,
            )
            results.append({
                'step': step['label'],
                'ok': proc.returncode == 0,
                'stdout': proc.stdout[-3000:] if proc.stdout else '',
                'stderr': proc.stderr[-1000:] if proc.stderr else '',
            })
            if proc.returncode != 0:
                break
        except subprocess.TimeoutExpired:
            results.append({'step': step['label'], 'ok': False, 'stdout': '', 'stderr': 'Timed out after 300s'})
            break
        except Exception as e:
            results.append({'step': step['label'], 'ok': False, 'stdout': '', 'stderr': str(e)})
            break

    aab_path = os.path.join(android_dir, 'app/build/outputs/bundle/release/app-release.aab')
    aab_exists = os.path.exists(aab_path)
    overall_ok = all(r['ok'] for r in results) and aab_exists

    return jsonify({'ok': overall_ok, 'steps': results, 'aab': aab_path if aab_exists else None})


@app.route('/api/beta/signup', methods=['POST'])
@limiter.limit("5 per hour")
def beta_signup():
    """Handle beta tester signup and send email notification."""
    try:
        data = request.get_json()
        email = data.get('email', '').strip()
        platform = data.get('platform', 'unknown')
        
        if not email or '@' not in email:
            return jsonify({"error": "Valid email is required"}), 400
            
        from services.emailer import send_email
        from db import get_session
        from flask_login import current_user
        
        # Save to database
        try:
            with get_session() as db_session:
                new_signup = BetaSignup(
                    email=email,
                    platform=platform,
                    user_id=current_user.id if current_user.is_authenticated else None
                )
                db_session.add(new_signup)
                db_session.commit()
        except Exception as db_err:
            current_app.logger.error(f"Failed to save beta signup to DB: {db_err}")
            # Continue anyway so user gets their email
        
        # Notify admin
        admin_email = os.getenv("AHOY_ADMIN_EMAIL", "alex@littlemarket.org")
        send_email(
            to_email=admin_email,
            subject=f"New Beta Tester Signup: {email}",
            text=f"New beta tester signup for {platform} platform.\nEmail: {email}",
            html=f"<p>New beta tester signup for <b>{platform}</b> platform.</p><p>Email: {email}</p>"
        )
        
        # Send confirmation to user
        send_email(
            to_email=email,
            subject="Welcome to the Ahoy Beta Program! ⚓",
            text="Thanks for signing up for the Ahoy beta! You're now eligible for free stickers for life. We'll send instructions on how to join the Android or iOS beta soon.",
            html="""
            <h1>Welcome to the Ahoy Beta Program! ⚓</h1>
            <p>Thanks for signing up to be a beta tester. Because you joined early, you've earned <b>free stickers for life!</b></p>
            <p>We will send you a follow-up email shortly with specific instructions for your platform.</p>
            <p>Fair winds!</p>
            """
        )
        
        return jsonify({"ok": True, "message": "Signup successful! Check your email for next steps."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ========================================
# 🕸️ SEO & UTILITY ROUTES
# ========================================

@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt with sitemap reference."""
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /ops/",
        "Disallow: /admin",
        "Disallow: /api/",
        f"Sitemap: {request.url_root.rstrip('/')}/sitemap.xml"
    ]
    return Response("\n".join(lines), mimetype='text/plain')

@app.route('/sitemap.xml')
def sitemap_xml():
    """Generate dynamic sitemap.xml for SEO."""
    from services.content_db import content_db
    
    pages = []
    now = datetime.now().strftime("%Y-%m-%d")
    
    # Static core pages
    static_routes = [
        '', '/music', '/shows', '/artists', '/podcasts', '/events', 
        '/live-tv', '/radio', '/about', '/whats-new'
    ]
    for route in static_routes:
        pages.append({
            'loc': f"{request.url_root.rstrip('/')}{route}",
            'lastmod': now,
            'changefreq': 'daily',
            'priority': '1.0' if not route else '0.8'
        })
    
    # Dynamic Content
    try:
        # Artists
        for artist in content_db.get_artists():
            slug = artist.get('slug') or artist.get('id')
            if slug:
                pages.append({
                    'loc': f"{request.url_root.rstrip('/')}/artists/{slug}",
                    'lastmod': now, 'changefreq': 'weekly', 'priority': '0.7'
                })
        
        # Shows
        for show in content_db.get_shows():
            slug = show.get('slug') or show.get('id')
            if slug:
                pages.append({
                    'loc': f"{request.url_root.rstrip('/')}/videos?play={slug}",
                    'lastmod': now, 'changefreq': 'weekly', 'priority': '0.6'
                })
                
        # Podcasts
        for show in content_db.get_podcasts():
            slug = show.get('slug') or show.get('id')
            if slug:
                pages.append({
                    'loc': f"{request.url_root.rstrip('/')}/podcasts/{slug}",
                    'lastmod': now, 'changefreq': 'weekly', 'priority': '0.6'
                })
    except Exception as e:
        app.logger.error(f"Sitemap generation error: {e}")

    sitemap_template = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{% for page in pages %}
  <url>
    <loc>{{ page.loc }}</loc>
    <lastmod>{{ page.lastmod }}</lastmod>
    <changefreq>{{ page.changefreq }}</changefreq>
    <priority>{{ page.priority }}</priority>
  </url>
{% endfor %}
</urlset>"""
    
    from flask import render_template_string
    return Response(render_template_string(sitemap_template, pages=pages), mimetype='application/xml')


# --- SPA (Vue) fallback: serve index.html for client routes; assets from spa-dist ---
# Registered last so they only match when no other route does.
_SPA_DIST = Path(__file__).resolve().parent / "spa-dist"

# Keep the sidebar brand mark legible if a locally cached SPA bundle predates
# the current AppSidebar component styles. The production build contains the
# same rules, but this lets the Flask-served preview stay accurate as well.
_SPA_RUNTIME_STYLE = """<style id=\"ahoy-spa-runtime-overrides\">
.app-sidebar-logo img {
    width: 104px !important;
    height: auto !important;
    max-height: 32px !important;
    object-fit: contain;
    border-radius: 0 !important;
    box-shadow: none !important;
    filter: drop-shadow(0 2px 7px rgba(0, 0, 0, 0.28));
}
.app-sidebar.is-collapsed .app-sidebar-logo img {
    width: 42px !important;
    max-height: 22px !important;
}
</style>"""


def _spa_dist_ready():
    return _SPA_DIST.exists() and (_SPA_DIST / "index.html").is_file()


@lru_cache(maxsize=1)
def _spa_index_html():
    return (_SPA_DIST / "index.html").read_text(encoding="utf-8")


def _spa_entrypoint_asset(ext: str) -> Optional[str]:
    """Return the current Vite entrypoint asset name for a given extension."""
    assets_dir = _SPA_DIST / "assets"
    if not assets_dir.is_dir():
        return None

    candidates = list(assets_dir.glob(f"index-*.{ext.lstrip('.')}"))
    if not candidates:
        return None

    # Prefer the newest build artifact when more than one exists.
    candidates.sort(key=lambda path: path.stat().st_mtime, reverse=True)
    return candidates[0].name


def _spa_rewrite_entrypoint_links(html: str) -> str:
    """Rewrite stale Vite entrypoint links to whichever current bundle exists."""
    js_name = _spa_entrypoint_asset("js")
    css_name = _spa_entrypoint_asset("css")

    if js_name:
        html = re.sub(
            r'src="/assets/index-[^"]+\.js"',
            f'src="/assets/{js_name}"',
            html,
        )
    if css_name:
        html = re.sub(
            r'href="/assets/index-[^"]+\.css"',
            f'href="/assets/{css_name}"',
            html,
        )

    return html


def _spa_posthog_config_script():
    key = (os.getenv("VITE_POSTHOG_KEY") or os.getenv("POSTHOG_PROJECT_TOKEN") or "").strip()
    if not key:
        return ""
    payload = json.dumps({
        "key": key,
        "host": (os.getenv("VITE_POSTHOG_HOST") or os.getenv("POSTHOG_HOST") or "https://us.i.posthog.com").strip(),
        "debug": (os.getenv("VITE_POSTHOG_DEBUG") or "").strip().lower() == "true",
    })
    return f'<script>window.__AHOY_POSTHOG__ = {payload};</script>'


def _spa_index_response():
    html = _spa_index_html()
    html = _spa_rewrite_entrypoint_links(html)
    if "ahoy-spa-runtime-overrides" not in html:
        html = html.replace("</head>", f"{_SPA_RUNTIME_STYLE}</head>", 1)
    config_script = _spa_posthog_config_script()
    if config_script and "window.__AHOY_POSTHOG__" not in html:
        html = html.replace("</head>", f"{config_script}</head>", 1)
    response = make_response(html)
    response.mimetype = "text/html"
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.route("/")
@limiter.exempt
def spa_root():
    """Serve SPA for root path."""
    if not _spa_dist_ready():
        abort(404)
    return _spa_index_response()

@app.route("/assets/<path:filename>")
@limiter.exempt
def spa_assets(filename):
    """Serve Vue SPA assets (JS/CSS) from spa-dist when SPA is built."""
    if not _spa_dist_ready():
        abort(404)
    assets_dir = _SPA_DIST / "assets"
    if not assets_dir.is_dir():
        abort(404)
    asset_path = assets_dir / filename
    if not asset_path.is_file() and filename.startswith("index-"):
        if filename.endswith(".js"):
            fallback_name = _spa_entrypoint_asset("js")
        elif filename.endswith(".css"):
            fallback_name = _spa_entrypoint_asset("css")
        else:
            fallback_name = None
        if fallback_name:
            asset_path = assets_dir / fallback_name
    if not asset_path.is_file():
        abort(404)
    response = send_from_directory(str(assets_dir), asset_path.name)
    # Vite assets are hashed, so we can cache them for a long time (1 year)
    response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
    return response

@app.route("/favicon.ico")
@limiter.exempt
def spa_favicon():
    """Serve favicon from spa-dist when SPA is built, falling back to static/img."""
    if _SPA_DIST.exists() and (_SPA_DIST / "favicon.ico").exists():
        return send_from_directory(str(_SPA_DIST), "favicon.ico", mimetype="image/x-icon")
    static_img = Path(__file__).resolve().parent / "static" / "img"
    return send_from_directory(str(static_img), "favicon.ico", mimetype="image/x-icon")

@app.route("/manifest.webmanifest")
@limiter.exempt
def spa_manifest():
    """Serve PWA manifest from spa-dist when SPA is built, falling back to static."""
    if _SPA_DIST.exists() and (_SPA_DIST / "manifest.webmanifest").exists():
        return send_from_directory(str(_SPA_DIST), "manifest.webmanifest", mimetype="application/manifest+json")
    static_dir = Path(__file__).resolve().parent / "static"
    return send_from_directory(str(static_dir), "manifest.webmanifest", mimetype="application/manifest+json")


@app.route("/<path:path>")
@limiter.exempt
def spa_fallback(path):
    """Serve SPA index.html for any unclaimed GET so client-side router can handle it."""
    if request.method != "GET":
        abort(404)
    if not _spa_dist_ready():
        abort(404)
    # Don't serve SPA for paths that are strictly server-handled (API, static, ops, etc.)
    server_prefixes = (
        "api/", "static/", "assets/", "ops/", "downloads/", "admin", "checkout", "success",
        "healthz", "readyz", "refresh", "offline", "payments/", "sitemap", "robots.txt",
        "favicon.ico", "manifest.webmanifest", "googleb3a3eb3401de50dc.html",
        "auth", "feedback", "contact", "cast", "debug",
    )
    path_lower = (path or "").strip().lower()
    if any(path_lower.startswith(p) or path_lower == p.rstrip("/") for p in server_prefixes):
        abort(404)
    
    # Handle legacy What's New redirects
    if path_lower.startswith("whats-new/"):
        sub = path_lower[len("whats-new/"):].strip("/")
        if sub == "archive":
            return redirect("/whats-new")
        if sub:
            import re
            # Match mar26 (3 letters + 2 digits)
            m = re.match(r"^([a-z]{3})(\d{2})(?:/|$)", sub)
            if m:
                return redirect(f"/whats-new/20{m.group(2)}/{m.group(1)}")
    return _spa_index_response()


@app.after_request
def add_header(response):
    """Add global headers to every response."""
    # Ensure sane defaults for API and other responses if not already set
    if "Cache-Control" not in response.headers:
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        else:
            response.headers["Cache-Control"] = "public, max-age=3600"

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"  # Prevent MIME-type sniffing
    response.headers["X-Frame-Options"] = "SAMEORIGIN"  # Prevent clickjacking
    response.headers["X-XSS-Protection"] = "1; mode=block"  # Legacy XSS protection
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"  # Control referrer info
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"  # Disable unused APIs

    # HSTS in production (tells browsers to always use HTTPS)
    if request.environ.get("HTTPS") == "on" or request.headers.get("X-Forwarded-Proto") == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


# Exempt music play count and listening session endpoints from CSRF
# ── Poems ────────────────────────────────────────────────────────────────────

@app.route('/api/poems')
@limiter.exempt
def api_poems():
    """Return all published poems, ordered by position then published_at."""
    try:
        from models import Poem
        with get_session() as session:
            poems = (session.query(Poem)
                     .filter_by(is_published=True)
                     .order_by(Poem.position.asc(), Poem.published_at.desc())
                     .all())
            data = [{
                'id': p.id,
                'poem_id': p.poem_id,
                'title': p.title,
                'poet_name': p.poet_name,
                'poet_slug': p.poet_slug,
                'body_text': p.body_text,
                'handwriting_image_url': p.handwriting_image_url,
                'note': p.note,
                'published_at': p.published_at.isoformat() if p.published_at else None,
            } for p in poems]
        resp = jsonify({'poems': data})
        resp.headers['Cache-Control'] = 'public, max-age=300'
        return resp
    except Exception as e:
        app.logger.error(f'api_poems error: {e}')
        return jsonify({'poems': [], 'error': str(e)}), 500


@app.route('/api/poems/<poem_id>')
@limiter.exempt
def api_poem_detail(poem_id):
    """Return a single published poem by its slug, with prev/next neighbours."""
    try:
        from models import Poem
        with get_session() as session:
            p = (session.query(Poem)
                 .filter_by(poem_id=poem_id, is_published=True)
                 .first())
            if not p:
                return jsonify({'error': 'Not found'}), 404
            ordered = (session.query(Poem.poem_id, Poem.title)
                       .filter_by(is_published=True)
                       .order_by(Poem.position.asc(), Poem.published_at.desc())
                       .all())
            ids = [row.poem_id for row in ordered]
            idx = ids.index(poem_id) if poem_id in ids else -1
            prev_p = ordered[idx - 1] if idx > 0 else None
            next_p = ordered[idx + 1] if 0 <= idx < len(ordered) - 1 else None
            data = {
                'id': p.id,
                'poem_id': p.poem_id,
                'title': p.title,
                'poet_name': p.poet_name,
                'poet_slug': p.poet_slug,
                'body_text': p.body_text,
                'handwriting_image_url': p.handwriting_image_url,
                'note': p.note,
                'published_at': p.published_at.isoformat() if p.published_at else None,
                'prev': {'poem_id': prev_p.poem_id, 'title': prev_p.title} if prev_p else None,
                'next': {'poem_id': next_p.poem_id, 'title': next_p.title} if next_p else None,
            }
        return jsonify(data)
    except Exception as e:
        app.logger.error(f'api_poem_detail error: {e}')
        return jsonify({'error': str(e)}), 500


@app.route('/api/admin/poems', methods=['GET'])
@admin_required
def api_admin_poems_list():
    """List all poems (published + drafts) for admin."""
    from models import Poem
    with get_session() as session:
        poems = session.query(Poem).order_by(Poem.position.asc(), Poem.id.desc()).all()
        data = [{
            'id': p.id,
            'poem_id': p.poem_id,
            'title': p.title,
            'poet_name': p.poet_name,
            'poet_slug': p.poet_slug,
            'body_text': p.body_text,
            'handwriting_image_url': p.handwriting_image_url,
            'note': p.note,
            'is_published': p.is_published,
            'position': p.position,
            'published_at': p.published_at.isoformat() if p.published_at else None,
            'created_at': p.created_at.isoformat() if p.created_at else None,
        } for p in poems]
    return jsonify({'poems': data})


@app.route('/api/admin/poems', methods=['POST'])
@admin_required
def api_admin_poem_create():
    """Create a new poem. Body: {poem_id, title, poet_name, poet_slug?, body_text, handwriting_image_url?, note?, is_published?, position?}"""
    from models import Poem
    body = request.get_json(silent=True) or {}
    required = ('poem_id', 'title', 'poet_name', 'body_text')
    missing = [f for f in required if not body.get(f)]
    if missing:
        return jsonify({'error': f'Missing fields: {missing}'}), 400
    with get_session() as session:
        existing = session.query(Poem).filter_by(poem_id=body['poem_id']).first()
        if existing:
            return jsonify({'error': 'poem_id already exists'}), 409
        p = Poem(
            poem_id=body['poem_id'],
            title=body['title'],
            poet_name=body['poet_name'],
            poet_slug=body.get('poet_slug'),
            body_text=body['body_text'],
            handwriting_image_url=body.get('handwriting_image_url'),
            note=body.get('note'),
            is_published=bool(body.get('is_published', False)),
            position=int(body.get('position', 0)),
            published_at=datetime.utcnow() if body.get('is_published') else None,
        )
        session.add(p)
        session.flush()
        result = {'id': p.id, 'poem_id': p.poem_id}
    return jsonify(result), 201


@app.route('/api/admin/poems/<int:poem_id>', methods=['PUT'])
@admin_required
def api_admin_poem_update(poem_id):
    """Update an existing poem."""
    from models import Poem
    body = request.get_json(silent=True) or {}
    with get_session() as session:
        p = session.query(Poem).filter_by(id=poem_id).first()
        if not p:
            return jsonify({'error': 'Not found'}), 404
        for field in ('title', 'poet_name', 'poet_slug', 'body_text',
                      'handwriting_image_url', 'note', 'position'):
            if field in body:
                setattr(p, field, body[field])
        if 'is_published' in body:
            was_published = p.is_published
            p.is_published = bool(body['is_published'])
            if p.is_published and not was_published and not p.published_at:
                p.published_at = datetime.utcnow()
        result = {'id': p.id, 'poem_id': p.poem_id, 'is_published': p.is_published}
    return jsonify(result)


@app.route('/api/admin/poems/<int:poem_id>', methods=['DELETE'])
@admin_required
def api_admin_poem_delete(poem_id):
    """Delete a poem."""
    from models import Poem
    with get_session() as session:
        p = session.query(Poem).filter_by(id=poem_id).first()
        if not p:
            return jsonify({'error': 'Not found'}), 404
        session.delete(p)
    return jsonify({'deleted': poem_id})


# ─────────────────────────────────────────────────────────────────────────────

_csrf_ext2 = app.extensions.get('csrf')
if _csrf_ext2 is not None:
    _csrf_ext2.exempt(api_music_play)
    _csrf_ext2.exempt(api_listening_start)
    _csrf_ext2.exempt(api_listening_end)

# Allow `python -m app` locally if needed
if __name__ == "__main__":
    import os, socket, subprocess, shutil, sys, platform

    def _is_port_free(p: int) -> bool:
        """Check if port is free on all interfaces (0.0.0.0) to match gunicorn binding"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("0.0.0.0", p))
            return True
        except OSError:
            return False

    # 2) Pick a free port automatically if requested is busy
    requested = int(os.getenv("PORT", "5000"))
    chosen = requested
    if not _is_port_free(requested):
        alt = find_available_port(5001, 5020)
        if alt:
            print(f"WARN: Port {requested} busy — starting on {alt}")
            chosen = alt
        else:
            # Fallback: let OS pick an ephemeral port
            print(f"ERROR: Port {requested} busy and no alternates free in 5001-5020.")
            print("🔁 Falling back to PORT=0 (OS-assigned ephemeral port).")
            print("💡 Set explicit PORT env var if you prefer a fixed port, e.g. PORT=5050 python app.py")
            chosen = 0

    # 3) Local run strategy:
    # - Default to Flask dev server (more stable locally, esp. on macOS where fork() + Objective-C can crash).
    # - Allow opting into gunicorn via AHOY_USE_GUNICORN=1 for parity testing.
    is_windows = platform.system() == "Windows"
    is_macos = platform.system() == "Darwin"
    want_gunicorn = str(os.getenv("AHOY_USE_GUNICORN", "")).lower() in ("1", "true", "yes", "on")

    gunicorn_bin = shutil.which("gunicorn") if (not is_windows) else None
    if gunicorn_bin and want_gunicorn and (not is_macos):
        print(f"Starting gunicorn on port {chosen}...")
        os.execv(gunicorn_bin, ["gunicorn", "app:app", "--workers", "2", "--threads", "4", "--timeout", "120", "-b", f"0.0.0.0:{chosen}"])
    else:
        if gunicorn_bin and is_macos and not want_gunicorn:
            print("🧯 macOS detected: skipping gunicorn by default to avoid fork()/objc crashes.")
            print("   Set AHOY_USE_GUNICORN=1 if you want to run gunicorn locally anyway.")
        # Allow network access with AHOY_HOST=0.0.0.0 for mobile testing
        host = os.environ.get('AHOY_HOST', '127.0.0.1')
        if host == '0.0.0.0':
            import socket
            local_ip = socket.gethostbyname(socket.gethostname())
            print(f"Starting Flask dev server on http://{local_ip}:{chosen} (network accessible)")
        elif is_windows:
            print(f"Starting Flask dev server on http://127.0.0.1:{chosen} (Windows detected)")
        else:
            print(f"Starting Flask dev server on http://127.0.0.1:{chosen}")
        app.run(host=host, port=chosen, use_reloader=False)
