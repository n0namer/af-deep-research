# R31 Crew Reducer QA

Status: CANDIDATE / UNACCEPTED

## Scope and source of truth

This independent reducer covers the current source contracts only; it does not modify production code or live CrewSync/Ruflo state. The target project is `af-deep-research`, and the authorized files are this report and `tests/test_r31_crew_reducer.py`.

## Definition of done

- One positive current-code test proves grounded report persistence is idempotent and terminal effects are fenced.
- Three negative tests prove stale source identity, stale checkpoint revision/sequence, and citation-free final-verifier abstention fail closed.
- The focused native `.venv` pytest receipt and current production source SHA are recorded below.
- The result remains CANDIDATE / UNACCEPTED pending independent QA and CrewSync readback.

## Evidence

Focused command:

```text
.venv/Scripts/python.exe -m pytest -q tests/test_r31_crew_reducer.py
```

Result: PASS — exit_code=0; 4 passed in 0.66s; runner status=PASS; runner source_identity_sha256=6f7cb59a23b6b1ce25141b7ee9ab29eae9a526e6b63704248c18114a9cc2637a.

Production source under test:

- `reasoners/deep_research_ext/verified_pipeline.py`
- Expected SHA-256: `97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87`

## Review boundary

This artifact is QA evidence, not product acceptance. It intentionally leaves source defects unchanged and reports any failure as a product or infrastructure finding for independent review.
