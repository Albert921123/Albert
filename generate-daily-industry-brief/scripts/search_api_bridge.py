#!/usr/bin/env python3
"""Search API bridge for the daily brief skill.

The bridge reads only documented environment variables, never command-line keys,
and normalizes discovery results from supported public search APIs. Results remain
discovery leads: callers must open and verify each original record page separately.

Supported providers, selected automatically in this order:
  - Tencent Cloud Web Search API (Sogou-powered): TENCENTCLOUD_WSA_APIKEY
  - Tavily:  TAVILY_API_KEY
  - Brave:   BRAVE_SEARCH_API_KEY
  - SerpAPI: SERPAPI_API_KEY
  - Bing:    BING_SEARCH_V7_SUBSCRIPTION_KEY (+ optional BING_SEARCH_ENDPOINT)
  - SearXNG: SEARXNG_URL (a user-configured public/private instance URL)
"""

from __future__ import print_function

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

try:
    from py36_compat import configure_utf8_stdio
except ImportError:
    configure_utf8_stdio = None


PROVIDER_ENV = {
    "tencent-wsa": ("TENCENTCLOUD_WSA_APIKEY",),
    "tavily": ("TAVILY_API_KEY",),
    "brave": ("BRAVE_SEARCH_API_KEY",),
    "serpapi": ("SERPAPI_API_KEY",),
    "bing": ("BING_SEARCH_V7_SUBSCRIPTION_KEY",),
    "searxng": ("SEARXNG_URL",),
}
AUTO_ORDER = ("tencent-wsa", "tavily", "brave", "serpapi", "bing", "searxng")


def stored_tavily_key():
    """Return the current user's locally saved Tavily key on Windows, if any.

    The setup helper writes this to the user's Environment registry key instead
    of the shared skill directory.  Reading it here lets a newly started Python
    process use the key even before a terminal is restarted.  On other systems,
    callers should use the host's secret store or TAVILY_API_KEY environment
    variable.
    """
    value = os.environ.get("TAVILY_API_KEY", "").strip()
    if value or os.name != "nt":
        return value
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
        try:
            value, _kind = winreg.QueryValueEx(key, "TAVILY_API_KEY")
        finally:
            winreg.CloseKey(key)
        return str(value or "").strip()
    except Exception:
        return ""


def provider_credential(name):
    if name == "tavily":
        return stored_tavily_key()
    names = PROVIDER_ENV[name]
    return os.environ.get(names[0], "").strip()


def request_json(url, method="GET", headers=None, payload=None, timeout=20):
    body = None
    merged_headers = {"Accept": "application/json", "User-Agent": "zhixun-search-bridge/1.0"}
    if headers:
        merged_headers.update(headers)
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        merged_headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=merged_headers, method=method)
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def first_text(record, names):
    for name in names:
        value = record.get(name)
        if value:
            return str(value).strip()
    return ""


def normalized_item(title, url, snippet="", published_at="", source_name=""):
    parsed = urlparse(url)
    return {
        "title": str(title or "").strip(),
        "url": str(url or "").strip(),
        "snippet": str(snippet or "").strip(),
        "published_at": str(published_at or "").strip(),
        "source_name": str(source_name or parsed.netloc).strip(),
    }


def search_tavily(query, limit, days):
    payload = {"api_key": provider_credential("tavily"), "query": query, "max_results": limit,
               "search_depth": "basic", "include_answer": False, "include_raw_content": False}
    if days:
        payload["days"] = days
    data = request_json("https://api.tavily.com/search", method="POST", payload=payload)
    return [normalized_item(item.get("title"), item.get("url"), item.get("content"),
                            item.get("published_date"), item.get("source"))
            for item in data.get("results", [])]


def search_tencent_wsa(query, limit, days):
    """Call Tencent Cloud Web Search API's simple service-API-key endpoint.

    Tencent returns each page as a JSON string in Response.Pages. The bridge does
    not request paid-plan-only options such as Cnt, Industry or Freshness, so a
    configured account controls its own plan capabilities in the cloud console.
    """
    payload = {"Query": query, "Mode": 0}
    data = request_json(
        "https://api.wsa.cloud.tencent.com/SearchPro",
        method="POST",
        headers={"Authorization": "Bearer " + os.environ["TENCENTCLOUD_WSA_APIKEY"]},
        payload=payload,
    )
    pages = data.get("Response", {}).get("Pages", [])
    results = []
    for page in pages[:limit]:
        try:
            item = json.loads(page) if isinstance(page, str) else page
        except (TypeError, ValueError):
            continue
        results.append(normalized_item(
            item.get("title"), item.get("url"), item.get("content") or item.get("passage"),
            item.get("date"), item.get("site"),
        ))
    return results


