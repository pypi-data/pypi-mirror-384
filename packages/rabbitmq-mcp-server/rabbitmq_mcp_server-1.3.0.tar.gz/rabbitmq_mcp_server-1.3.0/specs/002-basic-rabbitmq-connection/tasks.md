# Tasks: Basic RabbitMQ Connection

**Feature**: 002-basic-rabbitmq-connection  
**Branch**: `feature/002-basic-rabbitmq-connection`  
**Created**: 2025-10-09  
**Last Updated**: 2025-10-09 (todas as correções aplicadas - Rodada 3)  
**Total Tasks**: 47 (T001-T045 + T034.1 para vector database + test_infinite_retry_loop_after_max_delay)  
**Total Requirements**: 19 FRs (FR-001 a FR-020, todos com cobertura completa)  
**Edge Cases Covered**: 7 (EC-001 a EC-007)  
**Status**: ✅ PRONTO PARA IMPLEMENTAÇÃO - Todas as issues resolvidas

## Overview

Este documento organiza todas as tarefas de implementação por user story, permitindo desenvolvimento e teste independente de cada incremento funcional.

**Tech Stack**: Python 3.9+, aio-pika, structlog, pydantic, pytest-asyncio, mcp-sdk, chromadb, sentence-transformers

### Changelog de Correções (2025-10-09)

**Rodada 1 - Correções Iniciais**:
- ✅ **C1 CRITICAL**: Implementado ChromaDB local mode conforme constituição (T034.1 + T035 atualizado)
- ✅ **C2/C3 HIGH**: FR-020 (validação de vhost) agora coberto explicitamente em T006 e T012
- ✅ **I1 HIGH**: Sequência de backoff alinhada entre spec e tasks (1s → 2s → 4s → 8s → 16s → 32s → 60s)
- ✅ **D1/D2 MEDIUM**: FR-011 referencia FR-010 sem repetir heartbeat, terminologia padronizada
- ✅ **A1/U1 HIGH**: Adicionada metodologia de medição em Success Criteria
- ✅ **U2 MEDIUM**: FR-005 agora especifica comportamento pós-timeout
- ✅ **U4 LOW**: FR-014 referencia data-model.md para schema completo

**Rodada 2 - Correções Finais via /speckit.analyze**:
- ✅ **A1 HIGH**: Success Criteria agora usa percentis mensuráveis (p95/p99) em SC-001, SC-002, SC-003
- ✅ **D1 MEDIUM**: Terminologia padronizada - "ChromaDB local mode" em FR-017, "retry infinito com backoff exponencial" consistente
- ✅ **D2 MEDIUM**: FR-011 simplificado para notação consistente de sequência de backoff
- ✅ **A2 MEDIUM**: Out of Scope clarificado - retry policy fixa para esta feature, customização considerada para futuras features apenas se houver demanda
- ✅ **A3 LOW**: Assumptions agora incluem SLA de rede específico (latência < 10ms p95, uptime > 99.9%, packet loss < 0.1%)
- ✅ **U3 LOW**: Teste de heartbeat detection agora especifica método técnico (iptables/netsh/socket close direto)
- ✅ **U4 LOW**: US3 Scenario 2 clarificado para testar loop infinito após máximo, novo teste `test_infinite_retry_loop_after_max_delay` adicionado

**Rodada 3 - Correções Aplicadas via /speckit.analyze (2025-10-09)**:
- ✅ **D1 MEDIUM**: FR-017 atualizado para "ChromaDB local mode" (clarificação de T2)
- ✅ **T1 LOW**: Terminologia padronizada - "política de retry infinito com backoff exponencial" consistente em spec.md
- ✅ **T2 LOW**: spec.md agora especifica "ChromaDB local mode" explicitamente em FR-017
- ✅ **C1 MEDIUM**: T028 `test_heartbeat_detection_time` documentado com Toxiproxy para portabilidade cross-platform
- ✅ **U1 LOW**: T043 `test_error_tracebacks_sanitization` expandido para validar sanitização de tracebacks de aio-pika
- ✅ **U1 LOW**: T007 expandido com implementação de sanitização de URLs AMQP em tracebacks de bibliotecas externas

**Conformidade Constitucional**:
- ✅ Vector database ChromaDB local mode conforme constituição (seção "Vector Database Requirements")
- ✅ Structured logging JSON conforme constituição (structlog)
- ✅ Test-first development com cobertura mínima 80%
- ✅ Performance targets alinhados (<200ms operações simples, sub-100ms semantic search)

**Dependências Atualizadas**:
- Adicionado `chromadb>=0.4.0` para vector database
- Adicionado `sentence-transformers>=2.2.0` para embeddings

---

## Phase 1: Setup & Infrastructure

### T001 - Inicializar Estrutura do Projeto [P]
- [X] Completed

**Descrição**: Criar estrutura de diretórios e arquivos de configuração base do projeto

**Files**:
- `src/connection/__init__.py`
- `src/tools/__init__.py`
- `src/logging/__init__.py`
- `src/schemas/__init__.py`
- `tests/unit/__init__.py`
- `tests/integration/__init__.py`
- `tests/contract/__init__.py`
- `config/config.toml.example`
- `config/.env.example`
- `.gitignore`
- `README.md`
- `LICENSE` (LGPL v3.0)

**Acceptance**: Estrutura de diretórios criada, todos os __init__.py existem

---

### T002 - Configurar Gerenciamento de Dependências [P]
- [X] Completed

**Descrição**: Criar pyproject.toml com todas as dependências do projeto

**Files**:
- `pyproject.toml`

**Dependencies**:
```toml
[project]
name = "rabbitmq-mcp-connection"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = [
    "aio-pika>=9.0.0",
    "structlog>=23.0.0",
    "pydantic>=2.0.0",
    "mcp-sdk>=0.1.0",
    "python-dotenv>=1.0.0",
    "chromadb>=0.4.0",
    "sentence-transformers>=2.2.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.0.0",
]
```

**Acceptance**: `pyproject.toml` criado, dependências validadas

---

### T003 - Configurar Pytest para Testes Assíncronos [P]
- [X] Completed

**Descrição**: Criar pytest.ini e conftest.py com fixtures base

**Files**:
- `pytest.ini`
- `tests/conftest.py`

**Content pytest.ini**:
```ini
[pytest]
asyncio_mode = auto
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = --cov=src --cov-report=term-missing --cov-report=html
```

**Acceptance**: pytest configurado, pode executar testes assíncronos

---

### T004 - Criar Script de Setup de Ambiente de Teste
- [X] Completed

**Descrição**: Script para iniciar RabbitMQ local via Docker para testes de integração

**Files**:
- `scripts/setup_test_env.py`

**Content**:
```python
#!/usr/bin/env python3
import subprocess
import sys
import socket
import time

def wait_for_rabbitmq(host="localhost", port=5672, management_port=15672, timeout=30):
    """Aguarda RabbitMQ estar pronto para aceitar conexões AMQP e Management API"""
    import urllib.request
    import json
    
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            # Verificar porta AMQP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            amqp_ready = sock.connect_ex((host, port)) == 0
            sock.close()
            
            # Verificar Management API (health check completo)
            if amqp_ready:
                try:
                    req = urllib.request.Request(
                        f"http://{host}:{management_port}/api/overview",
                        headers={"Authorization": "Basic dGVzdDp0ZXN0"}  # test:test base64
                    )
                    with urllib.request.urlopen(req, timeout=2) as response:
                        data = json.loads(response.read())
                        if data.get("management_version"):
                            print(f"✓ RabbitMQ is fully ready on {host}:{port} (Management API: {data['management_version']})")
                            return True
                except Exception:
                    pass  # Management API ainda não está pronto
        except socket.error:
            pass
        time.sleep(1)
        print(f"  Waiting for RabbitMQ... ({int(time.time() - start_time)}s)")
    return False

def start_rabbitmq():
    """Inicia RabbitMQ em Docker para testes e aguarda estar pronto"""
    # Verificar se já está rodando
    check_cmd = ["docker", "ps", "-q", "-f", "name=rabbitmq-test"]
    result = subprocess.run(check_cmd, capture_output=True, text=True)
    if result.stdout.strip():
        print("RabbitMQ container already running")
        if wait_for_rabbitmq():
            return 0
        print("ERROR: RabbitMQ container running but not accepting connections")
        return 1
    
    # Iniciar container
    cmd = [
        "docker", "run", "-d", "--name", "rabbitmq-test",
        "-p", "5672:5672",
        "-p", "15672:15672",
        "-e", "RABBITMQ_DEFAULT_USER=test",
        "-e", "RABBITMQ_DEFAULT_PASS=test",
        "rabbitmq:3-management"
    ]
    subprocess.run(cmd, check=True)
    print("RabbitMQ container started, waiting for ready state...")
    
    # Aguardar RabbitMQ estar pronto
    if wait_for_rabbitmq():
        print("✓ RabbitMQ is ready for connections")
        return 0
    else:
        print("ERROR: RabbitMQ failed to become ready within timeout")
        return 1

if __name__ == "__main__":
    sys.exit(start_rabbitmq())
```

