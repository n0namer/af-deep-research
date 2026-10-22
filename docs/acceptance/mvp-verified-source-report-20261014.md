# MVP Verified Source Report — 2026-10-14

Status: CANDIDATE / UNACCEPTED

## Scope

The MVP adds a typed, source-bound report boundary in `reasoners/deep_research_ext/verified_pipeline.py` without changing the existing pipeline result contract.

## Contract

- `VerifiedSourceReport` requires a non-empty report identity and query, unique source IDs, a positive integer revision, and a mapping payload.
- `persist_verified_source_report` accepts only the first report or the next contiguous revision.
- Replaying an identical revision is idempotent and does not call the store again.
- Wrong identity, conflicting same-revision payloads, revision gaps, malformed DTOs, and invalid stores fail closed before persistence.
- The pipeline checks cancellation before research, verification, synthesis, and report persistence; cancellation raises `asyncio.CancelledError` without a report-store effect.

## Focused evidence

Authorized focused target: `tests/test_mvp_verified_source_report_20261014.py`.

The test matrix covers:

1. Positive typed DTO construction and one-time persistence.
2. Wrong identity and same-revision tampering rejection.
3. Malformed revision/source IDs and cancellation with no persistence.
4. Restart replay: revision 1 is preserved, revision 2 is applied once, and replay of revision 1 does not regress state or duplicate the effect.

## Validation receipt

- Repair target: previous host-native collection failed with `SyntaxError: unexpected character after line continuation character` at the report-store persistence block; the escaped literals were corrected in this attempt.
- Focused runner: `tests/test_mvp_verified_source_report_20261014.py` — `BLOCKED`, `PYTHON_VENV_UNAVAILABLE`, `engine=python:pytest`, `exit_code=null`, stderr `A regular local .venv Python executable is required.`
- Affected runner: `tests/test_northstar_independent_source_adversarial_20261014.py` — the same infrastructure blocker; no PASS is inferred.

## Acceptance posture

This artifact remains CANDIDATE / UNACCEPTED pending the independent verifier/reviewer and authoritative CrewSync readback. No deployment, commit, or external publication is performed by this worker.
