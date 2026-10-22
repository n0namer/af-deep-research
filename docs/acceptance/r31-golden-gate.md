# R31 Golden Gate — Six-Domain Source-Grounded QA

Status: CANDIDATE / UNACCEPTED

## Scope

This isolated gate checks the current production boundaries in
`reasoners/deep_research_ext/final_verifier.py` and
`reasoners/deep_research_ext/verified_pipeline.py`. It does not modify
product code, invoke providers, or mutate live task state.

## Acceptance matrix

| Case | Expected evidence |
| --- | --- |
| Six-domain golden answer | Six material claims pass strict source adjudication; the r10 report contains six unique grounded facts and a current source SHA. |
| Missing citation | Verification abstains with `material_claim_has_no_citation`. |
| Unavailable cited source | Verification abstains with `cited_source_not_available_for_verification`. |
| Duplicate citation marker | Verification abstains with `duplicate_citation_ids`. |

## Validation

Run:

```text
.venv/Scripts/python.exe -m pytest -q tests/test_r31_golden_gate.py
```

The focused test is the authoritative runtime check for this lane. Independent QA
and CrewSync readback remain required; this artifact never self-accepts.
