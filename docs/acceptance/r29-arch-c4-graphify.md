# R29 ArchSteer C4 Graphify — source-bound candidate

Status: CANDIDATE / UNACCEPTED

## Definition of done

This artifact binds current readable production signatures and source hashes to a native pytest check. It covers one valid grounded VerifiedSourceReport and four adversarial negatives: malformed SHA-256, duplicate fact IDs, stale checkpoint revision, and unsupported DTO version.

## Current source evidence

| Source | Current SHA-256 | Interfaces checked |
| --- | --- | --- |
| reasoners/deep_research_ext/research_run.py | 87c193a386be13daa2b89dceac6b749a87ae9b47efd84b18bd598017c6e9e8c3 | begin_research_run, checkpoint_research_run |
| reasoners/deep_research_ext/verified_pipeline.py | 97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87 | build_grounded_verified_report, resume_grounded_verified_report |

The current source defines VerifiedSourceReport.dto_version == r10 and validates grounded facts against lowercase 64-character SHA-256 values. ResearchRun checkpoints enforce source revision and sequence fencing.

## Graphify / ArchSteer boundary

The authorized read scope does not include .archsteer/model.json, .archsteer/architecture.md, or graphify-out/graph.json; therefore this candidate does not claim fresh hashes for those artifacts. The existing basefive-r14-contracts.json records a stale research_run.py hash (a4caa1...) versus the current scoped read (87c193...) and itself states that Graphify lacks source hashes/signatures. Independent QA must supply or verify the actual Graphify/ArchSteer artifacts before acceptance.

## Validation

Command requested: python -m pytest -q tests/test_r29_arch_c4_graphify.py

The scoped MCP runner may only authorize Node/Vitest/tsx targets; if it denies this Python file, that is an infrastructure blocker and must not be converted to PASS.
