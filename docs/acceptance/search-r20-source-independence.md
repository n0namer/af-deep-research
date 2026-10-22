# Search R20 source-independence oracle

Status: CANDIDATE / UNACCEPTED

## Scope and source of truth

This acceptance artifact defines the focused oracle for source diversity. It composes the existing `skills/search/fusion.py` URL/RRF contract with the semantic snapshot provenance policy in `reasoners/deep_research_ext/evaluation.py`; no production search code is changed.

## Decision rules

- Canonical URL variants and tracking parameters collapse to one fused retrieval result.
- Reciprocal-rank scores and output ordering remain deterministic when provider response order is permuted.
- Provider count is not semantic source count: mirrors, proxy/syndicated pages, and derivative publications sharing a `provenance_group` count once.
- A primary source bucket is required where the fixture requires it; fabricated, inadmissible, adversarial, or non-primary documents cannot substitute for it.
- Two provider hits with different URLs remain two retrieval records because `fusion.py` has no upstream-lineage field. The semantic oracle therefore uses `source_class`, `provenance_group`, and `admissible` from the frozen snapshot policy.

## Evidence

Focused test target: `tests/test_search_r20_source_independence.py`

Required commands:

    python -m pytest -q tests/test_search_r20_source_independence.py
    python -m pytest -q tests/test_evaluation_suite.py

The test target covers canonical deduplication, RRF order stability, same-upstream mirror suppression, primary-source requirements, fabricated-source negatives, and the false-green case where two providers point to one upstream article.

## Known limitation

`SearchResult` records retrieval providers and canonical URLs, but not semantic upstream provenance. Consequently, `fuse_search_responses` alone cannot prove independence for different URLs. This candidate deliberately fails closed by requiring the semantic snapshot provenance policy for that judgment; a future production change would need an explicit provenance contract and an independent review.

## Acceptance

This artifact remains CANDIDATE / UNACCEPTED pending independent verification and coordinator readback.
