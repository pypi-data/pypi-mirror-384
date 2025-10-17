# Quickstart Guide: Base MCP Architecture

**Feature**: Base MCP Architecture  
**Date**: 2025-10-09  
**Target Audience**: Developers integrating with the RabbitMQ MCP Server

## Overview

Este guia rápido demonstra como usar o servidor MCP com padrão de descoberta semântica para interagir com RabbitMQ em 5 minutos.

## Prerequisites

- Python 3.12+
- RabbitMQ 3.12+ com Management Plugin habilitado
- Credenciais RabbitMQ (username/password)
- MCP client (Cursor, VS Code com extensão MCP, ou qualquer cliente MCP compatível)

## Quick Setup (5 minutos)

### 1. Instalar o servidor MCP

```bash
# Usando uvx (recomendado - gerenciamento de dependências rápido)
uvx install rabbitmq-mcp-server

# Ou com pip
pip install rabbitmq-mcp-server
```

### 2. Configurar variáveis de ambiente

```bash
# Linux/macOS
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=15672
export RABBITMQ_USERNAME=guest
export RABBITMQ_PASSWORD=guest
export RABBITMQ_API_VERSION=3.13

# Windows PowerShell
$env:RABBITMQ_HOST="localhost"
$env:RABBITMQ_PORT="15672"
$env:RABBITMQ_USERNAME="guest"
$env:RABBITMQ_PASSWORD="guest"
$env:RABBITMQ_API_VERSION="3.13"
```

### 3. Iniciar o servidor MCP

```bash
# Modo development
rabbitmq-mcp-server --dev

# Modo production
rabbitmq-mcp-server --config config/config.yaml
```

### 4. Configurar MCP client

#### Cursor / VS Code

Adicione ao `.mcp/settings.json`:

```json
{
  "mcpServers": {
    "rabbitmq": {
      "command": "rabbitmq-mcp-server",
      "args": ["--config", "config/config.yaml"],
      "env": {
        "RABBITMQ_HOST": "localhost",
        "RABBITMQ_USERNAME": "guest",
        "RABBITMQ_PASSWORD": "guest"
      }
    }
  }
}
```

## Basic Usage: 3-Step Workflow

O servidor MCP expõe **apenas 3 ferramentas públicas** que seguem o padrão de descoberta semântica:

### Step 1: 🔍 Descobrir operações (search-ids)

Use linguagem natural para encontrar operações relevantes:

```json
{
  "tool": "search-ids",
  "input": {
    "query": "listar todas as filas",
    "pagination": {
      "page": 1,
      "pageSize": 10
    }
  }
}
```

**Resposta**:
```json
{
  "items": [
    {
      "operation_id": "queues.list",
      "name": "List Queues",
      "description": "List all queues in a virtual host with optional filtering",
      "namespace": "queues",
      "similarity_score": 0.92,
      "parameter_hint": "vhost (required), page, pageSize"
    },
    {
      "operation_id": "queues.get",
      "name": "Get Queue",
      "description": "Get detailed information about a specific queue",
      "namespace": "queues",
      "similarity_score": 0.85,
      "parameter_hint": "vhost (required), name (required)"
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 10,
    "totalItems": 2,
    "totalPages": 1,
    "hasNextPage": false,
    "hasPreviousPage": false
  }
}
```

### Step 2: 📋 Obter detalhes da operação (get-id)

Consulte o esquema completo e exemplos:

```json
{
  "tool": "get-id",
  "input": {
    "endpoint_id": "queues.list"
  }
}
```

**Resposta**:
```json
{
  "operation_id": "queues.list",
  "name": "List Queues",
  "description": "List all queues in a virtual host with optional filtering...",
  "namespace": "queues",
  "request_schema": {
    "type": "object",
    "properties": {
      "vhost": {
        "type": "string",
        "description": "Virtual host name",
        "default": "/"
      },
      "page": {
        "type": "integer",
        "minimum": 1,
        "default": 1
      },
      "pageSize": {
        "type": "integer",
        "minimum": 1,
        "maximum": 200,
        "default": 50
      }
    },
    "required": ["vhost"]
  },
  "response_schema": {
    "type": "array",
    "items": { /* Queue schema */ }
  },
  "examples": [ /* Usage examples */ ],
  "deprecated": false,
  "requires_auth": true,
  "timeout_seconds": 30,
  "supports_pagination": true
}
```

### Step 3: ⚡ Executar operação (call-id)

Execute a operação com parâmetros validados:

```json
{
  "tool": "call-id",
  "input": {
    "endpoint_id": "queues.list",
    "params": {
      "vhost": "/"
    },
    "pagination": {
      "page": 1,
      "pageSize": 50
    }
  }
}
```

