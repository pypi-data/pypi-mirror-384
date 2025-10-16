# Feature Specification: Basic Structured Logging

**Feature Branch**: `007-basic-structured-logging`  
**Created**: 2025-10-09  
**Status**: Draft  
**Input**: User description: "Basic Structured Logging"

## Clarifications

### Session 2025-10-09

- Q: Quando uma falha de escrita de log ocorre (ex: disco cheio), qual deve ser o comportamento do sistema? → A: Log para stderr/console - tenta output alternativo, operação principal segue
- Q: Como stack traces e mensagens multi-linha devem ser armazenadas no JSON estruturado? → A: String única com \n - preserva quebras de linha como caracteres escape
- Q: Quando geração de correlation ID falha, como o sistema deve proceder? → A: Timestamp-based - gera ID usando timestamp + random para garantir unicidade
- Q: Como o sistema deve lidar com mensagens de log que excedem 1MB? → A: Truncar - corta mensagem em limite fixo (ex: 100KB) e adiciona "...[truncated]"
- Q: Quando e onde correlation IDs devem ser gerados no ciclo de vida de uma operação? → A: Por requisição MCP - gerado quando MCP tool é invocado, mesmo ID para toda operação
- Q: O que acontece quando arquivos de log estão sendo lidos ou arquivados enquanto o sistema está escrevendo neles? → A: Write-through - sistema continua escrevendo normalmente; ferramentas externas são responsáveis por lidar com arquivos ativos de forma segura
- Q: O que acontece quando data/hora muda (horário de verão, mudanças de timezone)? → A: UTC always - todos timestamps em UTC (ISO 8601 com Z), imune a DST e mudanças de timezone local
- Q: Qual o comportamento quando o buffer de logs assíncronos atinge capacidade máxima? → A: Block writes - bloqueia operações até buffer ter espaço, garantindo que nenhum log seja perdido (crítico para auditoria)
- Q: Como o sistema procede quando não consegue definir permissões seguras (600) em arquivos de log? → A: Warn and continue - registra aviso em stderr/console mas prossegue com permissões padrão do sistema (cross-platform compatibility)
- Q: Qual deve ser a capacidade mínima esperada do sistema de logging em termos de throughput? → A: No limit specified - sem limite hard-coded; throughput determinado por hardware, buffer assíncrono e I/O (latência 5ms/op já especificada)

### Session 2025-10-12

- Q: How should runtime log level changes be implemented for "increase log verbosity without restarting the system" (User Story 5)? → A: Signal-based reload (SIGHUP/SIGUSR1) - Send OS signal to trigger config reload
- Q: Should log entries include a schema version field to support backward-compatible parsing when log structure evolves? → A: Add version field ("1.0.0") - Include semantic version in every LogEntry
- Q: When the MCP server process shuts down (SIGTERM, SIGINT, normal termination), what happens to logs still in the async buffer? → A: Flush on shutdown - Block process termination until all buffered logs written to disk

## User Scenarios & Testing *(mandatory)*

### User Story 1 - System Observability for Operations Team (Priority: P1)

As an operations engineer, I need structured logs to monitor system health and diagnose issues when the RabbitMQ MCP server encounters problems, so I can quickly identify and resolve production incidents.

**Why this priority**: Core observability is the foundation for all other logging capabilities. Without basic logging, the system is a black box, making troubleshooting impossible.

**Independent Test**: Can be fully tested by triggering various system operations (connections, message operations, errors) and verifying that structured JSON logs are written to the logs directory with appropriate timestamps, levels, and operation details.

**Acceptance Scenarios**:

1. **Given** the system is starting up, **When** a connection to RabbitMQ is attempted, **Then** connection events are logged with connection details, timestamp, and status
2. **Given** the system is running, **When** any MCP tool operation is executed, **Then** operation logs capture the tool name, parameters, execution time, and result
3. **Given** an error occurs during any operation, **When** the error is handled, **Then** error logs include the exception type, message, stack trace, and context
4. **Given** logs are being written, **When** I open the log file, **Then** all entries are in valid JSON format and can be parsed by standard JSON tools

---

### User Story 2 - Security Compliance and Audit Trail (Priority: P1)

As a security officer, I need all sensitive data automatically redacted from logs and a complete audit trail of operations, so I can ensure compliance with security policies and investigate security incidents without exposing credentials.

