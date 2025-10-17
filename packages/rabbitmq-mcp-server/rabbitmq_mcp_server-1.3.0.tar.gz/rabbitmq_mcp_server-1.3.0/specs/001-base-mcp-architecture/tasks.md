# Implementation Tasks: Base MCP Architecture

**Feature**: Base MCP Architecture  
**Date**: 2025-10-09  
**Status**: Ready for Implementation  
**Branch**: `feature/001-base-architecture`

## Overview

Este documento organiza as tarefas de implementação baseadas nas User Stories do [spec.md](./spec.md). As tarefas estão agrupadas por fase, com cada User Story formando uma entrega independente e testável.

**Total Tasks**: 73 tarefas (56 originais + 17 novas: T004a, T008a, T019.1, T035.1, T050a, T057-T068)  
**Parallelizable**: 32 tarefas marcadas com [P] (21 originais + 11 novas)  
**Estimated Duration**: 7-9 semanas (console client + multilingual incluídos conforme constitution)

**Novas Tasks Adicionadas**:
- **Análise /speckit.analyze**: T004a, T008a, T019.1, T035.1, T050a (gaps de validação)
- **Constitution Compliance (CC3/CC4)**: T057-T068 (console client + multilingual - ADR-002)

**Breakdown**:
- T004a: Testes de validação de logging JSON e sanitização - 19 patterns (CC5)
- T008a: Geração de schemas para múltiplas versões de OpenAPI com fallback (U4)
- T019.1: Teste específico de threshold 0.7 com exemplos reais (C1, A2)
- T035.1: Teste de timeout + pagination para listagens >1000 items ou >50MB (C2, A1)
- T050a: Teste de integração OpenTelemetry end-to-end com métrica 95% (C3)
- T057-T068: Console client + i18n 20 idiomas (constitution §VIII mandatory - ADR-002)

## Task Organization

- **Phase 1**: Setup (T001-T006) - Configuração inicial do projeto
- **Phase 2**: Foundational (T007-T013f) - Pré-requisitos bloqueantes + AMQP
- **Phase 3**: User Story 1 - Descobrir Operações (T014-T021) - 🔍 Busca semântica
- **Phase 4**: User Story 2 - Obter Detalhes (T022-T026) - 📋 Documentação de operações
- **Phase 5**: User Story 3 - Executar Operações (T027-T042) - ⚡ Execução validada
- **Phase 6**: User Story 4 - Feedback de Erros (T043-T047) - 🛡️ Error handling
- **Phase 6.5**: Console Client & i18n (T057-T068) - 🖥️ CLI + 20 idiomas (constitution §VIII)
- **Phase 7**: Polish & Integration (T048-T056) - Finalização e testes adicionais

---

## Phase 1: Setup & Project Initialization

**Goal**: Configurar estrutura de projeto, dependências e CI/CD básico  
**Duration**: 1-2 dias  
**Prerequisites**: Nenhum

### T001: Inicializar estrutura de projeto Python

**User Story**: Setup  
**File**: `pyproject.toml`, `README.md`, `.gitignore`  
**Description**: Criar estrutura base do projeto com Poetry, Python 3.12+, configurações iniciais
**Status**: [X] Completed

**Steps**:
1. Criar `pyproject.toml` com metadados do projeto
2. Configurar Poetry com Python 3.12+
3. Adicionar dependências principais: mcp, pydantic, jsonschema, pyyaml, httpx
4. Criar `README.md` básico com instruções de instalação
5. Configurar `.gitignore` para Python

**Acceptance Criteria**:
- ✅ Poetry instalado e configurado
- ✅ `poetry install` executa sem erros
- ✅ Python 3.12+ configurado como versão mínima
- ✅ README contém instruções claras de setup

**Parallel**: ❌ (bloqueia outras tasks de setup)

---

### T002: Configurar dependências de desenvolvimento

**User Story**: Setup  
**File**: `pyproject.toml`  
**Description**: Adicionar ferramentas de desenvolvimento, testing e code quality
**Status**: [X] Completed

**Steps**:
1. Adicionar pytest, pytest-asyncio, pytest-cov, pytest-mock
2. Adicionar testcontainers para integração com RabbitMQ
3. Adicionar datamodel-code-generator para geração de schemas
4. Adicionar black, ruff, mypy para code quality
5. Configurar scripts Poetry para comandos comuns

**Acceptance Criteria**:
- ✅ Todas as deps de dev instaladas
- ✅ `poetry run pytest` executa (mesmo sem testes ainda)
- ✅ `poetry run black .` executa
- ✅ `poetry run mypy .` executa

**Parallel**: ❌ (depende de T001)

---

### T003: Criar estrutura de diretórios

**User Story**: Setup  
**File**: Estrutura de pastas  
**Description**: Criar estrutura de diretórios conforme plan.md
**Status**: [X] Completed

**Steps**:
1. Criar `src/mcp_server/` com `__init__.py`
2. Criar subpastas: `tools/`, `openapi/`, `operations/`, `vector_db/`, `schemas/`, `utils/`
3. Criar `scripts/` para geração de artefatos
4. Criar `tests/` com subpastas: `contract/`, `integration/`, `unit/`
5. Criar `data/` para SQLite databases
6. Criar `config/` para arquivos de configuração
7. Criar `logs/` para logs estruturados

**Acceptance Criteria**:
- ✅ Estrutura de diretórios criada conforme plan.md
- ✅ Cada diretório Python tem `__init__.py`
- ✅ Estrutura de testes reflete estrutura de código

**Parallel**: ✅ [P] (pode rodar em paralelo com T002)

---

### T004: Configurar logging estruturado

**User Story**: Setup  
**File**: `src/mcp_server/utils/logging.py`, `config/config.yaml`  
**Description**: Implementar logging estruturado com structlog e JSON output

**Steps**:
1. Criar `utils/logging.py` com configuração structlog
2. Configurar JSON renderer para production
3. Configurar níveis de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
4. Adicionar redação automática de credenciais (formato: "***") para patterns: `password`, `passwd`, `pwd`, `token`, `secret`, `api_key`, `apikey`, `auth`, `authorization`, `credentials`, `private_key`, `access_token`, `refresh_token`, `bearer`, `jwt`, `session_id`, `cookie`, `client_secret` (19 patterns total, case-insensitive matching)
5. Configurar rotação de logs: daily rotation, max 100MB/file, retention (30 days info/debug, 90 days error/warn, 1 year audit), gzip compression, automatic cleanup
6. Adicionar suporte a variável de ambiente `LOG_LEVEL`

**Acceptance Criteria**:
- ✅ Logs em formato JSON
- ✅ Níveis de log configuráveis via env var
- ✅ Credenciais redatadas automaticamente (todos os patterns listados acima)
- ✅ Logs escritos em `logs/rabbitmq-mcp-{date}.log`

**Parallel**: ✅ [P] (independente de outras tasks de setup)

---

### T004a: Escrever testes de validação de logging

**User Story**: Setup  
**File**: `tests/unit/test_logging.py`  
**Description**: Validar formato JSON de logs e sanitização de credenciais

**Steps**:
1. Criar teste que valida logs são JSON válidos
2. Testar que credenciais são redatadas para todos os 19 patterns: password, passwd, pwd, token, secret, api_key, apikey, auth, authorization, credentials, private_key, access_token, refresh_token, bearer, jwt, session_id, cookie, client_secret (case-insensitive)
3. Testar que níveis de log (DEBUG, INFO, WARNING, ERROR, CRITICAL) funcionam
4. Testar que campos obrigatórios estão presentes (timestamp, level, message)
5. Testar que logs de erro incluem contexto suficiente
6. Validar que dados sensíveis não aparecem em logs (case-insensitive pattern matching)
7. Testar log rotation policies (daily, 100MB max, retention periods)

**Acceptance Criteria**:
- ✅ Logs em formato JSON validados
- ✅ Credenciais redatadas corretamente para todos os patterns listados (ex: password: "***", token: "***", api_key: "***")
- ✅ Todos os níveis de log funcionam
- ✅ Campos obrigatórios presentes

**Parallel**: ✅ [P] (pode rodar em paralelo com T005)

---

### T005: Configurar OpenTelemetry instrumentação

**User Story**: Setup  
**File**: `src/mcp_server/utils/telemetry.py`, `config/config.yaml`  
**Description**: Implementar instrumentação completa com traces, metrics e logs correlacionados

**Steps**:
1. Criar `utils/telemetry.py` com setup OpenTelemetry
2. Configurar OTLP exporter
3. Adicionar auto-instrumentation para HTTP e database
4. Configurar métricas: latência, error rate, cache hits/misses
5. Correlacionar logs com trace IDs
6. Adicionar configuração para endpoint do exporter

**Acceptance Criteria**:
- ✅ OpenTelemetry SDK configurado
- ✅ Traces gerados para operações
- ✅ Métricas expostas via OTLP
- ✅ Logs correlacionados com trace IDs

**Parallel**: ✅ [P] (independente de outras tasks de setup)

---

### T006: Configurar gerenciamento de configuração

**User Story**: Setup  
**File**: `config/config.yaml`, `src/mcp_server/config.py`  
**Description**: Implementar configuração via YAML + env vars com pydantic-settings

**Steps**:
1. Criar `config/config.yaml` com estrutura de configuração
2. Criar `src/mcp_server/config.py` com Pydantic models
3. Implementar substituição de env vars em YAML (${VAR})
4. Validar configurações obrigatórias no startup
5. Documentar variáveis de ambiente em README

**Acceptance Criteria**:
- ✅ Configuração carregada de YAML + env vars
- ✅ Validação com Pydantic models
- ✅ Env vars substituídas corretamente
- ✅ Erros claros para configs inválidas

**Parallel**: ✅ [P] (independente de outras tasks de setup)

---

## Phase 2: Foundational - Prerequisites for All User Stories

**Goal**: Implementar componentes fundamentais que TODAS as user stories dependem  
**Duration**: 2-3 dias  
**Prerequisites**: Phase 1 completa

⚠️ **CHECKPOINT**: Nenhuma User Story pode começar antes desta fase estar completa.

### T007: Implementar parser de OpenAPI

**User Story**: Foundational  
**File**: `src/mcp_server/openapi/parser.py`  
**Description**: Parser para especificação OpenAPI do RabbitMQ HTTP API

