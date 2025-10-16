"""Module providing synchronous and asynchronous Redis Streams utilities."""

import base64
import json
import logging
import time
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Dict, List, Optional, Union, Any, Callable
import redis
import asyncio
import redis.asyncio as redis_asyncio
from redis.exceptions import ConnectionError as RedisConnectionError, ResponseError


class RedisUtils:
    """Utility class for synchronous Redis operations."""

    def __init__(
        self, 
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        username: Optional[str] = None,
        db: int = 0,
        connection_timeout: int = 30
    ) -> None:
        """Initialize Redis utils with connection parameters.

        Args:
            host: Redis server hostname or IP address
            port: Redis server port
            password: Password for Redis authentication
            username: Username for Redis authentication (Redis 6.0+)
            db: Database number to connect to
            connection_timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.password = password
        self.username = username
        self.db = db
        self.connection_timeout = connection_timeout
        self.client = None
        self._streams = set()  # Set of stream names we're working with
        self._consumer_groups = {}  # Map of stream -> consumer group
        self._consumer_names = {}  # Map of stream -> consumer name
        
        # Metrics collection for performance monitoring
        self._metrics_lock = threading.Lock()
        self._metrics_log = deque(maxlen=10000)  # Keep last 10000 metrics entries
        self._pending_operations = {}  # Track pending operations for timing
        
        # Background metrics reporting
        self._metrics_reporting_config = None
        self._metrics_thread = None
        self._metrics_stop_event = threading.Event()
        self._last_metrics_reset = time.time()
        
        logging.info(
            "Initialized RedisUtils with host: %s:%d, db: %d",
            host, port, db
        )

    def _record_metric(self, operation: str, stream: str, start_time: float, end_time: float, 
                      success: bool, error_msg: str = None, message_key: str = None, 
                      message_size: int = None) -> None:
        """Record a performance metric for aggregation.
        
        Args:
            operation: Type of operation ('add' or 'read')
            stream: Redis stream name
            start_time: Operation start timestamp
            end_time: Operation end timestamp
            success: Whether operation was successful
            error_msg: Error message if operation failed
            message_key: Message key if available
            message_size: Message size in bytes if available
        """
        duration_ms = (end_time - start_time) * 1000  # Convert to milliseconds
        
        metric = {
            'timestamp': end_time,
            'operation': operation,
            'stream': stream,
            'duration_ms': duration_ms,
            'success': success,
            'error_msg': error_msg,
            'message_key': message_key,
            'message_size': message_size,
            'redis_host': f"{self.host}:{self.port}",
            'type': 'sync'
        }
        
        with self._metrics_lock:
            self._metrics_log.append(metric)
        
        # Log summary for monitoring
        status = "SUCCESS" if success else "FAILED"
        logging.info(
            "Redis %s %s: stream=%s, duration=%.2fms, key=%s, size=%s%s",
            operation.upper(), status, stream, duration_ms, message_key or 'None', 
            message_size or 'Unknown', f", error={error_msg}" if error_msg else ""
        )

    def get_metrics(self, clear_after_read: bool = False) -> List[Dict]:
        """Get collected metrics for aggregation and reporting.
        
        Args:
            clear_after_read: Whether to clear metrics after reading
            
        Returns:
            List of metric dictionaries
        """
        with self._metrics_lock:
            metrics = list(self._metrics_log)
            if clear_after_read:
                self._metrics_log.clear()
        
        return metrics

    def configure_metrics_reporting(self, 
                                   rpc_client,
                                   deployment_id: str = None,
                                   interval: int = 60,
                                   batch_size: int = 1000) -> None:
        """Configure background metrics reporting to backend API.
        
        Args:
            rpc_client: RPC client instance for API communication
            deployment_id: Deployment identifier for metrics context
            interval: Reporting interval in seconds (default: 60)
            batch_size: Maximum metrics per batch (default: 1000)
        """
        self._metrics_reporting_config = {
            'rpc_client': rpc_client,
            'deployment_id': deployment_id,
            'interval': interval,
            'batch_size': batch_size,
            'enabled': True
        }
        
        # Start background reporting thread
        if not self._metrics_thread or not self._metrics_thread.is_alive():
            self._metrics_stop_event.clear()
            self._metrics_thread = threading.Thread(
                target=self._metrics_reporter_worker,
                daemon=True,
                name=f"redis-metrics-reporter-{id(self)}"
            )
            self._metrics_thread.start()
            logging.info("Started background Redis metrics reporting thread")

    def _metrics_reporter_worker(self) -> None:
        """Background thread worker for sending metrics to backend API."""
        logging.info("Redis metrics reporter thread started")
        
        while not self._metrics_stop_event.is_set():
            try:
                if not self._metrics_reporting_config or not self._metrics_reporting_config.get('enabled'):
                    self._metrics_stop_event.wait(10)  # Check every 10 seconds if disabled
                    continue
                
                interval = self._metrics_reporting_config.get('interval', 60)
                
                # Wait for the specified interval or stop event
                if self._metrics_stop_event.wait(interval):
                    break  # Stop event was set
                
                # Collect and send metrics
                self._collect_and_send_metrics()
                
            except Exception as exc:
                logging.error(f"Error in Redis metrics reporter thread: {exc}")
                # Wait before retrying to avoid rapid failure loops
                self._metrics_stop_event.wait(30)
        
        logging.info("Redis metrics reporter thread stopped")

    def _collect_and_send_metrics(self) -> None:
        """Collect metrics and send them to the backend API."""
        try:
            # Get metrics since last collection
            raw_metrics = self.get_metrics(clear_after_read=True)
            
            if not raw_metrics:
                logging.debug("No new Redis metrics to report")
                return
            
            # Aggregate metrics by stream for API format
            aggregated_data = self._aggregate_metrics_for_api(raw_metrics)
            
            if aggregated_data.get('stream'):
                # Send to backend API
                success = self._send_metrics_to_api(aggregated_data)
                if success:
                    logging.info(f"Successfully sent {len(raw_metrics)} Redis metrics to backend API")
                else:
                    logging.warning("Failed to send Redis metrics to backend API")
            else:
                logging.debug("No stream-level metrics to report")
                
        except Exception as exc:
            logging.error(f"Error collecting and sending Redis metrics: {exc}")

    def _aggregate_metrics_for_api(self, raw_metrics: List[Dict]) -> Dict:
        """Aggregate raw metrics into the API format expected by backend.
        
        Args:
            raw_metrics: List of raw metric dictionaries
            
        Returns:
            Aggregated metrics in API format
        """
        # Group metrics by stream
        stream_stats = {}
        current_time = datetime.now(timezone.utc).isoformat()
        
        for metric in raw_metrics:
            stream = metric.get('stream', 'unknown')
            operation = metric.get('operation', 'unknown')
            success = metric.get('success', False)
            duration_ms = metric.get('duration_ms', 0)
            
            # Skip timeout and error entries for aggregation
            if stream in ['(timeout)', '(error)', 'unknown']:
                continue
            
            if stream not in stream_stats:
                stream_stats[stream] = {
                    'stream': stream,
                    'addCount': 0,
                    'readCount': 0,
                    'totalLatency': 0,
                    'latencies': [],  # Temporary for calculations
                    'avgLatency': 0,
                    'minlatency': float('inf'),
                    'maxlatency': 0
                }
            
            stats = stream_stats[stream]
            
            # Count operations by type
            if operation == 'add' and success:
                stats['addCount'] += 1
            elif operation in ['read', 'get_message'] and success:
                stats['readCount'] += 1
            
            # Track latencies (convert ms to nanoseconds for API compatibility)
            if success and duration_ms > 0:
                latency_ns = int(duration_ms * 1_000_000)  # Convert ms to ns
                stats['latencies'].append(latency_ns)
                stats['totalLatency'] += latency_ns
                stats['minlatency'] = min(stats['minlatency'], latency_ns)
                stats['maxlatency'] = max(stats['maxlatency'], latency_ns)
        
        # Calculate averages and clean up
        for stream, stats in stream_stats.items():
            if stats['latencies']:
                stats['avgLatency'] = stats['totalLatency'] // len(stats['latencies'])
            else:
                stats['avgLatency'] = 0
                stats['minlatency'] = 0
            
            # Remove temporary latencies list
            del stats['latencies']
        
        # Format for API
        api_payload = {
            'stream': list(stream_stats.values()),
            'status': 'success',
            'host': self.host,
            'port': str(self.port),
            'createdAt': current_time,
            'updatedAt': current_time
        }
        
        return api_payload

    def _send_metrics_to_api(self, aggregated_metrics: Dict) -> bool:
        """Send aggregated metrics to backend API using RPC client.
        
        Args:
            aggregated_metrics: Metrics data in API format
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            rpc_client = self._metrics_reporting_config.get('rpc_client')
            if not rpc_client:
                logging.error("No RPC client configured for Redis metrics reporting")
                return False
            
            # Send POST request to the Redis metrics endpoint
            response = rpc_client.post(
                path="/v1/monitoring/add_redis_metrics",
                payload=aggregated_metrics,
                timeout=30
            )
            
            # Check response following existing RPC patterns
            if response and response.get("success"):
                logging.debug("Successfully sent Redis metrics to backend API")
                return True
            else:
                error_msg = response.get('message', 'Unknown error') if response else 'No response'
                logging.error(f"Backend API rejected Redis metrics: {error_msg}")
                return False
                
        except Exception as exc:
            logging.error(f"Error sending Redis metrics to API: {exc}")
            return False

    def stop_metrics_reporting(self) -> None:
        """Stop the background metrics reporting thread."""
        if self._metrics_reporting_config:
            self._metrics_reporting_config['enabled'] = False
        
        if self._metrics_thread and self._metrics_thread.is_alive():
            logging.info("Stopping Redis metrics reporting thread...")
            self._metrics_stop_event.set()
            self._metrics_thread.join(timeout=5)
            if self._metrics_thread.is_alive():
                logging.warning("Redis metrics reporting thread did not stop gracefully")
            else:
                logging.info("Redis metrics reporting thread stopped")

    def setup_client(self, **kwargs) -> None:
        """Set up Redis client connection.

        Args:
            **kwargs: Additional Redis client configuration options

        Raises:
            RedisConnectionError: If client initialization fails
        """
        client_config = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "socket_timeout": self.connection_timeout,
            "socket_connect_timeout": self.connection_timeout,
            "retry_on_timeout": True,
            "health_check_interval": 30,
            "decode_responses": False,  # Keep bytes for compatibility
        }
        
        # Add authentication if configured
        if self.password:
            client_config["password"] = self.password
        if self.username:
            client_config["username"] = self.username
        
        # Override with any additional config
        client_config.update(kwargs)
        
        try:
            self.client = redis.Redis(**client_config)
            # Test connection
            self.client.ping()
            logging.info("Successfully set up Redis client")
        except Exception as exc:
            error_msg = f"Failed to initialize Redis client: {str(exc)}"
            logging.error(error_msg)
            raise RedisConnectionError(error_msg)

    def setup_stream(self, stream_name: str, consumer_group: str, consumer_name: str = None) -> None:
        """Set up Redis stream with consumer group.

        Args:
            stream_name: Name of the Redis stream
            consumer_group: Name of the consumer group
            consumer_name: Name of the consumer (defaults to hostname-timestamp)

        Raises:
            RedisConnectionError: If stream setup fails
        """
        if not self.client:
            self.setup_client()
        
        try:
            # Ensure all parameters are strings, not bytes
            stream_name = self._safe_decode(stream_name)
            consumer_group = self._safe_decode(consumer_group)
            
            # Generate default consumer name if not provided
            if not consumer_name:
                consumer_name = f"consumer-{int(time.time())}-{threading.current_thread().ident}"
            else:
                consumer_name = self._safe_decode(consumer_name)
            
            # Create consumer group if it doesn't exist
            try:
                self.client.xgroup_create(stream_name, consumer_group, id='0', mkstream=True)
                logging.info(f"Created consumer group '{consumer_group}' for stream '{stream_name}'")
            except ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logging.debug(f"Consumer group '{consumer_group}' already exists for stream '{stream_name}'")
                else:
                    raise
            
            # Store stream configuration (ensure all are strings)
            self._streams.add(stream_name)
            self._consumer_groups[stream_name] = consumer_group
            self._consumer_names[stream_name] = consumer_name
            
            logging.info(f"Successfully set up Redis stream '{stream_name}' with consumer group '{consumer_group}'")
        except Exception as exc:
            error_msg = f"Failed to set up Redis stream: {str(exc)}"
            logging.error(error_msg)
            raise RedisConnectionError(error_msg)

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize message value to bytes.
        
        Args:
            value: Message value to serialize
            
        Returns:
            Serialized value as bytes
        """
        if isinstance(value, dict):
            return json.dumps(value).encode('utf-8')
        elif isinstance(value, str):
            return value.encode('utf-8')
        elif isinstance(value, bytes):
            return value
        else:
            return str(value).encode('utf-8')

    def _safe_decode(self, value: Union[str, bytes]) -> str:
        """Safely decode bytes to string, handling both str and bytes input.
        
        Args:
            value: Value to decode (str or bytes)
            
        Returns:
            Decoded string
        """
        if isinstance(value, bytes):
            return value.decode('utf-8')
        elif isinstance(value, str):
            return value
        else:
            return str(value)

    def add_message(
        self,
        stream_name: str,
        message: Union[dict, str, bytes, Any],
        message_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> str:
        """Add message to Redis stream.

        Args:
            stream_name: Stream to add message to
            message: Message to add (dict will be converted to fields)
            message_key: Optional message key for routing
            timeout: Maximum time to wait for add completion in seconds

        Returns:
            Message ID assigned by Redis

        Raises:
            RuntimeError: If client is not set up
            RedisConnectionError: If message addition fails
            ValueError: If stream_name is empty or message is None
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized. Call setup_client() first")
        if not stream_name or message is None:
            raise ValueError("Stream name and message must be provided")
        
        # Ensure stream_name is always a string
        stream_name = self._safe_decode(stream_name)
        
        # Ensure message_key is always a string if provided
        if message_key is not None:
            message_key = self._safe_decode(message_key)

        # Prepare message fields for Redis stream
        if isinstance(message, dict):
            fields = {}
            for k, v in message.items():
                # Ensure both keys and values are strings
                key_str = self._safe_decode(k)
                if isinstance(v, (dict, list)):
                    fields[key_str] = json.dumps(v)
                elif isinstance(v, bytes):
                    try:
                        fields[key_str] = v.decode('utf-8')
                    except UnicodeDecodeError:
                        # If bytes can't be decoded as UTF-8, encode as base64
                        fields[key_str] = base64.b64encode(v).decode('ascii')
                        fields[f'{key_str}_encoding'] = 'base64'
                else:
                    fields[key_str] = str(v)
            # Add message key if provided
            if message_key:
                fields['_message_key'] = message_key
        else:
            # For non-dict messages, handle different types
            if isinstance(message, bytes):
                try:
                    data_str = message.decode('utf-8')
                except UnicodeDecodeError:
                    # If bytes can't be decoded as UTF-8, encode as base64
                    data_str = base64.b64encode(message).decode('ascii')
                    fields = {'data': data_str, 'data_encoding': 'base64'}
                else:
                    fields = {'data': data_str}
            else:
                fields = {'data': str(message)}
            
            if message_key:
                fields['_message_key'] = message_key

        message_size = sum(len(str(k)) + len(str(v)) for k, v in fields.items())

        start_time = time.time()
        try:
            # Redis XADD returns the message ID
            message_id = self.client.xadd(stream_name, fields)
            end_time = time.time()
            
            # Record successful add metrics
            self._record_metric(
                operation="add",
                stream=stream_name,
                start_time=start_time,
                end_time=end_time,
                success=True,
                error_msg=None,
                message_key=message_key,
                message_size=message_size
            )
            
            logging.debug(
                "Successfully added message to stream: %s, ID: %s",
                stream_name, message_id
            )
            return self._safe_decode(message_id)
            
        except Exception as exc:
            end_time = time.time()
            error_msg = f"Failed to add message: {str(exc)}"
            logging.error(error_msg, exc_info=True)
            
            # Record failed add metrics
            self._record_metric(
                operation="add",
                stream=stream_name,
                start_time=start_time,
                end_time=end_time,
                success=False,
                error_msg=error_msg,
                message_key=message_key,
                message_size=message_size
            )
            raise RedisConnectionError(error_msg)

    def subscribe_to_stream(
        self, 
        stream_name: str,
        consumer_group: str,
        consumer_name: str = None
    ) -> None:
        """Subscribe to a Redis stream (alias for setup_stream for compatibility).

        Args:
            stream_name: Stream to subscribe to
            consumer_group: Consumer group name
            consumer_name: Consumer name (optional)

        Raises:
            RedisConnectionError: If stream setup fails
            ValueError: If stream_name is empty
        """
        if not stream_name:
            raise ValueError("Stream name must be provided")

        # This is just an alias for setup_stream for compatibility
        self.setup_stream(stream_name, consumer_group, consumer_name)

    def unsubscribe_from_stream(self, stream_name: str) -> None:
        """Remove stream from local tracking (consumer group remains on Redis).

        Args:
            stream_name: Stream to unsubscribe from
        """
        try:
            # Ensure stream_name is a string
            stream_name = self._safe_decode(stream_name)
            self._streams.discard(stream_name)
            self._consumer_groups.pop(stream_name, None)
            self._consumer_names.pop(stream_name, None)
            logging.info("Successfully unsubscribed from stream: %s", stream_name)
        except Exception as exc:
            logging.error("Failed to unsubscribe from stream %s: %s", stream_name, str(exc))

    def _parse_message_value(self, value: bytes) -> Any:
        """Parse message value from bytes.
        
        Args:
            value: Message value in bytes
            
        Returns:
            Parsed value or original bytes if parsing fails
        """
        if not value:
            return None

        try:
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return value

    def get_message(self, stream_name: str = None, timeout: float = 1.0) -> Optional[Dict]:
        """Get a single message from Redis stream.

        Args:
            stream_name: Stream to read from (if None, reads from all configured streams)
            timeout: Maximum time to block waiting for message in seconds

        Returns:
            Message dict if available, None if timeout. Dict contains:
                - stream: Stream name
                - message_id: Message ID from Redis
                - data: Parsed message data
                - fields: Raw fields dictionary

        Raises:
            RuntimeError: If no streams are configured
            RedisConnectionError: If message retrieval fails
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized. Call setup_client() first")
        
        # Determine which streams to read from
        if stream_name:
            if stream_name not in self._consumer_groups:
                raise RuntimeError(f"Stream '{stream_name}' not set up. Call setup_stream() first")
            streams_to_read = [stream_name]
        else:
            streams_to_read = list(self._streams)
            if not streams_to_read:
                raise RuntimeError("No streams configured. Call setup_stream() first")
        
        start_time = time.time()
        try:
            # Build streams dictionary for XREADGROUP
            streams_dict = {}
            # For multi-stream setups, we'll use the first stream's consumer group/name
            # This is a limitation of Redis XREADGROUP when reading from multiple streams
            first_stream = streams_to_read[0]
            primary_consumer_group = self._consumer_groups[first_stream]
            primary_consumer_name = self._consumer_names[first_stream]
            
            for stream in streams_to_read:
                # Ensure stream names are strings, not bytes
                stream_str = self._safe_decode(stream)
                streams_dict[stream_str] = '>'  # Read new messages
            
            # Use XREADGROUP to read from streams
            timeout_ms = int(timeout * 1000) if timeout > 0 else 0
            
            result = self.client.xreadgroup(
                groupname=self._safe_decode(primary_consumer_group),
                consumername=self._safe_decode(primary_consumer_name),
                streams=streams_dict,
                count=1,
                block=timeout_ms
            )
            
            end_time = time.time()
            
            if not result:
                # Record timeout as successful operation with no message
                self._record_metric(
                    operation="read",
                    stream="(timeout)",
                    start_time=start_time,
                    end_time=end_time,
                    success=True,
                    error_msg=None,
                    message_key=None,
                    message_size=None
                )
                return None
            
            # Extract the first message from the result
            stream_name, messages = result[0]
            if not messages:
                return None
            
            # Decode stream_name and message_id to strings immediately
            stream_name = self._safe_decode(stream_name)
            message_id, fields = messages[0]
            message_id = self._safe_decode(message_id)
            
            # Parse fields into structured data
            parsed_data = {}
            message_key = None
            total_size = 0
            
            for field_name, field_value in fields.items():
                field_name = self._safe_decode(field_name)
                field_value = self._safe_decode(field_value)
                total_size += len(field_name) + len(field_value)

                if field_name == '_message_key':
                    message_key = field_value
                    continue

                # Try to parse JSON values
                try:
                    parsed_data[field_name] = json.loads(field_value)
                except (json.JSONDecodeError, ValueError):
                    parsed_data[field_name] = field_value
            
            # Record successful message retrieval metrics
            self._record_metric(
                operation="read",
                stream=stream_name,  # Already decoded
                start_time=start_time,
                end_time=end_time,
                success=True,
                error_msg=None,
                message_key=message_key,
                message_size=total_size
            )
            
            # Acknowledge the message
            try:
                consumer_group = self._consumer_groups[stream_name]
                self.client.xack(stream_name, consumer_group, message_id)
            except Exception as ack_exc:
                logging.warning("Failed to acknowledge message: %s", str(ack_exc))
            
            result = {
                "stream": stream_name,  # Already decoded
                "message_id": message_id,  # Already decoded
                "data": parsed_data,
                "fields": {self._safe_decode(k): self._safe_decode(v) for k, v in fields.items()},
                "message_key": message_key
            }
            return result
            
        except Exception as exc:
            end_time = time.time()
            error_msg = f"Failed to get message: {str(exc)}"
            logging.error(error_msg)
            
            # Record error metrics
            self._record_metric(
                operation="read",
                stream="(error)",
                start_time=start_time,
                end_time=end_time,
                success=False,
                error_msg=error_msg,
                message_key=None,
                message_size=None
            )
            raise RedisConnectionError(error_msg)

    def listen_for_messages(self, callback: Optional[Callable] = None, stream_name: str = None) -> None:
        """Listen for messages on configured streams (blocking).

        Args:
            callback: Optional callback function for all messages
            stream_name: Optional specific stream to listen to (listens to all if None)

        Raises:
            RuntimeError: If no streams are configured
            RedisConnectionError: If listening fails
        """
        if not self._streams:
            raise RuntimeError("No streams configured. Call setup_stream() first")

        try:
            logging.info("Starting to listen for Redis stream messages...")
            while True:
                try:
                    message = self.get_message(stream_name=stream_name, timeout=5.0)
                    if message:
                        # Execute callback
                        if callback:
                            try:
                                callback(message)
                            except Exception as callback_exc:
                                logging.error("Error in stream callback: %s", str(callback_exc))
                except RedisConnectionError as exc:
                    logging.error("Redis connection error while listening: %s", str(exc))
                    # Sleep briefly before retrying
                    time.sleep(1.0)
                except Exception as exc:
                    logging.error("Unexpected error while listening: %s", str(exc))
                    time.sleep(1.0)
                            
        except KeyboardInterrupt:
            logging.info("Stopped listening for Redis stream messages")
        except Exception as exc:
            error_msg = f"Error listening for messages: {str(exc)}"
            logging.error(error_msg)
            raise RedisConnectionError(error_msg)

    def close(self) -> None:
        """Close Redis client connections."""
        try:
            # Stop metrics reporting thread first
            self.stop_metrics_reporting()
            
            # Clear stream tracking
            if self._streams:
                try:
                    self._streams.clear()
                    self._consumer_groups.clear()
                    self._consumer_names.clear()
                    logging.debug("Cleared stream tracking")
                except Exception as exc:
                    logging.warning("Error clearing stream tracking: %s", str(exc))
                
            if self.client:
                try:
                    self.client.close()
                except Exception as exc:
                    logging.warning("Error closing Redis client: %s", str(exc))
                self.client = None
                
            logging.info("Closed Redis connections")
        except Exception as exc:
            logging.error("Error closing Redis connections: %s", str(exc))
            raise


class AsyncRedisUtils:
    """Utility class for asynchronous Redis Streams operations."""

    def __init__(
        self, 
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        username: Optional[str] = None,
        db: int = 0,
        connection_timeout: int = 30
    ) -> None:
        """Initialize async Redis utils with connection parameters.
        
        Args:
            host: Redis server hostname or IP address
            port: Redis server port
            password: Password for Redis authentication
            username: Username for Redis authentication (Redis 6.0+)
            db: Database number to connect to
            connection_timeout: Connection timeout in seconds
        """
        self.host = host
        self.port = port
        self.password = password
        self.username = username
        self.db = db
        self.connection_timeout = connection_timeout
        self.client: Optional[redis_asyncio.Redis] = None
        self._streams = set()  # Set of stream names we're working with
        self._consumer_groups = {}  # Map of stream -> consumer group
        self._consumer_names = {}  # Map of stream -> consumer name
        
        # Metrics collection for performance monitoring (async-safe)
        self._metrics_log = deque(maxlen=10000)  # Keep last 10000 metrics entries
        self._metrics_lock = threading.Lock()
        self._pending_operations = {}  # Track pending async operations for timing
        
        # Background metrics reporting (shared with sync version)
        self._metrics_reporting_config = None
        self._metrics_thread = None
        self._metrics_stop_event = threading.Event()
        
        logging.info("Initialized AsyncRedisUtils with host: %s:%d, db: %d", host, port, db)

    def _record_metric(self, operation: str, stream: str, start_time: float, end_time: float, 
                      success: bool, error_msg: str = None, message_key: str = None, 
                      message_size: int = None) -> None:
        """Record a performance metric for aggregation.
        
        Args:
            operation: Type of operation ('add' or 'read')
            stream: Redis stream name
            start_time: Operation start timestamp
            end_time: Operation end timestamp
            success: Whether operation was successful
            error_msg: Error message if operation failed
            message_key: Message key if available
            message_size: Message size in bytes if available
        """
        duration_ms = (end_time - start_time) * 1000  # Convert to milliseconds
        
        metric = {
            'timestamp': end_time,
            'operation': operation,
            'stream': stream,
            'duration_ms': duration_ms,
            'success': success,
            'error_msg': error_msg,
            'message_key': message_key,
            'message_size': message_size,
            'redis_host': f"{self.host}:{self.port}",
            'type': 'async'
        }
        
        # Protect with lock to coordinate with background reporter thread
        try:
            self._metrics_lock.acquire()
            self._metrics_log.append(metric)
        finally:
            self._metrics_lock.release()
        
        # Log summary for monitoring
        status = "SUCCESS" if success else "FAILED"
        logging.info(
            "Async Redis %s %s: stream=%s, duration=%.2fms, key=%s, size=%s%s",
            operation.upper(), status, stream, duration_ms, message_key or 'None', 
            message_size or 'Unknown', f", error={error_msg}" if error_msg else ""
        )

    def get_metrics(self, clear_after_read: bool = False) -> List[Dict]:
        """Get collected metrics for aggregation and reporting.
        
        Args:
            clear_after_read: Whether to clear metrics after reading
            
        Returns:
            List of metric dictionaries
        """
        try:
            self._metrics_lock.acquire()
            metrics = list(self._metrics_log)
            if clear_after_read:
                self._metrics_log.clear()
        finally:
            self._metrics_lock.release()
        
        return metrics

    def configure_metrics_reporting(self, 
                                   rpc_client,
                                   deployment_id: str = None,
                                   interval: int = 60,
                                   batch_size: int = 1000) -> None:
        """Configure background metrics reporting to backend API.
        
        Args:
            rpc_client: RPC client instance for API communication
            deployment_id: Deployment identifier for metrics context
            interval: Reporting interval in seconds (default: 60)
            batch_size: Maximum metrics per batch (default: 1000)
        """
        self._metrics_reporting_config = {
            'rpc_client': rpc_client,
            'deployment_id': deployment_id,
            'interval': interval,
            'batch_size': batch_size,
            'enabled': True
        }
        
        # Start background reporting thread (reuse sync implementation)
        if not self._metrics_thread or not self._metrics_thread.is_alive():
            self._metrics_stop_event.clear()
            self._metrics_thread = threading.Thread(
                target=self._metrics_reporter_worker,
                daemon=True,
                name=f"async-redis-metrics-reporter-{id(self)}"
            )
            self._metrics_thread.start()
            logging.info("Started background async Redis metrics reporting thread")

    def _metrics_reporter_worker(self) -> None:
        """Background thread worker for sending metrics to backend API (async version)."""
        logging.info("Async Redis metrics reporter thread started")
        
        while not self._metrics_stop_event.is_set():
            try:
                if not self._metrics_reporting_config or not self._metrics_reporting_config.get('enabled'):
                    self._metrics_stop_event.wait(10)
                    continue
                
                interval = self._metrics_reporting_config.get('interval', 60)
                
                if self._metrics_stop_event.wait(interval):
                    break
                
                self._collect_and_send_metrics()
                
            except Exception as exc:
                logging.error(f"Error in async Redis metrics reporter thread: {exc}")
                self._metrics_stop_event.wait(30)
        
        logging.info("Async Redis metrics reporter thread stopped")

    def _collect_and_send_metrics(self) -> None:
        """Collect metrics and send them to the backend API (async version)."""
        try:
            raw_metrics = self.get_metrics(clear_after_read=True)
            
            if not raw_metrics:
                logging.debug("No new async Redis metrics to report")
                return
            
            aggregated_data = self._aggregate_metrics_for_api(raw_metrics)
            
            if aggregated_data.get('stream'):
                success = self._send_metrics_to_api(aggregated_data)
                if success:
                    logging.info(f"Successfully sent {len(raw_metrics)} async Redis metrics to backend API")
                else:
                    logging.warning("Failed to send async Redis metrics to backend API")
            else:
                logging.debug("No async stream-level metrics to report")
                
        except Exception as exc:
            logging.error(f"Error collecting and sending async Redis metrics: {exc}")

    def _aggregate_metrics_for_api(self, raw_metrics: List[Dict]) -> Dict:
        """Aggregate raw metrics into the API format expected by backend (async version)."""
        stream_stats = {}
        current_time = datetime.now(timezone.utc).isoformat()
        
        for metric in raw_metrics:
            stream = metric.get('stream', 'unknown')
            operation = metric.get('operation', 'unknown')
            success = metric.get('success', False)
            duration_ms = metric.get('duration_ms', 0)
            
            if stream in ['(timeout)', '(error)', 'unknown']:
                continue
            
            if stream not in stream_stats:
                stream_stats[stream] = {
                    'stream': stream,
                    'addCount': 0,
                    'readCount': 0,
                    'totalLatency': 0,
                    'latencies': [],
                    'avgLatency': 0,
                    'minlatency': float('inf'),
                    'maxlatency': 0
                }
            
            stats = stream_stats[stream]
            
            if operation == 'add' and success:
                stats['addCount'] += 1
            elif operation in ['read', 'get_message'] and success:
                stats['readCount'] += 1
            
            if success and duration_ms > 0:
                latency_ns = int(duration_ms * 1_000_000)
                stats['latencies'].append(latency_ns)
                stats['totalLatency'] += latency_ns
                stats['minlatency'] = min(stats['minlatency'], latency_ns)
                stats['maxlatency'] = max(stats['maxlatency'], latency_ns)
        
        for stream, stats in stream_stats.items():
            if stats['latencies']:
                stats['avgLatency'] = stats['totalLatency'] // len(stats['latencies'])
            else:
                stats['avgLatency'] = 0
                stats['minlatency'] = 0
            del stats['latencies']
        
        payload = {
            'stream': list(stream_stats.values()),
            'status': 'success',
            'host': self.host,
            'port': str(self.port),
            'createdAt': current_time,
            'updatedAt': current_time
        }

        return payload

    def _send_metrics_to_api(self, aggregated_metrics: Dict) -> bool:
        """Send aggregated metrics to backend API using RPC client (async version)."""
        try:
            rpc_client = self._metrics_reporting_config.get('rpc_client')
            if not rpc_client:
                logging.error("No RPC client configured for async Redis metrics reporting")
                return False
            
            response = rpc_client.post(
                path="/v1/monitoring/add_redis_metrics",
                payload=aggregated_metrics,
                timeout=30
            )
            
            if response and response.get("success"):
                logging.debug("Successfully sent async Redis metrics to backend API")
                return True
            else:
                error_msg = response.get('message', 'Unknown error') if response else 'No response'
                logging.error(f"Backend API rejected async Redis metrics: {error_msg}")
                return False
                
        except Exception as exc:
            logging.error(f"Error sending async Redis metrics to API: {exc}")
            return False

    def stop_metrics_reporting(self) -> None:
        """Stop the background metrics reporting thread (async version)."""
        if self._metrics_reporting_config:
            self._metrics_reporting_config['enabled'] = False
        
        if self._metrics_thread and self._metrics_thread.is_alive():
            logging.info("Stopping async Redis metrics reporting thread...")
            self._metrics_stop_event.set()
            self._metrics_thread.join(timeout=5)
            if self._metrics_thread.is_alive():
                logging.warning("Async Redis metrics reporting thread did not stop gracefully")
            else:
                logging.info("Async Redis metrics reporting thread stopped")

    def _safe_decode(self, value: Union[str, bytes]) -> str:
        """Safely decode bytes to string, handling both str and bytes input.
        
        Args:
            value: Value to decode (str or bytes)
            
        Returns:
            Decoded string
        """
        if isinstance(value, bytes):
            return value.decode('utf-8')
        elif isinstance(value, str):
            return value
        else:
            return str(value)

    async def setup_client(self, **kwargs) -> None:
        """Set up async Redis client connection.
        
        Args:
            **kwargs: Additional Redis client configuration options
            
        Raises:
            RedisConnectionError: If client initialization fails
        """
        client_config = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "socket_timeout": self.connection_timeout,
            "socket_connect_timeout": self.connection_timeout,
            "retry_on_timeout": True,
            "health_check_interval": 30,
            "decode_responses": False,  # Keep bytes for compatibility
        }
        
        # Add authentication if configured
        if self.password:
            client_config["password"] = self.password
        if self.username:
            client_config["username"] = self.username
        
        # Override with any additional config
        client_config.update(kwargs)
        
        # Close existing client if any
        if self.client:
            try:
                await self.client.close()
            except Exception:
                pass  # Ignore errors during cleanup
                
        try:
            self.client = redis_asyncio.Redis(**client_config)
            # Test connection
            await self.client.ping()
            logging.info("Successfully set up async Redis client")
        except Exception as exc:
            error_msg = f"Failed to initialize async Redis client: {str(exc)}"
            logging.error(error_msg)
            # Clean up on failure
            self.client = None
            raise RedisConnectionError(error_msg)

    async def setup_stream(self, stream_name: str, consumer_group: str, consumer_name: str = None) -> None:
        """Set up Redis stream with consumer group asynchronously.

        Args:
            stream_name: Name of the Redis stream
            consumer_group: Name of the consumer group
            consumer_name: Name of the consumer (defaults to hostname-timestamp)

        Raises:
            RedisConnectionError: If stream setup fails
        """
        if not self.client:
            await self.setup_client()
        
        try:
            # Ensure all parameters are strings, not bytes
            stream_name = self._safe_decode(stream_name)
            consumer_group = self._safe_decode(consumer_group)
            
            # Generate default consumer name if not provided
            if not consumer_name:
                import threading
                consumer_name = f"async-consumer-{int(time.time())}-{threading.current_thread().ident}"
            else:
                consumer_name = self._safe_decode(consumer_name)
            
            # Create consumer group if it doesn't exist
            try:
                await self.client.xgroup_create(stream_name, consumer_group, id='0', mkstream=True)
                logging.info(f"Created async consumer group '{consumer_group}' for stream '{stream_name}'")
            except Exception as e:
                error_str = str(e)
                if "BUSYGROUP" in error_str:
                    logging.debug(f"Async consumer group '{consumer_group}' already exists for stream '{stream_name}'")
                else:
                    raise
            
            # Store stream configuration (ensure all are strings)
            self._streams.add(stream_name)
            self._consumer_groups[stream_name] = consumer_group
            self._consumer_names[stream_name] = consumer_name
            
            logging.info(f"Successfully set up async Redis stream '{stream_name}' with consumer group '{consumer_group}'")
        except Exception as exc:
            error_msg = f"Failed to set up async Redis stream: {str(exc)}"
            logging.error(error_msg)
            raise RedisConnectionError(error_msg)

    def _serialize_value(self, value: Any) -> bytes:
        """Serialize message value to bytes.
        
        Args:
            value: Message value to serialize
            
        Returns:
            Serialized value as bytes
        """
        if isinstance(value, dict):
            return json.dumps(value).encode('utf-8')
        elif isinstance(value, str):
            return value.encode('utf-8')
        elif isinstance(value, bytes):
            return value
        else:
            return str(value).encode('utf-8')

    async def add_message(
        self,
        stream_name: str,
        message: Union[dict, str, bytes, Any],
        message_key: Optional[str] = None,
        timeout: float = 30.0,
    ) -> str:
        """Add message to Redis stream asynchronously.
        
        Args:
            stream_name: Stream to add message to
            message: Message to add (dict will be converted to fields)
            message_key: Optional message key for routing
            timeout: Maximum time to wait for add completion in seconds
            
        Returns:
            Message ID assigned by Redis
            
        Raises:
            RuntimeError: If client is not initialized
            ValueError: If stream_name or message is invalid
            RedisConnectionError: If message addition fails
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized. Call setup_client() first.")
        if not stream_name or message is None:
            raise ValueError("Stream name and message must be provided")
        
        # Ensure stream_name is always a string
        stream_name = self._safe_decode(stream_name)
        
        # Ensure message_key is always a string if provided
        if message_key is not None:
            message_key = self._safe_decode(message_key)
            
        # Prepare message fields for Redis stream
        if isinstance(message, dict):
            fields = {}
            for k, v in message.items():
                # Ensure both keys and values are strings
                key_str = self._safe_decode(k)
                if isinstance(v, (dict, list)):
                    fields[key_str] = json.dumps(v)
                elif isinstance(v, bytes):
                    try:
                        fields[key_str] = v.decode('utf-8')
                    except UnicodeDecodeError:
                        # If bytes can't be decoded as UTF-8, encode as base64
                        fields[key_str] = base64.b64encode(v).decode('ascii')
                        fields[f'{key_str}_encoding'] = 'base64'
                else:
                    fields[key_str] = str(v)
            # Add message key if provided
            if message_key:
                fields['_message_key'] = message_key
        else:
            # For non-dict messages, handle different types
            if isinstance(message, bytes):
                try:
                    data_str = message.decode('utf-8')
                except UnicodeDecodeError:
                    # If bytes can't be decoded as UTF-8, encode as base64
                    data_str = base64.b64encode(message).decode('ascii')
                    fields = {'data': data_str, 'data_encoding': 'base64'}
                else:
                    fields = {'data': data_str}
            else:
                fields = {'data': str(message)}
            
            if message_key:
                fields['_message_key'] = message_key

        message_size = sum(len(str(k)) + len(str(v)) for k, v in fields.items())
        
        start_time = time.time()
        try:
            # Redis XADD returns the message ID
            message_id = await self.client.xadd(stream_name, fields)
            end_time = time.time()
            
            # Record successful add metrics
            self._record_metric(
                operation="add",
                stream=stream_name,
                start_time=start_time,
                end_time=end_time,
                success=True,
                error_msg=None,
                message_key=message_key,
                message_size=message_size
            )
            
            logging.debug("Successfully added async message to stream: %s, ID: %s", stream_name, message_id)
            return self._safe_decode(message_id)
        except Exception as exc:
            end_time = time.time()
            error_msg = f"Failed to add async message: {str(exc)}"
            logging.error(error_msg, exc_info=True)
            
            # Record failed add metrics
            self._record_metric(
                operation="add",
                stream=stream_name,
                start_time=start_time,
                end_time=end_time,
                success=False,
                error_msg=error_msg,
                message_key=message_key,
                message_size=message_size
            )
            raise RedisConnectionError(error_msg)

    async def subscribe_to_stream(
        self, 
        stream_name: str,
        consumer_group: str,
        consumer_name: str = None
    ) -> None:
        """Subscribe to a Redis stream asynchronously (alias for setup_stream for compatibility).

        Args:
            stream_name: Stream to subscribe to
            consumer_group: Consumer group name
            consumer_name: Consumer name (optional)

        Raises:
            RedisConnectionError: If stream setup fails
            ValueError: If stream_name is empty
        """
        if not stream_name:
            raise ValueError("Stream name must be provided")

        # This is just an alias for setup_stream for compatibility
        await self.setup_stream(stream_name, consumer_group, consumer_name)

    async def unsubscribe_from_stream(self, stream_name: str) -> None:
        """Remove stream from local tracking asynchronously (consumer group remains on Redis).

        Args:
            stream_name: Stream to unsubscribe from
        """
        try:
            # Ensure stream_name is a string
            stream_name = self._safe_decode(stream_name)
            self._streams.discard(stream_name)
            self._consumer_groups.pop(stream_name, None)
            self._consumer_names.pop(stream_name, None)
            logging.info("Successfully unsubscribed from async stream: %s", stream_name)
        except Exception as exc:
            logging.error("Failed to unsubscribe from async stream %s: %s", stream_name, str(exc))

    def _parse_message_value(self, value: bytes) -> Any:
        """Parse message value from bytes.
        
        Args:
            value: Message value in bytes
            
        Returns:
            Parsed value or original bytes if parsing fails
        """
        if not value:
            return None
            
        try:
            return json.loads(value.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return value

    async def get_message(self, stream_name: str = None, timeout: float = 60.0) -> Optional[Dict]:
        """Get a single message from Redis stream asynchronously.
        
        Args:
            stream_name: Stream to read from (if None, reads from all configured streams)
            timeout: Maximum time to wait for message in seconds
            
        Returns:
            Message dictionary if available, None if no message received
            
        Raises:
            RuntimeError: If no streams are configured
            RedisConnectionError: If message retrieval fails
        """
        if not self.client:
            raise RuntimeError("Redis client not initialized. Call setup_client() first.")
        
        # Determine which streams to read from
        if stream_name:
            if stream_name not in self._consumer_groups:
                raise RuntimeError(f"Stream '{stream_name}' not set up. Call setup_stream() first")
            streams_to_read = [stream_name]
        else:
            streams_to_read = list(self._streams)
            if not streams_to_read:
                raise RuntimeError("No streams configured. Call setup_stream() first")
        
        start_time = time.time()
        try:
            # Build streams dictionary for XREADGROUP
            streams_dict = {}
            # For multi-stream setups, we'll use the first stream's consumer group/name
            # This is a limitation of Redis XREADGROUP when reading from multiple streams
            
            # Find the first stream and ensure it's decoded
            first_stream = self._safe_decode(streams_to_read[0])
            primary_consumer_group = None
            primary_consumer_name = None
            
            # Find consumer group and name, handling both bytes and string keys
            for stored_stream in self._consumer_groups:
                if self._safe_decode(stored_stream) == first_stream:
                    primary_consumer_group = self._consumer_groups[stored_stream]
                    primary_consumer_name = self._consumer_names[stored_stream]
                    break
            
            if not primary_consumer_group or not primary_consumer_name:
                raise RuntimeError(f"Consumer group/name not found for stream '{first_stream}'")
            
            for stream in streams_to_read:
                # Ensure stream names are strings, not bytes
                stream_str = self._safe_decode(stream)
                streams_dict[stream_str] = '>'  # Read new messages
            
            # Use XREADGROUP to read from streams
            timeout_ms = int(timeout * 1000) if timeout > 0 else 0
            
            # Ensure all dict keys and values are strings for Redis client
            clean_streams_dict = {}
            for stream_name, stream_id in streams_dict.items():
                clean_streams_dict[self._safe_decode(stream_name)] = self._safe_decode(stream_id)
            
            # Use the standard dict approach for async Redis client
            try:
                result = await self.client.xreadgroup(
                    self._safe_decode(primary_consumer_group),
                    self._safe_decode(primary_consumer_name),
                    clean_streams_dict,
                    count=1,
                    block=timeout_ms
                )
            except Exception as xread_exc:
                logging.error(f"xreadgroup failed: {xread_exc}")
                raise
            
            end_time = time.time()
            
            if not result:
                # Record timeout as successful operation with no message
                self._record_metric(
                    operation="read",
                    stream="(timeout)",
                    start_time=start_time,
                    end_time=end_time,
                    success=True,
                    error_msg=None,
                    message_key=None,
                    message_size=None
                )
                return None
            
            # Extract the first message from the result
            stream_name, messages = result[0]
            if not messages:
                return None
            
            # Decode stream_name and message_id to strings immediately
            stream_name = self._safe_decode(stream_name)
            message_id, fields = messages[0]
            message_id = self._safe_decode(message_id)
            
            # Parse fields into structured data
            parsed_data = {}
            message_key = None
            total_size = 0
            
            for field_name, field_value in fields.items():
                field_name = self._safe_decode(field_name)
                field_value = self._safe_decode(field_value)
                total_size += len(field_name) + len(field_value)

                if field_name == '_message_key':
                    message_key = field_value
                    continue

                # Try to parse JSON values
                try:
                    parsed_data[field_name] = json.loads(field_value)
                except (json.JSONDecodeError, ValueError):
                    parsed_data[field_name] = field_value
            
            # Record successful message retrieval metrics
            self._record_metric(
                operation="read",
                stream=stream_name,  # Already decoded
                start_time=start_time,
                end_time=end_time,
                success=True,
                error_msg=None,
                message_key=message_key,
                message_size=total_size
            )
            
            # Acknowledge the message
            try:
                consumer_group = self._consumer_groups[stream_name]
                await self.client.xack(stream_name, consumer_group, message_id)
            except Exception as ack_exc:
                logging.warning("Failed to acknowledge async message: %s", str(ack_exc))
            
            result = {
                "stream": stream_name,  # Already decoded
                "message_id": message_id,  # Already decoded
                "data": parsed_data,
                "fields": {self._safe_decode(k): self._safe_decode(v) for k, v in fields.items()},
                "message_key": message_key
            }
            return result
            
        except asyncio.TimeoutError:
            end_time = time.time()
            # Record timeout as successful operation with no message
            self._record_metric(
                operation="read",
                stream="(timeout)",
                start_time=start_time,
                end_time=end_time,
                success=True,
                error_msg=None,
                message_key=None,
                message_size=None
            )
            return None
        except Exception as exc:
            end_time = time.time()
            error_msg = f"Failed to get async message: {str(exc)}"
            logging.error(error_msg, exc_info=True)
            
            # Record error metrics
            self._record_metric(
                operation="read",
                stream="(error)",
                start_time=start_time,
                end_time=end_time,
                success=False,
                error_msg=error_msg,
                message_key=None,
                message_size=None
            )
            raise RedisConnectionError(error_msg)

    async def listen_for_messages(self, callback: Optional[Callable] = None, stream_name: str = None) -> None:
        """Listen for messages on configured streams asynchronously (blocking).

        Args:
            callback: Optional callback function for all messages
            stream_name: Optional specific stream to listen to (listens to all if None)

        Raises:
            RuntimeError: If no streams are configured
            RedisConnectionError: If listening fails
        """
        if not self._streams:
            raise RuntimeError("No streams configured. Call setup_stream() first")

        try:
            logging.info("Starting to listen for async Redis stream messages...")
            while True:
                try:
                    message = await self.get_message(stream_name=stream_name, timeout=5.0)
                    if message:
                        # Execute callback
                        if callback:
                            try:
                                if asyncio.iscoroutinefunction(callback):
                                    await callback(message)
                                else:
                                    callback(message)
                            except Exception as callback_exc:
                                logging.error("Error in async stream callback: %s", str(callback_exc))
                except RedisConnectionError as exc:
                    logging.error("Async Redis connection error while listening: %s", str(exc))
                    # Sleep briefly before retrying
                    await asyncio.sleep(1.0)
                except Exception as exc:
                    logging.error("Unexpected error while listening async: %s", str(exc))
                    await asyncio.sleep(1.0)
                            
        except asyncio.CancelledError:
            logging.info("Stopped listening for async Redis stream messages (cancelled)")
        except Exception as exc:
            error_msg = f"Error listening for async messages: {str(exc)}"
            logging.error(error_msg)
            raise RedisConnectionError(error_msg)

    async def close(self) -> None:
        """Close async Redis client connections."""
        errors = []
        
        # Stop background metrics reporting first
        try:
            self.stop_metrics_reporting()
        except Exception as exc:
            error_msg = f"Error stopping async Redis metrics reporting: {str(exc)}"
            logging.error(error_msg)
            errors.append(error_msg)
        
        # Check if event loop is still running
        try:
            loop = asyncio.get_running_loop()
            if loop.is_closed():
                logging.warning("Event loop is closed, skipping async Redis cleanup")
                self.client = None
                return
        except RuntimeError:
            logging.warning("No running event loop, skipping async Redis cleanup")
            self.client = None
            return
        
        # Clear stream tracking
        if self._streams:
            try:
                self._streams.clear()
                self._consumer_groups.clear()
                self._consumer_names.clear()
                logging.debug("Cleared async stream tracking")
            except Exception as exc:
                error_msg = f"Error clearing async stream tracking: {str(exc)}"
                logging.warning(error_msg)
                errors.append(error_msg)
                
        # Close client connection
        if self.client:
            try:
                logging.debug("Closing async Redis client...")
                await self.client.close()
                self.client = None
                logging.debug("Async Redis client closed successfully")
            except Exception as exc:
                error_msg = f"Error closing async Redis client: {str(exc)}"
                logging.error(error_msg)
                errors.append(error_msg)
                self.client = None
                
        if not errors:
            logging.info("Closed async Redis connections successfully")
        else:
            # Don't raise exception during cleanup, just log errors
            logging.error("Errors occurred during async Redis close: %s", "; ".join(errors))


class MatriceRedisDeployment:
    """Class for managing Redis deployments for Matrice streaming API."""

    def __init__(
        self, 
        session, 
        service_id: str, 
        type: str, 
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        username: Optional[str] = None,
        db: int = 0,
        consumer_group: str = None,
        enable_metrics: bool = True,
        metrics_interval: int = 60
    ) -> None:
        """Initialize Redis streams deployment with deployment ID.

        Args:
            session: Session object for authentication and RPC
            service_id: ID of the deployment
            type: Type of deployment ("client" or "server")
            host: Redis server hostname or IP address
            port: Redis server port
            password: Password for Redis authentication
            username: Username for Redis authentication (Redis 6.0+)
            db: Database number to connect to
            consumer_group: Consumer group name (defaults to service_id-type)
            enable_metrics: Whether to auto-enable metrics reporting (default: True)
            metrics_interval: Metrics reporting interval in seconds (default: 60)
        Raises:
            ValueError: If type is not "client" or "server"
        """
        self.session = session
        self.rpc = session.rpc
        self.service_id = service_id
        self.type = type
        self.host = host
        self.port = port
        self.password = password
        self.username = username
        self.db = db

        self.setup_success = True
        self.request_stream = f"{service_id}_requests"
        self.result_stream = f"{service_id}_results"
        self.publishing_stream = None
        self.subscribing_stream = None

        # Consumer group configuration
        self.consumer_group = consumer_group or f"{service_id}_{type}_group"

        # Initialize Redis utilities as None - create as needed
        self.sync_redis = None
        self.async_redis = None
        
        # Initialize metrics configuration
        self._metrics_config = None

        # Configure streams based on deployment type
        if self.type == "client":
            self.publishing_stream = self.request_stream
            self.subscribing_stream = self.result_stream
        elif self.type == "server":
            self.publishing_stream = self.result_stream
            self.subscribing_stream = self.request_stream
        else:
            raise ValueError("Invalid type: must be 'client' or 'server'")

        logging.info(
            "Initialized MatriceRedisDeployment: deployment_id=%s, type=%s, host=%s:%d, consumer_group=%s",
            service_id, type, host, port, self.consumer_group
        )

        # Auto-enable metrics reporting by default
        if enable_metrics:
            self.configure_metrics_reporting(interval=metrics_interval)

    def check_setup_success(self) -> bool:
        """Check if the Redis setup is successful.
        
        Returns:
            bool: True if setup was successful, False otherwise
        """
        return self.setup_success

    def get_all_metrics(self) -> Dict:
        """Get aggregated metrics from all Redis utilities.
        
        Returns:
            Dict: Combined metrics from sync and async Redis utilities
        """
        all_metrics = {
            'sync_metrics': [],
            'async_metrics': [],
            'deployment_info': {
                'type': self.type,
                'setup_success': self.setup_success,
                'publishing_stream': getattr(self, 'publishing_stream', None),
                'subscribing_stream': getattr(self, 'subscribing_stream', None),
                'consumer_group': getattr(self, 'consumer_group', None)
            }
        }
        
        # Get sync metrics
        if self.sync_redis:
            try:
                all_metrics['sync_metrics'] = self.sync_redis.get_metrics()
            except Exception as exc:
                logging.warning("Error getting sync Redis metrics: %s", str(exc))
        
        # Get async metrics
        if self.async_redis:
            try:
                all_metrics['async_metrics'] = self.async_redis.get_metrics()
            except Exception as exc:
                logging.warning("Error getting async Redis metrics: %s", str(exc))
        
        return all_metrics

    def get_metrics_summary(self) -> Dict:
        """Get a summary of metrics from all Redis utilities.
        
        Returns:
            Dict: Summarized metrics with counts and statistics
        """
        all_metrics = self.get_all_metrics()
        summary = {
            'sync_summary': {
                'total_operations': len(all_metrics['sync_metrics']),
                'success_count': 0,
                'error_count': 0,
                'avg_latency': 0.0
            },
            'async_summary': {
                'total_operations': len(all_metrics['async_metrics']),
                'success_count': 0,
                'error_count': 0,
                'avg_latency': 0.0
            },
            'deployment_info': all_metrics['deployment_info']
        }
        
        # Calculate sync summary
        if all_metrics['sync_metrics']:
            sync_latencies = []
            for metric in all_metrics['sync_metrics']:
                if metric.get('success'):
                    summary['sync_summary']['success_count'] += 1
                    if 'duration_ms' in metric:
                        sync_latencies.append(metric['duration_ms'])
                else:
                    summary['sync_summary']['error_count'] += 1
            
            if sync_latencies:
                summary['sync_summary']['avg_latency'] = sum(sync_latencies) / len(sync_latencies)
        
        # Calculate async summary
        if all_metrics['async_metrics']:
            async_latencies = []
            for metric in all_metrics['async_metrics']:
                if metric.get('success'):
                    summary['async_summary']['success_count'] += 1
                    if 'duration_ms' in metric:
                        async_latencies.append(metric['duration_ms'])
                else:
                    summary['async_summary']['error_count'] += 1
            
            if async_latencies:
                summary['async_summary']['avg_latency'] = sum(async_latencies) / len(async_latencies)
        
        return summary

    def refresh(self):
        """Refresh the Redis client and subscriber connections."""
        logging.info("Refreshing Redis connections")
        # Clear existing connections to force recreation
        if self.sync_redis:
            try:
                self.sync_redis.close()
            except Exception as exc:
                logging.warning("Error closing sync Redis during refresh: %s", str(exc))
            self.sync_redis = None
            
        if self.async_redis:
            try:
                # Note: close() is async but we can't await here
                logging.warning("Async Redis connections will be recreated on next use")
            except Exception as exc:
                logging.warning("Error during async Redis refresh: %s", str(exc))
            self.async_redis = None
            
        logging.info("Redis connections will be refreshed on next use")

    def _ensure_sync_client(self):
        """Ensure sync Redis client is set up."""
        if not self.sync_redis:
            self.sync_redis = RedisUtils(
                host=self.host,
                port=self.port,
                password=self.password,
                username=self.username,
                db=self.db
            )
            # Configure metrics reporting if enabled
            if self._metrics_config and self._metrics_config.get('enabled'):
                try:
                    self.sync_redis.configure_metrics_reporting(
                        rpc_client=self.session.rpc,
                        deployment_id=self.service_id,
                        interval=self._metrics_config.get('interval', 60),
                        batch_size=self._metrics_config.get('batch_size', 1000)
                    )
                except Exception as exc:
                    logging.warning(f"Failed to configure sync Redis metrics reporting: {exc}")
        
        try:
            if not self.sync_redis.client:
                self.sync_redis.setup_client()
            return True
        except Exception as exc:
            logging.error("Failed to set up sync Redis client: %s", str(exc))
            return False

    def _ensure_sync_subscriber(self):
        """Ensure sync Redis stream subscriber is set up."""
        if not self._ensure_sync_client():
            return False
        
        try:
            # Check if stream is already set up
            if self.subscribing_stream not in self.sync_redis._streams:
                self.sync_redis.setup_stream(
                    stream_name=self.subscribing_stream,
                    consumer_group=self.consumer_group,
                    consumer_name=f"{self.service_id}_{self.type}_sync"
                )
            return True
        except Exception as exc:
            logging.error("Failed to set up sync Redis stream subscriber: %s", str(exc))
            return False

    async def _ensure_async_client(self):
        """Ensure async Redis client is set up.
        
        Returns:
            bool: True if setup was successful, False otherwise
        """
        if not self.async_redis:
            self.async_redis = AsyncRedisUtils(
                host=self.host,
                port=self.port,
                password=self.password,
                username=self.username,
                db=self.db,
            )
            # Configure metrics reporting if enabled
            if self._metrics_config and self._metrics_config.get('enabled'):
                try:
                    self.async_redis.configure_metrics_reporting(
                        rpc_client=self.session.rpc,
                        deployment_id=self.service_id,
                        interval=self._metrics_config.get('interval', 60),
                        batch_size=self._metrics_config.get('batch_size', 1000)
                    )
                except Exception as exc:
                    logging.warning(f"Failed to configure async Redis metrics reporting: {exc}")
        
        try:
            if not self.async_redis.client:
                await self.async_redis.setup_client()
            return True
        except Exception as exc:
            logging.error("Failed to set up async Redis client: %s", str(exc))
            return False

    async def _ensure_async_subscriber(self):
        """Ensure async Redis stream subscriber is set up.
        
        Returns:
            bool: True if setup was successful, False otherwise
        """
        if not await self._ensure_async_client():
            return False
        
        try:
            # Check if stream is already set up
            if self.subscribing_stream not in self.async_redis._streams:
                await self.async_redis.setup_stream(
                    stream_name=self.subscribing_stream,
                    consumer_group=self.consumer_group,
                    consumer_name=f"{self.service_id}_{self.type}_async"
                )
            return True
        except Exception as exc:
            logging.error("Failed to set up async Redis stream subscriber: %s", str(exc))
            return False

    def _parse_message(self, result: dict) -> dict:
        """Handle message parsing for consistency."""
        if not result:
            return result
        # Redis messages are already parsed by the utility classes
        return result

    def publish_message(self, message: dict, timeout: float = 60.0) -> str:
        """Add a message to Redis stream.

        Args:
            message: Message to add to stream
            timeout: Maximum time to wait for message addition in seconds
            
        Returns:
            Message ID assigned by Redis
            
        Raises:
            RuntimeError: If client is not initialized
            ValueError: If message is invalid
            RedisConnectionError: If message addition fails
        """
        if not self._ensure_sync_client():
            raise RuntimeError("Failed to set up Redis client")
        return self.sync_redis.add_message(self.publishing_stream, message, timeout=timeout)

    def get_message(self, timeout: float = 60.0) -> Optional[Dict]:
        """Get a message from Redis stream.

        Args:
            timeout: Maximum time to wait for message in seconds
            
        Returns:
            Message dictionary if available, None if no message received
            
        Raises:
            RuntimeError: If subscriber is not initialized
            RedisConnectionError: If message retrieval fails
        """
        if not self._ensure_sync_subscriber():
            logging.warning("Redis stream subscriber setup unsuccessful, returning None for get request")
            return None

        result = self.sync_redis.get_message(stream_name=self.subscribing_stream, timeout=timeout)
        result = self._parse_message(result)
        return result

    async def async_publish_message(self, message: dict, timeout: float = 60.0) -> str:
        """Add a message to Redis stream asynchronously.

        Args:
            message: Message to add to stream
            timeout: Maximum time to wait for message addition in seconds
            
        Returns:
            Message ID assigned by Redis
            
        Raises:
            RuntimeError: If client is not initialized
            ValueError: If message is invalid
            RedisConnectionError: If message addition fails
        """
        if not await self._ensure_async_client():
            raise RuntimeError("Failed to set up async Redis client")
        return await self.async_redis.add_message(self.publishing_stream, message, timeout=timeout)

    async def async_get_message(self, timeout: float = 60.0) -> Optional[Dict]:
        """Get a message from Redis stream asynchronously.

        Args:
            timeout: Maximum time to wait for message in seconds
            
        Returns:
            Message dictionary if available, None if no message received
            
        Raises:
            RuntimeError: If subscriber is not initialized
            RedisConnectionError: If message retrieval fails
        """
        try:
            if not await self._ensure_async_subscriber():
                logging.warning("Async Redis stream subscriber setup unsuccessful, returning None for get request")
                return None

            result = await self.async_redis.get_message(stream_name=self.subscribing_stream, timeout=timeout)
            result = self._parse_message(result)
            return result
        except RuntimeError as exc:
            logging.error("Runtime error in async_get_message: %s", str(exc), exc_info=True)
            return None
        except Exception as exc:
            logging.error("Unexpected error in async_get_message: %s", str(exc), exc_info=True)
            return None

    def configure_metrics_reporting(self, 
                                   interval: int = 60,
                                   batch_size: int = 1000) -> None:
        """Configure background metrics reporting for both sync and async Redis utilities.
        
        This method enables automatic metrics collection and reporting to the backend API
        for all Redis operations performed through this deployment.
        
        Args:
            interval: Reporting interval in seconds (default: 60)
            batch_size: Maximum metrics per batch (default: 1000)
        """
        try:
            # Configure metrics reporting for sync Redis utils if they exist
            if self.sync_redis:
                self.sync_redis.configure_metrics_reporting(
                    rpc_client=self.session.rpc,
                    deployment_id=self.service_id,
                    interval=interval,
                    batch_size=batch_size
                )
                logging.info(f"Configured sync Redis metrics reporting for deployment {self.service_id}")
            
            # Configure metrics reporting for async Redis utils if they exist
            if self.async_redis:
                self.async_redis.configure_metrics_reporting(
                    rpc_client=self.session.rpc,
                    deployment_id=self.service_id,
                    interval=interval,
                    batch_size=batch_size
                )
                logging.info(f"Configured async Redis metrics reporting for deployment {self.service_id}")
            
            # If no Redis utils exist yet, they will be configured when first created
            if not self.sync_redis and not self.async_redis:
                logging.info(f"Metrics reporting will be configured when Redis connections are established for deployment {self.service_id}")
                
            # Store configuration for future Redis utils creation
            self._metrics_config = {
                'interval': interval,
                'batch_size': batch_size,
                'enabled': True
            }
            
        except Exception as exc:
            logging.error(f"Error configuring Redis metrics reporting for deployment {self.service_id}: {exc}")

    async def close(self) -> None:
        """Close Redis client and subscriber connections.
        
        This method gracefully closes all Redis connections without raising exceptions
        to ensure proper cleanup during shutdown.
        """
        errors = []

        # Close sync Redis connections
        if self.sync_redis:
            try:
                logging.debug("Closing sync Redis connections...")
                self.sync_redis.close()
                self.sync_redis = None
                logging.debug("Sync Redis connections closed successfully")
            except Exception as exc:
                error_msg = f"Error closing sync Redis connections: {str(exc)}"
                logging.error(error_msg)
                errors.append(error_msg)
                self.sync_redis = None

        # Close async Redis connections
        if self.async_redis:
            try:
                logging.debug("Closing async Redis connections...")
                await self.async_redis.close()
                self.async_redis = None
                logging.debug("Async Redis connections closed successfully")
            except Exception as exc:
                error_msg = f"Error closing async Redis connections: {str(exc)}"
                logging.error(error_msg)
                errors.append(error_msg)
                self.async_redis = None

        if not errors:
            logging.info("Closed Redis connections successfully")
        else:
            # Log errors but don't raise exception during cleanup
            logging.error("Errors occurred during Redis close: %s", "; ".join(errors))