**Why this priority**: Security is non-negotiable. Logging credentials or sensitive data violates security policies and creates compliance risks. This must be part of the MVP.

**Independent Test**: Can be tested by executing operations with sensitive data (passwords, tokens, API keys) and verifying that logs contain redacted placeholders instead of actual values, while maintaining audit trail completeness.

**Acceptance Scenarios**:

1. **Given** a connection string contains a password, **When** connection logs are written, **Then** the password is replaced with "[REDACTED]" in all log output
2. **Given** any operation involves authentication credentials, **When** logs are written, **Then** no credential values appear in any log field
3. **Given** an MCP tool is invoked, **When** reviewing logs, **Then** a unique correlation ID is generated at invocation time and all related log entries share the same ID for complete traceability
4. **Given** a security audit is requested, **When** reviewing log files, **Then** all operations have complete audit trail with who, what, when, and outcome information
5. **Given** log files are created, **When** checking file permissions, **Then** files have secure permissions preventing unauthorized access

---

### User Story 3 - Performance Monitoring and Optimization (Priority: P2)

As a performance engineer, I need timing information and resource usage metrics in logs, so I can identify performance bottlenecks and optimize system operations.

**Why this priority**: Performance visibility helps ensure SLAs are met and enables proactive optimization. While important, the system can function without detailed performance metrics initially.

**Independent Test**: Can be tested by executing various operations and verifying that logs include timing data, operation duration, and resource usage metrics in a consistent format.

**Acceptance Scenarios**:

1. **Given** any operation is executed, **When** the operation completes, **Then** logs include the operation duration in milliseconds
2. **Given** operations are running, **When** reviewing performance logs, **Then** timing information shows the overhead of logging itself is under 5ms per operation
3. **Given** high-throughput scenarios occur, **When** many operations happen simultaneously, **Then** asynchronous logging prevents blocking the main operations

---

### User Story 4 - Log Management and Organization (Priority: P2)

As a system administrator, I need automatic log rotation and organized log files, so I can maintain disk space and easily locate logs from specific time periods without manual intervention.

**Why this priority**: Essential for long-running systems to prevent disk space issues, but the system can operate temporarily without rotation in early testing.

**Independent Test**: Can be tested by running the system across multiple days and file size limits, verifying that logs rotate correctly, old logs are retained per policy, and files are organized with clear naming conventions.

**Acceptance Scenarios**:

1. **Given** the system runs across midnight, **When** a new day starts, **Then** a new log file is created with the current date in the filename
2. **Given** a log file reaches 100MB, **When** more logs are written, **Then** the file is rotated and a new file is started
3. **Given** log files are older than 30 days, **When** the retention policy runs, **Then** old log files are removed or archived according to policy
4. **Given** logs are rotated, **When** compression is enabled, **Then** old log files are compressed with gzip to save disk space

---

### User Story 5 - Debugging and Development Support (Priority: P3)

As a developer, I need detailed debug-level logs during development and testing, so I can understand system behavior and troubleshoot issues during feature development.

**Why this priority**: Useful for development but not required for production operations. Can be added after core logging is stable.

**Independent Test**: Can be tested by setting log level to DEBUG and verifying that detailed internal operation logs are written, then setting to INFO and verifying debug logs are suppressed.

**Acceptance Scenarios**:

1. **Given** log level is set to DEBUG, **When** operations execute, **Then** detailed internal state and variable values are logged
2. **Given** log level is set to INFO, **When** operations execute, **Then** debug-level logs are not written to reduce noise
3. **Given** an issue needs investigation, **When** I send SIGHUP signal to the process (or update config and trigger reload), **Then** the new log level takes effect immediately and detailed operation flow appears in logs without process restart

---

### User Story 6 - RabbitMQ Log Streaming (Priority: P2 - Optional for MVP)

As a platform engineer, I need logs published to RabbitMQ AMQP exchanges in real-time, so I can build distributed log aggregation pipelines and enable multiple consumers to process logs independently for monitoring, alerting, and analytics.

