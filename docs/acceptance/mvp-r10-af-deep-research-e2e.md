# MVP r10 Grounded Report E2E

Status: CANDIDATE / UNACCEPTED

## Scope and source of truth

- Target: `af-deep-research`.
- Active BMad gate: `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md`.
- Goal: freeze source identity into a typed report, abstain safely on unresolved requirements, and resume without duplicate terminal effects.
- No external provider call is required by this slice.

## DTO contract

`VerifiedSourceReport` uses DTO version `r10` and records:

- `source_revision` and `source_owner` for ownership/fencing;
- `source_file_sha256` as the immutable source-file identity;
- unique `GroundedFact(fact_id, source_id, source_sha256)` records;
- `abstained_requirement_ids` for explicit partial abstention;
- a deep-copied payload so caller mutation cannot alter persisted evidence.

Replay identity includes all of those fields plus report/query/source identity. A same-revision payload with a changed source SHA, fact set, owner, or abstention set is rejected rather than replayed.

## Durable behavior

`DurableVerifiedSourceReportStore` clones reports at load/save boundaries, fences writes by `source_owner`, and records terminal `effect_id` values exactly once. `persist_grounded_verified_report` checks cancellation before persistence and before effect application. `resume_grounded_verified_report` rejects stale owners and stale source-file hashes.

## Focused acceptance matrix

| Scenario | Test | Expected result |
| --- | --- | --- |
| Positive typed durable result | `test_positive_report_records_source_sha_facts_abstention_and_one_effect` | Persist once; replay does not duplicate effect; payload remains immutable. |
| Invalid ownership | `test_invalid_owner_fails_closed_without_persisting_or_effect` | Reject before store mutation. |
| Invalid payload/cancellation | `test_invalid_payload_and_cancellation_fail_closed` | Reject malformed DTO and cancelled write without mutation. |
| Crash/replay and stale revision | `test_crash_replay_does_not_duplicate_terminal_effect_or_accept_stale_revision` | Reject skipped revision; replay terminal effect idempotently. |
| Resume fencing | `test_resume_rejects_stale_source_identity_and_file_hash` | Reject wrong owner and changed source SHA. |
| Live source SHA | `test_source_file_sha256_is_immutable_file_identity` | Record a deterministic 64-character SHA-256 digest. |

## Verification receipt

Requested command:

```text
python -m pytest -q tests/test_northstar_mvp_r10_grounded_report.py
```

Actual scoped runner receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
exit_code=null
stderr="A regular local .venv Python executable is required."
```

The identical denied test command was not retried. Therefore this artifact preserves a candidate/unaccepted result and does not claim runtime GREEN.

## Self-review

- Source SHA, owner, revision, facts, DTO version, and abstention IDs participate in replay identity.
- Payloads are deep-copied at construction and durable store boundaries.
- Owner mismatch, malformed payload, cancellation, stale revision, stale source SHA, and duplicate effect paths fail closed.
- No external API, live task, lease, lock, deployment, commit, or unrelated source file is changed.
- Independent verifier/reviewer and coordinator terminal readback remain required.
