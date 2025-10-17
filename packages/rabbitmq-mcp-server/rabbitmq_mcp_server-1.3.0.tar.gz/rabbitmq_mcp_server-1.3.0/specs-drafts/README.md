# RabbitMQ MCP Server Specifications

This directory contains detailed specifications for the RabbitMQ MCP Server project, organized by development phases.

## Development Phases

### Phase 1: MVP (Minimum Viable Product)
The MVP phase focuses on essential functionality to deliver a working RabbitMQ MCP server with core features.

#### MVP Specifications (8 specs)
- **[001-base-architecture.md](1-mvp/001-base-architecture.md)** - Base MCP Architecture
- **[002-basic-rabbitmq-connection.md](1-mvp/002-basic-rabbitmq-connection.md)** - Basic RabbitMQ Connection
- **[003-essential-topology-operations.md](1-mvp/003-essential-topology-operations.md)** - Essential Topology Operations
- **[004-message-publish-consume.md](1-mvp/004-message-publish-consume.md)** - Message Publishing and Consumption
- **[005-basic-console-client.md](1-mvp/005-basic-console-client.md)** - Basic Console Client
- **[006-basic-testing-framework.md](1-mvp/006-basic-testing-framework.md)** - Basic Testing Framework
- **[007-basic-structured-logging.md](1-mvp/007-basic-structured-logging.md)** - Basic Structured Logging
- **[008-mvp-documentation.md](1-mvp/008-mvp-documentation.md)** - MVP Documentation

### Phase 2: Full Product
The full product phase adds enterprise-grade features, advanced functionality, and production-ready capabilities.

#### Full Product Specifications (12 specs)
- **[009-advanced-vector-database.md](2-full-product/009-advanced-vector-database.md)** - Advanced Vector Database
- **[010-advanced-retry-dlq-system.md](2-full-product/010-advanced-retry-dlq-system.md)** - Advanced Retry and DLQ System
- **[011-config-import-export.md](2-full-product/011-config-import-export.md)** - Configuration Import/Export
- **[012-advanced-monitoring-metrics.md](2-full-product/012-advanced-monitoring-metrics.md)** - Advanced Monitoring and Metrics
- **[013-advanced-security.md](2-full-product/013-advanced-security.md)** - Advanced Security
- **[014-multilingual-console-client.md](2-full-product/014-multilingual-console-client.md)** - Multilingual Console Client
- **[015-comprehensive-testing-framework.md](2-full-product/015-comprehensive-testing-framework.md)** - Comprehensive Testing Framework
- **[016-enterprise-logging.md](2-full-product/016-enterprise-logging.md)** - Enterprise Logging
- **[017-performance-scalability.md](2-full-product/017-performance-scalability.md)** - Performance and Scalability
- **[018-advanced-messaging-features.md](2-full-product/018-advanced-messaging-features.md)** - Advanced Messaging Features
- **[019-comprehensive-documentation.md](2-full-product/019-comprehensive-documentation.md)** - Comprehensive Documentation
- **[020-cicd-quality-pipeline.md](2-full-product/020-cicd-quality-pipeline.md)** - CI/CD and Quality Pipeline

## Implementation Order

### Recommended Implementation Sequence

#### Phase 1: MVP (Sequential Implementation)
1. **001-base-architecture.md** - Foundation for all other components
2. **002-basic-rabbitmq-connection.md** - Core connectivity
3. **003-essential-topology-operations.md** - Basic RabbitMQ operations
4. **004-message-publish-consume.md** - Core messaging functionality
5. **005-basic-console-client.md** - User interface
6. **006-basic-testing-framework.md** - Quality assurance
7. **007-basic-structured-logging.md** - Observability
8. **008-mvp-documentation.md** - User enablement

#### Phase 2: Full Product (Parallel Implementation)
After MVP completion, full product specifications can be implemented in parallel based on priority:

**High Priority (Core Enterprise Features)**
- 009-advanced-vector-database.md
- 010-advanced-retry-dlq-system.md
- 012-advanced-monitoring-metrics.md
- 013-advanced-security.md

**Medium Priority (Enhanced Functionality)**
- 011-config-import-export.md
- 014-multilingual-console-client.md
- 015-comprehensive-testing-framework.md
- 016-enterprise-logging.md

**Lower Priority (Advanced Features)**
- 017-performance-scalability.md
- 018-advanced-messaging-features.md
- 019-comprehensive-documentation.md
- 020-cicd-quality-pipeline.md

## Specification Structure

Each specification follows a consistent structure:

- **Overview**: High-level description of the specification
- **Components**: Detailed breakdown of implementation components
- **Technical Requirements**: Performance, security, and compliance requirements
- **Acceptance Criteria**: Measurable criteria for completion
- **Dependencies**: Required libraries, tools, and frameworks
- **Implementation Notes**: Guidance for implementation

## Constitution Compliance

All specifications are designed to comply with the RabbitMQ MCP Server Constitution (`.specify/memory/constitution.md`), including:

### Critical Requirements
- **MCP Protocol Compliance**: JSON-RPC 2.0 support, schema validation mandatory
- **3-Tool Semantic Discovery Pattern**: ONLY `search-ids`, `get-id`, `call-id` are public MCP tools
- **OpenAPI Source of Truth**: All operations derived from `.specify/memory/rabbitmq-http-api-openapi.yaml`
- **Build-Time Code Generation**: Schemas, operation registry, and vector indices pre-generated and committed to repository
- **Test-First Development (TDD)**: Mandatory Red-Green-Refactor cycle, 80% minimum coverage for critical tools
- **Structured Logging**: structlog with JSON format, automatic sensitive data sanitization
- **Performance Requirements**: <200ms latency for basic operations, >500 requests/minute throughput
- **Security**: Username/Password authentication, TLS encryption, rate limiting
- **LGPL v3.0 Licensing**: All code and documentation licensed under LGPL
- **Enterprise-Grade Quality**: 95% overall test coverage, zero linting warnings

### Architecture Principles
- **OpenAPI-Driven**: HTTP API operations auto-generated from OpenAPI specification
- **AMQP Separation**: Message publish/consume/ack operations use AMQP protocol (NOT in OpenAPI)
- **Pre-computed Vector Database**: ChromaDB local mode with pre-generated embeddings
- **No Runtime Generation**: All code generation happens at build-time, NOT during server startup
- **Pagination**: Implemented only when RabbitMQ Management API supports it

## Getting Started

### For Implementers

1. **Review Constitution**: Read `.specify/memory/constitution.md` thoroughly to understand all requirements
2. **Understand OpenAPI-Driven Architecture**: All operations are derived from `.specify/memory/rabbitmq-http-api-openapi.yaml`
3. **Start with MVP**: Implement specifications 001-008 in sequential order
4. **Build-Time Setup**:
   - Set up code generation scripts: `python scripts/generate_schemas.py`
   - Set up vector database generation: `python scripts/generate_embeddings.py`
   - Configure pre-commit hooks to validate OpenAPI and artifacts
5. **TDD Approach**: Write tests first, get user approval, watch tests fail, then implement
6. **Ensure Acceptance Criteria**: All criteria must be met before moving to next specification
7. **Maintain Quality**: 80% minimum coverage for critical tools, zero linting warnings

### Key Implementation Notes

- **3-Tool Pattern**: Only register `search-ids`, `get-id`, `call-id` as MCP tools
- **AMQP vs HTTP**: Use pika for AMQP operations, requests/httpx for HTTP API operations
- **Pre-generated Artifacts**: Commit all generated schemas, registries, and vector indices to repository
- **CI/CD**: Pipeline verifies artifacts are current (does NOT regenerate)
- **Documentation**: All documentation in English, all examples tested and functional

## Contributing

When implementing specifications:

### Mandatory Requirements
1. **Follow Acceptance Criteria**: Meet all criteria exactly as specified
2. **TDD Mandatory**: Tests written → User approved → Tests fail → Implementation
3. **Constitution Compliance**: Verify compliance with all constitutional requirements
4. **Test Coverage**: Minimum 80% for critical tools, 100% for authentication and error handling
5. **Code Quality**: Zero linting warnings, zero type checking errors
6. **Documentation**: Keep documentation current with code changes

### Development Workflow
1. **OpenAPI First**: If adding/modifying operations, update OpenAPI specification first
2. **Generate Artifacts**: Run generation scripts when OpenAPI changes
3. **Write Tests**: Implement tests before implementation (TDD)
4. **Implement Features**: Follow implementation notes in specifications
5. **Verify Quality Gates**: All tests pass, coverage met, no linting warnings
6. **Update Documentation**: Ensure all documentation is current

### Code Generation Workflow
```bash
# When OpenAPI specification changes
python scripts/generate_schemas.py        # Generate Pydantic models
python scripts/generate_embeddings.py     # Generate vector database
python scripts/generate_operation_registry.py  # Generate operation registry
git add src/schemas/ data/vectors/ operation_registry.json
git commit -m "chore: regenerate artifacts from OpenAPI"
```

### Technology Stack
- **Language**: Python 3.12+
- **MCP SDK**: Official Python SDK (https://github.com/modelcontextprotocol/python-sdk)
- **AMQP**: pika library for RabbitMQ protocol operations
- **HTTP**: requests or httpx for Management API
- **Validation**: pydantic for schemas, jsonschema for runtime validation
- **Logging**: structlog for structured JSON logging
- **Testing**: pytest with pytest-asyncio, pytest-cov, pytest-xdist
- **Vector DB**: ChromaDB local mode (best for Python)
- **CLI**: click for command-line interface, rich for enhanced output

## Questions and Support

For questions about specifications or implementation guidance, refer to:

- The constitution for overall project requirements
- Individual specification files for detailed requirements
- Implementation notes within each specification
- Dependencies and technical requirements sections
