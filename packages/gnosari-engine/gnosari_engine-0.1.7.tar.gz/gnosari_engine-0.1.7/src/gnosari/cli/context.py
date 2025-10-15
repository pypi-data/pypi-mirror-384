"""CLI context for maintaining state across commands."""

from dataclasses import dataclass
from typing import Optional

from rich.console import Console


@dataclass
class CLIContext:
    """Context object passed between CLI commands."""
    
    console: Console
    debug: bool = False
    log_level: str = 'INFO'
    output_format: str = 'rich'
    
    def print_debug(self, message: str) -> None:
        """Print debug message if debug mode is enabled."""
        if self.debug:
            self.console.print(f"[dim]DEBUG: {message}[/dim]")
    
    def print_error(self, message: str) -> None:
        """Print error message."""
        self.console.print(f"[red]Error: {message}[/red]")
    
    def print_success(self, message: str) -> None:
        """Print success message."""
        self.console.print(f"[green]{message}[/green]")
    
    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self.console.print(f"[yellow]Warning: {message}[/yellow]")