"""Event consumer for processing events in Gnosari AI Teams.

This module provides Celery tasks and utilities for processing events
sent through the event system by agents and external sources.
"""

import asyncio
from typing import Dict, Any

from ..handlers import (
    EventHandlerRegistry,
    AgentCallEventHandler,
    ExecuteToolEventHandler,
    GenericEventHandler,
    LearningEventHandler,
    CustomEventHandler
)
from ...schemas.event import (
    AgentListener,
    EventProcessingError
)
from ...utils.logging import get_logger
from ...utils.opensearch_client import index_event_document

logger = get_logger(__name__)

# Initialize event handler registry
_event_registry = EventHandlerRegistry()


# Register all event handlers
def _initialize_event_handlers():
    """Initialize and register all event handlers."""
    global _event_registry

    _event_registry.register_handler(AgentCallEventHandler())
    _event_registry.register_handler(ExecuteToolEventHandler())
    _event_registry.register_handler(GenericEventHandler())
    _event_registry.register_handler(LearningEventHandler())
    _event_registry.register_handler(CustomEventHandler())

    logger.info("Event handlers initialized and registered")


# Initialize handlers on module import
_initialize_event_handlers()

# Import the Celery app for creating tasks
from ..app import celery_app

_agent_listeners: Dict[str, Dict[str, AgentListener]] = {}  # team_id -> agent_id -> listener
_agent_runners: Dict[str, Any] = {}  # team_id -> team_runner


async def initialize_event_system_async() -> None:
    """Initialize the event system with default settings (async version)."""
    from ...engine.queue_manager import QueueManager
    from ...queue.app import celery_app
    from ...schemas.event import QueueConfig
    import redis

    # Initialize Redis client
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
    )

    # Initialize queue manager with Celery app and Redis client
    queue_manager = QueueManager(celery_app, redis_client)

    # Create default demo queues
    default_queues = [
        QueueConfig(
            name="demo_events",
            priority=5,
            max_retries=3,
            retry_delay=60,
            routing_key="demo.*"
        ),
        QueueConfig(
            name="gnosari_events",
            priority=5,
            max_retries=3,
            retry_delay=60,
            routing_key="*"
        )
    ]

    # Create the queues
    for queue_config in default_queues:
        try:
            await queue_manager.create_queue(queue_config)
            logger.info(f"Created queue: {queue_config.name}")
        except Exception as e:
            logger.warning(f"Failed to create queue {queue_config.name}: {e}")

    logger.info("Event system initialized with Redis, Celery, and default queues")


def initialize_event_system() -> None:
    """Initialize the event system with default settings (sync wrapper)."""
    # Run async initialization
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    loop.run_until_complete(initialize_event_system_async())


def register_agent_listener(team_id: str, agent_id: str, listener: AgentListener, runner: Any) -> None:
    """Register an agent as an event listener.
    
    Args:
        team_id: Team identifier
        agent_id: Agent identifier  
        listener: Agent listener configuration
        runner: Agent runner instance for processing events
    """
    global _agent_listeners, _agent_runners

    if team_id not in _agent_listeners:
        _agent_listeners[team_id] = {}

    _agent_listeners[team_id][agent_id] = listener
    _agent_runners[team_id] = runner

    logger.info(f"Registered agent {agent_id} in team {team_id} as event listener")


def unregister_team_listeners(team_id: str) -> None:
    """Unregister all listeners for a team.
    
    Args:
        team_id: Team identifier
    """
    global _agent_listeners, _agent_runners

    if team_id in _agent_listeners:
        del _agent_listeners[team_id]
    if team_id in _agent_runners:
        del _agent_runners[team_id]

    logger.info(f"Unregistered all listeners for team {team_id}")


# Removed complex event processing - now using simple routing approach


# Removed complex async event processing - using simple routing approach


