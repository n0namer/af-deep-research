# R29 Report Durable Store

Status: CANDIDATE / UNACCEPTED

## Scope and source evidence

This bounded receipt tests the existing ResearchRunStore report path. The inspected source is reasoners/deep_research_ext/research_run.py at source revision e10580c89eac7a4f6efb50c921ae9107ce8ad8dc. It serializes a completed run, flushes and fsyncs a temporary JSON file, and atomically replaces the checkpoint path. resume_research_run reloads the report from persisted payload state.

No reasoners/deep_research_ext/report_store.py exists in the authorized read scope, so this task does not claim a separate report-store production interface or modify production code.

## Definition of Done evidence

- Positive: a completed report survives recreation of ResearchRunStore and is returned by resume_research_run.
- Boundary: a report absent from the checkpoint is reported as absent; in-memory construction alone is not durability.
- Adversarial negatives: corrupt JSON, foreign source revision, stale checkpoint writer, and path traversal run ID all fail closed.
- Duplicate provider IDs are normalized on restart rather than replayed as duplicates.
- Test target: tests/test_r29_report_durable_store.py.

## Verification status

The authorized validation command is:

    python -m pytest -q tests/test_r29_report_durable_store.py

This artifact must be updated with the actual scoped runner receipt before any acceptance claim. The worker result remains CANDIDATE / UNACCEPTED; independent QA and CrewSync terminal readback own acceptance.

## Remaining risk

The tests exercise the native ResearchRunStore and restart/resume interfaces, but do not prove an operating-system power-loss guarantee beyond the implementation fsync/atomic-replace path, nor a full external provider E2E.