def search_brave(query, limit, days):
    params = {"q": query, "count": limit, "search_lang": "zh-hans"}
    data = request_json("https://api.search.brave.com/res/v1/web/search?" + urlencode(params),
                        headers={"X-Subscription-Token": os.environ["BRAVE_SEARCH_API_KEY"]})
    return [normalized_item(item.get("title"), item.get("url"), item.get("description"),
                            item.get("age"), item.get("profile", {}).get("long_name", ""))
            for item in data.get("web", {}).get("results", [])]


def search_serpapi(query, limit, days):
    params = {"engine": "google", "q": query, "num": limit, "api_key": os.environ["SERPAPI_API_KEY"], "hl": "zh-CN"}
    data = request_json("https://serpapi.com/search.json?" + urlencode(params))
    results = []
    for item in data.get("organic_results", []):
        date = item.get("date") or item.get("snippet_highlighted_words", [""])[0]
        results.append(normalized_item(item.get("title"), item.get("link"), item.get("snippet"), date, item.get("displayed_link")))
    return results


def search_bing(query, limit, days):
    endpoint = os.environ.get("BING_SEARCH_ENDPOINT", "https://api.bing.microsoft.com/v7.0/search").rstrip("/")
    params = {"q": query, "count": limit, "mkt": "zh-CN", "textDecorations": "false", "textFormat": "Raw"}
    data = request_json(endpoint + "?" + urlencode(params),
                        headers={"Ocp-Apim-Subscription-Key": os.environ["BING_SEARCH_V7_SUBSCRIPTION_KEY"]})
    return [normalized_item(item.get("name"), item.get("url"), item.get("snippet"),
                            item.get("dateLastCrawled"), item.get("displayUrl"))
            for item in data.get("webPages", {}).get("value", [])]


def search_searxng(query, limit, days):
    base = os.environ["SEARXNG_URL"].rstrip("/")
    if not base.endswith("/search"):
        base += "/search"
    params = {"q": query, "format": "json", "language": "zh-CN", "safesearch": 0}
    data = request_json(base + "?" + urlencode(params))
    return [normalized_item(item.get("title"), item.get("url"), item.get("content"),
                            item.get("publishedDate"), item.get("engine"))
            for item in data.get("results", [])[:limit]]


SEARCHERS = {"tencent-wsa": search_tencent_wsa, "tavily": search_tavily, "brave": search_brave, "serpapi": search_serpapi,
             "bing": search_bing, "searxng": search_searxng}


def configured_providers():
    return [name for name in AUTO_ORDER if provider_credential(name)]


def emit(payload, code):
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return code


def main(argv=None):
    parser = argparse.ArgumentParser(description="Normalize configured search API results for discovery.")
    parser.add_argument("--query", required=True, help="Discovery query; never include API credentials.")
    parser.add_argument("--provider", choices=("auto",) + AUTO_ORDER, default="auto")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--days", type=int, default=0, help="Optional recency hint supported by some providers.")
    parser.add_argument("--output", help="Optional UTF-8 JSON output file.")
    args = parser.parse_args(argv)
    if not args.query.strip():
        return emit({"ok": False, "status": "invalid_query", "message": "query must not be empty"}, 2)
    if args.limit < 1 or args.limit > 20:
        return emit({"ok": False, "status": "invalid_limit", "message": "limit must be 1..20"}, 2)

    available = configured_providers()
    provider = available[0] if args.provider == "auto" and available else args.provider
    if provider == "auto" or provider not in available:
        return emit({"ok": False, "status": "no_configured_provider", "query": args.query,
                     "supported_environment_variables": PROVIDER_ENV,
                     "message": "No supported search API credential is configured. Continue with a browser, direct HTTP, RSS/listings or another exposed host route."}, 3)
    try:
        items = SEARCHERS[provider](args.query, args.limit, args.days)
    except (HTTPError, URLError, ValueError, KeyError, json.JSONDecodeError) as exc:
        return emit({"ok": False, "status": "provider_failed", "provider": provider,
                     "query": args.query, "message": str(exc)}, 4)
    results = [item for item in items if item["title"] and item["url"]]
    payload = {"ok": True, "status": "working", "provider": provider, "query": args.query,
               "result_count": len(results), "results": results,
               "next_step": "Discovery only. Open each original record URL and verify its time, actor and core fact before use."}
    if args.output:
        with open(args.output, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2)
    return emit(payload, 0)


if __name__ == "__main__":
    if configure_utf8_stdio:
        configure_utf8_stdio()
    sys.exit(main())
