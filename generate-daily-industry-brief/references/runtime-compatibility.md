# Runtime compatibility and retrieval fallbacks

Read this reference before the first retrieval run on a new host, whenever a host has no `webSearch` tool, or when an attached ZIP is being used without a confirmed persistent installation.

## Capability gate

Determine capabilities from the actual tool list and one harmless read-only probe. Do not infer them from a product name, model name, cloud branding, or physical location. Record these capabilities in the run notes:

- persistent skill directory available after a new session;
- archive extraction and file read/write;
- shell and Python 3.6+ execution for the bundled helpers; `Asia/Shanghai` works from the standard library without an external timezone package;
- web search;
- direct URL fetch or controllable browser;
- external structured-feed input;
- native recurring scheduler and readable next-run/recurrence fields;
- downloadable standalone HTML delivery without script removal.

If the skill arrived as a ZIP attachment, reading `SKILL.md` from the temporary attachment directory is not installation. Preserve the complete directory tree, run `scripts/verify_install.py`, and install or mount it in a persistent skill directory before claiming recurring use. If the host cannot persist files, use attachment mode only for the current turn and state that a later automation cannot rely on the attachment.

## Retrieval modes

Choose the highest available mode. Never silently jump to model memory or widen the time window.

### Mode A — search plus fetch

Use the host's search service for breadth-first discovery across every selected section, then use direct URL fetch/browser for candidate verification. Follow the adaptive finding and empty-section thresholds in `retrieval-audit.md` and the event-level route ladder in `retrieval-routing.md`; do not spend the run budget exhausting one section before every section receives a baseline pass. When search finds a candidate but raw URL fetch fails, reopen it from the search result reference or a controllable browser before treating the page as blocked.

For large subscriptions, batch independent section-specific queries up to the search tool's supported limit, then open candidates in a second phase. A successful zero-result query is retrieval evidence, not a capability failure. For quiet rows, inspect the compact official-index matrix in `source-map.md` and perform one independent authority/industry discovery pass before declaring the row checked-empty. Retry only rows whose query, index, timestamp, or page access actually failed.

### Mode B — direct-source navigation

Use when search is absent but direct URL fetch, a browser, RSS, site maps, official listing pages, or site-native search is available.

1. Open the curated Tier 1 source families in `source-map.md` directly.
2. Inspect their newest listing/feed entries and use official site-native search where available.
3. Count only independently maintained source families actually opened.
4. If a current item is verified, apply the finding threshold and mark the section `complete`; do not require empty-section breadth merely to retain the finding.
5. For a zero-item section, inspect one relevant current official listing/feed and run one topic-specific site-native or direct-source search. If both paths execute and show no qualifying item, record `checked-empty`. Use official RSS, sitemaps, print pages, alternate official records, and the bounded fallback pass only when one of those paths fails. Absence of a general search engine does not by itself justify calling the section empty or limited.

### Mode C — verified external JSON feed

Use when the Agent cannot search or browse but can read a feed created by an authorized collector or enterprise data service.

1. Require the structure in `news-input-schema.json` and validate it with `scripts/validate_news_input.py` when Python is available.
2. Accept only records with a direct original-source URL, timezone-aware publication or event timestamp, a retrieval timestamp, a primary-source verification status, and a short evidence excerpt.
3. Treat the collector as the verification boundary and disclose `外部已验证数据源` in the audit. Do not claim that the Agent independently opened the page.
4. Apply the same 24-hour primary window, per-section 24-to-48-hour fallback, deduplication, topic routing, item ceiling, and source-tier rules. Validate a feed against the full 48-hour maximum window, then derive each record's primary/fallback class from its timestamp; never use fallback records for a section that already has a qualifying primary record.
5. Apply the same asymmetric thresholds: a feed section with verified qualifying records may meet the finding threshold, while a zero-record section may be called `checked-empty` only when the collector supplies coverage metadata meeting the empty-section threshold. Otherwise mark it `limited`.

### Mode D — offline or cached input

Use only user-supplied documents or previously cached records. Label the artifact `非实时/检索受限`, do not write a success marker, and never present cached material as today's complete brief.

If none of Modes A–C is available, stop before making factual news claims. A valid partial HTML may explain the capability limitation, but model memory is not a current-information source.

## Standalone HTML delivery

The searchable report depends on the template's inline JavaScript, not on web search or internet access.

- Generate a real `.html` file from `assets/daily-brief-template.html`; do not paste HTML into a chat renderer and call that the artifact.
- Deliver the file as a downloadable attachment or filesystem link. A sanitized chat preview may remove `<script>` and is not proof that the artifact is broken.
- Run `scripts/validate_html.py` on the final file. A nonzero result means repair and revalidate; do not mark success.
- The validator must find the search input, filter function, highlighting logic, responsive sticky navigation, matching story structure, and safe new-window external links.
