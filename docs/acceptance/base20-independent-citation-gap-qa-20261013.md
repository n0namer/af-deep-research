# Base20 Independent Citation Gap QA

Status: BLOCKED / independent acceptance required
Recorded date: 2026-10-13 (scoped runner does not expose an execution clock)

## Scope and source identity

- Project: `af-deep-research`
- Task: `af-deep-research:v2-base20-qa-citation-gap-20261013-r1`
- Attempt: `attempt-0aa7f78e-66b7-4225-a895-7b0de14adfe3`
- Session: `manual-20261013-base20-independent-qa-af-deep-r-83f8cb317931410a`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- BMad gate: independent adversarial QA after two candidate producers; no new production pipeline was introduced.
- `reasoners/deep_research_ext/gap_research.py`: SHA-256 `0e268ac8c179938f4b2ddc37970bb89fd78438e23845b39db66f8ead1134b1fd`
- `reasoners/deep_research_ext/verification_bridge.py`: SHA-256 `aad1f5c7a85b26a0c7a3449e9b12df5b276f8b50c264e18688195326f12db270`
- `reasoners/deep_research_ext/final_verifier.py`: SHA-256 `d9210579b1a673b1cdc7dbd15f4f0cff660c1e75eedaa4abc54d9a910c00aef1`
- `tests/test_base20_independent_citation_gap_qa.py`: SHA-256 `370341a1288601fe7420050cb7e38696f20493848403cebc1008944600c0f52b`
- Prior producer test identities: `tests/test_gap_recovery_goal_wave.py` SHA-256 `a396edd446013cc495a042630891c980a457d0a3abce5eb02ba3b5a8bd9cde3e`; `tests/test_citation_entailment_goal_wave.py` SHA-256 `22fb7a69e16638b758837c70655f6269e2b8fcf9361d2a689cf3f9085a8d9b2e`.

## Independent frozen oracle

`tests/test_base20_independent_citation_gap_qa.py` composes the existing gap round and final verifier with a deterministic offline primary source:

- frozen citation ID: `2`
- frozen URL: `https://frozen.example/rfc-primary`
- frozen content identity: `sha256:base20-primary-v1`
- frozen evidence timestamp: `2026-10-13T00:00:00Z`

The positive path starts with unresolved `R1`, performs exactly one targeted `VerifiedGap_R1` retrieval under `source_budget=1`, admits the new source/evidence pair, records one new verified claim, and passes final verification only when `D1` is matched to the exact returned citation fact ID `D1:S2`.

## PASS / RED conditions

| Condition | Expected result | Oracle coverage |
| --- | --- | --- |
| `ACCEPT_SCOPED` candidate behavior | exact source identity, admitted targeted retrieval, `D1:S2`, and one supported final claim | `test_e2e_gap_retrieval_to_exact_citation_verification` |
| RED: forged source identity | ledger URL/source ID/content hash mismatch leaves claim unverified | `test_identity_fact_id_and_provider_timeout_fail_closed_to_abstention` |
| RED: cross-claim fact ID | returned `D2:S2` cannot verify `D1` | same test |
| RED: partial retrieval | URL-less, instruction-bearing, and duplicate-source payloads are skipped; no claim becomes verified | `test_gap_round_rejects_forged_injected_or_identityless_sources_and_stays_partial` |
| RED: prompt injection | `Ignore previous instructions ...` is rejected before evidence construction | same test |
| RED: missing citation/source identity | no citation produces `material_claim_has_no_citation` abstention | `test_final_verifier_abstains_when_partial_retrieval_has_no_verifiable_citation` |
| RED: provider timeout | final verifier emits `claim_verification_failed_closed`, with no supported claim | `test_identity_fact_id_and_provider_timeout_fail_closed_to_abstention` |

## Focused execution receipt

- Command attempted: `python -m pytest -q tests/test_base20_independent_citation_gap_qa.py`
- Scoped invocation: `go_wave.run_project_tests({file:"tests/test_base20_independent_citation_gap_qa.py"})`
- Result: `BLOCKED` before test execution with exact error `GO_WAVE_NODE_ERROR:test_file_not_allowed`.
- No identical retry was made. The requested affected regression command was not invoked because this scoped runner rejects Python targets by file type; retrying another Python file would not supply independent evidence.

## Review and remaining limitation

No bounded source repair is indicated: the inspected code already fails closed for missing/ambiguous source identity, invalid fact IDs, provider errors, and uncited material claims. The QA delta is test-only and does not self-accept either producer.

The frozen oracle cannot prove live provider availability, live retrieval quality, ownership/terminal status of the producer tasks, or source stability after the recorded source SHA values change. An independent reviewer must first confirm the three source hashes above remain unchanged and that both producer candidates are terminal, then run:

```text
python -m pytest -q tests/test_base20_independent_citation_gap_qa.py
python -m pytest -q tests/test_gap_recovery_goal_wave.py tests/test_citation_entailment_goal_wave.py
```

If source SHA, terminal status, runner availability, or ownership is ambiguous, the result remains `BLOCKED`; it must not be promoted to acceptance.
