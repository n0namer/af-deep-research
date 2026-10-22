# Search R26 receipt reconciliation

Status: CANDIDATE / UNACCEPTED

## Purpose

This independent reducer checks the boundary between an original worker/process
exit and an acceptance decision. It does not run providers or claim a full native
research acceptance. It does not mutate product code, CrewSync tasks, leases,
locks, or release state.

## Source-bound ledger

- Task: af-deep-research:v2-r26-receipt-reconciliation-20261015-r1
- Attempt: attempt-776caea4-c308-4a72-9bca-c8412d948dae
- Session: manual-20261015-qa-reducer-r26-af-deep-research-9050219efd894a72
- Source identity: docs/architecture/search-r16-contract.json
- Source binding: 98fae3d2e5259526139558c7cf492a9c96817606a2e486c7f1d22074772633c2
- Worker result required: go-core.worker-result.v1, CANDIDATE,
  acceptance.level=UNACCEPTED
- Acceptance authority: independent verifier/reviewer and authoritative
  CrewSync readback; this reducer cannot self-accept.

## Decision rule

The reducer returns READY_TO_COMPLETE only when the source binding matches,
the worker result has the original task key and typed candidate shape, and a
separate independent-QA receipt is present with status=PASS. The returned
acceptance remains UNACCEPTED.

It returns BLOCKED for missing/mismatched source evidence, missing or malformed
typed results, non-candidate or self-approved worker results, missing/non-pass
QA, and QA using the original task key.

## Focused checks

tests/test_search_r26_receipt_reconciliation.py contains one positive check and
three negative checks:

| Check | Expected result |
| --- | --- |
| Source-bound candidate + separate QA | READY_TO_COMPLETE, still UNACCEPTED |
| Missing independent QA | BLOCKED |
| ACCEPTED_GREEN / self-QA attempt | BLOCKED |
| Process success without typed result | BLOCKED |

These are receipt-boundary tests, not a mock or substitute for full research:
provider calls, native task-to-result E2E, and full answer-golden execution remain
unverified and require their original authorized owner.

## Validation receipt

Requested command:

    python -m pytest -q tests/test_search_r26_receipt_reconciliation.py

The scoped native GO Wave runner supports Node/Vitest/tsx targets, not Python.
Therefore this Python command must be run by an independent verifier in a regular
project Python environment; a runner denial is INFRA BLOCKED, never PASS.

## Affected-only future frontier

1. Run the exact pytest command and bind its output to the source/test SHA.
2. Supply the original typed worker publication and independent-QA readback.
3. Perform full native research/provider checks only under their original owner.
4. Reconcile again; retain CANDIDATE / UNACCEPTED until independent acceptance.
