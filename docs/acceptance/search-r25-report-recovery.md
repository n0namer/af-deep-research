# Search r25 report recovery oracle

Status: CANDIDATE / UNACCEPTED

## Scope

This source-bound pytest oracle exercises the existing native verified_pipeline and research_run APIs without mock-only end-to-end acceptance.

## Evidence contract

- Positive: exact source SHA/signatures, durable report persistence and recovery, duplicate provider-call idempotency, and explicit partial abstention.
- Negative: foreign owner/stale CAS, forged or stale source SHA, missing primary evidence, restart with no durable report, and provider outage fallback.
- The test imports the real Python modules and binds the expected source hashes; it does not modify production sources.
- Acceptance remains with independent QA/reviewer and coordinator terminal readback.

## Validation

Authorized command: python -m pytest -q tests/test_search_r25_report_recovery.py

Expected DoD: one positive path and at least three fail-closed or bounded-fallback paths, with exact source identity and no fabricated evidence.