**Resposta (Sucesso)**:
```json
{
  "items": [
    {
      "name": "my-queue",
      "vhost": "/",
      "durable": true,
      "messages": 42,
      "consumers": 2
    }
  ],
  "pagination": {
    "page": 1,
    "pageSize": 50,
    "totalItems": 1,
    "totalPages": 1,
    "hasNextPage": false,
    "hasPreviousPage": false
  },
  "metadata": {
    "operation_id": "queues.list",
    "duration_ms": 145,
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736"
  }
}
```

**Resposta (Erro)**:
```json
{
  "error": {
    "code": -32602,
    "message": "Invalid params: missing required field 'vhost'",
    "data": {
      "missing": ["vhost"],
      "invalid": [],
      "expected_schema": { /* Schema details */ }
    }
  }
}
```

## Common Use Cases

### Use Case 1: Criar uma fila

```json
// Step 1: Buscar operação
{"tool": "search-ids", "input": {"query": "criar fila"}}

// Step 2: Ver detalhes
{"tool": "get-id", "input": {"endpoint_id": "queues.create"}}

// Step 3: Executar
{
  "tool": "call-id",
  "input": {
    "endpoint_id": "queues.create",
    "params": {
      "vhost": "/",
      "name": "my-new-queue",
      "durable": true,
      "auto_delete": false
    }
  }
}
```

### Use Case 2: Criar um exchange

```json
// Step 1: Buscar
{"tool": "search-ids", "input": {"query": "criar exchange"}}

// Step 2: Ver detalhes
{"tool": "get-id", "input": {"endpoint_id": "exchanges.create"}}

// Step 3: Executar
{
  "tool": "call-id",
  "input": {
    "endpoint_id": "exchanges.create",
    "params": {
      "vhost": "/",
      "name": "my-exchange",
      "type": "direct",
      "durable": true
    }
  }
}
```

### Use Case 3: Criar binding entre exchange e queue

```json
// Step 1: Buscar
{"tool": "search-ids", "input": {"query": "binding queue exchange"}}

// Step 2: Ver detalhes
{"tool": "get-id", "input": {"endpoint_id": "bindings.create-exchange-queue"}}

// Step 3: Executar
{
  "tool": "call-id",
  "input": {
    "endpoint_id": "bindings.create-exchange-queue",
    "params": {
      "vhost": "/",
      "exchange": "my-exchange",
      "queue": "my-queue",
      "routing_key": "my.routing.key"
    }
  }
}
```

### Use Case 4: Listar conexões ativas

```json
// Step 1: Buscar
{"tool": "search-ids", "input": {"query": "conexões ativas"}}

// Step 2: Ver detalhes
{"tool": "get-id", "input": {"endpoint_id": "connections.list"}}

// Step 3: Executar
{
  "tool": "call-id",
  "input": {
    "endpoint_id": "connections.list",
    "params": {},
    "pagination": {"page": 1, "pageSize": 50}
  }
}
```

## Error Handling

### Validation Errors (-32602)

```json
{
  "error": {
    "code": -32602,
    "message": "Invalid params: validation failed",
    "data": {
      "missing": ["vhost"],
      "invalid": ["pageSize: must be <= 200"],
      "provided": ["name", "pageSize"],
      "expected_schema": { /* Full schema */ }
    }
  }
}
```

**Resolution**: Verifique os campos obrigatórios e limites usando `get-id` antes de executar.

### Connection Errors (-32000)

```json
{
  "error": {
    "code": -32000,
    "message": "Server error: RabbitMQ connection failed",
    "data": {
      "reason": "Connection refused",
      "rabbitmq_host": "localhost:15672",
      "resolution": "Check if RabbitMQ is running and credentials are correct"
    }
  }
}
```

**Resolution**: Verifique se RabbitMQ está rodando e credenciais estão corretas.

### Timeout Errors (-32001)

```json
{
  "error": {
    "code": -32001,
    "message": "Timeout error: operation exceeded 30s timeout",
    "data": {
      "operation_id": "queues.list",
      "timeout_seconds": 30,
      "resolution": "Try with more specific filters"
    }
  }
}
```

**Resolution**: Use filtros mais específicos ou aumente recursos do RabbitMQ.

### Rate Limit Errors (-32002)

```json
{
  "error": {
    "code": -32002,
    "message": "Rate limit error: client exceeded 100 requests per minute",
    "data": {
      "limit": 100,
      "retry_after_seconds": 45
    }
  }
}
```

**Resolution**: Aguarde o tempo indicado em `retry_after_seconds` antes de tentar novamente.

## Performance Tips

### 1. Use Pagination
Para listagens grandes, sempre use pagination para evitar timeouts:

```json
{
  "tool": "call-id",
  "input": {
    "endpoint_id": "queues.list",
    "params": {"vhost": "/"},
    "pagination": {"page": 1, "pageSize": 50}
  }
}
```

### 2. Cache Operation Details
Use `get-id` uma vez e armazene localmente. Schemas raramente mudam.

### 3. Batch Related Operations
Agrupe operações relacionadas em sequência para melhor performance:

```python
# Criar exchange, queue e binding em sequência
operations = [
    ("exchanges.create", {"vhost": "/", "name": "ex", "type": "direct"}),
    ("queues.create", {"vhost": "/", "name": "q", "durable": true}),
    ("bindings.create-exchange-queue", {"vhost": "/", "exchange": "ex", "queue": "q"})
]

for op_id, params in operations:
    call_id(endpoint_id=op_id, params=params)
```

### 4. Monitor Traces
Use OpenTelemetry trace IDs para debug de performance:

```json
{
  "metadata": {
    "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
    "duration_ms": 145
  }
}
```

## Configuration

### config.yaml

```yaml
rabbitmq:
  host: localhost
  port: 15672
  username: guest
  password: guest
  timeout_seconds: 30
  api_version: "3.13"

mcp:
  rate_limit_rpm: 100  # Requests per minute per client
  max_concurrent_requests: 50

vector_db:
  similarity_threshold: 0.7
  max_results_per_page: 25

logging:
  level: INFO
  format: json
  output: ./logs/
  rotation: daily
  retention_days: 30

telemetry:
  enabled: true
  exporter: otlp
  endpoint: http://localhost:4317
```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `RABBITMQ_HOST` | RabbitMQ host | localhost | ✅ |
| `RABBITMQ_PORT` | Management API port | 15672 | ❌ |
| `RABBITMQ_USERNAME` | Username | guest | ✅ |
| `RABBITMQ_PASSWORD` | Password | guest | ✅ |
| `RABBITMQ_API_VERSION` | OpenAPI version | 3.13 | ❌ |
| `LOG_LEVEL` | Logging level | INFO | ❌ |
| `RATE_LIMIT_RPM` | Rate limit per minute | 100 | ❌ |

## Troubleshooting

### Server não inicia

**Sintoma**: Erro ao iniciar servidor MCP

**Soluções**:
1. Verifique Python version: `python --version` (deve ser 3.12+)
2. Reinstale dependências: `uvx reinstall rabbitmq-mcp-server`
3. Verifique logs: `tail -f ./logs/rabbitmq-mcp-*.log`

### Busca semântica retorna resultados irrelevantes

**Sintoma**: `search-ids` retorna operações não relacionadas

**Soluções**:
1. Use queries mais específicas: "criar fila durável" em vez de "fila"
2. Verifique similarity_score (deve ser >= 0.7)
3. Combine múltiplas buscas para refinar resultados

### Timeout em operações

**Sintoma**: Erro `-32001` (timeout)

**Soluções**:
1. Use pagination para listagens grandes
2. Adicione filtros mais específicos aos parâmetros
3. Verifique performance do RabbitMQ
4. Aumente `timeout_seconds` no config (max: 30)

### Rate limit atingido

**Sintoma**: Erro `-32002` (rate limit)

**Soluções**:
1. Implemente backoff exponencial no cliente
2. Reduza frequência de requisições
3. Aumente `RATE_LIMIT_RPM` se justificado

## Next Steps

1. **Explore operações**: Use `search-ids` com diferentes queries para descobrir todas as ~150-300 operações disponíveis
2. **Leia contratos**: Veja `contracts/` para detalhes completos de cada ferramenta
3. **Consulte data model**: Veja `data-model.md` para entender entidades e relacionamentos
4. **Configure logging**: Ajuste `config.yaml` para seu ambiente
5. **Setup monitoring**: Configure OpenTelemetry exporters para observability
6. **Write tests**: Use os contratos para validar integrações

## Resources

- **Contracts**: `/specs/feature/001-base-architecture/contracts/`
- **Data Model**: `/specs/feature/001-base-architecture/data-model.md`
- **Research**: `/specs/feature/001-base-architecture/research.md`
- **MCP Protocol**: https://modelcontextprotocol.io/docs
- **RabbitMQ HTTP API**: https://www.rabbitmq.com/docs/management-http-api

## Support

Para issues ou dúvidas:
1. Verifique logs: `./logs/rabbitmq-mcp-*.log`
2. Consulte OpenTelemetry traces usando `trace_id`
3. Reporte issues com logs e trace IDs

---

**Tempo estimado para este quickstart**: 5-10 minutos  
**Nível**: Iniciante/Intermediário  
**Versão**: 1.0.0
