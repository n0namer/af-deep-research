from typing import Awaitable, Callable, List, Optional
from pydantic import BaseModel, Field
from doc_generation_pipeline import AIAssessmentList, FactForAdjudication, _classify_source, _normalize_source_strictness, adjudicate_evidence_ai


class DraftClaim(BaseModel):
    claim_id: str
    text: str
    citation_ids: List[int] = Field(default_factory=list)


class DraftClaimList(BaseModel):
    claims: List[DraftClaim] = Field(default_factory=list)


class UnsupportedDraftClaim(BaseModel):
    claim_id: str
    text: str
    citation_ids: List[int] = Field(default_factory=list)
    reason: str


class FinalVerificationState(BaseModel):
    material_claim_count: int = 0
    supported_claim_count: int = 0
    unsupported_claims: List[UnsupportedDraftClaim] = Field(default_factory=list)
    passed: bool = False


def _render_document_text(document_package: dict) -> str:
    parts = []
    summary = str(document_package.get("executive_summary") or "").strip()
    if summary:
        parts.append(f"Executive summary:\n{summary}")
    for section in document_package.get("sections", []) or []:
        title = str(section.get("title") or "").strip()
        content = str(section.get("content") or "").strip()
        if content:
            parts.append(f"Section: {title}\n{content}")
    return "\n\n".join(parts)


async def extract_material_draft_claims(*, document_package: dict, ai_call, model: Optional[str] = None, api_key: Optional[str] = None) -> DraftClaimList:
    text = _render_document_text(document_package)
    if not text:
        return DraftClaimList()
    prompt = f"""
<task>
Extract every externally verifiable material factual claim from the research draft below.
Split compound sentences into atomic claims when different evidence would be needed.
For each claim, preserve the proposition and list numeric citation markers attached to or clearly supporting it.
Do not judge truth. Do not add facts. Omit non-verifiable opinions.
</task>
<draft>{text}</draft>
<rules>
- claim_id: D1, D2, D3, ...
- citation_ids are integers from markers such as [1].
- If a material factual claim has no citation, return an empty list.
- Include material factual claims from the executive summary and sections.
</rules>
"""
    return await ai_call(system="You extract atomic factual claims and citation markers without judging truth.", user=prompt, schema=DraftClaimList, model=model, api_key=api_key)


async def verify_final_document(
    *,
    document_package: dict,
    research_package: dict,
    source_strictness: str,
    ai_call,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    claim_extractor: Callable[..., Awaitable[DraftClaimList]] = extract_material_draft_claims,
    adjudicator: Callable[..., Awaitable[AIAssessmentList]] = adjudicate_evidence_ai,
) -> FinalVerificationState:
    claims = await claim_extractor(
        document_package=document_package,
        ai_call=ai_call,
        model=model,
        api_key=api_key,
    )
    normalized = _normalize_source_strictness(source_strictness)
    source_notes = {
        int(note.get("citation_id")): note
        for note in document_package.get("source_notes", []) or []
        if note.get("citation_id") is not None
    }
    articles_by_url = {
        str(article.get("url") or ""): article
        for article in research_package.get("source_articles", []) or []
    }

    unsupported: List[UnsupportedDraftClaim] = []
    supported_count = 0
    for claim in claims.claims:
        if not claim.citation_ids:
            unsupported.append(
                UnsupportedDraftClaim(
                    claim_id=claim.claim_id,
                    text=claim.text,
                    citation_ids=[],
                    reason="material_claim_has_no_citation",
                )
            )
            continue

        candidates = []
        for citation_id in claim.citation_ids:
            note = source_notes.get(int(citation_id))
            if note is None:
                continue
            url = str(note.get("url") or "")
            article = articles_by_url.get(url)
            if article is None:
                continue
            source_type, reliability = _classify_source(url)
            candidates.append(
                FactForAdjudication(
                    fact_id=f"{claim.claim_id}:S{citation_id}",
                    content=claim.text,
                    source_id=int(article.get("id") or citation_id),
                    source_type=source_type,
                    source_reliability_score=reliability,
                    source_text=str(article.get("content") or ""),
                )
            )

        if not candidates:
            unsupported.append(
                UnsupportedDraftClaim(
                    claim_id=claim.claim_id,
                    text=claim.text,
                    citation_ids=claim.citation_ids,
                    reason="cited_source_not_available_for_verification",
                )
            )
            continue

        result = await adjudicator(
            candidates,
            normalized,
            model=model,
            api_key=api_key,
            ai_call=ai_call,
        )
        if any(item.is_allowed and item.is_source_supported for item in result.assessments):
            supported_count += 1
        else:
            unsupported.append(
                UnsupportedDraftClaim(
                    claim_id=claim.claim_id,
                    text=claim.text,
                    citation_ids=claim.citation_ids,
                    reason="cited_evidence_does_not_entail_claim",
                )
            )

    total = len(claims.claims)
    return FinalVerificationState(
        material_claim_count=total,
        supported_claim_count=supported_count,
        unsupported_claims=unsupported,
        passed=(len(unsupported) == 0),
    )
