import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs/architecture/basefive-r14-contracts.json"
SOURCE_PATH = "reasoners/deep_research_ext/verified_pipeline.py"
EXPECTED_SOURCE_SHA = "97cf7e84e8f62c1190d1b5a6c4ac59be6d175e336be8dd1db3b64b9ea81dbd87"
OWNER = "r24-source-owner"
REVISION = "e10580c89eac7a4f6efb50c921ae9107ce8ad8dc"
REPORT_ID = "r24-source-bound-report"
EFFECT_ID = "r24-terminal-effect"
FACT_TEXT = "The fixture records a measured temperature of 20 degrees Celsius."
FACT_SHA = hashlib.sha256(FACT_TEXT.encode("utf-8")).hexdigest()


def _pipeline():
    if str(ROOT) not in sys.path:
        sys.path.insert(0, str(ROOT))
    from reasoners.deep_research_ext import verified_pipeline

    return verified_pipeline


def _payload():
    return {
        "document": FACT_TEXT + " [source-1]",
        "citations": [{"fact_id": "fact-1", "source_id": "source-1"}],
        "evidence": [{
            "fact_id": "fact-1",
            "source_id": "source-1",
            "text": FACT_TEXT,
            "source_sha256": FACT_SHA,
        }],
    }


def _candidate(payload=None, owner=OWNER):
    pipeline = _pipeline()
    return pipeline.build_grounded_verified_report(
        report_id=REPORT_ID,
        query="What temperature was measured?",
        source_revision=REVISION,
        source_owner=owner,
        source_file_sha256=EXPECTED_SOURCE_SHA,
        facts=(pipeline.GroundedFact(
            fact_id="fact-1", source_id="source-1", source_sha256=FACT_SHA,
        ),),
        payload=_payload() if payload is None else payload,
    )


def _persist(store, candidate, owner=OWNER):
    return _pipeline().persist_grounded_verified_report(
        store, candidate, owner=owner, effect_id=EFFECT_ID,
    )


def _resume(store, owner=OWNER, source_sha=EXPECTED_SOURCE_SHA):
    return _pipeline().resume_grounded_verified_report(
        store, REPORT_ID, owner=owner, source_file_sha256=source_sha,
    )


def test_live_source_matches_c4_contract():
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    assert contract["project"] == "af-deep-research"
    assert contract["baseline_commit"] == REVISION
    source = next(item for item in contract["sources"] if item["path"] == SOURCE_PATH)
    actual = hashlib.sha256((ROOT / SOURCE_PATH).read_bytes()).hexdigest()
    assert source["sha256"] == EXPECTED_SOURCE_SHA == actual
    assert contract["versions"]["VerifiedSourceReport"] == "r10"


def test_positive_exact_identity_and_same_process_effect_replay():
    store = _pipeline().DurableVerifiedSourceReportStore()
    payload = _payload()
    candidate = _candidate(payload)
    _persist(store, candidate)
    payload["document"] = "caller mutation"
    receipt = store.load(REPORT_ID)
    assert receipt.source_owner == OWNER
    assert receipt.source_revision == REVISION
    assert receipt.source_file_sha256 == EXPECTED_SOURCE_SHA
    assert receipt.dto_version == "r10"
    assert receipt.source_ids == ("source-1",)
    assert receipt.facts == candidate.facts
    assert receipt.payload == _payload()
    assert len(store._effects) == 1
    _persist(store, candidate)
    assert store.load(REPORT_ID) == receipt
    assert len(store._effects) == 1
    _resume(store)


@pytest.mark.parametrize("mutation", ["foreign-source", "foreign-fact", "unsupported-document"])
def test_untrusted_document_rejected_before_receipt_or_effect(mutation):
    pipeline = _pipeline()
    store = pipeline.DurableVerifiedSourceReportStore()
    payload = copy.deepcopy(_payload())
    if mutation == "foreign-source":
        payload["citations"][0]["source_id"] = "foreign-source"
        payload["document"] = FACT_TEXT + " [foreign-source]"
    elif mutation == "foreign-fact":
        payload["citations"][0]["fact_id"] = "foreign-fact"
    else:
        payload["document"] = "The measured temperature was 900 degrees Celsius. [source-1]"
    try:
        with pytest.raises(pipeline.VerifiedSourceReportError):
            _persist(store, _candidate(payload))
    finally:
        assert store.load(REPORT_ID) is None
        assert len(store._effects) == 0


@pytest.mark.parametrize("foreign_owner", ["candidate", "caller"])
def test_foreign_owner_cannot_create_receipt_or_effect(foreign_owner):
    pipeline = _pipeline()
    store = pipeline.DurableVerifiedSourceReportStore()
    candidate = _candidate(owner="foreign-owner" if foreign_owner == "candidate" else OWNER)
    caller = "foreign-owner" if foreign_owner == "caller" else OWNER
    try:
        with pytest.raises(pipeline.VerifiedSourceReportError):
            _persist(store, candidate, owner=caller)
    finally:
        assert store.load(REPORT_ID) is None
        assert len(store._effects) == 0


@pytest.mark.parametrize("mismatch", ["owner", "source-sha"])
def test_resume_fencing_preserves_canonical_receipt(mismatch):
    pipeline = _pipeline()
    store = pipeline.DurableVerifiedSourceReportStore()
    _persist(store, _candidate())
    before = store.load(REPORT_ID)
    effects_before = set(store._effects)
    with pytest.raises(pipeline.VerifiedSourceReportError):
        _resume(
            store,
            owner="foreign-owner" if mismatch == "owner" else OWNER,
            source_sha="0" * 64 if mismatch == "source-sha" else EXPECTED_SOURCE_SHA,
        )
    assert store.load(REPORT_ID) == before
    assert set(store._effects) == effects_before


def _restart_probe(phase):
    store = _pipeline().DurableVerifiedSourceReportStore()
    if phase == "crash":
        _persist(store, _candidate())
        assert store.load(REPORT_ID).source_owner == OWNER
        assert len(store._effects) == 1
        print("R24_COMMITTED", flush=True)
        os._exit(73)
    assert phase == "resume"
    _resume(store)
    receipt = store.load(REPORT_ID)
    assert receipt.source_owner == OWNER
    assert receipt.source_file_sha256 == EXPECTED_SOURCE_SHA
    assert receipt.payload == _payload()
    assert len(store._effects) == 1
    _persist(store, _candidate())
    assert len(store._effects) == 1
    print("R24_RESUMED_NO_DUPLICATE", flush=True)


def test_real_process_crash_restart_preserves_receipt_and_effect(tmp_path):
    entry = "import runpy,sys; runpy.run_path(sys.argv[1])['_restart_probe'](sys.argv[2])"
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    def run_phase(phase):
        return subprocess.run(
            [sys.executable, "-B", "-c", entry, str(Path(__file__).resolve()), phase],
            cwd=tmp_path,
            env=environment,
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    crashed = run_phase("crash")
    assert crashed.returncode == 73, (crashed.returncode, crashed.stdout, crashed.stderr)
    assert "R24_COMMITTED" in crashed.stdout
    restarted = run_phase("resume")
    assert restarted.returncode == 0, (restarted.returncode, restarted.stdout, restarted.stderr)
    assert "R24_RESUMED_NO_DUPLICATE" in restarted.stdout
