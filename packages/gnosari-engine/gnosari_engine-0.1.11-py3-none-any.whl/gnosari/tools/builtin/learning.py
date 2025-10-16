"""Learning tool for agents to add learnings from their interactions."""

import logging
import json
from typing import Any, Optional, List
from pydantic import BaseModel, Field
from agents import RunContextWrapper, FunctionTool

from ...tools.interfaces import AsyncTool
from ...schemas.event import GenericEventContextWithData
from ...utils.event_sender import EventSender
from ...utils.logging import get_logger

logger = get_logger(__name__)


class LearningInput(BaseModel):
    """Input schema for learning tool."""
    content: str = Field(
        description="The learning content or insight to be recorded"
    )
    type: Optional[str] = Field(
        default="agent_interaction",
        description="Type of learning (e.g., 'communication_style', 'best_practices', 'warnings', 'howto')"
    )
    priority: Optional[str] = Field(
        default="medium",
        description="Priority level: critical, high, medium, low, contextual"
    )
    context: Optional[str] = Field(
        default=None,
        description="Context where this learning applies"
    )
    tags: Optional[List[str]] = Field(
        default=None,
        description="Tags for categorizing the learning"
    )


class LearningTool(AsyncTool):
    """Tool for agents to add learnings by sending events to the queue."""
    
    def __init__(self):
        """Initialize the learning tool."""
        super().__init__(
            name="add_learning",
            description="Add a new learning from your interaction experience. Provide the learning content and optional metadata (type, priority, context, tags).",
            input_schema=LearningInput
        )
        self.logger = logging.getLogger(__name__)
        
        # Create the FunctionTool with proper input schema
        self.tool = FunctionTool(
            name=self.name,
            description=self.description,
            params_json_schema=LearningInput.model_json_schema(),
            on_invoke_tool=self._run_learning_tool
        )
        
    async def _run_learning_tool(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """Send learning event to the queue.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing learning data
            
        Returns:
            Learning event result as string
        """
        try:
            # Parse the learning input from args
            if not args or not args.strip():
                self.logger.error("No learning content provided")
                return json.dumps({
                    "status": "error",
                    "message": "Learning content is required",
                    "error": "Missing learning content"
                }, indent=2)
            
            try:
                learning_input = LearningInput.model_validate_json(args)
                learning_data = {
                    "content": learning_input.content,
                    "type": learning_input.type,
                    "priority": learning_input.priority,
                    "context": learning_input.context or "Agent interaction",
                    "tags": learning_input.tags or ["agent_learning", "interaction"]
                }
            except (json.JSONDecodeError, ValueError) as e:
                self.logger.warning(f"Failed to parse JSON args '{args}', trying simple content extraction: {e}")
                # Fallback: treat args as simple content string
                if args and args.strip():
                    learning_data = {
                        "content": args.strip(),
                        "type": "agent_interaction", 
                        "priority": "medium",
                        "context": "Agent interaction",
                        "tags": ["agent_learning", "interaction"]
                    }
                    self.logger.info(f"Using fallback content: {learning_data['content'][:100]}...")
                else:
                    self.logger.error(f"No valid content found in args: {args}")
                    return json.dumps({
                        "status": "error",
                        "message": f"Invalid input format: {str(e)}",
                        "error": "Invalid JSON or missing required fields"
                    }, indent=2)
            
            self.logger.info(f"Adding learning event to queue: {learning_data['content'][:100]}...")
            
            # DEBUG: Log the full RunContextWrapper structure
            self.logger.debug(f"=== DEBUG RunContextWrapper ===")
            self.logger.debug(f"ctx type: {type(ctx)}")
            self.logger.debug(f"ctx dir: {dir(ctx)}")
            
            if hasattr(ctx, 'context'):
                self.logger.debug(f"ctx.context type: {type(ctx.context)}")
                self.logger.debug(f"ctx.context dir: {dir(ctx.context)}")
                if hasattr(ctx.context, '__dict__'):
                    self.logger.debug(f"ctx.context.__dict__: {ctx.context.__dict__}")
            
            if hasattr(ctx, '__dict__'):
                self.logger.debug(f"ctx.__dict__: {ctx.__dict__}")
            
            # Check for any session-related attributes
            for attr in dir(ctx):
                if 'session' in attr.lower():
                    self.logger.debug(f"Found session attribute: {attr} = {getattr(ctx, attr, 'N/A')}")
            
            if hasattr(ctx, 'context'):
                for attr in dir(ctx.context):
                    if 'session' in attr.lower():
                        self.logger.debug(f"Found session attribute in context: {attr} = {getattr(ctx.context, attr, 'N/A')}")
            
            self.logger.debug(f"=== END DEBUG ===")
            
            # Try multiple approaches to get session context
            session_context = self.get_session_context_from_ctx(ctx)
            
            # Approach 1: Try the RunContextWrapper session extraction
            if session_context:
                session_id = session_context.session_id
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
                self.logger.debug(f"Found session context via RunContextWrapper: session_id={session_id}")
            else:
                self.logger.error("No session context found - this indicates a bug in session context propagation")
                # Don't send learning event without proper session context
                return json.dumps({
                    "status": "error",
                    "message": "No session context available - cannot send learning event without session",
                    "error": "Missing session context"
                }, indent=2)
            
            # Create generic event context with learning data directly in data
            context_data = GenericEventContextWithData(
                source="learning_tool",
                priority=5,
                broadcast=False,
                data={
                    "session_id": session_id,
                    "learning": {
                        "content": learning_data["content"],
                        "type": learning_data["type"],
                        "priority": learning_data["priority"],
                        "context": learning_data["context"],
                        "tags": learning_data["tags"]
                    }
                }
            )
            
            # Send learning event to queue
            result = EventSender.create_and_send_event(
                event_type="learning.add_request",
                context_data=context_data,
                source="learning_tool",
                priority=5,
                metadata={"tool_name": "add_learning"},
                execution_context=ctx,
                session=session_data
            )
            
            if result["status"] == "success":
                self.logger.info(f"Successfully sent learning event {result['event_id']} to queue")
            else:
                self.logger.error(f"Failed to send learning event: {result.get('message', 'Unknown error')}")
            
            return json.dumps(result, indent=2)
                
        except Exception as e:
            error_result = {
                "status": "error",
                "message": f"Learning event sending failed: {str(e)}",
                "error": str(e)
            }
            self.logger.error(f"Error in learning tool: {e}")
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
            description=f"{self.description} (Sends events to queue)",
            params_json_schema=LearningInput.model_json_schema(),
            on_invoke_tool=self._run_learning_tool
        )


