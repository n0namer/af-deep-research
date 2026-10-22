# MVP Independent Audit — Verified Source Report Full Cycle

Status: CANDIDATE / UNACCEPTED

## Audit identity

- Task: `af-deep-research:v2-mvp-independent-audit-verified-source-report-fullcycle-20261014-r8`
- Attempt: `attempt-c8313e2b-69af-43dc-8064-eab706680423`
- Crew session: `manual-20261014-basefive-mvp-10owners-r8-af-dee-fccf5a20dd542764`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Prelaunch Git source: `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`
- Decision: `BLOCKED` for product acceptance; preserve `CANDIDATE / UNACCEPTED`.

## Scope and source identities

This audit is source-readonly for producer code and tests. The only project write is this reserved QA document.

| Input | Evidence |
| --- | --- |
| Project instructions | `AGENTS.md`, SHA-256 `490bdf70833a3ca86788830ead5fb9f7d8e8f37a0446626d166f5ac5e2107d08` |
| C4 acceptance artifact | `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md`; status `CANDIDATE / UNACCEPTED` |
| Producer source | `reasoners/deep_research_ext/verified_pipeline.py`, SHA-256 `1ea0b249afc0c84d57824b78c5b4e6b3a79ae40a5b5890ed1a91d1046a872d1f` |
| Existing adversarial test | `tests/test_northstar_independent_source_adversarial_20261014.py`, runner source identity SHA-256 `cff4ac0734798be957a545db4aa43e6f2a02fd4f4019b553cd1850163832be9f` |
| Required MVP audit test | `tests/test_mvp_verified_source_report_20261014.py`, absent from the target checkout |

## Acceptance matrix

| Requirement | Status | Evidence-backed result |
| --- | --- | --- |
| Exact typed DTO/revision proven against current Git/source SHA and C4 interface | `BLOCKED` | The permitted C4 artifact is a prior reducer candidate and explicitly says C4 interface/DTO sources and original producer/QA receipts are unavailable. The readable producer source does not expose the missing C4 DTO contract. |
| Real positive scenario is durable and reproducible | `BLOCKED` | The readable adversarial test defines `test_unique_source_entailment_updates_claim`, but the authorized pytest runner could not start because a regular local `.venv` is required. No runtime PASS is inferred. |
| Wrong identity fails closed without mutation | `BLOCKED` | `test_source_mismatched_assessment_is_rejected_without_mutation` defines the required negative assertion, but it was not executed. Source inspection alone is not runtime proof. |
| Malformed/duplicate evidence fails closed | `BLOCKED` | `test_duplicate_source_url_abstains_in_verified_only_mode` defines a duplicate-source negative path, but it was not executed. The requested MVP audit test is absent. |
| Cancellation fails closed without unauthorized effect | `BLOCKED` | No cancellation-focused test is present in the permitted test evidence, and no cancellation contract is readable in the permitted producer-source slice. This behavior cannot be asserted. |
| Crash/restart replay avoids duplicate persisted external effect | `BLOCKED` | `test_restart_retry_preserves_ledger_after_failure_then_verifies` defines retry/restart ledger preservation, but it was not executed. The C4 artifact also records the native restart E2E proof as unavailable. |
| Focused and affected regression evidence | `BLOCKED` | The exact requested focused test is missing; the available adversarial test is runner-blocked. No unrelated test was substituted. |
| Product acceptance | `FAIL` | Required runtime and interface evidence is missing. This is a release-gate failure classification, not a claim that producer behavior is intrinsically incorrect. |

## Source inspection notes

`execute_verified_pipeline` in the producer source has explicit checkpoint stages for research-package readiness, evidence verification, synthesis readiness, programmatic abstention, post-generation rejection, and completed delivery. It also records a run identifier and checkpoint sequence in returned metadata. These are source observations only; they do not prove persistence, replay idempotency, DTO compatibility, or cancellation behavior without executable evidence and the missing adjacent contracts.

The source includes a checkpoint-resume branch that reuses a cached research package when the run is no longer at the `started` stage. The permitted source slice does not establish whether all external effects are idempotent across replay, so no restart PASS is claimed.

## Test definitions observed

The available adversarial test contains:

1. One positive source-entailment update.
2. One duplicate-source-url abstention negative.
3. One mismatched source-identity non-mutation negative.
4. One transient failure followed by retry/restart verification.

These are test intent and source evidence, not executed results.

## Exact validation receipts

Requested focused command:

```text
python -m pytest -q -p no:cacheprovider tests/test_mvp_verified_source_report_20261014.py
```

Receipt:

```text
status=BLOCKED
code=test_file_missing
engine=python:pytest
exit_code=null
```

Available affected test command:

```text
python -m pytest -q -p no:cacheprovider tests/test_northstar_independent_source_adversarial_20261014.py
```

Receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
source_identity_sha256=cff4ac0734798be957a545db4aa43e6f2a02fd4f4019b553cd1850163832be9f
exit_code=null
stderr="A regular local .venv Python executable is required."
```

The identical runner blocker was not retried. No production source or test file was modified.

## Required evidence before acceptance

1. Restore or provide the exact `tests/test_mvp_verified_source_report_20261014.py` file at the authorized source revision.
2. Run the focused test in an environment with the required regular local `.venv`, preserving the exact command, exit code, count, and source/test SHA values.
3. Run the available adversarial test and retain its positive, two-negative, and restart receipts.
4. Provide the exact C4 DTO/interface source identities and original producer/independent-QA typed publications with authoritative terminal readback.
5. Exercise cancellation and native task-to-result restart/idempotency under the original owner and scope; do not infer these from this source-only audit.
6. Re-run the independent verifier after evidence fan-in. Preserve `CANDIDATE / UNACCEPTED` until the independent reviewer and coordinator authorize acceptance.

## Self-review

- No producer code or test was changed.
- Missing tests and infrastructure-blocked execution are reported as `BLOCKED`, never as PASS.
- Prior C4 candidate evidence is not promoted to product acceptance.
- Source hashes are distinguished from runtime receipts.
- No cancellation, DTO, persistence, or restart claim is inferred without the required evidence.
- The document remains a candidate QA artifact and does not self-accept.