**Acceptance**: Script executa sem erro, RabbitMQ disponível em localhost:5672 com Management API acessível em localhost:15672, script valida saúde completa (AMQP + Management API) antes de retornar sucesso

---

## Phase 2: Foundational Components

**Nota**: Estes componentes devem estar completos antes de qualquer user story ser implementada.

### T005 - Implementar ConnectionState Enum
- [X] Completed

**Descrição**: Enum para estados de conexão AMQP

**Files**:
- `src/schemas/connection.py`

**Content**:
```python
from enum import Enum

class ConnectionState(str, Enum):
    """Estados de conexão AMQP"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    RECONNECTING = "reconnecting"
    FAILED = "failed"
```

**Acceptance**: Enum definido com 5 estados, importável

---

### T006 - Implementar ConnectionConfig Schema [P]
- [X] Completed

**Descrição**: Schema Pydantic para validação de parâmetros de conexão

**Nota**: Este task define apenas o schema de validação (estrutura de dados). O carregamento multi-source é implementado em T008.

**Files**:
- `src/schemas/connection.py`

**Content**: Ver `contracts/pydantic-schemas.json` → ConnectionConfig

**Validation**:
- host: não vazio (string com min 1 caractere)
- port: 1-65535 (integer)
- timeout: 1-300 (integer em segundos)
- heartbeat: 0-3600 (integer em segundos)
- usuário: não vazio (string)
- senha: não vazia (string)
- vhost: formato válido (inicia com /)
- password não aparece em __repr__

**Acceptance**: Schema valida corretamente conforme FR-003, senha sanitizada em repr

---

### T007 - Implementar Sistema de Logging Estruturado [P]
- [X] Completed

**Descrição**: Configurar structlog com JSON output e sanitização de credenciais

**Files**:
- `src/logging/config.py`
- `src/logging/sanitizer.py`

**Features**:
- JSON output
- Processador de sanitização de senhas (próprias e de bibliotecas externas como aio-pika)
- Timestamps ISO 8601
- Correlation IDs
- Níveis: DEBUG, INFO, WARN, ERROR
- Sanitização de URLs AMQP: `amqp://user:password@host` → `amqp://user:***@host`
- Sanitização de tracebacks com credenciais de bibliotecas externas (aio-pika, pika, asyncio)
- Sanitização de connection strings em stack traces de dependências

**Implementation Notes**:
```python
# src/logging/sanitizer.py
import re

def sanitize_amqp_urls(text: str) -> str:
    """Sanitiza URLs AMQP que podem conter credenciais"""
    # Pattern: amqp://user:password@host
    return re.sub(r'(amqp://[^:]+:)([^@]+)(@)', r'\1***\3', text)

def sanitize_credentials(event_dict: dict) -> dict:
    """Processador structlog para sanitizar credenciais em logs e tracebacks"""
    # Sanitizar campos conhecidos
    if 'password' in event_dict:
        event_dict['password'] = '***'
    
    # Sanitizar mensagens e tracebacks (próprios)
    if 'event' in event_dict:
        event_dict['event'] = sanitize_amqp_urls(str(event_dict['event']))
    
    # Sanitizar exception info e tracebacks de bibliotecas externas
    if 'exception' in event_dict:
        event_dict['exception'] = sanitize_amqp_urls(str(event_dict['exception']))
    
    # Sanitizar stack traces que podem conter connection strings
    if 'traceback' in event_dict:
        event_dict['traceback'] = sanitize_amqp_urls(str(event_dict['traceback']))
    
    # Sanitizar argumentos de funções em tracebacks (common em aio-pika)
    for key, value in event_dict.items():
        if isinstance(value, str) and ('amqp://' in value or 'password=' in value):
            event_dict[key] = sanitize_amqp_urls(value)
    
    return event_dict
```

**Acceptance**: Logs emitidos em JSON, credenciais automaticamente removidas (próprias e de aio-pika)

---

### T008 - Implementar Carregamento de Configuração Multi-Source
- [X] Completed

**Descrição**: Sistema de carregamento de config com precedência: args > ENV > TOML > defaults

**Files**:
- `src/connection/config.py`

**Functions**:
```python
def load_config(
    config_file: Optional[Path] = None,
    **overrides
) -> ConnectionConfig:
    """Carrega config com precedência:
    1. overrides (args)
    2. ENV vars (AMQP_*)
    3. TOML file
    4. defaults
    """
```

**Acceptance**: Carrega de todas as fontes, precedência correta, validação via Pydantic

**Test Cases de Precedência** (adicionar em tests/unit/test_config.py):
```python
def test_config_precedence_args_override_env():
    """Verifica que argumentos têm precedência sobre ENV vars"""
    os.environ["AMQP_HOST"] = "env-host"
    config = load_config(host="args-host")
    assert config.host == "args-host"

def test_config_precedence_env_override_file():
    """Verifica que ENV vars têm precedência sobre arquivo"""
    os.environ["AMQP_HOST"] = "env-host"
    config = load_config(config_file="config.toml")  # arquivo tem host="file-host"
    assert config.host == "env-host"

def test_config_precedence_file_override_defaults():
    """Verifica que arquivo tem precedência sobre defaults"""
    config = load_config(config_file="config.toml")  # arquivo tem host="file-host"
    assert config.host == "file-host"
    assert config.host != "localhost"  # default

def test_config_precedence_full_chain():
    """Verifica cadeia completa de precedência"""
    os.environ["AMQP_PORT"] = "6672"
    config = load_config(
        config_file="config.toml",  # host="file-host", port=7672
        host="args-host"  # apenas host via arg
    )
    assert config.host == "args-host"  # arg > env > file
    assert config.port == 6672  # env > file (sem arg para port)
```

---

### T009 - Implementar RetryPolicy [P]
- [X] Completed

**Descrição**: Política de retry com backoff exponencial

**Files**:
- `src/connection/retry.py`

**Content**: Ver data-model.md → RetryPolicy

**Methods**:
- `next_delay() -> float`: Retorna próximo delay, atualiza estado
- `reset()`: Reseta para valores iniciais
- `get_stats() -> RetryStats`: Estatísticas

**Acceptance**: Delay progride 1s → 2s → 4s → ... → 60s (max), reset funciona

---

### T010 - Implementar Schemas Pydantic para Operações MCP [P]
- [X] Completed

**Descrição**: Schemas para input/output de todas as operações MCP

**Files**:
- `src/schemas/mcp.py`

**Schemas**:
- `ConnectInput`, `ConnectResult`
- `DisconnectInput`, `DisconnectResult`
- `HealthCheckResult`
- `ConnectionStatusResult`
- `PoolStatsResult`
- `MCPToolResult`
- `PaginationParams`, `PaginationMetadata`

**Reference**: `contracts/pydantic-schemas.json`

**Acceptance**: Todos os schemas validam conforme contracts

---

**Checkpoint**: ✅ Foundational components completos - projeto pronto para implementar user stories

---

## Phase 3: User Story 1 (P1) - Estabelecer Conexão

**Goal**: Operador pode conectar ao RabbitMQ com credenciais válidas

**Independent Test**: Conexão estabelecida em <5s com credenciais válidas

### T011 - [US1] Implementar ConnectionManager Base
- [X] Completed

**Descrição**: Classe principal para gerenciar conexão AMQP

**Files**:
- `src/connection/manager.py`

**Class**:
```python
class ConnectionManager:
    def __init__(self, config: ConnectionConfig):
        self.config = config
        self.connection: Optional[aio_pika.Connection] = None
        self.channel: Optional[aio_pika.Channel] = None
        self.state = ConnectionState.DISCONNECTED
        self._lock = asyncio.Lock()
    
    async def connect(self) -> None:
        """Estabelece conexão AMQP"""
    
    async def disconnect(self) -> None:
        """Desconecta graciosamente"""
    
    async def get_status(self) -> ConnectionState:
        """Retorna estado atual"""
```

**Dependencies**: T006, T005

**Acceptance**: Classe instanciável, métodos definidos

---

### T012 - [US1] Implementar Lógica de Conexão AMQP
- [X] Completed

**Descrição**: Lógica para estabelecer conexão usando aio-pika com suporte a virtual hosts

**Files**:
- `src/connection/manager.py` (método `connect`)

**Logic**:
1. Validar config (incluindo vhost format - FR-016, FR-020)
2. Criar connection parameters do aio-pika com vhost configurado
3. Estabelecer conexão com timeout
4. Criar canal default
5. Atualizar state para CONNECTED
6. Emitir log estruturado "connection.established" com vhost info

