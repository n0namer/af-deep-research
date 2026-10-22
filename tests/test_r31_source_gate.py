from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reasoners/deep_research_ext/verified_pipeline.py"
CONTRACT = ROOT / "docs/architecture/basefive-r14-contracts.json"
EXPECTED_SOURCE_SHA = "97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87"
OWNER = "r31-source-owner"
SOURCE_REVISION = "e10580c89eac7a4f6efb50c921ae9107ce8ad8dc"


def _pipeline():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from reasoners.deep_research_ext import verified_pipeline
    return verified_pipeline


def _candidate(pipeline, *, owner=OWNER, source_sha=EXPECTED_SOURCE_SHA):
    return pipeline.build_grounded_verified_report(
        report_id="r31-source-gate",
        query="source provenance gate",
        source_revision=SOURCE_REVISION,
        source_owner=owner,
        source_file_sha256=source_sha,
        facts=[{
            "fact_id": "fact-1",
            "source_id": "source-1",
            "source_sha256": "a" * 64,
        }],
        payload={"claim": "source-backed"},
    )


def test_positive_current_source_identity_and_idempotent_effect():
    pipeline = _pipeline()
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    source_entry = next(item for item in contract["sources"] if item["path"] == str(SOURCE.relative_to(ROOT)).replace("\\", "/"))
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == EXPECTED_SOURCE_SHA == source_entry["sha256"]
    assert contract["versions"]["VerifiedSourceReport"] == "r10"

    store = pipeline.DurableVerifiedSourceReportStore()
    candidate = _candidate(pipeline)
    first = pipeline.persist_grounded_verified_report(
        store, candidate, owner=OWNER, effect_id="r31-effect"
    )
    second = pipeline.persist_grounded_verified_report(
        store, candidate, owner=OWNER, effect_id="r31-effect"
    )

    assert first[1:] == (True, True)
    assert second[1:] == (False, False)
    receipt = store.load(candidate.report_id)
    assert receipt.source_owner == OWNER
    assert receipt.source_file_sha256 == EXPECTED_SOURCE_SHA
    assert receipt.dto_version == "r10"
    assert store.effect_count() == 1


def test_negative_malformed_source_hash_is_rejected_before_receipt():
    pipeline = _pipeline()
    store = pipeline.DurableVerifiedSourceReportStore()
    with pytest.raises(pipeline.VerifiedSourceReportError, match="lowercase SHA-256"):
        _candidate(pipeline, source_sha="not-a-sha")
    assert store.load("r31-source-gate") is None
    assert store.effect_count() == 0


def test_negative_foreign_owner_cannot_persist_or_record_effect():
    pipeline = _pipeline()
    store = pipeline.DurableVerifiedSourceReportStore()
    candidate = _candidate(pipeline, owner="foreign-owner")
    with pytest.raises(pipeline.VerifiedSourceReportError, match="owner"):
        pipeline.persist_grounded_verified_report(
            store, candidate, owner=OWNER, effect_id="foreign-effect"
        )
    assert store.load(candidate.report_id) is None
    assert store.effect_count() == 0


def test_negative_stale_resume_preserves_canonical_receipt():
    pipeline = _pipeline()
    store = pipeline.DurableVerifiedSourceReportStore()
    candidate = _candidate(pipeline)
    pipeline.persist_grounded_verified_report(
        store, candidate, owner=OWNER, effect_id="r31-effect"
    )
    before = store.load(candidate.report_id)
    with pytest.raises(pipeline.VerifiedSourceReportError, match="source file SHA"):
        pipeline.resume_grounded_verified_report(
            store, candidate.report_id, owner=OWNER, source_file_sha256="0" * 64
        )
    assert store.load(candidate.report_id) == before
    assert store.effect_count() == 1
