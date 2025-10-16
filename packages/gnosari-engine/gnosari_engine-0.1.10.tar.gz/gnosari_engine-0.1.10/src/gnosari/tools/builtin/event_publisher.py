"""Event Publisher tool for Gnosari AI Teams.

This tool allows agents to publish events to the event system for consumption
by other agents or external systems. Follows OpenAI Agents SDK patterns.
"""

import logging
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from agents import RunContextWrapper, FunctionTool

from ...tools.interfaces import AsyncTool
from ...schemas.event import EventTypes, GenericEventContextWithData
from ...utils.event_sender import EventSender
from ...utils.logging import get_logger


logger = get_logger(__name__)


class EventPublishArgs(BaseModel):
    """Arguments for event publishing."""
    
    event_type: str = Field(description="Type of event to publish (e.g., 'task.completed', 'user.action')")
    source: Optional[str] = Field(None, description="Event source identifier (defaults to agent name)")
    priority: int = Field(default=5, ge=1, le=10, description="Event priority (1=highest, 10=lowest)")
    broadcast: bool = Field(default=False, description="Broadcast to all teams")
    data: str = Field(default="{}", description="Event data as JSON string")


class EventPublisherTool(AsyncTool):
    """Tool for publishing events to the event system."""
    
    def __init__(self):
        """Initialize the event publisher tool."""
        super().__init__(
            name="event_publisher",
            description="Publishes events to the event system for consumption by other agents or systems",
            input_schema=EventPublishArgs
        )
        self.logger = logging.getLogger(__name__)
        
        # Create the FunctionTool (sync by default)
        self.tool = FunctionTool(
            name=self.name,
            description=self.description,
            params_json_schema=EventPublishArgs.model_json_schema(),
            on_invoke_tool=self._run_event_publisher
        )
        
    async def _run_event_publisher(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """Publish an event to the event system.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing EventPublishArgs
            
        Returns:
            Event publishing result as string
        """
        try:
            self.logger.info(f"Publishing event with args: {args}")
            
            # Parse arguments
            args_dict = json.loads(args)
            publish_args = EventPublishArgs(**args_dict)
            
            # Parse data JSON string
            try:
                data_dict = json.loads(publish_args.data)
            except json.JSONDecodeError:
                data_dict = {}
            
            # Get session context for root level
            session_context = self.get_session_context_from_ctx(ctx)
            session_data = None
            if session_context:
                session_data = {
                    "session_id": session_context.session_id,
                    "original_config": session_context.original_config,
                    "team_id": session_context.team_id,
                    "agent_id": session_context.agent_id,
                    "team_identifier": session_context.team_identifier,
                    "agent_identifier": session_context.agent_identifier,
                    "account_id": session_context.account_id,
                    "metadata": session_context.metadata
                }
            
            # Create generic event context
            context_data = GenericEventContextWithData(
                source=publish_args.source or "agent",
                priority=publish_args.priority,
                broadcast=publish_args.broadcast,
                data=data_dict
            )
            
            # Use unified event sender
            result = EventSender.create_and_send_event(
                event_type=publish_args.event_type,
                context_data=context_data,
                source=publish_args.source or "event_publisher_tool",
                priority=publish_args.priority,
                metadata={"tool_name": "event_publisher"},
                execution_context=ctx,
                session=session_data
            )
            
            if result["status"] == "success":
                self.logger.info(f"Successfully published event {result['event_id']} of type {result['event_type']}")
            else:
                self.logger.error(f"Failed to publish event: {result.get('message', 'Unknown error')}")
            
            return json.dumps(result, indent=2)
                
        except Exception as e:
            error_result = {
                "status": "error",
                "message": f"Event publishing failed: {str(e)}",
                "error": str(e)
            }
            self.logger.error(f"Error in event publisher: {e}")
            return json.dumps(error_result, indent=2)
    
    def get_tool(self):
        """Get the FunctionTool instance."""
        return self.tool
    
    def get_async_tool(self) -> FunctionTool:
        """Get the async FunctionTool instance for queue execution.
        
        Returns:
            FunctionTool: Tool configured for async queue execution
        """
        return FunctionTool(
            name=self.name,
            description=f"{self.description} (Uses unified event system)",
            params_json_schema=EventPublishArgs.model_json_schema(),
            on_invoke_tool=self._run_event_publisher
        )