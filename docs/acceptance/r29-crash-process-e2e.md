# R29 Crash-Process E2E

Status: CANDIDATE / UNACCEPTED

## Scope

This acceptance artifact records the real child-process kill/resume regression for the existing
research_run checkpoint contract and the no-repeat side-effect boundary for verified reports.
No production source file was changed because the inspected implementation already provides the
required atomic checkpoint, source-revision/checkpoint-sequence fencing, and effect-id idempotency.

## Evidence-bound behavior

- ResearchRunStore.save flushes and fsyncs a temporary JSON checkpoint before os.replace.
- resume_research_run reloads the durable checkpoint and returns recorded provider/evidence IDs.
- checkpoint_research_run rejects stale checkpoint sequences and deduplicates IDs.
- DurableVerifiedSourceReportStore.record_effect returns False for a repeated effect ID.

## Validation

Command: python -m pytest -q tests/test_r29_crash_process_e2e.py

Required receipt: native pytest exit 0 with five passing tests, including a real subprocess terminated with signal 9. A denied or unavailable runner must remain BLOCKED, never PASS.

## Source identities

- reasoners/deep_research_ext/research_run.py: a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea
- reasoners/deep_research_ext/verified_pipeline.py: 97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87

Independent reviewer and CrewSync terminal readback remain required.
