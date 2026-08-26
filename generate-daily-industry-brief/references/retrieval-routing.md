# Multi-route retrieval and evidence ladder

Read this reference for every live retrieval run. Its purpose is to keep one blocked page or one weak host fetch path from emptying a whole section. It does not create a promise that every section will have a distinct daily event.

## Non-negotiable distinction

- A **route failure** means one search, URL, parser or browser path failed.
- An **event failure** means the event still cannot be verified after all applicable routes below have been tried.
- A **quiet section** means the required discovery and current-index checks executed successfully and found no qualifying event.

Never convert a route failure directly into a `limited` section or an exclusion. Never call a section quiet merely because an original detail page could not be parsed.

## Breadth-first discovery

For each selected section, issue at least these two discovery forms before deep verification:

1. a freshness-bounded topic query using the section's exact cues plus one or more concrete AEC actors, scenarios or document types;
2. a source-oriented query naming an official source family, watchlist company, exchange, procurement index, association, research publisher or established industry outlet.

Use the host search service's supported batching. Record results per section even when several queries share one call. For a zero-result row, inspect the most relevant current official index and perform one independent authority/industry discovery pass before declaring it checked-empty.

## Candidate verification ladder

For every plausible in-window event, stop at the first route that establishes the title, actor, core fact, qualifying timestamp and stable evidence URL:

1. **Original result route:** open the search result reference or canonical original page. Prefer the search result reference when raw-URL safety or redirect handling differs.
2. **Controllable browser route:** open the same page in an available graphical or browser-control tool; inspect rendered text or metadata when a simple fetch sees only a script shell.
3. **Official alternate endpoint:** try official listing/detail APIs, RSS, sitemap, print/mobile page, PDF attachment, exchange filing, regulator database, procurement record or archived announcement on the same official domain.
4. **Event-counterparty route:** use an accessible official announcement from the buyer, seller, project owner, contractor, regulator, exchange, partner, conference organizer or other direct participant in the same event.
5. **Authority/industry evidence route:** for an ordinary non-controversial event, one established national, financial, construction-industry, vertical-industry, association or research source may verify it when the page is accessible, states the event and time, and clearly attributes the underlying actor or record. It may be the final reader-facing citation when the original is inaccessible or the source adds material reporting, but must be labeled `T2权威转述`. For financial results, major investment, policy meaning, safety incidents, legal disputes or other material/sensitive claims, require an official record or two independent credible sources.
6. **Attributed discovery-mirror route:** an established disclosure mirror or major portal reprint may verify an ordinary event only when it reproduces a named filing, government document, company announcement or identifiable original publisher, supplies a qualifying date, and the page is stable and accessible. Label it `T2公告镜像` or `T2转载`; never label it Tier 1. Search-result URLs, anonymous rewrites and pages without an identifiable underlying record remain discovery-only.

A search snippet alone is discovery evidence, not final evidence. An inaccessible original URL may still be shown as an additional provenance link, but the reader-facing source link must include at least one accessible verification page.

## When to mark limited

Mark a zero-item section `limited` only when at least one required discovery or verification capability could not be executed and the applicable route ladder did not produce an accessible substitute. The limitation reason must name the failed capability category, such as `search unavailable`, `rendered page inaccessible`, or `timestamp unverifiable`; do not use a generic `network restricted` phrase when another route succeeded.

If discovery queries and required current indexes executed successfully and no event qualified, mark `checked-empty`, even if individual irrelevant candidates were blocked. If one or more events qualify, mark `complete`; a failed extra page does not downgrade the row.

## Cross-section evidence without duplicate stories

One event can carry real business value for several selected sections. Assign one primary section and render the full story once. For every other genuinely relevant section, render a compact `关联资讯` card containing:

- the event title and anchor to the primary story;
- the distinct relevance bridge for this section;
- the accessible evidence source and timestamp.

Record these as `related_count`, not `included item count`. A standard section with a verified related card and completed discovery coverage may be `complete`, but the card must not be used to conceal a failed search or manufacture relevance. A custom-interest section can never be completed by a related card alone: if a directly relevant event exists, route at least one such event to the custom row as its formal main story; otherwise show a checked-empty or limited state after completing the required independent lanes.

## Host-neutral execution rule

Use capability names rather than product names. Search, fetch, browser control and structured feeds may be supplied by different services on different Agents. Probe them once, choose the strongest combination, and keep the same evidence standard across hosts. A host with a strong Chinese search index may discover more leads; a host with a stronger browser may verify more pages. The route ladder is designed to combine whichever capabilities are actually present.
