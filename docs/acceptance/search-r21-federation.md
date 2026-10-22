# Search R21 Federation Routing

Status: CANDIDATE / UNACCEPTED

## Scope

Task `af-deep-research:v2-r21-federation-routing-20261014-r1` wires the existing
federated search engine into `skills.search.search` without changing provider
implementations.

## Implementation evidence

- `SEARCH_PROVIDER` remains an explicit single-provider override.
- `SEARCH_MODE=auto` or `federated` selects the existing bounded provider set.
- Two or more providers use `search_with_providers`, preserving RRF
  canonicalization, provider provenance, safe error-class reporting, and partial
  failure fallback.
- Zero providers preserve the existing no-provider RuntimeError.
- One provider preserves the legacy single-provider response behavior.
- No credentials or provider exception text are included in the routing result.

Changed source: `skills/search/__init__.py`

## Validation receipts

- `tests/test_search_federation.py`: BLOCKED by scoped native runner,
  `PYTHON_VENV_UNAVAILABLE`, stderr: "A regular local .venv Python executable is required."
- `tests/test_search_r16_main_integration.py`: BLOCKED by runner policy,
  `test_outside_task_write_scope`.
- These are infrastructure/scope receipts, not test PASS claims.

Independent verification and acceptance remain required.
