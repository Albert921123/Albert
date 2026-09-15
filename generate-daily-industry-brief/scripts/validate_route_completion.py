#!/usr/bin/env python3
"""Reject a limited board unless A/B/C/D route evidence is present."""
from __future__ import print_function
import argparse
import json
import sys

ROUTES = ("A", "B", "C", "D")
ALLOWED = {"working", "no-candidates", "failed", "skipped-unavailable", "needs-auth", "denied", "route-failed"}

def valid_a_passes(item):
    """Require two independently documented A discovery passes before a limited closure."""
    passes = item.get("a_passes")
    if not isinstance(passes, list) or len(passes) < 2:
        return False, "requires two A discovery passes"
    required = {"broad", "board_split", "official_listing", "original_page"}
    source_families = set()
    terms = set()
    for one in passes:
        if not isinstance(one, dict) or not required.issubset(set(one.get("actions", []))):
            return False, "A pass lacks broad/board_split/official_listing/original_page actions"
        if not isinstance(one.get("query"), str) or not one["query"].strip():
            return False, "A pass lacks a query"
        if not isinstance(one.get("source_family"), str) or not one["source_family"].strip():
            return False, "A pass lacks a source family"
        terms.add(one["query"].strip())
        source_families.add(one["source_family"].strip())
    if len(terms) < 2 or len(source_families) < 2:
        return False, "two A passes must change both query and source family"
    return True, ""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("evidence_file")
    parser.add_argument("--expected-sections", type=int, required=True)
    args = parser.parse_args()
    try:
        payload = json.load(open(args.evidence_file, encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok": False, "issues": ["cannot read evidence: %s" % exc]}, ensure_ascii=False))
        return 2
    rows, issues = payload.get("sections"), []
    if not isinstance(rows, list) or len(rows) != args.expected_sections:
        issues.append("expected %d section route records" % args.expected_sections)
        rows = rows if isinstance(rows, list) else []
    for i, row in enumerate(rows):
        routes = row.get("routes") if isinstance(row, dict) else None
        if not isinstance(routes, dict):
            issues.append("section[%d] missing routes" % i); continue
        for route in ROUTES:
            item = routes.get(route)
            if not isinstance(item, dict):
                issues.append("section[%d] missing route %s" % (i, route)); continue
            if item.get("status") not in ALLOWED or not isinstance(item.get("reason"), str) or not item["reason"].strip():
                issues.append("section[%d] route %s lacks status/reason" % (i, route))
        if row.get("outcome") == "limited":
            attempted = [routes.get(x, {}) for x in ROUTES]
            if any(x.get("status") == "working" for x in attempted):
                issues.append("section[%d] is limited while a working route was not closed with evidence" % i)
            if not any(x.get("status") in {"no-candidates", "failed", "denied", "needs-auth"} for x in attempted):
                issues.append("section[%d] limited without any attempted route" % i)
            ok, reason = valid_a_passes(routes.get("A", {}))
            if not ok:
                issues.append("section[%d] limited %s" % (i, reason))
    print(json.dumps({"ok": not issues, "section_count": len(rows), "issues": issues}, ensure_ascii=False))
    return 0 if not issues else 1

if __name__ == "__main__":
    raise SystemExit(main())
