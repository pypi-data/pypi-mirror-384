# Implementation Plan: Essential Topology Operations

**Branch**: `feature/003-essential-topology-operations` | **Date**: 2025-10-09 | **Spec**: [specs/003-essential-topology-operations/spec.md](../spec.md)
**Input**: Feature specification from `/specs/003-essential-topology-operations/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementar operações essenciais de topologia RabbitMQ através do padrão de descoberta semântica de 3 ferramentas MCP, permitindo que operadores visualizem, criem e removam filas, exchanges e bindings de forma segura via built-in CLI. A abordagem técnica utiliza Python 3.12+ com requests para comunicação HTTP com a Management API, click para interface CLI, structlog para logging estruturado, e integração completa com o padrão OpenAPI-driven architecture definido na constituição. O sistema é um MCP Server with built-in CLI seguindo constitution.md linha 71.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: 
- requests (HTTP client para RabbitMQ Management API)
- click (framework CLI)
- structlog (structured logging)
- tabulate (formatação de tabelas)
- pydantic (validação de schemas)
- pytest (testing framework)
- chromadb (vector database local file-based)
- sentence-transformers (embeddings generation - all-MiniLM-L6-v2)

**Storage**: N/A (stateless MCP server with built-in CLI, sem armazenamento local)  
**Testing**: pytest com coverage mínimo de 80% (conforme constituição)  
**Target Platform**: Linux/Windows/macOS (cross-platform)  
**Project Type**: Single project (MCP Server with built-in CLI)  
**Performance Goals**: 
- Operações de listagem (classified as **complex operations**) < 2 segundos por página com paginação client-side (constitution.md linha 571 permite latência maior que 200ms para operações complexas)
- Operações de criação/deleção (classified as **complex operations**) < 1 segundo (incluem validação de existência, checks de segurança, e audit logging - não são "simple HTTP calls")
- Semantic search (basic operation) < 100ms por query (constitution requirement linha 571)
- **Classificação de Operações** (definição consolidada):

| Operation Type | Max Latency | Characteristics | Examples |
|---------------|-------------|-----------------|----------|
| **Basic operations** | < 200ms | Semantic search MCP tools, simples validações de schema, operações read-only sem side effects, sem validações complexas | search-ids, get-id, schema validation |
| **Complex operations (CRUD)** | < 1s | Operações com side effects (create, delete, update), múltiplas validações (vhost, resource existence, safety checks), audit logging obrigatório | queues.create, exchanges.delete, bindings.create |
| **Complex operations (List)** | < 2s/page | Operações de listagem com client-side pagination, processamento em memória, agregações client-side (ex: bindings_count) | queues.list, exchanges.list, bindings.list |

**Constraints**: 
- Latência de rede (RTT) até RabbitMQ < 100ms (aproximadamente 50ms one-way, típico de datacenter/cloud co-location)
- Memory usage < 1GB por instância (constitution requirement)
- Suporte até 1000 filas/exchanges sem degradação através de paginação client-side
- HTTP request timeouts: 5s default para CRUD operations (complex operations - incluem validações múltiplas), 30s configurável para list operations com grandes volumes
- **Timeout Clarification**: Constitution.md "<200ms for basic operations" aplica-se a operações simples de MCP semantic search, não a operações CRUD com validações múltiplas e audit logging

**Scale/Scope**: 
- Operações de topologia essenciais (filas, exchanges, bindings)
- Integração via RabbitMQ Management API HTTP
- CLI interface humanizada e JSON output
- Logging estruturado para auditoria

## Architecture & Quality Standards

*Quality gates to validate before and after implementation.*

### ✅ MCP Protocol Compliance
- **Status**: PASS
- **Justification**: Implementação seguirá o padrão de 3 ferramentas MCP (search-ids, get-id, call-id). Todas as operações de topologia serão expostas através deste padrão.
- **Tool Limit Compliance**: Constitution permite máximo 15 tools por servidor (constitution.md linha 107). Este projeto registra apenas 3 public MCP tools (search-ids, get-id, call-id), bem abaixo do limite. Todas as operações RabbitMQ são acessadas indiretamente através do padrão de descoberta semântica.

### ✅ Tool-First Architecture
- **Status**: PASS
- **Justification**: Arquitetura utilizará o padrão de descoberta semântica de 3 ferramentas. Operações de topologia (filas, exchanges, bindings) serão acessíveis via call-id com validação dinâmica baseada em OpenAPI.

### ✅ Test-First Development
- **Status**: PASS - Requer validação pós-implementação
- **Justification**: Mínimo 80% de cobertura de testes. Testes escritos antes da implementação, com foco em:
  - Unit tests para validação de schemas
  - Integration tests com RabbitMQ real
  - Contract tests validando OpenAPI specification

### ✅ OpenAPI Specification as Source of Truth
- **Status**: PASS
- **Justification**: Todas as operações de topologia derivadas de `contracts/*.yaml` (extraídos da documentação RabbitMQ Management API). Schemas Pydantic auto-gerados do OpenAPI. Operações mapeadas automaticamente (queues.list, queues.create, exchanges.create, bindings.create, etc.).

### ✅ Semantic Discovery Pattern
- **Status**: PASS
- **Justification**: Implementação das 3 ferramentas públicas MCP:
  - `search-ids`: busca semântica de operações de topologia
  - `get-id`: obtenção de schema detalhado
  - `call-id`: execução com validação dinâmica

### ✅ Vector Database Requirements
- **Status**: PASS
- **Justification**: ChromaDB em modo local file-based para embeddings. Índices pré-computados das operações RabbitMQ do OpenAPI. Busca semântica < 100ms. Arquivos de índice commitados no repositório (vector DB < 50MB).

### ✅ Structured Logging
- **Status**: PASS
- **Justification**: structlog para logging estruturado. Todas operações de criação/deleção/listagem logadas para auditoria. Sanitização automática de credenciais.

### ✅ Performance Standards
- **Status**: PASS
- **Justification**: 
  - Listagens < 2s por página (spec requirement SC-001)
  - Operações CRUD < 1s (spec requirements SC-002, SC-003)
  - Semantic search < 100ms (performance goal)
  - Memory < 1GB por instância (constraint)

### ✅ Documentation Requirements
- **Status**: PASS - Requer criação pós-planejamento
- **Justification**: Documentação obrigatória em inglês: README.md, docs/API.md, docs/ARCHITECTURE.md, docs/EXAMPLES.md com exemplos uvx.

### ✅ License (LGPL v3.0)
- **Status**: PASS
- **Justification**: Todo código licenciado sob LGPL v3.0. Headers de licença em todos os arquivos fonte validados em T001 e T052.

### 🔍 Potential Complexity Points
Nenhuma complexidade excessiva identificada. Implementação segue padrões estabelecidos de MCP servers.

## Project Structure

### Documentation (this feature)

```
specs/003-essential-topology-operations/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── queue-operations.yaml
│   ├── exchange-operations.yaml
│   └── binding-operations.yaml
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── tools/                      # MCP tools implementation
│   ├── search_ids.py          # Semantic search tool (PUBLIC MCP TOOL)
│   ├── get_id.py              # Get operation schema tool (PUBLIC MCP TOOL)
│   ├── call_id.py             # Execute operation tool (PUBLIC MCP TOOL)
│   ├── openapi/               # OpenAPI processing
│   │   ├── parser.py          # Parse OpenAPI YAML
│   │   ├── schema_generator.py # Auto-generate Pydantic models
│   │   ├── operation_registry.py # Map operation IDs to paths
│   │   └── validator.py       # Runtime validation
│   ├── operations/            # Internal operation executors (by OpenAPI tags)
│   │   ├── executor.py        # Base HTTP client executor
│   │   ├── queues.py          # Queue operations (queues.list, queues.create, etc.)
│   │   ├── exchanges.py       # Exchange operations
│   │   └── bindings.py        # Binding operations
│   ├── vector_db/             # Vector database for semantic search
│   │   ├── indexer.py         # Index operations from OpenAPI
│   │   ├── embeddings.py      # Generate embeddings
│   │   └── search.py          # Similarity search
│   └── schemas/               # Auto-generated Pydantic models (DO NOT EDIT)
│       ├── __init__.py
│       ├── queue.py           # Generated from OpenAPI
│       ├── exchange.py        # Generated from OpenAPI
│       └── binding.py         # Generated from OpenAPI
│
├── cli/                       # CLI commands (built-in)
│   ├── main.py               # Click CLI entry point
│   ├── commands/             # CLI command groups
│   │   ├── queue.py          # Queue commands (uses MCP tools)
│   │   ├── exchange.py       # Exchange commands
│   │   └── binding.py        # Binding commands
│   └── formatters/           # Output formatters
│       ├── table.py          # Tabulate formatting
│       └── json.py           # JSON output
│
├── config/                    # Configuration management
│   ├── settings.py           # Application settings
│   └── logging.py            # Structured logging setup
│
└── utils/                     # Shared utilities
    ├── connection.py         # RabbitMQ connection helpers
    └── validation.py         # Input validation helpers

tests/
├── unit/                      # Unit tests
│   ├── test_search_ids.py
│   ├── test_get_id.py
│   ├── test_call_id.py
│   ├── test_validator.py
│   └── test_operations.py
├── integration/               # Integration tests (real RabbitMQ)
│   ├── test_queue_operations.py
│   ├── test_exchange_operations.py
│   └── test_binding_operations.py
└── contract/                  # Contract tests (OpenAPI validation)
    ├── test_openapi_compliance.py
    └── test_schemas.py

scripts/
├── generate_schemas.py        # Generate Pydantic models from OpenAPI
├── generate_embeddings.py     # Generate vector DB indices
└── validate_openapi.py        # Validate OpenAPI specification

data/
└── vectors/                   # Pre-built vector database (committed to repo)
    └── rabbitmq.db

docs/
├── API.md                     # API documentation
├── ARCHITECTURE.md            # Architecture overview
├── EXAMPLES.md                # Usage examples with uvx
└── CONTRIBUTING.md            # Contribution guidelines

config/
└── config.yaml               # Default configuration
```

**Structure Decision**: Single project structure (MCP Server with built-in CLI). Esta é a estrutura apropriada para um MCP Server Python com CLI integrado seguindo constitution.md. O código fonte está organizado em:
- `tools/`: Implementação das 3 ferramentas MCP públicas e infraestrutura OpenAPI-driven
- `cli/`: CLI commands built-in usando click framework
- `tests/`: Testes separados por tipo (unit, integration, contract)
- `scripts/`: Scripts de geração de código (schemas, embeddings)
- `data/`: Vector database pré-computado
- `docs/`: Documentação mandatória conforme quality standards

## Complexity Tracking

*Nenhuma complexidade excessiva identificada. Implementação alinhada com quality standards.*
