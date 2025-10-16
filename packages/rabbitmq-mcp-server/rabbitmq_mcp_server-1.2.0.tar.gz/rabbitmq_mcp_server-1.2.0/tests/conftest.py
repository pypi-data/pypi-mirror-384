import os
from pathlib import Path
from typing import Iterator

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _set_env_defaults(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """Garante valores padrão de conexão para os testes."""
    env_defaults = {
        "AMQP_HOST": "localhost",
        "AMQP_PORT": "5672",
        "AMQP_USER": "guest",
        "AMQP_PASSWORD": "guest",
        "AMQP_VHOST": "/",
    }
    for key, value in env_defaults.items():
        monkeypatch.setenv(key, value)
    yield


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT
