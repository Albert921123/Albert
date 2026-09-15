#!/usr/bin/env python3
"""Validate the candidate-level retrieval ledger for a daily brief.

The implementation intentionally supports Python 3.6+ and uses only the
standard library so the same Skill bundle works on older Agent hosts.
"""

import argparse
import datetime
import hashlib
import json
import sys
import re
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from py36_compat import configure_utf8_stdio


SECTION_FIELDS = (
    "section_id",
    "label",
    "source_family_count",
    "query_count",
    "candidate_count",
    "primary_card_count",
    "cross_section_card_count",
    "related_count",
    "unique_event_count",
    "status",
    "reason",
)

CANDIDATE_FIELDS = (
    "section_id",
    "section_label",
    "title",
    "url",
    "source_name",
    "source_tier",
    "source_family_id",
    "source_class",
    "actor_class",
    "event_family",
    "time_basis",
    "query_lane",
    "relevance_level",
    "decision",
    "reason",
    "evidence_route",
)

STATUSES = {"complete", "observed", "expanded", "business-observation", "checked-empty", "limited", "baseline"}
QUERY_LANES = {"field", "actor", "official", "business-intersection", "expansion"}
REQUIRED_SECTION_LANES = {"field", "actor", "official", "business-intersection"}
RELEVANCE_LEVELS = {"A", "B", "C", "D"}
ACTOR_CLASSES = {
    "regulator-or-public-body", "central-soe", "local-soe",
    "listed-or-private-leader", "owner-customer-counterparty",
    "exchange-procurement-association-research",
}
EVENT_FAMILIES = {"policy-data", "project-order", "enterprise-product", "capital-market", "risk-regulatory", "analysis-report"}
SOURCE_CLASSES = {"official-or-regulatory", "company-or-disclosure", "transaction-or-project-platform", "national-or-financial-media", "vertical-or-local-media"}
DECISIONS = {
    "included-primary",
    "included-cross-section",
    "included-related",
    "included-date-observation",
    "included-expanded",
    "included-business-observation",
    "included-baseline",
    "excluded",
}
PLACEHOLDER_PATTERN = re.compile(r"某(?:软件厂商|企业|公司|媒体|机构|标准|高校)")
GENERIC_STOP_PATTERN = re.compile(r"(?:暂无更多|没有更多|搜索结果有限|节省\s*token|节省令牌|时间不足|来不及)", re.I)
LIVE_MODES = {"A", "B", "B1", "B2", "C"}
DIRECT_NETWORK_ROUTES = {
    "B1:yunzhu-browser-automation",
    "cloud-browser-automation",
    "B2:browser",
    "B2:browser-search-page",
    "browser",
    "browser-search-page",
    "http-client",
    "python-urllib",
    "rss",
    "sitemap",
    "official-listing",
    "public-api",
    "site-native-search",
}
TIME_PRECISIONS = {"datetime", "date-only"}
WINDOW_CLASSES = {"primary", "fallback", "observed"}
DIRECT_RECORD_KINDS = {"article", "announcement", "disclosure", "procurement-record", "official-record", "feed-item"}
INCLUDED_LIVE_DECISIONS = {
    "included-primary",
    "included-date-observation",
    "included-expanded",
    "included-business-observation",
}
GENERIC_SOURCE_FAMILY_PATTERN = re.compile(r"(?:web\s*search|网络搜索|混合来源|多个媒体)", re.I)


def is_nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def is_count(value):
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def parse_timestamp(value):
    """Return (aware datetime, precision) or (None, None); supports Python 3.6."""
    if not is_nonempty(value):
        return None, None
    text = value.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", text):
        try:
            return datetime.datetime.strptime(text, "%Y-%m-%d").replace(tzinfo=datetime.timezone.utc), "date-only"
        except ValueError:
            return None, None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    match = re.match(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2})?)([+-]\d{2}:\d{2})$", text)
    if not match:
        return None, None
    base, offset = match.groups()
    try:
        parsed = datetime.datetime.strptime(base, "%Y-%m-%dT%H:%M:%S" if len(base) == 19 else "%Y-%m-%dT%H:%M")
        sign = 1 if offset[0] == "+" else -1
        hours = int(offset[1:3])
        minutes = int(offset[4:6])
        zone = datetime.timezone(sign * datetime.timedelta(hours=hours, minutes=minutes))
        return parsed.replace(tzinfo=zone), "datetime"
    except ValueError:
        return None, None


def canonicalize_url(value):
    parsed = urlparse(value or "")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    path = parsed.path.rstrip("/") or "/"
    return (parsed.netloc.lower() + path).lower()


