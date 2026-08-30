# PLAN.md — Deep Research product/runtime SoT

Status: ACTIVE
Updated: 2026-08-30
Owner: Lane A — Deep Research product/runtime engineering
Coordination SoT: `n0namer/universal-solver/docs/runbooks/agentfield-dev-debug-test-handoff.md`

## North Star

Real task -> explicit research requirements -> adaptive retrieval -> validated evidence state -> evidence-bound reasoning -> faithful citations -> a clear, useful, decision-grade research report with explicit uncertainty or explicit abstention.

The product under test is the **AgentField Deep Research system**, not any particular underlying LLM. The model is a replaceable runtime dependency/provider choice.

Deep Research is a **verified evidence-processing system, not a prose-generation system**. Its primary artifact is a validated evidence state covering the user's research requirements. The final report is a constrained rendering of that state.

Deep Research is not DONE when a reasoner returns HTTP 200, a high internal quality score, or a fluent answer. It is DONE only when unseen research tasks are solved with sufficient and appropriate evidence, supported material claims, correct and complete citations, explicit handling of contradiction and temporal validity, graceful abstention when evidence is insufficient, and reproducible acceptance evidence.

### Product thesis

```text
LLM proposes / searches / interprets / synthesizes
program constrains / records / verifies
LLM writes only from accepted evidence
program verifies the final claims again
```

The system MUST prefer trustworthy incompleteness over unsupported completeness.

### Reasoning and evidence invariants

1. **No material factual claim without admissible evidence.**
2. **A citation must entail the claim, not merely discuss the same topic.**
3. **Evidence gaps MUST trigger more search or explicit abstention, never model-memory completion.**
4. **FACT, INFERENCE and HYPOTHESIS are distinct states and MUST NOT silently collapse into one another.**
5. **Contradictory evidence MUST be represented and resolved explicitly; it MUST NOT be silently averaged away.**
6. **Temporal claims MUST be valid for the requested `as_of` time and record relevant evidence dates.**
7. **Derivative sources sharing the same upstream origin MUST NOT count as independent corroboration.**
8. **Research completion is requirement/coverage-based, not `LLM says finished` or loop-count based.**
9. **False premises MUST be challengeable before explanatory synthesis.**
10. **Retrieved content is untrusted data, never executable instructions for the research agent.**
11. **The writer may compress accepted evidence but MUST NOT create new externally verifiable factual content.**
12. **The final draft MUST be independently re-checked at atomic-claim level before release.**

### Target evidence architecture

```text
USER TASK
  -> premise/task analysis
  -> Answer Contract: requirements + source needs + temporal needs + completion policy
  -> research plan / independent streams
  -> adaptive, source-aware retrieval
  -> source normalization: provenance + source class + freshness
  -> atomic evidence extraction
  -> exact-span claim/source entailment
  -> Evidence Ledger
  -> contradiction / temporal / provenance state
  -> coverage analysis
      -> insufficient: targeted retrieval
      -> sufficient: stop gate
  -> evidence-bound answer blueprint
  -> multi-source synthesis
  -> draft
  -> atomic claim extraction from draft
  -> claim <-> evidence verification
      -> supported: keep
      -> unsupported: search again / rewrite / remove / abstain
  -> final report + evaluation trace
```

The architecture is a target state, not permission to build every component eagerly. Implementation remains failure-driven: add the smallest primitive required by a demonstrated semantic failure.

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

## CURRENT evidence — 2026-08-30

Permanent DEV has been recovered around the preserved container-first product source. The previous source-pin startup failure is **no longer a current validation blocker** for Lane A product work.

CURRENT readback:
- `/app` git HEAD: `2cb0814deda4a9ab9158a4f9a876728e6977a799`;
- preserved live product delta: `main.py`, `doc_generation_pipeline.py`, `tests/test_agent.py`;
- health: HTTP 200;
- AgentField runtime: `3.0.0`;
- registered HTTP reasoner schema for `execute_intelligence_stream_comprehensive` now exposes `source_strictness`;
- regression suite after recovery: `20/20 PASS`;
- model: `openai/deepseek-ai/DeepSeek-V4-Flash-0731`;
- search: Tavily enabled + Firecrawl enabled.

Accepted lower-layer quality evidence:
- query-result starvation was fixed by fair interleaving across generated search queries;
- strict standards queries add deterministic RFC Editor / IETF companion searches;
- strict pre-cap source prioritization can retain/select RFC 9000 and RFC 9114 primary sources;
- exact-source adjudication distinguishes source-entailed facts from unsupported facts;
- strict evidence adjudication fails closed when no facts are supported;
- writer prompt already forbids filling evidence gaps from model memory, but full A1 proved prompt-only grounding is not sufficient.

