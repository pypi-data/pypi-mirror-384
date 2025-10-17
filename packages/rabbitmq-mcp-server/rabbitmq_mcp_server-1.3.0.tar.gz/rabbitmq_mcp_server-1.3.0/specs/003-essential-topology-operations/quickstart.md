# Quick Start Guide: Essential Topology Operations

**Feature**: 003-essential-topology-operations  
**Date**: 2025-10-09  
**Audience**: Operators and developers using RabbitMQ MCP Server

## Overview

Este guia demonstra como usar as operações essenciais de topologia RabbitMQ através do padrão de descoberta semântica MCP e da CLI integrada.

## Prerequisites

- Python 3.12+ instalado
- RabbitMQ Management API habilitado e acessível
- Credenciais de acesso ao RabbitMQ

## Installation

### Using uvx (Recommended)

```bash
# Run directly without installation
uvx rabbitmq-mcp-server --help

# Execute specific command
uvx rabbitmq-mcp-server queue list --host localhost --user admin --password admin
```

### Using pip

```bash
# Install globally
pip install rabbitmq-mcp-server

# Verify installation
rabbitmq-mcp-server --version
```

## Basic Usage Patterns

### 1. CLI Interface (Direct Commands)

A CLI oferece comandos diretos para operações comuns:

#### List Operations

```bash
# List all queues across all virtual hosts
rabbitmq-mcp-server queue list \
  --host localhost \
  --port 15672 \
  --user admin \
  --password admin

# List queues in specific virtual host
rabbitmq-mcp-server queue list \
  --host localhost \
  --user admin \
  --password admin \
  --vhost /production

# List all exchanges
rabbitmq-mcp-server exchange list \
  --host localhost \
  --user admin \
  --password admin

# List all bindings
rabbitmq-mcp-server binding list \
  --host localhost \
  --user admin \
  --password admin \
  --vhost /production
```

#### Create Operations

```bash
# Create a durable queue
rabbitmq-mcp-server queue create \
  --host localhost \
  --user admin \
  --password admin \
  --vhost /production \
  --name orders.processing.queue \
  --durable

# Create queue with arguments
rabbitmq-mcp-server queue create \
  --host localhost \
  --user admin \
  --password admin \
  --vhost /production \
  --name orders.dlq \
  --durable \
  --arguments '{"x-message-ttl": 86400000, "x-max-length": 1000}'

# Create topic exchange
rabbitmq-mcp-server exchange create \
  --host localhost \
  --user admin \
  --password admin \
  --vhost /production \
  --name orders.exchange \
  --type topic \
  --durable

# Create binding with routing key
rabbitmq-mcp-server binding create \
  --host localhost \
  --user admin \
  --password admin \
  --vhost /production \
  --exchange orders.exchange \
  --queue orders.processing.queue \
  --routing-key "orders.*.created"
```

#### Delete Operations

```bash
# Delete empty queue
rabbitmq-mcp-server queue delete \
  --host localhost \
  --user admin \
  --password admin \
  --vhost /production \
  --name orders.processing.queue

# Force delete queue with messages
rabbitmq-mcp-server queue delete \
  --host localhost \
  --user admin \
  --password admin \
  --vhost /production \
  --name orders.processing.queue \
  --force

# Delete exchange (only if no bindings)
rabbitmq-mcp-server exchange delete \
  --host localhost \
  --user admin \
  --password admin \
  --vhost /production \
  --name orders.exchange

# Delete binding
rabbitmq-mcp-server binding delete \
  --host localhost \
  --user admin \
  --password admin \
  --vhost /production \
  --exchange orders.exchange \
  --queue orders.processing.queue \
  --properties-key "orders.*.created"
```

### 2. Environment Variables (Avoid Repeating Credentials)

```bash
# Set environment variables
export RABBITMQ_HOST=localhost
export RABBITMQ_PORT=15672
export RABBITMQ_USER=admin
export RABBITMQ_PASSWORD=admin
export RABBITMQ_VHOST=/production

# Now commands are shorter
rabbitmq-mcp-server queue list
rabbitmq-mcp-server queue create --name orders.queue --durable
rabbitmq-mcp-server exchange list
```

### 3. JSON Output for Scripting

```bash
# Get JSON output for processing
rabbitmq-mcp-server queue list --format json > queues.json

# Parse with jq
rabbitmq-mcp-server queue list --format json | jq '.[] | select(.messages > 1000)'

# Get specific queue details
rabbitmq-mcp-server queue get \
  --name orders.processing.queue \
  --format json | jq '.messages_ready'
```

---

## MCP Semantic Discovery Pattern

Para operações programáticas via MCP client:

### Step 1: Search for Operations

