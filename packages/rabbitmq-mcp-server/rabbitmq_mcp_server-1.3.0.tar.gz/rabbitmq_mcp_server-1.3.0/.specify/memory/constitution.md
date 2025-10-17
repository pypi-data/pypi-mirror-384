# RabbitMQ MCP Server Constitution

## Core Principles

### I. MCP Protocol Compliance
Every MCP server MUST strictly adhere to the Model Context Protocol specification; Implementations MUST be compatible with official MCP specification; Mandatory JSON-RPC 2.0 support; Schema validation is mandatory; All tools MUST follow MCP tool interface standards

### Vector Database Requirements (Pre-generated)
- **Storage**: File-based embedded vector database (sqlite-vec recommended, ChromaDB local file mode as alternative)
- **Distribution**: Vector database files MUST be packaged with the application - no external database installations required
- **File Location**: Pre-built vector database files stored in application's data directory (e.g., `./data/vectors/rabbitmq.db`)
- **Generation Trigger**: Embeddings regenerated ONLY when:
  1. OpenAPI specification file is modified
  2. Generation script is manually executed (`python scripts/generate_embeddings.py`)
  3. Initial repository setup/clone
- **Embeddings**: Pre-computed embeddings for all RabbitMQ operations and documentation, generated from OpenAPI and committed to repository
- **Search Performance**: Sub-100ms semantic search response time per page from local file-based storage using pre-built indices
- **Version Control**: Vector database files MUST be committed to version control alongside other generated artifacts
- **Content**: Index operation descriptions, parameter names, use cases, and troubleshooting scenarios from OpenAPI specification
- **Pagination Support**: Vector search MUST support efficient pagination with relevance score preservation across pages using file-based indices
- **Performance Optimization**: Two-tier architecture with lightweight search index for discovery and rich content storage for detailed operation information, all stored in local database files
- **Portability**: Database files must be portable across platforms and require no additional dependencies beyond the application runtime

### II. Tool-First Architecture
Each functionality MUST be exposed as an MCP tool; Tools MUST be self-contained and independent; Standardized interface: JSON input → processing → JSON output; Mandatory documentation of parameters and returns; Tools MUST support both synchronous and asynchronous operations

### III. Test-First Development (NON-NEGOTIABLE)
TDD is mandatory: Tests written → User approved → Tests fail → Implementation; Red-Green-Refactor cycle strictly applied; **Minimum 80% coverage for all tools** (critical tools: connection management, message publishing/consuming, queue operations, authentication, error handling); Integration tests MUST use real RabbitMQ instances; Contract tests MUST validate MCP protocol compliance

### IV. Integration Testing Requirements
Areas requiring integration tests: New MCP tools, Protocol changes, RabbitMQ communication, Shared schemas, JSON-RPC contract validation, Console client functionality, Multi-broker connections

### V. Observability & Error Handling
**Structured logging mandatory with configurable output destinations**; Standardized error handling with MCP error codes; Performance metrics for all tools; MCP request tracing; RabbitMQ connection monitoring; Console client operation logging
**Clarification:** Both MCP server and console client MUST implement structured logging for all operations, errors, and security events. Logging requirements apply equally to client and server components.

#### Logging Configuration & Output Management
- **Default Output**: File-based logging (most commonly used for enterprise message queue applications)
- **File Location**: `./logs/` directory with structured naming (`rabbitmq-mcp-{date}.log`)
- **Configurable Outputs**: Elasticsearch (most popular for log aggregation), Splunk, RabbitMQ native logging, Fluentd, CloudWatch, Prometheus/Grafana, or custom log shippers
- **Log Format**: Structured JSON logs using structlog (industry standard for Python applications)
- **Log Levels**: error, warn, info, debug (standard enterprise logging levels)
- **Automatic Sensitive Data Sanitization**: Connection credentials, message content (when configured), authentication tokens redacted before logging
- **Message Correlation**: UUID-based correlation IDs for tracing messages across queues and consumers

#### Log Rotation & Retention Policies
- **File Rotation**: Daily rotation by default (most common enterprise practice for message queue systems)
- **Size-Based Rotation**: Maximum 100MB per file (prevents large files from impacting RabbitMQ performance)
- **Retention Policy**: 30 days for info/debug logs, 90 days for error/warn logs, 1 year for audit logs (message queue compliance-friendly defaults)
- **Compression**: Automatic gzip compression for rotated logs (saves storage space)
- **Cleanup**: Automatic deletion of logs exceeding retention periods
- **Archive Options**: Optional archival to S3, Azure Blob, or other cloud storage for long-term retention

#### Enterprise Log Management Integration
- **ELK Stack**: Native Elasticsearch, Logstash, Kibana integration (most popular open-source option for RabbitMQ)
- **RabbitMQ Native**: Integration with RabbitMQ's built-in logging and monitoring (most commonly used for RabbitMQ-specific insights)
- **Splunk**: Enterprise log management integration (most popular commercial option)
- **Cloud Native**: AWS CloudWatch, Azure Monitor, Google Cloud Logging support
- **Prometheus/Grafana**: Metrics and logging integration (most popular for RabbitMQ monitoring)
- **AMQP Logging**: Optional structured logging via AMQP to dedicated logging queues

### VI. Versioning & Backward Compatibility
Semantic versioning MAJOR.MINOR.PATCH; Breaking changes require documented migration; Support for multiple MCP protocol versions; Gradual deprecation of features; Console client version compatibility

### VII. Simplicity & Performance
YAGNI principles applied; Maximum 15 tools per server (increased for RabbitMQ operations); Latency < 200ms for simple operations; Efficient RabbitMQ resource usage; Console client must be lightweight and responsive

### VIII. Documentation Requirements
All documentation must be written in English; MCP servers MUST include comprehensive documentation with the following mandatory documents: README.md, docs/API.md, docs/ARCHITECTURE.md, docs/CONTRIBUTING.md, docs/DEPLOYMENT.md, docs/EXAMPLES.md; API documentation with TypeScript interfaces; Console help text for all commands; Architecture documentation with diagrams; Interactive help system within the console; Command reference with examples and usage patterns; MCP tool documentation must include input/output schemas and usage examples; README.md MUST include examples showing how to run CLI with uvx; EXAMPLES.md MUST include code samples for debugging in dev environment, command-line usage examples (bash, PowerShell, etc.), and MCP client configuration examples (Cursor, VS Code, etc.); Documentation MUST be kept current with code changes; All examples MUST be tested and functional

**Every MCP server MUST include a built-in console client.**

## Pagination Requirements

