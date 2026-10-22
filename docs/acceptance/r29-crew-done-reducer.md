# R29 Crew DONE Reducer

Status: CANDIDATE / UNACCEPTED

## Scope and source of truth

Target: `af-deep-research`; task:
`af-deep-research:v2-r29-crew-done-reducer-20261015-r1`.

The C4 acceptance artifact is the governing upstream evidence. Its source-bound
record says the prior reducer lacked native CrewSync task-to-result evidence.
The permitted production sources expose checkpoint sequencing and verified-report
file-hash interfaces, but no coordinator-owned CrewSync transport or DONE API.
No production fix is therefore justified in this write scope.

## Implemented bounded oracle

`tests/test_r29_crew_done_reducer.py` defines a conservative reducer:
DONE/refill is true only for a CANDIDATE receipt with:

- an explicit UTC ISO-8601 `recorded_at`;
- a 64-character lowercase source SHA-256;
- test exit code zero;
- an explicit refill-ready flag.

It rejects non-CANDIDATE outcomes, missing task identity, nonzero test exits,
false refill claims, naive timestamps, malformed timestamps, and invalid or
missing source identities. The positive test also introspects the current
`checkpoint_research_run` and `build_grounded_verified_report` signatures,
so the oracle is tied to real current source interfaces rather than mocks.

## Validation

Required command:

```text
python -m pytest -q tests/test_r29_crew_done_reducer.py
```

Expected native result: 8 passing tests, exit 0. The scoped GO Wave runner does
not expose a Python/pytest executor; if unavailable, that is infrastructure
blocked and must not be converted to PASS.

## Acceptance boundary

This artifact is not product acceptance. Independent QA/reducer and authoritative
CrewSync terminal readback must verify the native task/result path and DONE refill
before any acceptance decision.
