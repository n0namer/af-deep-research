import asyncio
from typing import Awaitable, Callable, Dict, List, Optional
from pydantic import BaseModel, Field
from .coverage import CoverageState
from .evidence_ledger import EvidenceLedger, build_evidence_ledger, merge_evidence_ledgers
from .models import AnswerContract
from .requirement_mapping import map_claims_to_requirements
from .verification_bridge import verify_ledger_claims


class GapQuery(BaseModel):
    requirement_id: str
    queries: List[str] = Field(default_factory=list)


class GapQueryPlan(BaseModel):
    gaps: List[GapQuery] = Field(default_factory=list)


class GapRoundTrace(BaseModel):
    attempted_requirements: List[str] = Field(default_factory=list)
    new_source_count: int = 0
    new_claim_count: int = 0
    new_verified_claim_count: int = 0
    skipped_source_count: int = 0
    budget_exhausted: bool = False
    novelty_exhausted: bool = False


_INSTRUCTION_MARKERS = (
    "ignore previous instructions",
    "disregard prior instructions",
    "reveal secret",
    "system message:",
    "follow these instructions",
)


def _source_is_admissible(source: Dict) -> bool:
    url = str(source.get("url") or "").strip()
    content = str(source.get("content") or "").strip()
    if not url or not content:
        return False
    lowered = content.lower()
    return not any(marker in lowered for marker in _INSTRUCTION_MARKERS)


def _source_identity(source: Dict) -> str:
    return str(source.get("url") or source.get("content_hash") or source.get("id") or "").strip()


