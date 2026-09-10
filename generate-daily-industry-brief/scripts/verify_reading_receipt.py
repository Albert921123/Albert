#!/usr/bin/env python3
"""Fail closed when a run receipt does not cover the current complete skill bundle."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from create_reading_receipt import inventory
from py36_compat import configure_utf8_stdio


def main():
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    issues = []
    try:
        receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    except Exception as exc:
        print(json.dumps({"ok": False, "issues": ["receipt unreadable: %s" % exc]}, ensure_ascii=False))
        return 2

    if receipt.get("purpose") != "full-package-reading-receipt":
        issues.append("receipt purpose mismatch")
    if receipt.get("run_id") != args.run_id:
        issues.append("receipt run_id mismatch")
    actual = inventory(args.skill_dir.resolve())
    expected = receipt.get("files")
    if expected != actual:
        issues.append("receipt does not match every current textual installation file")
    result = {"ok": not issues, "receipt": str(args.receipt), "file_count": len(actual), "issues": issues}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not issues else 2


if __name__ == "__main__":
    sys.exit(main())
