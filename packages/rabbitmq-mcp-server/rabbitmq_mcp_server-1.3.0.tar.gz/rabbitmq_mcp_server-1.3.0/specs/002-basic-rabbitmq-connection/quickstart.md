# Quickstart: Basic RabbitMQ Connection

**Feature**: 002-basic-rabbitmq-connection  
**Date**: 2025-10-09  
**Audience**: Desenvolvedores implementando ou usando a feature de conexão

## Overview

Este guia mostra exemplos práticos de como usar as operações de conexão RabbitMQ via MCP tools. Todos os exemplos utilizam o padrão de descoberta semântica com os 3 tools principais: `search-ids`, `get-id`, `call-id`.

---

## Prerequisites

### Environment Setup

```bash
# 1. Instalar dependências
pip install aio-pika structlog pydantic mcp-sdk

# 2. Iniciar RabbitMQ local (Docker)
docker run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=guest \
  -e RABBITMQ_DEFAULT_PASS=guest \
  rabbitmq:3-management

# 3. Verificar que RabbitMQ está rodando
curl http://localhost:15672/api/whoami -u guest:guest
```

### Configuration File

Crie `config.toml`:

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

[logging]
level = "INFO"
format = "json"
```

### Environment Variables

Ou configure via ENV vars (maior precedência):

```bash
export AMQP_HOST=localhost
export AMQP_PORT=5672
export AMQP_USER=guest
export AMQP_PASSWORD=guest
export AMQP_VHOST=/
```

---

## Example 1: Connect to RabbitMQ

### Step 1: Search for connection operation

```python
import asyncio
from mcp_client import MCPClient

async def main():
    client = MCPClient()
    
    # Busca semântica por operações de conexão
    result = await client.call_tool("search-ids", {
        "query": "connect to rabbitmq server",
        "pagination": {"page": 1, "page_size": 5}
    })
    
    print(result)
    # Output:
    # {
    #   "items": [
    #     {
    #       "operation_id": "connection.connect",
    #       "summary": "Estabelece conexão AMQP com RabbitMQ",
    #       "relevance_score": 0.95
    #     },
    #     {
    #       "operation_id": "connection.get_status",
    #       "summary": "Retorna estado atual da conexão",
    #       "relevance_score": 0.72
    #     }
    #   ],
    #   "pagination": {
    #     "page": 1,
    #     "page_size": 5,
    #     "total_items": 2,
    #     "total_pages": 1,
    #     "has_next": false,
    #     "has_previous": false
    #   }
    # }

asyncio.run(main())
```

### Step 2: Get operation schema

```python
async def main():
    client = MCPClient()
    
    # Obtém schema detalhado da operação
    schema = await client.call_tool("get-id", {
        "operation_id": "connection.connect"
    })
    
    print(schema)
    # Output:
    # {
    #   "operation_id": "connection.connect",
    #   "name": "Connect to RabbitMQ",
    #   "description": "Estabelece conexão AMQP com servidor RabbitMQ...",
    #   "category": "connection",
    #   "input_schema": {
    #     "type": "object",
    #     "properties": {
    #       "host": {"type": "string", "default": "localhost"},
    #       "port": {"type": "integer", "default": 5672},
    #       ...
    #     }
    #   },
    #   "output_schema": {...},
    #   "examples": [...]
    # }

asyncio.run(main())
```

### Step 3: Execute connection

```python
async def main():
    client = MCPClient()
    
    # Conecta usando defaults (localhost)
    result = await client.call_tool("call-id", {
        "operation_id": "connection.connect",
        "params": {}  # Usa defaults de config.toml ou ENV
    })
    
    print(result)
    # Output:
    # {
    #   "success": true,
    #   "result": {
    #     "connected": true,
    #     "connection_url": "amqp://guest:***@localhost:5672/",
    #     "latency_ms": 123.45,
    #     "server_properties": {
    #       "product": "RabbitMQ",
    #       "version": "3.12.0",
    #       "platform": "Erlang/OTP 25"
    #     }
    #   },
    #   "metadata": {
    #     "operation_id": "connection.connect",
    #     "duration_ms": 125.67,
    #     "timestamp": "2025-10-09T14:30:25.123Z"
    #   }
    # }

asyncio.run(main())
```

### Step 4: Connect to remote server

```python
async def main():
    client = MCPClient()
    
    # Conecta a servidor remoto com credenciais customizadas
    result = await client.call_tool("call-id", {
        "operation_id": "connection.connect",
        "params": {
            "host": "rabbitmq.example.com",
            "port": 5672,
            "user": "admin",
            "password": "secret123",
            "vhost": "/production",
            "timeout": 30,
            "heartbeat": 60
        }
    })
    
    if result["success"]:
        print(f"Conectado: {result['result']['connection_url']}")
        print(f"Latência: {result['result']['latency_ms']}ms")
    else:
        print(f"Erro: {result['error']['message']}")

