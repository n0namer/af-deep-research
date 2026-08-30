import asyncio
from types import SimpleNamespace

from reasoners.deep_research_ext.methodology import select_methodology
from reasoners.deep_research_ext.models import ExtensionTrace
from reasoners.deep_research_ext.task_contract import build_answer_contract
from reasoners.deep_research_ext.upstream_adapter import UpstreamDeepResearchAdapter


def test_answer_contract_infers_technical_pack_and_firewall():
    contract = build_answer_contract(
        "Using primary sources, identify RFC 9000 and RFC 9114 publication dates",
        source_strictness="strict",
    )
    assert contract.research_pack == "technical"
    assert contract.requirements[0].required_source_class == "primary_or_authoritative_where_applicable"
    assert contract.epistemic_firewall["model_memory"] == "hypotheses_and_search_queries_only"
    assert contract.epistemic_firewall["verified_fact"] == "requires_admissible_retrieved_evidence"


def test_selection_pack_uses_breadth_topology_and_mcda_methods():
    contract = build_answer_contract("Compare PostgreSQL vs MySQL and choose the better fit")
    methods = select_methodology(contract, research_scope=3, research_focus=3)
    assert contract.research_pack == "selection"
    assert methods.topology == "breadth_first"
    assert "weighted_mcda" in methods.active_methods
    assert "reversal_conditions" in methods.active_methods


def test_strict_high_focus_selects_max_verification_and_red_team():
    contract = build_answer_contract(
        "Evaluate the architecture and RFC compatibility",
        source_strictness="strict",
        research_type="technical",
    )
    methods = select_methodology(contract, research_scope=3, research_focus=5)
    assert methods.verification_level == "max"
    assert "fresh_context_verification" in methods.active_methods
    assert "adversarial_red_team" in methods.active_methods


def test_upstream_adapter_preserves_payload_and_adds_trace_only_to_metadata():
    payload = {"document": "baseline", "facts": [1, 2, 3]}
    seen = {}

    async def fake_upstream(**kwargs):
        seen.update(kwargs)
        return SimpleNamespace(mode="general", version="x", research_package=payload, metadata={"baseline": True})

    contract = build_answer_contract("Research QUIC", research_type="technical")
    methods = select_methodology(contract)
    trace = ExtensionTrace(answer_contract=contract, method_selection=methods)
    result = asyncio.run(
        UpstreamDeepResearchAdapter(fake_upstream).execute(
            trace=trace,
            upstream_kwargs={"query": "Research QUIC", "source_strictness": "mixed"},
        )
    )
    assert seen == {"query": "Research QUIC", "source_strictness": "mixed"}
    assert result.research_package is payload
    assert result.metadata["baseline"] is True
    ext = result.metadata["verified_research_extension"]
    assert ext["upstream_behavior_changed"] is False
    assert ext["answer_contract"]["research_pack"] == "technical"


def test_main_registers_additive_verified_reasoner_with_extension_schema():
    import main

    reasoner = next(r for r in main.app.reasoners if r["id"] == "execute_verified_deep_research")
    props = reasoner["input_schema"]["properties"]
    assert "research_type" in props
    assert "verification_level" in props
    assert "decision" in props
    assert "as_of" in props
    assert any(r["id"] == "execute_deep_research" for r in main.app.reasoners)
