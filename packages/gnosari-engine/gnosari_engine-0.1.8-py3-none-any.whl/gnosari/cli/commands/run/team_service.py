"""Team execution service following SOLID principles."""

import os
import tempfile
import uuid
from pathlib import Path
from typing import Optional, Dict, Any

import yaml

from ....engine.config.configuration_manager import ConfigurationManager
from ....engine.builder import TeamBuilder
from ....engine.runner import TeamRunner


class TeamConfigurationProvider:
    """Provides team configuration from various sources (SRP)."""
    
    def __init__(self):
        self._config_manager = ConfigurationManager()
    
    async def load_configuration(self, team_path: Path) -> tuple[Dict[str, Any], str]:
        """Load team configuration and return config dict and identifier."""
        if team_path.is_file():
            return await self._load_monolithic_config(team_path)
        elif team_path.is_dir():
            return await self._load_modular_config(team_path)
        else:
            raise ValueError(f"Invalid team path: {team_path}")
    
    async def _load_monolithic_config(self, file_path: Path) -> tuple[Dict[str, Any], str]:
        """Load monolithic YAML configuration."""
        with open(file_path, 'r') as f:
            config = yaml.safe_load(f)
        return config, file_path.stem
    
    async def _load_modular_config(self, dir_path: Path) -> tuple[Dict[str, Any], str]:
        """Load modular directory configuration."""
        team_yaml = dir_path / "team.yaml"
        main_yaml = dir_path / "main.yaml"
        
        if not (team_yaml.exists() or main_yaml.exists()):
            raise ValueError(f"No team.yaml or main.yaml found in directory: {dir_path}")
        
        # Check if it's truly modular (has component directories)
        if (dir_path / "agents").exists() or (dir_path / "tools").exists() or (dir_path / "knowledge").exists():
            # True modular configuration
            modular_config = await self._config_manager.load_team_from_directory(dir_path)
            config = await self._config_manager.convert_to_legacy_format(modular_config)
        else:
            # Single file in directory
            config_file = team_yaml if team_yaml.exists() else main_yaml
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
        
        return config, dir_path.name


class TeamConfigurationWriter:
    """Writes team configuration to temporary files for TeamBuilder (SRP)."""
    
    def create_temp_config_file(self, config: Dict[str, Any]) -> str:
        """Create a temporary config file and return its path."""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
        yaml.dump(config, temp_file, default_flow_style=False)
        temp_file.close()
        return temp_file.name


