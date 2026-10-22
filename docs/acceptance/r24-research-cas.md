# R24 Research Checkpoint CAS Concurrency Fence

Date: 2026-10-15
Outcome: **INFRA BLOCKED / UNACCEPTED**. The runtime Definition of Done is not met. No product PASS, PRODUCT_RED, acceptance or terminal completion is claimed.

## Authority and BMad gate

- Task: `af-deep-research:v2-r24-cas-concurrency-fence-20261015-r2`
- Attempt: `attempt-309786b9-0563-478d-9c5b-a9c76b9c1be8`
- Session: `manual-20261015-basefive-r24b-20owners-af-deep--b8f634028f399f60`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`, not BMAD-MNNZ.
- Coordinator-supplied baseline Git: `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`.
- Coordinator-supplied manifest SHA-256: `884b643fd03fee1478b03283d2703a325f4c1dc5edaab236a720952dd868107f`.
- Exact write scope: `tests/test_r24_research_cas_fence.py` and this report. Both targets were absent on initial reads and were created through the authorized scoped writer.
- Existing SoT: `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md`. Stage: bounded native implementation verification; next required gates: executable runtime evidence, independent QA and reducer fan-in. The existing frontier remains unchanged.

FACT: BMad Help was loaded first, followed by Quick Dev and its clarify/route and planning references, then Superpowers verification-before-completion. Configuration scripts, Git/status/history inspection, extra spec/sprint writes, interactive approval steps, source discovery outside read_scope and delegation are unavailable or prohibited in this lane. These workflow steps were not performed or represented as complete. The immutable task contract supplies the bounded plan/DoD; no competing PLAN.md or new scheduler was created. The Help response included a tool-side truncation marker, so complete delivery of its underlying canonical text is not claimed.

## Local Definition of Done and work estimate

Value: independent native evidence that one committed checkpoint generation cannot be replaced by a stale concurrent writer, ownership is retained, and a killed process can be resumed without replay advancing a stale generation.

Required proof: source/contract binding; real native positive sequence advancement; stale-generation and foreign-owner negatives; concurrent process contention; actual process kill and fresh-process resume; unchanged winner bytes on rejection; affected regression; test-only repair/retest where justified; self-review; one original-task typed UNACCEPTED publication. Any product repair outside the two authorized files must be referred to the coordinator rather than performed here.

Smallest compatible design: one new pytest module exercises the existing native ResearchRun DTO/store/checkpoint/resume interfaces in temporary directories. No production implementation or replacement store is added. The new value beyond the documented r16 oracle is subprocess contention and real OS-process termination after a completed durable checkpoint, not another implementation of checkpoint persistence.

Pre-implementation estimate: investigation 4 minutes, test implementation 6, execution 2, possible repair 3, review 2, evidence 2; W approximately 19 minutes. External restoration overhead H is unknown; efficiency and elapsed useful work cannot be measured with the available tools. The attempt stops at a real external blocker, not an invented duration target. Next meaningful milestone: successful native collection and a source-bound pytest receipt in this same sticky task context.

## Evidence and mechanism already present

FACT: `docs/architecture/basefive-r14-contracts.json` declares ResearchRun schema `0.1` and the public begin/checkpoint/resume APIs. It binds `reasoners/deep_research_ext/research_run.py` to SHA-256 `a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea`. This is a static contract binding, not a fresh source read in this attempt. Baseline Git, manifest and cache identities are coordinator-supplied, not independently recomputed checkout identities.

FACT: source files are outside this attempt's exact read_scope. Consequently, direct observed source call paths, constructor details and current source ownership cannot be freshly established here. The test pins source bytes at runtime, but that assertion has not executed. No current source SHA verification or compatibility PASS is inferred from a historical report.

Permitted evidence inspected before writing:

- `docs/acceptance/northstar-checkpoint-cas-repair-20261013.md`: documents a prior persisted-sequence repair and preservation of the checkpoint API. Its historical source hashes are not substituted for the r14 binding.
- `docs/acceptance/basefive-r16-checkpoint-external-call-dedupe.md`: records source inspection of a persisted-load/check/save path with unconditional file replacement, and existing stale/checkpoint/effect test artifacts. It also records repeated infrastructure blockers; these are historical receipts, not this attempt's runtime output.
- `docs/acceptance/northstar-research-checkpoint-c4-qa-20261013.md`: describes native save/load/resume and recorded provider-call APIs, filesystem restart assertions and identity seams.
- `docs/acceptance/base20-research-run-restart-20261013.md` and `docs/acceptance/mvp-r9-checkpoint-source-fence-producer.md`: document stage, source-owner, generation and provider-receipt expectations.
- The current C4 reducer frontier explicitly leaves native task-to-result/interface acceptance blocked. A ResearchRun component test does not discharge that broader gate.

Contract-declared path, not freshly observed execution: verified pipeline -> `checkpoint_research_run` -> ResearchRunStore JSON save/load; `resume_research_run` -> ResearchRunStore load -> resume plan. Relevant logical owner: `ResearchRun.source_owner`; this is not a Ruflo lease/fencing epoch or CrewSync task owner. The exact production repair task key is not supplied and is not invented.

HYPOTHESIS: persisted generation checking followed by unconditional save can still lose updates if two writers observe the same generation. The new contention oracle is intended to expose this as PRODUCT_RED if execution confirms it. Existing implementation is reused rather than modified. No runtime bug is asserted from unexecuted tests.

## New oracle and boundaries

Five intended pytest functions are present; actual collection and execution counts are unknown.

| Case | Intended native invariant | Current result |
| --- | --- | --- |
| Positive generation advance | Three sequential checkpoints reload exactly with generations 1, 2, 3 and the same owner. | BLOCKED before collection. |
| Negative stale generation | Winner persists generation 1; a generation-0 writer raises ResearchRunCheckpointError without changing checkpoint bytes. | BLOCKED before collection. |
| Negative foreign owner | Foreign source_owner is rejected; durable owner and checkpoint bytes remain unchanged. | BLOCKED before collection. |
| Concurrent stale writer | First subprocess pauses at native save; second contends; release winner then loser; require one commit, stale rejection and exact winner preservation. | BLOCKED before collection. |
| Process kill and restart | Child commits generation 1, is forcibly terminated, fresh child rejects generation-0 replay unchanged, another fresh child advances to generation 2; owner and recorded effect identity survive. | BLOCKED before collection. |

The concurrency seam wraps save only to schedule operations; it delegates actual file writes to the original native save and does not fake load values or rejection. If the native implementation serializes the critical section, the second process may block before save and then reject after winner release. The two-second second-writer observation window is bounded scheduling, not proof that both writers reached save: independent QA must inspect failure output/coverage and may require stronger scheduling evidence. Each child independently checks the native source SHA. Child failures, timeout and nonzero exits are failures rather than converted to expected rejection; children are killed/reaped in finally blocks.

The crash boundary is explicitly **after** native checkpoint returns and before orderly child exit. It does not cover a crash during fsync/replace, power loss, or an external provider effect before receipt persistence. Provider call identity is a literal checkpoint fixture; no provider effect is executed or counted. Its unchanged/reloaded identity is not proof of production exactly-once effects. There is no live AgentField, provider, Native task-to-result or distributed ownership exercise.

ASSUMPTION awaiting native execution: ResearchRunStore accepts a path positional argument, declared stage names are valid at this boundary, source_owner rejection is a ValueError-family exception, and resume exposes provider_call_ids as documented by the permitted acceptance records. These details cannot be upgraded to directly observed source facts without source read authorization or executable evidence. Test imports load the actual module by file location rather than a fake store or production replacement. Optional dependency/import behavior remains unverified.

## Exact validation receipt

Required validation command:

```text
python -m pytest -q -p no:cacheprovider tests/test_r24_research_cas_fence.py
```

Actual authorized invocation, exactly once:

```text
go_wave.run_project_tests({"file":"tests/test_r24_research_cas_fence.py"})
```

The adapter did not expose a raw command/argv receipt, so the requested full command is not claimed as executed. Exact returned result:

```json
{"status":"BLOCKED","code":"PYTHON_VENV_UNAVAILABLE","test":"tests/test_r24_research_cas_fence.py","engine":"python:pytest","source_identity_sha256":"5a5bd8c83b48012f00c24e8b351954a0f8490655c48798d7faa03aa740b79379","exit_code":null,"signal":null,"error":null,"duration_limit_ms":120000,"output_truncated":false,"stdout":"","stderr":"A regular local .venv Python executable is required."}
```

FACT: no collection, syntax/import assertion, Python process exit, positive/negative result, restart result or affected regression result exists. The receipt binds the new test bytes, not native production bytes. No identical retry, shell escape, alternate Node simulation, dependency installation or weakened fixture was used. The tool contract's generic Node/TypeScript description did not substitute for its actual returned python:pytest infrastructure receipt.

Affected regression: the entire authorized focused file was requested and blocked. Prior records name tests/test_research_run.py and tests/test_northstar_r16_checkpoint_cas.py, but neither is granted test_scope here. They were not invoked or read. Affected baseline execution therefore also requires explicit authorization; absence of a run is not PASS.

## Self-review and acceptance matrix

- Both writes stay in exact scope. Native source, C4 contracts, prior accepted siblings, lockfiles, live tasks, leases, claims and terminal state are unchanged by this attempt. Git dirty-state/diff proof is not available through the scoped tools.
- No xfail, skip, permissive success fallback, fake CAS implementation or expected-oracle computation from production helpers was added. Expected sequence, owner, winner identity and unchanged bytes are literal assertions.
- Static review is not runtime verification. Source SHA guard, constructor/exception assumptions, subprocess cleanup and scheduling need native execution. No fresh graph coverage, Graphify, Structurizr or ArchSteer Go coverage is claimed; graph/navigation tools are not exposed in this lane.
- Full BMad procedural compliance is not claimed where the workflow requires prohibited scripts, out-of-scope spec artifacts or unavailable interactive steps. Task authority takes precedence.
- Source-backed call-path/owner acceptance: PARTIAL contract/history evidence only; current direct source inspection is scope-blocked.
- Native positive and two negatives: INFRA BLOCKED.
- Process restart and no foreign owner: INFRA BLOCKED; exactly-once external effects remain outside this oracle's proof.
- Affected native regression: NOT RUN; no additional authorized test_scope and focused runner unavailable.
- Result publication: one typed BLOCKED/UNACCEPTED result is required after this write; its actual transport readback is reported separately. VERIFIED transport never means product accepted.

## Recovery and independent reducer request

Operator: restore the regular repository-local .venv interpreter and required project dependencies without changing these fixtures. Resume this exact task/owner rather than starting another implementation. Run the required command above and retain command/argv, exit code, counts, stdout/stderr, source/test SHAs and contention/restart evidence. Authorize direct read of reasoners/deep_research_ext/research_run.py and an explicit affected baseline test_scope to close the remaining evidence gaps.

If contention confirms PRODUCT_RED, preserve the failing oracle and unchanged winner expectation; route production repair for reasoners/deep_research_ext/research_run.py to its coordinator-selected authorized owner. This test-only worker must not patch native CAS. After any authorized artifact repair, rerun focused tests and affected baselines.

Independent reviewer/reducer: inspect the source-bound receipts, verify both concurrent schedules and process cleanup, distinguish fixture receipts from provider effects, consume native C4 interface/task-to-result evidence separately, and obtain authoritative CrewSync terminal readback. This implementer neither self-accepts nor performs task administration.
