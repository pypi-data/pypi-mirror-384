"""Carregamento multi-fonte de configurações de conexão AMQP.

Este módulo implementa a lógica descrita na tasks T008/T011-T017 para
obter uma instância validada de ``ConnectionConfig`` respeitando a
precedência: argumentos explícitos > variáveis de ambiente > arquivo TOML
> valores padrão do schema.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

from pydantic import ValidationError

from rabbitmq_mcp_connection.logging.config import get_logger
from rabbitmq_mcp_connection.schemas.connection import ConnectionConfig

try:  # pragma: no cover - disponibilidade depende da versão do Python
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:  # pragma: no cover - Python <3.11
    import tomli as tomllib  # type: ignore[no-redef]

LOGGER = get_logger(__name__)

ENV_PREFIX = "AMQP_"
ENV_MAPPING: Mapping[str, str] = {
    "AMQP_HOST": "host",
    "AMQP_PORT": "port",
    "AMQP_USER": "user",
    "AMQP_PASSWORD": "password",
    "AMQP_VHOST": "vhost",
    "AMQP_TIMEOUT": "timeout",
    "AMQP_HEARTBEAT": "heartbeat",
}

DEFAULT_CONFIG_PATHS: tuple[Path, ...] = (
    Path("config/config.toml"),
    Path("config.toml"),
)


def _load_toml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}

    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - erro raro
        LOGGER.error("config.toml_invalid", path=str(path), exception=str(exc))
        raise

    # Suportar estruturas simples ou aninhadas (e.g. [amqp])
    if "amqp" in data and isinstance(data["amqp"], Mapping):
        amqp_section = data["amqp"]
    else:
        amqp_section = data

    return {
        key: amqp_section.get(key)
        for key in ConnectionConfig.model_fields.keys()
        if isinstance(amqp_section, Mapping)
    }


def _load_env_values() -> Dict[str, Any]:
    values: Dict[str, Any] = {}
    for env_key, field_name in ENV_MAPPING.items():
        raw_value = os.getenv(env_key)
        if raw_value is None:
            continue
        values[field_name] = raw_value
    return values


def _apply_overrides(base: Dict[str, Any], overrides: Mapping[str, Any]) -> Dict[str, Any]:
    result = base.copy()
    for key, value in overrides.items():
        if key in ConnectionConfig.model_fields:
            result[key] = value
    return result


def _iter_existing_paths(custom_path: Path | None) -> Iterable[Path]:
    if custom_path:
        yield custom_path
    for candidate in DEFAULT_CONFIG_PATHS:
        if candidate.exists():
            yield candidate


def load_config(config_file: str | Path | None = None, **overrides: Any) -> ConnectionConfig:
    """Carrega configuração de conexão com precedência definida.

    Parameters
    ----------
    config_file:
        Caminho explícito para arquivo TOML. Quando ``None`` serão
        utilizados valores padrão conhecidos.
    overrides:
        Argumentos com maior precedência. Apenas campos válidos do
        ``ConnectionConfig`` são considerados.

    Returns
    -------
    ConnectionConfig
        Instância validada pronta para uso com ``ConnectionManager``.
    """

    base: Dict[str, Any] = {}

    path_obj: Path | None = Path(config_file) if config_file else None
    for path in _iter_existing_paths(path_obj):
        base.update({k: v for k, v in _load_toml(path).items() if v is not None})

    import os

    env_values = _load_env_values()
    base.update(env_values)

    base = _apply_overrides(base, overrides)
    try:
        return ConnectionConfig(**base)
    except ValidationError as exc:
        LOGGER.error("config.validation_failed", errors=exc.errors())
        raise


__all__ = ["load_config"]
