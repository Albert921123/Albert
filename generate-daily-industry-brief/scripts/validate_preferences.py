#!/usr/bin/env python3
"""Validate and normalize a 知讯日报 construction-intelligence configuration."""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config_fingerprint import compute_config_fingerprint
from py36_compat import configure_utf8_stdio, isoformat_seconds
from verify_schedule import build_contract


TOPICS = {
    "fintech": "数科",
    "sourcing": "寻源",
    "matching": "撮合",
    "employment": "用工",
    "overseas": "海外",
    "leadership": "高管观点",
    "enterprise": "企业经营",
    "capital": "投融资",
    "digital": "AI",
    "informatization": "建筑软件",
    "construction-tech": "建筑科技",
    "government": "政府宏观",
    "industry-data": "行业数据",
    "standards": "标准规范",
    "green": "绿色低碳",
    "extended": "拓展阅读",
}
ALIASES = {
    "金融数科": "fintech",
    "数字金融": "fintech",
    "信息化": "informatization",
    "软件生态": "informatization",
    "领导言论": "leadership",
    "高管言论": "leadership",
    "企业动态": "enterprise",
    "行业趋势": "industry-data",
}
NAME_TO_ID = {**{name: topic_id for topic_id, name in TOPICS.items()}, **ALIASES}
MAX_CUSTOM_INTERESTS = 20
MAX_CUSTOM_INTEREST_LENGTH = 50


def read_config(path):
    raw = Path(path).read_text(encoding="utf-8") if path else sys.stdin.read()
    data = json.loads(raw)
    if not isinstance(data, dict):
        raise ValueError("configuration must be a JSON object")
    return data


def normalize_custom_interests(value):
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError("custom_interests must be a list")
    if len(value) > MAX_CUSTOM_INTERESTS:
        raise ValueError(f"custom_interests must contain at most {MAX_CUSTOM_INTERESTS} values")
    normalized = []
    seen = set()
    for raw in value:
        raw_text = str(raw)
        if any(ord(character) < 32 for character in raw_text):
            raise ValueError("custom interest contains control characters")
        interest = " ".join(raw_text.split()).strip()
        if not interest:
            continue
        if len(interest) > MAX_CUSTOM_INTEREST_LENGTH:
            raise ValueError(f"custom interest exceeds {MAX_CUSTOM_INTEREST_LENGTH} characters")
        key = interest.casefold()
        if key not in seen:
            seen.add(key)
            normalized.append(interest)
    return normalized


def normalize(data):
    raw_ids = data.get("topic_ids")
    raw_names = data.get("topics")

    if isinstance(raw_ids, list):
        topic_ids = [str(value) for value in raw_ids]
    elif isinstance(raw_names, list):
        topic_ids = []
        for value in raw_names:
            name = str(value)
            if name in {"AI与数科", "AI数科"}:
                topic_ids.extend(["fintech", "digital"])
            else:
                topic_ids.append(NAME_TO_ID.get(name, ""))
    else:
        topic_ids = []

    topic_ids = list(dict.fromkeys(topic_ids))
    version = str(data.get("version", ""))
    legacy_names = {str(value) for value in raw_names} if isinstance(raw_names, list) else set()
    if "digital" in topic_ids and "fintech" not in topic_ids and ({"AI与数科", "AI数科"} & legacy_names or not version.startswith(("4.12", "4.13", "4.14", "4.15", "4.16", "4.17", "4.18", "4.19", "4.20", "4.21", "4.22"))):
        topic_ids.insert(0, "fintech")
    unknown = [topic_id for topic_id in topic_ids if topic_id not in TOPICS]
    if unknown:
        raise ValueError(f"unknown topic_ids: {', '.join(unknown)}")
    if len(topic_ids) > len(TOPICS):
        raise ValueError(f"choose at most {len(TOPICS)} standard topics")
    custom_interests = normalize_custom_interests(data.get("custom_interests"))
    if not topic_ids and not custom_interests:
        raise ValueError("choose a standard topic or add a custom interest")

    max_items = int(data.get("max_items_per_topic", 20))
    if not 1 <= max_items <= 20:
        raise ValueError("max_items_per_topic must be between 1 and 20")

    cadence = str(data.get("cadence", "weekdays"))
    if cadence not in {"daily", "weekdays"}:
        raise ValueError("cadence must be daily or weekdays")

    delivery_time = str(data.get("delivery_time", "08:30"))
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", delivery_time):
        raise ValueError("delivery_time must use 24-hour HH:MM format")

    delivery_channel = str(data.get("delivery_channel", "host-default"))
    if delivery_channel not in {"host-default", "email", "workbuddy-miniapp"}:
        raise ValueError("unsupported delivery_channel")

    subscription_id = str(data.get("subscription_id", "primary"))
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", subscription_id):
        raise ValueError("invalid subscription_id")

    schedule_contract = build_contract(
        cadence,
        delivery_time,
        str(data.get("timezone", "Asia/Shanghai")),
    )

    normalized = {
        "version": "4.22",
        "subscription_id": subscription_id,
        "update_existing": bool(data.get("update_existing", True)),
        "topics": [TOPICS[topic_id] for topic_id in topic_ids],
        "topic_ids": topic_ids,
        "custom_interests": custom_interests,
        "industry_scope": "建筑与建筑科技生态",
        "cadence": cadence,
        "delivery_time": delivery_time,
        "timezone": str(data.get("timezone", "Asia/Shanghai")),
        "max_items_per_topic": max_items,
        "language": "zh-CN",
        "output_format": "html",
        "lookback_hours": 24,
        "fallback_lookback_hours": 48,
        "fallback_policy": "extend_empty_sections",
        "source_policy": "tier1-first",
        "delivery_channel": delivery_channel,
        "create_schedule": bool(data.get("create_schedule", False)),
        "host": str(data.get("host", "unknown")),
        "missed_run_policy": "catch_up_same_day",
        "catch_up_dedupe": True,
        "schedule_contract": schedule_contract,
    }
    normalized["configuration_effective_at"] = str(
        data.get("configuration_effective_at")
        or isoformat_seconds(datetime.now(timezone(timedelta(hours=8), "Asia/Shanghai")))
    )
    normalized["config_fingerprint"] = compute_config_fingerprint(normalized)
    return normalized


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("path", nargs="?", help="JSON file; omit to read stdin")
    args = parser.parse_args()
    try:
        normalized = normalize(read_config(args.path))
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        print(f"invalid preferences: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(normalized, ensure_ascii=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
