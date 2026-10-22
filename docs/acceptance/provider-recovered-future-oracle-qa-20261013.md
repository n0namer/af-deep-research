# Provider-Recovered Future Oracle QA — 2026-10-13

Status: CANDIDATE / UNACCEPTED

## Authority and source binding

- Current task: `af-deep-research:v2-provider-recovery-postfailure-independent-qa-20261013-r1`
- Current attempt: `attempt-153ce2e3-9b32-4595-a9b5-4b0c02162691`
- Current session: `manual-20261013-provider-recovery-postfailure-w-a8f615541d524c86`
- Previous failed runtime-QA task: `af-deep-research:v2-native-future-oracle-runtime-independent-qa-20261013-r1`
- Previous failure: physical Codex exit `1` after OpenCodex `127.0.0.1:10110` returned `503` and timed out.
- Active oracle artifact: `docs/acceptance/native-future-independent-oracle-20261013.md`
- Trusted prelaunch Git commit: `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`
- Trusted manifest SHA-256: `f5c2b06b71eb58cfc69dde6e4acf503f8bd183d65feff81d85d87824e7156dfa`
- Trusted task-data SHA-256: `794dd87d2d8f6b28947e3faca1c6626c7749d808fcb93413d04f929c1c6214a3`
- Final QA test SHA-256: `e6694dbaecac599641b733571fe0acfb2f209ce0bb5a173e5f6c0b2a2efbf3be`

The Git, manifest, and task identities above are coordinator-supplied bindings. This lane had no authorization to inspect Git metadata or native source modules, so it does not claim an independently recomputed commit or source-interface comparison.

## Outcome

A new non-mutating provider-recovery regression harness was added at `tests/test_future_oracle_provider_recovery_20261013.py`. It separates provider liveness from product correctness and never creates synthetic native evidence.

The harness contains five focused checks:

1. Probe `GET http://127.0.0.1:10110/health` by default and require HTTP `200`.
2. Validate a real native positive path from externally supplied immutable evidence.
3. Validate a real retryable-failure, restart-load, retry-dispatch, persistence, and terminal-publication path.
4. Reuse the real evidence to prove a deliberately wrong source SHA binding is rejected.
5. Bind the run to the trusted prelaunch Git commit.

The coordinator reported that provider health recovered to HTTP `200`, but the scoped Python runner failed before test collection. Therefore this attempt did not independently observe the health response and does not convert the reported health recovery into a test PASS.

## Exact native regression command and exit

Authorized runner invocation:

```text
go_wave.run_project_tests({"file":"tests/test_future_oracle_provider_recovery_20261013.py"})
```

