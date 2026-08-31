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


def test_verified_pipeline_reuses_checkpointed_research_package_for_same_run_id():
    import asyncio, os, shutil
    from types import SimpleNamespace
    import reasoners.deep_research_ext.verified_pipeline as vp
    from reasoners.deep_research_ext.task_contract import build_answer_contract
    from agentfield.execution_context import set_execution_context, reset_execution_context

    root='/tmp/dr-resume-regression'
    shutil.rmtree(root, ignore_errors=True)
    old_root=os.environ.get('DR_RESEARCH_RUN_DIR')
    os.environ['DR_RESEARCH_RUN_DIR']=root
    calls={'prepare':0}

    async def prep(**kw):
        calls['prepare'] += 1
        return SimpleNamespace(research_package={'source_articles':[], 'article_evidence':[]}, metadata={'phase':'fresh'})

    class Doc:
        def __init__(self, metadata=None):
            self.research_package={'title':'ok'}
            self.metadata=metadata or {}
        def model_copy(self, update):
            return Doc(metadata=update['metadata'])

    async def gen(**kw): return Doc()
    async def ident(**kw): return kw['ledger']
    class Cov:
        verified_coverage_ratio=1.0
        unresolved_requirement_ids=[]
        def model_dump(self): return {'verified_coverage_ratio':1.0, 'unresolved_requirement_ids':[]}
    class Stop:
        def model_dump(self): return {'eligible_to_stop':True}

    old_map, old_verify, old_cov, old_stop = vp.map_claims_to_requirements, vp.verify_ledger_claims, vp.assess_candidate_coverage, vp.assess_stopping
    vp.map_claims_to_requirements=ident
    vp.verify_ledger_claims=ident
    vp.assess_candidate_coverage=lambda *a, **k: Cov()
    vp.assess_stopping=lambda *a, **k: Stop()
    trace=SimpleNamespace(answer_contract=build_answer_contract('resume test'), model_dump=lambda: {})
    kwargs={'query':'resume test','mode':'general','research_focus':1,'research_scope':1,'max_research_loops':1,'max_gap_rounds':0,'num_parallel_streams':1,'tension_lens':'balanced','source_strictness':'mixed','evidence_style':'standard','analysis_depth':'ANALYTICAL_BRIEF','model':None,'api_key':None}
    token=set_execution_context(SimpleNamespace(run_id='run_resume_regression', replay_source_run_id=None))
    try:
        async def run_twice():
            first=await vp.execute_verified_pipeline(trace=trace, prepare_research_package=prep, generate_document_from_package=gen, upstream_kwargs=kwargs)
            second=await vp.execute_verified_pipeline(trace=trace, prepare_research_package=prep, generate_document_from_package=gen, upstream_kwargs=kwargs)
            assert first.metadata['research_run']['run_id']=='run_resume_regression'
            assert second.metadata['research_phase_metadata']['resumed_from_checkpoint'] is True
        asyncio.run(run_twice())
        assert calls['prepare']==1
        assert Path(root, 'run_resume_regression.json').exists()
    finally:
        reset_execution_context(token)
        vp.map_claims_to_requirements, vp.verify_ledger_claims, vp.assess_candidate_coverage, vp.assess_stopping = old_map, old_verify, old_cov, old_stop
        if old_root is None: os.environ.pop('DR_RESEARCH_RUN_DIR', None)
        else: os.environ['DR_RESEARCH_RUN_DIR']=old_root


def test_agentfield_replay_source_run_reuses_saved_research_package():
    import shutil
    from types import SimpleNamespace
    from agentfield.execution_context import set_execution_context, reset_execution_context
    root=Path('/tmp/deep-research-replay-source')
    shutil.rmtree(root, ignore_errors=True)
    store=ResearchRunStore(str(root))

    source_token=set_execution_context(SimpleNamespace(run_id='run_source_fixture', replay_source_run_id=None))
    try:
        _, source=begin_research_run('query-replay', store=store)
        source=checkpoint_research_run(
            store, source, stage='research_package_ready',
            source_ids=('S1',), payload={'research_package': {'source_articles':[{'id':1}]}, 'research_phase_metadata': {'origin':'source'}},
        )
    finally:
        reset_execution_context(source_token)

    replay_token=set_execution_context(SimpleNamespace(run_id='run_replay_fixture', replay_source_run_id='run_source_fixture'))
    try:
        _, replay=begin_research_run('query-replay', store=store)
    finally:
        reset_execution_context(replay_token)

    assert replay.run_id=='run_replay_fixture'
    assert replay.replay_source_run_id=='run_source_fixture'
    assert replay.stage=='research_package_ready'
    assert replay.source_ids==('S1',)
    assert replay.payload['research_package']['source_articles'][0]['id']==1
    assert next_resume_stage(replay)=='evidence_verification'
