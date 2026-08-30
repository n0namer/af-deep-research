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


def test_verification_bridge_promotes_only_source_entailed_verified_claims():
    from doc_generation_pipeline import AIAssessment, AIAssessmentList
    from reasoners.deep_research_ext.coverage import assess_candidate_coverage
    from reasoners.deep_research_ext.evidence_ledger import build_evidence_ledger
    from reasoners.deep_research_ext.stopping import assess_stopping
    from reasoners.deep_research_ext.verification_bridge import verify_ledger_claims

    package = {
        "source_articles": [{"id": 1, "title": "RFC", "url": "https://rfc-editor.org/rfc/rfc9000", "content_hash": "x", "content": "RFC 9000 specifies QUIC."}],
        "article_evidence": [{"article_id": 1, "facts": ["RFC 9000 specifies QUIC.", "Google invented HTTP/3."], "quotes": []}],
    }
    ledger = build_evidence_ledger(package, ["R1"])

    async def fake_adjudicator(batch, strictness, **kwargs):
        assert strictness == "verified-only"
        return AIAssessmentList(assessments=[
            AIAssessment(fact_id=batch[0].fact_id, is_allowed=True, is_source_supported=True, is_verified=True, disagreement_score=0.0),
            AIAssessment(fact_id=batch[1].fact_id, is_allowed=True, is_source_supported=False, is_verified=True, disagreement_score=0.0),
        ])

    verified = asyncio.run(verify_ledger_claims(ledger=ledger, research_package=package, source_strictness="strict", adjudicator=fake_adjudicator))
    assert verified.claims[0].status == "verified"
    assert verified.claims[0].support_state == "source_entailed"
    assert verified.claims[1].status == "overturned"
    assert verified.claims[1].support_state == "unsupported"

    contract = build_answer_contract("What does RFC 9000 specify?", research_type="technical", source_strictness="strict")
    coverage = assess_candidate_coverage(contract, verified)
    assert coverage.verified_coverage_ratio == 1.0
    assert assess_stopping(coverage).recommendation == "eligible_to_stop"


def test_verification_bridge_marks_supported_conflict_as_disputed_not_verified():
    from doc_generation_pipeline import AIAssessment, AIAssessmentList
    from reasoners.deep_research_ext.coverage import assess_candidate_coverage
    from reasoners.deep_research_ext.evidence_ledger import build_evidence_ledger
    from reasoners.deep_research_ext.verification_bridge import verify_ledger_claims

    package = {
        "source_articles": [{"id": 1, "title": "Source", "url": "https://rfc-editor.org/rfc/rfc9000", "content_hash": "x", "content": "Claim text."}],
        "article_evidence": [{"article_id": 1, "facts": ["Claim text."], "quotes": []}],
    }
    ledger = build_evidence_ledger(package, ["R1"])

    async def fake_adjudicator(batch, strictness, **kwargs):
        return AIAssessmentList(assessments=[AIAssessment(fact_id=batch[0].fact_id, is_allowed=True, is_source_supported=True, is_verified=True, disagreement_score=0.8)])

    verified = asyncio.run(verify_ledger_claims(ledger=ledger, research_package=package, source_strictness="strict", adjudicator=fake_adjudicator))
    assert verified.claims[0].status == "disputed"
    assert verified.claims[0].support_state == "source_entailed"
    contract = build_answer_contract("Question", source_strictness="strict")
    assert assess_candidate_coverage(contract, verified).verified_coverage_ratio == 0.0


def test_continue_research_preserves_strictness_contract_and_child_policy():
    import ast
    from pathlib import Path

    tree = ast.parse(Path('/app/main.py').read_text())
    fn = next(node for node in tree.body if isinstance(node, ast.AsyncFunctionDef) and node.name == 'continue_research')
    arg_names = [arg.arg for arg in fn.args.args]
    assert 'source_strictness' in arg_names

    child_calls = [node for node in ast.walk(fn) if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 'execute_intelligence_stream_comprehensive']
    assert child_calls
    assert all(any(kw.arg == 'source_strictness' for kw in call.keywords) for call in child_calls)
    assert any(getattr(node.func, 'id', None) == '_augment_queries_for_source_policy' for node in ast.walk(fn) if isinstance(node, ast.Call))


