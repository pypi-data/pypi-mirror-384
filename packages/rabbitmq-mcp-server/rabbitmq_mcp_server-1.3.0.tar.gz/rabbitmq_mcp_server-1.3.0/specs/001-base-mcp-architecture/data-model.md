# Data Model: Base MCP Architecture

**Feature**: Base MCP Architecture  
**Date**: 2025-10-09  
**Phase**: 1 - Design & Contracts

## Overview

Este documento define as entidades principais, seus campos, relacionamentos e regras de validação para o servidor MCP com descoberta semântica de operações RabbitMQ.

## Core Entities

### 1. Operation

Representa uma operação executável no RabbitMQ, acessível via MCP tools.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string | ✅ | Identificador único no formato `{namespace}.{name}` | Pattern: `^[a-z-]+\.[a-z-]+$` |
| `name` | string | ✅ | Nome legível da operação | Min: 3, Max: 100 chars |
| `description` | string | ✅ | Descrição detalhada extraída do OpenAPI | Min: 10 chars |
| `namespace` | string | ✅ | Categoria lógica (tag do OpenAPI) | Enum: ver Namespace entity |
| `http_method` | string | ✅ | Método HTTP da operação | Enum: GET, POST, PUT, DELETE, PATCH |
| `http_path` | string | ✅ | Path do endpoint RabbitMQ API | Pattern: `^/api/.*$` |
| `openapi_operation_id` | string | ❌ | Operation ID original do OpenAPI | - |
| `request_schema` | Schema | ❌ | Esquema de parâmetros de entrada | Ver Schema entity |
| `response_schema` | Schema | ✅ | Esquema de resposta esperada | Ver Schema entity |
| `examples` | list[Example] | ❌ | Exemplos de uso | - |
| `deprecated` | boolean | ✅ | Se a operação está deprecated | Default: false |
| `requires_auth` | boolean | ✅ | Se requer autenticação RabbitMQ | Default: true |
| `timeout_seconds` | integer | ✅ | Timeout máximo para execução | Default: 30, Max: 30 |
| `created_at` | datetime | ✅ | Timestamp de criação no registry | ISO 8601 format |

**Relationships**:
- `namespace`: Many-to-One com Namespace
- `embedding`: One-to-One com Embedding
- `examples`: One-to-Many com Example

**State Transitions**: N/A (entidade read-only após build)

**Validation Rules**:
- `id` deve ser único no registry
- `http_path` deve ser válido e corresponder ao OpenAPI spec
- Se `deprecated = true`, deve incluir mensagem em `description`
- `timeout_seconds` não pode exceder 30 segundos (constitutional limit)

**Example**:
```json
{
  "id": "queues.list",
  "name": "List Queues",
  "description": "List all queues in a virtual host with optional filtering",
  "namespace": "queues",
  "http_method": "GET",
  "http_path": "/api/queues/{vhost}",
  "openapi_operation_id": "listQueues",
  "request_schema": {
    "type": "object",
    "properties": {
      "vhost": {"type": "string", "default": "/"},
      "page": {"type": "integer", "minimum": 1},
      "pageSize": {"type": "integer", "minimum": 1, "maximum": 200}
    },
    "required": ["vhost"]
  },
  "response_schema": {
    "type": "array",
    "items": {"$ref": "#/components/schemas/Queue"}
  },
  "deprecated": false,
  "requires_auth": true,
  "timeout_seconds": 30,
  "created_at": "2025-10-09T10:00:00Z"
}
```

### 2. Namespace

Agrupamento lógico de operações relacionadas, derivado das tags do OpenAPI.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `name` | string | ✅ | Nome do namespace | Pattern: `^[a-z-]+$` |
| `display_name` | string | ✅ | Nome legível | - |
| `description` | string | ✅ | Descrição da categoria | Min: 10 chars |
| `operation_count` | integer | ✅ | Número de operações no namespace | Min: 0 |

**Relationships**:
- `operations`: One-to-Many com Operation

**Known Namespaces** (from OpenAPI tags):
```python
NAMESPACES = [
    "cluster",      # Cluster management
    "nodes",        # Node monitoring
    "connections",  # Connection management
    "channels",     # Channel operations
    "exchanges",    # Exchange CRUD
    "queues",       # Queue CRUD
    "bindings",     # Binding management
    "vhosts",       # Virtual host operations
    "users",        # User management
    "permissions",  # Permission management
    "parameters",   # Runtime parameters
    "policies",     # Policy management
    "health",       # Health checks
    "definitions",  # Import/export
    "features",     # Feature flags
    "amqp",         # AMQP protocol operations (not in OpenAPI)
]
```

