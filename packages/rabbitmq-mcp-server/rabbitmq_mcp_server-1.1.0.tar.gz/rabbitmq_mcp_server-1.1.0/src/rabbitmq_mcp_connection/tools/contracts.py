"""Utilitários para carregar contratos MCP."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict

from rabbitmq_mcp_connection.schemas.mcp import OperationSchema

CONTRACTS_DIR = Path(__file__).resolve().parent.parent / "contracts"
CONNECTION_OPERATIONS_PATH = CONTRACTS_DIR / "connection-operations.json"


@lru_cache(maxsize=1)
def load_connection_operations() -> Dict[str, OperationSchema]:
    if not CONNECTION_OPERATIONS_PATH.exists():
        raise FileNotFoundError(
            f"Arquivo de contrato não encontrado: {CONNECTION_OPERATIONS_PATH}"
        )

    data = json.loads(CONNECTION_OPERATIONS_PATH.read_text(encoding="utf-8"))
    operations = {}
    for entry in data.get("operations", []):
        schema = OperationSchema(**entry)
        operations[schema.operation_id] = schema
    return operations


__all__ = ["load_connection_operations"]
