"""
Auto-configuration for Ninja Kafka SDK.
Detects environment and sets appropriate Kafka settings.
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from kafka.coordinator.assignors.roundrobin import RoundRobinPartitionAssignor

logger = logging.getLogger(__name__)


class NinjaKafkaConfig:
    """Explicit configuration for Ninja Kafka SDK."""
    
    def __init__(
        self,
        kafka_servers: str,
        consumer_group: str,
        environment: Optional[str] = None,
        tasks_topic: str = 'ninja-tasks',
        results_topic: str = 'ninja-results'
    ):
        """
        Initialize Ninja Kafka configuration.
        
        Args:
            kafka_servers: REQUIRED. Kafka bootstrap servers (e.g., 'localhost:9092' or 'broker1:9092,broker2:9092')
            consumer_group: REQUIRED. Consumer group for this client
            environment: Optional environment name for logging only
            tasks_topic: Topic name for sending tasks
            results_topic: Topic name for receiving results
            
        Example:
            # Local development
            config = NinjaKafkaConfig(
                kafka_servers='localhost:9092',
                consumer_group='my-service'
            )
            
            # Production/cloud
            config = NinjaKafkaConfig(
                kafka_servers='broker1:9092,broker2:9092,broker3:9092',
                consumer_group='my-service-prod'
            )
        """
        if not kafka_servers:
            raise ValueError("kafka_servers is required. SDK is environment-agnostic and requires explicit broker configuration.")
        if not consumer_group:
            raise ValueError("consumer_group is required. Specify the consumer group for your application.")
            
        self.kafka_servers = kafka_servers
        self.consumer_group = consumer_group
        self.environment = environment or "unknown"
        self.tasks_topic = tasks_topic
        self.results_topic = results_topic
        self.producer_settings = self._get_producer_settings()
        self.consumer_settings = self._get_consumer_settings()
        
        logger.info(f"Ninja Kafka SDK configured")
        logger.info(f"Kafka servers: {self.kafka_servers}")
        logger.info(f"Consumer group: {self.consumer_group}")
        logger.info(f"Environment: {self.environment}")
    
    
    def _get_producer_settings(self) -> Dict[str, Any]:
        """Get default producer settings."""
        return {
            'acks': 1,
            'retries': 10,
            'retry_backoff_ms': 1000,
            'request_timeout_ms': 60000,
            'delivery_timeout_ms': 120000,
            'linger_ms': 0,
            'batch_size': 16384,
            'buffer_memory': 33554432,
            'metadata_max_age_ms': 60000,
            'max_in_flight_requests_per_connection': 5
        }
    
    def _get_consumer_settings(self) -> Dict[str, Any]:
        """Get optimized consumer settings for MSK/Kafka."""
        import socket
        import os

        # Generate static member ID based on hostname + consumer group
        # This ensures the same consumer always gets the same member ID
        hostname = socket.gethostname()
        static_member_id = f"{hostname}-{self.consumer_group}"

        # Support environment override for multi-instance scenarios
        if os.getenv('KAFKA_STATIC_INSTANCE_ID'):
            static_member_id = f"{hostname}-{self.consumer_group}-{os.getenv('KAFKA_STATIC_INSTANCE_ID')}"

        consumer_config = {
            'auto_offset_reset': 'earliest',
            'enable_auto_commit': False,  # Manual commit for reliability
            'max_poll_records': 1,
            'consumer_timeout_ms': 5000,
            # Faster timeouts for quicker rebalancing
            'session_timeout_ms': 10000,      # 10s session timeout (faster failure detection)
            'heartbeat_interval_ms': 3000,    # 3s heartbeat (1/3 of session)
            'max_poll_interval_ms': 120000,   # 2 min max poll interval (sufficient for processing)
            'request_timeout_ms': 30000,      # 30s request timeout (> session timeout)
            # Connection stability
            'connections_max_idle_ms': 540000,  # 9 min max idle
            'reconnect_backoff_ms': 50,
            'reconnect_backoff_max_ms': 1000,
            'retry_backoff_ms': 100,
            # Partition assignment strategy - import classes not strings
            'partition_assignment_strategy': [RoundRobinPartitionAssignor],  # Better for multi-instance
            # API version for MSK compatibility
            'api_version': (0, 10, 1)
        }

        # Note: group_instance_id (static membership) and cooperative rebalancing
        # are not supported by kafka-python library. These features require
        # the Java client or confluent-kafka-python.
        # For now, we rely on the optimized timeouts to minimize rebalancing issues.

        return consumer_config