asyncio.run(main())
```

---

## Example 2: Health Check

```python
async def main():
    client = MCPClient()
    
    # Verifica saúde da conexão
    result = await client.call_tool("call-id", {
        "operation_id": "connection.health_check",
        "params": {}
    })
    
    health = result["result"]
    
    if health["is_healthy"]:
        print(f"✓ Conexão saudável (latência: {health['latency_ms']}ms)")
    else:
        print(f"✗ Conexão não saudável: {health.get('error_message', 'Unknown')}")
    
    print(f"Conectado: {health['is_connected']}")
    print(f"Broker disponível: {health['broker_available']}")
    print(f"Última verificação: {health['last_check']}")

asyncio.run(main())
```

---

## Example 3: Get Connection Status

```python
async def main():
    client = MCPClient()
    
    # Obtém estado atual da conexão
    result = await client.call_tool("call-id", {
        "operation_id": "connection.get_status",
        "params": {}
    })
    
    status = result["result"]
    
    print(f"Estado: {status['state']}")
    print(f"URL: {status['connection_url']}")
    
    if status['state'] == 'connected':
        print(f"Conectado desde: {status['connected_since']}")
    elif status['state'] == 'reconnecting':
        print(f"Tentativas de reconexão: {status['retry_attempts']}")
        print(f"Próxima tentativa em: {status['next_retry_in_seconds']}s")

asyncio.run(main())
```

---

## Example 4: Monitor Connection Pool

```python
async def main():
    client = MCPClient()
    
    # Obtém estatísticas do pool
    result = await client.call_tool("call-id", {
        "operation_id": "pool.get_stats",
        "params": {}
    })
    
    stats = result["result"]
    
    print(f"Pool: {stats['in_use']}/{stats['total_connections']} em uso")
    print(f"Disponíveis: {stats['available']}")
    print(f"Aguardando: {stats['waiting_for_connection']}")
    print(f"Máximo: {stats['max_size']}")
    print(f"Timeout de aquisição: {stats['acquire_timeout_seconds']}s")
    
    # Alerta se pool está esgotado
    if stats['available'] == 0:
        print("⚠️ ALERTA: Pool esgotado!")

asyncio.run(main())
```

---

## Example 5: Graceful Disconnect

```python
async def main():
    client = MCPClient()
    
    # Desconecta graciosamente
    result = await client.call_tool("call-id", {
        "operation_id": "connection.disconnect",
        "params": {
            "force": False  # Aguarda operações pendentes
        }
    })
    
    if result["success"]:
        disconnect = result["result"]
        print(f"Desconectado: {disconnect['disconnected']}")
        print(f"Limpa: {disconnect['graceful']}")
        print(f"Duração: {disconnect['duration_ms']}ms")

asyncio.run(main())
```

---

## Example 6: Error Handling

```python
async def main():
    client = MCPClient()
    
    # Tenta conectar com credenciais inválidas
    result = await client.call_tool("call-id", {
        "operation_id": "connection.connect",
        "params": {
            "host": "localhost",
            "user": "invalid",
            "password": "wrong"
        }
    })
    
    if not result["success"]:
        error = result["error"]
        print(f"Erro: {error['code']}")
        print(f"Mensagem: {error['message']}")
        
        if error['code'] == 'AUTHENTICATION_FAILED':
            print("Resolução: Verifique usuário e senha")
        elif error['code'] == 'CONNECTION_TIMEOUT':
            print("Resolução: Verifique se servidor está acessível")
        elif error['code'] == 'VHOST_NOT_FOUND':
            print("Resolução: Crie o vhost ou use um existente")

asyncio.run(main())
```

---

## Example 7: Automatic Reconnection Monitoring

```python
async def monitor_connection():
    """Monitora estado da conexão continuamente"""
    client = MCPClient()
    
    while True:
        status_result = await client.call_tool("call-id", {
            "operation_id": "connection.get_status",
            "params": {}
        })
        
        status = status_result["result"]
        state = status["state"]
        
        if state == "connected":
            print(f"✓ Conectado: {status['connection_url']}")
        elif state == "reconnecting":
            attempts = status["retry_attempts"]
            next_retry = status["next_retry_in_seconds"]
            print(f"⟳ Reconectando... Tentativa #{attempts}, próxima em {next_retry}s")
        elif state == "disconnected":
            print(f"✗ Desconectado")
        
        await asyncio.sleep(5)  # Verifica a cada 5 segundos

