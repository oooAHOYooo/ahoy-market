#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.analytics_snapshot import build_analytics_snapshot
from services.analytics_backfill import backfill_analytics
from services.posthog_import import import_posthog_export
from services.posthog_sync import (
    build_posthog_env_status,
    build_posthog_mirror_status,
    build_posthog_sync_status,
    format_posthog_env_status,
    format_posthog_mirror_status,
    format_posthog_sync_status,
)

# Import YouTube downloader (handles ImportError gracefully)
try:
    sys.path.insert(0, str(ROOT / "tools"))
    from youtube_to_bucket import YouTubeDownloader, main as youtube_main
except ImportError:
    YouTubeDownloader = None
    youtube_main = None

OWNER_EMAIL = (os.getenv("AHOY_ADMIN_EMAIL") or "alex@ahoy.ooo").strip().lower()


def _git(args: list[str], default: str = "") -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    except Exception:
        return default


def repo_status() -> dict:
    dirty = _git(["status", "--porcelain"], "")
    branch = _git(["rev-parse", "--abbrev-ref", "HEAD"], "unknown")
    commit = _git(["rev-parse", "--short", "HEAD"], "unknown")
    subject = _git(["log", "-1", "--pretty=%s"], "")
    dirty_files = [line[3:] for line in dirty.splitlines() if line.strip()]

    return {
        "repo": str(ROOT),
        "branch": branch,
        "commit": commit,
        "subject": subject,
        "dirty": bool(dirty.strip()),
        "dirty_files": dirty_files,
        "owner_email": OWNER_EMAIL,
        "stats_url": "/ops/stats",
        "docs": [
            "docs/APP_OVERVIEW.md",
            "CLAUDE.md",
            "README.md",
        ],
    }


def print_json(data: dict):
    print(json.dumps(data, indent=2, default=str))


def _read_text_source(path: str | None) -> str:
    if not path or path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


def _parse_jsonish(text: str):
    raw = (text or "").strip()
    if not raw:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    entries = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if entries:
        return entries
    raise ValueError("Could not parse JSON or JSONL payload")


def _coerce_entries(value):
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        if all(isinstance(value.get(k), list) for k in ("audio", "video")):
            raise ValueError("Combined export should be read via the top-level object handler")
        if isinstance(value.get("entries"), list):
            return [item for item in value["entries"] if isinstance(item, dict)]
        return [value]
    return []


def _diagnostic_timestamp(entry: dict) -> int | None:
    for key in ("at", "timestamp", "ts", "time"):
        value = entry.get(key)
        if value is None:
            continue
        try:
            return int(float(value))
        except (TypeError, ValueError):
            continue
    return None


def _diagnostic_event(entry: dict) -> str:
    for key in ("event", "type", "name"):
        value = entry.get(key)
        if value:
            return str(value).strip().lower()
    return ""


def _median_or_none(values):
    values = [v for v in values if v is not None]
    if not values:
        return None
    return statistics.median(values)


def _extract_diagnostic_sets(raw, kind: str | None = None):
    if isinstance(raw, dict):
        audio = raw.get("audio") or raw.get("audioDiagnostics") or raw.get("ahoy.audioDiagnostics") or []
        video = raw.get("video") or raw.get("videoDiagnostics") or raw.get("ahoy.videoDiagnostics") or []
        if audio or video:
            return _coerce_entries(audio), _coerce_entries(video)

        if kind == "audio":
            return _coerce_entries(raw), []
        if kind == "video":
            return [], _coerce_entries(raw)

        if isinstance(raw.get("entries"), list):
            return _coerce_entries(raw.get("entries")), []

    if isinstance(raw, list):
        if kind == "audio":
            return _coerce_entries(raw), []
        if kind == "video":
            return [], _coerce_entries(raw)
        return _coerce_entries(raw), []
    return [], []


def _benchmark_runs(entries: list[dict], start_event: str, end_events: tuple[str, ...]):
    runs = []
    current = None

    for entry in sorted(entries, key=_diagnostic_timestamp):
        event = _diagnostic_event(entry)
        at = _diagnostic_timestamp(entry)
        if not event or at is None:
            continue

        if event == start_event:
            if current and current.get("start_at") is not None and current.get("end_at") is None:
                runs.append(current)
            current = {
                "start_at": at,
                "end_at": None,
                "stall_count": 0,
                "first_play_at": None,
                "first_frame_at": None,
            }
            continue

        if current is None:
            continue

        if event in {"waiting", "stalled"} and at - current["start_at"] <= 60000:
            current["stall_count"] += 1

        if event == "play" and current["first_play_at"] is None:
            current["first_play_at"] = at

        if event == "timeupdate" and current["first_play_at"] is not None and current["first_frame_at"] is None and at >= current["first_play_at"]:
            current["first_frame_at"] = at

        if event in end_events and current["end_at"] is None:
            current["end_at"] = at
            runs.append(current)
            current = None

    return runs