async def _handle_call_agent_event(event_context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle call_agent event by executing delegation.
    
    Args:
        event_context: Event context containing delegation data
        
    Returns:
        Dict: Delegation execution result
    """
    try:
        event_data = event_context.get("data", {})
        target_agent = event_data.get("target_agent")
        message = event_data.get("message")
        session_id = event_data.get("session_id")
        team_config = event_data.get("team_config")

        if not all([target_agent, message, team_config]):
            raise EventProcessingError(
                "Missing required fields for call_agent event",
                error_code="MISSING_AGENT_CALL_DATA"
            )

        logger.info(f"🤝 Processing call_agent event for '{target_agent}'")

        # Build team from configuration
        from ...engine.builder import TeamBuilder
        import tempfile
        import yaml
        import os

        builder = TeamBuilder(session_id=session_id or "event_session")

        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(team_config, temp_file)
            temp_config_path = temp_file.name

        try:
            # Build team
            team = await builder.build_team(temp_config_path)
            if not team:
                raise EventProcessingError(
                    "Failed to build team for agent call",
                    error_code="TEAM_BUILD_FAILED"
                )

            # Get target agent
            agent = team.get_agent(target_agent)
            if not agent:
                available_agents = ', '.join(team.list_agents())
                raise EventProcessingError(
                    f"Agent '{target_agent}' not found. Available: {available_agents}",
                    error_code="AGENT_NOT_FOUND"
                )

            # Execute delegation
            from ...engine.runner import TeamRunner
            team_executor = TeamRunner(team)

            result = await team_executor.run_agent_until_done_async(
                agent,
                message,
                session_id=session_id
            )

            # Extract response content
            response_content = ""
            if hasattr(result, '__getitem__') and "outputs" in result:
                for output in result["outputs"]:
                    if output.get("type") == "response":
                        content = output.get("content", "")
                        if hasattr(content, 'plain'):
                            response_content += content.plain
                        else:
                            response_content += str(content)
            else:
                response_content = str(result)

            logger.info(f"✅ call_agent event completed for '{target_agent}'")

            return {
                "status": "success",
                "target_agent": target_agent,
                "response": response_content,
                "message": f"Successfully executed call_agent for '{target_agent}'"
            }

        finally:
            # Clean up temp file
            if os.path.exists(temp_config_path):
                os.unlink(temp_config_path)

    except Exception as e:
        logger.error(f"Failed to handle call_agent event: {e}")
        raise EventProcessingError(
            f"call_agent event failed: {e}",
            error_code="CALL_AGENT_FAILED"
        )


# Removed event parsing - using direct dict processing


@celery_app.task(name='gnosari.queue.consumers.event.process_event_message')
def process_event_message(event_data: dict) -> dict:
    """Process an event message using the event handler system.
    
    Args:
        event_data: Event message data as dictionary
        
    Returns:
        dict: Processing result
    """
    processing_result = None

    try:
        event_type = event_data.get('event_type', 'unknown')
        event_id = event_data.get('event_id', 'unknown')

        logger.info(f"Processing event: {event_type} with ID {event_id}")

        # Get appropriate handler from registry
        handler = _event_registry.get_handler(event_data)

        if handler:
            logger.info(f"Using handler: {handler.__class__.__name__} for event: {event_type}")
            processing_result = handler.handle(event_data)
        else:
            # No handler found, return error
            processing_result = {
                "status": "failed",
                "error": "No handler found for event type",
                "event_id": event_id,
                "event_type": event_type,
                "message": f"No handler registered for event type: {event_type}",
                "available_handlers": _event_registry.list_handlers()
            }
            logger.warning(f"No handler found for event type: {event_type}")

        # Queue OpenSearch indexing asynchronously
        try:
            celery_app.send_task(
                'gnosari.queue.consumers.event.index_event_in_opensearch',
                args=[event_data, processing_result],
                queue='gnosari-events',
                priority=8  # Lower priority for indexing
            )
            logger.debug(f"Queued OpenSearch indexing for event {event_id}")
        except Exception as queue_error:
            logger.warning(f"Failed to queue OpenSearch indexing for event {event_id}: {queue_error}")
            # Don't fail the whole task if queuing fails

        return processing_result

    except Exception as e:
        processing_result = {
            "status": "failed",
            "error": str(e),
            "event_id": event_data.get("event_id"),
            "event_type": event_data.get("event_type"),
            "message": f"Failed to process event: {e}"
        }
        logger.error(f"Failed to process event: {e}")

        # Queue OpenSearch indexing for failed event
        try:
            celery_app.send_task(
                'gnosari.queue.consumers.event.index_event_in_opensearch',
                args=[event_data, processing_result],
                queue='gnosari-events',
                priority=8  # Lower priority for indexing
            )
            logger.debug(f"Queued OpenSearch indexing for failed event {event_data.get('event_id', 'unknown')}")
        except Exception as queue_error:
            logger.warning(f"Failed to queue OpenSearch indexing for failed event: {queue_error}")

        return processing_result


@celery_app.task(name='gnosari.queue.consumers.event.index_event_in_opensearch')
def index_event_in_opensearch(event_data: dict, processing_result: dict = None) -> dict:
    """Async task to index event in OpenSearch.
    
    Args:
        event_data: Event data to index
        processing_result: Optional processing result
        
    Returns:
        dict: Indexing result
    """
    try:
        event_id = event_data.get("event_id", "unknown")
        logger.debug(f"Indexing event {event_id} in OpenSearch")
        
        success = index_event_document(event_data, processing_result)
        
        if success:
            logger.debug(f"Successfully indexed event {event_id} in OpenSearch")
            return {
                "status": "success",
                "event_id": event_id,
                "message": "Event indexed in OpenSearch"
            }
        else:
            logger.warning(f"Failed to index event {event_id} in OpenSearch")
            return {
                "status": "failed",
                "event_id": event_id,
                "message": "Failed to index event in OpenSearch"
            }
            
    except Exception as e:
        logger.error(f"Error indexing event in OpenSearch: {e}")
        return {
            "status": "error",
            "event_id": event_data.get("event_id", "unknown"),
            "message": f"Error indexing event: {str(e)}"
        }


# Legacy handler functions removed - now using event handler classes
# The event handling logic has been moved to dedicated handler classes:
# - AgentCallEventHandler for agent_call events
# - ExecuteToolEventHandler for execute_tool events  
# - GenericEventHandler for task.*, user.*, system.* events
# - CustomEventHandler for all other custom events
