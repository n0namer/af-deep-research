# R29 CAS concurrency E2E — candidate evidence

Status: CANDIDATE / UNACCEPTED

## Scope and source evidence

The current ResearchRunStore uses a temporary file plus os.replace() for atomic publication, but its read/check/write path has no cross-process compare-and-swap token or inter-process lock. checkpoint_research_run() can therefore let two processes validate the same checkpoint_seq before either save, after which the later replacement can overwrite the winner.

The authorized production files are read-only for this task. This candidate adds a real multiprocessing regression test and records the required production repair boundary; it does not claim the product fix is implemented.

## Checks

- Positive: two real OS processes race from one stale snapshot; exactly one commit must remain.
- Negative 1: source revision mismatch is rejected.
- Negative 2: source owner mismatch is rejected.
- Negative 3: corrupt persisted JSON is rejected.
- Required command: python -m pytest -q tests/test_r29_cas_concurrency_e2e.py.

## Current blocker

The test requires a production change in reasoners/deep_research_ext/research_run.py (or an explicitly authorized shared persistence primitive) to perform an atomic revision/token CAS at the persistence boundary. That file is outside this attempt's write scope, so the test is expected to expose the defect until the coordinator grants the affected production repair to the owning lane.

No acceptance or PASS is inferred without a native pytest exit code 0. The scoped MCP runner does not execute Python tests, so this attempt preserves the exact requested command as unrun infrastructure evidence rather than converting it to PASS.
