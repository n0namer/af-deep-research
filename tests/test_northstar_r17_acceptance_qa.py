"""Independent R17 contract probes; no native-runtime acceptance is inferred."""
import hashlib
import importlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RUN_SOURCE = ROOT / "reasoners/deep_research_ext/research_run.py"
REPORT_SOURCE = ROOT / "reasoners/deep_research_ext/verified_pipeline.py"
RUN_SHA = "a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea"
REPORT_SHA = "97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87"


@pytest.fixture
def runs(monkeypatch):
    name = "_r17_independent_research_run"
    spec = importlib.util.spec_from_file_location(name, RUN_SOURCE)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, name, module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "current_agentfield_identity", lambda: (None, None))
    return module


@pytest.fixture
def reports():
    return importlib.import_module("reasoners.deep_research_ext.verified_pipeline")


def report(api, document="Paris. [source:fact]"):
    evidence = b"Paris."
    return api.build_grounded_verified_report(
        report_id="r17-independent", query="Capital?", source_revision=REPORT_SHA,
        source_owner="r17-owner", source_file_sha256=REPORT_SHA,
        facts=[{"fact_id": "fact", "source_id": "source",
                "source_sha256": hashlib.sha256(evidence).hexdigest()}],
        payload={"document": document, "evidence": [{
            "fact_id": "fact", "source_id": "source",
            "source_sha256": hashlib.sha256(evidence).hexdigest(), "excerpt": "Paris.",
        }]},
    )


def test_source_hashes_and_c4_literal_anchors():
    contract = json.loads((ROOT / "docs/architecture/basefive-r14-contracts.json").read_text())
    for path, expected in ((RUN_SOURCE, RUN_SHA), (REPORT_SOURCE, REPORT_SHA)):
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
        declared = next(item for item in contract["sources"]
                        if item["path"] == path.relative_to(ROOT).as_posix())
        assert declared["sha256"] == expected
    for diagram in contract["diagrams"]:
        for item in diagram.get("nodes", []) + diagram.get("edges", []):
            assert item["source"] in {
                RUN_SOURCE.relative_to(ROOT).as_posix(),
                REPORT_SOURCE.relative_to(ROOT).as_posix(),
            }
            assert item["anchor"] in (ROOT / item["source"]).read_text()


def test_checkpoint_positive_restart_and_two_negative_writers(runs, tmp_path):
    store, initial = runs.begin_research_run(
        "independent", store=runs.ResearchRunStore(str(tmp_path)),
        source_revision=RUN_SHA, source_owner="r17-owner",
    )
    current = runs.checkpoint_research_run(
        store, initial, stage="retrieval", expected_checkpoint_seq=0,
        payload={"provider_call_ids": ["once", "once"]},
    )
    restarted = runs.ResearchRunStore(str(tmp_path))
    resumed, receipt = runs.resume_research_run(
        restarted, initial.run_id, source_revision=RUN_SHA, source_owner="r17-owner",
    )
    assert resumed == current and receipt["provider_call_ids"] == ("once",)
    before = restarted.path_for(initial.run_id).read_bytes()
    for snapshot, options in (
        (initial, {}),
        (current, {"source_owner": "foreign"}),
    ):
        with pytest.raises(runs.ResearchRunCheckpointError):
            runs.checkpoint_research_run(restarted, snapshot, stage="ledger", **options)
        assert restarted.path_for(initial.run_id).read_bytes() == before


def test_report_positive_and_duplicate_effect(reports):
    store = reports.DurableVerifiedSourceReportStore()
    candidate = report(reports)
    _, changed, effect = reports.persist_grounded_verified_report(
        store, candidate, owner="r17-owner", effect_id="r17-effect",
    )
    assert changed is True and effect is True
    _, changed, effect = reports.persist_grounded_verified_report(
        store, candidate, owner="r17-owner", effect_id="r17-effect",
    )
    assert changed is False and effect is False and store.effect_count() == 1


@pytest.mark.parametrize("document", ["Unsupported population. [source:fact]", "Paris. [foreign:fact]"])
def test_untrusted_citation_rejected_before_effect(reports, document):
    store = reports.DurableVerifiedSourceReportStore()
    with pytest.raises(reports.VerifiedSourceReportError):
        candidate = report(reports, document)
        reports.persist_grounded_verified_report(
            store, candidate, owner="r17-owner", effect_id="forbidden",
        )
    assert store.load("r17-independent") is None and store.effect_count() == 0


def test_report_receipt_survives_recreated_store(reports):
    original = reports.DurableVerifiedSourceReportStore()
    candidate = report(reports)
    reports.persist_grounded_verified_report(
        original, candidate, owner="r17-owner", effect_id="r17-effect",
    )
    restarted = reports.DurableVerifiedSourceReportStore()
    resumed = reports.resume_grounded_verified_report(
        restarted, candidate.report_id, owner="r17-owner", source_file_sha256=REPORT_SHA,
    )
    assert resumed == candidate
    _, changed, effect = reports.persist_grounded_verified_report(
        restarted, resumed, owner="r17-owner", effect_id="r17-effect",
    )
    assert changed is False and effect is False and restarted.effect_count() == 1


def test_interleaved_checkpoint_cas_preserves_winner(runs, tmp_path):
    store, initial = runs.begin_research_run(
        "independent CAS", store=runs.ResearchRunStore(str(tmp_path)),
        source_revision=RUN_SHA, source_owner="r17-owner",
    )
    before_winner = runs.checkpoint_research_run(store, initial, stage="query")
    winner_bytes = []

    class InterleavingStore(runs.ResearchRunStore):
        def load(self, run_id, *, source_revision=None):
            observed = super().load(run_id, source_revision=source_revision)
            runs.checkpoint_research_run(
                store, observed, stage="retrieval", payload={"provider_call_ids": ["winner"]},
            )
            winner_bytes.append(store.path_for(run_id).read_bytes())
            return observed

    with pytest.raises(runs.ResearchRunCheckpointError):
        runs.checkpoint_research_run(
            InterleavingStore(str(tmp_path)), before_winner, stage="ledger",
            expected_checkpoint_seq=before_winner.checkpoint_seq,
            payload={"provider_call_ids": ["loser"]},
        )
    assert store.path_for(initial.run_id).read_bytes() == winner_bytes[0]
