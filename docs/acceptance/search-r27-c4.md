# Search C4 Drift Oracle — r27/c4

Status: CANDIDATE / UNACCEPTED

## Scope and source of truth

This independent oracle validates the existing R16 C4/Structurizr claims against the
current search implementation. It does not modify producer code, diagrams, live tasks,
leases, tokens, or sends.

Current source receipts:

| File | Current SHA-256 |
| --- | --- |
| `skills/search/__init__.py` | `327c1a80311e381cfe92005b621d76473258d088f62953b2767c45d7c0b66e74` |
| `skills/search/federated.py` | `b4c5085bdecb9b5c737df4701f664bac495e1a4ebde749d80f0ab3c16b957a7a` |
| `skills/search/registry.py` | `58d587dff3951e0d86fb5249e493b9dc5ca9813512dfc308d12107fde3b807c6` |

The R16 contract records a stale `skills/search/__init__.py` SHA
(`07e2f88feea292fe3b645b142639d41bd9ff6cbd25a2f8f2b2ae5a3a3d0b6f10`).
Graphify and ArchSteer indexes are unavailable in the authorized read scope, so their
coverage is recorded as UNVERIFIED, not empty or complete.

## Oracle coverage

- Positive: imports the real `search`, `select_federated_providers`, and
  `get_default_provider`; checks their source hashes and function presence.
- Negative: rejects stale contract SHA.
- Negative: rejects Structurizr's declared fusion topology because no `fusion`
  function exists in the inspected federated module.
- Negative: rejects false graph coverage when the Graphify/ArchSteer index artifacts
  are absent or empty.
- Routing guard: requires the actual auto/federated branch to preserve both the
  multi-provider and single-provider paths, with default-provider fallback.

## Validation

Command: `python -m pytest -q tests/test_search_r27_c4_fingerprint.py`

Expected evidence is actual pytest output from the authorized runner; no mock-only result
is sufficient. This report remains UNACCEPTED pending independent QA and CrewSync
terminal readback.
