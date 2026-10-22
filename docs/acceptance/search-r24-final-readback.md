# Search R24 final readback audit

Status: CANDIDATE / UNACCEPTED

## Purpose

This independent, read-only audit checks the R19-R23 receipt boundary against the
source-bound artifacts available in this task. It does not mutate old tasks,
leases, locks, source code, or release state.

## Findings

- Current primary source identity and the declared search() signature are read
  from skills/search/__init__.py; the declared SHA is compared as a drift
  signal. A mismatch is never treated as green.
- Worker exit, publication transport, or a candidate receipt cannot imply
  acceptance. The available reducer and R23 artifacts remain
  CANDIDATE / UNACCEPTED.
- Post-failure self-promotion is rejected: acceptance remains owned by the
  independent verifier/reviewer, reducer coordinator, and authoritative
  CrewSync readback.
- A missing primary source is a fail-closed condition, not a successful audit.
- Graphify/ArchSteer are explicitly UNVERIFIED, and native full task-to-result
  failure/restart E2E output is unavailable. Readiness therefore remains
  BLOCKED, not ACCEPTED_GREEN.

## Test evidence

Requested command:
python -m pytest -q tests/test_search_r24_final_receipt_audit.py

The test contains one positive source/signature check plus negative fail-closed
checks for worker/acceptance conflation, post-failure promotion, missing source,
and absent live E2E/readiness evidence. The authorized GO Wave runner supports
Node/Vitest/tsx targets only; if it rejects this Python target, that is an
infrastructure blocker and must remain recorded as such.

## Remaining

Independent QA/reducer and authoritative CrewSync terminal readback remain
required. No product acceptance is claimed.
