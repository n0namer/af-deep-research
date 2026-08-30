import time
from typing import Any, Awaitable, Callable, Dict

from .coverage import assess_candidate_coverage
from .evidence_ledger import build_evidence_ledger
from .models import ExtensionTrace
from .stopping import assess_stopping
from .verification_bridge import verify_ledger_claims


async def execute_verified_pipeline(
    *,
    trace: ExtensionTrace,
    prepare_research_package: Callable[..., Awaitable[Any]],
    generate_document_from_package: Callable[..., Awaitable[Any]],
    upstream_kwargs: Dict[str, Any],
) -> Any:
    """Run upstream phases with an additive evidence-state checkpoint between them."""
    started = time.time()
    research = await prepare_research_package(
        query=upstream_kwargs["query"],
        mode=upstream_kwargs["mode"],
        research_focus=upstream_kwargs["research_focus"],
        research_scope=upstream_kwargs["research_scope"],
        max_research_loops=upstream_kwargs["max_research_loops"],
        num_parallel_streams=upstream_kwargs["num_parallel_streams"],
        source_strictness=upstream_kwargs["source_strictness"],
        model=upstream_kwargs.get("model"),
        api_key=upstream_kwargs.get("api_key"),
    )
    package = dict(research.research_package)
    requirement_ids = [item.requirement_id for item in trace.answer_contract.requirements]
    ledger = build_evidence_ledger(package, requirement_ids)
    ledger = await verify_ledger_claims(
        ledger=ledger,
        research_package=package,
        source_strictness=upstream_kwargs["source_strictness"],
        model=upstream_kwargs.get("model"),
        api_key=upstream_kwargs.get("api_key"),
    )
    coverage = assess_candidate_coverage(trace.answer_contract, ledger)
    stopping = assess_stopping(coverage)

    document = await generate_document_from_package(
        package=package,
        main_query=upstream_kwargs["query"],
        tension_lens=upstream_kwargs["tension_lens"],
        source_strictness=upstream_kwargs["source_strictness"],
        evidence_style=upstream_kwargs["evidence_style"],
        analysis_depth=upstream_kwargs["analysis_depth"],
        model=upstream_kwargs.get("model"),
        api_key=upstream_kwargs.get("api_key"),
    )

    ext = trace.model_dump()
    ext["mode"] = "verified_phase_checkpoint"
    ext["evidence_ledger_summary"] = ledger.summary()
    ext["coverage_state"] = coverage.model_dump()
    ext["stopping_assessment"] = stopping.model_dump()

    metadata = dict(getattr(document, "metadata", {}) or {})
    metadata.update({
        "total_orchestration_time_seconds": round(time.time() - started, 2),
        "research_phase_metadata": getattr(research, "metadata", {}) or {},
        "verified_research_extension": ext,
    })
    if hasattr(document, "model_copy"):
        return document.model_copy(update={"metadata": metadata})
    document.metadata = metadata
    return document
