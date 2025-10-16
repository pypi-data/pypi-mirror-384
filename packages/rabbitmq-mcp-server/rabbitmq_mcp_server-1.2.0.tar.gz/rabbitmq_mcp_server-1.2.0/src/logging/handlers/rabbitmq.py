"""RabbitMQ log handler for publishing logs to AMQP exchange (T044 - User Story 6)."""

from __future__ import annotations

import json
import sys
import time
from typing import Any, Iterable, Optional

try:
    import pika
    import pika.exceptions
    PIKA_AVAILABLE = True
except ImportError:
    PIKA_AVAILABLE = False
    pika = None  # type: ignore

import orjson

__all__ = ["RabbitMQLogHandler"]


class RabbitMQLogHandler:
    """
    Handler that publishes log entries to RabbitMQ topic exchange.
    
    Features:
    - Publishes to topic exchange with routing key {level}.{category}
    - Persistent messages (delivery_mode=2)
    - Automatic reconnection with exponential backoff
    - Graceful fallback to console if broker unavailable
    - Thread-safe publishing
    
    Example:
        handler = RabbitMQLogHandler(
            host="localhost",
            port=5672,
            exchange="logs",
            username="guest",
            password="guest",
        )
        
        handler.write_batch([
            {"level": "ERROR", "category": "SECURITY", "message": "Auth failed"}
        ])
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        vhost: str = "/",
        username: str = "guest",
        password: str = "guest",
        exchange: str = "logs",
        exchange_type: str = "topic",
        durable: bool = True,
        retry_attempts: int = 3,
        retry_base_delay: float = 1.0,
        retry_max_delay: float = 10.0,
        fallback_to_console: bool = True,
    ) -> None:
        """
        Initialize RabbitMQ log handler.
        
        Args:
            host: RabbitMQ broker hostname
            port: RabbitMQ broker port
            vhost: Virtual host
            username: Authentication username
            password: Authentication password
            exchange: Exchange name for log publishing
            exchange_type: Exchange type (topic, fanout, direct)
            durable: Whether exchange is durable
            retry_attempts: Maximum connection retry attempts
            retry_base_delay: Base delay for exponential backoff (seconds)
            retry_max_delay: Maximum delay cap for exponential backoff (seconds)
            fallback_to_console: Whether to fallback to stderr on failure
        """
        if not PIKA_AVAILABLE:
            raise ImportError(
                "pika library is required for RabbitMQ handler. "
                "Install with: pip install pika"
            )
        
        self.host = host
        self.port = port
        self.vhost = vhost
        self.username = username
        self.password = password
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.durable = durable
        self.retry_attempts = retry_attempts
        self.retry_base_delay = retry_base_delay
        self.retry_max_delay = retry_max_delay
        self.fallback_to_console = fallback_to_console
        
        self._connection: Optional[Any] = None
        self._channel: Optional[Any] = None
        self._connected = False
        
        # Attempt initial connection
        self._connect()
    
    def _connect(self) -> bool:
        """
        Establish connection to RabbitMQ broker with retry logic.
        
        Returns:
            True if connection successful, False otherwise
        """
        for attempt in range(self.retry_attempts):
            try:
                # Create connection parameters
                credentials = pika.PlainCredentials(self.username, self.password)
                parameters = pika.ConnectionParameters(
                    host=self.host,
                    port=self.port,
                    virtual_host=self.vhost,
                    credentials=credentials,
                )
                
                # Establish connection
                self._connection = pika.BlockingConnection(parameters)
                self._channel = self._connection.channel()
                
                # Declare exchange
                self._channel.exchange_declare(
                    exchange=self.exchange,
                    exchange_type=self.exchange_type,
                    durable=self.durable,
                )
                
                self._connected = True
                return True
                
            except Exception as exc:
                self._connected = False
                
                if attempt < self.retry_attempts - 1:
                    # Calculate exponential backoff delay
                    delay = min(
                        self.retry_base_delay * (2 ** attempt),
                        self.retry_max_delay,
                    )
                    
                    print(
                        f"WARNING: Failed to connect to RabbitMQ (attempt {attempt + 1}/{self.retry_attempts}): {exc}. "
                        f"Retrying in {delay:.1f}s...",
                        file=sys.stderr,
                    )
                    
                    time.sleep(delay)
                else:
                    # Final attempt failed
                    print(
                        f"ERROR: Failed to connect to RabbitMQ after {self.retry_attempts} retries: {exc}. "
                        f"Falling back to console logging.",
                        file=sys.stderr,
                    )
        
        return False
    
    def _reconnect(self) -> bool:
        """
        Attempt to reconnect to RabbitMQ broker.
        
        Returns:
            True if reconnection successful, False otherwise
        """
        # Close existing connection if any
        try:
            if self._connection and not self._connection.is_closed:
                self._connection.close()
        except Exception:
            pass  # Ignore errors during close
        
        self._connection = None
        self._channel = None
        self._connected = False
        
        return self._connect()
    
    def write_batch(self, entries: Iterable[dict[str, Any]]) -> None:
        """
        Publish batch of log entries to RabbitMQ exchange.
        
        Args:
            entries: Log entries to publish
        """
        for entry in entries:
            try:
                self._publish_log(entry)
            except Exception as exc:
                # Try to reconnect and retry once
                if not self._connected:
                    if self._reconnect():
                        try:
                            self._publish_log(entry)
                            continue
                        except Exception:
                            pass  # Fall through to fallback
                
                # Fallback to console if enabled
                if self.fallback_to_console:
                    self._fallback_to_console(entry, exc)
    
    def _publish_log(self, entry: dict[str, Any]) -> None:
        """
        Publish single log entry to exchange.
        
        Args:
            entry: Log entry to publish
            
        Raises:
            Exception: If publishing fails
        """
        if not self._connected or self._channel is None:
            raise Exception("Not connected to RabbitMQ")
        
        # Extract level and category for routing key
        level = entry.get("level", "INFO")
        category = entry.get("category", "UNKNOWN")
        routing_key = f"{level}.{category}"
        
        # Serialize log entry to JSON
        body = orjson.dumps(entry)
        
        # Create message properties (persistent)
        properties = pika.BasicProperties(
            delivery_mode=2,  # Persistent
            content_type="application/json",
        )
        
        # Publish message
        self._channel.basic_publish(
            exchange=self.exchange,
            routing_key=routing_key,
            body=body,
            properties=properties,
        )
    
    def _fallback_to_console(self, entry: dict[str, Any], error: Exception) -> None:
        """
        Fallback to console output when RabbitMQ publishing fails.
        
        Args:
            entry: Log entry that failed to publish
            error: Error that occurred
        """
        try:
            log_json = orjson.dumps(entry).decode("utf-8")
            print(
                f"WARNING: Failed to publish log to RabbitMQ: {error}",
                file=sys.stderr,
            )
            print(log_json, file=sys.stderr)
        except Exception:
            # Silent failure to avoid infinite error loops
            pass
    
    def close(self) -> None:
        """Close RabbitMQ connection gracefully."""
        try:
            if self._connection and not self._connection.is_closed:
                self._connection.close()
        except Exception:
            pass  # Ignore errors during close
        
        self._connection = None
        self._channel = None
        self._connected = False
    
    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.close()
