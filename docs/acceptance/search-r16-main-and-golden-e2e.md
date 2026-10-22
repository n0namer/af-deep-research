# Main search pipeline integration evidence

Status: candidate harness, not independent acceptance.

## Scope and source binding

This artifact covers the real `main.search_web_for_content` bridge and the
real `skills.search` auto, single-provider, and federated paths. The only
test double is deterministic `aiohttp.ClientSession` transport; provider
selection, availability checks, provider parsing, federation, fusion, canonical
dedupe, and result transformation remain production code.

No LLM calls, API keys, network requests, or long-running model tasks are used.
The test file is intentionally limited to the authorized write scope.

## Acceptance matrix

| Signal | Evidence in harness |
| --- | --- |
| Real main bridge | Auto-mode test calls `main.search_web_for_content` directly |
| Positive paths | Main auto, single Tavily, federated two-provider |
| Negative paths | One-provider fallback, all-provider failure, zero-result, malformed payload, no-key |
| Provenance | Federated canonical URLs, contributing providers, per-provider ranks |
| Hard signals | Typed all-provider error, provider error map, zero-result distinction, no fabricated source identity |
| Golden plans | Six explicit semantic prompts across six source-policy domains |

## Six golden semantic test plans

1. **DR-S01 — Protocol:** current behavior; require an RFC/editorial primary source.
2. **DR-S02 — Science:** contradictory study result; require DOI/primary study evidence.
3. **DR-S03 — State:** authoritative transition; require an official/government source.
4. **DR-S04 — History:** causal historical event; require an archive or primary record.
5. **DR-S05 — Business:** official metric; require a filing or company source.
6. **DR-S06 — Adversarial product:** risks and prompt-injection traps; require vendor docs
   plus explicit adversarial-source handling.

A future opt-in live run may replay these prompts only when a user supplies a
token through the process environment; it must never print, persist, or auto-run
the token.

## Fresh validation

Required command:

```text
python -m pytest -q tests/test_search_r16_main_integration.py
```

The scoped GO runner only exposes Node/Vitest/tsx execution and cannot execute
this Python pytest file. Therefore this attempt must preserve the exact
pytest command as **EVIDENCE_MISSING / infrastructure-blocked**, not PASS.
Run it in a Python-enabled verifier environment after this candidate is handed
off.

## Known limitation

The current read-only `main.search_web_for_content` transformation emits only
`url`, `title`, `content`, and `description`; it does not forward
`canonical_url`, `retrieval_providers`, or `provider_ranks`. The harness
proves provenance preservation in the federated `SearchResponse` and makes the
bridge gap explicit. Repairing that transformation is outside this task's write scope.

Source evidence:
- `main.py` SHA-256: `5bebcfd28bd954561aaa5fcc7654dbb5615d4a552d9daaa4656db42cc76649c8`
- `skills/search/__init__.py` SHA-256: `07e2f88feea292be3b645b142639d41bd9ff6cbd25a2f8f2b2ae5a3a3d0b6f10`
- `skills/search/federated.py` SHA-256: `b4c5085bdecb9b5c737df4701f664bac495e1a4ebde749d80f0ab3c16b957a7a`
- `skills/search/base.py` SHA-256: `88c4ec5647699ac873530df846cfa078e820980aa3e35d3659ebeb1bf3781a239`

No source or production file was modified.
