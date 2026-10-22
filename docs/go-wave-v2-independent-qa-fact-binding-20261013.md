# Independent QA — Wave v2 Fact-ID Semantic Binding

**Task:** `af-deep-research:v2-independent-qa-fact-binding-20261013-r1`  
**Attempt:** `attempt-cd666439-6399-4be0-9446-eabfbcf7e415`  
**Session:** `manual-20261013-uniso-af-deep-research-independ-4949be3097227e89`  
**Date:** 2026-10-13  
**Outcome:** **PENDING** — source-level semantic review is PASS, but the authorized test runner rejected the Python test files before execution. This report remains **UNACCEPTED** pending independent coordinator/reviewer acceptance.

## Scope and authority

- **FACT:** This is an independent QA report for the already-produced Wave v2 candidate. No source rewrite, paid request, web request, deployment, commit, or CrewSync/Native state mutation was performed.
- **FACT:** The only changed path is the exact authorized target `docs/go-wave-v2-independent-qa-fact-binding-20261013.md`.
- **FACT:** The target checkout is `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`; the live inventory is Python despite stale TypeScript/Node wording in `AGENTS.md`.
- **SOURCE OF TRUTH:** Existing implementation and tests, plus the prior semantic/provider report `docs/go-wave-v2-a1-semantic-provider-gate-20261011.md`. No competing plan or status artifact was created.

## Candidate snapshot inspected

- `reasoners/deep_research_ext/final_verifier.py` — SHA-256 `d9210579b1a673b1cdc7dbd15f4f0cff660c1e75eedaa4abc54d9a910c00aef1`.
- `tests/test_deep_research_ext.py` — SHA-256 `f230a7700b0573509f1c742d2863d34097770a698e43e3f2caf33b28aac4539d`.
- `tests/test_evaluation_suite.py` — SHA-256 `99e130ababb00ef648669e81ab4f71a5a9da2ac6d9cd61d76aec518464765617`.
- Prior report records the original gap as final-verifier claim-to-assessment identity binding; the current source readback contains the claimed repair and the focused regression.
- Git diff/status could not be independently obtained through the granted scoped interfaces; no Git claim is made beyond the exact source readback hashes above.

## Semantic review verdict

### PASS — identity binding is fail-closed in current source

`reasoners/deep_research_ext/final_verifier.py:151-157` now:

1. Computes `expected_fact_ids` from the actual candidates generated for the current claim.
2. Rejects any empty, unknown, cross-claim, or otherwise mismatched assessment ID.
3. Rejects duplicate assessment IDs.
4. Only after those checks accepts a claim when at least one remaining assessment is both `is_allowed` and `is_source_supported`.

This closes the prior fail-open path: a positive assessment for `D1:S999`, `D2:S1`, or another claim cannot satisfy `D1`, and duplicate/empty IDs cannot pass through the semantic gate.

### PASS — required adversarial regression is present

`tests/test_deep_research_ext.py:480-535` (`test_final_verifier_requires_unique_matching_assessment_fact_ids`) deterministically exercises one claim with candidates `D1:S1` and `D1:S2` and checks that the verifier rejects:

- empty fact ID;
- duplicate `D1:S1` assessment IDs;
- unknown `D1:S999` ID;
- cross-claim `D2:S1` ID;
- mixed valid-for-claim plus unrelated cross-claim IDs.

The same test then supplies only `D1:S2` as a legitimate supported citation and checks `passed is True` with one supported claim. This covers the required “one legitimate citation among candidates” behavior.

### PASS — adjacent fail-closed behavior remains represented

- `tests/test_deep_research_ext.py:440-478` covers uncited material claims and the matching happy path.
- `tests/test_deep_research_ext.py:537-610` covers bounded concurrency, empty adjudicator output (zero support), provider exception, preserved claim order, and fail-closed unsupported reasons.
- `tests/test_deep_research_ext.py:612-650` covers strict-pipeline rejection when final verification fails.
- `tests/test_evaluation_suite.py:36-49`, `:51-63`, `:71-100`, `:103-122`, and `:149-180` cover frozen positive replay, evidence removal, 24-case core replay, holdout replay, and prompt-injection delivery signals. These deterministic tests preserve the semantic/provider separation described in the prior report.

## Validation receipts

### Attempted focused checks

