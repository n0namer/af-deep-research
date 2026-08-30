from typing import Dict, List, Literal
from pydantic import BaseModel, Field
from .evidence_ledger import EvidenceLedger
from .models import AnswerContract

CoverageStatus = Literal["no_candidate_evidence", "candidate_evidence_present", "verified", "explicit_gap"]


class RequirementCoverage(BaseModel):
    requirement_id: str
    status: CoverageStatus
    candidate_claim_count: int = 0
    independent_source_groups: int = 0


class CoverageState(BaseModel):
    requirements: List[RequirementCoverage] = Field(default_factory=list)
    candidate_coverage_ratio: float = 0.0
    verified_coverage_ratio: float = 0.0
    epistemic_note: str = "candidate coverage is not verification"


def assess_candidate_coverage(contract: AnswerContract, ledger: EvidenceLedger) -> CoverageState:
    states: List[RequirementCoverage] = []
    for requirement in contract.requirements:
        claims = [c for c in ledger.claims if requirement.requirement_id in c.requirement_ids]
        groups = {c.source_independence_group for c in claims if c.source_independence_group}
        verified = [c for c in claims if c.status == "verified" and c.support_state == "source_entailed"]
        status: CoverageStatus
        if verified:
            status = "verified"
        elif claims:
            status = "candidate_evidence_present"
        else:
            status = "no_candidate_evidence"
        states.append(RequirementCoverage(
            requirement_id=requirement.requirement_id,
            status=status,
            candidate_claim_count=len(claims),
            independent_source_groups=len(groups),
        ))
    total = len(states) or 1
    candidate = sum(1 for state in states if state.status in {"candidate_evidence_present", "verified"})
    verified = sum(1 for state in states if state.status == "verified")
    return CoverageState(
        requirements=states,
        candidate_coverage_ratio=round(candidate / total, 4),
        verified_coverage_ratio=round(verified / total, 4),
    )
