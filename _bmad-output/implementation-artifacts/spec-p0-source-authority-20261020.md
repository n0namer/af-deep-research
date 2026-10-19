---
status: in-review
route: build
title: P0 exact authority hostname recognition for source policy
source_task: af-deep-research:p0-full-regression-e2e-quality-benchmark-20261019
date: 2026-10-20
base_sha: e10580c89eac7a4f6efb50c921ae9107ce8ad8dc
gate: IMPLEMENTED_REGRESSION_GREEN_INDEPENDENT_QA_PENDING
---

# Scope / evidence

The real 12-case native AgentField Deep Research benchmark had 12/12 technical successes but only 5/12 conservative quality-screen passes. WHO, EUR-Lex, IPCC, IAU and Python PEP primary-source URLs were previously classified as `blog`; deceptive hostnames containing trusted strings were incorrectly promoted by substring-based checks. Existing `verified-only` already uses source-category admissibility and verified-coverage gating; do not build new orchestration or rewrite those guards.

## Implementation (one cohesive P0 bug)

- `doc_generation_pipeline.py::_classify_source`: extract URL hostname with `urllib.parse.urlsplit`; match explicit official domain and subdomain boundaries; reject misleading media and government substrings and malformed/non-HTTP URLs. Official provenance does not itself prove claim entailment.
- `tests/test_p0_source_authority_classifier_20261020.py`: positive official URLs, malformed/misleading-domain negatives, and previously admitted sources. No external calls or paid model usage.

## Given / When / Then acceptance

- Given a WHO, EUR-Lex, IPCC, IAU, Python PEP or RFC Editor URL, when classified, then it is an admitted `primary_doc` in verified-only mode.
- Given a malicious URL such as `who.int.attacker.example`, `reuters-blogs.example.net` or `fakenews.gov.evil.example`, when classified, then it is not promoted to any trusted source category.
- Given empty/non-HTTP URLs, when classified, then they fail closed as `blog`.
- Given the original official NASA, NIST, RFC and DOI examples, when classified, then they remain admissible.

## Tested status

- RED: 9 failures and 20 passes on clean baseline.
- GREEN: 29 passes on patch.
- Affected regression: 111 passed, 1 deselected. The deselected test hardcodes Linux-only `/app/main.py` and cannot run from Windows without the container-specific path; this is not evidence of product failure.
- `git diff --check`: PASS.
- No changes were made in the shared dirty worktree. No deployment, global container restart, CrewSync server DONE, or independent QA is claimed.

## Next P0 gates (not part of this bug)

Reconcile the isolated worktree commit with ongoing dirty dev branch changes via explicit conflict inspection; fix claim `fact_id -> source_id -> citation` proof when the verified coverage is zero; run multi-article live E2E under verified-only; independent QA of exact integrated SHA. Do not mark technical task SERVER_DONE based solely on successful tests.
