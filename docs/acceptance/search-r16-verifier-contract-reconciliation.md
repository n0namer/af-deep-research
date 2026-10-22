# Search R16 Verifier Contract Reconciliation — 2026-10-14

Status: CANDIDATE / UNACCEPTED

## Authority

- Task: `af-deep-research:v2-r17-legacy-verifier-test-reconcile-20261014-r1`
- Attempt: `attempt-d3fd9c30-b898-439f-9e20-49112378a612`
- Session: `manual-20261014-search-live-hyperwave-r17-af-de-3f575709f26cb6d3`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Authorized write scope: this report and `tests/test_deep_research_ext.py`
- Acceptance authority: independent verifier/reviewer and coordinator readback

## Contract reconciliation

The existing `verification_bridge.verify_ledger_claims` contract admits an assessment only when:

1. its fact identity is present in the eligible ledger exactly once;
2. its assessment `source_id` exactly matches the ledger fact source; and
3. the source/article URL and content fingerprint match.

The two original positive/conflict fixtures omitted `source_id`, so they were correctly rejected by the fail-closed contract. The portability fixture hardcoded `/app/main.py`; it now resolves `main.py` from the test file's repository root.

Added negative probes cover missing source identity, foreign source identity, and duplicate fact identity. Existing positive verified-source and supported-conflict/disputed cases retain their intended assertions with exact source identity.

## Changed files

- `tests/test_deep_research_ext.py` — corrected source-bound assessment fixtures, repository-relative AST path, and three fail-closed identity tests.
- `docs/acceptance/search-r16-verifier-contract-reconciliation.md` — this evidence report.

Production verifier files were not changed.

## Validation receipts

Requested command:

```text
python -m pytest -q tests/test_deep_research_ext.py
```

Scoped runner receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
test=tests/test_deep_research_ext.py
engine=python:pytest
exit_code=null
source_identity_sha256=f230a7700b0573509f1c742d2863d34097770a698e43e3f2caf33b28aac4539d
stderr="A regular local .venv Python executable is required."
```

The baseline supplied by the coordinator was 55 PASS / 3 FAIL. The focused test file now contains 58 tests after adding three negative probes, but the post-change pytest result is not claimed because the authorized runner is unavailable.

## Remaining

- Re-run the exact pytest command in an environment with the required regular local `.venv`.
- Independent review and authoritative acceptance readback remain pending.
