# Universal section retrieval protocol

Read this reference before retrieving any section. It began as an unknown-section protocol, but the same mature “overseas-style” search depth is now mandatory for every standard, renamed, custom and uncatalogued section so that a configured keyword list, a short conversation or the first valid result never becomes a ceiling on discovery.

## 0. Overseas-parity is a universal contract

For every selected section, build and execute a three-dimensional search matrix before closure:

- actor classes: regulator/public institution, central SOE, local SOE, listed/private leader, owner/customer/counterparty, and exchange/procurement/association/research;
- source classes: official/regulatory, company/disclosure, transaction/project platform, national/financial media, and vertical/local media;
- event families: policy/data, project/order, enterprise/product, capital/market, risk/regulatory, and analysis/report.

Choose the relevant cells from the validated profile; do not mechanically force an irrelevant class. The profile must explain any genuinely inapplicable class. Search depth must be independent of how many times the user questioned a section. An Agent may batch transport calls, but it must persist separate section evidence and may not infer that another section's search covered this one.

## 1. Build the section profile before searching

Create one object per selected section in `section-profiles-YYYY-MM-DD.json` with:

- `section_id` and `label`;
- `definition`: the decision question this section should answer;
- `include`: at least three admissible subject or event descriptions;
- `exclude`: at least two confusing but out-of-scope descriptions;
- `keyword_tree`: non-empty arrays for `synonyms`, `subfields`, `actions`, and `risk_terms`;
- `actor_pool`: non-empty arrays for `regulators`, `central_enterprises`, `local_enterprises`, `listed_or_private_leaders`, and `counterparties_or_platforms`; use `not_applicable_reason` only where a class is genuinely irrelevant;
- `source_pool`: non-empty arrays for `official`, `disclosure_or_transaction`, `national_media`, and `vertical_media`; use named organizations/domains, never “网络”“媒体” or “搜索引擎”;
- `event_types`: applicable members of `policy-data`, `project-order`, `enterprise-product`, `capital-market`, `risk-regulatory`, and `analysis-report`;
- `time_policy`: which timestamp governs each selected event type;
- `queries`: distinct section-specific strings for `field`, `actor`, `official`, `business_intersection`, and `expansion`.

The Agent must infer this profile from the user's label and business context. Do not ask the user to supply a keyword list unless the label is genuinely ambiguous enough to change the section's meaning.

## 2. Use a source matrix, not one preferred website

Search the strongest relevant members of each pool:

1. competent ministries, regulators, local governments and public institutions;
2. exchanges, disclosure systems, procurement/public-resource platforms and project owners;
3. central SOEs, local SOEs, listed companies, private leaders, vendors and counterparties;
4. national news agencies and established financial media;
5. established vertical media, industry associations and research bodies.

A local SOE or specialist publisher is not optional merely because a central SOE or national portal was searched. Search-result aggregators may discover a lead but cannot replace the original record when that record can be reached.

## 3. Run four lanes plus expansion

- `field`: synonyms/subfields + current date/window + applicable event actions.
- `actor`: named actor pool members + event actions; rotate central, local and private actors.
- `official`: regulator, exchange, procurement, disclosure and project-owner records.
- `business_intersection`: the section plus adjacent decision dimensions such as procurement, delivery, finance, operations, technology, compliance or risk.
- `expansion`: mandatory when fewer than two cards survive; change both the vocabulary and at least two source families, search counterparties and vertical media, then reverse-trace every promising lead to its original page.

Batching tool calls is allowed, but every section keeps its own query text, results and decisions. One construction-wide or multi-section query cannot satisfy a lane.

## 4. Separate relevance from time admission

Build a broad relevant candidate pool first, then apply the clock:

- project/order/signing/start/completion items use the explicit underlying event time when the page provides it;
- original news, analysis, daily/weekly reports and newly released datasets use the original publication time, and must be labelled as analysis/data rather than rewritten as a new project event;
- repost, crawl, update and search-snippet times never admit an older event;
- a deadline is usable only when the deadline itself is the business event being reported, and the card must say so plainly;
- apply the 24-hour primary window first and the configured fallback only to a section with zero primary cards.

## 5. Rank, assign and close honestly

Rank candidates by source authority, directness, time precision, factual completeness and decision value. Open every non-duplicate candidate that survives the title/time/source/relevance screen. Assign one normalized event to exactly one strongest section. Include every independent qualifying event up to the configured maximum; never stop after the first convenient source.

If only one item survives, retain it and record the expansion work and specific rejected alternatives. Close a section empty only when all four lanes plus expansion have been executed, at least two changed source families were checked, every discovered lead has a decision, and the reason states the actual evidence failure. “没有搜到”“搜索结果有限” and “时间不足” are invalid closure reasons.

## 6. Required machine gate

Run `scripts/validate_section_profiles.py` before retrieval and preserve the validated profile path in the run/ledger. Then start the loop with `scripts/run_pipeline.py init --plan <plan> --profiles <profiles> --reading-receipt <receipt> --work-state <work-state> --output <pipeline-state>`. Every supervisor `record-query` call must reference a hash-bound `--raw-results` receipt and state the source families, actor classes and event families actually checked; every candidate must carry `source_family_id`, `source_class`, `actor_class` and `event_family`. Rendering is prohibited when a selected section lacks a validated profile, when its ledger lacks the four lanes and required expansion lane, when a raw receipt is missing or altered, or when work-state decisions do not exactly match the ledger.