**Why this priority**: Valuable for enterprise message queue applications where domain-aligned logging (RabbitMQ server publishing logs to RabbitMQ) enables real-time observability. While constitution requires "configurable log destinations", MVP satisfies this with File + Console destinations; RabbitMQ AMQP is an advanced destination for Phase 2. Priority P2 reflects that core logging functionality (File + Console) provides sufficient observability for initial release.

**Independent Test**: Can be tested by configuring RabbitMQ destination, executing operations, and verifying logs are published to the exchange with correct routing keys; consumers can filter by level/category; system continues functioning if RabbitMQ broker is unavailable.

**Concurrent Consumer Support**: Multiple consumers MUST be able to subscribe to the same log exchange independently using separate queues bound with routing key patterns (e.g., "error.*" for all errors, "*.security" for all security events across levels), ensuring each consumer receives log copies without interference.

**Acceptance Scenarios**:

1. **Given** RabbitMQ destination is enabled in configuration, **When** any log is written, **Then** the log is published to the configured topic exchange with routing key {level}.{category} within 500ms maximum latency
2. **Given** a consumer subscribes to routing key "error.*", **When** ERROR level logs are generated, **Then** the consumer receives only error logs and can filter by category
3. **Given** the RabbitMQ broker becomes unavailable, **When** logs are written, **Then** the system falls back to console logging without blocking operations and automatically reconnects when broker recovers using exponential backoff (3 attempts, 1s base delay, 2x backoff, 10s max delay)
4. **Given** multiple consumers subscribe to the log exchange with separate queues, **When** logs are published, **Then** all consumers receive copies of log messages independently without interfering with each other (each consumer has its own queue bound to the exchange)
5. **Given** the system starts with RabbitMQ unavailable, **When** RabbitMQ becomes available later, **Then** the logging system automatically establishes connection using retry logic (3 attempts, exponential backoff) and begins publishing logs without manual intervention

---

### Edge Cases

