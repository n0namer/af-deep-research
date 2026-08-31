from pathlib import Path

from reasoners.deep_research_ext.research_run import (
    ResearchRunStore,
    begin_research_run,
    checkpoint_research_run,
    next_resume_stage,
)


def test_research_run_store_persists_and_resumes_same_run(tmp_path=None):
    root = Path(tmp_path) if tmp_path is not None else Path('/tmp/deep-research-run-test')
    if root.exists():
        for item in root.iterdir():
            item.unlink()
    store = ResearchRunStore(str(root))
    _, run = begin_research_run('query-a', store=store)
    run = checkpoint_research_run(
        store,
        run,
        stage='research_package_ready',
        source_ids=('S1', 'S2'),
        payload={'research_package': {'articles': [1, 2]}},
    )
    loaded = store.load(run.run_id)
    assert loaded is not None
    assert loaded.checkpoint_seq == 1
    assert loaded.stage == 'research_package_ready'
    assert loaded.source_ids == ('S1', 'S2')
    assert loaded.payload['research_package']['articles'] == [1, 2]
    assert next_resume_stage(loaded) == 'evidence_verification'


def test_research_run_checkpoint_is_atomic_and_monotonic():
    root = Path('/tmp/deep-research-run-atomic')
    root.mkdir(parents=True, exist_ok=True)
    for item in root.iterdir():
        item.unlink()
    store = ResearchRunStore(str(root))
    _, run = begin_research_run('query-b', store=store)
    first = checkpoint_research_run(store, run, stage='research_package_ready')
    second = checkpoint_research_run(store, first, stage='evidence_verified', evidence_summary={'verified': 3})
    assert second.checkpoint_seq == 2
    assert store.load(second.run_id) == second
    assert not list(root.glob('*.tmp-*'))
    assert next_resume_stage(second) == 'synthesis'


def test_research_run_rejects_unsafe_run_id():
    store = ResearchRunStore('/tmp/deep-research-run-safe')
    try:
        store.path_for('../escape')
    except ValueError:
        pass
    else:
        raise AssertionError('unsafe run id accepted')
