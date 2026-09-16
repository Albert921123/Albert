#!/usr/bin/env python3
"""Create a deterministic, resumable section work plan for a 知讯日报 run.

This helper deliberately does not search the web. Host-native search, cloud
browser and API tools remain under the Agent's control. Its purpose is to make
the complete board queue, required lanes and review depth visible before any
candidate is admitted or HTML is rendered.
"""
from __future__ import print_function

import argparse
import datetime
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

from py36_compat import configure_utf8_stdio


STANDARD = [
    ("fintech", "数科"), ("sourcing", "寻源"), ("matching", "撮合"),
    ("employment", "用工"), ("overseas", "海外"), ("leadership", "高管观点"),
    ("enterprise", "企业经营"), ("capital", "投融资"), ("digital", "AI"),
    ("informatization", "建筑软件"), ("construction-tech", "建筑科技"),
    ("government", "政府宏观"), ("industry-data", "行业数据"),
    ("standards", "标准规范"), ("green", "绿色低碳"), ("extended", "拓展阅读"),
]

ACTOR_CLASSES = [
    "regulator-or-public-body", "central-soe", "local-soe",
    "listed-or-private-leader", "owner-customer-counterparty",
    "exchange-procurement-association-research",
]
SOURCE_CLASSES = [
    "official-or-regulatory", "company-or-disclosure",
    "transaction-or-project-platform", "national-or-financial-media",
    "vertical-or-local-media",
]
EVENT_FAMILIES = [
    "policy-data", "project-order", "enterprise-product",
    "capital-market", "risk-regulatory", "analysis-report",
]


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise SystemExit("cannot read configuration: %s" % exc)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temporary, str(path))
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def selected_standard(config):
    wanted = set(config.get("topic_ids") or [])
    labels = set(config.get("topics") or [])
    return [(section_id, label) for section_id, label in STANDARD if section_id in wanted or label in labels]


def custom_id(index, label):
    safe = re.sub(r"[^a-z0-9]+", "-", label.lower()).strip("-")
    return "custom-%02d%s" % (index, ("-" + safe[:24]) if safe else "")


def main():
    configure_utf8_stdio()
    parser = argparse.ArgumentParser(description="Prepare a resumable 知讯日报 section plan")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--report-date", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config-fingerprint", default="")
    args = parser.parse_args()

    config = load_json(args.config)
    # record_config_state.py persists the normalized subscription under
    # ``config``; accept that durable wrapper as well as a bare selector JSON.
    if isinstance(config.get("config"), dict):
        config = config["config"]
    relevance = config.get("topic_relevance") or {}
    rows = []
    for section_id, label in selected_standard(config):
        score = int(relevance.get(section_id, 5) or 5)
        high = score >= 7
        rows.append({
            "section_id": section_id, "label": label, "section_kind": "standard",
            "relevance": score, "target_card_count": 3 if high else 2,
            "candidate_review_floor": 6 if high else 4,
            "source_family_floor": 3 if high else 2,
            "lanes": ["field", "actor", "official", "business-intersection"],
            "actor_classes": ACTOR_CLASSES,
            "source_classes": SOURCE_CLASSES,
            "event_families": EVENT_FAMILIES,
            "expansion_trigger": "fewer-than-target-after-candidate-review",
            "status": "pending", "checkpoint": "not-started"
        })
    for index, label in enumerate(config.get("custom_interests") or [], 1):
        label = str(label).strip()
        if not label:
            continue
        rows.append({
            "section_id": custom_id(index, label), "label": label, "section_kind": "custom",
            "relevance": 7, "target_card_count": 3, "candidate_review_floor": 6,
            "source_family_floor": 3,
            "lanes": ["field", "actor", "official", "business-intersection"],
            "actor_classes": ACTOR_CLASSES,
            "source_classes": SOURCE_CLASSES,
            "event_families": EVENT_FAMILIES,
            "expansion_trigger": "fewer-than-target-after-candidate-review",
            "status": "pending", "checkpoint": "not-started"
        })
    if not rows:
        raise SystemExit("configuration has no selected sections")

    payload = {
        "schema_version": 1,
        "run_id": args.run_id,
        "report_date": args.report_date,
        "config_fingerprint": args.config_fingerprint,
        "created_at": datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat(),
        "selected_section_count": len(rows),
        "retrieval_contract": "universal-overseas-parity-v2",
        "sections": rows,
        "execution_order": [
            "capability-preflight", "breadth-first-discovery-all-sections",
            "original-page-verification", "section-ledger-closure",
            "locked-template-render", "four-gate-validation", "delivery"
        ],
        "resume_contract": "A blocked run resumes this exact plan; it may not create a fresh plan to skip pending rows.",
        "delivery_contract": "No reader-facing HTML or success marker until every row has a final evidence-backed status and all four gates pass."
    }
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    payload["plan_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    write_json(args.output, payload)
    print(json.dumps({"ok": True, "plan": str(args.output), "selected_section_count": len(rows), "plan_sha256": payload["plan_sha256"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
