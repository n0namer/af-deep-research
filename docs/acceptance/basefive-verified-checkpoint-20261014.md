# BaseFive Verified Checkpoint — 2026-10-14

Status: CANDIDATE / UNACCEPTED

## Authority and source binding

- Task: `af-deep-research:v2-basefive-checkpoint-verified-research-fullcycle-20261014-r4`
- Attempt: `attempt-e02539e3-5b2c-472c-9a2a-566d4437e58c`
- Sticky thread: `01a1378f-a0c6-7122-a512-14c5603c4b45`
- Session: `manual-20261014-basefive-northstar-hyper-r4-af--f36450f566672b6c`
- Target root: `D:/Users/NIKITA/Documents/DEV/universal-solver-site/af-deep-research`
- Baseline Git SHA: `e10580c89eac7a4f6efb50c921ae9107ce8ad8dc`
- Acceptance remains with the independent reviewer/reducer and authoritative CrewSync readback.

## D1 — C4 interface and source identity

Source-bound DTO/interface signature from `reasoners/deep_research_ext/research_run.py`:

```text
checkpoint_research_run(
    store: ResearchRunStore,
    run: ResearchRun,
    *,
    stage: str,
    status: Optional[str] = None,
    source_revision: Optional[str] = None,
    expected_checkpoint_seq: Optional[int] = None,
    source_ids: Optional[Tuple[str, ...]] = None,
    evidence_summary: Optional[Mapping[str, Any]] = None,
    coverage_state: Optional[Mapping[str, Any]] = None,
    open_gap_ids: Optional[Tuple[str, ...]] = None,
    conflicts: Optional[Tuple[str, ...]] = None,
    budgets: Optional[Mapping[str, Any]] = None,
    payload: Optional[Mapping[str, Any]] = None,
) -> ResearchRun
```

- Current source SHA-256 after this repair: `1a3d5e432f43687e09218512897b61d0832eb803d728288c7466f83b81715b5d`
- Focused test SHA-256: `825887e53f2b8ca3354025c89b71202d05ad418da7bdf88b1b348c3f14996737`

## D2–D3 — Reproduction and repair

Independent host reproduction identified the defect in:

```text
tests/test_basefive_verified_checkpoint_restart_20261014.py::test_full_cycle_persists_verified_citation_and_partial_abstention
```

The retrieval checkpoint persisted `provider_call_ids=['provider-1']`. The next evidence-verified checkpoint supplied a new payload, and `resume_research_run(...).plan['provider_call_ids']` became `()`. This could permit duplicate external provider work after restart.

Root cause: checkpoint payload snapshots replace the prior payload. The previous implementation preserved no provider-call IDs when a later payload omitted that field.

Repair: preserve existing payload replacement semantics for unrelated fields, but merge provider-call IDs monotonically across checkpoints, normalize them to strings, deduplicate while preserving first-seen order, and tolerate an explicit null provider-ID collection. The existing stale in-memory checkpoint sequence fence remains intact.

The focused regression covers:

- positive retrieval → evidence verification → resume with verified citation and partial abstention;
- mismatched source-revision resume;
- stale in-memory checkpoint write without an optional sequence argument;
- replay creation across source revisions.

## D4 — Validation receipts

Independent host-native receipt supplied by QA:

```text
command=python pytest -q -p no:cacheprovider tests/test_basefive_verified_checkpoint_restart_20261014.py tests/test_basefive_frozen_fact_citation_20261014.py
status=RED
result=1 failed / 8 passed
log=D:/Temp/base20-qa-20261013/wave-r4-deep_py-final-20261014.log
failure=provider_call_ids were lost across the evidence_verified checkpoint
```

Post-repair scoped Wave runner receipt:

```text
status=BLOCKED
code=PYTHON_VENV_UNAVAILABLE
engine=python:pytest
file=tests/test_basefive_verified_checkpoint_restart_20261014.py
exit_code=null
stderr="A regular local .venv Python executable is required."
```

The requested second focused file was not authorized for this worker's test scope:

```text
status=BLOCKED_SCOPE
file=tests/test_basefive_frozen_fact_citation_20261014.py
error=test_outside_task_write_scope
```

No unrun or infrastructure-blocked check is promoted to PASS. Host evidence proves the pre-repair failure; post-repair runtime evidence remains unavailable in this Wave environment.

## D5 — Self-review and handoff

- Changed files remain inside the exact authorized write scope.
- Source change is limited to durable provider-call ID accumulation plus the prior stale checkpoint fence.
- The explicit null provider-ID boundary is handled as an empty collection.
- No live task, lease, lock, deployment, commit, push, or acceptance state was changed.
- Independent reviewer must rerun both host-focused tests in an environment with a regular local `.venv` and verify the source/test SHAs before acceptance.
- Status remains CANDIDATE / UNACCEPTED pending fresh post-repair runtime evidence and authoritative readback.
