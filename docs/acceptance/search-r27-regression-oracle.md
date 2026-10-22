# Search R27 Regression Oracle

Status: CANDIDATE / UNACCEPTED

## Scope

This independent oracle uses the current public skills.search interfaces and the durable
verified-source report boundary. It does not edit production code or the prior r26 tests.

## Source evidence

- skills/search/fusion.py current SHA-256:
  c7c0684e8d5d55df099ebf7690bfceafff78e79fe4ad15a6265ecb29a5a5625c
- reasoners/deep_research_ext/verified_pipeline.py raises native
  asyncio.CancelledError before persistence and before terminal-effect fencing.
- Correct imports are from skills.search.base, skills.search,
  skills.search.fusion, and reasoners.deep_research_ext.verified_pipeline.

## Oracle coverage

Positive behavior: canonical URL fusion deduplicates tracking variants, keeps both real
provider ranks, and selects the longer content.

True negatives:

1. empty URLs are excluded rather than becoming fabricated evidence;
2. unknown single-provider dispatch is rejected;
3. cancellation before persistence raises CancelledError and leaves no report/effect;
4. cancellation before effect fencing leaves the report but applies no terminal effect;
5. resume with a drifted source SHA is rejected.

The SHA assertion detects stale or substituted fusion source. No mock-only result is used
to claim production behavior.

## Validation

Command required by the task:

python -m pytest -q tests/test_search_r27_regression_oracle.py

Acceptance remains UNACCEPTED pending independent QA and coordinator readback.
