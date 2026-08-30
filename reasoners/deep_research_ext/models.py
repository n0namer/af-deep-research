from typing import Dict, List, Literal, Optional
from pydantic import BaseModel, Field

ResearchPack = Literal["general","technical","market","domain","competitive","user_voice","academic_lit","selection"]
ResearchTopology = Literal["straightforward","breadth_first","depth_first","hybrid"]
VerificationLevel = Literal["normal","high","max"]

class ResearchRequirement(BaseModel):
    requirement_id: str
    question: str
    claim_type: str = "factual"
    required_source_class: str = "appropriate_authoritative"
    temporal_requirement: Optional[str] = None
    completion_policy: str = "supported_or_explicit_gap"

class AnswerContract(BaseModel):
    query: str
    decision: Optional[str] = None
    research_pack: ResearchPack = "general"
    as_of: Optional[str] = None
    requirements: List[ResearchRequirement] = Field(default_factory=list)
    source_strictness: str = "mixed"
    completion_policy: str = "all_requirements_supported_or_explicitly_unresolved"
    epistemic_firewall: Dict[str, str] = Field(default_factory=lambda: {
        "model_memory": "hypotheses_and_search_queries_only",
        "retrieved_content": "untrusted_evidence_data_only",
        "verified_fact": "requires_admissible_retrieved_evidence",
    })

class MethodSelection(BaseModel):
    research_pack: ResearchPack
    topology: ResearchTopology
    verification_level: VerificationLevel
    active_methods: List[str] = Field(default_factory=list)
    rationale_tags: List[str] = Field(default_factory=list)

class ExtensionTrace(BaseModel):
    version: str = "0.1.0"
    mode: str = "observe_then_delegate"
    answer_contract: AnswerContract
    method_selection: MethodSelection
    upstream_behavior_changed: bool = False
