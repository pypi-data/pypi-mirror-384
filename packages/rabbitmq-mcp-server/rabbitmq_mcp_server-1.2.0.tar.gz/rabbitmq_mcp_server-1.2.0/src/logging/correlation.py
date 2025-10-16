from __future__ import annotations

import contextvars
import secrets
import time
import uuid
from typing import Optional

__all__ = [
    "generate_correlation_id",
    "set_correlation_id",
    "get_correlation_id",
    "reset_correlation_id",
]


_correlation_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


def generate_correlation_id() -> str:
    try:
        return str(uuid.uuid4())
    except Exception:
        timestamp = int(time.time() * 1_000_000)
        random_part = secrets.token_hex(3)
        return f"fallback-{timestamp}-{random_part}"


def set_correlation_id(value: Optional[str] = None) -> str:
    correlation_id = value or generate_correlation_id()
    _correlation_var.set(correlation_id)
    return correlation_id


def get_correlation_id() -> Optional[str]:
    return _correlation_var.get()


def reset_correlation_id() -> None:
    _correlation_var.set(None)
