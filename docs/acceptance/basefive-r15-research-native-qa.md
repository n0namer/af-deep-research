# Basefive R15 Research Native Independent QA — 2026-10-14

Status: **BLOCKED / UNACCEPTED**. No runtime PASS or product acceptance is established.

## Authority and source of truth

- Task: `af-deep-research:v2-r15-independent-native-mvp-qa-20261014-r1`
- Attempt: `attempt-95603b3f-3efe-4c0a-a5b0-bea2eebe2de2`
- Session: `manual-20261014-basefive-r15-native-qa-af-deep--5a4ff357eb0bc8db`
- Target: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Existing BMad gate: `docs/acceptance/c4-releasegate-reducer-frontier-20261013.md` (independent QA/reduction; product acceptance blocked).
- Architecture input: `docs/architecture/basefive-r14-contracts.json` (static CANDIDATE/UNACCEPTED contracts, not a runtime receipt).
- Exclusive changes: this report and `tests/test_northstar_r15_independent_evidence_qa.py` only.
- No production changes, live task/lease mutation, external sends, commits, deploys, or independent acceptance were performed.

FACT: both authorized targets were absent on initial scoped reads (ENOENT). They were created through the authorized atomic writer. The native report mechanism already exists in the inspected production source; no replacement production implementation was added.

## Local Definition of Done and work sizing

Value: independent, reproducible evidence about the native frozen-source report boundary without overstating whole-pipeline or process-restart behavior.

Required proof: freshly bound source/test fingerprints; real native API signatures; a positive cited report with an explicit unresolved requirement; foreign-owner and stale-source negatives; interruption/replay assertions; affected regression evidence; honest independent reducer handoff. Full acceptance additionally requires native question-to-generated-report integration, stale ResearchRun checkpoint coverage, and actual process-crash persistence evidence.

Smallest compatible design: a new pytest module importing the actual native module, using an independent literal fixture/oracle, calling existing report APIs, and prohibiting socket connections. The fixture hashes frozen bulletin bytes independently with hashlib and checks fact_id/source_id/source_sha256 relationships and explicit cost abstention. No production helper is used to compute expected citations or answer text.

Useful-work estimate before implementation: investigation 4 minutes, tests 7, potential repair 4, review 3, evidence 3 (21 minutes total, excluding external coordination). The native runner blocked at the first validation boundary; no padding or indefinite retry was performed. Exact elapsed worker time is not exposed by the scoped tools and is not claimed.

## Source-bound evidence

| Input | SHA-256 | Evidence level |
| --- | --- | --- |
| `AGENTS.md` | `490bdf70833a3ca86788830ead5fb9f7d8e8f37a0446626d166f5ac5e2107d08` | Scoped reader receipt. |
| `reasoners/deep_research_ext/verified_pipeline.py` | `97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87` | Fresh scoped source-reader receipt, consistent with R14 contract. |
| `tests/test_northstar_r15_independent_evidence_qa.py` | `8c5434937b00cea96e7bd1e78e130a6dbff2d3ab18613151b223efc2efcdad94` | Scoped reader SHA equals blocked runner source_identity_sha256; 243 lines. |
| Existing C4 reducer frontier | `e776f4091b4e24a2091e97d08ea6f215fbe2b1ed548d1e13b5fed75fb09538ce` | Trusted prelaunch hash; artifact content read, not independently hashed in this lane. |
| Baseline Git | `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc` | Coordinator-supplied identity only, not independently queried. |
| Manifest | `d51c03f54025cef418104d7a0c90f38b3ea9bd46e6e7f2b8d723dd4c41329ffa` | Coordinator-supplied binding. |
| Project cache | `34e40fc5edc92343b4168f73c1828e65c7b75904ba2af97a4667e8945f17e94f` | Coordinator-supplied binding, not acceptance. |

FACT: these identities bind the inspected production file and final test file, not the complete dirty checkout. Branch, git status, complete dirty-tree snapshot, imported dependency fingerprints, and post-run source stability are unavailable through this exact scope. The test asserts the inspected code SHA at execution time, but that assertion has not executed. A whole-checkout identity must not be inferred from HEAD or the project cache.

## Real native C4/report-boundary API

The following signatures are present in production source, not invented substitutes:

```python
build_grounded_verified_report(*, report_id, query, source_revision, source_owner,
                              source_file_sha256, facts, payload,
                              abstained_requirement_ids=(), revision=1)
persist_grounded_verified_report(store, candidate, *, owner,
                                cancellation=None, effect_id=None)
resume_grounded_verified_report(store, report_id, *, owner, source_file_sha256)
```

