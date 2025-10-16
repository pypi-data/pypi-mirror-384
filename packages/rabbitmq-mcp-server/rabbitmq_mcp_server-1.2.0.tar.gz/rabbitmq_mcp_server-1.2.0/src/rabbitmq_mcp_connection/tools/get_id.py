"""Implementação do MCP tool get-id."""

from __future__ import annotations

from typing import Any, Dict

from rabbitmq_mcp_connection.schemas.mcp import MCPError, MCPToolResult
from rabbitmq_mcp_connection.tools.contracts import load_connection_operations


class OperationNotFoundError(KeyError):
    """Erro quando uma operação solicitada não existe."""


def get_operation_schema(operation_id: str) -> Dict[str, Any]:
    operations = load_connection_operations()
    if operation_id not in operations:
        raise OperationNotFoundError(operation_id)

    schema = operations[operation_id]
    return schema.model_dump(by_alias=True)


def handle_get_id(operation_id: str) -> MCPToolResult:
    try:
        schema = get_operation_schema(operation_id)
        return MCPToolResult(success=True, result={"schema": schema})
    except OperationNotFoundError as exc:
        return MCPToolResult(
            success=False,
            error=MCPError(
                code="OPERATION_NOT_FOUND",
                message=f"Operation '{exc.args[0]}' not found",
            ),
        )


__all__ = ["handle_get_id", "get_operation_schema", "OperationNotFoundError"]
