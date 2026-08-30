from typing import Any, Awaitable, Callable, Optional
from .methodology import select_methodology
from .models import ExtensionTrace
from .task_contract import build_answer_contract
from .upstream_adapter import UpstreamDeepResearchAdapter


def install_verified_deep_research(app: Any, execute_deep_research: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
    if getattr(app, "_verified_deep_research_installed", False):
        return getattr(app, "_verified_deep_research_reasoner")
    adapter = UpstreamDeepResearchAdapter(execute_deep_research)

    async def execute_verified_deep_research(
        query: str,
        mode: str = "general",
        research_focus: int = 3,
        research_scope: int = 3,
        max_research_loops: int = 3,
        num_parallel_streams: int = 2,
        tension_lens: str = "balanced",
        source_strictness: str = "mixed",
        evidence_style: str = "standard",
        analysis_depth: str = "ANALYTICAL_BRIEF",
        research_type: str = "auto",
        verification_level: str = "auto",
        decision: Optional[str] = None,
        as_of: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
    ) -> Any:
        contract = build_answer_contract(query, decision=decision, research_type=research_type, source_strictness=source_strictness, as_of=as_of)
        methods = select_methodology(contract, research_scope=research_scope, research_focus=research_focus, verification_level=verification_level)
        trace = ExtensionTrace(answer_contract=contract, method_selection=methods, upstream_behavior_changed=False)
        return await adapter.execute(
            trace=trace,
            upstream_kwargs={
                "query": query,
                "mode": mode,
                "research_focus": research_focus,
                "research_scope": research_scope,
                "max_research_loops": max_research_loops,
                "num_parallel_streams": num_parallel_streams,
                "tension_lens": tension_lens,
                "source_strictness": source_strictness,
                "evidence_style": evidence_style,
                "analysis_depth": analysis_depth,
                "model": model,
                "api_key": api_key,
            },
        )

    execute_verified_deep_research.__name__ = "execute_verified_deep_research"
    execute_verified_deep_research.__doc__ = (
        "Experimental upgrade-friendly Deep Research endpoint. Builds an explicit "
        "Answer Contract and BMAD-style method selection, delegates to the unchanged "
        "upstream pipeline, and exposes the extension trace in metadata."
    )
    registered = app.reasoner()(execute_verified_deep_research)
    setattr(app, "_verified_deep_research_installed", True)
    setattr(app, "_verified_deep_research_reasoner", registered)
    return registered