**CRITICAL CLARIFICATION**: Pagination will be available ONLY for RabbitMQ Management API endpoints that have pagination parameters. Not all RabbitMQ operations support pagination natively, and the MCP server MUST respect the underlying API capabilities.

All list operations that correspond to RabbitMQ Management API endpoints with pagination support MUST implement pagination to ensure constitutional compliance and optimal performance.

### Mandatory Pagination Schema

```typescript
interface PaginationParams {
  page?: number;        // 1-based page number (default: 1)
  pageSize?: number;    // Items per page (default: 50, max: 200)
  cursor?: string;      // Cursor-based pagination token (optional)
}

interface PaginatedResponse<T> {
  items: T[];
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
    hasNextPage: boolean;
    hasPreviousPage: boolean;
    nextCursor?: string;
    previousCursor?: string;
  };
}
```

### Implementation Requirements

1. **Default Limits**: List operations that support pagination default to maximum 50 items per page
2. **Maximum Limits**: No single request may return more than 200 items (only applies to pagination-enabled endpoints)
3. **Conditional Pagination**: Pagination is implemented ONLY when the underlying RabbitMQ Management API endpoint supports it
4. **Performance Compliance**: Paginated responses must maintain <100ms response time per page
5. **Cursor Support**: For real-time data streams, implement cursor-based pagination alongside page-based (when supported by RabbitMQ API)
6. **RabbitMQ Integration**: Leverage RabbitMQ Management API pagination parameters when available; respect API limitations when pagination is not supported

### Pagination-Enabled Operations

**Note**: The following operations support pagination ONLY if the corresponding RabbitMQ Management API endpoint provides pagination parameters:

- Queue listings with message counts and consumer information (when RabbitMQ API supports pagination)
- Exchange listings with binding details (when RabbitMQ API supports pagination)
- Binding enumerations with routing key patterns (when RabbitMQ API supports pagination)
- Connection listings with client information (when RabbitMQ API supports pagination)
- Channel listings with consumer details (when RabbitMQ API supports pagination)
- Node listings with cluster status (when RabbitMQ API supports pagination)
- Message browsing with content preview (when RabbitMQ API supports pagination)
- Performance metrics with time-series data (when RabbitMQ API supports pagination)

**Implementation Note**: Developers MUST check the official RabbitMQ Management API documentation to determine which specific endpoints support pagination parameters before implementing pagination features.

## API Source of Truth

### OpenAPI Specification Reference
**All RabbitMQ operations, schemas, entities, and services MUST be derived from the canonical OpenAPI specification located at:**
```
.specify/memory/rabbitmq-http-api-openapi.yaml
```

This OpenAPI YAML file serves as the **single source of truth** for:
- **Paths/Endpoints**: All RabbitMQ Management API endpoints (GET, POST, PUT, DELETE operations)
- **Components/Schemas**: Data models, request/response structures, error formats
- **Parameters**: Query parameters, path parameters, request bodies
- **Responses**: Success and error response structures
- **Tags**: Operation categorization (Queues, Exchanges, Bindings, Users, etc.)
- **Security Schemes**: Authentication and authorization mechanisms

### Operation Discovery and Execution
**CRITICAL**: All internal operation IDs, schemas, and implementations MUST be automatically generated from the OpenAPI specification. Manual endpoint lists are **PROHIBITED**.

### Code Generation Requirements (Build-Time)
**CRITICAL**: All code generation MUST occur during build/pre-pack time, NOT during runtime startup.

**Code generation triggers:**
1. **OpenAPI YAML file changes**: Generation script MUST be executed automatically when `.specify/memory/rabbitmq-http-api-openapi.yaml` is modified
2. **Manual script execution**: Developers can manually run generation scripts (e.g., `python scripts/generate_schemas.py`) when needed
3. **Initial build**: Generation MUST run during first-time project setup/build

**Generated artifacts:**
- **Schema Validation**: Pydantic models MUST be auto-generated from OpenAPI `components.schemas` 
- **Operation Routing**: Internal operation registry MUST be generated from OpenAPI `paths`
- **Parameter Validation**: Request/response validation schemas MUST be pre-compiled from OpenAPI specification
- **Documentation**: Operation descriptions and examples MUST be extracted from OpenAPI
- **Pagination Detection**: Endpoint pagination capabilities MUST be detected from OpenAPI
- **Vector Embeddings**: Semantic search embeddings MUST be pre-computed from OpenAPI descriptions

### Implementation Strategy
1. **Code Generation Phase** (triggered by YAML changes or manual execution):
   - **Trigger**: Runs when `.specify/memory/rabbitmq-http-api-openapi.yaml` is modified OR when manually invoked
   - **Process**:
     - Parse OpenAPI YAML specification
     - Generate Pydantic models from OpenAPI `components.schemas`
     - Generate operation registry mapping operation IDs to OpenAPI paths
     - Generate vector database indices with operation descriptions and embeddings
     - Generate TypeScript interface definitions for documentation
   - **Output**: Generated artifacts committed to repository (schemas/, operation_registry.json, vector_db/indices/)
   - **Automation**: Use file watchers or pre-commit hooks to detect OpenAPI YAML changes

2. **Build/Package Phase** (one-time during deployment preparation):
   - Verify all generated artifacts are present and up-to-date
   - Validate generated schemas against OpenAPI specification
   - Package application with pre-generated artifacts
   - NO code generation occurs during this phase (only validation)

3. **Server Initialization** (runtime startup):
   - Load pre-generated Pydantic models from committed files
   - Load pre-generated operation registry from committed files
   - Load pre-computed vector database indices from committed files
   - Initialize HTTP client for RabbitMQ Management API
   - Initialize AMQP client for protocol operations
   - NO code generation occurs at runtime

4. **Request Processing** (runtime):
   - Validate requests against pre-generated schemas
   - Execute operations by mapping to RabbitMQ Management API endpoints

### Synchronization and Updates
**Code generation triggers ONLY on:**
1. **OpenAPI YAML file modifications**: File watcher or pre-commit hook detects changes to `.specify/memory/rabbitmq-http-api-openapi.yaml`
2. **Manual script execution**: Developer runs `python scripts/generate_schemas.py` (or equivalent generation scripts)
3. **Fresh repository clone**: Initial setup script runs generation for first-time setup

**When triggered, regenerate:**
- Pydantic models from updated OpenAPI schemas
- Operation registry from updated OpenAPI paths
- Vector database indices with updated descriptions
- Validation schemas from updated request/response definitions

