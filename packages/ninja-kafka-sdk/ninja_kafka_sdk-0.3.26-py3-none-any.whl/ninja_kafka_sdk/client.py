"""
Main Ninja Kafka SDK client.
Provides simple interface for sending tasks to Ninja services and receiving results.
"""

import json
import logging
import asyncio
import threading
import time
import uuid
from typing import Optional, Dict, Any, List, AsyncIterator, Callable, Union
from queue import Queue
from kafka import KafkaProducer, KafkaConsumer, ConsumerRebalanceListener
from kafka.errors import KafkaError

from .config import NinjaKafkaConfig
from .models import NinjaTaskRequest, NinjaTaskResult, NinjaTaskProgress
from .exceptions import (
    NinjaKafkaError, NinjaKafkaConnectionError, 
    NinjaTaskTimeoutError, NinjaTaskError
)
from .self_healing import SelfHealingMixin

logger = logging.getLogger(__name__)


class NinjaClient(SelfHealingMixin):
    """
    Main client for communicating with Ninja services via Kafka.

    Auto-detects environment and provides simple API for task execution.

    Message Routing:
    - All correlation_ids are automatically prefixed with the consumer group name
    - Results are filtered to only process messages for this consumer group
    - This ensures complete isolation between different services

    Example:
        client = NinjaClient(
            kafka_servers='localhost:9092',
            consumer_group='auto-login'  # All correlation_ids will start with 'auto-login:'
        )
    """
    
    def __init__(
        self,
        kafka_servers: str,
        consumer_group: str,
        environment: Optional[str] = None,
        timeout: int = 300,
        retry_attempts: int = 3,
        tasks_topic: str = 'ninja-tasks',
        results_topic: str = 'ninja-results',
        health_check_interval: int = 60,
        config: Optional[NinjaKafkaConfig] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Ninja client with explicit configuration.
        
        Args:
            kafka_servers: REQUIRED. Kafka bootstrap servers (e.g., 'localhost:9092' or 'server1:9092,server2:9092')
            consumer_group: REQUIRED. Consumer group for this client
            environment: Optional environment name for logging
            timeout: Default timeout for tasks in seconds
            retry_attempts: Number of retry attempts for failed operations
            tasks_topic: Kafka topic for sending tasks
            results_topic: Kafka topic for receiving results
            health_check_interval: Health check interval in seconds (default: 60)
            config: Custom configuration object (overrides other parameters)
            metadata: Optional metadata dict for logging (e.g., commit_hash, instance_type)
            
        Example:
            # Local development
            client = NinjaClient(
                kafka_servers='localhost:9092',
                consumer_group='my-service'
            )
            
            # Production
            client = NinjaClient(
                kafka_servers='broker1:9092,broker2:9092,broker3:9092',
                consumer_group='my-service-prod'
            )
        """
        # Validate consumer group name doesn't contain reserved characters
        if ':' in consumer_group:
            raise ValueError(
                f"Consumer group name cannot contain ':' character: '{consumer_group}'. "
                f"This character is reserved for correlation ID prefixing."
            )

        if config:
            # Also validate config's consumer_group if provided
            if ':' in config.consumer_group:
                raise ValueError(
                    f"Consumer group name cannot contain ':' character: '{config.consumer_group}'. "
                    f"This character is reserved for correlation ID prefixing."
                )
            self.config = config
        else:
            self.config = NinjaKafkaConfig(
                kafka_servers=kafka_servers,
                consumer_group=consumer_group,
                environment=environment,
                tasks_topic=tasks_topic,
                results_topic=results_topic
            )
        self.timeout = timeout
        self.retry_attempts = retry_attempts
        self.health_check_interval = health_check_interval
        self.metadata = metadata or {}  # Store metadata for health check logs
        self.producer = None
        self.results_consumer = None  # Direct consumer for listen_results
        self.task_consumer = None
        self.task_consumer_thread = None
        self._running = False
        self._tasks_queue = Queue()  # Still needed for task consumption in browser-ninja
        self._pending_tasks = {}  # correlation_id -> task info
        self._pending_commits = {}  # correlation_id -> commit info for manual commit
        
        # Initialize self-healing
        self._init_self_healing()
        
        logger.info(f"NinjaClient initialized (env: {self.config.environment})")
        logger.info(f"✅ Kafka configuration:")
        logger.info(f"   - Environment: {self.config.environment}")
        logger.info(f"   - Kafka servers: {self.config.kafka_servers}")
        logger.info(f"   - Tasks topic: {self.config.tasks_topic}")
        logger.info(f"   - Results topic: {self.config.results_topic}")
        logger.info(f"   - Health check interval: {self.health_check_interval}s")

        # Log metadata if provided
        if self.metadata:
            logger.info(f"📊 Client metadata:")
            for key, value in self.metadata.items():
                logger.info(f"   - {key}: {value}")
    
    async def send_task(
        self,
        task: str,
        account_id: int,
        email: Optional[str] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> str:
        """
        Send task to Ninja service.

        The correlation_id returned will be prefixed with the consumer group name
        to ensure proper message routing. For example, if consumer_group is 'auto-login',
        the correlation_id will be 'auto-login:uuid-...'

        Args:
            task: Task type (e.g., 'linkedin_verification')
            account_id: Account ID
            email: Account email (optional)
            user_id: User ID (optional)
            **kwargs: Additional task parameters
                - correlation_id: If provided, will be prefixed with consumer group
                - parameters: Task-specific parameters
                - api_endpoints: API endpoint configuration

        Returns:
            correlation_id: Unique ID to track this task (prefixed with consumer group)

        Raises:
            NinjaKafkaConnectionError: If cannot connect to Kafka
            NinjaKafkaError: For other Kafka-related errors
        """
        if not self.producer:
            self._start_producer()
            
        # No background consumer needed - listen_results will consume directly

        # Extract special fields from kwargs that should go to their proper fields
        # instead of being nested in metadata
        parameters = kwargs.pop('parameters', None)
        api_endpoints = kwargs.pop('api_endpoints', None)
        provided_correlation_id = kwargs.pop('correlation_id', None)

        # Generate correlation_id with consumer group prefix
        if provided_correlation_id:
            # User provided one - add our consumer group prefix
            correlation_id = f"{self.config.consumer_group}:{provided_correlation_id}"
        else:
            # Auto-generate with consumer group prefix
            correlation_id = f"{self.config.consumer_group}:{str(uuid.uuid4())}"

        # Build request args with the prefixed correlation_id
        request_args = {
            'task': task,
            'account_id': account_id,
            'email': email,
            'user_id': user_id,
            'parameters': parameters,
            'api_endpoints': api_endpoints,
            'correlation_id': correlation_id,  # Always provide the prefixed version
            'metadata': kwargs  # Only remaining kwargs go to metadata
        }

        # Create task request with proper field assignments
        request = NinjaTaskRequest(**request_args)
        
        # API endpoints should be provided by the calling service (Auto Login)
            
        # Track pending task
        self._pending_tasks[request.correlation_id] = {
            'request': request,
            'sent_at': time.time(),
            'status': 'pending'
        }
        
        try:
            # Send to Kafka (force partition 0 like autologin)
            future = self.producer.send(
                self.config.tasks_topic,
                value=request.to_dict(),
                key=f"task_{task}_account_{account_id}",
                partition=0
            )
            
            # Wait for send to complete
            result = future.get(timeout=30)
            
            logger.info(f"✅ Task sent successfully: {task} (correlation_id: {request.correlation_id[:8]})")
            logger.debug(f"Kafka result: topic={result.topic}, partition={result.partition}, offset={result.offset}")
            
            return request.correlation_id
            
        except KafkaError as e:
            # Check if this is a retryable partition leadership error
            retryable_errors = [
                'NotLeaderForPartitionError',
                'LeaderNotAvailableError',
                'RequestTimedOutError',
                'NetworkError'
            ]
            
            error_name = type(e).__name__
            if any(retryable in error_name for retryable in retryable_errors):
                logger.warning(f"⚠️ Retryable Kafka error ({error_name}), this is usually temporary")
                logger.warning(f"💡 MSK partition leadership is rebalancing - this should resolve automatically")
            
            # Remove from pending tasks on failure
            self._pending_tasks.pop(request.correlation_id, None)
            logger.error(f"❌ Failed to send task: {e}")
            raise NinjaKafkaConnectionError(f"Failed to send task: {e}") from e
    
    def send_task_sync(
        self,
        task: str,
        account_id: int,
        email: Optional[str] = None,
        user_id: Optional[int] = None,
        **kwargs
    ) -> str:
        """Synchronous version of send_task."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # We're in an async context, use thread executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._send_task_in_thread, task, account_id, email, user_id, **kwargs)
                return future.result(timeout=30)
        except RuntimeError:
            # No running loop, we can safely create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.send_task(task, account_id, email, user_id, **kwargs)
                )
            finally:
                loop.close()
    
    def _send_task_in_thread(self, task: str, account_id: int, email: Optional[str] = None, user_id: Optional[int] = None, **kwargs) -> str:
        """Helper method to run send_task in a separate thread with its own event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.send_task(task, account_id, email, user_id, **kwargs)
            )
        finally:
            loop.close()
    
    async def execute_task(
        self,
        task: str,
        account_id: int,
        timeout: Optional[int] = None,
        **kwargs
    ) -> NinjaTaskResult:
        """
        Send task and wait for result (high-level API).
        
        Args:
            task: Task type
            account_id: Account ID
            timeout: Timeout in seconds (uses default if None)
            **kwargs: Additional task parameters
            
        Returns:
            NinjaTaskResult: Task execution result
            
        Raises:
            NinjaTaskTimeoutError: If task times out
            NinjaTaskError: If task fails
        """
        timeout = timeout or self.timeout
        
        # No background consumer needed for execute_task
            
        # Send task
        correlation_id = await self.send_task(task, account_id, **kwargs)
        
        # Wait for result
        start_time = time.time()
        while time.time() - start_time < timeout:
            # For execute_task, we need a simple result consumer
            # This is a blocking wait, not the async listen_results
            # TODO: Implement proper result waiting without background thread
            # For now, just check pending tasks
            if correlation_id in self._pending_tasks:
                task_info = self._pending_tasks[correlation_id]
                # Without background consumer, we can't get results in execute_task
                # This method needs rethinking - perhaps should use async listen_results
                pass
            
            # Brief sleep to avoid tight loop
            await asyncio.sleep(0.5)
        
        # Timeout
        self._pending_tasks.pop(correlation_id, None)
        raise NinjaTaskTimeoutError(f"Task {task} timed out after {timeout}s")
    
    def execute_task_sync(
        self,
        task: str,
        account_id: int,
        timeout: Optional[int] = None,
        **kwargs
    ) -> NinjaTaskResult:
        """Synchronous version of execute_task."""
        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
            # We're in an async context, use thread executor
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(self._execute_task_in_thread, task, account_id, timeout, **kwargs)
                return future.result(timeout=(timeout or self.timeout) + 10)
        except RuntimeError:
            # No running loop, we can safely create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(
                    self.execute_task(task, account_id, timeout, **kwargs)
                )
            finally:
                loop.close()
    
    def _execute_task_in_thread(self, task: str, account_id: int, timeout: Optional[int] = None, **kwargs) -> NinjaTaskResult:
        """Helper method to run execute_task in a separate thread with its own event loop."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.execute_task(task, account_id, timeout, **kwargs)
            )
        finally:
            loop.close()
    
    async def listen_results(
        self,
        correlation_ids: Optional[List[str]] = None,
        handler: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Listen for task results directly from Kafka.

        This method automatically filters results based on the consumer group prefix.
        Only results with correlation_ids starting with '{consumer_group}:' will be
        processed. This ensures each service only receives its own results.

        This is a simple async iterator that polls Kafka directly without background threads.
        The consumer runs in the caller's async context. Includes automatic retry logic
        for connection issues.

        Args:
            correlation_ids: Only yield results for these specific IDs (must include prefix)
            handler: Optional callback for each result

        Yields:
            Dict[str, Any]: Raw result messages as they arrive (including progress updates)
        """
        # Retry logic for consumer creation
        max_retries = 5
        retry_delay = 5  # seconds
        retry_count = 0

        # Create a direct consumer if needed
        while not self.results_consumer and retry_count < max_retries:
            servers = self.config.kafka_servers
            if isinstance(servers, str):
                servers = [s.strip() for s in servers.split(',')]

            try:
                self.results_consumer = KafkaConsumer(
                    self.config.results_topic,
                    bootstrap_servers=servers,
                    group_id=f"{self.config.consumer_group}-results",  # Separate group for results
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='earliest',
                    enable_auto_commit=False,  # Manual commit after processing
                    max_poll_records=10,
                    # Add connection timeout settings
                    request_timeout_ms=30000,
                    api_version_auto_timeout_ms=10000,
                    connections_max_idle_ms=540000
                )
                logger.info(f"✅ Direct results consumer created for {self.config.results_topic}")
                break  # Success, exit retry loop

            except Exception as e:
                retry_count += 1
                logger.error(f"❌ Failed to create results consumer (attempt {retry_count}/{max_retries}): {e}")
                logger.error(f"   Kafka servers: {servers}")
                logger.error(f"   Results topic: {self.config.results_topic}")
                logger.error(f"   Consumer group: {self.config.consumer_group}-results")

                if retry_count >= max_retries:
                    # Final attempt failed, raise error
                    raise NinjaKafkaConnectionError(
                        f"Failed to create Kafka results consumer after {max_retries} attempts: {e}. "
                        f"Check Kafka connectivity and configuration. "
                        f"Servers: {servers}, Topic: {self.config.results_topic}"
                    ) from e

                # Wait before retrying
                logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)
                # Exponential backoff for next retry
                retry_delay = min(retry_delay * 2, 60)  # Cap at 60 seconds

        # Simple direct consumption - no queues, no threads!
        while True:
            try:
                # Check if consumer is valid before polling
                if not self.results_consumer:
                    logger.error("❌ Results consumer is None, cannot poll")
                    raise NinjaKafkaConnectionError("Results consumer not initialized")

                # Poll Kafka with VERY SHORT timeout to avoid blocking
                # Use 10ms for minimal blocking
                messages = self.results_consumer.poll(timeout_ms=10)

                for topic_partition, records in messages.items():
                    for record in records:
                        result = record.value  # Already deserialized to dict

                        # Get correlation_id from result
                        result_correlation_id = result.get('correlation_id', '')

                        # FILTER BY CONSUMER GROUP PREFIX
                        if not result_correlation_id.startswith(f"{self.config.consumer_group}:"):
                            # Not for this consumer group - commit and skip
                            self.results_consumer.commit()
                            continue

                        # Additional filtering by specific correlation_ids if specified
                        if correlation_ids:
                            if result_correlation_id not in correlation_ids:
                                # Still commit to advance offset
                                self.results_consumer.commit()
                                continue

                        # Call handler if provided
                        if handler:
                            try:
                                handler(result)
                            except Exception as e:
                                logger.error(f"Handler error: {e}")

                        # Yield the result to the caller
                        yield result

                        # Commit after yielding to caller
                        self.results_consumer.commit()

                # Yield control without sleeping - just cooperative yield
                await asyncio.sleep(0)  # Zero sleep for cooperative multitasking

            except NinjaKafkaConnectionError:
                # Re-raise connection errors - these are fatal
                raise
            except Exception as e:
                logger.error(f"Error in listen_results: {e}", exc_info=True)

                # Check if this is a connection-related error
                error_str = str(e).lower()
                connection_errors = [
                    'connection', 'timeout', 'disconnected', 'unavailable',
                    'coordinator', 'broker', 'network', 'not available'
                ]

                if any(err in error_str for err in connection_errors):
                    logger.warning("⚠️ Detected possible connection issue, attempting to reconnect...")

                    # Close the current consumer
                    if self.results_consumer:
                        try:
                            self.results_consumer.close()
                        except:
                            pass
                        self.results_consumer = None

                    # Wait a bit before reconnecting
                    await asyncio.sleep(5)

                    # The next iteration will recreate the consumer
                    logger.info("🔄 Will attempt to recreate consumer on next iteration...")
                    continue

                # Check if consumer is still valid
                if self.results_consumer is None:
                    logger.error("❌ Results consumer became None during operation")
                    # Don't raise here, let it recreate on next iteration
                    await asyncio.sleep(5)
                    continue

                # Don't sleep on error - just yield control
                await asyncio.sleep(0)
    
    async def listen_tasks(
        self,
        handler: Optional[Callable[[NinjaTaskRequest], None]] = None
    ) -> AsyncIterator[NinjaTaskRequest]:
        """
        Listen for incoming tasks (for Ninja services).
        
        Args:
            handler: Optional callback for each task
            
        Yields:
            NinjaTaskRequest: Task requests as they arrive
        """
        if not self._running:
            self._start_task_consumer()
            
        while self._running:
            try:
                # Check tasks queue  
                if hasattr(self, '_tasks_queue') and not self._tasks_queue.empty():
                    task = self._tasks_queue.get_nowait()
                    
                    # Call handler if provided
                    if handler:
                        try:
                            handler(task)
                        except Exception as e:
                            logger.error(f"Task handler error: {e}")
                    
                    yield task
                else:
                    await asyncio.sleep(0.1)  # Brief pause if no tasks
                    
            except Exception as e:
                logger.error(f"Error in listen_tasks: {e}")
                await asyncio.sleep(1)
    
    async def send_task_result(
        self,
        correlation_id: str,
        task: str,
        status: str,
        account_id: Optional[int] = None,
        verification_data: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send task result back to requesting service.
        
        Args:
            correlation_id: Request correlation ID
            task: Task type (e.g., 'linkedin_verification')  
            status: Status ('VERIFIED', 'FAILED', etc.)
            account_id: Account ID
            verification_data: Result data
            error: Error details if failed
            metrics: Performance metrics
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self.producer:
            self._start_producer()
            
        # Create result using our model
        result = NinjaTaskResult(
            correlation_id=correlation_id,
            task=task,
            status=status,
            account_id=account_id,
            success=status == 'SUCCESS',
            data=verification_data,
            error=error,
            metrics=metrics
        )
        
        try:
            # Get available partition or let Kafka auto-select
            working_partition = self._get_working_partition(self.config.results_topic)

            # Send with partition if specified, otherwise let Kafka auto-select
            if working_partition is not None:
                future = self.producer.send(
                    self.config.results_topic,
                    value=result.__dict__,
                    key=correlation_id,
                    partition=working_partition
                )
            else:
                # Let Kafka auto-select partition based on key hash
                future = self.producer.send(
                    self.config.results_topic,
                    value=result.__dict__,
                    key=correlation_id
                )
            
            # Wait for send to complete
            record_metadata = future.get(timeout=30)
            
            logger.info(f"✅ Task result sent: {task} ({correlation_id[:8]}) - {status}")
            logger.debug(f"Kafka result: topic={record_metadata.topic}, partition={record_metadata.partition}")
            
            return True
            
        except Exception as e:
            # Check if this is a retryable Kafka partition error
            error_str = str(e)
            retryable_patterns = [
                'NotLeaderForPartitionError',
                'LeaderNotAvailableError', 
                'RequestTimedOutError',
                'NetworkError'
            ]
            
            if any(pattern in error_str for pattern in retryable_patterns):
                logger.warning(f"⚠️ Retryable Kafka partition error: {e}")
                logger.warning(f"💡 This is usually temporary during MSK rebalancing")
                logger.warning(f"🔄 Task result will be lost - consider implementing retry logic in handlers")
            else:
                logger.error(f"❌ Non-retryable error sending task result: {e}")
            
            return False
    
    async def send_success_result(
        self,
        correlation_id: str,
        account_id: int,
        email: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send success result - compatibility with browser-ninja API.
        
        Args:
            correlation_id: Request correlation ID
            account_id: Account ID
            email: Account email
            details: Additional payload data
            
        Returns:
            True if sent successfully
        """
        result_data = {
            'email': email
        }
        if details:
            result_data.update(details)
            
        return await self.send_task_result(
            correlation_id=correlation_id,
            task='linkedin_verification',
            status='SUCCESS',
            account_id=account_id,
            verification_data=result_data
        )
    
    async def send_error_result(
        self,
        correlation_id: str,
        account_id: Optional[int],
        email: Optional[str],
        error_code: str,
        error_message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send error result - compatibility with browser-ninja API.
        
        Args:
            correlation_id: Request correlation ID
            account_id: Account ID if available
            email: Email if available  
            error_code: Error code
            error_message: Error message
            details: Additional error details
            
        Returns:
            True if sent successfully
        """
        verification_data = {'email': email} if email else None
        error_dict = {
            'code': error_code,
            'message': error_message
        }
        if details:
            error_dict.update(details)
            
        return await self.send_task_result(
            correlation_id=correlation_id,
            task='linkedin_verification',
            status='FAIL',
            account_id=account_id or 0,
            verification_data=verification_data,
            error=error_dict
        )
    
    def commit_task(self, correlation_id: str, success: bool = True):
        """
        Commit offset after task processing completes.
        This should be called by browser-ninja after task completion.

        Args:
            correlation_id: The task correlation ID
            success: Whether the task succeeded (for logging)
        """
        if correlation_id in self._pending_commits:
            try:
                # Commit the offset for this task
                if self.task_consumer:
                    self.task_consumer.commit()
                    commit_info = self._pending_commits[correlation_id]
                    elapsed = time.time() - commit_info['timestamp']
                    logger.info(f"✅ Committed offset for task {correlation_id[:8]} (success={success}, elapsed={elapsed:.1f}s)")
                    logger.debug(f"   Commit details: partition={commit_info['partition']}, offset={commit_info['offset']}")

                    # Clean up pending commit
                    del self._pending_commits[correlation_id]
                else:
                    logger.warning(f"⚠️ Cannot commit - task consumer not available for {correlation_id[:8]}")
            except Exception as e:
                logger.error(f"❌ Failed to commit offset for {correlation_id[:8]}: {e}")
        else:
            logger.warning(f"⚠️ No pending commit found for correlation_id {correlation_id[:8]}")
            logger.debug(f"   Available pending commits: {list(self._pending_commits.keys())[:5]}")

    def _get_working_partition(self, topic: str) -> Optional[int]:
        """
        Get an available partition for the given topic.

        Dynamically detects available partitions instead of hardcoding.
        Returns None to let Kafka auto-select partition if preferred.
        """
        try:
            # Get available partitions for the topic
            if not self.producer:
                return None  # Let Kafka decide if producer not initialized

            available_partitions = self.producer.partitions_for(topic)

            if not available_partitions:
                logger.warning(f"No partitions found for topic {topic}, letting Kafka auto-select")
                return None

            # For single partition topics (common in local dev), use partition 0
            if len(available_partitions) == 1:
                return 0

            # For multiple partitions, let Kafka handle partition selection
            # This allows for better load balancing and failover
            logger.debug(f"Topic {topic} has {len(available_partitions)} partitions, using auto-selection")
            return None  # Let Kafka auto-select based on key hash

        except Exception as e:
            logger.warning(f"Could not determine partitions for {topic}: {e}, using auto-selection")
            return None  # Let Kafka decide on error
    
    def _start_producer(self):
        """Start Kafka producer with self-healing."""
        def start_producer_with_healing():
            # Convert comma-separated string to list if needed
            servers = self.config.kafka_servers
            if isinstance(servers, str):
                servers = [s.strip() for s in servers.split(',')]
            
            producer_settings = self.config.producer_settings
            logger.debug(f"Creating KafkaProducer with servers={servers}, settings={producer_settings}")
            
            self.producer = KafkaProducer(
                bootstrap_servers=servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                **producer_settings
            )
            logger.info(f"✅ Kafka producer started (servers: {self.config.kafka_servers})")
            return True
        
        # Use self-healing wrapper
        success = self._attempt_with_self_healing(
            start_producer_with_healing,
            "start_producer"
        )
        
        if not success:
            raise NinjaKafkaConnectionError("Failed to start producer after self-healing attempts")
    
    
    def _start_task_consumer(self):
        """Start Kafka task consumer in background thread with self-healing."""
        if self._running:
            return
        
        def start_task_consumer_with_healing():
            self._running = True
            self.task_consumer_thread = threading.Thread(target=self._consume_tasks, daemon=True)
            self.task_consumer_thread.start()
            logger.info("✅ Kafka task consumer started in background thread")
            return True
        
        # Use self-healing wrapper
        success = self._attempt_with_self_healing(
            start_task_consumer_with_healing,
            "start_task_consumer"
        )
        
        if not success:
            raise NinjaKafkaConnectionError("Failed to start task consumer after self-healing attempts")
    
    
    def _consume_tasks(self):
        """Task consumer loop (runs in background thread for Ninja services)."""
        try:
            # Suppress kafka internal logging
            kafka_logger = logging.getLogger('kafka')
            original_level = kafka_logger.level
            kafka_logger.setLevel(logging.WARNING)
            
            # Convert comma-separated string to list if needed
            servers = self.config.kafka_servers
            if isinstance(servers, str):
                servers = [s.strip() for s in servers.split(',')]
            
            # Start with config settings as the base (config takes precedence)
            consumer_settings = dict(self.config.consumer_settings)

            # Only set defaults for missing keys
            defaults = {
                'auto_offset_reset': 'earliest',
                'enable_auto_commit': False,  # Manual commit for task consumer - commit only after task completion
                'consumer_timeout_ms': 10000,
                'api_version_auto_timeout_ms': 10000,
                'max_poll_records': 1,
            }

            # Add defaults only if not already in config
            for key, value in defaults.items():
                if key not in consumer_settings:
                    consumer_settings[key] = value

            # Create client_id for better debugging
            client_id = f"ninja-{self.config.consumer_group}"
            if self.metadata and 'instance_type' in self.metadata:
                client_id = f"{client_id}-{self.metadata['instance_type']}"

            self.task_consumer = KafkaConsumer(
                # NOTE: Don't pass topic here - use subscribe() for proper group membership
                bootstrap_servers=servers,
                group_id=self.config.consumer_group,
                client_id=client_id,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                **consumer_settings
            )

            # Create rebalance listener for visibility
            class RebalanceListener(ConsumerRebalanceListener):
                def __init__(listener_self, consumer_group, client_metadata=None):
                    listener_self.consumer_group = consumer_group
                    listener_self.client_metadata = client_metadata or {}

                def _get_metadata_suffix(listener_self):
                    """Get metadata suffix for log messages"""
                    if not listener_self.client_metadata:
                        return ""

                    metadata_parts = []
                    if 'commit_hash' in listener_self.client_metadata:
                        metadata_parts.append(f"commit:{listener_self.client_metadata['commit_hash'][:8]}")
                    if 'instance_type' in listener_self.client_metadata:
                        metadata_parts.append(f"instance:{listener_self.client_metadata['instance_type']}")

                    return f" ({', '.join(metadata_parts)})" if metadata_parts else ""

                def on_partitions_assigned(listener_self, assigned):
                    metadata_suffix = listener_self._get_metadata_suffix()
                    if not assigned:
                        logger.info(f"🔄 REBALANCE ASSIGN: {listener_self.consumer_group} got 0 partitions{metadata_suffix}")
                        return
                    try:
                        partition_info = [f'{p.topic}:{p.partition}' for p in assigned]
                        logger.info(f"🔄 REBALANCE ASSIGN: {listener_self.consumer_group} got {len(assigned)} partitions: {partition_info}{metadata_suffix}")
                    except Exception as e:
                        logger.info(f"🔄 REBALANCE ASSIGN: {listener_self.consumer_group} got {len(assigned)} partitions{metadata_suffix}")
                        logger.debug(f"Partition details error: {e}")

                def on_partitions_revoked(listener_self, revoked):
                    metadata_suffix = listener_self._get_metadata_suffix()
                    if not revoked:
                        logger.info(f"🔄 REBALANCE REVOKE: {listener_self.consumer_group} releasing 0 partitions{metadata_suffix}")
                        return
                    try:
                        partition_info = [f'{p.topic}:{p.partition}' for p in revoked]
                        logger.info(f"🔄 REBALANCE REVOKE: {listener_self.consumer_group} releasing {len(revoked)} partitions: {partition_info}{metadata_suffix}")
                    except Exception as e:
                        logger.info(f"🔄 REBALANCE REVOKE: {listener_self.consumer_group} releasing {len(revoked)} partitions{metadata_suffix}")
                        logger.debug(f"Partition details error: {e}")
                    # Note: Commit is handled automatically with enable_auto_commit=False and manual commits

            # CRITICAL: Must call subscribe() for proper consumer group membership!
            listener = RebalanceListener(self.config.consumer_group, self.metadata)
            self.task_consumer.subscribe(
                [self.config.tasks_topic],
                listener=listener
            )
            
            # Restore logging level
            kafka_logger.setLevel(original_level)
            
            logger.info(f"✅ Task consumer created successfully")
            logger.info(f"   Topic: {self.config.tasks_topic}")
            logger.info(f"   Bootstrap servers: {', '.join(servers)}")
            logger.info(f"   Consumer group: {self.config.consumer_group}")
            
            # Wait for partition assignment like original implementation
            logger.info("⏳ Waiting for partition assignment...")
            assignment_timeout = time.time() + 15
            assigned = set()
            
            while time.time() < assignment_timeout and not assigned:
                # Check if consumer is still valid before polling
                if not self.task_consumer or getattr(self.task_consumer, '_closed', False):
                    logger.warning("⚠️ Consumer closed during partition assignment, exiting")
                    return

                self.task_consumer.poll(timeout_ms=1000)
                assigned = self.task_consumer.assignment()
                if assigned:
                    break
                logger.info(f"⏳ Still waiting for partition assignment... ({int(15 - (assignment_timeout - time.time()))}s elapsed)")
            
            if assigned:
                try:
                    partition_details = [f'{tp.topic}:{tp.partition}' for tp in assigned]
                    logger.info(f"✅ Partition assignment successful: {partition_details}")
                except Exception as e:
                    logger.info(f"✅ Partition assignment successful: {len(assigned)} partitions assigned")
                logger.info(f"🏷️  CONSUMER GROUP: {self.config.consumer_group}")
                logger.info("📊 Detailed offset information will be shown in periodic health checks")

                # Seek to correct position after assignment to ensure no messages were lost
                # during the assignment wait loop (which calls poll but discards messages)
                logger.info("🔍 Seeking partitions to correct offset positions...")
                for partition in assigned:
                    try:
                        # Check if there's a committed offset for this partition
                        committed_offset = self.task_consumer.committed(partition)

                        if committed_offset is None:
                            # No committed offset - seek to beginning (earliest behavior)
                            self.task_consumer.seek_to_beginning(partition)
                            logger.info(f"📍 Partition {partition.topic}:{partition.partition} → BEGINNING (no committed offset)")
                        else:
                            # Has committed offset - seek to it (recovery from assignment wait)
                            self.task_consumer.seek(partition, committed_offset)
                            logger.info(f"📍 Partition {partition.topic}:{partition.partition} → offset {committed_offset}")
                    except Exception as e:
                        logger.warning(f"⚠️ Could not seek partition {partition.topic}:{partition.partition}: {e}")

                logger.info("✅ All partitions positioned correctly")
            else:
                logger.error("❌ No partitions assigned after 15 seconds - consumer group coordination failed!")
                logger.error("🔧 Triggering self-healing for partition assignment failure...")
                
                # Close current consumer before healing
                if self.task_consumer:
                    self.task_consumer.close()
                    self.task_consumer = None
                
                # Trigger self-healing with enhanced logging
                logger.warning("🔧 INITIATING SELF-HEALING PROCESS...")
                logger.warning(f"   - Consumer group: {self.config.consumer_group}")
                logger.warning(f"   - Kafka servers: {self.config.kafka_servers}")
                logger.warning(f"   - Current healing attempts: {self.self_healing.stats.total_healing_attempts}")
                
                healing_result = self.self_healing.detect_and_heal_issues("partition_assignment_failure")
                
                if healing_result:
                    logger.warning("✅ SELF-HEALING COMPLETED SUCCESSFULLY - retrying consumer creation...")
                    # Retry consumer creation with healing
                    return self._retry_task_consumer_with_healing()
                else:
                    logger.error("❌ SELF-HEALING FAILED - consumer cannot start")
                    logger.error(f"   - Healing attempts made: {self.self_healing.stats.total_healing_attempts}")
                    logger.error(f"   - Successful healings: {self.self_healing.stats.successful_healings}")
                    logger.error("   - Check healing logs above for detailed diagnostics")
                    return
            
            logger.info(f"📨 Consumer loop started - waiting for messages...")
            logger.info(f"🏷️  CONSUMER GROUP: {self.config.consumer_group}")
            
            # Health check variables like original implementation
            last_poll_time = time.time()
            poll_count = 0
            message_count = 0
            
            # Consumer loop with detailed logging
            while self._running:
                try:
                     # Check if consumer is still valid before polling
                    if not self.task_consumer or getattr(self.task_consumer, '_closed', False):
                        logger.warning("⚠️ Consumer closed during loop, exiting gracefully")
                        break

                    messages = self.task_consumer.poll(timeout_ms=100)
                    poll_count += 1
                    
                    # Configurable health check interval
                    current_time = time.time()
                    if current_time - last_poll_time > self.health_check_interval:
                        logger.info(f"🔄 Consumer health check (every {self.health_check_interval}s):")
                        logger.info(f"   📊 Last {self.health_check_interval}s: {poll_count} polls, {message_count} messages processed")
                        logger.info(f"   🏷️  CONSUMER GROUP: {self.config.consumer_group}")

                        # Include metadata in health check if provided
                        if self.metadata:
                            metadata_str = ", ".join([f"{k}: {v}" for k, v in self.metadata.items()])
                            logger.info(f"   Metadata: {metadata_str}")
                        
                        # Get partition assignment info
                        try:
                            assigned_partitions = self.task_consumer.assignment() if self.task_consumer else set()
                            logger.info(f"   📍 Assigned partitions ({len(assigned_partitions)}): {[f'{tp.topic}:{tp.partition}' for tp in assigned_partitions] if assigned_partitions else ['NONE']}")
                            logger.info(f"   ⏸️  Queue size: {self._tasks_queue.qsize()}")
                        except Exception as health_error:
                            logger.warning(f"   ❌ Health check failed: {str(health_error)[:100]}")
                        
                        last_poll_time = current_time
                        poll_count = 0
                        message_count = 0
                    
                    if messages:
                        for topic_partition, records in messages.items():
                            for record in records:
                                if not self._running:
                                    break
                                    
                                message_count += 1
                                try:
                                    task_data = record.value
                                    task = NinjaTaskRequest.from_dict(task_data)

                                    # Track commit info for manual commit after task completion
                                    correlation_id = task.correlation_id or task.message_id
                                    self._pending_commits[correlation_id] = {
                                        'partition': record.partition,
                                        'offset': record.offset,
                                        'topic': record.topic,
                                        'timestamp': time.time()
                                    }

                                    self._tasks_queue.put(task)

                                    logger.info(f"📩 Received message: {task.message_id} (pending commit)")
                                    logger.debug(f"✅ Task queued: {task.task} ({task.message_id[:8]}) - will commit after processing")

                                    # DON'T commit here - wait for task completion
                                    # self.task_consumer.commit()  # REMOVED for manual commit

                                except Exception as e:
                                    logger.error(f"❌ Error processing task: {e}")
                                    # For bad messages, still commit to avoid poison pill
                                    self.task_consumer.commit()
                                    logger.warning(f"⚠️ Committed bad message to avoid reprocessing")
                                    continue
                                
                except Exception as e:
                    if self._running:
                        logger.error(f"❌ Consumer poll error: {e}")
                        
                        # Recovery logic like original implementation
                        if "commit" in str(e).lower() or "timeout" in str(e).lower():
                            logger.warning("🔄 Detected commit/timeout error - attempting to recover consumer")
                            time.sleep(2)
                        else:
                            time.sleep(2)
                        
        except Exception as e:
            import traceback
            logger.error(f"Task consumer error: {str(e)}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
        finally:
            if self.task_consumer:
                self.task_consumer.close()
                logger.info("Task consumer closed")
    
    def _retry_task_consumer_with_healing(self):
        """
        Retry task consumer creation after healing.
        This creates a new consumer after self-healing has resolved issues.
        """
        logger.warning("🔄 RETRYING TASK CONSUMER CREATION AFTER HEALING...")
        logger.warning(f"   - Wait time: 5 seconds for healing effects to take place")
        logger.warning(f"   - Consumer group: {self.config.consumer_group}")
        logger.warning(f"   - Tasks topic: {self.config.tasks_topic}")
        
        try:
            # Brief wait to ensure healing changes take effect
            time.sleep(5)
            logger.warning("✅ HEALING WAIT COMPLETE - recreating task consumer...")
            
            # Re-run the consumer setup
            result = self._consume_tasks()
            logger.warning(f"🔄 CONSUMER RETRY RESULT: {result}")
            return result
            
        except Exception as e:
            logger.error(f"❌ TASK CONSUMER RETRY FAILED: {e}")
            logger.error(f"   - Exception type: {type(e).__name__}")
            logger.error(f"   - Exception message: {str(e)}")
            import traceback
            logger.error(f"   - Full traceback: {traceback.format_exc()}")
            return False
    
    
    
    def stop(self):
        """Stop all Kafka connections gracefully."""
        logger.info("🛑 Initiating graceful shutdown of NinjaClient...")
        logger.info("📊 Starting partition release process...")

        # Set running to False first to stop consumer loops
        self._running = False

        # Close task consumer first (most important for browser-ninja)
        if self.task_consumer:
            try:
                logger.info("📤 Closing task consumer and leaving consumer group...")
                logger.info(f"   Consumer group: {self.config.consumer_group}")

                # Log current partition assignment before closing
                released_count = 0
                try:
                    current_assignment = self.task_consumer.assignment()
                    if current_assignment:
                        partition_list = [f"{tp.topic}:{tp.partition}" for tp in current_assignment]
                        released_count = len(partition_list)
                        logger.info(f"   📍 Releasing {released_count} partitions: {partition_list}")
                    else:
                        logger.info("   📍 No partitions currently assigned")
                except:
                    pass

                # Unsubscribe to trigger immediate rebalance
                logger.info("   🔄 Unsubscribing from topics...")
                self.task_consumer.unsubscribe()
                logger.info("   ✅ Unsubscribed successfully")

                # Close consumer to leave group cleanly
                logger.info("   📤 Sending LeaveGroup request to Kafka...")
                self.task_consumer.close()
                self.task_consumer = None
                logger.info("✅ Task consumer closed and left consumer group")
                if released_count > 0:
                    logger.info(f"✨ Released {released_count} Kafka partitions for reassignment!")
                else:
                    logger.info("✨ Kafka consumer closed cleanly (no partitions were assigned)")
            except Exception as e:
                logger.error(f"Error closing task consumer: {e}")

        # Close results consumer if it exists
        if self.results_consumer:
            try:
                logger.info("📤 Closing results consumer...")
                self.results_consumer.unsubscribe()
                self.results_consumer.close()
                self.results_consumer = None
                logger.info("✅ Results consumer closed")
            except Exception as e:
                logger.error(f"Error closing results consumer: {e}")

        if self.task_consumer_thread and self.task_consumer_thread.is_alive():
            logger.info("⏳ Waiting for task consumer thread to finish...")
            self.task_consumer_thread.join(timeout=5)
            if not self.task_consumer_thread.is_alive():
                logger.info("✅ Task consumer thread stopped")
            else:
                logger.warning("⚠️ Task consumer thread did not stop within timeout")

        # Close producer last (after all consumers are done)
        if self.producer:
            try:
                logger.info("📤 Flushing and closing producer...")
                self.producer.flush(timeout=5)
                self.producer.close()
                self.producer = None
                logger.info("✅ Producer stopped")
            except Exception as e:
                logger.error(f"Error stopping producer: {e}")

        logger.info("✅ NinjaClient graceful shutdown complete")
    
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    # SelfHealingMixin interface methods
    def _get_consumer_group_id(self) -> str:
        """Get the consumer group ID for self-healing operations."""
        return self.config.consumer_group
    
    def _get_bootstrap_servers(self) -> str:
        """Get the bootstrap servers for self-healing operations."""
        return self.config.kafka_servers