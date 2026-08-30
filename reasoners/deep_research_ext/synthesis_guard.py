from typing import Dict, List
from doc_generation_pipeline import DocumentResponse, DocumentSection, FinalDocument, SourceNote
from .coverage import CoverageState
from .evidence_ledger import EvidenceLedger
from .models import AnswerContract

STRICT_VALUES = {"strict", "verified-only", "verified_only"}


def requires_programmatic_abstention(source_strictness: str, coverage: CoverageState) -> bool:
    return (source_strictness or "").strip().lower() in STRICT_VALUES and coverage.verified_coverage_ratio < 1.0


def build_evidence_only_gap_response(
    *,
    contract: AnswerContract,
    ledger: EvidenceLedger,
    coverage: CoverageState,
    metadata: Dict,
) -> DocumentResponse:
    source_by_id = {source.source_id: source for source in ledger.sources}
    citation_ids = {source.source_id: index for index, source in enumerate(ledger.sources, start=1)}

    sections: List[DocumentSection] = []
    unresolved: List[str] = []
    for requirement in contract.requirements:
        verified = [
            claim for claim in ledger.claims
            if requirement.requirement_id in claim.requirement_ids
            and claim.status == "verified"
            and claim.support_state == "source_entailed"
        ]
        if verified:
            lines = []
            for claim in verified:
                citation = citation_ids.get(claim.source_id)
                suffix = f" [{citation}]" if citation else ""
                lines.append(f"- {claim.text}{suffix}")
            content = "\n".join(lines)
        else:
            unresolved.append(requirement.requirement_id)
            content = "Insufficient verified evidence for this requirement. The system abstains rather than filling the gap from model memory."
        sections.append(DocumentSection(title=f"{requirement.requirement_id}: {requirement.question}", content=content))

    source_notes = [
        SourceNote(
            citation_id=citation_ids[source.source_id],
            title=source.title or source.url,
            domain=source.provenance_group,
            url=source.url,
        )
        for source in ledger.sources
        if source.source_id in citation_ids
    ]

    verified_count = sum(1 for item in coverage.requirements if item.status == "verified")
    total = len(coverage.requirements)
    summary = (
        f"Verified evidence covers {verified_count} of {total} requested requirements. "
        + (f"Unresolved requirements: {', '.join(unresolved)}. " if unresolved else "")
        + "Only source-entailed verified claims are shown below."
    )
    document = FinalDocument(
        document_title="Verified Research — Partial Evidence Report",
        executive_summary=summary,
        sections=sections,
        source_notes=source_notes,
        disclaimers=["This strict-mode report is intentionally incomplete where verified evidence is insufficient."],
    )
    return DocumentResponse(
        mode="verified_partial",
        version="0.1",
        research_package=document.model_dump(),
        metadata=metadata,
    )
