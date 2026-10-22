# R29 Primary-Source Evaluation

Status: CANDIDATE / UNACCEPTED

## Scope and source evidence

This artifact evaluates existing production interfaces, not a new provider integration.
The inspected signatures are GroundedFact and VerifiedSourceReport in reasoners/deep_research_ext/verified_pipeline.py, plus ResearchRunStore.load and StaleResearchRunError in reasoners/deep_research_ext/research_run.py.
The architecture contract records the r10 DTO and source-bound APIs. The C4 reducer remains CANDIDATE/UNACCEPTED and records an earlier Python runner blocker.

## Definition of done

- Positive: six distinct source identities are accepted into one r10 grounded report.
- Negative: malformed hash, duplicate fact identity, unsupported DTO version, and stale source revision are rejected.
- Native pytest exit 0 is required; unavailable pytest is BLOCKED, never PASS.
- No credentials, network calls, mocks, production edits, commits, or deployments.

## Test evidence

Command: python -m pytest -q tests/test_r29_primary_source_eval.py

The scoped GO runner accepts Node/Vitest/tsx targets only, so native pytest execution is unavailable through this interface. This is an infrastructure verification blocker until the coordinator runs the command in the project Python environment.

## Self-review

The tests call production functions directly, cover one positive and four adversarial negatives, bind source revision and file hash, and do not claim an unavailable pytest run passed.
