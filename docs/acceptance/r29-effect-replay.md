# R29 effect replay

Status: CANDIDATE / UNACCEPTED

Source-bound finding: `reasoners/deep_research_ext/verified_pipeline.py` already implements the bounded external-effect fence. `persist_grounded_verified_report` persists a grounded report monotonically, then calls `DurableVerifiedSourceReportStore.record_effect`; duplicate effect IDs return `False` and do not apply the effect again.

Focused evidence target: `python -m pytest -q tests/test_r29_effect_replay.py`

Coverage:
- positive: first effect applies, identical retry is idempotent;
- negative: conflicting same-revision payload is rejected;
- negative: wrong owner cannot persist or apply an effect;
- negative: cancellation prevents persistence and effect application.

No production source change is proposed because the current implementation already satisfies the requested replay boundary; this task adds executable evidence only.