**Steps**:
1. Criar `openapi/parser.py` com função de parsing YAML
2. Extrair operações com IDs, paths, métodos HTTP
3. Extrair schemas de request e response
4. Extrair tags (namespaces) e descriptions
5. Validar estrutura do OpenAPI spec
6. Implementar cache de parsing

**Acceptance Criteria**:
- ✅ Parser carrega `.specify/memory/rabbitmq-http-api-openapi.yaml`
- ✅ Extrai operações, schemas, tags corretamente
- ✅ Valida estrutura do OpenAPI
- ✅ Parsing em <100ms

**Parallel**: ❌ (bloqueia geração de schemas e operations)

---

### T008: Implementar geração de registry de operações

**User Story**: Foundational  
**File**: `scripts/generate_operations.py`, `src/mcp_server/openapi/operation_registry.py`  
**Description**: Gerar e popular SQLite database com registro de operações

**Steps**:
1. Criar schema SQLite conforme data-model.md
2. Criar script `generate_operations.py`
3. Extrair operações do OpenAPI via parser
4. Popular tabelas: `namespaces`, `operations`, `metadata`
5. Gerar IDs no formato `{namespace}.{name}`
6. Adicionar índices para performance
7. Implementar `operation_registry.py` para queries

**Acceptance Criteria**:
- ✅ SQLite database criado em `data/rabbitmq_operations.db`
- ✅ ~150-300 operações registradas
- ✅ Namespaces populados corretamente
- ✅ Registry queryable via API Python

**Parallel**: ❌ (depende de T007, bloqueia embeddings e tools)

---

### T008a: Gerar schemas para múltiplas versões de OpenAPI

**User Story**: Foundational  
**File**: `scripts/generate_operations.py` (atualização), `data/rabbitmq_operations_*.db`  
**Description**: Suportar múltiplas versões de OpenAPI (3.11, 3.12, 3.13) geradas em build time

**Steps**:
1. Atualizar script para aceitar versão como parâmetro
2. Gerar registries separados: `rabbitmq_operations_3.11.db`, `rabbitmq_operations_3.12.db`, `rabbitmq_operations_3.13.db`
3. Cada registry contém operações específicas da versão
4. Runtime carrega apenas versão especificada via RABBITMQ_API_VERSION
5. Adicionar validação de versão suportada com fallback claro: erro "Unsupported version: X.Y" + listar versões disponíveis "Supported: 3.11, 3.12, 3.13" + sugerir "Set RABBITMQ_API_VERSION to one of the supported versions"
6. Documentar versões disponíveis em README

**Acceptance Criteria**:
- ✅ Múltiplos registries gerados (um por versão)
- ✅ Runtime carrega versão correta baseado em env var
- ✅ Erro claro para versões não suportadas
- ✅ Documentação de versões completa

**Parallel**: ✅ [P] (pode rodar após T008 inicial)

---

### T009: Implementar geração de schemas Pydantic

**User Story**: Foundational  
**File**: `scripts/generate_schemas.py`, `src/mcp_server/schemas/`  
**Description**: Gerar modelos Pydantic a partir de OpenAPI schemas

**Steps**:
1. Criar script `generate_schemas.py` usando datamodel-code-generator
2. Processar OpenAPI components/schemas
3. Gerar arquivos Python em `schemas/` (auto-generated)
4. Adicionar header "DO NOT EDIT" em arquivos gerados
5. Criar `schemas/__init__.py` com exports
6. Validar que modelos são type-safe

**Acceptance Criteria**:
- ✅ Schemas gerados em `src/mcp_server/schemas/`
- ✅ Modelos Pydantic type-safe e validáveis
- ✅ Generation script executável
- ✅ Schemas commitados no repo

**Parallel**: ✅ [P] (depende de T007 mas paralelo com T008)

---

### T010: Implementar validação de schemas

**User Story**: Foundational  
**File**: `src/mcp_server/openapi/validator.py`  
**Description**: Validação de parâmetros usando jsonschema + Pydantic

**Steps**:
1. Criar `openapi/validator.py` com funções de validação
2. Implementar validação contra request_schema (jsonschema)
3. Implementar validação contra response_schema
4. Gerar mensagens de erro detalhadas listando campos faltantes/inválidos
5. Garantir overhead <10ms (constitutional requirement)
6. Adicionar suporte a validação de pagination params

**Acceptance Criteria**:
- ✅ Validação de parâmetros funcional
- ✅ Overhead de validação <10ms
- ✅ Erros detalhados com campos específicos
- ✅ Suporta validação dinâmica de qualquer schema

**Parallel**: ✅ [P] (depende de T007 mas paralelo com T008)

---

### T011: Implementar geração de embeddings

**User Story**: Foundational  
**File**: `scripts/generate_embeddings.py`, `src/mcp_server/vector_db/embeddings.py`  
**Description**: Gerar embeddings ML para todas as operações

**Steps**:
1. Criar `vector_db/embeddings.py` com sentence-transformers
2. Baixar modelo `all-MiniLM-L6-v2` (384 dims)
3. Criar script `generate_embeddings.py`
4. Para cada operação: concatenar description + examples → gerar embedding
5. Popular tabela `embeddings` no SQLite
6. Adicionar metadata: model_name, model_version
7. Validar que todos os embeddings têm 384 dimensões

**Acceptance Criteria**:
- ✅ Modelo ML baixado e cached
- ✅ Embeddings gerados para ~150-300 operações
- ✅ Embeddings salvos no SQLite
- ✅ Todos os vetores têm 384 dimensões

**Parallel**: ❌ (depende de T008)

---

### T012: Implementar busca semântica por similaridade

**User Story**: Foundational  
**File**: `src/mcp_server/vector_db/search.py`  
**Description**: Motor de busca semântica usando embeddings

**Steps**:
1. Criar `vector_db/search.py` com função de busca
2. Implementar cálculo de cosine similarity
3. Aplicar threshold 0.7 para filtragem
4. Ordenar resultados por similarity_score DESC
5. Implementar pagination dos resultados
6. Otimizar para <100ms de latência

**Acceptance Criteria**:
- ✅ Busca semântica funcional
- ✅ Threshold 0.7 aplicado corretamente
- ✅ Resultados ordenados por relevância
- ✅ Latência <100ms

**Parallel**: ❌ (depende de T011)

---

### T013: Implementar rate limiting por cliente

**User Story**: Foundational  
**File**: `src/mcp_server/utils/rate_limit.py`  
**Description**: Rate limiting básico usando slowapi (100 req/min por cliente)

**Steps**:
1. Criar `utils/rate_limit.py` com configuração slowapi
2. Implementar rate limiter in-memory
3. Extrair client ID do contexto MCP
4. Configurar limite padrão: 100 req/min (configurável via RATE_LIMIT_RPM)
5. Retornar HTTP 429 com header Retry-After
6. Adicionar métricas de rate limit hits

**Acceptance Criteria**:
- ✅ Rate limiting funcional por cliente
- ✅ 100 req/min padrão configurável
- ✅ HTTP 429 retornado quando excedido
- ✅ Retry-After header presente

**Parallel**: ✅ [P] (independente de outras foundational tasks)

---

### T013a: Implementar cliente AMQP com pika

**User Story**: Foundational  
**File**: `src/mcp_server/amqp/client.py`  
**Description**: Cliente AMQP para operações de protocolo não cobertas pela HTTP API

**Steps**:
1. Criar `amqp/client.py` com classe AmqpClient usando pika
2. Implementar connection pooling para AMQP
3. Configurar autenticação (username/password de env vars)
4. Implementar channel management
5. Adicionar health checks de conexão AMQP
6. Configurar timeout de 30 segundos para operações
7. Implementar fail-fast (sem retry automático)

**Acceptance Criteria**:
- ✅ Cliente AMQP async funcional com pika
- ✅ Connection pooling implementado
- ✅ Autenticação via env vars
- ✅ Timeout de 30s respeitado
- ✅ Fail-fast implementado

**Parallel**: ✅ [P] (independente de HTTP operations)

---

### T013b: Implementar schemas AMQP manuais

**User Story**: Foundational  
**File**: `src/mcp_server/schemas/amqp_operations.py`  
**Description**: Schemas Pydantic para operações AMQP (não geradas por OpenAPI)

**Steps**:
1. Criar `schemas/amqp_operations.py` com modelos Pydantic
2. Definir PublishMessageSchema (exchange, routing_key, body, properties)
3. Definir ConsumeMessageSchema (queue, consumer_tag, auto_ack)
4. Definir AckMessageSchema (delivery_tag, multiple)
5. Definir NackMessageSchema (delivery_tag, multiple, requeue)
6. Definir RejectMessageSchema (delivery_tag, requeue)
7. Adicionar documentação de cada campo

**Acceptance Criteria**:
- ✅ Schemas AMQP completos e validáveis
- ✅ Todos os campos documentados
- ✅ Tipos de dados corretos
- ✅ Validação com Pydantic funcional

**Parallel**: ✅ [P] (independente de cliente AMQP)

---

### T013c: Adicionar operações AMQP ao registry

**User Story**: Foundational  
**File**: `scripts/register_amqp_operations.py`, `src/mcp_server/openapi/operation_registry.py`  
**Description**: Registrar operações AMQP no SQLite para descoberta via search-ids

**Steps**:
1. Criar script `register_amqp_operations.py`
2. Definir operation IDs: amqp.publish, amqp.consume, amqp.ack, amqp.nack, amqp.reject
3. Criar namespace "amqp" no registry
4. Popular metadados: description, examples, parameters
5. Linkar schemas manuais (T013b) aos operation IDs
6. Adicionar flag is_amqp=true para diferenciar de HTTP ops
7. Executar script durante build/setup

**Acceptance Criteria**:
- ✅ 5 operações AMQP registradas no SQLite
- ✅ Namespace "amqp" criado
- ✅ Metadados completos e precisos
- ✅ Schemas linkados corretamente

**Parallel**: ❌ (depende de T008 e T013b)

---

### T013d: Adicionar operações AMQP ao vector database

**User Story**: Foundational  
**File**: `scripts/generate_embeddings.py` (atualização)  
**Description**: Gerar embeddings para operações AMQP para busca semântica

