from __future__ import annotations

import hashlib
import importlib.util
import inspect
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
RESEARCH_RUN = ROOT / 'reasoners/deep_research_ext/research_run.py'
VERIFIED_PIPELINE = ROOT / 'reasoners/deep_research_ext/verified_pipeline.py'

def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

research_run = __import__('reasoners.deep_research_ext.research_run', fromlist=['*'])
verified_pipeline = __import__('reasoners.deep_research_ext.verified_pipeline', fromlist=['*'])

def sha256(path): return hashlib.sha256(path.read_bytes()).hexdigest()

def test_current_source_sha_and_archsteer_signatures_are_explicit():
    assert sha256(RESEARCH_RUN) == '87c193a386be13daa2b89dceac6b749a87ae9b47efd84b18bd598017c6e9e8c3'
    assert sha256(VERIFIED_PIPELINE) == '97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87'
    assert inspect.signature(research_run.begin_research_run).parameters['source_revision'].kind is inspect.Parameter.KEYWORD_ONLY
    assert inspect.signature(research_run.checkpoint_research_run).parameters['expected_checkpoint_seq'].kind is inspect.Parameter.KEYWORD_ONLY
    assert inspect.signature(verified_pipeline.build_grounded_verified_report).parameters['source_file_sha256'].kind is inspect.Parameter.KEYWORD_ONLY
    assert inspect.signature(verified_pipeline.resume_grounded_verified_report).parameters['source_file_sha256'].kind is inspect.Parameter.KEYWORD_ONLY

def test_grounded_report_accepts_current_sha_and_r10_dto():
    digest = sha256(VERIFIED_PIPELINE)
    report = verified_pipeline.build_grounded_verified_report(report_id='r29-positive', query='graphify archsteer C4', source_revision=digest, source_owner='r29', source_file_sha256=digest, facts=[{'fact_id':'f1','source_id':'verified_pipeline.py','source_sha256':digest}], payload={'c4':'component'})
    assert report.dto_version == 'r10'
    assert report.source_file_sha256 == digest

def test_negative_rejects_malformed_source_sha():
    with pytest.raises(verified_pipeline.VerifiedSourceReportError, match='lowercase SHA-256'):
        verified_pipeline.GroundedFact('f1','source.py','not-a-sha')

def test_negative_rejects_duplicate_fact_ids():
    digest = sha256(VERIFIED_PIPELINE)
    with pytest.raises(verified_pipeline.VerifiedSourceReportError, match='unique fact_id'):
        verified_pipeline.build_grounded_verified_report(report_id='r29-duplicate', query='graphify', source_revision=digest, source_owner='r29', source_file_sha256=digest, facts=[{'fact_id':'same','source_id':'source.py','source_sha256':digest},{'fact_id':'same','source_id':'source.py','source_sha256':digest}], payload={})

def test_negative_rejects_stale_checkpoint_revision(tmp_path):
    store = research_run.ResearchRunStore(str(tmp_path))
    _, run = research_run.begin_research_run('graphify', store=store, source_revision='sha-current', source_owner='r29')
    with pytest.raises(research_run.StaleResearchRunError):
        research_run.checkpoint_research_run(store, run, stage='query', source_revision='sha-stale', source_owner='r29', expected_checkpoint_seq=0)

def test_negative_rejects_unsupported_dto_version():
    digest = sha256(VERIFIED_PIPELINE)
    with pytest.raises(verified_pipeline.VerifiedSourceReportError, match='unsupported DTO version'):
        verified_pipeline.VerifiedSourceReport(report_id='r29-bad-version', query='graphify', source_ids=('source.py',), revision=1, payload={}, source_revision=digest, source_owner='r29', source_file_sha256=digest, facts=(verified_pipeline.GroundedFact('f1','source.py',digest),), dto_version='r9')
