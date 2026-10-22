import asyncio
import dataclasses
import hashlib
import importlib
import inspect
import re
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reasoners/deep_research_ext/verified_pipeline.py"
SOURCE_SHA = "97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87"
QUESTION = "What is the capital of France?"
FACT_ID = "fact-france-capital"
SOURCE_ID = "frozen-geography"
EVIDENCE = b"The capital of France is Paris.\n"
EVIDENCE_SHA = hashlib.sha256(EVIDENCE).hexdigest()
OWNER = "r16-disposable-owner"
EFFECT_ID = "r16-report-terminal-effect"


@pytest.fixture(scope="module")
def api():
    return importlib.import_module("reasoners.deep_research_ext.verified_pipeline")


@pytest.fixture
def store(api):
    return api.DurableVerifiedSourceReportStore()


def candidate(api, *, revision=1, payload=None, facts=None, owner=OWNER):
    if payload is None:
        payload = {
            "question": QUESTION,
            "evidence": [{
                "fact_id": FACT_ID,
                "source_id": SOURCE_ID,
                "source_sha256": EVIDENCE_SHA,
                "excerpt": EVIDENCE.decode().strip(),
            }],
            "document": f"The capital of France is Paris. [{SOURCE_ID}:{FACT_ID}]",
        }
    if facts is None:
        facts = [{"fact_id": FACT_ID, "source_id": SOURCE_ID,
                  "source_sha256": EVIDENCE_SHA}]
    return api.build_grounded_verified_report(
        report_id="r16-disposable-report", query=QUESTION,
        source_revision=SOURCE_SHA, source_owner=owner,
        source_file_sha256=SOURCE_SHA, facts=facts, payload=payload,
        abstained_requirement_ids=("population-unavailable",), revision=revision,
    )


def assert_frozen_citations(report):
    assert report.query == QUESTION
    assert report.payload["question"] == QUESTION
    assert report.source_ids == (SOURCE_ID,)
    assert [(fact.fact_id, fact.source_id, fact.source_sha256)
            for fact in report.facts] == [(FACT_ID, SOURCE_ID, EVIDENCE_SHA)]
    assert report.payload["evidence"] == [{
        "fact_id": FACT_ID, "source_id": SOURCE_ID,
        "source_sha256": EVIDENCE_SHA, "excerpt": EVIDENCE.decode().strip(),
    }]
    assert re.findall(r"\[([^\[\]]+)\]", report.payload["document"]) == [
        f"{SOURCE_ID}:{FACT_ID}"
    ]
    assert report.payload["document"] == (
        f"The capital of France is Paris. [{SOURCE_ID}:{FACT_ID}]"
    )
    assert report.abstained_requirement_ids == ("population-unavailable",)


def test_source_bytes_match_pinned_r14_identity():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA


@pytest.mark.parametrize("symbol,parameters", [
    ("build_grounded_verified_report", (
        "report_id", "query", "source_revision", "source_owner",
        "source_file_sha256", "facts", "payload", "abstained_requirement_ids", "revision",
    )),
    ("persist_grounded_verified_report", (
        "store", "candidate", "owner", "cancellation", "effect_id",
    )),
    ("resume_grounded_verified_report", (
        "store", "report_id", "owner", "source_file_sha256",
    )),
])
def test_current_api_signatures(api, symbol, parameters):
    signature = inspect.signature(getattr(api, symbol))
    assert tuple(signature.parameters) == parameters
    keyword_start = 0 if symbol == "build_grounded_verified_report" else 2
    assert all(parameter.kind == inspect.Parameter.KEYWORD_ONLY
               for parameter in tuple(signature.parameters.values())[keyword_start:])


def test_current_dto_fields_and_version(api):
    assert tuple(field.name for field in dataclasses.fields(api.GroundedFact)) == (
        "fact_id", "source_id", "source_sha256",
    )
    assert tuple(field.name for field in dataclasses.fields(api.VerifiedSourceReport)) == (
        "report_id", "query", "source_ids", "revision", "payload", "source_revision",
        "source_owner", "source_file_sha256", "facts", "abstained_requirement_ids",
        "dto_version",
    )
    assert candidate(api).dto_version == "r10"


