# R26 federated live-evidence acceptance

Status: CANDIDATE / UNACCEPTED

## Scope

This acceptance artifact records the deterministic oracle for the existing `skills.search` path. It does not change product code, call external providers, or claim independent research acceptance.

## Evidence

- Test: `tests/test_search_r26_federated_evidence.py`
- Validation command: `python -m pytest -q tests/test_search_r26_federated_evidence.py`
- Coverage: one positive identity/fusion case and three negative/boundary cases: partial 429/503 failure isolation, deterministic refusal for unknown/unconfigured providers, and auto/single provider identity.
- Configured adapter path: Brave, Perplexity, Tavily, and Firecrawl are injected as deterministic test transports; no API keys or environment secrets are stored.
- Source identity: `skills/search/fusion.py` SHA-256 `c7c0684e8d5d55df099ebf7690bfceafff78e79fe4ad15a6265ecb29a5a5625c`.
- Citation rule: canonical URL aliases are one evidence item; `retrieval_providers` records retrieval corroboration only and cannot turn duplicate URLs into independent sources.

## Gate

A PASS requires actual pytest output from the exact command. A blocked or unavailable Python runner remains INFRA BLOCKED and must not be converted to GREEN. Independent QA and CrewSync readback own acceptance.
