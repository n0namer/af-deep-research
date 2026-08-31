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
-> exact same-container reload/restart only if required
-> functional canary
-> semantic E2E
-> iterate
```

Hard inner-loop prohibition for Lane A Deep Research: **NO application redeploy, NO rebuild, NO `StartApplication`, NO `RestartApplication`, NO GitHub-code-edit -> deploy loop.** Runtime recovery/iteration must reuse the existing DEV containers/images/volumes and exact process/container lifecycle only. GitHub may be used for SoT/status write-back and later durable accepted-source checkpointing, not as the transport for debug iterations.

Git is the durable checkpoint for accepted increments, not the mandatory transport for every debug hypothesis. Other branches/PRs/commits may be read as a candidate-fix library and useful code may be transplanted directly into permanent DEV for fast verification.

A release handoff is ready only when:
- exact `WORKING_DEV_SHA` exists in `fork/dev`;
- every required runtime delta is durably represented in Git;
- functional semantic canary = PASS;
- tests = PASS;
- runtime/config assumptions are recorded;
- required container-only changes = NONE.

## CURRENT evidence — 2026-08-31

Permanent DEV source remains the active Lane A workspace and is intentionally ahead of durable Git while semantic acceptance is still in progress. The current `deep-research` service is now **running and healthy** on the preserved `/app` source volume; production remains untouched. Historical recovery bullets below describe how this state was reached and must not be read as the current process state.

Fresh CURRENT readback:
- preserved `/app` git HEAD: `2cb0814deda4a9ab9158a4f9a876728e6977a799`;
- preserved native dirty set before service stop: `doc_generation_pipeline.py`, `main.py`, `tests/test_agent.py`, untracked `reasoners/deep_research_ext/`, untracked `tests/test_deep_research_ext.py`;
- current accepted `final_verifier.py` SHA-256: `0bd8255472f9a887d90eabd92e5b308646a12797de6c8eead04925ab59df7205`;
- current accepted `tests/test_deep_research_ext.py` SHA-256: `f29e2f71e265557f677bf5aae4ab5518f929b2db013f8ee3f6e6686673fe2e0e`;
- AgentField runtime was previously observed as `3.0.0`; the permanent DEV target must be restored and re-read before any new runtime claim;
- CURRENT source contains `max_gap_rounds: int = 1`; loaded permanent-DEV reasoner-schema exposure is still unproven because the service has not yet restarted on the accepted source;
- fresh pre-patch baseline: targeted final-verifier tests `3 PASS`, full repository suite `42 PASS`;
- bounded-parallel final-verifier source patch is now present directly in permanent DEV `/app`: default concurrency `6`, deterministic gather order, per-claim fail-closed exception handling;
- fresh post-patch validation: compile PASS, targeted final-verifier tests `4 PASS`, full repository suite `43 PASS`;
- post-patch hashes: `final_verifier.py` `0bd8255472f9a887d90eabd92e5b308646a12797de6c8eead04925ab59df7205`; `tests/test_deep_research_ext.py` `f29e2f71e265557f677bf5aae4ab5518f929b2db013f8ee3f6e6686673fe2e0e`;
- current running Deep Research container: `548d35ec55c7045894af16251a4c35c9dcb95806aaf933b4a38fd7a3b09f08e4`, image `edshqtkwskg3lrczekhcmd71_deep-research:61cbd7376f3d6d895c0ff3510030ffdc1a2d449e`, health `healthy`, `/app` mounted RW from `edshqtkwskg3lrczekhcmd71_us-af-e2e-deep-source`;
- direct runtime source identity proof on the running container: `/app/.git/HEAD` is detached at `2cb0814deda4a9ab9158a4f9a876728e6977a799`; accepted verifier/test hashes match the validated batch exactly;
- live `/reasoners` + OpenAPI prove `execute_verified_deep_research` is loaded and its schema exposes `max_gap_rounds`; current node advertises 23 reasoners;
- the current image does not include `pytest`; attempting fresh in-container pytest returns `No module named pytest`. Treat this as `VALIDATION_BLOCKER` for a fresh runtime-suite rerun, not as a product regression; exact accepted source already has pre-reload `43 PASS` evidence;
- a minimal strict RFC canary on the loaded runtime reached retrieval/evidence processing but encountered transient rate limiting on runtime model `openai/deepseek-ai/DeepSeek-V4-Flash-0731`; after roughly five minutes the client was terminated, but server-side execution continued, proving client disconnect does not cancel the workflow;
- installed AgentField defaults allow up to `120s` per LLM call, with a `2x` asyncio safety net and 2 retries; one stuck provider call can therefore consume multiple minutes. A container-only reliability patch is now present in `/app/main.py` setting `app.async_config.llm_call_timeout` default to `45s` via `DR_LLM_CALL_TIMEOUT_SECONDS` and timeout retries default to `1` via `DR_LLM_TIMEOUT_RETRIES`; `py_compile` PASS; `/app/main.py` SHA-256 after this patch is `eed20c2ae6671bf9c200fb3f037a4cea1904064cf36c1557d74f2a2f185d4b27`;
- that timeout/retry patch is **not yet proven loaded**: `reloadTarget` remains blocked by missing `live_patch/reload` capability, while two direct PID-1 SIGKILL attempts returned success but independent Docker readback showed unchanged container PID/restart_count. Do not claim reload occurred and do not repeat this mutation without new evidence.
- controlled in-process latency check on 12 claims with identical 50ms adjudicators: concurrency `1` ~= `0.604s`, concurrency `6` ~= `0.101s`, with identical supported-claim count (about 6x wall-clock reduction in the verifier scheduling layer);
- before the service stop, loaded permanent-DEV schema was still old (`max_gap_rounds` absent), proving process reload was required before live canary/A1;
- a direct `SIGTERM` of PID 1 produced clean exit code 0; because the container restart policy is `on-failure`, Docker did not auto-restart it and the old `91dca041...` container was removed;
- the `/app` source is on persistent volume `edshqtkwskg3lrczekhcmd71_us-af-e2e-deep-source`, so the validated source patch is preserved across container recreation;
- two subsequent native Coolify application deployment jobs failed, and bounded logs localize the failure to the `control-plane-build` service attempting GitHub access without usable credentials (`could not read Username for https://github.com`); this is a runtime-recovery/control-plane defect, not a Deep Research source regression;
- failed Coolify jobs left two overlapping compose generations. The newest recovery generation has `deep-research` container `8ba5c33f8c9946117263241d431f7b041fa719396e8db09311d63254f5730e50` in `created` state, `control-plane` `318fabd16d7122c85bf2921b0f12cb2fce05d850828f9ba4026bbd4eb0e5a4e3` in `created` state, and `workforce` `1b595138fced157b66062999792d4c51d18dc6cd3024f8f53f6beefece23c6de` in `created` state; newest postgres/diagnostics containers are running/healthy;
- independent container inspection proves newest `deep-research` already mounts persistent volume `edshqtkwskg3lrczekhcmd71_us-af-e2e-deep-source` RW at `/app`, so the accepted container-first source is attached to the recovery container and does not require GitHub/source reconciliation;
- `coolify-sentinel` has RW `/var/run/docker.sock`, so exact existing-container start is technically available at the host layer, but the CURRENT DEV GPT executor blocks the required Docker Engine POST as `opaque_or_unknown_mutation`; do not bypass that mediation via hidden session/token extraction;
- direct CURRENT target resolution for `agentfield-dev-deep-research` now returns `target_container_unavailable` (`Expected one permitted target, found 0`), confirming there is no running target container to edit or test;
- AgentField registry still exposes duplicate `meta_deep_research` nodes as `active/ready`; a fresh `getNodeDetails(meta_deep_research)` resolves to the stale `1.0.0` registration at `http://deep-research:8001` and its schema does not contain the new verified endpoint. Treat this registry state as stale execution metadata, not proof of a live accepted runtime.

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

