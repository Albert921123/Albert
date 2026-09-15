# Retrieval coverage and audit

Read this reference whenever generating or catching up a brief. It prevents an unsearched section from being mislabeled as a quiet section. The primary window remains the rolling 24 hours; a section confirmed empty in that window may use the separate 24-to-48-hour fallback segment. This creates no minimum article quota.

## Coverage ledger

Create one ledger row before searching for every selected standard topic and every custom interest. Keep it in working memory or a temporary structured record until the HTML is complete.

Each row contains:

- exact section ID and displayed label;
- distinct source families checked;
- section-specific targeted query count;
- candidate pages opened;
- independent primary-card count and unique-event count; cross-section and compact-related counts must be zero;
- primary-window and fallback-window included counts;
- excluded counts for `outside-window`, `date-only-ambiguous`, `duplicate`, `not-industry-relevant`, `not-primary-enough`, `inaccessible`, and `other`;
- final status: `complete`, `observed`, `expanded`, `business-observation`, `checked-empty`, `limited`, or `baseline`;
- a short reason whenever status is not `complete`. A `baseline` row means the continuity ladder was exhausted and a clearly non-news tracking card was rendered instead of visual blank space.
- verification route used for each included event: original, browser-rendered original, official alternate, event counterparty, or authority/industry fallback.
- one candidate-ledger record for every opened plausible candidate, including title, URL, time basis, query lane, relevance level (`A`, `B`, `C`, or `D`), decision, exact exclusion reason, and evidence route.
- `retrieval_proof` as defined in `anti-shortcut-execution.md`, including `screened_candidate_count`, `candidate_pool_closure` (`required-lanes-exhausted` or `max-items-reached`), `source_families_checked`, `actor_classes_checked`, `event_families_checked`, per-query evidence, and a specific `closure_reason`. It is mandatory for new live, direct-fetch, and feed-backed runs. The aggregate class arrays must exactly reconcile to the union of the per-query evidence.
- `run_discovery`: `live`, `feed`, or `offline`; an HTML/ledger from an earlier run is never a valid discovery source. If it is consulted as a lead, record the fresh page that re-verified the retained event.

For Mode A/B1/B2 runs, the top-level `run` object also contains `network_probe` from `network-retrieval-playbook.md`: `internet_reachable`, `working_routes`, `failed_routes`, and a concrete `mode_selection_reason`. A B1 run additionally contains `cloud_browser_probe` with the exact capability name and its result. Every section's `retrieval_proof` then contains `transport_routes` and `direct_source_passes`. `direct_source_passes` must identify an **official-index** pass and an **independent-discovery** pass. A missing tool named `webSearch` is not a failed source pass when another public network route works.

A source family is an independently maintained primary-source channel, such as a ministry or local-government publication stream, a public-procurement platform, an exchange filing system, a company newsroom or investor-relations site, a standards publisher, or an original research publisher. Multiple search queries against the same website count as one source family.

## Adaptive search coverage

Use the topic cues in `topics.md`, the source pool in `source-map.md`, and the exact lanes in `section-source-catalog.md`. Coverage is asymmetric: proving a verified finding and asserting that a section is quiet are different tasks. These thresholds measure search effort, not desired article count.

### Section-first relevance

