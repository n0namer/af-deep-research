from typing import Any, Awaitable, Callable, Optional
from .methodology import select_methodology
from .models import ExtensionTrace
from .task_contract import build_answer_contract
from .requirement_decomposition import decompose_answer_contract
from .upstream_adapter import UpstreamDeepResearchAdapter
from .verified_pipeline import execute_verified_pipeline
from .provider_telemetry import reset_provider_events


def install_verified_deep_research(
    app: Any,
    execute_deep_research: Callable[..., Awaitable[Any]],
    prepare_research_package: Optional[Callable[..., Awaitable[Any]]] = None,
    generate_document_from_package: Optional[Callable[..., Awaitable[Any]]] = None,
    stream_executor: Optional[Callable[..., Awaitable[Any]]] = None,
    ai_call=None,
) -> Callable[..., Awaitable[Any]]:
    if getattr(app, "_verified_deep_research_installed", False):
        return getattr(app, "_verified_deep_research_reasoner")
    adapter = UpstreamDeepResearchAdapter(execute_deep_research)

    async def execute_verified_deep_research(
        query: str,
        mode: str = "general",
        research_focus: int = 3,
        research_scope: int = 3,
        max_research_loops: int = 3,
        max_gap_rounds: int = 1,
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
        reset_provider_events()
        contract = build_answer_contract(query, decision=decision, research_type=research_type, source_strictness=source_strictness, as_of=as_of)
        if ai_call is not None:
            contract = await decompose_answer_contract(
                contract,
                ai_call=ai_call,
                model=model,
                api_key=api_key,
            )
        methods = select_methodology(contract, research_scope=research_scope, research_focus=research_focus, verification_level=verification_level)
        trace = ExtensionTrace(answer_contract=contract, method_selection=methods, upstream_behavior_changed=False)
        upstream_kwargs = {
            "query": query,
            "mode": mode,
            "research_focus": research_focus,
            "research_scope": research_scope,
            "max_research_loops": max_research_loops,
            "max_gap_rounds": max_gap_rounds,
            "num_parallel_streams": num_parallel_streams,
            "tension_lens": tension_lens,
            "source_strictness": source_strictness,
            "evidence_style": evidence_style,
            "analysis_depth": analysis_depth,
            "model": model,
            "api_key": api_key,
        }
        if prepare_research_package is not None and generate_document_from_package is not None:
            return await execute_verified_pipeline(
                trace=trace,
                prepare_research_package=prepare_research_package,
                generate_document_from_package=generate_document_from_package,
                stream_executor=stream_executor,
                upstream_kwargs=upstream_kwargs,
                ai_call=ai_call,
            )
        return await adapter.execute(trace=trace, upstream_kwargs=upstream_kwargs)

    execute_verified_deep_research.__name__ = "execute_verified_deep_research"
    execute_verified_deep_research.__doc__ = (
        "Experimental upgrade-friendly Deep Research endpoint with an explicit Answer Contract, "
        "method selection and evidence-state checkpoint around unchanged upstream primitives."
    )
    registered = app.reasoner()(execute_verified_deep_research)
    setattr(app, "_verified_deep_research_installed", True)
    setattr(app, "_verified_deep_research_reasoner", registered)
    return registered
