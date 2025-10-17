# Research Document: Basic RabbitMQ Connection

**Feature**: 002-basic-rabbitmq-connection  
**Date**: 2025-10-09  
**Phase**: 0 - Research & Technical Decisions

## Overview

Este documento consolida as decisões técnicas, alternativas consideradas e justificativas para a implementação da feature de conexão básica com RabbitMQ.

---

## Decision 1: Cliente AMQP Assíncrono

**Decision**: Utilizar `aio-pika` como biblioteca cliente AMQP assíncrona

**Rationale**: 
- `aio-pika` é a biblioteca oficial recomendada para Python assíncrono
- Suporte completo a async/await pattern do Python 3.9+
- Excelente integração com asyncio para operações non-blocking
- Manutenção ativa e comunidade robusta
- Performance superior em operações de alta concorrência
- API bem documentada com exemplos práticos

**Alternatives Considered**:
1. **pika (síncrono)**: Cliente oficial mas síncrono, bloqueante
   - **Rejected**: Não atende requisito de operações assíncronas de alta performance
   - Performance inferior em cenários de múltiplas conexões simultâneas
   
2. **aioamqp**: Cliente AMQP assíncrono alternativo
   - **Rejected**: Menor comunidade, documentação limitada
   - Manutenção irregular comparado ao aio-pika
   
3. **kombu**: Abstração de alto nível com múltiplos backends
   - **Rejected**: Overhead desnecessário para conexão direta
   - Complexidade adicional sem benefícios claros para este use case

