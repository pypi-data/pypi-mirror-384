# Implementation Tasks: Essential Topology Operations

**Feature**: 003-essential-topology-operations  
**Generated**: 2025-10-09  
**Status**: Ready for implementation

## Overview

Este documento contém todas as tarefas necessárias para implementar as operações essenciais de topologia RabbitMQ, organizadas por user story para permitir implementação e teste independentes.

### User Stories Priority Order
1. **US1 (P1)**: View and Monitor - Visualizar filas, exchanges e bindings
2. **US2 (P2)**: Create Infrastructure - Criar filas, exchanges e bindings
3. **US3 (P3)**: Remove Infrastructure - Deletar com segurança

---

## Phase 1: Project Setup & Infrastructure

**Goal**: Inicializar projeto Python com dependências e estrutura básica

### T001: Initialize Python Project Structure
**Story**: Setup  
**Type**: Setup  
**Files**: `pyproject.toml`, `README.md`, `LICENSE`

Criar estrutura inicial do projeto Python:
- Criar `pyproject.toml` com Python 3.12+ e dependências (requests, click, structlog, tabulate, pydantic, pytest)
- Criar arquivo `LICENSE` com texto completo da LGPL v3.0
- Validar que LICENSE contém texto oficial da licença (não apenas referência)
- Criar `README.md` básico com overview, badge de licença, e instruções de instalação via uvx
- Criar `.gitignore` para Python (venv, __pycache__, .pytest_cache, etc.)

**Success Criteria**: Projeto Python válido com dependências declaradas, LICENSE completo validado
 [X]

---

### T002: [P] Create Directory Structure
**Story**: Setup  
**Type**: Setup  
**Files**: Estrutura de diretórios conforme `plan.md`

Criar toda a estrutura de diretórios do projeto:
```
src/
├── tools/
│   ├── operations/
│   ├── openapi/
│   ├── vector_db/
│   └── schemas/
├── cli/
│   ├── commands/
│   └── formatters/
├── config/
└── utils/

tests/
├── unit/
├── integration/
└── contract/

scripts/
data/vectors/
docs/
config/
```

**Success Criteria**: Todas as pastas criadas, arquivos `__init__.py` onde necessário
 [X]

---

## Phase 2: Foundational Components (Blocking Prerequisites)

**Goal**: Componentes base que todas as user stories dependem

### T003: Implement OpenAPI Parser
**Story**: Foundational  
**Type**: Core Infrastructure  
**Files**: `src/tools/openapi/parser.py`

Implementar parser para ler e processar OpenAPI YAML:
- Função `parse_openapi_spec(path: str) -> dict` que carrega YAML
- Extração de operações, schemas, paths, parameters
- Validação básica da estrutura OpenAPI 3.1.0
- Tratamento de erros de parsing

