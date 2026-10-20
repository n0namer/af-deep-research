---
status: in-review
route: build
source_task: af-deep-research:v2-r29-final-fact-verifier-20261015-r1
baseline_commit: 904906c5f82493ac3ce1f77a7d938fbb543a8f97
date: 2026-10-20
---

# P0 strict final-verifier source identity

## Intent

Eliminate false-positive acceptance of an otherwise matching fact_id when a model
returns the wrong source_id or omits source_id. Reuse the existing verified pipeline,
AIAssessment, source notes, and final_verifier; no additional orchestration.

## Scope

- doc_generation_pipeline.py: preserve the existing dirty main's seven-line
  schema and assessment-prompt change as a tracked integration overlay.
- reasoners/deep_research_ext/final_verifier.py: preserve its existing two
  guard changes, then require the assessment source_id to match the exact
  candidate source_id by fact_id before trusting the source-supported verdict.
- tests/test_p0_final_assessment_source_identity_20261020.py: real DTO
  positive and adversarial negative cases.

## Acceptance

- Given RFC 9114 as source article id 10 and citation 1, when the assessment
  echoes fact D1:S1 and source 10, then final verification passes.
- Given matching fact id but source None, 1 or 999, then verification rejects.
- Given source 10 but a foreign fact id, then verification rejects.
- Exact source content and citation URL must be the same candidate.
- No edits are made in the main dirty dev worktree.

## Evidence

- Current dirty main overlay source SHA is recorded by the integration worktree.
- RED before code change: 3 failed, 2 passed.
- GREEN after code change: 5 passed.
- Previous legacy fixture that accepts supported facts without source_id is
  outdated for strict verification, and is a disclosed QA compatibility blocker.
- Other concurrent dirty files are copied into a separate snapshot only; never
  committed or overwritten in dev.

## Release boundary

Do not claim independent review, runtime deployment, native multi-source E2E,
or CrewSync SERVER_DONE on the basis of these local tests.

## QA update 2026-10-20
- Clean worktree HEAD 8cd4490515f7321126cd845fe3f4c301ba2b56ff.
- Fixed stale test-only source identity fixtures and nonportable /app/main.py reference.
- Exact clean SHA regression: 117 passed, pytest exit 0.
- Integrated live source overlay: 105 passed, 8 skipped, one legacy test deselected.
- Independent semantic reviewer, live multi-source E2E, and server terminal acceptance are still pending.
