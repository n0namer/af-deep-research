# Base20 Partial Abstention Acceptance

## Contract

For strict evidence-only research with one supported requirement and one unresolved requirement:

- the native verified pipeline must not invoke the free-form document writer;
- the response mode must be `verified_partial`;
- supported material claims must be rendered only with an available citation;
- unresolved requirements must state explicit abstention rather than model-memory completion;
- source notes must retain citation ID, title, provenance domain, and URL;
- disputed source-entailed claims must be disclosed as contradictory evidence;
- evidence removal must leave the affected requirement unresolved.

## Implemented mechanism

`reasoners/deep_research_ext/verified_pipeline.py` computes coverage before synthesis and routes strict incomplete coverage to `build_evidence_only_gap_response` in `reasoners/deep_research_ext/synthesis_guard.py`. This path returns before `generate_document_from_package` and builds sections from source-entailed verified or disputed ledger claims only.

The guard records delivery verification in `metadata.verified_research_extension.delivery_verification`, including `verified_partial` mode and unresolved requirement IDs. Citation-bearing `source_notes` provide the provenance map for delivered evidence. Disputed evidence is disclosed without counting as verified support; the requirement remains explicitly abstained when it has no verified claim.

## Regression coverage

`tests/test_partial_abstention_goal_wave.py` exercises:

1. supported-plus-unresolved partial abstention;
2. fluent final synthesis bypass prevention;
3. decisive evidence removal with explicit abstention;
4. disputed-source disclosure without promotion to verified evidence.

## Verification status

- Static source review: PASS for the bounded contract above.
- Focused Python execution: BLOCKED by the authorized `go_wave.run_project_tests` runner, which returned `GO_WAVE_NODE_ERROR:test_file_not_allowed` for the `.py` test file.
- Independent QA and reducer acceptance: pending; this worker reports `CANDIDATE` / `UNACCEPTED` only.
