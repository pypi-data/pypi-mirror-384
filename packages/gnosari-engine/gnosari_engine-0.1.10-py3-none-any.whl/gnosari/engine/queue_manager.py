"""Queue manager for dynamic queue creation and management in Gnosari AI Teams.

This module provides the QueueManager class that handles dynamic queue creation,
configuration, and lifecycle management for the event system.
"""

import asyncio
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

import redis.asyncio as redis
from celery import Celery

from ..schemas.event import (
    QueueConfig, 
    EventMessage, 
    EventSystemError,
    QueueConfigurationError
)
from ..utils.logging import get_logger


logger = get_logger(__name__)


class QueueManager:
    """Manages dynamic queue creation, configuration, and lifecycle."""
    
    def __init__(self, celery_app: Celery, redis_client: redis.Redis):
        """Initialize the queue manager.
        
        Args:
            celery_app: Celery application instance
            redis_client: Redis client for queue operations
        """
        self.celery_app = celery_app
        self.redis_client = redis_client
        self.configured_queues: Dict[str, QueueConfig] = {}
        self.active_queues: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
        
        # Queue monitoring
        self._stats_cache: Dict[str, Any] = {}
        self._stats_cache_ttl = 60  # seconds
        self._last_stats_update = datetime.min
        
    async def create_queue(self, config: QueueConfig) -> bool:
        """Create a new queue with the specified configuration.
        
        Args:
            config: Queue configuration
            
        Returns:
            bool: True if queue was created successfully
            
        Raises:
            QueueConfigurationError: If queue creation fails
        """
        async with self._lock:
            try:
                # Validate configuration
                await self._validate_queue_config(config)
                
                # Check if queue already exists
                if config.name in self.configured_queues:
                    logger.warning(f"Queue {config.name} already exists, updating configuration")
                
                # Store configuration
                self.configured_queues[config.name] = config
                
                # Create queue metadata in Redis
                queue_metadata = {
                    "name": config.name,
                    "priority": config.priority,
                    "max_retries": config.max_retries,
                    "retry_delay": config.retry_delay,
                    "dead_letter_queue": config.dead_letter_queue,
                    "routing_key": config.routing_key,
                    "created_at": datetime.utcnow().isoformat(),
                    "status": "active"
                }
                
                await self.redis_client.hset(
                    f"gnosari:queue:metadata:{config.name}",
                    mapping=queue_metadata
                )
                
                # Initialize queue statistics
                await self._initialize_queue_stats(config.name)
                
                # Configure Celery routing
                await self._configure_celery_routing(config)
                
                self.active_queues[config.name] = queue_metadata
                
                logger.info(f"Created queue {config.name} with priority {config.priority}")
                return True
                
            except Exception as e:
                logger.error(f"Failed to create queue {config.name}: {e}")
                raise QueueConfigurationError(
                    f"Queue creation failed: {e}",
                    error_code="QUEUE_CREATION_ERROR"
                )
    
    async def delete_queue(self, queue_name: str, force: bool = False) -> bool:
        """Delete a queue and its associated data.
        
        Args:
            queue_name: Name of the queue to delete
            force: Force deletion even if queue has pending messages
            
        Returns:
            bool: True if queue was deleted successfully
        """
        async with self._lock:
            try:
                if queue_name not in self.configured_queues:
                    logger.warning(f"Queue {queue_name} does not exist")
                    return True
                
                # Check for pending messages unless forced
                if not force:
                    pending_count = await self.get_queue_size(queue_name)
                    if pending_count > 0:
                        raise QueueConfigurationError(
                            f"Queue {queue_name} has {pending_count} pending messages. Use force=True to delete anyway.",
                            error_code="QUEUE_NOT_EMPTY"
                        )
                
                # Remove from configuration
                del self.configured_queues[queue_name]
                
                # Remove from active queues
                if queue_name in self.active_queues:
                    del self.active_queues[queue_name]
                
                # Clean up Redis metadata
                await self.redis_client.delete(f"gnosari:queue:metadata:{queue_name}")
                await self.redis_client.delete(f"gnosari:queue:stats:{queue_name}")
                
                # Clean up any remaining messages in Redis (if using Redis as broker)
                await self.redis_client.delete(f"celery:{queue_name}")
                await self.redis_client.delete(f"_kombu.binding.celery:{queue_name}")
                
                logger.info(f"Deleted queue {queue_name}")
                return True
                
            except QueueConfigurationError:
                raise
            except Exception as e:
                logger.error(f"Failed to delete queue {queue_name}: {e}")
                return False
    
    async def publish_to_queue(self, queue_name: str, event: EventMessage) -> str:
        """Publish an event to a specific queue.
        
        Args:
            queue_name: Name of the target queue
            event: Event message to publish
            
        Returns:
            str: Event ID of the published event
            
        Raises:
            QueueConfigurationError: If queue doesn't exist or publishing fails
        """
        try:
            if queue_name not in self.configured_queues:
                raise QueueConfigurationError(
                    f"Queue {queue_name} is not configured",
                    error_code="QUEUE_NOT_FOUND"
                )
            
            config = self.configured_queues[queue_name]
            
            # Prepare message for Celery
            message_data = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "source": event.source,
                "data": event.data,
                "metadata": event.metadata,
                "timestamp": event.timestamp.isoformat(),
                "priority": event.priority,
                "broadcast": event.broadcast,
                "target_teams": event.target_teams,
                "correlation_id": event.correlation_id
            }
            
            # Send to Celery queue with priority and routing
            task_options = {
                "queue": queue_name,
                "priority": 10 - event.priority,  # Celery uses 0-9, higher is more priority
                "retry": True,
                "retry_policy": {
                    "max_retries": config.max_retries,
                    "interval_start": config.retry_delay,
                    "interval_step": config.retry_delay,
                    "interval_max": config.retry_delay * 3
                }
            }
            
            # Apply routing key if configured
            if config.routing_key:
                task_options["routing_key"] = config.routing_key
            
            # Send task to process event
            self.celery_app.send_task(
                "gnosari.queue.consumers.event.process_event",
                args=[message_data],
                **task_options
            )
            
            # Update queue statistics
            await self._update_queue_stats(queue_name, "published")
            
            logger.debug(f"Published event {event.event_id} to queue {queue_name}")
            return event.event_id
            
        except QueueConfigurationError:
            raise
        except Exception as e:
            logger.error(f"Failed to publish event {event.event_id} to queue {queue_name}: {e}")
            raise QueueConfigurationError(
                f"Event publishing failed: {e}",
                error_code="PUBLISH_ERROR",
                event_id=event.event_id
            )
    
    async def get_queue_size(self, queue_name: str) -> int:
        """Get the number of pending messages in a queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            int: Number of pending messages
        """
        try:
            # Use Celery's inspect to get queue length
            inspect = self.celery_app.control.inspect()
            active_queues = inspect.active_queues()
            
            if not active_queues:
                return 0
            
            # Sum up messages across all workers for this queue
            total_size = 0
            for worker, queues in active_queues.items():
                for queue_info in queues:
                    if queue_info.get("name") == queue_name:
                        total_size += queue_info.get("messages", 0)
            
            return total_size
            
        except Exception as e:
            logger.error(f"Failed to get queue size for {queue_name}: {e}")
            return 0
    
    async def get_queue_stats(self, queue_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed statistics for a queue.
        
        Args:
            queue_name: Name of the queue
            
        Returns:
            Dict: Queue statistics or None if queue doesn't exist
        """
        try:
            if queue_name not in self.configured_queues:
                return None
            
            # Get metadata
            metadata = await self.redis_client.hgetall(f"gnosari:queue:metadata:{queue_name}")
            if not metadata:
                return None
            
            # Get statistics
            stats = await self.redis_client.hgetall(f"gnosari:queue:stats:{queue_name}")
            
            # Get current queue size
            current_size = await self.get_queue_size(queue_name)
            
            # Convert byte strings to appropriate types
            processed_metadata = {k.decode(): v.decode() for k, v in metadata.items()}
            processed_stats = {}
            
            for k, v in stats.items():
                key = k.decode()
                value = v.decode()
                try:
                    # Try to convert to int if it's a number
                    processed_stats[key] = int(value)
                except ValueError:
                    processed_stats[key] = value
            
            return {
                "queue_name": queue_name,
                "config": processed_metadata,
                "current_size": current_size,
                "stats": processed_stats,
                "last_updated": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue stats for {queue_name}: {e}")
            return None
    
    async def list_queues(self) -> List[Dict[str, Any]]:
        """List all configured queues with their basic information.
        
        Returns:
            List[Dict]: List of queue information
        """
        queues = []
        
        for queue_name, config in self.configured_queues.items():
            queue_info = {
                "name": queue_name,
                "priority": config.priority,
                "max_retries": config.max_retries,
                "retry_delay": config.retry_delay,
                "routing_key": config.routing_key,
                "dead_letter_queue": config.dead_letter_queue,
                "current_size": await self.get_queue_size(queue_name),
                "status": "active" if queue_name in self.active_queues else "inactive"
            }
            queues.append(queue_info)
        
        return sorted(queues, key=lambda x: x["priority"])
    
    async def purge_queue(self, queue_name: str) -> int:
        """Purge all messages from a queue.
        
        Args:
            queue_name: Name of the queue to purge
            
        Returns:
            int: Number of messages purged
        """
        try:
            if queue_name not in self.configured_queues:
                raise QueueConfigurationError(
                    f"Queue {queue_name} is not configured",
                    error_code="QUEUE_NOT_FOUND"
                )
            
            # Use Celery's control to purge the queue
            self.celery_app.control.purge()
            
            # Update statistics
            await self._update_queue_stats(queue_name, "purged")
            
            logger.info(f"Purged queue {queue_name}")
            return 0  # Celery doesn't return count for purge
            
        except Exception as e:
            logger.error(f"Failed to purge queue {queue_name}: {e}")
            raise QueueConfigurationError(
                f"Queue purge failed: {e}",
                error_code="PURGE_ERROR"
            )
    
    async def _validate_queue_config(self, config: QueueConfig) -> None:
        """Validate queue configuration parameters.
        
        Args:
            config: Queue configuration to validate
            
        Raises:
            QueueConfigurationError: If configuration is invalid
        """
        # Basic validation is handled by Pydantic, but we can add business logic here
        
        # Check for reserved queue names
        reserved_names = {"celery", "kombu", "gnosari_system"}
        if config.name.lower() in reserved_names:
            raise QueueConfigurationError(
                f"Queue name '{config.name}' is reserved",
                error_code="RESERVED_QUEUE_NAME"
            )
        
        # Validate dead letter queue exists if specified
        if config.dead_letter_queue:
            if config.dead_letter_queue == config.name:
                raise QueueConfigurationError(
                    "Dead letter queue cannot be the same as the main queue",
                    error_code="INVALID_DEAD_LETTER_QUEUE"
                )
    
    async def _initialize_queue_stats(self, queue_name: str) -> None:
        """Initialize statistics tracking for a queue.
        
        Args:
            queue_name: Name of the queue
        """
        initial_stats = {
            "published_count": 0,
            "processed_count": 0,
            "failed_count": 0,
            "retry_count": 0,
            "purged_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "last_activity": datetime.utcnow().isoformat()
        }
        
        await self.redis_client.hset(
            f"gnosari:queue:stats:{queue_name}",
            mapping=initial_stats
        )
    
    async def _update_queue_stats(self, queue_name: str, operation: str) -> None:
        """Update statistics for a queue operation.
        
        Args:
            queue_name: Name of the queue
            operation: Type of operation (published, processed, failed, etc.)
        """
        try:
            stats_key = f"gnosari:queue:stats:{queue_name}"
            
            # Update specific counter
            counter_field = f"{operation}_count"
            await self.redis_client.hincrby(stats_key, counter_field, 1)
            
            # Update last activity timestamp
            await self.redis_client.hset(
                stats_key,
                "last_activity",
                datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Failed to update stats for queue {queue_name}: {e}")
    
    async def _configure_celery_routing(self, config: QueueConfig) -> None:
        """Configure Celery routing for the queue.
        
        Args:
            config: Queue configuration
        """
        try:
            # Update Celery routing configuration
            routing_key = config.routing_key or config.name
            
            # Add queue to Celery's routing table
            if not hasattr(self.celery_app.conf, 'task_routes'):
                self.celery_app.conf.task_routes = {}
            
            # Configure routing for event processing task
            route_pattern = f"gnosari.queue.consumers.event.process_event"
            if route_pattern not in self.celery_app.conf.task_routes:
                self.celery_app.conf.task_routes[route_pattern] = {
                    'queue': config.name,
                    'routing_key': routing_key
                }
            
            logger.debug(f"Configured Celery routing for queue {config.name}")
            
        except Exception as e:
            logger.warning(f"Failed to configure Celery routing for queue {config.name}: {e}")
    
    async def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health information.
        
        Returns:
            Dict: System health metrics
        """
        try:
            # Check Redis connection
            redis_healthy = await self._check_redis_health()
            
            # Check Celery workers
            celery_healthy = await self._check_celery_health()
            
            # Queue statistics
            total_queues = len(self.configured_queues)
            active_queues = len(self.active_queues)
            
            # Calculate total pending messages
            total_pending = 0
            for queue_name in self.configured_queues:
                total_pending += await self.get_queue_size(queue_name)
            
            return {
                "status": "healthy" if redis_healthy and celery_healthy else "degraded",
                "redis_healthy": redis_healthy,
                "celery_healthy": celery_healthy,
                "total_queues": total_queues,
                "active_queues": active_queues,
                "total_pending_messages": total_pending,
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get system health: {e}")
            return {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def _check_redis_health(self) -> bool:
        """Check Redis connection health."""
        try:
            await self.redis_client.ping()
            return True
        except Exception:
            return False
    
    async def _check_celery_health(self) -> bool:
        """Check Celery worker health."""
        try:
            inspect = self.celery_app.control.inspect()
            stats = inspect.stats()
            return stats is not None and len(stats) > 0
        except Exception:
            return False
    
    async def create_learning_queue(self, queue_name: str = "learning_queue") -> bool:
        """Create a queue specifically for learning tasks.
        
        Args:
            queue_name: Name of the learning queue
            
        Returns:
            bool: True if queue was created successfully
        """
        from ..schemas.event import QueueConfig
        
        learning_queue_config = QueueConfig(
            name=queue_name,
            priority=5,  # Medium priority
            max_retries=3,
            retry_delay=30,  # 30 seconds
            routing_key=f"learning.{queue_name}",
            description="Queue for processing learning tasks"
        )
        
        return await self.create_queue(learning_queue_config)
    
    async def publish_learning_event(self, 
                                   queue_name: str,
                                   agent_name: str,
                                   team_path: str,
                                   learning_data: dict) -> str:
        """Publish a learning event to the queue.
        
        Args:
            queue_name: Target queue name
            agent_name: Name of the agent to learn
            team_path: Path to team configuration
            learning_data: Learning-specific data
            
        Returns:
            str: Event ID
        """
        from ..schemas.event import create_event
        
        learning_event = create_event(
            event_type="agent_learning",
            source="learning_system",
            data={
                "agent_name": agent_name,
                "team_path": team_path,
                **learning_data
            },
            metadata={
                "learning_mode": "async",
                "agent_name": agent_name,
                "task_type": "learning"
            },
            priority=5  # Medium priority
        )
        
        return await self.publish_to_queue(queue_name, learning_event)