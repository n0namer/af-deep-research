"""Independent r24 replay/report oracle against the importable Python APIs."""
from __future__ import annotations

import hashlib
import importlib
import inspect
from dataclasses import asdict
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_RUN_SHA = "a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea"
VERIFIED_PIPELINE_SHA = "97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87"
OWNER = "r24-oracle-owner"
REVISION = "source-r24"
SOURCE_SHA = VERIFIED_PIPELINE_SHA
CALL_ID = "provider-call-r24-1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def api():
    return importlib.import_module("reasoners.deep_research_ext.verified_pipeline")


@pytest.fixture(scope="module")
def runs():
    return importlib.import_module("reasoners.deep_research_ext.research_run")


@pytest.fixture()
def report_store(api):
    return api.DurableVerifiedSourceReportStore()


def grounded_report(api, *, revision=1, owner=OWNER, source_sha=SOURCE_SHA,
                    abstentions=()):
    return api.build_grounded_verified_report(
        report_id="r24-report",
        query="Which facts are supported?",
        source_revision=REVISION,
        source_owner=owner,
        source_file_sha256=source_sha,
        facts=[{
            "fact_id": "fact-1",
            "source_id": "source-1",
            "source_sha256": "1" * 64,
        }],
        payload={"document": "Only fact-1 is supported."},
        abstained_requirement_ids=abstentions,
        revision=revision,
    )


def test_source_contract_and_signatures_are_current(api, runs):
    assert sha256(ROOT / "reasoners/deep_research_ext/research_run.py") == RESEARCH_RUN_SHA
    assert sha256(ROOT / "reasoners/deep_research_ext/verified_pipeline.py") == VERIFIED_PIPELINE_SHA
    assert tuple(inspect.signature(runs.checkpoint_research_run).parameters) == (
        "store", "run", "stage", "status", "source_revision", "source_owner",
        "expected_checkpoint_seq", "source_ids", "evidence_ids", "evidence_summary",
        "coverage_state", "open_gap_ids", "conflicts", "budgets", "payload",
    )
    assert api.VerifiedSourceReport.__dataclass_fields__["dto_version"].default == "r10"


def test_positive_report_run_replay_is_source_bound_and_idempotent(api, runs, tmp_path):
    store = api.DurableVerifiedSourceReportStore()
    report = grounded_report(api, abstentions=("missing-fact",))
    saved, changed, effect = api.persist_grounded_verified_report(
        store, report, owner=OWNER, effect_id=CALL_ID
    )
    assert saved == report and changed is True and effect is True

    recovered = api.resume_grounded_verified_report(
        store, report.report_id, owner=OWNER, source_file_sha256=SOURCE_SHA
    )
    assert recovered == report
    duplicate, changed, effect = api.persist_grounded_verified_report(
        store, recovered, owner=OWNER, effect_id=CALL_ID
    )
    assert duplicate == report and changed is False and effect is False
    assert store.effect_count() == 1

    run_store = runs.ResearchRunStore(str(tmp_path))
    run_store, run = runs.begin_research_run(
        "Which facts are supported?", store=run_store,
        source_revision=REVISION, source_owner=OWNER,
    )
    run = runs.checkpoint_research_run(
        run_store, run, stage="research_package_ready",
        source_revision=REVISION, source_owner=OWNER,
        payload={"report": asdict(report), "provider_call_ids": [CALL_ID],
                 "partial_abstention": True},
    )
    resumed, receipt = runs.resume_research_run(
        run_store, run.run_id, source_revision=REVISION, source_owner=OWNER
    )
    assert resumed.checkpoint_seq == 1
    assert receipt["provider_call_ids"] == (CALL_ID,)
    assert receipt["partial_abstention"] is True
    assert receipt["report"]["abstained_requirement_ids"] == ("missing-fact",)


def test_foreign_owner_fails_closed_without_mutation(api):
    store = api.DurableVerifiedSourceReportStore()
    report = grounded_report(api)
    api.persist_grounded_verified_report(store, report, owner=OWNER)
    with pytest.raises(api.VerifiedSourceReportError, match="owner"):
        api.persist_grounded_verified_report(
            store, grounded_report(api, revision=2), owner="foreign-owner"
        )
    assert store.load(report.report_id) == report
    assert store.effect_count() == 0


def test_stale_source_sha_fails_closed_without_fabrication(api):
    store = api.DurableVerifiedSourceReportStore()
    report = grounded_report(api, abstentions=("missing-fact",))
    api.persist_grounded_verified_report(store, report, owner=OWNER)
    with pytest.raises(api.VerifiedSourceReportError, match="SHA"):
        api.resume_grounded_verified_report(
            store, report.report_id, owner=OWNER, source_file_sha256="0" * 64
        )
    assert store.load(report.report_id) == report
    assert store.effect_count() == 0
    assert "missing-fact" in report.abstained_requirement_ids


def test_restart_and_duplicate_provider_call_are_rejected_or_deduped(api, runs, tmp_path):
    store = api.DurableVerifiedSourceReportStore()
    report = grounded_report(api)
    api.persist_grounded_verified_report(store, report, owner=OWNER, effect_id=CALL_ID)

    restarted = api.DurableVerifiedSourceReportStore()
    with pytest.raises(api.VerifiedSourceReportError, match="not found"):
        api.resume_grounded_verified_report(
            restarted, report.report_id, owner=OWNER, source_file_sha256=SOURCE_SHA
        )

    run_store = runs.ResearchRunStore(str(tmp_path))
    _, run = runs.begin_research_run(
        "replay", store=run_store, source_revision=REVISION, source_owner=OWNER
    )
    checkpoint = runs.checkpoint_research_run(
        run_store, run, stage="ledger", source_revision=REVISION,
        source_owner=OWNER, payload={"provider_call_ids": [CALL_ID, CALL_ID]}
    )
    assert runs.recorded_provider_call_ids(checkpoint) == (CALL_ID,)
    assert runs.provider_call_already_recorded(checkpoint, CALL_ID)


def test_missing_fact_is_explicit_abstention_not_fabricated_claim(api):
    report = grounded_report(api, abstentions=("requirement-missing",))
    assert report.abstained_requirement_ids == ("requirement-missing",)
    assert "requirement-missing" not in report.payload["document"]