def test_answer_contract_decomposition_splits_multi_part_request_without_answers():
    from reasoners.deep_research_ext.requirement_decomposition import RequirementProposal, RequirementProposalList, decompose_answer_contract

    contract = build_answer_contract(
        "Using primary sources, identify the RFC numbers for HTTP/3 and QUIC transport, the month/year each was published, and the direct standards lineage from Google QUIC to IETF QUIC. Distinguish protocol ancestry from standard publication.",
        source_strictness="strict",
        research_type="technical",
    )

    async def fake_ai(**kwargs):
        return RequirementProposalList(requirements=[
            RequirementProposal(question="Identify the RFC number for QUIC transport.", required_source_class="primary_standard"),
            RequirementProposal(question="Identify the publication month/year for the QUIC transport RFC.", required_source_class="primary_standard"),
            RequirementProposal(question="Identify the RFC number for HTTP/3.", required_source_class="primary_standard"),
            RequirementProposal(question="Identify the publication month/year for the HTTP/3 RFC.", required_source_class="primary_standard"),
            RequirementProposal(question="Establish the standards lineage from Google QUIC to IETF QUIC using primary evidence.", claim_type="lineage", required_source_class="primary_or_first_party"),
            RequirementProposal(question="Distinguish protocol ancestry from the publication of the resulting standards.", claim_type="distinction", required_source_class="primary_or_authoritative"),
        ])

    decomposed = asyncio.run(decompose_answer_contract(contract, ai_call=fake_ai))
    assert [r.requirement_id for r in decomposed.requirements] == ["R1", "R2", "R3", "R4", "R5", "R6"]
    assert "9000" not in " ".join(r.question for r in decomposed.requirements)
    assert "9114" not in " ".join(r.question for r in decomposed.requirements)
    assert decomposed.requirements[4].claim_type == "lineage"


def test_claim_requirement_mapping_routes_relevance_without_changing_truth_state():
    from reasoners.deep_research_ext.evidence_ledger import build_evidence_ledger
    from reasoners.deep_research_ext.models import ResearchRequirement
    from reasoners.deep_research_ext.requirement_mapping import ClaimRequirementMap, ClaimRequirementMapList, map_claims_to_requirements

    contract = build_answer_contract("Research standards", research_type="technical")
    contract = contract.model_copy(update={"requirements": [
        ResearchRequirement(requirement_id="R1", question="What RFC specifies QUIC transport?"),
        ResearchRequirement(requirement_id="R2", question="When was that RFC published?"),
        ResearchRequirement(requirement_id="R3", question="What is the Google QUIC to IETF QUIC lineage?"),
    ]})
    package = {
        "source_articles": [{"id": 1, "title": "RFC", "url": "https://rfc-editor.org/rfc/rfc9000", "content_hash": "x"}],
        "article_evidence": [{"article_id": 1, "facts": [
            "RFC 9000 specifies QUIC transport.",
            "RFC 9000 was published in May 2021.",
            "This source says nothing about Google QUIC lineage.",
        ], "quotes": []}],
    }
    ledger = build_evidence_ledger(package, [])
    before = [(c.status, c.support_state) for c in ledger.claims]

    async def fake_ai(**kwargs):
        return ClaimRequirementMapList(mappings=[
            ClaimRequirementMap(claim_id="A1-C1", requirement_ids=["R1"]),
            ClaimRequirementMap(claim_id="A1-C2", requirement_ids=["R2"]),
            ClaimRequirementMap(claim_id="A1-C3", requirement_ids=[]),
        ])

    mapped = asyncio.run(map_claims_to_requirements(ledger=ledger, contract=contract, ai_call=fake_ai))
    assert mapped.claims[0].requirement_ids == ["R1"]
    assert mapped.claims[1].requirement_ids == ["R2"]
    assert mapped.claims[2].requirement_ids == []
    assert [(c.status, c.support_state) for c in mapped.claims] == before


