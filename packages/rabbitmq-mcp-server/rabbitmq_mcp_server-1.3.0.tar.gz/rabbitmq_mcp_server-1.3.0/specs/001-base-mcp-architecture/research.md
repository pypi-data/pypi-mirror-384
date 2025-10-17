# Research Document: Base MCP Architecture

**Feature**: Base MCP Architecture  
**Date**: 2025-10-09  
**Phase**: 0 - Outline & Research

## Overview

Este documento consolida as decisões técnicas, pesquisa de tecnologias e padrões de implementação para a arquitetura base do servidor MCP com padrão de descoberta semântica.

## Technical Decisions

### 1. Vector Database Selection

**Decision**: ChromaDB (local file mode) ou sqlite-vec

**Rationale**:
- ChromaDB é a opção mais popular para Python com suporte nativo a embeddings
- Modo local file garante zero dependências externas
- Performance excelente para ~150-300 operações
- API simples para busca por similaridade
- sqlite-vec como alternativa mais leve e integrada ao SQLite

**Alternatives Considered**:
- **FAISS**: Mais rápido mas requer mais setup e menos features out-of-the-box
- **Milvus**: Overkill para esse volume, requer servidor separado
- **Pinecone**: Cloud-based, contra requisito de embedded/local

**Implementation Notes**:
- Embeddings pré-computados em build-time
- Threshold de similaridade: 0.7 (apenas resultados altamente relevantes)
- Índice persistido em arquivo local junto ao repo

### 2. Embedding Model Selection

**Decision**: sentence-transformers/all-MiniLM-L6-v2

**Rationale**:
- Modelo compacto (80MB) e rápido
- Excelente balance entre qualidade e performance
- Amplamente usado em produção
- Suporta embeddings de 384 dimensões
- Treinado para semantic similarity tasks

**Alternatives Considered**:
- **OpenAI embeddings**: Requer API key, custos, latência de rede
- **all-mpnet-base-v2**: Melhor qualidade mas 2x mais lento
- **multilingual models**: Desnecessário, documentação é em inglês

**Implementation Notes**:
- Download do modelo em build-time
- Cache local do modelo
- Embeddings gerados offline e commitados

### 3. Schema Validation Strategy

**Decision**: Pydantic v2 + jsonschema

**Rationale**:
- Pydantic para models Python type-safe
- jsonschema para validação dinâmica de operações
- Auto-generation de Pydantic a partir de OpenAPI usando datamodel-code-generator
- Performance excelente (<10ms overhead)

**Alternatives Considered**:
- **Marshmallow**: Mais verboso, menos integrado com type hints
- **attrs + cattrs**: Bom mas menos popular que Pydantic
- **Apenas jsonschema**: Perde type safety no código Python

**Implementation Notes**:
- Geração automática via datamodel-code-generator
- Schemas commitados no repo (não gerados em runtime)
- Validação em duas camadas: Pydantic para tipos estáticos, jsonschema para parâmetros dinâmicos

### 4. OpenTelemetry Integration

**Decision**: OpenTelemetry SDK completo (traces, metrics, logs)

**Rationale**:
- Padrão industry standard para observability
- Suporte nativo para exporters (OTLP, Jaeger, Prometheus)
- Instrumentação automática disponível
- Correlation IDs automáticos entre traces e logs

**Alternatives Considered**:
- **Prometheus client apenas**: Não cobre traces e logs correlacionados
- **Custom metrics**: Reinventar a roda, sem compatibilidade com ferramentas existentes
- **APM vendors (DataDog, NewRelic)**: Lock-in, custos

**Implementation Notes**:
- Auto-instrumentation para HTTP e database
- Custom spans para operações RabbitMQ
- Métricas: latência, error rate, cache hits, concurrent requests
- Logs estruturados correlacionados via trace IDs

### 5. Rate Limiting Implementation

**Decision**: slowapi (FastAPI-style rate limiting)

**Rationale**:
- Simples e efetivo para rate limiting por cliente
- Integração fácil com async Python
- Suporte a Redis para distributed scenarios (futuro)
- Headers padrão (Retry-After) incluídos automaticamente

**Alternatives Considered**:
- **Custom implementation**: Mais trabalho, bugs potenciais
- **nginx/API gateway**: Adiciona infraestrutura externa
- **Redis-based apenas**: Over-engineering para MVP

**Implementation Notes**:
- In-memory rate limiting para MVP
- 100 req/min padrão por client_id (configurável)
- Client ID extraído do MCP connection context
- Rejeição com HTTP 429 + Retry-After header

### 6. Structured Logging Strategy

**Decision**: structlog com JSON renderer

**Rationale**:
- Logging estruturado essencial para parsing automatizado
- structlog é o padrão de facto para Python
- JSON output facilita integração com Elasticsearch, CloudWatch, etc.
- Suporte nativo para context binding e processors

