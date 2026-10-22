# BaseFive Source-Bound Reducer — 2026-10-14

Status: CANDIDATE / UNACCEPTED

## Authority and scope

- Task: `af-deep-research:v2-basefive-sourcebound-release-reducer-20261014-r4`
- Attempt: `attempt-0f80d4aa-9bef-4f23-b1da-d823a4d3f058`
- Session: `manual-20261014-basefive-northstar-hyper-r4-af--e4c991deb6179c00`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Source baseline Git SHA: `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc` (coordinator-supplied immutable task context; not recomputed in this read-restricted lane).
- Authorized write: this reducer report only.
- Acceptance authority: independent verifier/reviewer, reducer coordinator, and authoritative CrewSync terminal readback.

This report is a source-bound reduction receipt. It does not mutate production code, tests, live tasks, leases, locks, provider state, or CrewSync authority. It does not make a live-provider quality claim and cannot promote a candidate to `ACCEPTED`, `GREEN`, or `ACCEPTED_GREEN`.

## BMad state and bounded decision

BMad Help resolved `af-deep-research` as the target project and identified the existing acceptance documents as the available source of truth for this reducer lane. The requested reducer artifact did not exist in the exact authorized write scope, so this file is created as the missing bounded artifact. Quick Dev is the applicable implementation route; systematic debugging applies to the recorded runner failure; verification-before-completion requires preserving the absence of fresh executable runtime output.

**Decision: BLOCKED for product acceptance; remain CANDIDATE / UNACCEPTED.**

The permitted evidence supports a source-bound interface map and executable assertion descriptions, but it does not prove the native C4 ReleaseGate 19/19 suite, native frozen E2E, independent QA, or a live-provider benchmark. Missing runtime evidence is not converted into `PASS`.

## D1 — Source-bound interface and identity map

The following existing public interface signatures are quoted from `docs/acceptance/longbundle-holdout-truth-20261014.md`, whose source-bound implementation identities are recorded below. They are the contract surface consumed by the frozen evaluation/restart gate; no replacement interface is introduced here.

```text
ResearchRunStore(root=None)

begin_research_run(
  query,
  *,
  store=None,
  source_revision=None
) -> (ResearchRunStore, ResearchRun)

checkpoint_research_run(
  store,
  run,
  *,
  stage,
  status=None,
  source_revision=None,
  expected_checkpoint_seq=None,
  source_ids=None,
  evidence_summary=None,
  coverage_state=None,
  open_gap_ids=None,
  conflicts=None,
  budgets=None,
  payload=None
) -> ResearchRun

resume_research_run(
  store,
  run_id,
  *,
  source_revision=None
) -> (ResearchRun, dict)

replay_frozen_fixture(fixture, corpus)
  -> replay result with gate, observation, and used source IDs

remove_all_admissible_evidence(corpus)
mutate_corpus_remove_documents(corpus, document_ids)
evaluate_stored_semantic_snapshot(fixture, snapshot)
```

Source identity recorded by the permitted holdout artifact:

- `evaluation.py`: `0399e49ab5e5867f57c2731fa68b94b6fca35282ddb0c64c7baa098fc03f2f6d`
- `research_run.py`: `338ed08b70260969a7e73e30df0939df1d039bf3599aa4e6ab993b32457350fb`
- Project baseline Git SHA: `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`

**Boundary:** the permitted read scope contains no C4-specific DTO declaration, version manifest, producer publication, or independent-QA publication. Therefore DTO compatibility and the exact C4 version cannot be asserted from this lane.

## D2 — Reproduction matrix

The following assertions are source-bound descriptions from the holdout acceptance artifact. They are not fresh execution receipts in this reducer attempt.

| Assertion | Expected behavior | Evidence status |
| --- | --- | --- |
| Positive frozen baseline | All 24 frozen-core fixtures and six distinct holdout fixtures replay to passing baselines. | `DESCRIBED; runtime BLOCKED` |
| Negative: remove all holdout evidence | Every holdout gate fails after admissible evidence is removed. | `DESCRIBED; runtime BLOCKED` |
| Negative: remove decisive source | `DR-H02` fails closed and marks `R1` unresolved when its decisive admissible source is removed. | `DESCRIBED; runtime BLOCKED` |
| Adversarial missing signal | `DR-H04` becomes `EVIDENCE_MISSING` when `prompt_injection_success` is absent. | `DESCRIBED; runtime BLOCKED` |
| Restart and fencing | Checkpoint reload preserves the deduplicated provider call ID; stale checkpoint sequence and stale source revision are rejected. | `DESCRIBED; runtime BLOCKED` |

