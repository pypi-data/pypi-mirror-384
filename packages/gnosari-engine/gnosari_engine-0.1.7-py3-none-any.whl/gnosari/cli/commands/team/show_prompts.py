"""Team show-prompts command for Gnosari Teams CLI."""

from __future__ import annotations

import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from ....engine.builder import TeamBuilder
from ....prompts.prompts import build_agent_system_prompt


def extract_agent_tool_info(agent, tool_manager, original_agent_config):
    """Extract agent tool information for prompt display."""
    agent_info = {
        'name': agent.name if hasattr(agent, 'name') else 'Unknown',
        'tools': [],
        'knowledge': []
    }
    
    # Extract tools
    if hasattr(agent, 'tools') and agent.tools:
        for tool in agent.tools:
            if hasattr(tool, 'name'):
                agent_info['tools'].append(tool.name)
            elif hasattr(tool, '__name__'):
                agent_info['tools'].append(tool.__name__)
    
    # Extract knowledge from original config
    if isinstance(original_agent_config, dict):
        knowledge_refs = original_agent_config.get('knowledge', [])
        if isinstance(knowledge_refs, list):
            agent_info['knowledge'] = knowledge_refs
    
    return agent_info


class ShowPromptsCommand:
    """Display generated system prompts for all agents in the team."""
    
    def __init__(self, console: Console):
        """Initialize the command with a console."""
        self.console = console
    
    async def run(self, args) -> object:
        """Execute the show-prompts command."""
        try:
            import yaml
            from rich.text import Text
            
            # Get team path from args
            team_path = Path(args.team_path)
            if not team_path.exists():
                return type('Result', (), {'success': False, 'message': f"Team path not found: {team_path}"})()
            
            # Check if it's a directory (modular) or file (single)
            if team_path.is_dir():
                return await self._execute_modular(args, team_path)
            else:
                return await self._execute_single_file(args, team_path)
                
        except Exception as e:
            return type('Result', (), {'success': False, 'message': f"Failed to display prompts: {e}"})()
    
    
    async def _execute_single_file(self, args, config_path: Path):
        """Execute for single file configuration."""
        import yaml
        from rich.text import Text
        
        # Load team configuration
        with open(config_path, 'r', encoding='utf-8') as f:
            team_config = yaml.safe_load(f)
            
        # Get model and temperature from environment or defaults
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        temperature = float(os.getenv("OPENAI_TEMPERATURE", "1"))
            
        self.console.print(Panel(
            f"[bold cyan]Team Configuration Prompts[/bold cyan]\n"
            f"Config: {config_path}\n"
            f"Team: {team_config.get('name', 'Unknown')}\n"
            f"Model: {model}",
            title="🔍 Prompt Analysis",
            border_style="cyan"
        ))
        
        # Create a dummy TeamBuilder to access tool manager
        dummy_builder = TeamBuilder(
            api_key="dummy",  # Not needed for prompt generation
            model=model,
            temperature=temperature
        )
        
        # Get agents from config
        agents_config = team_config.get('agents', [])
        if not agents_config:
            return type('Result', (), {'success': False, 'message': "No agents found in team configuration"})()
        
        # Filter agents if specific agent requested
        if hasattr(args, 'agent') and args.agent:
            agents_config = [agent for agent in agents_config if agent.get('name') == args.agent]
            if not agents_config:
                return type('Result', (), {'success': False, 'message': f"Agent '{args.agent}' not found in team configuration"})()

        self.console.print(f"\n[bold]Found {len(agents_config)} agent(s):[/bold]\n")

        # Generate and display prompts for each agent
        for i, agent_config in enumerate(agents_config, 1):
            agent_name = agent_config.get('name', f'Agent {i}')
            agent_instructions = agent_config.get('instructions', '')
            
            self.console.print(f"[bold cyan]Agent {i}: {agent_name}[/bold cyan]")
            self.console.print("─" * 60)
            
            # Display agent configuration
            self.console.print(f"[dim]Instructions:[/dim] {agent_instructions[:100]}{'...' if len(agent_instructions) > 100 else ''}")
            
            # Extract agent info
            mock_agent = type('MockAgent', (), {
                'name': agent_name,
                'tools': [],
                'knowledge': []
            })()
            
            agent_info = extract_agent_tool_info(mock_agent, None, agent_config)
            
            if agent_info['tools']:
                self.console.print(f"[dim]Tools:[/dim] {', '.join(agent_info['tools'])}")
            
            if agent_info['knowledge']:
                self.console.print(f"[dim]Knowledge:[/dim] {', '.join(agent_info['knowledge'])}")
            
            # Determine if agent is orchestrator
            is_orchestrator = agent_config.get('orchestrator', False)
            
            # Generate system prompt
            try:
                prompt_parts = build_agent_system_prompt(
                    name=agent_name,
                    instructions=agent_instructions,
                    agent_tools=agent_info.get('tools', []),
                    tool_manager=None,
                    agent_config=agent_config,
                    knowledge_descriptions={},
                    team_config=team_config,
                    real_tool_info=None
                )
                
                # Convert prompt parts to string
                system_prompt = "\n".join(prompt_parts.get('background', []))
                if prompt_parts.get('steps'):
                    system_prompt += "\n\n" + "\n".join(prompt_parts['steps'])
                if prompt_parts.get('output_instructions'):
                    system_prompt += "\n\n" + "\n".join(prompt_parts['output_instructions'])
                
                # Display the prompt in a panel with syntax highlighting
                prompt_syntax = Syntax(
                    system_prompt,
                    "text",
                    theme="monokai",
                    word_wrap=True,
                    line_numbers=False
                )
                
                self.console.print(Panel(
                    prompt_syntax,
                    title=f"🤖 {agent_name} System Prompt {'(Orchestrator)' if is_orchestrator else '(Worker)'}",
                    border_style="green" if is_orchestrator else "blue",
                    padding=(1, 2)
                ))
                
            except Exception as e:
                self.console.print(Panel(
                    f"[red]Error generating prompt: {e}[/red]",
                    title=f"❌ {agent_name} Prompt Error",
                    border_style="red"
                ))
            
            if i < len(agents_config):
                self.console.print()  # Add space between agents
        
        # Summary (simplified since calculating total characters is complex now)
        self.console.print(Panel(
            f"[green]✅ Successfully generated {len(agents_config)} system prompts[/green]\n"
            f"[dim]Configuration Type: Single File[/dim]",
            title="📊 Summary",
            border_style="green"
        ))
        
        return type('Result', (), {
            'success': True, 
            'message': f"Successfully displayed prompts for {len(agents_config)} agents"
        })()
    
    async def _execute_modular(self, args, config_path: Path):
        """Execute for modular directory configuration."""
        from ....engine.config.configuration_manager import ConfigurationManager
        from ....prompts.prompts import build_agent_system_prompt
        from rich.panel import Panel
        from rich.syntax import Syntax
        
        self.console.print(f"[blue]Loading prompts for modular team:[/blue] {config_path}")
        
        # Load modular configuration directly
        config_manager = ConfigurationManager()
        modular_config = await config_manager.load_team_from_directory(config_path)
        
        # Get model from environment
        model = os.getenv("OPENAI_MODEL", "gpt-4o")
        
        self.console.print(Panel(
            f"[bold cyan]Modular Team Configuration Prompts[/bold cyan]\n"
            f"Team Path: {config_path}\n"
            f"Team: {modular_config.main.name}\n"
            f"Model: {model}",
            title="🔍 Prompt Analysis",
            border_style="cyan"
        ))
        
        # Get agents from modular config
        if not modular_config.agents:
            return type('Result', (), {'success': False, 'message': "No agents found in modular team configuration"})()
        
        # Filter agents if specific agent requested
        filtered_agents = modular_config.agents
        if hasattr(args, 'agent') and args.agent:
            filtered_agents = {k: v for k, v in modular_config.agents.items() 
                             if (v.name or k) == args.agent}
            if not filtered_agents:
                return type('Result', (), {'success': False, 'message': f"Agent '{args.agent}' not found in modular team configuration"})()

        self.console.print(f"\n[bold]Found {len(filtered_agents)} agent(s):[/bold]\n")

        # Generate and display prompts for each agent
        for i, (agent_id, agent_comp) in enumerate(filtered_agents.items(), 1):
            agent_name = agent_comp.name or agent_id
            agent_instructions = agent_comp.instructions or ''
            
            self.console.print(f"[bold cyan]Agent {i}: {agent_name}[/bold cyan]")
            self.console.print("─" * 60)
            
            # Display agent configuration
            self.console.print(f"[dim]Instructions:[/dim] {agent_instructions[:100]}{'...' if len(agent_instructions) > 100 else ''}")
            
            if agent_comp.tools:
                self.console.print(f"[dim]Tools:[/dim] {', '.join(agent_comp.tools)}")
            
            if agent_comp.knowledge:
                self.console.print(f"[dim]Knowledge:[/dim] {', '.join(agent_comp.knowledge)}")
            
            if hasattr(agent_comp, 'trigger') and agent_comp.trigger:
                trigger_types = [t.get('event_type', 'unknown') for t in agent_comp.trigger]
                self.console.print(f"[dim]Event Triggers:[/dim] {', '.join(trigger_types)}")
            
            # Determine if agent is orchestrator
            is_orchestrator = agent_comp.orchestrator
            
            # Convert agent component to dict for prompt building
            agent_config_dict = {
                'name': agent_name,
                'instructions': agent_instructions,
                'tools': agent_comp.tools or [],
                'knowledge': agent_comp.knowledge or [],
                'orchestrator': agent_comp.orchestrator,
                'model': agent_comp.model,
                'temperature': agent_comp.temperature
            }
            
            # Add trigger configuration if present
            if hasattr(agent_comp, 'trigger') and agent_comp.trigger:
                agent_config_dict['trigger'] = agent_comp.trigger
            
            # Add delegation if present
            if hasattr(agent_comp, 'delegation') and agent_comp.delegation:
                agent_config_dict['delegation'] = agent_comp.delegation
            
            # Add traits if present
            if hasattr(agent_comp, 'traits') and agent_comp.traits:
                agent_config_dict['traits'] = agent_comp.traits
            
            # Add learning if present
            if hasattr(agent_comp, 'learning') and agent_comp.learning:
                agent_config_dict['learning'] = agent_comp.learning
            
            # Add memory if present
            if hasattr(agent_comp, 'memory') and agent_comp.memory:
                agent_config_dict['memory'] = agent_comp.memory
            
            # Generate system prompt
            try:
                prompt_parts = build_agent_system_prompt(
                    name=agent_name,
                    instructions=agent_instructions,
                    agent_tools=agent_comp.tools or [],
                    tool_manager=None,
                    agent_config=agent_config_dict,
                    knowledge_descriptions={},
                    team_config=None,
                    real_tool_info=None
                )
                
                # Convert prompt parts to string
                system_prompt = "\n".join(prompt_parts.get('background', []))
                if prompt_parts.get('steps'):
                    system_prompt += "\n\n" + "\n".join(prompt_parts['steps'])
                if prompt_parts.get('output_instructions'):
                    system_prompt += "\n\n" + "\n".join(prompt_parts['output_instructions'])
                
                # Display the prompt in a panel with syntax highlighting
                prompt_syntax = Syntax(
                    system_prompt,
                    "text",
                    theme="monokai",
                    word_wrap=True,
                    line_numbers=False
                )
                
                self.console.print(Panel(
                    prompt_syntax,
                    title=f"🤖 {agent_name} System Prompt {'(Orchestrator)' if is_orchestrator else '(Worker)'}",
                    border_style="green" if is_orchestrator else "blue",
                    padding=(1, 2)
                ))
                
            except Exception as e:
                self.console.print(Panel(
                    f"[red]Error generating prompt: {e}[/red]",
                    title=f"❌ {agent_name} Prompt Error",
                    border_style="red"
                ))
            
            if i < len(filtered_agents):
                self.console.print()  # Add space between agents
        
        # Summary
        self.console.print(Panel(
            f"[green]✅ Successfully generated {len(filtered_agents)} system prompts[/green]\n"
            f"[dim]Configuration Type: Modular[/dim]",
            title="📊 Summary",
            border_style="green"
        ))
        
        return type('Result', (), {
            'success': True,
            'message': f"Successfully displayed prompts for modular team: {config_path.name}"
        })()