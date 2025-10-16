"""Prompts create command for Gnosari Teams CLI."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict

from rich.panel import Panel

from ...base import AsyncCommand
from ...exceptions import ValidationError, ConfigurationError
from ...registry import register_command
from ...schemas import CommandResponse
from ...utils import ensure_directory_exists
from ....prompts.manager import PromptManager


def substitute_variables(content: str, variables: Dict[str, str]) -> str:
    """Substitute variables in content."""
    result = content
    for var_name, var_value in variables.items():
        placeholder = f"{{{{{var_name}}}}}"
        result = result.replace(placeholder, var_value)
    return result


@register_command("prompts")
class PromptsCreateCommand(AsyncCommand):
    """Create a new prompt file from a template."""
    
    name = "create"
    description = "Create a new prompt file from a template"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            'name',
            help='Name of the template to use (without .md extension)'
        )
        parser.add_argument(
            'filepath',
            help='Path where the new prompt file should be saved'
        )
        parser.add_argument(
            'message',
            help='Message for the prompt creation'
        )
        parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='Overwrite existing file if it exists'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating the file'
        )
        
        # Note: Dynamic variable arguments (--var_name value) are handled in the router
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """Validate command arguments."""
        if not args.name.strip():
            self.console.print("[red]Template name cannot be empty[/red]")
            return False
        
        if not args.filepath.strip():
            self.console.print("[red]File path cannot be empty[/red]")
            return False
        
        if not args.message.strip():
            self.console.print("[red]Message cannot be empty[/red]")
            return False
        
        # Check if output file already exists
        output_path = Path(args.filepath)
        if output_path.exists() and not args.force and not args.dry_run:
            self.console.print(f"[red]File already exists: {output_path}[/red]")
            self.console.print("[yellow]Use --force to overwrite or choose a different path[/yellow]")
            return False
        
        return True
    
    async def execute(self, args: argparse.Namespace) -> CommandResponse:
        """Execute the create command."""
        try:
            prompt_manager = PromptManager()
            
            # Check if template exists
            available_prompts = await prompt_manager.list_available_prompts()
            if args.name not in available_prompts:
                available_list = ", ".join(sorted(available_prompts))
                raise ValidationError(
                    f"Prompt template '{args.name}' not found. "
                    f"Available templates: {available_list}"
                )
            
            # Load template content
            template_path = prompt_manager.get_prompt_path(args.name)
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            # Get variables from args (these would be set by the router from unknown_args)
            variables = getattr(args, 'variables', {})
            
            # Add message as a built-in variable
            variables['message'] = args.message
            
            # Substitute variables in template
            processed_content = substitute_variables(template_content, variables)
            
            output_path = Path(args.filepath)
            
            if args.dry_run:
                # Dry run - show what would be created
                self.console.print(f"[blue]Dry run: Would create file at:[/blue] {output_path}")
                self.console.print(f"[blue]Template:[/blue] {args.name}")
                self.console.print(f"[blue]Variables used:[/blue] {len(variables)}")
                
                for var_name, var_value in variables.items():
                    display_value = var_value[:50] + "..." if len(var_value) > 50 else var_value
                    self.console.print(f"  {var_name} = {display_value}")
                
                self.console.print("\n[dim]Preview of processed content:[/dim]")
                preview_content = processed_content[:500] + "..." if len(processed_content) > 500 else processed_content
                
                self.console.print(Panel(
                    preview_content,
                    title="Content Preview",
                    border_style="blue"
                ))
                
                return CommandResponse(
                    success=True,
                    message="Dry run completed - no file was created",
                    data={
                        "template_name": args.name,
                        "output_path": str(output_path),
                        "variables_used": variables,
                        "content_length": len(processed_content),
                        "dry_run": True
                    }
                )
            
            # Ensure output directory exists
            ensure_directory_exists(output_path.parent)
            
            # Write the processed content to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(processed_content)
            
            self.console.print(f"[green]✅ Successfully created prompt file![/green]")
            self.console.print(f"[green]Template:[/green] {args.name}")
            self.console.print(f"[green]Output file:[/green] {output_path}")
            self.console.print(f"[green]File size:[/green] {len(processed_content):,} characters")
            
            if variables:
                self.console.print(f"\n[dim]Variables substituted:[/dim]")
                for var_name, var_value in variables.items():
                    display_value = var_value[:50] + "..." if len(var_value) > 50 else var_value
                    self.console.print(f"  {var_name} = {display_value}")
            
            # Show next steps
            next_steps_panel = Panel(
                "[bold]Next Steps:[/bold]\n"
                f"1. Review the created file: [cyan]{output_path}[/cyan]\n"
                "2. Edit the content as needed\n"
                "3. Use the prompt in your team configurations",
                title="📝 File Created",
                border_style="green"
            )
            self.console.print(next_steps_panel)
            
            return CommandResponse(
                success=True,
                message="Prompt file created successfully",
                data={
                    "template_name": args.name,
                    "output_path": str(output_path),
                    "variables_used": variables,
                    "content_length": len(processed_content),
                    "file_size": output_path.stat().st_size if output_path.exists() else 0
                }
            )
            
        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Create prompt command failed: {e}")
            raise ConfigurationError(f"Failed to create prompt file: {e}")