- Search the selected field itself before searching its intersection with construction. A qualifying field event does not need an artificial AEC reference when the section is broad by definition or was entered as a custom interest.
- `industry_scope` is a ranking context. It may raise an AEC-related candidate above another candidate of equal authority and freshness, but it must not silently remove valid `数科`, `政府宏观`, `AI`, `投融资`, `行业数据`, `拓展阅读` or custom-interest news.
- Keep construction-specific admission rules for inherently AEC sections such as `sourcing`, `employment`, `informatization` and `construction-tech`.
- Use 2–3 non-duplicate, decision-useful main stories per active high-output field as a discovery/ranking depth target, not a quota or output cap. For a live run, the candidate ledger must nonetheless contain at least four real candidate records across two source families for an ordinary row, and at least six across three source families for a high-output, 7–10 relevance, or broad custom-interest row. First screen every current candidate exposed by the required discovery lanes; then open and verify every non-duplicate candidate that passes the title/time/source/relevance screen. Include all independently qualifying candidates up to the configured per-section maximum. When fewer than two qualify after the baseline passes, execute the additional discovery pass below before finalizing the row.
- Apply the A/B/C/D admission policy in `topics.md` from the perspective of each selected row. A and B candidates qualify as full cards. C qualifies only when no A/B item exists and is capped at one card. D is excluded. When a later candidate also qualifies, include it up to the configured ceiling; do not stop merely because one valid card has already been found.
- For broad sections and custom interests, never add construction, engineering, infrastructure or `industry_scope` to every query. At least the field lane, actor lane and official-record lane must execute without an AEC term. The business-intersection lane runs afterwards.
- Treat `数科`, `AI`, `政府宏观`, `行业数据`, `海外`, `企业经营`, `投融资`, `绿色低碳` and broad custom interests as high-output fields. If they finish with fewer than two full section cards, run the additional discovery pass even when compact related evidence exists.
- For every high-output or 7–10 relevance row, record at least one Layer 2/3/4 discovery family from `discovery-source-ladder.md` in addition to a primary/statutory family, and at least three independent source families in total. The record may be an excluded candidate or a final citation, but it must be genuinely inspected; an agent may not report a broad search after checking only ministry, government or company homepages.
- On a live-search host, do not finalize an active selected row after a single result merely because it is an official page. First execute one national/statutory or major-financial discovery lane and one independent official, vertical, exchange/disclosure or procurement lane. The only exception is a demonstrably quiet 24-hour field after its required empty-section checks; record that evidence explicitly.
- On any networked Mode B1 or B2 host, the same rule applies through direct navigation: one official index/feed/listing plus one independent site-native-search, public-search-page, financial/vertical, counterparty, mirror, sitemap or public-API route. It is not permissible to skip this because an RSS aggregator or named web-search tool is absent.

## Candidate ledger artifact

Write `retrieval-ledger-YYYY-MM-DD.json` next to the final HTML before rendering. Use a top-level object with `run`, `sections`, and `candidates` arrays.

Each `sections` row must include `section_id`, `label`, `source_family_count`, `query_count`, `candidate_count`, `primary_card_count`, `cross_section_card_count`, `related_count`, `unique_event_count`, `status`, and `reason`. Its source-family count must equal the distinct independently maintained `source_family_id` values recorded for that row; a publisher name and the same publisher's domain are one family.

Each `candidates` row must include:

- `section_id`, `section_label`, `title`, `url`, `direct_record_url`, `direct_record_kind`, `canonical_url`, `source_family_id`, `source_class`, `actor_class`, `event_family`, `event_fingerprint`, `source_name`, and `source_tier`;
- `published_at` or `event_at`, plus `time_basis`, `time_basis_type`, `timestamp_precision`, and `window_class`; an `included-baseline` row may instead use `retrieved_at` and `baseline_kind`;
- `query_lane`: `field`, `actor`, `official`, `business-intersection`, or `expansion`;
- `relevance_level`: `A`, `B`, `C`, or `D`;
- `decision`: `included-primary`, `included-cross-section`, `included-related`, `included-date-observation`, `included-expanded`, `included-business-observation`, `included-baseline`, or `excluded`; cross-section and related inclusion are prohibited in final delivery;
- `reason`: required for every exclusion and recommended for every inclusion;
- `evidence_route` and a stable `event_id` when the event is included in any form.

Run `python scripts/validate_retrieval_ledger.py <ledger> --expected-sections <selected-count> --plan <run-plan>` and `python scripts/validate_source_registry.py <ledger> --registry references/source-registry.json` before authorization when Python is available. Each query-evidence row must name the source families, actor classes and event families actually inspected and must carry `raw_results`, `raw_results_sha256` and `transport_evidence`. The referenced receipt must be readable and hash-identical; its result count must equal the persisted candidate IDs. An under-target section must have exactly one expansion evidence row covering at least two source families and adding at least one changed family. A missing row, unexplained exclusion, malformed URL, unsupported source claim, missing raw receipt, missing network probe/direct-source proof, missing universal search-matrix proof, or included event without an `event_id` blocks the success marker. `validate_html.py` repeats the strict ledger validation for every normal dated report; it cannot be bypassed with an included-cards-only ledger. In the reader-facing HTML, show the top excluded candidates for every checked-empty row with title, date and concise reason. Do not expose raw query strings.

