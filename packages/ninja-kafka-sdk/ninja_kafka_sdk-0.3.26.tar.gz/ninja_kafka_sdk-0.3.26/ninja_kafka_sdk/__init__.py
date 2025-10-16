"""
Ninja Kafka SDK - Simplified Kafka communication for Ninja services.

A lean SDK for distributed task processing with Kafka messaging.
Provides a simple, unified API for sending tasks and receiving results.
"""

from .client import NinjaClient
from .models import NinjaTaskRequest, NinjaTaskResult
from .exceptions import NinjaKafkaError, NinjaTaskTimeoutError

__version__ = "0.3.26"
__all__ = ["NinjaClient", "NinjaTaskRequest", "NinjaTaskResult", "NinjaKafkaError", "NinjaTaskTimeoutError"]