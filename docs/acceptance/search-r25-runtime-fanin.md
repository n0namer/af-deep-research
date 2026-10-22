# Search r25 runtime fan-in acceptance

Status: CANDIDATE / UNACCEPTED

## Scope

This independent acceptance artifact covers the real public search interfaces for four registered adapters: Jina, Tavily, Firecrawl, and Serper. It changes no production source.

## Source-bound evidence

- Read-only source inputs: `skills/search/__init__.py`, `federated.py`, `fusion.py`, `jina.py`, `registry.py`.
- Prior candidate reference: `tests/test_search_r24_acceptance_oracle.py`.
- Exact source identity is bound by the coordinator task context; this lane does not recompute or substitute SHA values.
- The test imports the real registry, provider base, federation, fusion, and Jina parser. Transport calls are replaced only at the async provider boundary for deterministic default tests.

## Acceptance matrix

| Requirement | Evidence |
| --- | --- |
| Explicit single selection | `test_explicit_single_selection_calls_only_selected_provider` proves only the selected provider is awaited. |
| Auto bounded federation | `test_auto_federation_is_bounded_and_deduplicates_provider_names` proves duplicate names are removed and the provider cap is respected. |
| Four provider adapters | `test_registry_exposes_four_real_provider_adapters` checks the registered real adapter classes through the public registry. |
| RRF duplicate independence | `test_rrf_deduplicates_same_canonical_url_but_preserves_independent_provenance` checks canonical dedupe and provider rank provenance. |
| 429/503 failover | `test_provider_outage_keeps_healthy_fallback_and_redacts_transport_error` covers both statuses; all-failed behavior is separately fail-closed. |
| Invalid Jina URLs | `test_invalid_jina_urls_fail_closed` covers non-HTTPS and relative URLs. |
| Opt-in true request | `test_opt_in_true_request_is_bounded_and_skipped_by_default` is skipped unless `R25_TRUE_REQUESTS=1`, with a 1–10 second timeout bound. |

## Negative coverage

The suite has more than three negative paths: duplicate/invalid URL rejection, both outage statuses, all-provider failure, secret redaction, and absent credentials for the opt-in request.

## Validation

Required command:

```text
python -m pytest -q tests/test_search_r25_runtime_fanin.py
```

A default run must execute the deterministic tests and report the true-request probe as an explicit skip when not opted in. A denied or unavailable Python runner is infrastructure-blocked and must not be converted to PASS.

## Review boundary

The result remains CANDIDATE / UNACCEPTED pending independent QA and authoritative CrewSync terminal readback.
