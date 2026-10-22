# Search R18 Golden Source Policy

Status: CANDIDATE / UNACCEPTED  
Scope: DR-L01 through DR-L06 source-policy oracle

## Decision

The six golden domains require two independent conditions:

1. the deterministic evaluator must replay an admissible requirement from a cited document; and
2. the citation must be an official primary HTTPS source whose provenance host matches its URL and whose content records the requested `as_of` date.

A semantic evaluator PASS alone is not source-policy acceptance. This prevents a secondary-only citation, stale dated evidence, or fabricated attribution from becoming a false-premise PASS.

## Coverage

| Golden | Domain | Primary source bucket | As-of |
| --- | --- | --- | --- |
| DR-L01 | standards | RFC Editor | 2026-08-31 |
| DR-L02 | science | Nature | 2026-08-31 |
| DR-L03 | current-state | GOV.UK | 2026-08-31 |
| DR-L04 | history | U.S. National Archives | 2026-08-31 |
| DR-L05 | business-decision | SEC EDGAR | 2026-08-31 |
| DR-L06 | software-product | Python.org | 2026-08-31 |

These are source-policy buckets, not claims that the placeholder paths are live-web retrievals. The oracle checks the source identity and dated attribution contract; it does not substitute a mock-only evaluator result for that policy check.

## Required negative behavior

For every golden domain, the focused pytest rejects:

- a semantically supporting secondary-only citation;
- a primary citation whose effective date is stale relative to the requested as-of date;
- a primary-looking citation whose provenance attribution does not match its URL host.

The tests intentionally show that the existing semantic replay can pass these cases while the independent source-policy oracle rejects them. That separation is the acceptance boundary.

## Validation

- Focused: `python -m pytest -q tests/test_search_r18_golden_source_policy.py`
- Affected regression: `python -m pytest -q tests/test_evaluation_suite.py`

Acceptance remains UNACCEPTED pending independent QA and coordinator readback.