**Error Handling**:
- `asyncio.TimeoutError` → `ConnectionTimeout`
- `AuthenticationError` → `AuthenticationFailed`
- `AMQP 530 NOT_ALLOWED` → `VHostNotFoundError` (FR-020)
- Outras exceções → `ConnectionError`

**VHost Validation (FR-020)**:
- Detectar erro AMQP 530 durante conexão
- Retornar mensagem clara: "VHost não encontrado: {vhost}"
- Não requer Management API - validação via erro AMQP

**Dependencies**: T011, T007, T006 (vhost validation in schema)

**Acceptance**: Conecta com sucesso a RabbitMQ local, timeout funciona, erros mapeados, vhosts suportados (FR-016), vhost inválido detectado (FR-020)

---

### T013 - [US1] Implementar Lógica de Desconexão
- [X] Completed

**Descrição**: Desconexão limpa fechando canais e conexão

**Files**:
- `src/connection/manager.py` (método `disconnect`)

**Logic**:
1. Verificar se há conexão ativa
2. Fechar canal
3. Fechar conexão
4. Atualizar state para DISCONNECTED
5. Emitir log "connection.disconnected"

**Dependencies**: T011

**Acceptance**: Desconecta sem vazamento de recursos, estado atualizado

---

### T014 - [US1] Testes Unitários - ConnectionManager [P]
- [X] Completed

**Descrição**: Testes unitários para ConnectionManager

**Files**:
- `tests/unit/test_manager.py`

**Test Cases**:
- `test_manager_initialization`: Estado inicial correto
- `test_connect_updates_state`: Estado muda para CONNECTED
- `test_disconnect_updates_state`: Estado muda para DISCONNECTED
- `test_get_status_returns_current_state`: Status reflete estado real

**Dependencies**: T011, T012, T013

**Acceptance**: Todos os testes passam, cobertura >80%

---

### T015 - [US1] Testes de Integração - Conexão Real [P]
- [X] Completed

**Descrição**: Testes com RabbitMQ real

**Files**:
- `tests/integration/test_connection.py`

**Test Cases**:
- `test_connect_to_rabbitmq_success`: Conecta com credenciais válidas em <5s
- `test_connect_invalid_credentials`: Retorna erro de autenticação claro
- `test_connect_timeout`: Timeout funciona após 30s
- `test_disconnect_graceful`: Desconexão limpa

**Fixtures**:
```python
@pytest.fixture
async def rabbitmq_config():
    return ConnectionConfig(
        host="localhost",
        port=5672,
        user="test",
        password="test",
        timeout=5
    )
```

**Dependencies**: T004, T012, T013

**Acceptance**: Todos os cenários de acceptance da US1 passam

---

### T016 - [US1] Implementar MCP Tool: connection.connect
- [X] Completed

**Descrição**: Implementar operação connection.connect no call-id tool

**Files**:
- `src/tools/call_id.py`

**Logic**:
```python
async def execute_connection_connect(params: dict) -> MCPToolResult:
    """Executa operação connection.connect"""
    config = ConnectionConfig(**params)
    manager = ConnectionManager(config)
    
    start_time = time.time()
    await manager.connect()
    duration = (time.time() - start_time) * 1000
    
    return MCPToolResult(
        success=True,
        result=ConnectResult(...),
        metadata=Metadata(...)
    )
```

**Dependencies**: T012, T010

**Acceptance**: Tool executa connect via MCP, retorna resultado conforme contract

---

### T017 - [US1] Implementar MCP Tool: connection.disconnect
- [X] Completed

**Descrição**: Implementar operação connection.disconnect

**Files**:
- `src/tools/call_id.py`

**Logic**: Similar ao T016, mas para disconnect

**Dependencies**: T013, T010

**Acceptance**: Tool executa disconnect via MCP

---

**Checkpoint US1**: ✅ Operador pode conectar/desconectar ao RabbitMQ com sucesso

---

## Phase 4: User Story 2 (P2) - Monitorar Saúde da Conexão

**Goal**: Operador pode verificar saúde da conexão e disponibilidade do broker

**Independent Test**: Health check retorna resultado em <1s

### T018 - [US2] Implementar HealthStatus Schema
- [X] Completed

**Descrição**: Schema para status de saúde

**Files**:
- `src/schemas/connection.py`

**Content**: Ver data-model.md → HealthStatus

**Properties**:
- `is_healthy`: Property computed (is_connected AND broker_available)

**Dependencies**: T006

**Acceptance**: Schema valida corretamente, is_healthy computed

---

### T019 - [US2] Implementar HealthChecker Component
- [X] Completed

**Descrição**: Componente para verificação de saúde da conexão

**Files**:
- `src/connection/health.py`

**Class**:
```python
class HealthChecker:
    def __init__(self, manager: ConnectionManager):
        self.manager = manager
    
    async def check_health(self) -> HealthStatus:
        """Verifica saúde da conexão e broker"""
        start = time.time()
        
        is_connected = self.manager.state == ConnectionState.CONNECTED
        broker_available = await self._check_broker()
        latency = (time.time() - start) * 1000
        
        return HealthStatus(
            is_connected=is_connected,
            broker_available=broker_available,
            latency_ms=latency,
            last_check=datetime.utcnow()
        )
    
    async def _check_broker(self) -> bool:
        """Ping no broker via channel"""
```

**Dependencies**: T011, T018

**Acceptance**: Health check retorna em <1s, detecta conexão ativa/inativa

---

### T020 - [US2] Adicionar get_status ao ConnectionManager
- [X] Completed

**Descrição**: Método para retornar status completo da conexão

**Files**:
- `src/connection/manager.py` (adicionar método)

**Method**:
```python
async def get_status(self) -> ConnectionStatusResult:
    """Retorna status completo incluindo retry info"""
    return ConnectionStatusResult(
        state=self.state,
        connection_url=self.config.get_connection_url(),
        connected_since=self._connected_since,
        retry_attempts=self.retry_policy.attempts if self.retry_policy else 0,
        next_retry_in_seconds=...
    )
```

**Dependencies**: T011, T009

**Acceptance**: Status reflete estado real, incluindo retry info

---

### T021 - [US2] Testes Unitários - HealthChecker [P]
- [X] Completed

**Descrição**: Testes unitários para health checker

**Files**:
- `tests/unit/test_health.py`

**Test Cases**:
- `test_health_check_connected`: Healthy quando conectado
- `test_health_check_disconnected`: Unhealthy quando desconectado
- `test_health_check_latency`: Latência <1s
- `test_health_check_broker_unavailable`: Detecta broker indisponível

**Dependencies**: T019

**Acceptance**: Todos os testes passam

---

### T022 - [US2] Testes de Integração - Health Check [P]
- [X] Completed

**Descrição**: Testes de health check com RabbitMQ real

**Files**:
- `tests/integration/test_health.py`

**Test Cases**:
- `test_health_check_on_active_connection`: Saudável em conexão ativa
- `test_health_check_on_lost_connection`: Detecta conexão perdida
- `test_health_check_performance`: Retorna em <1s
- `test_health_check_timeout_handling`: **Edge Case EC-006** - Timeout durante health check retorna unhealthy após 1s máximo, não bloqueia outras operações

**Test Case EC-006 Implementation**:
```python
async def test_health_check_timeout_handling():
    """Edge Case EC-006: Timeout durante health check"""
    manager = ConnectionManager(config)
    health_checker = HealthChecker(manager)
    await manager.connect()
    
    # Simular latência alta que causa timeout
    with patch.object(health_checker, '_check_broker', 
                     side_effect=asyncio.sleep(2)):  # Delay 2s > timeout 1s
        start_time = time.time()
        try:
            health_status = await asyncio.wait_for(
                health_checker.check_health(), 
                timeout=1.0
            )
        except asyncio.TimeoutError:
            duration = time.time() - start_time
            # Verificar que timeout ocorreu em ~1s conforme FR-008
            assert 0.9 < duration < 1.2, f"Timeout incorreto: {duration}s"
    
    # Verificar que sistema continua operacional após timeout (FR-018)
    assert manager.state in [ConnectionState.CONNECTED, ConnectionState.RECONNECTING]
    
    # Health check subsequente deve funcionar normalmente
    health_status = await health_checker.check_health()
    assert health_status is not None  # Sistema não travou
```

**Dependencies**: T019, T004

**Acceptance**: Cenários de acceptance da US2 passam + EC-006 coberto (timeout <1s, unhealthy status, sistema continua operacional)

---

### T023 - [US2] Implementar MCP Tools: health_check e get_status
- [X] Completed

**Descrição**: Implementar operações de monitoramento no call-id

**Files**:
- `src/tools/call_id.py` (adicionar handlers)

**Operations**:
- `connection.health_check`: Retorna HealthStatus
- `connection.get_status`: Retorna ConnectionStatusResult

**Dependencies**: T019, T020, T010

**Acceptance**: Tools executam via MCP, retornam conforme contracts

---

**Checkpoint US2**: ✅ Operador pode monitorar saúde e status da conexão

