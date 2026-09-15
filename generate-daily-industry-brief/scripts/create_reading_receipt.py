#!/usr/bin/env python3
"""Create a hash-bound inventory after an Agent has read the full skill bundle."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

from py36_compat import configure_utf8_stdio


TEXT_SUFFIXES = {".md", ".json", ".html", ".py", ".cmd", ".sh", ".yaml", ".yml", ".txt"}
SKIP_PARTS = {"__pycache__", ".git", ".DS_Store", ".zhixun-state"}


def inventory(root):
    rows = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        relative = path.relative_to(root)
        if any(part in SKIP_PARTS for part in relative.parts):
            continue
        payload = path.read_bytes()
        rows.append({
            "path": relative.as_posix(),
            "sha256": hashlib.sha256(payload).hexdigest(),
            "bytes": len(payload),
        })
    return rows


def main():
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--skill-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()

    root = args.skill_dir.resolve()
    rows = inventory(root)
    receipt = {
        "schema_version": 1,
        "purpose": "full-package-reading-receipt",
        "run_id": args.run_id,
        "skill_dir": str(root),
        "instruction": "Create this receipt only after every listed installation file has been read to EOF.",
        "file_count": len(rows),
        "files": rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "receipt": str(args.output.resolve()), "file_count": len(rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
