"""
Unified event sender utility for all event types.
"""

import json
import uuid
import logging
from typing import Dict, Any
from datetime import datetime, timezone
from agents import RunContextWrapper
from pydantic import BaseModel

from ..schemas.event import EventMessage, create_event

logger = logging.getLogger(__name__)


class EventSender:
    """Unified event sender for all event types."""
    
    @staticmethod
    def send_event_to_queue(event: EventMessage, context: RunContextWrapper[Any] = None) -> str:
        """Send event to the gnosari-events queue.
        
        Args:
            event: Event message to send
            context: Optional execution context
            
        Returns:
            str: Message ID
        """
        try:
            # Import here to avoid circular imports
            from ..queue.consumers.event import celery_app
            
            # Convert event to dict for serialization
            event_dict = event.model_dump()
            
            # Convert datetime objects to ISO format strings
            for key, value in event_dict.items():
                if hasattr(value, 'isoformat'):  # datetime object
                    event_dict[key] = value.isoformat()
            
            # Send to the unified event processor
            task = celery_app.send_task(
                'gnosari.queue.consumers.event.process_event_message',
                args=[event_dict],
                queue='gnosari-events',
                priority=event.priority
            )
            
            message_id = task.id
            logger.info(f"Event {event.event_id} sent to queue with message ID {message_id}")
            
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to send event to queue: {e}")
            raise
    
    @staticmethod
    def create_and_send_event(event_type: str, context_data: BaseModel, 
                            source: str = "system", priority: int = 5,
                            metadata: Dict[str, Any] = None,
                            execution_context: RunContextWrapper[Any] = None,
                            session: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create and send an event in one operation.
        
        Args:
            event_type: Type of event
            context_data: Event context data
            source: Event source identifier
            priority: Event priority
            metadata: Additional metadata
            execution_context: Optional execution context
            session: Session context information
            
        Returns:
            Dict: Event sending result
        """
        try:
            # Create event
            event = create_event(
                event_type=event_type,
                context=context_data,
                source=source,
                priority=priority,
                metadata=metadata,
                session=session
            )
            
            # Send to queue
            message_id = EventSender.send_event_to_queue(event, execution_context)
            
            # Queue OpenSearch indexing asynchronously when sent
            try:
                # Import here to avoid circular imports
                from ..queue.consumers.event import celery_app
                
                celery_app.send_task(
                    'gnosari.queue.consumers.event.index_event_in_opensearch',
                    args=[event.model_dump()],
                    queue='gnosari-events',
                    priority=8  # Lower priority for indexing
                )
                logger.debug(f"Queued OpenSearch indexing for sent event {event.event_id}")
            except Exception as queue_error:
                logger.warning(f"Failed to queue OpenSearch indexing for sent event {event.event_id}: {queue_error}")
                # Don't fail the send operation if queuing fails
            
            return {
                "status": "success",
                "event_id": event.event_id,
                "event_type": event.event_type,
                "message_id": message_id,
                "message": f"Event '{event.event_type}' queued for processing",
                "published_at": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to send event: {str(e)}",
                "error": str(e)
            }