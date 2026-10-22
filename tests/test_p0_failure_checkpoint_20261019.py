import json
import pytest
from pathlib import Path
from reasoners.deep_research_ext.bootstrap import install_verified_deep_research
from reasoners.deep_research_ext.research_run import ResearchRunStore
class App:
    def reasoner(self):
        return lambda fn: fn
@pytest.mark.asyncio
async def test_provider_failure_checkpoints_failed_not_perpetual_running(tmp_path,monkeypatch):
    monkeypatch.setenv("DR_RESEARCH_RUN_DIR",str(tmp_path))
    app=App()
    async def broken_prepare(**kwargs):
        raise RuntimeError("live provider unavailable")
    async def unused_doc(**kwargs):
        raise AssertionError("must not generate after provider outage")
    endpoint=install_verified_deep_research(
        app,broken_prepare,prepare_research_package=broken_prepare,
        generate_document_from_package=unused_doc,ai_call=None,
    )
    with pytest.raises(RuntimeError,match="live provider unavailable"):
        await endpoint(query="Which RFC defines HTTP/3?",max_gap_rounds=0)
    files=list(Path(tmp_path).glob("*.json"))
    assert len(files)==1
    saved=ResearchRunStore(str(tmp_path)).load(files[0].stem)
    assert saved.stage=="failed"
    assert saved.status=="failed"
    assert saved.payload.get("failure_stage")=="research_pipeline"
