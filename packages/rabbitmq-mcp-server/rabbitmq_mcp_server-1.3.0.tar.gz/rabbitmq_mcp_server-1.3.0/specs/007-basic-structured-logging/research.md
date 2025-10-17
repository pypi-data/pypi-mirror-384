# Research: Basic Structured Logging

**Feature**: 007-basic-structured-logging  
**Date**: 2025-10-09  
**Status**: Phase 0 Complete

## Overview

Este documento consolida as decisões de pesquisa técnica para implementação do sistema de logging estruturado. Cada seção documenta uma decisão tecnológica, sua justificativa e alternativas consideradas.

---

## R1: Biblioteca de Logging Estruturado

### Decision
**structlog** será utilizado como biblioteca principal para logging estruturado em Python.

### Rationale
- **Industry Standard**: structlog é a biblioteca mais popular para logging estruturado em Python, amplamente usada em produção
- **JSON Nativo**: Suporte nativo para output JSON estruturado sem customizações complexas
- **Processadores Encadeados**: Arquitetura de processadores permite fácil extensão (redação, correlation IDs, timestamps)
- **Performance**: Benchmarks mostram overhead mínimo (<1ms) para operações de log estruturado
- **Integração**: Funciona perfeitamente com logging padrão do Python e permite interceptar logs de bibliotecas terceiras
- **Constitution Compliance**: Especificado explicitamente na constitution (Seção V: "Structured JSON logs using structlog")

### Alternatives Considered
- **python-json-logger**: Mais simples, mas menos flexível para processadores customizados e redação automática
- **loguru**: Excelente UX mas adiciona dependências pesadas e não é o padrão especificado pela constitution
- **Logging padrão Python com JSONFormatter custom**: Possível mas requer muito código boilerplate e não oferece processadores encadeados

### Implementation Notes
```python
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso", utc=True),  # UTC timestamps
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer()  # JSON output
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
    context_class=dict,
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)
```

---

## R2: Async Logging Pattern

### Decision
Implementar **queue-based async logging com blocking on saturation** usando `asyncio.Queue` e background task.

### Rationale
- **Zero Log Loss**: Constitution e spec exigem zero perda de logs (FR-017) - blocking garante isso
- **Performance**: Async I/O evita bloquear operações principais durante escrita de logs
- **Simplicidade**: `asyncio.Queue` é built-in, sem dependências externas
- **Backpressure**: Blocking quando buffer cheio previne saturação de memória e garante auditoria completa
- **Constitutional Requirement**: "System MUST support asynchronous logging; when buffer reaches capacity, MUST block writes until space is available to ensure zero log loss"

### Alternatives Considered
- **Drop on overflow**: Violaria requisito de zero perda de logs (FR-017) para auditoria
- **QueueHandler do logging padrão**: Não oferece controle fino sobre backpressure e comportamento de overflow
- **Threading-based queue**: Performance inferior ao asyncio para I/O-bound operations e mais complexo de integrar com MCP server async

### Implementation Notes
```python
import asyncio
from typing import Dict

class AsyncLogWriter:
    def __init__(self, queue_size: int = 10000):
        self._queue = asyncio.Queue(maxsize=queue_size)
        self._writer_task = None
    
    async def start(self):
        self._writer_task = asyncio.create_task(self._writer_loop())
    
    async def write_log(self, entry: Dict):
        # Blocks if queue is full - ensures zero log loss
        await self._queue.put(entry)
    
    async def _writer_loop(self):
        while True:
            entry = await self._queue.get()
            await self._write_to_file(entry)
```

---

## R3: Sensitive Data Redaction Pattern

### Decision
Implementar **regex-based pattern matching** com whitelist approach através de processador structlog customizado.

### Rationale
- **Constitution Mandate**: "Automatic Sensitive Data Sanitization: Connection credentials, message content (when configured), authentication tokens redacted before logging" (Seção V)
- **Defense in Depth**: Redação na camada de processamento garante que dados sensíveis nunca chegam ao arquivo
- **Configurável**: Patterns podem ser adicionados/removidos via configuração sem mudanças de código
- **Performance**: Regex compilation cache mantém overhead baixo
- **Compliance**: FR-004 exige redação automática obrigatória (zero credentials em logs)

