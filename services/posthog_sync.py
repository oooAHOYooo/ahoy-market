from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func

DEFAULT_POSTHOG_HOST = "https://us.i.posthog.com"

log = logging.getLogger(__name__)


def _clean(value) -> str:
    return str(value or "").strip()


def _parse_bool(value, default: bool = False) -> bool:
    if value is None:
        return default
    raw = str(value).strip().lower()
    if raw in {"1", "true", "t", "yes", "y", "on"}:
        return True
    if raw in {"0", "false", "f", "no", "n", "off"}:
        return False
    return default


def _source_label(primary: str, fallback: str, fallback_label: str) -> str:
    if primary:
        return primary
    if fallback:
        return fallback_label
    return "unset"


@dataclass
class PostHogEnvConfig:
    spa_key: str = ""
    spa_host: str = ""
    spa_debug: bool = False
    server_key: str = ""
    server_host: str = DEFAULT_POSTHOG_HOST

    @property
    def runtime_key(self) -> str:
        return self.spa_key or self.server_key

    @property
    def runtime_host(self) -> str:
        return self.spa_host or self.server_host or DEFAULT_POSTHOG_HOST

    @property
    def key_matches(self) -> bool:
        return not (self.spa_key and self.server_key and self.spa_key != self.server_key)

    @property
    def host_matches(self) -> bool:
        return not (self.spa_host and self.server_host and self.spa_host != self.server_host)

    @property
    def enabled(self) -> bool:
        return bool(self.runtime_key)


def _read_env_config(app=None) -> PostHogEnvConfig:
    if app is not None:
        server_key = _clean(app.config.get("POSTHOG_PROJECT_TOKEN") or os.getenv("POSTHOG_PROJECT_TOKEN"))
        server_host = _clean(app.config.get("POSTHOG_HOST") or os.getenv("POSTHOG_HOST") or DEFAULT_POSTHOG_HOST)
    else:
        server_key = _clean(os.getenv("POSTHOG_PROJECT_TOKEN"))
        server_host = _clean(os.getenv("POSTHOG_HOST") or DEFAULT_POSTHOG_HOST)

    return PostHogEnvConfig(
        spa_key=_clean(os.getenv("VITE_POSTHOG_KEY")),
        spa_host=_clean(os.getenv("VITE_POSTHOG_HOST")),
        spa_debug=_parse_bool(os.getenv("VITE_POSTHOG_DEBUG"), False),
        server_key=server_key,
        server_host=server_host,
    )


def build_posthog_env_status(app=None) -> dict:
    """Return a compact report for PostHog env parity only."""

    config = _read_env_config(app=app)
    notes = []

    if not config.enabled:
        notes.append("PostHog is disabled because no public token is configured.")
    elif config.spa_key and config.server_key and config.spa_key == config.server_key:
        notes.append("SPA and server are using the same public token.")
    elif config.spa_key and not config.server_key:
        notes.append("Browser capture is enabled, but server-side capture is still disabled.")
    elif config.server_key and not config.spa_key:
        notes.append("Browser capture uses the Flask fallback token from POSTHOG_PROJECT_TOKEN.")

    if not config.key_matches:
        notes.append("VITE_POSTHOG_KEY and POSTHOG_PROJECT_TOKEN do not match.")
    if not config.host_matches:
        notes.append("VITE_POSTHOG_HOST and POSTHOG_HOST do not match.")
    if config.enabled and not config.spa_host and config.server_host:
        notes.append("SPA host falls back to POSTHOG_HOST through Flask runtime injection.")

    status = "disabled" if not config.enabled else "warning" if (not config.key_matches or not config.host_matches) else "ok"

    return {
        "status": status,
        "generated_at": datetime.utcnow().isoformat(),
        "env": {
            "spa_key_present": bool(config.spa_key),
            "server_key_present": bool(config.server_key),
            "spa_host_present": bool(config.spa_host),
            "server_host_present": bool(config.server_host),
            "runtime_enabled": config.enabled,
            "runtime_key_source": _source_label(config.spa_key, config.server_key, "POSTHOG_PROJECT_TOKEN"),
            "runtime_host_source": _source_label(config.spa_host, config.server_host, "POSTHOG_HOST"),
            "runtime_key_matches_server": config.key_matches,
            "runtime_host_matches_server": config.host_matches,
            "runtime_key": config.runtime_key,
            "runtime_host": config.runtime_host,
            "spa_debug": config.spa_debug,
        },
        "notes": notes,
    }


