import re
from typing import Optional
from .models import AnswerContract, ResearchPack, ResearchRequirement

_SELECTION_RE = re.compile(r"\b(vs\.?|versus|compare|comparison|choose|select|which should|лучше|выбрать|сравн)\b", re.I)
_ACADEMIC_RE = re.compile(r"\b(paper|study|studies|literature|meta-analysis|systematic review|academic|научн|исследован|литератур)\b", re.I)
_TECH_RE = re.compile(r"\b(api|sdk|rfc|protocol|database|architecture|framework|library|repository|github|техничес|архитект|протокол)\b", re.I)
_MARKET_RE = re.compile(r"\b(market|tam|sam|som|pricing|segment|gtm|рынок|цена|сегмент)\b", re.I)
_COMPETITIVE_RE = re.compile(r"\b(competitor|competition|competitive|конкурент)\b", re.I)
_USER_VOICE_RE = re.compile(r"\b(review|reviews|complaint|workaround|jtbd|customer voice|отзыв|жалоб|пользовател)\b", re.I)
_DOMAIN_RE = re.compile(r"\b(regulation|regulator|standard|industry|value chain|регуляц|стандарт|отрасл)\b", re.I)
_TEMPORAL_RE = re.compile(r"\b(now|current|latest|today|as of|currently|сейчас|текущ|последн|на сегодня)\b", re.I)


def infer_research_pack(query: str, requested: str = "auto") -> ResearchPack:
    requested = (requested or "auto").strip().lower().replace("-", "_")
    allowed = {"general","technical","market","domain","competitive","user_voice","academic_lit","selection"}
    if requested in allowed:
        return requested  # type: ignore[return-value]
    if _SELECTION_RE.search(query): return "selection"
    if _ACADEMIC_RE.search(query): return "academic_lit"
    if _COMPETITIVE_RE.search(query): return "competitive"
    if _USER_VOICE_RE.search(query): return "user_voice"
    if _MARKET_RE.search(query): return "market"
    if _TECH_RE.search(query): return "technical"
    if _DOMAIN_RE.search(query): return "domain"
    return "general"


def build_answer_contract(query: str, *, decision: Optional[str] = None, research_type: str = "auto", source_strictness: str = "mixed", as_of: Optional[str] = None) -> AnswerContract:
    """Build a deterministic observable contract without changing upstream semantics."""
    clean_query = " ".join(str(query or "").split())
    if not clean_query:
        raise ValueError("query must be non-empty")
    pack = infer_research_pack(clean_query, research_type)
    temporal = as_of or ("current_at_execution" if _TEMPORAL_RE.search(clean_query) else None)
    requirement = ResearchRequirement(
        requirement_id="R1",
        question=clean_query,
        claim_type="decision" if pack == "selection" else "factual_and_analytical",
        required_source_class="primary_or_authoritative_where_applicable" if source_strictness in {"strict","verified-only","verified_only"} else "appropriate_authoritative",
        temporal_requirement=temporal,
    )
    return AnswerContract(
        query=clean_query,
        decision=decision or None,
        research_pack=pack,
        as_of=temporal,
        requirements=[requirement],
        source_strictness=source_strictness,
    )
