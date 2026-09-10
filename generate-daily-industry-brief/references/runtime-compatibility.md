# Runtime compatibility and retrieval fallbacks

Read this reference before the first retrieval run on a new host, whenever a host has no `webSearch` tool, or when an attached ZIP is being used without a confirmed persistent installation.

## Capability gate

Determine capabilities from the actual tool list and harmless read-only probes. Do not infer them from a product name, model name, cloud branding, or physical location. In particular, the absence of a tool literally named `webSearch` or `webFetch` is not evidence that the host cannot retrieve current webpages. Record every tested route as `working`, `skipped-unavailable`, `denied`, or `failed`; select one working primary transport and do not invoke an unavailable optional route again. Follow `network-retrieval-playbook.md` and record these capabilities in the run notes:

- persistent skill directory available after a new session;
- archive extraction and file read/write;
- shell and, if available, Python 3.6+ execution for the bundled helpers; Python is an enhancement rather than a requirement;
- exposed search API/tool, if present — inspect the host's actual tool list and documented connectors for capability rather than an exact name. Examples may include `webSearch`, `search_web`, `internet_search`, `browser.search`, knowledge/news search, or a configured Bing/Google/SerpAPI-style connector. Select the strongest declared working API with one harmless query; never guess an unexposed endpoint, tool name, API key or credential;
- controllable browser and whether it can navigate a public listing or a search-result page, including a user-authorized personal cloud computer/cloud desktop. A personal cloud desktop that the Agent can actually control is a Mode B transport, not an offline host: use it to search, open results, and inspect original pages without requiring a separately named `webSearch` tool;
- direct URL access through any shell/native client (`curl`, `wget`, PowerShell `Invoke-WebRequest`, Node `fetch`, Python `urllib`, or host equivalent);
- RSS, Atom, sitemap, official listing, public JSON/API, and site-native-search access;
- external structured-feed input;
- native recurring scheduler and readable next-run/recurrence fields;
- downloadable standalone HTML delivery without script removal.

If the skill arrived as a ZIP attachment, reading `SKILL.md` from the temporary attachment directory is not installation. Preserve the complete directory tree, run `scripts/verify_install.py` when Python is available, and install or mount it in a persistent skill directory before claiming recurring use. Without Python, verify the required files manually from `manifest.json` and record `manual-install-check`. If the host cannot persist files, use attachment mode only for the current turn and state that a later automation cannot rely on the attachment.

## Native-search selection gate

Mode A means **any host-native capability that accepts a keyword query and returns candidate webpages/news records**. It is not limited to a tool literally called `webSearch`, and it does not require a separately purchased API key.

Before the first board query, the Agent itself must inspect its exposed tools, connectors and documented browser integrations, then make one harmless, topic-relevant probe in this order:

1. a native keyword-search, news-search, knowledge-search or browser-search tool (regardless of its exact name);
2. a configured MCP or enterprise search connector;
3. `scripts/search_api_bridge.py` when a documented local or centrally managed credential exists;
4. a controllable browser search-results page, which is Mode B rather than Mode A because the Agent is operating a webpage.

Record the exact capability name, route class, probe query, whether candidate URLs were returned, one original page opened for verification, and the failure reason if it did not work. Product branding (for example Codex, WorkBuddy, Claude Code or yz claw), a generic statement that the Internet is available, or the absence of `webSearch` is not capability evidence. A missing option is `skipped-unavailable`; immediately test the next route. Platform-native tools are normally visible only to the Agent, not to a local Python process, so a bundled script cannot discover or invoke a hidden host tool. Search output is discovery only and never replaces original-page verification.

## Retrieval modes

Choose the highest available mode. Never silently jump to model memory or widen the time window. A live outbound connection must use Mode A or Mode B; Mode C is an enhancement or a last resort only when direct live retrieval genuinely cannot be performed. Optional unavailable modes are recorded as skipped, not treated as failures of the report. For every selected row, apply `coverage-continuity.md`: a qualifying 24/48-hour card is preferred; otherwise output a transparent extended-related or baseline-tracking card rather than a blank block.

### Mode A — search API plus fetch

Use the strongest exposed and working host search API/service for breadth-first discovery across every selected section, then use direct URL fetch/browser for candidate verification. A tool called `webSearch` is merely one possible implementation; use the host's own documented search API when it exposes a different name. Follow the adaptive finding and empty-section thresholds in `retrieval-audit.md` and the event-level route ladder in `retrieval-routing.md`; do not spend the run budget exhausting one section before every section receives a baseline pass. When search finds a candidate but raw URL fetch fails, reopen it from the search result reference or a controllable browser before treating the page as blocked.

For large subscriptions, batch independent section-specific queries up to the search tool's supported limit, then open candidates in a second phase. A successful zero-result query is retrieval evidence, not a capability failure. For quiet rows, inspect the compact official-index matrix in `source-map.md` and perform one independent authority/industry discovery pass before declaring the row checked-empty. Retry only rows whose query, index, timestamp, or page access actually failed.

