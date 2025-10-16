"""Schemas Pydantic para validação de dados.

Este pacote agrega todos os schemas utilizados na feature de conexão RabbitMQ.
Os módulos exportados aqui são referenciados nos tasks T005-T023 da feature
`002-basic-rabbitmq-connection`.
"""

from .connection import ConnectionConfig, ConnectionState  # noqa: F401
from .retry import RetryPolicy, RetryStats  # noqa: F401

__all__ = [
    "ConnectionConfig",
    "ConnectionState",
    "RetryPolicy",
    "RetryStats",
]