def test_requirement_level_coverage_does_not_overcount_verified_claims():
    from reasoners.deep_research_ext.coverage import assess_candidate_coverage
    from reasoners.deep_research_ext.evidence_ledger import EvidenceClaim, EvidenceLedger
    from reasoners.deep_research_ext.models import ResearchRequirement

    contract = build_answer_contract("multi requirement")
    contract = contract.model_copy(update={"requirements": [
        ResearchRequirement(requirement_id="R1", question="A"),
        ResearchRequirement(requirement_id="R2", question="B"),
        ResearchRequirement(requirement_id="R3", question="C"),
    ]})
    ledger = EvidenceLedger(
        sources=[],
        created_at="now",
        claims=[
            EvidenceClaim(claim_id="C1", text="supports A", source_id=1, requirement_ids=["R1"], status="verified", support_state="source_entailed"),
            EvidenceClaim(claim_id="C2", text="candidate B", source_id=1, requirement_ids=["R2"], status="unverified", support_state="candidate_extracted"),
        ],
    )
    coverage = assess_candidate_coverage(contract, ledger)
    assert coverage.verified_coverage_ratio == 0.3333
    assert coverage.candidate_coverage_ratio == 0.6667
    assert [r.status for r in coverage.requirements] == ["verified", "candidate_evidence_present", "no_candidate_evidence"]


def test_strict_incomplete_coverage_uses_programmatic_abstention_report():
    from reasoners.deep_research_ext.coverage import assess_candidate_coverage
    from reasoners.deep_research_ext.evidence_ledger import EvidenceClaim, EvidenceLedger, EvidenceSource
    from reasoners.deep_research_ext.models import ResearchRequirement
    from reasoners.deep_research_ext.synthesis_guard import build_evidence_only_gap_response, requires_programmatic_abstention

    contract = build_answer_contract("multi", source_strictness="strict")
    contract = contract.model_copy(update={"requirements": [
        ResearchRequirement(requirement_id="R1", question="Identify QUIC RFC"),
        ResearchRequirement(requirement_id="R2", question="Establish lineage"),
    ]})
    ledger = EvidenceLedger(
        created_at="now",
        sources=[EvidenceSource(source_id=1, title="RFC", url="https://rfc-editor.org/rfc/rfc9000", content_hash="x", source_class="primary_standard", provenance_group="rfc-editor.org", retrieved_at="now")],
        claims=[EvidenceClaim(claim_id="C1", text="RFC 9000 specifies QUIC.", source_id=1, requirement_ids=["R1"], status="verified", support_state="source_entailed")],
    )
    coverage = assess_candidate_coverage(contract, ledger)
    assert requires_programmatic_abstention("strict", coverage) is True
    response = build_evidence_only_gap_response(contract=contract, ledger=ledger, coverage=coverage, metadata={"x": 1})
    assert response.mode == "verified_partial"
    assert "RFC 9000 specifies QUIC. [1]" in response.research_package["sections"][0]["content"]
    assert "Insufficient verified evidence" in response.research_package["sections"][1]["content"]
    assert "R2" in response.research_package["executive_summary"]


def test_mixed_mode_does_not_force_programmatic_abstention():
    from reasoners.deep_research_ext.coverage import CoverageState
    from reasoners.deep_research_ext.synthesis_guard import requires_programmatic_abstention
    assert requires_programmatic_abstention("mixed", CoverageState(candidate_coverage_ratio=0.0, verified_coverage_ratio=0.0)) is False


