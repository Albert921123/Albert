#!/usr/bin/env python3
"""Validate and acknowledge a selector-to-scheduler deployment handoff.

The local selector cannot call a host's native Automation API.  This helper
therefore creates a durable, auditable boundary: an Agent may acknowledge a
pending selector submission only after the host scheduler has actually been
updated and verified.
"""
from __future__ import print_function

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path


def load_pending(path):
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ValueError("pending deployment unreadable: {0}".format(exc))
    required = ("subscription_id", "submitted_at", "config", "automation_request", "consumed")
    missing = [key for key in required if key not in data]
    if missing:
        raise ValueError("pending deployment missing: {0}".format(", ".join(missing)))
    if not isinstance(data["config"], dict) or not isinstance(data["automation_request"], dict):
        raise ValueError("pending deployment has invalid config or automation_request")
    if data["config"].get("subscription_id") != data["subscription_id"]:
        raise ValueError("pending deployment subscription mismatch")
    return data


def atomic_write(path, data):
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(str(temp), str(path))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inspect or acknowledge a 知讯日报 pending deployment")
    parser.add_argument("--file", required=True, type=Path)
    parser.add_argument("--mark-consumed", action="store_true")
    parser.add_argument("--scheduler-id", default="")
    args = parser.parse_args(argv)
    try:
        path = args.file.resolve()
        pending = load_pending(path)
        if args.mark_consumed:
            if pending.get("consumed"):
                raise ValueError("pending deployment is already consumed")
            pending["consumed"] = True
            pending["deployment_receipt"] = {
                "acknowledged_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
                "scheduler_id": args.scheduler_id or None,
                "acknowledged_by": "host-scheduler-verified",
            }
            atomic_write(path, pending)
        result = {
            "ok": True,
            "file": str(path),
            "subscription_id": pending["subscription_id"],
            "consumed": bool(pending.get("consumed")),
            "scheduler_id": pending.get("deployment_receipt", {}).get("scheduler_id"),
        }
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except ValueError as exc:
        print("pending deployment error: {0}".format(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
