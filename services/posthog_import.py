from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse


@dataclass
class PostHogImportResult:
    inserted: int = 0
    skipped: int = 0
    errors: int = 0
    parsed: int = 0


def _safe_datetime(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if not value:
        return datetime.now(timezone.utc)
    text = str(value).strip()
    if not text:
        return datetime.now(timezone.utc)
    text = text.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(text)
    except Exception:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _load_records(path: Path) -> list[dict]:
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []

    if raw.startswith("["):
        data = json.loads(raw)
        return data if isinstance(data, list) else data.get("results", []) if isinstance(data, dict) else []

    if raw.startswith("{"):
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            for key in ("results", "events", "data"):
                value = data.get(key)
                if isinstance(value, list):
                    return value
        return [data]

    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))

    records: list[dict] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def _normalize_event_name(name: str) -> str | None:
    if not name:
        return None
    clean = str(name).strip()
    lower = clean.lower()
    if lower in {"$autocapture", "$pageleave", "$identify", "$create_alias"}:
        return None
    if lower in {"$pageview", "pageview", "page_view"}:
        return "page_view"
    if lower in {"signup", "user_signed_up", "auth_signup"}:
        return "user_signed_up"
    return clean


def _path_from_props(props: dict) -> str | None:
    for key in ("path", "$pathname", "pathname"):
        value = props.get(key)
        if value:
            return str(value)
    for key in ("$current_url", "current_url", "url"):
        value = props.get(key)
        if value:
            try:
                parsed = urlparse(str(value))
                if parsed.path:
                    return parsed.path
            except Exception:
                return str(value)
    return None


def _resolve_user_id(session, props: dict):
    from models import User

    email = (
        props.get("email")
        or props.get("$email")
        or props.get("user_email")
        or props.get("distinct_id_email")
    )
    if email:
        user = session.query(User).filter(User.email == str(email).strip().lower()).first()
        if user:
            return int(user.id)
    distinct_id = props.get("distinct_id")
    if distinct_id and str(distinct_id).isdigit():
        user = session.query(User).filter(User.id == int(distinct_id)).first()
        if user:
            return int(user.id)
    return None


def import_posthog_export(session_factory, source_path: str, dry_run: bool = False, limit: int | None = None) -> PostHogImportResult:
    from models import AnalyticsEvent

    path = Path(source_path).expanduser().resolve()
    records = _load_records(path)
    result = PostHogImportResult()

    with session_factory() as session:
        for index, record in enumerate(records):
            if limit is not None and index >= limit:
                break
            try:
                if not isinstance(record, dict):
                    result.skipped += 1
                    continue
                result.parsed += 1

                event_name = _normalize_event_name(
                    record.get("event")
                    or record.get("event_name")
                    or record.get("name")
                    or record.get("type")
                    or ""
                )
                if not event_name:
                    result.skipped += 1
                    continue

                props = record.get("properties") or record.get("props") or {}
                if isinstance(props, str):
                    try:
                        props = json.loads(props)
                    except Exception:
                        props = {}
                if not isinstance(props, dict):
                    props = {}

                created_at = _safe_datetime(
                    record.get("timestamp")
                    or record.get("created_at")
                    or record.get("time")
                    or props.get("timestamp")
                    or props.get("$timestamp")
                )
                path_value = _path_from_props(props)
                source_id = (
                    record.get("uuid")
                    or record.get("event_id")
                    or record.get("id")
                    or f"{event_name}:{record.get('distinct_id') or props.get('distinct_id') or ''}:{created_at.isoformat()}"
                )

                existing = session.query(AnalyticsEvent.id).filter(
                    AnalyticsEvent.event_type == event_name,
                    AnalyticsEvent.metadata_json["source_table"].as_string() == "posthog",
                    AnalyticsEvent.metadata_json["source_id"].as_string() == str(source_id),
                ).first()
                if existing:
                    result.skipped += 1
                    continue

                user_id = _resolve_user_id(session, {**props, **record})
                if event_name == "user_signed_up" and user_id is None:
                    user_id = _resolve_user_id(session, props)

                event = AnalyticsEvent(
                    event_type=event_name,
                    path=path_value,
                    user_id=user_id,
                    ip_address=None,
                    session_id=str(record.get("distinct_id") or props.get("distinct_id") or source_id),
                    created_at=created_at,
                    metadata_json={
                        "source_table": "posthog",
                        "source_id": str(source_id),
                        "source_file": path.name,
                        "posthog_event": record.get("event") or record.get("event_name") or record.get("name") or record.get("type"),
                        "posthog_distinct_id": record.get("distinct_id") or props.get("distinct_id"),
                        "properties": props,
                    },
                )
                session.add(event)
                result.inserted += 1
            except Exception:
                result.errors += 1

        if dry_run:
            session.rollback()
        else:
            session.commit()

    return result
