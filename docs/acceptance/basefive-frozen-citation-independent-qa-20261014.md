# BaseFive Frozen Fact Citation — Independent QA Receipt — 2026-10-14

Status: CANDIDATE / UNACCEPTED

## Task binding

- Task: `af-deep-research:v2-basefive-fact-citation-frozen-independent-qa-20261014-r4`
- Attempt: `attempt-b8b11c11-6468-4fe8-81b2-d5f8c43a6b16`
- Session: `manual-20261014-basefive-northstar-hyper-r4-af--579e99ed806d16b6`
- Project: `af-deep-research`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Baseline Git SHA supplied by coordinator: `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`
- Authorized writes: this receipt and `tests/test_basefive_frozen_fact_citation_20261014.py` only.

## D1 — Source-bound interface

The existing implementation under test is `reasoners/deep_research_ext/verification_bridge.py` at the supplied baseline Git SHA. The C4-relevant interface signature is:

```python
async def verify_ledger_claims(
    *,
    ledger: EvidenceLedger,
    research_package: dict,
    source_strictness: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    ai_call=None,
    adjudicator: Callable[..., Awaitable[AIAssessmentList]] = adjudicate_evidence_ai,
) -> EvidenceLedger
```

The source also binds adjudication batches to `ADJUDICATION_BATCH_SIZE = 25`. Eligibility requires a unique ledger source, unique article ID and URL, and exact URL/content-hash equality. Assessment application requires one assessment for a known fact ID with the expected source owner; otherwise the claim remains unchanged.

## D2/D3 — Focused native test coverage

`tests/test_basefive_frozen_fact_citation_20261014.py` contains five source-bound assertions:

- positive 26-claim bundle verifies every eligible claim and preserves source-entailment state;
- foreign `fact_id` leaves the affected claim pending without partial credit;
- wrong source owner leaves the affected claim pending without partial credit;
- duplicate assessment leaves the affected claim pending without partial credit;
- a second-batch crash leaves the ledger unchanged, while a clean restart replay verifies all claims without mutating the original ledger.

The 26-claim fixture intentionally crosses the batch boundary (`25 + 1`) so the restart and duplicate checks cover multi-batch behavior.

## D4 — Validation receipt

Requested focused command:

```text
python -m pytest -q tests/test_basefive_frozen_fact_citation_20261014.py
```

Actual scoped runner receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
exit_code=null
source_identity_sha256=38777ab6bc07cf240bb70ee35051104214cbfbfaa86ca35e63df3142122855b4
stderr="A regular local .venv Python executable is required."
```

Classification: `BLOCKED_INFRA`. The test was not converted to PASS, and the identical denied runner was not retried. Affected Python regression tests were not run because the same local `.venv` prerequisite is unavailable in this lane.

## D5 — Self-review and handoff

- Only the two authorized write-scope files were changed.
- No production source, DTO, live task, lease, lock, or terminal state was modified.
- The test uses the existing `verify_ledger_claims` contract rather than introducing a parallel implementation.
- Positive behavior and four adversarial/restart boundaries are explicit.
- Crash handling is asserted as abstention, not partial success; replay is asserted from the original unchanged ledger.
- The supplied Git SHA is recorded as coordinator evidence, not recomputed in the read-restricted lane.
- The focused result remains `CANDIDATE / UNACCEPTED` because the native Python test could not execute.

## Remaining blocker and next action

An independent verifier or coordinator should run the exact command above in an environment with a regular local `.venv`, bind its real pytest exit code and test count to the test-file SHA, then perform affected regression and authoritative terminal readback. No `ACCEPTED_GREEN` conclusion is supported by this receipt alone.
