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
