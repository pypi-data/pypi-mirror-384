# Research: Essential Topology Operations

**Feature**: 003-essential-topology-operations  
**Phase**: 0 - Research & Technical Decisions  
**Date**: 2025-10-09

## Executive Summary

Este documento consolida as decisões técnicas para implementação de operações essenciais de topologia RabbitMQ através do padrão de descoberta semântica MCP. Todas as decisões foram tomadas considerando os requisitos constitucionais e as necessidades específicas do projeto.

## Technical Decisions

### 1. Linguagem e Runtime

**Decision**: Python 3.12+

**Rationale**:
- Ecossistema maduro para RabbitMQ com bibliotecas robustas
- Excelente suporte para desenvolvimento CLI com click framework
- Pydantic para validação de schemas tipo-safe
- structlog para logging estruturado amplamente adotado
- Facilidade de manutenção e debugabilidade
- Conforme especificação clarificada na sessão 2025-10-09 Round 3

**Alternatives considered**:
- **Node.js/TypeScript**: Rejeitado por menor maturidade de bibliotecas RabbitMQ Management API e preferência explícita por Python no spec
- **Go**: Rejeitado por maior complexidade de desenvolvimento CLI e ausência de requisito de performance extrema
- **Rust**: Rejeitado por complexidade excessiva e tempo de desenvolvimento maior

---

### 2. HTTP Client para RabbitMQ Management API

**Decision**: requests library

**Rationale**:
- Biblioteca HTTP padrão Python, amplamente usada e testada
- Máximo controle sobre requisições HTTP
- Integração simples com validação Pydantic
- Excelente documentação e comunidade ativa
- Performance adequada para requisitos do projeto (< 2s listagens, < 1s operações)
- Conforme especificação clarificada na sessão 2025-10-09 Round 3

**Alternatives considered**:
- **httpx**: Rejeitado por adicionar complexidade async desnecessária para caso de uso CLI
- **pika (AMQP)**: Rejeitado porque operações de topologia são feitas via Management HTTP API, não AMQP protocol
- **aiohttp**: Rejeitado por não haver necessidade de I/O async para CLI tool sequencial

---

### 3. Framework CLI

**Decision**: click framework

**Rationale**:
- Framework mais popular para CLIs profissionais Python
- Validação automática de argumentos e tipos
- Help text gerado automaticamente
- Estrutura organizada com command groups
- Suporte nativo para opções via argumentos ou variáveis de ambiente
- Excelente integração com testes pytest
- Conforme especificação clarificada na sessão 2025-10-09 Round 3

**Alternatives considered**:
- **argparse**: Rejeitado por verbosidade excessiva e menor qualidade de help text
- **typer**: Rejeitado por menor maturidade e comunidade menor que click
- **docopt**: Rejeitado por abordagem baseada em docstrings ser menos type-safe

---

### 4. Structured Logging

**Decision**: structlog library

**Rationale**:
- Padrão da indústria para structured logging Python
- Output JSON nativo para ingestão em sistemas de log management
- Rico em contexto (correlation IDs, metadata)
- Integração nativa com processadores de log (Elasticsearch, Splunk)
- Sanitização automática de dados sensíveis
- Mandatório pela constituição (seção V - Observability)
- Conforme especificação clarificada na sessão 2025-10-09 Round 3

**Alternatives considered**:
- **logging (stdlib)**: Rejeitado por não ter structured logging nativo, requer configuração complexa
- **loguru**: Rejeitado por não ser padrão da indústria para structured logging empresarial
- **python-json-logger**: Rejeitado por menor funcionalidade e comunidade que structlog

---

### 5. Formatação de Output CLI

**Decision**: tabulate library

**Rationale**:
- Biblioteca mais comum para formatação de tabelas Python
- Leve, simples e focada em clareza
- Suporte múltiplos formatos de tabela (grid, simple, fancy)
- Alinhamento automático de colunas
- Performance adequada para até 1000 linhas
- Conforme especificação clarificada na sessão 2025-10-09 Round 3

**Alternatives considered**:
- **rich**: Rejeitado por adicionar complexidade excessiva e dependências pesadas para caso de uso simples
- **prettytable**: Rejeitado por menor performance e comunidade menos ativa
- **Manual formatting**: Rejeitado por reinventar a roda e aumentar custo de manutenção

---

### 6. Vector Database para Semantic Search

**Decision**: ChromaDB (local file mode)

