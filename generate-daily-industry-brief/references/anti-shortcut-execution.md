# Anti-shortcut retrieval contract

Read this reference for every live or feed-backed daily run. Its purpose is to make insufficiently reviewed retrieval visible and to prevent a run from ending after the first convenient result.

## What it can and cannot guarantee

This contract verifies evidence of work; it cannot prove that a remote Agent did not hide a page it never opened. It therefore never authorizes fabricated search logs or filler. A host without search/fetch must use its declared capability mode and emit a limited artifact, not pretend that the contract passed.

## Required run record

The retrieval ledger `run` object must contain:

- `mode`: `A`, `B`, `C`, or `D`;
- `audit_contract`: exactly `anti-shortcut-v1`;
- `started_at` and `finished_at` in the run timezone;
- `selected_section_count`;
- `candidate_pool_origin`: `live-search`, `direct-fetch`, `validated-feed`, or `offline`.
- `primary_window_start`, `primary_window_end`, and `fallback_window_start`, all timezone-aware ISO timestamps.

For mode A, B, or C, a prior daily HTML, prior ledger, search snippet, or model memory is never an admissible candidate pool. It may supply keywords only. Every rendered event needs a current-run candidate record and its opened direct evidence URL.

## Required section proof

Every section row must include a `retrieval_proof` object:

```json
{
  "lanes_attempted": ["field", "actor", "official", "business-intersection"],
  "source_families_checked": ["来源族名称一", "来源族名称二"],
  "opened_candidate_count": 4,
  "screened_candidate_count": 7,
  "target_card_count": 2,
  "additional_discovery_completed": false,
  "below_target_reason": "额外候选均因超出时窗、重复或相关性不足被排除",
  "candidate_pool_closure": "required-lanes-exhausted",
  "closure_reason": "四条必经路径已完成初筛；其余候选均已记录具体排除原因",
  "stop_reason": "已完成候选池核验；收录全部符合时效、来源、相关性与去重要求的资讯"
}
```

- A broad or custom section must list `field`, `actor`, and `official`; `business-intersection` is also required when it is meaningful for that section.
- An inherently AEC row may use the closest equivalent lanes, but must still have at least three recorded lanes.
- `source_families_checked` must name actual independently maintained channels, not “网络搜索” or “多个媒体”.
- A publisher name and the same publisher's domain are one source family. `WebSearch 混合来源结果` is a transport label, never a source family.
- `opened_candidate_count` must equal or be lower than that row's candidate-ledger count; it is the count actually opened, not search-result snippets.

## Stop rules

Set `target_card_count` to 2 for every selected row, and 3 for high-output rows or rows with relevance 9–10. A live ledger with `target_card_count: 1` is invalid. This is a screening-depth target, never an early-stop threshold. For each required lane, screen every current candidate entry; open and verify every non-duplicate candidate that passes the initial title/time/source/relevance screen. The Agent may end the row only when all required lanes and their discovered candidate pool are exhausted, or when it reaches the configured per-section item maximum.

If fewer than the screening target number of full cards are retained, the row must set `additional_discovery_completed: true`, open and retain at least `target + 2` real candidates across at least two domains, record at least two distinct extra source families or discovery routes in its candidate records, and give a specific `below_target_reason` plus an exact reason for each rejected candidate. “暂无更多”“搜索结果有限”“节省 token” and equivalent generic reasons are invalid. This is a review-depth requirement, not an output quota: the row may remain `complete` when it has at least one valid full card and the extra candidates were genuinely excluded for recorded evidence-based reasons.

If multiple verified A/B candidates exist, rank and include every non-duplicate qualifying candidate up to the configured per-section maximum rather than silently choosing one, two or three. Candidates not selected because of duplication, assignment to a more directly relevant section, weak relevance, outside-window time, or lower rank must remain in the candidate ledger with the exact reason. A candidate already used in another section is not available to fill this row.

## Candidate evidence contract

Every included live candidate must additionally contain:

- `direct_record_url` and `direct_record_kind`: the direct article, announcement, filing, procurement record or feed item that supports the card; a generic listing, agency directory or search result cannot be a formal-card record;
- `canonical_url`, `source_family_id`, and `event_fingerprint`: normalized values used to prevent the same announcement, procurement or business event from appearing in two sections through different mirrors;
- `time_basis_type`: `published` or `event`; `timestamp_precision`: `datetime` or `date-only`; and `window_class`: `primary`, `fallback`, or `observed`.

Use `published` whenever the page publication time is the basis. If an older document announces a current scheduled event, use `event` only when the event date/time is explicit in that direct record; display publication and event time separately in HTML. A `date-only` candidate can only be `observed` and use `included-date-observation`; it cannot be labeled primary, fallback, expanded or business-observation. Expanded and business-observation cards must still have a datetime inside the rolling 48-hour range.

Before assignment, derive `event_fingerprint` from the actor, action/event, affected object, event date and canonical record. The same fingerprint or canonical URL may be included in only one section. Other sections retain it only as an excluded `assigned-to-<section-id>` candidate.

## Delivery gate

For modes A/B/C, do not call a report `完整` or write a success marker unless:

1. the ledger validator passes the anti-shortcut checks;
2. every selected row has the required proof;
3. every under-target high-output row documents its expansion pass and `below_target_reason`, and every row documents how its candidate pool was closed; and
4. the reader-facing audit reports the number of opened candidates, included cards, distinct final domains, and rows that did not meet their target.

When Python is absent, render the same proof in the audit and state `manual-validation`. When a host has no live source access, it must not claim this gate passed.

## No early-baseline rule

`baseline` exists only for Mode D: no working live route and no validated current external feed. It is not a time-saving outcome for a Mode A/B/C run. If `run.network_probe.internet_reachable` is true and a working route is recorded, every selected row must finish its required discovery and verification lanes before rendering. The valid outcomes are a timestamped full card, a date-only observation, an expanded/business observation backed by a real current source, or a documented checked-empty result.

If a run is interrupted before all rows have reached one of those outcomes, it is **unfinished**, not a partial brief. Do not produce a reader-facing HTML that mixes a few verified cards with live-mode baseline cards. Preserve the working ledger if useful, report the unfinished rows, and restart those rows from fresh discovery on the next run.

The automated delivery gate is mandatory: run `validate_retrieval_ledger.py`, then `validate_html.py --ledger`, and let `mark_success.py --ledger-file` rerun both checks. A missing matching ledger, a live baseline row, or a failed gate blocks both success marking and the words “已补发完成” / “完整日报”.
