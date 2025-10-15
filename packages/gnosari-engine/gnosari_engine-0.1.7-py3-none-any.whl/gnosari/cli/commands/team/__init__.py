"""Team command module."""

import click
from ...context import CLIContext


@click.group()
def cli():
    """Team management commands."""
    pass


@cli.command()
@click.argument('team_path', type=click.Path(exists=True))
@click.option('--api-url', help='Custom API URL')
@click.pass_obj
def push(ctx: CLIContext, team_path: str, api_url: str = None):
    """Push team configuration to Gnosari API."""
    try:
        from .push import PushCommand
        cmd = PushCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.team_path = team_path
                self.api_url = api_url
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if result.success:
            ctx.print_success(result.message or "Team pushed successfully")
        else:
            ctx.print_error(result.message or "Failed to push team")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to push team: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command()
@click.argument('team_identifier')
@click.option('--api-url', help='Custom API URL')
@click.pass_obj
def pull(ctx: CLIContext, team_identifier: str, api_url: str = None):
    """Pull team configuration from Gnosari API."""
    try:
        from .pull import PullCommand
        cmd = PullCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.team_identifier = team_identifier
                self.api_url = api_url
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if result.success:
            ctx.print_success(result.message or "Team pulled successfully")
        else:
            ctx.print_error(result.message or "Failed to pull team")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to pull team: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command('show-prompts')
@click.argument('team_path', type=click.Path(exists=True))
@click.option('--agent', '-a', help='Show prompts for specific agent only')
@click.pass_obj
def show_prompts(ctx: CLIContext, team_path: str, agent: str = None):
    """Display the generated system prompts for team agents."""
    try:
        from .show_prompts import ShowPromptsCommand
        cmd = ShowPromptsCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.team_path = team_path
                self.agent = agent
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if not result.success:
            ctx.print_error(result.message or "Failed to show prompts")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to show prompts: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command('structure')
@click.argument('team_path', type=click.Path(exists=True))
@click.option('--detailed', '-d', is_flag=True, help='Show detailed information including learning data and traits')
@click.option('--format', '-f', type=click.Choice(['tree', 'table', 'json']), default='tree', 
              help='Output format: tree (visual), table (tabular), json (machine-readable)')
@click.pass_obj
def structure(ctx: CLIContext, team_path: str, detailed: bool = False, format: str = 'tree'):
    """Display comprehensive team structure including agents, tools, knowledge, and relationships."""
    try:
        from .structure import StructureCommand
        cmd = StructureCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.team_path = team_path
                self.detailed = detailed
                self.format = format
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if not result.success:
            ctx.print_error(result.message or "Failed to display team structure")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to display team structure: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command()
@click.argument('team_path', type=click.Path(exists=True))
@click.option('--agent', '-a', help='Learn for specific agent only')
@click.option('--mode', '-m', type=click.Choice(['sync', 'async']), default='async', 
              help='Execution mode: sync (immediate) or async (queue-based)')
@click.option('--wait', '-w', is_flag=True, help='Wait for async learning to complete')
@click.option('--team-wide', '-t', is_flag=True, 
              help='Use all team conversations for learning (not just agent-specific sessions)')
@click.pass_obj
def learn(ctx: CLIContext, team_path: str, agent: str = None, mode: str = 'async', wait: bool = False, team_wide: bool = False):
    """Trigger learning for team agents based on session history.
    
    Execution Modes:
    - sync: Execute learning immediately and return results
    - async: Queue learning tasks for background processing (default)
    """
    try:
        from .learn import LearnCommand
        cmd = LearnCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.team_path = team_path
                self.agent = agent
                self.mode = mode
                self.wait = wait
                self.team_wide = team_wide
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if result.success:
            ctx.print_success(result.message)
        else:
            ctx.print_error(result.message or "Learning failed")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to execute learning: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)