**Important notes:**
- Generated artifacts MUST be committed to version control
- CI/CD pipeline MUST verify generated artifacts are up-to-date with OpenAPI specification
- Schema changes MUST be validated against existing implementations
- Deprecated endpoints in OpenAPI MUST be marked as deprecated in operation registry
- Version changes in OpenAPI MUST be reflected in MCP server versioning

### AMQP Protocol Extensions
**IMPORTANT**: The OpenAPI specification covers only the RabbitMQ Management HTTP API. AMQP protocol operations (publish, consume, ack, nack, etc.) are NOT included in the OpenAPI specification and MUST be implemented separately.

**AMQP Operations (NOT in OpenAPI):**
- Message publishing via AMQP protocol
- Message consumption and streaming
- Message acknowledgment (ack/nack/reject)
- Queue subscriptions with consumer callbacks
- Connection management via AMQP (separate from HTTP API connections)
- Channel management via AMQP protocol
- Transaction support (tx.select, tx.commit, tx.rollback)
- Publisher confirms and consumer acknowledgments

**Implementation Strategy:**
- AMQP operations MUST be exposed as separate internal operation IDs (e.g., `amqp.publish`, `amqp.consume`, `amqp.ack`)
- AMQP operation schemas MUST be manually defined using Pydantic models (not auto-generated)
- AMQP operations MUST be indexed in the vector database alongside HTTP API operations
- Use `pika` library for AMQP protocol implementation
- AMQP operations MUST be accessible through the same 3-tool pattern (`search-ids`, `get-id`, `call-id`)

## Performance Monitoring

🔑 **Core Capabilities**

_All capabilities described in this section MUST be implemented in Python._

>A RabbitMQ MCP server should not just be a thin AMQP bridge — it should handle publish, consume, ack/nack, retry/delay, DLQ management, config import/export, monitoring, and logging, while giving the MCP client control over ack/nack decisions.

**Connection Management**
- Connect to RabbitMQ via AMQP (optionally TLS & auth).
- Support multiple vhosts.

**Queue & Exchange Management**
- Create/delete/list exchanges, queues, bindings.
- Import/export topology (definitions.json) for setup.
- Safe merge vs. destructive overwrite.

**Message Publishing**
- Publish messages (with headers, properties, routing keys).
- Support JSON, text, binary payloads.
- Optionally mark persistent vs. transient.

**Message Consumption (Streaming to MCP Client)**
- Subscribe to queues and stream messages to MCP client.
- The MCP client can:
  - ack → confirm successful processing.
  - nack → trigger retry/delay/DLX logic.
  - reject → send to DLQ immediately.

🔄 **Retry & Error Handling**

**Retry Pattern with DLX + TTL**
- Built-in support for delayed retries (e.g., 5s → 15s → 60s → DLQ).
- Configurable retry attempts and exponential backoff.

**Dynamic Retry Control**
- Let the MCP client decide per message:
  - retry immediately
  - retry after N seconds
  - send to DLQ now

📊 **Monitoring & Introspection**

**Message Metadata & Stats**
- Inspect queue depth, consumers, unacked count.
- Show retry history (via headers like x-retry-count).

**Dead Letter Queue (DLQ) Visibility**
- Ability to list, requeue, purge, or replay DLQ messages.

🔧 **Operational Features**

**Import/Export of Config**
- Use RabbitMQ's definitions JSON format.
- Support safe merges (preserve users/vhosts).
- Option to "clear before import" for full reset.

**Management API Bridge**
- Proxy RabbitMQ Management API to MCP client via semantic discovery pattern.
- All Management API endpoints MUST be accessible through `call-id` tool.
- Expose metrics (queues, connections, channels) as defined in OpenAPI specification.

**Audit & Logging**
- Log all published/consumed messages (optionally).
- Track message paths (main → retry → DLQ).

🛡️ **Advanced / Nice-to-Have**

**Security**
- Per-user/vhost isolation in MCP.
- TLS and RabbitMQ credentials securely stored.

**Message Shaping**
- Optional transformations (e.g., decode JSON, unwrap Avro).
- Attach retry metadata in headers automatically.

**Testing & Simulation**
- Inject test messages into queues.
- Simulate consumer failures to test retry/DLX flows.

---

### Capability Map

The RabbitMQ MCP server MUST expose operations derived from `.specify/memory/rabbitmq-http-api-openapi.yaml`. All operations are accessed through the semantic discovery pattern (`search-ids`, `get-id`, `call-id`).

**Capabilities are automatically discovered from OpenAPI tags:**
- **Cluster**: Cluster management operations
- **Nodes**: Node monitoring and management
- **Connections**: Connection management and monitoring
- **Channels**: Channel operations and statistics
- **Exchanges**: Exchange CRUD and management
- **Queues**: Queue CRUD and management
- **Bindings**: Binding creation and management
- **Virtual Hosts**: VHost operations
- **Users**: User management and permissions
- **Permissions**: Permission management
- **Parameters**: Runtime parameter management
- **Policies**: Policy management
- **Health**: Health checks and monitoring
- **Definitions**: Import/export operations
- **Feature Flags**: Feature flag management
- **Streams**: Stream operations

#### ✅ Example Flow
MCP client searches for operations:
```python
# Search for queue-related operations
await mcp_client.call_tool("search-ids", {
    "query": "list queues with message counts"
})
# Returns: ["queues.list", "queues.get-stats", ...]

# Get operation schema
await mcp_client.call_tool("get-id", {
    "endpoint_id": "queues.list"
})
# Returns full schema with parameters and response format

# Execute operation
await mcp_client.call_tool("call-id", {
    "endpoint_id": "queues.list",
    "params": {"vhost": "/", "page": 1, "pageSize": 50}
})
```

All operation IDs, schemas, and behaviors are automatically derived from the OpenAPI specification.

## Semantic Discovery & Tool Architecture

### Core Tool Pattern
The RabbitMQ MCP server MUST implement a 3-tool semantic discovery pattern to efficiently manage hundreds of RabbitMQ operations:

**CRITICAL ARCHITECTURE REQUIREMENT**: Only these 3 tools are registered as public MCP tools. All other RabbitMQ functionality is accessed indirectly through these tools.

#### 🔍 search-ids(query: string, pagination?: PaginationParams) → PaginatedResponse[EndpointSummary]
- **Purpose**: Semantic search across RabbitMQ operations and documentation
- **Implementation**: Vector database (ChromaDB local mode or sqlite-vec) for embedding search
- **Input**: Natural language query describing desired RabbitMQ functionality + optional pagination parameters
- **Output**: Paginated list of operation IDs with short descriptions and parameter hints
- **Performance**: Response time < 100ms for search queries per page
- **Pagination**: Mandatory for all list operations to prevent performance degradation (default: 10 items per page, max: 25)
- **Vector Database**: Must support embedding storage and similarity search for RabbitMQ operations with efficient pagination