**Steps**:
1. Atualizar `generate_embeddings.py` para incluir AMQP
2. Para cada operação AMQP: criar description rica otimizada para busca semântica
3. amqp.publish: "Publish message to exchange with routing key" (queries esperadas: "send message", "publish to exchange", "post to rabbitmq")
4. amqp.consume: "Subscribe to queue and receive messages" (queries esperadas: "consume queue", "listen to messages", "receive from queue")
5. amqp.ack: "Acknowledge message processing success" (queries esperadas: "acknowledge message", "confirm processing", "ack message")
6. amqp.nack: "Negative acknowledge - trigger retry or DLQ" (queries esperadas: "reject message", "nack message", "retry failed message")
7. amqp.reject: "Reject message - send to DLQ immediately" (queries esperadas: "reject message", "send to dlq", "discard message")
8. Gerar embeddings e adicionar ao SQLite

**Acceptance Criteria**:
- ✅ Embeddings gerados para 5 operações AMQP
- ✅ Descriptions otimizadas para busca semântica
- ✅ Embeddings adicionados ao vector database
- ✅ Busca por "publish message" retorna amqp.publish

**Parallel**: ❌ (depende de T011 e T013c)

---

### T013e: Implementar executores de operações AMQP

**User Story**: Foundational  
**File**: `src/mcp_server/operations/amqp.py`  
**Description**: Implementar execução de operações AMQP via call-id tool

**Steps**:
1. Criar `operations/amqp.py` com classe AmqpExecutor
2. Implementar execute_publish (basic_publish via pika)
3. Implementar execute_consume (basic_consume com callback)
4. Implementar execute_ack (basic_ack)
5. Implementar execute_nack (basic_nack)
6. Implementar execute_reject (basic_reject)
7. Integrar com call-id tool via operation registry
8. Adicionar error handling específico AMQP

**Acceptance Criteria**:
- ✅ 5 operações AMQP executáveis
- ✅ Integração com call-id funcional
- ✅ Error handling robusto
- ✅ Validação de parâmetros funcional

**Parallel**: ❌ (depende de T013a e T013c)

---

### T013f: Escrever testes de integração AMQP

**User Story**: Foundational  
**File**: `tests/integration/test_amqp_operations.py`  
**Description**: Testes end-to-end com RabbitMQ via AMQP

**Steps**:
1. Criar fixture de RabbitMQ container para AMQP
2. Testar amqp.publish envia mensagem corretamente
3. Testar amqp.consume recebe mensagem
4. Testar amqp.ack confirma processamento
5. Testar amqp.nack move para retry ou DLQ
6. Testar amqp.reject move para DLQ imediatamente
7. Validar mensagens realmente trafegam via AMQP
8. Cleanup automático após testes

**Acceptance Criteria**:
- ✅ Testes AMQP funcionais com RabbitMQ real
- ✅ Publish/consume testados end-to-end
- ✅ Ack/nack/reject testados
- ✅ Cleanup automático

**Parallel**: ✅ [P] (independente de outras tasks de teste)

---

⚠️ **CHECKPOINT FOUNDATIONAL + AMQP**: Todas as tasks T007-T013f devem estar completas antes de iniciar User Stories. **TDD OBRIGATÓRIO**: Escrever testes (T013f) ANTES de implementar executores (T013e).

---

## Phase 3: User Story 1 - Descobrir Operações Disponíveis (P1)

**Goal**: Implementar busca semântica de operações via ferramenta `search-ids`  
**Duration**: 2-3 dias  
**Prerequisites**: Phase 2 completa  
**Priority**: P1 (Crítico - sem isso, usuários não podem navegar pelas capacidades)

🔍 **User Story**: Como desenvolvedor integrando com RabbitMQ, preciso buscar operações relevantes usando linguagem natural, para que eu possa encontrar rapidamente a funcionalidade que preciso sem conhecer todos os endpoints disponíveis.

**Independent Test Criteria**: Enviar consultas em linguagem natural (ex: "listar filas") e verificar se operações relevantes são retornadas com descrições claras.

⚠️ **TDD CHECKPOINT US1**: Para cada task de implementação (T014-T018), escrever testes PRIMEIRO (T019-T021) antes de implementar a funcionalidade. Red → Green → Refactor.

### T014: Implementar ferramenta search-ids - interface MCP

**User Story**: US1  
**File**: `src/mcp_server/tools/search_ids.py`  
**Description**: Implementar interface MCP da ferramenta search-ids

**Steps**:
1. Criar `tools/search_ids.py` com classe SearchIdsTool
2. Implementar schema de input conforme contract (query, pagination)
3. Implementar schema de output (items, pagination metadata)
4. Registrar tool no MCP server
5. Validar inputs usando Pydantic
6. Adicionar documentação da ferramenta

**Acceptance Criteria**:
- ✅ Tool registrada no MCP server
- ✅ Input schema validado
- ✅ Output schema conforme contrato
- ✅ Documentação completa

**Parallel**: ❌ (primeira task da US1)

---

### T015: Conectar search-ids ao motor de busca semântica

**User Story**: US1  
**File**: `src/mcp_server/tools/search_ids.py`  
**Description**: Integrar busca semântica ao tool search-ids

**Steps**:
1. Importar `vector_db/search.py`
2. Converter query em embedding usando modelo ML
3. Executar busca por similaridade
4. Filtrar resultados com threshold 0.7
5. Aplicar pagination aos resultados
6. Formatar response conforme schema

**Acceptance Criteria**:
- ✅ Query convertida em embedding
- ✅ Busca semântica executada
- ✅ Resultados filtrados e paginados
- ✅ Response formatado corretamente

**Parallel**: ❌ (depende de T014)

---

### T016: Adicionar parameter hints aos resultados

**User Story**: US1  
**File**: `src/mcp_server/tools/search_ids.py`  
**Description**: Gerar hints de parâmetros principais para cada resultado

**Steps**:
1. Para cada operação encontrada, carregar request_schema
2. Extrair campos obrigatórios (required)
3. Extrair 2-3 campos opcionais mais importantes
4. Formatar como string: "vhost (required), page, pageSize"
5. Limitar a 100 caracteres
6. Adicionar ao campo `parameter_hint`

**Acceptance Criteria**:
- ✅ Parameter hints gerados para todos os resultados
- ✅ Campos obrigatórios marcados como "(required)"
- ✅ Hints limitados a 100 caracteres
- ✅ Hints são informativos e úteis

**Parallel**: ✅ [P] (pode rodar em paralelo com T017)

---

### T017: Adicionar tratamento de erros ao search-ids

**User Story**: US1  
**File**: `src/mcp_server/tools/search_ids.py`  
**Description**: Implementar error handling robusto para search-ids

**Steps**:
1. Validar query length (min: 3, max: 200)
2. Validar pagination params (page >= 1, pageSize 1-25)
3. Capturar erro de vector database unavailable
4. Retornar erros no formato JSON-RPC 2.0
5. Usar códigos de erro corretos (-32602, -32603)
6. Adicionar logging estruturado de erros

**Acceptance Criteria**:
- ✅ Validação de inputs completa
- ✅ Erros formatados como JSON-RPC 2.0
- ✅ Códigos de erro corretos
- ✅ Erros logados estruturadamente

**Parallel**: ✅ [P] (pode rodar em paralelo com T016)

---

### T018: Otimizar performance do search-ids

**User Story**: US1  
**File**: `src/mcp_server/tools/search_ids.py`, `src/mcp_server/vector_db/search.py`  
**Description**: Otimizar para latência <100ms por página

**Steps**:
1. Adicionar cache de embeddings de queries comuns (TTL 5min)
2. Otimizar cálculo de cosine similarity (numpy vectorization)
3. Implementar early exit se threshold não atingido
4. Adicionar índices SQLite otimizados
5. Medir latência com OpenTelemetry spans
6. Validar que 95% das buscas são <100ms

**Acceptance Criteria**:
- ✅ Latência <100ms para 95% das queries
- ✅ Cache funcional com TTL
- ✅ Métricas de latência disponíveis
- ✅ Otimizações validadas com testes de performance

**Parallel**: ✅ [P] (pode rodar em paralelo com T019)

---

### T019: Escrever testes unitários para search-ids

**User Story**: US1  
**File**: `tests/unit/test_search_ids.py`  
**Description**: Cobertura de testes para search-ids tool

**Steps**:
1. Criar fixtures de operações e embeddings mock
2. Testar busca com query válida retorna resultados
3. Testar threshold filtering (apenas >= 0.7)
4. Testar ordenação por similarity_score DESC
5. Testar pagination funciona corretamente
6. Testar validação de inputs (query length, pageSize)
7. Testar erros (query muito curta, vector db unavailable)
8. Atingir cobertura >80%

**Acceptance Criteria**:
- ✅ Cobertura de testes >80%
- ✅ Todos os cenários de sucesso testados
- ✅ Todos os cenários de erro testados
- ✅ Testes executam em <5s

**Parallel**: ✅ [P] (independente de otimizações)

---

### T019.1: Escrever teste específico de threshold 0.7

**User Story**: US1  
**File**: `tests/unit/test_search_ids_threshold.py`  
**Description**: Validar que threshold 0.7 de similaridade é aplicado corretamente (FR-006)

**Steps**:
1. Criar fixtures com queries de diferentes similaridades
2. Query "criar fila" → validar "queues.create" score ≥0.7 (esperado ~0.95) ACEITO
3. Query "criar fila" → validar "users.create" score <0.7 (esperado ~0.32) REJEITADO
4. Query irrelevante "xyz123" → validar retorna lista vazia
5. Validar que todos os resultados retornados têm score ≥0.7
6. Testar queries com exatamente threshold 0.7 (boundary test)
7. Testar comportamento quando 0 resultados acima threshold (sugestão: "Try broader search terms")

**Acceptance Criteria**:
- ✅ Threshold 0.7 aplicado corretamente a todas as queries
- ✅ Scores testados com exemplos reais (conforme FR-006)
- ✅ Boundary cases testados (score = 0.7 exato)
- ✅ Zero results retorna sugestão útil

**Parallel**: ✅ [P] (independente de T020)

---

### T020: Escrever testes de integração para search-ids

**User Story**: US1  
**File**: `tests/integration/test_search_ids_integration.py`  
**Description**: Testes end-to-end com database real

**Steps**:
1. Criar fixture de SQLite database populado
2. Testar busca por "list queues" retorna operações de filas
3. Testar busca por "create exchange" retorna operações de exchanges
4. Testar busca genérica retorna múltiplos namespaces
5. Testar busca sem resultados (query irrelevante)
6. Testar pagination com múltiplas páginas
7. Validar performance com database real

