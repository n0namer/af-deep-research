# R31 Source Gate

Status: CANDIDATE / UNACCEPTED

## Scope

This isolated QA artifact binds the current verified-source persistence boundary to the r14 architecture contract. It does not modify production code or claim product acceptance.

## Covered behavior

- Positive: current VerifiedSourceReport r10 source identity persists with the expected source SHA and repeated terminal effect recording is idempotent.
- Negative: malformed source hashes are rejected before persistence.
- Negative: a foreign caller cannot persist a report or record an effect.
- Negative: resume with a stale source-file SHA is rejected without mutating the canonical receipt.

## Source-bound evidence

- reasoners/deep_research_ext/verified_pipeline.py
- Expected SHA-256: 97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87
- Contract: docs/architecture/basefive-r14-contracts.json
- Contract DTO: VerifiedSourceReport=r10

## Validation

Run:

    .venv/Scripts/python.exe -m pytest -q tests/test_r31_source_gate.py

Acceptance remains with independent QA/reviewer and the authoritative CrewSync readback.
