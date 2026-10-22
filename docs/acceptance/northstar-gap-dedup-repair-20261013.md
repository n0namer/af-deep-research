# Northstar Gap Dedup Repair — 2026-10-13

Status: BLOCKED / UNACCEPTED

## Authority

- Task: `af-deep-research:v2-northstar-equivalent-gap-once-red6-spawnfix-repair-20261013-r2`
- Attempt: `attempt-e527ed17-564b-47e9-b843-c6dbc71b2fb4`
- Session: `manual-20261013-research-native-red6-production-763a3c591e1bab4e`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Independent verifier/reviewer retains acceptance authority.

## Root cause

`run_gap_research_round` scheduled every planner `GapQuery` independently. Equivalent entries for the same requirement and query set therefore created duplicate retrieval coroutines when their only differences were whitespace, casing, query order, or repeated queries inside one entry.

## Functional delta

- Normalize each scheduled query by collapsing surrounding and repeated whitespace.
- Deduplicate queries within one gap by case-insensitive identity while preserving the first normalized query text sent to the executor.
- Deduplicate equivalent gap entries by exact requirement ownership plus their normalized query set.
- Preserve distinct query sets for the same requirement, foreign-requirement filtering, source budgets, source-ID allocation behavior, and crash/replay atomicity.

## Compatibility

- `GapQuery`, `GapQueryPlan`, `GapRoundTrace`, `plan_gap_queries`, and `run_gap_research_round` public signatures are unchanged.
- Return tuple shape, trace fields, executor call shape, Pydantic models, ledger flow, source filtering, and budget enforcement are unchanged.
- Requirement ownership remains exact and case-sensitive; normalization applies only to query identity.

## Source identities

| File | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| `reasoners/deep_research_ext/gap_research.py` | `0e268ac8c179938f4b2ddc37970bb89fd78438e23845b39db66f8ead1134b1fd` | `1f00f5144b193bed2f26cd13a31742466e391814e52f926e1f2d58051b961a8e` |
| `tests/test_northstar_gap_dedup_regression_r1.py` | new | `9f92b681ffaab15e74eaa43acb4b5ab7ac97755463b69f926cd5b23396f4e0da` |

## Regression coverage added

- Equivalent whitespace/case/query duplicates schedule once while a distinct gap remains scheduled under the same source budget.
- A foreign requirement with an equivalent query cannot suppress the owned requirement's gap.
- A crashing retrieval attempt leaves checkpoint inputs unchanged; retry schedules the equivalent gap once and accepts the recovered source once.

## Verification receipt

Requested validation:

```text
python -m pytest -q -p no:cacheprovider tests/test_northstar_gap_loop_contract_20261013.py tests/test_northstar_gap_dedup_regression_r1.py
```

Authorized runner attempt against the original affected test:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
source_identity_sha256=e14e57d1a0cbd92c9a279d8163a6cddb10374234ef6109cd720ed6921c09d94b
exit_code=null
stderr="A regular local .venv Python executable is required."
```

The identical missing-runtime dependency was not retried. No PASS claim is made for the original or new tests.

## Adversarial self-review

- Equivalent identity includes the exact requirement ID, preventing cross-owner suppression.
- Query ordering does not create duplicate work because the identity tuple is sorted.
- Duplicate queries inside one gap do not consume executor query budget twice.
- The executor receives normalized first-occurrence text rather than lowercased identity text.
- Distinct query sets for one requirement remain separate scheduled tasks.
- Deduplication occurs before coroutine creation, so no duplicate retrieval side effect starts.
- Crash behavior remains governed by `asyncio.gather`; input package and ledger are not mutated before successful outputs are processed.
- Existing source-budget enforcement remains global across accepted articles and is not converted into a task-count budget.
- Public models and callable signatures remain unchanged.
- No files outside the exact write scope were modified by this worker.

## Remaining blocker

A regular local `.venv` Python executable must be available to the scoped runner. Then run the exact requested validation command and bind its exit code and test count to the source/test hashes above. Until that evidence exists, this repair remains BLOCKED / UNACCEPTED rather than CANDIDATE.
