# Search r21 Independent QA

Status: CANDIDATE / UNACCEPTED

## Scope

Independent QA for the real skills.search package and Jina adapter. Producer files were read but not modified. The test uses a deterministic transport only at the HTTP boundary; routing, parsing, federation, failure typing, and RRF fusion execute the real package code.

## Cases

- Positive: real Jina adapter parses a source-bound result.
- Positive: real federated path preserves Jina provenance.
- Negative: explicit single-provider mode does not federate.
- Negative: all provider failures produce a typed error without exposing a key.
- Negative: malformed Jina source is checked for fail-closed identity behavior.
- Negative: RRF does not claim independent providers when the same provider is repeated.

## Source evidence

- skills/search/jina.py SHA-256: 178b534f29100265d9db4886c77be1da648301f39cd65d7b2a400282e9fa1c54
- skills/search/fusion.py SHA-256: c7c0684e8d5d55df099ebf7690bfceafff78e79fe4ad15a6265ecb29a5a5625c

## Validation

Required native commands:

    python -m pytest -q tests/test_search_r21_independent_qa.py
    python -m pytest -q tests/test_evaluation_suite.py

The scoped GO Wave runner supports Node/Vitest/tsx targets only; Python pytest execution must therefore be recorded from the authorized environment if available. No producer source change is authorized by this task.

## Acceptance boundary

This artifact remains CANDIDATE / UNACCEPTED until the coordinator's independent verifier confirms fresh native pytest output and authoritative task readback.
