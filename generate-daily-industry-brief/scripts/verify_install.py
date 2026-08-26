#!/usr/bin/env python3
"""Verify that the complete skill bundle is present and version-consistent."""

import argparse
import json
import sys
from pathlib import Path

from py36_compat import configure_utf8_stdio


REQUIRED = (
    "README.md",
    "SKILL.md",
    "manifest.json",
    "agents/openai.yaml",
    "assets/browser-subscription-selector.html",
    "assets/codex-subscription-selector.html",
    "assets/daily-brief-template.html",
    "references/topics.md",
    "references/source-map.md",
    "references/retrieval-audit.md",
    "references/retrieval-routing.md",
    "references/runtime-compatibility.md",
    "references/news-input-schema.json",
    "scripts/validate_preferences.py",
    "scripts/py36_compat.py",
    "scripts/validate_html.py",
    "scripts/validate_news_input.py",
    "scripts/verify_schedule.py",
)


def main():
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--expected-version", default="1.9.8")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = args.skill_dir.resolve()
    missing = [relative for relative in REQUIRED if not (root / relative).is_file()]
    issues = []
    manifest = {}
    try:
        manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    except Exception as exc:
        issues.append(f"manifest unreadable: {exc}")

    if manifest.get("name") != "generate-daily-industry-brief":
        issues.append("manifest skill name mismatch")
    if manifest.get("distribution_version") != args.expected_version:
        issues.append(
            f"distribution version mismatch: expected {args.expected_version}, "
            f"got {manifest.get('distribution_version')!r}"
        )
    issues.extend(f"missing required file: {name}" for name in missing)

    result = {
        "ok": not issues,
        "skill_dir": str(root),
        "distribution_version": manifest.get("distribution_version"),
        "core_version": manifest.get("core_version"),
        "required_file_count": len(REQUIRED),
        "issues": issues,
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("INSTALL_OK" if result["ok"] else "INSTALL_INVALID")
        print(json.dumps(result, ensure_ascii=False))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