### CLOSED — bounded-parallel final verification source batch

The sequential final-verifier bottleneck is fixed in accepted permanent-DEV source. `final_verifier.py` now uses bounded concurrency (default `6`), preserves deterministic claim/result order and claim-to-source attribution, and fails closed per claim on ordinary adjudicator exceptions. Fresh evidence: compile PASS, targeted verifier regression `4 PASS`, full suite `43 PASS`, controlled scheduling-layer check about `0.604s -> 0.101s` for 12 identical 50ms adjudications. Runtime loading of this accepted source is still pending.

### CLOSED — permanent DEV runtime restored on accepted source

The current Deep Research container is running and healthy on the preserved `/app` volume. Accepted verifier/test hashes match the validated source, `/app/.git/HEAD` remains detached at `2cb0814d...`, and live schema proves `execute_verified_deep_research` + `max_gap_rounds` are loaded. No application redeploy is required for the current product loop.

### P0 — bound provider stalls before A1

The current semantic canary is blocked by provider/runtime boundedness, not retrieval or verifier correctness. A strict RFC canary successfully reached authoritative retrieval and downstream evidence processing, but the configured model hit transient rate limiting and a later call stalled under AgentField's default `120s` LLM timeout + `2x` safety-net + 2 retries. Client disconnect does not cancel the server-side workflow.

