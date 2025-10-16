"""Modular merge command for Gnosari Teams CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from ...base import AsyncCommand
from ...exceptions import ValidationError, ConfigurationError
from ...registry import register_command
from ...schemas import CommandResponse


@register_command("modular")
class ModularMergeCommand(AsyncCommand):
    """Merge modular components into monolithic YAML."""
    
    name = "merge"
    description = "Merge modular components into monolithic YAML"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            'team_dir',
            help='Path to modular team directory'
        )
        parser.add_argument(
            'output_file',
            help='Output YAML file path'
        )
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """Validate command arguments."""
        # Check if team directory exists
        team_path = Path(args.team_dir)
        if not team_path.exists():
            self.console.print(f"[red]Modular team directory not found: {team_path}[/red]")
            return False
        
        if not team_path.is_dir():
            self.console.print(f"[red]Path is not a directory: {team_path}[/red]")
            return False
        
        return True
    
    async def execute(self, args: argparse.Namespace) -> CommandResponse:
        """Execute the merge command."""
        try:
            from ....engine.config.team_splitter import TeamConfigurationMerger
            
            self.console.print(f"[blue]Merging modular team:[/blue] {args.team_dir}")
            self.console.print(f"[blue]Output file:[/blue] {args.output_file}")
            
            # Create merger and merge configuration
            merger = TeamConfigurationMerger()
            await merger.merge_configuration(Path(args.team_dir), Path(args.output_file))
            
            self.console.print(f"[green]✅ Successfully merged modular configuration![/green]")
            self.console.print(f"[green]Monolithic YAML created at:[/green] {args.output_file}")
            
            # Show file size information
            output_path = Path(args.output_file)
            if output_path.exists():
                file_size = output_path.stat().st_size
                self.console.print(f"[dim]Output file size: {file_size:,} bytes[/dim]")
            
            return CommandResponse(
                success=True,
                message="Configuration merged successfully",
                data={
                    "input_directory": args.team_dir,
                    "output_file": args.output_file,
                    "file_size": file_size if output_path.exists() else 0
                }
            )
            
        except Exception as e:
            self.logger.error(f"Merge command failed: {e}")
            raise ConfigurationError(f"Failed to merge configuration: {e}")