def _numeric_source_id(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _normalized_query_key(value: str) -> str:
    return " ".join(str(value or "").split()).casefold()


def _attempted_gap_queries(research_package: Dict) -> set[tuple[str, str]]:
    return {
        (str(item.get("requirement_id") or ""), _normalized_query_key(item.get("query")))
        for item in research_package.get("gap_research_attempts", []) or []
        if item.get("requirement_id") and _normalized_query_key(item.get("query"))
    }


def unresolved_requirement_ids(coverage: CoverageState) -> List[str]:
    return [item.requirement_id for item in coverage.requirements if item.status != "verified"]


async def plan_gap_queries(*, contract: AnswerContract, coverage: CoverageState, ai_call, model: Optional[str] = None, api_key: Optional[str] = None, queries_per_gap: int = 2) -> GapQueryPlan:
    unresolved = set(unresolved_requirement_ids(coverage))
    if not unresolved or ai_call is None:
        return GapQueryPlan()
    requirements = [item for item in contract.requirements if item.requirement_id in unresolved]
    req_text = "\n".join(f"{r.requirement_id}: {r.question} | source need: {r.required_source_class}" for r in requirements)
    prompt = f"""
<task>
Generate targeted web-search queries only for the unresolved research requirements below.
Do not answer the requirements. Queries may use hypotheses to locate evidence, but must not be treated as evidence themselves.
</task>
<requirements>{req_text}</requirements>
<source_strictness>{contract.source_strictness}</source_strictness>
<rules>
- Return exactly one GapQuery entry per unresolved requirement.
- Return 1 to {queries_per_gap} concise queries per requirement.
- Prefer primary/official source surfaces when the requirement asks for them.
- For standards, favor RFC Editor / IETF; for first-party history, favor official organizational sources.
- Do not repeat generic queries that fail to target the specific gap.
</rules>
"""
    result = await ai_call(system="You plan evidence-seeking search queries for unresolved research requirements without answering them.", user=prompt, schema=GapQueryPlan, model=model, api_key=api_key)
    filtered = []
    for item in result.gaps:
        if item.requirement_id in unresolved:
            filtered.append(GapQuery(requirement_id=item.requirement_id, queries=[q.strip() for q in item.queries if q.strip()][:queries_per_gap]))
    return GapQueryPlan(gaps=filtered)


async def run_gap_research_round(
    *,
    contract: AnswerContract,
    coverage: CoverageState,
    ledger: EvidenceLedger,
    research_package: Dict,
    stream_executor: Callable[..., Awaitable[object]],
    ai_call,
    source_strictness: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    source_budget: Optional[int] = None,
) -> tuple[Dict, EvidenceLedger, GapRoundTrace]:
    if source_budget is not None and source_budget <= 0:
        return research_package, ledger, GapRoundTrace(budget_exhausted=True, novelty_exhausted=True)

    plan = await plan_gap_queries(contract=contract, coverage=coverage, ai_call=ai_call, model=model, api_key=api_key)
    if not plan.gaps:
        return research_package, ledger, GapRoundTrace(novelty_exhausted=True)

    max_id = max([_numeric_source_id(a.get("id")) for a in research_package.get("source_articles", []) or []] or [0])
    requirement_by_id = {item.requirement_id: item for item in contract.requirements}
    attempted_queries = _attempted_gap_queries(research_package)
    round_attempts = []
    tasks = []
    active_gaps = []
    scheduled_gaps = set()
    for index, gap in enumerate(plan.gaps):
        normalized_queries = []
        query_keys = set()
        for query in gap.queries:
            normalized_query = " ".join(query.split())
            query_key = normalized_query.casefold()
            if normalized_query and query_key not in query_keys:
                query_keys.add(query_key)
                round_attempts.append({"requirement_id": gap.requirement_id, "query": normalized_query})
                if (gap.requirement_id, query_key) in attempted_queries:
                    continue
                normalized_queries.append(normalized_query)
        if not normalized_queries:
            continue
        requirement = requirement_by_id.get(gap.requirement_id)
        if requirement is None:
            continue
        gap_key = (gap.requirement_id, tuple(sorted(query_keys)))
        if gap_key in scheduled_gaps:
            continue
        scheduled_gaps.add(gap_key)
        active_gaps.append(gap.requirement_id)
        tasks.append(stream_executor(
            f"VerifiedGap_{gap.requirement_id}",
            normalized_queries,
            requirement.question,
            contract.query,
            requirement.question,
            max_id + 1 + (index * 1000),
            model,
            api_key,
            source_strictness=source_strictness,
        ))
    if not tasks:
        attempted_package = dict(research_package)
        attempted_package["gap_research_attempts"] = list(
            research_package.get("gap_research_attempts", []) or []
        ) + round_attempts
        return attempted_package, ledger, GapRoundTrace(
            attempted_requirements=active_gaps,
            skipped_source_count=len(round_attempts),
            novelty_exhausted=True,
        )

    outputs = await asyncio.gather(*tasks)
    existing_keys = {
        _source_identity(article)
        for article in research_package.get("source_articles", []) or []
        if _source_identity(article)
    }
    new_articles = []
    new_evidence = []
    skipped_source_count = 0
    budget_skipped_count = 0
    accepted_keys = set()
    for output in outputs:
        candidates = [
            item.model_dump() if hasattr(item, "model_dump") else dict(item)
            for item in getattr(output, "source_articles", []) or []
        ]
        for article in candidates:
            key = _source_identity(article)
            if not _source_is_admissible(article) or not key or key in existing_keys or key in accepted_keys:
                skipped_source_count += 1
                continue
            if source_budget is not None and len(new_articles) >= source_budget:
                skipped_source_count += 1
                budget_skipped_count += 1
                continue
            accepted_keys.add(key)
            new_articles.append(article)
        accepted_ids = {str(article.get("id")) for article in new_articles}
        for item in getattr(output, "article_evidence", []) or []:
            evidence = item.model_dump() if hasattr(item, "model_dump") else dict(item)
            if str(evidence.get("article_id")) in accepted_ids:
                new_evidence.append(evidence)

    extra_package = {"source_articles": new_articles, "article_evidence": new_evidence}
    extra_ledger = build_evidence_ledger(extra_package, [])
    extra_ledger = await map_claims_to_requirements(ledger=extra_ledger, contract=contract, ai_call=ai_call, model=model, api_key=api_key)
    extra_ledger = await verify_ledger_claims(ledger=extra_ledger, research_package=extra_package, source_strictness=source_strictness, model=model, api_key=api_key, ai_call=ai_call)
    merged_ledger = merge_evidence_ledgers(ledger, extra_ledger)

    merged_package = dict(research_package)
    merged_package["gap_research_attempts"] = list(
        research_package.get("gap_research_attempts", []) or []
    ) + round_attempts
    existing_keys = {
        _source_identity(article)
        for article in merged_package.get("source_articles", []) or []
        if _source_identity(article)
    }
    merged_package["source_articles"] = list(merged_package.get("source_articles", []) or []) + [
        article for article in new_articles
        if _source_identity(article) not in existing_keys
    ]
    merged_package["article_evidence"] = list(merged_package.get("article_evidence", []) or []) + new_evidence

    new_verified = sum(1 for claim in extra_ledger.claims if claim.status == "verified" and claim.support_state == "source_entailed")
    trace = GapRoundTrace(
        attempted_requirements=active_gaps,
        new_source_count=len(new_articles),
        new_claim_count=len(extra_ledger.claims),
        new_verified_claim_count=new_verified,
        skipped_source_count=skipped_source_count,
        budget_exhausted=(budget_skipped_count > 0),
        novelty_exhausted=(new_verified == 0),
    )
    return merged_package, merged_ledger, trace
