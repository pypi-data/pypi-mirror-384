# Data Model: Essential Topology Operations

**Feature**: 003-essential-topology-operations  
**Phase**: 1 - Design  
**Date**: 2025-10-09

## Overview

Este documento define as entidades de dados, seus atributos, validações e relacionamentos para operações de topologia RabbitMQ. Todas as entidades são derivadas dos schemas OpenAPI e requisitos funcionais especificados.

## Core Entities

### 1. Queue

Representa uma fila de mensagens no RabbitMQ.

**Attributes**:
```python
name: str
    - Description: Nome único da fila dentro do virtual host
    - Validation: ^[a-zA-Z0-9._-]{1,255}$ (FR-004)
    - Required: Yes
    - Example: "orders.processing.queue"

vhost: str
    - Description: Virtual host onde a fila reside
    - Validation: Non-empty string
    - Required: Yes
    - Default: "/"
    - Example: "/production"

durable: bool
    - Description: Fila sobrevive restart do broker
    - Required: No
    - Default: false
    - Example: true

auto_delete: bool
    - Description: Fila deletada automaticamente quando último consumidor desconecta
    - Required: No
    - Default: false
    - Example: false

exclusive: bool
    - Description: Fila exclusiva para uma conexão
    - Required: No
    - Default: false
    - Example: false

arguments: dict[str, Any]
    - Description: Argumentos adicionais (x-message-ttl, x-max-length, etc.)
    - Required: No
    - Default: {}
    - Example: {"x-message-ttl": 60000, "x-max-length": 1000}

# Statistics (read-only, from Management API)
messages: int
    - Description: Contagem total de mensagens na fila (FR-002)
    - Source: GET /api/queues response
    - Example: 1523

messages_ready: int
    - Description: Mensagens prontas para entrega
    - Source: GET /api/queues response
    - Example: 1200

messages_unacknowledged: int
    - Description: Mensagens entregues mas não confirmadas
    - Source: GET /api/queues response
    - Example: 323

consumers: int
    - Description: Número de consumidores ativos (FR-002)
    - Source: GET /api/queues response
    - Example: 5

memory: int
    - Description: Uso de memória em bytes (FR-002)
    - Source: GET /api/queues response
    - Example: 2048576

state: str
    - Description: Estado atual da fila (running, idle, etc.)
    - Source: GET /api/queues response
    - Example: "running"
```

**Validation Rules**:
- Name must match regex: `^[a-zA-Z0-9._-]{1,255}$` (FR-004)
- Name must be unique per vhost (FR-005)
- Cannot create queue with duplicate name (FR-005)
- Virtual host must exist before creating queue (FR-024)

**State Transitions**:
- `creating` → `running`: Queue successfully created
- `running` → `idle`: No active consumers or message flow
- `running` → `deleting`: Delete operation initiated
- `deleting` → `deleted`: Queue removed (only if empty or --force used)

**Business Rules**:
- Deletion blocked if `messages > 0` without --force flag (FR-007, FR-008)
- Deletion allowed if `messages == 0` (FR-007)
- Force deletion requires explicit flag (FR-008)

---

### 2. Exchange

Representa um roteador de mensagens no RabbitMQ.

**Attributes**:
```python
name: str
    - Description: Nome único do exchange dentro do virtual host
    - Validation: ^[a-zA-Z0-9._-]{1,255}$ (FR-013)
    - Required: Yes
    - Example: "orders.exchange"

vhost: str
    - Description: Virtual host onde o exchange reside
    - Validation: Non-empty string
    - Required: Yes
    - Default: "/"
    - Example: "/production"

type: str
    - Description: Tipo de exchange define algoritmo de roteamento
    - Validation: enum("direct", "topic", "fanout", "headers") (FR-012, FR-013)
    - Required: Yes
    - Example: "topic"

durable: bool
    - Description: Exchange sobrevive restart do broker
    - Required: No
    - Default: false
    - Example: true

auto_delete: bool
    - Description: Exchange deletado automaticamente quando último binding é removido
    - Required: No
    - Default: false
    - Example: false

internal: bool
    - Description: Exchange não aceita mensagens diretamente de publishers
    - Required: No
    - Default: false
    - Example: false

arguments: dict[str, Any]
    - Description: Argumentos adicionais (alternate-exchange, etc.)
    - Required: No
    - Default: {}
    - Example: {"alternate-exchange": "dead.letters"}

# Statistics (read-only, from Management API)
message_stats: dict
    - Description: Estatísticas de throughput de mensagens (FR-010)
    - Source: GET /api/exchanges response
    - Example: {"publish_in": 1523, "publish_out": 1523}

bindings_count: int
    - Description: Número de bindings ativos (FR-010)
    - Source: Count from GET /api/bindings
    - Example: 15
```