def _run_metrics(runs: list[dict]):
    complete = [run for run in runs if run.get("start_at") is not None and run.get("end_at") is not None]
    durations = [run["end_at"] - run["start_at"] for run in complete if run["end_at"] >= run["start_at"]]
    stalls = [run.get("stall_count", 0) for run in complete]
    first_frame = [
        run["first_frame_at"] - run["first_play_at"]
        for run in complete
        if run.get("first_play_at") is not None
        and run.get("first_frame_at") is not None
        and run["first_frame_at"] >= run["first_play_at"]
    ]
    return {
        "runs": len(complete),
        "median_ms": _median_or_none(durations),
        "median_stalls": _median_or_none(stalls),
        "median_first_frame_ms": _median_or_none(first_frame),
    }


def command_benchmark(args):
    raw = None
    if args.audio_source or args.video_source:
        audio_raw = _parse_jsonish(_read_text_source(args.audio_source)) if args.audio_source else []
        video_raw = _parse_jsonish(_read_text_source(args.video_source)) if args.video_source else []
        audio_entries = _coerce_entries(audio_raw)
        video_entries = _coerce_entries(video_raw)
    else:
        if args.source == "-" and sys.stdin.isatty():
            raise SystemExit("Provide a benchmark export file or pipe JSON/JSONL into ahoy-cli benchmark")
        raw = _parse_jsonish(_read_text_source(args.source))
        audio_entries, video_entries = _extract_diagnostic_sets(raw, kind=args.kind)

    audio_runs = _benchmark_runs(audio_entries, "loadstart", ("canplay",))
    video_runs = _benchmark_runs(video_entries, "loadstart", ("loadedmetadata", "canplay"))

    audio = _run_metrics(audio_runs)
    video = _run_metrics(video_runs)

    audio_score = round((audio["median_ms"] or 0) / 100)
    video_score = round((video["median_ms"] or 0) / 100)
    stall_score = int(round((audio["median_stalls"] or 0) + (video["median_stalls"] or 0))) * 2
    score = audio_score + video_score + stall_score

    result = {
        "label": args.label or None,
        "device": args.device or None,
        "network": args.network or None,
        "score": score,
        "audio": audio,
        "video": video,
        "source": args.source if args.source else None,
        "audio_source": args.audio_source or None,
        "video_source": args.video_source or None,
    }

    if args.json:
        print_json(result)
        return

    print("Ahoy media benchmark")
    if args.label:
        print(f"Label: {args.label}")
    if args.device:
        print(f"Device: {args.device}")
    if args.network:
        print(f"Network: {args.network}")
    print(f"Score: {score}")
    print("")
    print("Audio")
    print(f"  Runs: {audio['runs']}")
    print(f"  Median loadstart -> canplay: {audio['median_ms'] if audio['median_ms'] is not None else 'n/a'} ms")
    print(f"  Median stalls: {audio['median_stalls'] if audio['median_stalls'] is not None else 'n/a'}")
    if audio["median_first_frame_ms"] is not None:
        print(f"  Median play -> first timeupdate: {audio['median_first_frame_ms']} ms")
    print("Video")
    print(f"  Runs: {video['runs']}")
    print(f"  Median loadstart -> loadedmetadata: {video['median_ms'] if video['median_ms'] is not None else 'n/a'} ms")
    print(f"  Median stalls: {video['median_stalls'] if video['median_stalls'] is not None else 'n/a'}")
    if video["median_first_frame_ms"] is not None:
        print(f"  Median play -> first timeupdate: {video['median_first_frame_ms']} ms")
    print("")
    print("Rule: lower score is better. Keep the same device, same network throttle, and cold-start flow each run.")


