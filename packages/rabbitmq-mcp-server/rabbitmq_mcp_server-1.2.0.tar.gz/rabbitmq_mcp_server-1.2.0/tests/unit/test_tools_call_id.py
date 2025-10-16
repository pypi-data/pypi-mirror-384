from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from pytest import MonkeyPatch

from rabbitmq_mcp_connection.schemas.connection import ConnectionState
from rabbitmq_mcp_connection.tools import call_id
from rabbitmq_mcp_connection.tools.call_id import handle_call_id, reset_tool_state


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    reset_tool_state()
    yield
    reset_tool_state()


@pytest.fixture(autouse=True)
def _stub_connection(monkeypatch: MonkeyPatch) -> None:
    async def fake_connect(self: call_id.ConnectionManager) -> None:
        self.state = ConnectionState.CONNECTED
        self.channel = SimpleNamespace(is_closed=False)

        async def close_channel() -> None:
            self.channel.is_closed = True

        self.channel.close = close_channel  # type: ignore[attr-defined]

        self.connection = SimpleNamespace(
            is_closed=False,
            server_properties={"product": "RabbitMQ"},
        )

        async def close_connection() -> None:
            self.connection.is_closed = True

        self.connection.close = close_connection  # type: ignore[attr-defined]
        self.retry_policy.reset()
        self._metadata.connected_since = datetime.now(UTC)
        self._metadata.server_properties = self.connection.server_properties

    monkeypatch.setattr(call_id.ConnectionManager, "connect", fake_connect)


@pytest.mark.asyncio
async def test_handle_call_id_unknown_operation() -> None:
    result = await handle_call_id("invalid.operation")
    assert result.success is False
    assert result.error is not None
    assert result.error.code == "UNKNOWN_OPERATION"


@pytest.mark.asyncio
async def test_handle_call_id_connect_success() -> None:
    result = await handle_call_id("connection.connect", {})
    assert result.success is True
    assert result.result is not None
    assert result.result["connected"] is True
    assert "connection_url" in result.result


@pytest.mark.asyncio
async def test_handle_call_id_disconnect_without_connection() -> None:
    result = await handle_call_id("connection.disconnect", {})
    assert result.success is False
    assert result.error is not None
    assert result.error.code == "NOT_CONNECTED"


@pytest.mark.asyncio
async def test_handle_call_id_disconnect_success() -> None:
    await handle_call_id("connection.connect", {})
    result = await handle_call_id("connection.disconnect", {})
    assert result.success is True
    assert result.result is not None
    assert result.result["disconnected"] is True


@pytest.mark.asyncio
async def test_handle_call_id_health_check() -> None:
    await handle_call_id("connection.connect", {})
    result = await handle_call_id("connection.health_check", {})
    assert result.success is True
    assert result.result is not None
    assert result.result["is_connected"] is True


@pytest.mark.asyncio
async def test_handle_call_id_get_status() -> None:
    await handle_call_id("connection.connect", {})
    result = await handle_call_id("connection.get_status", {})
    assert result.success is True
    assert result.result is not None
    assert result.result["state"] in {state.value for state in ConnectionState}


@pytest.mark.asyncio
async def test_handle_call_id_pool_stats() -> None:
    await handle_call_id("connection.connect", {})
    result = await handle_call_id("pool.get_stats", {})
    assert result.success is True
    assert result.result is not None
    assert "max_size" in result.result
