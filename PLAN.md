# PLAN.md — Deep Research product/runtime SoT

Status: ACTIVE
Updated: 2026-08-30
Owner: Lane A — Deep Research product/runtime engineering
Coordination SoT: `n0namer/universal-solver/docs/runbooks/agentfield-dev-debug-test-handoff.md`

## North Star

Real task -> AgentField Deep Research -> real retrieval -> source-entailing evidence -> faithful citations -> a clear, useful, decision-grade research report with explicit uncertainty.

The product under test is the **AgentField Deep Research system**, not any particular underlying LLM. The model is a replaceable runtime dependency/provider choice. Deep Research is not DONE when a reasoner returns HTTP 200 or a high internal quality score. It is DONE only when unseen research tasks are solved with supported claims, correct and complete citations, adequate source coverage, and graceful abstention when evidence is insufficient.

## Lane boundary

This file owns the Deep Research application/runtime product plan.

Lane A MAY mutate:
- permanent DEV `/app`;
- application/reasoner/retrieval/evidence/document-generation code;
- tests and DEV runtime;
- accepted product fixes in `n0namer/af-deep-research:dev`.

Lane A MUST NOT mutate the Source Loop/promotion control plane owned by Lane B without explicit recoordinaton: fleet lock, fleet promotion workflows, source-root reconciliation/materialization, production deployment provenance, production registry cleanup.

## Operating model

Default inner debug loop is container-first:

```text
CURRENT /app
-> bounded live patch
-> targeted unit/regression
-> targeted pipeline/reasoner canary
-> reload/restart only if required
-> functional canary
-> semantic E2E
-> iterate
```

Git is the durable checkpoint for accepted increments, not the mandatory transport for every debug hypothesis. Other branches/PRs/commits may be read as a candidate-fix library and useful code may be transplanted directly into permanent DEV for fast verification.

A release handoff is ready only when:
- exact `WORKING_DEV_SHA` exists in `fork/dev`;
- every required runtime delta is durably represented in Git;
- functional semantic canary = PASS;
- tests = PASS;
- runtime/config assumptions are recorded;
- required container-only changes = NONE.

## Baseline evidence — 2026-08-30

Repository `dev` at the start of the current development cycle:
- `2cb0814deda4a9ab9158a4f9a876728e6977a799`.

Permanent DEV CURRENT readback before the next batch:
- source marker: `2cb0814deda4a9ab9158a4f9a876728e6977a799`;
- `/app` git HEAD: `2cb0814deda4a9ab9158a4f9a876728e6977a799`;
- container-only modified files: `doc_generation_pipeline.py`, `tests/test_agent.py`;
- model: `openai/deepseek-ai/DeepSeek-V4-Flash-0731`;
- search: Tavily enabled + Firecrawl enabled;
- health: HTTP 200.

Accepted evidence from the current container-only source-entailment increment:
- regression suite reached `18/18 PASS`;
- real DeepSeek adjudication canary distinguished a source-entailed fact from an unsupported fact;
- strict runtime canary failed closed when no evidence passed source adjudication.

## Current open product defect

The strict-primary-source retrieval increment is now locally proven but full A1 still fails semantically.

Fresh evidence after the latest live DEV patch:
- `/app` modified files: `main.py`, `doc_generation_pipeline.py`, `tests/test_agent.py`;
- regression suite: `20/20 PASS`;
- explicit `site:rfc-editor.org` provider canaries return official RFC 9000 and RFC 9114 pages;
- direct/local `execute_intelligence_stream_comprehensive(..., source_strictness="strict")` selects RFC 9000/9114 among the capped articles;
- full `execute_deep_research` A1 still produced incomplete/generic evidence and unsupported dated claims;
- local Python signature contains `source_strictness`, while the CURRENT registered `/reasoners` schema for `execute_intelligence_stream_comprehensive` does not expose that field;
- CURRENT AgentField registry simultaneously reports two active `meta_deep_research` registrations for the same endpoint `http://deep-research:8001` (versions `1.0.0` and `3.0.0`). This is registry drift evidence, not permission for Lane A to perform registry cleanup.

Current failing-layer hypothesis:

```text
parent strict mode
-> nested AgentField reasoner call boundary
-> stale/partial registered child contract may omit source_strictness
-> child defaults to mixed semantics
-> full A1 retrieval differs from the directly verified strict child behavior
```

A second independently evidenced defect remains after retrieval: when admissible evidence is insufficient, the writer can still fill factual gaps from model knowledge instead of abstaining.

## Current 30-minute batch — strict-policy propagation across AgentField child boundary

BMAD route semantics: `bmad-help -> bmad-quick-dev`. CURRENT AgentField discovery exposes no BMAD skill, so do not pretend a BMAD action ran; apply the same stages/DoD discipline directly.

### Goal

Make full AgentField Deep Research preserve strict-source semantics across the nested child-reasoner boundary without mutating Lane B registry/source-loop control-plane state.

### DoD

1. Inspect the CURRENT AgentField SDK/decorator schema generation and nested-call serialization path enough to explain why local Python signature and registered child schema diverge.
2. Add a targeted regression reproducing strictness loss at the parent→child call boundary, or an equivalent deterministic contract test if the SDK boundary cannot be instantiated cheaply.
3. Implement the smallest Lane A-safe fix so strict semantics reach the child execution even under the current registry state.
4. Direct child canary proves primary-source strict behavior through the same call path used by the full pipeline.
5. Full repository regression suite remains green.
6. Rerun the same A1 prompt only after lower gates PASS.
7. A1 PASS only if material externally verifiable claims are supported by cited sources; if evidence remains insufficient, the report must abstain rather than fill gaps.

### Stop / replan conditions

- If SDK schema generation is locally wrong and safely fixable in application usage, fix the application/decorator contract and retest.
- If duplicate/stale registry selection is the failing layer, do not clean registry in Lane A; make the product call path robust to it or hand the registry finding to Lane B.
- If strict semantics propagate correctly but source coverage remains incomplete, return to retrieval coverage.
- If source coverage becomes adequate but writer still invents claims, move immediately to programmatic evidence-sufficiency/abstention enforcement.

## Subsequent gates

Do not skip semantic gates:
- after A1 true PASS -> A2 contradiction/architecture task;
- after A2 PASS -> A3 false-premise task;
- then A4 current-trend, A5 temporal/freshness, A6 decision-matrix;
- only after A1-A6 semantic acceptance prepare final Lane A handoff with exact `WORKING_DEV_SHA`.

## Anti-drift rules

Before every material batch:
1. reread this file;
2. reread the coordination SoT in `universal-solver`;
3. read CURRENT runtime source marker + git HEAD + native `git status`;
4. compare CURRENT tests/execution state with the last recorded evidence;
5. if facts differ, update this file before following a stale plan.

After every material batch:
- record PASS/FAIL/PARTIAL evidence;
- record exact files/runtime state changed;
- record the one next bounded move;
- do not claim DONE without end-to-end semantic evidence.
