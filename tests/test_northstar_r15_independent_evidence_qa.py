import asyncio
import hashlib
import inspect
from dataclasses import replace
from pathlib import Path

import pytest

from reasoners.deep_research_ext import verified_pipeline as native


ROOT = Path(__file__).resolve().parents[1]
SOURCE_PATH = ROOT / "reasoners/deep_research_ext/verified_pipeline.py"
EXPECTED_CODE_SHA256 = "97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87"
FROZEN_SOURCE = b"Frozen QA bulletin: the pilot used three sensors. Cost was not reported.\n"
FROZEN_SHA256 = hashlib.sha256(FROZEN_SOURCE).hexdigest()
QUESTION = "How many sensors did the pilot use, and what did it cost?"
OWNER = "r15-independent-qa"
FACT_ID = "fact-pilot-sensors"
SOURCE_ID = "source-frozen-bulletin"
ANSWER_REQUIREMENT = "requirement-sensors"
GAP_REQUIREMENT = "requirement-cost"


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch):
    import socket

    def denied(*args, **kwargs):
        raise AssertionError("R15 independent QA must not open a network connection")

    monkeypatch.setattr(socket.socket, "connect", denied)
    monkeypatch.setattr(socket.socket, "connect_ex", denied)
    monkeypatch.setattr(socket, "create_connection", denied)


def make_report(*, revision=1):
    return native.build_grounded_verified_report(
        report_id="report-r15-frozen-question",
        query=QUESTION,
        source_revision="frozen-bulletin-v1",
        source_owner=OWNER,
        source_file_sha256=FROZEN_SHA256,
        facts=[{
            "fact_id": FACT_ID,
            "source_id": SOURCE_ID,
            "source_sha256": FROZEN_SHA256,
        }],
        payload={
            "answers": [{
                "requirement_id": ANSWER_REQUIREMENT,
                "text": "The pilot used three sensors.",
                "fact_id": FACT_ID,
                "source_id": SOURCE_ID,
            }],
            "abstentions": [{
                "requirement_id": GAP_REQUIREMENT,
                "reason": "Cost is absent from the frozen bulletin.",
            }],
        },
        abstained_requirement_ids=[GAP_REQUIREMENT],
        revision=revision,
    )


def assert_frozen_question_oracle(report):
    assert report.query == QUESTION
    assert report.source_owner == OWNER
    assert report.source_revision == "frozen-bulletin-v1"
    assert report.source_file_sha256 == FROZEN_SHA256
    assert report.dto_version == "r10"
    assert report.source_ids == (SOURCE_ID,)
    assert tuple((fact.fact_id, fact.source_id, fact.source_sha256) for fact in report.facts) == (
        (FACT_ID, SOURCE_ID, FROZEN_SHA256),
    )
    assert report.payload["answers"] == [{
        "requirement_id": ANSWER_REQUIREMENT,
        "text": "The pilot used three sensors.",
        "fact_id": FACT_ID,
        "source_id": SOURCE_ID,
    }]
    assert report.abstained_requirement_ids == (GAP_REQUIREMENT,)
    assert report.payload["abstentions"] == [{
        "requirement_id": GAP_REQUIREMENT,
        "reason": "Cost is absent from the frozen bulletin.",
    }]
    assert b"three sensors" in FROZEN_SOURCE
    assert b"Cost was not reported" in FROZEN_SOURCE


def test_exact_source_fingerprint_and_real_api_signatures():
    assert hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest() == EXPECTED_CODE_SHA256
    assert native.source_file_sha256(SOURCE_PATH) == EXPECTED_CODE_SHA256
    assert inspect.getsourcefile(native.build_grounded_verified_report) == str(SOURCE_PATH)
    assert str(inspect.signature(native.build_grounded_verified_report)) == (
        "(*, report_id, query, source_revision, source_owner, source_file_sha256, "
        "facts, payload, abstained_requirement_ids=(), revision=1)"
    )
    assert str(inspect.signature(native.persist_grounded_verified_report)) == (
        "(store, candidate, *, owner, cancellation=None, effect_id=None)"
    )
    assert str(inspect.signature(native.resume_grounded_verified_report)) == (
        "(store, report_id, *, owner, source_file_sha256)"
    )


def test_positive_frozen_question_report_and_idempotent_effect():
    store = native.DurableVerifiedSourceReportStore()
    report = make_report()
    canonical, changed, effect = native.persist_grounded_verified_report(
        store, report, owner=OWNER, effect_id="terminal-r15"
    )
    assert (changed, effect) == (True, True)
    assert_frozen_question_oracle(canonical)
    replayed, changed, effect = native.persist_grounded_verified_report(
        store, make_report(), owner=OWNER, effect_id="terminal-r15"
    )
    assert (changed, effect) == (False, False)
    assert replayed == canonical
    assert store.effect_count() == 1


def test_foreign_owner_rejected_before_any_write_or_effect():
    store = native.DurableVerifiedSourceReportStore()
    report = make_report()
    with pytest.raises(native.VerifiedSourceReportError, match="source owner"):
        native.persist_grounded_verified_report(
            store, report, owner="foreign-owner", effect_id="terminal-r15"
        )
    assert store.load(report.report_id) is None
    assert store.effect_count() == 0


