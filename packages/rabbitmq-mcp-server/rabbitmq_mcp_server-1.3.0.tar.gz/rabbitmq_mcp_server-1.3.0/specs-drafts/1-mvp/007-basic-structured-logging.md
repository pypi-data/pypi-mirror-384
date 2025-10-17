# SPEC-007: Basic Structured Logging

## Overview
Essential structured logging system for monitoring, debugging, and audit purposes with basic log management and security features.

## Components

### Logging Framework (Constitution Mandated)
- **Structured Logging**: JSON-formatted logs using structlog (mandatory)
- **Log Levels**: error, warn, info, debug (standard enterprise levels)
- **Default Output**: File-based logging to ./logs/ directory (most common for message queue apps)
- **Log Formatting**: Consistent JSON structure for all log entries
- **File Naming**: `rabbitmq-mcp-{date}.log` format
- **Configurable Destinations**: Support for multiple outputs (Elasticsearch, Splunk, CloudWatch, etc.) in full product

### Log Categories
- **Connection Logs**: RabbitMQ connection events and status
- **Operation Logs**: MCP tool execution and results
- **Error Logs**: Error conditions and exception handling
- **Security Logs**: Authentication and authorization events
- **Performance Logs**: Operation timing and resource usage

### Security Features (Constitution Mandated)
- **Sensitive Data Sanitization**: Automatic redaction of credentials and secrets (MANDATORY before logging)
- **Log Correlation**: UUID-based correlation IDs for request tracing (required for message tracking)
- **Audit Trail**: Complete audit trail for all operations
- **Access Control**: Secure log file permissions (600)
- **No Credentials in Logs**: Constitution requirement - credentials must never appear in log output
- **Tested Redaction**: Redaction logic must be tested and reviewed in code reviews

### Log Management (Basic - Full Product has Advanced Features)
- **File Organization**: Structured file naming (rabbitmq-mcp-{date}.log)
- **Log Rotation**: Daily rotation by default (configurable)
- **Retention Policy**: 30 days for basic logs (MVP), advanced policies in full product
- **Log Compression**: Optional gzip compression for rotated logs
- **Maximum File Size**: 100MB per file to prevent large files impacting performance
- **Full Product Note**: Enterprise features like ELK stack, Splunk, CloudWatch integration in Phase 2

## Technical Requirements

### Logging Configuration
- Default log level: INFO
- Log format: Structured JSON
- File location: ./logs/rabbitmq-mcp-{date}.log
- Maximum file size: 100MB per file

### Performance
- Logging overhead < 5ms per operation
- Asynchronous logging for high-throughput scenarios
- Efficient log serialization and writing

### Security
- Automatic sanitization of sensitive data
- Secure log file permissions (600)
- No credentials in log output
- Correlation ID tracking for all operations

### Log Content
- Timestamp (ISO 8601 format)
- Log level and category
- Operation details and parameters
- Error information and stack traces
- Performance metrics and timing

## Acceptance Criteria

### Functional Requirements
- [ ] Structured JSON logs are generated correctly
- [ ] All log levels work as expected
- [ ] Log files are created in correct location
- [ ] Log rotation functions properly
- [ ] Sensitive data is properly sanitized
- [ ] Correlation IDs are tracked across operations

### Performance Requirements
- [ ] Logging overhead under 5ms per operation
- [ ] Asynchronous logging works efficiently
- [ ] No performance impact on main operations

### Security Requirements
- [ ] No credentials appear in log files
- [ ] Log files have secure permissions
- [ ] Sensitive data is properly redacted
- [ ] Audit trail is complete and accurate

### Quality Requirements
- [ ] Log format is consistent and parseable
- [ ] Error information is comprehensive
- [ ] Performance metrics are captured
- [ ] Log files are properly rotated and compressed

## Dependencies
- structlog for structured logging
- asyncio for asynchronous logging
- JSON serialization for log formatting

## Implementation Notes
- Use structlog for structured logging framework
- Implement custom processors for data sanitization
- Use asyncio for non-blocking log operations
- Configure log rotation with size and time limits
- Implement correlation ID tracking across operations
- Set up secure file permissions for log files
- Create log parsing utilities for debugging
