"""
Message models for Ninja Kafka SDK.
"""

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List


@dataclass
class NinjaTaskRequest:
    """Request message for Ninja task execution."""
    task: str
    account_id: int
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    email: Optional[str] = None
    user_id: Optional[int] = None
    retry_count: int = 0
    version: str = "1.0"
    api_endpoints: Optional[Dict[str, str]] = None
    parameters: Optional[Dict[str, Any]] = None  # Task-specific parameters
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for Kafka serialization."""
        result = {
            'message_id': self.message_id,
            'correlation_id': self.correlation_id,
            'timestamp': self.timestamp,
            'retry_count': self.retry_count,
            'task': self.task,
            'version': self.version,
            'account_id': self.account_id,
            'user_id': self.user_id,
            'email': self.email,
            'api_endpoints': self.api_endpoints,
            'parameters': self.parameters
        }
        # Safely handle metadata - ensure it's a dict before spreading
        if isinstance(self.metadata, dict):
            result.update(self.metadata)
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NinjaTaskRequest':
        """Create from dictionary."""
        # Extract known fields
        known_fields = {
            'message_id', 'correlation_id', 'timestamp', 'retry_count',
            'task', 'version', 'account_id', 'user_id', 'email', 'api_endpoints', 'parameters', 'metadata'
        }

        kwargs = {k: v for k, v in data.items() if k in known_fields}

        # Handle metadata specially - ensure it's always a dict
        if 'metadata' in kwargs:
            # If metadata is not a dict, convert it or use empty dict
            if not isinstance(kwargs['metadata'], dict):
                kwargs['metadata'] = {}
        else:
            # Collect unknown fields as metadata
            metadata = {k: v for k, v in data.items() if k not in known_fields}
            kwargs['metadata'] = metadata

        return cls(**kwargs)


@dataclass 
class NinjaTaskResult:
    """Result message from Ninja task execution."""
    correlation_id: str
    task: str
    status: str
    account_id: Optional[int] = None
    success: bool = False
    timestamp: Optional[str] = None
    source: str = "ninja"
    version: str = "1.0"
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, str]] = None
    metrics: Optional[Dict[str, Any]] = None

    @property
    def is_success(self) -> bool:
        """Check if task was successful."""
        return self.success

    @property
    def error_message(self) -> Optional[str]:
        """Get error message if failed."""
        if self.error:
            return self.error.get('message') or self.error.get('error_message')
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NinjaTaskResult':
        """Create from dictionary."""
        # Handle nested payload data
        payload = data.get('payload', {})
        if payload and not data.get('data'):
            data['data'] = payload
            
        return cls(
            correlation_id=data.get('correlation_id', ''),
            task=data.get('task', 'unknown'),
            status=data.get('status', 'unknown'),
            account_id=data.get('account_id'),
            success=data.get('success', False),
            timestamp=data.get('timestamp'),
            source=data.get('source', 'ninja'),
            version=data.get('version', '1.0'),
            data=data.get('data'),
            error=data.get('error'),
            metrics=data.get('metrics')
        )


@dataclass
class NinjaTaskProgress:
    """Progress update from Ninja task."""
    correlation_id: str
    status: str
    message: str
    progress_percentage: Optional[int] = None
    timestamp: Optional[str] = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NinjaTaskProgress':
        """Create from dictionary."""
        return cls(
            correlation_id=data.get('correlation_id', ''),
            status=data.get('status', ''),
            message=data.get('message', ''),
            progress_percentage=data.get('progress'),
            timestamp=data.get('timestamp')
        )