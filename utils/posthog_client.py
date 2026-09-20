"""
PostHog server-side analytics client for Ahoy Indie Media.

Usage:
    from utils.posthog_client import get_posthog_client

    ph = get_posthog_client()
    if ph:
        ph.capture(distinct_id=str(user_id), event='event_name', properties={...})
"""
import atexit
import logging
import os

log = logging.getLogger(__name__)

_posthog_client = None


def get_posthog_client():
    """Return the initialized PostHog client, or None if not configured."""
    return _posthog_client


def init_posthog(app=None):
    """Initialize the PostHog Posthog() instance from Flask app config or env vars.

    Call once from create_app() after loading config.
    Returns the client instance (or None if token is not configured).
    """
    global _posthog_client

    if app is not None:
        token = app.config.get("POSTHOG_PROJECT_TOKEN") or os.environ.get("POSTHOG_PROJECT_TOKEN", "")
        host = app.config.get("POSTHOG_HOST") or os.environ.get("POSTHOG_HOST", "")
    else:
        token = os.environ.get("POSTHOG_PROJECT_TOKEN", "")
        host = os.environ.get("POSTHOG_HOST", "")

    if not token:
        if app is not None:
            app.logger.info("PostHog: POSTHOG_PROJECT_TOKEN not set, server-side analytics disabled")
        return None

    try:
        from posthog import Posthog

        kwargs = dict(
            project_api_key=token,
            enable_exception_autocapture=True,
        )
        if host:
            kwargs["host"] = host

        _posthog_client = Posthog(**kwargs)
        atexit.register(_posthog_client.shutdown)

        if app is not None:
            app.logger.info("PostHog server-side analytics initialized")
        return _posthog_client

    except Exception as e:
        if app is not None:
            app.logger.warning(f"PostHog initialization failed: {e}")
        else:
            log.warning(f"PostHog initialization failed: {e}")
        return None
