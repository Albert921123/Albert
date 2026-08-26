#!/usr/bin/env python3
"""Persist the effective subscription and its catch-up fingerprint atomically."""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config_fingerprint import compute_config_fingerprint
from py36_compat import configure_utf8_stdio, isoformat_seconds, parse_iso_datetime
from validate_preferences import normalize


SUBSCRIPTION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")
SHANGHAI_TZ = timezone(timedelta(hours=8), "Asia/Shanghai")


def read_source(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("configuration source must be a JSON object")
    if isinstance(data.get("config"), dict):
        return data["config"], str(data.get("submitted_at") or "") or None
    return data, None


def normalize_effective_at(value):
    if not value:
        return isoformat_seconds(datetime.now(SHANGHAI_TZ))
    parsed = parse_iso_datetime(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=SHANGHAI_TZ)
    return isoformat_seconds(parsed.astimezone(SHANGHAI_TZ))


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--subscription-id", default="primary")
    parser.add_argument("--state-dir", type=Path, default=Path(".zhixun-state"))
    parser.add_argument("--config-file", type=Path, required=True)
    parser.add_argument("--effective-at")
    args = parser.parse_args()

    if not SUBSCRIPTION_ID_PATTERN.fullmatch(args.subscription_id):
        raise SystemExit("invalid subscription ID")
    try:
        config, source_effective_at = read_source(args.config_file)
        config = normalize(config)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"invalid configuration source: {exc}") from exc
    config_subscription = str(config.get("subscription_id", args.subscription_id))
    if config_subscription != args.subscription_id:
        raise SystemExit("configuration subscription ID does not match")

    fingerprint = compute_config_fingerprint(config)
    effective_at = normalize_effective_at(
        args.effective_at
        or str(config.get("configuration_effective_at") or "")
        or source_effective_at
    )
    args.state_dir.mkdir(parents=True, exist_ok=True)
    target = args.state_dir / f"current-config-{args.subscription_id}.json"
    temp = target.with_suffix(".tmp")
    payload = {
        "schema_version": 1,
        "subscription_id": args.subscription_id,
        "effective_at": effective_at,
        "config_fingerprint": fingerprint,
        "config": config,
    }
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(target)
    print(json.dumps({
        "config_state": str(target.resolve()),
        "subscription_id": args.subscription_id,
        "effective_at": effective_at,
        "config_fingerprint": fingerprint,
    }, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
