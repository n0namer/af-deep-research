# Basefive r16 Checkpoint External-Call Dedupe — r19 Resumption

Date: 2026-10-14
Outcome: BLOCKED / UNACCEPTED. No product GREEN or independent acceptance claimed.

## Authority and current gate

- Task: `af-deep-research:v2-r19-checkpoint-external-call-dedupe-20261014-r1`
- Attempt: `attempt-e14eabcf-3e66-47c8-bd0a-d2f68ad26921`
- Session: `manual-20261014-basefive-r19-affected-native-af-de8891916492dbe9`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`, not canonical BMAD-MNNZ.
- Coordinator-supplied Git revision: `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`. Branch, dirty state and history were not independently queried; shell is unavailable under task policy.
- Write scope: existing `tests/test_northstar_r16_checkpoint_cas.py` and this artifact only. Production source, contract and C4 reducer artifact remain read-only.
- BMad stage: bounded implementation verification/recovery, followed by independent QA and reducer evidence fan-in. Existing SoT: `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md`; it remains unchanged and records blocked C4 acceptance.
- BMad Help, systematic-debugging and verification-before-completion were loaded through the scoped adapter. Configuration scripts, Git commands, graph tools and independent acceptance tools are unavailable or outside scope; those method steps were not executed.

## Local measurable Definition of Done

Value: preserve and evaluate the existing source-bound r16 checkpoint/external-effect oracle without reimplementing the prior candidate or weakening failures.

The complete DoD requires source/contract/test identity binding; native pytest execution of positive receipt/restart, negative owner/revision/generation and interleaved/crash cases; affected regression evidence; repair of any authorized test defect followed by retesting; review of compatibility; and one typed original-task UNACCEPTED result. Native product repairs outside write scope require coordinator authorization. This attempt does not meet the runtime DoD because pytest did not start.

Smallest safe move: keep the existing 257-line oracle byte-for-byte, attempt its exact authorized runner once, inspect the native failure boundaries, and write this missing authorized evidence artifact. No parallel writers, live tasks, claims, sends, commits or production changes.

Useful-work estimate before further coding: inspection 4 minutes, implementation 0 (existing oracle already present), test execution 2, repair 0 pending actual results, compatibility review 3, evidence 3: W approximately 12 minutes. External runner restoration overhead H is unknown, so efficiency cannot be quantified. No artificial work was added to reach a duration target. Actual elapsed work was not instrumented. Next meaningful milestone is successful native collection and a source-bound focused receipt in the same sticky context.

## Source identities

FACT: scoped readers returned the following current SHA-256 identities. The Python hash/signature assertion itself was not executed.

| Input | SHA-256 |
| --- | --- |
| `AGENTS.md` | `490bdf70833a3ca86788830ead5fb9f7d8e8f37a0446626d166f5ac5e2107d08` |
| `reasoners/deep_research_ext/research_run.py` | `a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea` |
| `tests/test_northstar_r16_checkpoint_cas.py` (preserved) | `0e356850035a965363a33d281c7537fc12dfb57ef1652a86795aa47656a433b1` |
| `docs/architecture/basefive-r14-contracts.json` | `7d81581ed610a64337712806f7fb2edf4d6fc85d981cbfbdc692d267e79afc66` |
| `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md` | `e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce` |

FACT: current source SHA matches the test's SOURCE_SHA256 and the r14 contract's ResearchRun source entry. Source inspection confirms schema `0.1` and the declared begin/checkpoint/resume interfaces, including keyword-only `expected_checkpoint_seq`. The test additionally checks DTO field order and parameter kinds/defaults at runtime; those checks remain unrun. The r14 artifact explicitly describes static contracts for two Python modules, not whole-repository/native C4 release acceptance. The older C4 reducer quotes a different historical ResearchRun hash (`713caa8e...`); it is not a current source identity and must not replace this attempt's reader receipt.

## Actual test receipt

Authorized validation command requested through `go_wave.run_project_tests`:

```text
python -m pytest -q tests/test_northstar_r16_checkpoint_cas.py
```

Exact returned receipt:

```json
{"status":"BLOCKED","code":"PYTHON_VENV_UNAVAILABLE","test":"tests/test_northstar_r16_checkpoint_cas.py","engine":"python:pytest","source_identity_sha256":"0e356850035a965363a33d281c7537fc12dfb57ef1652a86795aa47656a433b1","exit_code":null,"signal":null,"error":null,"duration_limit_ms":120000,"output_truncated":false,"stdout":"","stderr":"A regular local .venv Python executable is required."}
```

FACT: collection, execution, test counts and product exit status are unavailable. This is an infrastructure blocker, not product RED or PASS. No identical retry, fallback shell, unrelated Node test or runner substitution was attempted.

## Oracle review and mechanism findings

- FACT: existing positive test records one local offline effect, persists its receipt, constructs a fresh store, then asserts replay does not change the checkpoint bytes or duplicate the effect.
- FACT: existing negatives check stale snapshot/expected generation, foreign owner/revision, invalid stage, cancellation before effect, terminal no-effect behavior, monotonic provider/evidence IDs and inherited replay receipts. These are assertions, not passing results.
- FACT: `checkpoint_research_run` loads persisted state, validates the observed generation/identity, constructs the next DTO and calls `store.save`. `save` fsyncs a temporary JSON file and replaces the target without an atomic persisted-generation comparison. Atomic file replacement is not compare-and-swap.
- HYPOTHESIS (source-backed, not runtime-confirmed): the existing `InterleavingStore.load` test advances a winner after the stale writer's read but returns the old snapshot. The stale writer can then replace the winner with its own checkpoint and lose `winner-call`. Its expected exception/assertions are meaningful and must remain unchanged. Required repair boundary is `reasoners/deep_research_ext/research_run.py` store/checkpoint persistence; this file is outside write scope. A second unlocked load would not close the race.
- FACT: `offline_provider_once` is a test driver, not a production provider API. It writes/fsyncs the local simulated effect before checkpointing the receipt. Its cancellation and generation checks are partly driver guards and must not be promoted to proof of production cancellation/CAS.
- HYPOTHESIS (source-backed, not runtime-confirmed): the injected save failure leaves the first effect durable but no provider receipt; a fresh store resumes with an empty call-ID list, permitting the driver to append the same call again. Receipt-after-effect alone cannot prove exactly-once behavior across this window.
- Required crash repair boundary: a production external-call path needs durable operation identity plus provider-side idempotency/reconciliation or an equivalent recoverable effect protocol. ResearchRun does not expose such a provider invocation API in the inspected file. The actual caller/provider integration is not readable in this task scope, so its exact file is unknown. Do not fabricate one or fix the test helper to manufacture production GREEN. An intent record alone does not establish whether the remote effect occurred.

## Gate matrix and affected regression

| Gate | Status | Evidence |
| --- | --- | --- |
| Reader source/test/contract SHA binding | PASS (static only) | Current scoped-reader hashes agree with test and r14 declaration. |
| ResearchRun DTO/API compatibility | Inspected; runtime BLOCKED | Source and contract reviewed; existing signature/field test unrun. |
| Positive and owner/revision/generation negatives | BLOCKED | pytest unavailable before collection. |
| Interleaved CAS and crash-before-receipt restart | BLOCKED runtime; unresolved source hypotheses | Existing assertions retained; native mechanisms are outside authorized write scope. |
| Affected regression | BLOCKED | Existing same-file monotonic IDs, terminal resume and inherited receipt cases are the authorized regression surface; none executed. No additional test_scope was supplied. |
| Native C4 ReleaseGate interfaces/E2E | BLOCKED | r14 static component model does not supply missing C4 producer/QA results, source/interface versions or task-to-result restart evidence. |
| Independent QA/reducer acceptance | Pending external gate | No acceptance or terminal readback claimed. |

## Changes, self-review and recovery

Only this previously absent authorized report is created. Existing r16 test bytes, source pin and all expected rejection/no-duplicate assertions are preserved; no xfail/skip, fixture weakening, altered expected duplicate count or local dedupe subsystem is introduced. Production source, shared contract and prior C4 artifact remain unchanged. No impact on previous r16 artifacts beyond adding this evidence/handoff is intended; no regression-freedom claim is made without runtime output.

Recovery: coordinator/operator restores the regular local `.venv` Python executable expected by the existing scoped runner, then resumes this exact sticky task/context and runs the recorded command. Diagnose actual outputs before any test edit. If native CAS/crash defects reproduce, authorize the necessary production boundary under coordinator ownership; do not dispatch a duplicate full r16 oracle implementation. Current exact source repair dependency is `reasoners/deep_research_ext/research_run.py`; external-call integration location needs separately authorized discovery. After authorized repair, rerun the whole focused file and source-pin compatibility gate, record any authorized source-contract revision rather than blindly updating hashes, and obtain source-bound independent QA/reducer plus authoritative terminal readback before ACCEPTED_GREEN.

This file is an evidence artifact, not a competing plan or acceptance ledger. One original-task BLOCKED/UNACCEPTED typed publication is required; its transport status/readback is reported separately and is not product acceptance.

## Resumed attempt receipt — 2026-10-14

The preceding sections retain the prior attempt's evidence; its attempt/session IDs do not identify this resumed execution.

- Current task: `af-deep-research:v2-r19-checkpoint-external-call-dedupe-20261014-r1`.
- Current attempt: `attempt-d8471fab-6e86-41b3-975e-3752c5accb20`.
- Current session: `manual-20261014-basefive-r19-resume-open-r21-af-8b75c89458f12a4b`.
- Outcome: infrastructure BLOCKED / UNACCEPTED; no native product PASS or FAIL is inferred.
- FACT: BMad Help and verification-before-completion were loaded. Target remains the explicit af-deep-research root; active gate remains source-bound native verification followed by independent QA/reducer. Configuration scripts, Git status/history, graph navigation and acceptance readback were not available through authorized tools. No new plan, production changes or task administration was introduced.
- FACT: current scoped range readers confirm source SHA `a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea`, contract SHA `7d81581ed610a64337712806f7fb2edf4d6fc85d981cbfbdc692d267e79afc66`, C4 reducer SHA `e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce`, and test SHA `0e356850035a965363a33d281c7537fc12dfb57ef1652a86795aa47656a433b1`. Source, test and r14 declaration agree on the ResearchRun pin; this is static binding, not execution of DTO/signature checks or verification of native C4 APIs. The C4 reducer still reports missing native interface/QA/E2E evidence.

Fresh authorized runner request: `go_wave.run_project_tests({"file":"tests/test_northstar_r16_checkpoint_cas.py"})`, corresponding to `python -m pytest -q tests/test_northstar_r16_checkpoint_cas.py`.

Exact fresh receipt:

```json
{"status":"BLOCKED","code":"PYTHON_VENV_UNAVAILABLE","test":"tests/test_northstar_r16_checkpoint_cas.py","engine":"python:pytest","source_identity_sha256":"0e356850035a965363a33d281c7537fc12dfb57ef1652a86795aa47656a433b1","exit_code":null,"signal":null,"error":null,"duration_limit_ms":120000,"output_truncated":false,"stdout":"","stderr":"A regular local .venv Python executable is required."}
```

FACT: no collection, test count or process exit occurred. The same denial was not retried. Positive, negative, restart and affected regression assertions remain unexecuted. No fixture, pin, assertion, skip or xfail was changed, and no unrelated Node substitute was run.

Source-backed self-review confirms the earlier boundaries: `checkpoint_research_run` checks a loaded generation before an unconditional `store.save`, whose atomic replacement has no persisted-generation CAS. The existing interleaving oracle remains relevant. The local driver fsyncs an effect before saving its receipt; its injected crash leaves no receipt for restart dedupe. These remain runtime-unconfirmed failure hypotheses, not proof of actual production provider invocation behavior. Native CAS repair would require authorized edits to `reasoners/deep_research_ext/research_run.py`; external-provider reconciliation/idempotency integration requires separately authorized discovery. Both are outside this write scope.

Only this report receives an append; the existing 257-line r16 oracle is preserved. This avoids repeating the prior implementation or concealing unresolved acceptance. Useful-work estimate for this bounded recovery: investigation 3 minutes, implementation/evidence 2, runner 1, compatibility/self-review 2, repair 0 absent runnable evidence: W approximately 8 minutes, H unknown. This is an estimate, not measured elapsed time. Additional code or repeated tooling would not advance the authorized DoD while infrastructure remains blocked.

Next meaningful milestone: operator restores the regular local `.venv` Python executable, then resumes this exact sticky task/context for the full recorded pytest command. Preserve source/test identity, diagnose actual output before test edits, and request production authorization only for reproduced out-of-scope defects. Independent source-bound QA/reducer and authoritative terminal readback remain required before acceptance. The single current-attempt typed publication and its exact transport readback are reported in the final handoff, not promoted to acceptance.

## Resumed attempt receipt — 2026-10-15

- Task: `af-deep-research:v2-r19-checkpoint-external-call-dedupe-20261014-r1`.
- Attempt: `attempt-b9c55992-9b49-44d8-98d0-33cd3523d407`.
- Session: `manual-20261015-basefive-long-hyperwave-af-deep-796f04ff5b34f441`.
- Outcome: infrastructure BLOCKED / UNACCEPTED. Earlier attempt/session identifiers above remain historical, not current authority.

FACT: target is the launcher-declared af-deep-research root. Existing C4 reducer remains the BMad source of truth; stage is implementation verification/recovery, with native runtime evidence then independent QA/reducer as the unmet gates. BMad Help and verification-before-completion were loaded. Git root/branch/dirty state, local BMad configuration scripts and graph freshness could not be independently queried through the authorized interfaces; no shell, graph tool, broad discovery, claim or acceptance operation was substituted.

Local DoD remains source/test/contract binding, native positive and negative checks including restart/crash and stale writers, affected regression, repair/retest where authorized, self-review and one original-task typed publication. The existing oracle already implements those assertions; no missing test mechanism was established that justifies editing it before executable evidence. Useful-work estimate for this recovery was investigation 3 minutes, implementation 0, runner 1, repair 0 pending runtime output, compatibility review 2 and evidence 2: W approximately 8 minutes, H unknown. These are estimates, not measured elapsed time. The next meaningful milestone is native pytest collection, not another implementation of the existing oracle.

### Fresh identity and runner evidence

FACT: current scoped source range receipt gives SHA-256 `a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea`. It matches the existing test pin and the r14 contract source declaration. Current contract reader SHA is `7d81581ed610a64337712806f7fb2edf4d6fc85d981cbfbdc692d267e79afc66`; current C4 reducer reader SHA is `e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce`. Runtime DTO/signature assertions remain unexecuted. The contract describes static ResearchRun interfaces, not proof of native C4 ReleaseGate APIs; the C4 reducer explicitly records missing native interface/DTO and E2E evidence. That acceptance criterion remains unverified rather than silently downgraded.

Fresh request: `go_wave.run_project_tests({"file":"tests/test_northstar_r16_checkpoint_cas.py"})` for the authorized command `python -m pytest -q tests/test_northstar_r16_checkpoint_cas.py`.

Exact returned receipt:

```json
{"status":"BLOCKED","code":"PYTHON_VENV_UNAVAILABLE","test":"tests/test_northstar_r16_checkpoint_cas.py","engine":"python:pytest","source_identity_sha256":"0e356850035a965363a33d281c7537fc12dfb57ef1652a86795aa47656a433b1","exit_code":null,"signal":null,"error":null,"duration_limit_ms":120000,"output_truncated":false,"stdout":"","stderr":"A regular local .venv Python executable is required."}
```

FACT: no Python process exit, collection, test count, positive/negative/restart result or affected regression result is available. The current runner binds the preserved test SHA above. No identical denial retry, Node substitution, fixture change, xfail/skip or fabricated product GREEN was used. No additional executable regression target is authorized; the whole focused file is the available affected regression surface and remains infrastructure-blocked.

### Source-backed self-review and handoff

FACT: `checkpoint_research_run` checks an observed persisted generation and then calls `store.save(updated)`; `save` fsyncs a temporary file and unconditionally replaces the checkpoint. Atomic replacement is not an atomic persisted-generation compare-and-swap. The existing test deliberately advances the persisted checkpoint after its load snapshot, then expects rejection and preservation of winner bytes/receipts. HYPOTHESIS: this oracle will expose the stale-writer defect when the native runner is restored; no runtime RED is claimed.

FACT: the offline test driver writes and fsyncs an effect before checkpointing its provider receipt. The crash test interrupts that save, reopens the store, and asserts no second effect despite the absent receipt. HYPOTHESIS: the local crash oracle will expose duplicate effects. This driver is not a production provider integration, and it cannot establish production exactly-once behavior or native C4 task-to-result semantics. Existing owner/revision/generation negatives and rejection expectations are retained without weakening trust checks.

Only this append changes; its base SHA was `2047aa98ca5391ee9686a3eaf65d7b7085bb3db5f89cc3462ccb40da33427ddb`. Existing r16 tests, production source, contract, prior C4 artifact and earlier receipt sections are preserved. No code/API/DTO or provider behavior is changed, and no runtime regression-freedom claim is made. Publication transport/readback will be reported separately; it does not satisfy independent acceptance.

Recovery: operator must restore the regular local `.venv` executable required by the scoped runner, then resume the same sticky owner/task with the exact recorded pytest command. Do not launch another full oracle implementation. Diagnose actual test outputs before editing tests. Any native CAS repair requires newly authorized scope for `reasoners/deep_research_ext/research_run.py`; production provider idempotency/reconciliation integration needs separately authorized discovery. Supply the missing source-bound C4 interface/DTO and native E2E/QA receipts before independent reduction. The current attempt remains BLOCKED / UNACCEPTED.
