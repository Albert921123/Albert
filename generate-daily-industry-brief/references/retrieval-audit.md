# Retrieval coverage and audit

Read this reference whenever generating or catching up a brief. It prevents an unsearched section from being mislabeled as a quiet section. The primary window remains the rolling 24 hours; a section confirmed empty in that window may use the separate 24-to-48-hour fallback segment. This creates no minimum article quota.

## Coverage ledger

Create one ledger row before searching for every selected standard topic and every custom interest. Keep it in working memory or a temporary structured record until the HTML is complete.

Each row contains:

- exact section ID and displayed label;
- distinct source families checked;
- section-specific targeted query count;
- candidate pages opened;
- included item count;
- related-evidence count for events whose full story is rendered in another selected section;
- primary-window and fallback-window included counts;
- excluded counts for `outside-window`, `date-only-ambiguous`, `duplicate`, `not-industry-relevant`, `not-primary-enough`, `inaccessible`, and `other`;
- final status: `complete`, `checked-empty`, or `limited`;
- a short limitation reason when status is `limited`.
- verification route used for each included or related event: original, browser-rendered original, official alternate, event counterparty, or authority/industry fallback.

A source family is an independently maintained primary-source channel, such as a ministry or local-government publication stream, a public-procurement platform, an exchange filing system, a company newsroom or investor-relations site, a standards publisher, or an original research publisher. Multiple search queries against the same website count as one source family.

## Adaptive search coverage

Use the topic cues in `topics.md`, the source pool in `source-map.md`, and the exact lanes in `section-source-catalog.md`. Coverage is asymmetric: proving a verified finding and asserting that a section is quiet are different tasks. These thresholds measure search effort, not desired article count.

### Section-first relevance

- Search the selected field itself before searching its intersection with construction. A qualifying field event does not need an artificial AEC reference when the section is broad by definition or was entered as a custom interest.
- `industry_scope` is a ranking context. It may raise an AEC-related candidate above another candidate of equal authority and freshness, but it must not silently remove valid `数科`, `政府宏观`, `AI`, `投融资`, `行业数据`, `拓展阅读` or custom-interest news.
- Keep construction-specific admission rules for inherently AEC sections such as `sourcing`, `employment`, `informatization` and `construction-tech`.
- Aim to retain 2–3 non-duplicate, decision-useful main stories per active high-output field when the verified window supplies them. This is a discovery/ranking target, not a quota and never permits stale or unverified filler. When fewer than two qualify after the baseline passes, execute the additional discovery pass below before finalizing the row.

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

A section with one or more qualifying items is `complete` when:

- at least one section-specific discovery pass was executed;
- every included item has a qualifying timestamp, a direct evidence URL, an explicit section/industry bridge, and the required primary-source or corroborated Tier 2 verification;
- at least one independently maintained relevant source family supplied or verified the included evidence.

A section may also be `complete` with one or more verified `关联资讯` cards when the underlying full story appears in another selected section, the card states a distinct section-specific business bridge, and that row's own field, source/actor, independent Tier 2 discovery and applicable empty-section passes were completed. Related cards improve navigation across genuinely overlapping domains; they never count toward the row's main-story target and never justify ending retrieval early.

### Additional discovery pass for thin high-output rows

Run this bounded pass for a high-output section with zero or one qualifying main story after its normal field and source/actor lanes:

1. Search one established national/financial/construction news family and one independent vertical-industry or disclosure-mirror family from `discovery-source-ladder.md`.
2. Open up to five new plausible candidate pages when available; do not count search snippets as opened candidates.
3. Route each candidate toward an original filing, government page, company announcement or event counterparty. If the original is unavailable, retain an accessible established Tier 2 account for an ordinary event when it names the underlying actor/record and date; label it `T2权威转述`.
4. Stop when three strong non-duplicate main stories qualify, or when both additional discovery forms have been exhausted. A genuine result of zero or one remains valid and must not be padded with stale or weak material.

Apply this pass by default to `fintech`, `overseas`, `enterprise`, `capital`, `digital`, `government`, `industry-data`, `standards`, `green`, `extended`, and broad recurring custom fields such as `专项债`, `光伏`, `房地产`, `城市更新`, `储能`, `AI方向`, and `半导体`. Use it for other sections when the day is evidently active.

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
4. Open and verify promising candidates only after every row has received its baseline pass. Then inspect the required official family or index for zero-result rows.
5. Retry only rows whose required path failed. Do not rerun every quiet section merely because it produced zero candidates.

A single official index may support several closely related rows only when its newest entries were inspected against each row's own cues. Record the same family separately in each applicable ledger row; never multiply one generic construction query across unrelated sections or use one construction-only query to declare a broad adjacent field empty.

## Three-pass retrieval

