# Releasegate Independent C4 Fan-In QA — 2026-10-13

## Verdict

**RED / BLOCKED — not `ACCEPT_SCOPED`.** The reviewed artifacts define a coherent offline release-gate candidate, but this independent lane obtained no executable PASS. The native-evidence suite was blocked before pytest collection because the checkout has no regular local `.venv`; the restart/resume suite was denied by the scoped runner as outside this task's executable test scope. No live provider receipt, native AgentField process evidence, authoritative CrewSync terminal readback, or terminal reducer result is present in the permitted evidence.

- Task: `af-deep-research:v2-releasegate-c4-independent-fanin-20261013-r1`
- Attempt: `attempt-d68aad08-4002-4a0c-9dcb-2b0f01743b0e`
- Session: `manual-20261013-releasegate-c4-fanin-independen-99ab20a4a79e01ee`
- Reviewed hyperwave: `20261013-native-releasegate-hyperwave-r1-af-deep-research`
- Authority: independent QA only; no source ownership, CrewSync mutation, release, deployment, provider call, or self-acceptance.

## Evidence State

### Facts

- `tests/test_releasegate_native_evidence_20261013.py` has SHA-256 `75171c60b92236c6fee6b7e47facc10af659e90c5796ed381250055b18c00b54` in the scoped reader and in its producer acceptance note.
- `tests/test_releasegate_restart_resume_20261013.py` has SHA-256 `850e3c0b97c886332bac8089c7e2a9dcd425f48186e25e4db6bdb16bbeab96cc` in the scoped reader and in its producer acceptance note.
- The native-evidence test embeds exact SHA-256 bindings for `verified_pipeline.py`, `gap_research.py`, `evidence_ledger.py`, `final_verifier.py`, and `research_run.py`.
- The producer notes report both release-gate artifacts as `CANDIDATE / UNACCEPTED` or `INFRA BLOCKED / UNACCEPTED`; neither reports independent acceptance.
- The trusted worker footer for this lane reports `thread_state: THREAD_PENDING` and requires `acceptance.level: UNACCEPTED`.
- The deterministic tests use controlled fixtures, monkeypatches, temporary filesystem storage, and synthetic identity tuples. The optional live test is skipped unless explicitly admitted.

### Constraint

The read scope excludes production source files and raw CrewSync/provider logs. Therefore this lane can inspect the frozen hashes, imports, calls, DTO construction, assertions, and producer receipts, but cannot independently recompute production source hashes or authenticate a provider/worker terminal receipt against raw runtime state.

### Assumption

The embedded source hashes identify the intended producer snapshot. This assumption is not promoted to a verified fact because the authorized runner could not execute the hash-binding test and the source files were outside this lane's read scope.

## Compact C4 Ledger

### C4 Context

| Actor / system | Interaction | Evidence-grounded contract | Trust boundary |
| --- | --- | --- | --- |
| Research caller | Supplies query and strictness knobs | `UPSTREAM` includes `query`, `mode`, loop/gap limits, parallel streams, `source_strictness`, evidence style, analysis depth, model, and API key | User/config input enters orchestration |
| Verified research system | Produces a `DocumentResponse` or fail-closed partial/evidence-only response | `execute_verified_pipeline(...)` is the central entrypoint used by both suites | Controls transition from retrieved material to deliverable claims |
| Search/model providers | Supply source packages, gap results, extracted claims, and adjudications | Callbacks `prepare_research_package`, `stream_executor`, `ai_call`, and optional live application adapters | External/untrusted data and model output must be admitted and verified |
| AgentField/native worker identity | Binds original and replay runs | `current_agentfield_identity()` is treated as `(current_run_id, replay_source_run_id)` by the restart suite | Coordination identity is distinct from evidence correctness and terminal acceptance |
| Release coordinator/reducer | Decides terminal release status | Not implemented or invoked by these tests | Acceptance remains outside the candidate worker |

### C4 Containers

| Container | Entrypoint / boundary | Responsibility evidenced by tests |
| --- | --- | --- |
| Verified pipeline | `verified_pipeline.execute_verified_pipeline(...)` | Orchestrates retrieval, ledger verification, gap handling, synthesis, final verification, checkpointing, and terminal mode selection |
| Durable research-run store | `ResearchRunStore`, `begin_research_run`, `checkpoint_research_run`, `resume_research_run` | Persists stage/payload, replays cached packages, fences source revision, exposes terminal resume state |
| Gap research | `gap_research.GapQueryPlan`, `GapQuery` and pipeline `stream_executor` | Converts unresolved requirement IDs into bounded queries and merges admissible new evidence |
| Evidence/final verification | `verify_final_document(...)`, `DraftClaimList`, `AIAssessmentList` | Requires cited material claims and exact assessment identities; rejects unknown/non-entailing facts |
| Document generation | `generate_document_from_package` returning `DocumentResponse` | Produces versioned report content only after the applicable evidence gate |
| Provider telemetry | `record_provider_event`, `provider_events_snapshot`, `reset_provider_events` | Carries operation, status, latency, model, and call ID receipts in the controlled suite |

