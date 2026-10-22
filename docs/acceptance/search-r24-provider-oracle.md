# Search r24 provider oracle

Status: CANDIDATE / UNACCEPTED

## Scope

This independent native pytest oracle is source-bound to the current search
contracts in `skills/search/federated.py`, `fusion.py`, `jina.py`, and
`base.py`. It is intentionally test-only; no production adapter is changed.

## Acceptance coverage

- Positive baseline: two providers are federated and provenance is retained.
- Positive baseline: a forced single-provider federation remains explicitly
  attributable to one provider.
- Negative: HTTP 429 and 503 failures fall back to a healthy provider while
  exposing only safe exception types.
- Negative: no-source/all-provider failure raises a closed error.
- Negative: canonical URL duplicates collapse to one evidence item while
  retaining retrieval provenance rather than implying two independent sources.
- Negative: invalid Jina URLs raise before a fabricated source identity can be
  returned.

## Verification

Focused command:

```text
python -m pytest -q tests/test_search_r24_acceptance_oracle.py
```

The result must be recorded from the authorized native runner. This artifact
does not claim product acceptance; independent QA/reducer and coordinator
readback remain required.

## Limitations

The provider responses are deterministic test doubles at the HTTP/provider
boundary. They verify current public contracts and failure semantics, not live
third-party availability or external service correctness.
