# SPEC-003: Essential Topology Operations

## Overview
Basic topology management operations for RabbitMQ queues, exchanges, and bindings with essential CRUD functionality.

## Components

### Queue Management
- **List Queues**: Retrieve all queues with basic statistics
- **Create Queue**: Create new queues with standard options
- **Delete Queue**: Remove queues (with safety checks)
- **Queue Statistics**: Basic queue metrics (depth, consumers, etc.)

### Exchange Management
- **List Exchanges**: Retrieve all exchanges with type information
- **Create Exchange**: Create exchanges with standard types (direct, topic, fanout, headers)
- **Delete Exchange**: Remove exchanges (with safety checks)
- **Exchange Statistics**: Basic exchange metrics

### Binding Management
- **List Bindings**: Retrieve all bindings between queues and exchanges
- **Create Binding**: Bind queues to exchanges with routing keys
- **Delete Binding**: Remove bindings between queues and exchanges

### Internal Operations (Auto-generated from OpenAPI)
- **Queue Operations** (derived from OpenAPI `paths` with tag "Queues"):
  - `queues.list`: GET /api/queues - List all queues with statistics
  - `queues.get`: GET /api/queues/{vhost}/{name} - Get specific queue details
  - `queues.create`: PUT /api/queues/{vhost}/{name} - Create new queue
  - `queues.delete`: DELETE /api/queues/{vhost}/{name} - Delete queue
- **Exchange Operations** (derived from OpenAPI `paths` with tag "Exchanges"):
  - `exchanges.list`: GET /api/exchanges - List all exchanges with types
  - `exchanges.get`: GET /api/exchanges/{vhost}/{name} - Get specific exchange
  - `exchanges.create`: PUT /api/exchanges/{vhost}/{name} - Create new exchange
  - `exchanges.delete`: DELETE /api/exchanges/{vhost}/{name} - Delete exchange
- **Binding Operations** (derived from OpenAPI `paths` with tag "Bindings"):
  - `bindings.list`: GET /api/bindings - List all bindings
  - `bindings.create-queue`: POST /api/bindings/{vhost}/e/{exchange}/q/{queue} - Bind queue to exchange
  - `bindings.delete-queue`: DELETE /api/bindings/{vhost}/e/{exchange}/q/{queue}/{props} - Delete binding

**Note**: All operation IDs, parameters, and schemas are automatically generated from `.specify/memory/rabbitmq-http-api-openapi.yaml`

## Technical Requirements

### Queue Operations
- Support standard queue options (durable, exclusive, auto-delete)
- Queue statistics: message count, consumer count, memory usage
- Safety checks before deletion (empty queue requirement)

### Exchange Operations
- Support standard exchange types: direct, topic, fanout, headers
- Exchange statistics: binding count, message rates
- Safety checks before deletion (no bindings requirement)

### Binding Operations
- Support routing key patterns
- Binding statistics and metadata
- Validation of queue and exchange existence

### Performance
- List operations complete within 2 seconds
- Create/delete operations complete within 1 second
- Support for up to 1000 queues/exchanges

## Acceptance Criteria

### Functional Requirements
- [ ] Successfully lists all queues with basic statistics
- [ ] Successfully lists all exchanges with type information
- [ ] Successfully lists all bindings with routing keys
- [ ] Creates queues with standard options
- [ ] Creates exchanges with standard types
- [ ] Creates bindings between queues and exchanges
- [ ] Deletes queues and exchanges safely
- [ ] Validates queue/exchange existence before operations

### Performance Requirements
- [ ] List operations complete within 2 seconds
- [ ] Create/delete operations complete within 1 second
- [ ] Handles up to 1000 queues/exchanges efficiently

### Safety Requirements
- [ ] Prevents deletion of non-empty queues
- [ ] Prevents deletion of exchanges with bindings
- [ ] Validates parameters before operations

## Dependencies
- pika for RabbitMQ operations
- RabbitMQ Management API (optional for statistics)

## Implementation Notes
- **OpenAPI-Driven**: All operations, schemas, and parameters derived from `.specify/memory/rabbitmq-http-api-openapi.yaml`
- Use RabbitMQ Management API (HTTP) for topology operations
- **Semantic Discovery**: All topology operations accessed via `search-ids` → `get-id` → `call-id` pattern
- Implement safety checks for destructive operations
- Log all topology changes for audit purposes using structlog
- Support both vhost-specific and global operations
- Handle RabbitMQ-specific error codes from OpenAPI responses section
- **Schema Validation**: Use pre-generated Pydantic models for request/response validation
- **Pagination**: Check OpenAPI specification to determine if operation supports pagination
- **Build-Time Generation**: Operation registry and schemas generated when OpenAPI changes
