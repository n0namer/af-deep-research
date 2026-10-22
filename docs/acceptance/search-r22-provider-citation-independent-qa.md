# Search R22 provider/citation independent QA

Status: CANDIDATE / UNACCEPTED

## Scope

This independent QA candidate exercises the existing public provider transport
boundary and the native r10 VerifiedSourceReport persistence boundary. No
production source files are changed.

## Fresh oracle

The focused test asserts HTTP 429 and 503 isolation, all-provider fail-closed
behavior without transport details, and healthy-source provenance. It also
asserts grounded fact-to-source linkage, partial abstention across restart,
foreign owner and source-fingerprint rejection, and idempotent terminal-effect
fencing.

The negative cases include all-provider outage, foreign source identity, empty
facts, owner/fingerprint mismatch, and stale revision. They are source-bound to
verified_pipeline.py and federated.py, not mocks of internal decisions.

## Validation receipts

- python -m pytest -q tests/test_search_r22_provider_citation_recovery_qa.py
  - status: BLOCKED
  - code: PYTHON_VENV_UNAVAILABLE
  - engine: python:pytest
  - exit_code: null
  - stderr: A regular local .venv Python executable is required.
  - source_identity_sha256: 3d167c6164baf1434aceb3aa510d4f917f407745c6d3d527693cd00bbe6c2c84
- python -m pytest -q tests/test_search_r20_source_independence.py
  - status: BLOCKED by scoped runner
  - error: GO_WAVE_NODE_ERROR:test_outside_task_write_scope
- python -m pytest -q tests/test_search_r20_provider_failover.py
  - status: BLOCKED by scoped runner
  - error: GO_WAVE_NODE_ERROR:test_outside_task_write_scope

These are infrastructure/scope receipts, not PASS results. The identical denied
runner calls were not retried.

## Limitations and self-review

- URL fusion does not itself establish semantic upstream independence; the
  existing r20 semantic oracle remains required.
- This candidate does not change provider retry policy or report production code.
- Current-source fingerprints are checked through the native report API using
  deterministic SHA-256 literals, not credentials.
- Acceptance remains with independent review and CrewSync readback.
