# Base20 Gap Retrieval Acceptance

Status: candidate / independent QA required
Date: 2026-10-13

## Scope

The adaptive gap round now treats retrieved payloads as untrusted data. It admits only sources with a stable citation identity and non-empty content, rejects known instruction-bearing payloads, deduplicates against the existing package, and keeps article evidence bound to admitted source IDs.

A non-positive `source_budget` returns an explicit budget-exhausted trace without invoking retrieval. Admissible supporting and contradictory sources remain represented together; the round does not silently collapse disagreement.

## Bounded acceptance cases

- Missing URL/content: skipped and cannot create a citation.
- Duplicate URL: skipped without a repeated effect.
- Prompt-injection marker in source content: skipped as inadmissible data.
- Contradictory admissible evidence: preserved in the merged ledger for downstream coverage/stopping logic.
- Zero budget: abstention-compatible trace; executor is not called.
- No new verified claim: `novelty_exhausted` remains true so the caller can stop.

## Evidence

Focused test target: `tests/test_gap_recovery_goal_wave.py`.

Requested command: `python -m pytest -q tests/test_gap_recovery_goal_wave.py`.

The scoped MCP runner rejected the Python test file with `GO_WAVE_NODE_ERROR:test_file_not_allowed`; Python execution was therefore not available in this worker. Independent QA must run the requested pytest command and the affected regression suite before acceptance.

Changed source: `reasoners/deep_research_ext/gap_research.py`.
