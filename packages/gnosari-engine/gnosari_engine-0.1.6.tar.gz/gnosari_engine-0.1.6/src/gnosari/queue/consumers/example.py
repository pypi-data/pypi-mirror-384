"""Example message and consumer implementation."""

import uuid
from typing import Dict, Any
from pydantic import Field
from ..base import BaseMessage, BaseConsumer
from ..app import celery_app
import asyncio


class ExampleMessage(BaseMessage):
    """Example message for demonstrating the queue system."""
    
    user_id: str = Field(description="User ID who triggered this task")
    action: str = Field(description="Action to perform")
    data: Dict[str, Any] = Field(default_factory=dict, description="Additional data for the task")
    
    @classmethod
    def create(cls, user_id: str, action: str, data: Dict[str, Any] = None) -> "ExampleMessage":
        """Create a new example message.
        
        Args:
            user_id: User ID who triggered this task
            action: Action to perform
            data: Additional data for the task
            
        Returns:
            ExampleMessage: New message instance
        """
        return cls(
            message_id=str(uuid.uuid4()),
            user_id=user_id,
            action=action,
            data=data or {}
        )


class ExampleConsumer(BaseConsumer):
    """Example consumer for processing example messages."""
    
    async def process(self, message: ExampleMessage) -> Dict[str, Any]:
        """Process an example message.
        
        Args:
            message: The example message to process
            
        Returns:
            Dict[str, Any]: Processing result
        """
        print(f"Processing message {message.message_id}")
        print(f"User: {message.user_id}")
        print(f"Action: {message.action}")
        print(f"Data: {message.data}")
        
        # Simulate some async work
        await asyncio.sleep(1)
        
        # Simulate different actions
        if message.action == "greet":
            result = f"Hello, user {message.user_id}!"
        elif message.action == "calculate":
            x = message.data.get("x", 0)
            y = message.data.get("y", 0)
            result = x + y
        elif message.action == "fail":
            raise ValueError("This task is designed to fail for testing")
        else:
            result = f"Unknown action: {message.action}"
        
        return {
            "message_id": message.message_id,
            "result": result,
            "processed_at": message.created_at.isoformat()
        }
    
    def on_success(self, result: Dict[str, Any], message: ExampleMessage) -> None:
        """Called when message processing succeeds."""
        print(f"✅ Successfully processed message {message.message_id}: {result}")
    
    def on_failure(self, exc: Exception, message: ExampleMessage) -> None:
        """Called when message processing fails."""
        print(f"❌ Failed to process message {message.message_id}: {exc}")


@celery_app.task(bind=True)
def process_example_task(self, message_data: Dict[str, Any]) -> Dict[str, Any]:
    """Celery task for processing example messages.
    
    Args:
        message_data: Serialized example message data
        
    Returns:
        Dict[str, Any]: Processing result
    """
    consumer = ExampleConsumer()
    message = ExampleMessage.from_dict(message_data)
    
    try:
        # Run async process method
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(consumer.process(message))
        loop.close()
        
        consumer.on_success(result, message)
        return result
    except Exception as exc:
        consumer.on_failure(exc, message)
        
        if consumer.should_retry(exc, message):
            message.retry_count += 1
            # Retry with exponential backoff
            raise self.retry(
                countdown=2 ** message.retry_count,
                max_retries=message.max_retries
            )
        raise


def send_example_message(user_id: str, action: str, data: Dict[str, Any] = None) -> str:
    """Send an example message to the queue.
    
    Args:
        user_id: User ID who triggered this task
        action: Action to perform
        data: Additional data for the task
        
    Returns:
        str: Message ID
    """
    message = ExampleMessage.create(user_id, action, data)
    process_example_task.delay(message.to_dict())
    return message.message_id