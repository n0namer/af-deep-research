# Northstar Fact/Source Fence Repair — 2026-10-13

Status: BLOCKED / UNACCEPTED

## Authority

- Task: `af-deep-research:v2-northstar-factid-source-fence-red6-spawnfix-repair-20261013-r2`
- Attempt: `attempt-58e86275-adfa-4beb-9004-20c8ff91545e`
- Session: `manual-20261013-research-native-red6-production-99c1e5529db4b843`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Independent QA and authoritative acceptance remain required.

## Source-Bound Change

The repair changes only the adjudication result fence in `verify_ledger_claims`:

- A returned assessment is eligible only when its `fact_id` is expected exactly once.
- Its `source_id` must exactly match the source owner used to construct that fact.
- Duplicate assessments for one fact abstain rather than allowing last-write-wins credit.
- Any adjudication batch exception aborts the whole verification call and returns the original ledger, preventing partial credit before a clean replay.
- Valid exact fact/source assessments preserve the existing status, support-state, admissibility, verification, and disagreement update behavior.

The public C4-facing API is unchanged: the module path, `verify_ledger_claims` name, keyword-only parameters, defaults, async return contract, `EvidenceLedger` result type, batch size, and normal claim update fields remain unchanged.

## Identity Receipts

| Artifact | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| `reasoners/deep_research_ext/verification_bridge.py` | `aad1f5c7a85b26a0c7a3449e9b12df5b276f8b50c264e18688195326f12db270` | `7a04c4e0cbb7d5dbc19127492aad8f673a14032e9a92c960bff83959634e5c0f` |
| `tests/test_northstar_factid_identity_regression_r1.py` | new | `205fc41d20bdc46c0ac81812f1556f6c302226ec71f5ad98050790db159e2d7a` |
| Original affected test | `f4b7b8df6f431b1def739a29fd0766d9cfb27f5e9d16821de2654c1f2983e44e` | read-only / unchanged |

## Focused Coverage Added

`tests/test_northstar_factid_identity_regression_r1.py` covers:

1. Exact fact/source ownership preserves valid evidence.
2. The same fact ID returned under a foreign source owner abstains.
3. Duplicate assessments for one fact abstain.
4. A 26-fact, two-batch run with a second-batch crash commits nothing; a clean replay verifies all facts while the input ledger remains unchanged.

## Validation Receipts

Requested command:

```text
python -m pytest -q -p no:cacheprovider tests/test_northstar_factid_source_identity_20261013.py tests/test_northstar_factid_identity_regression_r1.py
```

The scoped runner accepts one exact test file per invocation, so each authorized target was submitted once.

### Original affected test

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
source_identity_sha256=f4b7b8df6f431b1def739a29fd0766d9cfb27f5e9d16821de2654c1f2983e44e
exit_code=null
stderr="A regular local .venv Python executable is required."
```

### New regression test

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
source_identity_sha256=205fc41d20bdc46c0ac81812f1556f6c302226ec71f5ad98050790db159e2d7a
exit_code=null
stderr="A regular local .venv Python executable is required."
```

No PASS is claimed. The dependency blocker was not retried after each distinct authorized test file produced the same receipt.

## Adversarial Self-Review

- The old dictionary comprehension used last-write-wins behavior for duplicate fact IDs; the repair requires exactly one candidate.
- The old path trusted a matching fact ID without checking the source owner; the repair binds both identities.
- The old exception filtering could retain successful batches after another batch crashed; the repair makes the call transaction-like.
- Foreign or empty fact IDs remain unable to update a native claim.
- Missing or absent assessment `source_id` fails closed through `getattr(..., None)` rather than raising.
- Claims without an eligible, unique, correctly owned assessment remain byte-for-byte model values from the input ledger.
- The positive update semantics are unchanged after the new identity fence.
- The input ledger is never mutated; replay starts from the original pending claims.
- No signature, import path, DTO constructor, or persisted schema was changed.
- Only the three authorized write-scope paths were changed or created.

## Remaining Gate

Runtime acceptance is infrastructure-blocked until the repository has the regular local `.venv` required by the scoped Python runner. Independent QA should run the requested combined pytest command against the recorded source identities and review the implementation before any acceptance transition.
