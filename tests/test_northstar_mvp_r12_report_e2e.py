import asyncio
from dataclasses import replace
from pathlib import Path

import pytest

from reasoners.deep_research_ext.verified_pipeline import (
    DurableVerifiedSourceReportStore,
    VerifiedSourceReportError,
    build_grounded_verified_report,
    persist_grounded_verified_report,
    replay_verified_source_report,
    resume_grounded_verified_report,
    source_file_sha256,
)


@pytest.fixture
def report():
    source_path = (
        Path(__file__).resolve().parents[1]
        / "reasoners/deep_research_ext/verified_pipeline.py"
    )
    return build_grounded_verified_report(
        report_id="r12-local-report",
        query="Which source grounds this report?",
        source_revision="e10580c89eac7a4f6efb50c921ae9107ce8ad8dc",
        source_owner="r12-local-owner",
        source_file_sha256=source_file_sha256(source_path),
        facts=[{
            "fact_id": "fact-1",
            "source_id": "source-1",
            "source_sha256": source_file_sha256(source_path),
        }],
        payload={"answer": "source-1", "nested": {"verified": True}},
        abstained_requirement_ids=("unresolved-1",),
    )


def test_source_bound_report_and_duplicate_effect(report):
    store = DurableVerifiedSourceReportStore()
    canonical, changed, effect_applied = persist_grounded_verified_report(
        store, report, owner=report.source_owner, effect_id="local-effect-1"
    )
    assert (changed, effect_applied) == (True, True)
    assert canonical == report
    assert canonical.dto_version == "r10"
    assert canonical.facts[0].source_id in canonical.source_ids
    assert canonical.abstained_requirement_ids == ("unresolved-1",)
    canonical, changed, effect_applied = persist_grounded_verified_report(
        store, report, owner=report.source_owner, effect_id="local-effect-1"
    )
    assert canonical == report
    assert (changed, effect_applied) == (False, False)
    assert store.effect_count() == 1


@pytest.mark.parametrize("foreign_owner", ["foreign-owner", ""])
def test_foreign_owner_cannot_persist_or_record_effect(report, foreign_owner):
    store = DurableVerifiedSourceReportStore()
    persist_grounded_verified_report(
        store, report, owner=report.source_owner, effect_id="local-effect-1"
    )
    with pytest.raises(VerifiedSourceReportError, match="owner"):
        persist_grounded_verified_report(
            store,
            replace(report, source_owner=foreign_owner or report.source_owner),
            owner=foreign_owner,
            effect_id="foreign-effect",
        )
    with pytest.raises(VerifiedSourceReportError, match="owner"):
        store.record_effect(
            "foreign-effect", report_id=report.report_id,
            owner=foreign_owner, revision=report.revision,
        )
    assert store.load(report.report_id) == report
    assert store.effect_count() == 1


@pytest.mark.parametrize("mismatch", ["owner", "source_sha"])
def test_resume_rejects_foreign_identity_without_mutation(report, mismatch):
    store = DurableVerifiedSourceReportStore()
    persist_grounded_verified_report(store, report, owner=report.source_owner)
    with pytest.raises(VerifiedSourceReportError, match="owner|SHA"):
        resume_grounded_verified_report(
            store, report.report_id,
            owner="foreign-owner" if mismatch == "owner" else report.source_owner,
            source_file_sha256=(
                "0" * 64 if mismatch == "source_sha" else report.source_file_sha256
            ),
        )
    assert store.load(report.report_id) == report
    assert store.effect_count() == 0


def test_cancel_after_save_then_resume_same_store_without_duplicate_effect(report):
    store = DurableVerifiedSourceReportStore()
    cancellation_checks = iter((False, True))
    with pytest.raises(asyncio.CancelledError):
        persist_grounded_verified_report(
            store, report, owner=report.source_owner,
            cancellation=lambda: next(cancellation_checks),
            effect_id="local-effect-1",
        )
    assert store.load(report.report_id) == report
    assert store.effect_count() == 0
    resumed = resume_grounded_verified_report(
        store, report.report_id, owner=report.source_owner,
        source_file_sha256=report.source_file_sha256,
    )
    assert resumed == report
    assert persist_grounded_verified_report(
        store, resumed, owner=report.source_owner, effect_id="local-effect-1"
    )[1:] == (False, True)
    assert persist_grounded_verified_report(
        store, resumed, owner=report.source_owner, effect_id="local-effect-1"
    )[1:] == (False, False)
    assert store.effect_count() == 1


def test_revision_conflict_and_stale_effect_leave_canonical_report_unchanged(report):
    store = DurableVerifiedSourceReportStore()
    persist_grounded_verified_report(store, report, owner=report.source_owner)
    with pytest.raises(VerifiedSourceReportError, match="payload conflicts"):
        persist_grounded_verified_report(
            store, replace(report, payload={"answer": "conflicting"}),
            owner=report.source_owner,
        )
    with pytest.raises(VerifiedSourceReportError, match="advance by one"):
        replay_verified_source_report(report, replace(report, revision=3))
    next_report = replace(report, revision=2, payload={"answer": "updated"})
    assert persist_grounded_verified_report(
        store, next_report, owner=report.source_owner
    )[1] is True
    assert persist_grounded_verified_report(
        store, report, owner=report.source_owner
    )[0] == next_report
    with pytest.raises(VerifiedSourceReportError, match="revision is stale"):
        store.record_effect(
            "stale-effect", report_id=report.report_id,
            owner=report.source_owner, revision=1,
        )
    assert store.load(report.report_id) == next_report
    assert store.effect_count() == 0


def test_loaded_payload_does_not_mutate_stored_report(report):
    store = DurableVerifiedSourceReportStore()
    persist_grounded_verified_report(store, report, owner=report.source_owner)
    loaded = store.load(report.report_id)
    loaded.payload["nested"]["verified"] = False
    assert store.load(report.report_id).payload["nested"]["verified"] is True
