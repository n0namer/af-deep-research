---
title: AF Deep Research native AgentField multidomain E2E evidence
date: 2026-10-20
gate: TECHNICAL_GREEN_QUALITY_BLOCKED
git_base_sha: e10580c89eac7a4f6efb50c921ae9107ce8ad8dc
---

# Frozen native benchmark — evidence and acceptance

- Native submission: POST /api/v1/execute/async/meta_deep_research.execute_verified_deep_research.
- Result re-read: GET /api/v1/executions/{execution_id}, saved as 12 separate JSON receipts.
- Inference: OpenCodex gpt-6-luna via Responses API.
- Frozen cases: 12 topics, including two negative unknown/fabricated standards questions.
- Scope: research_focus=1, research_scope=1, max_research_loops=1, max_gap_rounds=0, max concurrent=3. Test launcher MAX_ARTICLES_PER_TASK=1, so this is smoke-scale, not full multi-source Deep Research.
- Technical E2E GREEN: 12/12 succeeded with 12/12 independent second server readbacks.
- Quality BLOCKED: 5/12 conservative quality screen PASS; 4/12 full verified requirement coverage; 9/12 reports cite a domain matching a prespecified primary-source domain.
- Negative cases include language signalling unknown/non-verifiability (heuristic screening only).
- Ordinary baseline: 12/12 search OK and 11/12 retrieved an expected official domain in top-ten sources. This does not establish report-quality superiority or matched cost.
- Temporary Docker Desktop relay bridges AgentField container to Windows Deep Research. It is not a durable production configuration.
- Costs: authoritative token billing and total per-task spend not established.
- Independent sentence-level citation entailment review and blinded judgement not completed; no crew-sync SERVER_DONE.
- Dirty shared tree: this record does not claim a clean integration commit; baseline git SHA above.
- Benchmark test SHA256: e2467d837cfaeaa9657160d5bdd3649c569f81655ea58f90e88e35a86915663f
- Frozen fixture SHA256: 299d25239aada77bc31ec33d4af23eb2fef9546df91b055f4a1e00b5b42980b4

## Remaining blocking gaps, ordered

1. Fix source-bound verification and final confident publication when verified coverage is zero; do not suppress failures or weaken fail-closed checks.
2. Stratified follow-up with 3+ independent source articles, blind citation-fact entailment review, and negatives; compare like-for-like evidence budgets.
3. Replace the temporary relay with supported network topology, prove restart/replay safely, then independent QA.
4. Add authoritative inference + search billing usage to compute spend per accepted and useful answer.

## Case details and receipts

# AF Deep Research — Native AgentField Multidomain Benchmark

Frozen corpus: 12 cases, breadth across standards/science/law/health/history and 2 unanswerable negatives.
Execution path: AgentField REST /execute/async/meta_deep_research.execute_verified_deep_research → OpenCodex gpt-6-luna.

**Completed:** 12/12; **succeeded:** 12; **technical pass:** 12; **strict quality screen:** 5.
**Primary-source cited:** 9 cases; **fully verified requirements:** 4 cases; **baseline ordinary search primary source found:** 11 cases.
Mean latency: 378.0 s; median: 379.02 s. Token billing: unavailable.

| Case | Status | Technical | Quality screen | Lexical anchor | Primary source | Verified coverage | Sec |
|---|---|---|---|---|---|---|---|
| net-http3 | succeeded | yes | no | 1.0 | no | 0 | 308.07 |
| net-quic | succeeded | yes | yes | 1.0 | yes | 1 | 467.95 |
| security-aes | succeeded | yes | yes | 1.0 | yes | 1 | 397.83 |
| space-apollo11 | succeeded | yes | no | 1.0 | yes | 1 | 384.3 |
| law-gdpr | succeeded | yes | no | 1.0 | yes | 0 | 366.59 |
| python-pep703 | succeeded | yes | no | 1.0 | yes | 0 | 338.9 |
| climate-ipcc | succeeded | yes | no | 1.0 | yes | 0 | 345.04 |
| geology-valdivia | succeeded | yes | yes | 1.0 | yes | 1 | 370.28 |
| health-malaria | succeeded | yes | no | 1.0 | yes | 0 | 383.89 |
| astronomy-pluto | succeeded | yes | no | 1.0 | no | 0 | 413.78 |
| negative-future-nobel | succeeded | yes | yes | — | no | 0 | 385.27 |
| negative-fake-rfc | succeeded | yes | yes | — | yes | 0.6667 | 374.15 |

## Quality screening failures

- **net-http3**: missing_primary_source, insufficient_verified_coverage; execution \`exec_20261019_205808_sxnp1rt1\`.
- **space-apollo11**: explicit_answer_incomplete; execution \`exec_20261019_210317_kzbxfsas\`.
- **law-gdpr**: insufficient_verified_coverage; execution \`exec_20261019_210449_qbafpw7p\`.
- **python-pep703**: insufficient_verified_coverage; execution \`exec_20261019_210558_mz9hurcs\`.
- **climate-ipcc**: insufficient_verified_coverage; execution \`exec_20261019_210942_qserp01c\`.
- **health-malaria**: insufficient_verified_coverage; execution \`exec_20261019_211139_x1e0cp60\`.
- **astronomy-pluto**: missing_primary_source, insufficient_verified_coverage; execution \`exec_20261019_211528_2wwyqux8\`.

## Interpretation

The strict quality screen is an intentionally conservative heuristic; source-domain match and lexical anchors are not a substitute for independent statement-level citation entailment review.

All receipts are preserved under the sibling files of this report. Do not mark CrewSync DONE solely from a native succeeded status.
