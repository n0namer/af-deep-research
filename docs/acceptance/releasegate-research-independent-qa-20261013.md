# Release-Gate Independent Verified-Recovery QA — 2026-10-13

## Verdict

**REPAIR REQUIRED / UNACCEPTED.** Independent runtime execution is infrastructure-blocked, and source review identifies a material terminal-replay idempotency violation that is not covered by the producer suites.

- QA task: `af-deep-research:v2-releasegate-independent-qa-20261013-r1`
- Attempt: `attempt-23e25573-2974-4bb4-831b-487fc60d396d`
- Session: `manual-20261013-native-releasegate-independent--d512a1ce667f6153`
- Producer tasks reviewed:
  - `af-deep-research:v2-releasegate-native-evidence-e2e-20261013-r1`
  - `af-deep-research:v2-releasegate-restart-resume-e2e-20261013-r1`
- Scope: one independent test file and this QA record only.
- Network, live model providers, live retrieval, CrewSync administration, Ruflo task state, production source, producer files, and existing QA files were not modified or invoked.

## BMad Gate and Source of Truth

The target is the explicit `af-deep-research` repository, not the canonical BMAD-MNNZ control plane. The current gate is independent adversarial release-gate QA after two producer candidates. No target-local BMad planning or sprint artifact is present in the authorized evidence; the producer acceptance records and native source are the applicable source of truth.

The producer records remain explicitly unaccepted:

- `docs/acceptance/releasegate-native-evidence-20261013.md` reports candidate evidence only and requires independent review plus authoritative CrewSync terminal readback.
- `docs/acceptance/releasegate-restart-resume-20261013.md` reports `INFRA BLOCKED / UNACCEPTED`.

The authorized read scope exposes no authoritative CrewSync receipt for either original producer task, no Git `HEAD` identity, and no immutable process-result readback. The coordinator-provided statement that the host-focused suite has `8 PASS, 1 SKIP` is not promoted to independent runtime evidence here. The skipped live-provider case remains a skip and is not described as live retrieval.

## Frozen Reviewed Inputs

`tests/test_releasegate_independent_verified_recovery_20261013.py` binds its review to these exact SHA-256 values:

| Artifact | SHA-256 | Review purpose |
| --- | --- | --- |
| `reasoners/deep_research_ext/verified_pipeline.py` | `1ea0b249afc0c84d57824b78c5b4e6b3a79ae40a5b5890ed1a91d1046a872d1f` | Resume, verification, abstention, synthesis, and terminal persistence path. |
| `reasoners/deep_research_ext/research_run.py` | `713caa8e1d6c4e96127b72571b42ab34882542cd478976fe83bb3e2785681d4c` | Native identity, replay inheritance, source fencing, and terminal resume plan. |
| `reasoners/deep_research_ext/final_verifier.py` | `d9210579b1a673b1cdc7dbd15f4f0cff660c1e75eedaa4abc54d9a910c00aef1` | Exact claim/citation `fact_id` binding and duplicate rejection. |
| `tests/test_releasegate_native_evidence_20261013.py` | `75171c60b92236c6fee6b7e47facc10af659e90c5796ed381250055b18c00b54` | Native evidence producer suite. |
| `tests/test_releasegate_restart_resume_20261013.py` | `850e3c0b97c886332bac8089c7e2a9dcd425f48186e25e4db6bdb16bbeab96cc` | Restart/resume producer suite. |
| `docs/acceptance/releasegate-native-evidence-20261013.md` | `1c315d1e2943cf3bd812a7d5d2d3eac038f1e9f2693725abef3ff223bdd83b76` | Producer claims and runner limitation. |
| `docs/acceptance/releasegate-restart-resume-20261013.md` | `d90c0894e3a3019166712b363ad7d44c4aeae1e2862080cfcd3a50321b0581ba` | Producer restart claims and runner limitation. |

Independent test SHA-256 at the attempted runner boundary: `acfb2c05b02117d60658374614153a096ae6f6ce003cc674cea0b46f0dc6d8f4`.

## Independent Challenges Added

The new focused suite contains five deterministic pytest cases after parameter expansion:

1. **Immutable reviewed-artifact binding** — fails when any reviewed source, producer test, or producer acceptance record changes without renewed review.
2. **Adversarial duplicate `fact_id`** — two positive assessments for the same exact `D1:S1` identity must fail closed and support zero claims.
3. **Positive same-native-identity retry** — an existing terminal run must reload byte-for-structure with terminal resume plan `done`.
4. **Crash/retry boundary: verified document** — replaying a completed `verified_document` under a new native identity must remain terminal and preserve provider-call receipts, preventing duplicate verification or report generation.
5. **Crash/retry boundary: partial abstention** — replaying completed `programmatic_partial_abstention` under a new native identity must remain terminal and must not reopen synthesis.

