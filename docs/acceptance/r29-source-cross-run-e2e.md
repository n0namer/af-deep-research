# R29 Source Cross-Run E2E Evidence

Status: CANDIDATE / UNACCEPTED

## Scope and source of truth

This receipt covers 'af-deep-research:v2-r29-source-cross-run-e2e-20261015-r1'.
No production file was changed: the inspected interfaces already implement the requested
source-owner, source-revision, checkpoint-sequence, report-identity, effect-id, and
source-file-SHA fencing.

Current source receipts from the scoped reader:

| Source | SHA-256 |
| --- | --- |
| 'reasoners/deep_research_ext/research_run.py' | '87c193a386be13daa2b89dceac6b749a87ae9b47efd84b18bd598017c6e9e8c3' |
| 'reasoners/deep_research_ext/verified_pipeline.py' | '97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87' |
| 'docs/architecture/basefive-r14-contracts.json' | '7d81581ed610a64337712806f7fb2edf4d6fc85d981cbfbdc692d267e79afc66' |

## Covered behavior

- Positive real persistence/resume of a grounded r10 report with one terminal effect.
- Cross-owner persistence rejection.
- Cross-source-file-SHA resume rejection.
- Citation/source identity contamination rejection during replay.
- Stale source revision and stale owner checkpoint rejection.

The test imports and exercises production Python implementations; it does not replace them
with mocks. It also asserts fresh SHA-256 computation over both inspected source files.

## Validation

Requested command:

'python -m pytest -q tests/test_r29_source_cross_run_e2e.py'

Expected result: 5 tests, exit 0. The authorized GO Wave runner exposes Node/Vitest/tsx
only; no Python/pytest runner was available in this lane, so this command could not be
executed here. This is an infrastructure-blocked verification, not PASS.

## Remaining

Independent QA must run the exact pytest command in a Python environment with the
repository dependencies installed, inspect any failure, and perform the required
CrewSync terminal readback. This candidate remains UNACCEPTED.
