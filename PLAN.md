# PLAN.md — Deep Research product/runtime SoT

Status: ACTIVE
Updated: 2026-08-31
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

## CURRENT evidence — 2026-08-31

Permanent DEV remains the active Lane A workspace and is intentionally ahead of durable Git while semantic acceptance is still in progress.

Fresh CURRENT readback:
- `/app` git HEAD: `2cb0814deda4a9ab9158a4f9a876728e6977a799`;
- native dirty set: `doc_generation_pipeline.py`, `main.py`, `tests/test_agent.py`, untracked `reasoners/deep_research_ext/`, untracked `tests/test_deep_research_ext.py`;
- `final_verifier.py` SHA-256: `ad47b288c9038b43facbbb6a7b2343411cac54b2fafe43511c33314658cbb132`;
- `tests/test_deep_research_ext.py` SHA-256: `516e0eb87998b9ee4cc8d526d88b5f1332b5377688ce89c56c289ba1b46ca141`;
- AgentField runtime previously observed as `3.0.0`; permanent DEV remains the target, production remains out of scope;
- CURRENT source contains `max_gap_rounds: int = 1` in the verified endpoint/bootstrap path, but loaded permanent-DEV reasoner-schema exposure has not yet been freshly re-proven after the latest source edits;
- the last repository suite evidence is `42 PASS` from the prior accepted handoff; CURRENT rerun is presently blocked by the DEV execution mediator, so this remains historical evidence rather than a fresh PASS.

Accepted application increments now present in CURRENT `/app` beyond the older PLAN state:
- fair multi-query retrieval and strict standards query augmentation;
- strict pre-cap primary-source prioritization;
- strictness propagation through continuation/expansion;
- exact-source entailment and strict fail-closed adjudication;
- Answer Contract / requirement decomposition and claim-to-requirement mapping;
- Evidence Ledger with conservative source/provenance state;
- candidate-vs-verified coverage and strict programmatic abstention;
- post-generation atomic final verifier;
- targeted unresolved-only gap research plus novelty stopping.

Fresh runtime evidence independently confirms the latest verified canary rather than relying only on handoff text:
- query: `Using an authoritative primary source, identify the RFC number that specifies QUIC transport.`;
- research phase: about `519s`;
- total verified orchestration: about `978s`;
- evidence state: 10 sources, 120 claims, 83 verified, 2 overturned, verified coverage `1.0`;
- final verifier: 36 material claims, 13 supported, 23 unsupported;
- final mode: `post_generation_rejected` with evidence-only fallback.

Interpretation: the epistemic firewall is working fail-closed at the final gate, but final verification is too slow and free-form synthesis still overproduces unsupported claims. The immediate 80/20 move is latency reduction without weakening verification semantics, then re-run A1.

## Current open product defects / blockers

### P0 — final verification is sequential and dominates latency

CURRENT `/app/reasoners/deep_research_ext/final_verifier.py` performs one awaited exact-source adjudication per material draft claim in a sequential loop. This preserves correctness but creates avoidable wall-clock latency. The next implementation should use bounded concurrency, preserve deterministic claim/result association, and fail closed per claim on adjudication exceptions.

### P0 — A1 semantic acceptance is still not achieved

The final verifier correctly rejected unsupported free-form prose, but the system has not yet produced an A1 result in which every material claim is source-entailed or explicitly unresolved. HTTP 200 / execution success / verified requirement coverage alone are not A1 PASS.

### P0 — DEV typed mutation/validation capability gap

CURRENT operator mediation allows observation but blocks generic `pytest`/opaque mutation. Fresh operator-registry readback localizes the gap precisely: `agentfield-dev-deep-research` already has `write_policy: auto`, `live_patch_roots: ["/app"]` and `checks.pytest_q: true`, but its `capabilities` list contains only `terminal`, `sessions`, `logs`, `process`, `network`, `stats`; it omits `live_patch` and `reload`. The live-ACI implementation requires `live_patch` plus a configured root, so the main typed plane correctly returns `live_patch_not_allowed` despite the existing `/app` root and validator.