Exact receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
source_identity_sha256=06c0416d36248811f99589d60d35e8a6ee10df798b6e182033da972b0d26a792
exit_code=null
signal=null
duration_limit_ms=120000
stdout=""
stderr="A regular local .venv Python executable is required."
```

The receipt was produced before final self-review hardening changed the test file to SHA-256 `e6694dbaecac599641b733571fe0acfb2f209ce0bb5a173e5f6c0b2a2efbf3be`. The identical unavailable `.venv` dependency was not retried, as required by the task's infrastructure-failure policy. No final test PASS is claimed.

## Required runtime inputs

The focused test consumes only real externally produced evidence:

```text
AF_OPENCODEX_BASE_URL=http://127.0.0.1:10110
AF_NATIVE_ORACLE_EVIDENCE=C:\absolute\path\native-oracle-evidence.json
AF_NATIVE_ORACLE_EXPECTED_SOURCE_SHA256=<64 lowercase hex source SHA-256>
AF_NATIVE_ORACLE_EXPECTED_GIT_SHA=e10580c89eac7a4f6efb50c921ae9107ce8ad8dc
```

If either native evidence variable is absent, the positive, restart/replay, and wrong-source checks emit `SKIP` with `BLOCKED_NATIVE_EVIDENCE`; they do not fabricate fixtures or pass product behavior. Provider health remains an independent check and cannot satisfy the native regression gates by itself.

## C4 DTO and API compatibility boundary

The harness encodes the active oracle's exact `af-native-releasegate-oracle.v1` boundary.

### Root DTO

Exact keys: `schema`, `source_sha256`, `native_contract_version`, `producer_task_key`, `qa_task_key`, `captured_at`, `scenarios`.

Constraints:

- `schema` equals `af-native-releasegate-oracle.v1`.
- `source_sha256` equals the independently supplied 64-character lowercase SHA-256.
- `native_contract_version` matches `c4-native-v<positive integer>`.
- Producer and QA task keys are non-empty and different.
- `captured_at` is RFC3339 UTC.

### Request DTO

Exact keys: `task_key`, `project`, `attempt_id`, `session_id`, `payload_sha256`, `source_sha256`, `idempotency_key`, `checkpoint_seq`.

Identity, payload, idempotency, source binding, non-negative checkpoints, and monotonic checkpoints are enforced across the event stream.

### Receipt DTO

Exact keys: `receipt_id`, `task_key`, `attempt_id`, `session_id`, `status`, `source_sha256`, `checkpoint_seq`, `persisted_at`, `result_sha256`.

Allowed statuses are `PENDING`, `FAILED_RETRYABLE`, `RETRYING`, `CANDIDATE`, `BLOCKED`, and `FAILED`. Receipt identity must match the request, source SHA must remain stable, checkpoints must be monotonic and not precede the request checkpoint, and timestamps must be RFC3339 UTC.

### Event envelope and paths

Exact keys: `event_id`, `event`, `occurred_at`, `persistence_id`, `request`, `receipt`.

Required positive path:

```text
request_submitted -> request_persisted -> receipt_persisted -> terminal_result_published
```

Required failure/restart path:

```text
request_submitted -> request_persisted -> attempt_failed -> restart_loaded -> retry_dispatched -> receipt_persisted -> terminal_result_published
```

The harness requires unique event IDs, chronological timestamps, stable identity, exact reload of the persisted `FAILED_RETRYABLE` receipt, monotonic request and receipt checkpoints, exactly one terminal publication, byte-equivalent persisted and terminal receipts, and final `CANDIDATE` status for both successful paths.

These are real contract signatures encoded from the active BMad acceptance artifact. Actual native API compatibility remains `BLOCKED` because current native source files and immutable native evidence were outside this task's read scope. Signature drift must be repaired by the original source owner after source-backed independent QA; this report does not relax the oracle.

## Acceptance matrix

| Gate | Status | Evidence |
| --- | --- | --- |
| New independent QA harness | `PASS` | New file only; final SHA-256 `e6694dbaecac599641b733571fe0acfb2f209ce0bb5a173e5f6c0b2a2efbf3be`. |
| Health 200 distinguished from test PASS | `PASS` | Dedicated health assertion plus explicit report that runner never collected tests. |
| Exact regression command and exit | `PASS` | Scoped runner receipt records `BLOCKED`, `PYTHON_VENV_UNAVAILABLE`, and `exit_code=null`. |
| Real positive native path | `BLOCKED` | Runner unavailable and no immutable native evidence was supplied. |
| Real negative/restart/replay path | `BLOCKED` | Runner unavailable and no immutable native restart evidence was supplied. |
| Wrong-source negative check | `BLOCKED` | Implemented against real evidence only; not executed because `.venv` is unavailable. |
| Current C4 native API compatibility | `BLOCKED` | Native source modules were not in read scope. |
| Product ReleaseGate | `UNACCEPTED` | Independent reducer and authoritative terminal readback remain required. |

## Affected-only repair and next evidence

1. Restore a regular local `.venv` Python executable for the scoped runner.
2. Supply immutable evidence generated by the real native transport, persistence, restart, retry, receipt, and terminal-publication path.
3. Set the independently computed source SHA-256 and rerun the exact focused target once.
4. If DTO keys, enums, or paths differ from native source, route affected-only repair to the original source owner; do not weaken this QA harness without source-backed evidence.
5. Send the command receipt, native evidence identity, source-interface comparison, and terminal publication readback to the C4 reducer.
6. Independent verifier/reviewer and coordinator perform final acceptance; this candidate does not self-accept.

## Self-review

- Writes are limited to the new QA test and this acceptance report.
- No prior oracle, reducer, production source, task, lease, or terminal state was modified.
- The test performs no provider mutation or production send.
- Missing native evidence skips explicitly rather than manufacturing a product PASS.
- Health liveness is not treated as persistence, replay, DTO, or terminal-publication proof.
- Positive, restart/replay, and source-binding failure behavior are separate assertions.
- The runner blocker is preserved exactly and was not retried indefinitely.
- Final runtime status is not claimed because the final test SHA was not executed.
- Product acceptance remains reducer-owned and `UNACCEPTED`.
