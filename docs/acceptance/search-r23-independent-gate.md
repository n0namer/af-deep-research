# Search R23 Independent Gate

Status: CANDIDATE / UNACCEPTED

## Scope

Independent QA for final current source. Provider multiplicity is not citation
independence, and mock-only evidence is not accepted.

## Frozen-source evidence

- Baseline commit: e10580c89eac7a4f6efb50c921ae9107ce8ad8dc.
- skills/search/federated.py: SHA-256 b4c5085bdecb9b5c737df4701f664bac495e1a4ebde749d80f0ab3c16b957a7a.
- skills/search/fusion.py: contract-declared SHA-256 c7c0684e8d5d55df099ebf7690bfceafff78e79fe4ad15a6265ecb29a5a5625c; the gate treats a stale declaration as RED.
- reasoners/deep_research_ext/verification_bridge.py: reader receipt SHA-256 9556010defde5e953949192127df0b0a03f877d5c512ae7438448682c588bfd4.
- No secrets, deployment state, live tasks, leases, or production authority changed.

## Gate matrix

| Case | Expected | Evidence |
| --- | --- | --- |
| Four providers, one canonical URL | PASS: one citation, four retrieval providers | test_four_provider_hits_are_one_canonical_citation |
| 429 / 503 with healthy sibling | PASS: healthy fallback only | test_transient_fault_uses_healthy_fallback_without_fake_citation |
| Empty + malformed providers | PASS: fail closed | test_empty_or_malformed_provider_set_fails_closed |
| Stale architecture signature | RED: never accepted | test_stale_architecture_signature_is_red_not_accepted |

Mismatched source-id remains a future defect if a native citation DTO exposes
an identifier distinct from canonical URL; no such DTO was readable in scope.

## Validation

Requested Python command: python -m pytest -q tests/test_search_r21_independent_qa.py tests/test_search_r22_architecture_golden_qa.py

The scoped GO Wave runner supports exact Node/Vitest/tsx targets, not Python
pytest files. Denial is INFRA BLOCKED and must not become PASS.

Required Node command: node --test docs/architecture/search-r16-contract.test.mjs

## Acceptance

Candidate only; independent verifier/reviewer and authoritative CrewSync readback remain required.
