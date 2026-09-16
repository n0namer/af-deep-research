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
    novelty_exhausted: bool = False


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
) -> tuple[Dict, EvidenceLedger, GapRoundTrace]:
    plan = await plan_gap_queries(contract=contract, coverage=coverage, ai_call=ai_call, model=model, api_key=api_key)
    if not plan.gaps:
        return research_package, ledger, GapRoundTrace(novelty_exhausted=True)

    max_id = max([int(a.get("id") or 0) for a in research_package.get("source_articles", []) or []] or [0])
    requirement_by_id = {item.requirement_id: item for item in contract.requirements}
    tasks = []
    active_gaps = []
    for index, gap in enumerate(plan.gaps):
        if not gap.queries:
            continue
        requirement = requirement_by_id.get(gap.requirement_id)
        if requirement is None:
            continue
        active_gaps.append(gap.requirement_id)
        tasks.append(stream_executor(
            f"VerifiedGap_{gap.requirement_id}",
            gap.queries,
            requirement.question,
            contract.query,
            requirement.question,
            max_id + 1 + (index * 1000),
            model,
            api_key,
            source_strictness=source_strictness,
        ))
    if not tasks:
        return research_package, ledger, GapRoundTrace(attempted_requirements=active_gaps, novelty_exhausted=True)

    outputs = await asyncio.gather(*tasks)
    new_articles = []
    new_evidence = []
    for output in outputs:
        new_articles.extend([item.model_dump() if hasattr(item, "model_dump") else dict(item) for item in output.source_articles])
        new_evidence.extend([item.model_dump() if hasattr(item, "model_dump") else dict(item) for item in output.article_evidence])

    extra_package = {"source_articles": new_articles, "article_evidence": new_evidence}
    extra_ledger = build_evidence_ledger(extra_package, [])
    extra_ledger = await map_claims_to_requirements(ledger=extra_ledger, contract=contract, ai_call=ai_call, model=model, api_key=api_key)
    extra_ledger = await verify_ledger_claims(ledger=extra_ledger, research_package=extra_package, source_strictness=source_strictness, model=model, api_key=api_key, ai_call=ai_call)
    merged_ledger = merge_evidence_ledgers(ledger, extra_ledger)

    merged_package = dict(research_package)
    existing_urls = {str(a.get("url") or "") for a in merged_package.get("source_articles", []) or []}
    merged_package["source_articles"] = list(merged_package.get("source_articles", []) or []) + [a for a in new_articles if str(a.get("url") or "") not in existing_urls]
    merged_package["article_evidence"] = list(merged_package.get("article_evidence", []) or []) + new_evidence

    new_verified = sum(1 for claim in extra_ledger.claims if claim.status == "verified" and claim.support_state == "source_entailed")
    trace = GapRoundTrace(
        attempted_requirements=active_gaps,
        new_source_count=len(extra_ledger.sources),
        new_claim_count=len(extra_ledger.claims),
        new_verified_claim_count=new_verified,
        novelty_exhausted=(new_verified == 0),
    )
    return merged_package, merged_ledger, trace
