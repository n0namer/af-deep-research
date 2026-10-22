# Base20 Citation Identity Entailment

## Scope and source of truth

- Project: `af-deep-research`
- Task: `af-deep-research:v2-base20-citation-identity-entailment-20261013-r1`
- Attempt: `attempt-17d196cd-2ecf-48f9-82d2-fd8349d2df80`
- Session: `manual-20261013-base20-af-deep-research-r1-v2-b-5a522a08baa5f41e`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Source of truth: repository `AGENTS.md`, `README.md`, existing verification modules/tests, and this scoped acceptance receipt.
- BMad state: BMad Help resolved the explicit target project; no competing PLAN.md was created. The repository documentation identifies Python runtime behavior despite stale TypeScript wording in `AGENTS.md`.

## Implemented behavior

`verification_bridge.verify_ledger_claims` now admits evidence only when the retrieved article matches the ledger source by exact source ID, URL, and `content_hash`. Reused URLs are ambiguous and rejected. Provider exceptions and invalid/stale assessment fact IDs fail closed, preserving the claim as unverified. Existing unsupported-source semantics remain overturned/unsupported, and `final_verifier.py` was not modified.

## Frozen evidence package

- Article ID: `101`
- URL: `https://frozen.example/article-101`
- Content hash: `sha256:frozen-article-101-v1`
- Retrieved content: `The protocol launched in 2024.`
- Ledger source receipt: URL and content hash above, retrieved at `2026-10-13T00:00:00Z`.

## Checks

| Check | Result | Evidence |
|---|---|---|
| Positive exact article identity | TEST DEFINED | `tests/test_citation_entailment_goal_wave.py` positive bridge and final-verifier cases |
| Stale content hash | TEST DEFINED | frozen package uses `sha256:stale`; claim remains unverified |
| Cross-document/source ID mismatch | TEST DEFINED | package article ID `202` cannot satisfy ledger source `101` |
| Reused URL ambiguity | TEST DEFINED | duplicate URL causes both candidate articles to be ineligible |
| Injection and unverified-only support | TEST DEFINED | inadmissible and source-unsupported adjudications fail closed |
| Provider timeout/failure recovery | TEST DEFINED | exception leaves candidate claim unverified without retry side effects |
| Stale/cross-document assessment fact ID | TEST DEFINED | returned `A202-C1` is not accepted for expected `A101-C1` |
| Focused Python execution | BLOCKED | `go_wave.run_project_tests({file:"tests/test_citation_entailment_goal_wave.py"})` returned `GO_WAVE_NODE_ERROR:test_file_not_allowed` before test execution; no repeated denial |
| Broader affected regression | BLOCKED | same authorized runner cannot execute Python tests in this manifest; independent QA must run the requested pytest commands |

## Changed source receipts

- `reasoners/deep_research_ext/verification_bridge.py` — SHA256 `aad1f5c7a85b26a0c7a3449e9b12df5b276f8b50c264e18688195326f12db270`
- `tests/test_citation_entailment_goal_wave.py` — SHA256 `22fb7a69e16638b758837c70655f6269e2b8fcf9361d2a689cf3f9085a8d9b2e`
- `docs/acceptance/base20-citation-entailment-20261013.md` — acceptance receipt created in this attempt

## Independent acceptance required

This is a candidate implementation, not product acceptance. An independent reviewer/reducer must run:

```text
python -m pytest -q tests/test_citation_entailment_goal_wave.py
python -m pytest -q tests/test_deep_research_ext.py tests/test_native_verified_research_goal_wave.py
```

The live provider path and production runtime remain unverified; tests use a frozen offline document package and deterministic adjudicator doubles only.
