from typing import List, Optional
from pydantic import BaseModel, Field
from .evidence_ledger import EvidenceLedger
from .models import AnswerContract


class ClaimRequirementMap(BaseModel):
    claim_id: str
    requirement_ids: List[str] = Field(default_factory=list)


class ClaimRequirementMapList(BaseModel):
    mappings: List[ClaimRequirementMap] = Field(default_factory=list)


async def map_claims_to_requirements(
    *,
    ledger: EvidenceLedger,
    contract: AnswerContract,
    ai_call,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    batch_size: int = 30,
) -> EvidenceLedger:
    """Map candidate claims to requested requirements. This classifies relevance only, never truth."""
    if not ledger.claims or not contract.requirements:
        return ledger
    if ai_call is None:
        return ledger

    allowed = {item.requirement_id for item in contract.requirements}
    requirement_text = "\n".join(
        f"{item.requirement_id}: {item.question}" for item in contract.requirements
    )

    async def map_batch(batch):
        claim_text = "\n".join(f"{claim.claim_id}: {claim.text}" for claim in batch)
        prompt = f"""
<task>
Map each evidence claim to zero or more research requirements that it is directly relevant to.
This is ONLY a relevance-routing task. Do not judge whether the claim is true, verified, contradicted, or sufficient.
</task>

<requirements>
{requirement_text}
</requirements>

<claims>
{claim_text}
</claims>

<rules>
- Use only requirement IDs listed above.
- Map a claim only when it provides evidence toward that specific requirement.
- Do not map a generic topical claim to every requirement.
- A claim may map to multiple requirements only when it genuinely bears on each one.
- If a claim is irrelevant to all requested requirements, return an empty list for it.
- Return one mapping entry for every claim_id in the batch.
</rules>
"""
        return await ai_call(
            system="You route evidence claims to research requirements without judging truth.",
            user=prompt,
            schema=ClaimRequirementMapList,
            model=model,
            api_key=api_key,
        )

    import asyncio
    batches = [ledger.claims[i:i + batch_size] for i in range(0, len(ledger.claims), batch_size)]
    results = await asyncio.gather(*(map_batch(batch) for batch in batches))
    mapped = {}
    for result in results:
        for item in result.mappings:
            mapped[item.claim_id] = [rid for rid in item.requirement_ids if rid in allowed]

    updated = [
        claim.model_copy(update={"requirement_ids": mapped.get(claim.claim_id, [])})
        for claim in ledger.claims
    ]
    return ledger.model_copy(update={"claims": updated})