### Alternatives Considered
- **Manual redaction por developers**: Alto risco de erro humano, violaria constitution requirement de redação automática
- **Post-processing de arquivos**: Vulnerável a janela de tempo onde dados sensíveis existem em disco
- **Blacklist de campos**: Menos seguro que whitelist approach; novos campos sensíveis podem ser esquecidos

### Implementation Notes
```python
import re
from typing import Dict, Any

SENSITIVE_PATTERNS = [
    (re.compile(r'password\s*=\s*["\']?([^"\'\s]+)', re.IGNORECASE), '[REDACTED]'),
    (re.compile(r'token\s*=\s*["\']?([^"\'\s]+)', re.IGNORECASE), '[REDACTED]'),
    (re.compile(r'api[_-]?key\s*=\s*["\']?([^"\'\s]+)', re.IGNORECASE), '[REDACTED]'),
    (re.compile(r'amqp://[^:]+:([^@]+)@', re.IGNORECASE), 'amqp://user:[REDACTED]@'),
]

def add_redaction_processor(logger, method_name, event_dict: Dict[str, Any]):
    """Processador structlog para redação automática"""
    for key, value in event_dict.items():
        if isinstance(value, str):
            for pattern, replacement in SENSITIVE_PATTERNS:
                value = pattern.sub(replacement, value)
            event_dict[key] = value
    return event_dict
```

---

## R4: File Rotation Strategy

### Decision
Usar **logging.handlers.RotatingFileHandler + TimedRotatingFileHandler** com custom wrapper para rotação dupla (tamanho + tempo).

### Rationale
- **Built-in Solution**: Handlers padrão do Python são battle-tested e não requerem dependências externas
- **Dual Rotation**: Spec requer rotação por dia (FR-012) E por tamanho 100MB (FR-013) - wrapper combina ambos
- **Thread-Safe**: Handlers built-in são thread-safe, importante para async contexts
- **Compression Support**: Fácil integrar gzip compression (FR-018) via namer/rotator callbacks
- **Constitutional Compliance**: "Daily rotation by default, maximum 100MB per file" (Seção V)

### Alternatives Considered
- **logrotate (external tool)**: Requer configuração do SO, não é cross-platform friendly
- **Custom implementation**: Mais complexo, propenso a bugs, reinventaria a roda
- **Bibliotecas terceiras (logging_tree)**: Overhead desnecessário para funcionalidade já disponível

### Implementation Notes
```python
import logging
from logging.handlers import TimedRotatingFileHandler, RotatingFileHandler
import gzip
import os

def namer(default_name):
    """Adiciona .gz aos arquivos rotacionados"""
    return default_name + ".gz"

def rotator(source, dest):
    """Comprime arquivo durante rotação"""
    with open(source, 'rb') as f_in:
        with gzip.open(dest, 'wb') as f_out:
            f_out.writelines(f_in)
    os.remove(source)

# Rotação por tempo (diária)
time_handler = TimedRotatingFileHandler(
    filename='logs/rabbitmq-mcp.log',
    when='midnight',
    interval=1,
    backupCount=30,  # 30 dias retention
    utc=True
)
time_handler.namer = namer
time_handler.rotator = rotator
```

---

## R5: Performance Optimization Strategy

### Decision
Implementar **lazy evaluation + batched writes + minimal serialization** para manter overhead <5ms por operação.

### Rationale
- **Critical Requirement**: FR-016 especifica <5ms overhead obrigatório
- **Lazy Evaluation**: Defer formatação JSON até momento de escrita evita trabalho se log level não for ativo
- **Batched Writes**: Agregar múltiplas entradas em write único reduz syscalls
- **Minimal Serialization**: Usar orjson (fast JSON library) em vez de json padrão
- **Benchmarking**: Todos componentes devem ter benchmarks para validar performance

### Alternatives Considered
- **Synchronous blocking writes**: Mais simples mas violaria requisito de <5ms
- **Compression on write**: Overhead muito alto, compression apenas para arquivos rotacionados (FR-018)
- **Rich formatting**: Sacrificaria performance por legibilidade, contra requisitos de spec

