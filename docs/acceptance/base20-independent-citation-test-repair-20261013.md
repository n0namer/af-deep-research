# Base20 Independent Citation Test Repair — 2026-10-13

Status: CANDIDATE / UNACCEPTED

## Authority and gate

- Task: `af-deep-research:v2-base20-independent-citation-qa-repair-20261013-r1`
- Attempt: `attempt-96599d5b-39e4-4889-9bc7-32d919046f00`
- Session: `manual-20261013-five-modules-targeted-repair-qa-2d93f2eef9defda1`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- BMad stage: independent QA repair after candidate implementation; independent reviewer, reducer, and exact CrewSync terminal readback remain required.
- Scope: QA fixtures, fail-closed expectations, and this evidence record only. No production, migration, scheduler, live-task, or deployment files were changed.

## Recorded producer source identity

The repair preserves the source identities recorded by the two independent QA artifacts; production source files were outside this task's write scope and were not modified.

| Source | Recorded SHA-256 |
| --- | --- |
| `reasoners/deep_research_ext/gap_research.py` | `0e268ac8c179938f4b2ddc37970bb89fd78438e23845b39db66f8ead1134b1fd` |
| `reasoners/deep_research_ext/verification_bridge.py` | `aad1f5c7a85b26a0c7a3449e9b12df5b276f8b50c264e18688195326f12db270` |
| `reasoners/deep_research_ext/final_verifier.py` | `d9210579b1a673b1cdc7dbd15f4f0cff660c1e75eedaa4abc54d9a910c00aef1` |
| `reasoners/deep_research_ext/research_run.py` | `713caa8e1d6c4e96127b72571b42ab34882542cd478976fe83bb3e2785681d4c` |
| `reasoners/deep_research_ext/synthesis_guard.py` | `a153a6c02e30bf82db0a78c6ae157abc483196ff713e051868687d7ae7f0ef7f` |
| `reasoners/deep_research_ext/verified_pipeline.py` | `1ea0b249afc0c84d57824b78c5b4e6b3a79ae40a5b5890ed1a91d1046a872d1f` |

These are comparison receipts from the original QA records, not newly recomputed production hashes in this restricted repair lane.

## Reproduced failure classification

The coordinator supplied the prior native Python receipt: `11 passed, 3 failed`.

1. Two failures were invalid QA fixtures. `tests/test_base20_independent_citation_gap_qa.py` passed `SimpleNamespace(requirements=...)` where gap research consumes the production `AnswerContract`, including its `.query` field. Both affected gap-round tests therefore failed before exercising the intended retrieval and trust behavior.
2. The third failure was an incorrect success expectation. The strict verification path had zero eligible evidence and raised `ValueError`. That is fail-closed verification behavior, not a production security defect; weakening it to synthesize a partial answer would convert absence of eligible evidence into unsupported output.

## Repair

- Replaced the structural contract stand-in with `build_answer_contract(...)` and a typed `ResearchRequirement`, preserving the real query and strictness contract.
- Retained exact provenance, content-hash, citation identity, and fact-ID assertions for the positive and adversarial citation paths.
- Changed the restart test to expect the observed zero-eligible-evidence rejection after the simulated interruption.
- Preserved durable retry assertions: the cached research package remains stored, preparation runs exactly once, the free-form writer runs zero times, and the rejected run remains resumable and non-terminal.
- Retained duplicate-restart receipt preservation plus stale source-revision and checkpoint-sequence fencing tests.

## Scoped file identities

| File | Before SHA-256 | After SHA-256 |
| --- | --- | --- |
| `tests/test_base20_independent_citation_gap_qa.py` | `370341a1288601fe7420050cb7e38696f20493848403cebc1008944600c0f52b` | `c8d93bd92191e2801c41d3f988aa9d1aa430543a758d4ad38ce48f58124653dc` |
| `tests/test_base20_independent_restart_abstention_qa.py` | `5e1c64fd7c9aa2fdc15cbf092a4697742de83725aa5e1b20defc2e67afb7b1da` | `1169573875412127c52ee3392dbcd2140a91b73213ab84d5aaa303c2ac02aa67` |

## Test evidence

Authorized focused invocation:

```text
go_wave.run_project_tests({file:"tests/test_base20_independent_citation_gap_qa.py"})
```

Result before collection:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
source_identity_sha256=370341a1288601fe7420050cb7e38696f20493848403cebc1008944600c0f52b
exit_code=null
stderr="A regular local .venv Python executable is required."
```

The identical runner dependency was not retried for the second Python file. No post-repair runtime PASS is claimed. The required independent commands remain:

```text
python -m pytest -q tests/test_base20_independent_citation_gap_qa.py
python -m pytest -q tests/test_base20_independent_restart_abstention_qa.py
```

The first command contains four focused citation/gap tests; the second contains three focused restart/fencing tests. Their positive and negative coverage includes exact citation entailment, provenance/content-hash mismatch, cross-claim fact IDs, injected and identityless sources, provider timeout, uncited abstention, cached-package retry, duplicate terminal receipt preservation, stale revision, and stale checkpoint sequence.

## Remaining producer gap

A Python-capable independent reviewer must run both focused files against the recorded production source state, confirm the repaired suite's actual counts and exit code, and investigate any source-hash drift before acceptance. The original producers remain CANDIDATE/UNACCEPTED until reviewer, reducer, and coordinator terminal readback complete. If strict zero-evidence rejection is not the intended product contract, that is a production-policy decision requiring a separately scoped original-owner change; this QA repair does not weaken it.
