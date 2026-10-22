# Search R27 epistemic release — independent QA candidate

Status: CANDIDATE / UNACCEPTED

## Authority and source identity

- Task: `af-deep-research:v2-r27-epistemic-release-20261015-r1`
- Attempt: `attempt-343a400b-6153-4b8d-8eec-53ad8016db41`
- Session: `manual-20261015-adversarial-qa-r27-af-deep-rese-c5037fa2b134f1d6`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Prelaunch git fingerprint: `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc` (coordinator-supplied; the focused test also records the live `git rev-parse HEAD` format).
- Acceptance authority: independent verifier/reviewer and authoritative CrewSync terminal readback.
- This report and test do not mutate product code, providers, tokens, sends, CrewSync tasks, leases, locks, or release state.

## Scope and DoD

The new gate tests the requested evidence boundaries:

| Gate | Expected result |
| --- | --- |
| Primary citation identity | Canonical URL, primary class, and content digest are stable |
| Derivative non-independence | A derivative sharing an upstream provenance group does not add independent primary evidence |
| Provider 503 failover | A 503 is skipped when a later provider is healthy |
| Missing golden answer | Missing expected answer remains BLOCKED despite source/provider evidence |

A green test result means only that these local gate predicates hold. It is not product acceptance and does not convert a worker exit into a CrewSync done state.

## Audit of r21–r26 evidence

The permitted prior artifacts consistently preserve the distinction between:

- a process/worker exit;
- a typed `go-core.worker-result.v1` candidate receipt;
- independent QA evidence; and
- authoritative CrewSync acceptance/readback.

The r26 reconciliation artifact states that missing independent QA, self-approved results, and process success without a typed result are BLOCKED. The c4 reducer artifact likewise records missing runtime evidence as BLOCKED and keeps the candidate UNACCEPTED. Those records are evidence quality and routing decisions, not acceptance.

## Affected-only replan

1. Run the new focused pytest under the authorized Python environment and retain its exact exit/count output.
2. If a gate fails, repair only `tests/test_search_r27_epistemic_gate.py`; do not alter search, evaluation, provider, or orchestration production code.
3. Have an independent verifier review this test/report and the live git fingerprint.
4. Preserve `CANDIDATE / UNACCEPTED` until the original typed result has independent QA and authoritative CrewSync readback.

## Verification receipt

Requested command:

```text
python -m pytest -q tests/test_search_r27_epistemic_gate.py
```

The worker will record the actual scoped runner result here; no result is inferred from mocks, source inspection, or process exit. The test uses the real `skills.search.fusion.canonicalize_url` import and probes the repository's current git fingerprint at runtime.

## Adversarial self-review

- The test does not treat a provider 503 as success without a later healthy provider.
- Derivative copies are excluded by provenance group, even when their URLs differ.
- Missing golden output blocks despite otherwise sufficient local evidence.
- URL normalization and content hashing are explicit parts of citation identity.
- No assertion claims CrewSync completion, acceptance, or GREEN.
- The report distinguishes source-backed observations from runtime checks.
- No product files, live task state, leases, locks, credentials, or network calls are changed.
- The focused check has five native pytest cases: two positive paths (identity/failover) and three negative/boundary cases (derivative exclusion, unavailable provider, missing golden answer).
- A coordinator-supplied SHA is labeled as supplied; the test records the live SHA shape independently.
- Any unavailable Python runner must remain INFRA BLOCKED, never PASS.

## Remaining

- Independent verifier/reviewer and authoritative CrewSync terminal readback are still required.
- Actual pytest output depends on the scoped Python runner and environment.
