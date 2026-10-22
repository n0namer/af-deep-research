# MVP r11 Independent C4 QA

Status: BLOCKED / UNACCEPTED

## Authority and scope

- Target: `af-deep-research` at the coordinator-provided Git identity `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`.
- Active BMad gate: `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md`.
- Task: `af-deep-research:v2-r11-sourcebound-native-qa-20261014-r1`.
- Attempt: `attempt-42ec47d9-cac3-4084-b30b-309fd766fc43`.
- Session: `manual-20261014-basefive-r11-qa-af-deep-researc-b84da70723d58d7f`.
- Authorized changes are limited to this report and `tests/test_northstar_mvp_r11_report_qa.py`; no producer source, original r10 test, live task, lease, lock, deployment, commit, or acceptance state was changed.

## Frozen-source comparison

The active C4 reducer artifact records the physical r10 `reasoners/deep_research_ext/verified_pipeline.py` SHA-256 as:

```text
1ea0b249afc0c84d57824b78c5b4e6b3a79ae40a5b5890ed1a91d1046a872d1f
```

A scoped read of the current producer returned:

```text
97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87
```

**Classification: STALE_SOURCE.** The current producer differs from the frozen r10 candidate. This is a source-identity finding, not proof of a product regression. It prevents a source-bound C4 release conclusion until the coordinator supplies a matching frozen candidate or replans QA against the new identity.

## Independent QA oracle

`tests/test_northstar_mvp_r11_report_qa.py` is a noncolliding oracle that uses the public r10 persistence boundary without importing or modifying the producer test. Its required scenarios are:

| Scenario | Boundary exercised | Expected behavior |
| --- | --- | --- |
| Source identity | `source_file_sha256` | Detect that the current producer differs from the recorded frozen r10 SHA. |
| Positive persistence | `persist_grounded_verified_report` | Persist a grounded report and apply one terminal effect. |
| Negative owner fencing | `persist_grounded_verified_report` | Reject an invalid owner before a report or effect is stored. |
| Negative source fencing | `resume_grounded_verified_report` | Reject a changed source SHA without mutating stored state. |
| Crash/replay | persistence + `resume_grounded_verified_report` | Reject a revision gap; replay the same terminal effect exactly once. |

The tests directly assert store state and effect counts after each failure path, so they do not rely on fixture-only claims or producer-test reuse.

## Native verification receipts

### Independent QA test

Requested command:

```text
python -m pytest -q tests/test_northstar_mvp_r11_report_qa.py
```

Actual scoped runner receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
test=tests/test_northstar_mvp_r11_report_qa.py
source_identity_sha256=eb26c911c27216f9e9e8479d57f7f4238f71329fa320f8b703e839bacc749d7c
exit_code=null
stderr="A regular local .venv Python executable is required."
```

### Prior r10 producer test

Requested command:

```text
python -m pytest -q tests/test_northstar_mvp_r10_grounded_report.py
```

Actual scoped runner receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
test=tests/test_northstar_mvp_r10_grounded_report.py
source_identity_sha256=6fa147faae338858604c8bfc96fad2ad8a14d7e703d0a6403833eed54f7ac3a1
exit_code=null
stderr="A regular local .venv Python executable is required."
```

The two commands are distinct required test targets. The runner gave the same infrastructure blocker for each; neither command was retried. No positive, negative, crash/replay, regression, or product-PASS claim is made without a non-blocked native exit code.

## C4 decision

| Gate | Status | Evidence-backed decision |
| --- | --- | --- |
| Source/test match to frozen r10 candidate | `STALE_SOURCE` | Current producer SHA differs from the frozen r10 SHA recorded by the active C4 reducer artifact. |
| Positive C4 persistence path | `BLOCKED` | The independent oracle exists but its native execution is blocked by the unavailable local `.venv`. |
| Negative owner fencing | `BLOCKED` | The independent oracle exists but its native execution is blocked. |
| Negative source-SHA fencing | `BLOCKED` | The independent oracle exists but its native execution is blocked. |
| Crash/replay idempotence | `BLOCKED` | The independent oracle exists but its native execution is blocked. |
| Prior r10 focused regression | `BLOCKED` | Its independently requested native runner invocation has the same `.venv` blocker. |
| Product RED classification | `NOT_ESTABLISHED` | No native product assertion executed; source drift alone is not a product failure. |
| C4 release/acceptance | `BLOCKED` | Stale source and missing native runtime receipts prevent reduction; independent reviewer and reducer remain required. |

## Adversarial self-review

- A SHA from an earlier C4 report is treated as a frozen comparison input, not as a freshly recomputed current source identity.
- The current SHA mismatch is not promoted to a behavioral product RED without a native test result.
- The QA test has unique IDs, owner, report ID, facts, and terminal-effect IDs; it cannot collide with the r10 producer test's state.
- Both negative tests verify post-failure state, preventing an exception-only false positive.
- The crash/replay test includes both skipped-revision rejection and duplicate-effect prevention.
- The source-identity test intentionally records drift rather than assuming the observed tree is r10.
- The original r10 test and producer source remain untouched.
- A runner denial is recorded as `BLOCKED`, never as a passing or skipped product check.
- The QA test and producer test have separate runner receipts and source identities.
- No typed publication, test runner success, or stale SHA is interpreted as `ACCEPTED_GREEN`.

## Recovery and remaining blockers

1. Provide a regular local `.venv` Python executable to the authorized test runner, then run the two commands above once each and preserve their exit codes, counts, and outputs.
2. Reconcile the current producer SHA `97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87` with the frozen r10 SHA, either by restoring the physical r10 candidate or by issuing a new source-bound QA task for the current source.
3. Submit fresh native receipts and source reconciliation to the independent C4 reducer. Only the reducer, independent reviewer, and authoritative CrewSync terminal readback may decide acceptance.