def test_positive_exact_fact_citation_effect_and_receipt(api, store):
    report = candidate(api)
    persisted, changed, effect = api.persist_grounded_verified_report(
        store, report, owner=OWNER, effect_id=EFFECT_ID,
    )
    assert changed is True and effect is True
    assert_frozen_citations(persisted)
    receipt = api.resume_grounded_verified_report(
        store, report.report_id, owner=OWNER, source_file_sha256=SOURCE_SHA,
    )
    assert receipt == persisted
    assert_frozen_citations(receipt)
    assert store.effect_count() == 1
    repeated, changed, effect = api.persist_grounded_verified_report(
        store, report, owner=OWNER, effect_id=EFFECT_ID,
    )
    assert repeated == receipt and changed is False and effect is False
    assert store.effect_count() == 1


@pytest.mark.parametrize("mutation", ["unsupported", "foreign-source", "wrong-fact-id"])
def test_untrusted_document_rejected_before_effect(api, store, mutation):
    payload = candidate(api).payload
    if mutation == "unsupported":
        payload["document"] = f"Paris has nine million residents. [{SOURCE_ID}:{FACT_ID}]"
    elif mutation == "foreign-source":
        payload["document"] = f"The capital of France is Paris. [foreign:{FACT_ID}]"
    else:
        payload["document"] = f"The capital of France is Paris. [{SOURCE_ID}:foreign-fact]"
    with pytest.raises(api.VerifiedSourceReportError):
        report = candidate(api, payload=payload)
        api.persist_grounded_verified_report(store, report, owner=OWNER, effect_id=EFFECT_ID)
    assert store.load("r16-disposable-report") is None
    assert store.effect_count() == 0


def test_cancel_before_persistence_has_no_effect(api, store):
    with pytest.raises(asyncio.CancelledError):
        api.persist_grounded_verified_report(
            store, candidate(api), owner=OWNER, cancellation=True, effect_id=EFFECT_ID,
        )
    assert store.load("r16-disposable-report") is None
    assert store.effect_count() == 0


def test_interrupt_after_save_retry_same_store_is_idempotent(api, store):
    report = candidate(api)
    checks = []

    def cancelled_after_save():
        checks.append(store.load(report.report_id) is not None)
        return checks[-1]

    with pytest.raises(asyncio.CancelledError):
        api.persist_grounded_verified_report(
            store, report, owner=OWNER,
            cancellation=cancelled_after_save, effect_id=EFFECT_ID,
        )
    assert checks == [False, True]
    assert store.load(report.report_id) == report
    assert store.effect_count() == 0
    resumed = api.resume_grounded_verified_report(
        store, report.report_id, owner=OWNER, source_file_sha256=SOURCE_SHA,
    )
    _, changed, effect = api.persist_grounded_verified_report(
        store, resumed, owner=OWNER, effect_id=EFFECT_ID,
    )
    assert changed is False and effect is True
    _, changed, effect = api.persist_grounded_verified_report(
        store, resumed, owner=OWNER, effect_id=EFFECT_ID,
    )
    assert changed is False and effect is False
    assert store.effect_count() == 1


def test_receipt_and_effect_survive_recreated_store(api):
    original = api.DurableVerifiedSourceReportStore()
    report = candidate(api)
    api.persist_grounded_verified_report(original, report, owner=OWNER, effect_id=EFFECT_ID)
    restarted = api.DurableVerifiedSourceReportStore()
    receipt = api.resume_grounded_verified_report(
        restarted, report.report_id, owner=OWNER, source_file_sha256=SOURCE_SHA,
    )
    assert receipt == report
    _, changed, effect = api.persist_grounded_verified_report(
        restarted, receipt, owner=OWNER, effect_id=EFFECT_ID,
    )
    assert changed is False and effect is False
    assert restarted.effect_count() == 1


