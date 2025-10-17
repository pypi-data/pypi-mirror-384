# Data Model: Basic Structured Logging

**Feature**: 007-basic-structured-logging  
**Date**: 2025-10-09  
**Phase**: 1 - Design & Contracts

## Overview

Este documento define as entidades principais, seus atributos, relacionamentos e regras de validação para o sistema de logging estruturado. Todos os modelos são implementados como Pydantic BaseModel para validação runtime.

---

## Entity: LogEntry

**Descrição**: Representa uma entrada única de log estruturado com todos os metadados necessários para rastreamento, auditoria e análise.

### Attributes

| Campo | Tipo | Obrigatório | Validação | Descrição |
|-------|------|-------------|-----------|-----------|
| `schema_version` | `str` | Sim | Semantic versioning: ^\\d+\\.\\d+\\.\\d+$ | Versão do schema de log para backward compatibility (inicia em "1.0.0") |
| `timestamp` | `str` | Sim | ISO 8601 UTC com Z | Momento exato da geração do log |
| `level` | `LogLevel` | Sim | Enum: ERROR, WARN, INFO, DEBUG | Nível de severidade |
| `category` | `LogCategory` | Sim | Enum: Connection, Operation, Error, Security, Performance | Categoria funcional |
| `correlation_id` | `str` | Sim | UUID v4 ou timestamp-based | ID único para rastrear operação completa |
| `message` | `str` | Sim | max_length=100000 (100KB após truncate) | Descrição legível do evento |
| `tool_name` | `str` | Não | pattern: ^[a-z\-]+$ | Nome da MCP tool (ex: "call-id") |
| `operation_id` | `str` | Não | - | ID interno da operação RabbitMQ |
| `duration_ms` | `float` | Não | >= 0 | Duração da operação em milissegundos |
| `operation_result` | `OperationResult` | Não | Enum: success, error, timeout | Resultado da operação |
| `error_type` | `str` | Não | - | Tipo de exceção Python (ex: "ConnectionError") |
| `stack_trace` | `str` | Não | - | Stack trace completo como string única com \n |
| `context` | `Dict[str, Any]` | Não | - | Dados contextuais adicionais específicos da operação |

### Enums

```python
from enum import Enum

class LogLevel(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"

class LogCategory(str, Enum):
    CONNECTION = "CONNECTION"
    OPERATION = "OPERATION"
    ERROR = "ERROR"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"

class OperationResult(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"
```

### Validation Rules

- `schema_version` DEVE seguir formato semântico "MAJOR.MINOR.PATCH" (ex: "1.0.0"); versão inicial é "1.0.0" (FR-027)
- `timestamp` DEVE estar sempre em UTC com sufixo "Z" (ex: "2025-10-09T14:32:15.123456Z")
- `message` DEVE ser truncado em 100KB com sufixo "...[truncated]" se exceder limite (FR-024)
- `stack_trace` DEVE armazenar quebras de linha como `\n` escaped em JSON (FR-022)
- `correlation_id` DEVE ser UUID v4 preferencial, fallback para timestamp+random (FR-023)
- Se `error_type` presente, `level` DEVE ser ERROR
- Se `duration_ms` presente, categoria DEVE ser Performance ou Operation

### State Transitions

Log entries são imutáveis após criação - não há estados ou transições.

### Example

```json
{
  "schema_version": "1.0.0",
  "timestamp": "2025-10-09T14:32:15.123456Z",
  "level": "INFO",
  "category": "Operation",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "MCP tool executed successfully",
  "tool_name": "call-id",
  "operation_id": "queues.list",
  "duration_ms": 42.5,
    "operation_result": "success",
  "context": {
    "vhost": "/",
    "queue_count": 15,
    "pagination": {"page": 1, "page_size": 50}
  }
}
```

---

## Entity: LogConfig

**Descrição**: Configuração do sistema de logging, define comportamentos de saída, rotação, níveis e políticas de retenção.

### Attributes