**Acceptance Criteria**:
- ✅ Integração com SQLite funcional
- ✅ Cenários de uso real testados
- ✅ Pagination testada com dados reais
- ✅ Performance validada

**Parallel**: ✅ [P] (independente de testes unitários)

---

### T021: Escrever testes de contrato MCP para search-ids

**User Story**: US1  
**File**: `tests/contract/test_search_ids_contract.py`  
**Description**: Validar compliance com protocolo MCP

**Steps**:
1. Validar tool registration no MCP server
2. Validar input schema é JSON Schema válido
3. Validar output schema é JSON Schema válido
4. Validar request/response seguem JSON-RPC 2.0
5. Validar códigos de erro seguem padrão MCP
6. Validar examples do contrato funcionam
7. Comparar com `contracts/search-ids.json`

**Acceptance Criteria**:
- ✅ 100% compliance com MCP protocol
- ✅ Schemas válidos
- ✅ Examples executam com sucesso
- ✅ Contrato JSON validado

**Parallel**: ✅ [P] (independente de outros testes)

---

⚠️ **CHECKPOINT US1**: Todas as tasks T014-T021 devem estar completas e testes passando antes de iniciar User Story 2.

---

## Phase 4: User Story 2 - Obter Detalhes de Operação (P1)

**Goal**: Implementar consulta de documentação via ferramenta `get-id`  
**Duration**: 1-2 dias  
**Prerequisites**: Phase 2 e US1 completas  
**Priority**: P1 (Crítico - usuários precisam entender operações antes de executar)

📋 **User Story**: Como desenvolvedor, preciso consultar a documentação completa e esquema de parâmetros de uma operação específica, para que eu possa entender exatamente como utilizá-la antes de executá-la.

**Independent Test Criteria**: Solicitar detalhes de uma operação conhecida e verificar se esquema de parâmetros, tipos de dados e documentação são retornados.

⚠️ **TDD CHECKPOINT US2**: Escrever testes (T025-T026) ANTES de implementar cache e otimizações (T024). Red → Green → Refactor.

### T022: Implementar ferramenta get-id - interface MCP

**User Story**: US2  
**File**: `src/mcp_server/tools/get_id.py`  
**Description**: Implementar interface MCP da ferramenta get-id

**Steps**:
1. Criar `tools/get_id.py` com classe GetIdTool
2. Implementar schema de input (endpoint_id)
3. Validar endpoint_id pattern: `^[a-z-]+\.[a-z-]+$`
4. Implementar schema de output conforme contract
5. Registrar tool no MCP server
6. Adicionar documentação da ferramenta

**Acceptance Criteria**:
- ✅ Tool registrada no MCP server
- ✅ Input validation funcional
- ✅ Output schema conforme contrato
- ✅ Pattern validation de endpoint_id

**Parallel**: ❌ (primeira task da US2)

---

### T023: Conectar get-id ao operation registry

**User Story**: US2  
**File**: `src/mcp_server/tools/get_id.py`  
**Description**: Buscar operação no registry e retornar detalhes completos

**Steps**:
1. Importar `operation_registry.py`
2. Buscar operação por ID no SQLite
3. Carregar request_schema e response_schema
4. Carregar examples se disponíveis
5. Carregar error_scenarios comuns
6. Formatar response completo
7. Retornar erro -32601 se operação não existe

**Acceptance Criteria**:
- ✅ Operação buscada corretamente no registry
- ✅ Schemas carregados e formatados
- ✅ Examples incluídos quando disponíveis
- ✅ Erro claro para operação inexistente

**Parallel**: ❌ (depende de T022)

---

### T024: Implementar cache de detalhes de operação

**User Story**: US2  
**File**: `src/mcp_server/tools/get_id.py`  
**Description**: Cache em memória com TTL de 5 minutos

**Steps**:
1. Criar cache dictionary thread-safe (asyncio.Lock)
2. Cache key: endpoint_id
3. Cache value: operation details completo
4. TTL: 5 minutos (300 segundos)
5. Invalidar cache automaticamente após TTL
6. Adicionar métricas de cache hits/misses

**Acceptance Criteria**:
- ✅ Cache funcional e thread-safe
- ✅ TTL de 5 minutos respeitado
- ✅ Métricas de cache disponíveis
- ✅ Performance melhorada para operações frequentes

**Parallel**: ✅ [P] (pode rodar em paralelo com T025)

---

### T025: Escrever testes unitários para get-id

**User Story**: US2  
**File**: `tests/unit/test_get_id.py`  
**Description**: Cobertura de testes para get-id tool

**Steps**:
1. Criar fixtures de operation registry mock
2. Testar busca por operação válida retorna detalhes
3. Testar schemas são retornados corretamente
4. Testar examples são incluídos
5. Testar erro para endpoint_id inválido (pattern)
6. Testar erro para operação não encontrada (-32601)
7. Testar cache hits e misses
8. Atingir cobertura >80%

**Acceptance Criteria**:
- ✅ Cobertura >80%
- ✅ Cenários de sucesso testados
- ✅ Cenários de erro testados
- ✅ Cache behavior validado

**Parallel**: ✅ [P] (independente de cache implementation)

---

### T026: Escrever testes de contrato MCP para get-id

**User Story**: US2  
**File**: `tests/contract/test_get_id_contract.py`  
**Description**: Validar compliance com protocolo MCP

**Steps**:
1. Validar tool registration
2. Validar input/output schemas
3. Validar JSON-RPC 2.0 compliance
4. Validar códigos de erro
5. Validar examples do contract funcionam
6. Comparar com `contracts/get-id.json`
7. Validar latência <50ms (target do contract)

**Acceptance Criteria**:
- ✅ 100% MCP compliance
- ✅ Schemas válidos
- ✅ Examples funcionam
- ✅ Latência <50ms validada

**Parallel**: ✅ [P] (independente de testes unitários)

---

⚠️ **CHECKPOINT US2**: Todas as tasks T022-T026 devem estar completas e testes passando antes de iniciar User Story 3.

---

## Phase 5: User Story 3 - Executar Operações RabbitMQ (P1)

**Goal**: Implementar execução validada de operações via ferramenta `call-id`  
**Duration**: 3-4 dias  
**Prerequisites**: Phase 2, US1, US2 completas  
**Priority**: P1 (Crítico - funcionalidade principal de valor)

⚡ **User Story**: Como desenvolvedor, preciso executar operações RabbitMQ passando parâmetros validados, para que eu possa gerenciar recursos (filas, exchanges, bindings) de forma programática e confiável.

**Independent Test Criteria**: Executar operações conhecidas com parâmetros válidos e verificar se ações são realizadas no RabbitMQ e resultados corretos são retornados.

⚠️ **TDD CHECKPOINT US3**: Escrever testes (T036-T039) ANTES de implementar funcionalidades (T027-T035). Para cada componente: escrever teste unitário → implementar → validar teste de integração. Red → Green → Refactor.

### T027: Implementar ferramenta call-id - interface MCP

**User Story**: US3  
**File**: `src/mcp_server/tools/call_id.py`  
**Description**: Implementar interface MCP da ferramenta call-id

**Steps**:
1. Criar `tools/call_id.py` com classe CallIdTool
2. Implementar schema de input (endpoint_id, params, pagination)
3. Validar endpoint_id pattern
4. Implementar schema de output (result, metadata)
5. Registrar tool no MCP server
6. Adicionar documentação da ferramenta

**Acceptance Criteria**:
- ✅ Tool registrada no MCP server
- ✅ Input schemas definidos
- ✅ Output schema com result + metadata
- ✅ Documentação completa

**Parallel**: ❌ (primeira task da US3)

---

### T028: Implementar cliente HTTP RabbitMQ

**User Story**: US3  
**File**: `src/mcp_server/operations/executor.py`  
**Description**: Cliente async HTTP para RabbitMQ Management API

**Steps**:
1. Criar `operations/executor.py` com classe BaseExecutor
2. Configurar httpx.AsyncClient com connection pooling
3. Implementar autenticação básica (username/password)
4. Configurar timeout de 30 segundos
5. Implementar retry lógica (fail-fast: sem retry automático)
6. Adicionar logging de requisições
7. Adicionar OpenTelemetry spans para cada chamada

**Acceptance Criteria**:
- ✅ Cliente HTTP async funcional
- ✅ Autenticação configurada
- ✅ Timeout de 30s respeitado
- ✅ Fail-fast (sem retry) implementado

**Parallel**: ❌ (depende de T027)

---

### T029: Implementar validação de parâmetros pré-execução

**User Story**: US3  
**File**: `src/mcp_server/tools/call_id.py`  
**Description**: Validar params contra request_schema antes de executar

**Steps**:
1. Buscar operação no registry
2. Carregar request_schema
3. Validar params usando `validator.py`
4. Validar campos obrigatórios estão presentes
5. Validar tipos de dados
6. Gerar erro detalhado listando missing/invalid fields
7. Garantir validação em <10ms

**Acceptance Criteria**:
- ✅ Validação completa pré-execução
- ✅ Erro detalhado com fields missing/invalid
- ✅ Validação em <10ms
- ✅ Nenhuma tentativa de execução se validação falhar

**Parallel**: ✅ [P] (pode rodar em paralelo com T028)

---

### T030: Conectar call-id ao executor de operações

**User Story**: US3  
**File**: `src/mcp_server/tools/call_id.py`, `src/mcp_server/operations/executor.py`  
**Description**: Executar operação RabbitMQ via HTTP API

**Steps**:
1. Buscar operação no registry
2. Validar params (T029)
3. Construir HTTP request (method, path, body)
4. Substituir path params (ex: {vhost})
5. Executar via BaseExecutor
6. Capturar response ou erro
7. Validar response contra response_schema
8. Formatar resultado final

**Acceptance Criteria**:
- ✅ Operação executada no RabbitMQ
- ✅ Path params substituídos corretamente
- ✅ Response validado contra schema
- ✅ Resultado formatado conforme output schema

**Parallel**: ❌ (depende de T028 e T029)

---

### T031: Implementar tratamento de timeouts

**User Story**: US3  
**File**: `src/mcp_server/operations/executor.py`  
**Description**: Abortar operações que excedem 30 segundos

**Steps**:
1. Adicionar timeout de 30s em httpx.AsyncClient
2. Capturar httpx.TimeoutException
3. Retornar erro -32001 (Timeout error)
4. Incluir detalhes: operation_id, timeout_seconds
5. Adicionar sugestão de resolução
6. Logar timeout events

