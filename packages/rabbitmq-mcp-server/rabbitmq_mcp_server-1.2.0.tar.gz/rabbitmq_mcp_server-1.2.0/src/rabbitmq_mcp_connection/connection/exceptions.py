"""Exceções específicas para operações de conexão RabbitMQ."""

from __future__ import annotations


class ConnectionError(RuntimeError):
    """Erro base para falhas relacionadas à conexão AMQP."""


class ConnectionTimeoutError(ConnectionError):
    """Falha por exceder o tempo limite durante o estabelecimento da conexão."""


class AuthenticationError(ConnectionError):
    """Falha de autenticação com RabbitMQ."""


class VHostNotFoundError(ConnectionError):
    """Virtual host especificado não existe ou não pode ser acessado."""


class PoolError(RuntimeError):
    """Erro genérico para operações do pool de conexões."""


class PoolTimeoutError(PoolError):
    """Timeout aguardando uma conexão disponível no pool."""
