# Stateful execution and delivery contract

Read this reference for every live generation, catch-up, retry, or scheduled run.

The Agent controls host-native search and browser tools. `scripts/run_pipeline.py` is the single supervisor that makes the next action observable, binds every evidence file and blocks skipped phases. `scripts/run_state.py` remains the subscription/run-history ledger; it is not a substitute search engine.

## One run, one durable state

The host-search loop is executable, not prose. Initialize it only with:

```text
python scripts/run_pipeline.py init --plan <plan> --profiles <validated-section-profiles> --reading-receipt <verified-receipt> --work-state <work-state> --output <pipeline-state>
```

Ask for work with `run_pipeline.py next`, execute that host action, and persist it through the same supervisor. Each `record-query` takes `--raw-results <query-receipt.json>` plus the actual `--source-families-checked`, `--actor-classes-checked`, and `--event-families-checked` values. Each candidate in the receipt carries `source_family_id`, `source_class`, `actor_class`, and `event_family`. The supervisor computes the result count and rejects incomplete persistence. If `next` returns another `host_search`, `verify_candidate` or `close_section`, continue; do not emit a heartbeat completion or claim background progress.

The raw query receipt must contain the exact query and route, status, the complete result array, and `transport_evidence` with the real host tool name, timezone-aware capture time, and either an invocation ID or a specific reason that the host does not expose one. A hand-authored count is not evidence. Keep the receipt file unchanged because its SHA-256 is reconciled between work state and ledger.

After the full-package reading receipt passes, create exactly one state file:

```text
python scripts/run_state.py start --state-dir .zhixun-state --report-date YYYY-MM-DD --run-id <unique-id> --selected-sections <count> --config-fingerprint <fingerprint>
```

Create `run-plan-<run-id>.json` first with `scripts/prepare_run_plan.py` and add `--plan <path>` to this command. The plan is the exact source of selected section IDs, lane order and review-depth floors. It must remain attached to the same run state after a block/resume.

Advance only after completing the preceding phase:

1. `full-package-reading`
2. `capability-preflight`
3. `candidate-discovery`
4. `original-page-verification`
5. `full-section-ledger`
6. `html-render`
7. `validation`
8. `delivered`

Use `run_state.py advance --state-file <path> --phase <next-phase>`. A query, a partial ledger, or an HTML draft is never sufficient to advance a phase.

Use `run_state.py checkpoint --state-file <path> --section <section-id>=<checkpoint>` after each actual batch. Valid checkpoint text is host-defined but must name completed work, for example `breadth-discovery-complete` or `original-pages-verified`; it must never say `running-in-background`.

## Interruption, retry, and conversation rules

- A running state file is **not** a background worker. Do not say that work continues after the Agent turn ends unless the host supplied a real observable job identifier.
- A user-requested run must not end voluntarily after a checkpoint. After every board batch, select the next unresolved row from the run plan and continue its lanes in the same turn. A valid stop requires an actual interruption, host execution limit, exhausted working routes, login/authorization requirement, or another external block; `候选不足` alone is never a stop because the row still needs its expansion pass and final continuity outcome.
- When a row is closed, persist `run_state.py checkpoint --section-outcome <section-id>=<outcome>` where outcome is one of `complete`、`observed`、`expanded`、`business-observation`、`checked-empty` or `limited`. Do not treat a prose checkpoint as closure. After three documented lanes, two source families and three opened candidates, a row whose plausible candidates were all concretely rejected must close as `checked-empty` or `limited`; it must not remain open merely because its presentation target was not reached. The helper prevents the HTML-render and delivery phases while any planned row lacks that outcome or remains pending.
- If the active turn cannot complete, use `block` with the exact reason, pending sections and next action. Add `--needs-human` only for a real login, authorization or unavailable user-controlled capability; this alone returns `未交付，需人工处理`. All ordinary interruptions, time limits and incomplete retrieval return `未交付，待续跑`. On the next invocation, first run `run_state.py resume --state-file <path>`; it reopens the same recorded phase and retains the pending-section list. Do not create a second run state for the same report date/configuration merely to bypass a blocked state.
- On the next invocation, inspect the newest non-delivered state and resume from its recorded phase. Rediscover/reverify candidates whose live time window expired; prior HTML and candidates are leads, not fresh evidence.
- Do not produce a reader-facing partial HTML for a live Mode A/B/C run.

## Completion

Before rendering, run `run_pipeline.py seal-retrieval` and `run_pipeline.py authorize-render` with the ledger, structured brief model and `references/source-registry.json`. Render only through `run_pipeline.py render`; it uses the locked template and the validated model instead of free-form HTML generation. Finish with `run_pipeline.py finalize`. Authorization refuses an unfinished loop, mismatched raw receipt, unsupported source claim, stale timestamp or thin editorial model. Finalization rejects any hash change and reruns the ledger, source, model, time, HTML, editorial and template gates. `validate_html.py` alone cannot legitimize a simplified or incomplete ledger. An HTML file without the formal receipt is a draft or limited artifact even when it opens normally.

For a one-card or zero-card row, do not manufacture additional stories. Close it only after recording `candidate_pool_exhausted: true`, `additional_discovery_completed: true` and a concrete `below_target_reason`; the ledger validator treats these as evidence that the presentation target was not confused with an output quota.

After all selected rows have valid final outcomes, render the locked template and run the ledger, HTML, editorial and delivery validators. Only `run_state.py deliver` from the `validation` phase, with all four gates set to `passed`, may make the state `delivered`. Write the success marker afterwards.

Final feedback must be one of these three results:

| Result | Required feedback |
|---|---|
| 已交付 | HTML path, ledger path, four passed gates, included-card and limited/checked-empty counts, success-marker result |
| 未交付，待续跑 | current phase, completed phases, pending sections, state path, precise resume action |
| 未交付，需人工处理 | blocked capability/authorization, exact user action and state path |

Progress messages may name only the current phase, completed/remaining row count and the next phase. They must not substitute for final delivery.