**Acceptance Criteria**:
- ✅ Timeouts detectados corretamente
- ✅ Erro -32001 retornado
- ✅ Mensagem descritiva com sugestões
- ✅ Operação abortada após 30s

**Parallel**: ✅ [P] (pode rodar em paralelo com T032)

---

### T032: Implementar tratamento de erros de conexão

**User Story**: US3  
**File**: `src/mcp_server/operations/executor.py`  
**Description**: Fail-fast para erros de conexão com RabbitMQ

**Steps**:
1. Capturar erros de conexão (httpx.ConnectError, etc)
2. Retornar erro -32000 (Server error)
3. Incluir detalhes: rabbitmq_host, reason
4. Adicionar resolução sugerida
5. Não implementar retry automático (fail-fast)
6. Logar connection errors

**Acceptance Criteria**:
- ✅ Erros de conexão detectados
- ✅ Erro -32000 retornado
- ✅ Fail-fast (sem retry)
- ✅ Mensagem descritiva

**Parallel**: ✅ [P] (pode rodar em paralelo com T031)

---

### T033: Implementar tratamento de respostas malformadas

**User Story**: US3  
**File**: `src/mcp_server/operations/executor.py`  
**Description**: Detectar e reportar respostas em formato inesperado

**Steps**:
1. Validar response é JSON válido
2. Validar response contra response_schema
3. Capturar erros de parsing (json.JSONDecodeError)
4. Capturar erros de validação (jsonschema.ValidationError)
5. Retornar erro descritivo sem expor stack traces
6. Logar parsing errors para debug

**Acceptance Criteria**:
- ✅ Respostas inválidas detectadas
- ✅ Erro descritivo retornado
- ✅ Stack traces não expostos ao cliente
- ✅ Errors logados para troubleshooting

**Parallel**: ✅ [P] (pode rodar em paralelo com T034)

---

### T034: Adicionar metadata de execução às respostas

**User Story**: US3  
**File**: `src/mcp_server/tools/call_id.py`  
**Description**: Incluir informações úteis de debug e observability

**Steps**:
1. Capturar timestamp de início e fim
2. Calcular duration_ms
3. Incluir operation_id executado
4. Incluir OpenTelemetry trace_id
5. Adicionar status (success/error/timeout)
6. Formatar metadata section na response

**Acceptance Criteria**:
- ✅ Metadata incluído em todas as responses
- ✅ duration_ms preciso
- ✅ trace_id correlacionável com logs
- ✅ Status claro

**Parallel**: ✅ [P] (pode rodar em paralelo com T035)

---

### T035: Implementar suporte a pagination em operações

**User Story**: US3  
**File**: `src/mcp_server/tools/call_id.py`  
**Description**: Suporte a pagination para operações de listagem

**Steps**:
1. Detectar se operação suporta pagination (flag no registry)
2. Aceitar pagination params (page, pageSize)
3. Validar pageSize <= 200 (constitutional limit)
4. Adicionar params ao request RabbitMQ
5. Formatar response paginada com metadata
6. Incluir hasNextPage, hasPreviousPage

**Acceptance Criteria**:
- ✅ Pagination funcional para operações que suportam
- ✅ pageSize limitado a 200
- ✅ Metadata de pagination completo
- ✅ Navegação entre páginas funcional

**Parallel**: ✅ [P] (independente de outros tratamentos de erro)

---

### T035.1: Escrever teste de timeout + pagination para listagens grandes

**User Story**: US3  
**File**: `tests/integration/test_call_id_large_lists.py`  
**Description**: Validar timeout 30s com pagination obrigatória para listagens >1000 items ou >50MB (FR-014)

**Steps**:
1. Criar fixture de RabbitMQ com >1000 filas simuladas
2. Testar listagem sem pagination → validar pageSize forçado ≤200
3. Testar que operação completa dentro de 30s com pagination
4. Testar que timeout é respeitado (aborta após 30s se não usar pagination)
5. Validar metadata de pagination correto (hasNextPage, totalItems)
6. Testar com diferentes tamanhos de resposta (10MB, 50MB, >50MB)
7. Validar erro claro quando timeout ocorre

**Acceptance Criteria**:
- ✅ Listagens grandes (>1000 items) forçam pagination pageSize≤200
- ✅ Timeout 30s respeitado com pagination
- ✅ Metadata de pagination completo e correto
- ✅ Erro de timeout claro e descritivo

**Parallel**: ✅ [P] (independente de T036)

---

### T036: Escrever testes unitários para call-id

**User Story**: US3  
**File**: `tests/unit/test_call_id.py`  
**Description**: Cobertura de testes para call-id tool

**Steps**:
1. Criar fixtures de RabbitMQ API mock
2. Testar execução com params válidos retorna sucesso
3. Testar validação pré-execução detecta params inválidos
4. Testar timeout após 30s
5. Testar erro de conexão retorna -32000
6. Testar resposta malformada é detectada
7. Testar metadata é incluído corretamente
8. Testar pagination params funcionam
9. Atingir cobertura >80%

**Acceptance Criteria**:
- ✅ Cobertura >80%
- ✅ Todos os cenários testados
- ✅ Mocks realistas de RabbitMQ API
- ✅ Edge cases cobertos

**Parallel**: ✅ [P] (pode começar após T027 estar completo)

---

### T037: Escrever testes de integração com RabbitMQ real

**User Story**: US3  
**File**: `tests/integration/test_call_id_rabbitmq.py`  
**Description**: Testes end-to-end com RabbitMQ em container

**Steps**:
1. Criar fixture de RabbitMQ container (testcontainers)
2. Testar criar fila e verificar no RabbitMQ
3. Testar criar exchange e verificar
4. Testar criar binding e verificar
5. Testar listar recursos criados
6. Testar deletar recursos
7. Validar operações realmente executam no RabbitMQ
8. Cleanup automático após testes

**Acceptance Criteria**:
- ✅ RabbitMQ container funcional
- ✅ Operações realmente executadas
- ✅ Resultados verificáveis no RabbitMQ
- ✅ Cleanup automático

**Parallel**: ❌ (requer infraestrutura de testes configurada)

---

### T038: Escrever testes de contrato MCP para call-id

**User Story**: US3  
**File**: `tests/contract/test_call_id_contract.py`  
**Description**: Validar compliance com protocolo MCP

**Steps**:
1. Validar tool registration
2. Validar input/output schemas
3. Validar JSON-RPC 2.0 compliance
4. Validar todos os códigos de erro (-32602, -32000, -32001)
5. Validar examples funcionam (se disponíveis)
6. Validar latência dentro de limites

**Acceptance Criteria**:
- ✅ 100% MCP compliance
- ✅ Todos os error codes validados
- ✅ Schemas válidos
- ✅ Performance dentro de limites

**Parallel**: ✅ [P] (independente de testes de integração)

---

### T039: Escrever testes de performance para call-id

**User Story**: US3  
**File**: `tests/integration/test_call_id_performance.py`  
**Description**: Validar métricas de performance (<200ms, <10ms validation)

**Steps**:
1. Testar validação é <10ms (95th percentile)
2. Testar operação básica é <200ms
3. Testar concorrência (múltiplas requisições simultâneas)
4. Testar uso de memória é <1GB
5. Testar rate limiting funciona corretamente
6. Gerar relatório de performance

**Acceptance Criteria**:
- ✅ Validação <10ms confirmada
- ✅ Operação básica <200ms confirmada
- ✅ Concorrência funcional
- ✅ Uso de memória <1GB

**Parallel**: ✅ [P] (independente de outros testes)

---

⚠️ **CHECKPOINT US3**: Todas as tasks T027-T039 devem estar completas e testes passando antes de iniciar User Story 4.

---

## Phase 6: User Story 4 - Receber Feedback Claro de Erros (P2)

**Goal**: Padronizar e melhorar mensagens de erro em todas as ferramentas  
**Duration**: 1 dia  
**Prerequisites**: US1, US2, US3 completas  
**Priority**: P2 (Importante para experiência do desenvolvedor)

🛡️ **User Story**: Como desenvolvedor, preciso receber mensagens de erro padronizadas e descritivas quando algo falha, para que eu possa identificar e corrigir problemas rapidamente.

**Independent Test Criteria**: Provocar diferentes tipos de erro (validação, conexão, operação inválida) e verificar se mensagens claras são retornadas.

⚠️ **TDD CHECKPOINT US4**: Escrever testes de error scenarios (T047) ANTES de implementar melhorias (T044-T046). Para cada tipo de erro: escrever teste → implementar mensagem → validar. Red → Green → Refactor.

### T043: Padronizar estrutura de erros JSON-RPC 2.0

**User Story**: US4  
**File**: `src/mcp_server/utils/errors.py`  
**Description**: Criar classes de erro padronizadas para todo o sistema

**Steps**:
1. Criar `utils/errors.py` com classes de erro
2. Definir códigos de erro conforme data-model.md
3. Implementar formatação JSON-RPC 2.0 automática
4. Adicionar campo `data` com detalhes extras
5. Criar helper functions para erro comum patterns
6. Documentar cada código de erro

**Acceptance Criteria**:
- ✅ Classes de erro para cada código (-32700 a -32002)
- ✅ Formatação JSON-RPC 2.0 automática
- ✅ Campo `data` com detalhes úteis
- ✅ Documentação completa

**Parallel**: ❌ (primeira task da US4)

---

### T044: Melhorar mensagens de erro de validação

**User Story**: US4  
**File**: `src/mcp_server/openapi/validator.py`, todas as tools  
**Description**: Erros de validação devem listar especificamente o que está errado

**Steps**:
1. Atualizar validator.py para gerar erros detalhados
2. Listar campos missing explicitamente
3. Listar campos invalid com razão (ex: "pageSize: must be <= 200")
4. Incluir expected_schema no erro quando útil
5. Evitar jargão técnico desnecessário
6. Aplicar em search-ids, get-id, call-id

**Acceptance Criteria**:
- ✅ Erros listam campos missing/invalid especificamente
- ✅ Mensagens são claras e acionáveis
- ✅ Expected schema incluído quando útil
- ✅ Consistente em todas as ferramentas

**Parallel**: ✅ [P] (pode rodar em paralelo com T045)

---

### T045: Adicionar resolução sugerida aos erros

**User Story**: US4  
**File**: Todas as tools e `operations/executor.py`  
**Description**: Erros devem incluir sugestões de como resolver

