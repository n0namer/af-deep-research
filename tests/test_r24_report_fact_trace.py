"""Strict r24 acceptance probes; product failures must not be xfailed."""

import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from reasoners.deep_research_ext.verified_pipeline import (
    DurableVerifiedSourceReportStore,
    GroundedFact,
    build_grounded_verified_report,
    persist_grounded_verified_report,
    resume_grounded_verified_report,
)


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = json.loads(
    (ROOT / "docs/architecture/basefive-r14-contracts.json").read_text(encoding="utf-8")
)
PIPELINE_PATH = "reasoners/deep_research_ext/verified_pipeline.py"
DECLARED_SOURCE_SHA = next(
    source["sha256"] for source in CONTRACT["sources"] if source["path"] == PIPELINE_PATH
)
OWNER = "r24-research-owner"
REPORT_ID = "r24-owned-report"
EFFECT_ID = "r24-terminal-effect"
SOURCE_TEXT = b"The measured sample contains twelve observations."
SOURCE_SHA = hashlib.sha256(SOURCE_TEXT).hexdigest()


def make_report(*, owner=OWNER, payload=None):
    if payload is None:
        payload = {
            "document": "The measured sample contains twelve observations. [source-1]",
            "claims": [
                {
                    "fact_id": "fact-1",
                    "source_id": "source-1",
                    "text": SOURCE_TEXT.decode("utf-8"),
                }
            ],
        }
    return build_grounded_verified_report(
        report_id=REPORT_ID,
        query="How many observations were measured?",
        source_revision=CONTRACT["baseline_commit"],
        source_owner=owner,
        source_file_sha256=DECLARED_SOURCE_SHA,
        facts=(GroundedFact("fact-1", "source-1", SOURCE_SHA),),
        payload=payload,
        abstained_requirement_ids=("unmeasured-population",),
    )


def persist(store, report, *, owner=OWNER):
    return persist_grounded_verified_report(
        store, report, owner=owner, effect_id=EFFECT_ID
    )


def assert_canonical(store):
    saved = store.load(REPORT_ID)
    assert saved is not None
    assert saved.source_owner == OWNER
    assert saved.source_revision == CONTRACT["baseline_commit"]
    assert saved.source_file_sha256 == DECLARED_SOURCE_SHA
    assert saved.dto_version == "r10"
    assert saved.facts == (GroundedFact("fact-1", "source-1", SOURCE_SHA),)
    assert saved.abstained_requirement_ids == ("unmeasured-population",)
    assert len(store._effects) == 1
    return saved


def test_positive_owned_fact_trace_replay_and_payload_isolation():
    store = DurableVerifiedSourceReportStore()
    report = make_report()
    persist(store, report)
    persist(store, report)
    saved = assert_canonical(store)
    assert saved.source_ids == ("source-1",)
    assert saved.payload["claims"][0]["fact_id"] == saved.facts[0].fact_id
    assert saved.payload["claims"][0]["source_id"] == saved.facts[0].source_id
    saved.payload["claims"][0]["source_id"] = "foreign-source"
    assert store.load(REPORT_ID).payload["claims"][0]["source_id"] == "source-1"
    resume_grounded_verified_report(
        store, REPORT_ID, owner=OWNER, source_file_sha256=DECLARED_SOURCE_SHA
    )
    assert_canonical(store)


@pytest.mark.parametrize("foreign_candidate", [False, True])
def test_negative_foreign_owner_cannot_replace_report_or_repeat_effect(foreign_candidate):
    store = DurableVerifiedSourceReportStore()
    persist(store, make_report())
    original = copy.deepcopy(store.load(REPORT_ID).payload)
    report = make_report(owner="foreign-owner") if foreign_candidate else make_report()
    caller = OWNER if foreign_candidate else "foreign-owner"
    with pytest.raises(ValueError):
        persist(store, report, owner=caller)
    assert_canonical(store)
    assert store.load(REPORT_ID).payload == original


def test_negative_stale_source_resume_cannot_change_receipt_or_effect():
    store = DurableVerifiedSourceReportStore()
    persist(store, make_report())
    with pytest.raises(ValueError):
        resume_grounded_verified_report(
            store, REPORT_ID, owner=OWNER, source_file_sha256="0" * 64
        )
    assert_canonical(store)


@pytest.mark.parametrize("mutation", ["foreign-source", "unowned-fact"])
def test_negative_every_payload_claim_requires_owned_fact(mutation):
    store = DurableVerifiedSourceReportStore()
    payload = copy.deepcopy(make_report().payload)
    if mutation == "foreign-source":
        payload["claims"][0]["source_id"] = "foreign-source"
        payload["document"] = "Twelve observations. [foreign-source]"
    else:
        payload["claims"].append(
            {"fact_id": "unowned-fact", "source_id": "source-1", "text": "Ninety observations."}
        )
        payload["document"] += " Ninety observations. [source-1]"
    with pytest.raises(ValueError):
        persist(store, make_report(payload=payload))
    assert store.load(REPORT_ID) is None
    assert len(store._effects) == 0


def run_child(mode):
    program = (
        "import runpy,sys; "
        "namespace=runpy.run_path(sys.argv[1]); "
        "namespace['restart_probe'](sys.argv[2])"
    )
    return subprocess.run(
        [sys.executable, "-B", "-c", program, str(Path(__file__).resolve()), mode],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
        shell=False,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def restart_probe(mode):
    store = DurableVerifiedSourceReportStore()
    if mode == "crash":
        persist(store, make_report())
        assert_canonical(store)
        print("R24_PERSISTED_BEFORE_CRASH", flush=True)
        os._exit(23)
    assert mode == "resume"
    resume_grounded_verified_report(
        store, REPORT_ID, owner=OWNER, source_file_sha256=DECLARED_SOURCE_SHA
    )
    assert_canonical(store)
    persist(store, make_report())
    assert_canonical(store)
    print("R24_RESUMED_WITH_ONE_EFFECT", flush=True)


def test_real_process_crash_restart_preserves_owned_report_and_single_effect():
    crashed = run_child("crash")
    assert crashed.returncode == 23, (crashed.stdout, crashed.stderr)
    assert "R24_PERSISTED_BEFORE_CRASH" in crashed.stdout
    restarted = run_child("resume")
    assert restarted.returncode == 0, (restarted.stdout, restarted.stderr)
    assert "R24_RESUMED_WITH_ONE_EFFECT" in restarted.stdout