### Mode B — direct-network retrieval

Use whenever any public outbound web route works but a full search tool is absent or insufficient: direct URL fetch, browser navigation, browser-based search-result pages, RSS/Atom, site maps, official listing pages, public JSON/API, or site-native search. This mode is not a weaker "no-news" path: it is a required live discovery path on networked hosts.

#### Personal cloud computer / cloud-browser route

When the host supplies a user-authorized personal cloud computer, cloud browser, remote desktop, or browser-control session, treat it as a first-class Mode B transport. Product names are irrelevant. After confirming that the Agent can navigate it, the Agent must: (1) open a topic-relevant official list or homepage as the harmless probe; (2) use a public search page or a site-native search page for section-specific discovery; (3) open each proposed reader-facing source page, not merely a result snippet; and (4) record the visited direct URL, title, source family, displayed publication/event time, and the cloud-browser transport in the ledger. It must not tell the user to manually search/copy results when the browser session is controllable. If the session is view-only, login-blocked, disconnected, or not exposed to the Agent, record that precise condition and continue to the next available route; never claim that the cloud computer was used when it was not.

1. Use the working transport in `network-retrieval-playbook.md` to open the curated per-section routes in `section-source-catalog.md` and `source-map.md` directly. The agent may use a browser, CLI HTTP, language-native HTTP, RSS reader, or public API; it must not require a prebuilt user feed.
2. For every section, inspect one named primary/official listing or feed and one distinct discovery route (official site-native search, public search-result page, financial/vertical publisher, public API, sitemap, or counterparty route). If one route fails, switch transport or endpoint before treating the source as unavailable.
3. Count only independently maintained source families actually opened. Record the transport route used, not just a generic claim that the Internet was unavailable.
4. If a current item is verified, apply the finding threshold and mark the section `complete`; do not require empty-section breadth merely to retain the finding. When the row is below its two/three-card screening target, continue the bounded additional discovery pass rather than stopping at its first item.
5. For a zero-item section, inspect one relevant current official listing/feed and run one topic-specific direct-source or site-native search. If both paths execute and show no qualifying item, record `checked-empty`, then apply the 48-hour and continuity steps. Use official RSS, sitemaps, print pages, alternate official records, and the bounded fallback pass when a path fails. Absence of a general search engine never by itself justifies asking the user for a feed, declaring a section limited, or leaving it visually blank.

### Mode C — verified external JSON feed

Use when the Agent cannot use any working direct-network route but can read a feed created by an authorized collector or enterprise data service. Do not choose this mode merely because no paid API, preconfigured RSS aggregator, or tool named `webSearch` exists.

1. Require the structure in `news-input-schema.json` and validate it with `scripts/validate_news_input.py` when Python is available.
2. Accept only records with a direct original-source URL, timezone-aware publication or event timestamp, a retrieval timestamp, a primary-source verification status, and a short evidence excerpt.
3. Treat the collector as the verification boundary and disclose `外部已验证数据源` in the audit. Do not claim that the Agent independently opened the page.
4. Apply the same 24-hour primary window, per-section 24-to-48-hour fallback, deduplication, topic routing, item ceiling, and source-tier rules. Validate a feed against the full 48-hour maximum window, then derive each record's primary/fallback class from its timestamp; never use fallback records for a section that already has a qualifying primary record.
5. Apply the same asymmetric thresholds: a feed section with verified qualifying records may meet the finding threshold, while a zero-record section may be called `checked-empty` only when the collector supplies coverage metadata meeting the empty-section threshold. Otherwise mark it `limited`.

### Mode D — offline or cached input

Use only user-supplied documents or previously cached records. Label the artifact `非实时/检索受限`, do not write a success marker, and never present cached material as today's complete brief.

If none of Modes A–C is available, stop before making factual news claims. Produce a continuous-tracking HTML with one `基线追踪` card per selected row, clearly marked non-real-time and linked to an authority entry point; model memory is not a current-information source. Do not write a success marker.

## Standalone HTML delivery

The searchable report depends on the template's inline JavaScript, not on web search or internet access.

- Generate a real `.html` file from `assets/daily-brief-template.html`; do not paste HTML into a chat renderer and call that the artifact.
- Deliver the file as a downloadable attachment or filesystem link. A sanitized chat preview may remove `<script>` and is not proof that the artifact is broken.
- When Python is present, write the matching `retrieval-ledger-YYYY-MM-DD.json`, run `scripts/validate_retrieval_ledger.py`, then run `scripts/validate_html.py` with the ledger-derived counts. A nonzero result from either validator means repair and revalidate; do not mark success. Without Python, apply the same checks manually and label the audit `manual-validation`.
- The validator must find the search input, filter function, highlighting logic, responsive sticky navigation, matching story structure, and safe new-window external links.