asyncio.run(monitor_connection())
```

---

## Example 8: Complete Workflow

```python
async def complete_workflow():
    """Workflow completo: conectar, verificar saúde, monitorar pool, desconectar"""
    client = MCPClient()
    
    try:
        # 1. Conectar
        print("1. Conectando ao RabbitMQ...")
        connect_result = await client.call_tool("call-id", {
            "operation_id": "connection.connect",
            "params": {
                "host": "localhost",
                "timeout": 10
            }
        })
        
        if not connect_result["success"]:
            raise Exception(f"Falha ao conectar: {connect_result['error']['message']}")
        
        print(f"   ✓ Conectado em {connect_result['result']['latency_ms']}ms")
        
        # 2. Verificar saúde
        print("\n2. Verificando saúde da conexão...")
        health_result = await client.call_tool("call-id", {
            "operation_id": "connection.health_check",
            "params": {}
        })
        
        health = health_result["result"]
        print(f"   ✓ Saudável: {health['is_healthy']}")
        print(f"   Latência: {health['latency_ms']}ms")
        
        # 3. Monitorar pool
        print("\n3. Estatísticas do pool...")
        pool_result = await client.call_tool("call-id", {
            "operation_id": "pool.get_stats",
            "params": {}
        })
        
        stats = pool_result["result"]
        print(f"   Conexões: {stats['in_use']}/{stats['total_connections']}")
        print(f"   Disponíveis: {stats['available']}")
        
        # 4. Simular operações (aguardar)
        print("\n4. Executando operações...")
        await asyncio.sleep(2)
        print("   ✓ Operações concluídas")
        
        # 5. Desconectar
        print("\n5. Desconectando...")
        disconnect_result = await client.call_tool("call-id", {
            "operation_id": "connection.disconnect",
            "params": {"force": False}
        })
        
        if disconnect_result["success"]:
            print(f"   ✓ Desconectado (limpa: {disconnect_result['result']['graceful']})")
        
        print("\n✓ Workflow completo!")
        
    except Exception as e:
        print(f"✗ Erro no workflow: {e}")

asyncio.run(complete_workflow())
```

---

## Example 9: Testing Reconnection

```python
async def test_reconnection():
    """Testa comportamento de reconexão automática"""
    client = MCPClient()
    
    # 1. Conectar
    await client.call_tool("call-id", {
        "operation_id": "connection.connect",
        "params": {}
    })
    print("✓ Conectado")
    
    # 2. Aguardar usuário simular falha
    print("\nSimule perda de conexão (pare o container RabbitMQ):")
    print("  docker stop rabbitmq")
    input("Pressione ENTER após parar o RabbitMQ...")
    
    # 3. Monitorar reconexão
    print("\nMonitorando reconexão...")
    for i in range(30):  # Monitora por 30 iterações
        status_result = await client.call_tool("call-id", {
            "operation_id": "connection.get_status",
            "params": {}
        })
        
        status = status_result["result"]
        state = status["state"]
        
        if state == "reconnecting":
            print(f"  ⟳ Tentativa #{status['retry_attempts']}, próxima em {status['next_retry_in_seconds']}s")
        elif state == "connected":
            print(f"  ✓ Reconectado com sucesso!")
            break
        
        await asyncio.sleep(2)
    
    print("\nReinicie o RabbitMQ:")
    print("  docker start rabbitmq")
    input("Pressione ENTER após reiniciar o RabbitMQ...")
    
    # 4. Aguardar reconexão
    print("\nAguardando reconexão...")
    for i in range(20):
        status_result = await client.call_tool("call-id", {
            "operation_id": "connection.get_status",
            "params": {}
        })
        
        if status_result["result"]["state"] == "connected":
            print("✓ Reconectado automaticamente!")
            
            # Verificar saúde
            health_result = await client.call_tool("call-id", {
                "operation_id": "connection.health_check",
                "params": {}
            })
            print(f"  Saúde: {health_result['result']['is_healthy']}")
            break
        
        await asyncio.sleep(3)

