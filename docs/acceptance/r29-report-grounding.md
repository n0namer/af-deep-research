# R29 Report Grounding

Status: CANDIDATE / UNACCEPTED

## Scope and source evidence

This bounded acceptance slice records the current report-grounding contracts. The requested
`reasoners/deep_research_ext/report_builder.py` is absent at the inspected source revision,
so no production edit is claimed. The available implementation is in
`reasoners/deep_research_ext/verified_pipeline.py` and
`reasoners/deep_research_ext/final_verifier.py`.

Source evidence read from the target checkout:

- `verified_pipeline.py`: grounded report construction/persistence/resume signatures,
  immutable `source_file_sha256`, owner fencing, DTO version `r10`, and monotonic revision checks.
- `final_verifier.py`: citation lookup, duplicate citation rejection, unavailable-source
  rejection, closed failure on adjudication errors, and unsupported-claim accounting.
- `research_run.py`: checkpoint schema/stage validation, safe run IDs, and stale
  `source_revision` rejection.
- Search federation sources provide canonical URL and provider provenance fields.

## Definition of done and boundary result

The focused pytest file contains one positive contract check and five adversarial negative
checks. It is deliberately source-backed rather than a mock-only E2E test. It must not be
reported as product acceptance: independent QA/reducer and CrewSync terminal readback remain
required.

The missing report-builder module is the explicit next repair dependency. A future owner
should add or restore that production module only after the intended interface is supplied;
this task does not invent an unowned production API.

## Validation receipt

Command:

`python -m pytest -q tests/test_r29_report_grounding.py`

Expected evidence: six passing tests, exit code 0, with the exact current source SHA
captured by the test's digest assertion. If the authorized runner cannot execute Python,
the result must be recorded as INFRA BLOCKED, never PASS.