- **Logs directory doesn't exist or is not writable**: System attempts to create directory on startup; if creation fails or log writing failures occur (disk full, permission denied), system uses stderr/console fallback per FR-019
- **Concurrent file access (reading/archiving during writes)**: System uses write-through approach, continuing to write normally while external tools (log analyzers, archivers, tail -f) handle active file access safely through OS-level file locking
- **Multi-line messages formatting (stack traces)**: Stored as single JSON string with escaped newline characters (\n) to preserve structure while maintaining JSON validity
- **Correlation ID generation failure**: System falls back to timestamp-based ID generation (timestamp + random component) to ensure uniqueness and maintain audit trail
- **Very large log messages (>1MB)**: Truncated at 100KB limit with "...[truncated]" suffix to prevent memory issues while preserving most relevant information
- **Date/time changes (DST, timezone shifts)**: All timestamps stored in UTC (ISO 8601 format with Z suffix) to avoid ambiguities from daylight saving transitions or timezone changes
- **Async buffer saturation**: When async buffer reaches capacity, system blocks write operations until buffer space is available, ensuring zero log loss for audit compliance (indicates system under-dimensioned)
- **File permission setting failure**: When system cannot set secure permissions (600) on log files, logs warning to stderr/console and continues with OS default permissions (cross-platform compatibility)
- **Graceful shutdown with buffered logs**: When process receives shutdown signals (SIGTERM, SIGINT) or terminates normally, system blocks exit for maximum 30 seconds until all buffered logs are flushed to disk, maintaining zero log loss guarantee (FR-025)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST write all logs in structured JSON format with consistent schema
- **FR-002**: System MUST support standard log levels: ERROR, WARN, INFO, DEBUG
- **FR-003**: System MUST write logs to files in ./logs/ directory with naming pattern rabbitmq-mcp-{date}.log
- **FR-004**: System MUST automatically redact all sensitive data including passwords, tokens, API keys, and credentials before writing logs, ensuring zero credentials or sensitive data appear in any log output (security compliance requirement); messages exceeding 100KB MUST be truncated at the limit with "...[truncated]" suffix appended
- **FR-005**: System MUST generate and assign unique correlation IDs at MCP tool invocation time, propagating the same ID across all log entries for that operation's complete lifecycle
- **FR-006**: System MUST log connection events including connection attempts, successes, failures, and disconnections
- **FR-007**: System MUST log all MCP tool operations including tool name, parameters, execution time, and results
- **FR-008**: System MUST log error conditions with exception type, message, stack trace, and contextual information
- **FR-009**: System MUST log security events including authentication and authorization attempts
- **FR-010**: System MUST log performance metrics including operation duration (duration_ms field) for all operations as mandatory baseline; system MUST achieve minimum throughput of 1000 logs/second on reference hardware (4-core CPU, 8GB RAM, SSD storage)
- **FR-011**: System MUST include ISO 8601 formatted timestamps in UTC (with Z suffix) in all log entries to avoid ambiguities from timezone or DST changes
- **FR-012**: System MUST rotate log files based on dual triggers: (1) daily at midnight UTC, and (2) when file size reaches 100MB limit, whichever occurs first
- **FR-013**: System MUST retain logs for 30 days minimum (configurable)
- **FR-014**: System MUST attempt to set secure file permissions (600 for files, 700 for directories) on log files and directories to restrict access; if setting fails, MUST log warning to stderr/console and continue with OS default permissions
- **FR-015**: System MUST complete logging operations in under 5ms overhead per operation
- **FR-016**: System MUST support asynchronous logging for high-throughput scenarios; when buffer reaches capacity, MUST block writes until space is available to ensure zero log loss
- **FR-017**: System MUST compress rotated log files using gzip to conserve disk space
- **FR-018**: System MUST create audit trail for all operations with complete operation lifecycle tracking
- **FR-019**: System MUST fallback to stderr/console output when file logging fails, allowing operations to continue without blocking
- **FR-020**: System MUST format multi-line messages (stack traces, error details) as single JSON strings with escaped newline characters (\n)
- **FR-021**: System MUST use timestamp-based ID generation (timestamp + random component) as fallback when UUID generation fails to ensure correlation ID uniqueness
- **FR-022**: System MUST use write-through approach for concurrent file access, allowing continuous writing while external tools access log files simultaneously
- **FR-023**: System MUST support runtime configuration reload (log level, output settings) via OS signal handling (SIGHUP/SIGUSR1 on Unix/Linux/macOS, file modification polling on Windows) without requiring process restart
- **FR-024**: System MUST include a schema_version field (semantic versioning format "MAJOR.MINOR.PATCH", starting at "1.0.0") in every log entry to enable backward-compatible parsing when log structure evolves; versioning rules: increment MAJOR for breaking structure changes (e.g., removing fields, changing field types), MINOR for backward-compatible additions (e.g., adding optional fields), PATCH for documentation or metadata clarifications only
- **FR-025**: System MUST flush all buffered async logs to disk during graceful shutdown (SIGTERM, SIGINT, normal termination), blocking process exit until flush completes with maximum timeout of 30 seconds to maintain zero log loss guarantee
- **FR-026**: System MUST support RabbitMQ AMQP as a configurable log destination (Priority P2 - optional for MVP), publishing logs to a durable topic exchange with routing keys in format {level}.{category} for real-time log streaming (<500ms max latency from generation to publish) and filtering; connection failures MUST fallback to console logging without blocking operations; uses persistent messages (delivery_mode=2) with connection pooling and automatic reconnection with exponential backoff (3 attempts, 1s base delay, 2x backoff factor, 10s max delay)

### Key Entities

- **LogEntry**: Represents a single log entry containing schema version, timestamp, level, category, message, correlation ID, and structured contextual data
- **Schema Version**: Semantic version string (e.g., "1.0.0") included in every LogEntry to enable backward-compatible parsing when log structure evolves
- **Correlation ID**: Unique identifier (preferably UUID, fallback to timestamp+random) generated per MCP tool invocation that links all related LogEntry instances across the complete operation lifecycle
- **Log Category**: Classification of LogEntry (Connection, Operation, Error, Security, Performance) for filtering and analysis
- **Sensitive Data Pattern**: Patterns identifying data requiring redaction (password fields, token formats, credential patterns)
- **LogFile**: Physical file containing LogEntry instances for a specific date with size and rotation tracking

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Operations team can diagnose 90% of production issues using log information alone without additional debugging (measured via post-implementation survey of operations team after 30 days of production use)
- **SC-002**: Security audits can trace complete operation lifecycle through correlation IDs with 100% coverage (verified by automated tests validating all log entries within an operation share the same correlation_id)
- **SC-003**: Log writing adds less than 5ms overhead to any operation execution time (measured by performance benchmark tests with 1000-operation sample size)
- **SC-004**: Zero instances of credentials or sensitive data appear in log files during security reviews (verified by automated regex scanning in CI/CD pipeline and manual security audit)
- **SC-005**: System maintains continuous operation with disk space usage under control through automatic log rotation and retention (verified by 7-day test run monitoring disk usage remains stable)
- **SC-006**: 95% of error investigations start with structured log queries rather than code inspection (measured via developer survey and incident response tracking after 30 days)
- **SC-007**: Log files can be parsed and analyzed by standard JSON processing tools without custom parsers (verified by successful parsing with jq, Python json module, and Elasticsearch ingestion)
- **SC-008**: Performance bottlenecks can be identified within 10 minutes using logged timing metrics (verified by timed exercise with operations team using jq queries on sample log data)

