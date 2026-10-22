# r29 Independent Product QA

Status: CANDIDATE / UNACCEPTED

## Scope and source evidence

This bounded QA lane tests the real filesystem-backed ResearchRunStore contract in
reasoners/deep_research_ext/research_run.py. The readable architecture receipt
identifies ResearchRun schema 0.1, with checkpoint sequence, source revision, source
owner, evidence IDs, and payload fields. The inspected C4 acceptance artifact remains
candidate/unaccepted and explicitly warns that comparison hashes and blocked runners
must not be promoted to product acceptance.

The test imports and executes production code; it does not mock the persistence
adapter or claim full C4 task-to-result E2E coverage.

## Cases

- Positive: create a real run, persist a terminal checkpoint, resume it, and verify status, sequence, evidence, and terminal receipt preservation.
- Negative 1: reject traversal-like run IDs before constructing a checkpoint path.
- Negative 2: reject resume against a stale source revision.
- Negative 3: reject a stale expected checkpoint sequence so an older writer cannot overwrite newer state.

## Verification

Requested command:

    python -m pytest -q tests/test_r29_independent_product_qa.py

Runner status must be recorded from the actual native pytest invocation. A denied,
missing, or dependency-blocked runner is INFRA BLOCKED, never PASS.

## Source-bound identities

- reasoners/deep_research_ext/research_run.py: SHA-256 87c193a386be13daa2b89dceac6b749a87ae9b47efd84b18bd598017c6e9e8c3
- reasoners/deep_research_ext/verified_pipeline.py: SHA-256 97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87
- docs/architecture/basefive-r14-contracts.json: SHA-256 7d81581ed610a64337712806f7fb2edf4d6fc85d981cbfbdc692d267e79afc66
- docs/acceptance/c4-releasegate-reducer-frontier-20261013.md: SHA-256 e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce

## Acceptance boundary

This artifact provides fresh independent regression/threat coverage for the inspected
research-run boundary. It does not assert Graphify/ArchSteer completeness, C4
acceptance, production release, or independent reviewer approval.