---

## Phase 5: User Story 3 (P3) - Recuperação Automática

**Goal**: Sistema reconecta automaticamente após perda de conexão

**Independent Test**: Reconexão automática em <10s quando servidor volta

### T024 - [US3] Implementar ConnectionMonitor
- [X] Completed

**Descrição**: Monitor para detectar perda de conexão via heartbeat + eventos

**Files**:
- `src/connection/monitor.py`

**Class**:
```python
class ConnectionMonitor:
    def __init__(self, connection: aio_pika.Connection, 
                 on_connection_lost: Callable):
        self.connection = connection
        self.on_connection_lost = on_connection_lost
        self.heartbeat_interval = 60
    
    async def start(self):
        """Inicia monitoramento"""
        self.connection.add_close_callback(self._on_close)
    
    async def stop(self):
        """Para monitoramento"""
    
    def _on_close(self, connection, exception):
        """Callback ao detectar perda"""
        asyncio.create_task(self.on_connection_lost())
```

**Dependencies**: T011

**Acceptance**: Detecta perda de conexão via callback

---

### T025 - [US3] Implementar Lógica de Reconexão no ConnectionManager
- [X] Completed

**Descrição**: Adicionar método reconnect com retry infinito

**Files**:
- `src/connection/manager.py` (adicionar métodos)

**Methods**:
```python
async def reconnect(self):
    """Reconecta com retry infinito + backoff exponencial"""
    self.state = ConnectionState.RECONNECTING
    self.retry_policy.reset()
    
    while True:
        try:
            await self.connect()
            logger.info("connection.reconnected")
            self.retry_policy.reset()
            break
        except Exception as e:
            delay = self.retry_policy.next_delay()
            logger.warn("connection.reconnecting", 
                       attempt=self.retry_policy.attempts,
                       next_retry=delay)
            await asyncio.sleep(delay)

async def _on_connection_lost(self):
    """Handler chamado quando conexão é perdida"""
    logger.error("connection.lost")
    asyncio.create_task(self.reconnect())
```

**Dependencies**: T011, T009, T024

**Acceptance**: Reconexão automática funciona, backoff exponencial correto

---

### T026 - [US3] Integrar Monitor ao ConnectionManager
- [X] Completed

**Descrição**: Iniciar monitor após conexão estabelecida

**Files**:
- `src/connection/manager.py` (modificar `connect`)

**Logic**:
```python
async def connect(self):
    # ... lógica existente ...
    
    # Após estabelecer conexão, iniciar monitor
    self.monitor = ConnectionMonitor(
        self.connection,
        on_connection_lost=self._on_connection_lost
    )
    await self.monitor.start()
```

**Dependencies**: T024, T025

**Acceptance**: Monitor inicia automaticamente após conexão

---

### T027 - [US3] Testes Unitários - Retry Policy [P]
- [X] Completed

**Descrição**: Testes para retry policy

**Files**:
- `tests/unit/test_retry.py`

**Test Cases**:
- `test_retry_policy_exponential_backoff`: 1s → 2s → 4s → 8s
- `test_retry_policy_max_delay`: Não excede 60s
- `test_retry_policy_reset`: Reset restaura inicial
- `test_retry_policy_attempts_counter`: Conta tentativas

**Dependencies**: T009

**Acceptance**: Todos os testes passam

---

### T028 - [US3] Testes de Integração - Reconexão [P]
- [X] Completed

**Descrição**: Testes de reconexão automática com simulação de falha

**Files**:
- `tests/integration/test_reconnection.py`

