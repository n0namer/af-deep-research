# Search R24 replay/report oracle

Status: CANDIDATE / UNACCEPTED

This independent pytest oracle binds the current raw SHA-256 identities of
`research_run.py` and `verified_pipeline.py`, imports their real report/run
APIs, and verifies one positive flow plus four fail-closed boundaries.

## Checks

- Positive: source-bound r10 report persistence, resume, terminal effect idempotence, run checkpoint/restart receipt, and explicit abstention.
- Negative: foreign owner cannot mutate a stored report.
- Negative: stale source SHA cannot resume or create an effect.
- Negative: a restarted in-memory report store cannot fabricate a missing receipt.
- Negative: duplicate provider call IDs are deduplicated, and missing facts remain abstentions rather than claims.

The fixture fails immediately when either current source SHA differs from the
reviewed contract, preventing stale blind acceptance. It uses no mock provider
or network call; all report/run behavior is exercised through importable
project APIs.

## Validation

Authorized command:

`python -m pytest -q tests/test_search_r24_replay_report_oracle.py`

The worker must preserve the actual runner receipt. A blocked Python environment
is infrastructure evidence, not a passing product result. This artifact remains
CANDIDATE / UNACCEPTED pending independent QA/reducer and authoritative
CrewSync readback.
