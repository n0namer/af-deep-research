"""R29 six-domain primary-source and hallucination-negative evaluation."""
from __future__ import annotations
import importlib
from pathlib import Path
import pytest
ROOT = Path(__file__).resolve().parents[1]
pipeline = importlib.import_module("reasoners.deep_research_ext.verified_pipeline")
runs = importlib.import_module("reasoners.deep_research_ext.research_run")
def _facts():
    return [pipeline.GroundedFact(fact_id=f"domain-{i}", source_id=f"source-{i}", source_sha256="a"*64) for i in range(1, 7)]
def test_six_domain_primary_source_report_is_grounded_and_versioned():
    report = pipeline.build_grounded_verified_report(report_id="r29-six-domain", query="six-domain primary-source evaluation", source_revision="e10580c89eac7a4f6efb50c921ae9107ce8ad8dc", source_owner="r29-primary-source-eval", source_file_sha256="b"*64, facts=_facts(), payload={"domains": 6, "policy": "primary-source"})
    assert report.dto_version == "r10"
    assert len(report.facts) == 6
    assert report.source_ids == tuple(f"source-{i}" for i in range(1, 7))
@pytest.mark.parametrize(("label", "mutator", "expected"), [
    ("malformed source hash", lambda kw: {**kw, "source_file_sha256": "not-a-sha"}, "source_file_sha256 must be a lowercase SHA-256 hex digest"),
    ("duplicate fact identity", lambda kw: {**kw, "facts": [kw["facts"][0], kw["facts"][0]]}, "facts must have unique fact_id values"),
])
def test_hallucination_negative_inputs_are_rejected(label, mutator, expected):
    kw = dict(report_id="negative-"+label, query="negative", source_revision="rev-r29", source_owner="owner-r29", source_file_sha256="b"*64, facts=_facts(), payload={})
    with pytest.raises(pipeline.VerifiedSourceReportError, match=expected):
        pipeline.build_grounded_verified_report(**mutator(kw))
def test_unsupported_dto_version_is_rejected():
    with pytest.raises(pipeline.VerifiedSourceReportError, match="unsupported DTO version"):
        pipeline.VerifiedSourceReport(report_id="bad", query="q", source_ids=("s",), revision=1, payload={}, dto_version="r11")
def test_checkpoint_rejects_stale_source_revision_without_false_resume(tmp_path):
    store = runs.ResearchRunStore(root=str(tmp_path))
    _, run = runs.begin_research_run("primary-source query", store=store, source_revision="rev-current", source_owner="owner-r29")
    store.save(run)
    with pytest.raises(runs.StaleResearchRunError):
        store.load(run.run_id, source_revision="rev-stale")