**Alternatives Considered**:
- **python-json-logger**: Mais básico, menos features
- **loguru**: Muito bonito mas menos estruturado
- **Standard logging + JSON formatter**: Mais verboso

**Implementation Notes**:
- Níveis: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Output: arquivo local `./logs/rabbitmq-mcp-{date}.log`
- Redação automática de credenciais e dados sensíveis
- Correlação com OpenTelemetry trace IDs

### 7. Configuration Management

**Decision**: Environment variables + YAML config file

**Rationale**:
- Env vars para credenciais (12-factor app)
- YAML para configurações estruturadas
- pydantic-settings para validação e parsing
- Separação clara entre secrets e config

**Alternatives Considered**:
- **Apenas env vars**: Difícil para configs complexas
- **JSON config**: Menos legível que YAML
- **TOML**: Menos adotado em Python ecosystem

**Implementation Notes**:
```yaml
# config/config.yaml
rabbitmq:
  host: ${RABBITMQ_HOST}
  port: 5672
  timeout_seconds: 30

mcp:
  rate_limit_rpm: 100

vector_db:
  similarity_threshold: 0.7
  max_results: 25

logging:
  level: INFO
  format: json
  output: ./logs/
```

### 8. Database Schema Design

**Decision**: SQLite com 3 tabelas principais

**Schema**:
```sql
-- Operation registry
CREATE TABLE operations (
    id TEXT PRIMARY KEY,           -- e.g., "queues.list"
    name TEXT NOT NULL,
    description TEXT,
    http_method TEXT,              -- GET, POST, PUT, DELETE
    http_path TEXT,                -- /api/queues/{vhost}
    tag TEXT,                      -- OpenAPI tag (namespace)
    openapi_operation_id TEXT,
    request_schema_json TEXT,      -- JSON schema
    response_schema_json TEXT,     -- JSON schema
    examples_json TEXT,            -- Usage examples
    deprecated BOOLEAN DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vector embeddings for semantic search
CREATE TABLE embeddings (
    operation_id TEXT PRIMARY KEY,
    embedding_vector BLOB,         -- numpy array serializado
    embedding_model TEXT,          -- e.g., "all-MiniLM-L6-v2"
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (operation_id) REFERENCES operations(id)
);

-- Metadata sobre a versão do OpenAPI
CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Rationale**:
- SQLite: zero config, file-based, queryable
- operations: registry completo de operações
- embeddings: vectors para semantic search
- metadata: versioning e tracking

### 9. Build-Time Generation Pipeline

**Decision**: Scripts Python + file watchers + pre-commit hooks

**Pipeline**:
```bash
# 1. Validate OpenAPI spec
python scripts/validate_openapi.py

# 2. Generate Pydantic models
python scripts/generate_schemas.py

# 3. Generate operation registry
python scripts/generate_operations.py

# 4. Generate embeddings
python scripts/generate_embeddings.py

# 5. Verify sync with OpenAPI
pytest tests/contract/test_openapi_sync.py
```

**Rationale**:
- Build-time generation evita overhead em runtime
- File watchers detectam mudanças em OpenAPI
- Pre-commit hooks garantem sync antes de commit
- CI/CD verifica mas não regenera

**Alternatives Considered**:
- **Runtime generation**: Viola constitution, impacta startup
- **Manual maintenance**: Error-prone, não escala
- **Code generation frameworks**: Over-engineering

### 10. MCP Tool Interface Design

**Decision**: 3 ferramentas públicas com interface JSON padronizada

**Interfaces**:
```python
# Tool 1: search-ids
{
  "query": str,                    # Natural language query
  "pagination": {                  # Optional
    "page": int,                   # Default: 1
    "pageSize": int                # Default: 10, max: 25
  }
}

# Tool 2: get-id
{
  "endpoint_id": str               # Operation ID from search results
}

# Tool 3: call-id
{
  "endpoint_id": str,              # Operation ID
  "params": dict,                  # Dynamic parameters
  "pagination": {                  # Optional, for list operations
    "page": int,
    "pageSize": int
  }
}
```

**Rationale**:
- Interface simples e consistente
- Pagination opcional e padronizada
- Params genérico permite validação dinâmica
- JSON-RPC 2.0 compliant

## Best Practices Research

### Python Async Best Practices

**Findings**:
- Use `asyncio` para I/O-bound operations (RabbitMQ HTTP API calls)
- Connection pooling com `httpx.AsyncClient` para reuso
- Timeouts explícitos em todas as network calls
- Graceful shutdown com cleanup de recursos

**Implementation**:
```python
# Connection pool singleton
client = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0),
    limits=httpx.Limits(max_connections=100)
)

# Timeout em todas as operações
async def call_rabbitmq_api(endpoint: str):
    try:
        response = await client.get(endpoint, timeout=30.0)
        return response.json()
    except httpx.TimeoutException:
        raise OperationTimeoutError(f"Operation exceeded 30s timeout")