DTO: `VerifiedSourceReport`, version `r10`; grounded fact fields: `fact_id`, `source_id`, `source_sha256`. Relevant anchors: builder around line 107, replay line 137, store line 197, grounded persistence line 247, resume line 273. The new test includes inspect.signature assertions and independently hashes source bytes. Runtime import/signature checks remain BLOCKED.

FACT: `DurableVerifiedSourceReportStore` stores reports/effects in dictionaries and a set under an RLock. It is not a disk-backed, restart-durable store despite its name. The inspected execute_verified_pipeline report path calls the legacy builder/persistence functions, not the grounded report API. Grounded DTO retention does not prove that the full pipeline generates grounded citations or automatically decides partial abstention.

## New independent scenarios

Static review identifies 14 intended pytest cases (including parameterized expansions); collection and execution counts are **unknown**, not 14 PASS.

| Scenario | Intended assertion | Runtime status |
| --- | --- | --- |
| Source and API binding | Exact production SHA, native source location, and three exact signatures. | BLOCKED |
| Frozen-source positive | Question, three-sensor answer, fact/source citation, source hash, r10 version, explicit cost abstention survive native persistence. | BLOCKED |
| Idempotent terminal effect | Repeated same report/effect changes nothing and effect_count remains one. | BLOCKED |
| Foreign writer | Owner mismatch rejects before report/effect creation. | BLOCKED |
| Resume owner/source drift (two cases) | Foreign owner and changed SHA reject without changing canonical report. | BLOCKED |
| Post-save interruption | Cancellation after native save leaves no effect; same-store resume/retry records one effect only. | BLOCKED |
| Pre-save cancellation | Neither report nor effect is created. | BLOCKED |
| Stale report revision | Older replay returns current revision; stale expected_revision and stale effect revision reject. | BLOCKED |
| Replay conflicts (three cases) | Same-revision payload conflict, skipped revision, and source identity drift reject without replacing canonical state. | BLOCKED |
| Payload isolation | Mutating input or a loaded nested payload does not alter stored report. | BLOCKED |
| New-adapter restart limitation | A fresh adapter cannot resume the original report; the original adapter retains it. | BLOCKED |

The oracle is written inside this new test file, independent of prior QA files. It checks retention of caller-supplied evidence/abstention, not semantic entailment performed by a generator. The interruption scenario is native cancellation with the same in-memory store, **not an OS crash or reconstructed durable process**. Stale report revision assertions are **not stale ResearchRun checkpoint_seq assertions**. The last negative test documents the known restart limitation; even if it passes, process durability would remain an unmet release gate.

## Actual validation receipt

Requested command:

```text
python -m pytest -q tests/test_northstar_r15_independent_evidence_qa.py
```

Actual tool: `go_wave.run_project_tests` with exact authorized file.

```json
{
  "status": "BLOCKED",
  "code": "PYTHON_VENV_UNAVAILABLE",
  "test": "tests/test_northstar_r15_independent_evidence_qa.py",
  "engine": "python:pytest",
  "source_identity_sha256": "8c5434937b00cea96e7bd1e78e130a6dbff2d3ab18613151b223efc2efcdad94",
  "exit_code": null,
  "signal": null,
  "error": null,
  "duration_limit_ms": 120000,
  "output_truncated": false,
  "stdout": "",
  "stderr": "A regular local .venv Python executable is required."
}
```

No collection, positive/negative assertion, import, or runtime signature check executed. No identical retry, Node surrogate, shell fallback, dependency installation, or weakened assertion was used. No product failure was diagnosed from this infrastructure receipt.

Affected baseline regression: **NOT RUN**. There is no authorized baseline test in this task's read/test scope, and the shared Python runner is blocked. The existing C4 artifact names prior Base20 commands, but those names do not authorize executing or modifying their files in this attempt. Coordinator must supply an exact affected baseline test_scope for resumption.

## Acceptance matrix

| Gate | Decision |
| --- | --- |
| D1 exact source/test identities | PARTIAL: fresh file-level identities; whole dirty-checkout/dependency identity and runtime signature proof missing. |
| D2 positive, negatives, restart | BLOCKED: written assertions have not run; real process crash and ResearchRun checkpoint sequence gates remain uncovered. |
| D3 independent new oracle | Implemented, statically reviewed; runtime verification BLOCKED. |
| D4 native focused and baseline | INFRA BLOCKED for focused pytest; baseline not authorized/not run. |
| D5 typed QA/reducer handoff | This report supports BLOCKED/UNACCEPTED publication only, not CANDIDATE or acceptance. |
| Product C4/native MVP acceptance | BLOCKED: no positive runtime evidence, full native integration, durable restart proof, or authoritative terminal readback. |