#### 📋 get-id(endpoint_id: string) → EndpointDetails
- **Purpose**: Retrieve detailed schema and documentation for specific RabbitMQ operation
- **Input**: Operation ID from search-ids results
- **Output**: Complete operation details extracted from OpenAPI specification:
  - Operation description from OpenAPI `paths[*][*].description`
  - Summary from OpenAPI `paths[*][*].summary`
  - Input schema from OpenAPI `paths[*][*].requestBody.content.application/json.schema`
  - Output schema from OpenAPI `paths[*][*].responses[200].content.application/json.schema`
  - Required vs optional parameters from OpenAPI `paths[*][*].parameters[*].required`
  - Usage examples from OpenAPI `paths[*][*].requestBody.content.application/json.examples`
  - Error scenarios from OpenAPI `paths[*][*].responses[400|404|500]`
- **Privacy**: Internal HTTP method and path details MUST remain hidden from clients
- **Validation**: Schema details MUST be auto-generated from `.specify/memory/rabbitmq-http-api-openapi.yaml`

#### ⚡ call-id(endpoint_id: string, params: dict, pagination?: PaginationParams) → dict | PaginatedResponse
- **Purpose**: Execute RabbitMQ operation with dynamic parameter validation
- **Input Schema**: Generic schema with endpoint_id (string), params (Record<string, any>), and optional pagination
- **Runtime Validation**: Dynamic schema validation using JSON Schema library against operation-specific requirements
- **Error Handling**: Detailed error messages for validation failures and RabbitMQ operation errors
- **Performance**: Validation overhead < 10ms per operation call
- **Pagination**: For operations returning large datasets (queue lists, message lists, connection stats), automatically apply pagination to maintain constitutional performance requirements

### Vector Database Requirements
- **Storage**: File-based embedded vector database optimized for Python (ChromaDB local file mode recommended as the best Python option)
- **Generation Trigger**: Embeddings regenerated ONLY when:
  1. `.specify/memory/rabbitmq-http-api-openapi.yaml` is modified
  2. `python scripts/generate_embeddings.py` is manually executed
  3. Initial repository setup script runs
- **Embeddings**: Pre-computed embeddings for all RabbitMQ operations derived from OpenAPI specification
- **Search Performance**: Sub-100ms semantic search response time per page using pre-built indices
- **Indexing Source**: Index content extracted from `.specify/memory/rabbitmq-http-api-openapi.yaml`:
  - Operation descriptions from `paths[*][*].description`
  - Operation summaries from `paths[*][*].summary`
  - Parameter names and descriptions from `paths[*][*].parameters[*]`
  - Tag descriptions from `tags[*].description`
  - Schema descriptions from `components.schemas[*].description`
- **Version Control**: Pre-built vector database indices MUST be committed to repository
- **CI/CD Validation**: Pipeline verifies indices are up-to-date with OpenAPI specification (does NOT regenerate)
- **Content**: Index operation descriptions, parameter names, use cases, and troubleshooting scenarios from OpenAPI
- **Pagination Support**: Vector search MUST support efficient pagination with relevance score preservation across pages
- **Performance Optimization**: Two-tier architecture with lightweight search index for discovery and rich content storage for detailed operation information

### Schema Management
- **Source of Truth**: All schemas MUST be derived from `.specify/memory/rabbitmq-http-api-openapi.yaml` (components.schemas section)
- **Generation Trigger**: Schemas regenerated ONLY when:
  1. `.specify/memory/rabbitmq-http-api-openapi.yaml` is modified
  2. `python scripts/generate_schemas.py` is manually executed
  3. Initial repository setup script runs
- **Schema Generation**: Auto-generate Pydantic models from OpenAPI `components.schemas`
- **Operation Schemas**: Extract and compile request/response schemas from OpenAPI `paths[*][*].requestBody` and `paths[*][*].responses`
- **Version Control**: Generated Pydantic models MUST be committed to repository (in `schemas/` directory)
- **Runtime Validation**: Use pre-generated schemas for runtime validation with jsonschema library
- **Compatibility**: Maintain compatibility between OpenAPI-style schemas and MCP tool definitions
- **Caching**: Cache validated schemas with 5-minute TTL for performance optimization
- **CI/CD Validation**: Pipeline verifies schemas are up-to-date with OpenAPI specification (does NOT regenerate)

### Integration with Existing Capabilities
- **ALL** RabbitMQ capabilities (connection management, queue operations, message handling, etc.) MUST be accessible **EXCLUSIVELY** through the 3-tool pattern
- **NO** direct tool registration for specific operations (connection, publish, subscribe, etc.)
- Only `search-ids`, `get-id`, and `call-id` are registered as public MCP tools
- Legacy direct tool access is **PROHIBITED** - all functionality goes through semantic discovery
- Console client MUST support both direct commands and semantic discovery workflow
- Documentation MUST include examples of semantic discovery for common RabbitMQ tasks

### MCP Tool Naming Conventions
All MCP tools MUST follow standardized naming patterns for consistency and cross-platform compatibility:

#### Universal Naming Rules
- **Primary Pattern**: `kebab-case` for maximum cross-platform compatibility
- **Python Alternative**: `snake_case` acceptable for Python-native tools but `kebab-case` preferred for cross-platform consistency
- **Namespace Pattern**: `namespace.action` for grouping related tools (e.g., `rabbitmq.publish-message`, `rabbitmq.subscribe-queue`)
- **Avoid**: PascalCase, camelCase, SCREAMING_CASE, or overly verbose names
- **Language Neutral**: Tool names must work regardless of server implementation language

#### MCP Tool Names vs Internal Operation IDs

**CRITICAL CLARIFICATION**: Only 3 tools are registered as public MCP tools. The namespaced examples below are **internal operation IDs** accessed through the `call-id` tool, NOT separate MCP tools.

