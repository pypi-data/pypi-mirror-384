"""
Custom exceptions for Ninja Kafka SDK.
"""


class NinjaKafkaError(Exception):
    """Base exception for all Ninja Kafka SDK errors."""
    pass


class NinjaKafkaConnectionError(NinjaKafkaError):
    """Raised when cannot connect to Kafka."""
    pass


class NinjaTaskTimeoutError(NinjaKafkaError):
    """Raised when task execution times out."""
    pass


class NinjaTaskError(NinjaKafkaError):
    """Raised when Ninja service reports task failure."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}


class NinjaConfigurationError(NinjaKafkaError):
    """Raised when SDK configuration is invalid."""
    pass