```

### MCP Protocol Compliance

**Key Requirements**:
- JSON-RPC 2.0 request/response format
- Error codes padronizados:
  - `-32700`: Parse error
  - `-32600`: Invalid request
  - `-32601`: Method not found
  - `-32602`: Invalid params
  - `-32603`: Internal error
- Tool registration via `tools/list` endpoint
- Schema definitions via `tools/describe` endpoint

**Implementation**:
```python
# MCP error response
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {
      "missing": ["vhost"],
      "invalid": ["pageSize: must be <= 200"]
    }
  },
  "id": request_id
}
```

### Testing Strategy

**Approach**:
1. **Contract Tests**: Validar MCP protocol compliance
2. **Unit Tests**: Testar cada componente isoladamente
3. **Integration Tests**: Testar com RabbitMQ real em container
4. **Performance Tests**: Validar métricas de latência e memory

**Coverage Goals**:
- Tools (search-ids, get-id, call-id): 80%+
- Validators e parsers: 90%+
- Operation executors: 70%+ (mocking RabbitMQ HTTP API)
- Integration tests: 100% dos cenários de user stories

**Tools**:
- pytest para test runner
- pytest-asyncio para testes async
- pytest-mock para mocking
- testcontainers-python para RabbitMQ container
- pytest-cov para coverage reporting

## Open Questions & Resolutions

### Q1: Como tratar operações que não estão no OpenAPI (AMQP)?

**Resolution**: 
- Manter schemas manuais separados em `src/mcp_server/schemas/amqp/`
- Indexar no mesmo vector database para descoberta unificada
- Marcar com tag especial "AMQP" no operation registry
- Implementar executors customizados usando biblioteca `pika`

### Q2: Como versionar mudanças na OpenAPI spec?

**Resolution**:
- Variável de ambiente `RABBITMQ_API_VERSION` (ex: "3.13", "3.12")
- Múltiplos SQLite databases: `data/rabbitmq_operations_v3.13.db`
- Carregar versão apropriada no startup
- CI/CD valida sync para todas as versões suportadas

### Q3: Como garantir thread-safety no cache?

**Resolution**:
- Usar `asyncio.Lock` para operações de cache
- Cache separado por tipo: schemas, operations, embeddings
- TTL de 5 minutos para balance entre freshness e performance
- Invalidação manual via admin endpoint (futuro)

### Q4: Como testar com RabbitMQ real?

**Resolution**:
- testcontainers-python para spin-up automático de RabbitMQ
- Container cleanup automático após testes
- Fixtures pytest para setup/teardown
- Integration tests marcados com `@pytest.mark.integration`

```python
@pytest.fixture(scope="session")
def rabbitmq_container():
    with RabbitMQContainer("rabbitmq:3.13-management") as rmq:
        yield rmq

@pytest.mark.integration
async def test_list_queues(rabbitmq_container):
    # Test implementation
    pass
```

## Dependencies & Versions

```toml
[tool.poetry.dependencies]
python = "^3.12"
mcp = "^1.0.0"                    # MCP Python SDK
pydantic = "^2.0"                 # Schema validation
pydantic-settings = "^2.0"        # Config management
jsonschema = "^4.20"              # Dynamic validation
pyyaml = "^6.0"                   # OpenAPI parsing
httpx = "^0.26"                   # Async HTTP client
sentence-transformers = "^2.2"    # Embeddings
chromadb = "^0.4"                 # Vector database
structlog = "^24.1"               # Structured logging
opentelemetry-api = "^1.22"       # Telemetry
opentelemetry-sdk = "^1.22"
opentelemetry-instrumentation = "^0.43b0"
slowapi = "^0.1"                  # Rate limiting
pika = "^1.3"                     # AMQP client (for future)

[tool.poetry.group.dev.dependencies]
pytest = "^8.0"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
pytest-mock = "^3.12"
testcontainers = "^3.7"
datamodel-code-generator = "^0.25"  # Schema generation
black = "^24.1"
ruff = "^0.2"
mypy = "^1.8"

[tool.poetry.scripts]
generate-schemas = "scripts.generate_schemas:main"
generate-embeddings = "scripts.generate_embeddings:main"
validate-openapi = "scripts.validate_openapi:main"
```

## Implementation Priorities

### Phase 0 (Current)
- ✅ Research completed
- ✅ Technology decisions documented
- ✅ Best practices identified

### Phase 1 (Next)
- Data model definition
- API contracts for 3 MCP tools
- Quickstart guide
- Schema generation scripts

### Phase 2 (Future - /speckit.tasks)
- Implementation tasks breakdown
- Test-first development plan
- CI/CD pipeline setup

## References

- [MCP Protocol Specification](https://modelcontextprotocol.io/docs)
- [RabbitMQ Management HTTP API](https://www.rabbitmq.com/docs/management-http-api)
- [ChromaDB Documentation](https://docs.trychroma.com/)
- [sentence-transformers](https://www.sbert.net/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/languages/python/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [datamodel-code-generator](https://github.com/koxudaxi/datamodel-code-generator)