### What counts as completed coverage

Treat coverage as evidence that a retrieval path was executed, not as a requirement to discover a minimum number of articles.

- Successfully opening a relevant official latest-news/listing page and inspecting its newest dated entries counts as one checked source family, even when its newest entry is older than the window.
- A topic-specific official-domain search that executes successfully and yields no qualifying current result counts as a completed discovery pass. Record zero candidates; do not convert a genuine zero-result response into a tool failure.
- An official RSS feed, sitemap, exchange announcement index, procurement index, regulator database, or site-native search counts as the corresponding source family when its current entries were actually inspected.
- Search result pages never become final citations, but their inspected zero-result or out-of-window result set may prove that the discovery pass ran.
- A blocked original detail page is only a failed route. Follow `retrieval-routing.md`; if an official alternate, direct counterparty, registry record, or qualifying authority/industry source verifies the event, the candidate remains eligible.
- `limited` is reserved for an unexecuted or unverifiable required path: tool denial, network failure, blocked listings with no alternate endpoint, interrupted execution, or timestamps that cannot be established. Sparse news, zero search results, and an official listing whose newest item is outside the window are not by themselves limitations.

This distinction is mandatory. If the required checks executed successfully and returned no qualifying items, use `checked-empty`; do not keep the entire subscription retrying because a quiet section had nothing to publish.

### Finding threshold

A section with one or more qualifying full section cards is `complete` when:

- at least one section-specific discovery pass was executed;
- every independent card has a qualifying timestamp, a direct evidence URL, a visible A/B/C relevance label when applicable, an explicit section/industry bridge, and the required primary-source or corroborated Tier 2 verification;
- at least one independently maintained relevant source family supplied or verified the included evidence.

A section cannot be completed by another row's event. When one event has implications for several rows, assign it once to its strongest direct match and continue discovery independently for the other rows.

### Additional discovery pass for under-target rows

Run this bounded pass for a high-output section with zero or one qualifying full section card after its normal field and source/actor lanes:

1. Search one established national/statutory or major-financial family and one independent vertical-industry, procurement, exchange/disclosure or mirror family from `discovery-source-ladder.md`. For government, standards, green and urban-renewal rows, the two lanes must include one central/ministerial channel and one provincial, municipal or project-execution channel; for enterprise/capital rows, include one statutory filing/exchange/company channel and one financial-media/disclosure-mirror channel. For technology, energy and data fields, include a named specialist publisher or association channel alongside the official/company route.
2. Open up to five new plausible candidate pages when available; do not count search snippets as opened candidates.
3. Route each candidate toward an original filing, government page, company announcement or event counterparty. If the original is unavailable, retain an accessible established Tier 2 account for an ordinary event when it names the underlying actor/record and date; label it `T2权威转述`. Do not reject a field-valid candidate merely because it lacks an AEC bridge.
4. Do not stop when three main stories qualify. Finish screening the candidates already exposed by both additional discovery forms and open every one that passes initial screening. End only when both additional discovery forms and their candidate pool are exhausted, or when the configured per-section maximum has been reached. A genuine result of zero or one remains valid and must not be padded with stale or weak material.

Apply this pass by default to `fintech`, `overseas`, `leadership`, `enterprise`, `capital`, `digital`, `government`, `industry-data`, `standards`, `green`, `extended`, and broad recurring custom fields such as `专项债`, `光伏`, `房地产`, `城市更新`, `储能`, `AI方向`, and `半导体`. Use it for other sections when the day is evidently active.

Do not keep a section `limited` merely because it did not reach the broader empty-section threshold after valid current items were found. Source breadth is required to claim quietness, not to invalidate a verified finding.

### Empty-section threshold

Use these thresholds only when no item qualifies:

