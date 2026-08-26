#!/usr/bin/env python3
"""Decide whether a missed same-day 知讯日报 run needs one catch-up."""

import argparse
import json
import re
import sys
from datetime import datetime, time, timedelta, timezone
from pathlib import Path

from config_fingerprint import compute_config_fingerprint
from py36_compat import configure_utf8_stdio, parse_iso_datetime

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python 3.6-3.8 fallback; Shanghai uses a fixed offset below
    ZoneInfo = None


SUBSCRIPTION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
TIME_PATTERN = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")


def resolve_timezone(name: str):
    if name == "Asia/Shanghai":
        return timezone(timedelta(hours=8), name)
    if ZoneInfo is None:
        raise SystemExit(f"timezone database unavailable for {name}")
    return ZoneInfo(name)


def parse_now(value, timezone_value):
    if not value:
        return datetime.now(timezone_value)
    parsed = parse_iso_datetime(value)
    return parsed.replace(tzinfo=timezone_value) if parsed.tzinfo is None else parsed.astimezone(timezone_value)


def is_valid_html_artifact(path: Path) -> bool:
    if not path.is_file() or path.suffix.lower() not in {".html", ".htm"}:
        return False
    try:
        if path.stat().st_size < 128:
            return False
        prefix = path.read_text(encoding="utf-8", errors="ignore")[:8192].lower()
    except OSError:
        return False
    return "<html" in prefix or "<!doctype html" in prefix


def load_json_object(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--cadence", choices=["daily", "weekdays"], required=True)
    parser.add_argument("--time", required=True, help="scheduled local HH:MM")
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--subscription-id", default="primary")
    parser.add_argument("--state-dir", type=Path, default=Path(".zhixun-state"))
    parser.add_argument("--output-dir", type=Path, default=Path("."))
    parser.add_argument("--config-state-file", type=Path)
    parser.add_argument("--now", help="testable ISO timestamp; defaults to current time")
    args = parser.parse_args()

    if not SUBSCRIPTION_ID_PATTERN.fullmatch(args.subscription_id):
        raise SystemExit("invalid subscription ID")
    if not TIME_PATTERN.fullmatch(args.time):
        raise SystemExit("time must use 24-hour HH:MM format")

    zone = resolve_timezone(args.timezone)
    now = parse_now(args.now, zone)
    hour, minute = map(int, args.time.split(":"))
    scheduled = datetime.combine(now.date(), time(hour, minute)).replace(tzinfo=zone)
    expected_file = args.output_dir / f"daily-industry-brief-{now.date().isoformat()}.html"
    marker_file = args.state_dir / f"last-success-{args.subscription_id}.json"
    marker = load_json_object(marker_file)
    config_state_file = args.config_state_file or (
        args.state_dir / f"current-config-{args.subscription_id}.json"
    )
    config_state = load_json_object(config_state_file)
    current_config = config_state.get("config")
    current_fingerprint = str(config_state.get("config_fingerprint") or "") or None
    if isinstance(current_config, dict):
        computed_fingerprint = compute_config_fingerprint(current_config)
        if current_fingerprint != computed_fingerprint:
            current_fingerprint = computed_fingerprint

    scheduled_day = args.cadence == "daily" or now.weekday() < 5
    expected_file_valid = is_valid_html_artifact(expected_file)
    marker_artifact = Path(str(marker.get("html_file", ""))) if marker.get("html_file") else None
    marker_artifact_valid = (
        marker.get("local_date") == now.date().isoformat()
        and marker_artifact is not None
        and is_valid_html_artifact(marker_artifact)
    )
    marker_fingerprint = str(marker.get("config_fingerprint") or "") or None
    marker_matches_current_config = (
        current_fingerprint is None or marker_fingerprint == current_fingerprint
    )
    marker_valid = marker_artifact_valid and marker_matches_current_config
    already_succeeded = marker_valid if current_fingerprint else (expected_file_valid or marker_valid)
    catch_up = scheduled_day and now >= scheduled and not already_succeeded
    stale_same_day_result = (
        current_fingerprint is not None
        and (expected_file_valid or marker_artifact_valid)
        and not marker_matches_current_config
    )
    reason = (
        "configuration_changed_after_success" if catch_up and stale_same_day_result else
        "catch_up_required" if catch_up else
        "already_succeeded" if already_succeeded else
        "not_a_scheduled_day" if not scheduled_day else
        "scheduled_time_not_reached"
    )
    print(json.dumps({
        "catch_up_required": catch_up,
        "reason": reason,
        "subscription_id": args.subscription_id,
        "local_date": now.date().isoformat(),
        "checked_at": now.isoformat(),
        "scheduled_at": scheduled.isoformat(),
        "expected_file": str(expected_file.resolve()),
        "expected_file_valid": expected_file_valid,
        "marker_artifact_valid": marker_artifact_valid,
        "marker_matches_current_config": marker_matches_current_config,
        "config_state": str(config_state_file.resolve()),
        "config_state_valid": current_fingerprint is not None,
        "current_config_fingerprint": current_fingerprint,
        "marker_config_fingerprint": marker_fingerprint,
        "success_marker": str(marker_file.resolve()),
    }, ensure_ascii=True, indent=2))
    return 10 if catch_up else 0


if __name__ == "__main__":
    raise SystemExit(main())