**Steps**:
1. Adicionar campo `resolution` aos erros
2. Para timeout: "Try with more specific filters"
3. Para conexão: "Check if RabbitMQ is running and credentials are correct"
4. Para validação: "Provide the 'vhost' parameter (e.g., '/' for default)"
5. Para rate limit: "Wait {retry_after} seconds before retrying"
6. Para operação não encontrada: "Use search-ids to find available operations"

**Acceptance Criteria**:
- ✅ Todos os erros incluem resolução sugerida
- ✅ Sugestões são práticas e acionáveis
- ✅ Sugestões contextuais (não genéricas)
- ✅ Consistência em todas as ferramentas

**Parallel**: ✅ [P] (pode rodar em paralelo com T044)

---

### T046: Garantir segurança de mensagens de erro

**User Story**: US4  
**File**: `src/mcp_server/utils/errors.py`, `utils/logging.py`  
**Description**: Erros não devem expor informações sensíveis

**Steps**:
1. Nunca incluir stack traces em erros retornados ao cliente
2. Redatar credenciais e tokens em logs
3. Erros internos (não esperados) devem retornar mensagem genérica
4. Stack traces completos apenas em logs (não no response)
5. Validar que dados sensíveis não aparecem em erros
6. Adicionar testes de segurança

**Acceptance Criteria**:
- ✅ Stack traces não expostos ao cliente
- ✅ Credenciais redatadas em logs
- ✅ Erros internos retornam mensagem segura
- ✅ Testes de segurança passando

**Parallel**: ✅ [P] (pode rodar em paralelo com T047)

---

### T047: Escrever testes de error scenarios

**User Story**: US4  
**File**: `tests/unit/test_error_handling.py`, `tests/integration/test_error_scenarios.py`  
**Description**: Validar todos os cenários de erro documentados

**Steps**:
1. Testar cada código de erro (-32700 a -32002)
2. Validar formato JSON-RPC 2.0
3. Validar mensagens são descritivas
4. Validar detalhes (data field) são úteis
5. Validar sugestões de resolução presentes
6. Validar segurança (sem dados sensíveis)
7. Testar error scenarios de cada acceptance criteria das US
8. **Testar erros internos não-capturados retornam mensagem genérica segura sem stack traces**
9. **Testar que exceções inesperadas (ex: KeyError, AttributeError) são capturadas e sanitizadas**
10. Atingir cobertura completa de error paths

**Acceptance Criteria**:
- ✅ Todos os códigos de erro testados
- ✅ Formato JSON-RPC validado
- ✅ Mensagens validadas
- ✅ Segurança validada
- ✅ Erros internos retornam mensagem genérica (ex: "Internal server error") sem detalhes sensíveis
- ✅ Stack traces nunca expostos ao cliente (apenas em logs)

**Parallel**: ✅ [P] (independente de outras tasks)

---

⚠️ **CHECKPOINT US4**: Todas as tasks T043-T047 devem estar completas antes de prosseguir para console client.

---

## Phase 6.5: Console Client & Multilingual Support (Constitution §VIII)

**Goal**: Implementar console client built-in + suporte a 20 idiomas conforme constitution  
**Duration**: 2-3 semanas  
**Prerequisites**: US1-US4 completas (ferramentas MCP funcionais)  
**Constitution**: §VIII linha 71 (console client obrigatório) + linhas 604-624 (20 idiomas)

🖥️ **Constitution Requirement**: "Every MCP server MUST include a built-in console client" + "MUST be available in the 20 most spoken languages worldwide"

**Architectural Decision**: ADR-002 (supersedes ADR-001) - Console simplificado em MVP para constitution compliance

⚠️ **TDD CHECKPOINT Phase 6.5**: Escrever testes (T067-T068) em paralelo com implementação (T057-T066).

### T057: Implementar CLI framework base com Click

**User Story**: Console Client  
**File**: `cli/main.py`, `cli/__init__.py`  
**Description**: Setup básico do console client usando Click framework

**Steps**:
1. Criar estrutura `cli/` com `main.py`
2. Configurar Click framework para CLI
3. Implementar entrypoint principal (`rabbitmq-mcp` command)
4. Adicionar global options: `--host`, `--user`, `--password`, `--vhost`, `--lang`
5. Implementar help system básico
6. Configurar Rich console para output formatado
7. Adicionar version command (`rabbitmq-mcp --version`)

**Acceptance Criteria**:
- ✅ CLI executável via `rabbitmq-mcp`
- ✅ Global options funcionais
- ✅ Help text gerado automaticamente
- ✅ Version command funcional

**Parallel**: ❌ (primeira task da Phase 6.5)

---

### T058: Implementar comando search

**User Story**: Console Client  
**File**: `cli/commands/search.py`  
**Description**: Comando para busca semântica de operações (wraps search-ids)

**Steps**:
1. Criar `cli/commands/search.py`
2. Implementar `rabbitmq-mcp search "<query>"`
3. Integrar com search-ids MCP tool
4. Formatar resultados em Rich table (operation_id, description, similarity_score)
5. Adicionar pagination support (`--page`, `--page-size`)
6. Adicionar exemplo no help text
7. Implementar error handling com mensagens i18n-ready

**Acceptance Criteria**:
- ✅ Comando funcional: `rabbitmq-mcp search "list queues"`
- ✅ Resultados formatados em table
- ✅ Pagination funcional
- ✅ Error handling claro

**Parallel**: ❌ (depende de T057)

---

### T059: Implementar comando describe

**User Story**: Console Client  
**File**: `cli/commands/describe.py`  
**Description**: Comando para obter detalhes de operação (wraps get-id)

**Steps**:
1. Criar `cli/commands/describe.py`
2. Implementar `rabbitmq-mcp describe <operation-id>`
3. Integrar com get-id MCP tool
4. Formatar output: description, parameters (required/optional), examples
5. Syntax highlighting para JSON schemas (pygments)
6. Adicionar exemplo no help text

**Acceptance Criteria**:
- ✅ Comando funcional: `rabbitmq-mcp describe queues.list`
- ✅ Output formatado e legível
- ✅ JSON highlighting funcional
- ✅ Examples displayed quando disponíveis

**Parallel**: ✅ [P] (pode rodar em paralelo com T060)

---

### T060: Implementar comando execute

**User Story**: Console Client  
**File**: `cli/commands/execute.py`  
**Description**: Comando para executar operações RabbitMQ (wraps call-id)

**Steps**:
1. Criar `cli/commands/execute.py`
2. Implementar `rabbitmq-mcp execute <operation-id> --params '{"vhost": "/"}'`
3. Integrar com call-id MCP tool
4. Parse JSON params de string ou file (`--params-file params.json`)
5. Formatar resultado com Rich (success/error color-coded)
6. Adicionar dry-run mode (`--dry-run` para validar params sem executar)
7. Progress indicator para operações longas

**Acceptance Criteria**:
- ✅ Comando funcional: `rabbitmq-mcp execute queues.list --params '{"vhost": "/"}'`
- ✅ Params via JSON string ou file
- ✅ Dry-run mode funcional
- ✅ Progress indicators para >5s operations

**Parallel**: ✅ [P] (pode rodar em paralelo com T059)

---

### T061: Implementar comando connect (test connection)

**User Story**: Console Client  
**File**: `cli/commands/connect.py`  
**Description**: Comando para testar conectividade com RabbitMQ

**Steps**:
1. Criar `cli/commands/connect.py`
2. Implementar `rabbitmq-mcp connect --host localhost --user guest --password guest`
3. Testar HTTP API connection (Management API health check)
4. Testar AMQP connection (via pika)
5. Exibir status: HTTP API (✓/✗), AMQP (✓/✗), version, uptime
6. Adicionar verbose mode para troubleshooting

**Acceptance Criteria**:
- ✅ Comando testa HTTP + AMQP
- ✅ Status claro (success/failure)
- ✅ Version info displayed
- ✅ Verbose mode para debugging

**Parallel**: ✅ [P] (independente de search/describe/execute)

---

### T062: Implementar framework i18n com gettext

**User Story**: Console Client (i18n)  
**File**: `cli/i18n/`, `setup.py` (i18n config)  
**Description**: Setup gettext para suporte multilingual

**Steps**:
1. Criar estrutura `cli/i18n/`
2. Configurar gettext com babel (extract, init, compile)
3. Criar `messages.pot` template com strings extraídas
4. Implementar wrapper `_()` para strings traduzíveis
5. Configurar locale detection via `locale.getdefaultlocale()`
6. Implementar fallback para English quando tradução ausente
7. Adicionar `--lang` flag para override manual

**Acceptance Criteria**:
- ✅ gettext configurado e funcional
- ✅ Locale detection automática
- ✅ Fallback para English funcional
- ✅ `--lang` override funcional

**Parallel**: ✅ [P] (pode rodar em paralelo com T058-T061)

---

### T063: Criar translation templates (.pot files)

**User Story**: Console Client (i18n)  
**File**: `cli/i18n/messages.pot`  
**Description**: Extrair strings traduzíveis e criar template

**Steps**:
1. Executar `pybabel extract` para coletar strings `_()`
2. Gerar `messages.pot` com ~50-100 strings
3. Categorizar strings: commands, errors, help text, status messages
4. Adicionar contexto para tradutores (comments)
5. Validar que todas as strings user-facing têm `_()` wrapper
6. Documentar processo de atualização de translations

**Acceptance Criteria**:
- ✅ messages.pot gerado com todas as strings
- ✅ ~50-100 strings extraídas
- ✅ Context comments adicionados
- ✅ Processo documentado

**Parallel**: ❌ (depende de T062)

---

### T064: Gerar traduções para 20 idiomas

**User Story**: Console Client (i18n)  
**File**: `cli/i18n/*/LC_MESSAGES/messages.po` (20 idiomas)  
**Description**: Criar arquivos .po para os 20 idiomas obrigatórios

**Steps**:
1. Executar `pybabel init` para cada um dos 20 idiomas (constitution linhas 604-624):
   - en (English - base), zh_CN (Mandarin), hi (Hindi), es (Spanish), fr (French)
   - ar (Arabic), bn (Bengali), ru (Russian), pt (Portuguese), id (Indonesian)
   - ur (Urdu), de (German), ja (Japanese), sw (Swahili), mr (Marathi)
   - te (Telugu), tr (Turkish), ta (Tamil), vi (Vietnamese), it (Italian)
