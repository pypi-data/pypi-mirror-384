"""Prompts list command for Gnosari Teams CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from rich.columns import Columns
from rich.panel import Panel
from rich.table import Table

from ...base import AsyncCommand
from ...exceptions import ConfigurationError
from ...registry import register_command
from ...schemas import CommandResponse
from ....prompts.manager import PromptManager


@register_command("prompts")
class PromptsListCommand(AsyncCommand):
    """List all available prompt templates."""
    
    name = "list"
    description = "List all available prompt templates"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            '--format', '-f',
            choices=['table', 'grid', 'simple'],
            default='table',
            help='Output format (default: table)'
        )
        parser.add_argument(
            '--show-description',
            action='store_true',
            help='Show prompt descriptions'
        )
    
    async def execute(self, args: argparse.Namespace) -> CommandResponse:
        """Execute the list command."""
        try:
            # Get available prompts
            prompt_manager = PromptManager()
            available_prompts = await prompt_manager.list_available_prompts()
            
            if not available_prompts:
                self.console.print("[yellow]No prompt templates found[/yellow]")
                return CommandResponse(
                    success=True,
                    message="No prompt templates found",
                    data={"prompts": []}
                )
            
            self.console.print(f"[green]Found {len(available_prompts)} prompt template(s):[/green]\n")
            
            if args.format == 'table':
                # Create table format
                table = Table(title="Available Prompt Templates")
                table.add_column("Name", style="cyan", no_wrap=True)
                table.add_column("File", style="blue")
                
                if args.show_description:
                    table.add_column("Description", style="dim")
                
                for prompt_name in sorted(available_prompts):
                    prompt_path = prompt_manager.get_prompt_path(prompt_name)
                    
                    row_data = [prompt_name, str(prompt_path.name)]
                    
                    if args.show_description:
                        try:
                            # Try to get the first line as description
                            with open(prompt_path, 'r', encoding='utf-8') as f:
                                first_line = f.readline().strip()
                                # Remove markdown comment syntax if present
                                if first_line.startswith('<!--') and first_line.endswith('-->'):
                                    description = first_line[4:-3].strip()
                                elif first_line.startswith('#'):
                                    description = first_line[1:].strip()
                                else:
                                    description = first_line[:50] + "..." if len(first_line) > 50 else first_line
                        except Exception:
                            description = "N/A"
                        row_data.append(description)
                    
                    table.add_row(*row_data)
                
                self.console.print(table)
            
            elif args.format == 'grid':
                # Create grid format
                panels = []
                for prompt_name in sorted(available_prompts):
                    prompt_path = prompt_manager.get_prompt_path(prompt_name)
                    
                    content = f"[cyan]{prompt_name}[/cyan]\n"
                    content += f"[dim]{prompt_path.name}[/dim]"
                    
                    if args.show_description:
                        try:
                            with open(prompt_path, 'r', encoding='utf-8') as f:
                                first_line = f.readline().strip()
                                if first_line.startswith('<!--') and first_line.endswith('-->'):
                                    description = first_line[4:-3].strip()
                                elif first_line.startswith('#'):
                                    description = first_line[1:].strip()
                                else:
                                    description = first_line[:30] + "..." if len(first_line) > 30 else first_line
                            content += f"\n[dim]{description}[/dim]"
                        except Exception:
                            pass
                    
                    panels.append(Panel(content, expand=True))
                
                self.console.print(Columns(panels, equal=True, expand=True))
            
            else:  # simple format
                for prompt_name in sorted(available_prompts):
                    self.console.print(f"  📄 {prompt_name}")
            
            return CommandResponse(
                success=True,
                message=f"Listed {len(available_prompts)} prompt templates",
                data={
                    "prompts": list(available_prompts),
                    "count": len(available_prompts)
                }
            )
            
        except Exception as e:
            self.logger.error(f"List prompts command failed: {e}")
            raise ConfigurationError(f"Failed to list prompt templates: {e}")