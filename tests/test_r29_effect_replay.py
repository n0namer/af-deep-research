import asyncio
import pytest

from reasoners.deep_research_ext import verified_pipeline as PIPELINE


def candidate(revision=1, owner="owner-a", payload=None):
    fact = PIPELINE.GroundedFact(
        fact_id="fact-1",
        source_id="source-1",
        source_sha256="a" * 64,
    )
    return PIPELINE.build_grounded_verified_report(
        report_id="report-1",
        query="effect replay",
        source_revision="rev-1",
        source_owner=owner,
        source_file_sha256="b" * 64,
        facts=[fact],
        payload=payload or {"answer": "stable"},
        revision=revision,
    )


def test_effect_replay_is_idempotent_after_retry():
    store = PIPELINE.DurableVerifiedSourceReportStore()
    first = PIPELINE.persist_grounded_verified_report(
        store, candidate(), owner="owner-a", effect_id="effect-1"
    )
    second = PIPELINE.persist_grounded_verified_report(
        store, candidate(), owner="owner-a", effect_id="effect-1"
    )

    assert first == (candidate(), True, True)
    assert second == (candidate(), False, False)
    assert store.effect_count() == 1


def test_replay_with_conflicting_identity_is_rejected():
    store = PIPELINE.DurableVerifiedSourceReportStore()
    PIPELINE.persist_grounded_verified_report(
        store, candidate(), owner="owner-a", effect_id="effect-1"
    )

    conflicting = candidate(payload={"answer": "changed"})
    with pytest.raises(PIPELINE.VerifiedSourceReportError, match="revision payload conflicts"):
        PIPELINE.persist_grounded_verified_report(
            store, conflicting, owner="owner-a", effect_id="effect-1"
        )
    assert store.effect_count() == 1


def test_wrong_owner_cannot_replay_or_apply_effect():
    store = PIPELINE.DurableVerifiedSourceReportStore()
    with pytest.raises(PIPELINE.VerifiedSourceReportError, match="source owner"):
        PIPELINE.persist_grounded_verified_report(
            store, candidate(), owner="attacker", effect_id="effect-1"
        )
    assert store.effect_count() == 0
    assert store.load("report-1") is None


def test_cancelled_retry_cannot_persist_or_apply_effect():
    store = PIPELINE.DurableVerifiedSourceReportStore()
    with pytest.raises(asyncio.CancelledError):
        PIPELINE.persist_grounded_verified_report(
            store, candidate(), owner="owner-a", cancellation=lambda: True,
            effect_id="effect-1",
        )
    assert store.effect_count() == 0
    assert store.load("report-1") is None