1. **Breadth-first baseline pass:** give every selected standard section and every custom interest a field-lane discovery pass before deep-verifying any section. Follow with source/actor lanes in the same breadth-first order. Batch related queries when supported, but create a separate ledger result for each topic. This prevents early high-volume sections from consuming the run budget and prevents the construction lens from suppressing adjacent-field news.
2. **Freshness/source pass:** inspect the newest entries in the most relevant accessible Tier 1 source families and the required independent authority/industry discovery path. For zero-result sections, continue only until the applicable empty-section threshold is met.
3. **Candidate-verification pass:** open every plausible event through the route ladder in `retrieval-routing.md` and verify source, timestamp or event time, core fact, stable evidence URL, industry bridge, and duplication before inclusion. Count actually opened evidence pages, not search snippets or unvisited result links.
4. **Limited-section retry pass:** before rendering, retry only zero-item rows whose required query or official-family check failed, using a different available route: official RSS/sitemap/site search, an alternate official record, a corroborated Tier 2 fallback, or a validated external JSON feed. Do not retry a row whose required checks completed successfully and simply found no qualifying news. Stop after this one bounded retry and record the actual remaining limitation.

Batch independent queries when the host supports it, but update ledger rows separately. A combined query counts for a section only when it contains that section's exact cue or named target and its results were inspected for that ledger row. A generic construction-news query cannot satisfy every section.

When an original page is blocked, follow `retrieval-routing.md`. For an ordinary non-controversial event, an accessible official alternate, direct event-counterparty page, or one established authority/industry source that identifies the actor, event and time can verify it. Material, sensitive or disputed claims still require an official record or two independent credible sources. A blocked page alone does not make a section `limited`; the status is decided only after the bounded fallback pass.

## Time handling

- Use the exact timezone-aware run timestamp, 24-hour primary cutoff, and 48-hour fallback cutoff.
- A page dated only with the run's current local date is inside the window because that local date begins after the cutoff.
- A page dated only with the cutoff date is ambiguous when the cutoff is later than midnight. Exclude it unless page metadata, a feed timestamp, an exchange record, or the underlying event supplies a qualifying time.
- A new effective date, filing, award, signing, opening, or other underlying event inside the window may qualify even when the announcing document was published earlier. State the event time basis clearly.
- Search the 24-to-48-hour fallback segment only for a section that has zero qualifying primary-window items and has met the 24-hour empty-section threshold. If the primary search is `limited`, do not treat zero results as proof of emptiness and do not use older items to conceal the limitation.
- Fallback items must independently pass the same source, timestamp, relevance, and verification rules and must be labeled `48小时补充` in the HTML and audit.
- If any primary-window item qualifies, do not add fallback items to that section. The fallback is section-specific, not a global widening of the entire brief.
- Weekend or holiday quietness never permits widening beyond 48 hours or to one week.

## Status decisions

- `complete`: for a standard section, the finding threshold is met and one or more primary stories or verified related-evidence cards qualified in the primary window, or the primary window was checked-empty and one or more explicitly labeled fallback items qualified. For a custom-interest section, at least one formal main story must qualify in the primary window, or the primary window must be checked-empty and at least one formal, explicitly labeled fallback story must qualify. A related card alone never makes a custom row complete.
- `checked-empty`: no item qualified in either window and the applicable checks executed successfully. This includes genuine zero-result searches and official listings whose newest entries are outside the window.
- `limited`: no item qualified, the empty-section threshold remains unmet after the bounded fallback retry, and the cause is a tool limit, blocked sources, network failure, unavailable timestamps, or interrupted execution.

Only `checked-empty` may use the normal no-update card. A `limited` section must say that coverage was insufficient and must not claim no news exists.

If any selected row is `limited`, still produce a clearly labeled partial HTML artifact when useful, but do not run `mark_success.py`. Report the limitation so the same Shanghai date remains eligible for retry or catch-up.

## Reader-facing audit

Populate the collapsible `检索审计` panel from the ledger:

- summary: `{{COVERAGE_COMPLETE}}/{{SELECTED_TOPIC_COUNT}} 板块完成`;
- aggregate candidate pages opened, included stories, and exclusions;
- one compact row per section showing label, source-family count, candidate count, primary included count, related count, and status;
- aggregate exclusion reasons in plain Chinese.
- source diversity: unique final source domains, Tier 1/Tier 2 story counts, and the largest single-domain share.

## Source-diversity audit

Run this audit after candidate selection and before HTML rendering:

- Count unique final evidence domains across main stories separately from related cards.
- For subscriptions of 12 or more sections, aim for at least `min(16, selected_section_count)` unique final domains when qualifying news exists across that breadth. This is an effort target, not permission to add weak items.
- No convenience mirror, aggregator or disclosure-reprint domain should provide more than 20% of main stories when equivalent independent official, exchange, company or authoritative-media pages are available. Direct official databases and exchange filing systems may exceed the threshold only when the brief documents that concentration as an exception.
- When two or more stories qualify in one section, prefer at least two independently maintained evidence domains unless both items are direct filings in the same official database.
- If the diversity target is missed, run one bounded source-substitution pass: replace mirrors with original/alternate official pages where accessible and search one unused source family for each thin high-output row. Record the remaining reason instead of silently reporting full diversity.

Do not expose internal reasoning, credentials, session details, or long raw query strings. The audit exists to distinguish verified quietness from incomplete retrieval.