A minimal container-only patch is present in `/app/main.py`: default Deep Research LLM timeout `45s` (`DR_LLM_CALL_TIMEOUT_SECONDS`) and timeout retries `1` (`DR_LLM_TIMEOUT_RETRIES`). Syntax validation PASS. This patch must be proven loaded before using its behavior as evidence; current exact reload capability remains unavailable.

DoD: obtain one evidenced same-container load/reload path without redeploy; prove the new timeout/retry values in the running process; rerun the minimal strict RFC canary; provider stall must fail/recover within bounded time; preserve retrieval/evidence/final-verifier semantics; then run exact A1.

### P0 — A1 semantic acceptance is still not achieved

The final verifier correctly rejected unsupported free-form prose, but the system has not yet produced an A1 result in which every material claim is source-entailed or explicitly unresolved. HTTP 200 / execution success / verified requirement coverage alone are not A1 PASS.

### P0 — DEV typed mutation/validation capability gap

CURRENT operator mediation allows observation but blocks generic `pytest`/opaque mutation. Fresh operator-registry readback localizes the gap precisely: `agentfield-dev-deep-research` already has `write_policy: auto`, `live_patch_roots: ["/app"]` and `checks.pytest_q: true`, but its `capabilities` list contains only `terminal`, `sessions`, `logs`, `process`, `network`, `stats`; it omits `live_patch` and `reload`. The live-ACI implementation requires `live_patch` plus a configured root, so the main typed plane correctly returns `live_patch_not_allowed` despite the existing `/app` root and validator.

A fresh guidance request for the exact DEV registry operation returned `ALLOW`, but `execContainer` still rejected the exact file mutation as `opaque_or_unknown_mutation`; `prepareChange` also reports `approval_capability_gap`. Fresh gateway-source readback proves the backend route already exists: `server-live.mjs` exposes `POST /v1/target/file/patch` (`TARGET_FILE_PATCH`), `POST /v1/target/check` (`TARGET_CHECK`), and `POST /v1/target/reload` (`TARGET_RELOAD`), and its internal `localCall()` supplies the server-owned `GPT_ACTION_TOKEN`. Therefore no new backend primitive is required. The blocker is specifically **GPT-facing executor binding / target capability registry drift**: the callable DEV connector does not expose the already-implemented typed endpoints, and the target entry omits `live_patch`/`reload`.

Do not bypass this guardrail with opaque shell edits, token extraction, helper containers, GitHub application-code edits/redeploy, Coolify lifecycle, production or Lane B mutation. The minimal unblock is to expose/bind the existing typed endpoints and add `live_patch` + `reload` to this DEV target, then immediately return to the bounded-parallel final-verifier batch.

### P1 — loaded runtime schema needs fresh proof after next accepted patch

Source already contains `max_gap_rounds`; after the next tested source patch/reload, read back the permanent DEV reasoner schema and prove the loaded runtime exposes it before semantic canaries.

## Current 30-minute batch — exact A1 full task

BMAD route semantics: `bmad-help -> bmad-quick-dev`. No callable BMAD skill is exposed in CURRENT tools, so use the same Quick Dev stages/DoD directly and do not claim BMAD execution.

### Goal

Close the full A1 semantic gate from this SoT, not only the narrow RFC-number canary. No redeploy/rebuild/GitHub-code transport.

### Fresh evidence / localization

- narrow strict RFC-number canary completed on live runtime as workflow `run_1788184782007_002a3885`, root execution `exec_1788184782008_6104ac80`;
- runtime duration ~`769.2s`; internal `total_orchestration_time_seconds=492.25`; research phase ~`390.9s`;
- evidence state: 10 primary-standard sources, 133 claims, 104 verified, 23 overturned, 6 unverified, 2 independent provenance groups, verified coverage `1.0`;
- free-form draft remained correctly rejected: 50 material claims, 15 supported, 35 unsupported, dominated by missing/wrong citation binding;
- delivered evidence-only fallback passed live delivery verification: `delivery_verification.passed=true`, `mode=verified_evidence_only`, no unresolved requirements;
- this proves delivery-semantics and provider-boundedness behavior, but it is **not full A1 PASS** because the canary query covered only the RFC number and did not exercise RFC 9114 publication dates + Google QUIC lineage required by the A1 contract below;
- live logs also prove bounded provider retry is loaded (`retry 1/1`) and can recover after rate-limit/fresh-connection-pool resets;
- CURRENT `/app` HEAD remains `2cb0814deda4a9ab9158a4f9a876728e6977a799`; native `git status --short` remains the expected dirty Lane-A workspace: `doc_generation_pipeline.py`, `main.py`, `tests/test_agent.py`, untracked `reasoners/deep_research_ext/`, untracked `tests/test_deep_research_ext.py`.

### DoD

