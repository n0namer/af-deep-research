# R29 Search Federation — Candidate Evidence

Status: CANDIDATE / UNACCEPTED

## Contract

Federated search fans out concurrently to at most four configured providers by default and by hard environment cap. Provider names are ordered, case-normalized, and deduplicated before availability filtering. A provider failure is isolated and recorded by exception class; all-provider failure remains an explicit error. Fused results use canonical URLs, remove common tracking parameters, and retain provider/rank evidence.

## Scoped change

- `skills/search/federated.py`: changed the bounded provider default from 2 to 4 and hard maximum from 8 to 4.
- `tests/test_r29_search_federation.py`: native pytest coverage for four-provider fanout/dedup, cap and duplicate-name handling, failure isolation, and empty-input rejection.
- No unowned source files were changed.

## Verification

Required command:

```text
python -m pytest -q tests/test_r29_search_federation.py
```

The scoped MCP runner must provide the actual exit code and output. This artifact must not be treated as PASS if the Python runner is unavailable or denied.

## Acceptance boundary

This is a candidate only. Independent QA/reviewer verification and coordinator terminal readback remain required.
