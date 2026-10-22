# R17 independent acceptance gate

Verdict: **BLOCKED / UNACCEPTED**. No ACCEPTANCE_RECOMMENDED or ACCEPTED_GREEN recommendation.

## Binding and scope
- Task: af-deep-research:v2-r17-acceptance-reducer-20261014-r1
- Attempt: attempt-031194f4-5cf7-4677-a177-cce782bec39c
- Session: manual-20261014-acceptance-resilience-r20-af-de-c93524355210b2ee
- Target: D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research
- Prelaunch Git: e10580c89eac7a4f6efb50c921ae9107ce8ad8dc (trusted launcher value; Git status/branch not independently available).
- Only this report and tests/test_northstar_r17_acceptance_qa.py were written. Producer source and live authority were not mutated.
- SoT: docs/acceptance/c4-releasegate-reducer-frontier-20261013.md; acceptance/reducer phase, unmet independent runtime and terminal-readback gate. BMad installation/config status unknown within exact read scope.

## Measurable DoD and result
Both original R16 typed publications must bind current source/test hashes; independent native positive, two adversarial negatives, restart and duplicate-effect checks must execute; architecture anchors must be verified; exact terminal CAS/readback must authorize any green recommendation.
This DoD is unmet. Static source identity is established, but original typed R16 receipts and native runtime/terminal evidence are absent from the authorized evidence set. Test-file names do not establish task/result identities.

## Exact source identities
Scoped reader SHA-256 receipts:
| File | SHA-256 |
| --- | --- |
| reasoners/deep_research_ext/research_run.py | a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea |
| reasoners/deep_research_ext/verified_pipeline.py | 97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87 |
| tests/test_northstar_r16_source_citation.py | cc601111b1a22c3bb10157f620cec22efa8c14d670adceed88e13191ab635aa3 |
| tests/test_northstar_r16_checkpoint_cas.py | 0e356850035a965363a33d281c7537fc12dfb57ef1652a86795aa47656a433b1 |
| docs/architecture/basefive-r14-contracts.json | 7d81581ed610a64337712806f7fb2edf4d6fc85d981cbfbdc692d267e79afc66 |
| docs/acceptance/c4-releasegate-reducer-frontier-20261013.md | e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce |
| tests/test_northstar_r17_acceptance_qa.py | 810e2567478a15949bc3b90896c0fa9c988c75d21ee730572223a92ba7b60b7d |

FACT: Both module hashes match R14 contract declarations and R16 source pins. This is not cross-verification against original typed producer publications: those publications are unavailable.

FACT: R14 contracts declare C4 literal source anchors and explicitly record missing/stale Graphify symbols. Actual Graphify and ArchSteer artifacts are outside read_scope; their recorded hashes cannot be independently refreshed. The QA adds literal-anchor checks; they remain unexecuted.

## Runtime receipts and classification
1. go_wave.run_project_tests(file="tests/test_northstar_r16_source_citation.py")
   returned isError=true, text="GO_WAVE_NODE_ERROR:test_outside_task_write_scope".
   Classification: INFRA / runner authorization mismatch. No process or test count.
2. The second requested command, python -m pytest -q tests/test_northstar_r16_checkpoint_cas.py, was not attempted through the same denied read-only test scope. No PASS is inferred.
3. go_wave.run_project_tests(file="tests/test_northstar_r17_acceptance_qa.py")
   returned status=BLOCKED, code=PYTHON_VENV_UNAVAILABLE, engine=python:pytest,
   source_identity_sha256=810e2567478a15949bc3b90896c0fa9c988c75d21ee730572223a92ba7b60b7d,
   exit_code=null, signal=null, error=null, duration_limit_ms=120000,
   output_truncated=false, stdout="", stderr="A regular local .venv Python executable is required."
   Classification: INFRA. Collection and execution did not occur; no runtime log SHA exists.
Identical denied/dependency-blocked calls were not retried. No unsupported shell fallback was used.

## Independent QA and static adversarial findings
The new QA uses actual module APIs, temporary checkpoint storage, and isolated report-store instances. It tests source hashes/C4 anchors, positive checkpoint restart, stale-generation and foreign-owner negatives with byte preservation, report duplicate-effect fencing, two invalid-citation negatives, recreated-store durability, and interleaved checkpoint CAS. It does not mock a native service or claim a native end-to-end run. No xfail or skipped assertion hides defects.

- FACT / static product finding: DurableVerifiedSourceReportStore.__init__ creates fresh _reports and _effects dictionaries, with no filesystem persistence. A newly constructed store cannot reload the old instance's report or effects. The R16 recreated-store expectation conflicts with this implementation. Runtime reproduction is blocked.
- FACT / static product finding: build_grounded_verified_report validates fact metadata and DTO fields; persist_grounded_verified_report checks identity/owner/cancellation. Neither checks document citation tokens or entailment against payload evidence. The R16 invalid-document rejection expectations lack corresponding validation on this API path. The new QA independently probes unsupported and foreign-source documents; runtime results are unavailable.
- FACT / static product finding: checkpoint_research_run loads the generation and then calls store.save(updated); save unconditionally uses os.replace. There is no atomic generation comparison around replacement. An intervening writer can be overwritten. The independent QA injects an intervening actual checkpoint write during load to assert loser rejection and winner-byte preservation. Runtime reproduction is blocked.
- FACT / fixture limitation: R16 offline_provider_once writes an effect before persisting its receipt. A crash before store.save leaves no provider-call receipt, so replay can repeat the driver effect. This is a fixture/orchestration ordering gap; it is not proof of native provider exactly-once behavior.
- FACT / evidence limitation: source-citation and checkpoint suites do not supply native service/task-to-result receipts, original typed R16 publications, or CrewSync terminal CAS/readback. No live task mutation is authorized here.

## Workflow and self-review
BMad Help was read completely; target and active artifact were resolved from trusted scope. BMad code review and verification-before-completion were loaded. Code-review step-01 was read; its Git diff/config resolver and later parallel-review workflow cannot execute under the no-shell/no-agents authority. The full skill workflow is therefore method-BLOCKED, not claimed complete. Scope overrides skill instructions. Verification-before-completion was applied: real runner receipts are preserved and no runtime success is claimed.

Self-review: QA writes are confined to the exact two paths; source is unchanged. Tests retain failing acceptance expectations instead of weakening them. Import/dependency failures, if encountered after infrastructure repair, must be classified separately from assertion failures. Recreating a Python object is weaker than process restart; even a passing local suite would not satisfy the native restart gate.

Sizing: estimated useful investigation 4 minutes, QA implementation 3, verification/repair 3, review/evidence 3 (13 total); infrastructure prevents runtime repair. No elapsed-time padding or duplicate producer implementation.

## Required recovery
Resume this exact sticky attempt after the coordinator permits both R16 test files in runner test_scope and restores the regular local .venv pytest runner. Run:
- python -m pytest -q tests/test_northstar_r16_source_citation.py
- python -m pytest -q tests/test_northstar_r16_checkpoint_cas.py
- python -m pytest -q tests/test_northstar_r17_acceptance_qa.py

Supply both original R16 typed publications with immutable source/test SHA and native positive/two-negative/restart logs, actual C4/Graphify/ArchSteer source-anchor evidence, and exact authorized terminal CAS/readback. Route confirmed product defects to original owners for affected-only repair; this lane cannot edit their source. Keep BLOCKED/UNACCEPTED until independent evidence and authority support reduction.
