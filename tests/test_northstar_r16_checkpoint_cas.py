from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import os
import sys
from dataclasses import fields, replace
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reasoners/deep_research_ext/research_run.py"
SOURCE_SHA256 = "a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea"
CONTRACT = ROOT / "docs/architecture/basefive-r14-contracts.json"


@pytest.fixture
def api(monkeypatch):
    module_name = "_northstar_r16_research_run"
    spec = importlib.util.spec_from_file_location(module_name, SOURCE)
    module = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, module_name, module)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "current_agentfield_identity", lambda: (None, None))
    return module


@pytest.fixture
def started(api, tmp_path):
    store = api.ResearchRunStore(str(tmp_path / "checkpoints"))
    return api.begin_research_run(
        "offline checkpoint oracle", store=store,
        source_revision=SOURCE_SHA256, source_owner="owner-a",
    )


def effect_ids(path):
    if not path.exists():
        return []
    return [json.loads(line)["call_id"] for line in path.read_text(encoding="utf-8").splitlines()]


def offline_provider_once(api, store, snapshot, effect_path, call_id, *, cancelled=False):
    current, receipt = api.resume_research_run(
        store, snapshot.run_id,
        source_revision=snapshot.source_revision, source_owner=snapshot.source_owner,
    )
    if current.checkpoint_seq != snapshot.checkpoint_seq:
        raise api.ResearchRunCheckpointError("test driver generation is stale")
    if cancelled:
        raise api.ResearchRunCheckpointError("test driver cancelled")
    if call_id in receipt["provider_call_ids"] or receipt["terminal"]:
        return current
    with effect_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"call_id": call_id}) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return api.checkpoint_research_run(
        store, current, stage="retrieval", expected_checkpoint_seq=current.checkpoint_seq,
        payload={"provider_call_ids": [call_id]},
    )


def test_source_sha_dto_and_public_signature_pin(api):
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    declared = next(item for item in contract["sources"] if item["path"] == SOURCE.relative_to(ROOT).as_posix())
    assert digest == SOURCE_SHA256 == declared["sha256"]
    assert api.SCHEMA_VERSION == contract["versions"]["ResearchRun"] == "0.1"
    declared_dto = next(item for item in contract["dtos"] if item["name"] == "ResearchRun")
    assert [item.name for item in fields(api.ResearchRun)] == declared_dto["fields"]
    expected = {
        "begin_research_run": ("query", "store", "source_revision", "source_owner"),
        "checkpoint_research_run": (
            "store", "run", "stage", "status", "source_revision", "source_owner",
            "expected_checkpoint_seq", "source_ids", "evidence_ids", "evidence_summary",
            "coverage_state", "open_gap_ids", "conflicts", "budgets", "payload",
        ),
        "resume_research_run": ("store", "run_id", "source_revision", "source_owner"),
    }
    for name, parameters in expected.items():
        signature = inspect.signature(getattr(api, name))
        assert tuple(signature.parameters) == parameters
        positional_count = 1 if name == "begin_research_run" else 2
        for index, parameter in enumerate(signature.parameters.values()):
            kind = inspect.Parameter.POSITIONAL_OR_KEYWORD if index < positional_count else inspect.Parameter.KEYWORD_ONLY
            assert parameter.kind == kind
            if index >= positional_count:
                default = inspect.Parameter.empty if parameter.name == "stage" else None
                assert parameter.default == default


def test_positive_effect_and_receipt_survive_store_restart(api, started, tmp_path):
    store, run = started
    effect_path = tmp_path / "effects.jsonl"
    updated = offline_provider_once(api, store, run, effect_path, "provider-1")
    assert effect_ids(effect_path) == ["provider-1"]
    persisted = json.loads(store.path_for(run.run_id).read_text(encoding="utf-8"))
    assert persisted["checkpoint_seq"] == updated.checkpoint_seq == 1
    assert persisted["payload"]["provider_call_ids"] == ["provider-1"]
    restarted_store = api.ResearchRunStore(str(store.root))
    resumed, receipt = api.resume_research_run(
        restarted_store, run.run_id, source_revision=SOURCE_SHA256, source_owner="owner-a",
    )
    assert receipt["provider_call_ids"] == ("provider-1",)
    checkpoint_bytes = store.path_for(run.run_id).read_bytes()
    replayed = offline_provider_once(api, restarted_store, resumed, effect_path, "provider-1")
    assert replayed == resumed
    assert effect_ids(effect_path) == ["provider-1"]
    assert store.path_for(run.run_id).read_bytes() == checkpoint_bytes


def test_provider_and_evidence_ids_are_monotonic_unique(api, started):
    store, run = started
    first = api.checkpoint_research_run(
        store, run, stage="retrieval", evidence_ids=("evidence-1", "evidence-1"),
        payload={"provider_call_ids": ["call-1", "call-1", ""], "evidence_ids": ["evidence-2"]},
    )
    second = api.checkpoint_research_run(
        store, first, stage="ledger", evidence_ids=("evidence-2", "evidence-3"),
        payload={"provider_call_ids": ["call-2", "call-1"], "evidence_ids": ["evidence-3"]},
    )
    third = api.checkpoint_research_run(store, second, stage="coverage", payload={"other": True})
    loaded = api.ResearchRunStore(str(store.root)).load(run.run_id)
    assert api.recorded_provider_call_ids(loaded) == ("call-1", "call-2")
    assert api.recorded_evidence_ids(loaded) == ("evidence-1", "evidence-2", "evidence-3")
    assert api.provider_call_already_recorded(loaded, "call-1")
    assert not api.provider_call_already_recorded(loaded, "missing")
    assert third.checkpoint_seq == 3
    assert loaded.stage_history == ("started", "retrieval", "ledger", "coverage")


