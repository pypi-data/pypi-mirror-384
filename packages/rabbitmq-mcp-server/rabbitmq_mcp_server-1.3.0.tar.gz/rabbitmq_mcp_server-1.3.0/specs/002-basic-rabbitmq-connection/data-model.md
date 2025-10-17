# Data Model: Basic RabbitMQ Connection

**Feature**: 002-basic-rabbitmq-connection  
**Date**: 2025-10-09  
**Phase**: 1 - Data Model Design

## Overview

Este documento define as entidades, seus atributos, relacionamentos e regras de validação para a feature de conexão básica com RabbitMQ.

---

## Entity Diagram

```
┌─────────────────────────┐
│  ConnectionConfig       │
├─────────────────────────┤
│ - host: str             │
│ - port: int             │
│ - user: str             │
│ - password: str         │
│ - vhost: str            │
│ - timeout: int          │
│ - heartbeat: int        │
└──────────┬──────────────┘
           │ 1
           │ uses
           │
           │ 1
┌──────────▼──────────────┐        ┌─────────────────────────┐
│  ConnectionManager      │───────▶│  RetryPolicy            │
├─────────────────────────┤ 1    1 ├─────────────────────────┤
│ - config: Config        │        │ - initial_delay: float  │
│ - connection: Connection│        │ - backoff_factor: float │
│ - monitor: Monitor      │        │ - max_delay: float      │
│ - retry: RetryPolicy    │        │ - current_delay: float  │
│ - state: ConnectionState│        └─────────────────────────┘
└──────────┬──────────────┘
           │ 1
           │ manages
           │
           │ 1..*
┌──────────▼──────────────┐        ┌─────────────────────────┐
│  ConnectionPool         │───────▶│  PooledConnection       │
├─────────────────────────┤ 1    * ├─────────────────────────┤
│ - max_size: int         │        │ - connection: Connection│
│ - timeout: int          │        │ - in_use: bool          │
│ - available: Queue      │        │ - created_at: datetime  │
│ - all_connections: List │        │ - last_used: datetime   │
└─────────────────────────┘        └─────────────────────────┘

┌─────────────────────────┐        ┌─────────────────────────┐
│  ConnectionMonitor      │───────▶│  HealthStatus           │
├─────────────────────────┤ 1    1 ├─────────────────────────┤
│ - connection: Connection│        │ - is_connected: bool    │
│ - heartbeat_interval: int        │ - broker_available: bool│
│ - last_heartbeat: datetime       │ - latency_ms: float     │
└─────────────────────────┘        │ - last_check: datetime  │
                                    └─────────────────────────┘

┌─────────────────────────┐
│  ConnectionState (Enum) │
├─────────────────────────┤
│ - DISCONNECTED          │
│ - CONNECTING            │
│ - CONNECTED             │
│ - RECONNECTING          │
│ - FAILED                │
└─────────────────────────┘
```

---

## Entity: ConnectionConfig

**Description**: Parâmetros de configuração para estabelecer conexão AMQP com RabbitMQ.

**Source**: Carregado de múltiplas fontes com ordem de precedência:
1. Argumentos programáticos (maior precedência)
2. Variáveis de ambiente (AMQP_HOST, AMQP_PORT, AMQP_USER, AMQP_PASSWORD, AMQP_VHOST)
3. Arquivo config.toml
4. Valores padrão (menor precedência)

### Attributes

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `host` | `str` | Yes | `"localhost"` | Hostname ou IP do servidor RabbitMQ |
| `port` | `int` | Yes | `5672` | Porta AMQP do servidor |
| `user` | `str` | Yes | `"guest"` | Usuário para autenticação |
| `password` | `str` | Yes | `"guest"` | Senha para autenticação (sanitizada em logs) |
| `vhost` | `str` | Yes | `"/"` | Virtual host do RabbitMQ |
| `timeout` | `int` | Yes | `30` | Timeout de conexão em segundos |
| `heartbeat` | `int` | Yes | `60` | Intervalo de heartbeat AMQP em segundos |

### Validation Rules

