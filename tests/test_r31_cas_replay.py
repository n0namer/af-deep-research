from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reasoners" / "deep_research_ext" / "research_run.py"
SOURCE_SHA256 = "e36c3727e2045afc02814d46397c17f2aa8d6ad8cca307a7698a3d2d9c9a6c72"
RUN_ID = "r31-cas-replay"
OWNER = "r31-owner"
REVISION = "r31-source"


def _native():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    name = "r31_native_research_run"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, SOURCE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        assert spec.loader is not None
        spec.loader.exec_module(module)
    return sys.modules[name]


def _seed(module, root):
    store = module.ResearchRunStore(root)
    run = module.ResearchRun(
        run_id=RUN_ID,
        query="restart-safe CAS replay",
        stage="started",
        checkpoint_seq=0,
        status="running",
        created_at=1.0,
        updated_at=1.0,
        source_revision=REVISION,
        source_owner=OWNER,
    )
    store.save(run)
    return store, run


def _checkpoint(module, store, run, sequence, label, *, owner=OWNER, revision=REVISION):
    return module.checkpoint_research_run(
        store, run, stage="retrieval",
        expected_checkpoint_seq=sequence,
        source_revision=revision, source_owner=owner,
        evidence_ids=(label,),
        payload={"provider_call_ids": ["effect-1"], "effect_receipt": label},
    )


def _worker(root, mode):
    module = _native()
    store = module.ResearchRunStore(root)
    run, _ = module.resume_research_run(
        store, RUN_ID, source_revision=REVISION, source_owner=OWNER,
    )
    if mode == "commit":
        updated = _checkpoint(module, store, run, 0, "pre-restart")
        print(json.dumps({"outcome": "committed", "seq": updated.checkpoint_seq}), flush=True)
        return
    if mode == "replay":
        try:
            _checkpoint(module, store, run, 0, "replay")
        except module.ResearchRunCheckpointError as error:
            print(json.dumps({"outcome": "rejected", "error": type(error).__name__}), flush=True)
            return
    raise AssertionError(mode)


def _run_worker(root, mode):
    completed = subprocess.run(
        [sys.executable, str(Path(__file__).resolve()), "--r31-worker", str(root), mode],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    return json.loads(completed.stdout.strip())


def test_positive_native_restart_rejects_replay_and_deduplicates_effect(tmp_path):
    module = _native()
    root = tmp_path / "run-store"
    store, _ = _seed(module, root)
    assert _run_worker(root, "commit") == {"outcome": "committed", "seq": 1}
    replay = _run_worker(root, "replay")
    assert replay["outcome"] == "rejected"
    durable = store.load(RUN_ID, source_revision=REVISION)
    assert durable.checkpoint_seq == 1
    assert durable.evidence_ids == ("pre-restart",)
    assert module.recorded_provider_call_ids(durable) == ("effect-1",)


def test_negative_stale_sequence_cannot_mutate_checkpoint(tmp_path):
    module = _native()
    store, run = _seed(module, tmp_path)
    winner = _checkpoint(module, store, run, 0, "winner")
    before = store.path_for(RUN_ID).read_bytes()
    with pytest.raises(module.ResearchRunCheckpointError, match="sequence is stale"):
        _checkpoint(module, store, run, 0, "stale")
    assert store.path_for(RUN_ID).read_bytes() == before
    assert store.load(RUN_ID, source_revision=REVISION) == winner


def test_negative_foreign_owner_and_revision_are_fenced(tmp_path):
    module = _native()
    store, run = _seed(module, tmp_path)
    with pytest.raises(module.ResearchRunCheckpointError, match="source owner"):
        _checkpoint(module, store, run, 0, "foreign", owner="intruder")
    with pytest.raises(module.StaleResearchRunError, match="source revision"):
        _checkpoint(module, store, run, 0, "stale-revision", revision="old-source")
    assert store.load(RUN_ID, source_revision=REVISION).checkpoint_seq == 0


def test_negative_duplicate_provider_effect_ids_are_normalized(tmp_path):
    module = _native()
    store, run = _seed(module, tmp_path)
    updated = _checkpoint(module, store, run, 0, "first")
    replayed = _checkpoint(module, store, updated, 1, "second")
    assert module.recorded_provider_call_ids(replayed) == ("effect-1",)
    assert replayed.payload["provider_call_ids"] == ["effect-1"]


if __name__ == "__main__":
    assert sys.argv[1] == "--r31-worker"
    _worker(sys.argv[2], sys.argv[3])
