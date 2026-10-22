# Search R16 ReleaseGate and Refill — 2026-10-14

Status: **CANDIDATE / UNACCEPTED**

## Scope and source binding

This reducer is limited to observed search/research runtime receipts. It does not
edit providers, pipeline code, live tasks, leases, owners, or prior QA artifacts.

- Project: `af-deep-research`
- Task: `af-deep-research:v2-r17-search-qa-reducer-20261014-r1`
- Attempt: `attempt-78fb8fdb-ed4f-469f-8251-f7cd0185d731`
- Session: `manual-20261014-search-live-hyperwave-r17-af-de-98ced8a42d5ef6f2`
- Baseline Git identity supplied by the coordinator:
  `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`
- Source artifact checked by the reducer:
  `reasoners/deep_research_ext/verified_pipeline.py`
- Source SHA bound by scoped readback:
  `97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87`
- Existing BMad source of truth remains
  `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md`.

A file SHA is not a dirty-checkout identity. The reducer therefore requires the
exact expected source SHA on every observed receipt and separately recomputes the
source artifact checksum.

## Layer-by-layer gate

Each layer is evaluated independently and must contain observed runtime evidence,
at least one successful provider, declared source IDs, verified non-empty citation
quotes, and the exact source SHA:

1. `ADAPTER_REAL_PASS`
2. `FEDERATED_ENGINE_PASS`
3. `PACKAGE_ROUTING_PASS`
4. `MAIN_INTEGRATION_PASS`
5. `FACT_ID_BRIDGE_PASS`
6. `NATIVE_FULL_RESEARCH_PASS`

The reducer distinguishes:

- `PASS`: the individual receipt satisfies the bounded evidence contract;
- `FAIL`: evidence is present but violates a release invariant;
- `INFRA_BLOCKED`: a provider returned HTTP 429;
- `PENDING_UNACCEPTED`: reducer output, never product acceptance.

A missing provider, fake/unverified citation, undeclared source ID, stale SHA, or
mock-only gold result is a rejection. Passing all local layer predicates still
does not produce `ACCEPTED_GREEN`: an independent fresh QA receipt is required,
and acceptance remains external.

## Future/frontier refill

The next affected-only tasks are dependency-ordered and intentionally unowned:

| Task | Dependency | DoD | Owner |
| --- | --- | --- | --- |
| `r17-adapter-and-federated-live-receipt` | none | fresh four-provider receipt with exact source SHA and provider outcomes | unassigned |
| `r17-native-research-qa` | adapter/federated receipt | independent QA for citation and restart boundaries | unassigned |
| `r17-reducer-refill` | native QA receipt | reduce only after preceding receipts are readable | unassigned |

These are future-ready descriptions, not claimed coordinator ownership or new live
tasks.

## Validation receipt

Requested validation:

```text
python -m pytest -q tests/test_search_r16_release_reducer.py
```

Actual scoped runner receipt:

```json
{
  "status": "BLOCKED",
  "code": "PYTHON_VENV_UNAVAILABLE",
  "test": "tests/test_search_r16_release_reducer.py",
  "engine": "python:pytest",
  "source_identity_sha256": "5556641cfdb6e201e304f93131d6c205a6c757500ada2cb057f706c17c189ddd",
  "exit_code": null,
  "stderr": "A regular local .venv Python executable is required."
}
```

The focused pytest did not start; collection and assertions are therefore
**unverified**, not PASS or FAIL. The artifact checksum assertion is implemented
and source-bound, but its runtime readback is likewise pending the same runner.
No mock provider, Node surrogate, dependency installation, shell fallback, or
weakened assertion is an acceptable substitute.

## Self-review

- No production source or previous QA artifact was modified.
- The reducer cannot turn candidate evidence into `ACCEPTED_GREEN`.
- SHA checks are exact and stale-safe.
- Provider absence, fake citation, bad source ID, stale SHA, mock-only evidence,
  missing QA, and 429 infrastructure are tested separately.
- Artifact checksum readback is bound to the inspected production file.
- Future work carries dependencies but no invented ownership.
- Independent verifier/reviewer and the coordinator retain acceptance and terminal
  readback authority.
