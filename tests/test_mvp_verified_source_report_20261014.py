import asyncio

import pytest

from reasoners.deep_research_ext.verified_pipeline import (
    VerifiedSourceReportError,
    _raise_if_cancelled,
    build_verified_source_report,
    persist_verified_source_report,
)


class Store:
    def __init__(self):
        self.values = {}
        self.saves = 0

    def load(self, report_id):
        return self.values.get(report_id)

    def save(self, report):
        self.saves += 1
        self.values[report.report_id] = report


def make_report(*, report_id="report-1", query="verified source report", revision=1, payload=None):
    return build_verified_source_report(
        report_id=report_id,
        query=query,
        source_ids=["source-1", "source-2"],
        revision=revision,
        payload=payload or {"answer": "supported"},
    )


def test_positive_report_is_typed_and_persisted_once():
    store = Store()

    report = persist_verified_source_report(store, make_report())
    replay = persist_verified_source_report(store, make_report())

    assert report.report_id == "report-1"
    assert report.revision == 1
    assert report.source_ids == ("source-1", "source-2")
    assert replay == report
    assert store.saves == 1


def test_wrong_identity_and_conflicting_payload_fail_closed():
    store = Store()
    persist_verified_source_report(store, make_report())

    with pytest.raises(VerifiedSourceReportError, match="identity"):
        persist_verified_source_report(store, make_report(query="tampered query"))

    with pytest.raises(VerifiedSourceReportError, match="conflicts"):
        persist_verified_source_report(store, make_report(payload={"answer": "tampered"}))

    assert store.saves == 1
    assert store.values["report-1"].payload == {"answer": "supported"}


def test_malformed_report_and_cancellation_have_no_persisted_effect():
    store = Store()

    with pytest.raises(VerifiedSourceReportError, match="positive integer"):
        build_verified_source_report(
            report_id="report-1",
            query="query",
            source_ids=["source-1"],
            revision=0,
            payload={},
        )

    with pytest.raises(VerifiedSourceReportError, match="unique"):
        build_verified_source_report(
            report_id="report-1",
            query="query",
            source_ids=["source-1", "source-1"],
            revision=1,
            payload={},
        )

    with pytest.raises(asyncio.CancelledError, match="cancelled"):
        _raise_if_cancelled(lambda: True)

    assert store.saves == 0
    assert store.values == {}


def test_restart_replay_accepts_next_revision_without_duplicate_previous_effect():
    store = Store()

    first = persist_verified_source_report(store, make_report(revision=1))
    second = persist_verified_source_report(store, make_report(revision=2, payload={"answer": "supported-v2"}))
    replayed_first = persist_verified_source_report(store, make_report(revision=1))

    assert first.revision == 1
    assert second.revision == 2
    assert replayed_first.revision == 2
    assert store.saves == 2
    assert store.values["report-1"].payload == {"answer": "supported-v2"}
