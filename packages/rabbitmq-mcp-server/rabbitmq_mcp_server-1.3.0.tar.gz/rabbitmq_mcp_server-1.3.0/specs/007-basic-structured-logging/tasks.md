# Tasks: Basic Structured Logging

**Feature**: 007-basic-structured-logging  
**Branch**: `feature/007-basic-structured-logging`  
**Date**: 2025-10-09

## Summary

Este documento organiza as tarefas de implementação do sistema de logging estruturado em fases, priorizando as user stories da especificação. Cada fase representa um incremento independente e testável.

**Total de Tarefas**: 53 tarefas (T001-T050 + T027A + T027B + T027C for comprehensive testing coverage)  
**Fases**: 9 (Setup + Foundational + 6 User Stories + Polish)  
**Abordagem**: TDD obrigatório (testes antes de implementação)

---

## Phase 1: Setup & Project Structure

**Objetivo**: Preparar estrutura básica do projeto e dependências necessárias.

### T001: Criar estrutura de diretórios do módulo logging [P]
**Status**: [X] Concluído
**Tipo**: Setup  
**Arquivos**:
```
src/logging/__init__.py
src/logging/logger.py
src/logging/config.py
src/logging/formatters.py
src/logging/processors.py
src/logging/redaction.py
src/logging/correlation.py
src/logging/rotation.py
src/logging/handlers/__init__.py
src/logging/handlers/file.py
src/logging/handlers/console.py
src/logging/handlers/rabbitmq.py
```
**Descrição**: Criar estrutura de diretórios completa do módulo `src/logging/` com arquivos `__init__.py` vazios.

---

### T002: Criar estrutura de diretórios de testes [P]
**Status**: [X] Concluído
**Tipo**: Setup  
**Arquivos**:
```
tests/unit/test_logger.py
tests/unit/test_redaction.py
tests/unit/test_correlation.py
tests/unit/test_rotation.py
tests/unit/test_formatters.py
tests/unit/handlers/test_file_handler.py
tests/unit/handlers/test_console_handler.py
tests/unit/handlers/test_rabbitmq_handler.py
tests/integration/test_log_flow.py
tests/integration/test_async_logging.py
tests/integration/test_performance.py
tests/contract/test_log_schema.py
```
**Descrição**: Criar estrutura completa de diretórios de testes (unit, integration, contract) com arquivos vazios.

---

### T003: Criar estrutura de configuração [P]
**Status**: [X] Concluído
**Tipo**: Setup  
**Arquivos**:
```
config/logging_config.yaml
logs/.gitkeep
```
**Descrição**: Criar diretório `config/` com arquivo YAML de configuração padrão e diretório `logs/` com `.gitkeep`.

---

### T004: Adicionar dependências ao projeto [P]
**Status**: [X] Concluído
**Tipo**: Setup  
**Arquivo**: `requirements.txt` ou `pyproject.toml`  
**Descrição**: Adicionar dependências necessárias:
- `structlog>=24.0.0` - Logging estruturado
- `pydantic>=2.0.0` - Validação de modelos
- `pyyaml>=6.0` - Parsing de configuração YAML
- `orjson>=3.9.0` - JSON serialization rápida
- `pytest>=8.0.0` - Framework de testes
- `pytest-asyncio>=0.23.0` - Suporte async para pytest
- `pytest-cov>=4.1.0` - Cobertura de testes

---

## Phase 2: Foundational Tasks (Blocking Prerequisites)

**Objetivo**: Implementar componentes core que todas as user stories dependem.

### T005: [Foundation] Criar modelo Pydantic LogEntry
**Status**: [X] Concluído
**Tipo**: Model  
**Arquivo**: `src/models/log_entry.py`  
**Dependências**: T001, T004  
**Descrição**: Implementar modelo Pydantic `LogEntry` com todos os campos do schema (schema_version, timestamp, level, category, correlation_id, message, campos opcionais). Incluir validadores para UTC timestamp, truncamento de mensagens >100KB, validação de enums (LogLevel, LogCategory, OperationResult), e validação de semantic versioning para schema_version.

**Acceptance Criteria**:
- ✅ Campo schema_version com default "1.0.0" em formato semantic versioning (MAJOR.MINOR.PATCH)
- ✅ Validador para schema_version usando regex ^\\d+\\.\\d+\\.\\d+$
- ✅ Modelo valida timestamp ISO 8601 UTC com sufixo Z
- ✅ Mensagens >100KB são truncadas com "...[truncated]"
- ✅ Enums LogLevel, LogCategory, OperationResult funcionam corretamente
- ✅ Campos opcionais (tool_name, duration_ms, etc) validam corretamente

---

### T006: [Foundation] Criar modelo Pydantic LogConfig
**Status**: [X] Concluído
**Tipo**: Model  
**Arquivo**: `src/models/log_config.py`  
**Dependências**: T001, T004  
**Descrição**: Implementar modelo Pydantic `LogConfig` com todos os campos de configuração (log_level, output_file, rotation_when, rotation_interval, rotation_max_bytes, retention_days, compression_enabled, async_queue_size, async_flush_interval, batch_size, file_permissions, fallback_to_console). Incluir validadores e defaults conforme spec.

**Acceptance Criteria**:
- ✅ Configuração padrão funciona sem argumentos
- ✅ Validação de valores mínimos (retention_days >= 1, async_queue_size >= 100, etc)
- ✅ Defaults corretos conforme spec (100MB rotation, 30 dias retention, etc)

---

### T007: [Foundation] Implementar gerenciamento de correlation IDs com contextvars
**Status**: [X] Concluído
**Tipo**: Core Feature  
**Arquivo**: `src/logging/correlation.py`  
**Dependências**: T001, T004  
**Descrição**: Implementar funções `generate_correlation_id()`, `set_correlation_id()`, `get_correlation_id()` usando `contextvars.ContextVar`. UUID v4 como padrão, fallback para timestamp+random se UUID falhar.

**Acceptance Criteria**:
- ✅ `generate_correlation_id()` gera UUID v4 válido
- ✅ Fallback para timestamp+random funciona se UUID falhar
- ✅ `contextvars` mantém isolation entre contextos async
- ✅ Correlation ID propaga através de await calls

---

