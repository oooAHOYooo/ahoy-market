from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta


def _safe_int(value) -> int:
    try:
        return int(value or 0)
    except Exception:
        return 0


def _resolve_media_labels(session, rows):
    from models import Track, Show, ContentVideo, PodcastEpisode

    ids_by_type = defaultdict(set)
    for row in rows:
        media_type = str(getattr(row, "media_type", "") or "")
        media_id = str(getattr(row, "media_id", "") or "")
        if media_type and media_id:
            ids_by_type[media_type].add(media_id)

    track_map = {}
    show_map = {}
    video_map = {}
    episode_map = {}

    if ids_by_type.get("track"):
        for item in session.query(Track).filter(Track.track_id.in_(ids_by_type["track"])).all():
            track_map[item.track_id] = item
    if ids_by_type.get("show"):
        for item in session.query(Show).filter(Show.show_id.in_(ids_by_type["show"])).all():
            show_map[item.show_id] = item
    if ids_by_type.get("video"):
        for item in session.query(ContentVideo).filter(ContentVideo.video_id.in_(ids_by_type["video"])).all():
            video_map[item.video_id] = item
    if ids_by_type.get("episode"):
        for item in session.query(PodcastEpisode).filter(PodcastEpisode.episode_id.in_(ids_by_type["episode"])).all():
            episode_map[item.episode_id] = item

    resolved = []
    for row in rows:
        media_type = str(getattr(row, "media_type", "") or "")
        media_id = str(getattr(row, "media_id", "") or "")
        title = media_id
        creator = ""

        if media_type == "track" and media_id in track_map:
            item = track_map[media_id]
            title = item.title or media_id
            creator = item.artist or ""
        elif media_type == "show" and media_id in show_map:
            item = show_map[media_id]
            title = item.title or media_id
            creator = item.host or ""
        elif media_type == "video" and media_id in video_map:
            item = video_map[media_id]
            title = item.title or media_id
            creator = ""
        elif media_type in {"episode", "podcastEpisode"} and media_id in episode_map:
            item = episode_map[media_id]
            title = item.title or media_id
            creator = item.show_slug or ""

        resolved.append({
            "media_type": media_type,
            "media_id": media_id,
            "title": title,
            "creator": creator,
            "plays": _safe_int(getattr(row, "plays", 0)),
            "listeners": _safe_int(getattr(row, "listeners", 0)),
        })

    return resolved


def _safe_float(value) -> float:
    try:
        return float(value or 0)
    except Exception:
        return 0.0


def _watch_viewer_key(row) -> str:
    user_id = getattr(row, "user_id", None)
    session_id = getattr(row, "session_id", None)
    ip_address = getattr(row, "ip_address", None)
    if user_id is not None:
      return f"user:{user_id}"
    if session_id:
      return f"session:{session_id}"
    if ip_address:
      return f"ip:{ip_address}"
    return f"event:{getattr(row, 'id', '')}"


def _watch_video_identity(row):
    metadata = getattr(row, "metadata_json", None) or {}
    path = str(getattr(row, "path", "") or "").strip()
    video_id = str(
        metadata.get("video_id")
        or metadata.get("content_id")
        or metadata.get("track_id")
        or metadata.get("media_id")
        or metadata.get("id")
        or path
        or ""
    ).strip()
    title = str(
        metadata.get("video_title")
        or metadata.get("track_title")
        or metadata.get("title")
        or metadata.get("name")
        or video_id
        or path
        or "Video"
    ).strip() or "Video"
    creator = str(
        metadata.get("video_host")
        or metadata.get("track_artist")
        or metadata.get("creator")
        or metadata.get("artist")
        or ""
    ).strip()
    return video_id, title, creator, path


