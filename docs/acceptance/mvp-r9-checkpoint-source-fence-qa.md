# MVP r9 Checkpoint Source-Fence QA

Status: `QA_READY_NOT_FINAL` / `CANDIDATE` / `UNACCEPTED`

## Authority and scope

- Task: `af-deep-research:v2-hyperwave-independent-checkpoint-source-fence-20261014-r9`
- Attempt: `attempt-69883be7-4d22-4ea7-97e9-5a1b8b687330`
- Session: `manual-20261014-basefive-hyperwave-r9-af-deep-r-71b980352a4a9f1d`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Producer state: r9 may still be running; this report must not be treated as final acceptance.
- Write scope used: `tests/test_northstar_mvp_r9_source_adversarial_qa.py`, this report.
- Product source was not modified.

## Frozen inputs

| Input | Identity | Evidence |
| --- | --- | --- |
| Coordinator prelaunch Git state | `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc` | Trusted task context; not independently recomputed in this read-restricted lane. |
| C4 reducer signature | `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md` | SHA-256 `e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce`. |
| Checkpoint source | `reasoners/deep_research_ext/research_run.py` | SHA-256 `1a3d5e432f43687e09218512897b61d0832eb803d728288c7466f83b81715b5d`. |
| Independent QA suite | `tests/test_northstar_mvp_r9_source_adversarial_qa.py` | SHA-256 `29183e22dbff5697f3d415082b0418200e8d600ea5ca3d59addcad20ffea7381`. |
| Project instructions | `AGENTS.md` | SHA-256 `490bdf70833a3ca86788830ead5fb9f7d8e8f37a0446626d166f5ac5e2107d08`. |

The source SHA and C4 signature above are the comparison boundary for this QA attempt. A later producer change requires a fresh QA run and new receipts.

## QA coverage

The independent suite contains four focused cases:

1. **Native positive / provenance:** creates a real `ResearchRunStore`, persists a retrieval checkpoint, and verifies source revision, source ID, provider receipt, and resumability.
2. **Foreign source rejection:** attempts resume with `sha-foreign` against a `sha-c4-r9` checkpoint and expects `StaleResearchRunError` before loading usable work.
3. **Stale owner/sequence rejection:** replays an older checkpoint sequence and expects `ResearchRunCheckpointError`.
4. **Crash/restart replay boundary:** resumes a persisted checkpoint, deduplicates repeated provider call IDs, advances exactly once, and rejects replay from the pre-restart object as stale.

The test-only change exercises existing product contracts; no producer or live task state is changed.

## Runtime evidence

Requested focused command:

```text
python -m pytest -q -p no:cacheprovider tests/test_northstar_mvp_r9_checkpoint_fence.py
```

The requested checkpoint-fence file is absent from the permitted checkout listing. The newly authorized independent suite was submitted to the scoped runner as:

```text
run_project_tests(tests/test_northstar_mvp_r9_source_adversarial_qa.py)
```

Actual runner receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
source_identity_sha256=29183e22dbff5697f3d415082b0418200e8d600ea5ca3d59addcad20ffea7381
exit_code=null
stderr="A regular local .venv Python executable is required."
```

No identical retry was made. Therefore no runtime PASS, test count, or regression claim is asserted.

## Acceptance matrix

| Requirement | Status | Evidence-backed decision |
| --- | --- | --- |
| Current source and C4 signature pinned | `PASS_STATIC` | Exact source/report signatures are recorded above; Git identity is coordinator-supplied and explicitly not recomputed. |
| Real native positive persists typed checkpoint | `BLOCKED_RUNTIME` | Test is present, but pytest cannot start without the required local `.venv`. |
| Foreign source fails closed | `BLOCKED_RUNTIME` | Test asserts `StaleResearchRunError`; no execution receipt exists. |
| Two adversarial stale/replay cases fail closed | `BLOCKED_RUNTIME` | Test covers foreign revision and stale checkpoint sequence; no execution receipt exists. |
| Crash/restart has no duplicate effects or stale-owner corruption | `BLOCKED_RUNTIME` | Test covers provider-call deduplication and stale replay rejection; no execution receipt exists. |
| Focused native plus affected regression | `BLOCKED` | Authorized Python runner is unavailable; no unrelated test was substituted. |
| Product acceptance | `UNACCEPTED` | Independent verifier/reviewer, QA/reducer, and authoritative CrewSync terminal readback remain required. |

`PASS_STATIC` means source-backed inspection only; it is not a runtime pass or product acceptance.

## Self-review and remaining work

- Product code remains untouched.
- Test storage is isolated under pytest `tmp_path`; no default `/e2e` path is used.
- The test suite does not mutate live Ruflo/CrewSync state or create foreign claims.
- No test result was converted from an infrastructure block into PASS.
- The report preserves the exact source and test hashes available in this lane.
- Remaining blocker: provision the required regular local `.venv` Python executable, then rerun the exact independent suite and the affected checkpoint-fence/regression command under the same source boundary.
- If the producer changes `research_run.py`, discard this boundary and regenerate the QA receipt.