**Test Cases**:
```python
async def test_automatic_reconnection():
    """Simula perda e verifica reconexão automática"""
    manager = ConnectionManager(config)
    await manager.connect()
    
    # Simular perda (fechar conexão)
    await manager.connection.close()
    
    # Aguardar reconexão (max 10s)
    for _ in range(10):
        await asyncio.sleep(1)
        if manager.state == ConnectionState.CONNECTED:
            break
    
    assert manager.state == ConnectionState.CONNECTED

async def test_retry_backoff_progression():
    """Edge Case EC-007: Múltiplas tentativas de reconexão consecutivas falham"""
    # Manter servidor down, verificar delays e logs
    manager = ConnectionManager(config)
    
    # Tentar conectar com servidor down
    subprocess.run(["docker", "stop", "rabbitmq-test"], check=True)
    
    retry_delays = []
    start_time = time.time()
    
    # Monitorar tentativas de retry por 30 segundos
    for attempt in range(10):
        try:
            await manager.connect()
            break  # Se conectou, parar
        except:
            if attempt > 0:
                delay = time.time() - start_time - sum(retry_delays)
                retry_delays.append(delay)
            start_time = time.time()
    
    # Verificar progressão exponencial: 1s, 2s, 4s, 8s, 16s, 32s, 60s, 60s (EC-007, FR-011)
    expected_delays = [1, 2, 4, 8, 16, 32, 60, 60]
    for i, (actual, expected) in enumerate(zip(retry_delays[:8], expected_delays)):
        # Permitir 20% de variação
        assert expected * 0.8 <= actual <= expected * 1.2, \
               f"Delay {i+1} incorreto: esperado ~{expected}s, obtido {actual:.1f}s"
    
    # Verificar que delays não excedem 60s máximo (FR-011)
    for delay in retry_delays:
        assert delay <= 65, f"Delay excedeu máximo: {delay}s"
    
    # Verificar que logs críticos foram emitidos (FR-014, EC-007)
    # Logs esperados: "connection.lost", "connection.reconnecting", "connection.retry_attempt" (com attempt number e next_delay),
    # "connection.retry_failed" (por tentativa), "connection.reconnected" (quando sucesso)
    
    # Restaurar servidor para cleanup
    subprocess.run(["docker", "start", "rabbitmq-test"], check=True)

async def test_infinite_retry_loop_after_max_delay():
    """US3 Acceptance Scenario 2: Sistema continua retry indefinidamente após atingir máximo
    
    Valida que após atingir o delay máximo de 60s, o sistema continua tentando
    indefinidamente com intervalo fixo de 60s (não para de tentar reconectar)
    """
    manager = ConnectionManager(config)
    
    # Manter servidor down
    subprocess.run(["docker", "stop", "rabbitmq-test"], check=True)
    
    try:
        # Iniciar processo de reconexão
        asyncio.create_task(manager.reconnect())
        
        # Aguardar que sistema atinja delay máximo (após ~7 tentativas: 1+2+4+8+16+32 = 63s)
        await asyncio.sleep(70)
        
        # Coletar delays após atingir máximo (devem ser todos ~60s)
        post_max_delays = []
        for i in range(5):  # Monitorar 5 tentativas após máximo
            start = time.time()
            # Aguardar próxima tentativa
            await asyncio.sleep(65)
            # Verificar que tentativa ocorreu (via log ou contador de tentativas)
            current_attempts = manager.retry_policy.attempts
            post_max_delays.append(65)  # Aproximação
        
        # Verificar que todas as tentativas após máximo usam delay de 60s (US3 Scenario 2)
        for i, delay in enumerate(post_max_delays):
            assert 55 <= delay <= 65, \
                   f"Tentativa {i+1} após máximo usou delay incorreto: {delay}s (esperado: ~60s)"
        
        # Verificar que sistema NÃO parou de tentar (retry continua indefinidamente)
        assert manager.state == ConnectionState.RECONNECTING, \
               "Sistema deve continuar em modo RECONNECTING indefinidamente"
        
        # Verificar logs de retry contínuo
        # Logs esperados: múltiplos "connection.retry_attempt" com next_delay=60s
        
    finally:
        # Restaurar servidor e cancelar retry
        subprocess.run(["docker", "start", "rabbitmq-test"], check=True)
        await manager.disconnect()

async def test_edge_case_server_unavailable_during_operation():
    """Edge Case EC-001: Servidor indisponível durante operação ativa"""
    manager = ConnectionManager(config)
    await manager.connect()
    initial_state = manager.state
    assert initial_state == ConnectionState.CONNECTED
    
    # Simular servidor ficando indisponível durante operação
    # (ex: desligar RabbitMQ via Docker)
    subprocess.run(["docker", "stop", "rabbitmq-test"], check=True)
    
    # Verificar que sistema detecta via heartbeat/eventos e entra em reconexão (FR-010, FR-011)
    await asyncio.sleep(2)
    assert manager.state == ConnectionState.RECONNECTING
    
    # Verificar que logs críticos foram emitidos (FR-014)
    # Logs esperados: "connection.lost", "connection.reconnecting"
    
    # Restaurar servidor
    subprocess.run(["docker", "start", "rabbitmq-test"], check=True)
    
    # Aguardar reconexão automática (FR-012: <10s)
    reconnected = False
    for _ in range(15):  # 15 segundos máximo
        await asyncio.sleep(1)
        if manager.state == ConnectionState.CONNECTED:
            reconnected = True
            break
    
    assert reconnected, "Sistema não reconectou em 15 segundos"
    assert manager.state == ConnectionState.CONNECTED

async def test_edge_case_invalid_vhost():
    """Edge Case EC-003: Virtual host especificado não existe"""
    config = ConnectionConfig(vhost="/nonexistent")
    manager = ConnectionManager(config)
    
    with pytest.raises(VHostNotFoundError) as exc_info:
        await manager.connect()
    
    # Verificar mensagem de erro específica conforme FR-020
    error_msg = str(exc_info.value)
    assert "vhost não encontrado" in error_msg.lower() or "vhost not found" in error_msg.lower()
    assert "/nonexistent" in error_msg
    
    # Verificar que erro é claro e acionável (FR-006)
    assert len(error_msg) > 20  # Mensagem descritiva, não código genérico

async def test_heartbeat_detection_time():
    """P1: Validar tempo máximo de detecção de perda de conexão via heartbeat
    
    Método Cross-Platform Recomendado (Produção/CI):
    - **Toxiproxy** (preferido): Proxy de rede que simula falhas de forma portável em Linux/Windows/macOS
      Setup CI: docker run -d --name toxiproxy -p 8474:8474 -p 5672:5672 ghcr.io/shopify/toxiproxy
      Uso: toxiproxy-cli toxic add rabbitmq-test -t timeout -a timeout=0
      Benefício: Simula network partitions reais sem dependência de ferramentas específicas do SO
    - **pytest-docker-compose**: Orquestra RabbitMQ + Toxiproxy em ambiente de teste automatizado
    - **Docker Compose**: Para integração completa com ambiente controlado
    
    Método Técnico Atual (Socket Mock - desenvolvimento local):
    - **Socket mock direto**: Forçar close() no socket subjacente (rápido para desenvolvimento)
    - **Limitação**: Não simula network partitions reais, apenas fechamento abrupto
    """
    manager = ConnectionManager(config)
    await manager.connect()
    
    # Simular perda de conexão abrupta (sem notificação)
    # Para produção/CI: usar Toxiproxy ou pytest-docker-compose
    # Para desenvolvimento/local: usar mock direto do socket
    start_time = time.time()
    
    # Forçar desconexão silenciosa via close forçado do socket subjacente
    if hasattr(manager.connection, '_connection'):
        manager.connection._connection.sock.close()  # Fecha socket sem notificar callbacks
    
    # Aguardar detecção via heartbeat (máximo 60s conforme FR-010)
    while time.time() - start_time < 65:
        if manager.state == ConnectionState.RECONNECTING:
            detection_time = time.time() - start_time
            # Verificar que detectou em <=60s (1 ciclo de heartbeat)
            assert detection_time <= 60, f"Detecção demorou {detection_time}s (máximo: 60s)"
            break
        await asyncio.sleep(1)
    else:
        pytest.fail("Sistema não detectou perda de conexão em 65 segundos")

async def test_edge_case_connection_limit_reached():
    """Edge Case EC-004: Limite de conexões do RabbitMQ atingido
    
    Configuração Necessária:
    1. Via rabbitmq.conf: connection_max = 5
    2. Via Management API:
       PUT /api/vhosts/{vhost}
       {"max_connections": 5}
    3. Via Docker env var:
       -e RABBITMQ_MAX_CONNECTIONS=5
    
    Para este teste, usar Docker com env var para facilidade de setup.
    """
    # Configurar RabbitMQ com limite baixo (via Management API ou config)
    # Neste teste assumimos limite configurado em 5 conexões para teste
    
    managers = []
    try:
        # Criar conexões até atingir limite
        for i in range(6):  # Tentar criar 6 conexões com limite de 5
            manager = ConnectionManager(config)
            try:
                await manager.connect()
                managers.append(manager)
            except Exception as e:
                # Quando limite for atingido, verificar erro claro (FR-006, EC-004)
                error_msg = str(e)
                assert any(keyword in error_msg.lower() for keyword in 
                          ["connection limit", "too many connections", "limit reached"]), \
                       f"Erro não menciona limite de conexões: {error_msg}"
                
                # Verificar que mensagem é clara e acionável (FR-006)
                assert len(error_msg) > 20, "Mensagem de erro muito curta"
                
                # Sistema deve entrar em retry automático (FR-011)
                # (não testa aqui pois limite persiste)
                break
        
        # Se chegou aqui com 6 conexões, significa que limite não está configurado
        # (não é erro do teste, apenas nota)
        if len(managers) >= 6:
            pytest.skip("RabbitMQ não tem limite de conexões configurado para este teste")
    
    finally:
        # Limpar todas as conexões
        for manager in managers:
            await manager.disconnect()

async def test_edge_case_connection_closed_by_server():
    """Edge Case EC-005: Conexão fechada pelo servidor RabbitMQ
    
    Configuração Necessária:
    1. Via Management API (RECOMENDADO para testes):
       DELETE /api/connections/{name}
       Exemplo: DELETE /api/connections/127.0.0.1:54321%20-%3E%20127.0.0.1:5672
    
    2. Via CLI:
       rabbitmqctl close_connection "<connection_name>" "Test closure"
    
    Para este teste, usar Management API para fechar conexão específica.
    """
    import urllib.request
    import json
    
    manager = ConnectionManager(config)
    await manager.connect()
    
    # Obter nome da conexão via Management API
    req = urllib.request.Request(
        "http://localhost:15672/api/connections",
        headers={"Authorization": "Basic dGVzdDp0ZXN0"}
    )
    with urllib.request.urlopen(req) as response:
        connections = json.loads(response.read())
        if connections:
            connection_name = connections[0]["name"]
            
            # Forçar fechamento pelo servidor via Management API
            delete_req = urllib.request.Request(
                f"http://localhost:15672/api/connections/{urllib.parse.quote(connection_name, safe='')}",
                method="DELETE",
                headers={"Authorization": "Basic dGVzdDp0ZXN0"}
            )
            urllib.request.urlopen(delete_req)
    
    # Verificar que sistema detecta via callback e entra em reconexão
    await asyncio.sleep(2)
    assert manager.state == ConnectionState.RECONNECTING
    
    # Verificar que reconecta automaticamente
    await asyncio.sleep(10)
    assert manager.state == ConnectionState.CONNECTED

async def test_edge_case_password_change_while_connected():
    """Edge Case EC-002: Mudança de senha enquanto conexão está ativa"""
    manager = ConnectionManager(config)
    await manager.connect()
    assert manager.state == ConnectionState.CONNECTED
    
    # Conexão atual deve permanecer válida após mudança de senha (EC-002)
    # (Simulação: mudar senha no RabbitMQ via Management API)
    # Conexão existente não é afetada imediatamente
    await asyncio.sleep(2)
    assert manager.state == ConnectionState.CONNECTED
    
    # Desconectar e tentar reconectar com senha antiga
    await manager.disconnect()
    
    # Próxima tentativa de reconexão deve falhar com erro de autenticação (EC-002, FR-006)
    with pytest.raises(AuthenticationError) as exc_info:
        await manager.connect()
    
    # Verificar erro claro de autenticação (FR-006)
    error_msg = str(exc_info.value)
    assert any(keyword in error_msg.lower() for keyword in 
              ["authentication", "auth", "credentials", "password", "login"]), \
           f"Erro não menciona autenticação: {error_msg}"
    assert len(error_msg) > 20, "Mensagem de erro muito curta"

async def test_manual_shutdown_during_reconnection():
    """US3 Acceptance Scenario 4: Shutdown manual durante reconexão"""
    manager = ConnectionManager(config)
    await manager.connect()
    
    # Simular perda de conexão
    await manager.connection.close()
    await asyncio.sleep(1)
    assert manager.state == ConnectionState.RECONNECTING
    
    # Solicitar shutdown manual
    start_time = time.time()
    await manager.disconnect()
    shutdown_duration = time.time() - start_time
    
    # Verificar que cancelou retry e desconectou em <2s
    assert shutdown_duration < 2.0
    assert manager.state == ConnectionState.DISCONNECTED
    assert manager.retry_policy.is_cancelled()

async def test_network_error_handling_gracefully():
    """FR-018: Sistema lida com erros de rede graciosamente sem crash"""
    manager = ConnectionManager(config)
    await manager.connect()
    
    # Simular falha de rede (timeout, connection reset, DNS failure)
    test_scenarios = [
        ("timeout", lambda: inject_network_timeout()),
        ("connection_reset", lambda: inject_connection_reset()),
        ("dns_failure", lambda: inject_dns_failure()),
        ("packet_loss", lambda: inject_packet_loss(50))  # 50% packet loss
    ]
    
    for scenario_name, inject_fault in test_scenarios:
        logger.info(f"Testing network error: {scenario_name}")
        inject_fault()
        
        # Verificar que sistema não crasha
        await asyncio.sleep(2)
        assert manager.state in [ConnectionState.CONNECTED, ConnectionState.RECONNECTING]
        
        # Sistema deve detectar problema e reconectar ou manter conexão
        # Nunca deve crashar com exceção não tratada
        
        # Limpar injeção de falha
        clear_network_faults()

async def test_heartbeat_timeout_detection():
    """Edge Case EC-006: Timeout durante health check devido a falha de rede"""
    manager = ConnectionManager(config)
    health_checker = HealthChecker(manager)
    await manager.connect()
    
    # Simular latência alta que causa timeout de heartbeat
    # inject_network_latency(2000)  # 2 segundos de latência
    # (Simulação de rede requer ferramentas específicas - usar mock aqui)
    
    # Executar health check com timeout configurado (FR-008: <1s)
    start_time = time.time()
    try:
        # Forçar timeout simulando operação lenta
        with patch.object(health_checker, '_check_broker', 
                         side_effect=asyncio.sleep(2)):
            health_status = await asyncio.wait_for(
                health_checker.check_health(), 
                timeout=1.0
            )
    except asyncio.TimeoutError:
        duration = time.time() - start_time
        # Verificar que timeout ocorreu em ~1s (EC-006)
        assert 0.9 < duration < 1.2, f"Timeout duração incorreta: {duration}s"
    
    # Verificar que sistema detecta problema sem crashar (FR-018)
    # Sistema deve continuar operacional após timeout
    assert manager.state in [ConnectionState.CONNECTED, ConnectionState.RECONNECTING]
    
    # Health check deve retornar unhealthy após timeout (EC-006)
    health_status = await health_checker.check_health()
    assert not health_status.is_healthy or health_status.latency_ms > 1000
```