These satisfy the required assertion shapes at the evidence-description level: one positive, at least two negatives, and restart/fencing. They do not satisfy executable proof because the authorized runner was unavailable in the recorded upstream lanes and no executable test target is authorized in this Markdown-only write scope.

## D3 — Reduction and release-gate matrix

| Gate | Status | Source-bound reason |
| --- | --- | --- |
| C4 DTO/interface signature | `BLOCKED` | Existing evidence exposes the research-run interface above, but no C4 DTO/version source is in read scope. |
| Frozen positive baseline | `BLOCKED` | Positive cases are documented, but no fresh native command output is available. |
| Two adversarial negatives | `BLOCKED` | Evidence-removal and missing-signal cases are documented, but not freshly executed here. |
| Restart / stale-state fencing | `BLOCKED` | Restart and fencing assertions are documented, but not freshly executed here. |
| 19/19 post-repair fact-ID suite | `BLOCKED` | No authorized receipt establishes 19/19 post-repair results. The long-bundle evidence records five focused assertions and a Python environment blocker, not a 19/19 C4 result. |
| Native frozen E2E task-to-result path | `BLOCKED` | No native C4 producer/consumer E2E output, task identity, or terminal readback is present in the permitted evidence. |
| Independent QA | `BLOCKED` | No independent-QA publication or artifact SHA is present in the permitted evidence. |
| Live-provider benchmark | `UNPROVEN` | The supplied artifacts explicitly distinguish source-bound replay from real-provider quality; no provider benchmark is authorized or evidenced. |
| Product release acceptance | `FAIL` | Required C4 DTO/version, native E2E, 19/19 runtime, independent QA, and terminal readback evidence are missing. Treating the candidate as release-ready would be unsupported. |

## D4 — Test and infrastructure receipts

No executable test file is authorized in this attempt's `write_scope` or supplied `test_scope`; the only authorized target is this Markdown reducer receipt. Running unrelated Node/Vitest/tsx tests would not prove the C4 reducer decision.

Recorded upstream focused runner receipt from the permitted acceptance evidence:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
exit_code=null
stderr="A regular local .venv Python executable is required."
```

Recorded affected regression receipt from the permitted fact/source lane:

```text
status=BLOCKED
code=test_outside_task_write_scope
engine=project test runner
file=tests/test_northstar_factid_source_identity_20261013.py
```

Reducer-lane execution status:

```text
status=SKIP
reason=No authorized executable target exists for the Markdown-only write scope; unrelated tests would not establish the C4 gate.
```

The identical Python dependency blocker is not retried. No unrun check is reported as `PASS`, and no native focused exit code is invented.

## D5 — Adversarial self-review and handoff

- The report binds its claims to the coordinator-supplied Git SHA and the exact source/test identities recorded by the permitted acceptance artifacts.
- The report distinguishes recorded interface descriptions from freshly executed runtime evidence.
- Positive, evidence-removal, decisive-source-removal, adversarial-missing-signal, restart, and fencing behaviors are listed without promoting descriptions to test passes.
- No C4 DTO version or compatibility claim is made without readable source evidence.
- The 19/19 suite, native frozen E2E, independent QA, and provider benchmark remain explicitly unproven or blocked.
- Infrastructure failures are preserved verbatim and are not repaired by changing expectations or fabricating exit codes.
- Only the authorized Markdown file is changed; producer source, tests, live task state, leases, locks, and external providers remain untouched.
- The artifact remains `CANDIDATE / UNACCEPTED`; independent review and authoritative terminal readback remain mandatory.

## Required next action

Provide the exact C4 producer and independent-QA receipts, DTO/interface source identities and versions, native frozen task-to-result failure/restart output, and current-SHA 19/19 fact-ID results to the reducer coordinator. Then run the native focused and affected regression commands in an environment with the required regular local `.venv`, bind exit codes and counts to immutable source/test SHAs, perform independent QA, and obtain authoritative CrewSync terminal readback before any acceptance decision.
