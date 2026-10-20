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


## Clean exact-SHA QA rerun

- Detached read-only validation worktree: `D:/Temp/afdr-p0-strict-independent-qa-20261020`.
- Evaluated source revision: `d854c650bf15980e1bcf1b22152937c4d4b7e584`.
- Verified canonical checkout source SHA256:
  `5C241D442E42D12E025623AD5BA15FFC4A43798F8EE62B6AA0A8BCEF9B8F6E34`.
- Full combined native test command with
  `test_p0_source_authority_classifier_20261020.py`,
  `test_p0_final_assessment_source_identity_20261020.py`,
  `test_p0_strict_source_owned_publication_20261020.py`,
  `test_deep_research_ext.py`, `test_agent.py`, `test_research_run.py`,
  and `test_evaluation_suite.py`.
- Result: **121 passed, exit 0**; warnings from an existing invalid escape
  sequence in `doc_generation_pipeline.py` remain non-blocking.
- Receipt: `D:/Temp/afdr-p0-strict-independent-qa-20261020/independent-qa-20261020.log`.
- This is a separate clean-worktree test run, not a distinct human/model
  independent semantic review; final integrated SHA and live Native E2E remain
  prerequisites for authoritative acceptance.

## P0 coverage accounting source-ownership follow-up

The requirement-level coverage accountant in
`reasoners/deep_research_ext/coverage.py` previously marked a claim as
verified on `status=verified` and `support_state=source_entailed` without
checking whether its `source_id` appeared in the ledger's saved sources.

- Existing code reused; smallest correction checks membership in the
  declared source IDs before counting a verified requirement or an
  independent source group.
- New `tests/test_p0_coverage_requires_declared_source_20261020.py`
  checks the legitimate source-10 claim and a foreign-source-999 negative.
- RED: 1 failed, 1 passed on uncorrected coverage code; a foreign claim
  incorrectly returned `verified_coverage_ratio=1.0`.
- GREEN: 2 passed after the minimal source identity fence.
- One existing test fixture in `tests/test_deep_research_ext.py` was stale:
  it previously asserted verified coverage while declaring no sources at all.
  It now declares its actual source, preserving the original positive meaning.
- Broader affected regression: **123 passed, exit 0**. Receipt:
  `D:/Temp/afdr-p0-strict-publication-20261020/coverage-regression-20261020.log`.
- No actual AgentField runtime or other dirty owner file was modified.
- This is a local verified-accounting fix, not yet integrated live E2E or a
  server-authoritative CrewSync DONE.