def main():
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger_file", type=Path)
    parser.add_argument("--expected-sections", type=int)
    parser.add_argument("--plan", type=Path, help="matching run-plan JSON created before retrieval")
    args = parser.parse_args()

    issues = []
    try:
        payload = json.loads(args.ledger_file.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok": False, "issues": ["cannot read ledger JSON: %s" % exc]}, ensure_ascii=False, indent=2))
        return 2

    if not isinstance(payload, dict):
        issues.append("ledger root must be an object")
        payload = {}
    run = payload.get("run")
    sections = payload.get("sections")
    candidates = payload.get("candidates")
    if not isinstance(run, dict):
        issues.append("run must be an object")
        run = {}
    if not isinstance(sections, list):
        issues.append("sections must be an array")
        sections = []
    if not isinstance(candidates, list):
        issues.append("candidates must be an array")
        candidates = []

    plan_rows = {}
    if args.plan is not None:
        try:
            plan_payload = json.loads(args.plan.read_text(encoding="utf-8"))
            raw_plan_rows = plan_payload.get("sections", []) if isinstance(plan_payload, dict) else []
            if not isinstance(raw_plan_rows, list):
                raise ValueError("sections must be an array")
            for row in raw_plan_rows:
                if isinstance(row, dict) and is_nonempty(row.get("section_id")):
                    plan_rows[row["section_id"]] = row
            if not plan_rows:
                issues.append("run plan has no usable section rows")
        except Exception as exc:
            issues.append("cannot read matching run plan: %s" % exc)

    if args.expected_sections is not None and len(sections) != args.expected_sections:
        issues.append(
            "section count mismatch: expected %s, found %s"
            % (args.expected_sections, len(sections))
        )

    mode = str(run.get("mode") or "").upper()
    live_contract = mode in LIVE_MODES
    network_reachable = False
    window_bounds = None
    reading = run.get("full_package_reading")
    if not isinstance(reading, dict):
        issues.append("run missing full_package_reading receipt")
    else:
        for field in ("run_id", "receipt_path", "file_count", "verified"):
            if field not in reading:
                issues.append("full_package_reading missing field: %s" % field)
        if reading.get("verified") is not True:
            issues.append("full_package_reading receipt is not verified")
        if not is_nonempty(reading.get("run_id")) or not is_nonempty(reading.get("receipt_path")):
            issues.append("full_package_reading needs run_id and receipt_path")
        if not isinstance(reading.get("file_count"), int) or reading.get("file_count") < 1:
            issues.append("full_package_reading needs a positive file_count")
    if live_contract:
        for field in (
            "audit_contract",
            "started_at",
            "finished_at",
            "selected_section_count",
            "candidate_pool_origin",
            "primary_window_start",
            "primary_window_end",
            "fallback_window_start",
        ):
            if field not in run:
                issues.append("run missing anti-shortcut field: %s" % field)
        if run.get("audit_contract") != "anti-shortcut-v1":
            issues.append("run audit_contract must be anti-shortcut-v1 for mode %s" % mode)
        if run.get("candidate_pool_origin") not in {"live-search", "direct-fetch", "validated-feed"}:
            issues.append("run has invalid live candidate_pool_origin")
        if run.get("selected_section_count") != len(sections):
            issues.append("run selected_section_count does not match sections")
        primary_start, primary_precision = parse_timestamp(run.get("primary_window_start"))
        primary_end, primary_end_precision = parse_timestamp(run.get("primary_window_end"))
        fallback_start, fallback_precision = parse_timestamp(run.get("fallback_window_start"))
        if not primary_start or not primary_end or not fallback_start or "date-only" in {primary_precision, primary_end_precision, fallback_precision}:
            issues.append("run windows need timezone-aware datetime values")
        elif not (fallback_start < primary_start < primary_end):
            issues.append("run window bounds are not ordered fallback < primary < end")
        else:
            window_bounds = (fallback_start, primary_start, primary_end)
        probe = run.get("network_probe")
        if not isinstance(probe, dict):
            issues.append("run missing network_probe for live mode")
        else:
            network_reachable = probe.get("internet_reachable") is True
            working_routes = probe.get("working_routes")
            failed_routes = probe.get("failed_routes")
            if not isinstance(working_routes, list):
                issues.append("network_probe working_routes must be an array")
                working_routes = []
            if not isinstance(failed_routes, list):
                issues.append("network_probe failed_routes must be an array")
            if not is_nonempty(probe.get("mode_selection_reason")):
                issues.append("network_probe needs mode_selection_reason")
            if mode in {"A", "B", "B1", "B2"} and not network_reachable:
                issues.append("live direct retrieval mode requires internet_reachable=true")
            if mode == "B1":
                cloud_probe = probe.get("cloud_browser_probe")
                if not isinstance(cloud_probe, dict) or cloud_probe.get("status") != "working":
                    issues.append("Mode B1 needs a working cloud_browser_probe")
                elif not is_nonempty(cloud_probe.get("capability")):
                    issues.append("Mode B1 cloud_browser_probe needs capability name")
                if not any(str(route).startswith("B1:") or str(route) == "cloud-browser-automation" for route in working_routes):
                    issues.append("Mode B1 needs a recorded cloud-browser automation route")
            if mode in {"B", "B2"} and not set(working_routes).intersection(DIRECT_NETWORK_ROUTES):
                issues.append("Mode %s needs a recorded direct-network route, not only a missing WebSearch claim" % mode)

    section_ids = []
    section_rows = {}
    for index, row in enumerate(sections):
        if not isinstance(row, dict):
            issues.append("section[%s] must be an object" % index)
            continue
        missing = [field for field in SECTION_FIELDS if field not in row]
        if missing:
            issues.append("section[%s] missing fields: %s" % (index, ", ".join(missing)))
        section_id = row.get("section_id")
        if not is_nonempty(section_id):
            issues.append("section[%s] has invalid section_id" % index)
            continue
        section_ids.append(section_id)
        section_rows[section_id] = row
        if not is_nonempty(row.get("label")):
            issues.append("section[%s] has invalid label" % index)
        for field in (
            "source_family_count",
            "query_count",
            "candidate_count",
            "primary_card_count",
            "cross_section_card_count",
            "related_count",
            "unique_event_count",
        ):
            if not is_count(row.get(field)):
                issues.append("section[%s] has invalid %s" % (index, field))
        status = row.get("status")
        if status not in STATUSES:
            issues.append("section[%s] has invalid status" % index)
        full_count = (row.get("primary_card_count") or 0) + (row.get("cross_section_card_count") or 0) + (row.get("date_observation_card_count") or 0) + (row.get("expanded_card_count") or 0) + (row.get("business_observation_card_count") or 0)
        if status == "complete" and full_count < 1:
            issues.append("section[%s] is complete without a full card" % index)
        if status == "observed" and (row.get("date_observation_card_count") or 0) < 1:
            issues.append("section[%s] is observed without a date-only observation card" % index)
        if status == "expanded" and (row.get("expanded_card_count") or 0) < 1:
            issues.append("section[%s] is expanded without an expanded card" % index)
        if status == "business-observation" and (row.get("business_observation_card_count") or 0) < 1:
            issues.append("section[%s] is business-observation without a business observation card" % index)
        if status in {"checked-empty", "limited", "baseline"} and full_count:
            issues.append("section[%s] is %s but has full cards" % (index, status))
        if status in {"observed", "expanded", "business-observation", "checked-empty", "limited", "baseline"} and not is_nonempty(row.get("reason")):
            issues.append("section[%s] needs a reason for status %s" % (index, status))
        # A baseline is an offline-continuity card, not a convenient early exit.
        # If this run had a working live route, the row must complete its lanes
        # and use a verified live card, observation, expanded/business card, or
        # a documented checked-empty result instead.
        if live_contract and network_reachable and status == "baseline":
            issues.append("section[%s] uses baseline despite a working live retrieval route" % index)
        if live_contract:
            proof = row.get("retrieval_proof")
            if not isinstance(proof, dict):
                issues.append("section[%s] missing retrieval_proof" % index)
            else:
                lanes = proof.get("lanes_attempted")
                query_evidence = proof.get("query_evidence")
                families = proof.get("source_families_checked")
                actor_classes = proof.get("actor_classes_checked")
                event_families = proof.get("event_families_checked")
                opened = proof.get("opened_candidate_count")
                screened = proof.get("screened_candidate_count")
                target = proof.get("target_card_count")
                stop_reason = proof.get("stop_reason")
                pool_closure = proof.get("candidate_pool_closure")
                closure_reason = proof.get("closure_reason")
                pool_exhausted = proof.get("candidate_pool_exhausted")
                additional_pass = proof.get("additional_discovery_completed")
                below_target_reason = proof.get("below_target_reason")
                lane_set = set(lane.strip() for lane in lanes if is_nonempty(lane)) if isinstance(lanes, list) else set()
                if not REQUIRED_SECTION_LANES.issubset(lane_set):
                    issues.append("section[%s] retrieval_proof must complete all four section-specific lanes" % index)
                if not isinstance(query_evidence, list):
                    issues.append("section[%s] retrieval_proof needs per-lane query_evidence" % index)
                    query_evidence = []
                evidenced_lanes = set()
                discovered_result_total = 0
                recorded_candidate_ids = []
                evidenced_source_families = set()
                evidenced_actor_classes = set()
                evidenced_event_families = set()
                for evidence_index, evidence in enumerate(query_evidence):
                    if not isinstance(evidence, dict):
                        issues.append("section[%s] query_evidence[%s] must be an object" % (index, evidence_index))
                        continue
                    lane = evidence.get("lane")
                    if lane not in QUERY_LANES:
                        issues.append("section[%s] query_evidence[%s] has invalid lane" % (index, evidence_index))
                    else:
                        evidenced_lanes.add(lane)
                    if not is_nonempty(evidence.get("query")):
                        issues.append("section[%s] query_evidence[%s] needs the section-specific query" % (index, evidence_index))
                    if not is_nonempty(evidence.get("route")):
                        issues.append("section[%s] query_evidence[%s] needs the executed route" % (index, evidence_index))
                    if evidence.get("status") not in {"completed", "failed"}:
                        issues.append("section[%s] query_evidence[%s] needs completed/failed status" % (index, evidence_index))
                    if not is_count(evidence.get("result_count")):
                        issues.append("section[%s] query_evidence[%s] needs a non-negative result_count" % (index, evidence_index))
                    else:
                        discovered_result_total += evidence.get("result_count")
                    lane_candidate_ids = evidence.get("recorded_candidate_ids")
                    if not isinstance(lane_candidate_ids, list):
                        issues.append("section[%s] query_evidence[%s] needs recorded_candidate_ids" % (index, evidence_index))
                    else:
                        recorded_candidate_ids.extend(lane_candidate_ids)
                        if is_count(evidence.get("result_count")) and evidence.get("result_count") != len(lane_candidate_ids):
                            issues.append("section[%s] query_evidence[%s] result_count does not equal persisted candidates" % (index, evidence_index))
                    for field, aggregate in (
                        ("source_families_checked", evidenced_source_families),
                        ("actor_classes_checked", evidenced_actor_classes),
                        ("event_families_checked", evidenced_event_families),
                    ):
                        values = evidence.get(field)
                        if not isinstance(values, list) or not any(is_nonempty(value) for value in values):
                            issues.append("section[%s] query_evidence[%s] needs named %s" % (index, evidence_index, field))
                        else:
                            aggregate.update(value.strip() for value in values if is_nonempty(value))
                    raw_path = Path(str(evidence.get("raw_results") or ""))
                    if not raw_path.is_absolute(): raw_path = args.ledger.parent / raw_path
                    raw_hash = str(evidence.get("raw_results_sha256") or "").strip().lower()
                    transport = evidence.get("transport_evidence") if isinstance(evidence.get("transport_evidence"), dict) else {}
                    if not raw_path.is_file() or not re.match(r"^[0-9a-f]{64}$", raw_hash):
                        issues.append("section[%s] query_evidence[%s] needs a readable hash-bound raw-results file" % (index, evidence_index))
                    elif hashlib.sha256(raw_path.read_bytes()).hexdigest() != raw_hash:
                        issues.append("section[%s] query_evidence[%s] raw-results hash mismatch" % (index, evidence_index))
                    captured_at = str(transport.get("captured_at") or "").strip()
                    invocation_id = str(transport.get("invocation_id") or "").strip()
                    no_id_reason = str(transport.get("invocation_id_not_exposed_reason") or "").strip()
                    if not is_nonempty(transport.get("tool_name")) or not captured_at:
                        issues.append("section[%s] query_evidence[%s] needs transport tool_name and captured_at" % (index, evidence_index))
                    elif not re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})$", captured_at):
                        issues.append("section[%s] query_evidence[%s] captured_at must include an ISO timezone" % (index, evidence_index))
                    if not invocation_id and len(no_id_reason) < 10:
                        issues.append("section[%s] query_evidence[%s] needs invocation_id or a specific not-exposed reason" % (index, evidence_index))
                if not REQUIRED_SECTION_LANES.issubset(evidenced_lanes):
                    issues.append("section[%s] query_evidence does not prove all four independent board lanes" % index)
                if is_count(row.get("query_count")) and row.get("query_count") != len(query_evidence):
                    issues.append("section[%s] query_count does not equal per-lane query_evidence records" % index)
                if not isinstance(families, list) or len(set([family.strip() for family in families if is_nonempty(family)])) < 2:
                    issues.append("section[%s] retrieval_proof needs two named source families" % index)
                else:
                    unique_families = set([family.strip() for family in families if is_nonempty(family)])
                    if any(GENERIC_SOURCE_FAMILY_PATTERN.search(family) for family in unique_families):
                        issues.append("section[%s] retrieval_proof uses a transport label as a source family" % index)
                    if is_count(row.get("source_family_count")) and row.get("source_family_count") != len(unique_families):
                        issues.append("section[%s] source_family_count does not equal distinct named source families" % index)
                    if unique_families != evidenced_source_families:
                        issues.append("section[%s] source_families_checked does not reconcile to per-query evidence" % index)
                if not isinstance(actor_classes, list) or len(set(value.strip() for value in actor_classes if is_nonempty(value))) < 3:
                    issues.append("section[%s] retrieval_proof needs at least three actor classes" % index)
                elif set(value.strip() for value in actor_classes if is_nonempty(value)) != evidenced_actor_classes:
                    issues.append("section[%s] actor_classes_checked does not reconcile to per-query evidence" % index)
                if not isinstance(event_families, list) or len(set(value.strip() for value in event_families if is_nonempty(value))) < 3:
                    issues.append("section[%s] retrieval_proof needs at least three event families" % index)
                elif set(value.strip() for value in event_families if is_nonempty(value)) != evidenced_event_families:
                    issues.append("section[%s] event_families_checked does not reconcile to per-query evidence" % index)
                if not is_count(opened):
                    issues.append("section[%s] retrieval_proof has invalid opened_candidate_count" % index)
                if not is_count(screened) or (is_count(opened) and screened < opened):
                    issues.append("section[%s] retrieval_proof needs screened_candidate_count at least opened_candidate_count" % index)
                if not is_count(target) or target < 2 or target > 3:
                    issues.append("section[%s] retrieval_proof target_card_count must be 2 or 3" % index)
                # target_card_count is a discovery target, never a rendered-card
                # quota. A genuinely scarce row may close below the ordinary
                # 4/6 review floor, but only with machine-readable proof that all
                # required lanes and an additional discovery pass were exhausted.
                is_closed_without_card = status in {"checked-empty", "limited"}
                min_candidates = 3 if is_closed_without_card else (6 if target == 3 else 4)
                min_families = 2 if is_closed_without_card else (3 if target == 3 else 2)
                rendered_full_count = (
                    (row.get("primary_card_count") or 0)
                    + (row.get("date_observation_card_count") or 0)
                    + (row.get("expanded_card_count") or 0)
                    + (row.get("business_observation_card_count") or 0)
                )
                scarce_pool_proved = (
                    pool_exhausted is True
                    and additional_pass is True
                    and is_nonempty(below_target_reason)
                    and not GENERIC_STOP_PATTERN.search(below_target_reason or "")
                    and REQUIRED_SECTION_LANES.issubset(evidenced_lanes)
                    and is_count(opened)
                    and is_count(screened)
                    and opened == row.get("candidate_count")
                    and screened >= opened
                    and discovered_result_total == len(recorded_candidate_ids)
                )
                if is_count(opened) and opened < min_candidates and not scarce_pool_proved:
                    issues.append(
                        "section[%s] below review depth needs exhausted-pool proof and an additional discovery pass (normal floor %s for target %s)"
                        % (index, min_candidates, target)
                    )
                if rendered_full_count < target and not scarce_pool_proved:
                    issues.append("section[%s] below target needs candidate_pool_exhausted, additional_discovery_completed and a specific below_target_reason" % index)
                if rendered_full_count < target:
                    expansion_rows = [e for e in query_evidence if isinstance(e, dict) and e.get("lane") == "expansion"]
                    if len(expansion_rows) != 1:
                        issues.append("section[%s] below target needs exactly one evidenced expansion pass" % index)
                    else:
                        expansion_families = set(value.strip() for value in expansion_rows[0].get("source_families_checked", []) if is_nonempty(value))
                        earlier_families = set()
                        for evidence in query_evidence:
                            if isinstance(evidence, dict) and evidence.get("lane") != "expansion":
                                earlier_families.update(value.strip() for value in evidence.get("source_families_checked", []) if is_nonempty(value))
                        if len(expansion_families) < 2 or not (expansion_families - earlier_families):
                            issues.append("section[%s] expansion must check two families and add a changed source family" % index)
                if isinstance(families, list) and len(set([family.strip() for family in families if is_nonempty(family)])) < min_families and not scarce_pool_proved:
                    issues.append(
                        "section[%s] retrieval_proof needs at least %s independent source families for target %s"
                        % (index, min_families, target)
                    )
                if pool_closure not in {"required-lanes-exhausted", "max-items-reached"}:
                    issues.append("section[%s] retrieval_proof has invalid candidate_pool_closure" % index)
                if not is_nonempty(closure_reason) or GENERIC_STOP_PATTERN.search(closure_reason or ""):
                    issues.append("section[%s] retrieval_proof needs a specific non-generic closure_reason" % index)
                if not is_nonempty(stop_reason) or GENERIC_STOP_PATTERN.search(stop_reason or ""):
                    issues.append("section[%s] retrieval_proof needs a specific non-generic stop_reason" % index)
                if mode in {"A", "B"} and network_reachable:
                    transports = proof.get("transport_routes")
                    direct_passes = proof.get("direct_source_passes")
                    if not isinstance(transports, list) or not any(is_nonempty(item) for item in transports):
                        issues.append("section[%s] needs a recorded working transport route" % index)
                    if not isinstance(direct_passes, list) or len([item for item in direct_passes if is_nonempty(item)]) < 2:
                        issues.append("section[%s] needs official-index and independent-discovery direct-source passes" % index)

    duplicates = [value for value, count in Counter(section_ids).items() if count > 1]
    if duplicates:
        issues.append("duplicate section ids: %s" % ", ".join(sorted(duplicates)))
    if plan_rows:
        ledger_ids = set(section_ids)
        planned_ids = set(plan_rows)
        if ledger_ids != planned_ids:
            missing = sorted(planned_ids - ledger_ids)
            extra = sorted(ledger_ids - planned_ids)
            if missing:
                issues.append("ledger omits planned sections: %s" % ", ".join(missing))
            if extra:
                issues.append("ledger contains sections absent from plan: %s" % ", ".join(extra))

    candidate_counts = Counter()
    decision_counts = Counter()
    section_decision_counts = {}
    section_events = {}
    event_decisions = {}
    included_fingerprints = {}
    included_canonical_urls = {}
    for index, row in enumerate(candidates):
        if not isinstance(row, dict):
            issues.append("candidate[%s] must be an object" % index)
            continue
        missing = [field for field in CANDIDATE_FIELDS if field not in row]
        if missing:
            issues.append("candidate[%s] missing fields: %s" % (index, ", ".join(missing)))
        section_id = row.get("section_id")
        if section_id not in section_rows:
            issues.append("candidate[%s] references unknown section_id" % index)
        else:
            candidate_counts[section_id] += 1
        for field in ("section_label", "title", "source_name", "source_tier", "source_family_id", "source_class", "actor_class", "event_family", "time_basis", "reason", "evidence_route"):
            if not is_nonempty(row.get(field)):
                issues.append("candidate[%s] has invalid %s" % (index, field))
        if PLACEHOLDER_PATTERN.search((row.get("title") or "") + (row.get("source_name") or "")):
            issues.append("candidate[%s] uses an anonymous placeholder title or source" % index)
        parsed = urlparse(row.get("url") or "")
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            issues.append("candidate[%s] has invalid URL" % index)
        if row.get("query_lane") not in QUERY_LANES:
            issues.append("candidate[%s] has invalid query_lane" % index)
        if row.get("relevance_level") not in RELEVANCE_LEVELS:
            issues.append("candidate[%s] has invalid relevance_level" % index)
        if row.get("actor_class") not in ACTOR_CLASSES:
            issues.append("candidate[%s] has invalid actor_class" % index)
        if row.get("event_family") not in EVENT_FAMILIES:
            issues.append("candidate[%s] has invalid event_family" % index)
        if row.get("source_class") not in SOURCE_CLASSES:
            issues.append("candidate[%s] has invalid source_class" % index)
        decision = row.get("decision")
        if decision not in DECISIONS:
            issues.append("candidate[%s] has invalid decision" % index)
            continue
        if live_contract and decision in INCLUDED_LIVE_DECISIONS:
            for field in ("direct_record_url", "canonical_url", "source_family_id", "event_fingerprint", "time_basis_type", "timestamp_precision", "window_class"):
                if not is_nonempty(row.get(field)):
                    issues.append("candidate[%s] included live item lacks %s" % (index, field))
            direct_record = urlparse(row.get("direct_record_url") or "")
            if direct_record.scheme not in {"http", "https"} or not direct_record.netloc:
                issues.append("candidate[%s] included live item has invalid direct_record_url" % index)
            if row.get("direct_record_kind") not in DIRECT_RECORD_KINDS:
                issues.append("candidate[%s] included live item has invalid direct_record_kind" % index)
            precision = row.get("timestamp_precision")
            window_class = row.get("window_class")
            basis_type = row.get("time_basis_type")
            if precision not in TIME_PRECISIONS:
                issues.append("candidate[%s] included live item has invalid timestamp_precision" % index)
            if window_class not in WINDOW_CLASSES:
                issues.append("candidate[%s] included live item has invalid window_class" % index)
            if basis_type not in {"published", "event"}:
                issues.append("candidate[%s] included live item has invalid time_basis_type" % index)
            timestamp_value = row.get("published_at") if basis_type == "published" else row.get("event_at")
            timestamp, parsed_precision = parse_timestamp(timestamp_value)
            if not timestamp:
                issues.append("candidate[%s] included live item has unusable selected time basis" % index)
            elif precision != parsed_precision:
                issues.append("candidate[%s] timestamp_precision does not match selected time basis" % index)
            elif precision == "date-only":
                if decision != "included-date-observation" or window_class != "observed":
                    issues.append("candidate[%s] date-only item must be included-date-observation with observed window" % index)
            elif decision == "included-date-observation" or window_class == "observed":
                issues.append("candidate[%s] datetime item has inconsistent observation classification" % index)
            elif window_bounds:
                fallback_start, primary_start, primary_end = window_bounds
                stamp_utc = timestamp.astimezone(datetime.timezone.utc)
                if window_class == "primary" and not (primary_start.astimezone(datetime.timezone.utc) <= stamp_utc <= primary_end.astimezone(datetime.timezone.utc)):
                    issues.append("candidate[%s] primary item lies outside primary window" % index)
                if window_class == "fallback" and not (fallback_start.astimezone(datetime.timezone.utc) <= stamp_utc < primary_start.astimezone(datetime.timezone.utc)):
                    issues.append("candidate[%s] fallback item lies outside fallback window" % index)
                if decision in {"included-expanded", "included-business-observation"} and not (fallback_start.astimezone(datetime.timezone.utc) <= stamp_utc <= primary_end.astimezone(datetime.timezone.utc)):
                    issues.append("candidate[%s] expanded/observation item lies outside rolling 48-hour window" % index)
        if decision == "included-baseline":
            if not (
                is_nonempty(row.get("published_at"))
                or is_nonempty(row.get("event_at"))
                or is_nonempty(row.get("retrieved_at"))
            ):
                issues.append("candidate[%s] baseline needs retrieved_at or a source date" % index)
        elif not is_nonempty(row.get("published_at")) and not is_nonempty(row.get("event_at")):
            issues.append("candidate[%s] needs published_at or event_at" % index)
        decision_counts[decision] += 1
        section_decision_counts.setdefault(section_id, Counter())[decision] += 1
        if decision in {"included-primary", "included-cross-section", "included-related", "included-date-observation", "included-expanded", "included-business-observation"}:
            event_id = row.get("event_id")
            if not is_nonempty(event_id):
                issues.append("candidate[%s] inclusion has no event_id" % index)
            else:
                event_decisions.setdefault(event_id, []).append(decision)
                section_events.setdefault(section_id, set()).add(event_id)
                if live_contract and decision in INCLUDED_LIVE_DECISIONS:
                    fingerprint = (row.get("event_fingerprint") or "").strip().lower()
                    canonical = canonicalize_url(row.get("canonical_url") or row.get("direct_record_url"))
                    if fingerprint:
                        included_fingerprints.setdefault(fingerprint, set()).add(section_id)
                    if canonical:
                        included_canonical_urls.setdefault(canonical, set()).add(section_id)
        if decision == "included-cross-section" and row.get("relevance_level") == "D":
            issues.append("candidate[%s] uses D-level cross-section inclusion" % index)
        if decision in {"included-cross-section", "included-related"}:
            issues.append("candidate[%s] uses prohibited cross-section or related inclusion" % index)
        if decision == "included-baseline" and not is_nonempty(row.get("baseline_kind")):
            issues.append("candidate[%s] baseline inclusion needs baseline_kind" % index)

    for section_id, row in section_rows.items():
        declared = row.get("candidate_count")
        if is_count(declared) and candidate_counts[section_id] != declared:
            issues.append(
                "candidate count mismatch for %s: declared %s, found %s"
                % (section_id, declared, candidate_counts[section_id])
            )
        actual = section_decision_counts.get(section_id, Counter())
        declared_decisions = {
            "included-primary": row.get("primary_card_count"),
            "included-cross-section": row.get("cross_section_card_count"),
            "included-related": row.get("related_count"),
            "included-date-observation": row.get("date_observation_card_count", 0),
            "included-expanded": row.get("expanded_card_count", 0),
            "included-business-observation": row.get("business_observation_card_count", 0),
            "included-baseline": row.get("baseline_card_count", 0),
        }
        for decision, declared_count in declared_decisions.items():
            if is_count(declared_count) and actual[decision] != declared_count:
                issues.append(
                    "%s count mismatch for %s: declared %s, found %s"
                    % (decision, section_id, declared_count, actual[decision])
                )
        declared_unique = row.get("unique_event_count")
        actual_unique = len(section_events.get(section_id, set()))
        if is_count(declared_unique) and actual_unique != declared_unique:
            issues.append(
                "unique event count mismatch for %s: declared %s, found %s"
                % (section_id, declared_unique, actual_unique)
            )
        if live_contract:
            proof = row.get("retrieval_proof") or {}
            opened = proof.get("opened_candidate_count")
            if is_count(opened) and opened != candidate_counts[section_id]:
                issues.append("opened candidate count mismatch for %s: declared %s, found %s" % (section_id, opened, candidate_counts[section_id]))
            target = proof.get("target_card_count")
            is_closed_without_card = row.get("status") in {"checked-empty", "limited"}
            min_candidates = 3 if is_closed_without_card else (6 if target == 3 else 4)
            if is_count(target) and candidate_counts[section_id] < min_candidates and not scarce_pool_proved:
                issues.append(
                    "section %s has insufficient real candidate records: needs %s for target %s, found %s"
                    % (section_id, min_candidates, target, candidate_counts[section_id])
                )
            full_count = sum(actual[decision] for decision in ("included-primary", "included-cross-section", "included-date-observation", "included-expanded", "included-business-observation"))
            if is_count(target) and full_count < target and not is_closed_without_card and not scarce_pool_proved:
                if proof.get("additional_discovery_completed") is not True:
                    issues.append("under-target row %s lacks completed additional discovery pass" % section_id)
                if candidate_counts[section_id] < target + 2:
                    issues.append("under-target row %s needs at least target+2 opened candidates" % section_id)
                below_target_reason = proof.get("below_target_reason")
                if not is_nonempty(below_target_reason) or GENERIC_STOP_PATTERN.search(below_target_reason or ""):
                    issues.append("under-target row %s needs a specific below_target_reason" % section_id)
                if actual["excluded"] < max(0, target + 2 - full_count):
                    issues.append("under-target row %s lacks documented excluded candidates" % section_id)
                domains = set()
                for candidate in candidates:
                    if candidate.get("section_id") == section_id:
                        parsed = urlparse(candidate.get("url") or "")
                        if parsed.netloc:
                            domains.add(parsed.netloc.lower())
                if len(domains) < 2:
                    issues.append("under-target row %s lacks evidence from two candidate domains" % section_id)
        if section_id in plan_rows:
            planned = plan_rows[section_id]
            floor = planned.get("candidate_review_floor")
            family_floor = planned.get("source_family_floor")
            if is_count(floor) and candidate_counts[section_id] < floor and not scarce_pool_proved:
                issues.append("section %s is below planned candidate review floor: needs %s, found %s" % (section_id, floor, candidate_counts[section_id]))
            if is_count(family_floor) and is_count(row.get("source_family_count")) and row.get("source_family_count") < family_floor and not scarce_pool_proved:
                issues.append("section %s is below planned source-family floor: needs %s, found %s" % (section_id, family_floor, row.get("source_family_count")))

    for event_id, decisions in event_decisions.items():
        full_count = sum(1 for decision in decisions if decision in {"included-primary", "included-cross-section", "included-date-observation", "included-expanded", "included-business-observation"})
        if full_count > 1:
            issues.append("event %s appears in more than one rendered section" % event_id)
        if "included-cross-section" in decisions:
            issues.append("event %s uses prohibited cross-section inclusion" % event_id)

    for fingerprint, assigned_sections in included_fingerprints.items():
        if len(assigned_sections) > 1:
            issues.append("event fingerprint %s is included in multiple sections: %s" % (fingerprint, ", ".join(sorted(assigned_sections))))
    for canonical, assigned_sections in included_canonical_urls.items():
        if len(assigned_sections) > 1:
            issues.append("canonical source %s is included in multiple sections: %s" % (canonical, ", ".join(sorted(assigned_sections))))

    result = {
        "ok": not issues,
        "ledger_file": str(args.ledger_file.resolve()),
        "section_count": len(sections),
        "candidate_count": len(candidates),
        "decision_counts": dict(decision_counts),
        "unique_included_event_count": len(event_decisions),
        "issues": issues,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
