# A1 Semantic Acceptance vs Provider Reliability — Evidence Report

**Task:** `af-deep-research:v2-a1-semantic-provider-gate-20261011-r1`  
**Attempt:** `attempt-f083094d-6fa0-41ca-9bbe-729be6727064`  
**Session:** `manual-20261011-7project-af-deep-research-stock-14dc11ed1b577e34`  
**Date:** 2026-10-11  
**Outcome:** Candidate evidence only; A1 is **not accepted**.

## Scope and source-of-truth status

- **FACT — current repository shape:** The live file inventory is Python (`main.py`, `doc_generation_pipeline.py`, `reasoners/`, and `tests/`); no JavaScript/TypeScript test files were present in the scoped inventory. `AGENTS.md` and the project heading still describe a TypeScript/Node project, so those instructions are stale relative to the checked-out source.
- **FACT — plan intent:** `PLAN.md` separates semantic acceptance from provider reliability. Provider latency, retries, 429s, and transport/auth failures are operational observations; they must not be treated as semantic failure. Semantic acceptance requires evidence-grounded claims, citation entailment, explicit contradiction/uncertainty, and fail-closed delivery.
- **FACT — deterministic evaluation exists:** `reasoners/deep_research_ext/evaluation.py` defines hard gates, six pilot corpora, a 24-case frozen core, holdout fixtures, evidence-removal mutations, and stored semantic-snapshot evaluation. Existing tests assert baseline replay passes and decisive-evidence removal fails closed.
- **FACT — provider telemetry is separate:** `main.py:ai_with_dynamic_params` records `started`, `success`, and normalized error events through `reasoners/deep_research_ext/provider_telemetry.py`; events deliberately exclude prompts, responses, API keys, and raw error bodies. A provider `success` event is therefore transport evidence only, not semantic proof.
- **UNKNOWN — live Git state:** The granted scoped tools expose source reads and Node test execution but no Git branch/status/diff command. The historical commit and runtime claims in `PLAN.md` are not treated as current Git proof. Current source readback hashes are recorded below instead.
- **UNKNOWN — loaded runtime provenance:** No live service, container, deployment, or paid/web provider was contacted. Runtime-loaded code was not independently proven from this scoped attempt.

## Source snapshot inspected

- `PLAN.md` SHA-256 `d6906ef66b6dca7d4537baf814bbb79b5249c501317cbbea5e7cba054c3f67`; it contains historical source/runtime notes through 2026-09-16 and explicitly defers product semantic acceptance.
- `reasoners/deep_research_ext/final_verifier.py` SHA-256 `922fe893a22fd55c5ed163d4849b3cfae30dea37118e609517e7742cbb737ddd`.
- `reasoners/deep_research_ext/verification_bridge.py` SHA-256 `afcfb8a9204b323fad30ea822590c95c44131216b5ab31e8e4cfa42658b86b3c`.
- `reasoners/deep_research_ext/verified_pipeline.py` SHA-256 `1ea0b249afc0c84d57824b78c5b4e6b3a79ae40a5b5890ed1a91d1046a872d1f`.
- `reasoners/deep_research_ext/evaluation.py` SHA-256 `0399e49ab5e5867f57c2731fa68b94b6fca35282ddb0c64c7baa098fc03f2f6d`.
- `tests/test_deep_research_ext.py` SHA-256 `e6d1062782c09d32ae8460332e4a9099b280551122636119acc9261d5011db2c`.
- `tests/test_evaluation_suite.py` SHA-256 `99e130ababb00ef648669e81ab4f71a5a9da2ac6d9cd61d76aec518464765617`.

## Highest-impact unproven correctness bug

### Fail-open claim identity in the final semantic gate

**Owner:** `reasoners/deep_research_ext/final_verifier.py`, `verify_final_document()` / nested `verify_one_claim()`.  
**Acceptance path:** `reasoners/deep_research_ext/verified_pipeline.py` invokes `verify_final_document()` for strict source modes and changes the result to `post_generation_rejected` only when that verifier reports failure.

For each draft claim, the verifier constructs expected adjudication facts with IDs of the form `D1:S1`, `D1:S2`, etc. After the provider/adjudicator returns, the implementation currently accepts the claim when **any** returned assessment has `is_allowed and is_source_supported`. It does not require the assessment `fact_id` to match one of the expected candidate IDs for that claim. Consequently, a structurally valid provider response can be cross-wired, stale, duplicated, or otherwise mis-associated and still mark an unrelated claim as supported.

This is a semantic correctness defect, not a provider-reliability defect: the provider may return HTTP/API success and valid schema data while the evidence-to-claim identity binding is wrong. The final gate must reject the claim unless a positive assessment is tied to the exact candidate fact generated for that claim.

### Deterministic reproduction

1. Build a document containing one material claim: `The Moon is made of cheese [1].`.
2. Provide citation `1` for a source whose content is `RFC 9000 specifies QUIC.`.
3. Make the claim extractor return `DraftClaim(claim_id="D1", text="The Moon is made of cheese.", citation_ids=[1])`.
4. Make the fake adjudicator return one positive `AIAssessment` with `fact_id="D1:S999"` (or a different claim ID), `is_allowed=True`, and `is_source_supported=True`.
5. The verifier has generated candidate ID `D1:S1`, but the current `any(...)` check ignores that mismatch and returns `supported=True`; the final state can therefore report `passed=True` for an unsupported claim.
6. Expected result: `passed=False`, `supported_claim_count=0`, and `unsupported_claims[0].reason == "cited_evidence_does_not_entail_claim"` (or a more specific fail-closed identity reason).

