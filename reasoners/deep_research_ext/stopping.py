from typing import Literal
from pydantic import BaseModel
from .coverage import CoverageState

StopRecommendation = Literal["continue_research", "eligible_to_stop", "insufficient_verification_signal"]


class StoppingAssessment(BaseModel):
    recommendation: StopRecommendation
    coverage_complete: bool
    novelty_exhausted: bool = False
    novelty_evaluated: bool = False
    rationale: str


def assess_stopping(coverage: CoverageState) -> StoppingAssessment:
    if coverage.verified_coverage_ratio >= 1.0:
        return StoppingAssessment(
            recommendation="eligible_to_stop",
            coverage_complete=True,
            rationale="all Answer Contract requirements are verified",
        )
    if coverage.candidate_coverage_ratio < 1.0:
        return StoppingAssessment(
            recommendation="continue_research",
            coverage_complete=False,
            rationale="one or more Answer Contract requirements have no candidate evidence",
        )
    return StoppingAssessment(
        recommendation="insufficient_verification_signal",
        coverage_complete=False,
        rationale="candidate evidence exists, but exact-source verification is not yet represented in the extension ledger",
    )