**Example**:
```json
{
  "name": "queues",
  "display_name": "Queues",
  "description": "Queue management operations including creation, deletion, and listing",
  "operation_count": 12
}
```

### 3. Schema

Define estrutura de parâmetros e validação para operações.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `type` | string | ✅ | Tipo JSON Schema | Enum: object, array, string, integer, boolean, number |
| `properties` | dict | ❌ | Propriedades do objeto (se type=object) | - |
| `items` | Schema | ❌ | Schema dos items (se type=array) | - |
| `required` | list[string] | ❌ | Campos obrigatórios | - |
| `additionalProperties` | boolean | ❌ | Permite propriedades extras | Default: false |
| `minimum` | number | ❌ | Valor mínimo (para numbers) | - |
| `maximum` | number | ❌ | Valor máximo (para numbers) | - |
| `minLength` | integer | ❌ | Tamanho mínimo (para strings) | - |
| `maxLength` | integer | ❌ | Tamanho máximo (para strings) | - |
| `pattern` | string | ❌ | Regex pattern (para strings) | Valid regex |
| `enum` | list | ❌ | Valores permitidos | - |
| `default` | any | ❌ | Valor padrão | - |
| `description` | string | ❌ | Descrição do campo | - |

**Validation Rules**:
- JSON Schema draft 7 compliant
- Deve ser validável por biblioteca jsonschema
- Referências ($ref) devem apontar para schemas existentes

**Example**:
```json
{
  "type": "object",
  "properties": {
    "vhost": {
      "type": "string",
      "description": "Virtual host name",
      "default": "/",
      "pattern": "^[\\w-]+$"
    },
    "page": {
      "type": "integer",
      "description": "Page number for pagination",
      "minimum": 1,
      "default": 1
    },
    "pageSize": {
      "type": "integer",
      "description": "Items per page",
      "minimum": 1,
      "maximum": 200,
      "default": 50
    }
  },
  "required": ["vhost"],
  "additionalProperties": false
}
```

### 4. Embedding

Vector embedding para busca semântica de operações.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `operation_id` | string | ✅ | ID da operação associada | FK: Operation.id |
| `vector` | array[float] | ✅ | Vector de embeddings (384 dims) | Length: 384 |
| `model_name` | string | ✅ | Nome do modelo usado | Default: "all-MiniLM-L6-v2" |
| `model_version` | string | ✅ | Versão do modelo | Semantic version |
| `source_text` | string | ✅ | Texto usado para gerar embedding | Concatenação de description + examples |
| `created_at` | datetime | ✅ | Timestamp de geração | ISO 8601 format |

**Relationships**:
- `operation`: One-to-One com Operation

**Validation Rules**:
- `vector` deve ter exatamente 384 dimensões (modelo all-MiniLM-L6-v2)
- `source_text` deve ser não-vazio
- Regeneração necessária se model_version mudar

**Example**:
```json
{
  "operation_id": "queues.list",
  "vector": [0.023, -0.145, 0.678, ...],  // 384 floats
  "model_name": "all-MiniLM-L6-v2",
  "model_version": "2.2.0",
  "source_text": "List all queues in a virtual host with optional filtering. Returns queue details including message counts, consumers, and configuration.",
  "created_at": "2025-10-09T10:00:00Z"
}
```

### 5. SearchResult

Resultado de busca semântica retornado por search-ids tool.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `operation_id` | string | ✅ | ID da operação encontrada | - |
| `name` | string | ✅ | Nome legível da operação | - |
| `description` | string | ✅ | Breve descrição | Max: 200 chars |
| `namespace` | string | ✅ | Namespace da operação | - |
| `similarity_score` | float | ✅ | Score de similaridade semântica | Range: 0.0-1.0 |
| `parameter_hint` | string | ❌ | Dica de parâmetros principais | Max: 100 chars |

**Validation Rules**:
- `similarity_score` >= 0.7 (threshold constitucional)
- Ordenado por `similarity_score` DESC
- Máximo 25 resultados por página

**Example**:
```json
{
  "operation_id": "queues.list",
  "name": "List Queues",
  "description": "List all queues in a virtual host with filtering options",
  "namespace": "queues",
  "similarity_score": 0.89,
  "parameter_hint": "vhost (required), page, pageSize"
}
```

### 6. OperationExecution

