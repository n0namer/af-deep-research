# R29 Abstention E2E Evidence

Status: CANDIDATE / UNACCEPTED

## Scope and source evidence

This bounded regression targets the production verify_final_document interface in
reasoners/deep_research_ext/final_verifier.py. The test imports and executes that
function, while deterministic callbacks stand in only for external AI extraction and
adjudication. Source lookup, citation identity checks, candidate construction, and
closed abstention decisions are production behavior.

The source receipt asserted by the test is:

- final_verifier.py SHA-256: d812e7f1b4f9b5375c5e0473076c84d8251b2e92e9aa42ae0d84be41f1b16e4f
- Contract: VerifiedSourceReport / ResearchRun versions remain read-only inputs; no production file was changed.

## Definition of done

- Positive real verifier path accepts a source-backed claim.
- Four adversarial negatives abstain: no citation, missing cited source, duplicate citation IDs, and adjudication failure.
- No unavailable runner is converted to PASS.
- The test remains CANDIDATE / UNACCEPTED pending independent QA and CrewSync readback.

## Validation

Requested command:

python -m pytest -q tests/test_r29_abstention_e2e.py

The actual exit status and output must be recorded by the authorized runner. A blocked
or unavailable Python environment is infrastructure evidence, not a passing result.