def _watch_seconds_from_event(row) -> float:
    metadata = getattr(row, "metadata_json", None) or {}
    event_type = str(getattr(row, "event_type", "") or "")
    for key in ("watched_seconds", "watch_seconds", "current_time_seconds", "duration_seconds"):
        value = metadata.get(key)
        if value is not None:
            return max(0.0, _safe_float(value))
    watched_ms = metadata.get("watched_ms")
    if watched_ms is not None:
        return max(0.0, _safe_float(watched_ms) / 1000.0)
    if event_type == "video_watch_complete":
        return max(0.0, _safe_float(metadata.get("duration_seconds")))
    return 0.0


def _build_watch_stats(rows):
    total_starts = 0
    total_completions = 0
    total_stops = 0
    total_progress = 0
    total_watch_seconds = 0.0
    viewers = set()
    videos = {}

    for row in rows:
        event_type = str(getattr(row, "event_type", "") or "")
        if event_type not in {
            "video_watch_start",
            "video_watch_progress",
            "video_watch_stop",
            "video_watch_complete",
        }:
            continue

        viewers.add(_watch_viewer_key(row))
        video_id, title, creator, path = _watch_video_identity(row)
        key = video_id or path or title
        bucket = videos.setdefault(
            key,
            {
                "video_id": video_id or path or title,
                "title": title,
                "creator": creator,
                "path": path,
                "watch_seconds": 0.0,
                "starts": 0,
                "completions": 0,
                "stops": 0,
                "progress_events": 0,
                "viewers": set(),
            },
        )
        bucket["title"] = bucket["title"] or title
        bucket["creator"] = bucket["creator"] or creator
        bucket["path"] = bucket["path"] or path
        bucket["viewers"].add(_watch_viewer_key(row))

        if event_type == "video_watch_start":
            total_starts += 1
            bucket["starts"] += 1
        elif event_type == "video_watch_complete":
            total_completions += 1
            bucket["completions"] += 1
            seconds = _watch_seconds_from_event(row)
            total_watch_seconds += seconds
            bucket["watch_seconds"] += seconds
        elif event_type == "video_watch_stop":
            total_stops += 1
            bucket["stops"] += 1
            seconds = _watch_seconds_from_event(row)
            total_watch_seconds += seconds
            bucket["watch_seconds"] += seconds
        elif event_type == "video_watch_progress":
            total_progress += 1
            bucket["progress_events"] += 1

    top_videos = sorted(
        videos.values(),
        key=lambda item: (item["watch_seconds"], item["starts"], item["completions"]),
        reverse=True,
    )

    top_video_rows = []
    for item in top_videos:
        starts = _safe_int(item["starts"])
        completions = _safe_int(item["completions"])
        watch_seconds = round(_safe_float(item["watch_seconds"]), 1)
        terminal_events = _safe_int(item["completions"] + item["stops"])
        top_video_rows.append({
            "video_id": item["video_id"],
            "title": item["title"],
            "creator": item["creator"],
            "path": item["path"],
            "watch_seconds": watch_seconds,
            "watch_hours": round(watch_seconds / 3600.0, 2),
            "starts": starts,
            "completions": completions,
            "stops": _safe_int(item["stops"]),
            "progress_events": _safe_int(item["progress_events"]),
            "viewers": len(item["viewers"]),
            "completion_rate": round((completions / starts) * 100, 1) if starts else 0.0,
            "avg_watch_seconds": round(watch_seconds / terminal_events, 1) if terminal_events else 0.0,
        })

    terminal_events = total_completions + total_stops
    return {
        "watch_starts_30d": total_starts,
        "watch_completions_30d": total_completions,
        "watch_stops_30d": total_stops,
        "watch_progress_events_30d": total_progress,
        "watch_sessions_30d": terminal_events,
        "unique_viewers_30d": len(viewers),
        "watch_seconds_30d": round(total_watch_seconds, 1),
        "watch_hours_30d": round(total_watch_seconds / 3600.0, 1),
        "completion_rate": round((total_completions / total_starts) * 100, 1) if total_starts else 0.0,
        "average_watch_seconds": round(total_watch_seconds / terminal_events, 1) if terminal_events else 0.0,
        "average_watch_minutes": round((total_watch_seconds / terminal_events) / 60.0, 1) if terminal_events else 0.0,
        "top_videos": top_video_rows,
    }