### T008: [Foundation] Implementar processador structlog para correlation IDs
**Status**: [X] Concluído
**Tipo**: Processor  
**Arquivo**: `src/logging/processors.py`  
**Dependências**: T007  
**Descrição**: Criar processador structlog `add_correlation_id()` que injeta correlation_id do contexto atual em cada log entry.

**Acceptance Criteria**:
- ✅ Processador adiciona correlation_id ao event_dict
- ✅ Se correlation_id não existe no contexto, log é criado sem o campo
- ✅ Processador não quebra pipeline se contexto for None

---

### T009: [Foundation] Implementar padrões de redação de dados sensíveis
**Status**: [X] Concluído
**Tipo**: Security  
**Arquivo**: `src/logging/redaction.py`  
**Dependências**: T001, T004  
**Descrição**: Implementar `BUILTIN_PATTERNS` com regex patterns para redação automática (password, api_key, token, amqp_password, bearer_token). Implementar função `apply_redaction()` que percorre event_dict e aplica patterns.

**Acceptance Criteria**:
- ✅ Passwords em connection strings são redagidos (amqp://user:[REDACTED]@host)
- ✅ API keys são redagidos (api_key=[REDACTED])
- ✅ Tokens são redagidos (token=[REDACTED])
- ✅ Bearer tokens são redagidos (Bearer [REDACTED])
- ✅ Username preservado em connection strings para debugging

---

### T010: [Foundation] Implementar processador structlog para redação
**Status**: [X] Concluído
**Tipo**: Processor  
**Arquivo**: `src/logging/processors.py`  
**Dependências**: T009  
**Descrição**: Criar processador structlog `add_redaction_processor()` que aplica redação automática recursivamente em todos os valores string do event_dict.

**Acceptance Criteria**:
- ✅ Processador itera por todos os campos do event_dict
- ✅ Strings são verificadas contra todos os patterns de redação
- ✅ Redação funciona em campos nested (dentro de context)
- ✅ Performance aceitável (<1ms adicional por log entry)

---

### T011: [Foundation] Configurar structlog com processadores básicos
**Status**: [X] Concluído
**Tipo**: Configuration  
**Arquivo**: `src/logging/logger.py`  
**Dependências**: T008, T010  
**Descrição**: Implementar função `configure_structlog()` que configura structlog com processadores essenciais: TimeStamper(utc=True), correlation ID, redaction, StackInfoRenderer, format_exc_info, JSONRenderer(orjson).

**Acceptance Criteria**:
- ✅ structlog configurado com todos os processadores na ordem correta
- ✅ Timestamps sempre em UTC com formato ISO 8601
- ✅ Output é JSON válido usando orjson
- ✅ Stack traces formatados corretamente
- ✅ Configuração é singleton (não reconfigura em múltiplas chamadas)

---

### T012: [Foundation] Implementar AsyncLogWriter para log buffering
**Status**: [X] Concluído
**Tipo**: Async Infrastructure  
**Arquivo**: `src/utils/async_writer.py`  
**Dependências**: T001, T004  
**Descrição**: Criar classe `AsyncLogWriter` com `asyncio.Queue` interno, métodos `start()`, `write_log()`, `_writer_loop()`, `stop()`. AsyncLogWriter com tamanho configurável, blocking on saturation para zero log loss.

**Acceptance Criteria**:
- ✅ Queue criada com maxsize configurável
- ✅ `write_log()` bloqueia quando queue está cheia (zero log loss)
- ✅ Background task `_writer_loop()` consome queue continuamente
- ✅ Batching de múltiplos logs por write quando possível
- ✅ Graceful shutdown com flush de logs pendentes

---

## Phase 3: User Story 1 - System Observability (Priority P1)

**Goal**: Implementar logging básico estruturado para observabilidade do sistema.

**Independent Test Criteria**: Executar operações diversas (conexões, operações MCP) e verificar que logs JSON estruturados são escritos com timestamps, níveis, categorias e detalhes apropriados.

### T013: [US1] Escrever testes para FileLogHandler
**Status**: [X] Concluído
**Tipo**: Test (TDD)  
**Arquivo**: `tests/unit/handlers/test_file_handler.py`  
**Dependências**: T002, T005, T006  
**Story**: US1  
**Descrição**: Escrever testes unitários para `FileLogHandler`:
- Criação de arquivo de log
- Escrita de log entries em formato JSON
- Append de múltiplas entries
- Handling de diretório não existente
- Fallback para console em erro

**Test Cases**:
```python
def test_file_handler_creates_log_file(temp_log_dir)
def test_file_handler_writes_json_entries(temp_log_dir)
def test_file_handler_appends_multiple_entries(temp_log_dir)
def test_file_handler_creates_directory_if_missing(tmp_path)
def test_file_handler_falls_back_on_permission_error(tmp_path)
def test_file_handler_handles_disk_full_error(tmp_path)
def test_file_handler_handles_concurrent_access(tmp_path)
def test_file_handler_handles_read_only_filesystem(tmp_path)
```

---

### T014: [US1] Implementar FileLogHandler
**Status**: [X] Concluído
**Tipo**: Handler Implementation  
**Arquivo**: `src/logging/handlers/file.py`  
**Dependências**: T013, T011  
**Story**: US1  
**Descrição**: Implementar `FileLogHandler` que escreve logs em arquivo JSON. Suportar criação automática de diretório, append mode, serialização JSON com orjson, fallback para console em erro.

**Acceptance Criteria**:
- ✅ Cria arquivo de log no caminho especificado
- ✅ Cria diretório automaticamente se não existir
- ✅ Escreve cada log entry como linha JSON separada
- ✅ Usa orjson para serialização rápida
- ✅ Tenta console fallback se escrita em arquivo falhar
- ✅ Todos os testes T013 passam

---

### T015: [US1] Escrever testes para ConsoleLogHandler [P]
**Status**: [X] Concluído
**Tipo**: Test (TDD)  
**Arquivo**: `tests/unit/handlers/test_console_handler.py`  
**Dependências**: T002, T005  
**Story**: US1  
**Descrição**: Escrever testes unitários para `ConsoleLogHandler`:
- Escrita para stderr
- Formato JSON
- Não bloqueia em erros

**Test Cases**:
```python
def test_console_handler_writes_to_stderr(capsys)
def test_console_handler_writes_json_format(capsys)
def test_console_handler_never_raises_exception()
```

---

### T016: [US1] Implementar ConsoleLogHandler [P]
**Status**: [X] Concluído
**Tipo**: Handler Implementation  
**Arquivo**: `src/logging/handlers/console.py`  
**Dependências**: T015, T011  
**Story**: US1  
**Descrição**: Implementar `ConsoleLogHandler` que escreve logs para stderr em formato JSON. Nunca lança exceções (fallback silencioso).

**Acceptance Criteria**:
- ✅ Escreve para sys.stderr
- ✅ Formato JSON usando orjson
- ✅ Não lança exceções em nenhuma circunstância
- ✅ Todos os testes T015 passam

---

### T017: [US1] Escrever testes para logger principal
**Status**: [X] Concluído
**Tipo**: Test (TDD)  
**Arquivo**: `tests/unit/test_logger.py`  
**Dependências**: T002, T005  
**Story**: US1  
**Descrição**: Escrever testes unitários para logger principal:
- Níveis de log (ERROR, WARN, INFO, DEBUG)
- Categorias de log
- Campos obrigatórios presentes
- Output é JSON válido
- Configuração de nível mínimo

**Test Cases**:
```python
def test_logger_supports_all_log_levels()
def test_logger_supports_all_categories()
def test_logger_includes_required_fields()
def test_logger_output_is_valid_json()
def test_logger_filters_by_minimum_level()
def test_logger_includes_timestamp_utc()
```

---

### T018: [US1] Implementar logger principal com múltiplos handlers
**Status**: [X] Concluído
**Tipo**: Core Feature  
**Arquivo**: `src/logging/logger.py`  
**Dependências**: T017, T014, T016, T012  
**Story**: US1  
**Descrição**: Implementar função `get_logger()` que retorna logger structlog configurado com FileLogHandler e ConsoleLogHandler (fallback). Integrar com AsyncLogWriter para performance.

**Acceptance Criteria**:
- ✅ `get_logger()` retorna logger configurado (singleton por nome)
- ✅ Suporta todos os níveis (ERROR, WARN, INFO, DEBUG)
- ✅ FileLogHandler é handler primário
- ✅ ConsoleLogHandler é fallback automático em erros
- ✅ Logs passam por AsyncLogWriter para batching
- ✅ Todos os testes T017 passam

---

### T019: [US1] Escrever testes de integração para fluxo completo de logging
**Status**: [X] Concluído
**Tipo**: Integration Test  
**Arquivo**: `tests/integration/test_log_flow.py`  
**Dependências**: T002, T018  
**Story**: US1  
**Descrição**: Escrever testes de integração end-to-end:
- Log escrito em arquivo contém todos os campos esperados
- Múltiplos logs em sequência
- Diferentes categorias e níveis
- Arquivo é JSON válido linha por linha

**Test Cases**:
```python
def test_end_to_end_log_flow(temp_log_dir)
def test_multiple_logs_written_sequentially(temp_log_dir)
def test_all_categories_logged_correctly(temp_log_dir)
def test_log_file_contains_valid_json_per_line(temp_log_dir)
```

---

### T020: [US1] Validar schema_version field em todos os logs (FR-026)
**Status**: [X] Concluído
**Tipo**: Test (TDD)  
**Arquivo**: `tests/integration/test_log_flow.py`  
**Dependências**: T019, T005  
**Story**: US1  
**Descrição**: Escrever teste que valida que todos os logs gerados incluem campo `schema_version` com valor "1.0.0" em formato semantic versioning.

**Test Cases**:
```python
def test_all_logs_include_schema_version(temp_log_dir)
def test_schema_version_format_is_semantic_versioning(temp_log_dir)
def test_schema_version_is_1_0_0_for_initial_release(temp_log_dir)
```

**Acceptance Criteria**:
- ✅ Todos os logs incluem campo schema_version
- ✅ Valor é "1.0.0" (versão inicial)
- ✅ Formato validado contra regex ^\\d+\\.\\d+\\.\\d+$

---

### T021: [US1] [CHECKPOINT] Validar User Story 1
**Status**: [X] Concluído
**Tipo**: Validation  
**Dependências**: T019, T020  
**Story**: US1  
**Descrição**: Executar testes de aceitação da User Story 1:
- ✅ Logs de conexão são escritos com detalhes, timestamp e status
- ✅ Operações MCP capturam tool name, parâmetros, tempo de execução e resultado
- ✅ Erros incluem tipo de exceção, mensagem, stack trace e contexto
- ✅ Todos os logs são JSON válido parseable por ferramentas padrão
- ✅ Todos os logs incluem schema_version field (FR-027)

**Validation**: Todos os testes passam + cobertura >= 80% nos arquivos implementados.

---

## Phase 4: User Story 2 - Security Compliance (Priority P1)

**Goal**: Garantir redação automática de dados sensíveis e audit trail completo.

**Independent Test Criteria**: Executar operações com dados sensíveis (passwords, tokens) e verificar que logs contêm placeholders redagidos, não valores reais. Validar correlation IDs linkam toda operação.

### T022: [US2] Escrever testes para redação de dados sensíveis
**Status**: [X] Concluído
**Tipo**: Test (TDD)  
**Arquivo**: `tests/unit/test_redaction.py`  
**Dependências**: T002  
**Story**: US2  
**Descrição**: Escrever testes unitários para redação automática:
- Passwords em connection strings
- API keys
- Tokens
- Bearer tokens
- AMQP passwords
- Preservação de username para debugging

**Test Cases**:
```python
def test_redact_password_in_connection_string()
def test_redact_api_key()
def test_redact_token()
def test_redact_bearer_token()
def test_redact_amqp_password_preserves_username()
def test_redaction_works_in_nested_context()
def test_no_credentials_in_log_output()
```

---

### T023: [US2] Validar redação automática em pipeline structlog
**Status**: [X] Concluído
**Tipo**: Implementation Validation  
**Arquivo**: `src/logging/processors.py`  
**Dependências**: T022, T010  
**Story**: US2  
**Descrição**: Validar que processador de redação está corretamente integrado no pipeline structlog e todos os testes de redação passam.

**Acceptance Criteria**:
- ✅ Todos os testes T022 passam
- ✅ Nenhuma credencial aparece em logs escritos em arquivo
- ✅ Redação funciona para todos os patterns built-in

---

### T024: [US2] Escrever testes para correlation ID tracking
**Status**: [X] Concluído
**Tipo**: Test (TDD)  
**Arquivo**: `tests/unit/test_correlation.py`  
**Dependências**: T002  
**Story**: US2  
**Descrição**: Escrever testes unitários para correlation IDs:
- Geração de UUID v4
- Fallback para timestamp-based
- Propagação via contextvars
- Persistência em logs
- Rastreamento de operação completa

**Test Cases**:
```python
def test_generate_correlation_id_returns_uuid()
def test_correlation_id_fallback_to_timestamp()
def test_correlation_id_propagates_in_async_context()
def test_correlation_id_included_in_logs()
def test_multiple_operations_have_different_ids()
def test_nested_operations_share_correlation_id()
```

---

### T025: [US2] Validar correlation ID tracking em operações completas
**Status**: [X] Concluído
**Tipo**: Implementation Validation  
**Arquivo**: `src/logging/correlation.py`  
**Dependências**: T024, T007, T008  
**Story**: US2  
**Descrição**: Validar que correlation IDs são gerados, propagados e incluídos em todos os logs de uma operação.

**Acceptance Criteria**:
- ✅ Todos os testes T024 passam
- ✅ Correlation ID único gerado por invocação MCP
- ✅ Mesmo ID aparece em todos os logs da operação
- ✅ IDs diferentes para operações diferentes

---

### T026: [US2] Implementar secure file permissions para logs
**Status**: [X] Concluído
**Tipo**: Security Feature  
**Arquivo**: `src/logging/handlers/file.py`  
**Dependências**: T014  
**Story**: US2  
**Descrição**: Adicionar tentativa de set_permissions(600) após criar arquivo de log. Se falhar (ex: Windows), logar warning em stderr e continuar com permissões padrão.

**Message Formats**:

Success (DEBUG level):
```
DEBUG: Secure permissions (600) set successfully on log file {filepath}
```

Warning (if failure):
```
WARNING: Failed to set secure permissions (600) on log file {filepath}: {error_message}. Using OS default permissions. This may expose sensitive log data on multi-user systems.
```

**Acceptance Criteria**:
- ✅ Em Unix/Linux, arquivos criados com permissões 600 (owner rw only)
- ✅ Success message logado em DEBUG level quando permissões são definidas com sucesso
- ✅ Em Windows, tentativa é feita mas erro é silencioso (plataforma não suporta Unix permissions)
- ✅ Warning logado em stderr com formato especificado se set_permissions falhar em Unix/Linux
- ✅ Warning inclui filepath e mensagem de erro original
- ✅ Sistema continua operando mesmo se permissões não puderem ser definidas

---

### T027: [US2] Escrever testes de integração para audit trail
**Status**: [X] Concluído
**Tipo**: Integration Test  
**Arquivo**: `tests/integration/test_log_flow.py`  
**Dependências**: T019  
**Story**: US2  
**Descrição**: Escrever testes de integração para validar audit trail completo:
- Operação completa rastreável por correlation ID
- Início, progresso e fim da operação logados
- Erros linkados à operação via correlation ID
- Nenhuma credencial em nenhum log

**Test Cases**:
```python
def test_complete_operation_audit_trail(temp_log_dir)
def test_correlation_id_links_all_operation_logs(temp_log_dir)
def test_no_sensitive_data_in_any_log(temp_log_dir)
```

---

### T027A: [US2] Teste end-to-end de redação em arquivos de log
**Status**: [X] Concluído
**Tipo**: Integration Test  
**Arquivo**: `tests/integration/test_log_flow.py`  
**Dependências**: T027  
**Story**: US2  
**Descrição**: Escrever teste de integração que valida end-to-end que operações contendo credenciais resultam em arquivos de log sem plaintext credentials. Teste deve:
- Executar operações com passwords, tokens, API keys
- Ler arquivo de log escrito no filesystem
- Validar que ZERO credenciais plaintext aparecem em qualquer campo
- Validar que placeholders [REDACTED] estão presentes

**Test Cases**:
```python
def test_no_plaintext_credentials_in_log_files(temp_log_dir)
def test_redacted_placeholders_present_in_log_files(temp_log_dir)
def test_operations_with_credentials_produce_safe_logs(temp_log_dir)
```

**Acceptance Criteria**:
- ✅ Teste lê arquivo de log real do filesystem
- ✅ Regex scan não encontra nenhum pattern de credencial (password=, token=, Bearer, api_key=)
- ✅ Placeholders [REDACTED] confirmados presentes
- ✅ Teste cobre connection strings, API keys, tokens, bearer tokens

---

### T027B: [US2] Teste de backward compatibility para schema_version
**Status**: [X] Concluído
**Tipo**: Integration Test  
**Arquivo**: `tests/integration/test_schema_compatibility.py`  
**Dependências**: T020  
**Story**: US2  
**Descrição**: Escrever teste que valida backward compatibility quando schema_version muda. Parser antigo (v1.0.0) deve conseguir ler logs com versões futuras se mudanças forem apenas MINOR ou PATCH.

**Test Cases**:
```python
def test_old_parser_reads_logs_with_minor_version_bump()
def test_old_parser_reads_logs_with_patch_version_bump()
def test_parser_warns_on_major_version_mismatch()
def test_schema_version_increment_follows_semver_rules()
```

**Acceptance Criteria**:
- ✅ Parser v1.0.0 consegue ler logs v1.1.0 (MINOR bump, novos campos opcionais)
- ✅ Parser v1.0.0 consegue ler logs v1.0.1 (PATCH bump, mesmo schema)
- ✅ Parser v1.0.0 detecta e avisa sobre logs v2.0.0 (MAJOR bump, breaking changes)
- ✅ Teste valida regras de versionamento semântico

---

### T027C: [US2] Teste de fallback multi-destino
**Status**: [X] Concluído
**Tipo**: Integration Test  
**Arquivo**: `tests/integration/test_multi_destination.py`  
**Dependências**: T016, T014  
**Story**: US2  
**Descrição**: Escrever teste que valida cadeia de fallback quando múltiplos destinos falham. Ordem: File → Console → (RabbitMQ em Phase 8).

**Test Cases**:
```python
def test_file_failure_falls_back_to_console()
def test_console_never_raises_exception()
def test_logs_written_to_all_available_destinations()
def test_destination_failure_doesnt_block_operations()
```

**Acceptance Criteria**:
- ✅ Quando File handler falha, logs aparecem em Console
- ✅ Console handler nunca lança exceções (silent fallback)
- ✅ Quando ambos os destinos funcionam, logs escritos em ambos
- ✅ Falha de destino não bloqueia operação principal (<5ms overhead mantido)

---

### T028: [US2] [CHECKPOINT] Validar User Story 2
**Status**: [X] Concluído
**Tipo**: Validation  
**Dependências**: T027, T027A, T027B, T027C  
**Story**: US2  
**Descrição**: Executar testes de aceitação da User Story 2:
- ✅ Passwords em connection strings são substituídos por "[REDACTED]"
- ✅ Nenhuma credencial aparece em nenhum campo de log (validado por T027A)
- ✅ Arquivos de log no filesystem contêm zero plaintext credentials (validado por T027A)
- ✅ Schema version backward compatibility funciona (validado por T027B)
- ✅ Fallback multi-destino funciona corretamente (validado por T027C)
- ✅ Correlation ID único por invocação MCP
- ✅ Audit trail completo com who, what, when, outcome
- ✅ Arquivos de log têm permissões seguras (Unix) ou warning logado

**Validation**: Security scan passa + T027A/B/C pass + audit trail 100% completo + cobertura >= 80%.

---

## Phase 5: User Story 3 - Performance Monitoring (Priority P2)

**Goal**: Adicionar timing information e métricas de performance nos logs.

**Independent Test Criteria**: Executar operações e verificar que logs incluem timing data, duration, e overhead de logging é <5ms.

### T029: [US3] Escrever testes de performance para overhead de logging
**Status**: [X] Concluído
**Tipo**: Performance Test  
**Arquivo**: `tests/integration/test_performance.py`  
**Dependências**: T002  
**Story**: US3  
**Descrição**: Escrever testes de performance:

- Overhead médio <5ms por log entry
- Throughput com async logging
- Batching reduz syscalls

**Test Cases**:

```python
def test_log_overhead_under_5ms()
def test_async_logging_throughput()
def test_batching_reduces_syscalls()
def test_performance_with_large_context_data()
```

---

### T030: [US3] Implementar batching e flush otimizados em AsyncLogWriter
**Status**: [X] Concluído
**Tipo**: Performance Optimization  
**Arquivo**: `src/utils/async_writer.py`  
**Dependências**: T029, T012  
**Story**: US3  
**Descrição**: Otimizar AsyncLogWriter com batching configurável (batch_size, flush_interval). Usar orjson para serialização rápida. Implementar flush inteligente (batch cheio OU intervalo expirado).

**Acceptance Criteria**:

- ✅ Batching de múltiplos logs em single write
- ✅ Flush automático quando batch atinge batch_size
- ✅ Flush automático após flush_interval segundos
- ✅ Serialização com orjson (fast)
- ✅ Todos os testes T029 passam (overhead <5ms)

---

### T031: [US3] Adicionar helper para logging com timing automático
**Status**: [X] Concluído
**Tipo**: Helper Function  
**Arquivo**: `src/logging/logger.py`  
**Dependências**: T018  
**Story**: US3  
**Descrição**: Criar decorator `@log_timing` e context manager `with log_duration()` para capturar automaticamente timing de operações.

**Acceptance Criteria**:

- ✅ Decorator adiciona duration_ms ao log automaticamente
- ✅ Context manager captura início e fim da operação
- ✅ Timing usa time.perf_counter() para precisão
- ✅ Categoria Performance automaticamente aplicada

**Example**:

```python
@log_timing
async def slow_operation():
    await asyncio.sleep(0.1)
    
# Automaticamente loga com duration_ms
```

---

### T032: [US3] Escrever testes de integração para performance logging
**Status**: [X] Concluído
**Tipo**: Integration Test  
**Arquivo**: `tests/integration/test_performance.py`  
**Dependências**: T029  
**Story**: US3  
**Descrição**: Testar que logs de performance incluem duration_ms, categoria Performance, e overhead é aceitável.

**Test Cases**:

```python
def test_performance_logs_include_duration()
def test_decorator_captures_operation_timing()
def test_context_manager_captures_timing()
def test_async_operations_dont_block_logging()
```

---

### T033: [US3] [CHECKPOINT] Validar User Story 3
**Status**: [X] Concluído
**Tipo**: Validation  
**Dependências**: T032  
**Story**: US3  
**Descrição**: Executar testes de aceitação da User Story 3:
- ✅ Logs incluem duration_ms para operações
- ✅ Overhead de logging <5ms por operação
- ✅ Async logging previne blocking
- ✅ Performance metrics facilmente queryáveis

**Validation**: Performance benchmarks passam + overhead verificado <5ms + cobertura >= 80%.

---

## Phase 6: User Story 4 - Log Management (Priority P2)

**Goal**: Implementar rotação automática e organização de logs.

**Independent Test Criteria**: Rodar sistema através de múltiplos dias e limites de tamanho, verificar rotação correta e retenção de arquivos.

### T034: [US4] Escrever testes para rotação de arquivos
**Status**: [X] Concluído
**Tipo**: Test (TDD)  
**Arquivo**: `tests/unit/test_rotation.py`  
**Dependências**: T002  
**Story**: US4  
**Descrição**: Escrever testes unitários para rotação:
- Rotação por tamanho (100MB)
- Rotação por tempo (midnight)
- Compressão gzip
- Retenção de dias
- Naming pattern de arquivos

**Test Cases**:
```python
def test_rotate_on_size_limit()
def test_rotate_on_midnight()
def test_compression_of_rotated_files()
def test_retention_policy_deletes_old_files()
def test_rotated_file_naming_pattern()
def test_only_one_active_file_at_a_time()
```

---

### T035: [US4] Implementar lógica de rotação usando Python logging handlers
**Status**: [X] Concluído
**Tipo**: Rotation Implementation  
**Arquivo**: `src/logging/rotation.py`  
**Dependências**: T034  
**Story**: US4  
**Descrição**: Implementar wrapper que combina `TimedRotatingFileHandler` (rotação diária) e verificação manual de tamanho. Adicionar callbacks `namer` e `rotator` para compression gzip.

**Acceptance Criteria**:
- ✅ Rotação automática em midnight (UTC)
- ✅ Rotação automática quando arquivo atinge 100MB
- ✅ Arquivos rotacionados são comprimidos com gzip
- ✅ Arquivos mais antigos que retention_days são deletados
- ✅ Naming pattern: rabbitmq-mcp-YYYY-MM-DD.log (active), .log.gz (rotated)
- ✅ Todos os testes T034 passam

---

### T036: [US4] Integrar rotação no FileLogHandler
**Status**: [X] Concluído
**Tipo**: Integration  
**Arquivo**: `src/logging/handlers/file.py`  
**Dependências**: T035, T014  
**Story**: US4  
**Descrição**: Modificar `FileLogHandler` para usar lógica de rotação. Handler deve verificar rotação a cada write e acionar quando necessário.

**Acceptance Criteria**:
- ✅ FileLogHandler usa rotation logic transparentemente
- ✅ Rotação não perde logs (flush antes de rotate)
- ✅ Thread-safe (lock durante rotação)
- ✅ Performance não degradada (<5ms por write)

---

### T037: [US4] Escrever testes de integração para rotação completa
**Status**: [X] Concluído
**Tipo**: Integration Test  
**Arquivo**: `tests/integration/test_log_flow.py`  
**Dependências**: T019  
**Story**: US4  
**Descrição**: Testar rotação end-to-end:
- Arquivo rotaciona quando atinge size limit
- Arquivo rotaciona em mudança de dia (simular com mock time)
- Arquivos antigos são deletados após retention period
- Compression funciona corretamente

**Test Cases**:
```python
def test_rotation_on_file_size_limit(temp_log_dir)
def test_rotation_on_date_change(temp_log_dir)
def test_old_files_deleted_after_retention(temp_log_dir)
def test_rotated_files_are_gzipped(temp_log_dir)
```

---

### T038: [US4] [CHECKPOINT] Validar User Story 4
**Status**: [X] Concluído
**Tipo**: Validation  
**Dependências**: T037  
**Story**: US4  
**Descrição**: Executar testes de aceitação da User Story 4:
- ✅ Novo arquivo criado com data no filename em novo dia
- ✅ Rotação quando arquivo atinge 100MB
- ✅ Arquivos >30 dias são removidos/arquivados
- ✅ Arquivos rotacionados comprimidos com gzip
- ✅ Disk space sob controle

**Validation**: Rotação funciona corretamente + retenção aplicada + cobertura >= 80%.

---

## Phase 7: User Story 5 - Debugging Support (Priority P3)

**Goal**: Suportar debug-level logs detalhados para desenvolvimento.

**Independent Test Criteria**: Configurar log level DEBUG e verificar logs detalhados; configurar INFO e verificar debug logs são suprimidos.

### T039: [US5] Escrever testes para níveis de log configuráveis
**Status**: [X] Concluído
**Tipo**: Test (TDD)  
**Arquivo**: `tests/unit/test_logger.py`  
**Dependências**: T017  
**Story**: US5  
**Descrição**: Escrever testes para filtro de log level:
- DEBUG level mostra tudo
- INFO level suprime DEBUG
- WARN level suprime INFO e DEBUG
- ERROR level mostra apenas erros

**Test Cases**:
```python
def test_debug_level_shows_all_logs()
def test_info_level_suppresses_debug()
def test_warn_level_suppresses_info_and_debug()
def test_error_level_shows_only_errors()
def test_log_level_configurable_at_runtime()
```

---

### T040: [US5] Implementar filtering por log level em structlog
**Status**: [X] Concluído
**Tipo**: Configuration  
**Arquivo**: `src/logging/logger.py`  
**Dependências**: T039, T018  
**Story**: US5  
**Descrição**: Configurar `structlog.make_filtering_bound_logger()` com nível mínimo configurável. Permitir mudança de nível em runtime.

**Acceptance Criteria**:
- ✅ Logger filtra logs abaixo do nível mínimo configurado
- ✅ Nível pode ser alterado em runtime sem restart
- ✅ Filtering aplicado antes de processadores (performance)
- ✅ Todos os testes T039 passam

---

### T041: [US5] Implementar signal handlers para runtime config reload
**Status**: [X] Concluído
**Tipo**: Signal Handling  
**Arquivo**: `src/logging/config.py`, `tests/unit/test_config_reload.py`  
**Dependências**: T040  
**Story**: US5  
**Descrição**: Implementar signal handlers para recarregar configuração em runtime sem restart (FR-025):
- Unix/Linux/macOS: SIGHUP ou SIGUSR1 para reload (platform-specific signal handling)
- Windows: File watcher polling config file a cada 5 segundos (watchdog library or polling loop)
- Recarregar log_level, output settings, rotation config
- Thread-safe reload com locking

**Implementation Notes**:
- Use `signal.signal()` for Unix/Linux/macOS SIGHUP/SIGUSR1 handlers
- For Windows, implement file modification time polling with 5-second interval (justification: balances responsiveness vs CPU overhead; config changes are infrequent operations; interval is configurable via LOGGING_CONFIG_POLL_INTERVAL_MS env var)
- Consider using `watchdog` library for cross-platform file monitoring (optional optimization)
- All config reload operations must acquire lock before modifying logger configuration

**Acceptance Criteria**:
- ✅ SIGHUP/SIGUSR1 dispara reload no Unix/Linux/macOS
- ✅ File watcher detecta mudanças no Windows (polling 5s)
- ✅ Reload aplica nova configuração imediatamente
- ✅ Reload é thread-safe (não corrompe estado)
- ✅ Testes cobrem reload em múltiplas plataformas

**Test Cases**:
```python
def test_sighup_triggers_config_reload_unix()
def test_sigusr1_triggers_config_reload_unix()
def test_file_watcher_detects_config_changes_windows()
def test_reload_applies_new_log_level()
def test_reload_is_thread_safe()
```

---

### T042: [US5] [CHECKPOINT] Validar User Story 5
**Status**: [X] Concluído
**Tipo**: Validation  
**Dependências**: T041  
**Story**: US5  
**Descrição**: Executar testes de aceitação da User Story 5:
- ✅ DEBUG level mostra detalhes internos
- ✅ INFO level suprime debug logs
- ✅ Log level pode ser alterado sem restart via signal
- ✅ Performance não degradada com DEBUG desabilitado

**Validation**: Filtering funciona corretamente + signal reload ok + cobertura >= 80%.

---

## Phase 8: User Story 6 - RabbitMQ Log Destination (Priority P2 - Optional)

**Goal**: Publicar logs em exchange RabbitMQ dedicada para consumo em tempo real (Priority P2 - optional for MVP per updated spec.md).

**Independent Test Criteria**: Configurar RabbitMQ destination, executar operações, verificar logs publicados em exchange com routing keys corretos.

### T043: [US6] Escrever testes para RabbitMQLogHandler
**Status**: [X] Concluído
**Tipo**: Test (TDD)  
**Arquivo**: `tests/unit/handlers/test_rabbitmq_handler.py`  
**Dependências**: T002  
**Story**: US6 (Priority P2 - Optional)  
**Descrição**: Escrever testes unitários para RabbitMQLogHandler:
- Conexão com RabbitMQ
- Publicação de logs em exchange
- Routing key pattern {level}.{category}
- Mensagens persistentes
- Graceful degradation se broker indisponível

**Test Cases**:
```python
def test_rabbitmq_handler_connects_to_broker()
def test_handler_publishes_log_to_exchange()
def test_routing_key_pattern_applied()
def test_messages_are_persistent()
def test_handler_fails_gracefully_if_broker_down()
```

---

### T044: [US6] Implementar RabbitMQLogHandler [P]
**Status**: [X] Concluído
**Tipo**: Handler Implementation  
**Arquivo**: `src/logging/handlers/rabbitmq.py`  
**Dependências**: T043  
**Story**: US6 (Priority P2 - Optional)  
**Descrição**: Implementar RabbitMQLogHandler que publica logs em exchange topic. Routing key = "{level}.{category}". Mensagens persistentes (delivery_mode=2). Graceful failure se broker indisponível.

**Acceptance Criteria**:
- ✅ Handler se conecta ao RabbitMQ via pika
- ✅ Declara exchange tipo topic (durable)
- ✅ Publica logs com routing key {level}.{category}
- ✅ Mensagens são persistentes
- ✅ Não quebra sistema se broker down (fallback para console)
- ✅ Todos os testes T043 passam

---

### T045: [US6] Adicionar configuração de RabbitMQ destination
**Status**: [X] Concluído
**Tipo**: Configuration  
**Arquivo**: `src/models/log_config.py`, `config/logging_config.yaml`  
**Dependências**: T006  
**Story**: US6 (Priority P2 - Optional)  
**Descrição**: Adicionar campos de configuração para RabbitMQ destination:
- enabled (bool)
- host, port, vhost, username, password
- exchange name
- routing_key_pattern

**Acceptance Criteria**:
- ✅ LogConfig suporta RabbitMQ destination config
- ✅ YAML config permite habilitar/desabilitar RabbitMQ
- ✅ Validação de configuração RabbitMQ

---

### T046: [US6] Integrar RabbitMQLogHandler no logger principal
**Status**: [X] Concluído
**Tipo**: Integration  
**Arquivo**: `src/logging/logger.py`  
**Dependências**: T044, T045, T018  
**Story**: US6 (Priority P2 - Optional)  
**Descrição**: Modificar `get_logger()` para adicionar RabbitMQLogHandler se habilitado em config. Multi-destination logging (File + RabbitMQ + Console fallback).

**Acceptance Criteria**:
- ✅ RabbitMQLogHandler adicionado se config.rabbitmq.enabled = true
- ✅ Logs escritos em múltiplos destinos simultaneamente
- ✅ Failure em um destino não afeta outros
- ✅ Console fallback sempre disponível

---

### T047: [US6] [CHECKPOINT] Validar User Story 6 (Priority P2 - Optional)
**Status**: [X] Concluído
**Tipo**: Validation  
**Dependências**: T046  
**Story**: US6 (Priority P2 - Optional)  
**Descrição**: Executar testes de aceitação da User Story 6:
- ✅ Logs publicados em exchange RabbitMQ
- ✅ Routing keys corretos ({level}.{category})
- ✅ Consumidores podem filtrar por routing key
- ✅ Sistema continua funcionando se broker indisponível

**Validation**: RabbitMQ destination funciona + filtering por routing key ok + cobertura >= 80%.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Goal**: Finalizações, validação de schemas, documentation.

### T048: [Polish] Implementar graceful shutdown com signal handling e flush de logs (FR-028)
**Status**: [X] Concluído
**Tipo**: Core Feature  
**Arquivo**: `src/utils/async_writer.py`, `src/logging/logger.py`, `tests/integration/test_graceful_shutdown.py`  
**Dependências**: T012, T018  
**Descrição**: Implementar signal handlers (SIGTERM, SIGINT, SIGHUP) que bloqueiam shutdown até todos os logs buffered serem escritos. Adicionar método `shutdown()` em AsyncLogWriter que realiza flush completo do async buffer.

**Acceptance Criteria**:
- ✅ Signal handlers registrados para SIGTERM, SIGINT, normal exit
- ✅ Shutdown bloqueia até AsyncLogWriter.flush() completar
- ✅ Zero perda de logs durante shutdown
- ✅ Timeout de 30 segundos para flush (prevent hang)
- ✅ Teste de integração valida flush completo

---

### T049: [Polish] Escrever testes de contrato para JSON schema validation
**Status**: [X] Concluído
**Tipo**: Contract Test  
**Arquivo**: `tests/contract/test_log_schema.py`  
**Dependências**: T002  
**Descrição**: Escrever testes que validam logs gerados contra JSON schemas:
- LogEntry.schema.json
- LogConfig.schema.json
- Todos os campos obrigatórios presentes
- Tipos corretos
- Constraints validados

**Test Cases**:
```python
def test_log_entry_validates_against_schema()
def test_log_config_validates_against_schema()
def test_required_fields_present()
def test_field_types_correct()
def test_constraints_enforced()
```

---

### T050: [Polish] Validar cobertura de testes >= 80% e gerar relatório
**Status**: [X] Concluído
**Tipo**: Coverage Validation  
**Dependências**: T049, todos os checkpoints  
**Descrição**: Executar `pytest --cov=src/logging --cov-report=html --cov-report=term` e validar cobertura >= 80% conforme constitution. Gerar relatório HTML.

**Acceptance Criteria**:
- ✅ Cobertura total >= 80% (Achieved: **83%**)
- ✅ Todos os módulos principais >= 80%
- ✅ Relatório HTML gerado para review (htmlcov/)
- ✅ Uncovered lines identificadas e documentadas (se aceitáveis)

**Coverage Results**:
- **Overall: 83%** (1067 statements, 186 missed)
- src/logging/logger.py: 81%
- src/logging/handlers/file.py: 83%
- src/logging/handlers/rabbitmq.py: 84%
- src/utils/async_writer.py: 87%
- src/models/log_entry.py: 87%
- src/models/log_config.py: 91%
- src/logging/redaction.py: 92%
- src/logging/processors.py: 100%

---

## Dependencies Graph

```
Phase 1 (Setup) → Phase 2 (Foundation) → Phases 3-7 (User Stories) → Phase 8 (Polish)
                                          ↓           ↓           ↓
                                          US1 (P1) ← US2 (P1)    
                                          ↓
                                          US3 (P2) ← US4 (P2) ← US5 (P3) ← US6 (Bonus)
```

**Foundation Blocks User Stories**: Phase 2 deve completar antes de qualquer User Story começar.

**US1 e US2 são parallelizáveis**: Após Foundation, US1 (Observability) e US2 (Security) podem ser implementadas em paralelo pois não têm dependências entre si.

**US3 depende de US1**: Performance testing precisa de logging básico funcionando.

**US4 é independente**: Log rotation pode ser implementado em paralelo com US3.

**US5 depende de US1**: Debug levels são extensão do logger principal.

**US6 é independente após US1**: RabbitMQ destination pode ser adicionado a qualquer momento após logger básico.

---

## Parallel Execution Opportunities

### Setup Phase (Todas parallelizáveis - [P])
- T001, T002, T003, T004 podem executar simultaneamente

### Foundation Phase
- T005, T006 (Models) [P]
- T007 (Correlation) → T008 (Processor) [Sequential]
- T009 (Redaction) → T010 (Processor) [Sequential]
- T011 depende de T008, T010
- T012 é independente [P]

### User Story 1 (US1)
- T013 (FileHandler tests), T015 (ConsoleHandler tests) [P]
- T014 (FileHandler impl), T016 (ConsoleHandler impl) [P after tests]
- T017 (Logger tests) → T018 (Logger impl) [Sequential]

### User Story 2 (US2) - Parallelizável com US1
- T022 (Redaction tests) [P]
- T024 (Correlation tests) [P]
- T023, T025 validam implementação existente [P after tests]

### User Story 3 (US3)
- T029 (Performance tests) → T030 (Batching) [Sequential]
- T031 (Helpers) [P]

### User Story 4 (US4) - Parallelizável com US3
- T034 (Rotation tests) → T035 (Rotation impl) [Sequential]

### User Story 6 (US6 Constitution Required) - Parallelizável após US1
- T042 (RabbitMQ tests) → T043 (RabbitMQ impl) [Sequential]

---

## Implementation Strategy

1. **MVP Scope (Minimum Viable Product)**:
   - Phase 1: Setup ✅
   - Phase 2: Foundation ✅
   - Phase 3: User Story 1 (System Observability - P1) ✅
   - Phase 4: User Story 2 (Security Compliance - P1) ✅
   - Phase 5: User Story 3 (Performance Monitoring - P2) ✅
   - Phase 6: User Story 4 (Log Management - P2) ✅
   
   **MVP Delivers**: Logging estruturado funcional, seguro, com redação automática, audit trail completo, performance otimizada, rotação automática. 2 destinos configuráveis (File + Console) atendem requisito constitucional.

2. **Phase 2 Enhancements (Optional)**:
   - Phase 7: User Story 5 (Debugging Support - P3) ✅
   - Phase 8: User Story 6 (RabbitMQ AMQP Destination - P2) ✅
   
   **Phase 2 Delivers**: Debug support avançado e integração RabbitMQ para streaming real-time (validar demanda real antes de implementar).

---

## Success Criteria Summary

| User Story | Criteria | Validation Method |
|------------|----------|-------------------|
| US1 - Observability | Logs estruturados JSON parseable | Integration tests + manual verification |
| US2 - Security | Zero credentials em logs, 100% traceability | Security scan + audit trail verification |
| US3 - Performance | Overhead <5ms, async logging | Performance benchmarks |
| US4 - Rotation | Rotação automática, disk space sob controle | Integration tests + manual verification |
| US5 - Debug | Debug level configurável | Unit tests + manual verification |
| US6 - RabbitMQ | Logs em exchange topic | Integration tests + consumer verification |

**Overall Success**: 
- ✅ 80%+ test coverage
- ✅ All user story checkpoints passed
- ✅ Constitution compliance validated
- ✅ Performance benchmarks met (<5ms overhead)
- ✅ Security scan passed (zero credentials)

---

## Next Steps

1. **Start Implementation**: Begin with Phase 1 (Setup) - execute T001-T004
2. **TDD Workflow**: For each task, write tests first → verify they fail → implement → verify they pass
3. **Checkpoint Validation**: After each user story phase, validate all acceptance criteria
4. **Coverage Monitoring**: Check coverage after each phase, ensure trending toward 80%+
5. **Constitution Check**: Validate compliance after MVP (US1+US2) completion

---

## Notes

- **TDD Obrigatório**: Constitution exige testes antes de implementação
- **Cobertura 80%+**: Mínimo constitucional para todos os módulos
- **Performance Critical**: FR-016 (<5ms overhead) deve ser validado continuamente
- **Security Non-Negotiable**: FR-004 (redação automática, zero credentials) P1 requirement
- **Parallel Opportunities**: Aproveitar tarefas [P] para acelerar desenvolvimento
- **Incremental Delivery**: MVP primeiro (US1+US2), depois features adicionais
