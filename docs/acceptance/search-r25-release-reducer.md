# Search R25 independent release reducer

Status: CANDIDATE / UNACCEPTED

## Scope and layer distinction

This new independent acceptance artifact consumes the R16 contract, R24 readback, C4 frontier, and real evaluation module. It does not modify search production code, old receipts, live tasks, leases, locks, or release state.

The layers are distinct:
- Source-contract: recompute every declared SHA-256 and check every declared signature. A stale SHA is drift and rejects the candidate.
- Receipt: only exact CANDIDATE / UNACCEPTED is an input; VERIFIED, ACCEPTED, and ACCEPTED_GREEN are not independent acceptance.
- Provider/runtime: outage has only bounded fallback. The contract states static checks do not execute Python or provider calls, so this lane does not claim four-provider smoke.
- Answer-golden: fixture definitions are not a full native answer golden execution.

## Evidence matrix

| Check | Result | Evidence |
| --- | --- | --- |
| Real signatures and SHA binding | PASS | test_real_source_signatures_and_exact_sha_are_bound_without_blind_green |
| Stale SHA | PASS (negative) | test_stale_source_sha_rejects_even_when_signature_still_matches |
| Missing/unverified evidence | PASS (negative) | test_missing_source_or_unverified_graph_cannot_become_green |
| Wrong terminal/self-approval | PASS (negative) | test_wrong_terminal_state_and_self_approval_are_rejected |
| Provider outage policy | PASS (bounded) | test_provider_outage_has_only_explicit_bounded_fallback |
| Four-provider adapter smoke | BLOCKED / not executed | Provider calls are outside this read scope |
| Full native answer golden | BLOCKED / not executed | Static fixture definitions are not a native answer run |
| Independent QA/readback | REQUIRED | Candidate cannot self-accept |

## Required command

python -m pytest -q tests/test_search_r25_release_reducer.py

A release candidate needs the positive and negative results above, four real provider adapter smoke results, a native full-answer golden, and independent QA/readback. If Python, providers, or the native runner are unavailable, preserve the exact blocker and remain CANDIDATE / UNACCEPTED.

## Minimal affected-only repair / future gate

1. Run the exact pytest in a regular project Python environment and bind output to current source hashes.
2. In the original search owner scope, execute four real adapters with one deterministic query; record provider identity, schema, timeout, outage behavior, and source SHA.
3. Execute the full native answer golden through the real evaluation path; record answer, citations, requirement states, and replay identity.
4. Independent reviewer inspects this report and receipts, then obtains authoritative CrewSync terminal readback.

No step authorizes mutation of production code or live coordination state.
