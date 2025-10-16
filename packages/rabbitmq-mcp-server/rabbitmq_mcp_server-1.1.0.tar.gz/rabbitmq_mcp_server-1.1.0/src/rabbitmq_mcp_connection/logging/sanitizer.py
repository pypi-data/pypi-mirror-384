"""Utilidades para sanitização de dados sensíveis em logs."""

from __future__ import annotations

import re
from typing import Any, Mapping

AMQP_URL_PATTERN = re.compile(r"(amqp://[^:]+:)([^@]+)(@)")


def sanitize_amqp_urls(value: str) -> str:
    """Substitui credenciais em URLs AMQP pela forma sanitizada."""

    return AMQP_URL_PATTERN.sub(r"\1***\3", value)


def sanitize_value(value: Any) -> Any:
    if isinstance(value, str):
        return sanitize_amqp_urls(value)
    if isinstance(value, Mapping):
        return {key: sanitize_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [sanitize_value(item) for item in value]
    return value