## Self-review and workflow limitations

- Scope review: only the two permitted new files were written; the production mechanisms were reused unchanged.
- Assertions target the real module, not AST-extracted replacements or mocked implementations of the APIs under test.
- Fixture source hash is distinct from the production-code SHA; both serve explicit different identities.
- Network connection guards are included, but their execution is unverified because pytest did not start.
- No invalid pytest result is described as PASS. No report-store restart is generalized to process durability.
- BMad Help was loaded first; target remains af-deep-research, not canonical BMAD-MNNZ. Quick Dev clarification/one-shot references and Superpowers verification were consulted.
- BMad customization/config scripts, out-of-scope sprint/spec writes, git inspection, editor launch, commits, and review subagents are unavailable or prohibited. Those method steps were not executed and no complete canonical workflow is claimed. No competing PLAN/spec/tracker was created.
- Graph/Graft tools are not exposed in the permitted tool surface. Exact permitted source reads were used; no graph coverage claim is made.
- Independent reviewer/reducer and coordinator retain all acceptance, task administration, and terminal readback authority.

## Same-owner recovery and reducer handoff

1. Coordinator provisions a regular local `.venv` Python executable and required project test dependencies without broadening this worker's permissions. Resume this exact task/attempt context, not a duplicate implementation.
2. Rerun the exact focused command against test SHA `8c5434937b00cea96e7bd1e78e130a6dbff2d3ab18613151b223efc2efcdad94` and inspected source SHA `97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87`; investigate drift before using the receipt. Repair only scoped test defects, retest, and preserve actual exit/count/output.
3. Coordinator supplies authorized affected-baseline tests plus source/evidence needed for real ResearchRun sequence fencing, full native generated-report integration, and OS/process crash durability. Those are distinct missing gates, not proved by this report API slice.
4. Any necessary durable-store or pipeline integration repair belongs to a properly authorized production owner; this lane must not edit production source.
5. Independent reducer consumes fresh source-bound runtime evidence and original producer/QA receipts, then coordinator obtains authoritative terminal readback. This worker never self-accepts.

## Single publication receipt

The single `go_wave.publish_worker_result` call returned **INVALID_REPORT**, not VERIFIED/PENDING_SYNC/CONFLICT. The typed report used the known local date `2026-10-14` for recorded_at; the publisher requires a full ISO timestamp. No valid result publication or transport verification occurred, and no second call was made.

```json
{
  "status": "INVALID_REPORT",
  "note_ref": {
    "scope": "go-core.worker-result.v1",
    "key": "af-deep-research:v2-r15-independent-native-mvp-qa-20261014-r1:attempt:attempt-95603b3f-3efe-4c0a-a5b0-bea2eebe2de2"
  },
  "questions": [{"question": "recorded_at: must be an ISO timestamp"}]
}
```

The attempted report referenced this document's pre-receipt SHA `f553d69a9623b33a17cae27bcd5cc86b087e1e20bc6474683fd9a696a3ef10e7`; this receipt append changes the document identity. Preserve the existing tests and infrastructure evidence. Per the publication-failure protocol, coordinator must arrange a new sticky attempt for a valid typed result with an actual full ISO timestamp; do not claim publication success or repeat implementation. Product verification remains independently blocked by the Python runner and missing gates.

## Sticky recovery evidence — 2026-10-15 (current attempt)

This section records the current attempt; preceding identities and receipts remain historical, not current validation. Current status: **INFRA BLOCKED / UNACCEPTED**.

- Task: `af-deep-research:v2-r15-independent-native-mvp-qa-20261014-r1`
- Attempt: `attempt-0b236a6a-4440-45ab-99eb-09b68cf8b7df`
- Session: `manual-20261015-basefive-goal20-af-deep-researc-440555c3fcbb321f`
- Trusted manifest SHA-256: `4ffd5b5bff18f4ba08df03978aefcd83e9f993a52de71da11542eed985c1e50f`
- Trusted project-cache SHA-256: `068492a1ad76fd3767e53d63c33e50bac0bf11022555d179a849dcd9744e7eb3`
- Trusted baseline commit: `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`; branch/dirty checkout not independently queried.

FACT: the authorized test and report already existed at entry. This attempt reused them rather than implementing a duplicate candidate. BMad Help was loaded first; the declared target is af-deep-research and the existing C4 frontier remains the governing independent QA/reduction gate. Verification-before-completion was consulted. No new production implementation or test repair is justified by an unavailable interpreter.

