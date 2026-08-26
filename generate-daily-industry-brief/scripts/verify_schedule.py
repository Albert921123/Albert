#!/usr/bin/env python3
"""Build and verify an unambiguous recurring-delivery schedule contract."""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone

from py36_compat import configure_utf8_stdio, isoformat_seconds, parse_iso_datetime

try:
    from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
except ImportError:  # Python 3.6-3.8 fallback; Shanghai uses a fixed offset below
    ZoneInfo = None
    ZoneInfoNotFoundError = Exception


TIME_PATTERN = re.compile(r"(?:[01]\d|2[0-3]):[0-5]\d")
WEEKDAY_CODES = {"MO", "TU", "WE", "TH", "FR"}
ALL_DAY_CODES = WEEKDAY_CODES | {"SA", "SU"}


def resolve_timezone(name):
    if name == "Asia/Shanghai":
        return timezone(timedelta(hours=8), name)
    if ZoneInfo is None:
        raise ValueError(f"timezone database unavailable for {name}")
    try:
        return ZoneInfo(name)
    except ZoneInfoNotFoundError as exc:
        raise ValueError(f"unknown timezone: {name}") from exc


def parse_instant(value, default_tz):
    text = value.strip()
    if re.fullmatch(r"\d+(?:\.\d+)?", text):
        timestamp = float(text)
        if timestamp >= 100_000_000_000:
            timestamp /= 1000
        return datetime.fromtimestamp(timestamp, timezone.utc)
    parsed = parse_iso_datetime(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=default_tz)
    return parsed


def next_occurrence(cadence, wall_clock_time, tz, now):
    if cadence not in {"daily", "weekdays"}:
        raise ValueError("cadence must be daily or weekdays")
    if not TIME_PATTERN.fullmatch(wall_clock_time):
        raise ValueError("time must use 24-hour HH:MM format")
    hour, minute = map(int, wall_clock_time.split(":"))
    local_now = now.astimezone(tz)
    candidate = local_now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if candidate <= local_now:
        candidate += timedelta(days=1)
    if cadence == "weekdays":
        while candidate.weekday() >= 5:
            candidate += timedelta(days=1)
    return candidate


def build_contract(cadence, wall_clock_time, timezone_name, now=None):
    tz = resolve_timezone(timezone_name)
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    expected = next_occurrence(cadence, wall_clock_time, tz, current)
    expected_utc = expected.astimezone(timezone.utc)
    hour, minute = map(int, wall_clock_time.split(":"))
    cron_days = "1-5" if cadence == "weekdays" else "*"
    byday = ";BYDAY=MO,TU,WE,TH,FR" if cadence == "weekdays" else ""
    rrule = (
        f"DTSTART;TZID={timezone_name}:{expected.strftime('%Y%m%dT%H%M%S')}\n"
        f"RRULE:FREQ=DAILY{byday};BYHOUR={hour};BYMINUTE={minute};BYSECOND=0"
    )
    return {
        "contract_generated_at": isoformat_seconds(current.astimezone(timezone.utc)).replace("+00:00", "Z"),
        "timezone": timezone_name,
        "utc_offset": expected.strftime("%z")[:3] + ":" + expected.strftime("%z")[3:],
        "wall_clock_time": wall_clock_time,
        "cadence": cadence,
        "expected_next_run_local": isoformat_seconds(expected),
        "expected_next_run_utc": isoformat_seconds(expected_utc).replace("+00:00", "Z"),
        "expected_next_run_epoch": int(expected_utc.timestamp()),
        "cron_expression": f"{minute} {hour} * * {cron_days}",
        "cron_timezone": timezone_name,
        "rrule": rrule,
        "verification_tolerance_seconds": 60,
    }


def verify_reported(contract, reported, tolerance_seconds):
    tz = resolve_timezone(str(contract["timezone"]))
    parsed = parse_instant(reported, tz)
    expected = parse_instant(str(contract["expected_next_run_utc"]), timezone.utc)
    delta = int(abs((parsed.astimezone(timezone.utc) - expected).total_seconds()))
    return {
        "reported_next_run_raw": reported,
        "reported_next_run_local": isoformat_seconds(parsed.astimezone(tz)),
        "reported_next_run_utc": isoformat_seconds(parsed.astimezone(timezone.utc)).replace("+00:00", "Z"),
        "delta_seconds": delta,
        "next_run_matches_expected": delta <= tolerance_seconds,
    }


