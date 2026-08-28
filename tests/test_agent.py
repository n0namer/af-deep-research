"""Smoke tests for the current Deep Research AgentField surface."""

import asyncio

from pydantic import BaseModel

import main


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