def print_status(data: dict):
    print(f"Ahoy CLI")
    print(f"Repo: {data['repo']}")
    print(f"Branch: {data['branch']}")
    print(f"Commit: {data['commit']}  {data['subject']}")
    print(f"Owner: {data['owner_email']}")
    print(f"Private stats page: {data['stats_url']}")
    print(f"Dirty: {'yes' if data['dirty'] else 'no'}")
    if data["dirty_files"]:
        print("Dirty files:")
        for path in data["dirty_files"]:
            print(f"  - {path}")


def command_status(args):
    data = repo_status()
    if args.json:
        print_json(data)
        return
    print_status(data)


def command_stats(args):
    snapshot = build_analytics_snapshot(days=args.days, top_limit=args.limit)
    if args.json:
        print_json(snapshot)
        return

    if snapshot.get("status") != "ok":
        print(f"Analytics snapshot error: {snapshot.get('error', 'unknown error')}")
        return

    users = snapshot["users"]
    listening = snapshot["listening"]
    activity = snapshot["activity"]
    watching = snapshot.get("watching") or {}
    trends = snapshot.get("trends") or []

    print(f"Ahoy Analytics ({args.days}d)")
    print(f"Active users: {users['active_30d']}")
    print(f"Signups: {users['new_7d']} in 7d / {users['new_24h']} in 24h")
    print(f"Song hours: {listening['music_hours']}")
    print(f"Video hours: {listening['video_hours']}")
    print(f"Guest hours: {listening['guest_hours_30d']}")
    print(f"Video watches: {activity['video_plays_30d']}")
    if watching:
        print(f"Watch starts: {watching.get('watch_starts_30d', 0)}")
        print(f"Watch completions: {watching.get('watch_completions_30d', 0)}")
        print(f"Completion rate: {watching.get('completion_rate', 0)}%")
        print(f"Avg watch: {watching.get('average_watch_minutes', 0)}m")
    print(f"Pageviews: {activity['pageviews_30d']}")
    if trends:
        latest = trends[-1]
        print(f"Today: {latest['pageviews']} pageviews, {latest['signups']} signups, {latest['listening_hours']} listening hours")
    print("")
    print("Top pages:")
    for row in activity["top_pages"][:args.limit]:
        print(f"  - {row['path']} ({row['views']} views)")
    print("")
    print("Top media:")
    for row in activity["top_media"][:args.limit]:
        label = row["title"]
        if row["creator"]:
            label = f"{label} — {row['creator']}"
        print(f"  - {row['media_type']}:{row['media_id']} | {label} ({row['plays']} plays)")
    if watching.get("top_videos"):
        print("")
        print("Top watched videos:")
        for row in watching["top_videos"][:args.limit]:
            label = row["title"]
            if row["creator"]:
                label = f"{label} — {row['creator']}"
            print(
                f"  - {row['video_id']} | {label} "
                f"({row['watch_seconds']}s, {row['starts']} starts, {row['completion_rate']}% complete)"
            )


def command_handoff(args):
    status = repo_status()
    stats = build_analytics_snapshot(days=args.days, top_limit=args.limit)
    handoff = {
        "status": status,
        "analytics": stats,
        "recommended_next": [
            "Use /ops/stats for quick internal checks",
            "Use posthog-sync-check before deploys to catch env drift early",
            "Expand the CLI with a PostHog export command if you want live cohort analysis",
            "Add a dashboard filter for platform and content type once the metric definitions settle",
        ],
    }
    if args.json:
        print_json(handoff)
        return

    print_status(status)
    print("")
    if stats.get("status") == "ok":
        users = stats["users"]
        listening = stats["listening"]
        activity = stats["activity"]
        watching = stats.get("watching") or {}
        print(f"Active users (30d): {users['active_30d']}")
        print(f"Signups (7d): {users['new_7d']}")
        print(f"Song hours total: {listening['music_hours']}")
        print(f"Video hours total: {listening['video_hours']}")
        print(f"Video watches total: {activity['video_plays_30d']}")
        if watching:
            print(f"Watch starts total: {watching.get('watch_starts_30d', 0)}")
            print(f"Watch completions total: {watching.get('watch_completions_30d', 0)}")
            print(f"Watch hours total: {watching.get('watch_hours_30d', 0)}")
        print(f"Top page: {activity['top_pages'][0]['path'] if activity['top_pages'] else 'n/a'}")
    else:
        print(f"Analytics unavailable: {stats.get('error', 'unknown error')}")
    print("")
    print("Recommended next steps:")
    for item in handoff["recommended_next"]:
        print(f"  - {item}")


