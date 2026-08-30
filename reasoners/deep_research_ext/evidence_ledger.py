from datetime import datetime, timezone
from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from .source_policy import classify_source, provenance_group

ClaimStatus = Literal["unverified", "verified", "disputed", "overturned"]
SupportState = Literal["candidate_extracted", "source_entailed", "unsupported", "contradicted"]


class EvidenceSource(BaseModel):
    source_id: int
    title: str
    url: str
    content_hash: str
    source_class: str
    provenance_group: str
    retrieved_at: str


class EvidenceClaim(BaseModel):
    claim_id: str
    text: str
    source_id: int
    requirement_ids: List[str] = Field(default_factory=list)
    status: ClaimStatus = "unverified"
    support_state: SupportState = "candidate_extracted"
    admissible: Optional[bool] = None
    source_verified: Optional[bool] = None
    disagreement_score: float = 0.0
    exact_span: Optional[str] = None
    source_independence_group: Optional[str] = None


class EvidenceLedger(BaseModel):
    sources: List[EvidenceSource] = Field(default_factory=list)
    claims: List[EvidenceClaim] = Field(default_factory=list)
    created_at: str

    def summary(self) -> Dict[str, object]:
        by_status: Dict[str, int] = {}
        by_class: Dict[str, int] = {}
        for claim in self.claims:
            by_status[claim.status] = by_status.get(claim.status, 0) + 1
        for source in self.sources:
            by_class[source.source_class] = by_class.get(source.source_class, 0) + 1
        return {
            "source_count": len(self.sources),
            "claim_count": len(self.claims),
            "claim_status_counts": by_status,
            "source_class_counts": by_class,
            "independent_provenance_groups": len({s.provenance_group for s in self.sources if s.provenance_group != "unknown"}),
            "verification_state": "candidate_only_until_exact_source_adjudication",
        }


def build_evidence_ledger(research_package: dict, requirement_ids: List[str]) -> EvidenceLedger:
    articles = {int(a.get("id")): a for a in research_package.get("source_articles", []) if a.get("id") is not None}
    retrieved_at = datetime.now(timezone.utc).isoformat()
    sources: List[EvidenceSource] = []
    for article_id, article in sorted(articles.items()):
        url = str(article.get("url") or "")
        sources.append(EvidenceSource(
            source_id=article_id,
            title=str(article.get("title") or ""),
            url=url,
            content_hash=str(article.get("content_hash") or ""),
            source_class=classify_source(url),
            provenance_group=provenance_group(url),
            retrieved_at=retrieved_at,
        ))

    source_group = {s.source_id: s.provenance_group for s in sources}
    claims: List[EvidenceClaim] = []
    for evidence in research_package.get("article_evidence", []):
        article_id = int(evidence.get("article_id"))
        for index, fact in enumerate(evidence.get("facts", []) or [], start=1):
            text = " ".join(str(fact or "").split())
            if not text:
                continue
            claims.append(EvidenceClaim(
                claim_id=f"A{article_id}-C{index}",
                text=text,
                source_id=article_id,
                requirement_ids=list(requirement_ids),
                source_independence_group=source_group.get(article_id),
            ))
    return EvidenceLedger(sources=sources, claims=claims, created_at=retrieved_at)
