# Native Evidence Release Gate — 2026-10-13

## Status

- Outcome target: `CANDIDATE / UNACCEPTED` only.
- Scope: one new release-gate test and this evidence note; no production or existing QA files are modified.
- Gate file: `tests/test_releasegate_native_evidence_20261013.py`.
- External effects: deterministic cases use only controlled in-process fixtures and a pytest temporary directory. Live network/provider use is disabled unless explicitly admitted.

## Source Binding

The release gate intentionally fails when any covered native implementation file changes without an evidence review and SHA refresh.

| Source | SHA-256 |
|---|---|
| `reasoners/deep_research_ext/verified_pipeline.py` | `1ea0b249afc0c84d57824b78c5b4e6b3a79ae40a5b5890ed1a91d1046a872d1f` |
| `reasoners/deep_research_ext/gap_research.py` | `0e268ac8c179938f4b2ddc37970bb89fd78438e23845b39db66f8ead1134b1fd` |
| `reasoners/deep_research_ext/evidence_ledger.py` | `343c4fdc149828980c2d919ee2a6ebef6a1080223aefff42707f07b2a2717e67` |
| `reasoners/deep_research_ext/final_verifier.py` | `d9210579b1a673b1cdc7dbd15f4f0cff660c1e75eedaa4abc54d9a910c00aef1` |
| `reasoners/deep_research_ext/research_run.py` | `713caa8e1d6c4e96127b72571b42ab34882542cd478976fe83bb3e2785681d4c` |

## Covered Behavior

1. **Positive native full cycle**
   - Starts with one controlled primary source and one unresolved requirement.
   - Uses the real native gap-round implementation to retrieve the missing source.
   - Builds and verifies the evidence ledger, reaches full requirement coverage, synthesizes a cited report, validates expected `fact_id` values, and persists a terminal report.
   - Checks persisted coverage, evidence summary, final verification, semantic snapshot, provider-event receipts, checkpoint sequence, stage history, and absence of abandoned atomic-write temporary files.

2. **Negative gap and abstention path**
   - Returns a prompt-injection source from the gap retriever.
   - Confirms native source admission rejects it, novelty is exhausted, strict coverage remains incomplete, the writer is never called, and the persisted terminal mode is programmatic partial abstention with the unresolved requirement retained.

3. **Restart behavior**
   - Persists a complete research package, reloads it through `resume_research_run`, and resumes the pipeline from the stored run.
   - Confirms initial retrieval and gap retrieval are not repeated, the resumed metadata identifies the durable run, and the terminal checkpoint remains reproducible.

4. **Citation and `fact_id` rejection**
   - Confirms a material claim without a citation fails closed.
   - Confirms an adjudicator response containing an unknown `fact_id` fails closed as non-entailing evidence.

5. **Real provider verification when locally admitted**
   - Default behavior is an explicit pytest skip, not a simulated provider PASS.
   - Set `AF_RELEASEGATE_LIVE_PROVIDER=1` only in an environment authorized for external search and model calls.
   - Admission also requires `OPENAI_API_KEY` or `OLLAMA_BASE_URL`, plus a configured search provider supported by the application.
   - The live case retrieves RFC Editor evidence through the application search adapter and obtains a structured claim through the application model adapter, then checks the provider telemetry success receipt.

## Reproduction

Authorized focused validation target:

```text
tests/test_releasegate_native_evidence_20261013.py
```

Final candidate test SHA-256: `75171c60b92236c6fee6b7e47facc10af659e90c5796ed381250055b18c00b54`.

Actual scoped runner receipt on 2026-10-13:

```text
status: BLOCKED
code: PYTHON_VENV_UNAVAILABLE
engine: python:pytest
source_identity_sha256: 90420f9b47ab799745cea7a90ce5caa57b5a0bb0fee80b32894e95aa90f565a3
exit_code: null
stderr: A regular local .venv Python executable is required.
```

The runner was not retried because the failure is an unchanged infrastructure prerequisite, not a product-test failure. The final candidate was then source-reviewed and reduced below the repository's 500-line limit, so its final SHA differs from the denied runner receipt and remains unexecuted. Therefore no test case is reported as PASS in this attempt.

Expected deterministic result after the runner prerequisite is restored and no live-provider admission is present:

```text
5 passed, 1 skipped
```

Expected result when live-provider admission is valid and both external adapters succeed:

```text
6 passed
```

A skipped live test proves only that external provider execution was not admitted in that run. It must not be reported as real-provider evidence. A provider/search error after explicit admission is a gate failure, not a reason to silently skip.

## Acceptance Boundary

This artifact supplies candidate evidence only. Independent review/reducer execution and exact CrewSync terminal readback remain required. A green focused test, process exit, or publisher transport receipt does not mean `ACCEPTED` or `ACCEPTED_GREEN`.
