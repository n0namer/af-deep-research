# R30 Native Smoke Acceptance

Status: CANDIDATE / UNACCEPTED

Target: `af-deep-research`; task `af-deep-research:v2-r29-native-smoke-20261015-r1`.

This independent test reads the current r29 Python source by path and covers one positive strict source/fact provenance and durable effect-idempotency flow, plus negative malformed source hash, stale source revision/checkpoint CAS, duplicate effect/wrong owner, and fail-closed verifier abstention checks. It does not edit r29 production files or self-accept the task.

Validation command:

```text
.venv/Scripts/python.exe -m pytest -q tests/test_r30_native_smoke.py
```

The final receipt must record the exact exit code and test output SHA. Acceptance remains with the independent reducer/verifier and CrewSync terminal readback.