A fresh guidance request for the exact DEV registry operation returned `ALLOW`, but `execContainer` still rejected the exact file mutation as `opaque_or_unknown_mutation`; `prepareChange` also reports `approval_capability_gap`. Fresh gateway-source readback proves the backend route already exists: `server-live.mjs` exposes `POST /v1/target/file/patch` (`TARGET_FILE_PATCH`), `POST /v1/target/check` (`TARGET_CHECK`), and `POST /v1/target/reload` (`TARGET_RELOAD`), and its internal `localCall()` supplies the server-owned `GPT_ACTION_TOKEN`. Therefore no new backend primitive is required. The blocker is specifically **GPT-facing executor binding / target capability registry drift**: the callable DEV connector does not expose the already-implemented typed endpoints, and the target entry omits `live_patch`/`reload`.

Do not bypass this guardrail with opaque shell edits, token extraction, helper containers, GitHub application-code edits/redeploy, Coolify lifecycle, production or Lane B mutation. The minimal unblock is to expose/bind the existing typed endpoints and add `live_patch` + `reload` to this DEV target, then immediately return to the bounded-parallel final-verifier batch.

### P1 — loaded runtime schema needs fresh proof after next accepted patch

Source already contains `max_gap_rounds`; after the next tested source patch/reload, read back the permanent DEV reasoner schema and prove the loaded runtime exposes it before semantic canaries.

## Current 30-minute batch — bounded-parallel final verification

BMAD route semantics: `bmad-help -> bmad-quick-dev`. The handoff/PLAN defines this route, but no callable BMAD skill is exposed in CURRENT tools; therefore use the same Quick Dev stages/DoD directly and do not claim BMAD execution.

### Goal

Reduce final-verifier wall-clock latency substantially without changing exact-source entailment semantics, per-claim citation mapping, deterministic output ordering, or fail-closed behavior; then prove loaded runtime identity and re-run a bounded verified canary before exact A1.

### DoD

1. Add a deterministic regression for bounded concurrent claim adjudication.
2. Preserve claim-to-citation/source attribution and deterministic result order even when adjudications complete out of order.
3. Bound concurrent adjudications (initial target: 4-8; default implementation candidate: 6), never unlimited `gather`.
4. Fail closed per claim on ordinary adjudicator exceptions without letting one claim's failure corrupt another claim's result.
5. Targeted final-verifier regression PASS.
6. Full repository suite PASS (fresh; historical `42 PASS` is insufficient for this batch).
7. Reread exact source/hashes after tests.
8. Reload/restart the SAME existing permanent DEV container only if code loading requires it; no recreate/redeploy.
9. Read back permanent-DEV reasoner schema and prove `max_gap_rounds` is loaded.
10. Run a small verified semantic canary and record total/final-verifier latency delta versus the ~978s baseline.
11. If lower gates pass, run exact A1 with `max_gap_rounds=1` and existing strict acceptance criteria.

### Planned minimal implementation

- add bounded asynchronous adjudication in `final_verifier.py` (for example an `asyncio.Semaphore` around adjudicator calls);
- gather per-claim results while preserving input order;
- keep existing missing-citation / missing-source / non-entailment reasons;
- add an explicit fail-closed reason for adjudication exception;
- add one regression with deliberately out-of-order completion and a tracked peak concurrency <= configured bound.

### Stop / replan conditions

- If targeted/full tests cannot be executed because the typed DEV validator route remains unavailable, stop mutation and report `CAPABILITY_GAP`; do not bypass mediation.
- If bounded concurrency changes semantic outcomes or claim/source attribution, revert that batch and redesign before runtime reload.
- If latency improves but A1 still rejects unsupported prose, diagnose the unsupported claim classes and evidence mapping before adding more architecture.
- If A1 passes, move to A2 contradiction handling; do not eagerly implement later backlog items.

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