Operational note: current runtime recovery uses a DEV-only runtime override that preserves the same `/app` source and avoids Git reconciliation. It is a temporary runtime mechanism, not a product-code change and not a release artifact.

## Current open product defects

### P0 — strictness propagation is incomplete across research expansion

Read-only inspection of CURRENT `/app/main.py` found a deterministic application bug:

```text
initial research stream
  -> passes source_strictness to execute_intelligence_stream_comprehensive ✅

continue_research / expansion stream
  -> does not expose/pass source_strictness
  -> child falls back to default "mixed" ❌
```

Therefore a strict research run can silently degrade during expansion even when the first research pass is strict.

### P0 — evidence gaps can still become unsupported prose

Full A1 also proved a separate upper-layer defect: when admissible evidence is incomplete, the writer can still emit externally verifiable facts from model knowledge despite prompt instructions to abstain. This requires programmatic evidence-sufficiency enforcement if it persists after strict retrieval is fixed.

### P1 — end-to-end citation faithfulness is not yet proven

Lower-layer exact-source entailment is working, but the final report is not yet independently re-verified claim-by-claim after writing. A citation adjacent to a sentence is not sufficient proof that every material claim is entailed.

## Current 30-minute batch — strict propagation through initial and expansion paths

BMAD route semantics: `bmad-help -> bmad-quick-dev`. If no callable BMAD skill exists in CURRENT tools, apply the same stages/DoD discipline directly and do not pretend the skill ran.

### Goal

Make `source_strictness` a preserved research-policy invariant across both the initial and continuation/expansion paths, then re-run the same semantic A1 gate.

### DoD

1. Add a targeted regression that fails when strict mode is lost in `continue_research` expansion.
2. Extend the continuation/expansion contract to accept and pass `source_strictness` explicitly.
3. Apply the same strict query augmentation/policy to expansion queries where applicable.
4. Targeted regression PASS.
5. Full repository suite remains green.
6. Live AgentField canary proves the runtime-loaded reasoner preserves strict policy through the path exercised by the full pipeline.
7. Rerun the same A1 prompt with the same acceptance criteria.
8. A1 PASS only if every material externally verifiable claim is supported by cited evidence; otherwise the output must expose the evidence gap instead of filling it.

### Stop / replan conditions

- If strict propagation is correct but required primary evidence is still absent, return to retrieval coverage/query policy rather than touching the writer.
- If required evidence is present but the writer still adds unsupported facts, implement the smallest programmatic `Answer Contract / coverage / abstention` gate before further prompt tuning.
- If the draft is evidence-bound but citation mapping still fails, add post-generation atomic claim/citation verification.
- Do not implement later architecture primitives merely because they are in the target architecture; require a demonstrated failing layer or acceptance-gate need.

## Semantic acceptance ladder

Do not skip gates or replace semantic evidence with health/tests alone.

### A1 — authoritative standards / citation faithfulness

Purpose: prove strict retrieval, source coverage, source-entailing claims, citation correctness and abstention behavior on the RFC 9000 / RFC 9114 / Google QUIC lineage task.

PASS requires:
- RFC 9000 and RFC 9114 identifiers and publication dates supported by authoritative primary evidence;
- lineage claims supported by admissible evidence or explicitly left unresolved;
- no fabricated title/date/status/source;
- every material claim supported by its cited evidence;
- no model-memory completion across evidence gaps.

### A2 — contradiction handling

Purpose: prove the system can represent conflicting evidence, distinguish disagreement causes and synthesize without silently averaging sources.

Likely primitive if current pipeline fails: contradiction ledger/graph with source authority, date and semantic-scope comparison.

### A3 — false-premise detection

Purpose: prove the system can challenge an incorrect premise before building an explanation around it.

Likely primitive if needed: explicit premise checker tied to the Answer Contract.

### A4 — current / changing evidence

Purpose: prove retrieval and synthesis on a topic whose state changes over time.

Required behavior: current evidence must outrank stale but previously authoritative evidence when the question is about `now` / current state.

### A5 — temporal correctness / freshness

Purpose: prove explicit `as_of` reasoning and distinction among event date, publication date, update date and retrieval date.

Likely primitive if needed: typed temporal evidence metadata and supersession checks.

### A6 — decision-grade multi-source synthesis

Purpose: prove the system can compare alternatives, expose trade-offs, preserve uncertainty and produce a useful decision matrix without inventing unsupported comparative claims.

Likely primitive if needed: compositional multi-source support and FACT / INFERENCE / HYPOTHESIS typing.

Only after A1-A6 semantic acceptance prepare final Lane A handoff with exact `WORKING_DEV_SHA`.

## Failure-driven growth backlog

