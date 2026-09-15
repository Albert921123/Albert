#!/usr/bin/env python3
"""Validate inferred section retrieval profiles before live discovery."""
from __future__ import print_function
import argparse, json, sys

REQUIRED_POOLS = ("regulators", "central_enterprises", "local_enterprises", "listed_or_private_leaders", "counterparties_or_platforms")
REQUIRED_SOURCES = ("official", "disclosure_or_transaction", "national_media", "vertical_media")
REQUIRED_KEYWORDS = ("synonyms", "subfields", "actions", "risk_terms")
REQUIRED_QUERIES = ("field", "actor", "official", "business_intersection", "expansion")

def filled_list(value):
    return isinstance(value, list) and any(isinstance(x, str) and x.strip() for x in value)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("profile_file")
    ap.add_argument("--expected-sections", type=int)
    args = ap.parse_args()
    issues = []
    try:
        with open(args.profile_file, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
    except Exception as exc:
        print(json.dumps({"ok": False, "issues": ["cannot read profile: %s" % exc]}, ensure_ascii=False, indent=2))
        return 2
    rows = payload.get("sections") if isinstance(payload, dict) else None
    if not isinstance(rows, list):
        rows = []
        issues.append("sections must be an array")
    if args.expected_sections is not None and len(rows) != args.expected_sections:
        issues.append("section count mismatch: expected %d found %d" % (args.expected_sections, len(rows)))
    seen = set()
    for idx, row in enumerate(rows):
        p = "sections[%d]" % idx
        if not isinstance(row, dict):
            issues.append(p + " must be an object")
            continue
        sid = str(row.get("section_id") or "").strip()
        label = str(row.get("label") or "").strip()
        if not sid or not label: issues.append(p + " needs section_id and label")
        if sid in seen: issues.append(p + " duplicates section_id " + sid)
        seen.add(sid)
        if len(str(row.get("definition") or "").strip()) < 12: issues.append(p + " definition is too thin")
        if not filled_list(row.get("include")) or len(row.get("include", [])) < 3: issues.append(p + " needs at least three include rules")
        if not filled_list(row.get("exclude")) or len(row.get("exclude", [])) < 2: issues.append(p + " needs at least two exclude rules")
        for group, keys in (("keyword_tree", REQUIRED_KEYWORDS), ("source_pool", REQUIRED_SOURCES)):
            obj = row.get(group)
            if not isinstance(obj, dict):
                issues.append(p + " missing " + group)
                continue
            for key in keys:
                if not filled_list(obj.get(key)): issues.append(p + " %s.%s must be non-empty" % (group, key))
        actors = row.get("actor_pool")
        if not isinstance(actors, dict):
            issues.append(p + " missing actor_pool")
        else:
            for key in REQUIRED_POOLS:
                value = actors.get(key)
                if not filled_list(value) and not str(actors.get(key + "_not_applicable_reason") or "").strip():
                    issues.append(p + " actor_pool.%s needs names or a reason" % key)
        if not filled_list(row.get("event_types")): issues.append(p + " event_types must be non-empty")
        if not isinstance(row.get("time_policy"), dict) or not row.get("time_policy"):
            issues.append(p + " time_policy must be non-empty")
        queries = row.get("queries")
        if not isinstance(queries, dict):
            issues.append(p + " missing queries")
        else:
            values = []
            for key in REQUIRED_QUERIES:
                q = str(queries.get(key) or "").strip()
                if len(q) < 8: issues.append(p + " query %s is missing or too generic" % key)
                values.append(q)
            if len(set(values)) != len(values): issues.append(p + " queries must be distinct")
    print(json.dumps({"ok": not issues, "section_count": len(rows), "issues": issues}, ensure_ascii=False, indent=2))
    return 0 if not issues else 2

if __name__ == "__main__":
    sys.exit(main())
