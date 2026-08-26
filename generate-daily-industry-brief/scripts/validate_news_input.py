#!/usr/bin/env python3
"""Validate a verified external JSON feed used when host search is unavailable."""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

from py36_compat import configure_utf8_stdio, parse_iso_datetime


def parse_time(value, field, issues):
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{field} must be a non-empty ISO timestamp")
        return None
    try:
        parsed = parse_iso_datetime(value)
    except ValueError:
        issues.append(f"{field} is not a valid ISO timestamp: {value!r}")
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        issues.append(f"{field} must include a UTC offset")
        return None
    return parsed


def nonempty(item, field, prefix, issues):
    value = item.get(field)
    if not isinstance(value, str) or not value.strip():
        issues.append(f"{prefix}.{field} must be non-empty")


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", type=Path)
    parser.add_argument("--run-at", help="Timezone-aware ISO run timestamp")
    parser.add_argument("--lookback-hours", type=int, default=24)
    args = parser.parse_args()

    issues = []
    try:
        payload = json.loads(args.input_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok": False, "issues": [f"invalid JSON: {exc}"]}, ensure_ascii=False, indent=2))
        return 2

    if not isinstance(payload, dict):
        issues.append("root must be a JSON object")
        payload = {}
    if payload.get("schema_version") != "1.0":
        issues.append("schema_version must be '1.0'")
    nonempty(payload, "timezone", "root", issues)
    parse_time(payload.get("generated_at"), "generated_at", issues)

    collector = payload.get("collector")
    if not isinstance(collector, dict):
        issues.append("collector must be an object")
    else:
        nonempty(collector, "name", "collector", issues)
        if collector.get("mode") not in {"enterprise-service", "authorized-crawler", "official-feed-aggregator"}:
            issues.append("collector.mode is unsupported")

    run_at = parse_time(args.run_at, "run_at", issues) if args.run_at else None
    cutoff = run_at - timedelta(hours=args.lookback_hours) if run_at else None
    items = payload.get("items")
    if not isinstance(items, list):
        issues.append("items must be an array")
        items = []

    seen_urls = set()
    qualifying = 0
    for index, raw in enumerate(items):
        prefix = f"items[{index}]"
        if not isinstance(raw, dict):
            issues.append(f"{prefix} must be an object")
            continue
        for field in ("section_id", "section_label", "title", "source_name", "source_url", "content_excerpt"):
            nonempty(raw, field, prefix, issues)
        url = raw.get("source_url")
        if isinstance(url, str):
            parsed_url = urlparse(url)
            if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
                issues.append(f"{prefix}.source_url must be an absolute HTTP(S) URL")
            if url in seen_urls:
                issues.append(f"{prefix}.source_url duplicates an earlier item")
            seen_urls.add(url)
        if raw.get("source_tier") not in {1, 2}:
            issues.append(f"{prefix}.source_tier must be 1 or 2")
        if raw.get("verification_status") != "primary-source-verified":
            issues.append(f"{prefix}.verification_status must be 'primary-source-verified'")
        parse_time(raw.get("retrieved_at"), f"{prefix}.retrieved_at", issues)
        published = parse_time(raw.get("published_at"), f"{prefix}.published_at", issues) if raw.get("published_at") else None
        event = parse_time(raw.get("event_at"), f"{prefix}.event_at", issues) if raw.get("event_at") else None
        basis = event or published
        if basis is None:
            issues.append(f"{prefix} requires published_at or event_at")
        elif run_at and cutoff:
            comparable = basis.astimezone(run_at.tzinfo)
            if comparable > run_at:
                issues.append(f"{prefix} occurs after run_at")
            elif comparable < cutoff:
                issues.append(f"{prefix} falls outside the rolling window")
            else:
                qualifying += 1

    result = {
        "ok": not issues,
        "item_count": len(items),
        "qualifying_count": qualifying if run_at else None,
        "lookback_hours": args.lookback_hours,
        "issues": issues,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