def test_verified_pipeline_skips_writer_when_strict_requirement_is_unverified(monkeypatch):
    from reasoners.deep_research_ext import verified_pipeline as vp
    from reasoners.deep_research_ext.evidence_ledger import EvidenceClaim, EvidenceLedger, EvidenceSource
    from reasoners.deep_research_ext.models import ExtensionTrace, ResearchRequirement
    from reasoners.deep_research_ext.methodology import select_methodology

    contract = build_answer_contract("multi", source_strictness="strict")
    contract = contract.model_copy(update={"requirements": [
        ResearchRequirement(requirement_id="R1", question="Identify RFC"),
        ResearchRequirement(requirement_id="R2", question="Establish lineage"),
    ]})
    trace = ExtensionTrace(answer_contract=contract, method_selection=select_methodology(contract))
    ledger = EvidenceLedger(
        created_at="now",
        sources=[EvidenceSource(source_id=1, title="RFC", url="https://rfc-editor.org/rfc/rfc9000", content_hash="x", source_class="primary_standard", provenance_group="rfc-editor.org", retrieved_at="now")],
        claims=[EvidenceClaim(claim_id="C1", text="RFC 9000 specifies QUIC.", source_id=1, requirement_ids=["R1"], status="verified", support_state="source_entailed")],
    )

    async def fake_prepare(**kwargs):
        return SimpleNamespace(research_package={"source_articles": [], "article_evidence": []}, metadata={"research": True})

    async def fake_map(**kwargs):
        return ledger

    async def fake_verify(**kwargs):
        return ledger

    writer_called = {"value": False}
    async def fake_writer(**kwargs):
        writer_called["value"] = True
        raise AssertionError("writer must not run for strict incomplete coverage")

    monkeypatch.setattr(vp, "build_evidence_ledger", lambda package, requirement_ids: ledger)
    monkeypatch.setattr(vp, "map_claims_to_requirements", fake_map)
    monkeypatch.setattr(vp, "verify_ledger_claims", fake_verify)

    result = asyncio.run(vp.execute_verified_pipeline(
        trace=trace,
        prepare_research_package=fake_prepare,
        generate_document_from_package=fake_writer,
        upstream_kwargs={
            "query": "multi", "mode": "general", "research_focus": 1, "research_scope": 1,
            "max_research_loops": 1, "num_parallel_streams": 1, "tension_lens": "balanced",
            "source_strictness": "strict", "evidence_style": "standard",
            "analysis_depth": "ANALYTICAL_BRIEF", "model": None, "api_key": None,
        },
        ai_call=lambda **kwargs: None,
    ))
    assert writer_called["value"] is False
    assert result.mode == "verified_partial"
    assert result.metadata["verified_research_extension"]["mode"] == "programmatic_partial_abstention"


def test_final_verifier_rejects_uncited_material_claim():
    from doc_generation_pipeline import AIAssessment, AIAssessmentList
    from reasoners.deep_research_ext.final_verifier import DraftClaim, DraftClaimList, verify_final_document
    document = {
        "executive_summary": "RFC 9000 was published in May 2021 [1]. Google invented HTTP/3.",
        "sections": [],
        "source_notes": [{"citation_id": 1, "title": "RFC 9000", "url": "https://rfc-editor.org/rfc/rfc9000", "domain": "rfc-editor.org"}],
    }
    research = {"source_articles": [{"id": 1, "title": "RFC 9000", "url": "https://rfc-editor.org/rfc/rfc9000", "content": "RFC 9000 was published in May 2021."}]}
    async def fake_extract(**kwargs):
        return DraftClaimList(claims=[
            DraftClaim(claim_id="D1", text="RFC 9000 was published in May 2021.", citation_ids=[1]),
            DraftClaim(claim_id="D2", text="Google invented HTTP/3.", citation_ids=[]),
        ])
    async def fake_adjudicator(batch, strictness, **kwargs):
        return AIAssessmentList(assessments=[AIAssessment(fact_id=batch[0].fact_id, is_allowed=True, is_source_supported=True, is_verified=True, disagreement_score=0.0)])
    state = asyncio.run(verify_final_document(document_package=document, research_package=research, source_strictness="strict", ai_call=lambda **kwargs: None, claim_extractor=fake_extract, adjudicator=fake_adjudicator))
    assert state.material_claim_count == 2
    assert state.supported_claim_count == 1
    assert state.passed is False
    assert state.unsupported_claims[0].reason == "material_claim_has_no_citation"


