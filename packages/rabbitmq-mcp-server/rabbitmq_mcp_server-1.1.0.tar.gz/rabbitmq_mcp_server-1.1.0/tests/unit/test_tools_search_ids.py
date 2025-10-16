from __future__ import annotations

import pytest
from pytest import MonkeyPatch

from rabbitmq_mcp_connection.tools import search_ids
from rabbitmq_mcp_connection.tools.search_ids import (
    KeywordFallbackBackend,
    handle_search_ids,
)


@pytest.fixture(autouse=True)
def _force_keyword_backend(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(search_ids, "_BACKEND", KeywordFallbackBackend())


def test_handle_search_ids_requires_query() -> None:
    result = handle_search_ids("")
    assert result.success is False
    assert result.error is not None
    assert result.error.code == "INVALID_QUERY"


def test_handle_search_ids_returns_results() -> None:
    result = handle_search_ids("connection")
    assert result.success is True
    assert result.result is not None
    items = result.result["items"]
    assert len(items) > 0
    assert all("operation_id" in item for item in items)
    assert result.metadata == {"backend": "KeywordFallbackBackend"}