@pytest.mark.parametrize("operation", ["persist", "resume", "effect"])
def test_stale_owner_cannot_write_or_resume(api, store, operation):
    report = candidate(api)
    api.persist_grounded_verified_report(store, report, owner=OWNER, effect_id=EFFECT_ID)
    before = store.load(report.report_id)
    with pytest.raises(api.VerifiedSourceReportError, match="owner"):
        if operation == "persist":
            api.persist_grounded_verified_report(
                store, candidate(api, revision=2), owner="stale-owner", effect_id="stale-effect",
            )
        elif operation == "resume":
            api.resume_grounded_verified_report(
                store, report.report_id, owner="stale-owner", source_file_sha256=SOURCE_SHA,
            )
        else:
            store.record_effect("stale-effect", report_id=report.report_id,
                                owner="stale-owner", revision=1)
    assert store.load(report.report_id) == before
    assert store.effect_count() == 1


def test_source_sha_mismatch_cannot_resume(api, store):
    report = candidate(api)
    api.persist_grounded_verified_report(store, report, owner=OWNER)
    with pytest.raises(api.VerifiedSourceReportError, match="SHA"):
        api.resume_grounded_verified_report(
            store, report.report_id, owner=OWNER, source_file_sha256="0" * 64,
        )
    assert store.load(report.report_id) == report and store.effect_count() == 0


@pytest.mark.parametrize("change", ["payload", "fact", "revision-gap"])
def test_conflicting_replay_does_not_overwrite_receipt(api, store, change):
    report = candidate(api)
    api.persist_grounded_verified_report(store, report, owner=OWNER, effect_id=EFFECT_ID)
    if change == "payload":
        replacement = dataclasses.replace(report, payload={"conflicting": True})
    elif change == "fact":
        replacement = dataclasses.replace(report, facts=(
            api.GroundedFact("foreign-fact", SOURCE_ID, EVIDENCE_SHA),
        ))
    else:
        replacement = dataclasses.replace(report, revision=3)
    with pytest.raises(api.VerifiedSourceReportError):
        api.persist_grounded_verified_report(
            store, replacement, owner=OWNER, effect_id="conflicting-effect",
        )
    assert store.load(report.report_id) == report and store.effect_count() == 1


def test_monotonic_revision_and_stale_effect_regression(api, store):
    first = candidate(api)
    api.persist_grounded_verified_report(store, first, owner=OWNER, effect_id=EFFECT_ID)
    second = candidate(api, revision=2)
    canonical, changed, effect = api.persist_grounded_verified_report(
        store, second, owner=OWNER, effect_id=EFFECT_ID,
    )
    assert canonical == second and changed is True and effect is False
    canonical, changed, effect = api.persist_grounded_verified_report(
        store, first, owner=OWNER, effect_id=EFFECT_ID,
    )
    assert canonical == second and changed is False and effect is False
    with pytest.raises(api.VerifiedSourceReportError, match="stale"):
        store.record_effect("old-effect", report_id=first.report_id, owner=OWNER, revision=1)
    assert store.load(first.report_id) == second and store.effect_count() == 1


def test_payload_isolated_at_build_save_and_load(api, store):
    payload = candidate(api).payload
    report = candidate(api, payload=payload)
    payload["evidence"][0]["excerpt"] = "tampered before persistence"
    assert_frozen_citations(report)
    api.persist_grounded_verified_report(store, report, owner=OWNER)
    report.payload["evidence"][0]["excerpt"] = "tampered after persistence"
    loaded = store.load(report.report_id)
    assert_frozen_citations(loaded)
    loaded.payload["evidence"].clear()
    assert_frozen_citations(store.load(report.report_id))


@pytest.mark.parametrize("facts", [[], [{
    "fact_id": FACT_ID, "source_id": SOURCE_ID, "source_sha256": "not-a-digest",
}], [
    {"fact_id": FACT_ID, "source_id": SOURCE_ID, "source_sha256": EVIDENCE_SHA},
    {"fact_id": FACT_ID, "source_id": SOURCE_ID, "source_sha256": EVIDENCE_SHA},
]])
def test_invalid_grounded_facts_rejected(api, store, facts):
    with pytest.raises(api.VerifiedSourceReportError):
        candidate(api, facts=facts)
    assert store.load("r16-disposable-report") is None and store.effect_count() == 0