### C4 Components and Interfaces

| Component | Observed API / DTO signature | Contract observed in scoped evidence |
| --- | --- | --- |
| Answer contract builder | `build_answer_contract(query, source_strictness=...)` | Produces the contract later updated with typed `ResearchRequirement` values |
| Method selector | `select_methodology(contract)` | Produces `ExtensionTrace.method_selection` for pipeline execution |
| Requirement DTO | `ResearchRequirement(requirement_id, question, required_source_class)` | Requirement IDs such as `R1` and `R2` are the coverage and abstention keys |
| Trace DTO | `ExtensionTrace(answer_contract, method_selection)` | Carries the typed contract into pipeline execution |
| Pipeline | `execute_verified_pipeline(trace, prepare_research_package, generate_document_from_package, upstream_kwargs, ai_call, run_store, research_run, stream_executor=...)` | Accepts injected adapters but owns the verified/partial/rejected delivery mode |
| Run start/replay | `begin_research_run(query, store, source_revision=...)` | Creates a run or replays from AgentField-provided source identity; stale revision raises `StaleResearchRunError` |
| Checkpoint | `checkpoint_research_run(store, run, stage, source_revision=..., source_ids=..., payload=...)` | Persists stage history, package, evidence state, semantic snapshot, and terminal mode |
| Resume | `resume_research_run(store, run_id, source_revision=...)` | Returns the durable run plus a plan containing `next_stage`, terminal state, and missing gaps |
| Final verifier | `verify_final_document(document_package, research_package, source_strictness, ai_call, claim_extractor=..., adjudicator=...)` | Fails closed for no citation or unknown/non-entailing `fact_id` |
| Draft DTO | `DraftClaim(claim_id, text, citation_ids)` / `DraftClaimList(claims)` | Citation IDs connect generated claims to source notes |
| Assessment DTO | `AIAssessment(fact_id, is_allowed, is_source_supported, is_verified, disagreement_score)` / list wrapper | Versioned fact handshake uses IDs such as `D1:S1`; unknown `D1:S999` is rejected |
| Document DTO | `DocumentResponse(mode, version, research_package, metadata)` | Test versions are `releasegate-native-v1` and `releasegate-v1` |

## Versioned Handshake and Trust Boundaries

1. **Source snapshot handshake:** production implementation is represented by frozen SHA-256 values; the native test is intended to fail when those files drift. This handshake was inspected but not executed here.
2. **Run compatibility handshake:** `source_revision` values fence persisted/replayed state. A mismatch from `releasegate-source-v1` to `releasegate-source-v2` must raise `StaleResearchRunError` before a new replay file is created.
3. **AgentField replay handshake:** synthetic `current_agentfield_identity()` values provide current and replay-source IDs. Tests show the intended dependency but do not prove a live AgentField process, distributed lease, fencing epoch, or crash recovery.
4. **Evidence identity handshake:** requirements use `R*`, draft claims use `D*`, citations use integer IDs, and adjudications use compound `D*:S*` fact IDs. Unknown positive assessments must not be silently accepted.
5. **Delivery handshake:** terminal payloads distinguish `verified_document`, `programmatic_partial_abstention`, and `post_generation_rejected`; `DocumentResponse.version` identifies the test document contract.
6. **Provider boundary:** deterministic provider events are manually recorded by the fixture and controlled AI callbacks return typed values. They are useful contract tests, not physical evidence that real search/model adapters executed.
7. **Filesystem boundary:** `ResearchRunStore` is exercised only with pytest temporary paths. This supports local atomic/replay semantics, not distributed durability.

## Focused Check Receipts

### Native Evidence Suite

Requested:

```text
go_wave.run_project_tests({"file":"tests/test_releasegate_native_evidence_20261013.py"})
```

Observed:

```json
{
  "status": "BLOCKED",
  "code": "PYTHON_VENV_UNAVAILABLE",
  "test": "tests/test_releasegate_native_evidence_20261013.py",
  "engine": "python:pytest",
  "source_identity_sha256": "75171c60b92236c6fee6b7e47facc10af659e90c5796ed381250055b18c00b54",
  "exit_code": null,
  "stderr": "A regular local .venv Python executable is required."
}
```

Classification: infrastructure blocked before collection. Positive full-cycle, negative unsafe-source abstention, restart reuse, missing-citation rejection, unknown-fact rejection, and optional live-provider behavior all remain unexecuted in this lane. Zero PASS is recorded.

### Restart/Resume Suite

Requested:

```text
go_wave.run_project_tests({"file":"tests/test_releasegate_restart_resume_20261013.py"})
```