```python
# ✅ PUBLIC MCP TOOLS (ONLY THESE 3 ARE REGISTERED)
"search-ids"              # Find RabbitMQ operations by natural language query
"get-id"                  # Get detailed operation schema
"call-id"                 # Execute operation with validation

# ✅ INTERNAL OPERATION IDs (auto-generated from OpenAPI paths and tags)
# These are examples - actual operation IDs are derived from OpenAPI specification:
# - Format: "{tag}.{operation-name}" where tag comes from OpenAPI tags
# - Operation name derived from path and HTTP method
# - Example generation logic:
#   GET /api/queues → "queues.list"
#   PUT /api/queues/{vhost}/{name} → "queues.create-or-update"
#   DELETE /api/exchanges/{vhost}/{name} → "exchanges.delete"
#   POST /api/bindings/{vhost}/e/{exchange}/q/{queue} → "bindings.create-exchange-queue"

# Example operation IDs (actual list generated from OpenAPI at runtime):
"cluster.get-name"            # GET /api/cluster-name
"nodes.list"                  # GET /api/nodes
"connections.list"            # GET /api/connections
"exchanges.list"              # GET /api/exchanges
"exchanges.create"            # PUT /api/exchanges/{vhost}/{name}
"queues.list"                 # GET /api/queues
"queues.get"                  # GET /api/queues/{vhost}/{name}
"queues.create"               # PUT /api/queues/{vhost}/{name}
"bindings.list"               # GET /api/bindings
"users.list"                  # GET /api/users
"definitions.export"          # GET /api/definitions
"definitions.import"          # POST /api/definitions

# ❌ Avoid These Patterns (for operation IDs)
"RabbitMQConnect"         # PascalCase breaks convention
"publishMessage"          # camelCase not MCP standard
"list_all_queues"         # snake_case/verbose
"QUEUE_OPERATIONS"        # SCREAMING_CASE not readable
```

**Usage Example**:
```python
# Client calls the call-id MCP tool with an internal operation ID
# Operation ID is auto-generated from OpenAPI: GET /api/exchanges/{vhost}/{name}/publish
await mcp_client.call_tool("call-id", {
    "endpoint_id": "exchanges.publish",  # Internal operation ID from OpenAPI
    "params": {
        "vhost": "/",
        "name": "my_exchange",
        "routing_key": "test",
        "payload": "Hello World",
        "payload_encoding": "string",
        "properties": {"content_type": "text/plain"}
    }
})

# All operation IDs, parameter names, and validation rules
# are automatically derived from the OpenAPI specification
```

#### File Organization Standards
File structure for OpenAPI-driven architecture:
```
tools/
├── search_ids.py            # Contains search-ids tool (PUBLIC MCP TOOL)
├── get_id.py                # Contains get-id tool (PUBLIC MCP TOOL)
├── call_id.py               # Contains call-id tool (PUBLIC MCP TOOL)
├── openapi/
│   ├── parser.py            # OpenAPI YAML parser and loader
│   ├── schema_generator.py  # Auto-generate Pydantic models from OpenAPI schemas
│   ├── operation_registry.py # Map operation IDs to OpenAPI paths
│   └── validator.py         # Runtime validation against OpenAPI schemas
├── operations/              # Internal operation executors (organized by OpenAPI tags)
│   ├── executor.py          # Base operation executor with HTTP client
│   ├── cluster.py           # Operations tagged as "Cluster" in OpenAPI
│   ├── nodes.py             # Operations tagged as "Nodes" in OpenAPI
│   ├── connections.py       # Operations tagged as "Connections" in OpenAPI
│   ├── exchanges.py         # Operations tagged as "Exchanges" in OpenAPI
│   ├── queues.py            # Operations tagged as "Queues" in OpenAPI
│   ├── bindings.py          # Operations tagged as "Bindings" in OpenAPI
│   ├── users.py             # Operations tagged as "Users" in OpenAPI
│   ├── permissions.py       # Operations tagged as "Permissions" in OpenAPI
│   ├── definitions.py       # Operations tagged as "Definitions" in OpenAPI
│   └── health.py            # Operations tagged as "Health" in OpenAPI
├── vector_db/
│   ├── indexer.py           # Index operations from OpenAPI for semantic search
│   ├── embeddings.py        # Generate embeddings from OpenAPI descriptions
│   └── search.py            # Vector similarity search implementation
└── schemas/                 # Auto-generated Pydantic models (DO NOT EDIT MANUALLY)
    ├── __init__.py
    ├── queue.py             # Generated from OpenAPI components.schemas.Queue
    ├── exchange.py          # Generated from OpenAPI components.schemas.Exchange
    ├── binding.py           # Generated from OpenAPI components.schemas.Binding
    └── ...                  # Other schemas from OpenAPI components.schemas
```

**Key Points:**
- Operation implementations are organized by OpenAPI tags for better maintainability
- All schemas in `schemas/` directory are auto-generated from OpenAPI specification
- Manual edits to generated schemas are PROHIBITED
- Re-run schema generation script when OpenAPI specification is updated

#### Tool Registration Requirements
- **ONLY** the semantic discovery pattern tools MUST be registered as public MCP tools:
  - `search-ids` (semantic search for RabbitMQ operations)
  - `get-id` (get detailed operation schema)
  - `call-id` (execute operation with validation)
- **ALL OTHER** RabbitMQ functionality (connection management, topology, messaging, monitoring, etc.) MUST be accessible **INDIRECTLY** through the 3-tool pattern
- Direct tool registration for specific operations (e.g., `rabbitmq.connect`, `topology.create-queue`, `message.publish`) is **PROHIBITED**
- Tool descriptions MUST be concise but descriptive
- Tool schemas MUST use Pydantic validation with RabbitMQ-specific types
- RabbitMQ operation schemas MUST include connection context and vhost metadata

## Security & Performance Requirements

### Security Standards
- **Authentication Priority**: Username/Password (preferred) → X.509 Client Certificates → LDAP → OAuth/JWT (if supported)
- **Mandatory authentication for RabbitMQ connections**: Input validation for all tools; Sensitive data sanitization in logs; Rate limiting for high-volume tools; TLS encryption for external connections; Console client authentication; Secure credential management; MCP tool access control
**Clarification:** All sensitive data (e.g., credentials, personal information, secrets) MUST be redacted from logs before storage or transmission. Redaction logic MUST be tested and reviewed in code reviews.

### Performance Standards
Maximum latency of 200ms for basic operations; Minimum throughput of 500 requests/minute; Memory usage < 1GB per instance; Optimized RabbitMQ connection pooling; Caching for frequent operations; Console client response time < 100ms; Efficient message serialization/deserialization; **Semantic Search**: Sub-100ms response time for search-ids queries, <10ms validation overhead for call-id operations; **Vector Database**: <50MB memory footprint for embedded vector storage; **Circuit Breaker**: Threshold (default: 5 failures), timeout (default: 60s), reset timeout (default: 30s); **Retry Logic**: Attempts (default: 3), delay (default: 1000ms), backoff factor (default: 2), max delay (default: 10000ms)

