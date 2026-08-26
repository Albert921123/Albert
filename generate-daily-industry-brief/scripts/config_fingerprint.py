#!/usr/bin/env python3
"""Build a stable fingerprint for the effective 知讯日报 subscription."""

import hashlib
import json


FINGERPRINT_FIELDS = (
    "subscription_id",
    "topic_ids",
    "custom_interests",
    "industry_scope",
    "cadence",
    "delivery_time",
    "timezone",
    "max_items_per_topic",
    "language",
    "output_format",
    "lookback_hours",
    "fallback_lookback_hours",
    "fallback_policy",
    "source_policy",
    "delivery_channel",
    "missed_run_policy",
    "catch_up_dedupe",
)


def canonical_config(config):
    """Return only fields whose change requires a fresh same-day result."""
    return {field: config.get(field) for field in FINGERPRINT_FIELDS}


def compute_config_fingerprint(config):
    payload = json.dumps(
        canonical_config(config),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
