import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reasoners/deep_research_ext/research_run.py"
SOURCE_SHA256 = "a4caa1f2d1ea2f4d70d3039fa3b2eac8371dde530ee0ebe5ec9537a602ac36ea"
OWNER = "r24-owner"
REVISION = "r24-frozen-source"
RUN_ID = "r24-cas-run"


def _native():
    assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == SOURCE_SHA256
    name = "r24_native_research_run"
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, SOURCE)
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def _store(module, root):
    return module.ResearchRunStore(Path(root))


def _seed(module, root):
    store = _store(module, root)
    run = module.ResearchRun(
        run_id=RUN_ID,
        query="Independent offline CAS oracle",
        stage="query",
        checkpoint_seq=0,
        status="running",
        created_at=1.0,
        updated_at=1.0,
        source_revision=REVISION,
        source_owner=OWNER,
        evidence_ids=("seed-evidence",),
        payload={"provider_call_ids": ["recorded-effect"], "report": "seed"},
    )
    store.save(run)
    return store, run


def _checkpoint(module, store, run, sequence, label, owner=OWNER):
    return module.checkpoint_research_run(
        store,
        run,
        stage="retrieval",
        expected_checkpoint_seq=sequence,
        source_revision=REVISION,
        source_owner=owner,
        evidence_ids=(label,),
        payload={"provider_call_ids": ["recorded-effect"], "report": label},
    )


def _load(module, root):
    return _store(module, root).load(RUN_ID, source_revision=REVISION)


def _snapshot(root):
    return {path.name: path.read_bytes() for path in Path(root).glob("*.json")}


def _wait(path, process=None, timeout=10):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if path.exists():
            return
        if process is not None and process.poll() is not None:
            stdout, stderr = process.communicate()
            pytest.fail(f"Child exited before {path.name}: {process.returncode}; {stdout}; {stderr}")
        time.sleep(0.01)
    raise AssertionError(f"Timed out waiting for {path.name}")


def _start(root, control, label, sequence, mode="checkpoint"):
    return subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "--r24-worker",
         str(root), str(control), label, str(sequence), mode],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
    )


def _finish(process):
    stdout, stderr = process.communicate(timeout=15)
    assert process.returncode == 0, (process.returncode, stdout, stderr)
    receipts = [line[4:] for line in stdout.splitlines() if line.startswith("R24:")]
    assert len(receipts) == 1, (stdout, stderr)
    return json.loads(receipts[0])


def _stop(process):
    if process.poll() is None:
        process.kill()
    process.communicate(timeout=10)


def _worker(root, control, label, sequence, mode):
    module = _native()
    store = _store(module, root)
    run, plan = module.resume_research_run(
        store, RUN_ID, source_revision=REVISION, source_owner=OWNER
    )
    control = Path(control)
    if mode == "gated":
        original_save = store.save

        def gated_save(updated):
            (control / f"{label}.ready").write_text("save entered", encoding="utf-8")
            _wait(control / f"{label}.release")
            return original_save(updated)

        store.save = gated_save
    try:
        updated = _checkpoint(module, store, run, int(sequence), label)
        receipt = {"outcome": "committed", "sequence": updated.checkpoint_seq,
                   "owner": updated.source_owner, "source_sha256": SOURCE_SHA256}
    except module.ResearchRunCheckpointError as error:
        receipt = {"outcome": "rejected", "error_type": type(error).__name__}
    print("R24:" + json.dumps(receipt, sort_keys=True), flush=True)
    if mode == "crash" and receipt["outcome"] == "committed":
        (control / "committed").write_text("durable checkpoint returned", encoding="utf-8")
        time.sleep(60)


def test_native_generation_advances_monotonically(tmp_path):
    module = _native()
    store, run = _seed(module, tmp_path)
    for sequence in range(3):
        run = _checkpoint(module, store, run, sequence, f"evidence-{sequence + 1}")
        durable = _load(module, tmp_path)
        assert durable == run
        assert durable.checkpoint_seq == sequence + 1
        assert durable.source_owner == OWNER
    assert len(_snapshot(tmp_path)) == 1


def test_stale_generation_rejected_without_mutation(tmp_path):
    module = _native()
    store, stale = _seed(module, tmp_path)
    winner = _checkpoint(module, store, stale, 0, "winner")
    before = _snapshot(tmp_path)
    with pytest.raises(module.ResearchRunCheckpointError):
        _checkpoint(module, store, stale, 0, "stale")
    assert _snapshot(tmp_path) == before
    assert _load(module, tmp_path) == winner


def test_foreign_owner_rejected_without_mutation(tmp_path):
    module = _native()
    store, run = _seed(module, tmp_path)
    before = _snapshot(tmp_path)
    with pytest.raises(ValueError):
        _checkpoint(module, store, run, 0, "foreign", owner="foreign-owner")
    assert _snapshot(tmp_path) == before
    assert _load(module, tmp_path).source_owner == OWNER


def test_concurrent_stale_writer_cannot_replace_winner(tmp_path):
    module = _native()
    root = tmp_path / "checkpoints"
    control = tmp_path / "control"
    control.mkdir()
    _seed(module, root)
    first = _start(root, control, "winner", 0, "gated")
    second = None
    try:
        _wait(control / "winner.ready", first)
        second = _start(root, control, "stale", 0, "gated")
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            if (control / "stale.ready").exists() or second.poll() is not None:
                break
            time.sleep(0.01)
        (control / "winner.release").touch()
        winner_receipt = _finish(first)
        assert winner_receipt["outcome"] == "committed"
        before = _snapshot(root)
        (control / "stale.release").touch()
        stale_receipt = _finish(second)
        assert stale_receipt["outcome"] == "rejected", stale_receipt
        assert _snapshot(root) == before
        durable = _load(module, root)
        assert durable.checkpoint_seq == 1
        assert durable.evidence_ids == ("winner",)
        assert durable.source_owner == OWNER
    finally:
        _stop(first)
        if second is not None:
            _stop(second)


def test_process_kill_restart_rejects_replay_and_advances(tmp_path):
    module = _native()
    root = tmp_path / "checkpoints"
    control = tmp_path / "control"
    control.mkdir()
    _seed(module, root)
    crashed = _start(root, control, "pre-crash", 0, "crash")
    try:
        _wait(control / "committed", crashed)
        crashed.kill()
        crashed.communicate(timeout=10)
        assert crashed.returncode != 0
    finally:
        _stop(crashed)
    before = _snapshot(root)
    restarted = _start(root, control, "replay", 0)
    try:
        assert _finish(restarted)["outcome"] == "rejected"
    finally:
        _stop(restarted)
    assert _snapshot(root) == before
    next_writer = _start(root, control, "post-restart", 1)
    try:
        receipt = _finish(next_writer)
    finally:
        _stop(next_writer)
    assert receipt["outcome"] == "committed"
    assert receipt["sequence"] == 2
    durable, plan = module.resume_research_run(
        _store(module, root), RUN_ID, source_revision=REVISION, source_owner=OWNER
    )
    assert durable.checkpoint_seq == 2
    assert durable.evidence_ids == ("post-restart",)
    assert durable.source_owner == OWNER
    assert tuple(plan["provider_call_ids"]) == ("recorded-effect",)
    assert len(_snapshot(root)) == 1


if __name__ == "__main__":
    assert sys.argv[1] == "--r24-worker"
    _worker(*sys.argv[2:])