These are **candidate capability increments**, ordered by expected product value. They are not automatically authorized implementation tasks; promote one into the active 30-minute batch only when a failing semantic gate or benchmark demonstrates the need.

1. **Answer Contract / requirement coverage** — decompose the user task into explicit research requirements, required source classes, temporal constraints and completion criteria.
2. **Evidence Ledger** — central durable in-run state for atomic claims, exact source spans, source class, provenance, timestamps, entailment, contradiction and requirement coverage.
3. **Programmatic evidence sufficiency / abstention gate** — prevent unsupported requirements from becoming prose even when the writer prompt is violated.
4. **Post-generation atomic claim verifier** — re-extract material claims from the draft and verify each against cited evidence before release.
5. **Contradiction graph** — preserve support/contradiction relationships and resolve based on semantic scope, authority and recency rather than averaging.
6. **Temporal evidence model** — `event_date`, `publication_date`, `last_updated`, `retrieval_date`, `as_of`, and supersession state.
7. **Source-policy by claim type** — choose authoritative evidence classes according to the claim: standards, legal, scientific, financial, current product state, historical analysis, etc.
8. **Source independence / provenance clustering** — prevent five derivative articles from counting as five independent confirmations of one upstream source.
9. **Negative-evidence semantics** — distinguish `contradicted`, `not found`, `search exhausted`, `no authoritative evidence`, and `unknown`.
10. **FACT / INFERENCE / HYPOTHESIS typing** — preserve epistemic status throughout planning, synthesis and writing.
11. **Adaptive stopping by marginal evidence gain** — continue research only while required coverage is incomplete and credible new evidence can still be acquired.
12. **Multi-source compositional attribution** — support claims that legitimately require multiple sources while preventing unsupported A+B=>C leaps.
13. **Exact evidence span + content provenance** — retain exact supporting paragraph/span, retrieval timestamp and content identity/hash where practical.
14. **Indirect prompt-injection boundary** — treat retrieved pages as untrusted data and prevent embedded instructions from affecting control flow or secrets/tools.
15. **Frozen + live evaluation split** — deterministic corpus for regression plus live-web evaluation for real-world retrieval quality.
16. **Repeatability evaluation** — run important tasks multiple times and measure claim/citation/source stability rather than accepting a single stochastic PASS.
17. **Human-reviewed golden calibration set** — small stable set for checking automated judges and preventing judge drift.

## Evaluation scorecard

Do not collapse product quality into one internal `quality_score`. Record the failing layer.

| Layer | Core metrics / checks |
| --- | --- |
| Task analysis | requirement coverage; premise correctness |
| Retrieval | evidence recall/coverage; context relevance; source-policy compliance; source diversity |
| Evidence | atomic extraction precision; exact-source entailment; provenance/independence; freshness |
| Reasoning | contradiction handling; temporal correctness; FACT/INFERENCE/HYPOTHESIS separation; gap detection |
| Generation | unsupported material claim rate; answer relevance; task fulfillment; abstention correctness |
| Citations | citation correctness/entailment; citation completeness; source identity accuracy |
| Robustness | repeatability; search variance sensitivity; provider degradation behavior |
| Security | indirect prompt-injection success rate; secret/tool instruction isolation |
| Operations | latency; cost; error rate; trace completeness |

### Strict-mode target thresholds

These are product engineering acceptance targets, not claims that the academic literature guarantees these exact numbers:

```text
fabricated citations / source titles / dates = 0
unsupported material factual claims          = 0
material-claim citation entailment            = 100%
required-answer coverage                      = 100% OR explicit unresolved gap
successful indirect prompt injection          = 0
```

## Benchmark strategy

Use two complementary evaluation planes:

```text
Frozen benchmark
  -> fixed tasks + fixed retrieved corpus
  -> deterministic regression / root-cause isolation

Live-web benchmark
  -> same capability classes against current providers/web
  -> production retrieval quality / freshness / robustness
```

After A1-A6, expand to a broader unseen set across factual, technical, scientific, current-state, conflicting-evidence, false-premise and decision-support tasks. Then add repeated runs and adversarial web-content tests.

A single successful run is not sufficient proof for a stochastic research system. Important gates should eventually record repeated-run stability for material claims and citations.

## Product defaults unless explicitly changed

- **Trustworthiness > completeness > latency > cost.**
- Prefer primary/official evidence where the claim type makes primary evidence authoritative; use strong secondary synthesis where primary material is conceptually insufficient.
- If evidence is incomplete, return the supported subset plus explicit unresolved gaps.
- Expose material disagreement instead of selecting a winner silently.
- Do not add architectural complexity unless it closes a demonstrated failure mode or materially improves benchmark evidence.

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
