# SPEC-001: Base MCP Architecture

## Overview
Implementation of the fundamental MCP server architecture with the essential 3-tool semantic discovery pattern.

## Components

### Core MCP Server
- MCP server with JSON-RPC 2.0 compliance
- Standardized tool interface with JSON input/output
- Protocol compliance validation
- Error handling with MCP error codes

### Semantic Discovery Tools (Public MCP Tools)
- **`search-ids`**: Semantic search across RabbitMQ operations
- **`get-id`**: Retrieve detailed schema and documentation for specific operations
- **`call-id`**: Execute RabbitMQ operations with dynamic parameter validation

### Internal Operations Structure
- **Auto-generated from OpenAPI**: All internal operation IDs derived from OpenAPI paths and tags
- **Operation ID Format**: `{tag}.{operation-name}` (e.g., `queues.list`, `exchanges.create`)
- **Pre-generated Registry**: Operation registry generated at build-time and committed to repository
- Namespace-based organization by OpenAPI tags
- Dynamic schema validation using jsonschema library
- Runtime parameter validation with <10ms overhead
- Operation metadata extracted from OpenAPI specification

### Schema Management
- **OpenAPI Source of Truth**: All schemas derived from `.specify/memory/rabbitmq-http-api-openapi.yaml`
- **Build-Time Generation**: Pydantic models auto-generated when OpenAPI changes (NOT at runtime)
- **Pre-generated Artifacts**: Schemas committed to repository in `src/schemas/` directory
- Cached validated schemas with 5-minute TTL for runtime validation
- Dynamic validation for all operation calls using pre-generated schemas
- Input/output schema documentation extracted from OpenAPI specification

## Technical Requirements

### Performance
- Latency < 200ms for basic operations
- Validation overhead < 10ms per operation call
- Memory usage < 1GB per instance

### Compliance
- Strict adherence to MCP protocol specification
- JSON-RPC 2.0 support mandatory
- All tools follow MCP tool interface standards
- Protocol compliance verification in tests

## Acceptance Criteria

### Functional Requirements
- [ ] Server responds to basic MCP requests
- [ ] All 3 public tools are registered and functional
- [ ] Dynamic schema validation works for all operations
- [ ] Error handling returns proper MCP error codes
- [ ] Internal operations are properly namespaced

### Performance Requirements
- [ ] Response time < 200ms for simple operations
- [ ] Validation overhead < 10ms per operation
- [ ] Memory usage stays under 1GB

### Compliance Requirements
- [ ] Passes MCP protocol compliance tests
- [ ] JSON-RPC 2.0 implementation verified
- [ ] All tools follow standardized interface

## Dependencies
- Python 3.12+
- MCP Python SDK (https://github.com/modelcontextprotocol/python-sdk)
- pydantic for schema validation
- jsonschema for runtime validation
- pyyaml for OpenAPI specification parsing
- datamodel-code-generator for Pydantic model generation from OpenAPI

## Implementation Notes
- **CRITICAL**: Only 3 tools are registered as public MCP tools (`search-ids`, `get-id`, `call-id`)
- All other RabbitMQ functionality accessed through semantic discovery
- Direct tool registration for specific operations is **PROHIBITED**
- Console client must support semantic discovery workflow
- **Build-Time Code Generation**: Run `python scripts/generate_schemas.py` when OpenAPI changes
- **Pre-generated Artifacts**: Schemas, operation registry, and vector indices must be committed to repository
- **OpenAPI as Source of Truth**: All operations, schemas, and documentation derived from `.specify/memory/rabbitmq-http-api-openapi.yaml`
- **AMQP Operations**: Message publish/consume/ack operations NOT in OpenAPI, must be implemented separately with manual schemas
