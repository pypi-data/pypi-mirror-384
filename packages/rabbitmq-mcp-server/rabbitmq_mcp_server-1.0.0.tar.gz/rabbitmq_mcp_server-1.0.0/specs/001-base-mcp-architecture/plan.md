# Implementation Plan: Base MCP Architecture

**Branch**: `feature/001-base-architecture` | **Date**: 2025-10-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-base-mcp-architecture/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementação da arquitetura fundamental do servidor MCP com padrão de descoberta semântica de 3 ferramentas. O sistema permite que desenvolvedores descubram operações RabbitMQ usando linguagem natural, obtenham detalhes completos de esquemas, e executem operações validadas. Todas as operações e esquemas são derivados automaticamente de uma especificação OpenAPI, com busca semântica implementada via embeddings ML, validação em <10ms, e comunicação via JSON-RPC 2.0.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: MCP Python SDK, pydantic, jsonschema, pyyaml, sentence-transformers, structlog, opentelemetry-api, slowapi, pika, chromadb (ou sqlite-vec como alternativa), click (CLI), rich (console formatting), gettext/babel (i18n)  
**Storage**: ChromaDB local file mode recomendado (best Python option per constitution, embedded, portable) para busca vetorial com embeddings pré-computados. SQLite3 standalone para registro de operações, schemas e metadata. sqlite-vec como alternativa ao ChromaDB. Todas opções file-based conforme constitution.  
**Testing**: pytest (unit/integration), contract tests para MCP compliance, CLI tests com Click CliRunner  
**Target Platform**: Linux/Windows/macOS server (cross-platform Python)  
**Project Type**: Single (servidor MCP com 3 ferramentas públicas + console client built-in conforme constitution §VIII)  
**Performance Goals**: <200ms resposta básica, <10ms validação, <100ms busca semântica, 100 req/min por cliente (rate limit via connection ID → fallback IP → fallback global)  
**Constraints**: <1GB memória, timeout 30s para operações RabbitMQ, threshold 0.7 para similaridade semântica (ex: "criar fila" score 0.95 vs "criar usuário" score 0.3)  
**Scale/Scope**: Contagem de operações por versão RabbitMQ HTTP API: v3.13.x (~280 ops), v3.12.x (~260 ops), v3.11.x (~240 ops). Estimativa: 150-300 operações por versão + 5 operações AMQP manuais. Total: 3 ferramentas MCP públicas + console client (4 comandos: search, describe, execute, connect) + 20 idiomas (constitution §VIII mandatory), suporte a múltiplas versões de OpenAPI via RABBITMQ_API_VERSION  
**Naming Conventions**: MCP tool registration usa kebab-case (search-ids, get-id, call-id) conforme constitution; arquivos Python internos usam snake_case (search_ids.py) conforme PEP 8; console command: `rabbitmq-mcp`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ MCP Protocol Compliance (§I)
- **Status**: COMPLIANT
- JSON-RPC 2.0 support: ✅ Planejado
- Schema validation: ✅ Planejado (jsonschema)
- Tool interface standards: ✅ 3 ferramentas públicas (search-ids, get-id, call-id)

### ✅ Tool-First Architecture (§II)
- **Status**: COMPLIANT
- Funcionalidades expostas como MCP tools: ✅ 3 ferramentas públicas
- Self-contained tools: ✅ Cada ferramenta independente
- JSON input → processing → JSON output: ✅ Planejado
- Documentação de parâmetros: ✅ Extraída de OpenAPI

### ✅ Test-First Development (§III)
- **Status**: COMPLIANT
- TDD mandatório: ✅ Testes antes de implementação
- Cobertura mínima 80%: ✅ Para ferramentas críticas
- Integration tests com RabbitMQ real: ✅ Planejado
- Contract tests MCP: ✅ Validação de compliance

### ✅ Observability & Error Handling (§V)
- **Status**: COMPLIANT
- Structured logging: ✅ structlog com JSON
- Error codes MCP padronizados: ✅ Planejado
- Performance metrics: ✅ OpenTelemetry completo
- Request tracing: ✅ Correlation IDs via OpenTelemetry

### ✅ Vector Database (Constitution)
- **Status**: COMPLIANT
- File-based embedded: ✅ ChromaDB local file mode (best Python option per constitution)
- Pre-generated embeddings: ✅ Build-time generation
- <100ms search: ✅ Threshold 0.7 de similaridade (testado com exemplos reais)
- Version control: ✅ Embeddings commitados no repo
- Alternative: sqlite-vec disponível como fallback

### ✅ OpenAPI Source of Truth (Constitution)
- **Status**: COMPLIANT
- Single source: ✅ `.specify/memory/rabbitmq-http-api-openapi.yaml`
- Build-time generation: ✅ Schemas e embeddings gerados no build
- No runtime generation: ✅ Artefatos pré-gerados
- CI/CD validation: ✅ Verificação de sincronização

### ✅ Performance Standards (Constitution)
- **Status**: COMPLIANT
- <200ms latency básica: ✅ Confirmado em requirements
- <10ms validation overhead: ✅ Confirmado (FR-010)
- <100ms semantic search: ✅ Confirmado em goals
- <1GB memory: ✅ Confirmado (SC-004)

### ✅ Semantic Discovery Pattern (Constitution)
- **Status**: COMPLIANT
- Apenas 3 tools públicas: ✅ search-ids, get-id, call-id
- Vector database para busca: ✅ Embeddings com sentence-transformers
- Pagination support: ✅ Planejado para resultados grandes
- Operation registry: ✅ SQLite com operações pré-indexadas

