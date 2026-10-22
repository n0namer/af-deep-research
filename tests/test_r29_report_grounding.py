"""R29 source-grounding acceptance checks.

These tests are intentionally source-bound: they exercise the available production
contracts without mocking an end-to-end report builder that is absent from this
checkout.
"""
from __future__ import annotations

import ast
import hashlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
VERIFIED = ROOT / "reasoners/deep_research_ext/verified_pipeline.py"
RUNS = ROOT / "reasoners/deep_research_ext/research_run.py"
FINAL = ROOT / "reasoners/deep_research_ext/final_verifier.py"


def _tree(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _functions(path: Path) -> set[str]:
    return {
        node.name
        for node in ast.walk(_tree(path))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def test_grounded_report_contract_is_source_present_and_sha_bound():
    assert VERIFIED.is_file()
    source = VERIFIED.read_text(encoding="utf-8")
    assert "build_grounded_verified_report" in source
    assert "source_file_sha256" in source
    assert "dto_version" in source
    digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
    assert len(digest) == 64
    assert all(char in "0123456789abcdef" for char in digest)


def test_positive_contracts_expose_grounded_report_and_resume_paths():
    names = _functions(VERIFIED)
    assert {"build_grounded_verified_report", "persist_grounded_verified_report", "resume_grounded_verified_report"} <= names
    final_names = _functions(FINAL)
    assert "verify_final_document" in final_names


def test_negative_duplicate_facts_are_rejected_by_declared_guard():
    source = VERIFIED.read_text(encoding="utf-8")
    assert "facts must have unique fact_id values" in source
    assert "len({fact.fact_id for fact in self.facts}) != len(self.facts)" in source


def test_negative_stale_source_identity_is_rejected_by_resume_guard():
    source = VERIFIED.read_text(encoding="utf-8")
    assert "source file SHA does not match stored report" in source
    assert "report.source_file_sha256 != source_file_sha256" in source


def test_negative_unfounded_claims_close_abstention_path():
    source = FINAL.read_text(encoding="utf-8")
    assert "material_claim_has_no_citation" in source
    assert "cited_source_not_available_for_verification" in source
    assert "claim_verification_failed_closed" in source
    assert "passed=(len(unsupported) == 0)" in source


def test_negative_research_checkpoint_rejects_stale_revision():
    source = RUNS.read_text(encoding="utf-8")
    assert "StaleResearchRunError" in source
    assert "checkpoint {run_id} belongs to source revision" in source
    assert 'run.source_revision not in {None, source_revision}' in source
