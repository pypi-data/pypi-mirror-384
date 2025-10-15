"""Modular validate command for Gnosari Teams CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from rich.panel import Panel
from rich.table import Table

from ...base import AsyncCommand
from ...exceptions import ValidationError, ConfigurationError
from ...registry import register_command
from ...schemas import CommandResponse


@register_command("modular")
class ModularValidateCommand(AsyncCommand):
    """Validate modular team configuration."""
    
    name = "validate"
    description = "Validate modular team configuration"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            'team_path',
            help='Path to modular team directory'
        )
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Show detailed validation information'
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
        """Execute the validate command."""
        try:
            from ....engine.config.configuration_manager import ConfigurationManager
            
            self.console.print(f"[blue]Validating modular team:[/blue] {args.team_path}")
            
            # Load and validate modular configuration
            config_manager = ConfigurationManager()
            modular_config = await config_manager.load_team_from_directory(Path(args.team_path))
            
            # Basic validation successful if we get here
            self.console.print(f"[green]✅ Modular team configuration is valid![/green]")
            
            # Display summary information
            team_name = modular_config.main.name if modular_config.main else "Unknown"
            agent_count = len(modular_config.agents) if modular_config.agents else 0
            tool_count = len(modular_config.tools) if modular_config.tools else 0
            knowledge_count = len(modular_config.knowledge) if modular_config.knowledge else 0
            
            # Create summary table
            summary_table = Table(title="Team Configuration Summary")
            summary_table.add_column("Property", style="cyan")
            summary_table.add_column("Value", style="green")
            
            summary_table.add_row("Team Name", team_name)
            summary_table.add_row("Agents", str(agent_count))
            summary_table.add_row("Tools", str(tool_count))
            summary_table.add_row("Knowledge Bases", str(knowledge_count))
            
            self.console.print(summary_table)
            
            # Verbose information
            if args.verbose:
                self.console.print()
                
                # Agent details
                if modular_config.agents:
                    agent_table = Table(title="Agent Details")
                    agent_table.add_column("Name", style="cyan")
                    agent_table.add_column("Type", style="yellow")
                    agent_table.add_column("Instructions", style="dim")
                    
                    for agent in modular_config.agents:
                        agent_type = "Orchestrator" if getattr(agent, 'orchestrator', False) else "Worker"
                        instructions = getattr(agent, 'instructions', '')
                        # Truncate long instructions
                        if len(instructions) > 50:
                            instructions = instructions[:47] + "..."
                        
                        agent_table.add_row(
                            getattr(agent, 'name', 'Unknown'),
                            agent_type,
                            instructions
                        )
                    
                    self.console.print(agent_table)
                    self.console.print()
                
                # Tool details
                if modular_config.tools:
                    tool_table = Table(title="Tool Details")
                    tool_table.add_column("Name", style="cyan")
                    tool_table.add_column("Module", style="yellow")
                    tool_table.add_column("Class", style="green")
                    
                    for tool in modular_config.tools:
                        tool_table.add_row(
                            getattr(tool, 'name', 'Unknown'),
                            getattr(tool, 'module', 'N/A'),
                            getattr(tool, 'class_name', 'N/A')
                        )
                    
                    self.console.print(tool_table)
                    self.console.print()
                
                # Knowledge details
                if modular_config.knowledge:
                    knowledge_table = Table(title="Knowledge Base Details")
                    knowledge_table.add_column("Name", style="cyan")
                    knowledge_table.add_column("Type", style="yellow")
                    knowledge_table.add_column("Data Sources", style="green")
                    
                    for kb in modular_config.knowledge:
                        data_sources = getattr(kb, 'data', [])
                        if isinstance(data_sources, list) and len(data_sources) > 2:
                            data_display = f"{len(data_sources)} sources"
                        else:
                            data_display = str(data_sources)
                        
                        knowledge_table.add_row(
                            getattr(kb, 'name', 'Unknown'),
                            getattr(kb, 'type', 'Unknown'),
                            data_display
                        )
                    
                    self.console.print(knowledge_table)
            
            # Check for common issues
            warnings = []
            
            if agent_count == 0:
                warnings.append("No agents defined in configuration")
            
            if agent_count > 0:
                # Check for orchestrator
                has_orchestrator = any(
                    getattr(agent, 'orchestrator', False) 
                    for agent in modular_config.agents
                )
                if not has_orchestrator:
                    warnings.append("No orchestrator agent found - consider setting orchestrator: true on one agent")
            
            if tool_count == 0:
                warnings.append("No tools defined - agents may have limited capabilities")
            
            # Display warnings if any
            if warnings:
                self.console.print()
                warning_panel = Panel(
                    "\n".join(f"⚠️  {warning}" for warning in warnings),
                    title="Validation Warnings",
                    border_style="yellow"
                )
                self.console.print(warning_panel)
            
            return CommandResponse(
                success=True,
                message="Modular team configuration validation completed",
                data={
                    "team_name": team_name,
                    "agent_count": agent_count,
                    "tool_count": tool_count,
                    "knowledge_count": knowledge_count,
                    "warnings": warnings
                }
            )
            
        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            self.console.print(f"[red]❌ Validation failed: {e}[/red]")
            raise ValidationError(f"Modular team validation failed: {e}")