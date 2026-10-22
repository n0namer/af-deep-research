# R24 Checkpoint Effect Replay — blocked evidence checkpoint

Date: 2026-10-15
Outcome: BLOCKED / UNACCEPTED. No runtime PASS, PRODUCT_RED, or product acceptance is claimed.

## Authority and current gate

- Task: `af-deep-research:v2-r24-checkpoint-effect-replay-20261015-r2`
- Attempt: `attempt-3d340ddd-b4dc-4c54-b2a2-634ce6518348`
- Session: `manual-20261015-basefive-r24b-20owners-af-deep--8ad29ce18fac3f48`
- Target: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`, not canonical BMAD-MNNZ.
- Coordinator-supplied Git identity: `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`. FACT: this is a trusted prelaunch identity, not an independently recomputed working-tree snapshot. Branch, dirty state and history were not queried.
- Exclusive write scope: `tests/test_r24_checkpoint_effect_replay.py`, `docs/acceptance/r24-checkpoint-effect.md`.
- Read scope: `AGENTS.md`, `docs/architecture/basefive-r14-contracts.json`, `docs/acceptance`, `graphify-out`, `.archsteer`, and the named C4 reducer artifact. Production Python modules and existing Python tests are not in that scope.
- Existing BMad SoT: `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md`. Stage: implementation verification/recovery; unmet gate: native source-bound execution, then independent reviewer/reducer QA. The SoT remains unchanged.

BMad Help was loaded first, followed by BMad Quick Dev and its clarify/route step, then Superpowers verification-before-completion. Configuration/customization scripts, unrelated planning artifacts, Git commands, graph MCP tools and shell execution were not available under this authorization; those method steps were not executed. Quick Dev implementation readiness is blocked by missing authorized source/prior-oracle inspection. No claim of completing the full skill workflow is made.

## Local measurable DoD and smallest safe move

Value: independently determine whether a native external-provider effect is repeated after a crash between effect and checkpoint receipt, without substituting a test-only scheduler or provider implementation.

The DoD requires current production source/contract binding; an observed native call path and ownership checks; one positive receipt/replay case; at least two fail-closed negative cases; a real child-process crash/restart at the effect-before-receipt boundary; focused native output and exit status; affected regression; authorized repair/retest if needed; self-review; and one original-task typed UNACCEPTED publication.

FACT: that DoD is not met. Missing new files are not a blocker: both authorized targets were queried and returned ENOENT, and creation is authorized. The blocker is that the evidence needed to design a native, non-duplicated test is outside read scope. Creating a speculative provider driver, a deliberate placeholder failure, or a document-only passing test would not establish the requested behavior.

Useful-work sizing at the scope decision: investigation 4 minutes, code implementation 0 while source-gated, test execution 0 while no justified executable exists, repair 0 pending reproduction, compatibility review 2 minutes, evidence 3 minutes; W approximately 9 minutes. External authorization/runner overhead H is unknown. This is an estimate, not measured elapsed work. No work was manufactured to fill a duration target. Next meaningful milestone: authorized inspection of native source and the existing crash oracle, followed by source-bound native collection in this same task context.

## Evidence inspected and limitations

1. FACT: `docs/architecture/basefive-r14-contracts.json` declares static contracts for two Python modules, baseline Git `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`, ResearchRun schema `0.1`, and source identities:
   - `reasoners/deep_research_ext/research_run.py`: `a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea`.
   - `reasoners/deep_research_ext/verified_pipeline.py`: `97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87`.
   These are contract declarations, not fresh source-reader or runtime hash receipts in this attempt.
2. FACT: the contract attributes checkpoint persistence and resume planning to `research_run.py::{begin_research_run,checkpoint_research_run,resume_research_run}`; checkpoint takes `source_owner`, `source_revision`, `expected_checkpoint_seq` and `payload`. The declared pipeline owns injected async research/generation callback orchestration and calls checkpoint persistence. These are declared component responsibilities, not observed native calls or coordinator ownership assignments.
3. FACT: `docs/acceptance/basefive-r16-checkpoint-external-call-dedupe.md` records an existing 257-line oracle at `tests/test_northstar_r16_checkpoint_cas.py`, preserved SHA `0e356850035a965363a33d281c7537fc12dfb57ef1652a86795aa47656a433b1`. It describes positive receipt replay, owner/revision/generation negatives, and an effect-before-save crash oracle. It explicitly says its local offline driver is not a production provider integration. The actual test is not readable in this task. The mechanism must not be declared absent or reimplemented blindly.
4. FACT: that report attributes generation validation followed by unconditional `store.save(updated)`/replace to the source and predicts stale-writer and duplicate-effect failures. HYPOTHESIS: a native source-grounded probe may expose those defects. This attempt has not observed PRODUCT_RED and does not promote upstream source descriptions into current source inspection.
5. FACT: `docs/acceptance/base20-research-run-restart-20261013.md` describes durable provider-call IDs and restart planning, not an atomic external-provider idempotency transaction. `docs/acceptance/basefive-verified-checkpoint-20261014.md` records a historical lost-provider-ID defect/repair and blocked post-repair verification. Neither is proof of exactly-once external effects.
6. FACT: the C4 reducer artifact remains BLOCKED for product acceptance and lists missing native interface/DTO and failure/restart evidence. Its older source hashes must not substitute for current production identity.
7. FACT: the permitted Graphify directory was listed, but no graph freshness, coverage or source completeness was established. Graph MCP/Graft tools are not exposed. No ArchSteer Go coverage, Structurizr runtime or complete graph claim is made. These indexes cannot resolve the native source-read authorization gap.

## Validation and error receipts

Required command, NOT EXECUTED:

```text
python -m pytest -q -p no:cacheprovider tests/test_r24_checkpoint_effect_replay.py
```

Current attempt: no Python process, collection count, exit status, positive/negative outcome, restart outcome or affected-regression outcome exists. No runner invocation was made against an absent placeholder, and no Node test was substituted. The test file was deliberately not created without adequate native API/call-path evidence. This is a scope/evidence BLOCKED finding, not an observed runner failure.

Exact current target-read errors:

```text
GO_WAVE_NODE_ERROR:ENOENT: no such file or directory, stat 'D:\Users\NIKITA\Documents\DEV\universal-solver-site\af-deep-research\tests\test_r24_checkpoint_effect_replay.py'
GO_WAVE_NODE_ERROR:ENOENT: no such file or directory, stat 'D:\Users\NIKITA\Documents\DEV\universal-solver-site\af-deep-research\docs\acceptance\r24-checkpoint-effect.md'
```

Historical runner receipt quoted by the r16 artifact, NOT executed or reconfirmed in this attempt:

```json
{"status":"BLOCKED","code":"PYTHON_VENV_UNAVAILABLE","test":"tests/test_northstar_r16_checkpoint_cas.py","engine":"python:pytest","source_identity_sha256":"0e356850035a965363a33d281c7537fc12dfb57ef1652a86795aa47656a433b1","exit_code":null,"signal":null,"error":null,"duration_limit_ms":120000,"output_truncated":false,"stdout":"","stderr":"A regular local .venv Python executable is required."}
```

The historical dependency may still need restoration, but current runner health is UNKNOWN. It must not be labeled a fresh infrastructure receipt.

## Acceptance review

| Criterion | Current result |
| --- | --- |
| Actual source SHA, C4 contract, observed call paths and owners | BLOCKED: static contract and upstream responsibility descriptions available; no authorized current native source or observed execution. |
| Native positive command and exit | NOT RUN: required command recorded above, exit unknown. |
| Two negatives and effect-before-receipt process restart | NOT RUN: no native provider entry point or executable oracle inspected. |
| Preserve RED evidence without weakening fixtures | Historical blocked receipt preserved with attribution; no current product RED, test weakening, xfail or skip. |
| Candidate test/report and typed publication | Partial: this report only; test not created. Publish BLOCKED/UNACCEPTED, not CANDIDATE. Independent review remains required. |

## Recovery requirements and self-review

Coordinator must authorize read access, not production writes, to:

- `reasoners/deep_research_ext/research_run.py` and `reasoners/deep_research_ext/verified_pipeline.py` to inspect exact source identity, store construction, receipt persistence, cancellation and ownership boundaries, and the actual external-callback path.
- `tests/test_northstar_r16_checkpoint_cas.py` to inspect and reuse the existing oracle rather than create a duplicate implementation.
- `tests/test_research_run.py` and `tests/test_durable_research_checkpoint_wave.py` for affected native regression inspection/execution, or supply an exact alternative authorized test scope.
- Any actual provider integration dependency identified by those modules, only after its exact path is known; no invented filename or owner is assigned here.

Then resume this same task/owner context: verify prior publications to avoid duplicate candidate work; inspect source and existing tests; implement only a necessary independent slice in the authorized new test; use an offline recorder at the actual injected provider boundary; verify the positive case, foreign-owner and stale-revision rejection before effects, and child-process interruption after durable effect but before receipt. Assert one effect and no false success after restart without adding test-owned reconciliation that masks missing production dedupe. If the native API cannot support safe reconciliation, retain a genuine product failure instead of weakening assertions. Run the exact focused command, preserve exit/output, repair only owned artifacts, then run separately authorized affected regression. Finally request independent reducer QA.

Only this report was written. Production source, prior tests, C4 SoT, live tasks, leases and terminal state were not modified. No external send, shell, commit, deployment, new agent, claim or acceptance action occurred. No source read was tunneled through a test or alternative execution tool. The publication response/readback is a separate transport receipt returned after this file is saved; it is not product acceptance.
