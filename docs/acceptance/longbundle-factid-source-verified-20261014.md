# Long-Bundle Fact/Source Verification — 2026-10-14

Status: CANDIDATE / UNACCEPTED

## Authority

- Task: `af-deep-research:v2-longbundle-factid-source-verified-spawnfix-20261014-r2`
- Attempt: `attempt-a242d40b-9e75-47b4-ac40-b07c675b559d`
- Session: `manual-20261014-base5-longbundles-spawnfix-r2-a-6272d3d9c714fe93`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Acceptance authority: independent verifier/reviewer and authoritative CrewSync terminal readback.

## Bounded change

`reasoners/deep_research_ext/verification_bridge.py` now fails closed when source/article identity is ambiguous or malformed:

- duplicate source IDs in the ledger are not eligible;
- duplicate article IDs are not eligible;
- malformed article IDs are ignored rather than raising during eligibility collection;
- duplicate `fact_id` claims cannot be credited by one assessment;
- existing exact fact/source ownership, duplicate assessment, stale snapshot, and crash/restart behavior remains unchanged.

## Source and test identities

| File | SHA-256 | Role |
| --- | --- | --- |
| `reasoners/deep_research_ext/verification_bridge.py` | `9556010defde5e953949192127df0b0a03f877d5c512ae7438448682c588bfd4` | scoped implementation and representation repair |
| `tests/test_northstar_longbundle_factid_source_20261014.py` | `47280f06ffaf24e23da8ef75de870dc1286cc3ec0a6c3347e8c365f27fee2980` | five long-bundle regression cases with per-claim fencing assertions |

The implementation write receipt reported prior source SHA `c243deccda2aa1e3068430f9d9b5d0951f3f067c53053b7a23ebb2f1dc54189c` and repaired source SHA `9556010defde5e953949192127df0b0a03f877d5c512ae7438448682c588bfd4`.

## Acceptance matrix

| Gate | Status | Evidence |
| --- | --- | --- |
| B1 reproduce / C4 signature | `PASS` | Existing authorized tests cover exact fact/source ownership, foreign fact IDs, duplicate assessments, stale source snapshots, and crash/restart replay. The new long-bundle test extends the same contract to 26 claims / two batches. |
| B2 smallest scoped fix | `PASS` | Only `verification_bridge.py` was changed in implementation; the guard is limited to ambiguous source/article IDs and duplicate fact IDs. |
| B3 positive + negative + restart coverage | `BLOCKED` | New test file contains valid 26-claim preservation, wrong owner abstention, duplicate assessment abstention, duplicate source ambiguity, and batch crash/restart replay. Runner could not execute Python because the required local `.venv` executable is unavailable. |
| B4 affected regression tests | `BLOCKED` | The original regression runner request was rejected as `test_outside_task_write_scope`; the authorized long-bundle request reached the Python runner but was blocked by the environment. No unrun check is treated as PASS. |
| B5 typed result / QA handoff | `PENDING` | Worker publishes `CANDIDATE` / `UNACCEPTED`; independent QA must run the three-file pytest command in an environment with a regular local `.venv`. |

## Repair evidence

Independent QA first reported 8 failures and 11 passes from a fresh host-Python run. The five pre-existing adversarial failures were fixed by preserving the original claims container shape. The remaining three new long-bundle failures were over-broad whole-ledger assertions: the canonical per-claim behavior preserves unrelated valid assessments while fencing only the wrong-owner, duplicate-assessment, or ambiguous-source claim. The tests now assert that affected claim remains unchanged and unrelated claims verify; production fail-closed identity checks remain unchanged.

QA log: `D:/Temp/base20-qa-20261013/base5-deep-factid-postwave-20261014.log`, SHA-256 `3aa28d602bac084f7034e43aaf33d682e35bf4a5db0791753e25008132159d67`.

## Validation receipts

Requested command:

```text
python -m pytest -q -p no:cacheprovider tests/test_northstar_factid_source_identity_20261013.py tests/test_northstar_factid_identity_regression_r1.py tests/test_northstar_longbundle_factid_source_20261014.py
```

Focused authorized runner receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
 test=tests/test_northstar_longbundle_factid_source_20261014.py
source_identity_sha256=47280f06ffaf24e23da8ef75de870dc1286cc3ec0a6c3347e8c365f27fee2980
exit_code=null
stderr="A regular local .venv Python executable is required."
```

Original regression runner receipt:

```text
status=BLOCKED
code=test_outside_task_write_scope
engine=project test runner
file=tests/test_northstar_factid_source_identity_20261013.py
```

## Adversarial self-review

- Valid evidence is still updated only after exactly one assessment with the expected `fact_id` and `source_id`.
- Foreign fact IDs, wrong source owners, duplicate assessments, malformed IDs, duplicate article IDs, and duplicate ledger source IDs do not credit claims.
- A batch exception returns the original ledger, so a failed attempt cannot partially credit evidence before restart.
- Duplicate fact IDs in the ledger are excluded from the assessment map, preventing one assessment from updating multiple claims.
- Duplicate URLs remain excluded as before; no evidence is accepted from an ambiguous URL snapshot.
- The implementation does not mutate live task state, leases, locks, or files outside the manifest write scope.
- Python execution remains unverified because of the recorded environment blocker.
- No acceptance or GREEN claim is made; independent QA and terminal readback remain required.

## Next action

Run the requested three-file pytest command with the repository's regular local `.venv`, bind the exit code and count to the two final file SHAs above, then perform independent QA and CrewSync terminal readback.
