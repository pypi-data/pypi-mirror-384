"""Schemas auxiliares para integração com MCP."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=5, ge=1, le=50)


class PaginationMetadata(BaseModel):
    page: int
    page_size: int
    total: int


class SearchItem(BaseModel):
    operation_id: str
    score: float
    metadata: Dict[str, Any] | None = None


class SearchResult(BaseModel):
    items: List[SearchItem]
    pagination: PaginationMetadata


class MCPError(BaseModel):
    code: str
    message: str
    details: Dict[str, Any] | None = None


class MCPToolResult(BaseModel):
    success: bool
    result: Dict[str, Any] | None = None
    error: MCPError | None = None
    metadata: Dict[str, Any] | None = None


class OperationSchema(BaseModel):
    operation_id: str
    name: str
    description: str
    category: str
    async_mode: bool = Field(alias="async")
    input_schema: Dict[str, Any]
    output_schema: Dict[str, Any]
    examples: List[Dict[str, Any]] | None = None
    errors: List[Dict[str, Any]] | None = None

    model_config = ConfigDict(populate_by_name=True)


__all__ = [
    "PaginationParams",
    "PaginationMetadata",
    "SearchResult",
    "SearchItem",
    "MCPToolResult",
    "MCPError",
    "OperationSchema",
]
