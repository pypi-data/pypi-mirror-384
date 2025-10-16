from __future__ import annotations

import re
from typing import Any, Dict

__all__ = ["apply_redaction", "apply_redaction_to_event"]


REDACTION_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"password\s*=\s*['\"]?([^'\"\s]+)"), "[REDACTED]"),
    (re.compile(r"api[_-]?key\s*=\s*['\"]?([^'\"\s]+)"), "[REDACTED]"),
    (re.compile(r"token\s*=\s*['\"]?([^'\"\s]+)"), "[REDACTED]"),
    (re.compile(r"Bearer\s+([A-Za-z0-9\-._~+/]+=*)", re.IGNORECASE), "Bearer [REDACTED]"),
    (re.compile(r"amqp://([^:]+):([^@]+)@"), r"amqp://\1:[REDACTED]@"),
)


SENSITIVE_KEYS = {"password", "api_key", "token", "authorization"}
SENSITIVE_KEY_SUBSTRINGS = ("password", "token", "secret", "api_key")


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    if lowered in SENSITIVE_KEYS:
        return True
    return any(sub in lowered for sub in SENSITIVE_KEY_SUBSTRINGS)


def _redacted_value_for_key(key: str) -> str:
    lowered = key.lower()
    if lowered == "authorization":
        return "Bearer [REDACTED]"
    return "[REDACTED]"


def _redact_string(value: str) -> str:
    redacted = value
    for pattern, replacement in REDACTION_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def _redact_mapping(mapping: Dict[str, Any]) -> Dict[str, Any]:
    redacted: Dict[str, Any] = {}
    for key, value in mapping.items():
        if isinstance(value, str) and _is_sensitive_key(key):
            redacted[key] = _redacted_value_for_key(key)
            continue
        redacted[key] = apply_redaction(value)
    return redacted


def _redact_sequence(sequence: Any) -> Any:
    if isinstance(sequence, list):
        return [apply_redaction(item) for item in sequence]
    if isinstance(sequence, tuple):
        return tuple(apply_redaction(item) for item in sequence)
    return sequence


def apply_redaction(data: Any) -> Any:
    if isinstance(data, str):
        return _redact_string(data)
    if isinstance(data, dict):
        return _redact_mapping(data)
    if isinstance(data, (list, tuple)):
        return _redact_sequence(data)
    return data


def apply_redaction_to_event(event_dict: Dict[str, Any]) -> Dict[str, Any]:
    # structlog may pass a proxy mapping; convert to a plain dict for consistent processing
    if not isinstance(event_dict, dict):
        event_dict = dict(event_dict)
    return _redact_mapping(event_dict)
