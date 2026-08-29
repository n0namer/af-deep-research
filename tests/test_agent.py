"""Smoke tests for the current Deep Research AgentField surface."""

import asyncio

import pytest
from pydantic import BaseModel

import main
from doc_generation_pipeline import (
    AIAssessmentList,
    _classify_source,
    _normalize_source_strictness,
    _source_allowed_by_policy,
    _writer_grounding_rule,
    generate_document_from_package_core,
)
from reasoners.research_orchestrator import _parse_llm_json


def test_agent_identity() -> None:
    assert main.app.node_id == "meta_deep_research"
    assert main.app.version == "3.0.0"


def test_current_reasoner_surface_is_importable() -> None:
    assert callable(main.merge_entity_pair)
    assert callable(main.detect_entity_duplicates_batch)
    assert callable(main.detect_relationship_duplicates_batch)
    assert callable(main.merge_relationship_pair)


def test_entity_schema_contract() -> None:
    assert issubclass(main.Entity, BaseModel)
    entity = main.Entity(name="OpenAI", type="organization", summary="AI research company")
    assert entity.name == "OpenAI"
    assert entity.type == "organization"
    assert entity.summary == "AI research company"


def test_merged_entity_schema_contract() -> None:
    assert issubclass(main.MergedEntity, BaseModel)
    fields = set(main.MergedEntity.model_fields)
    assert {"name", "type", "summary"}.issubset(fields)


def test_dynamic_ai_override_preserves_configured_api_base(monkeypatch) -> None:
    observed = {}

    async def fake_ai(*args, **kwargs):
        observed.update(kwargs)
        return "ok"

    monkeypatch.setattr(main.app, "ai", fake_ai)
    original_params = dict(main.litellm_params)
    main.litellm_params["api_base"] = "https://example.invalid/v1"
    try:
        result = asyncio.run(main.ai_with_dynamic_params(model="openai/test-model"))
    finally:
        main.litellm_params.clear()
        main.litellm_params.update(original_params)

    assert result == "ok"
    assert observed["model"] == "openai/test-model"
    assert observed["api_base"] == "https://example.invalid/v1"


def test_ai_config_uses_configured_api_base() -> None:
    assert main.ai_config.api_base == main.ollama_base_url


def test_parse_llm_json_accepts_think_wrapped_object() -> None:
    payload = '<think>reasoning that must be ignored</think>\n{"complexity_level":"complex","parallel_beneficial":true}'
    parsed = _parse_llm_json(payload)
    assert parsed["complexity_level"] == "complex"
    assert parsed["parallel_beneficial"] is True


def test_parse_llm_json_accepts_fenced_array_with_trailing_text() -> None:
    payload = '```json\n["q1", "q2", "q3"]\n```\nextra commentary'
    assert _parse_llm_json(payload) == ["q1", "q2", "q3"]


def test_parse_llm_json_rejects_non_json_payload() -> None:
    with pytest.raises(ValueError, match="No JSON object or array found"):
        _parse_llm_json("analysis only, no structured payload")


def test_source_strictness_aliases_match_public_contract() -> None:
    assert _normalize_source_strictness("strict") == "verified-only"
    assert _normalize_source_strictness("mixed") == "mixed"
    assert _normalize_source_strictness("permissive") == "exploratory"


def test_official_ietf_source_is_primary_and_allowed_in_strict_mode() -> None:
    source_type, score = _classify_source("https://datatracker.ietf.org/doc/html/rfc9114")
    assert source_type == "primary_doc"
    assert score == 1.0
    assert _source_allowed_by_policy(source_type, "verified-only") is True
    assert _source_allowed_by_policy("blog", "verified-only") is False


def _minimal_package(url: str) -> dict:
    return {
        "query": "test query",
        "core_thesis": "test",
        "key_discoveries": [],
        "confidence_assessment": "test",
        "entities": [],
        "relationships": [],
        "observed_causal_chains": [],
        "hypothesized_implications": [],
        "next_inquiry_probes": [],
        "source_articles": [
            {"id": 1, "title": "source", "url": url, "content": "fact", "content_hash": "x"}
        ],
        "article_evidence": [
            {"article_id": 1, "relevance_summary": "relevant", "facts": ["fact"], "quotes": []}
        ],
    }


def test_strict_mode_fails_closed_when_only_blog_evidence_exists() -> None:
    async def should_not_call_ai(*args, **kwargs):
        raise AssertionError("strict pre-filter should reject blog evidence before AI adjudication")

    with pytest.raises(ValueError, match="No eligible evidence remains"):
        asyncio.run(
            generate_document_from_package_core(
                _minimal_package("https://example.com/post"),
                "test query",
                source_strictness="strict",
                ai_call=should_not_call_ai,
            )
        )


def test_strict_mode_does_not_permissively_restore_rejected_primary_evidence() -> None:
    async def reject_all(*args, **kwargs):
        return AIAssessmentList(assessments=[])

    with pytest.raises(ValueError, match="No evidence passed verified-only"):
        asyncio.run(
            generate_document_from_package_core(
                _minimal_package("https://datatracker.ietf.org/doc/html/rfc9114"),
                "test query",
                source_strictness="strict",
                ai_call=reject_all,
            )
        )


def test_strict_research_adds_primary_source_companion_queries() -> None:
    queries = ["HTTP/3 RFC 9114", "HTTP/3 RFC 9114", "QUIC RFC 9000"]
    assert main._augment_queries_for_source_policy(queries, "strict") == [
        "HTTP/3 RFC 9114",
        "HTTP/3 RFC 9114 official primary source",
        "QUIC RFC 9000",
        "QUIC RFC 9000 official primary source",
    ]


def test_mixed_research_does_not_expand_search_queries() -> None:
    queries = ["HTTP/3 RFC 9114", "QUIC RFC 9000"]
    assert main._augment_queries_for_source_policy(queries, "mixed") == queries


def test_strict_writer_rule_forbids_background_knowledge_fill() -> None:
    rule = _writer_grounding_rule("strict")
    assert "Every externally verifiable factual claim MUST be" in rule
    assert "Do not fill gaps from background knowledge" in rule
    assert "evidence is insufficient" in rule


def test_query_fair_retrieval_interleaves_before_article_cap() -> None:
    q1 = [{"url": f"https://q1/{i}", "content": "x"} for i in range(5)]
    q2 = [{"url": f"https://q2/{i}", "content": "x"} for i in range(5)]
    q3 = [{"url": f"https://q3/{i}", "content": "x"} for i in range(5)]
    urls = [r["url"] for r in main._interleave_unique_search_results([q1, q2, q3])[:6]]
    assert urls == [
        "https://q1/0",
        "https://q2/0",
        "https://q3/0",
        "https://q1/1",
        "https://q2/1",
        "https://q3/1",
    ]