### Implementation Notes
```python
import orjson  # Fast JSON library (2-3x faster que json padrão)
import time
from typing import List, Dict

class PerformanceOptimizedLogger:
    def __init__(self, batch_size: int = 100, flush_interval: float = 0.1):
        self._batch: List[Dict] = []
        self._batch_size = batch_size
        self._flush_interval = flush_interval
        self._last_flush = time.monotonic()
    
    def log(self, entry: Dict):
        start = time.perf_counter()
        
        # Lazy evaluation - apenas prepara entrada
        self._batch.append(entry)
        
        # Flush se batch cheio ou intervalo expirado
        if len(self._batch) >= self._batch_size or \
           (time.monotonic() - self._last_flush) >= self._flush_interval:
            self._flush_batch()
        
        elapsed_ms = (time.perf_counter() - start) * 1000
        assert elapsed_ms < 5, f"Log overhead {elapsed_ms}ms exceeds 5ms limit"
    
    def _flush_batch(self):
        if not self._batch:
            return
        
        # Serialização em batch com orjson
        serialized = b'\n'.join(orjson.dumps(entry) for entry in self._batch)
        self._write_to_file(serialized)
        
        self._batch.clear()
        self._last_flush = time.monotonic()
```

---

## R6: Correlation ID Management

### Decision
Usar **contextvars** (Python 3.7+) para propagação de correlation IDs em contextos assíncronos.

### Rationale
- **Async-Safe**: contextvars mantém valores isolados por contexto async, perfeito para MCP server async
- **Automatic Propagation**: Valores propagam automaticamente através de await calls
- **Built-in**: Parte da stdlib Python, sem dependências
- **Constitutional Requirement**: "UUID-based correlation IDs for tracing messages across queues and consumers" (Seção V)
- **Spec Requirement**: FR-005 - "System MUST generate and assign unique correlation IDs at MCP tool invocation time"

### Alternatives Considered
- **Thread-local storage**: Não funciona corretamente com asyncio (contexto compartilhado entre tasks)
- **Manual passing via parameters**: Propenso a erros, difícil manter através de toda call stack
- **Request headers only**: Não captura internal operations não relacionadas a requests externos

### Implementation Notes
```python
import contextvars
import uuid
from typing import Optional

# Context var para correlation ID
correlation_id_var: contextvars.ContextVar[str] = contextvars.ContextVar(
    'correlation_id', 
    default=None
)

def generate_correlation_id() -> str:
    """Gera novo correlation ID (UUID v4)"""
    try:
        return str(uuid.uuid4())
    except Exception:
        # Fallback para timestamp-based se UUID falhar (edge case da spec)
        import time
        import random
        timestamp = int(time.time() * 1000000)
        random_part = random.randint(0, 999999)
        return f"{timestamp}-{random_part}"

def set_correlation_id(correlation_id: Optional[str] = None):
    """Define correlation ID para contexto atual"""
    if correlation_id is None:
        correlation_id = generate_correlation_id()
    correlation_id_var.set(correlation_id)
    return correlation_id

def get_correlation_id() -> Optional[str]:
    """Obtém correlation ID do contexto atual"""
    return correlation_id_var.get()

# Processador structlog para injetar correlation ID
def add_correlation_id(logger, method_name, event_dict):
    correlation_id = get_correlation_id()
    if correlation_id:
        event_dict['correlation_id'] = correlation_id
    return event_dict
```

---

## R7: Log Schema Design

### Decision
Adotar **schema flat com campos consistentes** baseado em práticas ECS (Elastic Common Schema) mas simplificado para MVP.

### Rationale
- **Queryability**: Schema flat facilita queries em ferramentas como jq, grep, log aggregators futuros
- **Consistency**: Campos padronizados em todas entradas facilitam parsing e análise
- **Extensibility**: Schema pode ser estendido com campos adicionais sem quebrar parsing existente
- **Industry Standard**: Inspirado em ECS, facilitará integração futura com Elasticsearch (fora de escopo MVP mas planejado)
- **Constitutional Requirement**: FR-001 - "System MUST write all logs in structured JSON format with consistent schema"

### Alternatives Considered
- **Nested objects**: Mais expressivo mas dificulta queries e aumenta tamanho de arquivos
- **Schema variável por tipo de log**: Complexo de manter e parsear, dificulta análise cross-category
- **Schema minimalista**: Perderia informação contextual importante para debugging

### Schema Structure
```json
{
  "timestamp": "2025-10-09T14:32:15.123456Z",
  "level": "INFO",
  "category": "Operation",
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "MCP tool executed successfully",
  "tool_name": "call-id",
  "operation_id": "queues.list",
  "duration_ms": 42.5,
  "result": "success",
  "context": {
    "vhost": "/",
    "queue_count": 15
  }
}
```

