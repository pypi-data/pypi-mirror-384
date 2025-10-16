"""Team execution strategies implementing the Strategy pattern."""

from typing import Any, Dict, Optional

from .interfaces import TeamExecutor
from ....engine.runner import TeamRunner
from ...exceptions import ValidationError


class StreamingTeamExecutor(TeamExecutor):
    """Executor for streaming team responses."""
    
    async def execute_team(
        self,
        runner: TeamRunner,
        message: str,
        agent_name: Optional[str] = None,
        stream: bool = False,
        debug: bool = False,
        session_id: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None,
        console: Any = None
    ) -> None:
        """Execute team with streaming output."""
        from rich.console import Console
        if not console:
            console = Console()
        
        if agent_name:
            await self._execute_single_agent_stream(
                runner, agent_name, message, debug, session_id, session_context, console
            )
        else:
            await self._execute_team_stream(
                runner, message, debug, session_id, session_context, console
            )
    
    async def _execute_single_agent_stream(
        self,
        runner: TeamRunner,
        agent_name: str,
        message: str,
        debug: bool,
        session_id: Optional[str],
        session_context: Optional[Dict[str, Any]],
        console: Any
    ) -> None:
        """Execute a single agent with streaming."""
        target_agent = runner.team.get_agent(agent_name)
        if not target_agent:
            available_agents = ", ".join(runner.team.list_agents())
            raise ValidationError(
                f"Agent '{agent_name}' not found in team. Available agents: {available_agents}"
            )
        
        console.print(f"[blue]🤖 {agent_name}:[/blue]", end=" ")
        
        async for event in runner.run_single_agent_stream(
            agent_name, message, debug, session_id=session_id, session_context=session_context
        ):
            self._handle_streaming_event(event, debug, console)
    
    async def _execute_team_stream(
        self,
        runner: TeamRunner,
        message: str,
        debug: bool,
        session_id: Optional[str],
        session_context: Optional[Dict[str, Any]],
        console: Any
    ) -> None:
        """Execute full team with streaming."""
        current_agent = None
        
        async for event in runner.run_team_stream(
            message, debug, session_id=session_id, session_context=session_context
        ):
            if debug:
                console.print(f"[dim][DEBUG] {event}[/dim]")
            else:
                if isinstance(event, dict):
                    agent_name = event.get('agent_name', 'Unknown')
                    
                    # Show agent name when it changes
                    if current_agent != agent_name and agent_name != 'Unknown':
                        if current_agent is not None:
                            print("\n")
                        console.print(f"[blue]🤖 {agent_name}:[/blue]", end=" ")
                        current_agent = agent_name
                    
                    self._handle_streaming_event(event, debug, console)
    
    def _handle_streaming_event(self, event: Dict[str, Any], debug: bool, console: Any) -> None:
        """Handle individual streaming events."""
        if debug:
            console.print(f"[dim][DEBUG] {event}[/dim]")
            return
        
        if not isinstance(event, dict):
            return
        
        event_type = event.get('type', '')
        
        if event_type == "response":
            content = event.get('content', '')
            print(content, end="", flush=True)
        elif event_type == "completion":
            print("\n")
        elif event_type == "tool_call":
            tool_name = event.get('tool_name', 'Unknown')
            console.print(f"\n[yellow]🔧 Using tool: {tool_name}[/yellow]")
        elif event_type == "tool_result":
            console.print("[green]✓[/green]", end="")


class NonStreamingTeamExecutor(TeamExecutor):
    """Executor for non-streaming team responses."""
    
    async def execute_team(
        self,
        runner: TeamRunner,
        message: str,
        agent_name: Optional[str] = None,
        stream: bool = False,
        debug: bool = False,
        session_id: Optional[str] = None,
        session_context: Optional[Dict[str, Any]] = None,
        console: Any = None
    ) -> None:
        """Execute team without streaming."""
        from rich.console import Console
        if not console:
            console = Console()
        
        if agent_name:
            await self._execute_single_agent(
                runner, agent_name, message, session_id, session_context, console
            )
        else:
            await self._execute_team(
                runner, message, debug, session_id, session_context, console
            )
    
    async def _execute_single_agent(
        self,
        runner: TeamRunner,
        agent_name: str,
        message: str,
        session_id: Optional[str],
        session_context: Optional[Dict[str, Any]],
        console: Any
    ) -> None:
        """Execute a single agent without streaming."""
        target_agent = runner.team.get_agent(agent_name)
        if not target_agent:
            available_agents = ", ".join(runner.team.list_agents())
            raise ValidationError(
                f"Agent '{agent_name}' not found in team. Available agents: {available_agents}"
            )
        
        result = await runner.run_agent_until_done_async(
            target_agent, message, session_id=session_id, session_context=session_context
        )
        
        if isinstance(result, dict) and "outputs" in result:
            for output in result["outputs"]:
                if output.get("type") == "completion":
                    console.print(f"\n[green]Agent Response:[/green]")
                    console.print(output.get("content", ""))
                    break
    
    async def _execute_team(
        self,
        runner: TeamRunner,
        message: str,
        debug: bool,
        session_id: Optional[str],
        session_context: Optional[Dict[str, Any]],
        console: Any
    ) -> None:
        """Execute full team without streaming."""
        result = await runner.run_team_async(
            message, debug, session_id=session_id, session_context=session_context
        )
        
        if hasattr(result, 'final_output'):
            console.print(f"\n[green]Team Response:[/green]")
            console.print(result.final_output)
        elif isinstance(result, dict) and "outputs" in result:
            for output in result["outputs"]:
                if output.get("type") == "completion":
                    console.print(f"\n[green]Team Response:[/green]")
                    console.print(output.get("content", ""))
                    break


class TeamExecutorFactory:
    """Factory for creating team executors."""
    
    def create_executor(self, stream: bool) -> TeamExecutor:
        """Create an executor based on streaming preference."""
        if stream:
            return StreamingTeamExecutor()
        else:
            return NonStreamingTeamExecutor()