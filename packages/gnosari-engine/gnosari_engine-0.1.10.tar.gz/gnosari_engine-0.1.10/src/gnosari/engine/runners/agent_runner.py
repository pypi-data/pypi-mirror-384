"""
Single agent execution runner
"""
from cohere.manually_maintained.cohere_aws.chat import StreamEvent
from typing import Optional, AsyncGenerator, Dict, Any
from agents import Runner, RunConfig, AgentUpdatedStreamEvent
from ..event_handlers import StreamEventHandler, ErrorHandler, MCPServerManager
from .base_runner import BaseRunner


class AgentRunner(BaseRunner):
    """Runner for executing single agent workflows."""
    
    async def run_agent_until_done_async(self, agent, message: str, 
                                        session_id: Optional[str] = None, 
                                        session_context: Optional[Dict[str, Any]] = None, 
                                        max_turns: Optional[int] = None) -> Dict[str, Any]:
        """Run a specific agent until completion.
        
        Args:
            agent: The agent to run
            message: Message to send
            session_id: Session ID for conversation persistence
            session_context: Session context data
            max_turns: Maximum number of turns
            
        Returns:
            Dict with agent outputs
        """
        mcp_manager = MCPServerManager()
        await mcp_manager.connect_servers([agent])

        try:
            # Create SessionContext with team_id and agent_id from YAML config
            context = self._enrich_session_context(
                session_context, 
                agent_name=agent.name,  # Use the specific agent being run
                session_id=session_id
            )
            
            # Create session with enriched context for proper database storage
            session = self._get_session(session_id, context_obj=context)
            self._log_session_info(session, session_id, f"agent '{agent.name}'")
            
            effective_max_turns = self._get_effective_max_turns(max_turns)
            run_config = RunConfig() if effective_max_turns else None
            
            # Only include max_turns if it's not None
            if effective_max_turns is not None:
                result = await Runner.run(
                    agent,
                    input=message,
                    session=session,
                    run_config=run_config,
                    context=context,
                    max_turns=effective_max_turns
                )
            else:
                result = await Runner.run(
                    agent,
                    input=message,
                    session=session,
                    run_config=run_config,
                    context=context
                )
            
            return {
                "outputs": [{"type": "completion", "content": result.final_output}],
                "agent_name": agent.name,
                "is_done": True
            }
        finally:
            await self.cleanup_manager.cleanup_all(session, mcp_manager, [agent])
    
    async def run_single_agent_stream(self, agent_name: str, message: str, 
                                     debug: bool = False, 
                                     session_id: Optional[str] = None, 
                                     session_context: Optional[Dict[str, Any]] = None, 
                                     max_turns: Optional[int] = None) -> AsyncGenerator[Dict[str, Any], None]:
        """Run a specific agent with streaming outputs using OpenAI Agents SDK.
        
        Args:
            agent_name: Name of the agent to run
            message: User message
            debug: Whether to show debug info
            session_id: Session ID for conversation persistence
            session_context: Session context data
            max_turns: Maximum number of turns
            
        Yields:
            Dict: Stream outputs (response chunks, tool calls, etc.)
        """
        # Get the target agent
        target_agent = self.team.get_agent(agent_name)
        if not target_agent:
            yield {
                "type": "error",
                "content": f"Agent '{agent_name}' not found in team configuration"
            }
            return
        
        self.logger.info(f"Executing single agent: {agent_name}")
        
        # Initialize handlers
        event_handler = StreamEventHandler(agent_name)
        error_handler = ErrorHandler(agent_name)
        mcp_manager = MCPServerManager()
        
        # Connect MCP servers for the target agent
        await mcp_manager.connect_servers([target_agent])
        
        session = None
        try:
            run_config = self._create_run_config(agent_name)
            
            # Create SessionContext with team_id and agent_id from YAML config
            context = self._enrich_session_context(
                session_context, 
                agent_name=agent_name,  # Use the specific agent being run
                session_id=session_id
            )
            
            # Create session with enriched context for proper database storage
            session = self._get_session(session_id, context_obj=context)
            self._log_session_info(session, session_id, f"single agent '{agent_name}' stream")
            
            # Prepare arguments for Runner.run_streamed
            effective_max_turns = self._get_effective_max_turns(max_turns)
            
            # Only include max_turns if it's not None
            if effective_max_turns is not None:
                result = Runner.run_streamed(
                    target_agent,
                    input=message,
                    run_config=run_config,
                    session=session,
                    context=context,
                    max_turns=effective_max_turns
                )
            else:
                result = Runner.run_streamed(
                    target_agent,
                    input=message,
                    run_config=run_config,
                    session=session,
                    context=context
                )
            
            self.logger.info(f"Starting to process streaming events for agent: {agent_name}")


            async for event in result.stream_events():
                if isinstance(event, AgentUpdatedStreamEvent):
                    self.logger.debug(f"Received event: {event.type}. Item: {event.new_agent.name}")

                self.logger.debug(f"Received event: {event.type}. Item: {event}")

                # Use event handler to process events
                async for response in event_handler.handle_event(event):
                    yield response

            # Yield final completion
            yield {
                "type": "completion",
                "content": result.final_output,
                "output": result.final_output,
                "agent_name": agent_name,
                "is_done": True
            }
            
        except Exception as e:
            self.logger.error(f"EXCEPTION occurred!!!! : {e}")
            # Use error handler
            error_response = error_handler.handle_error(e)
            yield error_response
            raise e
        finally:
            await self.cleanup_manager.cleanup_all(session, mcp_manager, [target_agent])