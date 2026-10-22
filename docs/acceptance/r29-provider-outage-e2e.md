# R29 provider-outage E2E acceptance receipt

Status: CANDIDATE / UNACCEPTED

## Scope and source evidence

Target: `af-deep-research` at the coordinator-declared root.

The permitted production interfaces are already present in the current source:

- `skills/search/federated.py` (`d9717cf8acb028dbfb1866902e5fdba873f810bbeccc5e6c45c46d60e63a94a8`) bounds provider count, deduplicates names, runs providers concurrently, preserves successful responses, and raises when all providers fail.
- `reasoners/deep_research_ext/research_run.py` (`87c193a386be13daa2b89dceac6b749a87ae9b47efd84b18bd598017c6e9e8c3`) fences stale source revisions and checkpoint sequence/owner mismatches.
- `reasoners/deep_research_ext/final_verifier.py` (`d812e7f1b4f9b5375c5e0473076c84d8251b2e92e9aa42ae0d84be41f1b16e4f`) converts missing citations, unavailable sources, adjudication errors, and invalid adjudicator identities into unsupported claims rather than PASS.
- `reasoners/deep_research_ext/verified_pipeline.py` (`97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87`) resumes persisted research packages and records provider telemetry.

No production edit was warranted within the exact write scope.

## Focused checks

Command required by the task:

`python -m pytest -q tests/test_r29_provider_outage_e2e.py`

Expected coverage is one positive partial-result path and three adversarial negatives: all providers unavailable, duplicate/capacity overflow, and malformed capacity configuration.

The scoped wave runner exposes only Node/Vitest/tsx execution and cannot execute native Python pytest. Therefore no pytest PASS is claimed until the coordinator runs the exact command in a Python environment.

## Remaining blocker

INFRA BLOCKED: native pytest execution was not available through the authorized runner. This receipt deliberately preserves the distinction between authored tests and unrun runtime evidence; it does not convert an unavailable runner into PASS.

Independent QA must run the exact pytest command, inspect the source hashes above, and perform the required CrewSync terminal readback.
