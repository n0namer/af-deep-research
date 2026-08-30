import asyncio
from typing import Awaitable, Callable, Optional
from doc_generation_pipeline import AIAssessmentList, FactForAdjudication, _classify_source, _normalize_source_strictness, adjudicate_evidence_ai
from .evidence_ledger import EvidenceLedger

ADJUDICATION_BATCH_SIZE = 25

async def verify_ledger_claims(*, ledger: EvidenceLedger, research_package: dict, source_strictness: str, model: Optional[str] = None, api_key: Optional[str] = None, adjudicator: Callable[..., Awaitable[AIAssessmentList]] = adjudicate_evidence_ai) -> EvidenceLedger:
    normalized = _normalize_source_strictness(source_strictness)
    articles = {int(a.get('id')): a for a in research_package.get('source_articles', []) if a.get('id') is not None}
    facts = []
    for claim in ledger.claims:
        article = articles.get(claim.source_id)
        if article is None:
            continue
        source_type, reliability = _classify_source(str(article.get('url') or ''))
        facts.append(FactForAdjudication(fact_id=claim.claim_id, content=claim.text, source_id=claim.source_id, source_type=source_type, source_reliability_score=reliability, source_text=str(article.get('content') or '')))
    if normalized == 'verified-only' and not facts:
        raise ValueError('No eligible evidence remains for verified ledger adjudication.')
    batches = [facts[start:start + ADJUDICATION_BATCH_SIZE] for start in range(0, len(facts), ADJUDICATION_BATCH_SIZE)]
    results = await asyncio.gather(*(adjudicator(batch, normalized, model=model, api_key=api_key) for batch in batches))
    assessments = [assessment for result in results for assessment in result.assessments]
    by_id = {a.fact_id: a for a in assessments}
    updated = []
    for claim in ledger.claims:
        a = by_id.get(claim.claim_id)
        if a is None:
            updated.append(claim)
            continue
        base = {'admissible': bool(a.is_allowed), 'source_verified': bool(a.is_verified), 'disagreement_score': float(a.disagreement_score)}
        if not a.is_allowed:
            updated.append(claim.model_copy(update=base)); continue
        if not a.is_source_supported:
            updated.append(claim.model_copy(update={**base, 'status': 'overturned', 'support_state': 'unsupported'})); continue
        status = 'disputed' if float(a.disagreement_score) >= 0.5 else ('verified' if a.is_verified else 'unverified')
        updated.append(claim.model_copy(update={**base, 'status': status, 'support_state': 'source_entailed'}))
    return ledger.model_copy(update={'claims': updated})
