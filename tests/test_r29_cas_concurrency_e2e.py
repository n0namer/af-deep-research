from __future__ import annotations

import multiprocessing as mp
import os
from pathlib import Path

import pytest

from reasoners.deep_research_ext.research_run import (
    ResearchRun,
    ResearchRunStore,
    checkpoint_research_run,
)


def _seed(path: str) -> None:
    store = ResearchRunStore(path)
    now = 1.0
    store.save(
        ResearchRun(
            run_id="race",
            query="q",
            stage="started",
            checkpoint_seq=0,
            status="running",
            created_at=now,
            updated_at=now,
            source_revision="rev-1",
            source_owner="owner",
        )
    )


def _writer(path: str, stage: str, ready: mp.Barrier, release: mp.Event, result: mp.Queue) -> None:
    store = ResearchRunStore(path)
    run = store.load("race", source_revision="rev-1")
    assert run is not None
    ready.wait()
    release.wait()
    try:
        checkpoint_research_run(
            store, run, stage=stage, expected_checkpoint_seq=0,
            source_revision="rev-1", source_owner="owner",
        )
    except Exception as exc:
        result.put((stage, type(exc).__name__, str(exc)))
    else:
        result.put((stage, "COMMITTED", ""))


@pytest.fixture
def process_context():
    return mp.get_context("spawn" if os.name == "nt" else "fork")


def test_two_os_processes_reject_stale_writer_after_winner(tmp_path: Path, process_context):
    _seed(str(tmp_path))
    ready = process_context.Barrier(2)
    release = process_context.Event()
    result = process_context.Queue()
    winner = process_context.Process(target=_writer, args=(str(tmp_path), "query", ready, release, result))
    stale = process_context.Process(target=_writer, args=(str(tmp_path), "retrieval", ready, release, result))
    winner.start()
    stale.start()
    ready.wait()
    release.set()
    winner.join(10)
    stale.join(10)
    assert winner.exitcode == 0
    assert stale.exitcode == 0

    outcomes = [result.get(timeout=2), result.get(timeout=2)]
    committed = [stage for stage, status, _ in outcomes if status == "COMMITTED"]
    rejected = [item for item in outcomes if item[1] != "COMMITTED"]
    assert len(committed) == 1, outcomes
    assert len(rejected) == 1, outcomes

    final = ResearchRunStore(str(tmp_path)).load("race")
    assert final is not None
    assert final.checkpoint_seq == 1
    assert final.stage == committed[0]


@pytest.mark.parametrize(
    ("revision", "owner", "expected"),
    [("rev-2", "owner", "StaleResearchRunError"), ("rev-1", "other-owner", "ResearchRunCheckpointError")],
)
def test_cross_boundary_identity_rejections(tmp_path: Path, revision: str, owner: str, expected: str):
    _seed(str(tmp_path))
    store = ResearchRunStore(str(tmp_path))
    run = store.load("race")
    assert run is not None
    with pytest.raises(Exception) as error:
        checkpoint_research_run(store, run, stage="query", expected_checkpoint_seq=0,
                                source_revision=revision, source_owner=owner)
    assert type(error.value).__name__ == expected


def test_corrupt_checkpoint_is_rejected(tmp_path: Path):
    _seed(str(tmp_path))
    (tmp_path / "race.json").write_text("{not-json", encoding="utf-8")
    with pytest.raises(Exception):
        ResearchRunStore(str(tmp_path)).load("race")
