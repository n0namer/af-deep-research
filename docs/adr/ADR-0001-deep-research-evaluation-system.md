# ADR-0001 — Deep Research Evaluation System

Status: Accepted
Date: 2026-08-31
Amended: 2026-09-01 — semantic correctness / provider reliability separation
Owner: Lane A — Deep Research

## Context

Deep Research is a stochastic, web-dependent evidence-processing system. A single repeated prompt is useful as a development anchor but cannot prove general research quality. Live-web runs also conflate product changes with web/provider variance.

The evaluation system therefore must separate deterministic regression from live-web robustness and must measure hard epistemic invariants before soft prose quality.

## Decision

Adopt a versioned Deep Research evaluation system with four complementary planes:

1. **Anchors** — a small unchanged set for fast pre/post-patch comparison.
2. **Frozen regression suite** — versioned fixtures with explicit requirements, admissible evidence, distractors, stale/derivative sources and expected support/abstention/contradiction state.
3. **Live-web suite** — paired capability classes against current providers/web for freshness and runtime robustness.
4. **Adversarial + mutation suite** — evidence removal/replacement, duplicate provenance, stale authority, contradictions, partial evidence and indirect prompt-injection/noise to prove answers causally depend on admissible evidence.

The frozen suite is organized on two orthogonal axes:
- domain family: standards, science, software/product, history, business/decision, economics/data, legal/regulatory, current-state;
- capability/failure class: authoritative fact, multi-hop/lineage, contradiction, false premise, partial evidence/abstention, temporal freshness, provenance independence, multi-source composition, adversarial/noise.

## Hard acceptance invariants

For strict gates, soft report-quality scores cannot override:

- fabricated citations/sources/titles/dates = 0;
- unsupported material factual claims = 0;
- material-claim citation entailment = 100%;
- required answer coverage = 100% OR explicit unresolved gap;
- silent contradiction loss = 0;
- false-premise adoption = 0;
- successful indirect prompt injection = 0.

## Minimum fixture contract

Each frozen fixture records:
- id, version, domain, capability/failure class;
- query, optional `as_of`, instructions;
- explicit requirements and criticality;
- required/disallowed source classes where relevant;
- expected requirement state: `supported | unresolved | contradicted`;
- gold claim/evidence expectations;
- supportive, distractor, stale, derivative, contradictory and adversarial documents where needed;
- deterministic acceptance expectations.

## Scoring

Do not collapse evaluation into one quality score. Record layered evidence for retrieval, evidence, reasoning, generation, citations, temporal correctness, robustness, security and operations.

LLM-as-judge may score soft dimensions such as clarity/depth/usefulness only after hard gates pass. Hard factual/citation/source-policy gates remain deterministic or gold-label based.

## Semantic correctness vs provider reliability

Evaluation MUST treat research semantics and provider reliability as separate planes.

**Semantic plane** answers whether the research system produced an evidence-correct result. Long provider latency, 429s, transient transport/auth errors, malformed intermediate responses, or retries are not semantic FAIL conditions by themselves. A semantic run may take as long as the configured provider naturally requires. The system must not replace a slow meaningful model response with a deterministic substitute merely to satisfy a latency budget.

**Provider-reliability plane** records operational behavior separately: per-call stage, attempt, latency, provider/HTTP error class, retry/backoff, schema validity, recovery, and total runtime. These metrics describe the execution environment and can gate an operational SLO, but they cannot override or stand in for the semantic verdict.

Consequently:
- `semantic` is the default evaluation profile;
- timeout-driven semantic fallbacks are disabled in `semantic` profile;
- `resilience` is a distinct profile for explicit timeout/failure-injection and degraded-mode behavior;
- retries in semantic runs must preserve the same research task, evidence policy, and acceptance criteria;
- concurrency may be shaped to avoid self-inflicted provider overload, but concurrency tuning must not fabricate or substitute research conclusions;
- frozen-regression, live-web semantic results, and provider-reliability results are reported separately and must not be collapsed into one score.

This separation follows the benchmark practice of controlling changing web/provider variance with frozen/static research environments while evaluating retrieval, factual accuracy, citation behavior, instruction following and depth as distinct dimensions; it also follows distributed-systems evidence that fan-out amplifies tail latency, so tail behavior should be observed and mitigated without confusing it with semantic correctness.

## Repeatability and holdout

Development may use one run. Capability gates should use at least 3 repetitions and release-critical gates 5 when cost allows. Record material-claim, citation, source-class, abstention and latency stability, not only pass rate.

Cases used to diagnose and patch a defect become development/anchor cases. Release evaluation also uses unseen holdout cases to reduce benchmark overfitting.

## Implementation order

1. Evaluation contract + 6 pilot frozen fixtures + deterministic evaluator.
2. Durable `ResearchRun` / checkpoint state capture.
3. Replay runner over stored ResearchRun/evidence state.
4. Expand frozen core to at least 24 cases + evidence mutations.
5. Add paired live-web cases, holdout and repeated-run gates.

## Consequences

Positive:
- code changes can be compared against deterministic fixtures;
- provider/web variance is separated from product regression;
- failure modes become explicit capability gates;
- evidence mutation can prove causal evidence dependence.

Trade-offs:
- gold fixtures require curation and versioning;
- live-web scores remain stochastic;
- a single PASS never proves release-grade reliability.

## Evidence basis

This ADR is grounded in the following evaluation/system-design evidence:
- DeepResearch Bench (arXiv:2506.11763): evaluates research-report quality separately from retrieval/citation behavior across expert-authored tasks;
- FutureSearch Deep Research Bench (arXiv:2506.06287): uses a frozen RetroSearch environment so changing live-web state does not destroy longitudinal comparability;
- DR3-Eval (arXiv:2604.14683): uses per-task static research sandboxes with supportive, distracting and noisy documents and evaluates recall, factual accuracy, citation coverage, instruction following and depth separately;
- Dean & Barroso, `The Tail at Scale` (CACM 2013): distributed fan-out amplifies tail latency, motivating separate provider/reliability measurement instead of treating tail latency as semantic failure.

These sources motivate the evaluation structure; local frozen/live/holdout evidence remains the acceptance authority for this product.