@pytest.mark.parametrize("drift", ["owner", "source-sha"])
def test_resume_rejects_foreign_owner_and_stale_source(drift):
    store = native.DurableVerifiedSourceReportStore()
    report = make_report()
    native.persist_grounded_verified_report(store, report, owner=OWNER)
    with pytest.raises(native.VerifiedSourceReportError, match="source owner|source file SHA"):
        native.resume_grounded_verified_report(
            store, report.report_id,
            owner="foreign-owner" if drift == "owner" else OWNER,
            source_file_sha256="0" * 64 if drift == "source-sha" else FROZEN_SHA256,
        )
    assert store.load(report.report_id) == report
    assert store.effect_count() == 0


def test_interruption_after_save_resumes_without_duplicate_terminal_effect():
    store = native.DurableVerifiedSourceReportStore()
    report = make_report()

    def cancel_after_persistence():
        return store.load(report.report_id) is not None

    with pytest.raises(asyncio.CancelledError):
        native.persist_grounded_verified_report(
            store, report, owner=OWNER,
            cancellation=cancel_after_persistence, effect_id="terminal-r15",
        )
    assert store.load(report.report_id) == report
    assert store.effect_count() == 0
    resumed = native.resume_grounded_verified_report(
        store, report.report_id, owner=OWNER, source_file_sha256=FROZEN_SHA256
    )
    assert_frozen_question_oracle(resumed)
    canonical, changed, effect = native.persist_grounded_verified_report(
        store, resumed, owner=OWNER, effect_id="terminal-r15"
    )
    assert canonical == report
    assert (changed, effect) == (False, True)
    assert native.persist_grounded_verified_report(
        store, resumed, owner=OWNER, effect_id="terminal-r15"
    )[1:] == (False, False)
    assert store.effect_count() == 1


def test_pre_save_cancellation_has_no_side_effects():
    store = native.DurableVerifiedSourceReportStore()
    report = make_report()
    with pytest.raises(asyncio.CancelledError):
        native.persist_grounded_verified_report(
            store, report, owner=OWNER, cancellation=True, effect_id="terminal-r15"
        )
    assert store.load(report.report_id) is None
    assert store.effect_count() == 0


def test_stale_report_revision_and_expected_revision_are_fenced():
    store = native.DurableVerifiedSourceReportStore()
    first = make_report()
    native.persist_grounded_verified_report(store, first, owner=OWNER)
    second = make_report(revision=2)
    assert native.persist_grounded_verified_report(store, second, owner=OWNER)[1] is True
    canonical, changed, effect = native.persist_grounded_verified_report(store, first, owner=OWNER)
    assert canonical.revision == 2
    assert (changed, effect) == (False, None)
    with pytest.raises(native.VerifiedSourceReportError, match="stored report revision is stale"):
        store.save(first, owner=OWNER, expected_revision=1)
    with pytest.raises(native.VerifiedSourceReportError, match="effect revision is stale"):
        store.record_effect("stale-terminal", report_id=first.report_id, owner=OWNER, revision=1)
    assert store.load(first.report_id) == second
    assert store.effect_count() == 0


@pytest.mark.parametrize("kind", ["payload-conflict", "revision-jump", "identity-drift"])
def test_replay_conflicts_preserve_canonical_report(kind):
    store = native.DurableVerifiedSourceReportStore()
    report = make_report()
    native.persist_grounded_verified_report(store, report, owner=OWNER)
    candidates = {
        "payload-conflict": replace(report, payload={"answers": []}),
        "revision-jump": replace(report, revision=3),
        "identity-drift": replace(report, source_revision="foreign-revision"),
    }
    with pytest.raises(native.VerifiedSourceReportError):
        native.persist_grounded_verified_report(store, candidates[kind], owner=OWNER)
    assert store.load(report.report_id) == report
    assert store.effect_count() == 0


def test_store_load_isolated_from_nested_payload_mutation():
    store = native.DurableVerifiedSourceReportStore()
    report = make_report()
    native.persist_grounded_verified_report(store, report, owner=OWNER)
    report.payload["answers"][0]["source_id"] = "foreign-source"
    loaded = store.load(report.report_id)
    assert_frozen_question_oracle(loaded)
    loaded.payload["abstentions"].clear()
    assert_frozen_question_oracle(store.load(report.report_id))


def test_new_adapter_does_not_claim_process_restart_durability():
    original = native.DurableVerifiedSourceReportStore()
    report = make_report()
    native.persist_grounded_verified_report(original, report, owner=OWNER)
    restarted = native.DurableVerifiedSourceReportStore()
    with pytest.raises(native.VerifiedSourceReportError, match="grounded report was not found"):
        native.resume_grounded_verified_report(
            restarted, report.report_id, owner=OWNER, source_file_sha256=FROZEN_SHA256
        )
    assert restarted.effect_count() == 0
    assert_frozen_question_oracle(original.load(report.report_id))
