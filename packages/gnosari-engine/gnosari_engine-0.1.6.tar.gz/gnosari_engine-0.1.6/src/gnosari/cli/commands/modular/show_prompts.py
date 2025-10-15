"""Modular show-prompts command for Gnosari Teams CLI."""

from __future__ import annotations

import argparse
import os
from pathlib import Path

from ...base import AsyncCommand
from ...exceptions import ValidationError, ConfigurationError
from ...registry import register_command
from ...schemas import CommandResponse


@register_command("modular")
class ModularShowPromptsCommand(AsyncCommand):
    """Display system prompts for modular team."""
    
    @property
    def name(self) -> str:
        return "show-prompts"
    
    @property
    def description(self) -> str:
        return "Display system prompts for modular team"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            'team_path',
            help='Path to modular team directory'
        )
        parser.add_argument(
            '--model',
            default=os.getenv("OPENAI_MODEL", "gpt-4o"),
            help='Model to use (default: gpt-4o)'
        )
        parser.add_argument(
            '--temperature',
            type=float,
            default=float(os.getenv("OPENAI_TEMPERATURE", "1")),
            help='Model temperature (default: 1.0)'
        )
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """Validate command arguments."""
        # Check if team directory exists
        team_path = Path(args.team_path)
        if not team_path.exists():
            self.console.print(f"[red]Modular team directory not found: {team_path}[/red]")
            return False
        
        if not team_path.is_dir():
            self.console.print(f"[red]Path is not a directory: {team_path}[/red]")
            return False
        
        return True
    
    async def execute(self, args: argparse.Namespace) -> CommandResponse:
        """Execute the show-prompts command for modular configuration."""
        try:
            from ....engine.config.configuration_manager import ConfigurationManager
            from ....prompts.prompts import build_agent_system_prompt
            from rich.panel import Panel
            from rich.syntax import Syntax
            
            self.console.print(f"[blue]Loading prompts for modular team:[/blue] {args.team_path}")
            
            # Load modular configuration directly
            config_manager = ConfigurationManager()
            modular_config = await config_manager.load_team_from_directory(Path(args.team_path))
            
            self.console.print(Panel(
                f"[bold cyan]Modular Team Configuration Prompts[/bold cyan]\n"
                f"Team Path: {args.team_path}\n"
                f"Team: {modular_config.main.name}\n"
                f"Model: {args.model}",
                title="🔍 Prompt Analysis",
                border_style="cyan"
            ))
            
            # Get agents from modular config
            if not modular_config.agents:
                raise ValidationError("No agents found in modular team configuration")
            
            self.console.print(f"\n[bold]Found {len(modular_config.agents)} agent(s):[/bold]\n")
            
            # Generate and display prompts for each agent
            for i, (agent_id, agent_comp) in enumerate(modular_config.agents.items(), 1):
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
                
                if i < len(modular_config.agents):
                    self.console.print()  # Add space between agents
            
            # Summary
            self.console.print(Panel(
                f"[green]✅ Successfully generated {len(modular_config.agents)} system prompts[/green]\n"
                f"[dim]Configuration Type: Modular[/dim]",
                title="📊 Summary",
                border_style="green"
            ))
            
            return CommandResponse(
                success=True,
                message=f"Successfully displayed prompts for modular team: {Path(args.team_path).name}",
                data={
                    "agent_count": len(modular_config.agents),
                    "team_path": args.team_path,
                    "model": args.model,
                    "config_type": "modular"
                }
            )
                
        except Exception as e:
            self.logger.error(f"Show prompts command failed: {e}")
            raise ConfigurationError(f"Failed to display prompts for modular team: {e}")