@pytest.mark.parametrize("violation", ["generation", "expected_generation", "owner", "revision", "stage"])
def test_invalid_writer_does_not_change_durable_checkpoint(api, started, violation):
    store, run = started
    current = api.checkpoint_research_run(store, run, stage="retrieval", payload={"provider_call_ids": ["accepted"]})
    before = store.path_for(run.run_id).read_bytes()
    candidate = current
    options = {"stage": "ledger"}
    if violation == "generation":
        candidate = run
    elif violation == "expected_generation":
        options["expected_checkpoint_seq"] = run.checkpoint_seq
    elif violation == "owner":
        options["source_owner"] = "owner-b"
    elif violation == "revision":
        options["source_revision"] = "foreign-revision"
    else:
        options["stage"] = "unknown-stage"
    with pytest.raises(api.ResearchRunCheckpointError):
        api.checkpoint_research_run(store, candidate, **options)
    assert store.path_for(run.run_id).read_bytes() == before
    assert api.recorded_provider_call_ids(store.load(run.run_id)) == ("accepted",)


@pytest.mark.parametrize("violation", ["cancel", "owner", "revision", "generation"])
def test_offline_driver_negative_paths_have_no_effect(api, started, tmp_path, violation):
    store, run = started
    candidate = run
    if violation == "owner":
        candidate = replace(run, source_owner="owner-b")
    elif violation == "revision":
        candidate = replace(run, source_revision="foreign-revision")
    elif violation == "generation":
        api.checkpoint_research_run(store, run, stage="query")
    before = store.path_for(run.run_id).read_bytes()
    effect_path = tmp_path / "effects.jsonl"
    with pytest.raises(api.ResearchRunCheckpointError):
        offline_provider_once(api, store, candidate, effect_path, "forbidden", cancelled=violation == "cancel")
    assert effect_ids(effect_path) == []
    assert store.path_for(run.run_id).read_bytes() == before


def test_completed_resume_does_not_repeat_offline_effect(api, started, tmp_path):
    store, run = started
    completed = api.checkpoint_research_run(
        store, run, stage="completed", status="completed", open_gap_ids=("gap-1",),
        payload={"report": {"result": "offline"}, "partial_abstention": True},
    )
    resumed, receipt = api.resume_research_run(api.ResearchRunStore(str(store.root)), run.run_id)
    assert receipt["terminal"] is True
    assert receipt["next_stage"] == "done"
    assert receipt["missing_gap_ids"] == ()
    assert receipt["report"] == {"result": "offline"}
    assert receipt["partial_abstention"] is True
    effect_path = tmp_path / "effects.jsonl"
    assert offline_provider_once(api, store, resumed, effect_path, "new-call") == completed
    assert effect_ids(effect_path) == []


def test_replay_inherits_provider_receipts(api, started, monkeypatch, tmp_path):
    store, run = started
    first = api.checkpoint_research_run(
        store, run, stage="research_package_ready",
        payload={"provider_call_ids": ["inherited-call"], "research_package": {"offline": True}},
    )
    monkeypatch.setattr(api, "current_agentfield_identity", lambda: ("replay-r16", first.run_id))
    replay_store, replay = api.begin_research_run(
        first.query, store=api.ResearchRunStore(str(store.root)),
        source_revision=SOURCE_SHA256, source_owner="owner-a",
    )
    assert replay.replay_source_run_id == first.run_id
    assert replay.stage == "research_package_ready"
    assert replay.checkpoint_seq == 0
    assert api.recorded_provider_call_ids(replay) == ("inherited-call",)
    effect_path = tmp_path / "effects.jsonl"
    assert offline_provider_once(api, replay_store, replay, effect_path, "inherited-call") == replay
    assert effect_ids(effect_path) == []


def test_interleaved_generation_compare_and_swap_rejects_stale_writer(api, started):
    store, run = started
    winner = api.checkpoint_research_run(store, run, stage="query")
    winner_bytes = None

    class InterleavingStore(api.ResearchRunStore):
        def load(self, run_id, *, source_revision=None):
            nonlocal winner, winner_bytes
            observed = super().load(run_id, source_revision=source_revision)
            winner = api.checkpoint_research_run(
                store, observed, stage="retrieval", payload={"provider_call_ids": ["winner-call"]},
            )
            winner_bytes = store.path_for(run_id).read_bytes()
            return observed

    interleaved = InterleavingStore(str(store.root))
    with pytest.raises(api.ResearchRunCheckpointError):
        api.checkpoint_research_run(
            interleaved, winner, stage="ledger", expected_checkpoint_seq=winner.checkpoint_seq,
            payload={"provider_call_ids": ["stale-call"]},
        )
    assert store.path_for(run.run_id).read_bytes() == winner_bytes
    assert api.recorded_provider_call_ids(store.load(run.run_id)) == ("winner-call",)


def test_crash_after_effect_before_receipt_does_not_duplicate_on_restart(api, started, tmp_path, monkeypatch):
    store, run = started
    effect_path = tmp_path / "effects.jsonl"
    before = store.path_for(run.run_id).read_bytes()

    def interrupted_save(candidate):
        raise OSError("injected crash before durable provider receipt")

    monkeypatch.setattr(store, "save", interrupted_save)
    with pytest.raises(OSError, match="injected crash"):
        offline_provider_once(api, store, run, effect_path, "crash-call")
    assert effect_ids(effect_path) == ["crash-call"]
    assert store.path_for(run.run_id).read_bytes() == before
    restarted = api.ResearchRunStore(str(store.root))
    resumed, receipt = api.resume_research_run(restarted, run.run_id)
    assert receipt["provider_call_ids"] == ()
    offline_provider_once(api, restarted, resumed, effect_path, "crash-call")
    assert effect_ids(effect_path) == ["crash-call"]
