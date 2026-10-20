---
status: in-review
route: build
date: 2026-10-20
source_task: af-deep-research:v2-r29-grounded-doc-entailment-20261015-r1
baseline_sha: 7a80dca29bb781962d5b74151dd1078f29d6b662
gate: FOCUSED_GREEN_INDEPENDENT_QA_PENDING
---

# P0 strict evidence-only publication — source ownership fence

## Goal
Prevent strict-mode fallback publishing a source-entailed-looking claim with a
foreign/missing source_id, even when an upstream coverage snapshot incorrectly
says 100% complete. Reuse the existing implementation already present in the
shared development workspace; do not build a parallel verifier.

## Exact source scope
- `reasoners/deep_research_ext/synthesis_guard.py`: copied the previously
  implemented source-membership guard from dirty dev into this isolated worktree.
  Existing `has_source_entailed_support` only permits claims when the claim
  source is declared and the support state is `source_entailed`.
- `tests/test_p0_strict_source_owned_publication_20261020.py`: deterministic
  full DocumentResponse test for real DTOs and adversarial claim/source states.

## Given / When / Then
- Given a verified claim, exact declared source and entailed support, when strict
  fallback is built, then the claim appears with its source note and a passing
  delivery verification.
- Given an otherwise verified claim pointing to source 999 (foreign), when a
  stale coverage ratio says 1.0, then the claim is omitted and delivery is PARTIAL.
- Given an inferred or unverified claim, when strict fallback is built, then
  no unproven claim appears in the source-bound final report.

## Reproducible evidence
- RED baseline: 1 failure, 3 passing current-code native pytest tests.
- GREEN after reusing existing code: 4 tests pass.
- Native affected regression: 67 passed, exit code 0; exact log
  `D:/Temp/afdr-p0-strict-publication-20261020/quality-regression.log`.
- No external LLM, provider, or deployment call.
- Independent QA and integrated exact-SHA live multi-source E2E have not been
  completed; do not mark CrewSync DONE.

## Next dependency
Reconcile this strict source guard against the separately owned dirty dev
`verified_pipeline.py` and exact QA branch, then perform one strict native E2E.
Avoid copying unrelated untracked owner changes.