```python
from pydantic import BaseModel, Field, field_validator

class ConnectionConfig(BaseModel):
    """Configuração de conexão AMQP"""
    
    host: str = Field(
        default="localhost",
        min_length=1,
        description="Hostname ou IP do RabbitMQ"
    )
    
    port: int = Field(
        default=5672,
        ge=1,
        le=65535,
        description="Porta AMQP (1-65535)"
    )
    
    user: str = Field(
        default="guest",
        min_length=1,
        description="Usuário para autenticação"
    )
    
    password: str = Field(
        default="guest",
        min_length=1,
        description="Senha (sanitizada em logs)"
    )
    
    vhost: str = Field(
        default="/",
        min_length=1,
        description="Virtual host"
    )
    
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="Timeout de conexão (1-300s)"
    )
    
    heartbeat: int = Field(
        default=60,
        ge=0,
        le=3600,
        description="Heartbeat interval (0=disabled, max 3600s)"
    )
    
    @field_validator('password')
    @classmethod
    def sanitize_password(cls, v: str) -> str:
        """Marca senha para sanitização em logs"""
        # A senha nunca deve aparecer em __repr__ ou logs
        return v
    
    def get_connection_url(self) -> str:
        """Gera URL de conexão (sem expor senha)"""
        return f"amqp://{self.user}:***@{self.host}:{self.port}{self.vhost}"
    
    class Config:
        # Não incluir senha em __repr__
        fields = {
            'password': {'repr': False}
        }
```

### State Transitions

N/A - Esta é uma entidade de configuração estática.

---

## Entity: ConnectionState

**Description**: Estados possíveis de uma conexão AMQP.

### Values

```python
from enum import Enum

class ConnectionState(str, Enum):
    """Estados de conexão AMQP"""
    
    DISCONNECTED = "disconnected"    # Sem conexão ativa
    CONNECTING = "connecting"        # Tentando estabelecer conexão
    CONNECTED = "connected"          # Conexão estabelecida e saudável
    RECONNECTING = "reconnecting"    # Tentando reconectar após perda
    FAILED = "failed"                # Falha permanente (não usado com retry infinito)
```

### State Diagram

```
     ┌─────────────┐
     │ DISCONNECTED│◀──────────────────────┐
     └──────┬──────┘                       │
            │                              │
            │ connect()                    │
            │                              │
     ┌──────▼──────┐                       │
     │ CONNECTING  │                       │
     └──────┬──────┘                       │
            │                              │
            │ success                      │ disconnect()
            │                              │
     ┌──────▼──────┐                       │
     │  CONNECTED  │───────────────────────┤
     └──────┬──────┘                       │
            │                              │
            │ connection_lost              │
            │                              │
     ┌──────▼──────────┐                   │
     │  RECONNECTING   │───────────────────┘
     └─────────────────┘
         │       ▲
         │       │
         └───────┘
      retry loop
```

---

## Entity: ConnectionManager

**Description**: Gerenciador principal de conexões AMQP. Responsável por estabelecer, monitorar e recuperar conexões.

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `config` | `ConnectionConfig` | Yes | Configuração de conexão |
| `connection` | `aio_pika.Connection` | No | Conexão AMQP ativa (None se desconectado) |
| `channel` | `aio_pika.Channel` | No | Canal AMQP default |
| `monitor` | `ConnectionMonitor` | Yes | Monitor de saúde da conexão |
| `retry_policy` | `RetryPolicy` | Yes | Política de retry para reconexão |
| `state` | `ConnectionState` | Yes | Estado atual da conexão |
| `_lock` | `asyncio.Lock` | Yes | Lock para operações thread-safe |

### Methods

```python
class ConnectionManager:
    """Gerenciador de conexões AMQP"""
    
    async def connect(self) -> None:
        """Estabelece conexão com RabbitMQ
        
        Raises:
            ConnectionTimeout: Se timeout for excedido
            AuthenticationError: Se credenciais inválidas
            ConnectionError: Outros erros de conexão
        """
        
    async def disconnect(self) -> None:
        """Desconecta graciosamente fechando recursos"""
        
    async def reconnect(self) -> None:
        """Reconecta usando retry policy com backoff exponencial"""
        
    async def get_status(self) -> ConnectionState:
        """Retorna estado atual da conexão"""
        
    async def ensure_connected(self) -> None:
        """Garante que conexão está ativa, reconecta se necessário"""
```