| Campo | Tipo | Obrigatório | Default | Validação | Descrição |
|-------|------|-------------|---------|-----------|-----------|
| `log_level` | `LogLevel` | Sim | INFO | Enum | Nível mínimo de log |
| `output_file` | `str` | Sim | ./logs/rabbitmq-mcp-{date}.log | - | Padrão de nome de arquivo |
| `rotation_when` | `str` | Sim | midnight | Valores: midnight, H, M | Quando rotar por tempo |
| `rotation_interval` | `int` | Sim | 1 | > 0 | Intervalo para rotação temporal |
| `rotation_max_bytes` | `int` | Sim | 104857600 (100MB) | > 0 | Tamanho máximo antes de rotação |
| `retention_days` | `int` | Sim | 30 | >= 1 | Dias para manter logs |
| `compression_enabled` | `bool` | Sim | True | - | Comprimir logs rotacionados com gzip |
| `async_queue_size` | `int` | Sim | 10000 | >= 100 | Tamanho do async buffer (fila interna) |
| `async_flush_interval` | `float` | Sim | 0.1 | >= 0.01 | Intervalo de flush em segundos |
| `batch_size` | `int` | Sim | 100 | >= 1 | Número de logs para batch write |
| `file_permissions` | `str` | Sim | 600 | Octal 3-dígitos | Permissões seguras para arquivos |
| `fallback_to_console` | `bool` | Sim | True | - | Usar stderr/console se arquivo falhar |

### Validation Rules

- `rotation_max_bytes` DEVE ser >= 1MB para evitar rotações excessivas
- `retention_days` DEVE ser >= 1 para garantir logs de pelo menos 1 dia
- `async_queue_size` DEVE ser suficiente para picos de throughput do async buffer (recomendado >= 10000)
- `file_permissions` DEVE ser modo octal válido Unix (ignorado no Windows)

### Example

```yaml
# config/logging_config.yaml
log_level: INFO
output_file: ./logs/rabbitmq-mcp-{date}.log
rotation_when: midnight
rotation_interval: 1
rotation_max_bytes: 104857600  # 100MB
retention_days: 30
compression_enabled: true
async_queue_size: 10000
async_flush_interval: 0.1
batch_size: 100
file_permissions: "600"
fallback_to_console: true
```

---

## Entity: SensitiveDataPattern

**Descrição**: Define padrões regex para identificar e redagir dados sensíveis automaticamente antes de escrever logs.

### Attributes

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `name` | `str` | Sim | Nome descritivo do padrão (ex: "password") |
| `pattern` | `str` | Sim | Regex pattern para detecção |
| `replacement` | `str` | Sim | Texto para substituir (ex: "[REDACTED]") |
| `flags` | `int` | Não | Flags regex (ex: re.IGNORECASE) |
| `enabled` | `bool` | Sim | Se padrão está ativo |

### Predefined Patterns

```python
BUILTIN_PATTERNS = [
    {
        "name": "password",
        "pattern": r'password\s*=\s*["\']?([^"\'\s]+)',
        "replacement": "password=[REDACTED]",
        "flags": re.IGNORECASE,
        "enabled": True
    },
    {
        "name": "api_key",
        "pattern": r'api[_-]?key\s*=\s*["\']?([^"\'\s]+)',
        "replacement": "api_key=[REDACTED]",
        "flags": re.IGNORECASE,
        "enabled": True
    },
    {
        "name": "token",
        "pattern": r'token\s*=\s*["\']?([^"\'\s]+)',
        "replacement": "token=[REDACTED]",
        "flags": re.IGNORECASE,
        "enabled": True
    },
    {
        "name": "amqp_password",
        "pattern": r'amqp://([^:]+):([^@]+)@',
        "replacement": r'amqp://\1:[REDACTED]@',
        "flags": 0,
        "enabled": True
    },
    {
        "name": "bearer_token",
        "pattern": r'Bearer\s+([A-Za-z0-9\-._~+/]+=*)',
        "replacement": "Bearer [REDACTED]",
        "flags": re.IGNORECASE,
        "enabled": True
    }
]
```

### Validation Rules

- `pattern` DEVE ser regex válido compilável
- `replacement` NÃO DEVE conter dados sensíveis
- Padrões DEVEM preservar contexto não-sensível para debugging (ex: username em connection string)

---

## Entity: CorrelationContext

**Descrição**: Contexto de execução que mantém correlation ID através de operações assíncronas usando contextvars.

### Attributes

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `correlation_id` | `str` | Sim | UUID v4 ou timestamp-based |
| `parent_id` | `str` | Não | ID da operação pai (para nested operations) |
| `root_id` | `str` | Não | ID da operação raiz (para traces distribuídos) |
| `operation_name` | `str` | Não | Nome da operação atual |
| `started_at` | `str` | Sim | Timestamp ISO 8601 UTC de início |

### Lifecycle

1. **Creation**: Gerado quando MCP tool é invocado (FR-005)
2. **Propagation**: Automática via contextvars através de await calls
3. **Inheritance**: Child tasks herdam correlation_id do parent context
4. **Cleanup**: Automaticamente limpo quando contexto async termina

### Example

