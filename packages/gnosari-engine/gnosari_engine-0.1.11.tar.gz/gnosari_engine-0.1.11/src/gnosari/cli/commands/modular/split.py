"""Modular split command for Gnosari Teams CLI."""

from __future__ import annotations

import argparse
from pathlib import Path

from ...base import AsyncCommand
from ...exceptions import ValidationError, ConfigurationError
from ...registry import register_command
from ...schemas import CommandResponse
from ...utils import ensure_directory_exists


@register_command("modular")
class ModularSplitCommand(AsyncCommand):
    """Split monolithic YAML into modular components."""
    
    name = "split"
    description = "Split monolithic YAML into modular components"
    
    def add_arguments(self, parser: argparse.ArgumentParser) -> None:
        """Add command-specific arguments."""
        parser.add_argument(
            'yaml_file',
            help='Path to existing team YAML file'
        )
        parser.add_argument(
            'output_dir',
            help='Output directory for modular components'
        )
    
    def validate_args(self, args: argparse.Namespace) -> bool:
        """Validate command arguments."""
        # Check if YAML file exists
        yaml_path = Path(args.yaml_file)
        if not yaml_path.exists():
            self.console.print(f"[red]YAML file not found: {yaml_path}[/red]")
            return False
        
        if not yaml_path.is_file():
            self.console.print(f"[red]Path is not a file: {yaml_path}[/red]")
            return False
        
        return True
    
    async def execute(self, args: argparse.Namespace) -> CommandResponse:
        """Execute the split command."""
        try:
            from ....engine.config.team_splitter import TeamConfigurationSplitter
            
            self.console.print(f"[blue]Splitting monolithic YAML:[/blue] {args.yaml_file}")
            self.console.print(f"[blue]Output directory:[/blue] {args.output_dir}")
            
            # Ensure output directory exists
            output_path = Path(args.output_dir)
            ensure_directory_exists(output_path)
            
            # Create splitter and split configuration
            splitter = TeamConfigurationSplitter()
            await splitter.split_configuration(Path(args.yaml_file), output_path)
            
            self.console.print(f"[green]✅ Successfully split configuration into modular format![/green]")
            self.console.print(f"[green]Modular team created at:[/green] {args.output_dir}")
            
            # List created files
            created_files = []
            for item in output_path.rglob('*'):
                if item.is_file():
                    created_files.append(str(item.relative_to(output_path)))
            
            if created_files:
                self.console.print(f"\n[dim]Created files:[/dim]")
                for file_path in sorted(created_files):
                    self.console.print(f"  - {file_path}")
            
            return CommandResponse(
                success=True,
                message="Configuration split successfully",
                data={
                    "input_file": args.yaml_file,
                    "output_directory": args.output_dir,
                    "created_files": created_files
                }
            )
            
        except Exception as e:
            self.logger.error(f"Split command failed: {e}")
            raise ConfigurationError(f"Failed to split configuration: {e}")