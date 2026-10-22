# Release-Gate Restart/Resume End-to-End QA — 2026-10-13

Status: **INFRA BLOCKED / UNACCEPTED**. The bounded offline QA artifact is present, but the authorized runner could not start pytest because the checkout has no regular local `.venv` Python executable. No runtime PASS is claimed.

## Authority and Scope

- Task: `af-deep-research:v2-releasegate-restart-resume-e2e-20261013-r1`
- Attempt: `attempt-dc08d345-8bf4-43cf-8347-f3708729825a`
- Session: `manual-20261013-native-releasegate-hyperwave-r1-31f057709c881d8c`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Changed paths are limited to the authorized QA test and this acceptance record.
- No production source, existing producer/QA artifact, dependency, provider, network, database, lock, lease, task state, commit, or deployment was changed.

## Frozen Source Evidence

| Artifact | SHA-256 | Reviewed behavior |
| --- | --- | --- |
| `reasoners/deep_research_ext/research_run.py` | `713caa8e1d6c4e96127b72571b42ab34882542cd478976fe83bb3e2785681d4c` | Atomic filesystem checkpoints, native run/replay identity, cached payload inheritance, source-revision fencing, terminal resume state. |
| `reasoners/deep_research_ext/verified_pipeline.py` | `1ea0b249afc0c84d57824b78c5b4e6b3a79ae40a5b5890ed1a91d1046a872d1f` | Persists the research package before verification, reuses a cached package after restart, applies strict partial-abstention and final-verification gates, records terminal payloads. |
| `reasoners/deep_research_ext/final_verifier.py` | `d9210579b1a673b1cdc7dbd15f4f0cff660c1e75eedaa4abc54d9a910c00aef1` | Rejects empty, unknown, cross-claim, or duplicate assessment `fact_id` values before accepting provider adjudication. |
| `reasoners/deep_research_ext/synthesis_guard.py` | `a153a6c02e30bf82db0a78c6ae157abc483196ff713e051868687d7ae7f0ef7f` | Emits only verified source-entailed claims and explicit unresolved-requirement abstention in strict partial mode. |
| `tests/test_releasegate_restart_resume_20261013.py` | `850e3c0b97c886332bac8089c7e2a9dcd425f48186e25e4db6bdb16bbeab96cc` | New deterministic release-gate suite; runner source identity receipt. |

The requested mechanism was therefore already implemented in production code. This task adds only scoped end-to-end release-gate evidence and does not rewrite source behavior.

## Added QA Cases

`tests/test_releasegate_restart_resume_20261013.py` contains three deterministic, disposable-storage cases:

1. **Native interruption and successful replay**
   - Uses a filesystem `ResearchRunStore` under pytest `tmp_path`.
   - Simulates an interruption immediately after the durable research-package snapshot and before evidence verification completes.
   - Starts a new native run identity with `replay_source_run_id` bound to the interrupted run.
   - Asserts the saved package is inherited byte-for-structure, source preparation is called once total, report generation is called once total, and the replay reaches a completed `verified_document` checkpoint.

2. **Stale revision and provider/fact-ID ambiguity rejection**
   - Attempts replay with a different source revision and expects `StaleResearchRunError` before the new run file is created.
   - Supplies one valid positive assessment plus an unknown positive `D1:S999` assessment.
   - Asserts the mixed provider result fails closed, the fluent report is not delivered as verified, and the terminal mode is `post_generation_rejected` with `cited_evidence_does_not_entail_claim`.

3. **Restarted partial abstention**
   - Interrupts after saving one source-entailed fact for a two-requirement contract.
   - Replays from the saved package without a second source call.
   - Asserts the free-form writer is never called, the supported fact is rendered with its citation, requirement `R2` is explicitly unresolved, and the terminal semantic snapshot reports zero unsupported material claims with citation entailment ratio `1.0`.

These are simulated offline boundaries. They do not claim a live AgentField process kill, distributed durability, paid-provider replay, or production release acceptance.

## Validation Receipt

Authorized focused call:

```text
go_wave.run_project_tests({"file":"tests/test_releasegate_restart_resume_20261013.py"})
```

Exact adapter result:

```json
{
  "status": "BLOCKED",
  "code": "PYTHON_VENV_UNAVAILABLE",
  "test": "tests/test_releasegate_restart_resume_20261013.py",
  "engine": "python:pytest",
  "source_identity_sha256": "850e3c0b97c886332bac8089c7e2a9dcd425f48186e25e4db6bdb16bbeab96cc",
  "exit_code": null,
  "signal": null,
  "error": null,
  "duration_limit_ms": 120000,
  "output_truncated": false,
  "stdout": "",
  "stderr": "A regular local .venv Python executable is required."
}
```

Classification: **infrastructure blocked before pytest collection**, not a product test failure and not a PASS. The denied invocation was not repeated.

## Definition-of-Done Comparison

| Criterion | Result | Evidence |
| --- | --- | --- |
| Physical scoped QA artifacts | PASS | Both authorized new paths were created; no production path was written. |
| Positive restart/reuse/no-duplicate case | PRESENT, runtime blocked | Deterministic call counters and terminal payload assertions in the focused suite. |
| Negative stale revision and fact-ID/provider ambiguity | PRESENT, runtime blocked | Explicit stale replay exception and mixed valid/unknown assessment rejection. |
| Faithful partial abstention | PRESENT, runtime blocked | Exact supported claim, unresolved `R2`, writer count zero, semantic snapshot assertions. |
| Disposable local storage and no unsafe effects | PASS by construction/source review | `tmp_path`-scoped files; no network/provider/DB/coordination operations. |
| Independent reproducible test exit | BLOCKED | `PYTHON_VENV_UNAVAILABLE`; no exit code because pytest did not start. |
| Independent acceptance | UNACCEPTED | Reducer/reviewer and authoritative CrewSync terminal readback remain external gates. |

## Repair / Verification Handoff

In a Python-capable checkout with the repository dependencies installed in a regular local `.venv`, run exactly:

```text
.venv\Scripts\python.exe -m pytest -q tests/test_releasegate_restart_resume_20261013.py
```

If the focused suite passes, run the affected existing regressions:

```text
.venv\Scripts\python.exe -m pytest -q tests/test_durable_research_checkpoint_wave.py tests/test_base20_independent_restart_abstention_qa.py tests/test_partial_abstention_goal_wave.py tests/test_verified_pipeline_wave_full_cycle.py
```

Any failure should be repaired by the owning source/test task without weakening source-revision fencing, exact assessment identity binding, cached-package reuse, or strict abstention. This worker does not self-accept the candidate.