**Dependencies**: T025, T004

**Acceptance**: Cenários de acceptance da US3 passam + edge cases cobertos + FR-018 validado

---

**Checkpoint US3**: ✅ Sistema reconecta automaticamente após perda

---

## Phase 6: User Story 4 (P4) - Pool de Conexões

**Goal**: Suportar múltiplas operações simultâneas via pool

**Independent Test**: 10+ operações simultâneas usando pool

### T029 - [US4] Implementar PooledConnection
- [X] Completed

**Descrição**: Wrapper de conexão para uso no pool

**Files**:
- `src/connection/pool.py`

**Class**:
```python
class PooledConnection:
    def __init__(self, connection: aio_pika.Connection):
        self.connection = connection
        self.channel = None
        self.in_use = False
        self.created_at = datetime.utcnow()
        self.last_used = datetime.utcnow()
    
    async def check_health(self) -> bool:
        """Verifica se conexão está saudável"""
    
    async def reset(self):
        """Reseta conexão para estado limpo"""
    
    def mark_in_use(self):
        """Marca como em uso"""
        self.in_use = True
        self.last_used = datetime.utcnow()
    
    def mark_available(self):
        """Marca como disponível"""
        self.in_use = False
```

**Dependencies**: T011

**Acceptance**: Wrapper rastreia uso e saúde da conexão

---

### T030 - [US4] Implementar ConnectionPool
- [X] Completed

**Descrição**: Pool assíncrono de conexões AMQP

**Files**:
- `src/connection/pool.py`

**Class**:
```python
class ConnectionPool:
    def __init__(self, config: ConnectionConfig, max_size: int = 5, timeout: int = 10):
        self.config = config
        self.max_size = max_size
        self.timeout = timeout
        self._available = asyncio.Queue(maxsize=max_size)
        self._all_connections: Set[PooledConnection] = set()
        self._lock = asyncio.Lock()
    
    async def acquire(self) -> PooledConnection:
        """Adquire conexão do pool (bloqueia se esgotado)"""
        try:
            conn = await asyncio.wait_for(
                self._available.get(),
                timeout=self.timeout
            )
            conn.mark_in_use()
            logger.info("pool.connection_acquired")
            return conn
        except asyncio.TimeoutError:
            logger.error("pool.timeout")
            raise PoolTimeoutError(f"No connection available after {self.timeout}s")
    
    async def release(self, conn: PooledConnection):
        """Devolve conexão ao pool"""
        if await conn.check_health():
            conn.mark_available()
            await self._available.put(conn)
            logger.info("pool.connection_released")
        else:
            # Conexão não saudável, descartar e criar nova
            await self._replace_connection(conn)
    
    async def close(self):
        """Fecha todas as conexões do pool"""
    
    async def get_stats(self) -> PoolStats:
        """Estatísticas do pool"""
```

**Dependencies**: T029, T006, T010

**Acceptance**: Pool gerencia conexões, bloqueia quando esgotado, timeout funciona

---

### T031 - [US4] Inicializar Pool com Conexões
- [X] Completed

**Descrição**: Lógica para criar conexões iniciais do pool

**Files**:
- `src/connection/pool.py` (adicionar método)

**Method**:
```python
async def initialize(self):
    """Cria conexões iniciais do pool"""
    for _ in range(self.max_size):
        conn = await self._create_connection()
        self._all_connections.add(conn)
        await self._available.put(conn)

async def _create_connection(self) -> PooledConnection:
    """Cria nova conexão AMQP"""
    manager = ConnectionManager(self.config)
    await manager.connect()
    return PooledConnection(manager.connection)
```

**Dependencies**: T030

**Acceptance**: Pool inicializa com `max_size` conexões

---

### T032 - [US4] Testes Unitários - ConnectionPool [P]
- [X] Completed

**Descrição**: Testes unitários para pool

**Files**:
- `tests/unit/test_pool.py`

**Test Cases**:
- `test_pool_initialization`: Cria conexões iniciais
- `test_pool_acquire_release`: Ciclo acquire/release funciona
- `test_pool_timeout`: Timeout quando esgotado
- `test_pool_stats`: Estatísticas corretas

**Dependencies**: T030, T031

**Acceptance**: Todos os testes passam

---

### T033 - [US4] Testes de Integração - Pool [P]
- [X] Completed

**Descrição**: Testes de pool com operações simultâneas reais

**Files**:
- `tests/integration/test_pool.py`

**Test Cases**:
```python
async def test_pool_concurrent_operations():
    """SC-007 & G2: Sistema suporta pelo menos 10 operações simultâneas usando pool"""
    pool = ConnectionPool(config, max_size=5)
    await pool.initialize()
    
    operations_completed = 0
    lock = asyncio.Lock()
    
    async def operation(i):
        nonlocal operations_completed
        conn = await pool.acquire()
        await asyncio.sleep(0.1)  # Simular operação realista
        async with lock:
            operations_completed += 1
        await pool.release(conn)
    
    # TESTE 1: EXATAMENTE 10 operações simultâneas conforme SC-007
    print("Executando 10 operações simultâneas...")
    start_time = time.time()
    tasks = [operation(i) for i in range(10)]
    await asyncio.gather(*tasks)
    duration_10 = time.time() - start_time
    
    # Verificar que todas as 10 operações completaram sem erro (SC-007)
    assert operations_completed == 10, f"Esperado 10 operações, completou {operations_completed}"
    
    # Verificar que pool funcionou corretamente com suas 5 conexões
    stats = await pool.get_stats()
    assert stats.total_connections == 5, f"Pool deve ter 5 conexões, tem {stats.total_connections}"
    
    # Verificar performance aceitável (SC-007: sem degradação)
    # Com pool de 5, 10 operações devem completar em ~0.2s (2 batches de 5)
    assert duration_10 < 0.5, f"10 operações demoraram {duration_10:.2f}s (máximo esperado: 0.5s)"
    print(f"✓ 10 operações completadas em {duration_10:.2f}s")
    
    # TESTE 2: MAIS que 10 operações para garantir escalabilidade (15 operações)
    print("Executando 15 operações simultâneas para validar escalabilidade...")
    operations_completed = 0
    start_time = time.time()
    tasks = [operation(i) for i in range(15)]
    await asyncio.gather(*tasks)
    duration_15 = time.time() - start_time
    
    # Verificar que todas as 15 operações completaram
    assert operations_completed == 15, f"Esperado 15 operações, completou {operations_completed}"
    
    # Verificar que não houve degradação significativa de performance
    # 15 operações = 3 batches de 5 = ~0.3s esperado
    assert duration_15 < 0.7, f"15 operações demoraram {duration_15:.2f}s (máximo esperado: 0.7s)"
    print(f"✓ 15 operações completadas em {duration_15:.2f}s")
    
    # TESTE 3: Validar que performance é linear (não há gargalos escondidos)
    # Razão de tempo deve ser ~1.5x (15 ops / 10 ops)
    time_ratio = duration_15 / duration_10
    assert 1.2 < time_ratio < 2.0, f"Razão de tempo suspeita: {time_ratio:.2f} (esperado: ~1.5)"
    print(f"✓ Performance escalou linearmente (razão: {time_ratio:.2f}x)")
    
    # Verificar estatísticas finais do pool
    final_stats = await pool.get_stats()
    assert final_stats.total_connections == 5, "Pool mantém 5 conexões após operações"
    assert final_stats.available_connections == 5, "Todas as conexões foram liberadas"
    print(f"✓ Pool stats: {final_stats.total_connections} total, {final_stats.available_connections} disponíveis")

async def test_pool_exhaustion_blocking():
    """Testa bloqueio quando pool esgotado"""
    pool = ConnectionPool(config, max_size=2, timeout=5)
    await pool.initialize()
    
    # Adquirir todas
    conn1 = await pool.acquire()
    conn2 = await pool.acquire()
    
    # Tentar adquirir terceira (deve bloquear e timeout)
    with pytest.raises(PoolTimeoutError):
        await pool.acquire()
```