**Standard Fields** (sempre presentes):
- `timestamp`: ISO 8601 UTC (string)
- `level`: ERROR | WARN | INFO | DEBUG (string)
- `category`: Connection | Operation | Error | Security | Performance (string)
- `correlation_id`: UUID v4 ou timestamp-based fallback (string)
- `message`: Descrição human-readable (string)

**Optional Fields** (contexto específico):
- `tool_name`: Nome da MCP tool (string)
- `operation_id`: ID interno da operação (string)
- `duration_ms`: Duração da operação (float)
- `result`: success | error | timeout (string)
- `error_type`: Tipo de exceção se erro (string)
- `stack_trace`: Stack trace completo como string única com \n (string)
- `context`: Dados adicionais específicos da operação (object)

---

## R8: Log Output Destinations

### Decision
Implementar **3 destinos configuráveis** baseados em "most commonly used" para enterprise message queue applications:
1. **File-based (default)** - Arquivo local com rotação
2. **Console/stderr (fallback)** - Output de emergência se arquivo falhar
3. **RabbitMQ AMQP** - Publicar logs em exchange dedicada

### Rationale
- **File-based**: Constitution especifica "most commonly used for enterprise message queue applications"
- **Console fallback**: Obrigatório por FR-021 para garantir logs nunca sejam perdidos
- **RabbitMQ AMQP**: Constitution menciona "RabbitMQ native logging" + domain-aligned (dogfooding - RabbitMQ server publicando logs no próprio RabbitMQ)
- **Centralização natural**: Logs em exchange RabbitMQ permitem consumidores em tempo real e integração futura com agregadores
- **Gradual adoption**: Agregadores externos (Elasticsearch, Splunk, CloudWatch) podem consumir da fila em releases futuras

### Alternatives Considered
- **Apenas arquivo local**: Insuficiente para constitution requirement de destinos configuráveis
- **Elasticsearch direto**: Mais popular para agregação, mas adiciona dependência pesada; melhor consumir de RabbitMQ queue
- **Splunk/CloudWatch direto**: Vendor lock-in; melhor via consumer RabbitMQ
- **Apenas RabbitMQ AMQP**: Sem fallback local para debugging quando broker está down

### Implementation Notes
```python
from enum import Enum
from typing import Protocol

class LogDestination(str, Enum):
    FILE = "file"
    CONSOLE = "console"
    RABBITMQ = "rabbitmq"

class LogHandler(Protocol):
    """Interface para handlers de log"""
    def write(self, log_entry: dict) -> None: ...
    def flush(self) -> None: ...
    def close(self) -> None: ...

# Handler para arquivo (default)
class FileLogHandler:
    def __init__(self, config: LogConfig):
        self.file = open(config.output_file, 'a')
        self.rotation = setup_rotation(config)
    
    def write(self, log_entry: dict):
        self.file.write(orjson.dumps(log_entry) + b'\n')
        self.rotation.check_and_rotate()

# Handler para console (fallback)
class ConsoleLogHandler:
    def write(self, log_entry: dict):
        sys.stderr.write(orjson.dumps(log_entry).decode() + '\n')

# Handler para RabbitMQ AMQP
class RabbitMQLogHandler:
    def __init__(self, connection_params: dict, exchange: str = "logs"):
        self.connection = pika.BlockingConnection(connection_params)
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange=exchange,
            exchange_type='topic',
            durable=True
        )
        self.exchange = exchange
    
    def write(self, log_entry: dict):
        routing_key = f"{log_entry['level']}.{log_entry['category']}"
        self.channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=orjson.dumps(log_entry),
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent
                content_type='application/json'
            )
        )

# Multi-handler setup
class MultiDestinationLogger:
    def __init__(self, config: LogConfig):
        self.handlers = []
        
        # Always add file handler (default)
        if config.file_enabled:
            self.handlers.append(FileLogHandler(config))
        
        # Add RabbitMQ handler if configured
        if config.rabbitmq_enabled:
            self.handlers.append(RabbitMQLogHandler(config.rabbitmq_params))
        
        # Console fallback
        if config.fallback_to_console:
            self.fallback = ConsoleLogHandler()
    
    def log(self, entry: dict):
        for handler in self.handlers:
            try:
                handler.write(entry)
            except Exception as e:
                # Fallback to console if handler fails
                self.fallback.write({
                    "level": "ERROR",
                    "message": f"Log handler failed: {e}",
                    "original_entry": entry
                })
```