### Health Checks & Monitoring
**Health Check Endpoint**: /health (configurable), timeout (default: 5000ms), interval (default: 30000ms); **RabbitMQ Service Monitoring**: Connection status, queue health, broker availability; **Status Checks**: Memory usage, connection pool health, message processing metrics; **Automatic Recovery**: Connection reconnection, queue rediscovery, service restart capabilities

### Performance Metrics & Observability
**Metrics Collection**: Response time per tool, error rate per endpoint, memory/CPU usage, request throughput, message processing rates; **Prometheus Integration**: Metrics export endpoints (/metrics), configurable collection intervals; **Alerting**: Authentication failures, RabbitMQ connection timeouts, performance degradation, queue depth warnings; **Monitoring Dashboards**: Grafana integration, real-time performance visualization; **Request Tracing**: MCP request correlation, message flow tracking, end-to-end latency monitoring

### Technology Stack
Python 3.12+ as primary language; pika for RabbitMQ client; pydantic for schema validation; pytest for testing; structlog for logging; uvx for dependency management; asyncio for concurrent operations; rich for console client UI; click for CLI interface; **Vector Database**: ChromaDB (local mode) or sqlite-vec for semantic search; **Schema Validation**: jsonschema for runtime validation; **Embeddings**: sentence-transformers for text embeddings; **Search**: Vector similarity search with <100ms response time

**Official RabbitMQ Management API documentation:**  
https://www.rabbitmq.com/docs/http-api-reference

**Official MCP Python SDK:**  
https://github.com/modelcontextprotocol/python-sdk

## Development Workflow

### Code Review Process
All PRs MUST verify constitution compliance; Mandatory review by 2 developers; Tests MUST pass with 100% success; Test coverage cannot decrease; Updated documentation mandatory; MCP protocol compliance verification; Console client functionality testing

### Quality Gates
Unit tests: 80% minimum coverage; Integration tests: 100% for critical tools; Linting: zero warnings; Type checking: zero errors; Performance: approved benchmarks; MCP tool validation: all tools tested; Console client usability testing

### Deployment Process
Semantic versioning mandatory; Updated changelog; Staging environment testing; Automatic rollback on failure; Active post-deployment monitoring; MCP server health checks; Console client deployment validation

## Console Client Requirements

### Built-in Console Client
MUST provide interactive console interface; Support for all MCP tools via CLI; Real-time RabbitMQ connection status; Message publishing and consumption; Queue management operations; User-friendly error messages; Command history and auto-completion

**The built-in console client MUST be available in the 20 most spoken languages worldwide:**
1. English
2. Mandarin Chinese
3. Hindi
4. Spanish
5. French
6. Arabic
7. Bengali
8. Russian
9. Portuguese
10. Indonesian
11. Urdu
12. German
13. Japanese
14. Swahili
15. Marathi
16. Telugu
17. Turkish
18. Tamil
19. Vietnamese
20. Italian

### Console Client Features
Interactive mode with rich UI; Batch command execution; Configuration management; Connection testing; Message monitoring; Performance metrics display; Help system with examples

## License Requirements

### LGPL License Compliance
All code MUST be licensed under GNU Lesser General Public License (LGPL) v3.0; Source code MUST be made available; Derivative works MUST maintain LGPL compatibility; Commercial use permitted with proper attribution; License headers MUST be included in all source files; License file MUST be present in project root; Documentation MUST reference LGPL terms; Third-party dependencies MUST be compatible with LGPL; License compliance verification in CI/CD pipeline

## Governance

This constitution supersedes all other practices; Amendments require documentation, approval, and migration plan; All PRs/reviews MUST verify compliance; Complexity must be justified; Use GEMINI.md for runtime development guidance; Console client changes require user experience validation

**Version**: 2.1.2 | **Ratified**: 2025-09-15 | **Last Amended**: 2025-01-15

## Additional Requirements

### API Versioning & Deprecation Policy
Clarify what constitutes a "breaking change" and how users are notified (e.g., changelog, release notes). Specify the format and location of migration guides.
**Smart guess:** Breaking changes are any changes that alter API contracts, remove or rename commands, or change input/output schemas. Users are notified via CHANGELOG.md and release notes. Migration guides are provided in docs/API.md.
**Further clarification:** Minor and patch releases MUST NOT introduce breaking changes. Deprecation warnings are added to API responses and CLI output for at least one MAJOR version before removal.
## Smart Guess Clarifications (2025-09-18)

### Internationalization (i18n) for Console Client
- Language selection defaults to system locale; users can override with a CLI flag (e.g., `--lang`).
- If a translation is missing, fallback to English.

### Accessibility Standards for CLI
- CLI output supports screen readers (plain text, no forced colors).
- High-contrast mode and keyboard-only navigation are supported.
- Accessibility is tested with automated tools (axe, Lighthouse) and manual review.

### Backup & Restore
- MVP implementation backs up topology (definitions.json).
- Message data backup is optional and can be added in future releases.

### Rate Limiting & Abuse Prevention
- Rate limits are enforced per user and per tool, configured in a YAML/JSON file in `config/`.
- Abuse triggers alerts and temporary blocks; exceptions require approval and documentation.

### API Versioning & Deprecation
- Migration scripts are included in `docs/DEPLOYMENT.md` and release assets.
- Deprecation warnings are shown in CLI output and API responses, with clear entries in CHANGELOG.md.

### Security & Secrets Management
- Secrets are managed via environment variables by default, with optional integration for Vault/AWS Secrets Manager.
- Secret rotation is triggered by scheduled jobs and verified in audit logs.

### Testing Requirements
- Integration tests use a local RabbitMQ container by default.
- Support for remote brokers is documented for staging/production environments.

### Accessibility Standards
Define which accessibility standards (e.g., WCAG 2.1 AA) are targeted. Clarify how accessibility testing is performed and documented.
**Smart guess:** Target WCAG 2.1 AA compliance. Accessibility testing is performed using automated tools (e.g., axe, Lighthouse) and manual review. Results are documented in docs/CONTRIBUTING.md.
**Further clarification:** Accessibility bugs are tracked as high-priority issues. All new UI features MUST include accessibility review in PRs.

### Internationalization (i18n) Testing
Clarify the process for validating translations (e.g., review by native speakers, automated checks). Specify how new languages are proposed and added.
**Smart guess:** Translations are validated by native speakers and checked with automated tools. New languages are proposed via GitHub issues and added after review.
**Further clarification:** Language files are stored in a dedicated i18n directory. Automated tests verify presence and format for all supported languages.