**Success Criteria**: Parser lê os 3 arquivos contracts/*.yaml sem erros
 [X]

**Dependencies**: T002

---

### T004: [P] Implement Operation Registry
**Story**: Foundational  
**Type**: Core Infrastructure  
**Files**: `src/tools/openapi/operation_registry.py`

Criar registry que mapeia operation IDs para seus metadados:
- Classe `OperationRegistry` que indexa todas as operações do OpenAPI
- Método `get_operation(operation_id: str) -> OperationMetadata`
- Método `list_operations(tag: Optional[str]) -> List[OperationMetadata]`
- Cache em memória das operações após primeira leitura

**Success Criteria**: Registry retorna metadados completos para "queues.list", "exchanges.create", etc.
 [X]

**Dependencies**: T003

---

### T005: [P] Generate Pydantic Schemas from OpenAPI
**Story**: Foundational  
**Type**: Code Generation  
**Files**: `scripts/generate_schemas.py`, `src/tools/schemas/*.py`

Criar script de geração de schemas Pydantic:
- Script que lê contracts/*.yaml
- Gera modelos Pydantic para Queue, Exchange, Binding, requests/responses
- Adiciona headers de licença LGPL em arquivos gerados
- Commitar schemas gerados ao repositório

**Success Criteria**: Schemas Pydantic válidos em `src/tools/schemas/` para todas as entidades
 [X]

**Dependencies**: T003

---

### T006: Implement HTTP Client Executor
**Story**: Foundational  
**Type**: Core Infrastructure  
**Files**: `src/tools/operations/executor.py`, `src/utils/connection.py`

Implementar cliente HTTP base para RabbitMQ Management API:
- Classe `RabbitMQExecutor` usando requests.Session
- Connection pooling e keep-alive (persistent connections)
- Autenticação básica (user/password via HTTP Basic Auth)
- **Timeout Strategy** (standardized, C2 resolved):
  - CRUD operations (create, delete, update): usar `crud_timeout` de Settings (default 5s) - **complex operations** devido a validações múltiplas
  - List operations (queues.list, exchanges.list, bindings.list): usar `list_timeout` de Settings (default 30s) - **complex operations** devido a client-side pagination
  - Auto-retry logic: 3 tentativas com exponential backoff (1s, 2s, 4s) para network errors
  - Note: Constitution.md "<200ms for basic operations" aplica-se a semantic search MCP tools, não a operações CRUD com validações
- **Error Handling** com mensagens formatadas (FR-025):
  - HTTP 401/403: "UNAUTHORIZED" com operação e permissão requerida
  - HTTP 404: "NOT_FOUND" com recurso específico
  - HTTP 500: "SERVER_ERROR" com detalhes do RabbitMQ
  - Network errors: "CONNECTION_ERROR" com suggested action de verificar conectividade
  - **Validação I1**: Para DELETE queue com flag --force, adicionar query parameter `if-empty=false` ao URL (ex: DELETE `/api/queues/{vhost}/{queue}?if-empty=false`)
- Parse de respostas JSON com validação
- Request/response logging para auditoria

**Success Criteria**: Executor faz requisições HTTP bem-sucedidas ao RabbitMQ Management API, timeouts padronizados funcionam, error messages seguem padrão FR-025, conversão de --force funciona
 [X]

**Dependencies**: T002

---

### T007: Setup Structured Logging with Enterprise Features
**Story**: Foundational  
**Type**: Core Infrastructure  
**Files**: `src/config/logging.py`, `config/logging.yaml`

Configurar structured logging com structlog seguindo constitution.md requisitos:
- **Processors structlog**: JSON output, timestamps ISO8601, correlation IDs (UUID), sanitização automática
- **Sensitive Data Sanitization**: Redact passwords, tokens, credenciais RabbitMQ (regex-based patterns)
- **Log Levels**: error, warn, info, debug (configurável via env var LOG_LEVEL, default: INFO)
- **Output Destinations** (configuráveis via config/logging.yaml):
  - File-based (default): `./logs/rabbitmq-mcp-{date}.log` 
  - Elasticsearch: HTTP endpoint com autenticação
  - Splunk: HEC (HTTP Event Collector) endpoint
  - Fluentd: Forward protocol endpoint
  - CloudWatch: AWS SDK integration
  - Prometheus/Grafana: Loki push API
  - Stdout: Para containers/cloud environments
- **File Rotation** (usando `logging.handlers.RotatingFileHandler`):
  - Daily rotation (00:00 UTC, most common enterprise practice)
  - Size-based rotation: max 100MB per file
  - Backup count: 30 files para info/debug, 90 para warn/error, 365 para audit logs
  - Automatic gzip compression de arquivos rotacionados
- **Retention Policies**:
  - info/debug logs: 30 dias
  - warn/error logs: 90 dias  
  - audit logs (create/delete operations): 1 ano (365 dias)
  - Automatic cleanup via scheduled task
- **Message Correlation**: UUID-based correlation IDs para tracing de operações multi-step
- **Logger Factory**: Função `get_logger(name: str)` para uso consistente em todo projeto

**Success Criteria**: 
 [X]
- Logs estruturados em JSON com timestamp, level, correlation_id, operation, sanitized context
- File rotation funciona automaticamente
- Pelo menos 2 output destinations configuráveis (file + Elasticsearch/Splunk)
- Credenciais sanitizadas em 100% dos logs

**Dependencies**: T002

---

### T008: [P] Implement Configuration Management
**Story**: Foundational  
**Type**: Core Infrastructure  
**Files**: `src/config/settings.py`, `config/config.yaml`

Implementar gerenciamento de configuração:
- Classe `Settings` com Pydantic para validação
- Prioridade: CLI args > Environment vars > Config file (config.yaml) > Defaults
- **Connection Params**: host, port, user, password, vhost, use_tls
- **Timeout Configuration** (standardized per analysis):
  - `crud_timeout`: 5s default (create, delete, update operations - constitution "basic operations")
  - `list_timeout`: 30s default configurável (list operations - constitution "complex operations")
  - `search_timeout`: 0.1s (100ms) semantic search (constitution requirement)
- Leitura de config.yaml opcional (formato enterprise-friendly)
- Suporte a arquivo .env para carregar variáveis de ambiente (usando python-dotenv)
- Validation: timeouts devem ser >= 1s, <= 60s; host/port obrigatórios

**Success Criteria**: Configuração carrega corretamente de múltiplas fontes com precedência correta, timeouts padronizados validados, .env suportado
 [X]

**Dependencies**: T002

---

### T009: Generate Vector Database Embeddings
**Story**: Foundational  
**Type**: Vector DB  
**Files**: `scripts/generate_embeddings.py`, `data/vectors/rabbitmq.db`

Criar script para gerar embeddings das operações:
- Script que lê todos os contracts/*.yaml
- Extrai operation IDs, descriptions, summaries
- Gera embeddings com sentence-transformers (all-MiniLM-L6-v2)
- Indexa no ChromaDB em modo local file-based (CRITICAL: não usar modo cliente-servidor)
- Configura ChromaDB com PersistentClient apontando para `data/vectors/`
- Commita database ao repositório (target: < 50MB conforme quality standard)
- **Size Validation & Remediation**: Script DEVE validar tamanho do vector DB antes de commit. Se > 50MB:
  1. **First try**: Reduzir dimensões dos embeddings (e.g., all-MiniLM-L6-v2 384d → MiniLM-L3-v2 384d com quantização)
  2. **Second try**: Usar modelo menor (e.g., paraphrase-MiniLM-L3-v2 com 128 dimensões)
  3. **Third try**: Aplicar compressão SQLite VACUUM e PRAGMA page_size=4096
  4. **If still > 50MB**: Documentar exceção em plan.md e obter aprovação antes de commit (limite constitucional pode ser ajustado para caso específico)
- Gera índices pré-computados para busca <100ms

**Success Criteria**: ChromaDB criado em `data/vectors/` com todas as operações indexadas, arquivos de índice commitados (< 50MB ou exceção documentada), modo local file-based confirmado
 [X]

**Dependencies**: T003, T004

---

### T009b: Setup OpenAPI Change Detection
**Story**: Foundational  
**Type**: Automation  
**Files**: `.git/hooks/pre-commit`, `scripts/validate_openapi.py`

Implementar detecção automática de mudanças no OpenAPI:
- Criar pre-commit hook que detecta mudanças em `contracts/*.yaml`
- Se OpenAPI modificado, executar automaticamente:
  - `scripts/validate_openapi.py` (validação de sintaxe)
  - `scripts/generate_schemas.py` (regenerar Pydantic models)
  - `scripts/generate_embeddings.py` (regenerar vector database)
- Hook bloqueia commit se validação falhar
- Adicionar instruções no README para instalar hooks
- Documentar processo em docs/CONTRIBUTING.md

**Success Criteria**: Mudanças em OpenAPI disparam regeneração automática, commits bloqueados se validação falhar
 [X]

**Dependencies**: T005, T009

---

### T010: [P] Implement Vector Search
**Story**: Foundational  
**Type**: Vector DB  
**Files**: `src/tools/vector_db/search.py`, `src/tools/vector_db/embeddings.py`

Implementar busca semântica no vector database:
- Função `semantic_search(query: str, limit: int) -> List[OperationMatch]`
- Carregamento do ChromaDB pré-computado
- Geração de embeddings para query
- Similarity search < 100ms (target constitucional)

**Success Criteria**: Busca por "list all queues" retorna "queues.list" como primeiro resultado
 [X]

**Dependencies**: T009

---

## Phase 3: User Story 1 (P1) - View and Monitor

**Goal**: Implementar visualização de filas, exchanges e bindings com estatísticas

**Independent Test**: Conectar a RabbitMQ com componentes pré-configurados e verificar listagens corretas

### T011: Implement search-ids Tool (MCP)
**Story**: US1  
**Type**: MCP Tool  
**Files**: `src/tools/search_ids.py`

Implementar ferramenta MCP de busca semântica:
- Função `search_ids(query: str, page: int, pageSize: int) -> SearchResult`
- Integração com vector search (T010)
- Paginação com defaults (page=1, pageSize=50, max=200)
- Response format conforme constituição

**Success Criteria**: Tool retorna operation IDs relevantes com paginação correta
 [X]

**Dependencies**: T010

---

### T012: [P] Implement get-id Tool (MCP)
**Story**: US1  
**Type**: MCP Tool  
**Files**: `src/tools/get_id.py`

Implementar ferramenta MCP de obtenção de schema:
- Função `get_id(endpoint_id: str) -> OperationSchema`
- Lookup no operation registry (T004)
- Retorna schema completo (params, responses, examples)
- Error handling para operation IDs inválidos

**Success Criteria**: Tool retorna schema completo para "queues.list"
 [X]

**Dependencies**: T004

---

### T013: Implement Queue List Operation
**Story**: US1  
**Type**: Operation  
**Files**: `src/tools/operations/queues.py`

Implementar operação de listagem de filas com paginação obrigatória (FR-033):
- Função `list_queues(vhost: Optional[str], page: int = 1, pageSize: int = 50) -> PaginatedQueueResponse`
- **Validação de vhost primeiro** se especificado (T022c)
- GET /api/queues ou /api/queues/{vhost} - **sem query params de paginação** (RabbitMQ API não suporta nativo)
- Buscar **todos os resultados** da API e aplicar slice client-side baseado em page/pageSize
- Parse de response JSON para Pydantic models (Queue, PaginationMetadata)
- Validação de parâmetros (page >= 1, 1 <= pageSize <= 200)
- Cálculo de metadados de paginação (totalItems, totalPages, hasNextPage, hasPreviousPage)
- Logging de operação com nível DEBUG
- Performance < 2s por página (SC-001, FR-036, complex operation)

**Success Criteria**: Retorna resposta paginada com lista de filas e metadados completos de paginação (SC-010), client-side pagination funciona
 [X]

**Dependencies**: T005, T006, T007, T022c

---

### T014: [P] Implement Exchange List Operation
**Story**: US1  
**Type**: Operation  
**Files**: `src/tools/operations/exchanges.py`

Implementar operação de listagem de exchanges com paginação obrigatória (FR-033):
- Função `list_exchanges(vhost: Optional[str], page: int = 1, pageSize: int = 50) -> PaginatedExchangeResponse`
- **Validação de vhost primeiro** se especificado (T022c)
- GET /api/exchanges ou /api/exchanges/{vhost} - **client-side pagination**
- Parse de response com tipos (direct, topic, fanout, headers)
- Estatísticas de throughput quando disponíveis (message_stats.publish_in, publish_out)
- Cálculo de metadados de paginação (totalItems, totalPages, hasNextPage, hasPreviousPage)
- Performance < 2s por página (SC-001, FR-036, complex operation)

**Success Criteria**: Retorna resposta paginada com lista de exchanges, tipos e metadados completos de paginação (SC-010)
 [X]

**Dependencies**: T005, T006, T007, T022c

---

### T015: [P] Implement Binding List Operation
**Story**: US1  
**Type**: Operation  
**Files**: `src/tools/operations/bindings.py`

Implementar operação de listagem de bindings com paginação obrigatória (FR-033):
- Função `list_bindings(vhost: Optional[str], page: int = 1, pageSize: int = 50) -> PaginatedBindingResponse`
- **Validação de vhost primeiro** se especificado (T022c)
- GET /api/bindings ou /api/bindings/{vhost} - **client-side pagination**
- Parse mostrando source, destination, routing_key
- Cálculo de metadados de paginação (totalItems, totalPages, hasNextPage, hasPreviousPage)
- Performance < 2s por página (SC-001, FR-036, complex operation)

**Success Criteria**: Retorna resposta paginada com lista de bindings e metadados completos de paginação (SC-010)
 [X]

**Dependencies**: T005, T006, T007, T022c

---

### T016: Implement call-id Tool for List Operations
**Story**: US1  
**Type**: MCP Tool  
**Files**: `src/tools/call_id.py`

Implementar ferramenta MCP de execução (apenas operações list):
- Função `call_id(endpoint_id: str, params: dict, pagination: dict = None) -> PaginatedResponse`
- Roteamento para operações: queues.list, exchanges.list, bindings.list
- Validação dinâmica de parâmetros com Pydantic (incluindo page, pageSize)
- Paginação obrigatória em todas operações list (FR-033)
- Validação de limites: 1 <= pageSize <= 200 (FR-034)
- Error handling e propagação de mensagens claras
- Retorno consistente com metadados de paginação (FR-035)

**Success Criteria**: Tool executa "queues.list" e retorna resposta paginada completa com metadados (SC-010)
 [X]

**Dependencies**: T013, T014, T015

---

### T017: Implement CLI Queue List Command
**Story**: US1  
**Type**: CLI  
**Files**: `src/cli/commands/queue.py`, `src/cli/main.py`

Implementar comando CLI para listar filas com paginação:
- Comando `rabbitmq-mcp-server queue list`
- Opções: --host, --port, --user, --password, --vhost, --format
- Opções de paginação: --page (default 1), --page-size (default 50, max 200)
- **Opção --verbose**: Exibe estatísticas opcionais quando disponíveis na resposta API (conforme FR-002 critério de exibição). Default: exibe apenas estatísticas obrigatórias
- Chama MCP tool call-id com "queues.list" incluindo params de paginação
- Output formatado com tabulate ou JSON
- Mostrar metadados de paginação no footer (Page 1 of 3, Total: 150 items)

**Success Criteria**: Comando lista filas paginadas em formato tabela legível com metadados de paginação visíveis, flag --verbose funciona
 [X]

**Dependencies**: T016

---

### T018: [P] Implement CLI Exchange List Command
**Story**: US1  
**Type**: CLI  
**Files**: `src/cli/commands/exchange.py`

Implementar comando CLI para listar exchanges com paginação:
- Comando `rabbitmq-mcp-server exchange list`
- Mesmas opções de conexão que T017
- Opções de paginação: --page (default 1), --page-size (default 50, max 200)
- **Opção --verbose**: Exibe estatísticas opcionais quando disponíveis na resposta API (conforme FR-010 critério de exibição). Default: exibe apenas estatísticas obrigatórias
- Output formatado mostrando nome, tipo, bindings count (agregado client-side conforme FR-010)
- Mostrar metadados de paginação no footer

**Success Criteria**: Comando lista exchanges paginados com tipos (direct, topic, etc.) e metadados de paginação, flag --verbose funciona
 [X]

**Dependencies**: T016

---

### T019: [P] Implement CLI Binding List Command
**Story**: US1  
**Type**: CLI  
**Files**: `src/cli/commands/binding.py`

Implementar comando CLI para listar bindings com paginação:
- Comando `rabbitmq-mcp-server binding list`
- Opções de paginação: --page (default 1), --page-size (default 50, max 200)
- Output formatado mostrando exchange → queue + routing key
- Mostrar metadados de paginação no footer

**Success Criteria**: Comando lista bindings paginados em formato claro com metadados de paginação
 [X]

**Dependencies**: T016

---

### T020: [P] Implement Table Formatter
**Story**: US1  
**Type**: Formatter  
**Files**: `src/cli/formatters/table.py`

Implementar formatador de saída em tabela:
- Função `format_table(data: List[dict], columns: List[str]) -> str`
- Usa biblioteca tabulate
- Alinhamento automático de colunas
- Truncamento de campos muito longos

**Success Criteria**: Listas formatadas em tabelas legíveis
 [X]

**Dependencies**: T017, T018, T019

---

### T021: [P] Implement JSON Formatter
**Story**: US1  
**Type**: Formatter  
**Files**: `src/cli/formatters/json.py`

Implementar formatador de saída JSON:
- Função `format_json(data: Any) -> str`
- JSON pretty-printed
- Serialização de Pydantic models

**Success Criteria**: Flag --format json produz JSON válido
 [X]

**Dependencies**: T017, T018, T019

---

### ✅ Checkpoint: User Story 1 Complete

**Validation**:
- [X] Comando `queue list` exibe filas paginadas com estatísticas e metadados de paginação
- [X] Comando `exchange list` exibe exchanges paginados com tipos e metadados
- [X] Comando `binding list` exibe bindings paginados com routing keys e metadados
- [X] Operações completam em < 2 segundos por página (SC-001, FR-036)
- [X] Suporta até 1000 entidades através de paginação sem degradação (SC-006)
- [X] MCP tools (search-ids, get-id, call-id) funcionam para operações list com paginação
- [X] Paginação funciona corretamente: page, pageSize, totalItems, totalPages, hasNextPage, hasPreviousPage (SC-010)
- [X] Limites de paginação respeitados: 1 <= pageSize <= 200 (FR-034)

**Deliverable**: Sistema completo de visualização e monitoramento com paginação obrigatória

---

## Phase 4: User Story 2 (P2) - Create Infrastructure

**Goal**: Implementar criação de filas, exchanges e bindings com validações

**Independent Test**: Criar componentes em RabbitMQ limpo e verificar configurações corretas

### T022: Implement Standardized Error Formatting
**Story**: US2  
**Type**: Core Infrastructure  
**Files**: `src/utils/errors.py`

Implementar sistema padronizado de error formatting conforme FR-025:
- Classe base `RabbitMQError(Exception)` com campos:
  - `code: str` - Error code categórico (e.g., "INVALID_NAME", "QUEUE_NOT_EMPTY")
  - `field: Optional[str]` - Campo/parâmetro afetado
  - `expected: Optional[str]` - Valor esperado
  - `actual: Optional[str]` - Valor fornecido
  - `action: str` - Ação corretiva sugerida
  - `context: dict` - Contexto adicional para logging
- Subclasses específicas:
  - `ValidationError(RabbitMQError)` - Para validação de entrada
  - `AuthorizationError(RabbitMQError)` - Para erros 401/403
  - `NotFoundError(RabbitMQError)` - Para erros 404
  - `ConflictError(RabbitMQError)` - Para duplicatas, filas não vazias, etc
  - `ConnectionError(RabbitMQError)` - Para problemas de rede
- Método `to_dict()` para serialização JSON
- Método `to_user_message()` para CLI output formatado
- Helper `format_error(error: Exception) -> RabbitMQError` para converter exceptions genéricas

**Success Criteria**: Todas as exceptions do sistema seguem padrão FR-025 com 4 elementos (code, field/context, expected/actual, action)
 [X]

**Dependencies**: T002

---

### T022b: Implement Input Validation Helpers
**Story**: US2  
**Type**: Validation  
**Files**: `src/utils/validation.py`

Implementar validações de entrada usando error formatting padronizado:
- Função `validate_name(name: str) -> None` - regex ^[a-zA-Z0-9._-]{1,255}$ (FR-004, FR-013)
  - Raises ValidationError com code="INVALID_NAME", expected="alphanumeric chars only", actual=name, action="Remove special characters"
- Função `validate_exchange_type(type: str) -> None` - enum validation (FR-012)
  - Raises ValidationError com code="INVALID_EXCHANGE_TYPE", expected="direct|topic|fanout|headers", actual=type
- Função `validate_routing_key(key: str, exchange_type: str) -> None` - wildcards para topic (FR-021)
  - Raises ValidationError se wildcards usados em exchange não-topic
- Todas as exceções usam RabbitMQError classes de T022

**Success Criteria**: Validações rejeitam nomes inválidos com mensagens claras seguindo padrão FR-025
 [X]

**Dependencies**: T022

---

### T022c: Implement Virtual Host Validation
**Story**: Foundational  
**Type**: Validation  
**Files**: `src/utils/validation.py`, `src/utils/connection.py`

Implementar validação de existência de virtual host (FR-024):
- Função `validate_vhost_exists(vhost: str, executor: RabbitMQExecutor) -> None`
- GET `/api/vhosts/{vhost}` para verificar existência
- **Cache**: Implementar cache de 60 segundos para resultados de validação (60s é padrão comum em aplicações RabbitMQ enterprise para balance entre freshness e performance - reduz overhead em operações sequenciais)
- **Cache Key**: Usar `vhost_exists:{vhost}` como chave
- **Cache Invalidation Strategy**: Cache DEVE ser invalidado imediatamente em caso de:
  - HTTP 404 (vhost não existe) - invalidar para permitir re-check após criação
  - HTTP 401/403 (sem permissão) - invalidar para permitir re-check após correção de credenciais
  - HTTP 5xx (server error) - NÃO cachear resultado negativo, tentar novamente
  - Sucesso (200 OK) - cachear por 60s (vhost confirmado existir)
- Raises ValidationError com code="VHOST_NOT_FOUND", expected="valid vhost", actual=vhost, action="Create vhost first with 'rabbitmqctl add_vhost {vhost}' or specify existing vhost"
- Integrar validação em todas operações de topology (list, create, delete) antes de executar operação principal

**Success Criteria**: 
- 100% das operações de topology validam vhost antes de executar (conforme FR-024)
- Cache funciona corretamente e reduz chamadas repetidas (60s TTL validado)
- Cache invalidation funciona para error responses (404, 401, 403)
- Erro claro quando vhost não existe seguindo padrão FR-025 com todos 4 elementos
 [X]

**Dependencies**: T006, T022

---

### T023: Implement Queue Create Operation
**Story**: US2  
**Type**: Operation  
**Files**: `src/tools/operations/queues.py`

Implementar operação de criação de fila:
- Função `create_queue(vhost: str, name: str, options: QueueOptions) -> Queue`
- **Validação de vhost primeiro** (T022c) - raise ValidationError se não existe
- Validação de nome antes de criar (T022b)
- PUT /api/queues/{vhost}/{name}
- Detecção de duplicatas (FR-005) - raise ConflictError
- Logging de auditoria (FR-026) - level INFO com campos: timestamp, correlation_id, operation="queue.create", vhost, queue_name=name, user, result="success"
- Performance < 1s (SC-002, classified as complex operation)

**Success Criteria**: Cria fila com opções (durable, exclusive, auto_delete, arguments), vhost validado primeiro
 [X]

**Dependencies**: T006, T007, T022b, T022c

---

### T024: [P] Implement Exchange Create Operation
**Story**: US2  
**Type**: Operation  
**Files**: `src/tools/operations/exchanges.py`

Implementar operação de criação de exchange:
- Função `create_exchange(vhost: str, name: str, type: str, options: ExchangeOptions) -> Exchange`
- **Validação de vhost primeiro** (T022c)
- Validação de nome e tipo (T022b)
- PUT /api/exchanges/{vhost}/{name}
- Detecção de duplicatas (FR-014) - raise ConflictError
- Logging de auditoria - level INFO com campos: timestamp, correlation_id, operation="exchange.create", vhost, exchange_name=name, type, user, result="success"
- Performance < 1s (complex operation)

**Success Criteria**: Cria exchange com tipo e opções corretas, vhost validado primeiro
 [X]

**Dependencies**: T006, T007, T022b, T022c

---

### T025: [P] Implement Binding Create Operation
**Story**: US2  
**Type**: Operation  
**Files**: `src/tools/operations/bindings.py`

Implementar operação de criação de binding:
- Função `create_binding(vhost: str, exchange: str, queue: str, routing_key: str, args: dict) -> Binding`
- **Validação de vhost primeiro** (T022c)
- **Validação de existência** (FR-020):
  - Validar exchange primeiro: GET `/api/exchanges/{vhost}/{exchange}` - raise NotFoundError(resource="exchange") se não existir
  - Validar queue depois: GET `/api/queues/{vhost}/{queue}` - raise NotFoundError(resource="queue") se não existir
  - Se ambos não existem, agregar erros: NotFoundError(resources=["exchange", "queue"])
  - Executar validações em paralelo quando possível para melhor performance
- Validação de routing key (wildcards para topic via T022b)
- POST /api/bindings/{vhost}/e/{exchange}/q/{queue}
- Detecção de duplicatas (FR-023) - raise ConflictError
- Logging de auditoria - level INFO com campos: timestamp, correlation_id, operation="binding.create", vhost, exchange, queue, routing_key, user, result="success"

**Success Criteria**: Cria binding conectando exchange a fila com routing key, ordem de validação correta (exchange → queue)
 [X]

**Dependencies**: T006, T007, T022b, T022c

---

### T026: Extend call-id Tool for Create Operations
**Story**: US2  
**Type**: MCP Tool  
**Files**: `src/tools/call_id.py`

Estender call-id para operações de criação:
- Adicionar roteamento: queues.create, exchanges.create, bindings.create
- Validação de parâmetros obrigatórios
- Error handling com mensagens claras (FR-025, SC-007)

**Success Criteria**: Tool executa "queues.create" com validação completa
 [X]

**Dependencies**: T023, T024, T025

---

### T027: Implement CLI Queue Create Command
**Story**: US2  
**Type**: CLI  
**Files**: `src/cli/commands/queue.py`

Implementar comando CLI para criar fila:
- Comando `rabbitmq-mcp-server queue create --name NAME`
- Opções: --durable, --exclusive, --auto-delete, --arguments (JSON)
- Validação de nome antes de enviar
- Mensagem de sucesso ou erro clara

**Success Criteria**: Comando cria fila com opções especificadas
 [X]

**Dependencies**: T026

---

### T028: [P] Implement CLI Exchange Create Command
**Story**: US2  
**Type**: CLI  
**Files**: `src/cli/commands/exchange.py`

Implementar comando CLI para criar exchange:
- Comando `rabbitmq-mcp-server exchange create --name NAME --type TYPE`
- Opções: --durable, --auto-delete, --internal, --arguments
- Validação de tipo (direct/topic/fanout/headers)

**Success Criteria**: Comando cria exchange do tipo especificado
 [X]

**Dependencies**: T026

---

### T029: [P] Implement CLI Binding Create Command
**Story**: US2  
**Type**: CLI  
**Files**: `src/cli/commands/binding.py`

Implementar comando CLI para criar binding:
- Comando `rabbitmq-mcp-server binding create --exchange X --queue Q`
- Opções: --routing-key, --arguments
- Exemplos de wildcards no help text

**Success Criteria**: Comando cria binding com routing key (incluindo wildcards)
 [X]

**Dependencies**: T026

---

### ✅ Checkpoint: User Story 2 Complete

**Validation**:
- [X] Comando `queue create` cria filas com opções corretas
- [X] Comando `queue create` cria filas com opções corretas
- [X] Comando `exchange create` cria exchanges de todos os tipos
- [X] Comando `binding create` cria bindings com wildcards (* e #)
- [X] Validações impedem nomes inválidos antes de enviar
- [X] Detecção de duplicatas funciona (FR-005, FR-014, FR-023)
- [X] Operações completam em < 1 segundo
- [X] Logs de auditoria registram todas as criações

**Deliverable**: Sistema completo de criação de infraestrutura

---

## Phase 5: User Story 3 (P3) - Remove Infrastructure

**Goal**: Implementar deleção segura com validações que previnem perda de dados

**Independent Test**: Testar validações de segurança e confirmar remoções bem-sucedidas quando apropriado

### T030: Implement Queue Validation Before Delete
**Story**: US3  
**Type**: Validation  
**Files**: `src/tools/operations/queues.py`

Adicionar validação de segurança para deleção de fila:
- Função `validate_queue_delete(vhost: str, name: str, force: bool) -> None`
- GET queue details para verificar message count
- Bloquear se messages > 0 e force=false (FR-007)
- Permitir se messages == 0 ou force=true (FR-008)
- Mensagem clara quando bloqueado (FR-025, SC-007)

**Success Criteria**: 100% prevenção de deleção de filas com mensagens sem --force (SC-004)
 [X]

**Dependencies**: T013

---

### T031: [P] Implement Exchange Validation Before Delete
**Story**: US3  
**Type**: Validation  
**Files**: `src/tools/operations/exchanges.py`

Adicionar validação de segurança para deleção de exchange:
- Função `validate_exchange_delete(vhost: str, name: str) -> None`
- Verificar se é exchange de sistema: prefixo "amq.*" ou "" (string vazia) (FR-017)
- GET bindings para contar bindings ativos
- Bloquear se bindings_count > 0 (FR-016)
- Mensagem indicando quais bindings remover primeiro

**Success Criteria**: 100% bloqueio de exchanges com bindings (SC-005), 100% prevenção de deleção de exchanges de sistema
 [X]

**Dependencies**: T014, T015

---

### T032: Implement Queue Delete Operation
**Story**: US3  
**Type**: Operation  
**Files**: `src/tools/operations/queues.py`

Implementar operação de deleção de fila:
- Função `delete_queue(vhost: str, name: str, force: bool) -> None`
- Validação antes de deletar (T030)
- DELETE /api/queues/{vhost}/{name}
- Logging de auditoria (FR-026)
- Performance < 1s (SC-003)

**Success Criteria**: Deleta fila vazia ou com --force
 [X]

**Dependencies**: T030

---

### T033: [P] Implement Exchange Delete Operation
**Story**: US3  
**Type**: Operation  
**Files**: `src/tools/operations/exchanges.py`

Implementar operação de deleção de exchange:
- Função `delete_exchange(vhost: str, name: str) -> None`
- Validação antes de deletar (T031)
- DELETE /api/exchanges/{vhost}/{name}
- Logging de auditoria
- Performance < 1s

**Success Criteria**: Deleta exchange sem bindings, bloqueia se tiver bindings
 [X]

**Dependencies**: T031

---

### T034: [P] Implement Binding Delete Operation
**Story**: US3  
**Type**: Operation  
**Files**: `src/tools/operations/bindings.py`

Implementar operação de deleção de binding:
- Função `delete_binding(vhost: str, exchange: str, queue: str, properties_key: str) -> None`
- DELETE /api/bindings/{vhost}/e/{exchange}/q/{queue}/{properties_key}
- Logging de auditoria
- Performance < 1s

**Success Criteria**: Deleta binding específico, fluxo de mensagens para imediatamente
 [X]

**Dependencies**: T015

---

### T035: Extend call-id Tool for Delete Operations
**Story**: US3  
**Type**: MCP Tool  
**Files**: `src/tools/call_id.py`

Estender call-id para operações de deleção:
- Adicionar roteamento: queues.delete, exchanges.delete, bindings.delete
- Propagação de erros de validação com mensagens claras
- Suporte a parâmetro force para queues.delete

**Success Criteria**: Tool executa deleções com validações de segurança funcionando
 [X]

**Dependencies**: T032, T033, T034

---

### T036: Implement CLI Queue Delete Command
**Story**: US3  
**Type**: CLI  
**Files**: `src/cli/commands/queue.py`

Implementar comando CLI para deletar fila:
- Comando `rabbitmq-mcp-server queue delete --name NAME`
- Opção: --force para forçar deleção com mensagens
- Mensagem clara quando bloqueado por ter mensagens
- Confirmação de sucesso após deleção

**Success Criteria**: Comando deleta fila vazia, bloqueia fila com mensagens sem --force
 [X]

**Dependencies**: T035

---

### T037: [P] Implement CLI Exchange Delete Command
**Story**: US3  
**Type**: CLI  
**Files**: `src/cli/commands/exchange.py`

Implementar comando CLI para deletar exchange:
- Comando `rabbitmq-mcp-server exchange delete --name NAME`
- Mensagem clara quando bloqueado por ter bindings
- Lista de bindings que devem ser removidos primeiro

**Success Criteria**: Comando deleta exchange sem bindings, bloqueia se tiver bindings
 [X]

**Dependencies**: T035

---

### T038: [P] Implement CLI Binding Delete Command
**Story**: US3  
**Type**: CLI  
**Files**: `src/cli/commands/binding.py`

Implementar comando CLI para deletar binding:
- Comando `rabbitmq-mcp-server binding delete --exchange X --queue Q --properties-key KEY`
- Confirmação de sucesso

**Success Criteria**: Comando deleta binding específico
 [X]

**Dependencies**: T035

---

### ✅ Checkpoint: User Story 3 Complete

**Validation**:
- [X] Deleção de fila com mensagens é bloqueada sem --force (SC-004)
- [X] Deleção de exchange com bindings é bloqueada (SC-005)
- [X] Flag --force permite forçar deleção de fila com mensagens
- [X] Exchanges de sistema (amq.*) não podem ser deletados (FR-017)
- [X] Mensagens de erro são claras e indicam como resolver (SC-007)
- [X] Operações completam em < 1 segundo
- [X] Logs de auditoria registram todas as deleções

**Deliverable**: Sistema completo de remoção segura

---

## Phase 6: Polish & Cross-Cutting Concerns

**Goal**: Completar documentação, testes e funcionalidades transversais

### T039: Write Unit Tests for Error Formatting and Validators
**Story**: Polish  
**Type**: Testing  
**Files**: `tests/unit/test_errors.py`, `tests/unit/test_validator.py`

Escrever testes unitários para error formatting e validações:
- **Error Formatting (test_errors.py)**:
  - Test RabbitMQError base class serialization (to_dict, to_user_message)
  - Test todas as subclasses (ValidationError, AuthorizationError, NotFoundError, ConflictError, ConnectionError)
  - Test que 95% dos errors incluem code, field/context, expected/actual, action (SC-007)
- **Validators (test_validator.py)**:
  - Validação de nomes (válidos e inválidos) - assert ValidationError raised com campos corretos
  - Validação de tipos de exchange - assert error messages seguem padrão FR-025
  - Validação de routing keys com wildcards
  - Edge cases (nomes muito longos, caracteres especiais)

**Success Criteria**: 100% cobertura de `src/utils/errors.py` e `src/utils/validation.py`, todos os errors testados têm 4 elementos obrigatórios
 [X]

**Dependencies**: T022, T022b

---

### T040: [P] Write Unit Tests for MCP Tools
**Story**: Polish  
**Type**: Testing  
**Files**: `tests/unit/test_search_ids.py`, `tests/unit/test_get_id.py`, `tests/unit/test_call_id.py`

Escrever testes unitários para ferramentas MCP:
- search-ids: busca semântica retorna resultados corretos
  - Performance test: busca < 100ms (Constitution requirement)
  - Test de paginação da busca (page, pageSize)
- get-id: schemas completos para operation IDs válidos
- call-id: roteamento correto para operações, validação de params
  - Test de paginação obrigatória em list operations (FR-033)
  - Test de limites de paginação: 1 <= pageSize <= 200 (FR-034)
  - Test de metadados de paginação completos (FR-035, SC-010)
- Mock de HTTP requests

**Success Criteria**: Testes cobrem happy paths, error cases, performance <100ms para search, e paginação completa

 [X]

**Dependencies**: T011, T012, T016, T026, T035

---

### T041: [P] Write Unit Tests for Operations
**Story**: Polish  
**Type**: Testing  
**Files**: `tests/unit/test_operations.py`

Escrever testes unitários para operações:
- Queues: list (com paginação), create, delete
- Exchanges: list (com paginação), create, delete
- Bindings: list (com paginação), create, delete
- Mock de HTTP client
- **Validação de vhost em todas operações** (T022c)
- Validações antes de requests
- Test de paginação: cálculo correto de totalPages, hasNextPage, hasPreviousPage
- Test de performance: operações list < 2s por página (SC-001, FR-036), CRUD < 1s
- **Test de column ordering (FR-030a)**: Validar que table formatters ordenam colunas corretamente:
  - Queue list: name → durable/exclusive/auto_delete → messages/consumers/memory
  - Exchange list: name → type/durable/auto_delete → bindings_count (+ message_stats com --verbose)
  - Binding list: source_exchange/destination_queue → routing_key → vhost
  - Test deve verificar ordem exata das colunas no output formatado
- **Test de audit logging (SC-008, G2 coverage gap CRÍTICO - ZERO TOLERÂNCIA)**:
  - **100% das operações create/delete DEVEM ser logadas** (FR-026 requirement absoluto)
  - Validar campos obrigatórios presentes em TODOS logs: timestamp, correlation_id, operation, vhost, resource_name, user, result (success/failure)
  - Operações list também logadas com nível DEBUG (incluindo vhost, page, pageSize)
  - Validar sanitização de credenciais nos logs (passwords, tokens) - testar que credenciais NÃO aparecem em plain text
  - **Test específico quantitativo**: criar 10 filas sequencialmente, verificar que exatamente 10 logs de audit foram gerados (não 9, não 11 - exato)
  - **Test de cobertura**: para cada operação create/delete implementada, DEVE haver test case validando log de audit
- Test de error messages: formato claro com código, campo, expected/actual (SC-007, I2 validation)
  - **Validar que 95% dos error test cases incluem todos 4 elementos obrigatórios**: código de erro (ex: "INVALID_NAME"), contexto específico (field afetado), expected vs actual value, ação corretiva sugerida
  - Criar matriz de test cases cobrindo todos error codes implementados (INVALID_NAME, QUEUE_NOT_EMPTY, VHOST_NOT_FOUND, UNAUTHORIZED, NOT_FOUND, etc.)
  - **Cálculo de 95%**: Se implementar 20 error codes diferentes, no mínimo 19 DEVEM ter todos 4 elementos testados
- Test de memory footprint:
  - Validar que list operations com 1000 itens não excedem 1GB de memória (plan.md constraint)
  - Usar memory_profiler ou tracemalloc para medir uso

**Success Criteria**: 80%+ cobertura de `src/tools/operations/`, paginação testada, **100% audit logging validado**, 95% error messages com 4 elementos, memory footprint < 1GB confirmado

 [X]

**Dependencies**: T013-T015, T023-T025, T032-T034, T022c

---

### T042: Write Integration Tests for Queue Operations
**Story**: Polish  
**Type**: Testing  
**Files**: `tests/integration/test_queue_operations.py`

Escrever testes de integração com RabbitMQ real:
- Setup: Usar testcontainers-python para RabbitMQ efêmero
- Test: Criar, listar (paginado), deletar filas
- Test: Paginação funcional com múltiplas páginas (criar 150 filas, paginar 50 por vez)
- Test: Validação de fila com mensagens (bloquear deleção)
- Test: Force delete de fila com mensagens
- Test: Timeout handling quando listagem demora muito (edge case)
- Test: Audit logging para create/delete (validar logs gerados)
- Test: Authorization errors propagados corretamente (FR-027)
- **Concurrency/Race Condition Test**: Test simultaneous conflicting operations:
  - Test: Criar e deletar mesma fila em threads paralelos → uma operação sucede, outra falha com erro apropriado (ConflictError ou NotFoundError)
  - Test: Criar mesma fila de duas threads paralelas → uma sucede, outra falha com "Queue already exists"
  - Usar threading.Thread ou asyncio para simular concorrência
- **Edge cases do spec.md**:
  - Test: Listar filas em virtual host inexistente → erro claro "Virtual host '/invalid' does not exist"
  - Test: Criar fila com nome inválido (caracteres especiais, > 255 chars) → erro de validação específico
  - Test: Conexão cai durante operação → erro de conectividade imediato
  - Test: Timeout em listagem com grande volume → erro de timeout com sugestão de filtrar por vhost
- Teardown: Limpar containers

**Success Criteria**: Testes passam contra RabbitMQ real, paginação funciona, race conditions testadas, todos edge cases validados, audit logging validado

[X]

**Dependencies**: T013, T023, T032

---

### T043: [P] Write Integration Tests for Exchange Operations
**Story**: Polish  
**Type**: Testing  
**Files**: `tests/integration/test_exchange_operations.py`

Escrever testes de integração para exchanges:
- Test: Criar exchanges de todos os tipos (direct, topic, fanout, headers)
- Test: Listar exchanges (paginado)
- Test: Paginação com múltiplas páginas
- Test: Bloquear deleção de exchange com bindings
- Test: Deletar exchange sem bindings
- Test: Audit logging para create/delete
- Test: Authorization errors propagados
- **Concurrency/Race Condition Test**: Test simultaneous conflicting operations:
  - Test: Criar e deletar mesmo exchange em threads paralelos → uma operação sucede, outra falha com erro apropriado
  - Test: Criar mesmo exchange de duas threads paralelas → uma sucede, outra falha com "Exchange already exists"
- **Edge cases do spec.md**:
  - Test: Deletar exchange com bindings ativos → erro indicando que bindings devem ser removidos primeiro
  - Test: Deletar exchange do sistema (amq.direct, amq.topic, "") → erro "System exchanges are protected"
  - Test: Operações conflitantes simultâneas (criar e deletar mesmo exchange) → uma falha com erro apropriado

**Success Criteria**: Testes validam todos os tipos de exchange, safety checks (FR-016, FR-017), race conditions testadas, paginação, edge cases e audit logging

[X]

**Dependencies**: T014, T024, T033

---

### T044: [P] Write Integration Tests for Binding Operations
**Story**: Polish  
**Type**: Testing  
**Files**: `tests/integration/test_binding_operations.py`

Escrever testes de integração para bindings:
- Test: Criar binding com routing key simples
- Test: Criar binding com wildcards (* e #)
  - Test específico: pattern "orders.*.created" match "orders.eu.created" mas não "orders.eu.us.created"
  - Test específico: pattern "orders.#" match "orders.created", "orders.eu.created", "orders.eu.us.created"
  - Test específico: wildcards em exchange type "topic" permitidos, rejeitados em "direct"
- Test: Listar bindings (paginado)
- Test: Paginação funcional
- Test: Prevenir duplicatas
- Test: Deletar binding
- Test: Audit logging para create/delete
- **Concurrency/Race Condition Test**: Test simultaneous conflicting operations:
  - Test: Criar mesmo binding de duas threads paralelas → uma sucede, outra falha com "Binding already exists"
  - Test: Criar e deletar mesmo binding simultaneamente → uma operação sucede, outra falha apropriadamente
- **Edge cases do spec.md**:
  - Test: Criar binding entre fila e exchange que não existem → erro claro (FR-020)

**Success Criteria**: Testes validam wildcards complexos (FR-021), prevenção de duplicatas (FR-023), validação de existência (FR-020), race conditions testadas, paginação e audit logging

[X]

**Dependencies**: T015, T025, T034

---

### T045: Write Contract Tests for OpenAPI Compliance
**Story**: Polish  
**Type**: Testing  
**Files**: `tests/contract/test_openapi_compliance.py`

Escrever testes de contrato validando OpenAPI:
- Validar requests gerados correspondem ao OpenAPI schema
- Validar responses do RabbitMQ correspondem ao esperado
- Validar schemas de paginação (PaginatedQueueResponse, PaginationMetadata)
- Validar params de paginação (page, pageSize) em operações list
- Usar schemathesis ou similar para fuzzing de schemas
- Test que PaginationMetadata está presente em todas respostas list

**Success Criteria**: 100% das operações validadas contra OpenAPI spec, schemas de paginação validados

[X]

**Dependencies**: T003, T005

---

### T046: [P] Write API Documentation
**Story**: Polish  
**Type**: Documentation  
**Files**: `docs/API.md`

Escrever documentação de API completa:
- Referência de todas as operações (queues, exchanges, bindings)
- Parâmetros, tipos, exemplos de request/response
- Códigos de erro e troubleshooting
- Exemplos de uso de wildcards

**Success Criteria**: Documentação em inglês, clara e completa
 [X]

**Dependencies**: T016, T026, T035

---

### T047: [P] Write Architecture Documentation
**Story**: Polish  
**Type**: Documentation  
**Files**: `docs/ARCHITECTURE.md`

Escrever documentação de arquitetura:
- Diagrama de componentes
- Padrão de 3 ferramentas MCP (search-ids, get-id, call-id)
- OpenAPI-driven architecture
- Vector database para semantic search
- Decisões técnicas principais

**Success Criteria**: Documentação explica design e justificativas
 [X]

**Dependencies**: Todas as tarefas anteriores

---

### T048: [P] Write Usage Examples Documentation
**Story**: Polish  
**Type**: Documentation  
**Files**: `docs/EXAMPLES.md`

Escrever exemplos de uso:
- Exemplos com uvx (recommended)
- Exemplos bash e PowerShell
- Casos de uso comuns (monitoramento, setup, cleanup)
- Debugging tips
- Integração com ferramentas (jq, grep)

**Success Criteria**: Exemplos práticos e copy-pasteable
 [X]

**Dependencies**: T017-T019, T027-T029, T036-T038

---

### T049: [P] Write Contributing Guide
**Story**: Polish  
**Type**: Documentation  
**Files**: `docs/CONTRIBUTING.md`

Escrever guia de contribuição:
- Como configurar ambiente de desenvolvimento
- Como rodar testes
- Como gerar schemas do OpenAPI
- Como gerar embeddings
- Code style e linting
- Processo de PR

**Success Criteria**: Guia permite novo contribuidor começar facilmente
 [X]

**Dependencies**: T005, T009

---

### T050: Update README with Complete Information
**Story**: Polish  
**Type**: Documentation  
**Files**: `README.md`

Atualizar README principal:
- Overview completo do projeto
- Quick start com uvx
- Link para documentação completa
- Features principais
- Requisitos e compatibilidade
- Licença LGPL v3.0
- Links para contribuição

**Success Criteria**: README profissional e informativo
 [X]

**Dependencies**: T046, T047, T048

---

### T051: Setup Linting and Code Quality
**Story**: Polish  
**Type**: Quality  
**Files**: `.pre-commit-config.yaml`, `pyproject.toml`

Configurar ferramentas de qualidade com regras específicas:
- **black** para formatação de código
  - line-length: 100 (padrão para Python CLI tools)
  - target-version: py312
- **ruff** para linting
  - select: ["E", "F", "I", "N", "W", "UP"] (pycodestyle, pyflakes, isort, naming, warnings, pyupgrade)
  - line-length: 100
  - ignore: ["E501", "N803", "N806", "N815", "E402", "F404"] (allow line length, non-standard names for API compatibility, module-level imports after docstrings)
- **mypy** para type checking
  - strict: true
  - python_version: "3.12"
  - warn_return_any: true
  - disallow_untyped_defs: true
- **pre-commit hooks**
  - black, ruff, mypy
  - trailing-whitespace, end-of-file-fixer
  - bandit (security checks)
- Configuração em pyproject.toml

**Success Criteria**: Linting passa em todo o código com 0 warnings, type checking 100% coverage
 [X]

**Dependencies**: Todas as tarefas de implementação

---

### T052: Add License Headers to All Source Files
**Story**: Polish  
**Type**: Legal  
**Files**: Todos os arquivos .py

Adicionar headers LGPL v3.0:
- Header padrão em todos os arquivos Python
- Script para verificar headers (scripts/add_license_headers.py)
- Automated check no CI (futuro)
- Handles files with shebangs correctly

**Success Criteria**: 100% dos arquivos fonte com header de licença
 [X]

**Dependencies**: Todas as tarefas de implementação

---

## Task Dependencies Graph

```
Setup Phase:
T001 (Init Project)
├─→ T002 (Directory Structure)

Foundational Phase (all parallel after T002):
T003 (OpenAPI Parser) ─┬─→ T004 (Operation Registry) ─→ T009 (Generate Embeddings) ─→ T009b (OpenAPI Change Detection) ─→ T010 (Vector Search)
                       └─→ T005 (Pydantic Schemas)
T006 (HTTP Executor) ─→ T022 (Error Formatting) ─┬─→ T022b (Input Validation)
T007 (Logging)                                    └─→ T022c (VHost Validation)
T008 (Configuration)

User Story 1 (View):
T010 ─→ T011 (search-ids)
T004 ─→ T012 (get-id)
T022c (VHost Validation) ─→ T013 (Queue List) ─┬
                            T014 (Exchange List) ├─→ T016 (call-id for list) ─┬─→ T017 (CLI Queue List) ─┬
                            T015 (Binding List) ─┘                             ├─→ T018 (CLI Exchange List) ├─→ T020 (Table Formatter)
                                                                               └─→ T019 (CLI Binding List) ─┴─→ T021 (JSON Formatter)

User Story 2 (Create):
T022 (Error Formatting) ─→ T022b (Input Validation) ─┬─→ T023 (Queue Create) ─┬
T022c (VHost Validation) ────────────────────────────┼─→ T024 (Exchange Create) ├─→ T026 (call-id for create) ─┬─→ T027 (CLI Queue Create)
                                                      └─→ T025 (Binding Create) ─┘                               ├─→ T028 (CLI Exchange Create)
                                                                                                                 └─→ T029 (CLI Binding Create)

User Story 3 (Delete):
T030 (Queue Delete Validation) ─→ T032 (Queue Delete) ─┬
T031 (Exchange Delete Validation) ─→ T033 (Exchange Delete) ├─→ T035 (call-id for delete) ─┬─→ T036 (CLI Queue Delete)
T034 (Binding Delete) ────────────────────────────────────┘                                  ├─→ T037 (CLI Exchange Delete)
                                                                                              └─→ T038 (CLI Binding Delete)

Polish Phase (mostly parallel):
T039-T045 (Tests)
T046-T050 (Documentation)
T051-T052 (Quality & Legal)
```

---

## Parallel Execution Opportunities

### Setup & Foundation (6-8 tasks parallel)
- T002, T003, T006, T007, T008 podem rodar em paralelo após T001
- T004, T005 podem rodar em paralelo após T003
- T009, T010 dependem de T003/T004 mas são sequenciais

### User Story 1 (5-7 tasks parallel)
- T011, T012 podem rodar em paralelo
- T013, T014, T015 (operações list) podem rodar totalmente em paralelo
- T017, T018, T019 (CLI) podem rodar em paralelo após T016
- T020, T021 (formatters) podem rodar em paralelo

### User Story 2 (4-5 tasks parallel)
- T023, T024, T025 (operações create) podem rodar em paralelo após T022
- T027, T028, T029 (CLI) podem rodar em paralelo após T026

### User Story 3 (4-5 tasks parallel)
- T030, T031 podem rodar em paralelo
- T032, T033, T034 (operações delete) podem rodar em paralelo
- T036, T037, T038 (CLI) podem rodar em paralelo após T035

### Polish Phase (12+ tasks parallel)
- Todos os testes (T039-T045) podem rodar em paralelo
- Toda a documentação (T046-T050) pode ser escrita em paralelo
- T051, T052 podem rodar após implementação completa

**Estimated parallel speed-up**: 2-3x com 4-6 desenvolvedores

---

## Implementation Strategy

### MVP (Minimum Viable Product)
**Scope**: User Story 1 only (View and Monitor)
**Tasks**: T001-T021
**Timeline**: Entrega valor imediato de visibilidade sem modificar infraestrutura
**Deliverable**: CLI completo de visualização + MCP tools para listagem

### Incremental Rollout
1. **Phase 1**: MVP (View) - T001 a T021
2. **Phase 2**: Create operations - T022 a T029
3. **Phase 3**: Delete operations - T030 a T038
4. **Phase 4**: Polish - T039 a T052

Cada fase entrega valor independente e pode ser testada isoladamente.

---

## Summary

**Total Tasks**: 55 tarefas (inclui T009b para OpenAPI change detection, T022b para input validation, e T022c para vhost validation)  
**Tasks per Story**:
- Setup: 2 tarefas (T001-T002)
- Foundational: 10 tarefas (blockers) - T003-T010, inclui T009b e T022c
- US1 (View): 11 tarefas (T011-T021)
- US2 (Create): 9 tarefas (T022-T029, inclui T022 error formatting + T022b input validation)
- US3 (Delete): 9 tarefas (T030-T038)
- Polish: 14 tarefas (T039-T052)

**Parallelization**: ~25 tarefas podem ser executadas em paralelo  
**Critical Path**: T001 → T002 → T003 → T004 → T009 → T009b → T010 → T011 → User Stories  
**Estimated Effort**: 15-20 dias com 1 desenvolvedor, 5-7 dias com equipe de 4

**Key Updates from /analyze Remediation**:
- **C1 RESOLVED**: Client-side pagination documentada e validada contra documentação oficial RabbitMQ (não suporta paginação nativa)
- **C2 RESOLVED**: Operações CRUD reclassificadas como "complex operations" com justificativa (validações múltiplas, audit logging)
- **A1 RESOLVED**: Estatísticas obrigatórias vs opcionais clarificadas em FR-002 e FR-010
- **I1 RESOLVED**: Conversão de --force para if-empty=false documentada em T006
- **G1 RESOLVED**: Task T022c adicionada para validação de virtual host (FR-024)
- **G3 RESOLVED**: Sistema clarificado como MCP Server com CLI built-in
- **I2 RESOLVED**: Validação de formato de erro em 95% dos casos adicionada em T041
- **U1 RESOLVED**: Ordem de validação exchange→queue documentada em T025
- **U2 RESOLVED**: Timeout para operações de listagem especificado em FR-036
- **D1 RESOLVED**: Cross-reference entre FR-026 e FR-027 adicionado
- **G2 RESOLVED**: Validação de audit logging 100% adicionada em T041

**Success Metrics**:
- ✅ Listagens < 2s por página paginada (SC-001, FR-036) - complex operations
- ✅ Operações CRUD < 1s cada - complex operations (validações múltiplas)
- ✅ 100% prevenção de deleção sem --force/validação
- ✅ 95% mensagens de erro claras (código, campo, expected/actual) (SC-007) - validado em T041
- ✅ 100% audit logging validado - validado em T041 (G2 resolved)
- ✅ 80%+ cobertura de testes
- ✅ Semantic search < 100ms (Constitution) - basic operation
- ✅ Paginação client-side funcionando (FR-033-036, SC-010) - validated contra API oficial
- ✅ Documentação completa em inglês

---

**Document Status**: ✅ Complete  
**Ready for Implementation**: Yes  
**Next Step**: Begin with T001 (Initialize Python Project Structure)
