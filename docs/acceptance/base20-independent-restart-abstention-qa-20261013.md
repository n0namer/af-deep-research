# Base20 Independent Restart and Abstention QA — 2026-10-13

## Verdict

**RED / BLOCKED — not `ACCEPT_SCOPED`.** This independent QA lane added deterministic adversarial regression coverage, but the only authorized test executor rejected the Python test file before collection. The allowed read scope also contains no authoritative terminal-state receipt for the two producer threads, so this QA lane fails closed rather than treating candidate artifacts as accepted or terminal.

- QA timestamp: 2026-10-13 (worker session `manual-20261013-base20-independent-qa-af-deep-r-d54a27b90f081e83`)
- QA task: `af-deep-research:v2-base20-qa-restart-abstention-20261013-r1`
- Verdict owner: independent QA only; original producers remain unaccepted.
- Network/provider retrieval: not invoked.

## Frozen Reviewed Inputs

The latest permitted producer records are candidates, not accepted evidence:

| Artifact | SHA-256 | Trust state |
| --- | --- | --- |
| `reasoners/deep_research_ext/research_run.py` | `713caa8e1d6c4e96127b72571b42ab34882542cd478976fe83bb3e2785681d4c` | reviewed source, candidate implementation |
| `reasoners/deep_research_ext/synthesis_guard.py` | `a153a6c02e30bf82db0a78c6ae157abc483196ff713e051868687d7ae7f0ef7f` | reviewed source, candidate implementation |
| `reasoners/deep_research_ext/verified_pipeline.py` | `1ea0b249afc0c84d57824b78c5b4e6b3a79ae40a5b5890ed1a91d1046a872d1f` | reviewed source, candidate implementation |
| `tests/test_durable_research_checkpoint_wave.py` | `9366c7cbde76f939c409ecd5c24c2fab3a85ac08545569817203f8ee2a60f465` | producer regression, unexecuted here |
| `tests/test_partial_abstention_goal_wave.py` | `10fb6b0b74cb6023128af69b1eee2d98aed32b2684a4179d7202776e44370055` | producer regression, unexecuted here |
| `docs/acceptance/base20-research-run-restart-20261013.md` | `a05182f160261a4cb42be08e3c401acb09fc5c9802743ecae220e7b3c91a349f` | producer reports `CANDIDATE` |
| `docs/acceptance/base20-partial-abstention-20261013.md` | `654ecd2b89f51bfb345f84369d977233408f52b3886dba9fac7089e6bfc2dcaf` | producer reports `CANDIDATE` |

No record in the authorized read scope establishes that both producer threads terminated. That missing ownership/lifecycle evidence independently blocks scoped acceptance.

## Added Independent Regression

`tests/test_base20_independent_restart_abstention_qa.py` (SHA-256 `5e1c64fd7c9aa2fdc15cbf092a4697742de83725aa5e1b20defc2e67afb7b1da`) is an offline, deterministic QA suite designed to exercise the existing `verified_pipeline`, `research_run`, and `synthesis_guard` path without adding a scheduler or retrieval dependency. It is unexecuted in this lane.

Its assertions cover:

1. An injected interruption after ledger work but after the `research_package_ready` durable checkpoint; restart reads the stored package, does not call preparation twice, and reaches a terminal checkpoint.
2. Strict partial coverage with one source-entailed claim and one unsupported material requirement; the free-form writer is not called, output mode is exactly `verified_partial`, the unsupported fluent outcome is absent, and the semantic snapshot reports zero unsupported material claims with citation entailment ratio `1.0`.
3. Duplicate run identity restart after completion; the existing terminal checkpoint, provider-call receipt, conflict state, and terminal plan are preserved rather than regressed.
4. Source revision mismatch and stale checkpoint sequence; both reject before a terminal run can be overwritten, then the original terminal state reloads unchanged.

Static source review found the implementation routes strict incomplete coverage before synthesis, builds rendered claims from `verified` plus `source_entailed` ledger entries, and fences checkpoint loads/updates by source revision and expected sequence. This is source-backed design evidence only, not dynamic acceptance.

## Test Evidence

Attempted exact focused execution:

```text
python -m pytest -q tests/test_base20_independent_restart_abstention_qa.py
```

Authorized execution adapter result:

```text
GO_WAVE_NODE_ERROR:test_file_not_allowed
```

Classification: **INFRA BLOCKED**, not a semantic pass or failure. Per runner policy, the same denied Python runner was not retried for the producer regression command:

```text
python -m pytest -q tests/test_durable_research_checkpoint_wave.py tests/test_partial_abstention_goal_wave.py
```

The required canonical regression remains unexecuted in this lane. No claims of passing tests, source acceptance, producer terminality, or final acceptance are made.

## Minimum Follow-up

1. A Python-capable independent QA environment must first verify both producer threads have terminal receipts matching the frozen source artifacts above.
2. Run the focused QA command, then the two producer regressions exactly as listed in **Test Evidence**.
3. If any assertion fails, request a same-owner repair limited to the failing behavior in `reasoners/deep_research_ext/research_run.py`, `reasoners/deep_research_ext/verified_pipeline.py`, or `reasoners/deep_research_ext/synthesis_guard.py`; do not create another scheduler or broaden source ownership.
4. If all commands pass and terminal receipts are present, a separate independent verifier may issue `ACCEPT_SCOPED`; this QA worker does not self-accept.