Observed:

```text
GO_WAVE_NODE_ERROR:test_outside_task_write_scope
```

Classification: runner authorization/infrastructure denial. The call was not retried. Positive replay, stale-revision rejection, ambiguous fact-ID rejection, and partial-abstention replay remain unexecuted in this lane. Zero PASS is recorded.

## Adversarial Findings

1. No focused suite reached pytest collection, so the fan-in has no fresh runtime success evidence.
2. The restart/resume test is readable but not executable under this task's runner admission, preventing independent reproduction of its producer claim.
3. The production source hashes were copied into a test and producer notes, but this lane could not independently recompute them from source or execute the hash assertion.
4. The native hash gate covers five modules but not every imported contract surface, including `task_contract`, `methodology`, `models`, `provider_telemetry`, `synthesis_guard`, and `doc_generation_pipeline`.
5. Both suites monkeypatch claim-to-requirement mapping and ledger verification, so passing them would not by itself prove those native components end to end.
6. Provider telemetry in the deterministic full-cycle case is manually emitted by test fixtures; it is not a physical receipt from the application search/model adapters.
7. The optional live-provider test has no admitted execution receipt. A default skip cannot support a native-provider GREEN claim.
8. AgentField integration is represented by monkeypatched identity tuples. There is no process kill, lease/fencing proof, cross-process recovery, or authoritative worker lifecycle receipt.
9. Interruption is simulated by raising `RuntimeError` around checkpoint flow. This does not prove durability under abrupt process termination, partial filesystem writes, or host restart.
10. The two suites use different source revision labels (`releasegate-src-v1` and `releasegate-source-v1`), with no separately reviewed shared version schema establishing intended interoperability.
11. Producer notes describe expected pass counts, but expected output is not runtime evidence and cannot be elevated to PASS.
12. The permitted evidence contains no authoritative CrewSync terminal readback for the reviewed producer tasks and no terminal reducer result for the hyperwave.
13. Controlled URLs and frozen packages prove deterministic behavior only; they do not establish real source retrieval, content freshness, or provider authentication.
14. A terminal `completed` checkpoint is application state, not release acceptance; the tests correctly separate these concepts, but no external acceptance receipt closes the gap.

## Acceptance Comparison

| Criterion | Result | Evidence |
| --- | --- | --- |
| Independent source SHA and physical provider/worker receipt inspected | **PARTIAL / BLOCKED** | Frozen SHA bindings and producer runner receipts inspected; no independent source recomputation, physical live-provider receipt, or authoritative worker terminal readback available |
| C4 context/container/component and DTO contract grounded in actual source | **PASS within read scope** | Imports, calls, typed DTO construction, assertions, and producer source notes define the ledger above; no invented production API is asserted |
| Reproducible positive and negative check, or explicit infrastructure block | **BLOCKED, correctly classified** | `PYTHON_VENV_UNAVAILABLE` and `test_outside_task_write_scope`; zero PASS |
| Typed QA verdict with scoped repair routes and no source writes | **PASS** | This document is the only write and records `RED / BLOCKED` |
| No full GREEN without native E2E and terminal reducer | **PASS** | No GREEN, ACCEPTED, or terminal claim is made |

## Narrow Sticky-Owner Repair and Replan

1. **Infrastructure owner:** provision the repository's regular local `.venv` with locked dependencies, then rerun `tests/test_releasegate_native_evidence_20261013.py` through the authorized scoped adapter. Do not refresh source hashes unless a reviewed source change explains the drift.
2. **Coordinator/test-scope owner:** authorize `tests/test_releasegate_restart_resume_20261013.py` for the same independent verifier or run it in the original sticky QA thread. Do not create a duplicate implementation task.
3. **Original native-evidence owner, only on semantic failure:** repair the smallest failing behavior in the already-owned module, preserving strict source admission, exact `fact_id` validation, source-revision fencing, and programmatic abstention.
4. **Original restart/resume owner, only on semantic failure:** repair replay identity, cached-package reuse, checkpoint durability, or final-verification rejection only where the focused failure proves a defect.
5. **Provider/integration gate:** if full native E2E is required, execute an explicitly admitted search/model run and bind its provider call IDs, source snapshot, output, and failure state. Do not treat controlled fixtures or a skip as provider evidence.
6. **Reducer/coordinator:** obtain authoritative terminal readback for producer threads and run the terminal reducer after focused and affected regressions pass. Only that separate authority may decide `ACCEPT_SCOPED` or broader release status.

## Final QA Boundary

This artifact is a source-backed independent review candidate, not acceptance. The current verdict remains **RED / BLOCKED** until the two focused suites execute under authorized infrastructure, any affected-only failures are repaired by original sticky owners, physical provider/worker evidence is supplied for claims that require it, and the independent terminal reducer completes against authoritative CrewSync state.
