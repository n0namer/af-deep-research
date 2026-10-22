# R30 Receipt Reducer — independent r29 evidence gate

Status: CANDIDATE / UNACCEPTED

## Scope and source of truth

Target: `af-deep-research`; task:
`af-deep-research:v2-r29-receipt-reducer-20261015-r1`.

The governing source of truth is
`docs/acceptance/c4-releasegate-reducer-frontier-20261013.md`. Its current
candidate state records that original producer and independent-QA receipts,
native task-to-result evidence, and a usable upstream pytest receipt are absent
from the permitted evidence. This report adds an independent reducer test only;
it does not edit or close any original r29 task.

## Reducer contract

`tests/test_r30_receipt_reducer.py` implements a conservative per-key readback:

| Required evidence | State |
| --- | --- |
| `WORKER_COMPLETED`, current source SHA, exit code 0, tests present, true independent QA | `ELIGIBLE` |
| Missing independent QA | `BLOCKED` |
| Stale/mismatched source | `BLOCKED` |
| Missing tests or nonzero/unknown exit | `BLOCKED` |
| Empty key or false DONE claim | `BLOCKED` |
| Any non-`WORKER_COMPLETED` outcome | `BLOCKED` |

Eligibility is not acceptance or terminal DONE. Coordinator-owned readback and
independent reviewer authority remain required.

## Affected-only dependency front

Eligible in this lane:

- The local source-bound reducer oracle and its focused pytest target.
- The two inspected source files, bound by their current SHA-256 values.

Blocked dependencies:

- Original r29 producer receipts and exact independent-QA receipts are not in
  the authorized evidence.
- Native CrewSync task-to-result terminal readback is coordinator-owned and absent.
- Any upstream test with no actual local `.venv` pytest result remains BLOCKED.

No replacement task, live-task mutation, or original r29 file edit is authorized.

## Validation receipt

Required command:

```text
.venv/Scripts/python.exe -m pytest -q tests/test_r30_receipt_reducer.py
```

Actual scoped runner receipt:

- exit code: `0`
- result: `8 passed in 0.07s`
- runner identity: `source_identity_sha256=f5033d63deec1caacefcab14a268dcf7fb391e268628a072ff6b2d504db60f03`
- source SHA-256: `research_run.py` =
  `87c193a386be13daa2b89dceac6b749a87ae9b47efd84b18bd598017c6e9e8c3`;
  `verified_pipeline.py` =
  `97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87`

This artifact remains CANDIDATE / UNACCEPTED until the real pytest receipt,
independent review, and authoritative terminal readback exist.