The reproduction uses no network, model, or live service and isolates the semantic binding defect from transport behavior.

### Why this outranks other observed gaps

- It sits on the strict post-generation acceptance boundary, where a false positive directly becomes a delivered verified report.
- Existing frozen-corpus replay proves the deterministic evaluator’s expected states, but does not exercise the live `final_verifier.py` provider-result identity binding.
- `reasoners/deep_research_ext/verification_bridge.py` already indexes assessments by `fact_id` and leaves unmatched claims unverified; the same defensive invariant is missing in the final verifier. This makes the final verifier the precise repair owner rather than a broad provider or corpus redesign.
- A transport `success` signal cannot detect this defect. Only an adversarial semantic regression with a mismatched assessment ID can prove the gate fails closed.

## Existing evidence and test owners

**Positive/frozen semantic evidence already present:**

- `tests/test_evaluation_suite.py::test_frozen_rfc_anchor_replays_to_pass_from_primary_evidence`.
- `tests/test_evaluation_suite.py::test_evidence_removal_mutation_forces_unresolved_and_gate_failure`.
- `tests/test_evaluation_suite.py::test_all_six_pilot_frozen_corpora_replay_to_expected_gate_pass`.
- `tests/test_evaluation_suite.py::test_each_pilot_has_a_causal_evidence_removal_mutation_that_fails_closed`.
- `tests/test_evaluation_suite.py::test_all_24_frozen_core_cases_replay_to_expected_baseline_pass`.
- `tests/test_evaluation_suite.py::test_all_24_frozen_core_cases_fail_after_removing_decisive_admissible_evidence`.
- `tests/test_evaluation_suite.py::test_all_holdout_cases_replay_to_expected_pass_and_fail_when_decisive_evidence_removed`.

**Current final-verifier coverage:**

- `tests/test_deep_research_ext.py::test_final_verifier_rejects_uncited_material_claim` proves an uncited claim fails.
- `tests/test_deep_research_ext.py::test_final_verifier_accepts_when_every_material_claim_is_cited_and_entailed` proves the happy path with a matching assessment ID.
- `tests/test_deep_research_ext.py::test_final_verifier_bounds_concurrency_and_preserves_claim_order_on_failures` proves bounded scheduling and fail-closed provider exceptions.
- `tests/test_deep_research_ext.py::test_verified_pipeline_rejects_strict_writer_draft_when_final_verifier_fails` proves pipeline fallback after verifier failure.

**Missing regression:** no test asserts that a positive assessment with a mismatched `fact_id` is rejected. Provider telemetry tests only prove safe metadata and `started`/`success` recording; they do not establish semantic acceptance.

## Validation performed in this attempt

- **FACT:** Read the live source, plan, README, evaluation tests, extension tests, provider telemetry, verification bridge, final verifier, and pipeline source through scoped MCP readback.
- **FACT:** Attempted `run_node_tests` on `tests/test_evaluation_suite.py`; the scoped tool returned `GO_WAVE_NODE_ERROR:test_file_not_allowed`. The repository inventory contains Python tests, not Node tests, so no Node test verdict is claimed.
- **FACT:** No Python test command was available in the authorized tool set; no pytest PASS/FAIL is claimed.
- **FACT:** No code, provider, web, deployment, Git, or live-service side effect was performed.
- **FACT:** The only changed file is this report under the exact authorized write scope.

## Pareto-prioritized next coding/test task

**Task:** Harden `reasoners/deep_research_ext/final_verifier.py` claim-to-assessment identity binding and add one focused regression in `tests/test_deep_research_ext.py`.

**Required implementation:**

1. In `verify_one_claim`, compute the expected candidate fact IDs from the claim’s citation candidates.
2. Accept only assessments whose `fact_id` exactly matches an expected candidate ID for this claim.
3. Treat missing, duplicate, unknown, or mismatched assessment IDs as fail-closed verification failure; do not let an assessment from another claim satisfy this claim.
4. Preserve the current bounded concurrency, exception fail-closed behavior, and multi-citation semantics: one matching admissible/source-supported citation may support a claim, but unrelated assessments may not.

**Exact acceptance criteria / DoD:**

- A mismatched positive assessment ID yields `passed=False`, zero supported count for that claim, and an explicit unsupported reason.
- An empty assessment list, provider exception, unavailable citation source, and mismatched-only response all fail closed.
- A matching positive assessment still passes the existing happy-path test.
- A batch containing one valid assessment and one unrelated positive assessment cannot cross-satisfy another claim.
- Frozen corpus replay and evidence-removal tests remain unchanged and pass.
- Provider telemetry `success` remains recorded independently and never substitutes for semantic verification.
- Focused Python tests and the repository’s broader Python suite are run by an environment with the appropriate Python test runner; this scoped attempt cannot claim that run.

**A1 status after this report:** semantic/provider separation is documented and mostly represented in source, but A1 remains **UNACCEPTED** because the strict final semantic gate has an unproven fail-open identity-binding path.