def command_summary(args):
    status = repo_status()
    stats = build_analytics_snapshot(days=args.days, top_limit=args.limit)

    if args.json:
        print_json({
            "status": status,
            "analytics": stats,
        })
        return

    print(f"Ahoy")
    print(f"Repo: {status['branch']}@{status['commit']}")
    print(f"Dirty: {'yes' if status['dirty'] else 'no'}")
    print(f"Owner: {status['owner_email']}")
    print(f"Stats page: {status['stats_url']}")
    if stats.get("status") == "ok":
        users = stats["users"]
        listening = stats["listening"]
        activity = stats["activity"]
        watching = stats.get("watching") or {}
        trends = stats.get("trends") or []
        print(f"Active: {users['active_30d']}")
        print(f"Signups: {users['new_7d']} / 7d")
        print(f"Song hrs: {listening['music_hours']}")
        print(f"Guest hrs: {listening['guest_hours_30d']}")
        print(f"Video watches: {activity['video_plays_30d']}")
        if watching:
            print(f"Watch starts: {watching.get('watch_starts_30d', 0)}")
            print(f"Watch completes: {watching.get('watch_completions_30d', 0)}")
            print(f"Watch hours: {watching.get('watch_hours_30d', 0)}")
        if trends:
            latest = trends[-1]
            print(f"Today: {latest['pageviews']} pv, {latest['signups']} signups")
    else:
        print(f"Analytics unavailable: {stats.get('error', 'unknown error')}")


def command_backfill(args):
    if args.json:
        print_json({"dry_run": args.dry_run, "source_tables": args.sources})
        return

    from db import get_session

    result = backfill_analytics(
        get_session,
        source_tables=[s.strip() for s in args.sources.split(",") if s.strip()],
        dry_run=args.dry_run,
    )

    print("Backfill complete")
    print(f"Inserted: {result.inserted}")
    print(f"Skipped: {result.skipped}")
    print(f"Errors: {result.errors}")


def command_posthog_import(args):
    from db import get_session

    result = import_posthog_export(
        get_session,
        source_path=args.source,
        dry_run=args.dry_run,
        limit=args.limit,
    )

    if args.json:
        print_json({
            "source": args.source,
            "dry_run": args.dry_run,
            "limit": args.limit,
            "inserted": result.inserted,
            "parsed": result.parsed,
            "skipped": result.skipped,
            "errors": result.errors,
        })
        return

    print("PostHog import complete")
    print(f"Inserted: {result.inserted}")
    print(f"Parsed: {result.parsed}")
    print(f"Skipped: {result.skipped}")
    print(f"Errors: {result.errors}")


def command_posthog_sync_check(args):
    report = build_posthog_sync_status()
    if args.json:
        print_json(report)
        return
    print(format_posthog_sync_status(report))


def command_posthog_env_check(args):
    report = build_posthog_env_status()
    if args.json:
        print_json(report)
        return
    print(format_posthog_env_status(report))


def command_posthog_mirror_check(args):
    report = build_posthog_mirror_status()
    if args.json:
        print_json(report)
        return
    print(format_posthog_mirror_status(report))


def command_youtube_download(args):
    """Handle YouTube download command by delegating to youtube_to_bucket.main()."""
    if youtube_main is None:
        print("YouTube downloader not available. Check your installation.")
        return 1

    # Build argv for the downloader
    argv = []
    if args.url:
        argv.extend(["--url", args.url])
    if args.playlist:
        argv.extend(["--playlist", args.playlist])
    if args.upload:
        argv.append("--upload")
    if args.bucket:
        argv.extend(["--bucket", args.bucket])
    if args.prefix:
        argv.extend(["--prefix", args.prefix])
    if args.output_file:
        argv.extend(["--output-file", str(args.output_file)])
    if args.dry_run:
        argv.append("--dry-run")

    return youtube_main(argv)


