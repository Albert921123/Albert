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


class BriefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.ids = Counter()
        self.classes = Counter()
        self.scripts = []
        self._script_parts = None
        self.external_links = []
        self.story_records = []
        self.related_records = []
        self.section_records = []
        self._section_stack = []

    def handle_starttag(self, tag, attrs):
        data = {key: value or "" for key, value in attrs}
        if data.get("id"):
            self.ids[data["id"]] += 1
        class_names = set(data.get("class", "").split())
        self.classes.update(class_names)
        if tag == "section" and "section" in class_names:
            section_record = {
                "attrs": data,
                "story_count": 0,
                "related_count": 0,
                "empty_states": [],
            }
            self.section_records.append(section_record)
            self._section_stack.append(section_record)
        if "story" in class_names:
            self.story_records.append(data)
            if self._section_stack:
                self._section_stack[-1]["story_count"] = int(self._section_stack[-1]["story_count"]) + 1
        if "related-evidence" in class_names:
            self.related_records.append(data)
            if self._section_stack:
                self._section_stack[-1]["related_count"] = int(self._section_stack[-1]["related_count"]) + 1
        if "empty" in class_names and self._section_stack:
            empty_states = self._section_stack[-1]["empty_states"]
            assert isinstance(empty_states, list)
            empty_states.append(data.get("data-empty-state", ""))
        if tag == "a" and data.get("href"):
            parsed = urlparse(data["href"])
            if parsed.scheme in {"http", "https"}:
                self.external_links.append(data)
        if tag == "script":
            self._script_parts = []

    def handle_endtag(self, tag):
        if tag == "script" and self._script_parts is not None:
            self.scripts.append("".join(self._script_parts))
            self._script_parts = None
        if tag == "section" and self._section_stack:
            self._section_stack.pop()

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
    parser.add_argument("--allow-placeholders", action="store_true")
    args = parser.parse_args()

    issues = []
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
    if "--mobile-topbar-height" not in text:
        issues.append("missing dynamic mobile sticky offset")

    if not args.allow_placeholders and re.search(r"\{\{[^{}]+\}\}", text):
        issues.append("unresolved template placeholders remain")

    story_count = document.classes["story"]
    section_count = document.classes["section"]
    related_count = document.classes["related-evidence"]
    if args.expected_items is not None and story_count != args.expected_items:
        issues.append(f"story count mismatch: expected {args.expected_items}, found {story_count}")
    if args.expected_sections is not None and section_count != args.expected_sections:
        issues.append(f"section count mismatch: expected {args.expected_sections}, found {section_count}")
    if args.expected_related is not None and related_count != args.expected_related:
        issues.append(f"related evidence count mismatch: expected {args.expected_related}, found {related_count}")
    for index, record in enumerate(document.story_records):
        if not record.get("id"):
            issues.append(f"story[{index}] has no id")
        if not record.get("data-story-section"):
            issues.append(f"story[{index}] has no data-story-section")
        freshness_window = record.get("data-freshness-window", "")
        unresolved_window = args.allow_placeholders and "{{" in freshness_window
        if not unresolved_window and freshness_window not in {"primary", "fallback"}:
            issues.append(f"story[{index}] has invalid data-freshness-window")
    for index, record in enumerate(document.related_records):
        if not record.get("data-related-section"):
            issues.append(f"related-evidence[{index}] has no data-related-section")
    for index, record in enumerate(document.section_records):
        attrs = record["attrs"]
        assert isinstance(attrs, dict)
        if attrs.get("data-section-kind") != "custom":
            continue
        status = attrs.get("data-coverage-status", "")
        custom_label = attrs.get("data-topic-name") or attrs.get("data-section-name") or attrs.get("id") or f"custom[{index}]"
        custom_story_count = int(record["story_count"])
        custom_related_count = int(record["related_count"])
        empty_states = record["empty_states"]
        assert isinstance(empty_states, list)
        if status not in {"complete", "checked-empty", "limited"}:
            issues.append(f"custom section {custom_label!r} has invalid data-coverage-status")
        if status == "complete" and custom_story_count < 1:
            issues.append(f"custom section {custom_label!r} is complete without a formal story")
        if status == "checked-empty" and (custom_story_count or "checked-empty" not in empty_states):
            issues.append(f"custom section {custom_label!r} lacks a matching checked-empty card")
        if status == "limited" and (custom_story_count or "limited" not in empty_states):
            issues.append(f"custom section {custom_label!r} lacks a matching limited card")
        if custom_story_count == 0 and custom_related_count and not empty_states:
            issues.append(f"custom section {custom_label!r} is related-only")

    if document.classes["freshness-badge"] != story_count:
        issues.append(
            "freshness badge count mismatch: "
            f"expected {story_count}, found {document.classes['freshness-badge']}"
        )
    fallback_story_count = sum(
        1 for record in document.story_records if record.get("data-freshness-window") == "fallback"
    )
    if fallback_story_count and "48小时补充" not in text:
        issues.append("fallback stories exist but the visible 48小时补充 label is missing")

    for index, link in enumerate(document.external_links):
        if link.get("target") != "_blank":
            issues.append(f"external link[{index}] does not use target=_blank")
        rel = set(link.get("rel", "").split())
        if not {"noopener", "noreferrer"}.issubset(rel):
            issues.append(f"external link[{index}] lacks noopener noreferrer")

    result = {
        "ok": not issues,
        "html_file": str(args.html_file.resolve()),
        "section_count": section_count,
        "story_count": story_count,
        "related_evidence_count": related_count,
        "fallback_story_count": fallback_story_count,
        "external_link_count": len(document.external_links),
        "inline_script_count": len(document.scripts),
        "issues": issues,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
