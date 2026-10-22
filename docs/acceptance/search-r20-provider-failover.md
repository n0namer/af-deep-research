# Search R20 provider failover

Status: CANDIDATE / UNACCEPTED

## Scope

This receipt covers independent tests of the public skills.search.federated.search_with_providers
and skills.search.fusion.fuse_search_responses behavior. The tests inject faults through
concrete SearchProvider implementations and do not patch registry, orchestration, or fusion
internals.

## Definition of Done

- 429, 503, and timeout failures are isolated while a healthy sibling contributes a source.
- Fused results retain healthy-provider provenance.
- All-provider failure fails closed and redacts transport details.
- A malformed response-model payload is isolated while the healthy sibling survives.
- Provider calls are concurrent over the bounded input set.
- The focused test exits through the real pytest runner.

## Validation

Required commands:

    python -m pytest -q tests/test_search_r20_provider_failover.py
    python -m pytest -q tests/test_search_federation.py

Runtime receipts:

- Focused command: `python -m pytest -q tests/test_search_r20_provider_failover.py`
  - status: BLOCKED
  - code: PYTHON_VENV_UNAVAILABLE
  - engine: python:pytest
  - exit_code: null
  - stderr: "A regular local .venv Python executable is required."
  - source_identity_sha256: b1c067d8532cfbbe54edf4bcf6f0f6a63849b0888fb6c85437d71e339f7ad3f6
- Regression command: `python -m pytest -q tests/test_search_federation.py`
  - status: BLOCKED by scoped runner
  - error: GO_WAVE_NODE_ERROR:test_outside_task_write_scope

These are infrastructure/scope receipts, not PASS results. This artifact is evidence for independent
review only; it does not claim acceptance.

## Self-review

- Production files remain unchanged.
- Faults are injected at the provider transport boundary.
- Error assertions permit only provider names and safe exception classes; exception messages and
  secrets are not returned.
- Empty or malformed provider contributions cannot replace a healthy source.