Contexto e resultado de execução de uma operação via call-id tool.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `request_id` | string | ✅ | ID único da requisição MCP | UUID v4 |
| `operation_id` | string | ✅ | ID da operação executada | FK: Operation.id |
| `params` | dict | ✅ | Parâmetros fornecidos | Validado contra Operation.request_schema |
| `status` | string | ✅ | Status da execução | Enum: success, error, timeout |
| `result` | any | ❌ | Resultado da operação (se success) | Validado contra Operation.response_schema |
| `error` | ErrorDetail | ❌ | Detalhes do erro (se error/timeout) | - |
| `started_at` | datetime | ✅ | Início da execução | ISO 8601 |
| `completed_at` | datetime | ✅ | Fim da execução | ISO 8601 |
| `duration_ms` | integer | ✅ | Duração em milissegundos | Max: 30000 (30s timeout) |
| `trace_id` | string | ✅ | OpenTelemetry trace ID | - |

**State Transitions**:
```
pending → running → success
                  → error
                  → timeout
```

**Validation Rules**:
- `duration_ms` <= 30000 (timeout constitucional)
- Se `status = error`, `error` deve estar presente
- Se `status = success`, `result` deve estar presente
- `completed_at` >= `started_at`

**Example (Success)**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "operation_id": "queues.list",
  "params": {"vhost": "/", "page": 1, "pageSize": 50},
  "status": "success",
  "result": [
    {
      "name": "my-queue",
      "vhost": "/",
      "durable": true,
      "messages": 42
    }
  ],
  "started_at": "2025-10-09T10:00:00.000Z",
  "completed_at": "2025-10-09T10:00:00.150Z",
  "duration_ms": 150,
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
}
```

**Example (Error)**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440001",
  "operation_id": "queues.create",
  "params": {"name": "test-queue"},
  "status": "error",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "details": {
      "missing": ["vhost"],
      "invalid": []
    }
  },
  "started_at": "2025-10-09T10:01:00.000Z",
  "completed_at": "2025-10-09T10:01:00.005Z",
  "duration_ms": 5,
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4737"
}
```

### 7. ErrorDetail

Estrutura padronizada de erros seguindo MCP protocol.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `code` | integer | ✅ | Código de erro JSON-RPC 2.0 | Ver tabela abaixo |
| `message` | string | ✅ | Mensagem de erro legível | - |
| `details` | dict | ❌ | Detalhes adicionais do erro | - |

**Error Codes** (JSON-RPC 2.0):
| Code | Name | Description | When to Use |
|------|------|-------------|-------------|
| `-32700` | Parse error | JSON inválido | Parsing de request/response falhou |
| `-32600` | Invalid request | Request malformado | Falta campos obrigatórios no request |
| `-32601` | Method not found | Método não existe | operation_id não encontrado |
| `-32602` | Invalid params | Parâmetros inválidos | Validação de params falhou |
| `-32603` | Internal error | Erro interno do servidor | Erros não esperados |
| `-32000` | Server error | RabbitMQ unreachable | Conexão com RabbitMQ falhou |
| `-32001` | Timeout error | Operation timeout | Operação excedeu 30s |
| `-32002` | Rate limit error | Rate limit exceeded | Cliente excedeu 100 req/min |

**Example**:
```json
{
  "code": -32602,
  "message": "Invalid params: missing required field 'vhost'",
  "details": {
    "missing": ["vhost"],
    "invalid": [],
    "provided": ["name", "durable"]
  }
}
```

### 8. PaginationParams

Parâmetros de paginação para operações de listagem.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `page` | integer | ❌ | Número da página (1-based) | Min: 1, Default: 1 |
| `pageSize` | integer | ❌ | Items por página | Min: 1, Max: 200, Default: 50 |

**Validation Rules**:
- Constitucional: max pageSize = 200
- Default pageSize: 50 (balance entre performance e UX)
- Page numbers são 1-based (user-friendly)

**Example**:
```json
{
  "page": 2,
  "pageSize": 25
}
```

### 9. PaginatedResponse

Resposta paginada para operações de listagem.

**Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `items` | array[T] | ✅ | Items da página atual | Max length: pageSize |
| `pagination` | PaginationMetadata | ✅ | Metadados de paginação | - |

**PaginationMetadata Fields**:
| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `page` | integer | ✅ | Página atual | >= 1 |
| `pageSize` | integer | ✅ | Items por página | 1-200 |
| `totalItems` | integer | ✅ | Total de items disponíveis | >= 0 |
| `totalPages` | integer | ✅ | Total de páginas | >= 0 |
| `hasNextPage` | boolean | ✅ | Indica se há próxima página | - |
| `hasPreviousPage` | boolean | ✅ | Indica se há página anterior | - |

**Example**:
```json
{
  "items": [
    {"operation_id": "queues.list", "name": "List Queues", "similarity_score": 0.92},
    {"operation_id": "queues.get", "name": "Get Queue", "similarity_score": 0.87}
  ],
  "pagination": {
    "page": 1,
    "pageSize": 25,
    "totalItems": 47,
    "totalPages": 2,
    "hasNextPage": true,
    "hasPreviousPage": false
  }
}
```

