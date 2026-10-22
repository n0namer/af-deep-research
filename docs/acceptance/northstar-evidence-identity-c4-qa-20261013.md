# North Star Evidence Identity C4 QA — 2026-10-13

Status: CANDIDATE / UNACCEPTED

## Authority

- Task: `af-deep-research:v2-c4-native-acceptance-evidence-identity-20261013-r1`
- Attempt: `attempt-372efc4b-4ae3-4966-9b5f-467f0180a3ff`
- Session: `manual-20261013-c4-native-acceptance-frontier-r-27fab3677fd2c14e`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Production source remains read-only in this lane.
- Independent verifier/reviewer and authoritative CrewSync readback retain acceptance authority.

## Source identities

| Input | SHA-256 | Provenance |
| --- | --- | --- |
| `reasoners/deep_research_ext/verification_bridge.py` | `aad1f5c7a85b26a0c7a3449e9b12df5b276f8b50c264e18688195326f12db270` | Fresh scoped ranged read. |
| `tests/test_northstar_factid_source_identity_20261013.py` | `f4b7b8df6f431b1def739a29fd0766d9cfb27f5e9d16821de2654c1f2983e44e` | Authorized test runner source-identity receipt. |
| Git source state | `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc` | Coordinator-supplied prelaunch identity; not independently recomputed in this read-restricted lane. |
| Active BMad artifact | `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md` | Trusted SHA-256 `e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce`; current C4 acceptance frontier. |

## C4 component and DTO boundary

The exercised production entry point is:

```text
verify_ledger_claims(*, ledger, research_package, source_strictness,
                     model=None, api_key=None, ai_call=None,
                     adjudicator=adjudicate_evidence_ai) -> EvidenceLedger
```

Observed boundary from source:

1. `EvidenceLedger.sources` supplies `source_id`, `url`, and `content_hash`.
2. `research_package.source_articles` is eligible only when its numeric `id`, URL, and content hash match one ledger source and its URL is not reused.
3. Each eligible claim becomes `FactForAdjudication(fact_id=claim.claim_id, source_id=claim.source_id, content, source_text, source classification)`.
4. The adjudicator returns an `AIAssessmentList`; the bridge consumes assessment `fact_id`, allow/verify/support booleans, and disagreement score.
5. The bridge indexes returned assessments only by `fact_id` and updates matching claims through `model_copy`.
6. The returned assessment identity is not checked against `source_id`, URL, content hash, or an immutable evidence token. Duplicate returned assessments with the same valid `fact_id` collapse through last-write-wins dictionary construction.

The focused tests call the real `verify_ledger_claims` function. The adjudicator is the documented dependency seam. Small immutable classes are explicitly named `*DtoDouble`; they represent only the attributes the production function reads and are not described as live DTOs or live-provider execution.

## Focused test design

File: `tests/test_northstar_factid_source_identity_20261013.py`

| Scenario | Required invariant | Runtime status |
| --- | --- | --- |
| Native positive path | The emitted fact retains exact claim `fact_id`, ledger `source_id`, claim text, and eligible source text; a matching assessment updates only that claim without changing its sentence. | `BLOCKED` before collection. |
| Foreign fact and empty injected citation IDs | Assessments whose IDs are absent from the emitted batch must not credit the native claim. | `BLOCKED` before collection. |
| Stale/restart source package | A content-hash mismatch under `verified-only` must abstain before invoking adjudication and leave the ledger unchanged. | `BLOCKED` before collection. |
| Crash then restart/retry | An adjudicator exception must not credit the failed attempt; a later clean invocation may evaluate the original immutable ledger. | `BLOCKED` before collection. |
| Same `fact_id`, wrong `source_id` | A returned assessment bound to a foreign source identity must not credit the claim. | `BLOCKED`; source inspection predicts failure because returned `source_id` is ignored. |
| Duplicate same-ID injection | Conflicting duplicate assessments for one valid `fact_id` must cause abstention instead of last-write-wins credit. | `BLOCKED`; source inspection predicts failure because `by_id` silently overwrites duplicates. |

No test is labelled live. No provider, shared service, Ruflo Native state, CrewSync claim, lease, lock, or terminal state is contacted or mutated.

## Actual validation receipt

Requested focused command:

```text
python -m pytest -q tests/test_northstar_factid_source_identity_20261013.py
```