def parse_rrule(value):
    text = value.replace("\\n", "\n").strip()
    dtstart_tzid = None
    rule_line = None
    for raw_line in text.splitlines() or [text]:
        line = raw_line.strip()
        upper = line.upper()
        if upper.startswith("DTSTART"):
            match = re.match(r"DTSTART(?:;TZID=([^:]+))?:", line, re.IGNORECASE)
            if match:
                dtstart_tzid = match.group(1)
        elif upper.startswith("RRULE:"):
            rule_line = line.split(":", 1)[1]
        elif "FREQ=" in upper and rule_line is None:
            rule_line = line
    if not rule_line:
        raise ValueError("reported recurrence rule has no RRULE/FREQ component")
    properties = {}
    for part in rule_line.split(";"):
        if not part:
            continue
        if "=" not in part:
            raise ValueError(f"invalid recurrence component: {part}")
        key, raw = part.split("=", 1)
        properties[key.strip().upper()] = raw.strip().upper()
    return properties, dtstart_tzid


def parse_int_set(properties, key):
    raw = properties.get(key)
    if raw is None:
        return set()
    try:
        return {int(value) for value in raw.split(",")}
    except ValueError as exc:
        raise ValueError(f"{key} must contain integers") from exc


def verify_recurrence(contract, reported_rrule, require_timezone_aware_rrule):
    properties, dtstart_tzid = parse_rrule(reported_rrule)
    hour, minute = map(int, str(contract["wall_clock_time"]).split(":"))
    cadence = str(contract["cadence"])
    issues = []

    if parse_int_set(properties, "BYHOUR") != {hour}:
        issues.append(f"BYHOUR must be exactly {hour}")
    if parse_int_set(properties, "BYMINUTE") != {minute}:
        issues.append(f"BYMINUTE must be exactly {minute}")
    if "BYSECOND" in properties and parse_int_set(properties, "BYSECOND") != {0}:
        issues.append("BYSECOND must be 0 when present")
    if properties.get("INTERVAL", "1") != "1":
        issues.append("INTERVAL must be 1")

    frequency = properties.get("FREQ")
    byday = {value for value in properties.get("BYDAY", "").split(",") if value}
    if cadence == "weekdays":
        if frequency not in {"DAILY", "WEEKLY"}:
            issues.append("weekday cadence requires FREQ=DAILY or FREQ=WEEKLY")
        if byday != WEEKDAY_CODES:
            issues.append("weekday cadence requires BYDAY=MO,TU,WE,TH,FR")
    else:
        if frequency != "DAILY":
            issues.append("daily cadence requires FREQ=DAILY")
        if byday and byday != ALL_DAY_CODES:
            issues.append("daily cadence must omit BYDAY or include all seven days")

    expected_timezone = str(contract["timezone"])
    timezone_matches = dtstart_tzid == expected_timezone
    if require_timezone_aware_rrule and not timezone_matches:
        issues.append(f"DTSTART must declare TZID={expected_timezone}")

    return {
        "reported_rrule_raw": reported_rrule,
        "reported_rrule_properties": properties,
        "reported_rrule_timezone": dtstart_tzid,
        "recurrence_timezone_matches_expected": timezone_matches,
        "recurrence_issues": issues,
        "recurrence_matches_expected": not issues,
    }


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--cadence", choices=["daily", "weekdays"], required=True)
    parser.add_argument("--time", dest="wall_clock_time", required=True)
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--now", help="ISO-8601 or Unix seconds/milliseconds; defaults to now")
    parser.add_argument("--reported-next-run", help="Host nextRunAt as ISO-8601 or Unix seconds/milliseconds")
    parser.add_argument("--reported-rrule", help="Host-persisted RRULE, with or without DTSTART")
    parser.add_argument(
        "--require-timezone-aware-rrule",
        action="store_true",
        help="Require DTSTART to carry the requested TZID",
    )
    parser.add_argument("--tolerance-seconds", type=int, default=60)
    args = parser.parse_args()
    try:
        tz = resolve_timezone(args.timezone)
        now = parse_instant(args.now, tz) if args.now else None
        contract = build_contract(args.cadence, args.wall_clock_time, args.timezone, now)
        if args.require_timezone_aware_rrule and not args.reported_rrule:
            raise ValueError("--require-timezone-aware-rrule requires --reported-rrule")
        result = dict(contract)
        if args.reported_next_run:
            result.update(verify_reported(contract, args.reported_next_run, max(0, args.tolerance_seconds)))
        if args.reported_rrule:
            result.update(
                verify_recurrence(
                    contract,
                    args.reported_rrule,
                    args.require_timezone_aware_rrule,
                )
            )
        checks = []
        if args.reported_next_run:
            checks.append(bool(result["next_run_matches_expected"]))
        if args.reported_rrule:
            checks.append(bool(result["recurrence_matches_expected"]))
        if checks:
            result["matches_expected"] = all(checks)
    except (OverflowError, OSError, TypeError, ValueError) as exc:
        print(f"invalid schedule: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=True, indent=2))
    if (args.reported_next_run or args.reported_rrule) and not result["matches_expected"]:
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
