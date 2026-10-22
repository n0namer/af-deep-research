import asyncio
from typing import Awaitable, Callable, Optional
from doc_generation_pipeline import AIAssessmentList, FactForAdjudication, _classify_source, _normalize_source_strictness, adjudicate_evidence_ai
from .evidence_ledger import EvidenceLedger

ADJUDICATION_BATCH_SIZE = 25


def _eligible_articles(ledger: EvidenceLedger, research_package: dict) -> dict[int, dict]:
    ledger_sources = {}
    duplicate_ledger_source_ids = set()
    for source in ledger.sources:
        if source.source_id in ledger_sources:
            duplicate_ledger_source_ids.add(source.source_id)
        ledger_sources[source.source_id] = source

    articles = [article for article in research_package.get('source_articles', []) if article.get('id') is not None]
    urls = [str(article.get('url') or '') for article in articles]
    reused_urls = {url for url in urls if url and urls.count(url) > 1}
    article_ids = []
    for article in articles:
        try:
            article_ids.append(int(article['id']))
        except (TypeError, ValueError):
            article_ids.append(None)
    duplicate_article_ids = {
        source_id
        for source_id in article_ids
        if source_id is not None and article_ids.count(source_id) > 1
    }

    eligible = {}
    for article, source_id in zip(articles, article_ids):
        if source_id is None:
            continue
        source = ledger_sources.get(source_id)
        url = str(article.get('url') or '')
        content_hash = str(article.get('content_hash') or '')
        if (
            source is None
            or source_id in duplicate_ledger_source_ids
            or source_id in duplicate_article_ids
            or url in reused_urls
        ):
            continue
        if source.url != url or source.content_hash != content_hash:
            continue
        eligible[source_id] = article
    return eligible


def validate_fact_ownership(*, fact_id: str, source_id: int, claim_source_id: int, eligible_source_ids: set[int]) -> None:
    """Enforce one-to-one claim/fact ownership before external adjudication."""
    if not isinstance(fact_id, str) or not fact_id.strip():
        raise ValueError("fact_id must be a non-empty string")
    if not isinstance(source_id, int) or isinstance(source_id, bool):
        raise ValueError("source_id must be an integer")
    if source_id != claim_source_id:
        raise ValueError("fact source ownership does not match claim ownership")
    if source_id not in eligible_source_ids:
        raise ValueError("fact source is not an eligible ledger source")


async def verify_ledger_claims(*, ledger: EvidenceLedger, research_package: dict, source_strictness: str, model: Optional[str] = None, api_key: Optional[str] = None, ai_call=None, adjudicator: Callable[..., Awaitable[AIAssessmentList]] = adjudicate_evidence_ai) -> EvidenceLedger:
    normalized = _normalize_source_strictness(source_strictness)
    articles = _eligible_articles(ledger, research_package)
    facts = []
    for claim in ledger.claims:
        article = articles.get(claim.source_id)
        if article is None:
            continue
        source_type, reliability = _classify_source(str(article.get('url') or ''))
        facts.append(FactForAdjudication(fact_id=claim.claim_id, content=claim.text, source_id=claim.source_id, source_type=source_type, source_reliability_score=reliability, source_text=str(article.get('content') or '')))
    if normalized == 'verified-only' and not facts:
        raise ValueError('No eligible evidence remains for verified ledger adjudication.')
    eligible_source_ids = set(articles)
    for fact in facts:
        claim = next(claim for claim in ledger.claims if claim.claim_id == fact.fact_id)
        validate_fact_ownership(
            fact_id=fact.fact_id,
            source_id=fact.source_id,
            claim_source_id=claim.source_id,
            eligible_source_ids=eligible_source_ids,
        )
    batches = [facts[start:start + ADJUDICATION_BATCH_SIZE] for start in range(0, len(facts), ADJUDICATION_BATCH_SIZE)]
    results = await asyncio.gather(*(
        adjudicator(batch, normalized, model=model, api_key=api_key, **({'ai_call': ai_call} if ai_call is not None else {}))
        for batch in batches
    ), return_exceptions=True)
    if any(isinstance(result, Exception) for result in results):
        return ledger
    assessments = [assessment for result in results for assessment in result.assessments]
    expected_sources = {}
    duplicate_fact_ids = set()
    for fact in facts:
        if fact.fact_id in expected_sources:
            duplicate_fact_ids.add(fact.fact_id)
        expected_sources[fact.fact_id] = fact.source_id
    assessments_by_id = {}
    for assessment in assessments:
        assessments_by_id.setdefault(assessment.fact_id, []).append(assessment)
    by_id = {
        fact_id: candidates[0]
        for fact_id, candidates in assessments_by_id.items()
        if fact_id in expected_sources
        and fact_id not in duplicate_fact_ids
        and len(candidates) == 1
        and getattr(candidates[0], 'source_id', None) == expected_sources[fact_id]
    }
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
    claims = tuple(updated) if isinstance(ledger.claims, tuple) else updated
    return ledger.model_copy(update={'claims': claims})