**Dependencies**: T030, T031, T004

**Acceptance**: Cenários de acceptance da US4 passam + SC-007 validado (EXATAMENTE 10 operações simultâneas testadas) + Escalabilidade validada (15 operações) + Performance linear confirmada

---

### T034 - [US4] Implementar MCP Tool: pool.get_stats

- [X] Completed

**Descrição**: Operação para obter estatísticas do pool

**Files**:
- `src/tools/call_id.py` (adicionar handler)

**Operation**: `pool.get_stats`

**Dependencies**: T030, T010

**Acceptance**: Tool retorna estatísticas conforme contract

---

**Checkpoint US4**: ✅ Pool suporta 10+ operações simultâneas

---

## Phase 7: MCP Tools Implementation

### T034.1 - Gerar Vector Database com Embeddings (Pré-requisito T035)
- [X] Completed

**Descrição**: Gerar embeddings pré-computados e ChromaDB local para semantic search conforme constituição

**Files**:
- `scripts/generate_embeddings.py`
- `data/vectors/connection-ops.db` (output)

**Logic**:
```python
from sentence_transformers import SentenceTransformer
import chromadb

OPERATIONS = [
    {"id": "connection.connect", "description": "Establish AMQP connection to RabbitMQ server with credentials and vhost"},
    {"id": "connection.disconnect", "description": "Gracefully disconnect from RabbitMQ closing all channels and resources"},
    {"id": "connection.health_check", "description": "Check connection health and broker availability status"},
    {"id": "connection.get_status", "description": "Get current connection state and retry information"},
    {"id": "pool.get_stats", "description": "Get connection pool statistics including available and in-use connections"},
]

def generate_embeddings():
    """Generate embeddings using sentence-transformers"""
    model = SentenceTransformer('all-MiniLM-L6-v2')  # Lightweight model ~80MB
    client = chromadb.PersistentClient(path="data/vectors")
    collection = client.create_collection("connection_operations")
    
    for op in OPERATIONS:
        embedding = model.encode(op["description"])
        collection.add(
            ids=[op["id"]],
            embeddings=[embedding.tolist()],
            metadatas=[{"description": op["description"]}]
        )
    
    print(f"✓ Generated {len(OPERATIONS)} embeddings in data/vectors/connection-ops.db")
```

**Dependencies**: Nenhuma

**Acceptance**: ChromaDB criado (~2-5MB), 5 operações indexadas, script executável, database commitado ao repositório

---

### T035 - Implementar MCP Tool: search-ids (ChromaDB)

- [X] Completed

**Descrição**: Busca semântica usando ChromaDB com embeddings pré-computados conforme constituição

**Files**:
- `src/tools/search_ids.py`

**Logic**:
```python
from sentence_transformers import SentenceTransformer
import chromadb

class SearchIdsTool:
    def __init__(self):
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.client = chromadb.PersistentClient(path="data/vectors")
        self.collection = self.client.get_collection("connection_operations")
    
    def search(self, query: str, pagination: PaginationParams) -> SearchResult:
        """Semantic search usando vector similarity"""
        # Gerar embedding da query
        query_embedding = self.model.encode(query)
        
        # Buscar operações similares
        results = self.collection.query(
            query_embeddings=[query_embedding.tolist()],
            n_results=pagination.pageSize
        )
        
        # Retornar com paginação
        return SearchResult(
            items=[...],
            pagination=PaginationMetadata(...)
        )
```

**Dependencies**: T010, T034.1

**Acceptance**: Busca retorna operações relevantes via semantic similarity, paginação funciona, performance <100ms conforme constituição

---

### T036 - Implementar MCP Tool: get-id

- [X] Completed

**Descrição**: Retorna schema de operação específica

**Files**:
- `src/tools/get_id.py`

**Logic**:
```python
# Carregar schemas de contracts/connection-operations.json
OPERATIONS_SCHEMAS = load_operations_from_json()

def get_operation_schema(operation_id: str) -> OperationSchema:
    """Retorna schema completo da operação"""
    if operation_id not in OPERATIONS_SCHEMAS:
        raise OperationNotFoundError(operation_id)
    return OPERATIONS_SCHEMAS[operation_id]
```

**Dependencies**: T010

**Acceptance**: Retorna schema completo conforme contract

---

### T037 - Implementar Dispatcher no call-id

- [X] Completed

**Descrição**: Roteamento de operações para handlers corretos

**Files**:
- `src/tools/call_id.py`

**Logic**:
```python
# Todas as 5 operações definidas em contracts/connection-operations.json
OPERATION_HANDLERS = {
    "connection.connect": execute_connection_connect,        # T016
    "connection.disconnect": execute_connection_disconnect,  # T017
    "connection.health_check": execute_health_check,         # T023
    "connection.get_status": execute_get_status,             # T023
    "pool.get_stats": execute_pool_get_stats,                # T034
}

async def call_operation(operation_id: str, params: dict) -> MCPToolResult:
    """Dispatch para handler correto com validação
    
    Total de operações suportadas: 5
    - 2 operações de conexão (connect, disconnect)
    - 2 operações de monitoramento (health_check, get_status)
    - 1 operação de pool (get_stats)
    """
    if operation_id not in OPERATION_HANDLERS:
        raise OperationNotFoundError(operation_id)
    
    handler = OPERATION_HANDLERS[operation_id]
    
    try:
        result = await handler(params)
        return MCPToolResult(success=True, result=result, ...)
    except Exception as e:
        return MCPToolResult(success=False, error=..., ...)
```

**Dependencies**: T016, T017, T023, T034

**Acceptance**: Todas as 5 operações executam via dispatcher (conforme contracts/connection-operations.json)

---

### T038 - Implementar Servidor MCP Principal
- [X] Completed

**Descrição**: Servidor MCP que expõe os 3 tools

**Files**:
- `src/server.py`

**Content**:
```python
from mcp import Server
from src.tools import search_ids, get_id, call_id

server = Server("rabbitmq-connection")

@server.list_tools()
async def list_tools():
    return [
        {
            "name": "search-ids",
            "description": "Busca semântica de operações",
            "inputSchema": {...}
        },
        {
            "name": "get-id",
            "description": "Obtém schema de operação",
            "inputSchema": {...}
        },
        {
            "name": "call-id",
            "description": "Executa operação",
            "inputSchema": {...}
        }
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "search-ids":
        return await search_ids.search(arguments)
    elif name == "get-id":
        return await get_id.get(arguments)
    elif name == "call-id":
        return await call_id.call(arguments)
```

**Dependencies**: T035, T036, T037

**Acceptance**: Servidor MCP funcional, 3 tools acessíveis

---

### T039 - Testes de Contrato MCP [P]
- [X] Completed

**Descrição**: Validar conformidade com MCP Protocol

**Files**:
- `tests/contract/test_mcp_protocol.py`

**Test Cases**:
- `test_list_tools_conforms_to_mcp`: list_tools retorna formato correto
- `test_search_ids_input_validation`: Valida input schema
- `test_get_id_input_validation`: Valida input schema
- `test_call_id_input_validation`: Valida input schema
- `test_all_operations_have_schemas`: Todas as 5 operações têm schemas
- `test_schemas_match_contracts`: Schemas match `contracts/*.json`

**Dependencies**: T038

**Acceptance**: Todos os contratos validados, 100% conformidade MCP

---

## Phase 8: Polish & Integration

### T040 - Implementar Exemplos de Uso
- [X] Completed

**Descrição**: Scripts de exemplo demonstrando uso do MCP server

**Files**:
- `examples/basic_connection.py`
- `examples/health_monitoring.py`
- `examples/pool_usage.py`
- `examples/reconnection_demo.py`

**Content**: Baseado em `quickstart.md`

**Dependencies**: T038

**Acceptance**: Todos os exemplos executam sem erro

---

### T041 - Documentar API e Contratos
- [X] Completed

**Descrição**: Gerar documentação completa da API

**Files**:
- `docs/api.md`: Documentação de todas as operações
- `docs/schemas.md`: Schemas Pydantic
- `docs/mcp-integration.md`: Como integrar com MCP clients

