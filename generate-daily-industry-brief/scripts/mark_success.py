#!/usr/bin/env python3
"""Write an atomic success marker after a daily HTML brief completes."""

import argparse
import json
import re
import subprocess
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
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    prefix = text[:8192].lower()
    if not ("<html" in prefix or "<!doctype html" in prefix):
        return False
    # A transparent date-only observation is useful to readers, but it is not
    # proof of a timestamped successful run.  Enforce the same rule here so a
    # caller cannot accidentally suppress target-period retries.
    return not bool(re.search(r'data-coverage-status=["\'](?:observed|expanded|business-observation|limited|baseline)["\']', text, re.I))


def validators_pass(html_file: Path, ledger_file: Path) -> bool:
    """Run both delivery gates; success markers cannot bypass the ledger."""
    scripts_dir = Path(__file__).resolve().parent
    commands = (
        [sys.executable, str(scripts_dir / "validate_retrieval_ledger.py"), str(ledger_file)],
        [sys.executable, str(scripts_dir / "validate_html.py"), str(html_file), "--ledger", str(ledger_file)],
    )
    for command in commands:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            return False
    return True


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
    parser.add_argument("--ledger-file", type=Path, required=True)
    parser.add_argument("--config-state-file", type=Path)
    parser.add_argument("--report-date", help="YYYY-MM-DD; required for a late catch-up target")
    args = parser.parse_args()
    if not SUBSCRIPTION_ID_PATTERN.fullmatch(args.subscription_id):
        raise SystemExit("invalid subscription ID")
    if not is_valid_html_artifact(args.html_file):
        raise SystemExit(f"valid HTML artifact not found: {args.html_file}")
    if not args.ledger_file.is_file():
        raise SystemExit(f"validated retrieval ledger not found: {args.ledger_file}")
    if not validators_pass(args.html_file, args.ledger_file):
        raise SystemExit("delivery gate failed: retrieval ledger and HTML must both validate before success marking")
    now = datetime.now(resolve_timezone(args.timezone))
    report_date = args.report_date
    if not report_date:
        match = re.search(r"daily-industry-brief-(\d{4}-\d{2}-\d{2})\.html$", args.html_file.name)
        report_date = match.group(1) if match else now.date().isoformat()
    try:
        datetime.strptime(report_date, "%Y-%m-%d")
    except ValueError:
        raise SystemExit("report-date must use YYYY-MM-DD")
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
        "local_date": report_date,
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