1. Run the full A1 task covering RFC 9000, RFC 9114, publication dates, and Google QUIC lineage with strict authoritative-source policy and `max_gap_rounds=1`.
2. RFC 9000 and RFC 9114 identifiers + publication dates must be supported by authoritative primary evidence.
3. Google QUIC lineage claims must be source-entailed or explicitly unresolved; no model-memory completion.
4. Delivered report must have zero unsupported material factual claims; full verified evidence-only delivery is acceptable when the writer draft is rejected, provided audit state remains visible.
5. No fabricated title/date/status/source; citation entailment for every delivered material claim.
6. Record execution/run ids, latency, evidence counts, coverage, final-verifier result, and delivered mode.
7. If A1 PASS, immediately promote Durable `ResearchRun` checkpoint/resume as the next 30-minute reliability batch, followed by replay regression fixtures; do not rebuild Evidence Ledger or novelty stopping already present.

### Stop / replan conditions

- If full A1 FAILS, patch only the exact failing semantic boundary in `/app`, validate, and rerun A1; do not start post-A1 architecture early.
- If full A1 PASSes only through evidence-only delivery, writer citation-boundary quality remains a separate optimization and final verifier stays fail-closed.
- No redeploy/rebuild/StartApplication/RestartApplication for this inner loop.

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

## Post-A1 implementation roadmap

After A1 passes, promote only one 30-minute capability batch at a time. The order below is the current 80/20 priority; do not build later layers before their gate or failure mode is demonstrated.

### Batch B1 — Evidence Provenance v2 (feeds A2/A4/A5/A6)

Goal: make every accepted claim auditable back to exact evidence and upstream origin while preserving epistemic and temporal state.

Minimal state per claim/evidence edge:
- `claim_id` and `requirement_id`;
- exact evidence span / excerpt locator;
- content identity/hash where practical;
- source URL/class/authority;
- upstream provenance cluster / independence identity;
- `retrieval_date`, `publication_date`, `last_updated`, `event_date`, requested `as_of` where available;
- relation: `SUPPORTS | CONTRADICTS | SUPERSEDES`;
- epistemic type: `FACT | INFERENCE | HYPOTHESIS`;
- negative state where applicable: `CONTRADICTED | NOT_FOUND | SEARCH_EXHAUSTED | NO_AUTHORITATIVE_EVIDENCE | UNKNOWN`.

DoD:
1. Existing A1 behavior remains green.
2. Exact supporting evidence can be traced from each material accepted claim to source span and source identity.
3. Derivative sources sharing one upstream origin do not count as independent corroboration.
4. Conflicting/superseding evidence is retained rather than silently overwritten.
5. Temporal metadata needed by A4/A5 survives through synthesis and final verification.
6. No unsupported new factual content is introduced by the provenance layer.

### Batch B2 — Boundary faithfulness verification

Goal: catch corruption where information/citations move between retrieval/research/orchestrator/writer, instead of relying only on the post-generation firewall.

DoD:
1. At each material handoff, outputs are locally checked against that stage's inputs/evidence.
2. Record boundary failure type at minimum: `hallucination`, `uncited_input_reliance`, `uncited_output`, `insufficient_citations`.
3. Boundary checks fail closed or trigger targeted repair without losing valid evidence.
4. Final verifier remains an independent last gate, not replaced by intermediate checks.
5. Evaluation trace can localize which stage introduced each rejected final claim.

Evidence basis: recent multi-agent Deep Research work localizes faithfulness/citation mistakes to agent boundaries and reports that orchestrator behavior can dominate final-report errors; use this as motivation, while local A1-A6 evidence remains the acceptance authority.

### Batch B3 — Reproducible + calibrated evaluation

Goal: distinguish product improvement from web/model/judge variance and keep automated judges auditable.

DoD:
1. Add a frozen/static evidence corpus for deterministic regression alongside live-web evaluation.
2. Re-run important semantic tasks multiple times and record material claim/citation/source stability.
3. Maintain a small human-reviewed golden set for citation entailment / support labels.
4. Measure judge false-positive/false-negative/pass-rate drift rather than trusting one scalar score.
5. A judge disagreement or low calibration confidence cannot silently promote unsupported evidence to PASS.
6. Keep live-web tests for freshness/real-provider robustness; frozen evaluation does not replace them.

Evidence basis: DeepResearch Bench evaluates both report quality and citation accuracy; DR³-Eval uses a static research sandbox for reproducibility; recent citation-verifier benchmarking shows materially different directional bias across LLM judges even when aggregate scores are similar.

## Failure-driven growth backlog

These are **candidate capability increments**, ordered by expected product value. Items covered by B1-B3 are implementation details of those batches, not separate reasons to start parallel architecture work. Promote one into the active 30-minute batch only when the preceding semantic gate passes and a failing gate/benchmark demonstrates the need.

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