2. Usar machine translation (DeepL API ou Google Translate) para gerar traduções iniciais
3. Marcar traduções como fuzzy para revisão futura
4. Compilar .po → .mo files (`pybabel compile`)
5. Testar que cada idioma carrega sem erros
6. Adicionar README em i18n/ explicando processo de contribuição de traduções

**Acceptance Criteria**:
- ✅ 20 idiomas com .po files completos
- ✅ Machine translation aplicada (fuzzy OK para MVP)
- ✅ .mo files compilados e funcionais
- ✅ Todos os idiomas testados (loadable)

**Parallel**: ❌ (depende de T063)

---

### T065: Implementar locale detection e fallback

**User Story**: Console Client (i18n)  
**File**: `cli/i18n/loader.py`  
**Description**: Sistema robusto de detecção e fallback de idiomas

**Steps**:
1. Criar `cli/i18n/loader.py` com função `load_translations()`
2. Detectar locale via `locale.getdefaultlocale()` ou `LANG` env var
3. Mapear locale para idioma suportado (ex: pt_BR → pt)
4. Fallback hierarchy: locale específico → idioma base → English
5. Testar com todas as 20 locales suportadas
6. Implementar `--lang` override (highest priority)
7. Log de idioma selecionado em debug mode

**Acceptance Criteria**:
- ✅ Locale detection funcional
- ✅ Fallback hierarchy implementada
- ✅ `--lang` override funciona
- ✅ Testado com 20 idiomas

**Parallel**: ✅ [P] (pode rodar em paralelo com T066)

---

### T066: Implementar Rich formatting para console output

**User Story**: Console Client  
**File**: `cli/formatter.py`  
**Description**: Formatação consistente de output usando Rich

**Steps**:
1. Criar `cli/formatter.py` com classes de formatação
2. Implementar table formatter (para search results)
3. Implementar JSON formatter com syntax highlighting
4. Implementar status messages (success: green, error: red, warning: yellow)
5. Implementar progress bars/spinners para long operations
6. Adicionar fallback para ambientes sem color support
7. Configurar via env var: `NO_COLOR` (respeitando standard)

**Acceptance Criteria**:
- ✅ Tables formatadas com Rich
- ✅ JSON syntax highlighting funcional
- ✅ Color-coded messages
- ✅ NO_COLOR respeitado

**Parallel**: ✅ [P] (pode rodar em paralelo com T065)

---

### T067: Escrever testes de console CLI

**User Story**: Console Client  
**File**: `tests/unit/test_cli_commands.py`, `tests/integration/test_cli_e2e.py`  
**Description**: Cobertura completa de testes para comandos CLI

**Steps**:
1. Criar fixtures para CLI testing (Click CliRunner)
2. Testar search command: query válida, pagination, errors
3. Testar describe command: operation válido, operation inexistente
4. Testar execute command: params válidos, params inválidos, dry-run
5. Testar connect command: connection success, connection failure
6. Testar global options: --host, --user, --lang
7. Testar help text de todos os comandos
8. Testes de integração end-to-end com RabbitMQ mock
9. Atingir cobertura >80% para CLI

**Acceptance Criteria**:
- ✅ Todos os 4 comandos testados (search, describe, execute, connect)
- ✅ Global options testados
- ✅ Error scenarios cobertos
- ✅ Cobertura >80% para cli/

**Parallel**: ✅ [P] (pode rodar em paralelo com T068)

---

### T068: Escrever testes de i18n coverage

**User Story**: Console Client (i18n)  
**File**: `tests/unit/test_i18n.py`  
**Description**: Validar que todos os 20 idiomas estão funcionais

**Steps**:
1. Criar teste que valida presença de 20 .po files
2. Testar que cada idioma carrega sem erros
3. Testar locale detection com diferentes env vars (LANG, LC_ALL)
4. Testar fallback hierarchy (specific locale → base lang → English)
5. Testar `--lang` override para todos os idiomas
6. Validar que strings não traduzidas usam English (no crashes)
7. Testar que todos os 20 idiomas têm mesmo número de strings

**Acceptance Criteria**:
- ✅ 20 idiomas validados (loadable)
- ✅ Locale detection testado
- ✅ Fallback hierarchy testado
- ✅ Sem crashes para idiomas incompletos

**Parallel**: ✅ [P] (pode rodar em paralelo com T067)

---

⚠️ **CHECKPOINT Phase 6.5**: Todas as tasks T057-T068 devem estar completas antes de prosseguir para Phase 7 (Polish).

**Constitution Compliance**: ✅ Console client + 20 idiomas implementados conforme §VIII

---

## Phase 7: Polish & Integration

**Goal**: Finalizar integração, documentação e CI/CD  
**Duration**: 2-3 dias  
**Prerequisites**: Todas as User Stories completas

### T048: Configurar CI/CD pipeline

**User Story**: Polish  
**File**: `.github/workflows/ci.yml` (ou similar)  
**Description**: Pipeline automático para testes, linting e validação

**Steps**:
1. Criar workflow de CI
2. Executar testes (unit, integration, contract) em cada PR
3. Executar linting (black, ruff, mypy)
4. Validar cobertura de testes (mínimo 80%)
5. Validar sync OpenAPI → schemas → embeddings
6. Executar scripts de geração em CI para validação
7. Falhar build se qualquer validação falhar

**Acceptance Criteria**:
- ✅ CI executa em cada PR
- ✅ Todos os testes executados
- ✅ Linting validado
- ✅ Cobertura mínima enforced

**Parallel**: ❌ (requer código completo)

---

### T049: Criar documentação de deployment

**User Story**: Polish  
**File**: `docs/DEPLOYMENT.md`, `docs/API.md`, `docs/ARCHITECTURE.md`, `docs/EXAMPLES.md`, README atualizado  
**Description**: Guia completo de deployment, API, arquitetura e exemplos (constitution §VIII)

**Steps**:
1. Criar `docs/DEPLOYMENT.md` com variáveis de ambiente, processo de build (geração schemas/embeddings), deployment em diferentes ambientes, configuração OpenTelemetry, troubleshooting
2. Criar `docs/API.md` com TypeScript interfaces para todas as 3 ferramentas MCP (search-ids, get-id, call-id), lista completa de operation IDs auto-gerados do OpenAPI, schemas de request/response, códigos de erro
3. Criar `docs/ARCHITECTURE.md` com diagramas (semantic discovery pattern, OpenAPI generation flow, ChromaDB integration), decisões arquiteturais (ADRs), justificativa de escolhas técnicas (ChromaDB vs sqlite-vec, threshold 0.7)
4. Criar `docs/EXAMPLES.md` com exemplos TESTADOS: debugging em dev environment, command-line usage (bash, PowerShell), MCP client configuration (Cursor, VS Code), exemplos de queries semânticas comuns
5. Atualizar README principal com overview, quick start, uvx usage examples, link para docs/
6. Validar que TODOS os exemplos em EXAMPLES.md são funcionais e testados

**Acceptance Criteria**:
- ✅ Documentação completa e testada
- ✅ Variáveis de ambiente documentadas
- ✅ Processo de build claro
- ✅ Troubleshooting útil

**Parallel**: ✅ [P] (pode rodar em paralelo com CI/CD)

---

### T050: Validar compliance constitucional final

**User Story**: Polish  
**File**: `tests/contract/test_constitution_compliance.py`  
**Description**: Teste final validando todas as regras da constitution

**Steps**:
1. Criar teste de compliance constitucional
2. Validar apenas 3 tools públicas registradas
3. Validar performance targets (<200ms, <10ms, <100ms, <1GB)
4. Validar rate limiting funcional (100 req/min)
5. Validar embeddings pré-computados (não gerados em runtime)
6. Validar OpenAPI como source of truth
7. Validar MCP protocol compliance completo
8. Validar structured logging e OpenTelemetry

**Acceptance Criteria**:
- ✅ 100% compliance com constitution
- ✅ Todas as métricas de performance atingidas
- ✅ MCP protocol compliance validado
- ✅ Teste documenta compliance

**Parallel**: ✅ [P] (independente de documentação)

---

### T050a: Teste de integração OpenTelemetry end-to-end

**User Story**: Polish  
**File**: `tests/integration/test_opentelemetry_e2e.py`  
**Description**: Validar instrumentação completa de traces, métricas e logs correlacionados

**Steps**:
1. Criar fixture com OTLP collector mock ou real (Jaeger in-memory)
2. Executar operação completa: search-ids → get-id → call-id
3. Validar que trace completo é gerado com spans para cada operação
4. Validar que métricas são exportadas (latência p50/p95/p99, error rate, cache hits/misses ratio)
5. Validar que logs incluem trace_id correlacionado
6. Testar que erros são traceable (100% dos erros têm trace)
7. Validar 95% das operações geram traces completos: executar 100 operações aleatórias, count traces completos (span com operation_id, duration_ms, status), assert ≥95 traces completos. Métrica: (operations_with_complete_trace / total_operations) ≥ 0.95
8. Medir overhead de instrumentação (<5% latency increase)

**Acceptance Criteria**:
- ✅ Traces completos gerados para operações
- ✅ Métricas exportadas corretamente (latência p50/p95/p99, cache ratio)
- ✅ Logs correlacionados com trace IDs
- ✅ 100% dos erros são traceable
- ✅ 95%+ das operações têm traces completos
- ✅ Overhead de instrumentação <5%

**Parallel**: ✅ [P] (independente de outras tasks de teste)

---

### T051: Teste de autenticação RabbitMQ (FR-013)

**User Story**: Polish  
**File**: `tests/integration/test_rabbitmq_authentication.py`  
**Description**: Validar autenticação com credenciais via variáveis de ambiente

**Steps**:
1. Criar fixture com RabbitMQ container e credenciais customizadas
2. Testar autenticação bem-sucedida com credenciais corretas
3. Testar falha de autenticação com credenciais inválidas
4. Testar erro descritivo quando RABBITMQ_USERNAME ausente
5. Testar erro descritivo quando RABBITMQ_PASSWORD ausente
6. Validar que credenciais são carregadas de env vars corretamente
7. Testar autenticação tanto HTTP API quanto AMQP

**Acceptance Criteria**:
- ✅ Autenticação validada para HTTP e AMQP
- ✅ Credenciais carregadas de env vars
- ✅ Erros descritivos para credenciais faltantes/inválidas
- ✅ Cobertura completa de cenários de auth

