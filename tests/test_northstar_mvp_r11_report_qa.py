from pathlib import Path

import pytest

from reasoners.deep_research_ext.verified_pipeline import (
    DurableVerifiedSourceReportStore,
    GroundedFact,
    VerifiedSourceReportError,
    build_grounded_verified_report,
    persist_grounded_verified_report,
    resume_grounded_verified_report,
    source_file_sha256,
)


FROZEN_R10_PRODUCER_SHA = "1ea0b249afc0c84d57824b78c5b4e6b3a79ae40a5b5890ed1a91d1046a872d1f"
SOURCE_SHA = "c" * 64
OWNER = "independent-r11-qa"
REVISION = "source-revision-r10"
PRODUCER_PATH = Path(__file__).resolve().parents[1] / "reasoners/deep_research_ext/verified_pipeline.py"


def make_report(*, revision=1, source_sha=SOURCE_SHA):
    return build_grounded_verified_report(
        report_id="independent-r11-qa-report",
        query="independent C4 boundary verification",
        source_revision=REVISION,
        source_owner=OWNER,
        source_file_sha256=source_sha,
        facts=[
            GroundedFact("qa-fact-1", "qa-source-1", SOURCE_SHA),
            GroundedFact("qa-fact-2", "qa-source-2", SOURCE_SHA),
        ],
        payload={"answer": "independently grounded", "citations": ["qa-fact-1", "qa-fact-2"]},
        abstained_requirement_ids=("qa-requirement-open",),
        revision=revision,
    )


def test_frozen_r10_producer_identity_is_stale_in_this_qa_lane():
    current_sha = source_file_sha256(PRODUCER_PATH)

    assert current_sha != FROZEN_R10_PRODUCER_SHA
    assert len(current_sha) == 64


def test_positive_persistence_boundary_preserves_grounded_report_and_effect_once():
    store = DurableVerifiedSourceReportStore()
    report = make_report()

    canonical, changed, applied = persist_grounded_verified_report(
        store, report, owner=OWNER, effect_id="independent-r11-terminal-effect"
    )

    assert (changed, applied) == (True, True)
    assert canonical.source_owner == OWNER
    assert canonical.source_file_sha256 == SOURCE_SHA
    assert canonical.abstained_requirement_ids == ("qa-requirement-open",)
    assert store.effect_count() == 1


def test_wrong_owner_is_rejected_without_persistence_or_terminal_effect():
    store = DurableVerifiedSourceReportStore()

    with pytest.raises(VerifiedSourceReportError, match="owner"):
        persist_grounded_verified_report(
            store, make_report(), owner="unauthorized-owner", effect_id="forbidden-effect"
        )

    assert store.load("independent-r11-qa-report") is None
    assert store.effect_count() == 0


def test_resume_rejects_stale_source_identity_without_mutating_store():
    store = DurableVerifiedSourceReportStore()
    persist_grounded_verified_report(store, make_report(), owner=OWNER)

    with pytest.raises(VerifiedSourceReportError, match="SHA"):
        resume_grounded_verified_report(
            store, "independent-r11-qa-report", owner=OWNER, source_file_sha256="d" * 64
        )

    assert store.load("independent-r11-qa-report").source_file_sha256 == SOURCE_SHA
    assert store.effect_count() == 0


def test_crash_replay_keeps_terminal_effect_idempotent_and_rejects_revision_gap():
    store = DurableVerifiedSourceReportStore()
    initial, changed, applied = persist_grounded_verified_report(
        store, make_report(), owner=OWNER, effect_id="crash-replay-effect"
    )

    assert (changed, applied) == (True, True)

    with pytest.raises(VerifiedSourceReportError, match="revision"):
        persist_grounded_verified_report(
            store, make_report(revision=3), owner=OWNER, effect_id="revision-gap-effect"
        )

    resumed = resume_grounded_verified_report(
        store, initial.report_id, owner=OWNER, source_file_sha256=SOURCE_SHA
    )
    replayed, replay_changed, replay_applied = persist_grounded_verified_report(
        store, resumed, owner=OWNER, effect_id="crash-replay-effect"
    )

    assert replayed == initial
    assert (replay_changed, replay_applied) == (False, False)
    assert store.effect_count() == 1