## Entity Relationships Diagram

```
┌─────────────┐
│  Namespace  │
└──────┬──────┘
       │
       │ 1:N
       │
       ▼
┌─────────────┐         1:1         ┌─────────────┐
│  Operation  │◄────────────────────┤  Embedding  │
└──────┬──────┘                     └─────────────┘
       │
       │ 1:N
       │
       ▼
┌─────────────┐
│   Example   │
└─────────────┘

┌──────────────────┐
│ OperationExecution│
└──────────┬───────┘
           │
           │ uses
           │
           ▼
┌─────────────┐
│  Operation  │
└─────────────┘
```

## Data Storage Strategy

### SQLite Database Schema

**File**: `data/rabbitmq_operations.db`

```sql
-- Namespaces table
CREATE TABLE namespaces (
    name TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    description TEXT NOT NULL,
    operation_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Operations table
CREATE TABLE operations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    namespace TEXT NOT NULL,
    http_method TEXT NOT NULL,
    http_path TEXT NOT NULL,
    openapi_operation_id TEXT,
    request_schema_json TEXT,
    response_schema_json TEXT NOT NULL,
    examples_json TEXT,
    deprecated BOOLEAN DEFAULT 0,
    requires_auth BOOLEAN DEFAULT 1,
    timeout_seconds INTEGER DEFAULT 30,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (namespace) REFERENCES namespaces(name)
);

-- Embeddings table
CREATE TABLE embeddings (
    operation_id TEXT PRIMARY KEY,
    vector BLOB NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    source_text TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operation_id) REFERENCES operations(id)
);

-- Metadata table (versioning and tracking)
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_operations_namespace ON operations(namespace);
CREATE INDEX idx_operations_deprecated ON operations(deprecated);
CREATE INDEX idx_operations_http_method ON operations(http_method);
```

## Validation Rules Summary

### Global Validation Rules
1. Todos os timestamps em formato ISO 8601
2. Todos os IDs de operação seguem pattern `{namespace}.{name}`
3. Todas as strings não-vazias a menos que explicitamente opcional
4. Timeout máximo: 30 segundos (constitutional)
5. PageSize máximo: 200 (constitutional)
6. Similarity threshold mínimo: 0.7 (constitutional)
7. Rate limit: 100 req/min por cliente (constitutional)

### Schema Validation Workflow
```python
# 1. Validate operation ID exists
operation = get_operation(operation_id)
if not operation:
    raise MethodNotFoundError(operation_id)

# 2. Validate params against request schema
validate_json_schema(params, operation.request_schema)

# 3. Execute operation with timeout
result = await execute_with_timeout(
    operation, 
    params, 
    timeout_seconds=operation.timeout_seconds
)

# 4. Validate result against response schema
validate_json_schema(result, operation.response_schema)

# 5. Return validated result
return result
```

## Migration Strategy

### Initial Build
1. Parse OpenAPI spec
2. Extract operations, namespaces, schemas
3. Generate Pydantic models
4. Generate embeddings
5. Populate SQLite database
6. Commit database to repo

### OpenAPI Updates
1. Detect changes in `.specify/memory/rabbitmq-http-api-openapi.yaml`
2. Re-run generation scripts
3. Verify schema compatibility
4. Update SQLite database
5. Regenerate embeddings if descriptions changed
6. Commit updated artifacts

### Version Support
- Multiple SQLite databases: `rabbitmq_operations_v{version}.db`
- Load appropriate database based on `RABBITMQ_API_VERSION` env var
- CI/CD validates all supported versions

## Data Integrity Checks

### Pre-commit Validation
```bash
# 1. Validate OpenAPI spec is valid YAML
python scripts/validate_openapi.py

# 2. Check all operations have embeddings
python scripts/check_embeddings_sync.py

# 3. Verify schemas are up-to-date
pytest tests/contract/test_openapi_sync.py

# 4. Validate database integrity
python scripts/validate_database.py
```

### Runtime Validation
- Operation ID exists before execution
- Parameters match request schema
- Response matches response schema
- Timeout enforcement
- Rate limit enforcement

## Performance Considerations

### Indexing Strategy
- B-tree indexes on `namespace`, `deprecated`, `http_method`
- Vector similarity search using ChromaDB/sqlite-vec
- In-memory cache for frequently accessed operations (TTL: 5min)

### Query Optimization
- Bulk loading of operations on startup
- Lazy loading of schemas
- Connection pooling for RabbitMQ HTTP API
- Prepared statements for SQLite queries

### Memory Management
- Embeddings kept in SQLite (not in memory)
- Load embeddings only during search
- Cache invalidation after TTL
- Maximum memory usage: <1GB (constitutional)
