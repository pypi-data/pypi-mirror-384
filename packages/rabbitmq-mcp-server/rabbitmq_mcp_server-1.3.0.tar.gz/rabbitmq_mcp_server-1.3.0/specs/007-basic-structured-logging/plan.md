# Implementation Plan: Basic Structured Logging

**Branch**: `feature/007-basic-structured-logging` | **Date**: 2025-10-09 | **Spec**: [spec.md](../../../specs/007-basic-structured-logging/spec.md)
**Input**: Feature specification from `/specs/007-basic-structured-logging/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implementar sistema de logging estruturado em JSON para o RabbitMQ MCP Server, fornecendo observabilidade, auditoria e conformidade de segurança. O sistema deve incluir redação automática de dados sensíveis, correlation IDs para rastreamento de operações, rotação de arquivos e performance com overhead <5ms por operação. Logs escritos em múltiplos destinos configuráveis: (1) Arquivos locais com formato JSON (default), (2) Console/stderr (fallback automático), e (3) RabbitMQ AMQP topic exchange (streaming real-time). Sistema suporta 3 destinos simultaneamente para máxima flexibilidade operacional.

## Technical Context

**Language/Version**: Python 3.12+  
**Primary Dependencies**: structlog (logging estruturado), pydantic (validação), asyncio (I/O assíncrono), pytest (testes)  
**Storage**: File system local - arquivos JSON em ./logs/ com rotação diária/tamanho  
**Testing**: pytest com cobertura mínima 80% (TDD obrigatório por constitution)  
**Target Platform**: Cross-platform (Windows/Linux/macOS) - servidor MCP Python
**Project Type**: Single project - biblioteca de logging integrada ao MCP server  
**Performance Goals**: <5ms overhead por operação de log, throughput limitado apenas por hardware/I/O  
**Constraints**: Zero perda de logs (blocking ao saturar buffer), redação automática obrigatória, UTC sempre  
**Scale/Scope**: Sistema single-instance MVP, integração futura com agregadores (ELK/Splunk) fora do escopo

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Compliance Verification

| Requisito Constitution | Status | Justificativa |
|------------------------|--------|---------------|
| **Logging estruturado obrigatório** (Seção V) | ✅ PASS | Feature implementa logging JSON estruturado conforme especificado |
| **TDD com 80% cobertura mínima** (Seção III) | ✅ PASS | Testes planejados para todas funcionalidades, cobertura 80%+ |
| **Redação automática de dados sensíveis** (Seção V) | ✅ PASS | FR-004 garante redação automática obrigatória com zero credentials em logs |
| **Performance <200ms para operações** (Seção VII) | ✅ PASS | Requisito mais rigoroso: <5ms overhead por operação de log |
| **Correlation IDs para rastreamento** (Seção V) | ✅ PASS | FR-005 implementa UUID por requisição MCP |
| **Rotação e retenção de logs** (Seção V) | ✅ PASS | FR-012 a FR-014: rotação diária/100MB, retenção 30 dias |
| **Destinos configuráveis (File, Elasticsearch, Splunk, etc)** (Seção V) | ✅ PASS | FR-003 (File-based default) + FR-019 (Console fallback) satisfy MVP; external aggregator integrations deferred to Phase 2 |
| **Compressão de logs rotacionados** (Seção V) | ✅ PASS | FR-017 implementa gzip obrigatório |
| **Níveis de log padrão (error, warn, info, debug)** (Seção V) | ✅ PASS | FR-002 implementa níveis exatos especificados |

### Gate Decision (Pre-Phase 0)

**STATUS**: ✅ **APPROVED - COMPLIANCE WITH CLARIFICATIONS**

Constitution requires "configurable outputs" for logging. MVP satisfies this requirement with:

1. **File-based (default)** - Primary destination, most common for enterprise applications requiring audit trails
2. **Console/stderr (fallback)** - Automatic fallback per FR-019, ensures zero log loss even when file system fails

**RabbitMQ AMQP Destination - Deferred to Phase 2 (Priority P2)**:
- Constitution's "most commonly used" principle applies to **any configurable destination**, not specifically RabbitMQ AMQP
- **File + Console** satisfy constitutional requirement for MVP
- RabbitMQ AMQP is valuable for advanced scenarios but not required for basic structured logging functionality
- Priority P2 reflects optional nature: core logging works without it

**Rationale for deferring RabbitMQ destination**:
- No evidence that RabbitMQ self-logging is industry standard practice
- File-based logging is universal baseline for all applications
- RabbitMQ AMQP adds complexity without validating real-world demand
- Can be added in Phase 2 if customer feedback confirms need
- Maintains constitution compliance through File + Console destinations

**Clarification on Elasticsearch/Splunk**: Constitution lists these as configurable options. For MVP:
- **File-based** provides foundation for all external integrations
- External aggregators (Elasticsearch, Splunk, CloudWatch) consume logs via file tailing, Fluentd, or similar
- Direct integrations deferred to Phase 2 based on validated customer requirements
- Decoupled architecture allows adding integrations without changing core logging system

**Constitutional Phased Implementation Note**: For MVP scope, the logging system implements File + Console destinations as foundation. RabbitMQ AMQP and enterprise aggregators (Elasticsearch, Splunk, Fluentd, CloudWatch) are deferred to Phase 2 because:
1. File-based logging is universal baseline satisfying "configurable outputs" requirement
2. External aggregators consume logs via file tailing (Fluentd, Filebeat) without requiring direct integration
3. Decoupled architecture allows adding advanced destinations in Phase 2 without changing core system
4. Constitution's "configurable outputs" requirement is satisfied through File + Console in MVP
5. RabbitMQ AMQP destination (Priority P2) represents advanced use case requiring validation of real-world demand

---

### Re-evaluation (Post-Phase 1 Design)

**Data**: 2025-10-09  
**Status**: ✅ **FINAL APPROVAL**

#### Design Compliance Review

| Aspecto | Status | Evidência |
|---------|--------|-----------|
| **Arquitetura alinhada com Constitution** | ✅ PASS | Estrutura modular em `src/logging/` facilita manutenção e extensão |
| **TDD preparado com 80% cobertura** | ✅ PASS | Estrutura de testes completa em `tests/unit/`, `tests/integration/`, `tests/contract/` |
| **Performance <5ms validável** | ✅ PASS | Design com batching, async I/O e orjson garante overhead mínimo |
| **Redação automática implementável** | ✅ PASS | Processador structlog dedicado com patterns regex built-in |
| **Correlation IDs via contextvars** | ✅ PASS | Solução async-safe usando Python contextvars nativo |
| **Schemas validáveis** | ✅ PASS | JSON schemas completos em `contracts/` + Pydantic models |
| **Rotação dual (tempo+tamanho)** | ✅ PASS | Wrapper de Python logging handlers built-in |
| **Destinos configuráveis (3 destinos MVP)** | ✅ PASS | File (default) + Console (fallback) + RabbitMQ AMQP (domain-aligned) |

#### Design Risks Mitigated

1. **Performance Risk**: Uso de orjson + batching + lazy evaluation garante <5ms overhead
2. **Security Risk**: Redação automática na camada de processamento (não depende de developers)
3. **Complexity Risk**: Uso de stdlib Python (logging, asyncio, contextvars) minimiza dependências
4. **Cross-platform Risk**: File-based logging funciona em Windows/Linux/macOS sem mudanças

#### Implementation Readiness

- ✅ Todas decisões técnicas documentadas em `research.md`
- ✅ Entidades e schemas definidos em `data-model.md`
- ✅ Contratos JSON validáveis em `contracts/`
- ✅ Guia de uso pronto em `quickstart.md`
- ✅ Agent context atualizado com tecnologias escolhidas

**DECISÃO FINAL**: Design aprovado para implementação. Próximo passo: `/speckit.tasks` para gerar tasks de implementação.

## Project Structure

### Documentation (this feature)

```
specs/feature/007-basic-structured-logging/
├── plan.md              # Este arquivo (saída do comando /speckit.plan)
├── research.md          # Saída Phase 0 (comando /speckit.plan)
├── data-model.md        # Saída Phase 1 (comando /speckit.plan)
├── quickstart.md        # Saída Phase 1 (comando /speckit.plan)
├── contracts/           # Saída Phase 1 (comando /speckit.plan)
│   ├── LogEntry.schema.json
│   ├── LogConfig.schema.json
│   └── LogOutput.schema.json
└── tasks.md             # Saída Phase 2 (comando /speckit.tasks - NÃO criado por /speckit.plan)
```

### Source Code (repository root)

```
src/
├── logging/                    # Módulo principal de logging estruturado
│   ├── __init__.py            # Exports públicos
│   ├── logger.py              # Logger principal estruturado
│   ├── config.py              # Configuração de logging
│   ├── formatters.py          # Formatadores JSON estruturados
│   ├── handlers/              # Handlers de output para múltiplos destinos
│   │   ├── __init__.py        # Handler interface (Protocol)
│   │   ├── file.py            # FileLogHandler com rotação
│   │   ├── console.py         # ConsoleLogHandler (fallback stderr)
│   │   └── rabbitmq.py        # RabbitMQLogHandler (AMQP publish)
│   ├── processors.py          # Processadores structlog (redação, correlation IDs)
│   ├── redaction.py           # Engine de redação de dados sensíveis
│   ├── correlation.py         # Gerenciamento de correlation IDs
│   └── rotation.py            # Lógica de rotação e retenção de arquivos
├── models/
│   └── log_entry.py           # Modelo Pydantic para entrada de log
└── utils/
    └── async_writer.py        # Buffer assíncrono para escritas de log

