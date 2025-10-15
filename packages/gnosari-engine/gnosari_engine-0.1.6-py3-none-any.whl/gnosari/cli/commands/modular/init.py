"""Modular init command for Gnosari Teams CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from rich.panel import Panel

from ...base import AsyncCommand
from ...exceptions import ValidationError, ConfigurationError
from ...registry import register_command
from ...schemas import CommandResponse
from ...utils import ensure_directory_exists


@register_command("modular")
class ModularInitCommand(AsyncCommand):
    """Initialize new modular team structure."""
    
    name = "init"
    description = "Initialize new modular team structure"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            'team_name',
            help='Name of the new team'
        )
        parser.add_argument(
            '--template',
            default='basic',
            choices=['basic', 'support', 'research'],
            help='Team template to use (default: basic)'
        )
        parser.add_argument(
            '--output-dir',
            default='./teams',
            help='Output directory for team (default: ./teams)'
        )
        parser.add_argument(
            '--force', '-f',
            action='store_true',
            help='Overwrite existing team directory if it exists'
        )
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """Validate command arguments."""
        # Validate team name
        if not args.team_name.strip():
            self.console.print("[red]Team name cannot be empty[/red]")
            return False
        
        # Check if output directory would conflict
        output_path = Path(args.output_dir) / args.team_name
        if output_path.exists() and not args.force:
            self.console.print(f"[red]Team directory already exists: {output_path}[/red]")
            self.console.print("[yellow]Use --force to overwrite existing directory[/yellow]")
            return False
        
        return True
    
    async def execute(self, args: argparse.Namespace) -> CommandResponse:
        """Execute the init command."""
        try:
            from ....engine.config.team_templates import TeamTemplateGenerator
            
            self.console.print(f"[blue]Initializing modular team:[/blue] {args.team_name}")
            self.console.print(f"[blue]Template:[/blue] {args.template}")
            self.console.print(f"[blue]Output directory:[/blue] {args.output_dir}")
            
            # Ensure output directory exists
            output_path = Path(args.output_dir)
            ensure_directory_exists(output_path)
            
            # Create team from template
            generator = TeamTemplateGenerator()
            team_dir = await generator.create_team_from_template(
                args.team_name, args.template, output_path
            )
            
            self.console.print(f"[green]✅ Successfully initialized modular team![/green]")
            self.console.print(f"[green]Team directory:[/green] {team_dir}")
            
            # Display next steps
            next_steps_panel = Panel(
                "[bold]Next Steps:[/bold]\n"
                "1. Edit component files in agents/, tools/, knowledge/ directories\n"
                "2. Customize main.yaml for overrides and configuration\n"
                f"3. Run with: [cyan]poetry run gnosari modular run {team_dir} --message 'Your message'[/cyan]\n"
                f"4. Test configuration: [cyan]poetry run gnosari modular validate {team_dir}[/cyan]",
                title="🚀 Getting Started",
                border_style="green"
            )
            self.console.print(next_steps_panel)
            
            # List created structure
            created_items = []
            if team_dir.exists():
                for item in team_dir.rglob('*'):
                    if item.is_file():
                        created_items.append(str(item.relative_to(team_dir)))
            
            if created_items:
                self.console.print(f"\n[dim]Created structure:[/dim]")
                for item in sorted(created_items):
                    self.console.print(f"  📄 {item}")
            
            return CommandResponse(
                success=True,
                message="Modular team initialized successfully",
                data={
                    "team_name": args.team_name,
                    "template": args.template,
                    "team_directory": str(team_dir),
                    "created_files": created_items
                }
            )
            
        except Exception as e:
            self.logger.error(f"Init command failed: {e}")
            raise ConfigurationError(f"Failed to initialize modular team: {e}")