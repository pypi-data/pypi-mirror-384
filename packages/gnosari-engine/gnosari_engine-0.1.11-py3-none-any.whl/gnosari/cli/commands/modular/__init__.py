"""Modular command module."""

import click
from ...context import CLIContext


@click.group()
def cli():
    """Modular team configuration commands."""
    pass


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.argument('output_dir', type=click.Path())
@click.pass_obj
def split(ctx: CLIContext, input_path: str, output_dir: str):
    """Split monolithic team YAML into modular directory structure."""
    try:
        from .split import ModularSplitCommand
        cmd = ModularSplitCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.input_path = input_path
                self.output_dir = output_dir
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if result.success:
            ctx.print_success(result.message or "Team split successfully")
        else:
            ctx.print_error(result.message or "Failed to split team")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to split team: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True))
@click.argument('output_path', type=click.Path())
@click.pass_obj
def merge(ctx: CLIContext, input_dir: str, output_path: str):
    """Merge modular directory structure into monolithic team YAML."""
    try:
        from .merge import ModularMergeCommand
        cmd = ModularMergeCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.input_dir = input_dir
                self.output_path = output_path
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if result.success:
            ctx.print_success(result.message or "Team merged successfully")
        else:
            ctx.print_error(result.message or "Failed to merge team")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to merge team: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command()
@click.argument('team_dir', type=click.Path(exists=True))
@click.pass_obj
def validate(ctx: CLIContext, team_dir: str):
    """Validate modular team configuration."""
    try:
        from .validate import ModularValidateCommand
        cmd = ModularValidateCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.team_dir = team_dir
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if result.success:
            ctx.print_success(result.message or "Team configuration is valid")
        else:
            ctx.print_error(result.message or "Team configuration is invalid")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to validate team: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command()
@click.argument('team_dir', type=click.Path())
@click.option('--team-name', prompt='Team name', help='Name of the team')
@click.option('--description', prompt='Team description', help='Description of the team')
@click.pass_obj
def init(ctx: CLIContext, team_dir: str, team_name: str, description: str):
    """Initialize a new modular team configuration directory."""
    try:
        from .init import ModularInitCommand
        cmd = ModularInitCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.team_dir = team_dir
                self.team_name = team_name
                self.description = description
        
        import asyncio
        result = asyncio.run(cmd.run(Args()))
        
        if result.success:
            ctx.print_success(result.message or "Team initialized successfully")
        else:
            ctx.print_error(result.message or "Failed to initialize team")
            raise click.Exit(1)
            
    except Exception as e:
        ctx.print_error(f"Failed to initialize team: {e}")
        if ctx.debug:
            import traceback
            ctx.console.print(traceback.format_exc())
        raise click.Exit(1)


@cli.command('show-prompts')
@click.argument('team_dir', type=click.Path(exists=True))
@click.option('--agent', '-a', help='Show prompts for specific agent only')
@click.pass_obj
def show_prompts(ctx: CLIContext, team_dir: str, agent: str = None):
    """Display the generated system prompts for modular team agents."""
    try:
        from .show_prompts import ModularShowPromptsCommand
        cmd = ModularShowPromptsCommand(ctx.console)
        # Convert to args object for compatibility
        class Args:
            def __init__(self):
                self.team_dir = team_dir
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