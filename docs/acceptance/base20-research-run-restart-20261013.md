# Base20 Research Run Restart Acceptance

Status: candidate implementation; independent QA remains required.

## Scope

This acceptance record covers the bounded offline checkpoint contract for a research run:

- explicit query, retrieval, ledger, coverage, and final-review checkpoints;
- atomic JSON replacement with monotonic checkpoint sequence;
- source-revision fencing so a stale run cannot resume against a different source;
- durable provider call IDs so restart logic can skip already-effected calls;
- preservation of unresolved gaps, contradiction identifiers, and terminal status;
- fail-closed handling for stale sequence numbers and corrupted checkpoint JSON.

The implementation is intentionally an in-memory/filesystem test contract. It does **not** claim distributed production durability or live-provider end-to-end acceptance.

## Evidence

- Implementation: `reasoners/deep_research_ext/research_run.py`
- Deterministic positive and adversarial tests: `tests/test_durable_research_checkpoint_wave.py`
- Existing affected regression: `tests/test_research_run.py`
- Source revision recorded in each checkpoint as `source_revision`.
- Stage transitions are retained in `stage_history`; restart returns `next_stage`, `missing_gap_ids`, `provider_call_ids`, and preserved `conflicts`.

## Definition of Done

- A first pass checkpoints through the explicit stage sequence and reaches `completed`.
- A simulated crash reloads the exact run and schedules only missing gaps; recorded provider calls are not repeated.
- Contradiction evidence survives restart and terminal completion.
- A mismatched source revision, stale checkpoint sequence, or malformed JSON is rejected without overwriting the newer checkpoint.
- No files outside the authorized task scope are changed.

## Validation

Requested command:

```text
python -m pytest -q tests/test_durable_research_checkpoint_wave.py
```

Affected regression:

```text
python -m pytest -q tests/test_research_run.py
```

The scoped MCP runner available to this worker accepts only authorized Node/Vitest/tsx test files and rejected the Python test invocation as `test_file_not_allowed`; Python execution is therefore recorded as infrastructure-blocked rather than claimed as passed. Independent QA should run both commands in a Python-capable environment.