- For high-output standard sections — `sourcing`, `government`, `enterprise`, `capital`, `industry-data`, `standards`, and `green` — check two distinct relevant Tier 1 source families and one independent authority/industry discovery pass. One Tier 1 check may be a successfully inspected official index, feed, or database reached through a topic-specific official-domain query.
- For every other selected standard section, check one relevant Tier 1 family plus two independent topic-specific discovery forms: one cue-led and one source/actor-led. If these execute successfully and yield no qualifying item, the primary window is checked-empty. Use the alternate-route retry only when a required check could not be executed or verified.
- For each custom interest, run four mandatory lanes — exact-field event, named source/actor, official/regulatory/registry/project, and industry-scope/business intersection — and check at least one relevant primary-source family. The first three lanes establish field coverage; the fourth enriches business relevance. If zero or one main story qualifies, run one additional national/vertical/mirror discovery pass. If any lane reveals a plausible lead, open and verify it before deciding status. Existing HTML, replay material, and candidates discovered for another row are lead sources only; they do not count as completion of the custom row's lanes.
- For `fintech`, the source-family pass must include the dedicated watchlist in `source-map.md` in compact batches, one financial-regulatory/industry lane, and one broader financial/data-technology lane. Record the named targets actually checked; do not let a generic fintech query stand in for the watchlist, and do not require every valid platform event to name an AEC customer.
- For `leadership`, use both a role query and an occasion query. Verify a current title only after a candidate is found.
- For `digital`, include a broad AI-event lane, an AI-specific AEC/industrial lane, and at least one official model, cloud, chip, construction-software or infrastructure-technology newsroom family.
- For `government`, inspect at least one central government/ministerial family and one provincial or municipal government family. Housing authorities alone never satisfy broad government coverage.
- For a custom `半导体` row, inspect at least one policy/government or exchange family and one semiconductor actor/association lane; an AEC-only query cannot prove the section empty.

When a relevant primary source has no searchable listing, a targeted official-domain query plus opening the returned official page or official listing counts as checking that family. A discovery-only result page does not count.

For custom interests, the two focused queries may be issued in the same batched tool call. When both searches complete and at least one relevant official listing or primary page is inspected, a zero-item result is `checked-empty`, not `limited`.

## Efficient query plan for large subscriptions

For subscriptions with more than eight sections, use a fixed breadth-first budget so all rows finish before deep reading consumes the run:

1. Issue topic-specific search queries in the host's maximum safe batch size (commonly four queries per call). Each query must name one ledger section; a tool call may carry several independent queries, but their evidence is recorded separately.
2. Cover standard topics in four clusters: market/project (`fintech`, `sourcing`, `matching`, `employment`), company/global (`overseas`, `leadership`, `enterprise`, `capital`), technology/policy (`digital`, `informatization`, `construction-tech`, `government`), and evidence/reading (`industry-data`, `standards`, `green`, `extended`).
3. Cover custom interests in the next batches using the exact-field, source/actor, official-record and business-intersection lanes. Do not postpone custom rows until after deep verification of standard topics. Schedule the extra national/vertical/mirror pass immediately for any custom row with zero or one qualifying main story.
4. Open and verify promising candidates only after every row has received its baseline pass. Then inspect the required official family or index for zero-result rows. Apply relevance from each row's perspective so one event may qualify as a primary card in one row and a cross-section full card in one other row.
5. Retry only rows whose required path failed. Do not rerun every quiet section merely because it produced zero candidates.

A single official index may support several closely related rows only when its newest entries were inspected against each row's own cues. Record the same family separately in each applicable ledger row; never multiply one generic construction query across unrelated sections or use one construction-only query to declare a broad adjacent field empty.

## Three-pass retrieval