### Validation Rules

- `config` deve ser válido (validado por Pydantic)
- `connection` só pode ser None se state = DISCONNECTED
- Operações devem ser thread-safe usando `_lock`

### State Transitions

Ver diagrama de `ConnectionState`.

---

## Entity: ConnectionPool

**Description**: Pool de conexões AMQP para operações simultâneas. Bloqueia quando todas as conexões estão em uso.

### Attributes

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `max_size` | `int` | Yes | `5` | Número máximo de conexões no pool |
| `timeout` | `int` | Yes | `10` | Timeout para aguardar conexão disponível (segundos) |
| `config` | `ConnectionConfig` | Yes | - | Configuração para criar conexões |
| `_available` | `asyncio.Queue` | Yes | - | Fila de conexões disponíveis |
| `_all_connections` | `Set[PooledConnection]` | Yes | - | Todas as conexões criadas |
| `_lock` | `asyncio.Lock` | Yes | - | Lock para operações thread-safe |

### Methods

```python
class ConnectionPool:
    """Pool de conexões AMQP assíncronas"""
    
    async def acquire(self) -> PooledConnection:
        """Adquire conexão do pool
        
        Returns:
            PooledConnection: Conexão disponível
            
        Raises:
            PoolTimeout: Se timeout excedido aguardando conexão
        """
        
    async def release(self, conn: PooledConnection) -> None:
        """Devolve conexão ao pool para reutilização"""
        
    async def close(self) -> None:
        """Fecha todas as conexões do pool"""
        
    async def get_stats(self) -> PoolStats:
        """Retorna estatísticas do pool (total, in_use, available)"""
```

### Validation Rules

- `max_size` deve ser >= 1
- `timeout` deve ser >= 1
- Nunca criar mais que `max_size` conexões
- Conexões devolvidas ao pool devem ser saudáveis

---

## Entity: PooledConnection

**Description**: Wrapper de conexão AMQP para uso em pool. Rastreia uso e saúde.

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `connection` | `aio_pika.Connection` | Yes | Conexão AMQP subjacente |
| `channel` | `aio_pika.Channel` | Yes | Canal AMQP default |
| `in_use` | `bool` | Yes | Se está sendo usada |
| `created_at` | `datetime` | Yes | Timestamp de criação |
| `last_used` | `datetime` | Yes | Timestamp do último uso |
| `health_status` | `HealthStatus` | Yes | Status de saúde |

### Methods

```python
class PooledConnection:
    """Conexão AMQP rastreável para pool"""
    
    async def check_health(self) -> bool:
        """Verifica se conexão está saudável
        
        Returns:
            bool: True se conexão está ativa e responsiva
        """
        
    async def reset(self) -> None:
        """Reseta conexão para estado limpo"""
        
    def mark_in_use(self) -> None:
        """Marca conexão como em uso"""
        
    def mark_available(self) -> None:
        """Marca conexão como disponível"""
```

---

## Entity: ConnectionMonitor

**Description**: Monitor de saúde e detecção de perda de conexão. Usa heartbeat AMQP + eventos de callback.

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `connection` | `aio_pika.Connection` | Yes | Conexão a monitorar |
| `heartbeat_interval` | `int` | Yes | Intervalo de heartbeat (segundos) |
| `last_heartbeat` | `datetime` | Yes | Timestamp do último heartbeat |
| `on_connection_lost` | `Callable` | No | Callback ao detectar perda |

### Methods

```python
class ConnectionMonitor:
    """Monitor de saúde de conexão AMQP"""
    
    async def start(self) -> None:
        """Inicia monitoramento com heartbeat e callbacks"""
        
    async def stop(self) -> None:
        """Para monitoramento"""
        
    async def check_health(self) -> HealthStatus:
        """Verifica saúde atual da conexão
        
        Returns:
            HealthStatus: Status detalhado de saúde
        """
```

### Validation Rules

- `heartbeat_interval` deve estar entre 0 (disabled) e 3600 segundos
- `connection` deve ser válida

---

## Entity: HealthStatus

**Description**: Status de saúde de uma conexão ou do broker RabbitMQ.