1. `go_wave.run_project_tests({"file":"tests/test_deep_research_ext.py"})`
   - **Result:** `GO_WAVE_NODE_ERROR:test_file_not_allowed`.
   - **Classification:** **INFRA BLOCKED**. The authorized runner is Node/Vitest/tsx-oriented and rejected this Python test file before executing it; this is not a semantic test failure.

2. `go_wave.run_project_tests({"file":"tests/test_evaluation_suite.py"})`
   - **Result:** `GO_WAVE_NODE_ERROR:test_file_not_allowed`.
   - **Classification:** **INFRA BLOCKED** for the same reason.

No Python test engine was available in the granted scoped tool set. Therefore this report does **not** claim pytest PASS, runtime PASS, or a green repository suite.

### Windows and `/app/main.py` / `agentfield` separation

- **FACT:** No Windows runtime failure or `agentfield` import failure was observed in this attempt because both test invocations were rejected before test collection or import.
- **FACT:** The existing test source contains an environment-specific AST check that reads `/app/main.py`; on a Windows checkout, a later pytest run may fail at that path even when the semantic verifier is correct. That would be a test-environment/fixture-path issue, not evidence that fact-ID binding is semantically wrong.
- **FACT:** Any later `agentfield` import error during collection should likewise be reported as a dependency/environment blocker unless it reaches the verifier assertions. It was not reproduced here and is not counted as a semantic failure.

## DoD comparison

| Criterion | Independent result | Evidence / risk |
|---|---|---|
| No source rewrite | PASS | Only authorized report path written; source inspected read-only. |
| Mismatched positive ID fails closed | PASS by source/test inspection; runtime PENDING | `final_verifier.py:151-157`; focused regression at `test_deep_research_ext.py:480-535`. |
| Missing/duplicate/unknown/cross-claim IDs fail | PASS by source/test inspection; runtime PENDING | Five invalid assessment variants in the focused regression. |
| One valid citation among candidates can support | PASS by source/test inspection; runtime PENDING | Final `D1:S2` case in focused regression. |
| Empty adjudication result and provider error fail closed | PASS by source/test inspection; runtime PENDING | Concurrency/provider test at `test_deep_research_ext.py:537-610`. |
| Frozen semantic corpus remains fail-closed | PENDING runtime | Positive and evidence-removal tests are present in `tests/test_evaluation_suite.py`; runner rejected the file. |
| Provider success is not semantic proof | PASS by design inspection; runtime PENDING | Prior report separates telemetry; no provider/web call made here. |
| Independent acceptance | UNACCEPTED | Coordinator and independent reviewer own acceptance; this worker cannot self-accept. |

## Uncovered or residual cases

- **PENDING runtime proof:** The Python-focused and evaluation suites need execution under an environment with pytest and project dependencies. The current authorized runner cannot execute them.
- **Narrow boundary coverage:** The current regression does not directly exercise duplicate citation markers in the input claim, malformed non-integer citation IDs, or a malformed adjudicator object whose `assessments` field is absent/non-list. These are outside the delivered fact-ID repair and should be considered only if the public input contract permits them.
- **No live provider proof:** No paid/web/provider request was allowed or made. Provider transport success remains separate from semantic acceptance by contract and source structure, not by a live call in this attempt.

## Narrow same-owner repair DoD

No source repair is requested from this independent QA lane. If a same-owner repair is later authorized, it should remain limited to:

1. Run `pytest -q tests/test_deep_research_ext.py tests/test_evaluation_suite.py` in a Python-capable environment with dependencies installed.
2. If collection fails on `/app/main.py`, replace only that test fixture path with a repository-root-resolved path in the test owner’s scope, or document the environment mapping without weakening semantic assertions.
3. If collection fails on `agentfield`, install/use the repository-pinned dependency or record the exact dependency blocker; do not change fact-ID semantics to accommodate it.
4. Re-run the focused final-verifier cases and the evaluation suite, recording counts and first meaningful failures.
5. Preserve the current identity invariant: expected candidate IDs must be exact, assessment IDs must be unique and known, and one matching allowed/source-supported assessment may pass.

## Final verdict

**PENDING / source semantic review PASS, runtime evidence unavailable.** The current implementation and adversarial regression address the previously reported fail-open fact-ID binding defect without an observed semantic regression. The candidate remains **UNACCEPTED** until an authorized Python test environment or independent verifier supplies executable test evidence and the coordinator performs the authoritative acceptance/readback.
