# Network retrieval playbook

Read this reference at the start of every live generation on a new host, and whenever a host lacks a dedicated `webSearch` or `webFetch` tool. Its purpose is to prevent a networked Agent from incorrectly treating an absent tool name, paid API, or prebuilt RSS aggregator as an inability to retrieve current information.

## Non-negotiable rule

If the host can reach public web content by **any** read-only route, it must perform Mode A or Mode B live retrieval. It must not request a user-created JSON feed as its first response, and it must not write `检索受限` solely because `webSearch` or `webFetch` is absent.

The only valid reasons to use Mode C or Mode D are: every available direct-network route was unavailable or denied, or a structured feed is the only current source the host is allowed to read. A feed is an optional coverage enhancer, not a prerequisite for ordinary public-web discovery.

## Capability probe

Do a small, read-only probe before retrieving. Do not rely on product branding or claim that a route works without using it. Try the available routes in this order, stopping after one route has actually returned a public page, feed, listing, or JSON response. Record unavailable tools as `skipped-unavailable` rather than calling them or presenting them as retrieval errors:

1. **Search API/tool** — inspect the host's declared tool list and configured connectors for a search-result API. It may be named `webSearch`, `search_web`, `internet_search`, `browser.search`, knowledge/news search, or a configured Bing/Google/SerpAPI-style connector. Run one small topic-relevant query through the strongest exposed candidate and use it for broad discovery when it returns usable result URLs. Do not guess endpoint URLs, API keys, tool names or credentials that the host has not exposed.
2. **Controllable browser / personal cloud computer** — when a user-authorized browser, cloud browser, cloud desktop, remote desktop, or computer-use session is exposed to the Agent, open one relevant official homepage or listing, then, if allowed, a public search-engine result page or an official site-native search page. This is a working Mode B route even if no tool is named `webSearch`; execute the queries and open original pages directly in the controllable session rather than asking the user to relay results.
3. **HTTP client** — use the host's available non-mutating client: `curl`, `wget`, PowerShell `Invoke-WebRequest`, Node `fetch`, Python `urllib`, or an equivalent built-in request tool.
4. **Feed/listing route** — directly read an RSS/Atom feed, XML sitemap, official announcements list, public-procurement index, exchange disclosure index, newsroom archive, or public JSON endpoint.
5. **Authorized connector/feed** — read a current enterprise data connector or a validated JSON feed only when it is actually available.

Use a relevant, publicly accessible target from `section-source-catalog.md` rather than a generic connectivity test. If Python 3.6+ exists, `scripts/probe_network.py --url <one-or-more-relevant-public-urls>` may record HTTP reachability; it is optional and does not replace browser or host-native routes.

Record the result in the ledger's `run.network_probe` object:

```json
{
  "internet_reachable": true,
  "working_routes": ["search-api: host-news-search", "browser", "official-listing"],
  "failed_routes": ["http-client: denied"],
  "mode_selection_reason": "The host's declared news-search API returned result URLs; browser verification and official listings are reachable."
}
```

`internet_reachable: false` requires concrete failed-route evidence. The phrase “没有现成 API/RSS 聚合器” is not an acceptable failure reason. A mode is selectable only when its route is `working`; `skipped-unavailable` and `denied` are not retried until host capabilities change.

### Host-native search rule

For Mode A selection, ask the Agent to inspect its own exposed tool schemas and connectors for any function that takes a keyword query and returns candidate webpages, news or knowledge records. It may have an unfamiliar name; do not require `webSearch`. Prefer a working native search tool, then a working MCP/enterprise connector, then the bundled API bridge when its documented credential is already present. A browser search page is a valid fallback, but classify it as Mode B. The probe record must state the exact tool/connector name and an original source URL opened after discovery. Do not claim a native search route based on the product name, a UI screenshot, an agent assertion that it can browse, or a Python process's inability to list host tools.

## Direct-network discovery matrix

For every selected board, use the exact source families in `section-source-catalog.md`. A usable transport must run this bounded matrix before a board may be finalized below its screening target, checked-empty, or limited:

| Pass | Required action | Examples of usable transport |
|---|---|---|
| 1. Official index | Open the newest official/regulatory/company/procurement/exchange list or feed for that board. | Browser, HTTP client, RSS, sitemap, public JSON. |
| 2. Independent discovery | Open a different source family: site-native search, public search page, authority/financial/vertical publisher, disclosure mirror, counterparty, or project owner. | Browser search page, HTTP client, public listing/API. |
| 3. Candidate verification | Open the candidate page or an alternate evidence route and confirm title, date/time, actor, core fact and direct URL. | Browser, HTTP client, official alternate, counterparty. |
| 4. Thin-row expansion | If fewer than the section target (normally 2; high-output/9–10 relevance normally 3), repeat Pass 2 using an unused family. | Any working transport. |

For a board with no strict 24-hour item, do not stop at Pass 2: perform the permitted 24–48-hour fallback and the continuity ladder. Where a genuine C-level related event or a current official statistic/project/industry observation exists, output it visibly as `扩展相关资讯` or `业务观察`, rather than a blank section. These are not falsely counted as complete realtime coverage.

## Choosing sources without a general search engine

Use source-family **entry points**, not a fictional universal API:

- policy, standards and data: official central/local government publication lists, regulator databases, statistical releases, standard publication indexes;
- procurement, projects and labour: government-procurement/public-resource indexes, owner/contractor procurement pages, public-employment releases;
- enterprise and capital: exchange/CNInfo/HKEX filings, investor-relations newsrooms, bond/rating disclosures, named financial-media and disclosure-mirror discovery pages;
- AI, software and construction technology: vendor newsrooms, customer/project-owner releases, research institute/association releases, specialist technology publishers;
- broad custom interests: derive field, actor, regulator/registry, transaction/project and industry-intersection terms, then use the same official index + independent discovery pattern.

Do not require a construction keyword for broad selected fields (`数科`, `AI`, `政府宏观`, `行业数据`, `投融资`, `海外`, `绿色低碳`, `拓展阅读`, or broad custom interests). Construction relevance ranks otherwise equal evidence; it does not erase current, field-valid news.

## Personal cloud computer evidence rule

For a controllable personal cloud computer route, a search-engine result page is discovery evidence only. Before an item can enter the HTML, open its original source page in the cloud browser (or a direct official alternate), collect the reader-facing URL and timestamp, and put `browser-cloud` or the host's documented cloud-browser capability name in `transport_routes`. A cloud computer that is merely visible to the user but cannot be controlled by the Agent is not a working route.

## Status discipline

- **complete**: at least one verified 24-hour item, or a permitted 48-hour supplement after the primary window was checked empty.
- **expanded / business-observation**: use a real current C-level event, official statistic, project/procurement record, association release, research, or established vertical/financial report when strict news is absent. This is the normal way to avoid a visual blank.
- **checked-empty**: only after the direct-network matrix has executed successfully and the 24/48-hour plus continuity passes contain no eligible current material.
- **limited / baseline**: only when the required route could not actually be completed because public access failed, network policy denied it, the host was interrupted, or all live transports were unavailable. State the failed transport and target type; do not state merely “无 WebSearch”.

No online workflow can guarantee that every field has a brand-new, independently verifiable event within 48 hours. It can, however, guarantee an honest, nonblank card through the continuity ladder whenever a real current related item or observation is available. Never fabricate an event to meet a card target.

## Tavily guided fallback

Tavily is a **last-resort discovery route**, not a reason to skip host-native search, a controllable browser, direct HTTP, official lists, RSS, public APIs or an authorized feed. Offer it only after the A/B/C preflight records no usable live route and `TAVILY_API_KEY` is absent.

The interaction must say why registration is being offered: this host cannot currently conduct public-web discovery and therefore cannot independently verify the day's sources. It must also explain the exact steps without exposing a secret: open `https://app.tavily.com/`; register or log in; create a Key from **API Keys**; paste it only in the host's masked/local secret field. On graphical local Python hosts, `scripts/setup_tavily.py` performs this flow, verifies a harmless query before saving, and on Windows persists only the current user's `TAVILY_API_KEY` environment setting. On other hosts the Agent must use the host's documented secret store or keep the activation session-only; it may never request the Key in ordinary chat.

A search result from Tavily is a discovery lead only. The normal original-page time, actor, fact and direct-URL verification remains compulsory.
