# Northstar Gap Retrieval C4 QA — 2026-10-13

Status: CANDIDATE / UNACCEPTED / INFRASTRUCTURE-BLOCKED

## Authority

- Task: `af-deep-research:v2-c4-native-acceptance-gap-retrieval-20261013-r1`
- Attempt: `attempt-b1ac549c-b30c-450a-8871-1003c5495435`
- Session: `manual-20261013-c4-native-acceptance-frontier-r-fa9342719f25eae6`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Production source is read-only in this task. No live Ruflo/CrewSync state was called or modified.
- Acceptance remains with an independent verifier/reviewer and authoritative coordinator readback.

## Source-bound identities

| Artifact | SHA-256 | Evidence |
| --- | --- | --- |
| `reasoners/deep_research_ext/gap_research.py` | `0e268ac8c179938f4b2ddc37970bb89fd78438e23845b39db66f8ead1134b1fd` | Fresh scoped read, 198 lines. |
| `tests/test_northstar_gap_loop_contract_20261013.py` (final) | `e14e57d1a0cbd92c9a279d8163a6cddb10374234ef6109cd720ed6921c09d94b` | Final scoped write identity after edge-case review. |
| `tests/test_northstar_gap_loop_contract_20261013.py` (runner attempt) | `ea1eb21ef184b9b5c90ca179b5148dd9378acb8422445df4a5c5a82cdb301efd` | Authorized blocked runner source identity before the prompt-injection assertion was added; collection never started. |
| Git source state | `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc` | Coordinator-supplied prelaunch binding; not recomputed in the read-restricted lane. |

## C4 boundary under test

### DTOs

- `GapQuery(requirement_id: str, queries: List[str])`
- `GapQueryPlan(gaps: List[GapQuery])`
- `GapRoundTrace(attempted_requirements, new_source_count, new_claim_count, new_verified_claim_count, skipped_source_count, budget_exhausted, novelty_exhausted)`

### Functions

- `plan_gap_queries(*, contract, coverage, ai_call, model=None, api_key=None, queries_per_gap=2) -> GapQueryPlan`
- `run_gap_research_round(*, contract, coverage, ledger, research_package, stream_executor, ai_call, source_strictness, model=None, api_key=None, source_budget=None) -> tuple[Dict, EvidenceLedger, GapRoundTrace]`

The focused suite calls both native functions. The retrieval executor is explicitly named a deterministic primary-source adapter; it is not represented as a live network/provider integration. Downstream claim mapping and verification are replaced with deterministic in-process seams so the suite isolates the C4 gap-loop contract without paid providers or shared services.

## Focused scenarios

| Scenario | Expected invariant | Runtime status |
| --- | --- | --- |
| Planner filtering and query budget | Ignore foreign/already-verified requirements, trim blanks, cap each gap to `queries_per_gap`. | `BLOCKED` before collection. |
| Native positive retrieval | Invoke the native round, accept an admissible primary source, merge one verified claim, preserve caller inputs. | `BLOCKED` before collection. |
| Equivalent-source dedup, hostile-source rejection, and global source budget | Accept a URL once, reject instruction-bearing content, skip duplicate and over-budget candidates, set `budget_exhausted`. | `BLOCKED` before collection. |
| Stale/restart replay | Reject a source URL already present in the checkpoint and preserve checkpoint package/ledger. | `BLOCKED` before collection. |
| Crash/retry atomicity | Propagate the adapter crash without mutating checkpoint state; a retry accepts the source exactly once. | `BLOCKED` before collection. |
| Insufficient-evidence abstention | Empty plan returns `novelty_exhausted` and never invokes retrieval. | `BLOCKED` before collection. |
| Equivalent-gap dedup | Repeated semantically identical entries for one requirement schedule only one retrieval task. | `BLOCKED`; source review indicates a likely product gap. |

## Source-review finding

`plan_gap_queries` filters by unresolved requirement ID and caps each entry's queries, but it appends every accepted `GapQuery` without tracking a previously emitted requirement/query identity. `run_gap_research_round` then schedules one task per returned gap. Therefore duplicate planner entries for the same requirement can schedule duplicate retrieval work even though duplicate returned source identities are later rejected.

This is a source-backed `HYPOTHESIS`, not a runtime-proven failure, because pytest could not start. The focused test `test_equivalent_gap_entries_are_scheduled_once` encodes the required invariant and should become the reproduction check when the Python environment is restored.

## Validation receipt

Command represented by the authorized runner:

```text
python -m pytest -q tests/test_northstar_gap_loop_contract_20261013.py
```

Actual receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
exit_code=null
source_identity_sha256=ea1eb21ef184b9b5c90ca179b5148dd9378acb8422445df4a5c5a82cdb301efd
duration_limit_ms=120000
stderr="A regular local .venv Python executable is required."
```

No test is reported PASS, FAIL, or SKIP because collection did not start. The identical runner call was not retried. Affected Python regression execution is also blocked by the same prerequisite; no unrelated Node/Vitest test can establish this Python contract.

## Root-cause-only repair route

1. Restore or provide the repository's regular local `.venv` Python executable under the environment owner, then rerun the exact focused command above.
2. If the equivalent-gap test fails as predicted, route the production repair to the original C4 gap-retrieval producer CrewSync task/owner with write authority for `reasoners/deep_research_ext/gap_research.py`; that exact producer task ID is absent from this task's authorized evidence and must not be invented.
3. Keep the repair minimal: canonicalize/deduplicate equivalent planned gaps before creating executor tasks while retaining foreign-ID filtering and per-gap query limits.
4. Rerun the focused suite, then the producer owner's affected regression set, and bind exit codes/counts to the exact source and test SHAs.
5. Require independent review and authoritative terminal readback before any GREEN claim.

## Adversarial self-review

- The suite exercises production functions rather than a replacement implementation.
- The deterministic adapter is not labeled live and performs no network/provider action.
- Positive, invalid/foreign, budget, stale/restart, crash/retry, abstention, and duplicate-gap boundaries are explicit.
- Caller package and ledger mutation checks protect restart/checkpoint atomicity.
- The report does not turn a blocked runner into PASS or infer acceptance from file creation.
- The report distinguishes a source-backed defect hypothesis from a runtime-proven failure.
- No production source, live task, lease, claim, lock, terminal state, commit, push, deployment, or shared service was changed.
- Changed artifacts remain inside the exact task write scope.

## Remaining

- Focused pytest collection and execution are blocked by the missing regular local `.venv` Python executable.
- The equivalent-gap invariant is not runtime-confirmed.
- Affected regression results are unavailable for the same infrastructure reason.
- The exact original production repair task identity is not present in authorized evidence.
