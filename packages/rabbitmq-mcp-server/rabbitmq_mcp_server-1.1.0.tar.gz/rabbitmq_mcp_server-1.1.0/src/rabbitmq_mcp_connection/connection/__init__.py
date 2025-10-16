"""Componentes núcleo de conexão AMQP.

Este pacote fornece classes de alto nível para gerenciamento de conexões com
RabbitMQ incluindo monitoramento, política de retry, pool de conexões e
integração com ferramentas MCP. Os módulos expostos aqui formam a base das
User Stories definidas na feature *002-basic-rabbitmq-connection*.
"""

from .exceptions import (  # noqa: F401
    AuthenticationError,
    ConnectionError,
    ConnectionTimeoutError,
    PoolError,
    PoolTimeoutError,
    VHostNotFoundError,
)
from .manager import ConnectionManager  # noqa: F401
from .health import HealthChecker  # noqa: F401
from .monitor import ConnectionMonitor  # noqa: F401
from .pool import ConnectionPool, PooledConnection  # noqa: F401

__all__ = [
    "AuthenticationError",
    "ConnectionError",
    "ConnectionTimeoutError",
    "ConnectionManager",
    "ConnectionMonitor",
    "ConnectionPool",
    "HealthChecker",
    "PoolError",
    "PoolTimeoutError",
    "PooledConnection",
    "VHostNotFoundError",
]