### Disaster Recovery & Backup
Clarify what data is included in backups (e.g., only topology, also messages?). Specify backup frequency and retention policy.
**Smart guess:** Backups include topology (definitions.json) and optionally message data (queue dumps). Backups are performed daily and retained for 30 days.
**Further clarification:** Restore procedures are tested quarterly in staging environments. Backup integrity is verified after each backup cycle.

### Rate Limiting & Abuse Prevention
Clarify default rate limits and how they are configured. Specify how abuse is detected and what actions are taken.
**Smart guess:** Default rate limits are 1000 requests/minute per user/tool. Limits are configured in server config files. Abuse is detected via monitoring logs and triggers alerts; offending users may be temporarily blocked.
**Further clarification:** Rate limit exceptions (e.g., for admin users) are documented and require approval. Abuse actions are logged and reviewed by maintainers.

### Incident Response & Security Auditing
Clarify where the incident response plan is documented and who is responsible for maintaining it. Specify the process for reviewing audit logs.
**Smart guess:** Incident response plan is documented in docs/SECURITY.md and maintained by the project security lead. Audit logs are reviewed monthly by the core team.
**Further clarification:** Security incidents are reported within 24 hours of discovery. Audit log access is restricted to authorized personnel.

### Upgrade & Migration Procedures
Clarify what constitutes a "major upgrade" and how migration scripts are delivered to users.
**Smart guess:** Major upgrades are any changes requiring manual intervention or schema migration. Migration scripts are delivered in the release assets and documented in docs/DEPLOYMENT.md.
**Further clarification:** Migration scripts include rollback instructions. Major upgrade announcements are posted on project website and mailing list.

### Community Contribution Guidelines
Clarify where templates and code of conduct are located. Specify the process for updating contribution guidelines.
**Smart guess:** Issue/PR templates and code of conduct are in .github/ directory. Contribution guidelines are updated via PR and reviewed by maintainers.
**Further clarification:** All contributors must sign a Contributor License Agreement (CLA) before PRs are merged.

### Environment Configuration & Secrets Management
Clarify which secret managers are supported. Specify how secret rotation is triggered and verified.
**Smart guess:** Supported secret managers include HashiCorp Vault, AWS Secrets Manager, and environment variables. Secret rotation is triggered via scheduled jobs and verified by audit logs.
**Further clarification:** Secrets are rotated at least every 90 days. Secret access is logged and reviewed quarterly.

### Resource Cleanup & Lifecycle Management
Clarify what triggers automatic cleanup and how users can manually invoke cleanup.
**Smart guess:** Automatic cleanup is triggered by resource inactivity (e.g., unused for 30 days). Manual cleanup is available via CLI commands.
**Further clarification:** Users are notified before automatic cleanup of resources. Cleanup actions are logged for audit purposes.

### API Rate/Quota Enforcement
Clarify default quotas and how users can request changes. Specify error codes for quota violations.
**Smart guess:** Default quotas are set in config files; users request changes via support tickets. Quota violations return error code MCP_QUOTA_EXCEEDED.
**Further clarification:** Quota changes are subject to approval by project maintainers. Quota enforcement is tested in integration tests.

### CI/CD Workflow Details
Clarify which CI/CD platforms are supported and where pipeline configuration is documented.
**Smart guess:** Supported platforms are GitHub Actions and GitLab CI. Pipeline configuration is documented in docs/DEPLOYMENT.md.
**Further clarification:** CI/CD failures block merges to main branches. Pipeline status is displayed in project README.md.

**Build/Pre-pack Phase Requirements:**
- CI/CD pipeline MUST verify that generated artifacts are up-to-date with OpenAPI specification (NOT regenerate them)
- Build step MUST fail if:
  - OpenAPI specification is invalid or cannot be parsed
  - Generated artifacts are missing or out-of-sync with OpenAPI specification
  - Schema validation tests fail
- Generated artifacts (schemas, operation registry, vector indices) MUST be committed to version control
- Changes to OpenAPI specification trigger code generation locally (via file watcher or manual script execution), NOT in CI/CD
- Pre-commit hooks SHOULD:
  - Validate OpenAPI specification syntax before allowing commits
  - Verify that generated artifacts are up-to-date with OpenAPI changes
  - Auto-run generation scripts if OpenAPI has changed but artifacts haven't been regenerated

### Third-Party Dependency Management
Clarify how dependency audits are performed (e.g., tools used, frequency).
**Smart guess:** Dependency audits are performed monthly using tools like pip-audit and safety.
**Further clarification:** Critical vulnerabilities trigger immediate dependency updates. Dependency changes are reviewed in PRs.

### End-of-Life Policy
Clarify how users are notified of deprecation and sunset schedules.
**Smart guess:** Users are notified via CHANGELOG.md, release notes, and direct email (if subscribed).
**Further clarification:** Deprecated features are marked in documentation and CLI help output. Sunset schedules are published in docs/CONTRIBUTING.md.

### Data Privacy & Compliance
Clarify which privacy regulations apply and how compliance is verified.
**Smart guess:** GDPR and CCPA apply if personal data is processed. Compliance is verified via automated checks in CI/CD and annual legal review.
**Further clarification:** Data subject requests (e.g., deletion) are processed within 30 days. Privacy policy is published in docs/PRIVACY.md.

## Artifact Requirements

In addition to tools (server), commands (client), and services (both), the following artifacts are typically produced or required:

- **OpenAPI Specification**: `.specify/memory/rabbitmq-http-api-openapi.yaml` - Single source of truth for all HTTP API operations, schemas, and documentation.
- **Schemas**: Pydantic models auto-generated from OpenAPI `components.schemas` for message validation and API contracts. Manual schemas required for AMQP protocol operations.
- **Configuration Files**: YAML, JSON, or ENV files for environment, secrets, and runtime settings.
- **Documentation**: Markdown files, API docs (auto-generated from OpenAPI), architecture diagrams, and usage guides.
- **Test Suites**: Unit, integration, contract, and end-to-end test scripts and fixtures. Contract tests MUST validate against OpenAPI specification.
- **Schema Generation Scripts**: Tools to auto-generate Pydantic models from OpenAPI specification (run during build/deployment).
- **Vector Database Index**: Pre-computed embeddings and search indices generated from OpenAPI operation descriptions.
- **Migration Scripts**: For database or topology changes.
- **Log Files**: Structured logs for audit, debugging, and monitoring.
- **Metrics & Monitoring Dashboards**: Grafana, Prometheus, or other dashboard configs.
- **Localization Files**: i18n translation files for multi-language support.
- **Deployment Manifests**: Dockerfiles, Kubernetes manifests, CI/CD pipeline configs.
- **License & Legal Files**: LICENSE (LGPL), NOTICE, and privacy policy documents.
- **Sample Data & Examples**: Example payloads derived from OpenAPI examples, CLI usage scripts, and mock data for development/testing.
- **Backup & Restore Scripts**: For disaster recovery.
- **Security Policies**: Access control lists, secret rotation policies, and incident response plans.

