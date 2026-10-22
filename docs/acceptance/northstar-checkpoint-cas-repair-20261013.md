# Northstar Checkpoint CAS Repair — 2026-10-13

Status: CANDIDATE / UNACCEPTED

## Authority

- Task: `af-deep-research:v2-northstar-checkpoint-stale-cas-red6-spawnfix-repair-20261013-r2`
- Attempt: `attempt-5684d4c0-c8bf-486f-b26b-80f887e4e6fc`
- Session: `manual-20261013-research-native-red6-production-a3bf0d817b31b218`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Acceptance remains with independent QA and authoritative coordinator readback.

## Root cause

`checkpoint_research_run` compared `expected_checkpoint_seq` only with the caller-supplied `ResearchRun`. Two writers holding the same sequence-zero object could therefore both pass the check, and the stale writer could replace the persisted sequence-one checkpoint and its newer evidence.

## Functional delta

- Load the persisted checkpoint before checkpoint ownership and sequence validation.
- Compare `expected_checkpoint_seq` with the persisted sequence when the checkpoint exists.
- Reject a different logical owner reusing the same `run_id` by checking query, creation timestamp, replay source identity, and conflicting non-null source revision.
- Build the next checkpoint from persisted state so omitted evidence, payload, budgets, gaps, conflicts, and history retain the latest durable values.
- Preserve the public function signature, return type, schema version `0.1`, stage names, source-revision fencing, and existing exception hierarchy.

## Focused regression coverage

`tests/test_northstar_checkpoint_cas_regression_r1.py` adds:

1. A positive persisted-sequence CAS update using a stale caller object with the correct persisted expected sequence.
2. A wrong-owner rejection for a different logical run attempting to reuse an existing `run_id`.
3. A crash/replay stale-writer rejection proving the latest verified evidence and accepted report remain durable.

The original stale-writer case remains in `tests/test_northstar_research_persistence_20261013.py`.

## Source identities

| File | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| `reasoners/deep_research_ext/research_run.py` | `713caa8e1d6c4e96127b72571b42ab34882542cd478976fe83bb3e2785681d4c` | `338ed08b70260969a7e73e30df0939df1d039bf3599aa4e6ab993b32457350fb` |
| `tests/test_northstar_research_persistence_20261013.py` | `53fd9ef2d10c65c0c3f90f7ad7d57e5851d9dd4ed12f8890bef0d4828859e5e1` | unchanged (read-only) |
| `tests/test_northstar_checkpoint_cas_regression_r1.py` | new | `41df87cab69a29bb35af68f0f51adce698b970d03ddcd62cdc9c25af9f2419d5` |

## Verification receipt

Requested validation:

```text
python -m pytest -q -p no:cacheprovider tests/test_northstar_research_persistence_20261013.py tests/test_northstar_checkpoint_cas_regression_r1.py
```

The scoped runner was invoked once against the original affected test and returned:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
exit_code=null
source_identity_sha256=53fd9ef2d10c65c0c3f90f7ad7d57e5851d9dd4ed12f8890bef0d4828859e5e1
stderr="A regular local .venv Python executable is required."
```

The same missing dependency was not retried. No test PASS is claimed. Independent QA must run the requested two-file pytest command with a regular local `.venv` Python executable.

## Compatibility and scope review

- C4 API compatibility: `checkpoint_research_run` parameters and `ResearchRun` DTO fields are unchanged; stale sequence still raises `ResearchRunCheckpointError`; source revision still raises `StaleResearchRunError`.
- Existing unsaved-run behavior remains available because the supplied run is used when no persisted checkpoint exists.
- Writes are limited to the three authorized paths.
- No Ruflo Native task, lease, claim, terminal state, dependency, lockfile, commit, push, or deployment was modified.

## Remaining gate

The implementation and regression artifacts are ready for independent execution, but the local Definition of Done remains infrastructure-blocked until the original and new pytest cases execute with exit code `0`.