class TeamExecutionService:
    """Main service for executing teams (SRP + DIP)."""
    
    def __init__(self, config_provider: TeamConfigurationProvider, config_writer: TeamConfigurationWriter):
        self._config_provider = config_provider
        self._config_writer = config_writer
    
    def _is_tool_noise(self, content: str) -> bool:
        """Check if content looks like raw tool output that should be filtered."""
        if not content:
            return True
            
        # Patterns that indicate raw tool output (only filter very obvious ones)
        noise_indicators = [
            'Title:',  # Raw knowledge retrieval
            'URL Source:',  # Raw knowledge retrieval  
            'Markdown Content:',  # Raw knowledge retrieval
        ]
        
        # Only filter if it clearly starts with raw tool output patterns
        return any(content.strip().startswith(indicator) for indicator in noise_indicators)
    
    def _format_agent_content(self, content: str) -> str:
        """Format agent content for better readability."""
        if not content:
            return ""
        
        # Just return the content as is for streaming - individual words/phrases
        # The sentence breaks will naturally happen as the agent streams
        return content
    
    async def execute_team(
        self,
        team_path: Path,
        message: str,
        agent: Optional[str] = None,
        session_id: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        stream: bool = False,
        show_prompts: bool = False,
        console = None,
        ctx = None
    ) -> Dict[str, Any]:
        """Execute a team with the given parameters."""
        
        # Validate API key
        final_api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not final_api_key:
            return {
                'success': False,
                'message': 'OpenAI API key is required. Set it with --api-key or OPENAI_API_KEY environment variable.'
            }
        
        try:
            # Load configuration
            config, team_identifier = await self._config_provider.load_configuration(team_path)
            
            # Write to temporary file for TeamBuilder
            temp_config_path = self._config_writer.create_temp_config_file(config)
            
            try:
                # Build team with reduced verbosity during construction
                if console:
                    console.print("[dim]Building team...[/dim]")
                
                # Temporarily reduce log level for cleaner output
                import logging
                original_level = logging.getLogger().level
                logging.getLogger().setLevel(logging.WARNING)
                
                try:
                    team_builder = TeamBuilder()
                    team = await team_builder.build_team(temp_config_path)
                    
                    if console:
                        console.print("[dim green]✅ Team built successfully[/dim green]")
                        console.print()
                finally:
                    # Restore original log level
                    logging.getLogger().setLevel(original_level)
                
                # Show prompts if requested
                if show_prompts and console:
                    console.print("\n[bold]Generated System Prompts:[/bold]")
                    # This would need implementation based on actual team structure
                    console.print("System prompt display not implemented yet")
                
                # Run team  
                team_runner = TeamRunner(team)
                
                final_session_id = session_id or str(uuid.uuid4())
                
                # Create session context with team identifier
                session_context_dict = {
                    'team_identifier': team_identifier,
                    'session_id': final_session_id
                }
                
                if stream:
                    # Use streaming execution
                    if console:
                        console.print(f"[dim]Session: {final_session_id}[/dim]")
                        console.print()
                        # Create clear visual separator for agent responses
                        console.print("┌" + "─" * 78 + "┐")
                        if agent:
                            console.print("│" + f" " * 20 + f"🎯 {agent.upper()} RESPONSE" + " " * 20 + "│")
                        else:
                            console.print("│" + " " * 25 + "🤖 AGENT RESPONSE" + " " * 25 + "│")
                        console.print("└" + "─" * 78 + "┘")
                        console.print()
                    
                    # Collect streaming results with enhanced formatting
                    results = []
                    current_agent = None
                    
                    # Use appropriate runner method based on whether specific agent is requested
                    if agent:
                        # Run specific agent using run_single_agent_stream
                        stream_generator = team_runner.run_single_agent_stream(
                            agent_name=agent,
                            message=message,
                            session_id=final_session_id,
                            session_context=session_context_dict
                        )
                    else:
                        # Run full team using run_team_stream
                        stream_generator = team_runner.run_team_stream(
                            message=message,
                            session_id=final_session_id,
                            session_context=session_context_dict
                        )
                    
                    async for response in stream_generator:
                        # DEBUG: Print the response structure to understand what we're getting
                        if console and ctx and ctx.debug:
                            console.print(f"[dim]DEBUG Response: {response}[/dim]")
                        
                        # Handle agent transitions with clear visual indicators
                        if response.get('agent') and response['agent'] != current_agent:
                            current_agent = response['agent']
                            if console:
                                console.print(f"\n[bold blue]🎯 {current_agent.upper()}:[/bold blue]")
                                console.print("─" * 40)
                        
                        # Handle tool calls - show what tool is being used
                        if console and response.get('type') == 'tool_call':
                            tool_name = response.get('tool_name', 'unknown')
                            args_str = response.get('arguments', '{}')
                            
                            try:
                                import json
                                args = json.loads(args_str) if isinstance(args_str, str) else args_str
                            except:
                                args = {}
                            
                            # Show tool usage clearly
                            if tool_name == 'knowledge_query':
                                query = args.get('query', 'Unknown query')
                                # Truncate long queries for display
                                display_query = query[:50] + "..." if len(query) > 50 else query
                                console.print(f"[dim yellow]🔍 Searching knowledge: {display_query}[/dim yellow]")
                            elif tool_name == 'delegate_agent':
                                agent_name = args.get('agent_name', 'unknown')
                                console.print(f"[dim yellow]👥 Delegating to: {agent_name}[/dim yellow]")
                            else:
                                console.print(f"[dim yellow]🔧 Using tool: {tool_name}[/dim yellow]")
                        
                        # Handle tool results - show success/failure status
                        elif console and response.get('type') == 'tool_result':
                            content = response.get('content', '')
                            
                            # Check if tool execution was successful
                            if 'error' in str(response).lower():
                                console.print("[dim red]❌ Tool failed[/dim red]")
                            else:
                                # Show success with minimal details for clean output
                                if len(content) > 1000:  # Large content likely from knowledge query
                                    # Count results for knowledge queries
                                    result_count = str(content).count('Title:') if content else 0
                                    console.print(f"[dim green]✅ Knowledge retrieved ({result_count} sources)[/dim green]")
                                else:
                                    console.print("[dim green]✅ Tool completed[/dim green]")
                        
                        # Display ONLY clean agent responses (not tool results)
                        elif console and response.get('type') == 'response' and response.get('content'):
                            content = response['content']
                            
                            # Skip raw tool outputs but show clean agent responses
                            if not self._is_tool_noise(content):
                                # Format for better readability
                                formatted_content = self._format_agent_content(content)
                                if formatted_content.strip():
                                    console.print(formatted_content, end='')
                        
                        results.append(response)
                    
                    if console:
                        console.print("\n")
                        console.print("┌" + "─" * 78 + "┐") 
                        console.print("│" + " " * 28 + "✨ COMPLETE ✨" + " " * 28 + "│")
                        console.print("└" + "─" * 78 + "┘")
                    
                    result = {'responses': results}
                else:
                    # Use non-streaming execution
                    if console:
                        console.print(f"[dim]Session: {final_session_id}[/dim]")
                        console.print()
                    
                    if agent:
                        # Get the specific agent object and run it
                        target_agent = team.get_agent(agent)
                        if not target_agent:
                            return {
                                'success': False,
                                'message': f"Agent '{agent}' not found in team configuration"
                            }
                        
                        result = await team_runner.run_agent_until_done_async(
                            agent=target_agent,
                            message=message,
                            session_id=final_session_id,
                            session_context=session_context_dict
                        )
                    else:
                        # Run full team
                        result = await team_runner.run_team_async(
                            message=message,
                            session_id=final_session_id,
                            session_context=session_context_dict
                        )
                    
                    # Display the result to console in non-streaming mode
                    if console and result:
                        console.print("┌" + "─" * 78 + "┐")
                        if agent:
                            console.print("│" + f" " * 20 + f"🎯 {agent.upper()} RESPONSE" + " " * 20 + "│")
                        else:
                            console.print("│" + " " * 25 + "🤖 AGENT RESPONSE" + " " * 25 + "│")
                        console.print("└" + "─" * 78 + "┘")
                        console.print()
                        
                        # Extract and display the final response content
                        content_displayed = False
                        
                        # Handle the expected TeamRunner response format
                        if isinstance(result, dict) and 'outputs' in result:
                            outputs = result['outputs']
                            if outputs and isinstance(outputs, list) and len(outputs) > 0:
                                first_output = outputs[0]
                                if isinstance(first_output, dict) and 'content' in first_output:
                                    content = first_output['content']
                                    if content and content.strip():
                                        console.print(content.strip())
                                        content_displayed = True
                        
                        # Fallback for other formats
                        if not content_displayed:
                            if hasattr(result, 'messages') and result.messages:
                                # Get the last assistant message
                                for msg in reversed(result.messages):
                                    if hasattr(msg, 'role') and msg.role == 'assistant':
                                        content = getattr(msg, 'content', None)
                                        if content and isinstance(content, list):
                                            # Handle content array (OpenAI format)
                                            for item in content:
                                                if hasattr(item, 'text') and item.text:
                                                    console.print(item.text.strip())
                                                    content_displayed = True
                                                    break
                                        elif content and isinstance(content, str):
                                            # Handle string content
                                            console.print(content.strip())
                                            content_displayed = True
                                        break
                            elif hasattr(result, 'content'):
                                # Direct content attribute
                                console.print(result.content.strip())
                                content_displayed = True
                            elif isinstance(result, dict) and 'content' in result:
                                # Dictionary with content key
                                console.print(result['content'].strip())
                                content_displayed = True
                            elif isinstance(result, str):
                                # String result
                                console.print(result.strip())
                                content_displayed = True
                        
                        # If we still couldn't display content, show debug info
                        if not content_displayed:
                            console.print(f"[dim]Result type: {type(result)}[/dim]")
                            if isinstance(result, dict):
                                console.print(f"[dim]Available keys: {list(result.keys())}[/dim]")
                            elif hasattr(result, '__dict__'):
                                console.print(f"[dim]Available attributes: {list(result.__dict__.keys())}[/dim]")
                        
                        console.print()
                        console.print("┌" + "─" * 78 + "┐") 
                        console.print("│" + " " * 28 + "✨ COMPLETE ✨" + " " * 28 + "│")
                        console.print("└" + "─" * 78 + "┘")
                
                return {
                    'success': True,
                    'message': 'Team execution completed successfully',
                    'result': result
                }
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_config_path)
                except OSError:
                    pass
                    
        except Exception as e:
            return {
                'success': False,
                'message': f'Team execution failed: {e}'
            }


# Factory following Dependency Injection principle
def create_team_execution_service() -> TeamExecutionService:
    """Factory function to create team execution service with dependencies."""
    config_provider = TeamConfigurationProvider()
    config_writer = TeamConfigurationWriter()
    return TeamExecutionService(config_provider, config_writer)