Local DoD: validate the existing literal frozen-source oracle against the real grounded APIs; retain positive citation/partial-abstention, foreign-owner/stale-source, cancellation/replay and stale-report assertions; bind source/test bytes to fresh receipts; run affected authorized regressions; preserve missing integration/checkpoint/crash gates; publish one typed UNACCEPTED result. This DoD is **not met** because the native test engine did not start. Estimated useful recovery work before the fresh runner check: 5–10 minutes for inspection, one runner check, self-review and evidence; implementation/repair contingent on executable failures. Repeating prior implementation or adding unexecutable tests would not resolve this blocker. Elapsed runtime is not exposed and is not claimed.

### Fresh native validation receipt

Requested command: `python -m pytest -q tests/test_northstar_r15_independent_evidence_qa.py`.
Actual authorized tool: `go_wave.run_project_tests`, called once in this attempt with that exact file.

```json
{
  "status": "BLOCKED",
  "code": "PYTHON_VENV_UNAVAILABLE",
  "test": "tests/test_northstar_r15_independent_evidence_qa.py",
  "engine": "python:pytest",
  "source_identity_sha256": "8c5434937b00cea96e7bd1e78e130a6dbff2d3ab18613151b223efc2efcdad94",
  "exit_code": null,
  "signal": null,
  "error": null,
  "duration_limit_ms": 120000,
  "output_truncated": false,
  "stdout": "",
  "stderr": "A regular local .venv Python executable is required."
}
```

FACT: no collection or test assertions executed. There is no exit code, PASS count, red/green repair cycle or runtime C4 signature verification. No identical retry, alternate runner, shell, dependency installation or unauthorized external send was attempted.

### Current source binding and bounded review

- Fresh scoped source receipt: `reasoners/deep_research_ext/verified_pipeline.py`, SHA-256 `97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87`; matches R14 contracts and the test's independent byte-hash assertion.
- Fresh runner test receipt: SHA-256 `8c5434937b00cea96e7bd1e78e130a6dbff2d3ab18613151b223efc2efcdad94`; existing test content was reviewed and left unchanged.
- Source inspection confirms the three grounded API signatures recorded above and DTO `r10`. These are report-boundary interfaces, not evidence of a distinct C4 ReleaseGate API or native orchestration task-to-result acceptance.
- The oracle's expected answer and abstention are literal fixture expectations, not generated by a production validator. The report itself is supplied by the test; this is not question-to-generated-answer integration.
- Foreign-owner rejection, stale source/report revision, cancellation after save and duplicate-effect checks are present. ResearchRun checkpoint sequence fencing is a separate contract and is not proved by stale report revision tests.
- A fresh store loses state; retained-store cancellation/replay is not OS-process restart durability. The existing negative test honestly exposes that boundary.
- Network guards are present but unexecuted. No production writes, live Native/CrewSync mutations, claims, agents, commits, deployment or outbound sends were performed by this attempt.
- Only this acceptance document was changed. Graph/Graft tools, git status, complete dirty-checkout fingerprints, BMad configuration scripts and unlisted baseline test files remain outside the exposed authorized interfaces; no claim of those checks is made.

### Current gate and next bounded move

| Gate | Current result |
| --- | --- |
| D1 source/test SHA and signatures | PARTIAL: fresh file-level binding and source signatures; no whole-checkout identity or executed signature check. |
| D2 actual positive/two negatives/crash | BLOCKED: existing assertions unexecuted; genuine process-crash and stale ResearchRun checkpoints not established. |
| D3 independent oracle | Existing implementation preserved and source-reviewed; runtime unverified. |
| D4 focused and affected baseline | INFRA BLOCKED for focused; baseline NOT RUN because no baseline test_scope is authorized. |
| D5 typed QA handoff | BLOCKED/UNACCEPTED report required; publication transport is not acceptance. |
| Independent reducer/terminal readback | NOT PERFORMED by this implementer; coordinator/reviewer authority retained. |

Coordinator recovery: provision the required regular local `.venv` and project dependencies, then resume this same task owner with the exact focused command and source/test hashes above. Supply an explicit affected baseline test_scope and permitted ResearchRun/integration evidence for the remaining checkpoint and process-crash gates. Diagnose any actual pytest failure before bounded test-only repair. Do not broaden this lane into production repairs or recreate the existing implementation. Independent reducer consumes the resulting source-bound receipts and obtains authoritative terminal readback; this attempt never self-accepts.

Publication for this attempt is made exactly once after this evidence write. Its actual status/readback belongs to the tool response and final handoff; the historical INVALID_REPORT above is not the current attempt's publication result.
