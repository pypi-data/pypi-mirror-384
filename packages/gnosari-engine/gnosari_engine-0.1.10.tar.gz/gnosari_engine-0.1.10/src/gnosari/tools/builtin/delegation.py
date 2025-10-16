"""
OpenAI Delegate Agent Tool - Clean implementation following SOLID principles
"""

import logging
import asyncio
import json
from typing import Any, Dict
from pydantic import BaseModel, Field
from agents import RunContextWrapper, FunctionTool
from ...tools.interfaces import AsyncTool
from ...schemas.event import EventTypes, AgentCallContext
from ...utils.event_sender import EventSender


class DelegateAgentArgs(BaseModel):
    """Arguments for the delegate agent tool."""
    target_agent: str = Field(..., description="Name of the agent to delegate the task to")
    message: str = Field(..., description="The message or task to delegate to the target agent")


class DelegationResult:
    """Encapsulates delegation result processing logic."""
    
    def __init__(self, raw_result: Any, target_agent: str):
        self.raw_result = raw_result
        self.target_agent = target_agent
        self.response_content = ""
        self.reasoning_content = ""
        self._extract_content()
    
    def _extract_content(self) -> None:
        """Extract response and reasoning content from raw result."""
        if not self._has_outputs():
            self.response_content = str(self.raw_result)
            return
        
        for output in self.raw_result["outputs"]:
            output_type = output.get("type", "")
            content = output.get("content", "")
            
            if output_type == "response":
                self.response_content += self._extract_text_content(content)
            elif output_type == "reasoning":
                self.reasoning_content += self._extract_text_content(content)
            elif output_type == "completion":
                self.response_content = self._extract_text_content(content)
    
    def _has_outputs(self) -> bool:
        """Check if result has outputs structure."""
        return (hasattr(self.raw_result, '__getitem__') and 
                "outputs" in self.raw_result)
    
    def _extract_text_content(self, content: Any) -> str:
        """Extract text content from various content types."""
        if hasattr(content, 'plain'):
            return content.plain
        return str(content)
    
    def get_formatted_response(self) -> str:
        """Get formatted response text."""
        if self.reasoning_content:
            return f"Reasoning: {self.reasoning_content}\nResponse: {self.response_content}"
        return self.response_content

