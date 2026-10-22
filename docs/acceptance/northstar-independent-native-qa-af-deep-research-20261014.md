# Northstar Independent Native QA — 2026-10-14

Status: CANDIDATE / UNACCEPTED

## Authority and scope

- Task: `af-deep-research:v2-independent-native-longbundle-qa-20261014-r1`
- Attempt: `attempt-e54412c4-0142-4766-a180-c3b559b33a15`
- Session: `manual-20261014-base5-independent-native-qa-hyp-4cf815ef752eabe5`
- Target: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Authorized writes: this report and `tests/test_northstar_independent_source_adversarial_20261014.py` only.
- Acceptance authority: independent verifier/reviewer, reducer coordinator, and authoritative CrewSync terminal readback.
- Producer implementation was not edited; `reasoners/deep_research_ext/verification_bridge.py` remained read-only.

## Source-bound evidence

| Evidence | Immutable identity | Finding |
| --- | --- | --- |
| `reasoners/deep_research_ext/verification_bridge.py` | SHA-256 `7a04c4e0cbb7d5dbc19127492aad8f673a14032e9a92c960bff83959634e5c0f` | `verify_ledger_claims` builds facts only from matching source ID, URL, and content hash; `verified-only` abstains when no eligible fact remains; adjudicator exceptions return the original ledger; assessment IDs must be unique and source IDs must match. |
| `tests/test_northstar_independent_source_adversarial_20261014.py` | SHA-256 `cff4ac0734798be957a545db4aa43e6f2a02fd4f4019b553cd1850163832be9f` | Four focused cases were written: one positive entailment, duplicate-source abstention, source-mismatched assessment rejection, and exception-safe restart retry. |
| `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md` | Read through scoped reader; prior reducer remains `CANDIDATE / UNACCEPTED` | Prior evidence explicitly warns that C4 producer/QA receipts and native task-to-result failure/restart output must not be inferred from unrelated Base20 evidence. |

## Focused test design

1. **Positive source entailment:** a unique article whose `id`, URL, and content hash match the ledger source produces a fact carrying the expected `fact_id` and `source_id`; a supported verified assessment moves the claim to `verified` / `source_entailed`.
2. **Fail-closed duplicate source:** two package articles reuse the same non-empty URL; `verified-only` must raise `ValueError("No eligible evidence remains for verified ledger adjudication.")` rather than adjudicate ambiguous evidence.
3. **Fail-closed source identity:** an assessment with the correct fact ID but a different source ID is ignored; the original pending claim remains unchanged.
4. **Restart/retry safety:** an adjudicator exception returns the exact original ledger without mutation; a subsequent retry against that preserved ledger can apply the valid assessment.

## Runtime validation

### Focused command

```text
python -m pytest -q tests/test_northstar_independent_source_adversarial_20261014.py
```

Actual authorized runner receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
exit_code=null
source_identity_sha256=cff4ac0734798be957a545db4aa43e6f2a02fd4f4019b553cd1850163832be9f
stderr="A regular local .venv Python executable is required."
```

Classification: `INFRA BLOCKED`, not PASS and not product FAIL. The runner could not start pytest because the required regular local `.venv` executable was unavailable. The identical denied call was not retried.

### Affected regression

Status: `BLOCKED / NOT RUN`.

No affected Python regression command was executed after the focused runner reported the missing `.venv`; repeating the same unavailable environment would not add evidence. The current five native tests therefore remain unverified in this lane. Recovery requires the coordinator to provide a permitted environment with a regular local `.venv` Python executable, then rerun the focused file before the affected native regression set.

## C4 / producer receipt comparison

Status: `BLOCKED`.

The authorized read scope contains the read-only verification source and the prior C4 reducer report, but no terminal producer publication, independent-QA publication, or immutable producer artifact receipt for `20261014-base5-longbundles-northstar-r1`. The source signature above is freshly read from the scoped source snapshot; it is not a producer acceptance receipt. No C4 acceptance, native task-to-result GREEN state, or producer/QA equivalence is inferred.

## Self-review

- The test file changes only the authorized test path and uses no production writes, live task mutation, or concurrent QA activity.
- The source function is imported and exercised through its public async verification entry point; no producer source repair was attempted.
- Positive behavior is separated from duplicate, identity-mismatch, and restart failure paths.
- The runner result is preserved as infrastructure-blocked; no unrun check is reported as PASS.
- Source and test SHA-256 identities are recorded for later coordinator comparison.
- The report remains `CANDIDATE / UNACCEPTED` pending a usable Python environment, affected regression output, producer receipt fan-in, independent review, and terminal readback.

## Remaining blockers and next action

- Provide a regular local `.venv` Python executable to the authorized runner.
- Run the focused command, then the affected five native tests, recording exact exits and counts.
- Supply the original producer and independent-QA receipts for `20261014-base5-longbundles-northstar-r1` so the reducer can compare immutable source signatures and producer identity.
- Keep `reasoners/deep_research_ext/verification_bridge.py` unchanged unless the original producer owner receives a separate affected-only repair task.