**Parallel**: ✅ [P] (independente de outras tasks de teste)

---

### T052: Teste de thread-safety do cache (FR-017)

**User Story**: Polish  
**File**: `tests/unit/test_cache_thread_safety.py`  
**Description**: Validar acesso concorrente ao cache com asyncio.Lock

**Steps**:
1. Criar fixtures de cache com asyncio.Lock
2. Testar múltiplas requisições simultâneas (50+ concurrent)
3. Testar cache hits/misses sob concorrência
4. Testar invalidação de cache durante leitura concorrente
5. Testar que não há condições de corrida (race conditions)
6. Testar que dados não são corrompidos sob concorrência
7. Validar que asyncio.Lock é usado corretamente
8. Medir overhead de locks (deve ser <1ms)

**Acceptance Criteria**:
- ✅ Cache funciona corretamente sob alta concorrência
- ✅ Sem race conditions detectadas
- ✅ Dados íntegros após 1000+ operações concorrentes
- ✅ asyncio.Lock implementado e testado
- ✅ Overhead de locks <1ms

**Parallel**: ✅ [P] (independente de outras tasks de teste)

---

### T053: Teste de multi-versão OpenAPI (FR-020)

**User Story**: Polish  
**File**: `tests/integration/test_openapi_versioning.py`  
**Description**: Validar suporte a versões configuráveis de OpenAPI via RABBITMQ_API_VERSION

**Steps**:
1. Criar fixtures com múltiplas versões de OpenAPI (ex: 3.12, 3.13)
2. Testar carregamento de schemas da versão correta
3. Testar que RABBITMQ_API_VERSION seleciona versão correta
4. Testar erro quando versão não suportada é especificada
5. Testar que embeddings são carregados da versão correta
6. Testar que operation registry usa versão correta
7. Validar que uma versão por vez é ativa
8. Documentar versões suportadas no README

**Acceptance Criteria**:
- ✅ Múltiplas versões de OpenAPI suportadas
- ✅ RABBITMQ_API_VERSION seleciona versão corretamente
- ✅ Erro claro para versões não suportadas
- ✅ Apenas uma versão ativa por deploy
- ✅ Documentação de versões suportadas completa

**Parallel**: ✅ [P] (independente de outras tasks de teste)

---

### T054: Teste de identificação de cliente para rate limiting

**User Story**: Polish  
**File**: `tests/unit/test_rate_limit_client_identification.py`  
**Description**: Validar identificação de cliente via connection ID do MCP

**Steps**:
1. Criar fixtures de múltiplos clients MCP
2. Testar que cada client tem rate limit independente
3. Testar extração de connection ID do contexto MCP
4. Testar fallback quando connection ID não disponível
5. Testar que rate limit não afeta clients diferentes
6. Testar que rate limit persiste por client
7. Validar métricas por client

**Acceptance Criteria**:
- ✅ Connection ID extraído corretamente do MCP
- ✅ Rate limit independente por client
- ✅ Fallback funcional
- ✅ Métricas por client funcionais

**Parallel**: ✅ [P] (independente de outras tasks de teste)

---

### T055: Teste de performance com carga realista

**User Story**: Polish  
**File**: `tests/performance/test_realistic_load.py`  
**Description**: Validar performance com cenários realistas de uso

**Steps**:
1. Criar cenário: 10 clients fazendo buscas concorrentes
2. Testar throughput: mínimo 500 req/min mantido
3. Testar latência p95 <200ms para operações básicas
4. Testar latência p99 <500ms
5. Testar uso de memória estável <1GB após 1h
6. Testar sem memory leaks (valgrind ou similar)
7. Gerar relatório de performance

**Acceptance Criteria**:
- ✅ 500+ req/min sustentado
- ✅ p95 latency <200ms
- ✅ Memória <1GB estável
- ✅ Sem memory leaks detectados

**Parallel**: ✅ [P] (independente de outras tasks)

---

### T056: Validação final de cobertura de requisitos

**User Story**: Polish  
**File**: `tests/contract/test_requirements_coverage.py`  
**Description**: Teste automatizado validando que todos os FR-001 a FR-021 têm testes

**Steps**:
1. Criar mapeamento de FR-XXX → tests
2. Para cada FR, validar que existe teste correspondente
3. Validar que teste cobre acceptance criteria
4. Gerar relatório de cobertura de requisitos
5. Falhar se qualquer FR não tem teste
6. Documentar coverage em README

**Acceptance Criteria**:
- ✅ 100% dos requisitos funcionais têm testes
- ✅ Relatório de coverage gerado
- ✅ Build falha se coverage <100%
- ✅ Documentação atualizada

**Parallel**: ✅ [P] (independente de outras tasks)

---

## Dependencies Graph

```
Phase 1 (Setup)
├─ T001 → T002
├─ T003 [P]
├─ T004 [P] → T004a [P] (logging validation tests)
├─ T005 [P]
└─ T006 [P]

Phase 2 (Foundational + AMQP) - BLOCKS ALL USER STORIES
├─ T007 → T008 → T008a [P] (multi-version schemas) → T011 → T012
├─ T007 → T009 [P]
├─ T007 → T010 [P]
├─ T013 [P]
├─ T013a [P] (AMQP client)
├─ T013b [P] (AMQP schemas)
├─ T008 + T013b → T013c → T013d (AMQP registry + embeddings)
├─ T013a + T013c → T013e (AMQP executors)
└─ T013f [P] (AMQP integration tests)

Phase 3 (US1) - Descobrir Operações
├─ T014 → T015
├─ T016 [P] ┐
├─ T017 [P] ├─ can run parallel
├─ T018 [P] │
├─ T019 [P] │
├─ T020 [P] │
└─ T021 [P] ┘

Phase 4 (US2) - Obter Detalhes
├─ T022 → T023
├─ T024 [P] ┐
├─ T025 [P] ├─ can run parallel
└─ T026 [P] ┘

Phase 5 (US3) - Executar Operações
├─ T027 → T028 → T030
├─ T027 → T029 → T030
├─ T031 [P] ┐
├─ T032 [P] │
├─ T033 [P] │
├─ T034 [P] ├─ can run parallel after T027
├─ T035 [P] │
├─ T036 [P] │
├─ T037      │  (requires infrastructure)
├─ T038 [P] │
└─ T039 [P] ┘

Phase 6 (US4) - Feedback de Erros
├─ T043 → T044 [P]
├─         T045 [P]
├─         T046 [P]
└─         T047 [P]

Phase 7 (Polish + Additional Tests)
├─ T048
├─ T049 [P]
├─ T050 [P]
├─ T050a [P] (OpenTelemetry e2e tests)
├─ T051 [P] (Auth tests)
├─ T052 [P] (Thread-safety tests)
├─ T053 [P] (Multi-version tests)
├─ T054 [P] (Rate limit client ID tests)
├─ T055 [P] (Performance tests)
└─ T056 [P] (Requirements coverage validation)
```

## Parallel Execution Examples

### Maximum Parallelization Opportunities

**During Setup (Phase 1)**:
- Run T003, T004, T005, T006 in parallel after T002
- **Speedup**: 4 tasks → ~1 day instead of 2-3 days

**During Foundational (Phase 2)**:
- Run T009, T010, T013 in parallel with T008
- **Speedup**: 3 tasks concurrently

**During US1 (Phase 3)**:
- After T015, run T016-T021 (6 tasks) in parallel
- **Speedup**: 6 tasks → ~1 day instead of 3 days

**During US3 (Phase 5)**:
- After T027, run T031-T039 (9 tasks) in parallel
- **Speedup**: 9 tasks → ~1-2 days instead of 4+ days

**During US4 (Phase 6)**:
- After T040, run T041-T044 (4 tasks) in parallel
- **Speedup**: 4 tasks → few hours instead of 1+ day

## Independent Testing Strategy

Cada User Story pode ser testada independentemente:

### US1 - Descobrir Operações
**Test**: Enviar query "list queues" → verificar resultados relevantes retornados
**Success**: Operações de filas retornadas com similarity_score >= 0.7

### US2 - Obter Detalhes
**Test**: Solicitar detalhes de "queues.list" → verificar schema completo retornado
**Success**: Request/response schemas, examples e documentação presentes

### US3 - Executar Operações
**Test**: Executar "queues.create" com params válidos → verificar fila criada no RabbitMQ
**Success**: Operação executada, resultado retornado, fila verificável no RabbitMQ

### US4 - Feedback de Erros
**Test**: Executar operação sem param obrigatório → verificar erro detalhado
**Success**: Erro lista especificamente "missing: ['vhost']" com sugestão de resolução

## Implementation Strategy

### MVP Scope (Recommended First Delivery)
**Focus**: User Story 1 apenas (T001-T021)
- Setup completo (Phase 1)
- Foundational completo (Phase 2)
- US1: Descobrir Operações (Phase 3)

**Rationale**: US1 é a porta de entrada do sistema. Entregar busca semântica funcional primeiro permite validar a proposta de valor do padrão de descoberta semântica.

**Timeline**: ~1 semana

### Incremental Delivery
1. **Week 1**: MVP (US1 apenas)
2. **Week 2**: US2 (Obter Detalhes) + US4 (Error Handling)
3. **Week 3**: US3 (Executar Operações) - funcionalidade principal
4. **Week 4**: Polish, integration, CI/CD

## Success Metrics

Após implementação completa, validar:

- ✅ **SC-001**: Desenvolvedores descobrem operações em <5s via busca semântica
- ✅ **SC-002**: Resposta básica em <200ms (95th percentile)
- ✅ **SC-003**: Validação adiciona <10ms
- ✅ **SC-004**: Uso de memória <1GB
- ✅ **SC-005**: 100% MCP compliance (validado por contract tests)
- ✅ **SC-006**: Desenvolvedores executam operações com sucesso na primeira tentativa
- ✅ **SC-007**: Erros permitem identificar problema em 90% dos casos
- ✅ **SC-008**: Timeouts >30s abortados com mensagem clara
- ✅ **SC-009**: Logs JSON permitem análise automatizada
- ✅ **SC-010**: Integridade de cache sob concorrência
- ✅ **SC-011**: OpenTelemetry traces/metrics/logs completos
- ✅ **SC-012**: Rate limiting protege RabbitMQ de sobrecarga

---

**Generated**: 2025-10-09  
**Version**: 1.0.0  
**Ready for**: Immediate implementation