1. **Breadth-first baseline pass:** give every selected standard section and every custom interest a field-lane discovery pass before deep-verifying any section. Follow with source/actor lanes in the same breadth-first order. Batch related queries when supported, but create a separate ledger result for each topic. This prevents early high-volume sections from consuming the run budget and prevents the construction lens from suppressing adjacent-field news.
2. **Freshness/source pass:** inspect the newest entries in the most relevant accessible Tier 1 source families and the required independent authority/industry discovery path. For zero-result sections, continue only until the applicable empty-section threshold is met.
3. **Candidate-verification pass:** after every required discovery lane has been initial-screened, open every non-duplicate plausible event through the route ladder in `retrieval-routing.md` and verify source, timestamp or event time, core fact, stable evidence URL, industry bridge, and duplication before inclusion. Include every eligible event up to the configured ceiling; count actually opened evidence pages, not search snippets or unvisited result links. Record a closure reason only when the discovered candidate pool is exhausted or that ceiling is reached.
4. **Limited-section retry pass:** before rendering, retry only zero-item rows whose required query or official-family check failed, using a different available route: official RSS/sitemap/site search, an alternate official record, a corroborated Tier 2 fallback, or a validated external JSON feed. Do not retry a row whose required checks completed successfully and simply found no qualifying news. Stop after this one bounded retry and record the actual remaining limitation.

On a host with outbound network access but no dedicated WebSearch/WebFetch tool, perform the same three passes using the direct-network matrix in `network-retrieval-playbook.md`. The transport can differ by source: for example, browse an official listing, read a public RSS using HTTP, then verify a candidate through the counterparty's newsroom. Do not ask the user to build a feed unless all of these available public routes were tried and denied.

Batch independent queries when the host supports it, but update ledger rows separately. A combined query counts for a section only when it contains that section's exact cue or named target and its results were inspected for that ledger row. A generic construction-news query cannot satisfy every section.

When an original page is blocked, follow `retrieval-routing.md`. For an ordinary non-controversial event, an accessible official alternate, direct event-counterparty page, or one established authority/industry source that identifies the actor, event and time can verify it. Material, sensitive or disputed claims still require an official record or two independent credible sources. A blocked page alone does not make a section `limited`; the status is decided only after the bounded fallback pass.

## Time handling

- Use the exact timezone-aware run timestamp, 24-hour primary cutoff, and 48-hour fallback cutoff.
- A page dated only with the run's current local date is inside the window because that local date begins after the cutoff.
- A page dated only with the cutoff date is ambiguous when the cutoff is later than midnight. First seek page metadata, a feed timestamp, an exchange record, attachment metadata, or the underlying event time. If none exists, but the page's local date is demonstrably within the overall rolling 48-hour range and the evidence is Tier 1 or qualifying Tier 2, retain it as `included-date-observation`: preserve the stated date, record `time_basis_type: published` or `event`, `timestamp_precision: date-only`, and `window_class: observed`, visibly label it `48小时窗口观察 · 原始页面未披露时分`, and never classify it as primary, fallback, expanded or business-observation. Otherwise exclude it as `date-only-ambiguous`.
- A new effective date, filing, award, signing, opening, or other underlying event inside the window may qualify even when the announcing document was published earlier. State the event time basis clearly.
- Search the 24-to-48-hour fallback segment only for a section that has zero qualifying primary-window items and has met the 24-hour empty-section threshold. If the primary search is `limited`, do not treat zero results as proof of emptiness and do not use older items to conceal the limitation.
- Fallback items must independently pass the same source, timestamp, relevance, and verification rules and must be labeled `48小时补充` in the HTML and audit.
- A date-only observation is a separate third time state, not a fallback item. It may make the report more informative but never satisfies the primary or fallback finding threshold and never authorizes a success marker.
- If any primary-window item qualifies, do not add fallback items to that section. The fallback is section-specific, not a global widening of the entire brief.
- Weekend or holiday quietness never permits widening beyond 48 hours or to one week.

## Status decisions

- `complete`: at least one qualifying full card meets the finding threshold. The declared target of two or three cards is a candidate-screening target, not a card quota. When the rendered count is below that target, the row may remain `complete` only after the mandatory additional discovery pass has opened at least `target + 2` candidates across two domains and records `below_target_reason` plus each candidate's evidence-based inclusion or exclusion reason. Compact related evidence never makes a row complete.
- `observed`: the section contains at least one direct `48小时窗口观察` card with a date-only time basis, but no independently timestamped primary/fallback card. It is a transparent partial state, not successful realtime coverage.
- `checked-empty`: no item qualified in either window and the applicable checks executed successfully. This includes genuine zero-result searches and official listings whose newest entries are outside the window.
- `limited`: no item qualified, the empty-section threshold remains unmet after the bounded fallback retry, and the cause is a tool limit, blocked sources, network failure, unavailable timestamps, or interrupted execution.

