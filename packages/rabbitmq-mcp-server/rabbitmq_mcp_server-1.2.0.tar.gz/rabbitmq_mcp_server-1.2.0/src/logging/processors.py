from __future__ import annotations

from typing import Any, Tuple

from .correlation import get_correlation_id
from .redaction import apply_redaction_to_event

__all__ = ["add_correlation_id", "redact_sensitive_data"]


ProcessorReturn = Tuple[Any, str, dict[str, Any]]


def add_correlation_id(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    correlation_id = get_correlation_id()
    if correlation_id:
        event_dict.setdefault("correlation_id", correlation_id)
    return event_dict


def redact_sensitive_data(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    return apply_redaction_to_event(event_dict)
