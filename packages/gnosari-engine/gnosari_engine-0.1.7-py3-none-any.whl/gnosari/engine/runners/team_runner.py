"""
Team execution runner
"""

import asyncio
import redis.asyncio as redis
from typing import Optional, AsyncGenerator, Dict, Any
from agents import Runner, AgentUpdatedStreamEvent
from celery import Celery

from ..event_handlers import StreamEventHandler, ErrorHandler, MCPServerManager
from .base_runner import BaseRunner
from ..queue_manager import QueueManager
from ...queue.consumers.event import (
    register_agent_listener, 
    unregister_team_listeners,
    process_event_message
)
from ...schemas.event import QueueConfig, EventConfig, AgentListener, AgentTrigger


class TeamRunner(BaseRunner):
    """Runner for executing team workflows."""
    
    def __init__(self, *args, **kwargs):
        """Initialize TeamRunner with event system support."""
        super().__init__(*args, **kwargs)
        self.queue_manager: Optional[QueueManager] = None
        self.event_listeners_registered = False
        self.team_id: Optional[str] = None
    
    async def initialize_event_system(self, team_config, celery_app: Optional[Celery] = None, 
                                     redis_client: Optional[redis.Redis] = None) -> None:
        """Initialize the event system for this team.
        
        Args:
            team_config: Team configuration with queue and event settings
            celery_app: Celery application instance (optional)
            redis_client: Redis client instance (optional)
        """
        try:
            if not hasattr(team_config, 'queues') and not hasattr(team_config, 'events'):
                self.logger.debug("No event configuration found, skipping event system initialization")
                return
            
            # Initialize Redis client if not provided
            if redis_client is None:
                redis_client = redis.from_url("redis://localhost:6379", decode_responses=True)
            
            # Initialize Celery app if not provided
            if celery_app is None:
                celery_app = Celery('gnosari_events', broker='redis://localhost:6379')
            
            # Create queue manager
            self.queue_manager = QueueManager(celery_app, redis_client)
            
            # Create and configure queues if specified
            if hasattr(team_config, 'queues') and team_config.queues:
                await self._create_queues(team_config.queues)
            
            # Event system initialized with queue manager
            
            # Set team ID for event routing
            self.team_id = getattr(team_config, 'name', 'default_team')
            
            # Register agent listeners
            await self._register_agent_listeners(team_config)
            
            self.logger.info(f"Event system initialized for team {self.team_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize event system: {e}")
            # Don't fail the entire team initialization if events fail
    
    async def _create_queues(self, queue_configs: list) -> None:
        """Create queues from configuration.
        
        Args:
            queue_configs: List of queue configuration dictionaries
        """
        for queue_config in queue_configs:
            try:
                # Convert dict to QueueConfig object
                config = QueueConfig(**queue_config)
                success = await self.queue_manager.create_queue(config)
                
                if success:
                    self.logger.info(f"Created queue: {config.name}")
                else:
                    self.logger.warning(f"Failed to create queue: {config.name}")
                    
            except Exception as e:
                self.logger.error(f"Error creating queue {queue_config.get('name', 'unknown')}: {e}")
    
    async def _register_agent_listeners(self, team_config) -> None:
        """Register agents as event listeners.
        
        Args:
            team_config: Team configuration with agent definitions
        """
        try:
            listeners = []
            
            # Process each agent's event listener configuration
            for agent_config in team_config.agents:
                if 'listen' in agent_config and agent_config['listen']:
                    try:
                        # Convert dict to AgentListener object
                        listener = AgentListener(**agent_config['listen'])
                        
                        # Register with event consumer
                        agent_name = agent_config.get('name', 'unknown')
                        register_agent_listener(self.team_id, agent_name, listener, self)
                        
                        listeners.append(listener)
                        self.logger.info(f"Registered event listener for agent {agent_name}")
                        
                    except Exception as e:
                        agent_name = agent_config.get('name', 'unknown')
                        self.logger.error(f"Failed to register listener for agent {agent_name}: {e}")
            
            # Register agent listeners for event processing
            if listeners:
                self.event_listeners_registered = True
                
        except Exception as e:
            self.logger.error(f"Failed to register agent listeners: {e}")
    
    async def cleanup_event_system(self) -> None:
        """Clean up event system resources."""
        try:
            if self.event_listeners_registered and self.team_id:
                # Unregister team listeners
                unregister_team_listeners(self.team_id)
                self.event_listeners_registered = False
                
                self.logger.info(f"Cleaned up event system for team {self.team_id}")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up event system: {e}")
    
    async def run_team_async(self, message: str, debug: bool = False, 
                            session_id: Optional[str] = None, 
                            session_context: Optional[Dict[str, Any]] = None, 
                            max_turns: Optional[int] = None) -> Dict[str, Any]:
        """Run team asynchronously using OpenAI Agents SDK Runner.
        
        Args:
            message: User message
            debug: Whether to show debug info
            session_id: Session ID for conversation persistence
            session_context: Session context data
            max_turns: Maximum number of turns
            
        Returns:
            Dict with outputs and completion status
        """
        if debug:
            self.logger.info(f"Contacting {self.team.orchestrator.name}")
        
        # Initialize MCP manager and connect servers
        mcp_manager = MCPServerManager()
        all_agents = [self.team.orchestrator] + list(self.team.workers.values())
        await mcp_manager.connect_servers(all_agents)

        session = None
        try:
            run_config = self._create_run_config()
            
            # Create SessionContext with team_id and agent_id from YAML config
            context = self._enrich_session_context(
                session_context, 
                agent_name=self.team.orchestrator.name,  # Start with orchestrator
                session_id=session_id
            )
            
            # Create session with enriched context for proper database storage
            session = self._get_session(session_id, context_obj=context)
            self._log_session_info(session, session_id, "team")
            
            # Only include max_turns if it's not None
            effective_max_turns = self._get_effective_max_turns(max_turns)
            if effective_max_turns is not None:
                result = await Runner.run(
                    self.team.orchestrator,
                    input=message,
                    run_config=run_config,
                    session=session,
                    context=context,
                    max_turns=effective_max_turns
                )
            else:
                result = await Runner.run(
                    self.team.orchestrator,
                    input=message,
                    run_config=run_config,
                    session=session,
                    context=context
                )
            
            # Convert result to our expected format
            return {
                "outputs": [{"type": "completion", "content": result.final_output}],
                "agent_name": self.team.orchestrator.name,
                "is_done": True
            }
        finally:
            await self.cleanup_manager.cleanup_all(session, mcp_manager, all_agents)
            await self.cleanup_event_system()
    
    def run_team(self, message: str, debug: bool = False, 
                session_id: Optional[str] = None, 
                max_turns: Optional[int] = None) -> Dict[str, Any]:
        """Run team synchronously."""
        return asyncio.run(self.run_team_async(message, debug, session_id, max_turns=max_turns))
    
    async def run_team_stream(self, message: str, debug: bool = False, 
                             session_id: Optional[str] = None, 
                             session_context: Optional[Dict[str, Any]] = None, 
                             max_turns: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Run team with streaming outputs using OpenAI Agents SDK.
        
        Args:
            message: User message
            debug: Whether to show debug info
            session_id: Session ID for conversation persistence
            session_context: Session context data
            max_turns: Maximum number of turns
            
        Yields:
            Dict: Stream outputs (response chunks, tool calls, handoffs, etc.)
        """
        self.logger.info(f"Contacting {self.team.orchestrator.name}")
        
        # Initialize handlers
        current_agent = self.team.orchestrator.name
        event_handler = StreamEventHandler(current_agent)
        error_handler = ErrorHandler(current_agent)
        mcp_manager = MCPServerManager()
        
        # Connect MCP servers before running
        all_agents = [self.team.orchestrator] + list(self.team.workers.values())
        await mcp_manager.connect_servers(all_agents)

        session = None
        try:
            run_config = self._create_run_config()
            
            # Create SessionContext with team_id and agent_id from YAML config
            context = self._enrich_session_context(
                session_context, 
                agent_name=self.team.orchestrator.name,  # Start with orchestrator
                session_id=session_id
            )
            
            # Create session with enriched context for proper database storage
            session = self._get_session(session_id, context_obj=context)
            self._log_session_info(session, session_id, "team stream")
            
            # Only include max_turns if it's not None
            effective_max_turns = self._get_effective_max_turns(max_turns)
            if effective_max_turns is not None:
                result = Runner.run_streamed(
                    self.team.orchestrator,
                    input=message,
                    run_config=run_config,
                    session=session,
                    context=context,
                    max_turns=effective_max_turns
                )
            else:
                result = Runner.run_streamed(
                    self.team.orchestrator,
                    input=message,
                    run_config=run_config,
                    session=session,
                    context=context
                )
            
            self.logger.info("Starting to process streaming events...")
            
            async for event in result.stream_events():
                if isinstance(event, AgentUpdatedStreamEvent):
                    self.logger.debug(f"Received event: {event.type}. Item: {event.new_agent.name}")

                self.logger.debug(f"Received event: {event.type}. Item: {event}")
                
                # Use event handler to process events
                async for response in event_handler.handle_event(event):
                    # Update current agent if changed
                    if response.get('type') == 'agent_updated':
                        current_agent = response.get('agent_name', current_agent)
                        event_handler.current_agent = current_agent
                        self.logger.debug(f"Current Agent: {event.type}. Item: {event}")
                    yield response

            # Yield final completion
            yield {
                "type": "completion",
                "content": result.final_output,
                "output": result.final_output,
                "agent_name": current_agent,
                "is_done": True
            }
            
        except Exception as e:
            # Use simplified error handler
            error_response = error_handler.handle_error(e)
            yield error_response
            raise e
        finally:
            await self.cleanup_manager.cleanup_all(session, mcp_manager, all_agents)
            await self.cleanup_event_system()