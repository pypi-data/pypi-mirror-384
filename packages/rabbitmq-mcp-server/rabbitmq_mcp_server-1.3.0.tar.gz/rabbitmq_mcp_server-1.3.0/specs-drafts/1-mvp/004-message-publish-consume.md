# SPEC-004: Message Publishing and Consumption

## Overview
Essential messaging functionality for publishing messages to exchanges and consuming messages from queues with basic acknowledgment handling.

## Components

### Message Publishing
- **Publish to Exchange**: Send messages to exchanges with routing keys
- **Message Properties**: Support for headers, content type, correlation ID
- **Message Persistence**: Option to mark messages as persistent
- **Routing**: Support for different routing key patterns

### Message Consumption
- **Subscribe to Queue**: Consume messages from specific queues
- **Message Streaming**: Stream messages to MCP client
- **Prefetch Control**: Configurable message prefetch limits
- **Auto-acknowledgment**: Optional automatic message acknowledgment

### Message Acknowledgment
- **Acknowledge**: Confirm successful message processing
- **Negative Acknowledge**: Reject message with requeue option
- **Delivery Tags**: Track individual messages for acknowledgment

### Internal Operations (AMQP Protocol - Manually Implemented)
**CRITICAL**: Message operations use AMQP protocol, NOT in OpenAPI specification. Must be implemented separately with manual Pydantic schemas.

- `amqp.publish`: Publish message to exchange via AMQP protocol
- `amqp.consume`: Subscribe to queue for message consumption via AMQP
- `amqp.ack`: Acknowledge successful message processing (basic.ack)
- `amqp.nack`: Negative acknowledge with requeue option (basic.nack)
- `amqp.reject`: Reject message (basic.reject)

**Implementation Note**: These operations are NOT derived from OpenAPI. They must be indexed in vector database alongside HTTP API operations for semantic discovery.

## Technical Requirements

### Message Publishing
- Support JSON, text, and binary payloads
- Message headers and properties
- Routing key validation
- Exchange existence validation

### Message Consumption
- Streaming message delivery to MCP client
- Configurable prefetch count (default: 10)
- Message metadata preservation
- Delivery tag tracking

### Acknowledgment System
- Reliable message acknowledgment
- Requeue on nack (configurable)
- Delivery tag validation
- Duplicate acknowledgment prevention

### Performance
- Publish operations complete within 100ms
- Message consumption latency < 50ms
- Support for 100+ concurrent consumers
- Throughput > 1000 messages/minute

## Acceptance Criteria

### Functional Requirements
- [ ] Successfully publishes messages to exchanges
- [ ] Supports different message payload types (JSON, text, binary)
- [ ] Consumes messages from queues reliably
- [ ] Streams messages to MCP client in real-time
- [ ] Acknowledges messages successfully
- [ ] Handles negative acknowledgment with requeue
- [ ] Validates exchange and queue existence
- [ ] Preserves message metadata and properties

### Performance Requirements
- [ ] Publish operations complete within 100ms
- [ ] Message consumption latency under 50ms
- [ ] Supports 100+ concurrent consumers
- [ ] Achieves > 1000 messages/minute throughput

### Reliability Requirements
- [ ] No message loss during normal operations
- [ ] Proper handling of connection failures
- [ ] Reliable acknowledgment system
- [ ] Graceful handling of consumer failures

## Dependencies
- pika for AMQP messaging
- asyncio for concurrent message handling
- JSON serialization for structured messages

## Implementation Notes
- **AMQP Protocol**: Use pika library for all message operations (publish, consume, ack/nack)
- **NOT in OpenAPI**: Message operations are AMQP protocol, separate from HTTP API
- **Manual Schemas**: Create Pydantic models manually for AMQP operations (not auto-generated)
- **Semantic Discovery**: Index AMQP operations in vector database for `search-ids` discovery
- Use pika's basic_publish for message publishing
- Implement consumer callbacks for message handling
- Track delivery tags for reliable acknowledgment
- Handle connection failures gracefully
- **Structured Logging**: Log all message operations using structlog with correlation IDs
- Support both synchronous and asynchronous operations
- **MCP Client Control**: MCP client decides ack/nack per message (constitution requirement)
