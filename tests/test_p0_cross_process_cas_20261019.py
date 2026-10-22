from __future__ import annotations
import multiprocessing as mp
import time
from pathlib import Path
from reasoners.deep_research_ext.research_run import (
    ResearchRunStore, ResearchRun, checkpoint_research_run,
)
class DelayedStore(ResearchRunStore):
    def save(self, run):
        time.sleep(0.12)
        return super().save(run)
def _writer(path, ready, answer):
    store=DelayedStore(path)
    run=store.load("two-owner-race")
    ready.wait(timeout=12)
    try:
        checkpoint_research_run(store, run, stage="retrieval",expected_checkpoint_seq=0)
        answer.put("COMMITTED")
    except Exception as e:
        answer.put(type(e).__name__)
def test_checkpoint_cas_is_atomic_across_two_windows_processes(tmp_path: Path):
    path=str(tmp_path)
    store=ResearchRunStore(path)
    run=ResearchRun(
        run_id="two-owner-race",query="Q",stage="started",
        checkpoint_seq=0,status="running",created_at=1.,updated_at=1.,
    )
    store.save(run)
    ctx=mp.get_context("spawn")
    ready=ctx.Barrier(3)
    answers=ctx.Queue()
    ps=[ctx.Process(target=_writer,args=(path,ready,answers)) for _ in range(2)]
    try:
        for p in ps:p.start()
        ready.wait(timeout=12)
        for p in ps:p.join(timeout=12)
        assert all(p.exitcode == 0 for p in ps),[(p.pid,p.exitcode) for p in ps]
        statuses=[answers.get(timeout=2) for _ in range(2)]
        assert statuses.count("COMMITTED") == 1, statuses
        assert statuses.count("ResearchRunCheckpointError") == 1, statuses
        final=store.load("two-owner-race")
        assert final.checkpoint_seq == 1
    finally:
        for p in ps:
            if p.is_alive():p.terminate()
            p.join(timeout=2)
