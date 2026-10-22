"""Focused source-identity tests for the Jina provider."""

from __future__ import annotations

import pytest

from skills.search.jina import _parse_result


def test_jina_parses_https_source_identity():
    result = _parse_result(
        {
            "title": "Canonical source",
            "url": "https://example.test/source",
            "content": "source content",
        }
    )

    assert result.title == "Canonical source"
    assert result.url == "https://example.test/source"
    assert result.content == "source content"


def test_jina_parses_optional_published_time():
    result = _parse_result(
        {
            "title": "Dated source",
            "url": "https://example.test/source",
            "publishedTime": "2026-01-02T03:04:05Z",
        }
    )

    assert result.published_time is not None
    assert result.published_time.isoformat() == "2026-01-02T03:04:05+00:00"


@pytest.mark.parametrize(
    "item",
    [
        {"title": "missing URL", "content": "text"},
        {"url": "https://example.test/source", "content": "text"},
        {"title": "   ", "url": "https://example.test/source", "content": "text"},
    ],
)
def test_jina_rejects_missing_or_blank_identity(item):
    with pytest.raises(ValueError):
        _parse_result(item)


def test_jina_rejects_non_https_url():
    with pytest.raises(ValueError):
        _parse_result(
            {
                "title": "Insecure source",
                "url": "http://example.test/source",
                "content": "text",
            }
        )


def test_jina_rejects_non_object_result():
    with pytest.raises(TypeError):
        _parse_result(["not", "an", "object"])