```python
import contextvars

correlation_context = contextvars.ContextVar('correlation_context', default=None)

async def handle_mcp_tool_invocation(tool_name: str, params: dict):
    # Generate new correlation context for this operation
    ctx = CorrelationContext(
        correlation_id=str(uuid.uuid4()),
        operation_name=tool_name,
        started_at=datetime.utcnow().isoformat() + "Z"
    )
    
    correlation_context.set(ctx)
    
    try:
        # All logs within this context will include this correlation_id
        logger.info(f"Tool {tool_name} started", extra={"params": params})
        result = await execute_tool(tool_name, params)
    logger.info(f"Tool {tool_name} completed", extra={"operation_result": result})
        return result
    finally:
        # Context cleanup is automatic, but explicit reset is safe
        correlation_context.set(None)
```

---

## Entity: LogFile

**Descrição**: Representa arquivo físico de log no file system com metadados de rotação e retenção.

### Attributes

| Campo | Tipo | Obrigatório | Descrição |
|-------|------|-------------|-----------|
| `filepath` | `Path` | Sim | Caminho completo do arquivo |
| `created_at` | `datetime` | Sim | Timestamp de criação |
| `size_bytes` | `int` | Sim | Tamanho atual em bytes |
| `is_active` | `bool` | Sim | Se é o arquivo ativo (escrita atual) |
| `is_compressed` | `bool` | Sim | Se está comprimido (.gz) |
| `rotation_reason` | `str` | Não | "size" ou "time" |
| `rotated_at` | `datetime` | Não | Quando foi rotacionado |

### State Transitions

```
[Created] -> active=True, compressed=False
    |
    v
[Writing] -> active=True, size increasing
    |
    v (rotation trigger: size >= max OR time >= interval)
[Rotating] -> active=False, being renamed/compressed
    |
    v
[Archived] -> active=False, compressed=True
    |
    v (age > retention_days)
[Deleted] -> removed from filesystem
```

### Validation Rules

- Arquivo ativo DEVE ter `is_active=True` e `is_compressed=False`
- Apenas UM arquivo pode ser `is_active=True` por processo
- Arquivos comprimidos DEVEM ter extensão `.gz`
- Arquivos mais antigos que `retention_days` DEVEM ser deletados automaticamente

---

## Entity Relationships

```
LogConfig (1) ----configures----> LogWriter (1)
    |
    +--> SensitiveDataPattern (0..*)
    |
    +--> LogFile (1..*)

CorrelationContext (1) ----enriches----> LogEntry (0..*)

LogWriter (1) ----produces----> LogEntry (0..*)
    |
    +--> LogFile (1..*)
```

### Relationship Descriptions

- **LogConfig → LogWriter**: Configuração define comportamento do writer (1:1)
- **LogConfig → SensitiveDataPattern**: Config contém padrões de redação ativos (1:N)
- **LogConfig → LogFile**: Config determina política de rotação e retenção de arquivos (1:N)
- **CorrelationContext → LogEntry**: Context enriquece entries com correlation ID (1:N)
- **LogWriter → LogEntry**: Writer cria e persiste log entries (1:N)
- **LogWriter → LogFile**: Writer gerencia arquivos de log (1:N)

---

## Invariants & Business Rules

### BR-001: Immutable Log Entries
Log entries DEVEM ser imutáveis após criação. Modificações violam auditoria e compliance.

### BR-002: Zero Log Loss
Sistema DEVE bloquear operações quando buffer assíncrono está cheio para garantir zero perda de logs (FR-017).

### BR-003: Automatic Redaction
Dados sensíveis DEVEM ser automaticamente redagidos antes de qualquer serialização ou persistência (FR-004).

### BR-004: UTC Timestamps Always
Todos timestamps DEVEM ser UTC com sufixo "Z" para evitar ambiguidades DST/timezone (FR-011).

### BR-005: Correlation ID per MCP Invocation
Novo correlation ID DEVE ser gerado exatamente quando MCP tool é invocado, não antes nem depois (FR-005).

### BR-006: Performance Budget
Overhead de logging DEVE ser <5ms por operação. Operações que excedem DEVEM ser otimizadas ou removidas (FR-016).

### BR-007: Single Active Log File
Apenas UM arquivo de log pode estar ativo (aberto para escrita) por processo a qualquer momento.

### BR-008: Retention Policy Enforcement
Arquivos mais antigos que `retention_days` DEVEM ser automaticamente deletados durante processo de rotação (FR-014).

### BR-009: Graceful Degradation
Se escrita em arquivo falhar, sistema DEVE tentar fallback para stderr/console E continuar operações normais (FR-021).

