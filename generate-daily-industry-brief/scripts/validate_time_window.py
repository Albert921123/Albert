#!/usr/bin/env python3
"""Block reader-facing candidates outside a ledger's exact 48-hour Shanghai window."""
from __future__ import print_function
import argparse
import datetime as dt
import json
import sys

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python 3.6 compatibility
    ZoneInfo = None

READER_KINDS = {"primary", "fallback", "date-observation", "expanded", "business-observation", "related", "highlight", "recommendation"}

def parse_time(value, tz):
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    if len(text) >= 6 and text[-6] in ("+", "-") and text[-3] == ":":
        text = text[:-3] + text[-2:]
    for pattern in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%d %H:%M%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            value = dt.datetime.strptime(text, pattern)
            if value.tzinfo is None:
                value = value.replace(tzinfo=tz)
            return value.astimezone(tz)
        except (TypeError, ValueError):
            pass
    return None

def all_candidates(payload):
    rows = payload.get("candidates", [])
    if isinstance(rows, list):
        return rows
    return []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger")
    parser.add_argument("--timezone", default="Asia/Shanghai")
    args = parser.parse_args()
    if ZoneInfo is None:
        # Asia/Shanghai has a fixed UTC+08:00 offset for this skill's supported
        # reporting period; retain Python 3.6 compatibility without a dependency.
        if args.timezone != "Asia/Shanghai":
            print(json.dumps({"ok": False, "issues": ["timezone support unavailable: %s" % args.timezone]}, ensure_ascii=False)); return 2
        tz = dt.timezone(dt.timedelta(hours=8), name="Asia/Shanghai")
    else:
        tz = ZoneInfo(args.timezone)
    try:
        payload = json.load(open(args.ledger, encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok": False, "issues": ["cannot read ledger: %s" % exc]}, ensure_ascii=False)); return 2
    run = payload.get("run", {}) if isinstance(payload, dict) else {}
    run_at = parse_time(run.get("generated_at") or run.get("finished_at") or run.get("run_timestamp"), tz)
    if not run_at:
        print(json.dumps({"ok": False, "issues": ["ledger lacks parseable exact run timestamp"]}, ensure_ascii=False)); return 1
    floor = run_at - dt.timedelta(hours=48)
    issues = []
    for index, item in enumerate(all_candidates(payload)):
        if not isinstance(item, dict):
            issues.append("candidate[%d] is not an object" % index); continue
        kind = item.get("render_kind") or item.get("entry_kind")
        eligible = item.get("render_eligible")
        shown = kind in READER_KINDS or eligible is True
        published = parse_time(item.get("published_at") or item.get("published") or item.get("timestamp"), tz)
        if shown and not published:
            issues.append("candidate[%d] reader-facing without original parseable published_at" % index)
        elif shown and published < floor:
            issues.append("candidate[%d] outside 48h: %s | %s" % (index, item.get("section", "unknown"), item.get("title", "untitled")))
        elif not shown and published and published < floor and eligible is True:
            issues.append("candidate[%d] old item marked render_eligible" % index)
    print(json.dumps({"ok": not issues, "run_timestamp": run_at.isoformat(), "fallback_floor": floor.isoformat(), "issues": issues}, ensure_ascii=False))
    return 0 if not issues else 1

if __name__ == "__main__":
    raise SystemExit(main())
