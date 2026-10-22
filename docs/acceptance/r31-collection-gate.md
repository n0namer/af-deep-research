# R31 Python collection gate

Status: CANDIDATE / UNACCEPTED

## Scope

This isolated QA gate verifies current r29/r30 Python test collection with the native project interpreter. It does not change production code or certify product acceptance.

## Checks

- Positive: native pytest --collect-only succeeds for the two current r30 targets (10 tests collected).
- Negative: r29 abstention collection exposes its syntax error.
- Negative: r29 architecture collection exposes its dynamic-module registration failure.
- Negative: r29 primary-source collection exposes its package-relative import failure.

The three r29 failures are preserved as product/test defects because those files are outside this task's write scope.

## Validation

Required command: .venv/Scripts/python.exe -m pytest -q tests/test_r31_collection_gate.py

Acceptance remains with independent QA/reviewer and CrewSync readback. A passing gate is collection evidence only; it is not ACCEPTED or GREEN.
