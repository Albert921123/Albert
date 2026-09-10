#!/usr/bin/env python3
"""Read-only HTTP reachability probe for Python 3.6+ Agent hosts.

This helper is optional. It helps a host distinguish a missing WebSearch tool
from a genuinely unavailable outbound network without adding dependencies.
"""

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

from py36_compat import configure_utf8_stdio


def probe(url, timeout):
    request = Request(url, headers={"User-Agent": "zhixun-daily-brief/1.17"})
    try:
        response = build_opener().open(request, timeout=timeout)
        try:
            return {
                "url": url,
                "reachable": True,
                "status": getattr(response, "status", response.getcode()),
                "content_type": response.headers.get("Content-Type", ""),
            }
        finally:
            response.close()
    except HTTPError as exc:
        # A server response still proves outbound reachability; callers may
        # choose an alternate endpoint for retrieval.
        return {"url": url, "reachable": True, "status": exc.code, "http_error": str(exc)}
    except (URLError, ValueError, OSError) as exc:
        return {"url": url, "reachable": False, "error": str(exc)}


def main():
    configure_utf8_stdio()
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", action="append", required=True, help="Public HTTP(S) URL; repeatable")
    parser.add_argument("--timeout", type=float, default=8.0)
    args = parser.parse_args()
    if args.timeout <= 0:
        parser.error("--timeout must be positive")

    results = [probe(url, args.timeout) for url in args.url]
    payload = {
        "ok": any(item.get("reachable") for item in results),
        "transport": "python-urllib",
        "results": results,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    sys.exit(main())
