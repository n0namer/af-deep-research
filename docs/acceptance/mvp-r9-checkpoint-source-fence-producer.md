# MVP R9 Checkpoint Source-Fence Producer

Status: CANDIDATE / UNACCEPTED

## Scope

This producer extends `reasoners/deep_research_ext/research_run.py` without activating `verified_pipeline.py` or `verification_bridge.py`.

- Checkpoints persist the frozen `source_revision` and explicit `source_owner`.
- Checkpoint sequence comparison rejects stale writers before replacing durable state.
- Provider call IDs and evidence IDs are normalized and deduplicated across checkpoint/restart.
- Resume validates source revision/owner and returns the durable report, abstention marker, missing gaps, and effect IDs.
- Atomic temporary-file replacement preserves the last complete checkpoint after interruption.

## Focused evidence

- Positive native path persists a verified-partial report and rehydrates it after restart.
- Wrong source owner is rejected for both checkpoint and resume, with the prior checkpoint unchanged.
- Stale source revision and stale in-memory checkpoint writers fail closed.
- Cancelled/partial runs retain provider call IDs and report state so resume does not repeat the recorded effect.

The focused test command is:

```text
python -m pytest -q -p no:cacheprovider tests/test_northstar_mvp_r9_checkpoint_fence.py
```

Acceptance remains with independent QA/reducer and authoritative CrewSync terminal readback; this artifact does not claim `ACCEPTED` or `ACCEPTED_GREEN`.
