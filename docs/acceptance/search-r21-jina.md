# Search R21 Jina source identity

Status: CANDIDATE / UNACCEPTED

## Scope

The Jina provider now parses each result through a source-identity boundary. A result is accepted only when it has a non-blank title and an absolute HTTPS URL. Missing, blank, malformed, or non-HTTPS identity raises a typed error before a SearchResult is constructed, so provenance is never fabricated.

## Evidence

- Positive coverage: valid HTTPS identity and optional ISO publication time.
- Negative coverage: missing URL, missing title, blank title, non-HTTPS URL, and non-object result.
- Affected integration coverage: malformed transport payload remains a typed failure through search_with_provider.

## Validation

Requested native commands:

    python -m pytest -q tests/test_search_r21_jina_identity.py
    python -m pytest -q tests/test_search_r16_main_integration.py

The scoped execution adapter available to this worker supports Node/Vitest test targets only; Python pytest execution is therefore an infrastructure capability gap and must remain reported as unverified until run in the project Python environment.