def test_final_verifier_accepts_when_every_material_claim_is_cited_and_entailed():
    from doc_generation_pipeline import AIAssessment, AIAssessmentList
    from reasoners.deep_research_ext.final_verifier import DraftClaim, DraftClaimList, verify_final_document
    document = {
        "executive_summary": "RFC 9000 specifies QUIC [1].",
        "sections": [],
        "source_notes": [{"citation_id": 1, "title": "RFC", "url": "https://rfc-editor.org/rfc/rfc9000", "domain": "rfc-editor.org"}],
    }
    research = {"source_articles": [{"id": 1, "title": "RFC", "url": "https://rfc-editor.org/rfc/rfc9000", "content": "RFC 9000 specifies QUIC."}]}
    async def fake_extract(**kwargs):
        return DraftClaimList(claims=[DraftClaim(claim_id="D1", text="RFC 9000 specifies QUIC.", citation_ids=[1])])
    async def fake_adjudicator(batch, strictness, **kwargs):
        return AIAssessmentList(assessments=[AIAssessment(fact_id=batch[0].fact_id, is_allowed=True, is_source_supported=True, is_verified=True, disagreement_score=0.0)])
    state = asyncio.run(verify_final_document(document_package=document, research_package=research, source_strictness="strict", ai_call=lambda **kwargs: None, claim_extractor=fake_extract, adjudicator=fake_adjudicator))
    assert state.passed is True
    assert state.supported_claim_count == 1


def test_verified_pipeline_rejects_strict_writer_draft_when_final_verifier_fails(monkeypatch):
    from doc_generation_pipeline import DocumentResponse
    from reasoners.deep_research_ext import verified_pipeline as vp
    from reasoners.deep_research_ext.evidence_ledger import EvidenceClaim, EvidenceLedger, EvidenceSource
    from reasoners.deep_research_ext.final_verifier import FinalVerificationState, UnsupportedDraftClaim
    from reasoners.deep_research_ext.models import ExtensionTrace
    from reasoners.deep_research_ext.methodology import select_methodology

    contract = build_answer_contract("one", source_strictness="strict")
    trace = ExtensionTrace(answer_contract=contract, method_selection=select_methodology(contract))
    ledger = EvidenceLedger(
        created_at="now",
        sources=[EvidenceSource(source_id=1, title="RFC", url="https://rfc-editor.org/rfc/rfc9000", content_hash="x", source_class="primary_standard", provenance_group="rfc-editor.org", retrieved_at="now")],
        claims=[EvidenceClaim(claim_id="C1", text="RFC 9000 specifies QUIC.", source_id=1, requirement_ids=["R1"], status="verified", support_state="source_entailed")],
    )
    async def fake_prepare(**kwargs):
        return SimpleNamespace(research_package={"source_articles": [], "article_evidence": []}, metadata={})
    async def fake_map(**kwargs): return ledger
    async def fake_verify(**kwargs): return ledger
    async def fake_writer(**kwargs):
        return DocumentResponse(mode="general", version="1", research_package={"document_title":"x","executive_summary":"Unsupported fact.","sections":[],"source_notes":[],"disclaimers":[]}, metadata={})
    async def fake_final(**kwargs):
        return FinalVerificationState(material_claim_count=1, supported_claim_count=0, passed=False, unsupported_claims=[UnsupportedDraftClaim(claim_id="D1", text="Unsupported fact.", citation_ids=[], reason="material_claim_has_no_citation")])
    monkeypatch.setattr(vp, "build_evidence_ledger", lambda package, requirement_ids: ledger)
    monkeypatch.setattr(vp, "map_claims_to_requirements", fake_map)
    monkeypatch.setattr(vp, "verify_ledger_claims", fake_verify)
    monkeypatch.setattr(vp, "verify_final_document", fake_final)