### BR-010: Message Truncation
Mensagens >100KB DEVEM ser truncadas com sufixo "...[truncated]" para prevenir problemas de memória (FR-024).

---

## Data Flow

```
[MCP Tool Invocation]
    ↓
[Generate Correlation ID] (CorrelationContext)
    ↓
[Create Log Entry] (LogEntry)
    ↓
[Apply Processors]
    ├─→ [Add Correlation ID]
    ├─→ [Add Timestamp (UTC)]
    ├─→ [Redact Sensitive Data] (SensitiveDataPattern)
    ├─→ [Truncate if >100KB]
    └─→ [Format as JSON]
    ↓
[Write to Async Buffer]
    ↓
[Batch & Flush] (async)
    ↓
[Write to LogFile]
    ↓
[Check Rotation Triggers]
    ├─→ Size >= 100MB → Rotate
    └─→ Time >= midnight → Rotate
    ↓
[Optional Compression] (.gz)
    ↓
[Check Retention]
    └─→ Age > 30 days → Delete
```

---

## Schema Evolution Strategy

### Backward Compatibility

- Novos campos podem ser ADICIONADOS sem quebrar parsers existentes
- Campos existentes NÃO DEVEM mudar tipo ou semântica
- Campos deprecados DEVEM ser marcados mas mantidos por 1 versão major

### Version Indicator

Embora não incluído por padrão, schema pode incluir campo opcional `schema_version` para migração futura:

```json
{
  "schema_version": "1.0",
  "timestamp": "...",
  // ... resto dos campos
}
```

### Migration Path

Se mudanças breaking forem necessárias:
1. Adicionar `schema_version` field
2. Manter ambas versões durante período de transição
3. Documentar migração em CHANGELOG.md
4. Fornecer script de conversão se necessário

---

## Pydantic Models (Implementation Reference)

```python
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import re

class LogLevel(str, Enum):
    ERROR = "ERROR"
    WARN = "WARN"
    INFO = "INFO"
    DEBUG = "DEBUG"

class LogCategory(str, Enum):
    CONNECTION = "CONNECTION"
    OPERATION = "OPERATION"
    ERROR = "ERROR"
    SECURITY = "SECURITY"
    PERFORMANCE = "PERFORMANCE"

class OperationResult(str, Enum):
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"

class LogEntry(BaseModel):
    timestamp: str = Field(..., description="ISO 8601 UTC timestamp with Z suffix")
    level: LogLevel
    category: LogCategory
    correlation_id: Optional[str] = Field(None, min_length=1)
    message: str = Field(..., max_length=100000)
    tool_name: Optional[str] = Field(None, pattern=r'^[a-z0-9_\-]+$')
    operation_id: Optional[str] = None
    duration_ms: Optional[float] = Field(None, ge=0)
    operation_result: Optional[OperationResult] = None
    error_type: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    
    @validator('timestamp')
    def validate_utc_timestamp(cls, v):
        if not v.endswith('Z'):
            raise ValueError('Timestamp must be UTC with Z suffix')
        # Validate ISO 8601 format
        datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v
    
    @validator('message')
    def truncate_large_messages(cls, v):
        max_length = 100000  # 100KB
        if len(v) > max_length:
            return v[:max_length] + "...[truncated]"
        return v

class LogConfig(BaseModel):
    log_level: LogLevel = LogLevel.INFO
    output_file: str = "./logs/rabbitmq-mcp-{date}.log"
    rotation_when: str = "midnight"
    rotation_interval: int = Field(1, gt=0)
    rotation_max_bytes: int = Field(104857600, gt=0)  # 100MB
    retention_days: int = Field(30, ge=1)
    compression_enabled: bool = True
    async_queue_size: int = Field(10000, ge=100)
    async_flush_interval: float = Field(0.1, ge=0.01)
    batch_size: int = Field(100, ge=1)
    file_permissions: str = "600"
    fallback_to_console: bool = True

class SensitiveDataPattern(BaseModel):
    name: str
    pattern: str
    replacement: str
    flags: int = 0
    enabled: bool = True
    
    @validator('pattern')
    def validate_regex(cls, v):
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f'Invalid regex pattern: {e}')
        return v

class CorrelationContext(BaseModel):
    correlation_id: str
    parent_id: Optional[str] = None
    root_id: Optional[str] = None
    operation_name: Optional[str] = None
    started_at: str
```

---

## Next Steps

- ✅ Data model complete
- 🔄 Criar JSON schemas em contracts/
- 🔄 Criar quickstart.md
- 🔄 Atualizar agent context
