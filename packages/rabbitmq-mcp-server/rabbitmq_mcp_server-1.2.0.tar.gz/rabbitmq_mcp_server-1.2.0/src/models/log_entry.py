from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

__all__ = ["LogLevel", "LogCategory", "OperationResult", "LogEntry"]

MAX_MESSAGE_LENGTH = 100_000
TRUNCATION_SUFFIX = "...[truncated]"
SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"
TOOL_NAME_PATTERN = r"^[a-z\-]+$"


class LogLevel(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"


class LogCategory(str, Enum):
    CONNECTION = "Connection"
    OPERATION = "Operation"
    ERROR = "Error"
    SECURITY = "Security"
    PERFORMANCE = "Performance"


class OperationResult(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class LogEntry(BaseModel):
    """Structured log entry validated against the documented schema."""

    model_config = ConfigDict(extra="forbid")

    schema_version: str = Field(
        default="1.0.0",
        pattern=SEMVER_PATTERN,
        description="Semantic version for the log entry schema",
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp in UTC with trailing Z",
    )
    level: LogLevel
    category: LogCategory
    correlation_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)

    tool_name: Optional[str] = Field(None, pattern=TOOL_NAME_PATTERN)
    operation_id: Optional[str] = None
    duration_ms: Optional[float] = Field(None, ge=0)
    result: Optional[OperationResult] = None
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, value: str) -> str:
        if not value.endswith("Z"):
            raise ValueError("timestamp must be in UTC and end with 'Z'")
        try:
            datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be ISO 8601 compliant") from exc
        return value

    @field_validator("schema_version")
    @classmethod
    def validate_schema_version(cls, value: str) -> str:
        major_str, *_ = value.split(".")
        try:
            major = int(major_str)
        except ValueError as exc:
            raise ValueError("schema_version major component must be numeric") from exc
        if major != 1:
            raise ValueError(
                "unsupported schema_version major component for parser v1.0.0"
            )
        return value

    @field_validator("message")
    @classmethod
    def truncate_message(cls, value: str) -> str:
        if len(value) <= MAX_MESSAGE_LENGTH:
            return value
        return value[:MAX_MESSAGE_LENGTH] + TRUNCATION_SUFFIX

    @field_validator("error_type")
    @classmethod
    def validate_error_type(cls, value: Optional[str], info) -> Optional[str]:
        if value is None:
            return None
        level = info.data.get("level")
        if level is not None and level is not LogLevel.ERROR:
            raise ValueError("error_type requires level ERROR")
        return value
