# R29 Grounded Document Entailment

Status: CANDIDATE / UNACCEPTED

## Goal

Strict synthesis must emit only claims that both declare a source present in the evidence ledger and are marked source_entailed. A claim with an absent source, inferred support, or contradicted support is rejected.

## Current interface evidence

- reasoners/deep_research_ext/synthesis_guard.py
  - has_source_entailed_support(claim, source_ids) -> bool
  - build_evidence_only_gap_response(...) -> DocumentResponse
- The guard now applies the source-membership predicate to verified claims, disputed claims, source-note selection, and contradiction metadata.
- Source identity is the ledger's source_id; no model-only claim is accepted as evidence.

## Focused acceptance cases

1. Positive: declared source plus source_entailed is accepted.
2. Negative: undeclared source is rejected.
3. Negative: model_inferred support is rejected.
4. Negative: source_contradicted support is rejected.

## Verification receipt

Requested command: python -m pytest -q tests/test_r29_grounded_doc_entailment.py

The scoped GO Wave runner available to this worker exposes only direct Node/Vitest execution, not Python pytest. Therefore no Python exit code is claimed here; this is an infrastructure verification blocker, not a PASS.

## Review boundary

The change is limited to source-grounded synthesis filtering. It does not alter provider retrieval, report DTOs, persistence, leases, or external task state.
