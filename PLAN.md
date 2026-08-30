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

The latest full A1 after the source-entailment fix still failed semantically.

Observed failure shape:
- strict research did not guarantee adequate primary-source coverage before the article cap;
- the research package could contain high-quality but incomplete admissible evidence;
- the writer could still state factual claims over remaining evidence gaps.

Current root-cause hypothesis with runtime evidence:

```text
strict query augmentation is largely generic "official primary source"
-> search results are interleaved
-> MAX_ARTICLES_PER_TASK cap is applied
-> strict admissibility happens too late to guarantee primary-source coverage
-> needed primary documents can be excluded
```

Direct provider canary showed explicit primary-source queries such as `site:rfc-editor.org RFC 9000 QUIC` and `site:rfc-editor.org RFC 9114 HTTP/3` return the expected official RFC pages, so the next fix belongs in Deep Research search strategy/prioritization rather than provider availability.

## Current 30-minute batch — strict primary-source retrieval before cap

BMAD route semantics: `bmad-help -> bmad-quick-dev`. If a callable BMAD skill is not present in the CURRENT tool surface, do not pretend it ran; use the same stages/DoD discipline directly.

### Goal

Prevent strict research packages from losing needed admissible primary sources to the generic article cap.

### DoD

1. Add a targeted regression reproducing the cap/policy failure.
2. In strict mode, preserve/prioritize admissible primary-source candidates before the global article cap.
3. Direct primary-source search canary still returns expected official RFC 9000/9114 pages.
4. Full repository regression suite remains green.
5. Reload only if required for changed code.
6. Rerun the same A1 prompt with the same parameters.
7. A1 PASS only if each key externally verifiable claim is actually supported by the cited source; if evidence remains insufficient, the report must abstain instead of filling from model knowledge.

### Stop / replan conditions

- If the verified primary-source query is not generated, fix query augmentation first.
- If the query is generated but provider results are bad, inspect provider/query semantics before ranking changes.
- If primary docs are retrieved but dropped before document generation, fix pre-cap prioritization/admissibility.
- If source coverage is adequate but writer still invents claims, move to gap-aware abstention prompt/programmatic gate.

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
