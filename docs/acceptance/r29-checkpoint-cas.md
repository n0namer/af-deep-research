# R29 checkpoint CAS fencing

Status: CANDIDATE / UNACCEPTED

## Contract

ResearchRun.source_owner is part of the persisted checkpoint compare-and-swap identity. A checkpoint update is accepted only when the in-memory snapshot and persisted checkpoint have the same owner identity, and any caller-supplied owner agrees with that identity. This fences a stale snapshot from an owner that did not create or currently own the checkpoint.

The existing checkpoint sequence and source-revision checks remain active. The implementation does not change checkpoint storage format or terminal-task state.

## Evidence

Production source: reasoners/deep_research_ext/research_run.py
Focused test: tests/test_r29_checkpoint_cas.py

Positive coverage:
- matching owner and expected sequence persists the next checkpoint.

Adversarial coverage:
- a caller with a foreign owner is rejected;
- a stale checkpoint sequence is rejected without overwriting the current checkpoint;
- a stale unowned in-memory snapshot cannot adopt a checkpoint claimed by another owner;
- a foreign source revision is rejected during resume.

Validation command:

    python -m pytest -q tests/test_r29_checkpoint_cas.py

Acceptance remains with independent QA/reducer and CrewSync terminal readback.