**All source code and distributed artifacts MUST be licensed under GNU Lesser General Public License (LGPL).**

These artifacts MUST be maintained and kept up-to-date with code and feature changes. Changes to the OpenAPI specification MUST trigger re-generation of dependent artifacts.

## Artifact Examples

Below are code snippets for common artifact types in a Python MCP server:

### 1. Schema Definition (Auto-generated from OpenAPI)
```python
# schemas/queue.py
# AUTO-GENERATED FROM OPENAPI - DO NOT EDIT MANUALLY
# Source: .specify/memory/rabbitmq-http-api-openapi.yaml
# Generated: 2025-01-15 10:30:00 UTC
from pydantic import BaseModel, Field
from typing import Optional

class Queue(BaseModel):
    """Auto-generated from OpenAPI components.schemas.Queue"""
    name: str = Field(..., description="Name of the queue")
    vhost: str = Field(..., description="Virtual host")
    durable: bool = Field(..., description="Whether the queue is durable")
    auto_delete: bool = Field(..., description="Whether the queue is auto-deleted")
    arguments: Optional[dict] = Field(None, description="Queue arguments")
    messages: int = Field(..., description="Number of messages in queue")
    messages_ready: int = Field(..., description="Messages ready for delivery")
    messages_unacknowledged: int = Field(..., description="Unacknowledged messages")
    consumers: int = Field(..., description="Number of consumers")
```

### 2. Configuration File (YAML)
```yaml
# config/config.yaml
rabbitmq:
  host: "localhost"
  port: 5672
  user: "guest"
  password: "guest"
  vhost: "/"
logging:
  level: "INFO"
  format: "json"
```

### 3. MCP Tool Example (Python) - Semantic Discovery Pattern
```python
# tools/call_id.py
from mcp_sdk import MCPTool
from openapi.operation_registry import OperationRegistry
from openapi.validator import validate_params
from operations.executor import execute_operation

class CallIdTool(MCPTool):
    """Execute RabbitMQ operation with dynamic validation from OpenAPI"""
    
    def __init__(self, openapi_spec_path: str):
        self.registry = OperationRegistry(openapi_spec_path)
    
    def run(self, endpoint_id: str, params: dict, pagination: dict = None):
        # Get operation details from OpenAPI specification
        operation = self.registry.get_operation(endpoint_id)
        
        # Validate parameters against OpenAPI schema
        validated_params = validate_params(operation, params)
        
        # Execute operation using HTTP client or AMQP client
        result = execute_operation(operation, validated_params, pagination)
        
        return result
```

### 4. CLI Command (Click)
```python
# cli/main.py
import click

@click.command()
@click.option('--queue', required=True)
def list_messages(queue):
    """List messages in a queue."""
    # ...logic to list messages...
    click.echo(f"Messages in {queue}: ...")
```

### 5. Logging Setup (structlog)
```python
# logging_config.py
import structlog

structlog.configure(
    processors=[
        structlog.processors.JSONRenderer()
    ]
)
```

### 6. Test Case (pytest)
```python
# tests/test_publish.py
import pytest
from tools.publish import PublishTool

def test_publish_success():
    tool = PublishTool()
    result = tool.run("main-exchange", "rk", {"foo": "bar"})
    assert result["status"] == "success"
```

### 7. Dockerfile (Deployment Manifest)
```dockerfile
# Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt
CMD ["python", "cli/main.py"]
```

### 8. Example MCP Request (JSON) - Semantic Discovery Pattern
```json
// examples/search_operation.json
{
  "jsonrpc": "2.0",
  "method": "search-ids",
  "params": {
    "query": "list all queues in a virtual host",
    "pagination": {"page": 1, "pageSize": 10}
  },
  "id": 1
}

// examples/get_operation_schema.json
{
  "jsonrpc": "2.0",
  "method": "get-id",
  "params": {
    "endpoint_id": "queues.list"
  },
  "id": 2
}

// examples/execute_operation.json
// Operation schema derived from OpenAPI: GET /api/queues/{vhost}
{
  "jsonrpc": "2.0",
  "method": "call-id",
  "params": {
    "endpoint_id": "queues.list",
    "params": {
      "vhost": "/"
    },
    "pagination": {"page": 1, "pageSize": 50}
  },
  "id": 3
}
```

### 9. Schema Generation Script (Python)
```python
# scripts/generate_schemas.py
"""
Auto-generate Pydantic models from OpenAPI specification.
Run this script when the OpenAPI specification is updated.
"""
import yaml
from pathlib import Path
from datetime import datetime
from datamodel_code_generator import generate

OPENAPI_SPEC = Path(".specify/memory/rabbitmq-http-api-openapi.yaml")
OUTPUT_DIR = Path("src/schemas")

def generate_schemas():
    """Generate Pydantic models from OpenAPI components.schemas"""
    with open(OPENAPI_SPEC) as f:
        spec = yaml.safe_load(f)
    
    # Generate header with metadata
    header = f"""
# AUTO-GENERATED FROM OPENAPI - DO NOT EDIT MANUALLY
# Source: {OPENAPI_SPEC}
# Generated: {datetime.utcnow().isoformat()} UTC
# OpenAPI Version: {spec['info']['version']}
"""
    
    # Use datamodel-code-generator to create Pydantic models
    generate(
        input_filename=OPENAPI_SPEC,
        input_file_type="openapi",
        output=OUTPUT_DIR,
        output_model_type="pydantic_v2.BaseModel",
        use_double_quotes=True,
        use_standard_collections=True,
        custom_template_dir=None,
        extra_template_data={"header": header}
    )
    
    print(f"✓ Generated schemas in {OUTPUT_DIR}")
    print(f"✓ Source: {OPENAPI_SPEC}")
    print(f"✓ OpenAPI version: {spec['info']['version']}")

if __name__ == "__main__":
    generate_schemas()
```

### 10. License File (LGPL)
```text
# LICENSE
This project is licensed under the GNU Lesser General Public License (LGPL) v3.0.
See https://www.gnu.org/licenses/lgpl-3.0.html for details.
```