def build_parser():
    parser = argparse.ArgumentParser(prog="ahoy-cli", description="Ahoy repo command center")
    sub = parser.add_subparsers(dest="command")

    p_status = sub.add_parser("status", help="Show repo and owner context")
    p_status.add_argument("--json", action="store_true", help="Output JSON")
    p_status.set_defaults(func=command_status)

    p_stats = sub.add_parser("stats", help="Show internal analytics snapshot")
    p_stats.add_argument("--days", type=int, default=30, help="Analytics window in days")
    p_stats.add_argument("--limit", type=int, default=10, help="Top-N rows to show")
    p_stats.add_argument("--json", action="store_true", help="Output JSON")
    p_stats.set_defaults(func=command_stats)

    p_handoff = sub.add_parser("handoff", help="Show a compact agent-friendly summary")
    p_handoff.add_argument("--days", type=int, default=30, help="Analytics window in days")
    p_handoff.add_argument("--limit", type=int, default=10, help="Top-N rows to show")
    p_handoff.add_argument("--json", action="store_true", help="Output JSON")
    p_handoff.set_defaults(func=command_handoff)

    p_summary = sub.add_parser("summary", help="Show the shortest useful overview")
    p_summary.add_argument("--days", type=int, default=30, help="Analytics window in days")
    p_summary.add_argument("--limit", type=int, default=10, help="Top-N rows to show")
    p_summary.add_argument("--json", action="store_true", help="Output JSON")
    p_summary.set_defaults(func=command_summary)

    p_benchmark = sub.add_parser("benchmark", help="Score media startup using exported diagnostics")
    p_benchmark.add_argument("source", nargs="?", default="-", help="Path to a combined JSON/JSONL export, or '-' for stdin")
    p_benchmark.add_argument("--audio-source", help="Path to an audio diagnostics export")
    p_benchmark.add_argument("--video-source", help="Path to a video diagnostics export")
    p_benchmark.add_argument("--kind", choices=("audio", "video"), help="Treat the source as a single-medium export")
    p_benchmark.add_argument("--device", help="Device label for reporting")
    p_benchmark.add_argument("--network", help="Network label for reporting")
    p_benchmark.add_argument("--label", help="Optional release label")
    p_benchmark.add_argument("--json", action="store_true", help="Output JSON")
    p_benchmark.set_defaults(func=command_benchmark)

    p_backfill = sub.add_parser("backfill", help="Seed historical analytics events from first-party tables")
    p_backfill.add_argument("--sources", default="users,purchases,tips,wallet_transactions", help="Comma-separated source tables")
    p_backfill.add_argument("--dry-run", action="store_true", help="Do not commit anything")
    p_backfill.add_argument("--json", action="store_true", help="Output JSON")
    p_backfill.set_defaults(func=command_backfill)

    p_posthog = sub.add_parser("posthog-import", help="Import a PostHog export into analytics_events")
    p_posthog.add_argument("source", help="Path to a JSON, JSONL, or CSV export file")
    p_posthog.add_argument("--limit", type=int, default=None, help="Optional row limit for testing")
    p_posthog.add_argument("--dry-run", action="store_true", help="Do not commit anything")
    p_posthog.add_argument("--json", action="store_true", help="Output JSON")
    p_posthog.set_defaults(func=command_posthog_import)

    p_posthog_sync = sub.add_parser("posthog-sync-check", help="Validate PostHog env parity and DB mirror status")
    p_posthog_sync.add_argument("--json", action="store_true", help="Output JSON")
    p_posthog_sync.set_defaults(func=command_posthog_sync_check)

    p_posthog_env = sub.add_parser("posthog-env-check", help="Validate PostHog env parity only")
    p_posthog_env.add_argument("--json", action="store_true", help="Output JSON")
    p_posthog_env.set_defaults(func=command_posthog_env_check)

    p_posthog_mirror = sub.add_parser("posthog-mirror-check", help="Validate PostHog mirror status in analytics_events")
    p_posthog_mirror.add_argument("--json", action="store_true", help="Output JSON")
    p_posthog_mirror.set_defaults(func=command_posthog_mirror_check)

    if youtube_main is not None:
        p_youtube = sub.add_parser("youtube-download", help="Download videos from YouTube and upload to GCS")
        p_youtube.add_argument("--url", help="YouTube video URL")
        p_youtube.add_argument("--playlist", help="YouTube playlist URL")
        p_youtube.add_argument("--upload", action="store_true", help="Upload to GCS bucket")
        p_youtube.add_argument("--bucket", help="GCS bucket name (overrides AHOY_VIDEOS_GCS_BUCKET)")
        p_youtube.add_argument("--prefix", default="videos/", help="GCS path prefix")
        p_youtube.add_argument("--output-file", help="Save metadata to JSON file")
        p_youtube.add_argument("--dry-run", action="store_true", help="Show what would be done")
        p_youtube.set_defaults(func=command_youtube_download)

    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if not getattr(args, "command", None):
        args = parser.parse_args(["summary"])
    args.func(args)


if __name__ == "__main__":
    main()