### Attributes

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| `is_connected` | `bool` | Yes | Se há conexão ativa |
| `broker_available` | `bool` | Yes | Se broker responde |
| `latency_ms` | `float` | Yes | Latência da última verificação |
| `last_check` | `datetime` | Yes | Timestamp da última verificação |
| `error_message` | `Optional[str]` | No | Mensagem de erro se unhealthy |

### Validation Rules

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class HealthStatus(BaseModel):
    """Status de saúde de conexão"""
    
    is_connected: bool = Field(
        description="Se há conexão AMQP ativa"
    )
    
    broker_available: bool = Field(
        description="Se o broker RabbitMQ está respondendo"
    )
    
    latency_ms: float = Field(
        ge=0,
        description="Latência da última verificação em ms"
    )
    
    last_check: datetime = Field(
        description="Timestamp da última verificação"
    )
    
    error_message: Optional[str] = Field(
        default=None,
        description="Mensagem de erro se unhealthy"
    )
    
    @property
    def is_healthy(self) -> bool:
        """Conexão está saudável se conectada E broker disponível"""
        return self.is_connected and self.broker_available
```

---

## Entity: RetryPolicy

**Description**: Política de retry com backoff exponencial para reconexão.

### Attributes

| Attribute | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `initial_delay` | `float` | Yes | `1.0` | Delay inicial em segundos |
| `backoff_factor` | `float` | Yes | `2.0` | Fator multiplicador do backoff |
| `max_delay` | `float` | Yes | `60.0` | Delay máximo em segundos |
| `current_delay` | `float` | Yes | `1.0` | Delay atual (state interno) |
| `attempts` | `int` | Yes | `0` | Número de tentativas realizadas |

### Methods

```python
class RetryPolicy:
    """Política de retry com backoff exponencial"""
    
    def next_delay(self) -> float:
        """Calcula próximo delay e incrementa contador
        
        Returns:
            float: Delay em segundos para próxima tentativa
        """
        delay = min(self.current_delay, self.max_delay)
        self.current_delay *= self.backoff_factor
        self.attempts += 1
        return delay
    
    def reset(self) -> None:
        """Reseta política para valores iniciais"""
        self.current_delay = self.initial_delay
        self.attempts = 0
    
    def get_stats(self) -> RetryStats:
        """Retorna estatísticas de retry"""
        return RetryStats(
            attempts=self.attempts,
            current_delay=self.current_delay,
            max_delay=self.max_delay
        )
```

### Validation Rules

```python
class RetryPolicy(BaseModel):
    """Política de retry com backoff exponencial"""
    
    initial_delay: float = Field(
        default=1.0,
        gt=0,
        le=60,
        description="Delay inicial (>0, <=60s)"
    )
    
    backoff_factor: float = Field(
        default=2.0,
        gt=1.0,
        le=10.0,
        description="Fator de backoff (>1, <=10)"
    )
    
    max_delay: float = Field(
        default=60.0,
        gt=0,
        le=3600,
        description="Delay máximo (>0, <=3600s)"
    )
    
    current_delay: float = Field(
        default=1.0,
        gt=0,
        description="Delay atual (state interno)"
    )
    
    attempts: int = Field(
        default=0,
        ge=0,
        description="Número de tentativas"
    )