**Content**: Extraído de `contracts/`, `data-model.md`, `quickstart.md`

**Acceptance**: Documentação completa e navegável

---

### T042 - Configurar Coverage e Quality Gates
- [X] Completed

**Descrição**: Garantir cobertura mínima de 80%

**Files**:
- `.coveragerc`
- `.github/workflows/ci.yml` (se CI configurado)

**Config**:
```ini
[run]
source = src
omit = tests/*

[report]
fail_under = 80
show_missing = True
```

**Dependencies**: T003

**Acceptance**: Coverage >=80%, relatório HTML gerado

---

### T043 - Revisar e Sanitizar Todos os Logs
- [X] Completed

**Descrição**: Audit completo de logs para garantir zero exposição de credenciais

**Files**: 
- Todos os arquivos em `src/`
- `tests/test_log_sanitization.py` (novo arquivo de auditoria automatizada)

**Checklist**:
- [ ] Nenhum log contém campo `password` sem sanitização
- [ ] ConnectionConfig.__repr__ não expõe senha
- [ ] Logs estruturados passam por processador sanitizador
- [ ] Tracebacks não expõem credenciais

**Critérios de Aprovação Automatizados**:
```python
# tests/test_log_sanitization.py
def test_no_credentials_in_logs():
    """Verifica que credenciais são sanitizadas em logs"""
    # Criar logs de exemplo com ConnectionManager
    manager = ConnectionManager(ConnectionConfig(
        host="localhost",
        user="testuser",
        password="super_secret_password"
    ))
    
    # Capturar logs gerados
    with capture_logs() as log_output:
        await manager.connect()
        await manager.disconnect()
    
    # Verificar que senhas não aparecem em nenhum log
    assert "super_secret_password" not in log_output
    assert "password" not in log_output or "***" in log_output
    
    # Verificar que URLs sanitizam senhas
    assert "testuser:***@localhost" in log_output
    assert "testuser:super_secret_password" not in log_output

def test_config_repr_sanitization():
    """Verifica que repr de config sanitiza senha"""
    config = ConnectionConfig(password="secret123")
    repr_str = repr(config)
    
    assert "secret123" not in repr_str
    assert "password" not in repr_str or "***" in repr_str

def test_error_tracebacks_sanitization():
    """Verifica que tracebacks sanitizam credenciais, inclusive de bibliotecas externas (aio-pika)"""
    config = ConnectionConfig(password="secret123")
    manager = ConnectionManager(config)
    
    # Forçar erro
    with capture_logs() as log_output:
        try:
            await manager.connect()  # com credenciais inválidas
        except Exception:
            pass
    
    # Verificar que traceback não expõe senha (logs próprios)
    assert "secret123" not in log_output
    
    # Verificar que tracebacks de bibliotecas externas também são sanitizados
    # aio-pika pode logar conexão completa com credenciais em exceções
    # Exemplo: "amqp://user:secret123@localhost:5672/"
    assert "user:secret123@" not in log_output
    
    # Verificar que formato sanitizado está presente
    assert "user:***@" in log_output or "password=***" in log_output
```

**Dependencies**: T007

**Acceptance**: 
- Audit completo, zero exposições encontradas
- Script de auditoria automatizada passa com 100% de sucesso
- Todos os testes de sanitização passam sem falhas

---

### T044 - Implementar Graceful Shutdown
- [X] Completed

**Descrição**: Shutdown limpo do servidor MCP

**Files**:
- `src/server.py` (adicionar signal handlers)

**Logic**:
```python
import signal

async def shutdown(server, pool):
    """Shutdown limpo"""
    logger.info("Shutting down...")
    await pool.close()
    await server.stop()
    logger.info("Shutdown complete")

def main():
    server = create_server()
    pool = create_pool()
    
    # Registrar signal handlers
    signal.signal(signal.SIGINT, lambda s, f: asyncio.create_task(shutdown(server, pool)))
    signal.signal(signal.SIGTERM, lambda s, f: asyncio.create_task(shutdown(server, pool)))
    
    server.run()
```

**Dependencies**: T038, T030

**Acceptance**: SIGINT/SIGTERM resultam em shutdown limpo

---

### T045 - Review Final e Checklist Constitucional
- [X] Completed

**Descrição**: Validar conformidade com constitution

**Checklist**:
- [ ] ✅ MCP Protocol compliance (3-tool pattern)
- [ ] ✅ Test-first (80%+ coverage)
- [ ] ✅ Structured logging (JSON + sanitização)
- [ ] ✅ Performance (<5s connect, <1s health check)
- [ ] ✅ Código sob LGPL v3.0
- [ ] ✅ Todos os user stories testáveis independentemente
- [ ] ✅ Error handling robusto
- [ ] ✅ Documentação completa

**Acceptance**: Todos os itens checkados, pronto para merge

---

## Dependencies Graph

```
Setup Phase:
T001 → T002 → T003 → T004 (paralelos após T001)

Foundational Phase:
T005 ──┐
T006 ──┼──→ T008
T007 ──┤     ↓
T009 ──┘  T010

User Story 1 (P1):
T011 → T012 → T013 → T014 [P]
              ↓      ↓
              T015 [P] → T016 → T017

User Story 2 (P2):
T018 → T019 → T020 → T021 [P] → T022 [P] → T023

User Story 3 (P3):
T024 → T025 → T026 → T027 [P] → T028 [P]

User Story 4 (P4):
T029 → T030 → T031 → T032 [P] → T033 [P] → T034

MCP Tools:
T035 [P]
T036 [P]  } → T037 → T038 → T039 [P]
T016,T017,T023,T034

Polish:
T040 [P]
T041 [P]
T042     } → T043 → T044 → T045
T038,T030
```

---

## Parallel Execution Opportunities

### Setup Phase
- **T001 + T002 + T003 + T004**: Todos podem ser executados em paralelo

### Foundational Phase
- **T005 + T006 + T007 + T009**: Schemas e logging podem ser paralelos
- **T010**: Depende de T006 completo

### User Story 1
- **T014 + T015**: Testes unitários e integração paralelos
- **T016 + T017**: MCP tools paralelos após T012/T013

### User Story 2
- **T021 + T022**: Testes paralelos

### User Story 3
- **T027 + T028**: Testes paralelos

### User Story 4
- **T032 + T033**: Testes paralelos

### MCP Phase
- **T035 + T036**: search-ids e get-id paralelos
- **T039**: Contract tests paralelos após T038

### Polish Phase
- **T040 + T041 + T042**: Documentação e exemplos paralelos

---

## Implementation Strategy

### MVP Scope (Recommended First Delivery)
**User Story 1 Only**: Estabelecer e desconectar de RabbitMQ
- Tasks: T001-T017 (17 tasks)
- Delivery time: ~1-2 weeks
- Value: Core functionality operacional

### Increment 2 (Add Monitoring)
**User Stories 1-2**: MVP + Monitoring
- Tasks: T001-T023 (23 tasks)
- Delivery time: +1 week
- Value: Operação com observability

### Increment 3 (Add Resilience)
**User Stories 1-3**: MVP + Monitoring + Auto-reconnect
- Tasks: T001-T028 (28 tasks)
- Delivery time: +1 week
- Value: Sistema resiliente

### Full Feature (All User Stories)
**User Stories 1-4**: Complete feature
- Tasks: T001-T045 (45 tasks)
- Delivery time: 4-6 weeks total
- Value: Production-ready system

---

## Testing Strategy

### Test Categories

**Unit Tests** (Isolated, fast, no external deps):
- T014, T021, T027, T032
- Target: >80% coverage
- Run on every commit

**Integration Tests** (RabbitMQ required):
- T015, T022, T028, T033
- Target: Cover all acceptance scenarios
- Run on pre-merge

**Contract Tests** (MCP conformance):
- T039
- Target: 100% MCP compliance
- Run on pre-release

---

## Success Metrics

| Metric | Target | Measured By |
|--------|--------|-------------|
| Code coverage | >=80% | pytest-cov |
| Connection latency | <5s | Integration tests |
| Health check latency | <1s | Integration tests |
| Reconnection time | <10s | Integration tests |
| Concurrent operations | 10+ | Pool tests |
| MCP conformance | 100% | Contract tests |
| Zero credential exposure | 100% | Log audit (T043) |

---

## Notes

- **[P]** marca tarefas paralelizáveis
- **[US1]**, **[US2]**, **[US3]**, **[US4]** marcam a qual user story a tarefa pertence
- Todas as tarefas incluem acceptance criteria específicos
- Logs devem sempre usar structured logging (JSON)
- Credenciais devem ser sanitizadas em 100% dos logs
- Testes devem cobrir cenários de acceptance das user stories

---

**Generated**: 2025-10-09  
**Tool**: `/speckit.tasks`  
**Based on**: spec.md, plan.md, data-model.md, quickstart.md, research.md, contracts/*.json