**Validation Rules**:
- Name must match regex: `^[a-zA-Z0-9._-]{1,255}$` (FR-013)
- Type must be one of: "direct", "topic", "fanout", "headers" (FR-012, FR-013)
- Name must be unique per vhost (FR-014)
- Cannot create exchange with duplicate name (FR-014)
- Virtual host must exist before creating exchange (FR-024)
- Cannot delete system exchanges: "amq.*" prefix or "" (empty string default exchange) (FR-017)

**Exchange Types**:
- **direct**: Routes messages to queues based on exact routing key match
- **topic**: Routes messages using wildcard patterns (* and #) (FR-021)
- **fanout**: Routes messages to all bound queues, ignoring routing key
- **headers**: Routes based on message header attributes

**Business Rules**:
- Deletion blocked if `bindings_count > 0` (FR-016)
- System exchanges (amq.* prefix and "" default exchange) cannot be deleted (FR-017)
- Operator must delete all bindings before deleting exchange (FR-016)

---

### 3. Binding

Representa uma regra de roteamento conectando exchange a fila.

**Attributes**:
```python
source: str
    - Description: Nome do exchange de origem
    - Validation: Must be existing exchange name
    - Required: Yes
    - Example: "orders.exchange"

destination: str
    - Description: Nome da fila de destino
    - Validation: Must be existing queue name
    - Required: Yes
    - Example: "orders.processing.queue"

destination_type: str
    - Description: Tipo de destino (queue ou exchange)
    - Validation: enum("queue", "exchange")
    - Required: Yes
    - Default: "queue"
    - Example: "queue"

vhost: str
    - Description: Virtual host onde binding existe
    - Validation: Non-empty string
    - Required: Yes
    - Default: "/"
    - Example: "/production"

routing_key: str
    - Description: Chave de roteamento para matching
    - Validation: String, supports wildcards for topic exchanges (FR-021)
    - Required: No
    - Default: ""
    - Example: "orders.*.created"

arguments: dict[str, Any]
    - Description: Argumentos adicionais para binding
    - Required: No
    - Default: {}
    - Example: {"x-match": "all"}

properties_key: str
    - Description: Identificador único do binding gerado pelo RabbitMQ (usado para deleção)
    - Source: RabbitMQ Management API (campo "properties_key" na response)
    - Read-only: Yes
    - Note: Geralmente deriva da routing_key mas pode incluir hash de arguments se presentes
    - Example: "orders.*.created" ou "~" para binding sem routing key
```

**Validation Rules**:
- Source exchange must exist before creating binding (FR-020)
- Destination queue must exist before creating binding (FR-020)
- Cannot create duplicate binding (same source, destination, routing_key) (FR-023)
- Routing key wildcards (* and #) only valid for topic exchanges (FR-021)
- Virtual host must exist (FR-024)

**Routing Key Patterns** (for topic exchanges - FR-021):
- `*` (asterisk): Matches exactly one word
  - Example: `orders.*.created` matches `orders.eu.created` but not `orders.eu.us.created`
- `#` (hash): Matches zero or more words
  - Example: `orders.#` matches `orders.created`, `orders.eu.created`, `orders.eu.us.created`

**Business Rules**:
- Duplicate bindings prevented (FR-023)
- Binding validation occurs before creation (FR-020)
- Deleting binding stops message flow immediately (FR-022)

---

### 4. VirtualHost (Context)

Representa agrupamento lógico isolando conjuntos de filas, exchanges e bindings.

**Attributes**:
```python
name: str
    - Description: Nome do virtual host
    - Validation: Non-empty string
    - Required: Yes
    - Default: "/"
    - Example: "/production"

# Note: VirtualHost operations are not in scope for this feature
# but the entity is referenced for context and validation
```

**Validation Rules**:
- Must exist before any queue/exchange/binding operations (FR-024)
- Error clearly indicates if vhost doesn't exist (Edge case documentation)

---

## Relationships

```
            ┌─────────────────┐
            │  VirtualHost    │
            │  (namespace)    │
            └────────┬────────┘
                     │ contains (1:N)
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
    ┌──────────┐          ┌──────────┐
    │ Exchange │          │  Queue   │
    │ (router) │          │ (buffer) │
    └─────┬────┘          └─────┬────┘
          │                     │
          │     ┌──────────┐    │
          └─────►  Binding ◄────┘
                │ (M:N rule)│
                └──────────┘

Relationships:
• VirtualHost → Exchange: 1:N (one vhost, many exchanges)
• VirtualHost → Queue: 1:N (one vhost, many queues)
• Exchange ↔ Queue: M:N via Binding (many-to-many routing rules)
```

**Relationship Rules**:
1. **VirtualHost → Exchange**: 1:N
   - One vhost contains many exchanges
   - Exchange cannot exist without vhost

2. **VirtualHost → Queue**: 1:N
   - One vhost contains many queues
   - Queue cannot exist without vhost

3. **Exchange → Binding → Queue**: M:N
   - Many-to-many through Binding entity
   - One exchange can bind to many queues
   - One queue can bind to many exchanges
   - Binding requires both exchange and queue to exist (FR-020)

---

## Operation Schemas

### Pagination Entities

**PaginationParams** (Input):
```python
page: int
    - Description: Page number (1-based)
    - Validation: >= 1
    - Required: No
    - Default: 1
    - Example: 1

pageSize: int
    - Description: Items per page
    - Validation: 1 <= pageSize <= 200
    - Required: No
    - Default: 50
    - Example: 50
```

**PaginationMetadata** (Output):
```python
page: int
    - Description: Current page number (1-based)
    - Required: Yes (OBRIGATÓRIO em todas respostas paginadas - FR-035)
    - Example: 1

pageSize: int
    - Description: Items per page
    - Required: Yes (OBRIGATÓRIO em todas respostas paginadas - FR-035)
    - Example: 50

totalItems: int
    - Description: Total number of items across all pages
    - Required: Yes (OBRIGATÓRIO em todas respostas paginadas - FR-035)
    - Example: 150

totalPages: int
    - Description: Total number of pages
    - Required: Yes (OBRIGATÓRIO em todas respostas paginadas - FR-035)
    - Calculation: ceil(totalItems / pageSize)
    - Example: 3

hasNextPage: bool
    - Description: Whether there is a next page
    - Required: Yes (OBRIGATÓRIO em todas respostas paginadas - FR-035)
    - Calculation: page < totalPages
    - Example: true

hasPreviousPage: bool
    - Description: Whether there is a previous page
    - Required: Yes (OBRIGATÓRIO em todas respostas paginadas - FR-035)
    - Calculation: page > 1
    - Example: false
```

---

## Operation Schemas

### Queue Operations

**List Queues** (`queues.list`):
- Method: GET
- OpenAPI Path: `/api/queues` or `/api/queues/{vhost}`
- Input: vhost (optional), page (default 1), pageSize (default 50, max 200)
- Output: PaginatedQueueResponse { items: List[Queue], pagination: PaginationMetadata }
- Validation: vhost must exist if specified (FR-024), page >= 1, 1 <= pageSize <= 200 (FR-034)
- Performance: < 2 seconds per page (SC-001, SC-006, FR-036)

**Create Queue** (`queues.create`):
- Method: PUT
- OpenAPI Path: `/api/queues/{vhost}/{name}`
- Input: Queue (name, vhost, durable, exclusive, auto_delete, arguments)
- Output: Success or error
- Validation: FR-004 (name pattern), FR-005 (no duplicates), FR-024 (vhost exists)
- Performance: < 1 second (SC-002)

**Delete Queue** (`queues.delete`):
- Method: DELETE
- OpenAPI Path: `/api/queues/{vhost}/{name}`
- Input: vhost, name, force (optional flag)
- Output: Success or error
- Validation: FR-007 (check empty), FR-008 (force flag)
- Performance: < 1 second (SC-003)
- Safety: 100% prevention without force flag (SC-004)

---

### Exchange Operations

**List Exchanges** (`exchanges.list`):
- Method: GET
- OpenAPI Path: `/api/exchanges` or `/api/exchanges/{vhost}`
- Input: vhost (optional), page (default 1), pageSize (default 50, max 200)
- Output: PaginatedExchangeResponse { items: List[Exchange], pagination: PaginationMetadata }
- Validation: vhost must exist if specified (FR-024), page >= 1, 1 <= pageSize <= 200 (FR-034)
- Performance: < 2 seconds per page (SC-001, SC-006, FR-036)

**Create Exchange** (`exchanges.create`):
- Method: PUT
- OpenAPI Path: `/api/exchanges/{vhost}/{name}`
- Input: Exchange (name, vhost, type, durable, auto_delete, internal, arguments)
- Output: Success or error
- Validation: FR-013 (name + type), FR-014 (no duplicates), FR-024 (vhost exists)
- Performance: < 1 second (SC-002)

**Delete Exchange** (`exchanges.delete`):
- Method: DELETE
- OpenAPI Path: `/api/exchanges/{vhost}/{name}`
- Input: vhost, name
- Output: Success or error
- Validation: FR-016 (no active bindings), FR-017 (no system exchanges)
- Performance: < 1 second (SC-003)
- Safety: 100% block if bindings exist (SC-005)

---

### Binding Operations

**List Bindings** (`bindings.list`):
- Method: GET
- OpenAPI Path: `/api/bindings` or `/api/bindings/{vhost}`
- Input: vhost (optional), page (default 1), pageSize (default 50, max 200)
- Output: PaginatedBindingResponse { items: List[Binding], pagination: PaginationMetadata }
- Validation: vhost must exist if specified (FR-024), page >= 1, 1 <= pageSize <= 200 (FR-034)
- Performance: < 2 seconds per page (SC-001, FR-036)

**Create Binding** (`bindings.create`):
- Method: POST
- OpenAPI Path: `/api/bindings/{vhost}/e/{exchange}/q/{queue}`
- Input: vhost, exchange, queue, routing_key, arguments
- Output: Success or error
- Validation: FR-020 (exchange + queue exist), FR-023 (no duplicates)
- Performance: < 1 second (SC-002)

**Delete Binding** (`bindings.delete`):
- Method: DELETE
- OpenAPI Path: `/api/bindings/{vhost}/e/{exchange}/q/{queue}/{properties_key}`
- Input: vhost, exchange, queue, properties_key
- Output: Success or error
- Validation: Binding must exist
- Performance: < 1 second (SC-003)

---

## Error Handling

### Validation Errors

```python
class ValidationError:
    code: str          # "INVALID_NAME", "DUPLICATE_ENTITY", etc.
    message: str       # Human-readable error message (FR-025)
    field: str         # Field that failed validation
    expected: str      # Expected format or value
    actual: str        # Actual value provided
```

**Examples**:
- Invalid queue name: "Queue name 'my queue!' contains invalid characters. Only alphanumeric, hyphen, underscore, and dot allowed (max 255 chars)."
- Duplicate queue: "Queue 'orders.queue' already exists in vhost '/production'."
- Missing vhost: "Virtual host '/invalid' does not exist."

### Operation Errors

```python
class OperationError:
    code: str          # "QUEUE_NOT_EMPTY", "EXCHANGE_HAS_BINDINGS", etc.
    message: str       # Clear, actionable error message (FR-025, SC-007)
    suggestion: str    # How to fix the issue
    details: dict      # Additional context
```

**Examples**:
- Queue not empty: "Cannot delete queue 'orders.queue' containing 523 messages. Use --force flag to force deletion."
- Exchange has bindings: "Cannot delete exchange 'orders.exchange' with 5 active bindings. Remove bindings first using 'binding delete' command."
- System exchange: "Cannot delete system exchange 'amq.direct'. System exchanges (amq.* and '' default exchange) are protected."

---

## Audit Logging

All mutation operations (create, delete) must be logged for audit (FR-026, SC-008):

```python
class AuditLogEntry:
    timestamp: datetime
    operation: str         # "queues.create", "exchanges.delete", etc.
    entity_type: str       # "queue", "exchange", "binding"
    entity_name: str       # Name of the entity
    vhost: str            # Virtual host
    user: str             # RabbitMQ user who performed operation
    status: str           # "success", "failed"
    error: str | None     # Error message if failed
    correlation_id: str   # UUID for request tracing
```

**Log Format** (structured JSON via structlog):
```json
{
  "timestamp": "2025-10-09T10:30:45Z",
  "level": "INFO",
  "operation": "queues.create",
  "entity_type": "queue",
  "entity_name": "orders.processing.queue",
  "vhost": "/production",
  "user": "admin",
  "status": "success",
  "correlation_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "duration_ms": 150
}
```

---

## Performance Considerations

### Caching
- Operation schemas cached with 5-minute TTL
- No entity data caching (always fetch fresh from Management API)

### Batch Operations
- Not in scope for this feature (Phase 1)
- Future consideration for bulk queue/exchange creation

### Pagination
- **Client-side pagination obrigatória** em todas operações list (FR-033)
- RabbitMQ Management API não suporta paginação nativa, então:
  - Sistema busca todos resultados do RabbitMQ API
  - Aplica slice em memória baseado em page/pageSize
  - Calcula metadados (totalItems, totalPages, hasNextPage, hasPreviousPage)
- Default: 50 itens por página, máximo 200 (FR-034)
- Performance target: < 2 segundos por página mesmo com 1000+ entidades (SC-006)

---

## Next Steps

1. ✅ Data model defined with complete attributes and validations
2. → Create OpenAPI contracts in `contracts/` directory
3. → Create quickstart guide with practical examples
4. → Update agent context with technology decisions

---

**Data Model Complete**: ✅  
**Entities validated against requirements**: ✅  
**Ready for contract generation**: ✅
