"""Base classes for Gnosari queue system messages and consumers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, TypeVar
from pydantic import BaseModel, Field
from celery import Task
from datetime import datetime


class BaseMessage(BaseModel):
    """Base class for all queue messages.
    
    All messages should inherit from this class and define their payload structure.
    This ensures consistent serialization and validation across the queue system.
    """
    
    message_id: str = Field(description="Unique identifier for this message")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Message creation timestamp")
    priority: int = Field(default=5, description="Message priority (1-10, lower is higher priority)")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum number of retries allowed")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        data = self.model_dump()
        # Convert datetime to ISO string for JSON serialization
        if 'created_at' in data and isinstance(data['created_at'], datetime):
            data['created_at'] = data['created_at'].isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseMessage":
        """Create message from dictionary."""
        return cls(**data)


MessageType = TypeVar("MessageType", bound=BaseMessage)


class BaseConsumer(ABC):
    """Base class for all message consumers.
    
    Each consumer should inherit from this class and implement the process method.
    This ensures consistent error handling and logging across all consumers.
    """
    
    def __init__(self):
        """Initialize consumer."""
        self.name = self.__class__.__name__
    
    @abstractmethod
    async def process(self, message: MessageType) -> Any:
        """Process a message.
        
        Args:
            message: The message to process
            
        Returns:
            Any: Processing result
            
        Raises:
            Exception: If processing fails
        """
        pass
    
    def on_success(self, result: Any, message: MessageType) -> None:
        """Called when message processing succeeds.
        
        Args:
            result: The processing result
            message: The processed message
        """
        pass
    
    def on_failure(self, exc: Exception, message: MessageType) -> None:
        """Called when message processing fails.
        
        Args:
            exc: The exception that occurred
            message: The message that failed to process
        """
        pass
    
    def should_retry(self, exc: Exception, message: MessageType) -> bool:
        """Determine if a failed message should be retried.
        
        Args:
            exc: The exception that occurred
            message: The message that failed
            
        Returns:
            bool: True if should retry, False otherwise
        """
        return message.retry_count < message.max_retries


class ConsumerTask(Task):
    """Custom Celery task class for consumers."""
    
    def __init__(self, consumer_class: type[BaseConsumer]):
        """Initialize task with consumer class.
        
        Args:
            consumer_class: The consumer class to instantiate
        """
        self.consumer_class = consumer_class
        self.consumer_instance = None
    
    def get_consumer(self) -> BaseConsumer:
        """Get or create consumer instance."""
        if self.consumer_instance is None:
            self.consumer_instance = self.consumer_class()
        return self.consumer_instance
    
    async def run(self, message_data: Dict[str, Any], message_class: type[BaseMessage]) -> Any:
        """Run the consumer task.
        
        Args:
            message_data: Serialized message data
            message_class: Message class to deserialize to
            
        Returns:
            Any: Processing result
        """
        consumer = self.get_consumer()
        message = message_class.from_dict(message_data)
        
        try:
            result = await consumer.process(message)
            consumer.on_success(result, message)
            return result
        except Exception as exc:
            consumer.on_failure(exc, message)
            
            if consumer.should_retry(exc, message):
                message.retry_count += 1
                # Re-queue the message with updated retry count
                raise self.retry(
                    args=[message.to_dict(), message_class],
                    countdown=2 ** message.retry_count,  # Exponential backoff
                    max_retries=message.max_retries
                )
            raise