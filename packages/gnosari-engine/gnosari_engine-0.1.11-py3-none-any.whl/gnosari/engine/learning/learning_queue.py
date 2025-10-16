"""Learning queue system for handling learning events and updates."""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class LearningEventType(str, Enum):
    """Types of learning events that can be queued."""
    LEARNING_ADDED = "learning_added"
    LEARNING_UPDATED = "learning_updated"
    LEARNING_APPLIED = "learning_applied"
    LEARNING_REMOVED = "learning_removed"
    AGENT_LEARNING_REQUEST = "agent_learning_request"


@dataclass
class LearningEvent:
    """Learning event for queue processing."""
    event_type: LearningEventType
    agent_id: str
    team_path: str
    learning_data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'event_type': self.event_type.value,
            'agent_id': self.agent_id,
            'team_path': self.team_path,
            'learning_data': self.learning_data,
            'metadata': self.metadata or {},
            'timestamp': self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LearningEvent':
        """Create event from dictionary."""
        return cls(
            event_type=LearningEventType(data['event_type']),
            agent_id=data['agent_id'],
            team_path=data['team_path'],
            learning_data=data['learning_data'],
            metadata=data.get('metadata'),
            timestamp=data.get('timestamp')
        )


class LearningQueueManager:
    """Manages learning event queues and processing."""
    
    def __init__(self, max_queue_size: int = 1000):
        self.max_queue_size = max_queue_size
        self.event_queue: asyncio.Queue = asyncio.Queue(maxsize=max_queue_size)
        self.subscribers: Dict[str, List[Callable]] = {}
        self.running = False
        self.processor_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start the queue processor."""
        if self.running:
            return
        
        self.running = True
        self.processor_task = asyncio.create_task(self._process_events())
        logger.info("Learning queue manager started")
    
    async def stop(self):
        """Stop the queue processor."""
        if not self.running:
            return
        
        self.running = False
        if self.processor_task:
            self.processor_task.cancel()
            try:
                await self.processor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Learning queue manager stopped")
    
    async def publish_event(self, event: LearningEvent):
        """Publish a learning event to the queue."""
        try:
            await self.event_queue.put(event)
            logger.debug(f"Published learning event: {event.event_type.value} for agent {event.agent_id}")
        except asyncio.QueueFull:
            logger.error(f"Learning queue is full, dropping event: {event.event_type.value}")
    
    def subscribe(self, event_type: LearningEventType, callback: Callable[[LearningEvent], None]):
        """Subscribe to learning events of a specific type."""
        if event_type.value not in self.subscribers:
            self.subscribers[event_type.value] = []
        
        self.subscribers[event_type.value].append(callback)
        logger.debug(f"Subscribed to learning events: {event_type.value}")
    
    def unsubscribe(self, event_type: LearningEventType, callback: Callable[[LearningEvent], None]):
        """Unsubscribe from learning events."""
        if event_type.value in self.subscribers:
            try:
                self.subscribers[event_type.value].remove(callback)
                logger.debug(f"Unsubscribed from learning events: {event_type.value}")
            except ValueError:
                pass
    
    async def _process_events(self):
        """Process events from the queue."""
        while self.running:
            try:
                # Wait for events with timeout to allow periodic checks
                event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                await self._handle_event(event)
                self.event_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing learning event: {e}")
    
    async def _handle_event(self, event: LearningEvent):
        """Handle a learning event by notifying subscribers."""
        event_type = event.event_type.value
        
        if event_type in self.subscribers:
            for callback in self.subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    logger.error(f"Error in learning event callback: {e}")
        
        logger.debug(f"Handled learning event: {event_type} for agent {event.agent_id}")


class LearningEventPublisher:
    """Helper class for publishing learning events."""
    
    def __init__(self, queue_manager: LearningQueueManager):
        self.queue_manager = queue_manager
    
    async def publish_learning_added(self, agent_id: str, team_path: str, learning_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Publish a learning added event."""
        event = LearningEvent(
            event_type=LearningEventType.LEARNING_ADDED,
            agent_id=agent_id,
            team_path=team_path,
            learning_data=learning_data,
            metadata=metadata
        )
        await self.queue_manager.publish_event(event)
    
    async def publish_learning_updated(self, agent_id: str, team_path: str, learning_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Publish a learning updated event."""
        event = LearningEvent(
            event_type=LearningEventType.LEARNING_UPDATED,
            agent_id=agent_id,
            team_path=team_path,
            learning_data=learning_data,
            metadata=metadata
        )
        await self.queue_manager.publish_event(event)
    
    async def publish_learning_applied(self, agent_id: str, team_path: str, learning_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Publish a learning applied event."""
        event = LearningEvent(
            event_type=LearningEventType.LEARNING_APPLIED,
            agent_id=agent_id,
            team_path=team_path,
            learning_data=learning_data,
            metadata=metadata
        )
        await self.queue_manager.publish_event(event)
    
    async def publish_agent_learning_request(self, agent_id: str, team_path: str, learning_data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """Publish an agent learning request event."""
        event = LearningEvent(
            event_type=LearningEventType.AGENT_LEARNING_REQUEST,
            agent_id=agent_id,
            team_path=team_path,
            learning_data=learning_data,
            metadata=metadata
        )
        await self.queue_manager.publish_event(event)


# Global learning queue manager instance
_learning_queue_manager: Optional[LearningQueueManager] = None


def get_learning_queue_manager() -> LearningQueueManager:
    """Get the global learning queue manager instance."""
    global _learning_queue_manager
    if _learning_queue_manager is None:
        _learning_queue_manager = LearningQueueManager()
    return _learning_queue_manager


async def initialize_learning_queue():
    """Initialize and start the global learning queue manager."""
    queue_manager = get_learning_queue_manager()
    await queue_manager.start()
    return queue_manager


async def shutdown_learning_queue():
    """Shutdown the global learning queue manager."""
    global _learning_queue_manager
    if _learning_queue_manager:
        await _learning_queue_manager.stop()
        _learning_queue_manager = None