**Rationale**:
- Melhor opção Python para vector database embeddable (conforme constituição)
- Modo local file-based, sem dependências externas
- Excelente performance < 100ms para semantic search
- Arquivos de índice podem ser commitados ao repositório
- Integração nativa com sentence-transformers para embeddings
- Suporte eficiente para paginação de resultados
- Mandatório pela constituição (seção Vector Database Requirements)

**Alternatives considered**:
- **sqlite-vec**: Rejeitado por menor maturidade e funcionalidades limitadas comparado a ChromaDB
- **FAISS**: Rejeitado por não ter interface Python amigável e complexidade de configuração
- **pgvector**: Rejeitado por requerer PostgreSQL instalado, violando requisito de embedded database

---

### 7. Schema Validation

**Decision**: Pydantic v2 + jsonschema

**Rationale**:
- Pydantic models auto-gerados do OpenAPI specification
- Validação tipo-safe em runtime
- Integração nativa com FastAPI e MCP tooling
- Conversão automática OpenAPI schema → Pydantic
- jsonschema para validação dinâmica de operações
- Performance < 10ms overhead conforme requisito constitucional
- Mandatório pela constituição (seção Schema Management)

**Alternatives considered**:
- **marshmallow**: Rejeitado por menor performance e comunidade menos ativa que Pydantic
- **attrs + cattrs**: Rejeitado por não ter geração automática de OpenAPI schemas
- **dataclasses (stdlib)**: Rejeitado por não ter validação runtime integrada

---

### 8. Testing Framework

**Decision**: pytest

**Rationale**:
- Framework de testes Python mais popular e maduro
- Fixtures para setup/teardown complexo
- Parametrização de testes para múltiplos cenários
- Coverage tracking integrado (pytest-cov)
- Suporte nativo para integration tests com containers (testcontainers-python)
- Mandatório pela constituição (80% coverage mínimo, seção III)

**Alternatives considered**:
- **unittest (stdlib)**: Rejeitado por verbosidade excessiva e menor funcionalidade
- **nose2**: Rejeitado por desenvolvimento descontinuado
- **ward**: Rejeitado por menor maturidade e comunidade

---

### 9. OpenAPI Code Generation

**Decision**: datamodel-code-generator + custom scripts

**Rationale**:
- Geração automática de Pydantic models do OpenAPI YAML
- Suporte Pydantic v2 nativo
- Customização via templates para headers e metadata
- Geração triggada por mudanças no OpenAPI (file watcher ou manual)
- Artifacts commitados ao repositório conforme constituição
- Mandatório pela constituição (seção Code Generation Requirements)

**Alternatives considered**:
- **openapi-python-client**: Rejeitado por gerar código HTTP client completo, mais do que precisamos
- **Manual schemas**: Rejeitado por violar princípio DRY e requisito constitucional de OpenAPI como source of truth
- **Runtime schema parsing**: Rejeitado por violar requisito de build-time generation da constituição

---

### 10. Embeddings Generation

**Decision**: sentence-transformers (all-MiniLM-L6-v2 model)

**Rationale**:
- Modelo leve e eficiente para semantic similarity
- < 50MB memory footprint conforme requisito constitucional
- Rápido para embedding generation (< 100ms por operação)
- Integração nativa com ChromaDB
- Multilingual support para futuras extensões i18n
- Modelo open-source, sem dependências de APIs externas

**Alternatives considered**:
- **OpenAI embeddings API**: Rejeitado por requerer API key e chamadas externas (latência, custo)
- **BERT-base**: Rejeitado por modelo muito pesado (> 400MB) para uso embeddable
- **USE (Universal Sentence Encoder)**: Rejeitado por menor performance que all-MiniLM-L6-v2

---

## Integration Strategy

### MCP Semantic Discovery Pattern

A arquitetura seguirá rigorosamente o padrão de 3 ferramentas MCP definido na constituição:

1. **search-ids**: Vector similarity search em operações RabbitMQ
   - Input: query natural language + pagination
   - Output: Lista paginada de operation IDs com descrições
   - Implementation: ChromaDB similarity search

2. **get-id**: Recuperação de schema detalhado de operação
   - Input: operation ID (ex: "queues.create")
   - Output: Schema completo (params, response, examples)
   - Implementation: Lookup em operation registry gerado do OpenAPI

3. **call-id**: Execução de operação com validação dinâmica
   - Input: operation ID + params + pagination (opcional)
   - Output: Resultado da operação ou resposta paginada
   - Implementation: Validação dinâmica + HTTP request via requests

