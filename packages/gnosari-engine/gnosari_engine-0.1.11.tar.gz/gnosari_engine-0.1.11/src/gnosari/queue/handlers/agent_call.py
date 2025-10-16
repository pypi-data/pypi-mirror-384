"""Agent call event handler following SOLID principles."""

import asyncio
import tempfile
import yaml
import os
from typing import Dict, Any

from .base import BaseEventHandler
from ...schemas.event import EventProcessingError
from ...utils.logging import get_logger

logger = get_logger(__name__)


class AgentCallEventHandler(BaseEventHandler):
    """Handler for agent_call events.
    
    This class follows the Single Responsibility Principle by handling
    only agent delegation events.
    """
    
    @property
    def event_type(self) -> str:
        """Return the event type this handler processes."""
        return "agent_call"
    
    def can_handle(self, event_data: Dict[str, Any]) -> bool:
        """Check if this handler can process the given event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            bool: True if this handler can process the event
        """
        event_type = event_data.get("event_type")
        if event_type != self.event_type:
            return False
            
        # Check required fields are present
        data = event_data.get("data", {})
        required_fields = ["target_agent", "message", "team_config"]
        return all(field in data for field in required_fields)
    
    def handle(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process the agent call event.
        
        Args:
            event_data: Event data dictionary
            
        Returns:
            Dict[str, Any]: Processing result
        """
        try:
            data = event_data.get("data", {})
            target_agent = data.get("target_agent")
            message = data.get("message")
            session_id = data.get("session_id")
            team_config = data.get("team_config")
            
            if not all([target_agent, message, team_config]):
                raise EventProcessingError(
                    "Missing required fields for agent call event",
                    error_code="MISSING_AGENT_CALL_DATA"
                )
            
            logger.info(f"🤝 Processing agent call for '{target_agent}'")
            
            # Execute the agent call
            result = asyncio.run(self._execute_agent_call(
                target_agent=target_agent,
                message=message,
                session_id=session_id,
                team_config=team_config
            ))
            
            return self._create_success_response(
                event_data=event_data,
                result=result,
                message=f"Successfully processed agent call for '{target_agent}'"
            )
            
        except Exception as e:
            logger.error(f"Failed to handle agent call: {e}")
            return self._create_error_response(
                event_data=event_data,
                error=e,
                message=f"Agent call processing failed: {e}"
            )
    
    async def _execute_agent_call(self, target_agent: str, message: str, 
                                  session_id: str, team_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the actual agent call.
        
        Args:
            target_agent: Name of the target agent
            message: Message to send to the agent
            session_id: Session identifier
            team_config: Team configuration
            
        Returns:
            Dict[str, Any]: Execution result
        """
        # Build team from configuration
        from ...engine.builder import TeamBuilder
        
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
            response_content = self._extract_response_content(result)
            
            logger.info(f"✅ Agent call completed for '{target_agent}'")
            
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
    
    def _extract_response_content(self, result: Any) -> str:
        """Extract response content from execution result.
        
        Args:
            result: Execution result
            
        Returns:
            str: Extracted response content
        """
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
        
        return response_content