tests/
├── unit/
│   ├── test_logger.py         # Testes do logger principal
│   ├── test_redaction.py      # Testes de redação automática
│   ├── test_correlation.py    # Testes de correlation IDs
│   ├── test_rotation.py       # Testes de rotação de arquivos
│   ├── test_formatters.py     # Testes de formatadores JSON
│   └── handlers/
│       ├── test_file_handler.py      # Testes de FileLogHandler
│       ├── test_console_handler.py   # Testes de ConsoleLogHandler
│       └── test_rabbitmq_handler.py  # Testes de RabbitMQLogHandler
├── integration/
│   ├── test_log_flow.py       # Testes de fluxo end-to-end
│   ├── test_async_logging.py # Testes de logging assíncrono
│   └── test_performance.py    # Testes de overhead <5ms
└── contract/
    └── test_log_schema.py     # Validação de schema JSON de logs

config/
└── logging_config.yaml        # Configuração padrão de logging

logs/                          # Diretório de logs (criado em runtime)
└── .gitkeep                   # Mantém diretório no Git
```

**Structure Decision**: Estrutura single-project escolhida porque o sistema de logging é uma biblioteca integrada ao MCP server Python existente, não um serviço independente. O módulo `src/logging/` encapsula toda a funcionalidade de logging estruturado e será importado por outras partes do MCP server.

## Complexity Tracking

*Fill ONLY if Constitution Check has violations that must be justified*

**Nenhuma violação identificada** - Todos os requisitos da constitution estão atendidos no design MVP.

---

## Implementation Plan Summary

### Phase 0: Research ✅ COMPLETE

**Deliverable**: `research.md` com todas decisões técnicas documentadas

**Decisões principais**:
- structlog para logging estruturado (constitution standard)
- asyncio.Queue com blocking para zero log loss
- Regex patterns + whitelist para redação automática
- Python logging handlers para rotação dual (tempo+tamanho)
- orjson + batching para performance <5ms
- contextvars para correlation IDs async-safe
- Schema flat JSON (ECS-inspired) para queryability
- 3 destinos configuráveis: File (default) + Console (fallback) + RabbitMQ AMQP (domain-aligned)
- pytest + TDD + 80% cobertura mínima

### Phase 1: Design & Contracts ✅ COMPLETE

**Deliverables**:
- `data-model.md` - Entidades, atributos, relacionamentos e regras de negócio
- `contracts/LogEntry.schema.json` - Schema JSON para log entries
- `contracts/LogConfig.schema.json` - Schema JSON para configuração
- `contracts/SensitiveDataPattern.schema.json` - Schema JSON para padrões de redação
- `contracts/README.md` - Documentação de uso dos schemas
- `quickstart.md` - Guia prático de uso em 10 minutos
- `.cursor/rules/specify-rules.mdc` - Contexto do agente atualizado

**Entidades principais**:
1. LogEntry - Entrada individual de log estruturado
2. LogConfig - Configuração do sistema de logging
3. SensitiveDataPattern - Padrões para redação automática
4. CorrelationContext - Contexto para propagação de correlation IDs
5. LogFile - Arquivo físico de log com metadados de rotação

### Phase 2: NOT STARTED

**Next Command**: `/speckit.tasks` para gerar tasks de implementação detalhadas

Este comando criará `tasks.md` com breakdown de tarefas para implementação TDD.

---

## Key Technical Decisions Summary

| Aspecto | Tecnologia/Pattern | Justificativa |
|---------|-------------------|---------------|
| Logging Core | structlog | Constitution standard, JSON nativo, processadores encadeados |
| Async Pattern | asyncio.Queue + blocking | Zero log loss, performance, simplicidade |
| Redação | Regex patterns | Segurança automática obrigatória por constitution |
| Rotação | Python logging handlers | Built-in, dual rotation, thread-safe |
| Performance | orjson + batching | <5ms overhead requirement |
| Correlation | contextvars | Async-safe propagation automática |
| Schema | Flat JSON (ECS-inspired) | Queryability, consistency, extensibility |
| Output Destinations | File + Console + RabbitMQ | Most common for enterprise message queue apps |
| Testing | pytest + 80% coverage | Constitution TDD requirement |

---

## Success Criteria Validation

| Critério | Status | Evidência no Design |
|----------|--------|---------------------|
| SC-001: 90% issues diagnosticáveis via logs | ✅ Ready | Schema completo com context, stack_trace, correlation_id |
| SC-002: 100% traceability via correlation IDs | ✅ Ready | CorrelationContext + contextvars garantem propagação |
| SC-003: <5ms overhead | ✅ Ready | orjson + batching + lazy eval projetados para performance |
| SC-004: Zero credentials em logs | ✅ Ready | Redação automática obrigatória em processador structlog |
| SC-005: Disk space sob controle | ✅ Ready | Rotação dual + retenção configurable + compression |
| SC-006: 95% investigações começam com logs | ✅ Ready | Structured JSON + jq queries facilitam análise |
| SC-007: Parsing com ferramentas padrão | ✅ Ready | JSON válido + schemas para validação |
| SC-008: Bottlenecks identificáveis em 10min | ✅ Ready | duration_ms + category Performance + jq queries |

---

## Branch Status

**Branch**: `feature/007-basic-structured-logging`  
**Status**: ✅ Ready for implementation  
**Next Step**: Execute `/speckit.tasks` to generate implementation tasks

**Artifacts Generated**:
```
specs/feature/007-basic-structured-logging/
├── plan.md                             ✅ Este arquivo
├── research.md                         ✅ Phase 0 complete
├── data-model.md                       ✅ Phase 1 complete
├── quickstart.md                       ✅ Phase 1 complete
└── contracts/
    ├── LogEntry.schema.json            ✅ Phase 1 complete
    ├── LogConfig.schema.json           ✅ Phase 1 complete
    ├── SensitiveDataPattern.schema.json ✅ Phase 1 complete
    └── README.md                       ✅ Phase 1 complete
```

**Agent Context**:
```
.cursor/rules/specify-rules.mdc         ✅ Updated with technologies
```