The suite uses only a pytest temporary directory and frozen in-process evidence. It does not claim live AgentField process termination, distributed storage durability, paid-provider execution, or production release acceptance.

## Material Finding

`reasoners/deep_research_ext/research_run.py` does not preserve terminal state when a new native run replays a completed source run:

- `begin_research_run` copies the completed source payload, source IDs, summaries, gaps, conflicts, and history.
- It nevertheless sets the new replay stage to `research_package_ready` whenever a cached research package exists and sets status to `running`.
- The inherited terminal mode and document package therefore coexist with a non-terminal replay state.

`reasoners/deep_research_ext/verified_pipeline.py` treats that inherited research package only as a retrieval cache. It rebuilds and verifies the ledger, checkpoints `evidence_verified`, and, for complete coverage, invokes document generation and final verification again before writing another terminal checkpoint.

This is a source-backed violation of the requested no-duplicate evidence/report boundary for a crash or retry that occurs after terminal persistence but before the caller durably records delivery/publication. The existing producer restart case interrupts before report generation and therefore does not exercise this terminal replay branch.

Required sticky repair belongs to the original source owner, not this QA task. The repair must define and enforce one terminal replay contract, for example:

- preserve the terminal stage/status and return the persisted terminal output without re-entering the pipeline; or
- reject a new replay identity for an already completed source run with an explicit terminal-result handoff.

The repair must retain source-revision fencing, exact citation/`fact_id` checks, faithful partial abstention, and same-identity idempotency. It should add a source-owned regression matching both parameterized terminal modes in the independent test.

## Focused Test Receipt

Authorized invocation:

```text
go_wave.run_project_tests({"file":"tests/test_releasegate_independent_verified_recovery_20261013.py"})
```

Exact result:

```json
{
  "status": "BLOCKED",
  "code": "PYTHON_VENV_UNAVAILABLE",
  "test": "tests/test_releasegate_independent_verified_recovery_20261013.py",
  "engine": "python:pytest",
  "source_identity_sha256": "acfb2c05b02117d60658374614153a096ae6f6ce003cc674cea0b46f0dc6d8f4",
  "exit_code": null,
  "signal": null,
  "error": null,
  "duration_limit_ms": 120000,
  "output_truncated": false,
  "stdout": "",
  "stderr": "A regular local .venv Python executable is required."
}
```

Classification: **infrastructure blocked before pytest collection**, not PASS and not a runtime product failure. The identical denied call was not retried. Affected producer regressions were not invoked because the unchanged missing `.venv` prerequisite would block the same Python engine.

## Acceptance Comparison

| Criterion | Result | Evidence |
| --- | --- | --- |
| Independent challenge of producer artifacts | PRESENT | Frozen producer/source SHA assertions and separate QA file. |
| Original CrewSync status/attempt independently verified | BLOCKED | No authoritative CrewSync readback in authorized tools/read scope. |
| Positive, negative, and crash/retry tests | PRESENT, runtime blocked | Five deterministic cases including duplicate `fact_id` and two terminal replay modes. |
| Immutable evidence SHA | PRESENT | Exact test/source/producer artifact hashes recorded above. |
| Factual violations recorded | PRESENT | Terminal replay resets completed state and permits repeated synthesis by source path. |
| No foreign edits | PASS by scoped write receipt | Only the two authorized independent QA paths were written. |
| Focused runtime evidence | BLOCKED | `PYTHON_VENV_UNAVAILABLE`; pytest did not collect tests. |
| Independent acceptance | UNACCEPTED | Separate source repair, rerun, reducer, and authoritative terminal readback remain required. |

## Reducer / Repair Handoff

1. Resume the original producer/source owner for a sticky repair to terminal replay idempotency in `reasoners/deep_research_ext/research_run.py` and/or `reasoners/deep_research_ext/verified_pipeline.py`.
2. In a checkout with a regular local `.venv`, run:

```text
.venv\Scripts\python.exe -m pytest -q tests/test_releasegate_independent_verified_recovery_20261013.py
```

3. After the focused suite passes, run affected release-gate regressions:

```text
.venv\Scripts\python.exe -m pytest -q tests/test_releasegate_native_evidence_20261013.py tests/test_releasegate_restart_resume_20261013.py tests/test_base20_independent_restart_abstention_qa.py tests/test_verified_pipeline_wave_full_cycle.py
```

4. Independently verify exact Git `HEAD`, both original producer attempt/thread terminal receipts, and the immutable typed worker-result publication before any reducer recommends scoped acceptance.
5. Keep the live-provider test skipped unless external provider execution is explicitly admitted; never convert that skip or mocked retrieval into live evidence.

This QA packet is evidence only. It does not accept, promote, integrate, deploy, or mark any producer or product task terminal.
