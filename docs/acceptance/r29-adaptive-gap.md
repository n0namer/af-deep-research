# R29 Adaptive Gap Retrieval

Status: CANDIDATE / UNACCEPTED

## Goal and source evidence

Adaptive retrieval must not schedule the same unresolved requirement/query repeatedly after an unverified round. The production implementation is in `reasoners/deep_research_ext/gap_research.py` (current write receipt SHA-256: `22a3d7b4511fabf2b964247425f5439983f5d95f70de3b4cfc677a6945440d78`).

The change records normalized gap query attempts in `research_package["gap_research_attempts"]`, including zero-result attempts, and filters previously attempted keys before invoking `stream_executor`. Existing admissibility checks still reject blank URL/content and instruction-injection markers.

## Focused checks

Test target: `tests/test_r29_adaptive_gap.py`

The authorized test runner returned:

```
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
exit_code=null
stderr="A regular local .venv Python executable is required."
source_identity_sha256=286d6dedbb789c19c06bc181acfe41a8b66b1d7151795ae3ea5027113e148bd3
```

No PASS is claimed because native pytest did not execute. The test file covers one positive retrieval path and adversarial negatives for prompt injection, invalid sources, duplicate normalization, repeated unverified queries, and zero budget.

## Self-review and remaining work

Only authorized files were changed. No provider, deployment, credential, task, lease, or acceptance state was modified. Independent QA must run `python -m pytest -q tests/test_r29_adaptive_gap.py` in an environment with a regular local `.venv`, inspect the current source/test hashes, and verify the affected retrieval path before acceptance.