Authorized runner response:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
exit_code=null
source_identity_sha256=f4b7b8df6f431b1def739a29fd0766d9cfb27f5e9d16821de2654c1f2983e44e
stdout=""
stderr="A regular local .venv Python executable is required."
```

The identical command was not retried. No `PASS` is reported. No affected Python regression file was authorized in this task's `write_scope` or `test_scope`, and running an unrelated Node/Vitest/tsx target would not validate this Python boundary.

## Root-cause assessment

### Source-backed facts

- Eligibility before adjudication is bound to ledger source ID plus exact URL and content hash.
- Emitted adjudication facts carry both `fact_id` and `source_id`.
- Returned assessments are selected only by `fact_id`.
- `invalid_ids` detects empty or foreign IDs, but it does not detect duplicate valid IDs.
- The dictionary comprehension keeps the last assessment for a duplicated valid ID.
- Adjudicator exceptions are collected and excluded, leaving affected claims unchanged.

### Product defects to verify under the production owner

1. **Assessment source identity is not enforceable at the bridge boundary.** A correct repair requires the production assessment DTO/result contract to return an identity that can be compared with the emitted fact's `source_id` or a stronger immutable evidence token, followed by strict abstention on mismatch.
2. **Duplicate valid assessment IDs are ambiguous but currently credited.** A correct repair must reject or abstain for every duplicated valid `fact_id`; choosing the first or last result still allows injected or replayed output to win.

These are source-review findings, not runtime-confirmed failures, because pytest did not start. The focused tests intentionally encode the strict-abstention behavior required by this task so the production owner can reproduce red/green evidence.

## Fixture-versus-production distinction

- The positive, foreign-ID, stale-source, and crash/retry tests exercise behavior directly visible in the read-only function and use no hidden fixture state.
- If collection fails because an imported production dependency is unavailable, that is an environment or repository test-bootstrap defect, not proof that the identity assertions are wrong.
- If the two identity-injection assertions fail after successful collection, the failure is production-contract behavior: the bridge has no returned source binding and silently overwrites duplicate valid IDs.
- If the actual `AIAssessmentList` DTO forbids a returned source identity, that confirms the boundary deficiency rather than making the source-swap invariant unnecessary; the DTO and bridge must be repaired together by their production owner.

## Root-cause-only repair route

The current lane owns only the new test and this evidence report. `reasoners/deep_research_ext/verification_bridge.py` is explicitly read-only.

The active C4 frontier states that the exact original C4 producer task/result identity is absent from the authorized evidence and must not be invented. Therefore the coordinator must route a sticky repair to the existing original owner of the C4 verification bridge plus adjudication DTO boundary, preserving its task identity and write scope. That owner should:

1. run this focused test in a regular local `.venv`;
2. preserve the positive, foreign-ID, stale-source, and crash/retry behavior;
3. bind returned assessments to source/evidence identity;
4. reject duplicate valid `fact_id` results atomically;
5. rerun this focused file and the affected verification-bridge regression suite;
6. publish exact source/test hashes, command, exit code, test counts, and independent QA evidence.

No replacement CrewSync task is created here, and no unknown task identifier is fabricated.

## Edge-case self-review

Unhandled production paths found within the reviewed function boundary:

- A returned assessment repeats a valid `fact_id` with conflicting verdicts.
- A returned assessment repeats a valid `fact_id` while representing another source.
- Two eligible claims share the same `claim_id`; one assessment can update both claims.
- A source article ID cannot be converted with `int(...)`; eligibility raises before strict abstention.
- An adjudicator returns a malformed non-exception result without `.assessments`; flattening raises rather than preserving abstention.

Only the first two are asserted by this task's bounded acceptance goal. The remaining paths are recorded for the production owner's affected review and are not expanded into unrelated fixes here.

## Acceptance decision

**CANDIDATE / UNACCEPTED.**

- The actual native function boundary and exact source identity are recorded.
- The focused test file contains a native positive assertion and at least two adversarial negatives, including stale/restart and crash/retry behavior.
- The runner was infrastructure-blocked before collection, so no test is reported as passing or failing.
- Source inspection identifies two root-cause identity gaps requiring repair outside this task's write scope.
- Independent reviewer execution and authoritative CrewSync readback remain required before any GREEN conclusion.