**References**:
- [aio-pika Documentation](https://aio-pika.readthedocs.io/)
- [Python AMQP Libraries Comparison](https://www.rabbitmq.com/tutorials/tutorial-one-python.html)

---

## Decision 2: Logging Estruturado

**Decision**: Utilizar `structlog` para logging estruturado em formato JSON

**Rationale**:
- Padrão de mercado para logging estruturado em Python
- Excelente suporte a contexto e processadores customizados
- Sanitização automática de dados sensíveis via processadores
- Integração nativa com sistemas de agregação de logs (ELK, Splunk)
- Performance otimizada para ambientes de produção
- Suporte a múltiplos outputs (console, arquivo, remote)

**Alternatives Considered**:
1. **logging padrão do Python + python-json-logger**: 
   - **Rejected**: Menos flexível para contexto estruturado
   - Sanitização de credenciais requer mais código manual
   
2. **loguru**: Logger moderno com boa UX
   - **Rejected**: Menos adotado em ambientes enterprise
   - Integração com sistemas de agregação menos madura

3. **eliot**: Logging focado em ações e causalidade
   - **Rejected**: Curva de aprendizado maior
   - Overhead conceitual desnecessário para este caso

**References**:
- [structlog Documentation](https://www.structlog.org/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)

---

## Decision 3: Pool de Conexões

**Decision**: Implementar pool de conexões assíncrono customizado sobre aio-pika

**Rationale**:
- aio-pika não possui pool de conexões nativo robusto
- Pool customizado permite controle fino sobre:
  - Timeout de aquisição (10s padrão)
  - Tamanho do pool (5 conexões padrão)
  - Estratégia de bloqueio quando pool esgotado
  - Monitoramento de saúde das conexões
- Implementação relativamente simples com asyncio.Queue
- Performance previsível e configurável

**Alternatives Considered**:
1. **Usar connection por operação (sem pool)**:
   - **Rejected**: Overhead de estabelecer conexão a cada operação
   - Latência inaceitável (>5s por operação)
   
2. **Pool genérico asyncio (aioredis-pool)**:
   - **Rejected**: Não específico para AMQP
   - Perda de features específicas de RabbitMQ

3. **Uma única conexão global compartilhada**:
   - **Rejected**: Gargalo de concorrência
   - Não escala para 10+ operações simultâneas

**Implementation Notes**:
```python
# Pool básico com asyncio.Queue:
class ConnectionPool:
    def __init__(self, max_size=5, timeout=10):
        self._queue = asyncio.Queue(maxsize=max_size)
        self._timeout = timeout
    
    async def acquire(self):
        return await asyncio.wait_for(
            self._queue.get(), 
            timeout=self._timeout
        )
    
    async def release(self, conn):
        await self._queue.put(conn)
```

**References**:
- [asyncio Queue Documentation](https://docs.python.org/3/library/asyncio-queue.html)
- [Connection Pooling Patterns](https://en.wikipedia.org/wiki/Connection_pool)

---

## Decision 4: Retry Policy com Backoff Exponencial

**Decision**: Retry infinito com backoff exponencial (1s → 2s → 4s → ... → 60s max)

**Rationale**:
- Balanceamento entre resiliência e carga no servidor
- Backoff exponencial evita "thundering herd" problem
- Retry infinito garante reconexão eventual sem intervenção manual
- Valores baseados em best practices da indústria:
  - Inicial 1s: tempo razoável para falhas transientes
  - Fator 2x: crescimento sustentável
  - Máximo 60s: evita aguardar muito entre tentativas
- Simples de implementar e testar

**Alternatives Considered**:
1. **Retry limitado (ex: 10 tentativas)**:
   - **Rejected**: Requer intervenção manual após esgotar tentativas
   - Não atende requisito de reconexão automática
   
2. **Backoff linear (1s, 2s, 3s, 4s...)**:
   - **Rejected**: Crescimento muito lento
   - Pode sobrecarregar servidor em cenários de múltiplas falhas

3. **Retry imediato com jitter aleatório**:
   - **Rejected**: Pode causar sobrecarga em falhas massivas
   - Menos previsível para diagnóstico

**Implementation Notes**:
```python
class RetryPolicy:
    def __init__(self, initial=1.0, factor=2.0, maximum=60.0):
        self.initial = initial
        self.factor = factor
        self.maximum = maximum
        self.current = initial
    
    def next_delay(self):
        delay = min(self.current, self.maximum)
        self.current *= self.factor
        return delay
    
    def reset(self):
        self.current = self.initial
```

**References**:
- [Exponential Backoff Algorithm](https://en.wikipedia.org/wiki/Exponential_backoff)
- [AWS Best Practices for Retries](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)

---

## Decision 5: Formato de Configuração

**Decision**: Utilizar TOML como formato de configuração principal

**Rationale**:
- TOML é moderno, legível e suporta tipos nativos
- Melhor estruturação hierárquica que ENV vars
- Suporte nativo no Python 3.11+ (tomllib)
- Comentários inline para documentação
- Validação com Pydantic após parse

**Alternatives Considered**:
1. **YAML**:
   - **Rejected**: Sintaxe sensível a indentação pode causar erros
   - Parsing mais lento que TOML
   
2. **JSON**:
   - **Rejected**: Não suporta comentários
   - Menos legível para humanos

3. **Apenas ENV vars**:
   - **Rejected**: Dificulta configurações complexas
   - Não adequado para estruturas aninhadas

**Configuration Hierarchy**:
```
1. Argumentos programáticos (maior precedência)
2. Variáveis de ambiente (AMQP_*)
3. Arquivo config.toml
4. Valores padrão (menor precedência)
```

**Example TOML**:
```toml
[connection]
host = "localhost"
port = 5672
vhost = "/"
timeout = 30

[connection.credentials]
user = "guest"
password = "guest"

[pool]
max_size = 5
acquire_timeout = 10

[retry]
initial_delay = 1.0
backoff_factor = 2.0
max_delay = 60.0

[heartbeat]
interval = 60
```

**References**:
- [TOML Specification](https://toml.io/)
- [Python tomllib](https://docs.python.org/3/library/tomllib.html)

---

## Decision 6: Detecção de Perda de Conexão

**Decision**: Híbrido - Heartbeat AMQP (60s) + Eventos de Callback

**Rationale**:
- Heartbeat AMQP é protocolo nativo do RabbitMQ
- Detecção rápida de falhas de rede
- Eventos de callback capturam desconexões imediatas
- Combinação garante detecção robusta em todos os cenários
- 60s é o padrão default do RabbitMQ (balanceado)

**Alternatives Considered**:
1. **Apenas Heartbeat**:
   - **Rejected**: Delay de até 60s para detectar falha
   - Não captura desconexões imediatas (ex: kill do processo)
   
2. **Apenas Eventos**:
   - **Rejected**: Pode não detectar falhas silenciosas de rede
   - Depende completamente da implementação da biblioteca

3. **Polling manual periódico**:
   - **Rejected**: Overhead de CPU desnecessário
   - Menos eficiente que heartbeat nativo

**Implementation Notes**:
```python
# Configuração de heartbeat no aio-pika
connection_params = ConnectionParameters(
    host="localhost",
    heartbeat=60  # 60 segundos
)

# Registro de callbacks
connection.add_close_callback(on_connection_closed)
connection.add_on_close_callback(on_connection_lost)
```

**References**:
- [RabbitMQ Heartbeats](https://www.rabbitmq.com/heartbeats.html)
- [aio-pika Connection Callbacks](https://aio-pika.readthedocs.io/en/latest/quick-start.html#connection-callbacks)

---

## Decision 7: Validação de Schemas

**Decision**: Utilizar Pydantic v2 para validação de configurações e schemas

**Rationale**:
- Padrão moderno para validação de dados em Python
- Type hints nativos do Python
- Validação em runtime com mensagens de erro claras
- Serialização/deserialização automática
- Integração excelente com FastAPI e MCP
- Performance otimizada (Rust backend)

**Alternatives Considered**:
1. **Marshmallow**:
   - **Rejected**: API mais verbosa
   - Performance inferior ao Pydantic v2
   
2. **attrs + validators**:
   - **Rejected**: Menos integrado ao ecossistema moderno
   - Validação menos robusta

3. **Validação manual**:
   - **Rejected**: Propenso a erros
   - Manutenção difícil

**Example Schema**:
```python
from pydantic import BaseModel, Field, validator

class ConnectionConfig(BaseModel):
    host: str = Field(default="localhost")
    port: int = Field(default=5672, ge=1, le=65535)
    user: str = Field(default="guest")
    password: str = Field(default="guest")
    vhost: str = Field(default="/")
    timeout: int = Field(default=30, ge=1)
    
    @validator('password')
    def sanitize_password_in_logs(cls, v):
        # Não incluir senha em __repr__
        return v
```

**References**:
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pydantic v2 Performance](https://docs.pydantic.dev/latest/concepts/performance/)

---

## Decision 8: Exposição via MCP

**Decision**: Implementar semantic discovery pattern com 3 tools (search-ids, get-id, call-id)

**Rationale**:
- Mandatório pela constitution do projeto
- Permite descoberta semântica de operações
- Escala melhor que expor cada operação como tool individual
- Padrão consistente para futuras features
- Facilita integração com agentes de IA

**Alternatives Considered**:
1. **Tool individual por operação**:
   - **Rejected**: Não escala (violaria limite de 15 tools)
   - Violação constitucional explícita
   
2. **API REST tradicional**:
   - **Rejected**: Não segue padrão MCP
   - Dificulta integração com agentes

3. **GraphQL**:
   - **Rejected**: Overhead desnecessário
   - MCP já resolve descoberta de schema

**Operations Exposed**:
- `connection.connect`: Estabelecer conexão AMQP
- `connection.disconnect`: Desconectar graciosamente
- `connection.health_check`: Verificar saúde
- `connection.get_status`: Obter status atual
- `pool.get_stats`: Estatísticas do pool

**References**:
- [MCP Protocol Specification](https://github.com/modelcontextprotocol/protocol)
- [Constitution: Semantic Discovery Pattern](../../.specify/memory/constitution.md)

---

## Testing Strategy

### Unit Tests (pytest + pytest-asyncio)
- Testes isolados de cada componente
- Mocks para conexões AMQP
- Cobertura mínima: 80%

### Integration Tests
- RabbitMQ real em Docker
- Testes de reconexão com simulação de falhas
- Validação de timeout e retry policies

### Contract Tests
- Conformidade com MCP Protocol
- Validação de schemas JSON
- Testes de descoberta semântica

**Test Environment**:
```bash
# docker-compose.yml
services:
  rabbitmq:
    image: rabbitmq:3-management
    ports:
      - "5672:5672"
      - "15672:15672"
    environment:
      RABBITMQ_DEFAULT_USER: test
      RABBITMQ_DEFAULT_PASS: test
```

---

## Performance Considerations

### Latency Targets
- Conexão inicial: <5s (servidor disponível)
- Health check: <1s
- Reconexão: <10s (após servidor voltar)
- Aquisição de conexão do pool: <10s (timeout)

### Concurrency
- Suporte a 10+ operações simultâneas
- Pool de 5 conexões (padrão)
- Operações non-blocking com async/await

### Resource Usage
- Memory: <100MB por instância
- CPU: <5% em idle
- Network: Minimal overhead (AMQP heartbeat apenas)

---

## Security Considerations

### Credential Management
- Suporte a variáveis de ambiente (AMQP_*)
- Sanitização automática em logs
- Nunca expor senha em tracebacks ou __repr__

### Network Security
- TLS/SSL será implementado em feature futura
- Por enquanto: conexões em rede confiável apenas

### Logging Security
- Credenciais removidas automaticamente
- Structured logging com campos sanitizados
- Audit trail de conexões

---

## Dependencies

### Runtime Dependencies
```
aio-pika >= 9.0.0        # AMQP client assíncrono
structlog >= 23.0.0      # Structured logging
pydantic >= 2.0.0        # Schema validation
mcp-sdk >= 0.1.0         # Model Context Protocol
python-dotenv >= 1.0.0   # ENV file support
```

### Development Dependencies
```
pytest >= 7.0.0
pytest-asyncio >= 0.21.0
pytest-cov >= 4.0.0
docker >= 6.0.0          # Para integration tests
```

---

## Known Limitations

1. **TLS/SSL**: Não implementado nesta feature (futuro)
2. **Certificados**: Autenticação apenas user/password
3. **Clustering**: Sem suporte a múltiplos brokers (futuro)
4. **Metrics**: Métricas básicas apenas, sem Prometheus (futuro)
5. **Vector Database**: Semantic search limitado, sem vector DB (futuro)

---

## Conclusion

Todas as decisões técnicas foram baseadas em:
- Requisitos da constitution
- Best practices da indústria
- Performance e escalabilidade
- Manutenibilidade e testabilidade

O design proposto atende todos os requisitos funcionais da spec com tecnologias maduras e bem suportadas. A implementação será incremental seguindo TDD rigoroso para garantir 80%+ de cobertura.

**Next Steps**: Phase 1 - Data Model e Contracts