```python
# Find queue-related operations
await mcp_client.call_tool("search-ids", {
    "query": "list all queues with message counts",
    "pagination": {"page": 1, "pageSize": 10}
})

# Response:
{
    "items": [
        {
            "operation_id": "queues.list",
            "description": "List all queues with statistics",
            "summary": "Get queue information including message counts"
        },
        {
            "operation_id": "queues.get",
            "description": "Get specific queue details",
            "summary": "Retrieve detailed queue information"
        }
    ],
    "pagination": {
        "page": 1,
        "pageSize": 10,
        "totalItems": 2,
        "hasNextPage": false
    }
}
```

### Step 2: Get Operation Schema

```python
# Get detailed schema for queues.list
await mcp_client.call_tool("get-id", {
    "endpoint_id": "queues.list"
})

# Response:
{
    "operation_id": "queues.list",
    "description": "List all queues across all virtual hosts with statistics",
    "parameters": {
        "vhost": {
            "type": "string",
            "required": false,
            "description": "Filter queues by virtual host",
            "example": "/production"
        }
    },
    "response_schema": {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "name": "string",
                "vhost": "string",
                "messages": "integer",
                "consumers": "integer"
            }
        }
    },
    "examples": [
        {
            "description": "List all queues",
            "params": {}
        },
        {
            "description": "List queues in specific vhost",
            "params": {"vhost": "/production"}
        }
    ]
}
```

### Step 3: Execute Operation

```python
# Execute queues.list operation
await mcp_client.call_tool("call-id", {
    "endpoint_id": "queues.list",
    "params": {
        "vhost": "/production"
    }
})

# Response:
[
    {
        "name": "orders.processing.queue",
        "vhost": "/production",
        "durable": true,
        "messages": 1523,
        "messages_ready": 1200,
        "messages_unacknowledged": 323,
        "consumers": 5,
        "memory": 2048576,
        "state": "running"
    }
]
```

---

## Common Use Cases

### Use Case 1: View Infrastructure State

```bash
# Check queue statistics
rabbitmq-mcp-server queue list --format json | \
  jq '.[] | {name, messages, consumers}'

# Output:
# {
#   "name": "orders.processing.queue",
#   "messages": 1523,
#   "consumers": 5
# }

# Find queues with many messages
rabbitmq-mcp-server queue list --format json | \
  jq '.[] | select(.messages > 1000) | .name'

# Find queues without consumers
rabbitmq-mcp-server queue list --format json | \
  jq '.[] | select(.consumers == 0) | .name'
```

### Use Case 2: Setup New Message Flow

```bash
# Step 1: Create exchange
rabbitmq-mcp-server exchange create \
  --name orders.exchange \
  --type topic \
  --durable

# Step 2: Create queue
rabbitmq-mcp-server queue create \
  --name orders.processing.queue \
  --durable \
  --arguments '{"x-message-ttl": 3600000}'

# Step 3: Create binding
rabbitmq-mcp-server binding create \
  --exchange orders.exchange \
  --queue orders.processing.queue \
  --routing-key "orders.*.created"

# Step 4: Verify setup
rabbitmq-mcp-server binding list | grep orders.exchange
```

### Use Case 3: Safe Cleanup

```bash
# Step 1: Check queue is empty
rabbitmq-mcp-server queue get --name old.queue --format json | jq '.messages'

# Step 2: If empty, delete
rabbitmq-mcp-server queue delete --name old.queue

# Step 3: Delete binding first if exchange has bindings
rabbitmq-mcp-server binding delete \
  --exchange old.exchange \
  --queue old.queue \
  --properties-key ""

# Step 4: Now delete exchange
rabbitmq-mcp-server exchange delete --name old.exchange
```

### Use Case 4: Error Handling Examples

```bash
# Attempt to delete queue with messages (will fail)
rabbitmq-mcp-server queue delete --name busy.queue

# Output:
# Error: Cannot delete queue 'busy.queue' containing 523 messages.
# Use --force flag to force deletion.

# Force deletion
rabbitmq-mcp-server queue delete --name busy.queue --force

# Attempt to delete exchange with bindings (will fail)
rabbitmq-mcp-server exchange delete --name orders.exchange

# Output:
# Error: Cannot delete exchange 'orders.exchange' with 5 active bindings.
# Remove bindings first using 'binding delete' command.
```

---

## Routing Key Patterns (Topic Exchanges)

### Single Wildcard (*)

Matches exactly one word:

```bash
# Binding: orders.*.created
# Matches:
#   - orders.eu.created ✓
#   - orders.us.created ✓
# Does NOT match:
#   - orders.created ✗ (zero words)
#   - orders.eu.us.created ✗ (two words)

rabbitmq-mcp-server binding create \
  --exchange orders.exchange \
  --queue orders.eu.queue \
  --routing-key "orders.*.created"
```

### Multi Wildcard (#)

Matches zero or more words:

```bash
# Binding: orders.#
# Matches:
#   - orders.created ✓
#   - orders.eu.created ✓
#   - orders.eu.us.created ✓
#   - orders.anything.here ✓

rabbitmq-mcp-server binding create \
  --exchange orders.exchange \
  --queue orders.all.queue \
  --routing-key "orders.#"
```

### Combined Wildcards