def build_analytics_snapshot(days: int = 30, top_limit: int = 10) -> dict:
    from sqlalchemy import func
    from db import get_session
    from models import User, PlayHistory, ListeningTotal, ListeningSession, AnalyticsEvent
    from services.user_resolver import guest_user_email

    now = datetime.utcnow()
    active_since = now - timedelta(days=days)
    week_ago = now - timedelta(days=7)
    day_ago = now - timedelta(days=1)

    snapshot = {
        "status": "ok",
        "generated_at": now.isoformat(),
        "window_days": days,
        "users": {},
        "content": {},
        "listening": {},
        "activity": {},
        "trends": [],
    }

    try:
        with get_session() as s:
            guest_email = guest_user_email()
            total_users = _safe_int(
                s.query(func.count(User.id))
                .filter(User.email != guest_email)
                .scalar()
            )
            active_users = _safe_int(
                s.query(func.count(User.id))
                .filter(User.last_active_at.isnot(None))
                .filter(User.last_active_at >= active_since)
                .filter(User.email != guest_email)
                .scalar()
            )
            new_7d = _safe_int(
                s.query(func.count(User.id))
                .filter(User.created_at >= week_ago)
                .filter(User.email != guest_email)
                .scalar()
            )
            new_24h = _safe_int(
                s.query(func.count(User.id))
                .filter(User.created_at >= day_ago)
                .filter(User.email != guest_email)
                .scalar()
            )

            pageviews_30d = _safe_int(
                s.query(func.count(AnalyticsEvent.id))
                .filter(AnalyticsEvent.event_type == "page_view")
                .filter(AnalyticsEvent.created_at >= active_since)
                .scalar()
            )
            tracked_events_30d = _safe_int(
                s.query(func.count(AnalyticsEvent.id))
                .filter(AnalyticsEvent.created_at >= active_since)
                .scalar()
            )
            guest_pageviews_30d = _safe_int(
                s.query(func.count(AnalyticsEvent.id))
                .filter(AnalyticsEvent.event_type == "page_view")
                .filter(AnalyticsEvent.created_at >= active_since)
                .filter(AnalyticsEvent.user_id.is_(None))
                .scalar()
            )
            unique_visitors_30d = _safe_int(
                s.query(func.count(func.distinct(AnalyticsEvent.session_id)))
                .filter(AnalyticsEvent.created_at >= active_since)
                .filter(AnalyticsEvent.session_id.isnot(None))
                .scalar()
            )
            guest_visitors_30d = _safe_int(
                s.query(func.count(func.distinct(AnalyticsEvent.session_id)))
                .filter(AnalyticsEvent.created_at >= active_since)
                .filter(AnalyticsEvent.user_id.is_(None))
                .filter(AnalyticsEvent.session_id.isnot(None))
                .scalar()
            )
            unique_paths_30d = _safe_int(
                s.query(func.count(func.distinct(AnalyticsEvent.path)))
                .filter(AnalyticsEvent.event_type == "page_view")
                .filter(AnalyticsEvent.created_at >= active_since)
                .filter(AnalyticsEvent.path.isnot(None))
                .filter(AnalyticsEvent.path != "")
                .scalar()
            )

            track_plays_30d = _safe_int(
                s.query(func.count(PlayHistory.id))
                .filter(PlayHistory.media_type == "track")
                .filter(PlayHistory.played_at >= active_since)
                .scalar()
            )
            video_plays_30d = _safe_int(
                s.query(func.count(PlayHistory.id))
                .filter(PlayHistory.media_type.in_(["video", "show"]))
                .filter(PlayHistory.played_at >= active_since)
                .scalar()
            )

            listening_totals = s.query(
                func.sum(ListeningTotal.total_seconds),
                func.sum(ListeningTotal.music_seconds),
                func.sum(ListeningTotal.podcast_seconds),
                func.sum(ListeningTotal.video_seconds),
            ).one()
            total_seconds = _safe_int(listening_totals[0])
            music_seconds = _safe_int(listening_totals[1])
            podcast_seconds = _safe_int(listening_totals[2])
            video_seconds = _safe_int(listening_totals[3])

            total_sessions = _safe_int(
                s.query(func.count(ListeningSession.id))
                .filter(ListeningSession.started_at >= active_since)
                .scalar()
            )
            unique_listeners = _safe_int(
                s.query(func.count(func.distinct(ListeningSession.user_id)))
                .filter(ListeningSession.started_at >= active_since)
                .scalar()
            )
            guest_sessions = _safe_int(
                s.query(func.count(ListeningSession.id))
                .join(User, User.id == ListeningSession.user_id)
                .filter(ListeningSession.started_at >= active_since)
                .filter(User.email == guest_email)
                .scalar()
            )
            guest_listening_seconds = _safe_int(
                s.query(func.sum(ListeningSession.seconds))
                .join(User, User.id == ListeningSession.user_id)
                .filter(ListeningSession.started_at >= active_since)
                .filter(User.email == guest_email)
                .scalar()
            )
            radio_sessions = _safe_int(
                s.query(func.count(ListeningSession.id))
                .filter(ListeningSession.started_at >= active_since)
                .filter(ListeningSession.source == "radio")
                .scalar()
            )
            manual_sessions = _safe_int(
                s.query(func.count(ListeningSession.id))
                .filter(ListeningSession.started_at >= active_since)
                .filter(ListeningSession.source == "manual")
                .scalar()
            )

            top_pages_rows = s.query(
                AnalyticsEvent.path.label("path"),
                func.count(AnalyticsEvent.id).label("views"),
                func.count(func.distinct(AnalyticsEvent.user_id)).label("users"),
            ).filter(
                AnalyticsEvent.event_type == "page_view",
                AnalyticsEvent.created_at >= active_since,
                AnalyticsEvent.path.isnot(None),
                AnalyticsEvent.path != "",
            ).group_by(
                AnalyticsEvent.path
            ).order_by(
                func.count(AnalyticsEvent.id).desc()
            ).limit(top_limit).all()

            top_media_rows = s.query(
                PlayHistory.media_type.label("media_type"),
                PlayHistory.media_id.label("media_id"),
                func.count(PlayHistory.id).label("plays"),
                func.count(func.distinct(PlayHistory.user_id)).label("listeners"),
            ).filter(
                PlayHistory.played_at >= active_since
            ).group_by(
                PlayHistory.media_type,
                PlayHistory.media_id,
            ).order_by(
                func.count(PlayHistory.id).desc()
            ).limit(top_limit).all()

            watch_rows = s.query(
                AnalyticsEvent.id,
                AnalyticsEvent.user_id,
                AnalyticsEvent.event_type,
                AnalyticsEvent.path,
                AnalyticsEvent.metadata_json,
                AnalyticsEvent.ip_address,
                AnalyticsEvent.session_id,
                AnalyticsEvent.created_at,
            ).filter(
                AnalyticsEvent.created_at >= active_since,
                AnalyticsEvent.event_type.in_([
                    "video_watch_start",
                    "video_watch_progress",
                    "video_watch_stop",
                    "video_watch_complete",
                ]),
            ).order_by(
                AnalyticsEvent.created_at.asc()
            ).all()

            trend_days = max(7, min(days, 14))
            trend_since = now - timedelta(days=trend_days - 1)
            trend_keys = []
            trend_rows = {}
            for offset in range(trend_days):
                day_key = (trend_since + timedelta(days=offset)).date().isoformat()
                trend_keys.append(day_key)
                trend_rows[day_key] = {
                    "date": day_key,
                    "pageviews": 0,
                    "signups": 0,
                    "track_plays": 0,
                    "video_plays": 0,
                    "listening_hours": 0.0,
                }

            pageview_trends = s.query(
                func.date(AnalyticsEvent.created_at),
                func.count(AnalyticsEvent.id),
            ).filter(
                AnalyticsEvent.event_type == "page_view",
                AnalyticsEvent.created_at >= trend_since,
            ).group_by(
                func.date(AnalyticsEvent.created_at)
            ).all()
            for day, count in pageview_trends:
                day_key = str(day)
                if day_key in trend_rows:
                    trend_rows[day_key]["pageviews"] = _safe_int(count)

            signup_trends = s.query(
                func.date(User.created_at),
                func.count(User.id),
            ).filter(
                User.created_at >= trend_since,
                User.email != guest_email,
            ).group_by(
                func.date(User.created_at)
            ).all()
            for day, count in signup_trends:
                day_key = str(day)
                if day_key in trend_rows:
                    trend_rows[day_key]["signups"] = _safe_int(count)

            track_trends = s.query(
                func.date(PlayHistory.played_at),
                func.count(PlayHistory.id),
            ).filter(
                PlayHistory.played_at >= trend_since,
                PlayHistory.media_type == "track",
            ).group_by(
                func.date(PlayHistory.played_at)
            ).all()
            for day, count in track_trends:
                day_key = str(day)
                if day_key in trend_rows:
                    trend_rows[day_key]["track_plays"] = _safe_int(count)

            video_trends = s.query(
                func.date(PlayHistory.played_at),
                func.count(PlayHistory.id),
            ).filter(
                PlayHistory.played_at >= trend_since,
                PlayHistory.media_type.in_(["video", "show"]),
            ).group_by(
                func.date(PlayHistory.played_at)
            ).all()
            for day, count in video_trends:
                day_key = str(day)
                if day_key in trend_rows:
                    trend_rows[day_key]["video_plays"] = _safe_int(count)

            listening_trends = s.query(
                func.date(ListeningSession.ended_at),
                func.sum(ListeningSession.seconds),
            ).filter(
                ListeningSession.ended_at.isnot(None),
                ListeningSession.ended_at >= trend_since,
            ).group_by(
                func.date(ListeningSession.ended_at)
            ).all()
            for day, seconds in listening_trends:
                day_key = str(day)
                if day_key in trend_rows:
                    trend_rows[day_key]["listening_hours"] = round(_safe_int(seconds) / 3600.0, 2)

            snapshot["users"] = {
                "total": total_users,
                "active_30d": active_users,
                "new_7d": new_7d,
                "new_24h": new_24h,
            }
            snapshot["activity"] = {
                "pageviews_30d": pageviews_30d,
                "tracked_events_30d": tracked_events_30d,
                "guest_pageviews_30d": guest_pageviews_30d,
                "unique_visitors_30d": unique_visitors_30d,
                "guest_visitors_30d": guest_visitors_30d,
                "unique_paths_30d": unique_paths_30d,
                "track_plays_30d": track_plays_30d,
                "video_plays_30d": video_plays_30d,
                "top_pages": [
                    {
                        "path": row.path or "/",
                        "views": _safe_int(row.views),
                        "users": _safe_int(row.users),
                    }
                    for row in top_pages_rows
                ],
                "top_media": _resolve_media_labels(s, top_media_rows),
            }
            snapshot["watching"] = _build_watch_stats(watch_rows)
            snapshot["listening"] = {
                "total_hours": round(total_seconds / 3600, 1),
                "music_hours": round(music_seconds / 3600, 1),
                "podcast_hours": round(podcast_seconds / 3600, 1),
                "video_hours": round(video_seconds / 3600, 1),
                "sessions_30d": total_sessions,
                "listeners_30d": unique_listeners,
                "guest_sessions_30d": guest_sessions,
                "guest_hours_30d": round(guest_listening_seconds / 3600, 1),
                "radio_sessions_30d": radio_sessions,
                "manual_sessions_30d": manual_sessions,
            }
            snapshot["trends"] = [trend_rows[key] for key in trend_keys]
    except Exception as e:
        snapshot["status"] = "error"
        snapshot["error"] = str(e)

    return snapshot
