# R29 Source/Owner Trust — Candidate Evidence

Status: CANDIDATE / UNACCEPTED

## Scope and source evidence

- Task: `af-deep-research:v2-r29-source-owner-trust-20261015-r1`
- Target source: `reasoners/deep_research_ext/verification_bridge.py`
- Baseline SHA-256: `9556010defde5e953949192127df0b0a03f877d5c512ae7438448682c588bfd4`
- Candidate SHA-256 after scoped change: `90e8574ff40f22440e4c48c4965fde149d73293c49fb143f21a415d6949e48c4`
- Contract evidence: `docs/architecture/basefive-r14-contracts.json` declares source-bound `GroundedFact(fact_id, source_id, source_sha256)` and r10 verified-source DTOs.

## Functional delta

`validate_fact_ownership` now enforces that a non-empty fact ID maps to the exact integer source ID claimed by the ledger and that the source is in the eligible source set. `verify_ledger_claims` invokes this check before adjudication.

## Focused coverage

The authorized test file contains one positive case and four adversarial negatives:

1. cross-source fact/claim ownership;
2. undeclared source;
3. missing fact identity;
4. boolean source ID masquerading as an integer.

Requested command:

```text
python -m pytest -q tests/test_r29_source_owner_trust.py
```

Execution receipt: NOT RUN in this lane. The available scoped GO runner supports authorized Node/Vitest/tsx files, not Python pytest. This is an infrastructure/tooling limitation, not a PASS.

## Review notes

- No production files outside the authorized write scope were changed.
- No external provider, credential, deployment, commit, or live task state was touched.
- Independent QA/reducer and authoritative CrewSync terminal readback remain required.
