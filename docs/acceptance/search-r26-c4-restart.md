# Search R26 checkpoint/restart evidence

Status: CANDIDATE / UNACCEPTED

This independent check exercises existing native APIs without changing production code. It separates disk checkpoint persistence from the process-local report/effect store.

Proves: positive checkpoint resume and duplicate effect refusal; foreign-owner refusal; stale source-revision refusal; stale checkpoint-sequence refusal; cancellation before persistence leaves no report.

The report store is deliberately treated as process-local memory guarded by a lock. The disk-backed ResearchRunStore is checked across a store reload boundary; a real interpreter restart is not claimed.

Source binding:
- reasoners/deep_research_ext/research_run.py SHA-256 a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea
- reasoners/deep_research_ext/verified_pipeline.py SHA-256 97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87
- docs/architecture/search-r16-contract.json SHA-256 98fae3d2e5259526139558c7cf492a9c96817606a2e486c7f1d22074772633c2

Validation: python -m pytest -q tests/test_search_r26_checkpoint_c4.py
No provider, network, environment secret, production source, prior C4 artifact, or live task state is touched. Acceptance remains with independent review.
