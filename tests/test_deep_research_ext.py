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


def test_evidence_ledger_keeps_extracted_facts_unverified_and_tracks_provenance():
    from reasoners.deep_research_ext.evidence_ledger import build_evidence_ledger

    package = {
        "source_articles": [
            {"id": 1, "title": "RFC", "url": "https://www.rfc-editor.org/rfc/rfc9000", "content_hash": "h1"},
            {"id": 2, "title": "RFC copy", "url": "https://rfc-editor.org/info/rfc9000", "content_hash": "h2"},
        ],
        "article_evidence": [
            {"article_id": 1, "facts": ["RFC 9000 defines QUIC version 1."], "quotes": []},
            {"article_id": 2, "facts": ["RFC 9000 was published in May 2021."], "quotes": []},
        ],
    }
    ledger = build_evidence_ledger(package, ["R1"])
    assert len(ledger.claims) == 2
    assert all(c.status == "unverified" for c in ledger.claims)
    assert all(c.support_state == "candidate_extracted" for c in ledger.claims)
    assert ledger.summary()["independent_provenance_groups"] == 1
    assert ledger.sources[0].source_class == "primary_standard"


def test_candidate_coverage_is_not_verification_and_does_not_allow_stop():
    from reasoners.deep_research_ext.coverage import assess_candidate_coverage
    from reasoners.deep_research_ext.evidence_ledger import build_evidence_ledger
    from reasoners.deep_research_ext.stopping import assess_stopping

    contract = build_answer_contract("What does RFC 9000 specify?", research_type="technical")
    ledger = build_evidence_ledger(
        {
            "source_articles": [{"id": 1, "title": "RFC", "url": "https://rfc-editor.org/rfc/rfc9000", "content_hash": "x"}],
            "article_evidence": [{"article_id": 1, "facts": ["RFC 9000 defines QUIC."], "quotes": []}],
        },
        ["R1"],
    )
    coverage = assess_candidate_coverage(contract, ledger)
    stop = assess_stopping(coverage)
    assert coverage.candidate_coverage_ratio == 1.0
    assert coverage.verified_coverage_ratio == 0.0
    assert coverage.requirements[0].status == "candidate_evidence_present"
    assert stop.recommendation == "insufficient_verification_signal"
    assert stop.coverage_complete is False


def test_no_candidate_evidence_recommends_more_research():
    from reasoners.deep_research_ext.coverage import assess_candidate_coverage
    from reasoners.deep_research_ext.evidence_ledger import EvidenceLedger
    from reasoners.deep_research_ext.stopping import assess_stopping

    contract = build_answer_contract("Unknown question")
    ledger = EvidenceLedger(sources=[], claims=[], created_at="now")
    coverage = assess_candidate_coverage(contract, ledger)
    assert assess_stopping(coverage).recommendation == "continue_research"
