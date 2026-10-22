# North Star Research Checkpoint C4 QA — 2026-10-13

Status: CANDIDATE / UNACCEPTED / RUNTIME BLOCKED

## Authority

- Task: `af-deep-research:v2-c4-native-acceptance-research-checkpoint-20261013-r1`
- Attempt: `attempt-fab8ea83-e1e8-4b25-83dd-af41ef036322`
- Session: `manual-20261013-c4-native-acceptance-frontier-r-ca5b55076135939d`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Production source is read-only in this lane; only the new focused test and this QA report are writable.
- Independent reviewer/reducer and authoritative CrewSync readback retain acceptance authority.

## Source-bound identities

| Artifact | SHA-256 | Evidence |
| --- | --- | --- |
| Git source revision | `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc` | Coordinator-supplied prelaunch binding. |
| `reasoners/deep_research_ext/research_run.py` | `713caa8e1d6c4e96127b72571b42ab34882542cd478976fe83bb3e2785681d4c` | Recomputed by scoped project reader. |
| `tests/test_northstar_research_persistence_20261013.py` | `53fd9ef2d10c65c0c3f90f7ad7d57e5851d9dd4ed12f8890bef0d4828859e5e1` | Final post-review SHA-256 from the scoped writer; the blocked runner receipt is bound to the prior `5d56d62ad1a588c5d21608d4458fcd69588003f8ba4c906bcd5c0811ad7561f5` version before the invalid-`run_id` case was added. |
| Active C4 BMad artifact | `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md` | Trusted SHA-256 `e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce`. |

## C4 component and DTO boundary

The scoped native boundary is the immutable `ResearchRun` DTO and these existing functions in `reasoners/deep_research_ext/research_run.py`:

- `ResearchRunStore.save(run) -> Path` performs atomic JSON checkpoint replacement.
- `ResearchRunStore.load(run_id, source_revision=...) -> Optional[ResearchRun]` validates schema/stage and fences foreign source revisions.
- `begin_research_run(query, store=..., source_revision=...) -> (store, run)` creates or reuses the AgentField `run_id` and imports a replay source.
- `checkpoint_research_run(store, run, stage=..., expected_checkpoint_seq=..., ...) -> ResearchRun` advances the checkpoint DTO.
- `resume_research_run(store, run_id, source_revision=...) -> (run, resume_plan)` exposes terminal state, remaining gaps, conflicts, and durable provider-call IDs.
- `recorded_provider_call_ids(run) -> tuple[str, ...]` deduplicates durable provider-call identities during replay.

The DTO schema version is `0.1`. The focused test does not replace this boundary with a fake store: it writes and reloads actual JSON files through `ResearchRunStore` in pytest temporary directories. Two tests replace only the optional AgentField identity lookup with deterministic IDs; those tests are controlled identity-seam checks and are not labelled live AgentField integration.

## Focused test matrix

| Scenario | Expected invariant | Runtime status |
| --- | --- | --- |
| Native terminal save/load/restart | Same DTO and path reload; terminal resume is `done`; one accepted report remains; provider call IDs are deduplicated; no temporary file remains. | `BLOCKED` — collection/execution did not start. |
| Same `run_id` after persistent restart | `begin_research_run` returns the original checkpoint and creates only one JSON checkpoint. | `BLOCKED` — collection/execution did not start. |
| Foreign query with reused `run_id` | Raises `ValueError` and leaves the original checkpoint unchanged. | `BLOCKED` — collection/execution did not start. |
| Invalid traversal `run_id` | Raises `ValueError` and writes no JSON file outside or inside the checkpoint root. | `BLOCKED`; added after the runner attempt during edge-case self-review. |
| Stale source revision after restart | Raises `StaleResearchRunError`. | `BLOCKED` — collection/execution did not start. |
| Crash replay and retry | Inherits research package/evidence once, records replay source, deduplicates provider-call IDs, and reuses the retry checkpoint after restart. | `BLOCKED` — collection/execution did not start. |
| Stale checkpoint writer | Must raise `ResearchRunCheckpointError` and preserve the newer evidence/checkpoint sequence. | `BLOCKED`; source review indicates a probable production defect described below. |