def build_posthog_mirror_status(session_factory=None) -> dict:
    """Return the PostHog-import mirror status from analytics_events."""

    report = {
        "available": False,
        "status": "unavailable",
        "table": "analytics_events",
        "source_table": "posthog",
        "total": 0,
        "last_24h": 0,
        "last_7d": 0,
        "latest_at": None,
        "notes": [],
    }

    if session_factory is None:
        try:
            from db import get_session

            session_factory = get_session
        except Exception as exc:  # pragma: no cover - import/runtime guard
            report["notes"].append(f"Analytics mirror lookup unavailable: {exc}")
            return report

    try:
        from models import AnalyticsEvent

        now = datetime.utcnow()
        with session_factory() as session:
            source_filter = AnalyticsEvent.metadata_json["source_table"].as_string() == "posthog"
            report.update(
                {
                    "available": True,
                    "status": "ok",
                    "total": int(
                        session.query(func.count(AnalyticsEvent.id))
                        .filter(source_filter)
                        .scalar()
                        or 0
                    ),
                    "last_24h": int(
                        session.query(func.count(AnalyticsEvent.id))
                        .filter(source_filter)
                        .filter(AnalyticsEvent.created_at >= now - timedelta(days=1))
                        .scalar()
                        or 0
                    ),
                    "last_7d": int(
                        session.query(func.count(AnalyticsEvent.id))
                        .filter(source_filter)
                        .filter(AnalyticsEvent.created_at >= now - timedelta(days=7))
                        .scalar()
                        or 0
                    ),
                    "latest_at": session.query(func.max(AnalyticsEvent.created_at)).filter(source_filter).scalar(),
                }
            )
            if report["total"] == 0:
                report["notes"].append("No PostHog-imported rows are present in analytics_events yet.")
    except Exception as exc:
        report["status"] = "error"
        report["error"] = str(exc)
        report["notes"].append(f"Could not read analytics_events mirror status: {exc}")

    return report


def build_posthog_sync_status(session_factory=None, app=None) -> dict:
    """Combine env parity and mirror status into one report for UIs."""

    env = build_posthog_env_status(app=app)
    mirror = build_posthog_mirror_status(session_factory=session_factory)
    status = env["status"]
    if mirror.get("status") == "error":
        status = "warning" if status == "ok" else status

    return {
        "status": status,
        "generated_at": datetime.utcnow().isoformat(),
        "env": env["env"],
        "mirror": mirror,
        "notes": [*env.get("notes", []), *mirror.get("notes", [])],
    }


def validate_posthog_environment(app=None) -> dict:
    """Log and return the PostHog env parity report without touching the database."""

    report = build_posthog_env_status(app=app)
    logger = app.logger if app is not None else log

    if report["status"] == "disabled":
        logger.info("PostHog disabled: no public token configured")
    elif report["status"] == "warning":
        logger.warning("PostHog env mismatch detected: %s", "; ".join(report["notes"]) or "unknown issue")
    else:
        logger.info(
            "PostHog env aligned: runtime key source=%s, runtime host source=%s",
            report["env"]["runtime_key_source"],
            report["env"]["runtime_host_source"],
        )

    return report


def format_posthog_sync_status(report: dict) -> str:
    """Render a human-friendly multi-line summary for CLI output."""

    env = report.get("env") or {}
    mirror = report.get("mirror") or {}
    lines = [
        "PostHog sync check",
        f"Status: {report.get('status', 'unknown')}",
        f"Runtime key source: {env.get('runtime_key_source', 'unknown')}",
        f"Runtime host source: {env.get('runtime_host_source', 'unknown')}",
        f"Runtime key matches server: {'yes' if env.get('runtime_key_matches_server') else 'no'}",
        f"Runtime host matches server: {'yes' if env.get('runtime_host_matches_server') else 'no'}",
    ]
    if mirror:
        lines.extend(
            [
                f"Mirror status: {mirror.get('status', 'unknown')}",
                f"Mirror rows: {mirror.get('total', 0)} total / {mirror.get('last_7d', 0)} in 7d / {mirror.get('last_24h', 0)} in 24h",
            ]
        )
        latest_at = mirror.get("latest_at")
        if latest_at:
            lines.append(f"Latest mirrored row: {latest_at}")
    notes = report.get("notes") or []
    if notes:
        lines.append("Notes:")
        lines.extend(f"  - {note}" for note in notes)
    return "\n".join(lines)


def format_posthog_env_status(report: dict) -> str:
    """Render the env-only PostHog status for CLI output."""

    env = report.get("env") or {}
    lines = [
        "PostHog env check",
        f"Status: {report.get('status', 'unknown')}",
        f"Runtime key source: {env.get('runtime_key_source', 'unknown')}",
        f"Runtime host source: {env.get('runtime_host_source', 'unknown')}",
        f"Runtime key matches server: {'yes' if env.get('runtime_key_matches_server') else 'no'}",
        f"Runtime host matches server: {'yes' if env.get('runtime_host_matches_server') else 'no'}",
    ]
    notes = report.get("notes") or []
    if notes:
        lines.append("Notes:")
        lines.extend(f"  - {note}" for note in notes)
    return "\n".join(lines)


def format_posthog_mirror_status(report: dict) -> str:
    """Render the mirror-only PostHog status for CLI output."""

    lines = [
        "PostHog mirror check",
        f"Status: {report.get('status', 'unknown')}",
        f"Mirror status: {report.get('status', 'unknown')}",
        f"Mirror rows: {report.get('total', 0)} total / {report.get('last_7d', 0)} in 7d / {report.get('last_24h', 0)} in 24h",
    ]
    latest_at = report.get("latest_at")
    if latest_at:
        lines.append(f"Latest mirrored row: {latest_at}")
    notes = report.get("notes") or []
    if notes:
        lines.append("Notes:")
        lines.extend(f"  - {note}" for note in notes)
    return "\n".join(lines)
