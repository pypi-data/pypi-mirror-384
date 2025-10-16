"""Configuração centralizada de logging estruturado com structlog."""

from __future__ import annotations

import logging
import sys
from typing import Any, Iterable

import structlog

from .sanitizer import sanitize_value

DEFAULT_LOG_LEVEL = logging.INFO
SENSITIVE_KEYS = {"password", "credentials", "secret", "token"}


def _sanitize_processor(_: logging.Logger, __: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Sanitiza campos sensíveis e URLs AMQP em qualquer payload."""

    for key in list(event_dict.keys()):
        value = event_dict[key]
        if key in SENSITIVE_KEYS:
            event_dict[key] = "***"
            continue
        event_dict[key] = sanitize_value(value)

    message = event_dict.get("event")
    if isinstance(message, str):
        event_dict["event"] = sanitize_value(message)

    if "exception" in event_dict and isinstance(event_dict["exception"], str):
        event_dict["exception"] = sanitize_value(event_dict["exception"])

    if "traceback" in event_dict and isinstance(event_dict["traceback"], str):
        event_dict["traceback"] = sanitize_value(event_dict["traceback"])

    return event_dict


def configure_logging(
    level: int = DEFAULT_LOG_LEVEL,
    processors: Iterable[structlog.types.Processor] | None = None,
) -> None:
    """Inicializa logging estruturado com sanitização e saída JSON."""

    logging.basicConfig(
        level=level,
        stream=sys.stdout,
        format="%(message)s",
    )

    structlog.configure(
        processors=list(
            processors
            or (
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_log_level,
                structlog.stdlib.add_logger_name,
                _sanitize_processor,
                structlog.processors.dict_tracebacks,
                structlog.processors.JSONRenderer(),
            )
        ),
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Retorna um logger estruturado pronto para uso."""

    return structlog.get_logger(name)