## Verification receipt

Requested focused command:

```text
python -m pytest -q tests/test_northstar_research_persistence_20261013.py
```

Authorized scoped runner result:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
source_identity_sha256=5d56d62ad1a588c5d21608d4458fcd69588003f8ba4c906bcd5c0811ad7561f5
exit_code=null
signal=null
stdout=""
stderr="A regular local .venv Python executable is required."
```

The identical runner call was not retried. Affected regression was not run because the same missing `.venv` dependency blocks Python execution and no authorized JavaScript/TypeScript test can prove this Python persistence boundary. No test is reported as PASS.

## Source-backed defect candidate

**FACT:** `checkpoint_research_run` compares `expected_checkpoint_seq` only with the caller-supplied `run.checkpoint_seq`. It does not reload the currently persisted checkpoint before `store.save(updated)`.

**HYPOTHESIS requiring the blocked runtime test:** Two workers can retain checkpoint sequence `0`; one persists sequence `1`, then the stale worker also passes `expected_checkpoint_seq=0` against its stale in-memory DTO and atomically replaces the newer file with different sequence-`1` evidence. The final focused test is designed to fail if this lost-update path remains reachable.

This is the root-cause-only repair route if runtime confirms the failure:

1. Route the production repair to the original C4 `ResearchRun` producer owner with write authority for `reasoners/deep_research_ext/research_run.py`; this QA task must not modify it.
2. Inside `checkpoint_research_run`, load the persisted `run_id` immediately before save and compare its sequence/source revision with the caller's expected sequence.
3. Reject missing, advanced, foreign-revision, or identity-mismatched persisted state before constructing/writing the update.
4. Resume this same QA task to run the seven focused tests and affected ResearchRun regressions against the exact repaired source SHA.

The exact original C4 producer task key is absent from the authorized evidence. It remains a coordinator lookup in existing CrewSync, not permission to invent a task or create a replacement owner.

## Adversarial self-review

- The positive path uses the real native JSON store and restart via a new `ResearchRunStore` instance.
- The report explicitly distinguishes deterministic identity substitution from live AgentField integration.
- The matrix includes foreign-query, stale-revision, crash/retry, terminal restart, duplicate provider-call, and stale-writer boundaries.
- No blocked or unrun check is converted to PASS.
- The test preserves production source as read-only and creates no mock production subsystem.
- The stale-writer claim is separated into source fact and runtime hypothesis.
- No C4 DTO version beyond the source-declared `SCHEMA_VERSION = "0.1"` is invented.
- No CrewSync task, lease, lock, terminal state, commit, or deployment was mutated.

## Worker-result publication receipt

The one permitted `go_wave.publish_worker_result` call returned:

```text
status=INVALID_REPORT
note_ref.scope=go-core.worker-result.v1
note_ref.key=af-deep-research:v2-c4-native-acceptance-research-checkpoint-20261013-r1:attempt:attempt-fab8ea83-e1e8-4b25-83dd-af41ef036322
validation=recorded_at: must be an ISO timestamp
```

The call used `recorded_at="2026-10-13"`; the contract requires a full ISO timestamp. It was not retried because this attempt authorizes exactly one publication call. A new sticky attempt must republish the same evidence with a full ISO timestamp and updated final report SHA; no VERIFIED or PENDING_SYNC publication exists for this attempt.

## Remaining gate

1. Provision a regular repository-local `.venv` Python executable without changing this task's source scope.
2. Run `python -m pytest -q tests/test_northstar_research_persistence_20261013.py` and record exact exit code, count, and failures.
3. If the stale-writer test fails as source analysis predicts, repair only under the original C4 production owner and rerun focused plus affected regression tests.
4. Require independent review and authoritative terminal readback before any GREEN or acceptance claim.
