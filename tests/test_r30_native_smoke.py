"""R30 independent current-source smoke for provenance and fail-closed gates."""
from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
EXT = ROOT / "reasoners" / "deep_research_ext"
if str(EXT) not in sys.path:
    sys.path.insert(0, str(EXT))


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


runs = _load("r30_research_run", EXT / "research_run.py")
from reasoners.deep_research_ext import verified_pipeline as pipeline
from reasoners.deep_research_ext import final_verifier as verifier


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _candidate(source_sha: str):
    return pipeline.build_grounded_verified_report(
        report_id="r30-report",
        query="strict provenance",
        source_revision=source_sha,
        source_owner="r30-owner",
        source_file_sha256=source_sha,
        facts=[{
            "fact_id": "fact-1",
            "source_id": "verified_pipeline.py",
            "source_sha256": source_sha,
        }],
        payload={"strict": True},
    )


def test_current_source_positive_provenance_and_effect_smoke():
    source_sha = _sha(EXT / "verified_pipeline.py")
    report = _candidate(source_sha)
    assert report.dto_version == "r10"
    assert report.facts[0].source_sha256 == source_sha

    store = pipeline.DurableVerifiedSourceReportStore()
    first = pipeline.persist_grounded_verified_report(
        store, report, owner="r30-owner", effect_id="effect-1"
    )
    second = pipeline.persist_grounded_verified_report(
        store, report, owner="r30-owner", effect_id="effect-1"
    )
    assert first[1:] == (True, True)
    assert second[1:] == (False, False)
    assert store.effect_count() == 1


def test_negative_rejects_malformed_source_fact_hash():
    with pytest.raises(
        pipeline.VerifiedSourceReportError,
        match="lowercase SHA-256",
    ):
        pipeline.GroundedFact("fact-1", "source.py", "not-a-sha")


def test_negative_rejects_stale_revision_and_checkpoint_cas(tmp_path):
    store = runs.ResearchRunStore(str(tmp_path))
    _, run = runs.begin_research_run(
        "r30 query", store=store, source_revision="rev-current", source_owner="r30"
    )
    with pytest.raises(runs.StaleResearchRunError):
        store.load(run.run_id, source_revision="rev-stale")
    with pytest.raises(runs.ResearchRunCheckpointError, match="sequence is stale"):
        runs.checkpoint_research_run(
            store,
            run,
            stage="query",
            source_revision="rev-current",
            source_owner="r30",
            expected_checkpoint_seq=1,
        )


def test_negative_rejects_duplicate_effect_and_wrong_owner():
    source_sha = _sha(EXT / "verified_pipeline.py")
    report = _candidate(source_sha)
    store = pipeline.DurableVerifiedSourceReportStore()
    pipeline.persist_grounded_verified_report(
        store, report, owner="r30-owner", effect_id="effect-1"
    )
    assert store.record_effect(
        "effect-1", report_id=report.report_id, owner="r30-owner", revision=report.revision
    ) is False
    with pytest.raises(pipeline.VerifiedSourceReportError, match="owner"):
        pipeline.persist_grounded_verified_report(
            store, report, owner="wrong-owner", effect_id="effect-2"
        )


@pytest.mark.asyncio
async def test_negative_final_verifier_abstains_closed_without_source_fact():
    async def extractor(**kwargs):
        return verifier.DraftClaimList(
            claims=[verifier.DraftClaim(
                claim_id="D1", text="Unsupported claim", citation_ids=[]
            )]
        )

    state = await verifier.verify_final_document(
        document_package={"executive_summary": "Unsupported claim"},
        research_package={"source_articles": []},
        source_strictness="strict",
        ai_call=None,
        claim_extractor=extractor,
        adjudicator=SimpleNamespace(),
    )
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "material_claim_has_no_citation"
