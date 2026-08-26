#!/usr/bin/env python3
"""Write an atomic success marker after a daily HTML brief completes."""

import argparse
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from config_fingerprint import compute_config_fingerprint
from py36_compat import configure_utf8_stdio

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python 3.6-3.8 fallback; Shanghai uses a fixed offset below
    ZoneInfo = None


SUBSCRIPTION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}")


def resolve_timezone(name: str):
    if name == "Asia/Shanghai":
        return timezone(timedelta(hours=8), name)
    if ZoneInfo is None:
        raise SystemExit(f"timezone database unavailable for {name}")
    return ZoneInfo(name)


def is_valid_html_artifact(path: Path) -> bool:
    """Reject empty, mislabeled, or obviously incomplete success artifacts."""
    if not path.is_file() or path.suffix.lower() not in {".html", ".htm"}:
        return False
    try:
        if path.stat().st_size < 128:
            return False
        prefix = path.read_text(encoding="utf-8", errors="ignore")[:8192].lower()
    except OSError:
        return False
    return "<html" in prefix or "<!doctype html" in prefix


def load_config_state(path: Path) -> dict:
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def main() -> int:
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--subscription-id", default="primary")
    parser.add_argument("--timezone", default="Asia/Shanghai")
    parser.add_argument("--state-dir", type=Path, default=Path(".zhixun-state"))
    parser.add_argument("--html-file", type=Path, required=True)
    parser.add_argument("--config-state-file", type=Path)
    args = parser.parse_args()
    if not SUBSCRIPTION_ID_PATTERN.fullmatch(args.subscription_id):
        raise SystemExit("invalid subscription ID")
    if not is_valid_html_artifact(args.html_file):
        raise SystemExit(f"valid HTML artifact not found: {args.html_file}")
    now = datetime.now(resolve_timezone(args.timezone))
    args.state_dir.mkdir(parents=True, exist_ok=True)
    config_state_file = args.config_state_file or (
        args.state_dir / f"current-config-{args.subscription_id}.json"
    )
    config_state = load_config_state(config_state_file)
    current_config = config_state.get("config")
    config_fingerprint = None
    if isinstance(current_config, dict):
        config_fingerprint = compute_config_fingerprint(current_config)
    target = args.state_dir / f"last-success-{args.subscription_id}.json"
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps({
        "subscription_id": args.subscription_id,
        "local_date": now.date().isoformat(),
        "completed_at": now.isoformat(),
        "html_file": str(args.html_file.resolve()),
        "config_fingerprint": config_fingerprint,
        "configuration_effective_at": config_state.get("effective_at"),
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(target)
    print(target.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
