"""Prompts use command for Gnosari Teams CLI."""

from __future__ import annotations

import argparse
import re
from typing import Dict

from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax

from ...base import AsyncCommand
from ...exceptions import ValidationError, ConfigurationError
from ...registry import register_command
from ...schemas import CommandResponse
from ....prompts.manager import PromptManager


def parse_variable_args(unknown_args: list) -> Dict[str, str]:
    """Parse --variable_name value arguments from unknown args."""
    variables = {}
    i = 0
    while i < len(unknown_args):
        if unknown_args[i].startswith('--'):
            var_name = unknown_args[i][2:]  # Remove --
            if i + 1 < len(unknown_args) and not unknown_args[i + 1].startswith('--'):
                variables[var_name] = unknown_args[i + 1]
                i += 2
            else:
                # Variable without value - treat as flag or empty string
                variables[var_name] = ""
                i += 1
        else:
            i += 1
    return variables


def substitute_variables(content: str, variables: Dict[str, str]) -> str:
    """Substitute variables in content."""
    result = content
    for var_name, var_value in variables.items():
        placeholder = f"{{{{{var_name}}}}}"
        result = result.replace(placeholder, var_value)
    return result


def find_missing_variables(content: str, provided_vars: Dict[str, str]) -> list:
    """Find variables that are required but not provided."""
    pattern = r'\{\{([^}]+)\}\}'
    required_vars = set(re.findall(pattern, content))
    provided_var_names = set(provided_vars.keys())
    return list(required_vars - provided_var_names)


@register_command("prompts")
class PromptsUseCommand(AsyncCommand):
    """Use a prompt template with variable substitution."""
    
    name = "use"
    description = "Use a prompt template with variable substitution"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            'name',
            help='Name of the prompt template (without .md extension)'
        )
        parser.add_argument(
            'message',
            help='Message to use with the prompt'
        )
        parser.add_argument(
            '--format', '-f',
            choices=['rich', 'markdown', 'raw'],
            default='rich',
            help='Output format (default: rich)'
        )
        parser.add_argument(
            '--check-variables',
            action='store_true',
            help='Check for missing variables without processing'
        )
        parser.add_argument(
            '--show-substitutions',
            action='store_true',
            help='Show variable substitutions made'
        )
        
        # Note: Dynamic variable arguments (--var_name value) are handled in the router
        # They will be parsed from unknown_args in the CLI router
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """Validate command arguments."""
        if not args.name.strip():
            self.console.print("[red]Prompt name cannot be empty[/red]")
            return False
        
        if not args.message.strip():
            self.console.print("[red]Message cannot be empty[/red]")
            return False
        
        return True
    
    async def execute(self, args: argparse.Namespace) -> CommandResponse:
        """Execute the use command."""
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
                template_content = f.read()
            
            # Get variables from args (these would be set by the router from unknown_args)
            variables = getattr(args, 'variables', {})
            
            # Add message as a built-in variable
            variables['message'] = args.message
            
            # Check for missing variables
            missing_vars = find_missing_variables(template_content, variables)
            
            if args.check_variables:
                if missing_vars:
                    self.console.print(f"[yellow]Missing variables for prompt '{args.name}':[/yellow]")
                    for var in sorted(missing_vars):
                        self.console.print(f"  --{var} <value>")
                    return CommandResponse(
                        success=False,
                        message=f"Missing {len(missing_vars)} variables",
                        data={
                            "missing_variables": missing_vars,
                            "provided_variables": list(variables.keys())
                        },
                        exit_code=1
                    )
                else:
                    self.console.print(f"[green]All variables provided for prompt '{args.name}'[/green]")
                    return CommandResponse(
                        success=True,
                        message="All variables provided",
                        data={
                            "provided_variables": list(variables.keys())
                        }
                    )
            
            if missing_vars:
                self.console.print(f"[yellow]Warning: Missing variables: {', '.join(missing_vars)}[/yellow]")
                self.console.print("[dim]These will appear as {{variable_name}} in the output[/dim]")
            
            # Substitute variables in template
            processed_content = substitute_variables(template_content, variables)
            
            # Show substitutions if requested
            if args.show_substitutions and variables:
                self.console.print(f"[dim]Variable substitutions made:[/dim]")
                for var_name, var_value in variables.items():
                    display_value = var_value[:50] + "..." if len(var_value) > 50 else var_value
                    self.console.print(f"  {var_name} = {display_value}")
                self.console.print()
            
            # Display processed content
            self.console.print(f"[green]Processed Prompt: {args.name}[/green]")
            
            if args.format == 'rich':
                # Rich markdown rendering
                markdown_content = Markdown(processed_content)
                self.console.print(Panel(
                    markdown_content,
                    title=f"🚀 {args.name} (Processed)",
                    border_style="green",
                    padding=(1, 2)
                ))
            
            elif args.format == 'markdown':
                # Syntax highlighted markdown
                syntax = Syntax(
                    processed_content,
                    "markdown",
                    theme="monokai",
                    line_numbers=False,
                    word_wrap=True
                )
                self.console.print(Panel(
                    syntax,
                    title=f"🚀 {args.name} (Markdown)",
                    border_style="blue",
                    padding=(1, 2)
                ))
            
            else:  # raw format
                self.console.print(processed_content)
            
            return CommandResponse(
                success=True,
                message=f"Successfully processed prompt '{args.name}'",
                data={
                    "prompt_name": args.name,
                    "variables_used": variables,
                    "missing_variables": missing_vars,
                    "content_length": len(processed_content),
                    "format": args.format
                }
            )
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Use prompt command failed: {e}")
            raise ConfigurationError(f"Failed to use prompt template: {e}")