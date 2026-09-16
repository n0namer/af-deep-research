from .models import AnswerContract, MethodSelection, ResearchTopology, VerificationLevel

PACK_METHODS = {
    "general": ["decision_framing", "broad_first_lead_following", "claim_source_binding"],
    "technical": ["first_principles", "production_reality_check", "claim_source_binding"],
    "market": ["reachable_market", "jtbd", "triangulation"],
    "domain": ["value_chain", "regulatory_enforcement", "triangulation"],
    "competitive": ["trajectory_analysis", "customer_voice", "triangulation"],
    "user_voice": ["jtbd", "review_mining", "workaround_as_latent_demand"],
    "academic_lit": ["survey_first", "bidirectional_citation_chasing", "replication_check"],
    "selection": ["hard_gates", "weighted_mcda", "reversal_conditions"],
}


def _topology(contract: AnswerContract, research_scope: int, research_focus: int) -> ResearchTopology:
    if contract.research_pack == "selection" or research_scope >= 4:
        return "breadth_first"
    if research_focus >= 4:
        return "depth_first"
    if research_scope <= 2 and research_focus <= 2:
        return "straightforward"
    return "hybrid"


def _verification(source_strictness: str, research_focus: int, requested: str) -> VerificationLevel:
    requested = (requested or "auto").lower()
    if requested in {"normal", "high", "max"}:
        return requested  # type: ignore[return-value]
    if source_strictness in {"strict", "verified-only", "verified_only"} and research_focus >= 4:
        return "max"
    if source_strictness in {"strict", "verified-only", "verified_only"} or research_focus >= 3:
        return "high"
    return "normal"


def select_methodology(contract: AnswerContract, *, research_scope: int = 3, research_focus: int = 3, verification_level: str = "auto") -> MethodSelection:
    topology = _topology(contract, research_scope, research_focus)
    verification = _verification(contract.source_strictness, research_focus, verification_level)
    methods = list(PACK_METHODS.get(contract.research_pack, PACK_METHODS["general"]))
    methods.extend(["research_firewall", "coverage_tracking"])
    if verification in {"high", "max"}:
        methods.extend(["independent_source_verification", "fresh_context_verification"])
    if verification == "max":
        methods.append("adversarial_red_team")
    return MethodSelection(
        research_pack=contract.research_pack,
        topology=topology,
        verification_level=verification,
        active_methods=methods,
        rationale_tags=[f"pack:{contract.research_pack}", f"scope:{research_scope}", f"focus:{research_focus}", f"strictness:{contract.source_strictness}"],
    )