### ✅ Console Client (§VIII linha 71)
- **Status**: COMPLIANT (ADR-002)
- Built-in console client: ✅ tasks.md T057-T068 implementam CLI com click framework
- Console commands: ✅ 4 comandos (search, describe, execute, connect)
- Rich formatting: ✅ Tables, JSON highlighting, progress indicators
- Integration com MCP tools: ✅ Wraps search-ids, get-id, call-id
- **Architectural Decision**: ADR-002 supersedes ADR-001 - console client incluído no MVP para constitution compliance

### ✅ Multilingual Support (§VIII linhas 604-624)
- **Status**: COMPLIANT (ADR-002)
- 20 idiomas obrigatórios: ✅ tasks.md T062-T068 implementam i18n via gettext/babel
- Idiomas: en, zh_CN, hi, es, fr, ar, bn, ru, pt, id, ur, de, ja, sw, mr, te, tr, ta, vi, it
- Locale detection: ✅ Auto-detection via locale.getdefaultlocale()
- Fallback hierarchy: ✅ locale específico → idioma base → English
- Machine translation: ✅ DeepL/Google Translate para traduções iniciais (MVP-appropriate)

### ⚠️ Simplicity (§VII)
- **Status**: JUSTIFIED
- Maximum 15 tools: ✅ Apenas 3 ferramentas públicas registradas
- YAGNI applied: ✅ Implementação apenas do essencial
- **Justification**: Architecture complexa necessária para suportar 150-300 operações RabbitMQ de forma eficiente via semantic discovery

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
src/
├── mcp_server/
│   ├── __init__.py
│   ├── server.py              # MCP server initialization
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── search_ids.py      # search-ids tool (PUBLIC MCP TOOL)
│   │   ├── get_id.py          # get-id tool (PUBLIC MCP TOOL)
│   │   └── call_id.py         # call-id tool (PUBLIC MCP TOOL)
│   ├── openapi/
│   │   ├── __init__.py
│   │   ├── parser.py          # OpenAPI YAML parser
│   │   ├── schema_generator.py # Auto-generate Pydantic models
│   │   ├── operation_registry.py # Map operation IDs to paths
│   │   └── validator.py       # Runtime validation
│   ├── operations/
│   │   ├── __init__.py
│   │   ├── executor.py        # Base operation executor
│   │   ├── cluster.py         # Cluster operations
│   │   ├── queues.py          # Queue operations
│   │   ├── exchanges.py       # Exchange operations
│   │   ├── bindings.py        # Binding operations
│   │   └── ...                # Other operation modules by tag
│   ├── vector_db/
│   │   ├── __init__.py
│   │   ├── indexer.py         # Index operations for search
│   │   ├── embeddings.py      # Generate embeddings
│   │   └── search.py          # Vector similarity search
│   ├── schemas/               # Auto-generated from OpenAPI (DO NOT EDIT)
│   │   ├── __init__.py
│   │   ├── queue.py           # Generated from OpenAPI components.schemas.Queue
│   │   ├── exchange.py        # Generated from OpenAPI components.schemas.Exchange
│   │   ├── amqp_operations.py # MANUAL: AMQP protocol schemas (não na OpenAPI)
│   │   └── ...                # Other auto-generated schemas
│   └── utils/
│       ├── __init__.py
│       ├── logging.py         # Structured logging setup
│       ├── rate_limit.py      # Rate limiting
│       └── telemetry.py       # OpenTelemetry setup

scripts/
├── generate_schemas.py        # Generate Pydantic models
├── generate_embeddings.py     # Generate vector embeddings
└── validate_openapi.py        # Validate OpenAPI spec

tests/
├── contract/
│   ├── test_mcp_compliance.py # MCP protocol validation
│   └── test_openapi_sync.py   # OpenAPI sync verification
├── integration/
│   ├── test_rabbitmq_ops.py   # Real RabbitMQ tests
│   └── test_tools_e2e.py      # End-to-end tool tests
└── unit/
    ├── test_search_ids.py     # search-ids tool tests
    ├── test_get_id.py         # get-id tool tests
    ├── test_call_id.py        # call-id tool tests
    ├── test_validator.py      # Validation tests
    └── test_embeddings.py     # Embedding tests

data/
├── rabbitmq_operations.db     # SQLite: operation registry, schemas, metadata
└── chromadb/                  # ChromaDB local file mode: pre-computed embeddings & vector search

.specify/
└── memory/
    └── rabbitmq-http-api-openapi.yaml # OpenAPI source

config/
└── config.yaml                # Server configuration
```

**Structure Decision**: Single project architecture escolhida pois trata-se de um servidor MCP standalone com 3 ferramentas públicas. A estrutura organiza o código por responsabilidade: tools/ para as 3 ferramentas MCP públicas, openapi/ para geração e parsing de schemas, operations/ para executores organizados por tags do OpenAPI (também chamados "namespaces" ou "Operation Categories" - ver spec.md linha 136), vector_db/ para busca semântica com sqlite-vec, e schemas/ para modelos auto-gerados. Scripts de geração são separados em scripts/ e executados em build-time. Testes seguem a estrutura mandatória da constitution (contract, integration, unit).

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**Status**: ✅ NO VIOLATIONS - Todas as verificações constitucionais passaram sem necessidade de justificativa.

A arquitetura complexa do padrão de descoberta semântica foi justificada na seção "Simplicity (§VII)" da Constitution Check como necessária para gerenciar eficientemente 150-300 operações RabbitMQ através de apenas 3 ferramentas MCP públicas.
