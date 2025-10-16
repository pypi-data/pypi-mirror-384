"""Prompts view command for Gnosari Teams CLI."""

from __future__ import annotations

import argparse
import re
from typing import Dict, Set

from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from ...base import AsyncCommand
from ...exceptions import ValidationError, ConfigurationError
from ...registry import register_command
from ...schemas import CommandResponse
from ....prompts.manager import PromptManager


def extract_variables_from_prompt(content: str) -> Set[str]:
    """Extract variable placeholders from prompt content."""
    # Look for {{variable}} patterns
    pattern = r'\{\{([^}]+)\}\}'
    matches = re.findall(pattern, content)
    return set(matches)


@register_command("prompts")
class PromptsViewCommand(AsyncCommand):
    """View a prompt template."""
    
    name = "view"
    description = "View a prompt template"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            'name',
            help='Name of the prompt template (without .md extension)'
        )
        parser.add_argument(
            'subcommand',
            nargs='?',
            choices=['variables'],
            help='View subcommands: variables - show only template variables'
        )
        parser.add_argument(
            '--format', '-f',
            choices=['rich', 'markdown', 'raw'],
            default='rich',
            help='Output format (default: rich)'
        )
        parser.add_argument(
            '--variables',
            action='store_true',
            help='Show template variables'
        )
        parser.add_argument(
            '--line-numbers',
            action='store_true',
            help='Show line numbers in output'
        )
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """Validate command arguments."""
        if not args.name.strip():
            self.console.print("[red]Prompt name cannot be empty[/red]")
            return False
        return True
    
    async def execute(self, args: argparse.Namespace) -> CommandResponse:
        """Execute the view command."""
        try:
            prompt_manager = PromptManager()
            
            # Check if prompt exists
            available_prompts = await prompt_manager.list_available_prompts()
            if args.name not in available_prompts:
                available_list = ", ".join(sorted(available_prompts))
                raise ValidationError(
                    f"Prompt template '{args.name}' not found. "
                    f"Available prompts: {available_list}"
                )
            
            # Load prompt content
            prompt_path = prompt_manager.get_prompt_path(args.name)
            with open(prompt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract variables from content
            variables = extract_variables_from_prompt(content)
            
            # Check if we should only show variables
            variables_only = args.subcommand == 'variables' or args.variables
            
            if variables_only:
                if variables:
                    self.console.print(f"[green]Variables in prompt '{args.name}':[/green]\n")
                    
                    # Create table for variables
                    table = Table(title=f"Template Variables for '{args.name}'")
                    table.add_column("Variable", style="cyan")
                    table.add_column("Placeholder", style="yellow")
                    table.add_column("Example Value", style="dim")
                    
                    for var in sorted(variables):
                        placeholder = f"{{{{{var}}}}}"
                        # Provide example values based on variable name
                        if 'name' in var.lower():
                            example = "John Doe"
                        elif 'email' in var.lower():
                            example = "user@example.com"
                        elif 'message' in var.lower():
                            example = "Hello, how can I help you?"
                        elif 'model' in var.lower():
                            example = "gpt-4o"
                        elif 'temperature' in var.lower():
                            example = "0.7"
                        else:
                            example = "your_value_here"
                        
                        table.add_row(var, placeholder, example)
                    
                    self.console.print(table)
                else:
                    self.console.print(f"[yellow]No variables found in prompt '{args.name}'[/yellow]")
                
                return CommandResponse(
                    success=True,
                    message=f"Displayed variables for prompt '{args.name}'",
                    data={
                        "prompt_name": args.name,
                        "variables": list(variables),
                        "variable_count": len(variables)
                    }
                )
            
            # Display full prompt content
            self.console.print(f"[green]Prompt Template: {args.name}[/green]")
            self.console.print(f"[dim]File: {prompt_path}[/dim]")
            
            if variables:
                self.console.print(f"[dim]Variables: {', '.join(sorted(variables))}[/dim]")
            
            self.console.print()
            
            # Display content based on format
            if args.format == 'rich':
                # Rich markdown rendering
                markdown_content = Markdown(content)
                self.console.print(Panel(
                    markdown_content,
                    title=f"📄 {args.name}",
                    border_style="blue",
                    padding=(1, 2)
                ))
            
            elif args.format == 'markdown':
                # Syntax highlighted markdown
                syntax = Syntax(
                    content,
                    "markdown",
                    theme="monokai",
                    line_numbers=args.line_numbers,
                    word_wrap=True
                )
                self.console.print(Panel(
                    syntax,
                    title=f"📄 {args.name} (Markdown)",
                    border_style="green",
                    padding=(1, 2)
                ))
            
            else:  # raw format
                # Raw text output
                if args.line_numbers:
                    lines = content.split('\n')
                    for i, line in enumerate(lines, 1):
                        self.console.print(f"{i:4d} │ {line}")
                else:
                    self.console.print(content)
            
            return CommandResponse(
                success=True,
                message=f"Displayed prompt template '{args.name}'",
                data={
                    "prompt_name": args.name,
                    "file_path": str(prompt_path),
                    "variables": list(variables),
                    "content_length": len(content),
                    "format": args.format
                }
            )
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"View prompt command failed: {e}")
            raise ConfigurationError(f"Failed to view prompt template: {e}")