### Operation ID Naming Convention

Operações seguirão padrão `{tag}.{operation-name}` derivado do OpenAPI:
- `queues.list` - GET /api/queues
- `queues.create` - PUT /api/queues/{vhost}/{name}
- `queues.delete` - DELETE /api/queues/{vhost}/{name}
- `exchanges.list` - GET /api/exchanges
- `exchanges.create` - PUT /api/exchanges/{vhost}/{name}
- `exchanges.delete` - DELETE /api/exchanges/{vhost}/{name}
- `bindings.list` - GET /api/bindings
- `bindings.create` - POST /api/bindings/{vhost}/e/{exchange}/q/{queue}
- `bindings.delete` - DELETE /api/bindings/{vhost}/e/{exchange}/q/{queue}/{props}

---

## Performance Optimizations

### Caching Strategy
- Schema validation cache: 5 minutos TTL
- Operation registry: Loaded once at startup
- Vector indices: Pre-loaded at startup (< 50MB memory)

### Request Optimization
- Connection pooling via requests.Session
- Keep-alive connections para Management API
- Timeout configurável (default: 5s)

### Pagination Strategy
- Default 50 items per page (constitution requirement)
- Max 200 items per page (constitution requirement)
- Cursor-based pagination para real-time data quando suportado pelo RabbitMQ API

---

## Security Considerations

### Credentials Management
- Priority: CLI arguments > Environment variables > Config file
- Nunca logar credenciais completas
- Sanitização automática via structlog processors

### Input Validation
- Validação Pydantic antes de qualquer operação
- Regex validation para nomes (alfanumérico, hífen, underscore, ponto)
- Length validation (max 255 chars para nomes)

### Permission Handling
- Delegação completa para RabbitMQ (usar credenciais da conexão)
- Propagação clara de erros de autorização 401/403

---

## Testing Strategy

### Unit Tests (80%+ coverage target)
- Validação de schemas Pydantic
- Parsing de OpenAPI specification
- Operation registry mapping
- Vector search functionality
- Input validation logic

### Integration Tests (100% critical paths)
- Queue CRUD operations contra RabbitMQ real
- Exchange CRUD operations
- Binding CRUD operations
- Error scenarios (fila com mensagens, exchange com bindings)
- testcontainers-python para RabbitMQ ephemeral instances

### Contract Tests (100% OpenAPI compliance)
- Validação de schemas gerados contra OpenAPI
- Request/response structure validation
- Error format compliance
- Pagination compliance

---

## Deployment Considerations

### Packaging
- pyproject.toml para dependency management
- uvx para instalação e execução (conforme memória do usuário)
- Wheels para distribuição
- Vector database files incluídos no package

### Documentation (mandatório conforme constituição)
- README.md: Overview e quick start com uvx
- docs/API.md: Referência completa de operações
- docs/ARCHITECTURE.md: Design e componentes
- docs/EXAMPLES.md: Exemplos de uso (bash, PowerShell, debug)
- docs/CONTRIBUTING.md: Guia de contribuição

### License
- LGPL v3.0 em todos os arquivos fonte
- LICENSE file no root
- Headers de licença em arquivos .py

---

## Open Questions (RESOLVED)

Todas as questões foram resolvidas através das clarificações do spec:
- ✅ Linguagem: Python 3.12+
- ✅ HTTP client: requests
- ✅ CLI framework: click
- ✅ Logging: structlog
- ✅ Formatação: tabulate
- ✅ Validação de permissões: Delegada ao RabbitMQ
- ✅ Comportamento em falha de conexão: Fail-fast, retry é responsabilidade do usuário
- ✅ Confirmação para deleção: Flag --force para forçar
- ✅ Validação de nomes: Regras do RabbitMQ (alfanumérico, hífen, underscore, ponto; max 255)
- ✅ Exchange com bindings: Bloquear deleção, operador deve remover bindings primeiro

---

## Next Steps (Phase 1)

1. **Create data-model.md**: Definir entidades (Queue, Exchange, Binding) com atributos completos
2. **Generate contracts/**: Criar schemas OpenAPI específicos para operações de topologia
3. **Create quickstart.md**: Exemplos práticos de uso da CLI
4. **Update agent context**: Executar script de atualização com tecnologias desta feature

---

**Research Complete**: ✅  
**All NEEDS CLARIFICATION resolved**: ✅  
**Constitution compliance verified**: ✅  
**Ready for Phase 1 (Design)**: ✅