class DelegateAgentTool(AsyncTool):
    """Configurable Delegate Agent Tool following SOLID principles."""
    
    def __init__(self):
        """Initialize the delegate agent tool."""
        # Call parent constructor first
        super().__init__(
            name="delegate_agent",
            description="Delegate a task to another agent in the team",
            input_schema=DelegateAgentArgs
        )
        self.logger = logging.getLogger(__name__)
        
        # Create the FunctionTool (sync by default)
        self.tool = FunctionTool(
            name=self.name,
            description=self.description,
            params_json_schema=DelegateAgentArgs.model_json_schema(),
            on_invoke_tool=self._run_delegate_agent
        )
        
    async def _run_delegate_agent(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """Delegate a task to another agent in the team.
        
        This is the synchronous version that executes delegation immediately.
        For async execution, use get_async_tool() which queues the delegation.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing DelegateAgentArgs
            
        Returns:
            Delegation result as string
        """
        self.logger.debug(f"🔍 DEBUG - _run_delegate_agent (SYNC) called with args: {args}")
        try:
            parsed_args = DelegateAgentArgs.model_validate_json(args)
            
            # Get session context using proper helper method
            session_context = self.get_session_context_from_ctx(ctx)
            session_id = session_context.session_id if session_context else None
            original_config = session_context.original_config if session_context else None

            self._log_delegation_start(parsed_args)
            
            if not original_config:
                return "Error: No team configuration available in context for delegation"
            
            # Build team and execute delegation
            team = await self._build_team(original_config, session_id)
            if not team:
                return "Error: Failed to build team for delegation"
            
            available_agents = team.list_agents()
            target_agent = team.get_agent(parsed_args.target_agent)
            
            if not target_agent:
                available_agents_str = ', '.join(available_agents)
                return f"Error: Agent '{parsed_args.target_agent}' not found in the team. Available agents: {available_agents_str}"
            
            # Execute delegation
            result = await self._execute_delegation(team, target_agent, parsed_args, session_id)
            
            # Process and format result
            delegation_result = DelegationResult(result, parsed_args.target_agent)
            self._log_delegation_success(delegation_result, parsed_args.target_agent)
            
            return delegation_result.get_formatted_response()
            
        except Exception as e:
            # Extract target agent name if available
            target_agent = 'unknown'
            try:
                parsed_args = DelegateAgentArgs.model_validate_json(args)
                target_agent = parsed_args.target_agent
            except (NameError, Exception):
                pass
            
            error_msg = f"Failed to delegate to agent '{target_agent}': {str(e)}"
            self.logger.error(f"❌ DELEGATION FAILED - {error_msg}")
            return error_msg
    
    def _log_delegation_start(self, parsed_args: DelegateAgentArgs) -> None:
        """Log delegation start information."""
        message_preview = f"{parsed_args.message[:100]}{'...' if len(parsed_args.message) > 100 else ''}"
        self.logger.info(f"🤝 DELEGATION STARTED - Target Agent: '{parsed_args.target_agent}' | Message: '{message_preview}'")
    
    async def _build_team(self, original_config: Dict[str, Any], session_id: str) -> Any:
        """Build team from configuration using existing TeamBuilder."""
        try:
            from ...engine.builder import TeamBuilder
            
            self.logger.debug(f"🔍 DEBUG - Original config keys: {list(original_config.keys())}")
            self.logger.debug(f"🔍 DEBUG - Config content: {original_config}")
            
            builder = TeamBuilder(session_id=session_id)
            temp_config_path = self._create_temp_config(original_config)
            self.logger.debug(f"🔍 DEBUG - Created temp config at: {temp_config_path}")
            
            try:
                self.logger.debug(f"🔍 DEBUG - Building team with TeamBuilder...")
                team = await asyncio.wait_for(
                    builder.build_team(temp_config_path),
                    timeout=120.0  # 2 minute timeout for team building
                )
                self.logger.debug(f"🔍 DEBUG - Team building completed, team type: {type(team)}")
                return team
            finally:
                self._cleanup_temp_file(temp_config_path)
                
        except asyncio.TimeoutError:
            self.logger.error("❌ Team building timed out after 2 minutes")
            return None
        except Exception as e:
            self.logger.error(f"❌ Team building failed: {str(e)}")
            self.logger.debug(f"🔍 DEBUG - Team building exception: {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.debug(f"🔍 DEBUG - Team building traceback: {traceback.format_exc()}")
            return None
    
    def _create_temp_config(self, config: Dict[str, Any]) -> str:
        """Create temporary YAML configuration file."""
        import tempfile
        import yaml
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
            yaml.dump(config, temp_file)
            return temp_file.name
    
    def _cleanup_temp_file(self, file_path: str) -> None:
        """Clean up temporary configuration file."""
        import os
        
        if os.path.exists(file_path):
            os.unlink(file_path)
    
    async def _execute_delegation(self, team: Any, target_agent: Any, parsed_args: DelegateAgentArgs, session_id: str) -> Any:
        """Execute delegation to target agent."""
        self.logger.info(f"Contacting Agent {parsed_args.target_agent}")
        
        from ...engine.runner import TeamRunner
        team_executor = TeamRunner(team)
        
        return await asyncio.wait_for(
            team_executor.run_agent_until_done_async(
                target_agent, 
                parsed_args.message, 
                session_id=session_id
            ),
            timeout=300.0  # 5 minute timeout for delegation
        )
    
    def _log_delegation_success(self, delegation_result: DelegationResult, target_agent: str) -> None:
        """Log successful delegation information."""
        response_text = delegation_result.get_formatted_response()
        response_preview = response_text[:200] + "..." if len(response_text) > 200 else response_text
        
        self.logger.info(f"[{target_agent}] Response: {delegation_result.response_content}")
        if delegation_result.reasoning_content:
            self.logger.info(f"[{target_agent}] Reasoning: {delegation_result.reasoning_content}")
        
        self.logger.info(f"✅ DELEGATION SUCCESSFUL - Agent '{target_agent}' responded with {len(response_text)} characters")
        self.logger.info(f"📄 Response preview: {response_preview}")
    
    async def _run_delegate_agent_async(self, ctx: RunContextWrapper[Any], args: str) -> str:
        """Send agent_call event to queue for async execution.
        
        Args:
            ctx: Run context wrapper
            args: JSON string containing DelegateAgentArgs
            
        Returns:
            Event publishing result
        """
        self.logger.debug(f"🔍 DEBUG - Starting async delegation with args: {args}")
        
        try:
            parsed_args = DelegateAgentArgs.model_validate_json(args)
            self.logger.debug(f"🔍 DEBUG - Parsed args: target_agent='{parsed_args.target_agent}', message_length={len(parsed_args.message)}")
            
            # Get session context using proper helper method
            session_context = self.get_session_context_from_ctx(ctx)
            session_id = session_context.session_id if session_context else None
            original_config = session_context.original_config if session_context else None
            
            self.logger.debug(f"🔍 DEBUG - Session context: session_id={session_id}, has_original_config={original_config is not None}")
            
            if not original_config:
                error_result = {
                    "status": "error",
                    "message": "No team configuration available for delegation",
                    "error": "Missing team config"
                }
                self.logger.error(f"❌ ASYNC DELEGATION FAILED - No team config available")
                return json.dumps(error_result, indent=2)
            
            # Create agent call context
            context_data = AgentCallContext(
                target_agent=parsed_args.target_agent,
                message=parsed_args.message,
                session_id=session_id,
                team_config=original_config
            )
            self.logger.debug(f"🔍 DEBUG - Created AgentCallContext: target_agent='{context_data.target_agent}', session_id='{context_data.session_id}'")
            
            # Send unified event
            self.logger.debug(f"🔍 DEBUG - About to call EventSender.create_and_send_event...")
            self.logger.debug(f"🔍 DEBUG - Event parameters: event_type={EventTypes.AGENT_CALL}, source='delegate_agent_tool', priority=5")
            
            result = EventSender.create_and_send_event(
                event_type=EventTypes.AGENT_CALL,
                context_data=context_data,
                source="delegate_agent_tool",
                priority=5,
                metadata={"tool_name": "delegate_agent", "async_execution": True},
                execution_context=ctx
            )
            
            self.logger.debug(f"🔍 DEBUG - EventSender result: {result}")
            
            if result["status"] == "success":
                result["target_agent"] = parsed_args.target_agent
                self.logger.info(f"🤝 ASYNC DELEGATION - Queued agent_call event for '{parsed_args.target_agent}'")
                self.logger.debug(f"🔍 DEBUG - Event successfully queued with ID: {result.get('event_id', 'unknown')}")
            else:
                self.logger.error(f"❌ ASYNC DELEGATION FAILED - {result.get('message', 'Unknown error')}")
                self.logger.debug(f"🔍 DEBUG - EventSender failure details: {result}")
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            error_msg = f"Failed to queue agent_call event: {str(e)}"
            self.logger.error(f"❌ ASYNC DELEGATION FAILED - {error_msg}")
            self.logger.debug(f"🔍 DEBUG - Exception details: {type(e).__name__}: {str(e)}")
            import traceback
            self.logger.debug(f"🔍 DEBUG - Full traceback: {traceback.format_exc()}")
            return json.dumps({
                "status": "error",
                "message": error_msg,
                "error": str(e)
            }, indent=2)
    
    
    def get_tool(self) -> FunctionTool:
        """Get the FunctionTool instance (sync version).
        
        Returns:
            FunctionTool instance
        """
        self.logger.debug(f"🔍 DEBUG - get_tool() called - returning SYNC delegation tool")
        return self.tool
    
    def get_async_tool(self) -> FunctionTool:
        """Get the async FunctionTool instance that sends messages to queue.
        
        Returns:
            FunctionTool instance for async execution
        """
        self.logger.debug(f"🔍 DEBUG - get_async_tool() called - returning ASYNC delegation tool")
        return FunctionTool(
            name=self.name,
            description=f"{self.description} (Async execution via queue)",
            params_json_schema=DelegateAgentArgs.model_json_schema(),
            on_invoke_tool=self._run_delegate_agent_async
        )
    
    def supports_async_execution(self) -> bool:
        """Check if this tool supports async execution.
        
        Returns:
            bool: True since delegation tools support async execution
        """
        return True
    
    def get_async_metadata(self) -> Dict[str, Any]:
        """Get metadata for async execution configuration.
        
        Returns:
            Dict containing async execution settings for delegation
        """
        return {
            "priority": 5,  # Normal priority for delegation
            "timeout": 900,  # 15 minutes for delegation operations
            "max_retries": 2,  # Limited retries for delegation
            "retry_delay": 3
        }
