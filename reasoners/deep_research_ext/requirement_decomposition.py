from typing import List, Optional
import asyncio
import os
import re
from pydantic import BaseModel, Field
from .models import AnswerContract, ResearchRequirement


class RequirementProposal(BaseModel):
    question: str
    role: str = "answer"
    claim_type: str = "factual"
    required_source_class: str = "appropriate_authoritative"
    temporal_requirement: Optional[str] = None


class RequirementProposalList(BaseModel):
    requirements: List[RequirementProposal] = Field(default_factory=list)


async def decompose_answer_contract(
    contract: AnswerContract,
    *,
    ai_call,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    max_requirements: int = 8,
) -> AnswerContract:
    """Decompose a user request into independently coverable requirements without answering it."""
    if ai_call is None:
        return contract

    prompt = f"""
<task>
Decompose the user's research request into the smallest useful set of independently verifiable research requirements.
Do NOT answer the questions. Do NOT introduce facts, dates, names, causal claims, or conclusions that are not already requested by the user.
Preserve explicit source-quality and temporal constraints.
</task>

<user_query>{contract.query}</user_query>
<research_pack>{contract.research_pack}</research_pack>
<source_strictness>{contract.source_strictness}</source_strictness>
<as_of>{contract.as_of or ''}</as_of>

<rules>
- Return 1 to {max_requirements} requirements.
- Each requirement should cover one independently judgeable part of the requested answer.
- Split identifiers, dates, lineage/causality, comparisons, and distinctions when the user asks for them separately.
- If the user asks for a distinction between concepts, represent that distinction as its own requirement.
- Do not merge separate requested entities when separate evidence may be needed.
- required_source_class should describe the kind of evidence needed, not a specific answer.
- If the user's request contains an explicit factual premise that later explanation depends on, add a separate requirement with role="premise_check" to verify/challenge that premise before synthesis. Otherwise role="answer".
- Do not invent hidden premises; only mark propositions explicitly asserted or necessarily presupposed by the user's wording.
</rules>
"""
    profile = (os.getenv("DR_EVAL_PROFILE", "semantic") or "semantic").strip().lower()
    try:
        proposal = await asyncio.wait_for(
            ai_call(
                system="You decompose research requests into evidence requirements without answering them.",
                user=prompt,
                schema=RequirementProposalList,
                model=model,
                api_key=api_key,
            ),
            timeout=(float(os.getenv("DR_REQUIREMENT_DECOMPOSITION_TIMEOUT_SECONDS", "25")) if profile == "resilience" else None),
        )
    except Exception:
        if profile != "resilience":
            raise
        query = " ".join(contract.query.split())
        premise_patterns = (
            r"\bwhy\s+.+?\s+(?:replaced|caused|led to|resulted in|triggered)\b",
            r"\bexplain\s+why\s+.+?\s+(?:replaced|caused|led to|resulted in|triggered)\b",
        )
        if any(re.search(pattern, query, flags=re.IGNORECASE) for pattern in premise_patterns):
            fallback = [
                ResearchRequirement(
                    requirement_id="R1",
                    question=f"Verify the explicit factual premise in the user's request before explaining it: {query}",
                    role="premise_check",
                    claim_type="factual",
                    required_source_class="appropriate_authoritative",
                    temporal_requirement=contract.as_of,
                    completion_policy="supported_or_explicit_gap",
                ),
                ResearchRequirement(
                    requirement_id="R2",
                    question=query,
                    role="answer",
                    claim_type="factual",
                    required_source_class="appropriate_authoritative",
                    temporal_requirement=contract.as_of,
                    completion_policy="supported_or_explicit_gap",
                ),
            ]
            return contract.model_copy(update={"requirements": fallback})
        return contract
    items = list(proposal.requirements or [])[:max_requirements]
    if not items:
        return contract

    requirements = []
    for index, item in enumerate(items, start=1):
        requirements.append(
            ResearchRequirement(
                requirement_id=f"R{index}",
                question=" ".join(item.question.split()),
                role="premise_check" if item.role == "premise_check" else "answer",
                claim_type=item.claim_type or "factual",
                required_source_class=item.required_source_class or "appropriate_authoritative",
                temporal_requirement=item.temporal_requirement or contract.as_of,
                completion_policy="supported_or_explicit_gap",
            )
        )
    return contract.model_copy(update={"requirements": requirements})
