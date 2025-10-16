"""Main CLI entry point using Click framework."""

import asyncio
import os
import sys
from typing import Optional

import click
from rich.console import Console

from .context import CLIContext
from .utils import setup_cli_logging, load_environment_variables
from .commands import run, team, worker, prompts, opensearch, modular, test


@click.group()
@click.option('--debug', is_flag=True, help='Enable debug mode')
@click.option('--log-level', type=click.Choice(['DEBUG', 'INFO', 'WARNING', 'ERROR']), 
              help='Set logging level')
@click.option('--output-format', type=click.Choice(['rich', 'json', 'yaml']), 
              default='rich', help='Output format')
@click.pass_context
def cli(ctx, debug: bool, log_level: Optional[str], output_format: str):
    """Gnosari Teams - Multi-Agent AI Team Runner."""
    # Ensure context exists
    ctx.ensure_object(dict)
    
    # Load environment variables
    load_environment_variables()
    
    # Setup logging
    env_log_level = os.getenv('LOG_LEVEL', os.getenv('GNOSARI_CLI_LOG_LEVEL', 'INFO')).upper()
    final_log_level = log_level if log_level else env_log_level
    
    setup_cli_logging(level=final_log_level, debug=debug)
    
    # Create CLI context
    console = Console()
    cli_context = CLIContext(
        console=console,
        debug=debug,
        log_level=final_log_level,
        output_format=output_format
    )
    
    # Store in Click context
    ctx.obj = cli_context


def main(argv=None):
    """Main entry point for the gnosari CLI."""
    try:
        # Add all command groups
        cli.add_command(run.cli, name='run')
        cli.add_command(team.cli, name='team')
        cli.add_command(worker.cli, name='worker')
        cli.add_command(prompts.cli, name='prompts')
        cli.add_command(opensearch.cli, name='opensearch')
        cli.add_command(modular.cli, name='modular')
        cli.add_command(test.cli, name='test')
        
        # Run CLI
        cli(args=argv, standalone_mode=False)
        
    except click.ClickException as e:
        e.show()
        sys.exit(e.exit_code)
    except KeyboardInterrupt:
        console = Console()
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console = Console()
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == '__main__':
    main()