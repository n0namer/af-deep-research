# Longbundle Holdout Truth — 2026-10-14

Status: CANDIDATE / UNACCEPTED

## Authority

- Task: `af-deep-research:v2-longbundle-frozen-holdout-e2e-20261014-r1`
- Attempt: `attempt-2beb8c9b-2484-41d9-81d9-0cc705c301e5`
- Session: `manual-20261014-base5-longbundles-northstar-r1--068efba01679c498`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Authorized writes: this acceptance receipt and `tests/test_northstar_longbundle_holdout_truth_20261014.py` only.
- Acceptance authority remains with independent review, reducer coordination, and authoritative CrewSync readback.

## Value and bounded DoD

This lane adds source-backed end-to-end assertions for the frozen 24-case development baseline and the separate six-case holdout corpus. It verifies one positive baseline, two evidence-removal negatives, explicit adversarial-signal abstention, and persisted research-run restart/fencing behavior without making live-provider quality claims.

The bounded DoD is only partially executable in this environment: the focused Python runner requires a regular local `.venv`, which was unavailable. No unrun check is promoted to PASS.

## Source-bound API and immutable identities

The test uses existing public functions and DTOs; it does not change production code or introduce a competing interface.

- `evaluation.py` SHA-256: `0399e49ab5e5867f57c2731fa68b94b6fca35282ddb0c64c7baa098fc03f2f6d`
- `research_run.py` SHA-256: `338ed08b70260969a7e73e30df0939df1d039bf3599aa4e6ab993b32457350fb`
- `ResearchRunStore(root=None)` persists JSON checkpoints with atomic replacement.
- `begin_research_run(query, *, store=None, source_revision=None) -> (ResearchRunStore, ResearchRun)` creates or resumes an owned run.
- `checkpoint_research_run(store, run, *, stage, status=None, source_revision=None, expected_checkpoint_seq=None, source_ids=None, evidence_summary=None, coverage_state=None, open_gap_ids=None, conflicts=None, budgets=None, payload=None) -> ResearchRun` enforces sequence and source-revision fencing.
- `resume_research_run(store, run_id, *, source_revision=None) -> (ResearchRun, dict)` returns the safe next stage, deduplicated provider IDs, and terminal state.
- `replay_frozen_fixture(fixture, corpus)` returns a replay result with gate, observation, and used source IDs.
- `remove_all_admissible_evidence(corpus)` and `mutate_corpus_remove_documents(corpus, document_ids)` provide causal negative mutations.
- `evaluate_stored_semantic_snapshot(fixture, snapshot)` reports missing hard signals instead of silently passing.

## Assertions added

`tests/test_northstar_longbundle_holdout_truth_20261014.py` adds five focused assertions:

1. Positive: all 24 frozen-core fixtures and all six distinct holdout fixtures replay to passing baselines.
2. Negative 1: removing all admissible holdout evidence fails every holdout gate.
3. Negative 2: removing a decisive admissible source from `DR-H02` fails closed and marks `R1` unresolved.
4. Negative/adversarial: `DR-H04` is `EVIDENCE_MISSING` when `prompt_injection_success` is absent, even with otherwise clean requirement signals.
5. Crash/restart and fencing: checkpoint reload preserves the deduplicated provider call ID, while stale checkpoint sequence and stale source revision are rejected.

## Verification receipt

Requested validation command:

```text
python -m pytest -q -p no:cacheprovider tests/test_evaluation_suite.py tests/test_northstar_longbundle_holdout_truth_20261014.py
```

Focused authorized runner receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
file=tests/test_northstar_longbundle_holdout_truth_20261014.py
source_identity_sha256=db581396b94611a8441275509edf7db9653fbdc0031757a2bb92cf4e3ca0f84b
exit_code=null
stderr="A regular local .venv Python executable is required."
```

The affected regression suite was not retried after the same runner-level dependency blocker. Therefore this receipt contains no PASS claim and no test count.

## Self-review

- Writes remain inside the exact two-file scope.
- No production source, live task state, lease, lock, provider, or external claim was changed.
- The holdout IDs are asserted disjoint from the 24-case development core.
- Positive replay, evidence removal, abstention, restart, duplicate-provider-ID, sequence-fencing, and source-revision-fencing behavior are all represented in executable tests.
- The runner blocker is preserved verbatim and is not converted into a product result.
- This document remains CANDIDATE / UNACCEPTED pending an environment with a regular local `.venv`, fresh focused plus affected regression output, and independent review/reducer readback.

## Remaining

- Install or expose the required regular local `.venv` Python executable, then run the exact combined validation command once.
- Independent verifier/reviewer and reducer must assess the source-bound result before any acceptance decision.
