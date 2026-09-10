#!/usr/bin/env python3
"""Static acceptance checks for a generated standalone daily-brief HTML file."""

import argparse
import json
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

from py36_compat import configure_utf8_stdio


def canonicalize_url(value):
    parsed = urlparse(value or "")
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    path = parsed.path.rstrip("/") or "/"
    return (parsed.netloc.lower() + path).lower()


class BriefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids = Counter()
        self.classes = Counter()
        self.scripts = []
        self._script_parts = None
        self.external_links = []
        self.story_records = []
        self.story_links = {}
        self._story_stack = []
        self.related_records = []
        self.section_records = []
        self.audit_rows = []
        self._audit_row_stack = []
        self.audit_detail_count = 0
        self._section_stack = []
        self._highlights_depth = 0
        self.highlight_links = []

    def handle_starttag(self, tag, attrs):
        data = {key: value or "" for key, value in attrs}
        if data.get("id"):
            self.ids[data["id"]] += 1
        class_names = set(data.get("class", "").split())
        self.classes.update(class_names)
        if tag == "section" and "highlights" in class_names:
            self._highlights_depth += 1
        if tag == "section" and "section" in class_names:
            section_record = {
                "attrs": data,
                "story_count": 0,
                "baseline_story_count": 0,
                "related_count": 0,
                "empty_states": [],
            }
            self.section_records.append(section_record)
            self._section_stack.append(section_record)
        if "story" in class_names:
            story_index = len(self.story_records)
            self.story_records.append(data)
            self._story_stack.append(story_index)
            if self._section_stack:
                self._section_stack[-1]["story_count"] = int(self._section_stack[-1]["story_count"]) + 1
                if data.get("data-entry-kind") == "baseline":
                    self._section_stack[-1]["baseline_story_count"] = int(
                        self._section_stack[-1]["baseline_story_count"]
                    ) + 1
        if "related-evidence" in class_names:
            self.related_records.append(data)
            if self._section_stack:
                self._section_stack[-1]["related_count"] = int(self._section_stack[-1]["related_count"]) + 1
        if data.get("data-audit-row"):
            audit_row = {"attrs": data, "tag": tag, "cell_count": 0}
            self.audit_rows.append(audit_row)
            self._audit_row_stack.append(audit_row)
        elif tag == "span" and self._audit_row_stack:
            self._audit_row_stack[-1]["cell_count"] += 1
        if "audit-section-detail" in class_names:
            self.audit_detail_count += 1
        if "empty" in class_names and self._section_stack:
            empty_states = self._section_stack[-1]["empty_states"]
            assert isinstance(empty_states, list)
            empty_states.append(data.get("data-empty-state", ""))
        if tag == "a" and data.get("href"):
            if self._highlights_depth and data["href"].startswith("#"):
                self.highlight_links.append(data)
            parsed = urlparse(data["href"])
            if parsed.scheme in {"http", "https"}:
                self.external_links.append(data)
                if self._story_stack:
                    self.story_links.setdefault(self._story_stack[-1], []).append(data)
        if tag == "script":
            self._script_parts = []

    def handle_endtag(self, tag):
        if tag == "script" and self._script_parts is not None:
            self.scripts.append("".join(self._script_parts))
            self._script_parts = None
        if tag == "section" and self._section_stack:
            self._section_stack.pop()
        if tag == "article" and self._story_stack:
            self._story_stack.pop()
        if self._audit_row_stack and tag == self._audit_row_stack[-1]["tag"]:
            self._audit_row_stack.pop()
        if tag == "section" and self._highlights_depth:
            self._highlights_depth -= 1

    def handle_data(self, data):
        if self._script_parts is not None:
            self._script_parts.append(data)


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("html_file", type=Path)
    parser.add_argument("--expected-items", type=int)
    parser.add_argument("--expected-sections", type=int)
    parser.add_argument("--expected-related", type=int)
    parser.add_argument("--expected-unique-events", type=int)
    parser.add_argument("--expected-cross-section", type=int)
    parser.add_argument("--expected-baseline", type=int)
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--allow-placeholders", action="store_true")
    args = parser.parse_args()

    # A live brief is not independently auditable without its candidate ledger.
    # Keep template validation usable, but make the normal artifact path fail
    # closed when the matching ledger was not supplied.
    if args.ledger is None and not args.allow_placeholders:
        sibling = args.html_file.with_name(
            args.html_file.name.replace("daily-industry-brief-", "retrieval-ledger-").replace(".html", ".json")
        )
        if sibling.is_file():
            args.ledger = sibling

    issues = []
    if args.ledger is None and not args.allow_placeholders:
        issues.append("missing matching retrieval ledger; normal briefs require --ledger or a sibling retrieval-ledger-YYYY-MM-DD.json")
    try:
        text = args.html_file.read_text(encoding="utf-8")
    except Exception as exc:
        print(json.dumps({"ok": False, "issues": [f"cannot read UTF-8 HTML: {exc}"]}, ensure_ascii=False, indent=2))
        return 2

    document = BriefParser()
    try:
        document.feed(text)
    except Exception as exc:
        issues.append(f"HTML parser error: {exc}")

    if "<!doctype html" not in text[:200].lower():
        issues.append("missing HTML5 doctype")
    for required_id in ("brief-search", "clear-search", "search-status", "topic-nav", "content-scroll", "no-results"):
        if document.ids[required_id] != 1:
            issues.append(f"expected exactly one id={required_id!r}, found {document.ids[required_id]}")
    for required_class in ("section", "topic-nav", "search-hit"):
        if required_class == "search-hit":
            if ".search-hit" not in text:
                issues.append("missing search-hit style")
        elif document.classes[required_class] < 1:
            issues.append(f"missing .{required_class} element")

    scripts = "\n".join(document.scripts)
    for marker in ("filterBrief", "searchableUnits", "ResizeObserver", "scrollIntoView"):
        if marker not in scripts:
            issues.append(f"missing interactive script marker: {marker}")
    if "Enter" not in scripts:
        issues.append("missing Enter-to-first-match search jump handler")
    if "--mobile-topbar-height" not in text:
        issues.append("missing dynamic mobile sticky offset")
    # A malformed character class was once introduced when JavaScript was
    # embedded in a Python string, leaving /[...|[\]\]/g in the output.  It
    # prevents the whole inline script from parsing only after a user types.
    if "[\\]\\]" in text:
        issues.append("search script contains malformed escaped character class")
    if document.classes["coverage-audit"] != 1 or document.classes["audit-body"] != 1:
        issues.append("missing complete reader-facing coverage audit panel")
    if document.classes["audit-grid"] != 1:
        issues.append("coverage audit is missing its section grid")
    if document.classes["highlights"] != 1 or document.classes["highlights-label"] != 1:
        issues.append("missing structured 今日重点 highlight area")
    if not args.allow_placeholders and len(document.highlight_links) not in {2, 3}:
        issues.append("今日重点 must contain two or three linked business cards")
    if "检索审计 · 本次为" in text or "检索审计：本次为" in text:
        issues.append("coverage audit was replaced by a trial-note summary")

    if not args.allow_placeholders and re.search(r"\{\{[^{}]+\}\}", text):
        issues.append("unresolved template placeholders remain")

    story_count = document.classes["story"]
    section_count = document.classes["section"]
    related_count = document.classes["related-evidence"]
    if args.expected_items is not None and story_count != args.expected_items:
        issues.append(f"story count mismatch: expected {args.expected_items}, found {story_count}")
    if args.expected_sections is not None and section_count != args.expected_sections:
        issues.append(f"section count mismatch: expected {args.expected_sections}, found {section_count}")
    if not args.allow_placeholders and len(document.audit_rows) != section_count:
        issues.append(f"audit row count mismatch: expected {section_count}, found {len(document.audit_rows)}")
    malformed_audit_rows = [
        row["attrs"].get("data-audit-row", "?")
        for row in document.audit_rows
        if row["cell_count"] != 7
    ]
    if malformed_audit_rows:
        issues.append("each audit row must contain exactly seven cells: " + ", ".join(malformed_audit_rows))
    if not args.allow_placeholders and document.audit_detail_count != section_count:
        issues.append(f"audit detail count mismatch: expected {section_count}, found {document.audit_detail_count}")
    if args.expected_related is not None and related_count != args.expected_related:
        issues.append(f"related evidence count mismatch: expected {args.expected_related}, found {related_count}")
    for index, record in enumerate(document.story_records):
        unresolved_story = args.allow_placeholders and any(
            "{{" in record.get(field, "")
            for field in ("id", "data-story-section", "data-event-id", "data-entry-kind")
        )
        if not record.get("id"):
            issues.append(f"story[{index}] has no id")
        if not record.get("data-story-section"):
            issues.append(f"story[{index}] has no data-story-section")
        if not record.get("data-event-id"):
            issues.append(f"story[{index}] has no data-event-id")
        if not unresolved_story and record.get("data-entry-kind") not in {"primary", "cross-section", "date-observation", "expanded", "business-observation", "baseline"}:
            issues.append(f"story[{index}] has invalid data-entry-kind")
        freshness_window = record.get("data-freshness-window", "")
        unresolved_window = args.allow_placeholders and "{{" in freshness_window
        if not unresolved_window and freshness_window not in {"primary", "fallback", "observed", "expanded", "business-observation", "baseline"}:
            issues.append(f"story[{index}] has invalid data-freshness-window")
    for index, record in enumerate(document.related_records):
        if not record.get("data-related-section"):
            issues.append(f"related-evidence[{index}] has no data-related-section")
    for index, record in enumerate(document.section_records):
        attrs = record["attrs"]
        assert isinstance(attrs, dict)
        status = attrs.get("data-coverage-status", "")
        unresolved_status = args.allow_placeholders and "{{" in status
        section_label = attrs.get("data-topic-name") or attrs.get("data-section-name") or attrs.get("id") or f"section[{index}]"
        section_story_count = int(record["story_count"])
        section_baseline_count = int(record["baseline_story_count"])
        section_formal_count = section_story_count - section_baseline_count
        section_related_count = int(record["related_count"])
        empty_states = record["empty_states"]
        assert isinstance(empty_states, list)
        if not unresolved_status and status not in {"complete", "observed", "expanded", "business-observation", "checked-empty", "limited", "baseline"}:
            issues.append(f"section {section_label!r} has invalid data-coverage-status")
        if not unresolved_status and status == "complete" and section_formal_count < 1:
            issues.append(f"section {section_label!r} is complete without a full story card")
        if not unresolved_status and status == "observed" and not any(
            item.get("data-entry-kind") == "date-observation" and item.get("data-story-section") == section_label
            for item in document.story_records
        ):
            issues.append(f"section {section_label!r} is observed without a date-only observation card")
        if not unresolved_status and status == "expanded" and not any(
            item.get("data-entry-kind") == "expanded" and item.get("data-story-section") == section_label
            for item in document.story_records
        ):
            issues.append(f"section {section_label!r} is expanded without an expanded card")
        if not unresolved_status and status == "business-observation" and not any(
            item.get("data-entry-kind") == "business-observation" and item.get("data-story-section") == section_label
            for item in document.story_records
        ):
            issues.append(f"section {section_label!r} is business-observation without an observation card")
        if status == "checked-empty" and (section_story_count or "checked-empty" not in empty_states):
            issues.append(f"section {section_label!r} lacks a matching checked-empty card")
        if status == "limited" and not (
            (section_story_count == 0 and "limited" in empty_states) or section_baseline_count >= 1
        ):
            issues.append(f"section {section_label!r} lacks a matching limited card")
        if status == "baseline" and section_baseline_count < 1:
            issues.append(f"section {section_label!r} lacks a baseline card")
        if section_story_count == 0 and section_related_count and not empty_states:
            issues.append(f"section {section_label!r} is compact-related-only")

    event_entries = {}
    cross_section_count = 0
    baseline_count = 0
    for index, record in enumerate(document.story_records):
        event_id = record.get("data-event-id", "")
        entry_kind = record.get("data-entry-kind", "")
        if entry_kind == "baseline":
            baseline_count += 1
            if "baseline-card" not in set(record.get("class", "").split()):
                issues.append(f"story[{index}] baseline entry lacks .baseline-card")
            continue
        if args.allow_placeholders and ("{{" in event_id or "{{" in entry_kind):
            continue
        if event_id:
            event_entries.setdefault(event_id, []).append(entry_kind)
        if entry_kind == "cross-section":
            cross_section_count += 1
            if "cross-section-story" not in set(record.get("class", "").split()):
                issues.append(f"story[{index}] cross-section entry lacks .cross-section-story")
    for event_id, entry_kinds in event_entries.items():
        if len(entry_kinds) > 1:
            issues.append(f"event {event_id!r} appears in more than one rendered section")
        if "cross-section" in entry_kinds:
            issues.append(f"event {event_id!r} uses prohibited cross-section inclusion")
    unique_event_count = len(event_entries)
    if args.expected_unique_events is not None and unique_event_count != args.expected_unique_events:
        issues.append(
            f"unique event count mismatch: expected {args.expected_unique_events}, found {unique_event_count}"
        )
    if args.expected_cross_section is not None and cross_section_count != args.expected_cross_section:
        issues.append(
            f"cross-section count mismatch: expected {args.expected_cross_section}, found {cross_section_count}"
        )
    if cross_section_count:
        issues.append(f"cross-section story count must be zero, found {cross_section_count}")
    if args.expected_baseline is not None and baseline_count != args.expected_baseline:
        issues.append(f"baseline count mismatch: expected {args.expected_baseline}, found {baseline_count}")

    formal_story_count = story_count - baseline_count
    if document.classes["freshness-badge"] != formal_story_count:
        issues.append(
            "freshness badge count mismatch: "
            f"expected {formal_story_count}, found {document.classes['freshness-badge']}"
        )
    fallback_story_count = sum(
        1 for record in document.story_records if record.get("data-freshness-window") == "fallback"
    )
    if fallback_story_count and "48小时补充" not in text:
        issues.append("fallback stories exist but the visible 48小时补充 label is missing")
    observation_story_count = sum(
        1 for record in document.story_records if record.get("data-freshness-window") == "observed"
    )
    if observation_story_count and "48小时窗口观察" not in text:
        issues.append("date-only observation stories exist but the visible 48小时窗口观察 label is missing")

    for index, link in enumerate(document.external_links):
        if link.get("target") != "_blank":
            issues.append(f"external link[{index}] does not use target=_blank")
        rel = set(link.get("rel", "").split())
        if not {"noopener", "noreferrer"}.issubset(rel):
            issues.append(f"external link[{index}] lacks noopener noreferrer")

    if args.ledger is not None:
        try:
            ledger = json.loads(args.ledger.read_text(encoding="utf-8"))
            ledger_candidates = ledger.get("candidates", []) if isinstance(ledger, dict) else []
        except Exception as exc:
            ledger_candidates = []
            issues.append(f"cannot read linked retrieval ledger: {exc}")
        included_decisions = {
            "included-primary",
            "included-date-observation",
            "included-expanded",
            "included-business-observation",
        }
        included_events = {}
        for candidate in ledger_candidates:
            if not isinstance(candidate, dict) or candidate.get("decision") not in included_decisions:
                continue
            event_id = candidate.get("event_id", "")
            if not event_id:
                issues.append("linked ledger has included item without event_id")
                continue
            included_events[event_id] = candidate
        html_events = {}
        for index, record in enumerate(document.story_records):
            if record.get("data-entry-kind") == "baseline":
                continue
            event_id = record.get("data-event-id", "")
            html_events[event_id] = index
            if event_id not in included_events:
                issues.append(f"HTML story event {event_id!r} is absent from linked ledger inclusions")
                continue
            expected_source = canonicalize_url(
                included_events[event_id].get("direct_record_url") or included_events[event_id].get("url")
            )
            story_sources = {
                canonicalize_url(link.get("href", ""))
                for link in document.story_links.get(index, [])
            }
            if expected_source and expected_source not in story_sources:
                issues.append(f"HTML story event {event_id!r} does not link to its ledger direct record")
        for event_id in included_events:
            if event_id not in html_events:
                issues.append(f"linked ledger included event {event_id!r} is absent from HTML")

    result = {
        "ok": not issues,
        "html_file": str(args.html_file.resolve()),
        "section_count": section_count,
        "story_count": story_count,
        "unique_event_count": unique_event_count,
        "cross_section_story_count": cross_section_count,
        "baseline_card_count": baseline_count,
        "related_evidence_count": related_count,
        "audit_row_count": len(document.audit_rows),
        "audit_detail_count": document.audit_detail_count,
        "fallback_story_count": fallback_story_count,
        "date_observation_story_count": observation_story_count,
        "external_link_count": len(document.external_links),
        "inline_script_count": len(document.scripts),
        "issues": issues,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