## Constraints & Tradeoffs *(optional)*

### Architectural Decisions

1. **JSON Structured Format vs Plain Text**
   - **Decision**: JSON structured logging
   - **Rationale**: Enables automated parsing, filtering, and analysis by standard tools (jq, log aggregators); sacrifices some human readability for machine processability
   - **Tradeoff**: Slightly larger file sizes and less readable raw logs, but vastly superior for operational analysis and debugging at scale

2. **Asynchronous vs Synchronous Logging**
   - **Decision**: Asynchronous with blocking on buffer saturation
   - **Rationale**: Industry standard for production systems; minimizes impact on operation latency while ensuring zero log loss for audit compliance
   - **Tradeoff**: Added complexity of buffer management vs improved throughput; chose reliability (blocking when full) over pure performance

3. **File-based vs System Logger (syslog/journald)**
   - **Decision**: Direct file-based logging
   - **Rationale**: Cross-platform consistency (Windows/Linux/macOS), simpler deployment, no external dependencies
   - **Tradeoff**: Manual log management vs OS-integrated solutions; chose simplicity and portability for MVP

4. **Automatic Redaction vs Developer Responsibility**
   - **Decision**: Automatic sensitive data redaction enforced at logging layer
   - **Rationale**: Security-first approach; eliminates human error in protecting credentials
   - **Tradeoff**: Small performance overhead for pattern matching vs risk of credential leaks; security is non-negotiable for P1 requirement

5. **Local Storage vs Centralized Logging**
   - **Decision**: Local file system storage only
   - **Rationale**: MVP scope; centralized logging (ELK, Splunk, CloudWatch) deferred to full product
   - **Tradeoff**: Requires file system access for log analysis vs real-time aggregation; acceptable for MVP with single-instance deployments

6. **Fixed Retention vs Unlimited History**
   - **Decision**: 30-day minimum retention with automatic cleanup
   - **Rationale**: Balances operational visibility with disk space management
   - **Tradeoff**: Historical data loss vs unbounded disk usage; 30 days covers typical incident investigation windows

## Dependencies *(optional)*

- JSON formatting library for consistent log structure
- File system access for writing log files and managing rotation
- Async I/O support for non-blocking log operations
- Pattern matching capability for sensitive data detection and redaction

## Assumptions *(optional)*

- Log files are stored on local file system with adequate disk space
- System has write permissions to create and manage log directory
- Operations team has access to file system to read logs
- Standard JSON parsing tools are available for log analysis
- Time synchronization is available for accurate timestamps
- Logging throughput capacity is determined by hardware capabilities, async buffer size, and I/O performance rather than hard-coded limits; 5ms per-operation overhead constraint ensures adequate performance for typical workloads
- Log analysis and visualization tools (ELK stack, Splunk, etc.) will be integrated in future phases
- Log shipping to centralized systems will be addressed in future phases
- Advanced log aggregation and real-time monitoring will be part of full product, not MVP

## Out of Scope *(optional)*

- Integration with specific log aggregation platforms (Elasticsearch, Splunk, CloudWatch) - deferred to full product
- Real-time log streaming or tailing interface
- Log search and filtering UI - analysis done with external tools
- Log alerting and notification system
- Advanced log analytics and visualization
- Multi-region or distributed log collection
- Log encryption at rest (file-level encryption only)
- Custom log exporters or formatters beyond JSON
- Log-based metrics and dashboards
- Integration with incident management systems