```bash
# Binding: orders.*.#
# Matches:
#   - orders.eu.created ✓
#   - orders.us.processing.completed ✓
# Does NOT match:
#   - orders.created ✗ (needs at least one word after orders)

rabbitmq-mcp-server binding create \
  --exchange orders.exchange \
  --queue orders.complex.queue \
  --routing-key "orders.*.#"
```

---

## Performance Tips

### Batch Operations (Script)

```bash
#!/bin/bash
# create-queues.sh

QUEUES=(
  "orders.processing.queue"
  "orders.retry.queue"
  "orders.dlq"
)

for queue in "${QUEUES[@]}"; do
  rabbitmq-mcp-server queue create \
    --name "$queue" \
    --durable \
    --arguments '{"x-message-ttl": 3600000}' && \
  echo "✓ Created $queue"
done
```

### PowerShell Batch Operations

```powershell
# create-queues.ps1

$queues = @(
  "orders.processing.queue",
  "orders.retry.queue",
  "orders.dlq"
)

foreach ($queue in $queues) {
  rabbitmq-mcp-server queue create `
    --name $queue `
    --durable `
    --arguments '{"x-message-ttl": 3600000}'
  
  if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Created $queue" -ForegroundColor Green
  } else {
    Write-Host "✗ Failed to create $queue" -ForegroundColor Red
  }
}
```

---

## Troubleshooting

### Connection Issues

```bash
# Test connection
rabbitmq-mcp-server health-check \
  --host localhost \
  --port 15672 \
  --user admin \
  --password admin

# Output:
# ✓ RabbitMQ Management API is accessible
# ✓ Authentication successful
# ✓ Connection latency: 15ms
```

### Permission Issues

```bash
# Check user permissions
rabbitmq-mcp-server user permissions \
  --user myuser

# Output:
# Error: User 'myuser' does not have configure permission on vhost '/production'
# Suggestion: Grant permissions using: rabbitmqctl set_permissions -p /production myuser ".*" ".*" ".*"
```

### Validation Errors

```bash
# Invalid queue name
rabbitmq-mcp-server queue create --name "my queue!"

# Output:
# Error: Queue name 'my queue!' contains invalid characters.
# Only alphanumeric, hyphen, underscore, and dot allowed (max 255 chars).
# Field: name
# Expected: ^[a-zA-Z0-9._-]{1,255}$
# Actual: my queue!

# Invalid exchange type
rabbitmq-mcp-server exchange create --name test --type invalid

# Output:
# Error: Exchange type 'invalid' is not supported.
# Allowed types: direct, topic, fanout, headers.
```

---

## Advanced Configuration

### Configuration File

Create `~/.rabbitmq-mcp/config.yaml`:

```yaml
connection:
  host: localhost
  port: 15672
  user: admin
  password: admin
  vhost: /production
  timeout: 5

logging:
  level: INFO
  format: json
  file: ~/.rabbitmq-mcp/logs/rabbitmq-mcp.log

output:
  format: table  # table, json
  colors: true
```

Use config file:

```bash
rabbitmq-mcp-server queue list --config ~/.rabbitmq-mcp/config.yaml
```

---

## Next Steps

- Read [API.md](../../../docs/API.md) for complete operation reference
- Read [ARCHITECTURE.md](../../../docs/ARCHITECTURE.md) for system design
- Read [EXAMPLES.md](../../../docs/EXAMPLES.md) for more usage patterns
- Check [CONTRIBUTING.md](../../../docs/CONTRIBUTING.md) to contribute

---

## Quick Reference

### Queue Commands
```bash
rabbitmq-mcp-server queue list [--vhost VHOST] [--format FORMAT]
rabbitmq-mcp-server queue create --name NAME [--durable] [--exclusive] [--auto-delete] [--arguments JSON]
rabbitmq-mcp-server queue delete --name NAME [--force]
rabbitmq-mcp-server queue get --name NAME [--format FORMAT]
```

### Exchange Commands
```bash
rabbitmq-mcp-server exchange list [--vhost VHOST] [--format FORMAT]
rabbitmq-mcp-server exchange create --name NAME --type TYPE [--durable] [--auto-delete] [--internal] [--arguments JSON]
rabbitmq-mcp-server exchange delete --name NAME
rabbitmq-mcp-server exchange get --name NAME [--format FORMAT]
```

### Binding Commands
```bash
rabbitmq-mcp-server binding list [--vhost VHOST] [--format FORMAT]
rabbitmq-mcp-server binding create --exchange EXCHANGE --queue QUEUE [--routing-key KEY] [--arguments JSON]
rabbitmq-mcp-server binding delete --exchange EXCHANGE --queue QUEUE --properties-key KEY
```

### MCP Tools (for programmatic access)
```bash
search-ids    # Semantic search for operations
get-id        # Get operation schema
call-id       # Execute operation
```

---

**Documentation Version**: 1.0  
**Last Updated**: 2025-10-09  
**Feature**: Essential Topology Operations