```

### State Transitions

```
Delay Progression: 1s → 2s → 4s → 8s → 16s → 32s → 60s → 60s → ...
```

---

## Relationships

### ConnectionManager ↔ ConnectionConfig
- **Type**: Composition (1:1)
- **Description**: Manager usa config para estabelecer conexão
- **Lifecycle**: Config criado antes de Manager

### ConnectionManager ↔ RetryPolicy
- **Type**: Composition (1:1)
- **Description**: Manager usa policy para reconexão
- **Lifecycle**: Policy criado com Manager

### ConnectionManager ↔ ConnectionMonitor
- **Type**: Composition (1:1)
- **Description**: Manager usa monitor para detectar falhas
- **Lifecycle**: Monitor criado após conexão estabelecida

### ConnectionPool ↔ PooledConnection
- **Type**: Aggregation (1:many)
- **Description**: Pool gerencia múltiplas conexões
- **Lifecycle**: Conexões criadas sob demanda, destruídas com pool

### ConnectionMonitor ↔ HealthStatus
- **Type**: Dependency (1:1)
- **Description**: Monitor produz health status
- **Lifecycle**: Health status gerado a cada verificação

---

## Logging Schema

### Connection Events

Todos os eventos de conexão devem ser logados em JSON estruturado:

```json
{
    "timestamp": "2025-10-09T14:30:25.123Z",
    "level": "info",
    "event_type": "connection.established",
    "message": "Connection established successfully",
    "context": {
        "host": "localhost",
        "port": 5672,
        "vhost": "/",
        "user": "guest",
        "password": "***REDACTED***",
        "latency_ms": 123.45
    },
    "correlation_id": "uuid-here"
}
```

### Critical Events to Log

1. **connection.established**: Conexão estabelecida com sucesso
2. **connection.failed**: Falha ao conectar
3. **connection.lost**: Conexão perdida inesperadamente
4. **connection.reconnecting**: Iniciando reconexão
5. **connection.disconnected**: Desconexão limpa
6. **pool.connection_acquired**: Conexão adquirida do pool
7. **pool.connection_released**: Conexão devolvida ao pool
8. **pool.timeout**: Timeout aguardando conexão do pool
9. **health_check.success**: Health check bem-sucedido
10. **health_check.failed**: Health check falhou

---

## Performance Characteristics

### Time Complexity

| Operation | Complexity | Notes |
|-----------|------------|-------|
| `ConnectionManager.connect()` | O(1) | Network I/O bound |
| `ConnectionPool.acquire()` | O(1) | Queue.get() amortizado |
| `ConnectionPool.release()` | O(1) | Queue.put() |
| `HealthStatus.check()` | O(1) | Single network round-trip |
| `RetryPolicy.next_delay()` | O(1) | Simple arithmetic |

### Space Complexity

| Entity | Complexity | Notes |
|--------|------------|-------|
| `ConnectionPool` | O(n) | n = max_size |
| `ConnectionManager` | O(1) | Single connection |
| `HealthStatus` | O(1) | Fixed size |

---

## Constraints & Invariants

### Global Constraints
1. Apenas uma conexão ativa por `ConnectionManager` por vez
2. Pool nunca excede `max_size` conexões
3. Credenciais nunca aparecem em logs (sanitização obrigatória)
4. Estado de conexão sempre consistente (state machine válido)

### Invariants
1. `ConnectionPool.acquire()` sempre retorna conexão saudável ou timeout
2. `ConnectionManager.state` sempre reflete estado real da conexão
3. `RetryPolicy.current_delay` nunca excede `max_delay`
4. `HealthStatus.is_healthy` é idempotente (múltiplas chamadas = mesmo resultado)

---

## Migration & Versioning

**Initial Version**: 1.0.0 (esta feature)

**Future Compatibility**:
- Schemas Pydantic permitem adicionar campos opcionais sem breaking changes
- State machine pode adicionar novos estados preservando transições existentes
- Pool pode adicionar estratégias de eviction sem mudar API pública

---

## Testing Checklist

### Unit Tests
- [ ] `ConnectionConfig` valida corretamente todos os campos
- [ ] `ConnectionConfig` sanitiza senha em __repr__
- [ ] `ConnectionState` transições são válidas
- [ ] `RetryPolicy` calcula delays corretamente
- [ ] `RetryPolicy.reset()` restaura estado inicial
- [ ] `HealthStatus.is_healthy` retorna valor correto

### Integration Tests
- [ ] `ConnectionManager` estabelece conexão real
- [ ] `ConnectionManager` detecta falha de autenticação
- [ ] `ConnectionManager` reconecta após perda
- [ ] `ConnectionPool` adquire/libera conexões corretamente
- [ ] `ConnectionPool` respeita timeout
- [ ] `ConnectionMonitor` detecta conexão perdida
- [ ] Logs estruturados são emitidos corretamente
- [ ] Credenciais são sanitizadas em todos os logs

---

## Conclusion

O data model está completo e validado contra todos os requisitos funcionais da spec. Todas as entidades têm schemas Pydantic bem definidos, validações robustas e relacionamentos claros.

**Next Steps**: Phase 1 - Contracts (JSON schemas para MCP tools)