When strict timed cards are absent, a section should normally use a real `expanded` or `business-observation` card before becoming `checked-empty`. `checked-empty` may appear only after the relevant live source families and all continuity levels have been exhausted. A `limited` section must say that coverage was insufficient and must not claim no news exists.

### Candidate identity gate

Every ledger candidate, whether included or excluded, needs a real publisher-facing title, source name, direct HTTP(S) page URL and date/time basis. Included formal cards additionally require a direct article, announcement, filing, procurement record or feed-item URL; a generic agency directory, search result, listing home or category page cannot be the final citation. Do not use placeholders such as `某软件厂商`, `某企业`, `某媒体`, `某机构`, `某标准`, synthetic-looking URLs, or generic landing pages as if they were a candidate page. An inaccessible but real page may be recorded with its real title and URL plus the failure reason; a made-up example is never audit evidence.

If any selected row is `limited`, still produce a clearly labeled partial HTML artifact when useful, but do not run `mark_success.py`. Report the limitation so the same Shanghai date remains eligible for retry or catch-up.

## Reader-facing audit

Populate the collapsible `检索审计` panel from the ledger:

- summary: `{{COVERAGE_COMPLETE}}/{{SELECTED_TOPIC_COUNT}} 板块完成`;
- aggregate candidate pages opened, included stories, and exclusions;
- one compact row per section showing label, source-family count, candidate count, primary included count, related count, and status;
- each compact row must be followed by a non-empty `audit-section-detail` disclosure. It names the actual checked source families with channel and domain, lists included title(s) with their time basis, and gives the row's candidate-pool closure/status reason. Under-target, observed, expanded, business-observation, checked-empty and limited rows also list the best three excluded candidates. This lets the reader verify the audit without exposing raw queries or internal chain-of-thought;
- aggregate exclusion reasons in plain Chinese.
- source diversity: unique final source domains, Tier 1/Tier 2 story counts, and the largest single-domain share.
- unique-event count, total full section-card count, cross-section full-card count, and compact related-card count as separate values;
- for every checked-empty section, up to three excluded-candidate summaries with title, date and exact reason, sourced from the validated ledger.

## Source-diversity audit

Run this audit after candidate selection and before HTML rendering:

- Count unique final evidence domains across main stories separately from related cards.
- For subscriptions of 12 or more sections, aim for at least `min(16, selected_section_count)` unique final domains when qualifying news exists across that breadth. This is an effort target, not permission to add weak items.
- No convenience mirror, aggregator or disclosure-reprint domain should provide more than 20% of main stories when equivalent independent official, exchange, company or authoritative-media pages are available. Direct official databases and exchange filing systems may exceed the threshold only when the brief documents that concentration as an exception.
- When two or more stories qualify in one section, prefer at least two independently maintained evidence domains unless both items are direct filings in the same official database.
- If the diversity target is missed, run one bounded source-substitution pass: replace mirrors with original/alternate official pages where accessible and search one unused source family for each under-target high-output row. Record the remaining reason instead of silently reporting full diversity.

Do not expose internal reasoning, credentials, session details, or long raw query strings. The audit exists to distinguish verified quietness from incomplete retrieval.

## Reader-facing writing quality

An included card is a compact business intelligence note, not a link preview. Before rendering a full card, check that its factual paragraph answers **who**, **what changed**, **when**, and at least two available **decision-bearing details** (amount, scale, place, project stage, policy tool, product capability or affected object). Its relevance paragraph must connect that fact to the selected section through a concrete mechanism; its `行动/风险点` must name a usable verification, sourcing, bidding, investment, compliance or customer action; and its `研判` must name a bounded implication and a next verification point.

Do not repeat a generic sentence across cards or sections. A source with only a headline/snippet is discovery evidence, not enough for a high-density card. Where a credible Tier 2 report is the most accessible evidence for an ordinary event, retain it with the `T2权威转述` label and identify the named underlying actor or record; do not lower the report into an empty baseline solely because the first-party page is inaccessible.