asyncio.run(test_reconnection())
```

---

## Example 10: Using with Context Manager

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def rabbitmq_connection(client: MCPClient, **connection_params):
    """Context manager para gerenciar ciclo de vida da conexão"""
    
    # Connect
    connect_result = await client.call_tool("call-id", {
        "operation_id": "connection.connect",
        "params": connection_params
    })
    
    if not connect_result["success"]:
        raise Exception(f"Failed to connect: {connect_result['error']['message']}")
    
    try:
        yield client
    finally:
        # Disconnect
        await client.call_tool("call-id", {
            "operation_id": "connection.disconnect",
            "params": {"force": False}
        })

async def main():
    client = MCPClient()
    
    async with rabbitmq_connection(client, host="localhost", timeout=10):
        # Usar conexão
        health = await client.call_tool("call-id", {
            "operation_id": "connection.health_check",
            "params": {}
        })
        print(f"Health: {health['result']['is_healthy']}")
    
    # Desconectado automaticamente ao sair do context

asyncio.run(main())
```

---

## Logging Output Examples

### Successful Connection

```json
{
  "timestamp": "2025-10-09T14:30:25.123Z",
  "level": "info",
  "event_type": "connection.established",
  "message": "Connection established successfully",
  "context": {
    "host": "localhost",
    "port": 5672,
    "vhost": "/",
    "user": "guest",
    "password": "***REDACTED***",
    "latency_ms": 123.45
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Connection Failed

```json
{
  "timestamp": "2025-10-09T14:31:00.456Z",
  "level": "error",
  "event_type": "connection.failed",
  "message": "Failed to establish connection",
  "context": {
    "host": "localhost",
    "port": 5672,
    "vhost": "/",
    "user": "guest",
    "password": "***REDACTED***",
    "error_code": "AUTHENTICATION_FAILED",
    "error_message": "Invalid credentials"
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440001"
}
```

### Reconnecting

```json
{
  "timestamp": "2025-10-09T14:32:15.789Z",
  "level": "warn",
  "event_type": "connection.reconnecting",
  "message": "Connection lost, attempting to reconnect",
  "context": {
    "host": "localhost",
    "port": 5672,
    "vhost": "/",
    "retry_attempt": 3,
    "next_retry_in_seconds": 8.0,
    "backoff_delay": 8.0
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440002"
}
```

---

## Performance Benchmarks

### Expected Performance

| Operation | Target | Typical |
|-----------|--------|---------|
| `connection.connect` | <5s | 100-500ms |
| `connection.health_check` | <1s | 10-50ms |
| `connection.disconnect` | N/A | 20-100ms |
| `connection.get_status` | <100ms | 1-5ms |
| `pool.get_stats` | <100ms | 1-5ms |

### Throughput

- **Operações simultâneas**: 10+ (pool de 5 conexões)
- **Latência adicional do pool**: <10ms
- **Overhead de retry**: Exponencial (1s → 2s → 4s → ... → 60s)

---

## Troubleshooting

### Connection Timeout

**Sintoma**: `CONNECTION_TIMEOUT` error após 30 segundos

**Causas possíveis**:
- RabbitMQ não está rodando
- Firewall bloqueando porta 5672
- Host/porta incorretos

**Solução**:
```bash
# Verificar se RabbitMQ está rodando
docker ps | grep rabbitmq

# Testar conectividade
telnet localhost 5672

# Ver logs do RabbitMQ
docker logs rabbitmq
```

### Authentication Failed

**Sintoma**: `AUTHENTICATION_FAILED` error

**Causas possíveis**:
- Credenciais inválidas
- Usuário sem permissão no vhost

**Solução**:
```bash
# Listar usuários
docker exec rabbitmq rabbitmqctl list_users

# Definir permissões
docker exec rabbitmq rabbitmqctl set_permissions -p / guest ".*" ".*" ".*"
```

### Pool Exhausted

**Sintoma**: `POOL_TIMEOUT` após 10 segundos

**Causas possíveis**:
- Mais de 5 operações simultâneas
- Conexões não sendo liberadas

**Solução**:
- Aumentar `max_size` do pool em config.toml
- Garantir que conexões sejam liberadas após uso
- Usar context manager para gerenciamento automático

---

## Next Steps

Após familiarizar-se com a conexão básica:

1. **Topology Operations** (Feature 003): Criar exchanges, queues, bindings
2. **Message Publishing** (Feature 004): Publicar mensagens
3. **Message Consumption** (Feature 004): Consumir mensagens com callbacks
4. **Advanced Monitoring** (Feature 012): Métricas detalhadas e alertas

---

## References

- [RabbitMQ Documentation](https://www.rabbitmq.com/docs)
- [aio-pika Documentation](https://aio-pika.readthedocs.io/)
- [MCP Protocol Specification](https://github.com/modelcontextprotocol/protocol)
- [Feature Specification](./spec.md)
- [Data Model](./data-model.md)
- [Contracts](./contracts/)
