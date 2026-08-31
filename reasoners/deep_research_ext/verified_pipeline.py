import time
from typing import Any, Awaitable, Callable, Dict, Optional

from .coverage import assess_candidate_coverage
from .evidence_ledger import build_evidence_ledger
from .final_verifier import verify_final_document
from .gap_research import run_gap_research_round, unresolved_requirement_ids
from .models import ExtensionTrace
from .requirement_mapping import map_claims_to_requirements
from .research_run import begin_research_run, checkpoint_research_run
from .stopping import assess_stopping
from .synthesis_guard import build_evidence_only_gap_response, requires_programmatic_abstention
from .verification_bridge import verify_ledger_claims


async def execute_verified_pipeline(
    *,
    trace: ExtensionTrace,
    prepare_research_package: Callable[..., Awaitable[Any]],
    generate_document_from_package: Callable[..., Awaitable[Any]],
    stream_executor: Optional[Callable[..., Awaitable[Any]]] = None,
    upstream_kwargs: Dict[str, Any],
    ai_call=None,
) -> Any:
    started = time.time()
    run_store, research_run = begin_research_run(upstream_kwargs["query"])
    cached_package = research_run.payload.get("research_package") if research_run.stage != "started" else None
    if isinstance(cached_package, dict):
        package = dict(cached_package)
        research_phase_metadata = dict(research_run.payload.get("research_phase_metadata") or {})
        research_phase_metadata["resumed_from_checkpoint"] = True
        research_phase_metadata["research_run_id"] = research_run.run_id
    else:
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
        research_phase_metadata = dict(getattr(research, "metadata", {}) or {})
        source_ids = tuple(str(item.get("id")) for item in package.get("source_articles", []) if item.get("id") is not None)
        research_run = checkpoint_research_run(
            run_store, research_run, stage="research_package_ready", source_ids=source_ids,
            payload={"research_package": package, "research_phase_metadata": research_phase_metadata},
        )
    ledger = build_evidence_ledger(package, [])
    ledger = await map_claims_to_requirements(
        ledger=ledger,
        contract=trace.answer_contract,
        ai_call=ai_call,
        model=upstream_kwargs.get("model"),
        api_key=upstream_kwargs.get("api_key"),
    )
    ledger = await verify_ledger_claims(
        ledger=ledger,
        research_package=package,
        source_strictness=upstream_kwargs["source_strictness"],
        model=upstream_kwargs.get("model"),
        api_key=upstream_kwargs.get("api_key"),
        ai_call=ai_call,
    )
    coverage = assess_candidate_coverage(trace.answer_contract, ledger)
    gap_round_traces = []
    max_gap_rounds = max(0, int(upstream_kwargs.get("max_gap_rounds", 0) or 0))
    if stream_executor is not None and max_gap_rounds > 0 and coverage.verified_coverage_ratio < 1.0:
        for _ in range(max_gap_rounds):
            package, ledger, gap_trace = await run_gap_research_round(
                contract=trace.answer_contract,
                coverage=coverage,
                ledger=ledger,
                research_package=package,
                stream_executor=stream_executor,
                ai_call=ai_call,
                source_strictness=upstream_kwargs["source_strictness"],
                model=upstream_kwargs.get("model"),
                api_key=upstream_kwargs.get("api_key"),
            )
            gap_round_traces.append(gap_trace)
            coverage = assess_candidate_coverage(trace.answer_contract, ledger)
            if coverage.verified_coverage_ratio >= 1.0 or gap_trace.novelty_exhausted:
                break

    stopping = assess_stopping(
        coverage,
        novelty_evaluated=bool(gap_round_traces),
        novelty_exhausted=bool(gap_round_traces and gap_round_traces[-1].novelty_exhausted),
    )
    ext = trace.model_dump()
    ext["mode"] = "verified_phase_checkpoint"
    ext["evidence_ledger_summary"] = ledger.summary()
    ext["coverage_state"] = coverage.model_dump()
    ext["stopping_assessment"] = stopping.model_dump()
    ext["gap_rounds"] = [item.model_dump() for item in gap_round_traces]
    research_run = checkpoint_research_run(
        run_store, research_run, stage="evidence_verified",
        evidence_summary=ledger.summary(), coverage_state=coverage.model_dump(),
        open_gap_ids=tuple(unresolved_requirement_ids(coverage)),
        payload={"research_package": package, "research_phase_metadata": research_phase_metadata},
    )
    base_metadata = {
        "total_orchestration_time_seconds": round(time.time() - started, 2),
        "research_phase_metadata": research_phase_metadata,
        "research_run": {"run_id": research_run.run_id, "checkpoint_seq": research_run.checkpoint_seq, "stage": research_run.stage},
        "verified_research_extension": ext,
    }

    if requires_programmatic_abstention(upstream_kwargs["source_strictness"], coverage):
        ext["mode"] = "programmatic_partial_abstention"
        research_run = checkpoint_research_run(
            run_store, research_run, stage="completed", status="completed",
            evidence_summary=ledger.summary(), coverage_state=coverage.model_dump(),
            open_gap_ids=tuple(unresolved_requirement_ids(coverage)),
            payload={"research_package": package, "research_phase_metadata": research_phase_metadata, "terminal_mode": ext["mode"]},
        )
        base_metadata["research_run"] = {"run_id": research_run.run_id, "checkpoint_seq": research_run.checkpoint_seq, "stage": research_run.stage}
        return build_evidence_only_gap_response(
            contract=trace.answer_contract,
            ledger=ledger,
            coverage=coverage,
            metadata=base_metadata,
        )

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
    metadata = dict(getattr(document, "metadata", {}) or {})
    metadata.update(base_metadata)
    research_run = checkpoint_research_run(
        run_store, research_run, stage="synthesis_ready",
        evidence_summary=ledger.summary(), coverage_state=coverage.model_dump(),
        open_gap_ids=tuple(unresolved_requirement_ids(coverage)),
        payload={
            "research_package": package,
            "research_phase_metadata": research_phase_metadata,
            "document_package": getattr(document, "research_package", {}),
        },
    )
    metadata["research_run"] = {"run_id": research_run.run_id, "checkpoint_seq": research_run.checkpoint_seq, "stage": research_run.stage}

    if (upstream_kwargs["source_strictness"] or "").strip().lower() in {"strict", "verified-only", "verified_only"}:
        final_verification = await verify_final_document(
            document_package=document.research_package,
            research_package=package,
            source_strictness=upstream_kwargs["source_strictness"],
            ai_call=ai_call,
            model=upstream_kwargs.get("model"),
            api_key=upstream_kwargs.get("api_key"),
        )
        ext["final_verification"] = final_verification.model_dump()
        if not final_verification.passed:
            ext["mode"] = "post_generation_rejected"
            research_run = checkpoint_research_run(
                run_store, research_run, stage="completed", status="completed",
                evidence_summary=ledger.summary(), coverage_state=coverage.model_dump(),
                open_gap_ids=tuple(unresolved_requirement_ids(coverage)),
                payload={
                    "research_package": package,
                    "research_phase_metadata": research_phase_metadata,
                    "document_package": getattr(document, "research_package", {}),
                    "terminal_mode": ext["mode"],
                },
            )
            metadata["research_run"] = {"run_id": research_run.run_id, "checkpoint_seq": research_run.checkpoint_seq, "stage": research_run.stage}
            return build_evidence_only_gap_response(
                contract=trace.answer_contract,
                ledger=ledger,
                coverage=coverage,
                metadata=metadata,
            )

    research_run = checkpoint_research_run(
        run_store, research_run, stage="completed", status="completed",
        evidence_summary=ledger.summary(), coverage_state=coverage.model_dump(),
        open_gap_ids=tuple(unresolved_requirement_ids(coverage)),
        payload={
            "research_package": package,
            "research_phase_metadata": research_phase_metadata,
            "document_package": getattr(document, "research_package", {}),
            "terminal_mode": "verified_document",
        },
    )
    metadata["research_run"] = {"run_id": research_run.run_id, "checkpoint_seq": research_run.checkpoint_seq, "stage": research_run.stage}
    if hasattr(document, "model_copy"):
        return document.model_copy(update={"metadata": metadata})
    document.metadata = metadata
    return document
