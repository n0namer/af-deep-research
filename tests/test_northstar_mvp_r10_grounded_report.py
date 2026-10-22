import asyncio
from pathlib import Path

import pytest

from reasoners.deep_research_ext.verified_pipeline import (
    DurableVerifiedSourceReportStore,
    GroundedFact,
    VerifiedSourceReportError,
    _raise_if_cancelled,
    build_grounded_verified_report,
    persist_grounded_verified_report,
    resume_grounded_verified_report,
    source_file_sha256,
)


SOURCE_SHA = "a" * 64
OWNER = "owner-r10"
REVISION = "source-revision-r10"


def make_report(*, revision=1, payload=None, owner=OWNER, source_sha=SOURCE_SHA):
    return build_grounded_verified_report(
        report_id="report-r10",
        query="grounded answer",
        source_revision=REVISION,
        source_owner=owner,
        source_file_sha256=source_sha,
        facts=[
            GroundedFact("fact-1", "source-1", SOURCE_SHA),
            GroundedFact("fact-2", "source-1", SOURCE_SHA),
        ],
        payload=payload or {"answer": "supported", "citations": ["fact-1", "fact-2"]},
        abstained_requirement_ids=("requirement-2",),
        revision=revision,
    )


def test_positive_report_records_source_sha_facts_abstention_and_one_effect():
    store = DurableVerifiedSourceReportStore()
    payload = {"answer": "supported", "nested": {"citations": ["fact-1"]}}
    report = make_report(payload=payload)

    canonical, changed, applied = persist_grounded_verified_report(
        store, report, owner=OWNER, effect_id="terminal-effect-1",
    )
    payload["nested"]["citations"].append("tampered")
    replay, replay_changed, replay_applied = persist_grounded_verified_report(
        store,
        report,
        owner=OWNER,
        effect_id="terminal-effect-1",
    )

    assert changed is True
    assert applied is True
    assert replay_changed is False
    assert replay_applied is False
    assert replay == canonical
    assert canonical.source_file_sha256 == SOURCE_SHA
    assert canonical.facts[0].fact_id == "fact-1"
    assert canonical.abstained_requirement_ids == ("requirement-2",)
    assert canonical.payload["nested"] == {"citations": ["fact-1"]}
    assert store.effect_count() == 1


def test_invalid_owner_fails_closed_without_persisting_or_effect():
    store = DurableVerifiedSourceReportStore()

    with pytest.raises(VerifiedSourceReportError, match="owner"):
        persist_grounded_verified_report(store, make_report(), owner="wrong-owner", effect_id="effect")

    assert store.load("report-r10") is None
    assert store.effect_count() == 0


def test_invalid_payload_and_cancellation_fail_closed():
    store = DurableVerifiedSourceReportStore()

    with pytest.raises(VerifiedSourceReportError, match="payload"):
        build_grounded_verified_report(
            report_id="bad",
            query="query",
            source_revision=REVISION,
            source_owner=OWNER,
            source_file_sha256=SOURCE_SHA,
            facts=[{"fact_id": "fact", "source_id": "source", "source_sha256": SOURCE_SHA}],
            payload=["not", "a", "mapping"],
        )

    with pytest.raises(VerifiedSourceReportError, match="lowercase SHA"):
        build_grounded_verified_report(
            report_id="bad",
            query="query",
            source_revision=REVISION,
            source_owner=OWNER,
            source_file_sha256="B" * 64,
            facts=[{"fact_id": "fact", "source_id": "source", "source_sha256": SOURCE_SHA}],
            payload={},
        )

    with pytest.raises(asyncio.CancelledError, match="cancelled"):
        _raise_if_cancelled(lambda: True)

    with pytest.raises(asyncio.CancelledError, match="cancelled"):
        persist_grounded_verified_report(store, make_report(), owner=OWNER, cancellation=True)

    assert store.load("report-r10") is None
    assert store.effect_count() == 0


def test_crash_replay_does_not_duplicate_terminal_effect_or_accept_stale_revision():
    store = DurableVerifiedSourceReportStore()
    first, changed, applied = persist_grounded_verified_report(
        store, make_report(), owner=OWNER, effect_id="effect-1",
    )
    assert (changed, applied) == (True, True)

    with pytest.raises(VerifiedSourceReportError, match="revision"):
        persist_grounded_verified_report(
            store, make_report(revision=3), owner=OWNER, effect_id="effect-2",
        )

    resumed = resume_grounded_verified_report(
        store, first.report_id, owner=OWNER, source_file_sha256=SOURCE_SHA,
    )
    replayed, replay_changed, replay_applied = persist_grounded_verified_report(
        store, resumed, owner=OWNER, effect_id="effect-1",
    )

    assert replayed == first
    assert replay_changed is False
    assert replay_applied is False
    assert store.effect_count() == 1


def test_resume_rejects_stale_source_identity_and_file_hash():
    store = DurableVerifiedSourceReportStore()
    persist_grounded_verified_report(store, make_report(), owner=OWNER)

    with pytest.raises(VerifiedSourceReportError, match="owner"):
        resume_grounded_verified_report(store, "report-r10", owner="other", source_file_sha256=SOURCE_SHA)
    with pytest.raises(VerifiedSourceReportError, match="SHA"):
        resume_grounded_verified_report(store, "report-r10", owner=OWNER, source_file_sha256="b" * 64)


def test_source_file_sha256_is_immutable_file_identity(tmp_path: Path):
    source = tmp_path / "source.txt"
    source.write_text("frozen source\n", encoding="utf-8")

    digest = source_file_sha256(source)

    assert len(digest) == 64
    assert digest == source_file_sha256(source)