### Configuration Example
```yaml
# config/logging_config.yaml
destinations:
  file:
    enabled: true
    path: ./logs/rabbitmq-mcp-{date}.log
    rotation_max_bytes: 104857600
    retention_days: 30
    compression: true
  
  rabbitmq:
    enabled: true
    host: localhost
    port: 5672
    vhost: /
    exchange: logs
    routing_key_pattern: "{level}.{category}"
  
  console:
    enabled: true  # Sempre como fallback
    format: json   # ou 'pretty' para desenvolvimento
```

---

## R9: Testing Strategy

### Decision
Implementar **TDD rigoroso com 80%+ cobertura** usando pytest + fixtures + mocking para I/O.

### Rationale
- **Constitutional Mandate**: "TDD is mandatory: Tests written → User approved → Tests fail → Implementation" (Seção III)
- **Minimum Coverage**: "Minimum 80% coverage for all tools" (Seção III)
- **Pytest**: Framework padrão especificado na constitution
- **I/O Mocking**: Testes unitários devem ser rápidos, sem I/O real; integration tests validam I/O real
- **Performance Tests**: Testes específicos para validar overhead <5ms (FR-016)

### Test Categories
1. **Unit Tests** (80% da cobertura):
   - Redação de dados sensíveis (test_redaction.py)
   - Correlation ID generation e propagation (test_correlation.py)
   - Log formatters e processadores (test_formatters.py)
   - Rotação de arquivos (test_rotation.py)
   - Logger principal (test_logger.py)

2. **Integration Tests** (validação E2E):
   - Fluxo completo de logging (test_log_flow.py)
   - Async logging com backpressure (test_async_logging.py)
   - Performance e overhead (test_performance.py)

3. **Contract Tests** (validação de schema):
   - Schema JSON válido (test_log_schema.py)
   - Campos obrigatórios presentes
   - Tipos corretos

### Implementation Notes
```python
import pytest
import json
from pathlib import Path

@pytest.fixture
def temp_log_dir(tmp_path):
    """Fixture para diretório temporário de logs"""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    return log_dir

def test_sensitive_data_redaction():
    """Test FR-004: Redação automática de dados sensíveis"""
    # Given
    log_entry = {
        "message": "Connection successful",
        "connection_string": "amqp://user:secretpassword@localhost"
    }
    
    # When
    redacted = apply_redaction(log_entry)
    
    # Then
    assert "secretpassword" not in json.dumps(redacted)
    assert "[REDACTED]" in redacted["connection_string"]
    assert "user" in redacted["connection_string"]  # Username preservado para debugging

def test_log_overhead_performance():
    """Test FR-016: Overhead <5ms por operação"""
    import time
    
    # Given
    logger = get_logger()
    iterations = 1000
    
    # When
    start = time.perf_counter()
    for _ in range(iterations):
        logger.info("test message", extra={"key": "value"})
    elapsed_ms = (time.perf_counter() - start) * 1000
    
    # Then
    avg_overhead = elapsed_ms / iterations
    assert avg_overhead < 5, f"Average overhead {avg_overhead}ms exceeds 5ms limit"
```

---

## Summary of Decisions

| Area | Technology/Pattern | Primary Reason |
|------|-------------------|----------------|
| Structured Logging | structlog | Constitution standard, JSON nativo, processadores |
| Async Pattern | asyncio.Queue + blocking | Zero log loss, performance, simplicidade |
| Redaction | Regex patterns + whitelist | Segurança automática, constitution mandate |
| File Rotation | Python logging handlers | Built-in, dual rotation (tempo+tamanho), thread-safe |
| Performance | Lazy eval + batched writes + orjson | <5ms overhead requirement |
| Correlation IDs | contextvars | Async-safe propagation, built-in |
| Schema | Flat JSON (ECS-inspired) | Queryability, consistency, extensibility |
| Output Destinations | File + Console + RabbitMQ AMQP | Most common for enterprise message queue apps |
| Testing | pytest + TDD + 80% coverage | Constitution requirement, quality assurance |

---

## Next Steps

Phase 1 actions:
1. ✅ Research complete - todas decisões documentadas
2. 🔄 Criar data-model.md (entidades e schemas detalhados)
3. 🔄 Criar contracts/ com JSON schemas
4. 🔄 Criar quickstart.md (guia de uso rápido)
5. 🔄 Atualizar agent context com tecnologias escolhidas
