from typing import Literal
from pydantic import BaseModel
from .coverage import CoverageState

StopRecommendation = Literal["continue_research", "eligible_to_stop", "insufficient_verification_signal", "stop_with_explicit_gaps"]

class StoppingAssessment(BaseModel):
    recommendation: StopRecommendation
    coverage_complete: bool
    novelty_exhausted: bool = False
    novelty_evaluated: bool = False
    rationale: str

def assess_stopping(coverage: CoverageState, *, novelty_evaluated: bool = False, novelty_exhausted: bool = False) -> StoppingAssessment:
    if coverage.verified_coverage_ratio >= 1.0:
        return StoppingAssessment(recommendation="eligible_to_stop", coverage_complete=True, novelty_evaluated=novelty_evaluated, novelty_exhausted=novelty_exhausted, rationale="all Answer Contract requirements are verified")
    if novelty_evaluated and novelty_exhausted:
        return StoppingAssessment(recommendation="stop_with_explicit_gaps", coverage_complete=False, novelty_evaluated=True, novelty_exhausted=True, rationale="a targeted gap round produced no new verified evidence; unresolved requirements must remain explicit gaps")
    if coverage.candidate_coverage_ratio < 1.0:
        return StoppingAssessment(recommendation="continue_research", coverage_complete=False, novelty_evaluated=novelty_evaluated, novelty_exhausted=novelty_exhausted, rationale="one or more Answer Contract requirements have no candidate evidence")
    return StoppingAssessment(recommendation="insufficient_verification_signal", coverage_complete=False, novelty_evaluated=novelty_evaluated, novelty_exhausted=novelty_exhausted, rationale="candidate evidence exists, but one or more requirements lack verified source-entailed support")
