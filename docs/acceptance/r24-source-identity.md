# R24 Source Identity Boundary — 2026-10-15

Status: INFRASTRUCTURE BLOCKED / UNACCEPTED. No runtime PASS or reproduced PRODUCT_RED is claimed.

## Authority and existing gate

- Task: `af-deep-research:v2-r24-source-id-boundary-20261015-r2`.
- Attempt: `attempt-7da82671-7875-457e-8018-71d832670a17`.
- Crew session: `manual-20261015-basefive-r24b-20owners-af-deep--8daa4130db591cac`.
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`, not the canonical BMAD-MNNZ skill repository.
- Prelaunch Git identity: `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`; coordinator supplied, not independently queried.
- Exclusive writes: `tests/test_r24_source_id_boundary.py` and this report. Both exact targets initially returned `GO_WAVE_NODE_ERROR:ENOENT`; both were created through the authorized writer.
- Existing BMad source of truth: `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md`. Stage: implementation-evidence recovery, before independent QA/reducer acceptance. Its missing original C4 producer/QA/interface/native-E2E gates remain unmet.

FACT: BMad Help, Quick Dev and verification-before-completion were loaded through scoped interfaces. Quick Dev clarify/route and planning instructions were read. Configuration/customization scripts, Git branch/status/history, graph MCP, and out-of-scope source inspection are unavailable under this lane's interfaces/authority. General workflow steps requiring those operations, additional specification writes or subagents were not performed; full BMad workflow completion is not claimed. No competing plan or tracker was introduced.

## Value, current state and bounded design

Value: provide independent executable assertions at the existing grounded-report trust boundary, including strict document rejection and a real child-process termination/restart probe, without replacing production validation or persistence.

FACT: The r14 contract and existing acceptance reports already describe grounded report build/persist/resume, owner/source fences and effect replay. The mechanism is not new. The new QA file tests that existing interface; it does not implement another validator or store.

FACT: `docs/acceptance/basefive-r16-source-citation-report.md` reports that document citation/claim support is not validated at grounded build/persistence and that the named durable report store is instance-local memory. These are attributed prior inspection findings, not fresh source inspection or runtime findings from this lane.

HYPOTHESIS: strict foreign-citation, foreign-fact, unsupported-document and process-restart assertions will expose product defects. The current environment prevented testing this hypothesis.

Local DoD: bind actual source bytes to the C4 contract; execute a valid positive and at least two document/identity negatives; prove no receipt/effect on rejected inputs, owner/source fencing and replay isolation; terminate and restart real Python processes against the production store; run affected regressions; self-review and publish one typed UNACCEPTED result for independent QA/reduction. Runtime DoD is NOT met.

Smallest compatible move: create only the authorized native QA suite and evidence report. Production modules, dependencies, live state and existing tests remain unchanged.

## Source-bound interfaces and owners

The scoped contract reader returned SHA-256 `7d81581ed610a64337712806f7fb2edf4d6fc85d981cbfbdc692d267e79afc66` for `docs/architecture/basefive-r14-contracts.json`.

| Contract evidence | Path / symbol and owner | Limitation |
| --- | --- | --- |
| Grounded report path | `reasoners/deep_research_ext/verified_pipeline.py`: `build_grounded_verified_report` constructs `VerifiedSourceReport` with `GroundedFact`; `persist_grounded_verified_report` calls revision replay and store effect recording; `resume_grounded_verified_report` checks owner/source identity. | Contract-observed path, not freshly traced source or executed calls in this attempt. |
| Current source pin | Contract records pipeline SHA-256 `97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87`; DTO version `r10`. | Test hashes actual bytes and requires exact agreement when executed; it has not run. |
| Report persistence owner | Production `DurableVerifiedSourceReportStore`; candidate `source_owner` and caller `owner` are checked independently by negative cases. | `_effects` observations are local marker assertions, not external delivery receipts. No human production repair owner is invented. |
| Distinct asynchronous path | `execute_verified_pipeline` awaits research/generation callbacks, checkpoints through `research_run.py`, and optionally persists a legacy-default report. | The contract explicitly distinguishes this from the separate grounded API. This suite is not full asynchronous pipeline or native CrewSync task-to-result acceptance. |
| Restart surface | Grounded report store, not the filesystem `ResearchRunStore` checkpoint adapter. | Checkpoint durability cannot be substituted for report/effect durability. |

FACT: The r14 contract records missing Graphify grounded symbols, stale line positions and absent graph source hashes/signatures. No graph tool is exposed in this lane. ArchSteer Python names/imports are not proof of runtime coverage; no Go or Structurizr coverage is claimed. Original C4 source/producer/QA readbacks still require independent evidence.

## Executable QA artifact

`tests/test_r24_source_id_boundary.py` contains ten cases by static parametrization count, not collected/passed count:

1. Require the actual pipeline SHA, r14 source pin, baseline revision and DTO version to agree.
2. Persist an exact fact/source/citation fixture, preserve source/owner/DTO identity and caller-payload isolation, replay without a second local effect marker, and resume in the same process.
3. Reject foreign document source citations before receipt/effect creation.
4. Reject foreign citation fact IDs before receipt/effect creation.
5. Reject a contradictory unsupported document while retaining the original evidence and grounded facts.
6–7. Reject candidate-owner and caller-owner mismatches independently, leaving no stored report/effect.
8–9. Reject resume with a foreign owner or different source hash without changing the canonical receipt/effects.
10. Use two fresh Python child processes in one temporary working directory: first persist a real report/effect then terminate with `os._exit(73)` after a flushed commit marker; second resume via the real production store and require preserved receipt/owner/hash and no duplicate local effect on replay. Both exit codes and output markers are asserted with captured stderr on failure.

ASSUMPTION requiring independent review: `payload.document`, `payload.citations` and `payload.evidence` express the requested document trust boundary. The r14 DTO exposes an unrestricted payload dictionary, not a semantic citation schema. These strict acceptance expectations must not be mistaken for an already implemented schema. No fixture-side validator or fabricated trusted production evidence is inserted to make them green.

The restart probe does not serialize or restore a fixture store, reuse the parent object, share an in-memory instance, or claim that a cancellation equals process death. The current default store has no backing locator in the inspected contract; inability to resume is an unmet product expectation, not permission to add a fake durable adapter. A crash is injected after successful persistence, not at every possible write boundary. The probe tests local marker continuity, not exactly-once external effects. Child execution is bounded to 20 seconds each, uses the runner's Python without a shell and makes no network/live-task calls.

## Exact native validation receipt

Requested validation:

```text
python -m pytest -q -p no:cacheprovider tests/test_r24_source_id_boundary.py
```

Actual authorized invocation:

```text
go_wave.run_project_tests({"file":"tests/test_r24_source_id_boundary.py"})
```

Actual response:

```json
{"status":"BLOCKED","code":"PYTHON_VENV_UNAVAILABLE","test":"tests/test_r24_source_id_boundary.py","engine":"python:pytest","source_identity_sha256":"fb49c9719a76297aea3b7b28e56f2bca85c38109b6b62d6d64bc007827ab21a0","exit_code":null,"signal":null,"error":null,"duration_limit_ms":120000,"output_truncated":false,"stdout":"","stderr":"A regular local .venv Python executable is required."}
```

FACT: The receipt hashes the QA file, not the production source. No pytest process, collection, imports, subprocess probe, source hash assertion or test body ran. The runner did not expose a launched argv, so the requested CLI flags are not represented as observed execution. No zero exit, product failure or test PASS count exists. One invocation was made; the identical environment failure was not retried and no alternate runner bypass was attempted.

## Acceptance and regression matrix

| Required evidence | Status | Receipt / gap |
| --- | --- | --- |
| Existing contract call-paths/owners cited | Static evidence only | r14 contract and attributed prior reports above; direct production source is outside read scope. |
| Fresh actual source SHA | BLOCKED | Executable pin assertion could not run. |
| Native positive and exact successful command/exit | BLOCKED | `PYTHON_VENV_UNAVAILABLE`, exit null. |
| At least two negatives with unchanged state/effects | BLOCKED | Strict cases written; no execution. |
| Real process restart without foreign owner/repeated local marker | BLOCKED | Child-process probe written; no execution. |
| Affected regression | BLOCKED | Included identity, owner/source resume fence, deep-copy and same-process replay checks could not run. Other existing test files have no authorized test scope here. |
| Preserve RED without weakening fixtures | Preserved infrastructure receipt | No skip, xfail, synthetic validator, persistence replacement, relaxed expectation or production edit. No reproduced PRODUCT_RED yet. |
| Independent QA/reducer | Required | Typed publication is evidence transport only, not acceptance. |

## Self-review and resumable handoff

- Only the two exact authorized paths were written. Source/contract hashes are attributed correctly; fresh production source hashing is not claimed.
- Tests reuse public production functions and DTOs. Private `_effects` is observed only for local marker counts and must be reviewed against actual source once access is authorized.
- Strict rejection assertions include unchanged state/effects even on failure; fixture trust checks do not preempt production behavior.
- No dependency install, shell execution, claims, task administration, credentials, external sends, deployment or acceptance action occurred.
- Test syntax/import/API compatibility and actual behavior remain unverified. Direct source inspection and Git diff/status were unavailable; write-tool receipts and authored content support the scope review only.
- Initial useful-work estimate: 10–15 minutes, including inspection, test authoring, runtime diagnosis and evidence; actual elapsed time is not exposed by the scoped tools. Infrastructure stopped the verification milestone; no artificial delay or redundant execution was added.

Next action: operator supplies a regular target-local `.venv` Python executable through authorized environment maintenance, then resumes this same sticky task context. Execute the exact requested command above through the authorized runner, inspect imports/API/fixture compatibility, preserve genuine PRODUCT_RED and repair only these owned QA artifacts. If citation enforcement or durable report/effect backing needs production changes, obtain explicit coordinator authorization for `reasoners/deep_research_ext/verified_pipeline.py`; do not mask defects with fixtures. Independent reviewer and reducer must consume actual source-bound runtime output and original C4 producer/QA/native-E2E receipts before acceptance.

Publication for this attempt is one typed `BLOCKED / UNACCEPTED` result. Exact transport response/readback is preserved in the final handoff after publication; transport verification is not product acceptance.
